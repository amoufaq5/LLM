"""
RxNorm API client for drug name normalization and relationships

API Documentation: https://lhncbc.nlm.nih.gov/RxNav/APIs/
Rate Limit: No official limit (20 req/sec recommended)
License: Free, no authentication required
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from data.scrapers.utils.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class RxNormClient(BaseScraper):
    """
    Client for RxNorm API
    Provides drug name normalization and relationship data
    """

    BASE_URL = "https://rxnav.nlm.nih.gov/REST"

    def __init__(self, output_dir: str = "data/raw/rxnorm"):
        """
        Initialize RxNorm client

        Args:
            output_dir: Directory to save data
        """
        super().__init__(
            name="RxNorm",
            output_dir=output_dir,
            user_agent="LumenMedicalBot/1.0",
            requests_per_second=10.0,  # Conservative rate
        )

    def get_rxcui(self, drug_name: str) -> Optional[str]:
        """
        Get RxCUI (RxNorm Concept Unique Identifier) for a drug name

        Args:
            drug_name: Drug name (brand or generic)

        Returns:
            RxCUI string or None
        """
        url = f"{self.BASE_URL}/rxcui.json?name={quote(drug_name)}"

        try:
            response = self.get(url)
            data = response.json()

            rxcui_list = data.get("idGroup", {}).get("rxnormId", [])
            return rxcui_list[0] if rxcui_list else None

        except Exception as e:
            logger.error(f"Error getting RxCUI for '{drug_name}': {e}")
            return None

    def get_drug_properties(self, rxcui: str) -> Optional[Dict[str, Any]]:
        """
        Get properties for a drug by RxCUI

        Args:
            rxcui: RxNorm Concept Unique Identifier

        Returns:
            Drug properties dictionary
        """
        url = f"{self.BASE_URL}/rxcui/{rxcui}/properties.json"

        try:
            response = self.get(url)
            data = response.json()
            return data.get("properties", {})

        except Exception as e:
            logger.error(f"Error getting properties for RxCUI {rxcui}: {e}")
            return None

    def get_related_drugs(self, rxcui: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get related drugs (generics, brands, ingredients)

        Args:
            rxcui: RxNorm Concept Unique Identifier

        Returns:
            Dictionary of related drugs by relationship type
        """
        url = f"{self.BASE_URL}/rxcui/{rxcui}/related.json?tty=IN+BN+SCD+GPCK"

        try:
            response = self.get(url)
            data = response.json()

            related = {}
            concept_groups = data.get("relatedGroup", {}).get("conceptGroup", [])

            for group in concept_groups:
                tty = group.get("tty")  # Term type
                concepts = group.get("conceptProperties", [])

                if tty and concepts:
                    related[tty] = concepts

            return related

        except Exception as e:
            logger.error(f"Error getting related drugs for RxCUI {rxcui}: {e}")
            return {}

    def get_ndc_codes(self, rxcui: str) -> List[str]:
        """
        Get NDC codes for a drug

        Args:
            rxcui: RxNorm Concept Unique Identifier

        Returns:
            List of NDC codes
        """
        url = f"{self.BASE_URL}/rxcui/{rxcui}/ndcs.json"

        try:
            response = self.get(url)
            data = response.json()

            ndcs = data.get("ndcGroup", {}).get("ndcList", {}).get("ndc", [])
            return ndcs

        except Exception as e:
            logger.error(f"Error getting NDCs for RxCUI {rxcui}: {e}")
            return []

    def get_drug_interactions(self, rxcui_list: List[str]) -> List[Dict[str, Any]]:
        """
        Get drug-drug interactions

        Args:
            rxcui_list: List of RxCUIs to check

        Returns:
            List of interaction dictionaries
        """
        # API supports up to 50 RxCUIs
        rxcuis = "+".join(rxcui_list[:50])
        url = f"{self.BASE_URL}/interaction/list.json?rxcuis={rxcuis}"

        try:
            response = self.get(url)
            data = response.json()

            interactions = []
            full_list = data.get("fullInteractionTypeGroup", [])

            for group in full_list:
                for interaction_type in group.get("fullInteractionType", []):
                    for interaction_pair in interaction_type.get("interactionPair", []):
                        interactions.append({
                            "severity": interaction_pair.get("severity", ""),
                            "description": interaction_pair.get("description", ""),
                            "drug1": {
                                "name": interaction_pair.get("interactionConcept", [{}])[0].get("minConceptItem", {}).get("name"),
                                "rxcui": interaction_pair.get("interactionConcept", [{}])[0].get("minConceptItem", {}).get("rxcui"),
                            },
                            "drug2": {
                                "name": interaction_pair.get("interactionConcept", [{}])[1].get("minConceptItem", {}).get("name") if len(interaction_pair.get("interactionConcept", [])) > 1 else None,
                                "rxcui": interaction_pair.get("interactionConcept", [{}])[1].get("minConceptItem", {}).get("rxcui") if len(interaction_pair.get("interactionConcept", [])) > 1 else None,
                            },
                        })

            return interactions

        except Exception as e:
            logger.error(f"Error getting interactions: {e}")
            return []

    def spell_suggestions(self, drug_name: str) -> List[str]:
        """
        Get spelling suggestions for misspelled drug names

        Args:
            drug_name: Possibly misspelled drug name

        Returns:
            List of suggested spellings
        """
        url = f"{self.BASE_URL}/spellingsuggestions.json?name={quote(drug_name)}"

        try:
            response = self.get(url)
            data = response.json()

            suggestions = data.get("suggestionGroup", {}).get("suggestionList", {}).get("suggestion", [])
            return suggestions

        except Exception as e:
            logger.error(f"Error getting spelling suggestions for '{drug_name}': {e}")
            return []

    def get_all_drugs_by_class(self, class_id: str) -> List[Dict[str, Any]]:
        """
        Get all drugs in a therapeutic class

        Args:
            class_id: Class identifier (e.g., ATC code)

        Returns:
            List of drugs in class
        """
        url = f"{self.BASE_URL}/rxclass/class/byId.json?classId={quote(class_id)}"

        try:
            response = self.get(url)
            data = response.json()

            drugs = []
            concept_list = data.get("rxclassMinConceptList", {}).get("rxclassMinConcept", [])

            for concept in concept_list:
                drugs.append({
                    "rxcui": concept.get("rxcui"),
                    "name": concept.get("className"),
                })

            return drugs

        except Exception as e:
            logger.error(f"Error getting drugs for class {class_id}: {e}")
            return []

    def build_drug_database(self, drug_names: List[str]) -> List[Dict[str, Any]]:
        """
        Build normalized drug database from list of drug names

        Args:
            drug_names: List of drug names to normalize

        Returns:
            List of normalized drug entries
        """
        drug_database = []

        logger.info(f"Building drug database for {len(drug_names)} drugs...")

        for i, drug_name in enumerate(drug_names):
            try:
                # Get RxCUI
                rxcui = self.get_rxcui(drug_name)

                if not rxcui:
                    logger.warning(f"No RxCUI found for '{drug_name}'")
                    continue

                # Get properties
                properties = self.get_drug_properties(rxcui)

                # Get related drugs
                related = self.get_related_drugs(rxcui)

                # Get NDC codes
                ndcs = self.get_ndc_codes(rxcui)

                drug_entry = {
                    "original_name": drug_name,
                    "rxcui": rxcui,
                    "properties": properties,
                    "related_drugs": related,
                    "ndc_codes": ndcs,
                }

                drug_database.append(drug_entry)

                if (i + 1) % 50 == 0:
                    logger.info(f"Processed {i + 1}/{len(drug_names)} drugs...")

                    # Save checkpoint
                    self.save_checkpoint({
                        "processed": i + 1,
                        "total": len(drug_names),
                    })

            except Exception as e:
                logger.error(f"Error processing drug '{drug_name}': {e}")
                continue

        return drug_database

    def scrape(self, drug_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Main scraping method

        Args:
            drug_names: List of drug names (uses common drugs if None)

        Returns:
            List of normalized drug entries
        """
        # Use common drugs if none provided
        if drug_names is None:
            drug_names = [
                # Common medications
                "aspirin", "acetaminophen", "ibuprofen", "naproxen",
                "metformin", "insulin", "lisinopril", "amlodipine",
                "atorvastatin", "simvastatin", "omeprazole", "pantoprazole",
                "levothyroxine", "albuterol", "fluticasone", "montelukast",
                "sertraline", "escitalopram", "duloxetine", "bupropion",
                "gabapentin", "pregabalin", "tramadol", "hydrocodone",
                "warfarin", "apixaban", "rivaroxaban", "clopidogrel",
                "metoprolol", "carvedilol", "losartan", "valsartan",
                "furosemide", "hydrochlorothiazide", "spironolactone",
                "amoxicillin", "azithromycin", "ciprofloxacin", "doxycycline",
                "prednisone", "methylprednisolone", "hydrocortisone",
                # Add more as needed
            ]

        logger.info(f"Processing {len(drug_names)} drugs...")

        # Build database
        drug_database = self.build_drug_database(drug_names)

        # Save all data
        self.save_json(
            drug_database,
            "rxnorm_drug_database.json",
            metadata={
                "source": "RxNorm",
                "total_drugs": len(drug_database),
                "input_drugs": len(drug_names),
            },
        )

        # Example: Get interactions for first 10 drugs
        if drug_database:
            rxcui_list = [drug["rxcui"] for drug in drug_database[:10] if drug.get("rxcui")]

            if rxcui_list:
                logger.info(f"Checking interactions for {len(rxcui_list)} drugs...")
                interactions = self.get_drug_interactions(rxcui_list)

                self.save_json(
                    interactions,
                    "rxnorm_drug_interactions_sample.json",
                    metadata={
                        "source": "RxNorm Drug Interactions",
                        "total_interactions": len(interactions),
                    },
                )

        return drug_database


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    client = RxNormClient()

    # Build normalized drug database
    drugs = client.run()

    print(f"\nProcessed {len(drugs)} drugs")

    # Example: Check interactions
    if drugs:
        rxcuis = [d["rxcui"] for d in drugs[:5] if d.get("rxcui")]
        print(f"\nChecking interactions for: {rxcuis}")
        interactions = client.get_drug_interactions(rxcuis)
        print(f"Found {len(interactions)} interactions")
