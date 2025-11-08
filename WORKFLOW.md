

# Lumen Medical LLM - Complete Workflow Guide

**End-to-end guide from data collection to trained model**

---

## Overview

This workflow takes you through the complete process of building Lumen Medical LLM:

1. **Data Collection** - Scrape comprehensive medical data
2. **Data Processing** - Clean and format for training
3. **Model Training** - Fine-tune with QLoRA
4. **Evaluation** - Test model performance
5. **Deployment** - (Phase 2)

---

## Prerequisites

### System Requirements
- **GPU:** NVIDIA GPU with 24GB+ VRAM (A100, A40, RTX 4090, etc.)
- **RAM:** 32GB+ recommended
- **Storage:** 100GB+ free space
- **OS:** Linux (Ubuntu 20.04+) or WSL2

### Software Requirements
```bash
# Python 3.10+
python --version

# CUDA 11.8+ or 12.1+
nvcc --version

# Git
git --version
```

### API Keys (Optional but Recommended)
- **PubMed:** https://www.ncbi.nlm.nih.gov/account/ (free)
- **WandB:** https://wandb.ai/ (for training monitoring)

---

## Step 1: Environment Setup

### 1.1 Clone Repository (Already Done)
```bash
cd /home/user/LLM
```

### 1.2 Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### 1.3 Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys
nano .env

# Add at minimum:
# PUBMED_API_KEY=your_key_here
# PUBMED_EMAIL=your_email@example.com
# WANDB_API_KEY=your_wandb_key (for training monitoring)
```

---

## Step 2: Data Collection

### 2.1 Run All Scrapers (Recommended)
```bash
# Interactive scraper selection
python data/scrapers/run_all_scrapers.py

# Select option 7 (ALL) to collect comprehensive data
```

**Expected Runtime:** 4-8 hours
**Expected Data:** 100K-500K examples, 2-10 GB

### 2.2 OR Run Individual Scrapers
```bash
# Medical literature
python data/scrapers/medical/pubmed_scraper.py        # ~2-4 hours

# Drug information
python data/scrapers/medical/openfda_client.py        # ~1-2 hours
python data/scrapers/medical/dailymed_scraper.py      # ~2-4 hours
python data/scrapers/medical/rxnorm_client.py         # ~10-20 min

# Clinical trials
python data/scrapers/medical/clinicaltrials_scraper.py  # ~1-2 hours

# Regulatory guidance
python data/scrapers/pharma/fda_guidance_scraper.py   # ~30-60 min
```

### 2.3 DrugBank (Manual Download Required)
```bash
# 1. Go to: https://go.drugbank.com/releases/latest
# 2. Create free account
# 3. Download "All full database" XML file
# 4. Place at: data/raw/drugbank/full_database.xml

