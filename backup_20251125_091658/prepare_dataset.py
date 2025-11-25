"""
Prepare fine-tuning dataset from Rackspace knowledge
Generates Q&A pairs in instruction-following format
"""
import json
from typing import List, Dict
from pathlib import Path
import logging
from config import DATA_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetPreparer:
    """Prepares training dataset for fine-tuning"""
    
    def __init__(self, knowledge_file: Path):
        self.knowledge_file = knowledge_file
        self.training_data = []
    
    def create_qa_pairs(self, documents: List[Dict]) -> List[Dict]:
        """Generate Q&A pairs from documents"""
        qa_pairs = []
        
        # Template-based Q&A generation
        qa_templates = [
            {
                'question_templates': [
                    'What is {topic}?',
                    'Tell me about {topic}',
                    'Explain {topic}',
                    'Can you describe {topic}?',
                    'I want to know about {topic}'
                ],
                'extract_topic': lambda doc: doc['title'].replace('About ', '').replace('Rackspace ', '')
            },
            {
                'question_templates': [
                    'What services does Rackspace offer?',
                    'What are Rackspace services?',
                    'Tell me about Rackspace services',
                    'What solutions does Rackspace provide?'
                ],
                'filter': lambda doc: 'service' in doc['title'].lower() or 'service' in doc['content'].lower()
            },
            {
                'question_templates': [
                    'What is Rackspace mission?',
                    'What is the mission of Rackspace?',
                    'Tell me about Rackspace mission',
                    'What does Rackspace aim to do?'
                ],
                'filter': lambda doc: 'mission' in doc['title'].lower() or 'mission' in doc['content'].lower()
            },
            {
                'question_templates': [
                    'What is Fanatical Experience?',
                    'Tell me about Fanatical Experience',
                    'Explain Rackspace Fanatical Experience',
                    'What does Fanatical Experience mean?'
                ],
                'filter': lambda doc: 'fanatical' in doc['title'].lower() or 'fanatical' in doc['content'].lower()
            }
        ]
        
        for doc in documents:
            content = doc['content']
            title = doc['title']
            
            # Create Q&A pairs using templates
            for template_group in qa_templates:
                questions = template_group['question_templates']
                
                # Apply filter if exists
                if 'filter' in template_group:
                    if not template_group['filter'](doc):
                        continue
                
                # Extract topic if needed
                if 'extract_topic' in template_group:
                    topic = template_group['extract_topic'](doc)
                    questions = [q.format(topic=topic) for q in questions]
                
                # Create Q&A pairs for this document
                for question in questions:
                    # Create answer from content (truncate if too long)
                    answer = content[:500] if len(content) > 500 else content
                    
                    qa_pairs.append({
                        'instruction': question,
                        'input': '',
                        'output': answer,
                        'source': doc.get('source', 'unknown'),
                        'title': title
                    })
        
        return qa_pairs
    
    def create_manual_qa_pairs(self) -> List[Dict]:
        """Create manually crafted Q&A pairs for better quality"""
        manual_pairs = [
            {
                'instruction': 'What is Rackspace?',
                'input': '',
                'output': 'Rackspace Technology is a leading provider of end-to-end multicloud solutions. Founded in 1998 and headquartered in San Antonio, Texas, Rackspace delivers expert services and innovative technologies across major public clouds including AWS, Google Cloud, Microsoft Azure, and VMware. The company combines technical expertise with proprietary software and automation to help businesses navigate complex cloud environments.'
            },
            {
                'instruction': 'Tell me about Rackspace',
                'input': '',
                'output': 'Rackspace is a multicloud solutions company that helps businesses design, build, and operate their cloud environments. With over 6,000 employees worldwide, Rackspace serves thousands of customers across various industries. The company is known for its Fanatical Experience commitment to exceptional customer service and support.'
            },
            {
                'instruction': 'What is the mission of Rackspace?',
                'input': '',
                'output': "Rackspace's mission is to design, build, and operate our customers' multi-cloud environments. The company is committed to providing Fanatical Experience, which means delivering exceptional service and support to every customer. Rackspace aims to be the world's leading multi-cloud solutions provider, helping companies leverage the power of cloud technology to accelerate their digital transformation journeys."
            },
            {
                'instruction': 'What services does Rackspace offer?',
                'input': '',
                'output': 'Rackspace offers comprehensive cloud services including: Managed Cloud Services for AWS, Azure, Google Cloud, and private clouds; Professional Services for cloud migrations and architecture design; Elastic Engineering for on-demand technical expertise; Cloud-Native Services including containerization and Kubernetes; Data Services covering databases, analytics, and AI/ML; Security Services including compliance and threat detection; and Colocation and private cloud infrastructure solutions.'
            },
            {
                'instruction': 'What is Fanatical Experience?',
                'input': '',
                'output': "Fanatical Experience is Rackspace's commitment to delivering exceptional customer service and support. It encompasses 24x7x365 support from cloud experts, proactive monitoring and management, rapid response times, and a customer-first approach to everything Rackspace does. This commitment has been a cornerstone of Rackspace's brand since its founding."
            },
            {
                'instruction': 'When was Rackspace founded?',
                'input': '',
                'output': 'Rackspace was founded in 1998 as a web hosting company. The company has since evolved into a leading multi-cloud solutions provider. In 2006, Rackspace introduced cloud computing services, and in 2010, it co-founded OpenStack, an open-source cloud computing platform.'
            },
            {
                'instruction': 'Where is Rackspace located?',
                'input': '',
                'output': 'Rackspace Technology is headquartered in San Antonio, Texas. However, the company has a global presence with over 6,000 employees worldwide serving customers across various countries and regions.'
            },
            {
                'instruction': 'What cloud platforms does Rackspace support?',
                'input': '',
                'output': 'Rackspace supports all major cloud platforms including Amazon Web Services (AWS), Microsoft Azure, Google Cloud Platform (GCP), and VMware. The company has strategic partnerships with these providers - AWS Premier Consulting Partner, Azure Gold Partner, Google Cloud Premier Partner, and VMware Premier Partner. This enables true multi-cloud flexibility for customers.'
            },
            {
                'instruction': 'What is Rackspace history?',
                'input': '',
                'output': 'Rackspace was founded in 1998 as a web hosting company. In 2006, it introduced cloud computing services and became a pioneer in the industry. In 2010, Rackspace co-founded OpenStack, an open-source cloud computing platform. The company went private in 2016 after being acquired by Apollo Global Management, and went public again in 2020 as Rackspace Technology, continuing to evolve as a leading multi-cloud solutions provider.'
            },
            {
                'instruction': 'Who are Rackspace partners?',
                'input': '',
                'output': 'Rackspace has strategic partnerships with major cloud providers: Amazon Web Services (AWS) as Premier Consulting Partner, Microsoft Azure as Gold Partner, Google Cloud Platform as Premier Partner, and VMware as Premier Partner. These partnerships enable Rackspace to deliver certified expertise and managed services across all major cloud platforms.'
            }
        ]
        
        return manual_pairs
    
    def prepare_dataset(self) -> List[Dict]:
        """Prepare complete training dataset"""
        logger.info(f"Loading knowledge from {self.knowledge_file}")
        
        with open(self.knowledge_file, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        logger.info(f"Loaded {len(documents)} documents")
        
        # Create Q&A pairs from documents
        logger.info("Generating Q&A pairs from documents...")
        auto_qa_pairs = self.create_qa_pairs(documents)
        
        # Add manual Q&A pairs
        logger.info("Adding manual Q&A pairs...")
        manual_qa_pairs = self.create_manual_qa_pairs()
        
        # Combine all pairs
        all_qa_pairs = manual_qa_pairs + auto_qa_pairs
        
        logger.info(f"Total Q&A pairs created: {len(all_qa_pairs)}")
        logger.info(f"  - Manual pairs: {len(manual_qa_pairs)}")
        logger.info(f"  - Auto-generated pairs: {len(auto_qa_pairs)}")
        
        return all_qa_pairs
    
    def format_for_training(self, qa_pairs: List[Dict]) -> List[Dict]:
        """Format Q&A pairs for model training"""
        formatted_data = []
        
        for pair in qa_pairs:
            # Format in instruction-following format
            formatted_data.append({
                'text': f"<|system|>\nYou are a helpful assistant that answers questions about Rackspace Technology.\n<|user|>\n{pair['instruction']}\n<|assistant|>\n{pair['output']}"
            })
        
        return formatted_data
    
    def save_dataset(self, output_dir: Path = DATA_DIR):
        """Save prepared dataset"""
        # Prepare dataset
        qa_pairs = self.prepare_dataset()
        
        # Save raw Q&A pairs
        qa_path = output_dir / "training_qa_pairs.json"
        with open(qa_path, 'w', encoding='utf-8') as f:
            json.dump(qa_pairs, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved Q&A pairs to {qa_path}")
        
        # Format for training
        formatted_data = self.format_for_training(qa_pairs)
        
        # Save formatted training data
        training_path = output_dir / "training_data.jsonl"
        with open(training_path, 'w', encoding='utf-8') as f:
            for item in formatted_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        logger.info(f"Saved training data to {training_path}")
        
        # Print statistics
        print(f"\n{'='*80}")
        print(f"Dataset preparation complete!")
        print(f"Total training examples: {len(formatted_data)}")
        print(f"Q&A pairs saved to: {qa_path}")
        print(f"Training data saved to: {training_path}")
        print(f"{'='*80}\n")
        
        return training_path


def main():
    """Main workflow"""
    knowledge_file = DATA_DIR / "rackspace_knowledge.json"
    
    if not knowledge_file.exists():
        logger.error(f"Knowledge file not found: {knowledge_file}")
        logger.error("Please run data_collection.py first!")
        return
    
    preparer = DatasetPreparer(knowledge_file)
    training_path = preparer.save_dataset()
    
    # Show sample
    print("\nSample training examples:")
    print("-" * 80)
    
    with open(training_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 3:  # Show first 3 examples
                break
            data = json.loads(line)
            print(f"\nExample {i+1}:")
            print(data['text'][:300] + "...")
            print()


if __name__ == "__main__":
    main()
