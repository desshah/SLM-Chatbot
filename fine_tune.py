"""
Fine-tune a small language model on Rackspace knowledge
Optimized for Apple M3 Mac with 16GB RAM using LoRA/QLoRA
"""
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset
import logging
from pathlib import Path
from config import (
    BASE_MODEL_NAME,
    FINE_TUNED_MODEL_PATH,
    DATA_DIR,
    LORA_R,
    LORA_ALPHA,
    LORA_DROPOUT,
    LEARNING_RATE,
    BATCH_SIZE,
    GRADIENT_ACCUMULATION_STEPS,
    NUM_EPOCHS,
    MAX_LENGTH,
    WARMUP_STEPS
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelFineTuner:
    """Fine-tune small LLM with LoRA for efficient training on M3 Mac"""
    
    def __init__(self, model_name: str = BASE_MODEL_NAME):
        self.model_name = model_name
        self.device = self._setup_device()
        logger.info(f"Using device: {self.device}")
        
    def _setup_device(self):
        """Set up device for M3 Mac"""
        if torch.backends.mps.is_available():
            logger.info("MPS (Metal Performance Shaders) available - using Apple Silicon GPU")
            return torch.device("mps")
        elif torch.cuda.is_available():
            logger.info("CUDA available - using GPU")
            return torch.device("cuda")
        else:
            logger.info("Using CPU")
            return torch.device("cpu")
    
    def load_model_and_tokenizer(self):
        """Load base model and tokenizer with quantization for efficiency"""
        logger.info(f"Loading model: {self.model_name}")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        
        # Set pad token if not present
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        
        # Load model with appropriate settings for M3 Mac
        # For MPS, we use float16 without quantization as quantization may not be fully supported
        if self.device.type == "mps":
            logger.info("Loading model in float16 for MPS")
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map=None,  # Manual device placement for MPS
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            model = model.to(self.device)
        else:
            # For CUDA, can use 8-bit quantization
            logger.info("Loading model with 8-bit quantization")
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0
            )
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=quantization_config,
                device_map="auto",
                trust_remote_code=True
            )
        
        logger.info(f"Model loaded successfully. Parameters: {model.num_parameters():,}")
        
        return model, tokenizer
    
    def setup_lora(self, model):
        """Configure LoRA for parameter-efficient fine-tuning"""
        logger.info("Setting up LoRA configuration")
        
        # Prepare model for training
        if self.device.type != "mps":
            model = prepare_model_for_kbit_training(model)
        
        # LoRA configuration
        lora_config = LoraConfig(
            r=LORA_R,
            lora_alpha=LORA_ALPHA,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],  # Attention modules
            lora_dropout=LORA_DROPOUT,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        # Apply LoRA
        model = get_peft_model(model, lora_config)
        
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in model.parameters())
        
        logger.info(f"Trainable parameters: {trainable_params:,} ({100 * trainable_params / total_params:.2f}%)")
        
        return model
    
    def prepare_dataset(self, tokenizer, dataset_path: Path):
        """Prepare and tokenize dataset"""
        logger.info(f"Loading dataset from {dataset_path}")
        
        # Load dataset
        dataset = load_dataset('json', data_files=str(dataset_path), split='train')
        logger.info(f"Loaded {len(dataset)} examples")
        
        # Tokenize function
        def tokenize_function(examples):
            outputs = tokenizer(
                examples['text'],
                truncation=True,
                max_length=MAX_LENGTH,
                padding='max_length',
                return_tensors=None
            )
            outputs['labels'] = outputs['input_ids'].copy()
            return outputs
        
        # Tokenize dataset
        logger.info("Tokenizing dataset...")
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names,
            desc="Tokenizing"
        )
        
        # Split into train and validation
        split_dataset = tokenized_dataset.train_test_split(test_size=0.1, seed=42)
        
        logger.info(f"Training examples: {len(split_dataset['train'])}")
        logger.info(f"Validation examples: {len(split_dataset['test'])}")
        
        return split_dataset
    
    def train(self, dataset_path: Path = DATA_DIR / "training_data.jsonl"):
        """Fine-tune the model"""
        logger.info("Starting fine-tuning process...")
        
        # Load model and tokenizer
        model, tokenizer = self.load_model_and_tokenizer()
        
        # Setup LoRA
        model = self.setup_lora(model)
        
        # Prepare dataset
        dataset = self.prepare_dataset(tokenizer, dataset_path)
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(FINE_TUNED_MODEL_PATH),
            num_train_epochs=NUM_EPOCHS,
            per_device_train_batch_size=BATCH_SIZE,
            per_device_eval_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
            learning_rate=LEARNING_RATE,
            warmup_steps=WARMUP_STEPS,
            logging_steps=10,
            eval_strategy="steps",
            eval_steps=50,
            save_steps=100,
            save_total_limit=2,
            load_best_model_at_end=True,
            report_to="none",  # Disable wandb, tensorboard
            fp16=False,  # Disable for MPS
            bf16=False,  # Not supported on MPS
            optim="adamw_torch",
            gradient_checkpointing=True,
            max_grad_norm=0.3,
            lr_scheduler_type="cosine",
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset['train'],
            eval_dataset=dataset['test'],
            data_collator=data_collator,
        )
        
        # Train
        logger.info("Starting training...")
        trainer.train()
        
        # Save final model
        logger.info(f"Saving fine-tuned model to {FINE_TUNED_MODEL_PATH}")
        trainer.save_model()
        tokenizer.save_pretrained(FINE_TUNED_MODEL_PATH)
        
        print(f"\n{'='*80}")
        print(f"Fine-tuning complete!")
        print(f"Model saved to: {FINE_TUNED_MODEL_PATH}")
        print(f"{'='*80}\n")
        
        return model, tokenizer


def main():
    """Main fine-tuning workflow"""
    dataset_path = DATA_DIR / "training_data.jsonl"
    
    if not dataset_path.exists():
        logger.error(f"Training data not found: {dataset_path}")
        logger.error("Please run prepare_dataset.py first!")
        return
    
    # Initialize fine-tuner
    fine_tuner = ModelFineTuner()
    
    # Train model
    model, tokenizer = fine_tuner.train(dataset_path)
    
    # Test the model
    print("\nTesting fine-tuned model...")
    test_prompt = "<|system|>\nYou are a helpful assistant that answers questions about Rackspace Technology.\n<|user|>\nWhat is Rackspace?\n<|assistant|>\n"
    
    inputs = tokenizer(test_prompt, return_tensors="pt").to(fine_tuner.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"\nTest Response:\n{response}\n")


if __name__ == "__main__":
    main()
