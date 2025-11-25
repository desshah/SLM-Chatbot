"""
CPU-Optimized Fine-tuning Script for Rackspace Chatbot
Stable training on Apple M3 Mac (avoids MPS issues)
Creates YOUR OWN trained model (NO AGENTS!)
"""
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from pathlib import Path
import logging
from config import BASE_MODEL_NAME, FINE_TUNED_MODEL_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CPUFineTuner:
    """CPU-optimized fine-tuning for M3 Mac"""
    
    def __init__(self):
        self.device = "cpu"  # Force CPU for stability
        self.model_name = BASE_MODEL_NAME
        self.output_dir = FINE_TUNED_MODEL_PATH
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("="*80)
        logger.info("CPU-OPTIMIZED FINE-TUNING")
        logger.info("Creating YOUR OWN model (NO AGENTS!)")
        logger.info("="*80)
        logger.info(f"Device: {self.device}")
        logger.info(f"Model: {self.model_name}")
        logger.info(f"Output: {self.output_dir}")
    
    def load_model_and_tokenizer(self):
        """Load model in CPU-optimized mode"""
        logger.info("Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        
        logger.info("Loading model (this takes 2-3 minutes on CPU)...")
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float32,  # CPU requires float32
            device_map=None,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        self.model = self.model.to(self.device)
        
        total_params = sum(p.numel() for p in self.model.parameters())
        logger.info(f"✓ Model loaded. Total parameters: {total_params:,}")
    
    def setup_lora(self):
        """Setup LoRA for efficient training"""
        logger.info("Setting up LoRA configuration...")
        
        lora_config = LoraConfig(
            r=8,  # Reduced rank for faster CPU training
            lora_alpha=16,
            target_modules=["q_proj", "v_proj"],  # Only essential modules
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        self.model = get_peft_model(self.model, lora_config)
        
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.model.parameters())
        
        logger.info(f"✓ LoRA configured")
        logger.info(f"  Trainable parameters: {trainable_params:,} ({100 * trainable_params / total_params:.2f}%)")
    
    def load_and_prepare_dataset(self, dataset_path: Path):
        """Load and tokenize dataset"""
        logger.info(f"Loading dataset from {dataset_path}...")
        
        dataset = load_dataset('json', data_files=str(dataset_path), split='train')
        logger.info(f"✓ Loaded {len(dataset)} examples")
        
        def tokenize_function(examples):
            """Tokenize examples"""
            return self.tokenizer(
                examples['text'],
                truncation=True,
                max_length=512,  # Reduced for faster training
                padding='max_length'
            )
        
        logger.info("Tokenizing dataset (this takes 1-2 minutes)...")
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names,
            desc="Tokenizing"
        )
        
        # Split into train/validation
        split_dataset = tokenized_dataset.train_test_split(test_size=0.1, seed=42)
        
        logger.info(f"✓ Training examples: {len(split_dataset['train'])}")
        logger.info(f"✓ Validation examples: {len(split_dataset['test'])}")
        
        return split_dataset
    
    def train(self, dataset_path: Path, num_epochs: int = 2):
        """Train the model"""
        logger.info("\n" + "="*80)
        logger.info("STARTING TRAINING")
        logger.info("="*80)
        
        # Load model
        self.load_model_and_tokenizer()
        
        # Setup LoRA
        self.setup_lora()
        
        # Load dataset
        dataset = self.load_and_prepare_dataset(dataset_path)
        
        # Training arguments - optimized for CPU
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=num_epochs,
            per_device_train_batch_size=2,  # Small batch for CPU
            per_device_eval_batch_size=2,
            gradient_accumulation_steps=8,  # Simulate larger batch
            learning_rate=2e-4,
            warmup_steps=100,
            logging_steps=50,
            eval_steps=200,
            save_steps=500,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            fp16=False,  # No FP16 on CPU
            optim="adamw_torch",  # CPU-compatible optimizer
            report_to="none",
            save_total_limit=2,
            push_to_hub=False,
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset['train'],
            eval_dataset=dataset['test'],
            data_collator=data_collator,
        )
        
        # Train
        logger.info("\n🚀 Starting training...")
        logger.info(f"⏰ Estimated time: {num_epochs * 90}-{num_epochs * 120} minutes on CPU")
        logger.info("💡 Tip: This will be slow but stable. Perfect for creating YOUR OWN model!\n")
        
        trainer.train()
        
        # Save final model
        logger.info("\n💾 Saving fine-tuned model...")
        trainer.save_model(str(self.output_dir))
        self.tokenizer.save_pretrained(str(self.output_dir))
        
        logger.info("\n" + "="*80)
        logger.info("✅ TRAINING COMPLETE!")
        logger.info("="*80)
        logger.info(f"Model saved to: {self.output_dir}")
        logger.info("\nYour own fine-tuned model is ready! 🎉")
        logger.info("NO AGENTS - This is YOUR trained model on YOUR data!")
        
        return self.model, self.tokenizer


def main():
    """Main training workflow"""
    import sys
    from pathlib import Path
    
    print("\n" + "="*80)
    print("RACKSPACE CHATBOT - CPU FINE-TUNING")
    print("Creating YOUR OWN Language Model (NO AGENTS!)")
    print("="*80)
    print("\n⚠️  IMPORTANT:")
    print("   - This uses CPU for stable training")
    print("   - Takes 3-4 hours (slower but works!)")
    print("   - Creates YOUR fine-tuned model")
    print("   - Perfect for M3 Mac compatibility")
    print("\n")
    
    # Ask for confirmation
    response = input("Ready to start training? This will take 3-4 hours. (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Training cancelled.")
        sys.exit(0)
    
    # Training data path
    dataset_path = Path("data/training_data.jsonl")
    
    if not dataset_path.exists():
        print(f"\n❌ Error: Training data not found at {dataset_path}")
        print("Run ./build_pipeline.sh first to prepare data")
        sys.exit(1)
    
    # Create trainer
    fine_tuner = CPUFineTuner()
    
    # Train
    try:
        model, tokenizer = fine_tuner.train(dataset_path, num_epochs=2)
        
        print("\n" + "="*80)
        print("🎉 SUCCESS! Your own model is trained!")
        print("="*80)
        print("\nNext steps:")
        print("  1. Restart Streamlit: ./start_streamlit.sh")
        print("  2. Chat with YOUR fine-tuned model!")
        print("\n" + "="*80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted!")
        print("You can restart anytime with: python fine_tune_cpu.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
