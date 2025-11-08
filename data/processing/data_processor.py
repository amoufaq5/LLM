"""
Data processing pipeline for converting raw scraped data to training format
Handles cleaning, normalization, deduplication, and instruction-tuning format conversion
"""

import json
import logging
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Process raw medical data into training-ready instruction-tuning format
    """

    def __init__(
        self,
        raw_data_dir: str = "data/raw",
        processed_data_dir: str = "data/processed",
        dataset_dir: str = "data/datasets",
    ):
        """
        Initialize data processor

        Args:
            raw_data_dir: Directory with raw scraped data
            processed_data_dir: Directory for processed data
            dataset_dir: Directory for training datasets
        """
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_data_dir = Path(processed_data_dir)
        self.dataset_dir = Path(dataset_dir)

        # Create directories
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.dataset_dir.mkdir(parents=True, exist_ok=True)

        self.instruction_examples = []

    def load_pubmed_data(self) -> List[Dict[str, Any]]:
        """Load and process PubMed articles"""
        logger.info("Processing PubMed data...")

        pubmed_dir = self.raw_data_dir / "pubmed"
        all_articles = []

        if not pubmed_dir.exists():
            logger.warning(f"PubMed directory not found: {pubmed_dir}")
            return []

        # Load all PubMed JSON files
        for json_file in pubmed_dir.glob("*.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                    articles = data.get("data", [])
                    all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")

        logger.info(f"Loaded {len(all_articles)} PubMed articles")

        # Convert to instruction format
        for article in all_articles:
            if not article.get("title") or not article.get("abstract"):
                continue

            # Create Q&A from title and abstract
            self.instruction_examples.append({
                "instruction": f"Summarize the medical research about: {article['title']}",
                "input": "",
                "output": article["abstract"],
                "metadata": {
                    "source": "pubmed",
                    "pmid": article.get("pmid", ""),
                    "type": "research_summary",
                    "mesh_terms": article.get("mesh_terms", []),
                },
            })

            # Create mesh term query examples
            for mesh_term in article.get("mesh_terms", [])[:3]:  # Top 3 terms
                self.instruction_examples.append({
                    "instruction": f"What does current research say about {mesh_term}?",
                    "input": "",
                    "output": f"Based on recent research: {article['abstract'][:500]}...",
                    "metadata": {
                        "source": "pubmed",
                        "type": "mesh_query",
                        "mesh_term": mesh_term,
                    },
                })

        return all_articles

    def load_drugbank_data(self) -> List[Dict[str, Any]]:
        """Load and process DrugBank data"""
        logger.info("Processing DrugBank data...")

        drugbank_dir = self.raw_data_dir / "drugbank"
        all_drugs = []

        if not drugbank_dir.exists():
            logger.warning(f"DrugBank directory not found: {drugbank_dir}")
            return []

        # Load DrugBank JSON
        drugbank_file = drugbank_dir / "drugbank_all_drugs.json"
        if drugbank_file.exists():
            try:
                with open(drugbank_file, "r") as f:
                    data = json.load(f)
                    all_drugs = data.get("data", [])
            except Exception as e:
                logger.error(f"Error loading DrugBank: {e}")
                return []

        logger.info(f"Loaded {len(all_drugs)} drugs from DrugBank")

        # Convert to instruction format
        for drug in all_drugs:
            drug_name = drug.get("name", "")
            if not drug_name:
                continue

            # Basic drug information
            self.instruction_examples.append({
                "instruction": f"Tell me about the drug {drug_name}",
                "input": "",
                "output": self._create_drug_description(drug),
                "metadata": {
                    "source": "drugbank",
                    "type": "drug_info",
                    "drug_name": drug_name,
                },
            })

            # Indication queries
            if drug.get("indication"):
                self.instruction_examples.append({
                    "instruction": f"What is {drug_name} used for?",
                    "input": "",
                    "output": drug["indication"],
                    "metadata": {
                        "source": "drugbank",
                        "type": "drug_indication",
                        "drug_name": drug_name,
                    },
                })

            # Side effects/toxicity
            if drug.get("toxicity"):
                self.instruction_examples.append({
                    "instruction": f"What are the side effects of {drug_name}?",
                    "input": "",
                    "output": drug["toxicity"],
                    "metadata": {
                        "source": "drugbank",
                        "type": "drug_side_effects",
                        "drug_name": drug_name,
                    },
                })

            # Drug interactions
            for interaction in drug.get("interactions", [])[:5]:  # Top 5
                if interaction.get("name") and interaction.get("description"):
                    self.instruction_examples.append({
                        "instruction": f"Does {drug_name} interact with {interaction['name']}?",
                        "input": "",
                        "output": f"Yes. {interaction['description']}",
                        "metadata": {
                            "source": "drugbank",
                            "type": "drug_interaction",
                            "drug1": drug_name,
                            "drug2": interaction["name"],
                        },
                    })

        return all_drugs

    def load_openfda_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load and process OpenFDA data"""
        logger.info("Processing OpenFDA data...")

        openfda_dir = self.raw_data_dir / "openfda"
        all_data = {}

        if not openfda_dir.exists():
            logger.warning(f"OpenFDA directory not found: {openfda_dir}")
            return {}

        # Load drug labels
        labels_file = openfda_dir / "openfda_drug_labels.json"
        if labels_file.exists():
            try:
                with open(labels_file, "r") as f:
                    data = json.load(f)
                    all_data["labels"] = data.get("data", [])
                    logger.info(f"Loaded {len(all_data['labels'])} FDA drug labels")
            except Exception as e:
                logger.error(f"Error loading FDA labels: {e}")

        # Process labels for training
        for label in all_data.get("labels", []):
            # Extract key information
            openfda = label.get("openfda", {})
            brand_names = openfda.get("brand_name", [])
            generic_names = openfda.get("generic_name", [])

            if not brand_names and not generic_names:
                continue

            drug_name = brand_names[0] if brand_names else generic_names[0]

            # Warnings
            warnings = label.get("warnings", [""])
            if warnings and warnings[0]:
                self.instruction_examples.append({
                    "instruction": f"What are the warnings for {drug_name}?",
                    "input": "",
                    "output": warnings[0][:1000],  # Truncate long warnings
                    "metadata": {
                        "source": "openfda",
                        "type": "drug_warnings",
                        "drug_name": drug_name,
                    },
                })

            # Indications and usage
            indications = label.get("indications_and_usage", [""])
            if indications and indications[0]:
                self.instruction_examples.append({
                    "instruction": f"When should I use {drug_name}?",
                    "input": "",
                    "output": indications[0][:1000],
                    "metadata": {
                        "source": "openfda",
                        "type": "drug_usage",
                        "drug_name": drug_name,
                    },
                })

        return all_data

    def load_dailymed_data(self) -> List[Dict[str, Any]]:
        """Load and process DailyMed data"""
        logger.info("Processing DailyMed data...")

        dailymed_dir = self.raw_data_dir / "dailymed"
        all_labels = []

        if not dailymed_dir.exists():
            logger.warning(f"DailyMed directory not found: {dailymed_dir}")
            return []

        # Load all DailyMed files
        for json_file in dailymed_dir.glob("*.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                    labels = data.get("data", [])
                    all_labels.extend(labels)
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")

        logger.info(f"Loaded {len(all_labels)} DailyMed labels")

        # Convert to instruction format
        for label in all_labels:
            title = label.get("title", "")
            if not title:
                continue

            sections = label.get("sections", {})

            # Create examples for each section
            for section_name, section_text in sections.items():
                if not section_text or len(section_text) < 50:
                    continue

                self.instruction_examples.append({
                    "instruction": f"Provide information about {section_name.lower()} for {title}",
                    "input": "",
                    "output": section_text[:1500],  # Limit length
                    "metadata": {
                        "source": "dailymed",
                        "type": "drug_label_section",
                        "section": section_name,
                        "drug_title": title,
                    },
                })

        return all_labels

    def load_clinicaltrials_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load and process ClinicalTrials.gov data"""
        logger.info("Processing ClinicalTrials data...")

        ct_dir = self.raw_data_dir / "clinicaltrials"
        all_data = {}

        if not ct_dir.exists():
            logger.warning(f"ClinicalTrials directory not found: {ct_dir}")
            return {}

        # Load all clinical trials files
        for json_file in ct_dir.glob("*.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                    trials = data.get("data", [])

                    if isinstance(trials, dict):
                        # Handle nested structure
                        for category, trial_list in trials.items():
                            if category not in all_data:
                                all_data[category] = []
                            all_data[category].extend(trial_list)
                    else:
                        all_data["general"] = all_data.get("general", []) + trials

            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")

        total_trials = sum(len(trials) for trials in all_data.values())
        logger.info(f"Loaded {total_trials} clinical trials")

        # Convert to instruction format
        for category, trials in all_data.items():
            for trial in trials:
                if not trial.get("title") or not trial.get("brief_summary"):
                    continue

                # Trial information query
                self.instruction_examples.append({
                    "instruction": f"Tell me about the clinical trial: {trial['title'][:100]}",
                    "input": "",
                    "output": trial["brief_summary"],
                    "metadata": {
                        "source": "clinicaltrials",
                        "type": "trial_info",
                        "nct_id": trial.get("nct_id", ""),
                        "category": category,
                    },
                })

                # Condition-based queries
                for condition in trial.get("conditions", [])[:2]:
                    self.instruction_examples.append({
                        "instruction": f"What clinical trials are being conducted for {condition}?",
                        "input": "",
                        "output": f"One relevant trial is: {trial['title']}. {trial['brief_summary'][:300]}...",
                        "metadata": {
                            "source": "clinicaltrials",
                            "type": "condition_trials",
                            "condition": condition,
                        },
                    })

        return all_data

    def _create_drug_description(self, drug: Dict[str, Any]) -> str:
        """Create comprehensive drug description"""
        parts = []

        if drug.get("description"):
            parts.append(drug["description"][:500])

        if drug.get("indication"):
            parts.append(f"\nIndications: {drug['indication'][:300]}")

        if drug.get("mechanism_of_action"):
            parts.append(f"\nMechanism: {drug['mechanism_of_action'][:300]}")

        if drug.get("pharmacodynamics"):
            parts.append(f"\nPharmacodynamics: {drug['pharmacodynamics'][:300]}")

        return "\n".join(parts) if parts else "Information not available."

    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep medical symbols
        # Keep: letters, numbers, spaces, punctuation, medical symbols
        text = re.sub(r'[^\w\s.,;:!?()\[\]{}<>/@#$%&*+=\-\'\"°µ]', '', text)

        return text.strip()

    def deduplicate_examples(self) -> None:
        """Remove duplicate training examples"""
        logger.info(f"Deduplicating {len(self.instruction_examples)} examples...")

        seen_outputs = set()
        unique_examples = []

        for example in self.instruction_examples:
            output_hash = hash(example["output"][:200])  # Hash first 200 chars

            if output_hash not in seen_outputs:
                seen_outputs.add(output_hash)
                unique_examples.append(example)

        removed = len(self.instruction_examples) - len(unique_examples)
        logger.info(f"Removed {removed} duplicates, kept {len(unique_examples)} unique examples")

        self.instruction_examples = unique_examples

    def create_train_val_test_split(
        self,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Split data into train/validation/test sets

        Args:
            train_ratio: Proportion for training
            val_ratio: Proportion for validation
            test_ratio: Proportion for testing

        Returns:
            Tuple of (train, val, test) datasets
        """
        # Shuffle data
        random.shuffle(self.instruction_examples)

        total = len(self.instruction_examples)
        train_size = int(total * train_ratio)
        val_size = int(total * val_ratio)

        train_data = self.instruction_examples[:train_size]
        val_data = self.instruction_examples[train_size:train_size + val_size]
        test_data = self.instruction_examples[train_size + val_size:]

        logger.info(f"Split sizes - Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")

        return train_data, val_data, test_data

    def save_datasets(self, train: List[Dict], val: List[Dict], test: List[Dict]) -> None:
        """Save datasets to JSON files"""
        logger.info("Saving datasets...")

        # Save as JSON
        with open(self.dataset_dir / "train.json", "w") as f:
            json.dump(train, f, indent=2)

        with open(self.dataset_dir / "validation.json", "w") as f:
            json.dump(val, f, indent=2)

        with open(self.dataset_dir / "test.json", "w") as f:
            json.dump(test, f, indent=2)

        # Save as JSONL (one example per line - better for streaming)
        with open(self.dataset_dir / "train.jsonl", "w") as f:
            for example in train:
                f.write(json.dumps(example) + "\n")

        with open(self.dataset_dir / "validation.jsonl", "w") as f:
            for example in val:
                f.write(json.dumps(example) + "\n")

        with open(self.dataset_dir / "test.jsonl", "w") as f:
            for example in test:
                f.write(json.dumps(example) + "\n")

        logger.info(f"Datasets saved to {self.dataset_dir}")

    def generate_statistics(self) -> Dict[str, Any]:
        """Generate dataset statistics"""
        stats = {
            "total_examples": len(self.instruction_examples),
            "sources": defaultdict(int),
            "types": defaultdict(int),
            "avg_instruction_length": 0,
            "avg_output_length": 0,
        }

        total_inst_len = 0
        total_output_len = 0

        for example in self.instruction_examples:
            metadata = example.get("metadata", {})
            stats["sources"][metadata.get("source", "unknown")] += 1
            stats["types"][metadata.get("type", "unknown")] += 1

            total_inst_len += len(example.get("instruction", ""))
            total_output_len += len(example.get("output", ""))

        if self.instruction_examples:
            stats["avg_instruction_length"] = total_inst_len / len(self.instruction_examples)
            stats["avg_output_length"] = total_output_len / len(self.instruction_examples)

        # Convert defaultdicts to regular dicts
        stats["sources"] = dict(stats["sources"])
        stats["types"] = dict(stats["types"])

        return stats

    def process_all(self) -> None:
        """
        Main processing pipeline - load all data and create training datasets
        """
        logger.info("="*60)
        logger.info("LUMEN MEDICAL LLM - DATA PROCESSING PIPELINE")
        logger.info("="*60)

        # Load all data sources
        self.load_pubmed_data()
        self.load_drugbank_data()
        self.load_openfda_data()
        self.load_dailymed_data()
        self.load_clinicaltrials_data()

        logger.info(f"Total examples before deduplication: {len(self.instruction_examples)}")

        # Deduplicate
        self.deduplicate_examples()

        # Generate statistics
        stats = self.generate_statistics()
        logger.info(f"Dataset statistics:\n{json.dumps(stats, indent=2)}")

        # Create splits
        train, val, test = self.create_train_val_test_split()

        # Save datasets
        self.save_datasets(train, val, test)

        # Save statistics
        with open(self.dataset_dir / "statistics.json", "w") as f:
            json.dump(stats, f, indent=2)

        logger.info("="*60)
        logger.info("DATA PROCESSING COMPLETE")
        logger.info(f"Training examples: {len(train)}")
        logger.info(f"Validation examples: {len(val)}")
        logger.info(f"Test examples: {len(test)}")
        logger.info(f"Datasets saved to: {self.dataset_dir}")
        logger.info("="*60)


# CLI interface
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    processor = DataProcessor()
    processor.process_all()

    print("\n✅ Data processing complete!")
    print(f"📁 Datasets location: {processor.dataset_dir}")
    print("\nFiles created:")
    print("  - train.json / train.jsonl")
    print("  - validation.json / validation.jsonl")
    print("  - test.json / test.jsonl")
    print("  - statistics.json")
