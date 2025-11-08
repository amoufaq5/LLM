"""
DailyMed scraper for FDA-approved drug labels (FIXED & EXPANDED)
Uses DailyMed REST API with XML parsing for maximum compatibility

API Documentation: https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm
Rate Limit: No official limit, but be respectful (2 req/sec)
"""

import logging
import re
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlencode

from data.scrapers.utils.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class DailyMedScraper(BaseScraper):
    """
    Scraper for DailyMed drug labels using REST API (XML format - most reliable)
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
            requests_per_second=2.0,  # Increased for efficiency
        )

    def get_all_setids_xml(self, max_results: int = 100000) -> List[str]:
        """
        Get ALL SPL Set IDs from DailyMed using XML (more reliable)

        Args:
            max_results: Maximum set IDs to retrieve (default: 100K = all)

        Returns:
            List of set IDs
        """
        all_setids = []
        page = 1
        page_size = 100

        logger.info("Fetching ALL drug set IDs from DailyMed (XML format)...")

        while len(all_setids) < max_results:
            try:
                # Use XML endpoint (more reliable than JSON)
                url = f"{self.BASE_URL}/spls.xml?page={page}&pagesize={page_size}"

                response = self.get(url)

                # Parse XML
                root = ET.fromstring(response.content)

                # Find all setids in XML
                setids = root.findall(".//setid")

                if not setids:
                    logger.info(f"No more results at page {page}. Collection complete.")
                    break

                for setid_elem in setids:
                    setid = setid_elem.text
                    if setid:
                        all_setids.append(setid.strip())

                logger.info(f"Retrieved {len(all_setids)} set IDs (page {page})...")

                # Save checkpoint every 1000
                if len(all_setids) % 1000 == 0:
                    self.save_checkpoint({
                        "setids_collected": len(all_setids),
                        "current_page": page,
                    })

                page += 1

                # If we got fewer results than page_size, we're at the end
                if len(setids) < page_size:
                    logger.info("Reached last page of results")
                    break

            except Exception as e:
                logger.error(f"Error fetching set IDs at page {page}: {e}")
                # Continue with what we have
                break

        logger.info(f"Total set IDs retrieved: {len(all_setids)}")
        return all_setids

    def get_drug_label_xml(self, setid: str) -> Optional[Dict[str, Any]]:
        """
        Get drug label by SPL Set ID using XML format

        Args:
            setid: SPL Set ID

        Returns:
            Drug label data
        """
        url = f"{self.BASE_URL}/spls/{setid}.xml"

        try:
            response = self.get(url)

            # Parse XML using robust parsing
            root = ET.fromstring(response.content)

            # Extract data from XML
            label_data = self._parse_spl_xml(root, setid)

            return label_data

        except Exception as e:
            logger.error(f"Error fetching XML for setid {setid}: {e}")
            return None

    def _parse_spl_xml(self, root: ET.Element, setid: str) -> Dict[str, Any]:
        """
        Parse SPL XML structure to extract drug information

        Args:
            root: XML root element
            setid: Set ID

        Returns:
            Structured drug data
        """
        try:
            # Namespace handling for SPL
            ns = {'spl': 'urn:hl7-org:v3'}

            # Title
            title_elem = root.find(".//spl:title", ns)
            title = title_elem.text if title_elem is not None and title_elem.text else ""

            # Effective time
            effective_time_elem = root.find(".//spl:effectiveTime", ns)
            effective_time = effective_time_elem.get('value', '') if effective_time_elem is not None else ""

            # Manufacturer
            manufacturer_elem = root.find(".//spl:representedOrganization/spl:name", ns)
            manufacturer = manufacturer_elem.text if manufacturer_elem is not None and manufacturer_elem.text else ""

            # Active ingredients
            active_ingredients = []
            for ingredient in root.findall(".//spl:activeIngredient", ns):
                name_elem = ingredient.find(".//spl:name", ns)
                if name_elem is not None and name_elem.text:
                    active_ingredients.append(name_elem.text)

            # Product codes
            product_codes = []
            for code_elem in root.findall(".//spl:code", ns):
                code = code_elem.get('code', '')
                if code:
                    product_codes.append(code)

            # Extract text sections (indications, dosage, warnings, etc.)
            sections = self._extract_sections(root, ns)

            return {
                "setid": setid,
                "title": title.strip(),
                "effective_time": effective_time,
                "manufacturer": manufacturer.strip(),
                "active_ingredients": active_ingredients,
                "product_codes": product_codes,
                "sections": sections,
            }

        except Exception as e:
            logger.error(f"Error parsing SPL XML for setid {setid}: {e}")
            return {
                "setid": setid,
                "error": str(e),
            }

    def _extract_sections(self, root: ET.Element, ns: dict) -> Dict[str, str]:
        """Extract text sections from SPL XML"""
        sections = {}

        # Common section codes and titles
        section_mappings = {
            "34067-9": "Indications and Usage",
            "34068-7": "Dosage and Administration",
            "34070-3": "Contraindications",
            "43685-7": "Warnings and Precautions",
            "34084-4": "Adverse Reactions",
            "34073-7": "Drug Interactions",
            "34071-1": "Warnings",
            "34090-1": "Description",
            "34091-9": "Clinical Pharmacology",
            "34069-5": "How Supplied",
            "42229-5": "Pregnancy",
            "43684-0": "Pediatric Use",
            "43683-2": "Geriatric Use",
        }

        # Find all sections
        for section in root.findall(".//spl:section", ns):
            # Try to get section code
            code_elem = section.find(".//spl:code", ns)
            section_code = code_elem.get('code', '') if code_elem is not None else ""

            # Get section title
            title_elem = section.find(".//spl:title", ns)
            section_title = title_elem.text if title_elem is not None and title_elem.text else ""

            # Get section text
            text_elem = section.find(".//spl:text", ns)
            section_text = self._extract_text_from_element(text_elem) if text_elem is not None else ""

            # Use mapped title or original title
            if section_code in section_mappings:
                key = section_mappings[section_code]
            elif section_title:
                key = section_title.strip()
            else:
                continue

            if section_text:
                sections[key] = section_text.strip()

        return sections

    def _extract_text_from_element(self, elem: ET.Element) -> str:
        """Extract all text from an XML element recursively"""
        text_parts = []

        if elem.text:
            text_parts.append(elem.text)

        for child in elem:
            child_text = self._extract_text_from_element(child)
            if child_text:
                text_parts.append(child_text)
            if child.tail:
                text_parts.append(child.tail)

        return " ".join(text_parts)

    def scrape_batch(self, setids: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape multiple drug labels

        Args:
            setids: List of SPL Set IDs

        Returns:
            List of drug label data
        """
        labels = []
        failed_count = 0
        max_failures = 50  # Stop if too many consecutive failures

        for i, setid in enumerate(setids):
            try:
                label_data = self.get_drug_label_xml(setid)

                if label_data and "error" not in label_data:
                    labels.append(label_data)
                    failed_count = 0  # Reset on success
                else:
                    failed_count += 1
                    logger.warning(f"Failed to get label for {setid}")

                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{len(setids)} labels ({len(labels)} successful)...")

                    # Save checkpoint
                    self.save_checkpoint({
                        "processed": i + 1,
                        "total": len(setids),
                        "successful": len(labels),
                        "last_setid": setid,
                    })

                    # Save intermediate results
                    if (i + 1) % 1000 == 0:
                        self.save_json(
                            labels,
                            f"dailymed_labels_batch_{i+1}.json",
                            metadata={
                                "batch": i + 1,
                                "count": len(labels),
                            },
                        )

                # Stop if too many consecutive failures
                if failed_count >= max_failures:
                    logger.error(f"Too many consecutive failures ({failed_count}). Stopping.")
                    break

            except Exception as e:
                logger.error(f"Error processing setid {setid}: {e}")
                failed_count += 1
                if failed_count >= max_failures:
                    break
                continue

        return labels

    def scrape(
        self,
        max_labels: int = 100000,  # Collect ALL labels (DailyMed has ~100K)
    ) -> List[Dict[str, Any]]:
        """
        Main scraping method - COLLECTS ALL AVAILABLE DATA

        Args:
            max_labels: Maximum labels to scrape (default: all ~100K labels)

        Returns:
            List of drug labels
        """
        # Load checkpoint if exists
        checkpoint = self.load_checkpoint()
        processed = checkpoint.get("processed", 0)

        if processed > 0:
            logger.info(f"Resuming from checkpoint: {processed} labels already processed")

        # Get ALL set IDs
        logger.info("=" * 60)
        logger.info("Fetching ALL drug set IDs from DailyMed...")
        logger.info("=" * 60)

        all_setids = self.get_all_setids_xml(max_results=max_labels)

        if not all_setids:
            logger.error("No set IDs retrieved. Aborting.")
            return []

        logger.info(f"Found {len(all_setids)} total drug labels to scrape")

        # Skip already processed
        setids_to_process = all_setids[processed:]

        logger.info(f"Processing {len(setids_to_process)} labels (skipping {processed})...")

        # Scrape all labels
        logger.info("=" * 60)
        logger.info("Scraping drug labels...")
        logger.info("=" * 60)

        labels = self.scrape_batch(setids_to_process)

        # Save all labels
        logger.info("Saving complete dataset...")

        self.save_json(
            labels,
            "dailymed_all_labels.json",
            metadata={
                "source": "DailyMed",
                "total_labels": len(labels),
                "total_available": len(all_setids),
                "processed": processed + len(labels),
            },
        )

        logger.info(f"Successfully scraped {len(labels)} drug labels")

        return labels


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    scraper = DailyMedScraper()

    # Scrape ALL drug labels
    labels = scraper.run()

    print(f"\n✅ Scraped {len(labels)} drug labels from DailyMed")
