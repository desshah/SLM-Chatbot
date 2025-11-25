"""
Prepare fine-tuning dataset from existing 4,107 Q&A pairs
Converts to proper instruction format for TinyLlama fine-tuning
"""
import json
from pathlib import Path
import logging
from config import DATA_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_finetuning_dataset():
    """Convert existing Q&A pairs to fine-tuning format"""
    
    # Load existing Q&A pairs
    qa_file = DATA_DIR / "training_qa_pairs.json"
    
    if not qa_file.exists():
        logger.error(f"Q&A pairs file not found: {qa_file}")
        return
    
    logger.info(f"Loading Q&A pairs from {qa_file}")
    with open(qa_file, 'r', encoding='utf-8') as f:
        qa_pairs = json.load(f)
    
    logger.info(f"Loaded {len(qa_pairs)} Q&A pairs")
    
    # Convert to training format
    training_data = []
    skipped = 0
    
    for idx, pair in enumerate(qa_pairs):
        # Extract question and answer (support both formats)
        question = pair.get('question', pair.get('instruction', ''))
        answer = pair.get('answer', pair.get('output', ''))
        
        # Skip if missing question or answer
        if not question or not answer:
            skipped += 1
            continue
        
        # Skip if answer is too short (likely low quality)
        if len(answer) < 50:
            skipped += 1
            continue
        
        # Format for TinyLlama Chat
        formatted_text = f"""<|system|>
You are a helpful Rackspace Technology support assistant. Provide accurate, detailed information about Rackspace services, products, and solutions.
<|user|>
{question}
<|assistant|>
{answer}"""
        
        training_data.append({
            'text': formatted_text
        })
        
        if (idx + 1) % 500 == 0:
            logger.info(f"Processed {idx + 1}/{len(qa_pairs)} Q&A pairs...")
    
    logger.info(f"Converted {len(training_data)} training examples")
    logger.info(f"Skipped {skipped} low-quality pairs")
    
    # Save training dataset
    output_file = DATA_DIR / "training_data.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in training_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    logger.info(f"Saved training data to {output_file}")
    
    # Print statistics
    print(f"\n{'='*80}")
    print(f"✅ FINE-TUNING DATASET PREPARED")
    print(f"{'='*80}")
    print(f"📊 Statistics:")
    print(f"   - Original Q&A pairs: {len(qa_pairs)}")
    print(f"   - Training examples: {len(training_data)}")
    print(f"   - Skipped (low quality): {skipped}")
    print(f"   - Output file: {output_file}")
    print(f"   - File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"{'='*80}\n")
    
    # Show samples
    print("📝 Sample training examples:")
    print("-" * 80)
    for i in range(min(3, len(training_data))):
        sample = training_data[i]['text']
        # Show first 300 chars
        print(f"\nExample {i+1}:")
        print(sample[:400] + "..." if len(sample) > 400 else sample)
        print()
    
    return output_file


if __name__ == "__main__":
    prepare_finetuning_dataset()