# Then run parser
python data/scrapers/medical/drugbank_parser.py
```

### 2.4 Verify Data Collection
```bash
# Check what was collected
ls -lh data/raw/*/

# Expected directories with data:
# - data/raw/pubmed/
# - data/raw/drugbank/
# - data/raw/openfda/
# - data/raw/dailymed/
# - data/raw/rxnorm/
# - data/raw/clinicaltrials/
# - data/raw/fda_guidance/
```

---

## Step 3: Data Processing

### 3.1 Process All Data
```bash
# Run data processor
python data/processing/data_processor.py
```

**What it does:**
- Loads all scraped data
- Cleans and normalizes text
- Converts to instruction-tuning format
- Deduplicates examples
- Creates train/val/test splits (80/10/10)

**Output:**
```
data/datasets/
├── train.json          # Training set
├── train.jsonl         # Training set (streaming format)
├── validation.json     # Validation set
├── validation.jsonl    # Validation set (streaming format)
├── test.json           # Test set
├── test.jsonl          # Test set (streaming format)
└── statistics.json     # Dataset statistics
```

### 3.2 Verify Datasets
```bash
# Check dataset sizes
wc -l data/datasets/*.jsonl

# View statistics
cat data/datasets/statistics.json | python -m json.tool

# Sample training example
head -n 1 data/datasets/train.jsonl | python -m json.tool
```

**Expected:** 50K-200K+ training examples

---

## Step 4: Model Training

### 4.1 Prepare for Training

**Check GPU:**
```bash
nvidia-smi
```

Should show available GPU with 24GB+ VRAM.

**Login to WandB (Optional but Recommended):**
```bash
wandb login
# Paste your API key from https://wandb.ai/authorize
```

### 4.2 Run Training

**Option A: Using Training Script (Recommended)**
```bash
# Make script executable
chmod +x model/training/train.sh

# Run training
bash model/training/train.sh
```

**Option B: Direct Python Command**
```bash
python model/training/train_qlora.py \
    --model_name_or_path "BioMistral/BioMistral-7B" \
    --dataset_path "data/datasets" \
    --output_dir "model/checkpoints/lumen-medical-v1" \
    --num_train_epochs 3 \
    --per_device_train_batch_size 4 \
    --gradient_accumulation_steps 4 \
    --learning_rate 2e-4 \
    --bf16 \
    --report_to "wandb"
```

**Training Time:**
- **A100 40GB:** 8-12 hours (3 epochs)
- **A100 80GB:** 6-10 hours
- **RTX 4090:** 12-18 hours

**Memory Usage:**
- **QLoRA 4-bit:** ~20GB VRAM
- **Batch size 4:** Safe for 24GB GPUs

### 4.3 Monitor Training

**WandB Dashboard:**
- Go to: https://wandb.ai/
- View real-time metrics:
  - Training loss
  - Validation loss
  - Learning rate
  - GPU utilization

**Terminal Output:**
```
Step 100: loss=0.523
Step 200: loss=0.401
Step 300: loss=0.356
...
```

### 4.4 Training Output
```
model/checkpoints/lumen-medical-v1/
├── adapter_config.json        # LoRA configuration
├── adapter_model.bin          # Trained LoRA weights
├── tokenizer_config.json      # Tokenizer config
├── tokenizer.model            # Tokenizer
├── special_tokens_map.json    # Special tokens
├── training_args.bin          # Training arguments
└── training_stats.json        # Final statistics
```

---

## Step 5: Model Evaluation

### 5.1 Run Evaluation
```bash
python model/evaluation/evaluate.py
```

**What it does:**
- Loads fine-tuned model
- Evaluates on test set (100 examples by default)
- Generates responses
- Computes metrics
- Saves results

### 5.2 View Results
```bash
# View metrics
cat model/evaluation/evaluation_metrics.json | python -m json.tool

# Read sample outputs
cat model/evaluation/sample_outputs.txt

# Example output:
# Instruction: What is metformin used for?
# Generated Response: Metformin is used to treat type 2 diabetes...
# Expected Response: Metformin is an antidiabetic medication...
```

---

## Step 6: Test the Model

### 6.1 Interactive Testing
```python
# Create test_model.py
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

# Load model
base_model = AutoModelForCausalLM.from_pretrained(
    "BioMistral/BioMistral-7B",
    device_map="auto",
    torch_dtype=torch.bfloat16,
)

model = PeftModel.from_pretrained(base_model, "model/checkpoints/lumen-medical-v1")
tokenizer = AutoTokenizer.from_pretrained("model/checkpoints/lumen-medical-v1")

# Test query
prompt = """Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
What are the side effects of metformin?

### Response:
"""

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=512)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)

print(response.split("### Response:")[-1].strip())
```

```bash
python test_model.py
```

---

## Step 7: Deployment (Phase 2)

### 7.1 Export for Inference
```bash
# Merge LoRA adapters with base model (optional)
python model/export/merge_adapters.py \
    --base_model "BioMistral/BioMistral-7B" \
    --peft_model "model/checkpoints/lumen-medical-v1" \
    --output_dir "model/checkpoints/lumen-medical-merged"
```

### 7.2 Deploy with vLLM (Fast Inference)
```bash
# Install vLLM
pip install vllm

# Start inference server
python -m vllm.entrypoints.api_server \
    --model model/checkpoints/lumen-medical-merged \
    --tensor-parallel-size 1 \
    --dtype bfloat16
```

### 7.3 Deploy to RunPod (Cloud)
```bash
# Create RunPod template
# Deploy to serverless endpoint
# Configure autoscaling
```

---

## Complete Workflow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                   LUMEN MEDICAL LLM WORKFLOW                 │
└─────────────────────────────────────────────────────────────┘

1. DATA COLLECTION (4-8 hours)
   ├── PubMed: 50K-200K articles
   ├── DrugBank: 14K drugs
   ├── OpenFDA: 100K labels + adverse events
   ├── DailyMed: 100K labels
   ├── RxNorm: Drug normalization
   ├── ClinicalTrials: 40K+ trials
   └── FDA Guidance: 500+ documents

2. DATA PROCESSING (30-60 min)
   ├── Load all sources
   ├── Clean & normalize
   ├── Convert to instruction format
   ├── Deduplicate
   └── Split train/val/test (80/10/10)
   → Result: 100K-500K training examples

3. MODEL TRAINING (8-18 hours)
   ├── Load BioMistral-7B
   ├── Apply QLoRA (4-bit quantization)
   ├── Fine-tune on medical data
   └── Save adapter weights
   → Result: Lumen Medical LLM v1

4. EVALUATION (30 min)
   ├── Test on held-out set
   ├── Generate responses
   └── Compute metrics
   → Result: Performance report

5. DEPLOYMENT (Phase 2)
   ├── Export model
   ├── Set up inference server
   └── Deploy to RunPod
   → Result: Production API

```

---

## Troubleshooting

### Issue: Out of Memory During Training
**Solution:**
```bash
# Reduce batch size
--per_device_train_batch_size 2  # Instead of 4

# Reduce sequence length
--max_seq_length 1024  # Instead of 2048

# Enable gradient checkpointing (already enabled)
--gradient_checkpointing True
```

### Issue: Scraper Rate Limited
**Solution:**
```bash
# The scrapers automatically handle rate limits
# If blocked, wait 1 hour and resume
# Checkpoint system will continue where it left off
```

### Issue: Dataset Not Found
**Solution:**
```bash
# Ensure data processing ran successfully
python data/processing/data_processor.py

# Check if files exist
ls -la data/datasets/
```

### Issue: Model Not Loading
**Solution:**
```bash
# Check if model was saved
ls -la model/checkpoints/lumen-medical-v1/

# Verify adapter files exist
# Should see: adapter_config.json, adapter_model.bin
```

---

## Performance Expectations

### Data Collection
- **PubMed:** 10K articles/hour
- **OpenFDA:** 5K records/hour
- **DailyMed:** 1K labels/hour
- **Total Time:** 4-8 hours for comprehensive collection

### Training
- **Training Loss:** Should decrease from ~2.0 to <0.5
- **Validation Loss:** Should decrease from ~1.8 to <0.6
- **Convergence:** 2-3 epochs sufficient

### Model Quality
- **Medical QA Accuracy:** 70-85% (subjective)
- **Response Relevance:** 80-90%
- **Hallucination Rate:** <10% (with proper prompting)

---

## Next Steps

After completing this workflow:

1. **Fine-tune Further:**
   - Add more domain-specific data
   - Increase training epochs
   - Tune hyperparameters

2. **Build Backend API** (Week 8-9)
   - FastAPI endpoints
   - RAG integration
   - User management

3. **Build Frontend** (Week 10-11)
   - Next.js interface
   - Patient dashboard
   - Pharma compliance UI

4. **Deploy to Production** (Week 12)
   - RunPod serverless
   - Database setup
   - Monitoring

---

## Support

**Issues?**
- Check logs: `data/scrapers/scraping.log`
- Check training logs: WandB dashboard
- Review error messages in terminal

**Questions?**
- Review documentation in `/docs`
- Check scraper README: `data/scrapers/README.md`
- Review code comments

---

## Success Checklist

- [ ] Environment set up with all dependencies
- [ ] API keys configured (at minimum PubMed)
- [ ] Data collected from all sources (100K+ examples)
- [ ] Data processed into training format
- [ ] Model trained for 3 epochs
- [ ] Evaluation completed with good metrics
- [ ] Model tested interactively
- [ ] Ready for backend development

---

**🎉 You now have a fully trained medical LLM!**

Next: Build the backend API and frontend interface (Weeks 8-11)
