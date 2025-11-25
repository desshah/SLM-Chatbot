"""
Enhanced RAG Chatbot with Training Data Integration
This version:
1. Uses the enhanced vector database
2. Leverages training Q&A pairs for better responses
3. Provides accurate, context-based answers
4. No repetitive navigation text
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from typing import List, Dict, Tuple
import re

from config import (
    VECTOR_DB_DIR, EMBEDDING_MODEL, BASE_MODEL_NAME,
    FINE_TUNED_MODEL_PATH, TOP_K_RETRIEVAL, DEVICE, USE_MPS
)


class EnhancedRAGChatbot:
    """Enhanced RAG chatbot with better context utilization"""
    
    def __init__(self):
        print("🤖 Initializing Enhanced RAG Chatbot...")
        
        # Set device
        if USE_MPS and torch.backends.mps.is_available():
            self.device = "mps"
            print("✅ Using Apple Silicon (MPS)")
        elif torch.cuda.is_available():
            self.device = "cuda"
            print("✅ Using CUDA")
        else:
            self.device = "cpu"
            print("✅ Using CPU")
        
        # Load vector database
        print("📚 Loading vector database...")
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_collection("rackspace_knowledge")
        
        # Load embedding model
        print(f"🔤 Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Load LLM - USE BASE MODEL (fine-tuned model ignores context)
        print(f"🧠 Loading BASE LLM (no fine-tuning): {BASE_MODEL_NAME}")
        print("   ⚠️  Fine-tuned model disabled - it was overtrained and ignores RAG context")
        
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)
        self.model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_NAME,
            torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
            device_map=self.device if self.device != "mps" else None,
            low_cpu_mem_usage=True
        )
        
        if self.device == "mps":
            self.model = self.model.to(self.device)
        
        self.model.eval()
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
        print("✅ Enhanced RAG Chatbot ready!")
    
    def retrieve_context(self, query: str, top_k: int = TOP_K_RETRIEVAL) -> Tuple[str, List[Dict]]:
        """Retrieve relevant context with source information"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Search vector database - get top K most relevant chunks
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        # Process results - ONLY real documents with URLs
        context_parts = []
        sources = []
        seen_urls = set()  # Track unique URLs
        seen_content = set()  # Track unique content
        
        # Get distances for relevance scoring (lower distance = more relevant)
        distances = results.get('distances', [[]])[0] if 'distances' in results else []
        
        for idx, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            # Skip duplicates
            doc_hash = hash(doc[:100])
            if doc_hash in seen_content:
                continue
            seen_content.add(doc_hash)
            
            # Add document chunk
            context_parts.append(doc)
            
            # Get URL and title
            url = metadata.get('url', 'N/A')
            title = metadata.get('title', 'N/A')
            
            # Only add source if URL is unique and valid
            if url and url != 'N/A' and url not in seen_urls:
                seen_urls.add(url)
                
                # Add relevance score (distance from query)
                relevance = 1.0 - (distances[idx] if idx < len(distances) else 0.5)
                
                sources.append({
                    'url': url,
                    'title': title,
                    'relevance': relevance
                })
        
        # Sort sources by relevance (highest first)
        sources.sort(key=lambda x: x.get('relevance', 0), reverse=True)
        
        # Combine context
        context = '\n\n'.join(context_parts)
        
        return context, sources
    
    def build_prompt(self, query: str, context: str, history: List[Dict[str, str]]) -> str:
        """Build prompt for the model - Force it to use ONLY the context"""
        
        prompt = f"""<|system|>
You are a helpful assistant. Answer the question using ONLY the information in the Context below. Do not make up information. Be concise and accurate.
<|user|>
Context:
{context}

Question: {query}

Answer using ONLY the information above:
<|assistant|>
"""
        
        return prompt
    
    def generate_response(self, prompt: str) -> str:
        """Generate response from the model"""
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate with stricter parameters to reduce hallucination
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=150,  # Reasonable length
                temperature=0.1,  # Very low temperature for factual responses
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.3,  # Higher penalty for repetition
                no_repeat_ngram_size=4,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the assistant's response
        if "<|assistant|>" in response:
            response = response.split("<|assistant|>")[-1].strip()
        
        # Clean up aggressive extraction
        # Remove everything before first actual sentence
        lines = response.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip system-like patterns
            if any(skip in line.lower() for skip in [
                'you are', 'answer the question', 'context:', 'question:', 
                'using only', 'be concise', '<|', '|>'
            ]):
                continue
            # Skip empty lines
            if not line:
                continue
            clean_lines.append(line)
        
        response = ' '.join(clean_lines)
        
        # If response is too short or still has issues, extract meaningful content
        if len(response) < 20 or 'based on actual answers' in response.lower():
            # Try to find the actual answer in the response
            sentences = response.split('.')
            good_sentences = []
            for sent in sentences:
                sent = sent.strip()
                # Skip bad patterns
                if any(bad in sent.lower() for bad in [
                    'based on actual', 'answer based', 'yes!', 'here\'s some quick facts'
                ]):
                    continue
                if sent and len(sent) > 10:
                    good_sentences.append(sent)
            
            if good_sentences:
                response = '. '.join(good_sentences[:3])  # Max 3 sentences
                if response and not response.endswith('.'):
                    response += '.'
        
        # Clean up
        response = self.clean_response(response)
        
        return response
    
    def clean_response(self, text: str) -> str:
        """Clean up the generated response"""
        # Remove any remaining system/user markers
        text = re.sub(r'<\|.*?\|>', '', text)
        
        # Remove repetitive sentences
        sentences = text.split('.')
        unique_sentences = []
        seen = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence.lower() not in seen:
                unique_sentences.append(sentence)
                seen.add(sentence.lower())
        
        text = '. '.join(unique_sentences)
        if text and not text.endswith('.'):
            text += '.'
        
        return text.strip()
    
    def format_sources(self, sources: List[Dict], response: str = "") -> str:
        """Format sources for display - DISABLED until we fix the retrieval issue"""
        # Sources are showing same URLs for every question
        # Disable until we properly fix the vector DB retrieval
        return ""
    
    def extract_services_list(self, context: str, sources: List[Dict]) -> str:
        """
        Extract service information directly from context WITHOUT LLM generation.
        This is FULLY EXTRACTIVE - no hallucinations possible.
        """
        services = []
        seen_services = set()
        
        # Extract services from retrieved documents
        lines = context.split('\n')
        
        for line in lines:
            line_lower = line.strip().lower()
            
            # Look for service mentions
            if 'aws' in line_lower and 'aws' not in seen_services:
                services.append("AWS Cloud Services and Managed AWS Solutions")
                seen_services.add('aws')
            if 'azure' in line_lower and 'azure' not in seen_services:
                services.append("Microsoft Azure Cloud Managed Services")
                seen_services.add('azure')
            if 'google cloud' in line_lower and 'google' not in seen_services:
                services.append("Google Cloud Platform (GCP) Services")
                seen_services.add('google')
            if 'kubernetes' in line_lower and 'kubernetes' not in seen_services:
                services.append("Managed Kubernetes and Container Services")
                seen_services.add('kubernetes')
            if 'security' in line_lower and 'security' not in seen_services:
                services.append("Cloud Security and Cybersecurity Solutions")
                seen_services.add('security')
            if 'migration' in line_lower and 'cloud' in line_lower and 'migration' not in seen_services:
                services.append("Cloud Migration and Adoption Services")
                seen_services.add('migration')
            if (('data' in line_lower and 'analytics' in line_lower) or 
                ('ai' in line_lower and 'ml' in line_lower)) and 'data' not in seen_services:
                services.append("Data Analytics, AI and Machine Learning")
                seen_services.add('data')
            if ('multicloud' in line_lower or 'multi-cloud' in line_lower) and 'multicloud' not in seen_services:
                services.append("Multi-Cloud and Hybrid Cloud Solutions")
                seen_services.add('multicloud')
            if ('professional services' in line_lower or 'consulting' in line_lower) and 'professional' not in seen_services:
                services.append("Professional Services and Consulting")
                seen_services.add('professional')
            if ('application' in line_lower and 
                ('modernization' in line_lower or 'development' in line_lower)) and 'apps' not in seen_services:
                services.append("Application Modernization and Development")
                seen_services.add('apps')
            if ('managed hosting' in line_lower or 'dedicated hosting' in line_lower) and 'hosting' not in seen_services:
                services.append("Managed Hosting and Dedicated Infrastructure")
                seen_services.add('hosting')
            if ('compliance' in line_lower and 
                ('fedramp' in line_lower or 'government' in line_lower)) and 'compliance' not in seen_services:
                services.append("FedRAMP Compliance and Government Cloud")
                seen_services.add('compliance')
        
        # Also check URLs for service categories
        for source in sources[:10]:
            url = source.get('url', '').lower()
            if '/aws' in url and 'aws' not in seen_services:
                services.append("AWS Cloud Services and Managed AWS Solutions")
                seen_services.add('aws')
            if '/azure' in url and 'azure' not in seen_services:
                services.append("Microsoft Azure Cloud Managed Services")
                seen_services.add('azure')
            if '/google-cloud' in url and 'google' not in seen_services:
                services.append("Google Cloud Platform (GCP) Services")
                seen_services.add('google')
            if '/kubernetes' in url and 'kubernetes' not in seen_services:
                services.append("Managed Kubernetes and Container Services")
                seen_services.add('kubernetes')
            if '/security' in url and 'security' not in seen_services:
                services.append("Cloud Security and Cybersecurity Solutions")
                seen_services.add('security')
            if '/migration' in url and 'migration' not in seen_services:
                services.append("Cloud Migration and Adoption Services")
                seen_services.add('migration')
            if '/data' in url and 'data' not in seen_services:
                services.append("Data Analytics, AI and Machine Learning")
                seen_services.add('data')
            if '/multi-cloud' in url and 'multicloud' not in seen_services:
                services.append("Multi-Cloud and Hybrid Cloud Solutions")
                seen_services.add('multicloud')
            if '/professional-services' in url and 'professional' not in seen_services:
                services.append("Professional Services and Consulting")
                seen_services.add('professional')
            if '/applications' in url and 'apps' not in seen_services:
                services.append("Application Management and Modernization")
                seen_services.add('apps')
        
        if not services:
            return None
        
        # Format response
        response = "Based on the available documentation, Rackspace Technology offers the following services:\n\n"
        for i, service in enumerate(services, 1):
            response += f"{i}. {service}\n"
        
        # Add source URLs (only unique, relevant ones)
        response += "\n**Learn more at:**\n"
        unique_urls = []
        for source in sources[:5]:
            url = source.get('url', '')
            if url and url not in unique_urls:
                unique_urls.append(url)
                response += f"• {url}\n"
        
        return response
    
    def generate_summary_with_citations(self, query: str, context: str, sources: List[Dict], history: str = None) -> str:
        """
        SUMMARIZATION MODE — Uses LLM to generate concise summaries with citations
        
        Generate a natural, concise summary from the context and add inline citations.
        
        Args:
            query: User's question
            context: Retrieved context from vector DB
            sources: Source documents with URLs
            history: Optional conversation history (for follow-up questions)
        
        Rules:
        - Use LLM to synthesize information from multiple sources
        - Generate 2-4 sentence summaries (concise and readable)
        - Add inline citations like [Source: URL] after key facts
        - Avoid marketing fluff - focus on factual information
        - If context insufficient: acknowledge limitations
        """
        
        # Build history context if provided
        history_context = ""
        if history:
            history_context = f"\nPrevious conversation:\n{history}\n"
        
        # Build a specialized prompt for summarization
        prompt = f"""<|system|>
You are a helpful assistant that provides concise summaries with citations. 
Summarize the answer to the question in 2-4 clear sentences using the Context below.
Focus on factual, technical details. Avoid marketing language.
After each key fact, add a citation: [Source: doc1], [Source: doc2], etc.
<|user|>
{history_context}Context:
{context[:1500]}

Question: {query}

Provide a concise 2-4 sentence summary with inline citations:
<|assistant|>
"""
        
        # Generate summary using LLM
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=200,  # Allow longer for citations
                temperature=0.4,  # Higher for more natural language
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.3,
                no_repeat_ngram_size=3,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode response
        summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only assistant's response
        if "<|assistant|>" in summary:
            summary = summary.split("<|assistant|>")[-1].strip()
        
        # Clean up
        summary = self.clean_response(summary)
        
        # Add actual source URLs at the end
        if sources and summary:
            summary += "\n\n**Referenced Sources:**\n"
            for idx, source in enumerate(sources[:3], 1):
                url = source.get('url', '')
                title = source.get('title', 'Document')
                if url:
                    summary += f"• [{title}]({url})\n"
        
        return summary
    
    def extract_answer_from_context(self, query: str, context: str, sources: List[Dict]) -> str:
        """
        EXTRACTION MODE (STRICT RETRIEVAL) — NO LLM GENERATION
        
        Extract answer directly from context using EXACT or NEAR-EXACT wording.
        Do NOT generate, infer, summarize beyond what context states.
        
        Rules:
        - For HOW/WHAT: prioritize procedural, operational, architectural details
        - Ignore marketing/promotional language
        - If context doesn't contain answer: return "Context does not contain the answer"
        - Behave like a retrieval engine, NOT a generative model
        """
        
        # Strict noise patterns - SKIP ENTIRELY
        noise_patterns = [
            'rackspace technology privacy notice',
            'to create a ticket', 'log into your account', 'fill out the form',
            'ready to start the conversation', 'you may withdraw your consent',
            'begin your', 'businesses today', 'journey',
            'accelerate digital transformation', 'struggling to',
            'transition to', 'move to', 'moving to',
            'ai launchpad', 'introduces new layers',  # Generic AI marketing
            'cuts through that complexity'  # Generic promises
        ]
        
        # Marketing phrases that indicate NON-ANSWER paragraphs
        marketing_indicators = [
            'begin', 'start your', 'embark', 'journey', 'transformation',
            'businesses are', 'organizations are', 'companies are',
            'introducing', 'discover', 'explore', 'learn how'
        ]
        
        # Answer phrases - paragraphs with these are ACTUAL ANSWERS
        answer_indicators = [
            'provides a', 'solves', 'by providing', 'includes',
            'comprised of', 'consists of', 'offers',
            'single pane of glass', 'curated platform',
            'specialized support', 'managed platform',
            'solution', 'features', 'capabilities'
        ]
        
        # Detect query type
        query_lower = query.lower()
        is_how_question = any(w in query_lower for w in ['how', 'manage', 'manages', 'managing'])
        is_what_question = any(w in query_lower for w in ['what', 'which', 'describe'])
        is_tell_me_about = 'tell me about' in query_lower or 'tell me more about' in query_lower
        
        # Extract query keywords for matching
        query_keywords = [w for w in query_lower.split() if len(w) > 3 and w not in ['does', 'will', 'can', 'tell', 'about']]
        
        # Split context into paragraphs AND sentences for better granularity
        paragraphs = []
        
        # First try splitting by double newlines (paragraphs)
        raw_paragraphs = context.split('\n\n')
        for para in raw_paragraphs:
            para = para.strip()
            if len(para) > 50:
                paragraphs.append(para)
        
        # If paragraphs are too long (>800 chars), split them further by sentences
        expanded_paragraphs = []
        for para in paragraphs:
            if len(para) > 800:
                # Split long paragraph into smaller chunks (by period or newline)
                sentences = para.replace('\n', '. ').split('. ')
                current_chunk = []
                current_length = 0
                
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    
                    if current_length + len(sent) > 400:  # Max 400 chars per chunk
                        if current_chunk:
                            expanded_paragraphs.append('. '.join(current_chunk) + '.')
                        current_chunk = [sent]
                        current_length = len(sent)
                    else:
                        current_chunk.append(sent)
                        current_length += len(sent)
                
                if current_chunk:
                    expanded_paragraphs.append('. '.join(current_chunk) + '.')
            else:
                expanded_paragraphs.append(para)
        
        paragraphs = expanded_paragraphs
        
        # STRICT scoring - only paragraphs that DIRECTLY answer
        scored_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            
            # Skip if too short
            if len(para) < 50:
                continue
            
            para_lower = para.lower()
            
            # IMMEDIATE REJECTION for noise
            if any(noise in para_lower for noise in noise_patterns):
                continue
            
            # IMMEDIATE REJECTION if starts with marketing
            first_words = ' '.join(para_lower.split()[:5])
            if any(bad in first_words for bad in marketing_indicators):
                continue
            
            # IMMEDIATE REJECTION if paragraph is just a list (bullets, dashes, numbered)
            # Lists like "- Item1 - Item2 - Item3" are not descriptive answers
            list_indicators = para.count('\n-') + para.count('\n•') + para.count('\n*')
            is_just_list = list_indicators > 3 or (para.count('-') > 5 and len(para) < 300)
            # For "tell me about" queries, skip lists - we want descriptions
            if is_just_list and (is_tell_me_about or is_what_question):
                continue
            
            # Start with negative score
            score = -10
            
            # STRONG BOOST for answer indicators
            answer_phrases = sum(5 for indicator in answer_indicators if indicator in para_lower)
            score += answer_phrases
            
            # BOOST for containing query keywords
            keyword_matches = sum(3 for kw in query_keywords if kw in para_lower)
            score += keyword_matches
            
            # For HOW questions: prioritize procedural/operational language
            if is_how_question:
                how_indicators = [
                    'by providing', 'provides a', 'solves', 'through',
                    'comprised of', 'team', 'support', 'managed',
                    'deployment', 'cluster', 'infrastructure', 'platform'
                ]
                score += sum(4 for ind in how_indicators if ind in para_lower)
            
            # For WHAT questions: prioritize definitions
            if is_what_question or is_tell_me_about:
                what_indicators = [
                    'is a', 'is the', 'powered by', 'solution',
                    'offers', 'includes', 'features', 'enables',
                    'designed to', 'helps', 'allows', 'service that'
                ]
                score += sum(3 for ind in what_indicators if ind in para_lower)
            
            # STRONG PENALTY for marketing fluff
            if any(bad in para_lower for bad in ['journey', 'transformation', 'accelerate', 'complexity']):
                score -= 8
            
            # Only keep paragraphs with positive score
            if score > 0:
                scored_paragraphs.append((score, para))
        
        # Sort by score (highest first)
        scored_paragraphs.sort(reverse=True, key=lambda x: x[0])
        
        # Take top 2-3 paragraphs with highest scores (lowered threshold to 3)
        top_paragraphs = [para for score, para in scored_paragraphs[:3] if score > 3]
        
        # DEBUG: Log scores for troubleshooting
        if not top_paragraphs and scored_paragraphs:
            print(f"⚠️  No paragraphs scored > 3. Top scores: {[(s, p[:80]+'...') for s, p in scored_paragraphs[:3]]}")
        
        if not top_paragraphs:
            return "The provided context does not contain a direct answer to your question. Please try rephrasing or ask about specific Rackspace services."
        
        # Build answer from top-scored paragraphs
        answer = '\n\n'.join(top_paragraphs)
        
        # Limit length (800 chars for detailed answers)
        if len(answer) > 800:
            truncated = answer[:800]
            last_period = truncated.rfind('.')
            if last_period > 200:  # Ensure we keep meaningful content
                answer = truncated[:last_period + 1]
        
        # Add sources
        if sources and answer:
            answer += "\n\n**Source:**\n"
            for source in sources[:2]:
                url = source.get('url', '')
                if url:
                    answer += f"• {url}\n"
        
        return answer
    
    def classify_query_type(self, query: str) -> str:
        """
        Classify query into categories to decide history usage
        
        Returns:
            - "independent": New topic, no history needed
            - "follow_up": Needs previous context (elaboration, clarification)
            - "recall": Asking about conversation itself
        """
        query_lower = query.lower().strip()
        
        # 1. RECALL queries (asking about conversation)
        recall_indicators = [
            'what did i ask', 'what was my question', 'what did we talk about',
            'earlier you said', 'you mentioned', 'my previous question',
            'our conversation', 'what have we discussed', 'remind me what'
        ]
        
        if any(ind in query_lower for ind in recall_indicators):
            return "recall"
        
        # 2. INDEPENDENT queries (new topics, facts, greetings)
        independent_indicators = [
            # Greetings
            'hello', 'hi ', 'hey', 'good morning', 'good afternoon',
            # Full questions (usually new topics)
            'what is rackspace', 'what are rackspace', 'who is rackspace',
            'what services does', 'what does rackspace',
            # List/overview requests
            'list', 'show me', 'give me a list'
        ]
        
        # Check if starts with common question words (likely independent)
        starts_with_wh = any(query_lower.startswith(q) for q in [
            'what is', 'what are', 'who is', 'who are', 
            'when is', 'when was', 'where is', 'where are',
            'which ', 'how much', 'how many'
        ])
        
        # Check independent indicators
        has_independent = any(ind in query_lower for ind in independent_indicators)
        
        if has_independent or (starts_with_wh and len(query_lower.split()) > 4):
            return "independent"
        
        # 3. FOLLOW-UP queries (needs history)
        follow_up_indicators = [
            # Pronouns (it, that, this, them, they)
            ' it ', ' it?', ' it.', 'about it', 'with it', 'of it',
            ' that ', ' that?', ' that.', 'about that', 'with that',
            ' this ', ' this?', ' this.', 'about this', 'with this',
            ' them ', ' them?', ' they ', ' their ', 'those ',
            
            # Continuation words
            'more about', 'tell me more', 'elaborate', 'explain that',
            'why did you', 'how did you', 'can you explain',
            'what do you mean', 'clarify', 'expand on', 'go deeper',
            
            # Comparative/relational
            'compared to', 'difference between', 'versus',
            'how does that', 'why does that', 'what about that'
        ]
        
        # Short queries are usually follow-ups
        is_short = len(query_lower.split()) <= 5
        has_follow_up = any(ind in query_lower for ind in follow_up_indicators)
        
        if has_follow_up or (is_short and not starts_with_wh):
            return "follow_up"
        
        # Default: independent (new topic)
        return "independent"
    
    def handle_recall(self, query: str) -> str:
        """Handle queries asking about conversation history"""
        if not self.conversation_history:
            return "This is the beginning of our conversation. You haven't asked any questions yet."
        
        # Return formatted history
        if len(self.conversation_history) == 1:
            first_q = self.conversation_history[0]['user']
            return f"You asked: '{first_q}'"
        else:
            response = "Here's our conversation so far:\n\n"
            for i, exchange in enumerate(self.conversation_history, 1):
                response += f"{i}. You asked: '{exchange['user']}'\n"
            return response
    
    def extract_subject(self, question: str) -> str:
        """Extract main subject from question for pronoun resolution"""
        question_lower = question.lower()
        
        # Patterns: "tell me about X", "what is X", "how does X"
        patterns = [
            ('tell me about ', 4),
            ('what is ', 3),
            ('what are ', 3),
            ('how does ', 3),
            ('how do ', 3),
            ('what does ', 3),
            ('about ', 2)
        ]
        
        for pattern, max_words in patterns:
            if pattern in question_lower:
                subject = question_lower.split(pattern)[-1].strip()
                # Take first few words
                subject_words = subject.split()[:max_words]
                # Remove question marks
                subject = ' '.join(subject_words).replace('?', '').strip()
                if subject:
                    return subject
        
        return ""
    
    def rewrite_query_with_history(self, query: str, history: str) -> str:
        """
        Rewrite follow-up query with relevant history context
        Simple concatenation approach (no LLM needed)
        """
        if not history:
            return query
        
        # Extract last question from history
        history_lines = history.strip().split('\n')
        last_question = None
        
        for line in history_lines:
            if line.startswith('User:'):
                last_question = line.replace('User:', '').strip()
        
        if not last_question:
            return query
        
        query_lower = query.lower()
        
        # Resolve pronouns
        query_resolved = query
        
        # Replace "it" with subject from last question
        if ' it ' in query_lower or query_lower.endswith('it?') or query_lower.startswith('it '):
            subject = self.extract_subject(last_question)
            if subject:
                query_resolved = query_resolved.replace(' it ', f' {subject} ')
                query_resolved = query_resolved.replace('it?', f'{subject}?')
                query_resolved = query_resolved.replace('It ', f'{subject.capitalize()} ')
        
        # Replace "that" similarly
        if ' that ' in query_lower or query_lower.endswith('that?'):
            subject = self.extract_subject(last_question)
            if subject:
                query_resolved = query_resolved.replace(' that ', f' {subject} ')
                query_resolved = query_resolved.replace('that?', f'{subject}?')
        
        # Replace "this" similarly
        if ' this ' in query_lower or query_lower.endswith('this?'):
            subject = self.extract_subject(last_question)
            if subject:
                query_resolved = query_resolved.replace(' this ', f' {subject} ')
                query_resolved = query_resolved.replace('this?', f'{subject}?')
        
        # For elaboration requests, combine with original question
        if any(word in query_lower for word in ['more', 'elaborate', 'explain', 'why did you', 'how did you']):
            query_resolved = f"{last_question} - {query_resolved}"
        
        return query_resolved
    
    def get_recent_history(self, n: int = 2) -> str:
        """Get last N exchanges formatted for context"""
        if not self.conversation_history:
            return ""
        
        recent = self.conversation_history[-n:] if len(self.conversation_history) >= n else self.conversation_history
        
        history_str = ""
        for exchange in recent:
            history_str += f"User: {exchange['user']}\n"
            # Truncate assistant response to save tokens
            assistant_response = exchange['assistant'][:200]
            if len(exchange['assistant']) > 200:
                assistant_response += "..."
            history_str += f"Assistant: {assistant_response}\n\n"
        
        return history_str
    
    def chat(self, user_message: str, mode: str = "extract") -> str:
        """
        Main chat interface with DUAL MODE support
        
        Args:
            user_message: The user's question
            mode: "extract" (default) or "summarize"
                - "extract": Returns exact text from documents (STRICT RETRIEVAL)
                - "summarize": Uses LLM to generate concise summaries with citations
        
        Returns:
            Response string based on selected mode
        """
        print(f"\n📝 Processing: {user_message}")
        print(f"🎯 Mode: {mode.upper()}")
        
        # 1. CLASSIFY QUERY TYPE (intelligent context detection)
        query_type = self.classify_query_type(user_message)
        print(f"🔍 Query type: {query_type.upper()}")
        
        # 2. HANDLE RECALL QUERIES (return from history directly)
        if query_type == "recall":
            return self.handle_recall(user_message)
        
        # 3. REWRITE QUERY IF FOLLOW-UP (with history context)
        if query_type == "follow_up":
            history_context = self.get_recent_history(n=2)
            search_query = self.rewrite_query_with_history(user_message, history_context)
            print(f"✅ Using history - Rewritten: {search_query[:80]}...")
        else:
            search_query = user_message
            print(f"🆕 New topic - Using original query")
        
        # 4. DETECT LIST QUERIES
        list_keywords = ['list', 'services', 'offer', 'provide', 'what does rackspace',
                        'tell me about services', 'what are the services', 'which services']
        is_list_query = any(keyword in user_message.lower() for keyword in list_keywords)
        
        # 5. RETRIEVE CONTEXT (use rewritten query for better results)
        top_k = 10 if is_list_query else 5
        context, sources = self.retrieve_context(search_query, top_k=top_k)
        
        if not context:
            return "I couldn't find relevant information to answer your question. Please try rephrasing or ask about Rackspace's cloud services, security, migration, or professional services."
        
        # 6. FOR SERVICE LIST QUERIES, use service extractor (works for both modes)
        if is_list_query:
            print("🔍 Using extractive approach for service list")
            extractive_response = self.extract_services_list(context, sources)
            if extractive_response:
                # Update history
                self.conversation_history.append({
                    'user': user_message,
                    'assistant': extractive_response
                })
                if len(self.conversation_history) > 5:
                    self.conversation_history = self.conversation_history[-5:]
                return extractive_response
        
        # 7. GENERATE RESPONSE based on mode (with conditional history)
        if mode == "summarize":
            print("📝 Using SUMMARIZATION mode - LLM generates concise summary with citations")
            # Pass history ONLY for follow-ups
            history = self.get_recent_history(n=2) if query_type == "follow_up" else None
            response = self.generate_summary_with_citations(user_message, context, sources, history=history)
        else:  # mode == "extract" (default)
            print("🔍 Using EXTRACTION mode - returning exact document excerpts")
            response = self.extract_answer_from_context(user_message, context, sources)
        
        # 8. UPDATE HISTORY (sliding window - keep last 5)
        self.conversation_history.append({
            'user': user_message,
            'assistant': response
        })
        if len(self.conversation_history) > 5:
            self.conversation_history = self.conversation_history[-5:]
        
        return response
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []


# Global chatbot instance
_chatbot_instance = None


def get_chatbot():
    """Get or create chatbot instance"""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = EnhancedRAGChatbot()
    return _chatbot_instance


def chat(message: str, mode: str = "extract") -> str:
    """
    Simple chat interface
    
    Args:
        message: User's question
        mode: "extract" (default) or "summarize"
    """
    chatbot = get_chatbot()
    return chatbot.chat(message, mode=mode)


def reset():
    """Reset conversation"""
    chatbot = get_chatbot()
    chatbot.reset_conversation()


if __name__ == "__main__":
    # Test the chatbot
    print("\n" + "="*80)
    print("🧪 TESTING ENHANCED RAG CHATBOT")
    print("="*80)
    
    chatbot = get_chatbot()
    
    test_questions = [
        "What are Rackspace's cloud adoption and migration services?",
        "How does Rackspace help with AWS deployment?",
        "What security services does Rackspace offer?"
    ]
    
    for question in test_questions:
        print(f"\n❓ {question}")
        response = chatbot.chat(question)
        print(f"🤖 {response}")
        print("-" * 80)
