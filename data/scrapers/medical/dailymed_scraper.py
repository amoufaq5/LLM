"""
DailyMed scraper for FDA-approved drug labels
Uses DailyMed REST API for structured drug information

API Documentation: https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm
Rate Limit: No official limit, but be respectful (1-2 req/sec recommended)
"""

import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from data.scrapers.utils.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class DailyMedScraper(BaseScraper):
    """
    Scraper for DailyMed drug labels using REST API
    """

    BASE_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

    def __init__(self, output_dir: str = "data/raw/dailymed"):
        """
        Initialize DailyMed scraper

        Args:
            output_dir: Directory to save data
        """
        super().__init__(
            name="DailyMed",
            output_dir=output_dir,
            user_agent="LumenMedicalBot/1.0",
            requests_per_second=1.5,  # Be conservative
        )

    def search_drugs(self, drug_name: str, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """
        Search for drugs by name

        Args:
            drug_name: Drug name to search
            page: Page number
            page_size: Results per page

        Returns:
            Search results
        """
        url = f"{self.BASE_URL}/spls.json"
        params = {
            "drug_name": quote(drug_name),
            "page": page,
            "pagesize": page_size,
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{query_string}"

        try:
            response = self.get(full_url)
            return response.json()

        except Exception as e:
            logger.error(f"Error searching for drug '{drug_name}': {e}")
            return {}

    def get_all_setids(self, max_results: int = 10000) -> List[str]:
        """
        Get all SPL Set IDs from DailyMed

        Args:
            max_results: Maximum set IDs to retrieve

        Returns:
            List of set IDs
        """
        all_setids = []
        page = 1
        page_size = 100

        logger.info("Fetching all drug set IDs from DailyMed...")

        url = f"{self.BASE_URL}/spls.json"

        while len(all_setids) < max_results:
            try:
                params = f"page={page}&pagesize={page_size}"
                full_url = f"{url}?{params}"

                response = self.get(full_url)
                data = response.json()

                # Extract set IDs
                results = data.get("data", [])

                if not results:
                    break

                for item in results:
                    setid = item.get("setid")
                    if setid:
                        all_setids.append(setid)

                logger.info(f"Retrieved {len(all_setids)} set IDs (page {page})...")

                page += 1

                # Check if we've reached the end
                if len(results) < page_size:
                    break

            except Exception as e:
                logger.error(f"Error fetching set IDs at page {page}: {e}")
                break

        logger.info(f"Total set IDs retrieved: {len(all_setids)}")
        return all_setids

    def get_drug_label(self, setid: str) -> Optional[Dict[str, Any]]:
        """
        Get drug label by SPL Set ID

        Args:
            setid: SPL Set ID

        Returns:
            Drug label data
        """
        url = f"{self.BASE_URL}/spls/{setid}.json"

        try:
            response = self.get(url)
            return response.json()

        except Exception as e:
            logger.error(f"Error fetching label for setid {setid}: {e}")
            return None

    def get_drug_label_xml(self, setid: str) -> Optional[str]:
        """
        Get drug label as XML (SPL format)

        Args:
            setid: SPL Set ID

        Returns:
            XML string
        """
        url = f"{self.BASE_URL}/spls/{setid}.xml"

        try:
            response = self.get(url)
            return response.text

        except Exception as e:
            logger.error(f"Error fetching XML for setid {setid}: {e}")
            return None

    def get_ndc_by_setid(self, setid: str) -> List[str]:
        """
        Get NDC codes for a drug by set ID

        Args:
            setid: SPL Set ID

        Returns:
            List of NDC codes
        """
        url = f"{self.BASE_URL}/spls/{setid}/ndcs.json"

        try:
            response = self.get(url)
            data = response.json()
            ndcs = [item.get("ndc") for item in data.get("data", []) if item.get("ndc")]
            return ndcs

        except Exception as e:
            logger.error(f"Error fetching NDCs for setid {setid}: {e}")
            return []

    def parse_drug_classes(self, label_data: Dict[str, Any]) -> List[str]:
        """Extract drug classes from label data"""
        classes = []

        # Check various fields for drug class information
        if "pharm_classes" in label_data:
            for pc in label_data["pharm_classes"]:
                if isinstance(pc, str):
                    classes.append(pc)
                elif isinstance(pc, dict):
                    classes.append(pc.get("name", ""))

        return [c for c in classes if c]

    def extract_structured_data(self, label_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from label JSON

        Args:
            label_data: Raw label data

        Returns:
            Structured drug information
        """
        try:
            data = label_data.get("data", {})

            # Basic information
            setid = data.get("setid", "")
            title = data.get("title", "")
            published_date = data.get("published_date", "")

            # Drug names
            drug_names = data.get("drug_names", [])

            # Active ingredients
            active_ingredients = data.get("active_ingredients", [])

            # Marketing info
            marketing = data.get("marketing", [])

            # Application numbers
            application_numbers = data.get("application_numbers", [])

            # SPL sections (indications, dosage, warnings, etc.)
            sections = {}

            # Common section mappings
            section_mappings = {
                "indications_and_usage": "Indications and Usage",
                "dosage_and_administration": "Dosage and Administration",
                "contraindications": "Contraindications",
                "warnings_and_precautions": "Warnings and Precautions",
                "adverse_reactions": "Adverse Reactions",
                "drug_interactions": "Drug Interactions",
                "use_in_specific_populations": "Use in Specific Populations",
                "description": "Description",
                "clinical_pharmacology": "Clinical Pharmacology",
                "how_supplied": "How Supplied",
            }

            for key, label in section_mappings.items():
                if key in data:
                    sections[label] = data[key]

            return {
                "setid": setid,
                "title": title,
                "published_date": published_date,
                "drug_names": drug_names,
                "active_ingredients": active_ingredients,
                "marketing_info": marketing,
                "application_numbers": application_numbers,
                "sections": sections,
                "pharm_classes": self.parse_drug_classes(data),
            }

        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return {}

    def scrape_batch(self, setids: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape multiple drug labels

        Args:
            setids: List of SPL Set IDs

        Returns:
            List of drug label data
        """
        labels = []

        for i, setid in enumerate(setids):
            try:
                label_data = self.get_drug_label(setid)

                if label_data:
                    structured_data = self.extract_structured_data(label_data)

                    # Add NDC codes
                    structured_data["ndc_codes"] = self.get_ndc_by_setid(setid)

                    labels.append(structured_data)

                    if (i + 1) % 100 == 0:
                        logger.info(f"Processed {i + 1}/{len(setids)} labels...")

                        # Save checkpoint
                        self.save_checkpoint({
                            "processed": i + 1,
                            "total": len(setids),
                            "last_setid": setid,
                        })

            except Exception as e:
                logger.error(f"Error processing setid {setid}: {e}")
                continue

        return labels

    def scrape(
        self,
        max_labels: int = 5000,
        checkpoint_file: str = "checkpoint.json",
    ) -> List[Dict[str, Any]]:
        """
        Main scraping method

        Args:
            max_labels: Maximum labels to scrape
            checkpoint_file: Checkpoint file for resume capability

        Returns:
            List of drug labels
        """
        # Load checkpoint if exists
        checkpoint = self.load_checkpoint(checkpoint_file)
        processed = checkpoint.get("processed", 0)

        # Get all set IDs
        logger.info("Fetching all drug set IDs...")
        all_setids = self.get_all_setids(max_results=max_labels)

        # Skip already processed
        setids_to_process = all_setids[processed:]

        logger.info(f"Processing {len(setids_to_process)} labels (skipping {processed})...")

        # Scrape labels
        labels = self.scrape_batch(setids_to_process)

        # Save all labels
        self.save_json(
            labels,
            "dailymed_all_labels.json",
            metadata={
                "source": "DailyMed",
                "total_labels": len(labels),
                "processed": processed + len(labels),
            },
        )

        # Group by drug class
        self._save_by_class(labels)

        return labels

    def _save_by_class(self, labels: List[Dict[str, Any]]) -> None:
        """Save labels grouped by pharmacological class"""
        classes = {}

        for label in labels:
            for pharm_class in label.get("pharm_classes", []):
                if pharm_class not in classes:
                    classes[pharm_class] = []
                classes[pharm_class].append(label)

        logger.info(f"Saving {len(classes)} pharmacological classes")

        for pharm_class, class_labels in classes.items():
            # Sanitize filename
            filename = pharm_class.lower().replace(" ", "_").replace("/", "_")[:50]
            filename = f"dailymed_class_{filename}.json"

            self.save_json(
                class_labels,
                filename,
                metadata={
                    "pharm_class": pharm_class,
                    "count": len(class_labels),
                },
            )


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    scraper = DailyMedScraper()

    # Scrape drug labels
    labels = scraper.run()

    print(f"\nScraped {len(labels)} drug labels from DailyMed")
