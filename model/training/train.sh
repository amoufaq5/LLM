#!/bin/bash
# Training script for Lumen Medical LLM
# Usage: bash model/training/train.sh

set -e

echo "========================================"
echo "LUMEN MEDICAL LLM - Training Script"
echo "========================================"

# Configuration
MODEL_NAME="BioMistral/BioMistral-7B"  # or "meta-llama/Llama-3.1-8B"
DATASET_PATH="data/datasets"
OUTPUT_DIR="model/checkpoints/lumen-medical-v1"
WANDB_PROJECT="lumen-medical-llm"

# Training hyperparameters
BATCH_SIZE=4
GRADIENT_ACCUM_STEPS=4  # Effective batch size = 4 * 4 = 16
LEARNING_RATE=2e-4
NUM_EPOCHS=3
MAX_SEQ_LENGTH=2048

# LoRA configuration
LORA_R=64
LORA_ALPHA=16
LORA_DROPOUT=0.05

# Check if dataset exists
if [ ! -f "$DATASET_PATH/train.jsonl" ]; then
    echo "❌ Training dataset not found at $DATASET_PATH/train.jsonl"
    echo "Please run data processing first:"
    echo "  python data/processing/data_processor.py"
    exit 1
fi

echo "✓ Dataset found"
echo "✓ Model: $MODEL_NAME"
echo "✓ Output: $OUTPUT_DIR"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run training
python model/training/train_qlora.py \
    --model_name_or_path "$MODEL_NAME" \
    --dataset_path "$DATASET_PATH" \
    --output_dir "$OUTPUT_DIR" \
    --num_train_epochs $NUM_EPOCHS \
    --per_device_train_batch_size $BATCH_SIZE \
    --per_device_eval_batch_size $BATCH_SIZE \
    --gradient_accumulation_steps $GRADIENT_ACCUM_STEPS \
    --evaluation_strategy "steps" \
    --eval_steps 500 \
    --save_strategy "steps" \
    --save_steps 1000 \
    --save_total_limit 3 \
    --learning_rate $LEARNING_RATE \
    --weight_decay 0.01 \
    --warmup_ratio 0.03 \
    --lr_scheduler_type "cosine" \
    --logging_steps 10 \
    --max_seq_length $MAX_SEQ_LENGTH \
    --lora_r $LORA_R \
    --lora_alpha $LORA_ALPHA \
    --lora_dropout $LORA_DROPOUT \
    --bf16 \
    --tf32 True \
    --load_in_4bit True \
    --bnb_4bit_compute_dtype "bfloat16" \
    --bnb_4bit_quant_type "nf4" \
    --use_nested_quant True \
    --gradient_checkpointing True \
    --report_to "wandb" \
    --run_name "lumen-medical-v1"

echo ""
echo "========================================"
echo "✅ Training Complete!"
echo "Model saved to: $OUTPUT_DIR"
echo "========================================"
