"""
DrugBank XML parser
Parses DrugBank database dump for drug information

DrugBank Download: https://go.drugbank.com/releases/latest
License: Free for academic use (requires account and citation)
Format: XML (large file ~1GB uncompressed)
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

from data.scrapers.utils.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class DrugBankParser(BaseScraper):
    """
    Parser for DrugBank XML database

    Note: DrugBank requires manual download due to license agreement
    Download from: https://go.drugbank.com/releases/latest
    """

    # DrugBank XML namespace
    NS = {"db": "http://www.drugbank.ca"}

    def __init__(self, output_dir: str = "data/raw/drugbank"):
        """
        Initialize DrugBank parser

        Args:
            output_dir: Directory to save parsed data
        """
        super().__init__(
            name="DrugBank",
            output_dir=output_dir,
            user_agent="DrugBankParser/1.0",
            requests_per_second=100,  # Local file parsing, no rate limit needed
        )

    def parse_file(self, xml_file: str) -> List[Dict[str, Any]]:
        """
        Parse DrugBank XML file

        Args:
            xml_file: Path to DrugBank XML file

        Returns:
            List of drug dictionaries
        """
        xml_path = Path(xml_file)

        if not xml_path.exists():
            raise FileNotFoundError(
                f"DrugBank XML file not found: {xml_file}\n"
                "Please download from: https://go.drugbank.com/releases/latest"
            )

        logger.info(f"Parsing DrugBank XML: {xml_path}")
        logger.info("This may take several minutes for large files...")

        drugs = []

        # Use iterparse for memory efficiency with large files
        context = ET.iterparse(xml_path, events=("start", "end"))
        context = iter(context)

        _, root = next(context)  # Get root element

        drug_count = 0

        for event, elem in context:
            if event == "end" and elem.tag == f"{{{self.NS['db']}}}drug":
                drug_data = self._parse_drug(elem)
                if drug_data:
                    drugs.append(drug_data)
                    drug_count += 1

                    if drug_count % 100 == 0:
                        logger.info(f"Parsed {drug_count} drugs...")

                    # Save checkpoint every 1000 drugs
                    if drug_count % 1000 == 0:
                        self.save_checkpoint({
                            "drugs_parsed": drug_count,
                            "last_drugbank_id": drug_data.get("drugbank_id"),
                        })

                # Clear element to free memory
                elem.clear()
                root.clear()

        logger.info(f"Completed parsing {len(drugs)} drugs from DrugBank")
        return drugs

    def _parse_drug(self, drug_elem: ET.Element) -> Dict[str, Any]:
        """Parse single drug element"""
        try:
            # Basic information
            drugbank_id = self._get_text(drug_elem, ".//db:drugbank-id[@primary='true']")
            name = self._get_text(drug_elem, ".//db:name")
            description = self._get_text(drug_elem, ".//db:description")
            cas_number = self._get_text(drug_elem, ".//db:cas-number")

            # Drug type
            drug_type = drug_elem.get("type", "")

            # Synonyms
            synonyms = self._get_list(drug_elem, ".//db:synonyms/db:synonym")

            # Indication
            indication = self._get_text(drug_elem, ".//db:indication")

            # Pharmacodynamics
            pharmacodynamics = self._get_text(drug_elem, ".//db:pharmacodynamics")

            # Mechanism of action
            mechanism = self._get_text(drug_elem, ".//db:mechanism-of-action")

            # Toxicity
            toxicity = self._get_text(drug_elem, ".//db:toxicity")

            # Metabolism
            metabolism = self._get_text(drug_elem, ".//db:metabolism")

            # Half-life
            half_life = self._get_text(drug_elem, ".//db:half-life")

            # Route of administration
            routes = self._get_list(drug_elem, ".//db:routes/db:route")

            # Categories
            categories = []
            for cat in drug_elem.findall(".//db:categories/db:category", self.NS):
                category = self._get_text(cat, ".//db:category")
                if category:
                    categories.append(category)

            # Drug interactions
            interactions = []
            for interaction in drug_elem.findall(".//db:drug-interactions/db:drug-interaction", self.NS):
                interactions.append({
                    "drugbank_id": self._get_text(interaction, ".//db:drugbank-id"),
                    "name": self._get_text(interaction, ".//db:name"),
                    "description": self._get_text(interaction, ".//db:description"),
                })

            # Food interactions
            food_interactions = self._get_list(drug_elem, ".//db:food-interactions/db:food-interaction")

            # Affected organisms
            organisms = self._get_list(drug_elem, ".//db:affected-organisms/db:affected-organism")

            # External identifiers
            external_ids = {}
            for ext_id in drug_elem.findall(".//db:external-identifiers/db:external-identifier", self.NS):
                resource = self._get_text(ext_id, ".//db:resource")
                identifier = self._get_text(ext_id, ".//db:identifier")
                if resource and identifier:
                    external_ids[resource] = identifier

            # Targets (proteins the drug acts on)
            targets = []
            for target in drug_elem.findall(".//db:targets/db:target", self.NS):
                targets.append({
                    "name": self._get_text(target, ".//db:name"),
                    "organism": self._get_text(target, ".//db:organism"),
                    "actions": self._get_list(target, ".//db:actions/db:action"),
                })

            # Patents
            patents = []
            for patent in drug_elem.findall(".//db:patents/db:patent", self.NS):
                patents.append({
                    "number": self._get_text(patent, ".//db:number"),
                    "country": self._get_text(patent, ".//db:country"),
                    "approved": self._get_text(patent, ".//db:approved"),
                    "expires": self._get_text(patent, ".//db:expires"),
                })

            return {
                "drugbank_id": drugbank_id,
                "name": name,
                "description": description,
                "cas_number": cas_number,
                "drug_type": drug_type,
                "synonyms": synonyms,
                "indication": indication,
                "pharmacodynamics": pharmacodynamics,
                "mechanism_of_action": mechanism,
                "toxicity": toxicity,
                "metabolism": metabolism,
                "half_life": half_life,
                "routes": routes,
                "categories": categories,
                "interactions": interactions,
                "food_interactions": food_interactions,
                "affected_organisms": organisms,
                "external_identifiers": external_ids,
                "targets": targets,
                "patents": patents,
            }

        except Exception as e:
            logger.error(f"Error parsing drug: {e}")
            return {}

    def _get_text(self, element: ET.Element, xpath: str) -> str:
        """Get text from element using xpath"""
        elem = element.find(xpath, self.NS)
        return elem.text.strip() if elem is not None and elem.text else ""

    def _get_list(self, element: ET.Element, xpath: str) -> List[str]:
        """Get list of texts from elements"""
        items = []
        for elem in element.findall(xpath, self.NS):
            if elem.text:
                items.append(elem.text.strip())
        return items

    def scrape(self, xml_file: str = "data/raw/drugbank/full_database.xml") -> List[Dict[str, Any]]:
        """
        Main method to parse DrugBank XML

        Args:
            xml_file: Path to DrugBank XML file

        Returns:
            List of drug dictionaries
        """
        drugs = self.parse_file(xml_file)

        # Save all drugs
        self.save_json(
            drugs,
            "drugbank_all_drugs.json",
            metadata={
                "source": "DrugBank",
                "total_drugs": len(drugs),
                "license": "Academic use only - cite DrugBank",
            },
        )

        # Create category-specific files
        self._save_by_category(drugs)

        return drugs

    def _save_by_category(self, drugs: List[Dict[str, Any]]) -> None:
        """Save drugs organized by category"""
        categories = {}

        for drug in drugs:
            for category in drug.get("categories", []):
                if category not in categories:
                    categories[category] = []
                categories[category].append(drug)

        logger.info(f"Saving {len(categories)} categories")

        for category, cat_drugs in categories.items():
            # Sanitize filename
            filename = category.lower().replace(" ", "_").replace("/", "_")
            filename = f"drugbank_category_{filename}.json"

            self.save_json(
                cat_drugs,
                filename,
                metadata={"category": category, "count": len(cat_drugs)},
            )


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = DrugBankParser()

    # Parse DrugBank XML file
    # Download from: https://go.drugbank.com/releases/latest
    drugs = parser.run()

    print(f"\nParsed {len(drugs)} drugs from DrugBank")
    print("\nExample drug:")
    if drugs:
        import json
        print(json.dumps(drugs[0], indent=2))
