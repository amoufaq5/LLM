"""
QLoRA Fine-tuning script for Lumen Medical LLM
Trains BioMistral-7B or Llama 3.1 8B on medical data using QLoRA (Quantized Low-Rank Adaptation)

This script provides:
- 4-bit quantization for memory efficiency
- LoRA adapters for parameter-efficient training
- WandB integration for monitoring
- Checkpointing and resume capability
- Evaluation during training
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import torch
import transformers
from datasets import load_dataset
from peft import (
    LoraConfig,
    PeftModel,
    get_peft_model,
    prepare_model_for_kbit_training,
)
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    HfArgumentParser,
    TrainingArguments,
    Trainer,
)

logger = logging.getLogger(__name__)


@dataclass
class ModelArguments:
    """Arguments for model configuration"""

    model_name_or_path: str = field(
        default="BioMistral/BioMistral-7B",
        metadata={"help": "Path to pretrained model or model identifier from huggingface.co/models"},
    )
    use_auth_token: bool = field(
        default=False,
        metadata={"help": "Whether to use HuggingFace auth token"},
    )


@dataclass
class DataArguments:
    """Arguments for data configuration"""

    dataset_path: str = field(
        default="data/datasets",
        metadata={"help": "Path to training datasets"},
    )
    max_seq_length: int = field(
        default=2048,
        metadata={"help": "Maximum sequence length"},
    )


@dataclass
class QLoraArguments:
    """Arguments for QLoRA configuration"""

    lora_r: int = field(
        default=64,
        metadata={"help": "LoRA rank"},
    )
    lora_alpha: int = field(
        default=16,
        metadata={"help": "LoRA alpha"},
    )
    lora_dropout: float = field(
        default=0.05,
        metadata={"help": "LoRA dropout"},
    )
    load_in_4bit: bool = field(
        default=True,
        metadata={"help": "Load model in 4-bit quantization"},
    )
    bnb_4bit_compute_dtype: str = field(
        default="bfloat16",
        metadata={"help": "Compute dtype for 4-bit base models"},
    )
    bnb_4bit_quant_type: str = field(
        default="nf4",
        metadata={"help": "Quantization type (nf4 or fp4)"},
    )
    use_nested_quant: bool = field(
        default=True,
        metadata={"help": "Use nested quantization"},
    )


def create_prompt(example):
    """
    Format example into prompt template

    Uses Alpaca-style prompt format
    """
    if example.get("input"):
        return f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{example['instruction']}

### Input:
{example['input']}

### Response:
{example['output']}"""
    else:
        return f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{example['instruction']}

### Response:
{example['output']}"""


def load_model_and_tokenizer(
    model_args: ModelArguments,
    qlora_args: QLoraArguments,
):
    """
    Load model with 4-bit quantization and tokenizer
    """
    logger.info(f"Loading model: {model_args.model_name_or_path}")

    # Quantization config
    compute_dtype = getattr(torch, qlora_args.bnb_4bit_compute_dtype)

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=qlora_args.load_in_4bit,
        bnb_4bit_quant_type=qlora_args.bnb_4bit_quant_type,
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=qlora_args.use_nested_quant,
    )

    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        model_args.model_name_or_path,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        use_auth_token=model_args.use_auth_token,
    )

    # Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.model_name_or_path,
        trust_remote_code=True,
        use_auth_token=model_args.use_auth_token,
    )

    # Set padding token if not set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        model.config.pad_token_id = model.config.eos_token_id

    return model, tokenizer


def create_peft_config(qlora_args: QLoraArguments):
    """
    Create PEFT (LoRA) configuration
    """
    config = LoraConfig(
        r=qlora_args.lora_r,
        lora_alpha=qlora_args.lora_alpha,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_dropout=qlora_args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )

    return config


def tokenize_and_format_dataset(
    dataset,
    tokenizer,
    max_seq_length: int,
):
    """
    Tokenize and format dataset for training
    """

    def tokenize_function(examples):
        # Create prompts
        prompts = [create_prompt(ex) for ex in examples]

        # Tokenize
        tokenized = tokenizer(
            prompts,
            truncation=True,
            max_length=max_seq_length,
            padding="max_length",
            return_tensors=None,
        )

        # Create labels (same as input_ids for causal LM)
        tokenized["labels"] = tokenized["input_ids"].copy()

        return tokenized

    # Process dataset in batches
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names,
        desc="Tokenizing dataset",
    )

    return tokenized_dataset


def train():
    """Main training function"""

    # Parse arguments
    parser = HfArgumentParser((ModelArguments, DataArguments, QLoraArguments, TrainingArguments))
    model_args, data_args, qlora_args, training_args = parser.parse_args_into_dataclasses()

    # Setup logging
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )

    logger.info("="*60)
    logger.info("LUMEN MEDICAL LLM - QLORA FINE-TUNING")
    logger.info("="*60)
    logger.info(f"Model: {model_args.model_name_or_path}")
    logger.info(f"Dataset: {data_args.dataset_path}")
    logger.info(f"Output: {training_args.output_dir}")
    logger.info("="*60)

    # Load model and tokenizer
    model, tokenizer = load_model_and_tokenizer(model_args, qlora_args)

    # Create PEFT config and wrap model
    peft_config = create_peft_config(qlora_args)
    model = get_peft_model(model, peft_config)

    # Print trainable parameters
    model.print_trainable_parameters()

    # Load datasets
    logger.info("Loading datasets...")

    dataset_path = Path(data_args.dataset_path)

    train_dataset = load_dataset(
        "json",
        data_files=str(dataset_path / "train.jsonl"),
        split="train",
    )

    eval_dataset = load_dataset(
        "json",
        data_files=str(dataset_path / "validation.jsonl"),
        split="train",
    )

    logger.info(f"Training examples: {len(train_dataset)}")
    logger.info(f"Validation examples: {len(eval_dataset)}")

    # Tokenize datasets
    logger.info("Tokenizing datasets...")

    train_dataset = tokenize_and_format_dataset(
        train_dataset,
        tokenizer,
        data_args.max_seq_length,
    )

    eval_dataset = tokenize_and_format_dataset(
        eval_dataset,
        tokenizer,
        data_args.max_seq_length,
    )

    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
    )

    # Train
    logger.info("Starting training...")
    trainer.train(resume_from_checkpoint=training_args.resume_from_checkpoint)

    # Save final model
    logger.info(f"Saving final model to {training_args.output_dir}")
    trainer.save_model()
    tokenizer.save_pretrained(training_args.output_dir)

    # Save training stats
    stats = {
        "train_loss": trainer.state.log_history[-1].get("train_loss") if trainer.state.log_history else None,
        "eval_loss": trainer.state.log_history[-1].get("eval_loss") if trainer.state.log_history else None,
        "total_steps": trainer.state.global_step,
    }

    with open(Path(training_args.output_dir) / "training_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    logger.info("="*60)
    logger.info("TRAINING COMPLETE")
    logger.info(f"Model saved to: {training_args.output_dir}")
    logger.info("="*60)


if __name__ == "__main__":
    train()
