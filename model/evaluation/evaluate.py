"""
Evaluation script for Lumen Medical LLM
Tests fine-tuned model on test set and generates metrics
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

import torch
from datasets import load_dataset
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Evaluate fine-tuned medical LLM"""

    def __init__(
        self,
        base_model_name: str = "BioMistral/BioMistral-7B",
        peft_model_path: str = "model/checkpoints/lumen-medical-v1",
        test_dataset_path: str = "data/datasets/test.jsonl",
    ):
        """
        Initialize evaluator

        Args:
            base_model_name: Base model name
            peft_model_path: Path to fine-tuned PEFT model
            test_dataset_path: Path to test dataset
        """
        self.base_model_name = base_model_name
        self.peft_model_path = peft_model_path
        self.test_dataset_path = test_dataset_path

        self.model = None
        self.tokenizer = None
        self.test_dataset = None

    def load_model(self):
        """Load fine-tuned model and tokenizer"""
        logger.info(f"Loading base model: {self.base_model_name}")

        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )

        # Load PEFT adapters
        logger.info(f"Loading PEFT adapters from: {self.peft_model_path}")
        self.model = PeftModel.from_pretrained(self.model, self.peft_model_path)

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.peft_model_path)

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model.eval()

        logger.info("Model loaded successfully")

    def load_test_dataset(self):
        """Load test dataset"""
        logger.info(f"Loading test dataset from: {self.test_dataset_path}")

        self.test_dataset = load_dataset(
            "json",
            data_files=self.test_dataset_path,
            split="train",
        )

        logger.info(f"Loaded {len(self.test_dataset)} test examples")

    def generate_response(self, instruction: str, input_text: str = "", max_length: int = 512) -> str:
        """
        Generate response for given instruction

        Args:
            instruction: Instruction text
            input_text: Optional input context
            max_length: Maximum generation length

        Returns:
            Generated response
        """
        # Format prompt
        if input_text:
            prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input_text}

### Response:
"""
        else:
            prompt = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Response:
"""

        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
            )

        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract only the response part
        if "### Response:" in response:
            response = response.split("### Response:")[-1].strip()

        return response

    def evaluate_example(self, example: Dict) -> Dict:
        """
        Evaluate single example

        Args:
            example: Test example

        Returns:
            Evaluation results
        """
        instruction = example["instruction"]
        input_text = example.get("input", "")
        expected_output = example["output"]

        # Generate response
        generated_output = self.generate_response(instruction, input_text)

        # Simple quality metrics (can be expanded)
        result = {
            "instruction": instruction,
            "expected": expected_output[:200],  # Truncate for readability
            "generated": generated_output[:200],
            "expected_length": len(expected_output),
            "generated_length": len(generated_output),
            "metadata": example.get("metadata", {}),
        }

        return result

    def evaluate_all(self, num_samples: int = 100) -> List[Dict]:
        """
        Evaluate model on test set

        Args:
            num_samples: Number of samples to evaluate (None = all)

        Returns:
            List of evaluation results
        """
        if self.model is None:
            self.load_model()

        if self.test_dataset is None:
            self.load_test_dataset()

        # Sample test set if requested
        if num_samples and num_samples < len(self.test_dataset):
            import random
            indices = random.sample(range(len(self.test_dataset)), num_samples)
            test_samples = [self.test_dataset[i] for i in indices]
        else:
            test_samples = self.test_dataset

        logger.info(f"Evaluating {len(test_samples)} examples...")

        results = []

        for example in tqdm(test_samples, desc="Evaluating"):
            result = self.evaluate_example(example)
            results.append(result)

        return results

    def compute_metrics(self, results: List[Dict]) -> Dict:
        """
        Compute aggregate metrics

        Args:
            results: Evaluation results

        Returns:
            Metrics dictionary
        """
        metrics = {
            "total_examples": len(results),
            "avg_generated_length": sum(r["generated_length"] for r in results) / len(results),
            "avg_expected_length": sum(r["expected_length"] for r in results) / len(results),
        }

        # Metrics by source
        sources = {}
        for result in results:
            source = result.get("metadata", {}).get("source", "unknown")
            if source not in sources:
                sources[source] = 0
            sources[source] += 1

        metrics["examples_by_source"] = sources

        return metrics

    def save_results(self, results: List[Dict], metrics: Dict, output_dir: str = "model/evaluation"):
        """
        Save evaluation results

        Args:
            results: Evaluation results
            metrics: Computed metrics
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save results
        with open(output_path / "evaluation_results.json", "w") as f:
            json.dump(results, f, indent=2)

        # Save metrics
        with open(output_path / "evaluation_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

        # Save sample outputs as readable text
        with open(output_path / "sample_outputs.txt", "w") as f:
            f.write("LUMEN MEDICAL LLM - EVALUATION SAMPLES\n")
            f.write("="*60 + "\n\n")

            for i, result in enumerate(results[:20], 1):  # First 20 samples
                f.write(f"Example {i}\n")
                f.write("-"*60 + "\n")
                f.write(f"Instruction: {result['instruction']}\n\n")
                f.write(f"Generated Response:\n{result['generated']}\n\n")
                f.write(f"Expected Response:\n{result['expected']}\n\n")
                f.write("="*60 + "\n\n")

        logger.info(f"Results saved to {output_path}")


def main():
    """Run evaluation"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    logger.info("="*60)
    logger.info("LUMEN MEDICAL LLM - MODEL EVALUATION")
    logger.info("="*60)

    # Create evaluator
    evaluator = ModelEvaluator()

    # Run evaluation
    results = evaluator.evaluate_all(num_samples=100)  # Evaluate 100 samples

    # Compute metrics
    metrics = evaluator.compute_metrics(results)

    # Print metrics
    logger.info("\nEvaluation Metrics:")
    logger.info(json.dumps(metrics, indent=2))

    # Save results
    evaluator.save_results(results, metrics)

    logger.info("="*60)
    logger.info("✅ Evaluation Complete")
    logger.info("="*60)


if __name__ == "__main__":
    main()
