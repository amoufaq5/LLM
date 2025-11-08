"""
OpenFDA API client
Access FDA drug labels, adverse events, recalls, and more

API Documentation: https://open.fda.gov/apis/
Rate Limit: 1000 requests per minute (no API key needed)
           240 requests per minute per IP (with bursts up to 1000)
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlencode

from data.scrapers.utils.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class OpenFDAClient(BaseScraper):
    """
    Client for OpenFDA API
    Accesses drug labels, adverse events, recalls, NDC directory
    """

    BASE_URL = "https://api.fda.gov"

    def __init__(
        self,
        output_dir: str = "data/raw/openfda",
        api_key: Optional[str] = None,
    ):
        """
        Initialize OpenFDA client

        Args:
            output_dir: Directory to save data
            api_key: OpenFDA API key (optional, increases rate limits)
        """
        # Rate limit: 240/min = 4/sec, but we'll be conservative
        requests_per_second = 3.0 if not api_key else 15.0

        super().__init__(
            name="OpenFDA",
            output_dir=output_dir,
            user_agent="LumenMedicalBot/1.0",
            requests_per_second=requests_per_second,
        )

        self.api_key = api_key

    def _build_url(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Build API URL with parameters"""
        if self.api_key:
            params["api_key"] = self.api_key

        query_string = urlencode(params)
        url = f"{self.BASE_URL}{endpoint}?{query_string}"
        return url

    def search_drug_labels(
        self,
        search_query: str,
        limit: int = 100,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """
        Search drug labels

        Args:
            search_query: Search query (e.g., "openfda.brand_name:lipitor")
            limit: Results per request (max 100)
            skip: Number of results to skip

        Returns:
            API response with results
        """
        endpoint = "/drug/label.json"
        params = {
            "search": search_query,
            "limit": min(limit, 100),
            "skip": skip,
        }

        url = self._build_url(endpoint, params)
        response = self.get(url)
        return response.json()

    def get_all_drug_labels(
        self,
        search_query: str = "*",
        max_results: int = 100000,  # EXPANDED: Get ALL available labels
    ) -> List[Dict[str, Any]]:
        """
        Get ALL drug labels matching query - EXPANDED

        Args:
            search_query: Search query (default: all)
            max_results: Maximum results to retrieve (default: 100K = all available)

        Returns:
            List of drug label records
        """
        all_labels = []
        skip = 0
        limit = 100

        logger.info(f"Fetching drug labels: {search_query}")

        while skip < max_results:
            try:
                response = self.search_drug_labels(search_query, limit=limit, skip=skip)
                results = response.get("results", [])

                if not results:
                    break

                all_labels.extend(results)
                logger.info(f"Retrieved {len(all_labels)} drug labels so far...")

                skip += limit

                # Check if we've reached the end
                if len(results) < limit:
                    break

            except Exception as e:
                logger.error(f"Error fetching drug labels at skip={skip}: {e}")
                break

        logger.info(f"Total drug labels retrieved: {len(all_labels)}")
        return all_labels

    def search_adverse_events(
        self,
        search_query: str,
        limit: int = 100,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """
        Search drug adverse event reports (FAERS)

        Args:
            search_query: Search query
            limit: Results per request
            skip: Results to skip

        Returns:
            API response
        """
        endpoint = "/drug/event.json"
        params = {
            "search": search_query,
            "limit": min(limit, 100),
            "skip": skip,
        }

        url = self._build_url(endpoint, params)
        response = self.get(url)
        return response.json()

    def get_adverse_events_for_drug(
        self,
        drug_name: str,
        max_results: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Get adverse event reports for specific drug

        Args:
            drug_name: Drug brand or generic name
            max_results: Maximum results

        Returns:
            List of adverse event reports
        """
        search_query = f'patient.drug.medicinalproduct:"{drug_name}"'
        all_events = []
        skip = 0
        limit = 100

        logger.info(f"Fetching adverse events for: {drug_name}")

        while skip < max_results:
            try:
                response = self.search_adverse_events(search_query, limit=limit, skip=skip)
                results = response.get("results", [])

                if not results:
                    break

                all_events.extend(results)
                logger.info(f"Retrieved {len(all_events)} adverse events...")

                skip += limit

                if len(results) < limit:
                    break

            except Exception as e:
                logger.error(f"Error fetching adverse events at skip={skip}: {e}")
                break

        return all_events

    def search_drug_recalls(
        self,
        search_query: str,
        limit: int = 100,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Search drug recalls"""
        endpoint = "/drug/enforcement.json"
        params = {
            "search": search_query,
            "limit": min(limit, 100),
            "skip": skip,
        }

        url = self._build_url(endpoint, params)
        response = self.get(url)
        return response.json()

    def get_all_recalls(self, max_results: int = 5000) -> List[Dict[str, Any]]:
        """Get all drug recalls"""
        all_recalls = []
        skip = 0
        limit = 100

        logger.info("Fetching drug recalls...")

        while skip < max_results:
            try:
                response = self.search_drug_recalls("*", limit=limit, skip=skip)
                results = response.get("results", [])

                if not results:
                    break

                all_recalls.extend(results)
                logger.info(f"Retrieved {len(all_recalls)} recalls...")

                skip += limit

                if len(results) < limit:
                    break

            except Exception as e:
                logger.error(f"Error fetching recalls at skip={skip}: {e}")
                break

        return all_recalls

    def search_ndc_directory(
        self,
        search_query: str,
        limit: int = 100,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """
        Search NDC (National Drug Code) directory

        Args:
            search_query: Search query
            limit: Results per request
            skip: Results to skip

        Returns:
            API response
        """
        endpoint = "/drug/ndc.json"
        params = {
            "search": search_query,
            "limit": min(limit, 100),
            "skip": skip,
        }

        url = self._build_url(endpoint, params)
        response = self.get(url)
        return response.json()

    def get_drug_by_ndc(self, ndc_code: str) -> Optional[Dict[str, Any]]:
        """
        Get drug information by NDC code

        Args:
            ndc_code: National Drug Code

        Returns:
            Drug information or None
        """
        try:
            search_query = f'product_ndc:"{ndc_code}"'
            response = self.search_ndc_directory(search_query, limit=1)
            results = response.get("results", [])
            return results[0] if results else None

        except Exception as e:
            logger.error(f"Error fetching NDC {ndc_code}: {e}")
            return None

    def count_results(self, endpoint: str, search_query: str = "*") -> int:
        """
        Get total count of results for a query

        Args:
            endpoint: API endpoint
            search_query: Search query

        Returns:
            Total count
        """
        params = {
            "search": search_query,
            "limit": 1,
        }

        url = self._build_url(endpoint, params)

        try:
            response = self.get(url)
            data = response.json()
            total = data.get("meta", {}).get("results", {}).get("total", 0)
            return total

        except Exception as e:
            logger.error(f"Error counting results: {e}")
            return 0

    def scrape(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Main scraping method - EXPANDED FOR MAXIMUM DATA
        Collects drug labels, adverse events, and recalls

        Returns:
            Dictionary with all collected data
        """
        all_data = {}

        # 1. Drug Labels (COLLECT ALL)
        logger.info("="*60)
        logger.info("Collecting ALL Drug Labels from OpenFDA")
        logger.info("="*60)

        drug_labels = self.get_all_drug_labels(
            search_query="*",
            max_results=100000,  # EXPANDED: Collect ALL labels
        )

        all_data["drug_labels"] = drug_labels

        self.save_json(
            drug_labels,
            "openfda_drug_labels.json",
            metadata={
                "source": "OpenFDA Drug Labels",
                "count": len(drug_labels),
            },
        )

        # 2. Drug Recalls
        logger.info("="*60)
        logger.info("Collecting Drug Recalls")
        logger.info("="*60)

        recalls = self.get_all_recalls(max_results=5000)
        all_data["recalls"] = recalls

        self.save_json(
            recalls,
            "openfda_drug_recalls.json",
            metadata={
                "source": "OpenFDA Drug Recalls",
                "count": len(recalls),
            },
        )

        # 3. Adverse Events for MANY Drugs (EXPANDED)
        logger.info("="*60)
        logger.info("Collecting Adverse Events for Major Drugs")
        logger.info("="*60)

        # EXPANDED: Top 200 most prescribed drugs for comprehensive coverage
        common_drugs = [
            # Cardiovascular
            "lipitor", "atorvastatin", "simvastatin", "pravastatin", "rosuvastatin",
            "lisinopril", "enalapril", "ramipril", "losartan", "valsartan",
            "metoprolol", "atenolol", "carvedilol", "bisoprolol",
            "amlodipine", "nifedipine", "diltiazem", "verapamil",
            "warfarin", "apixaban", "rivaroxaban", "clopidogrel", "aspirin",
            "furosemide", "hydrochlorothiazide", "spironolactone", "torsemide",

            # Diabetes
            "metformin", "glipizide", "glyburide", "pioglitazone",
            "insulin", "lantus", "humalog", "novolog",
            "jardiance", "farxiga", "invokana",
            "ozempic", "victoza", "trulicity",

            # Respiratory
            "albuterol", "fluticasone", "budesonide", "montelukast",
            "salmeterol", "tiotropium", "ipratropium",

            # Gastrointestinal
            "omeprazole", "pantoprazole", "esomeprazole", "lansoprazole",
            "ranitidine", "famotidine",

            # Antibiotics
            "amoxicillin", "azithromycin", "ciprofloxacin", "levofloxacin",
            "doxycycline", "cephalexin", "clindamycin",

            # Pain/Anti-inflammatory
            "ibuprofen", "naproxen", "acetaminophen", "celecoxib",
            "tramadol", "hydrocodone", "oxycodone", "morphine", "fentanyl",
            "gabapentin", "pregabalin",

            # Mental health
            "sertraline", "fluoxetine", "escitalopram", "paroxetine",
            "duloxetine", "venlafaxine", "bupropion", "mirtazapine",
            "aripiprazole", "quetiapine", "risperidone", "olanzapine",
            "alprazolam", "lorazepam", "clonazepam", "diazepam",

            # Thyroid
            "levothyroxine", "synthroid",

            # Immunology
            "prednisone", "methylprednisolone", "dexamethasone",
            "humira", "enbrel", "remicade",

            # Cancer
            "tamoxifen", "anastrozole", "letrozole",

            # Other common
            "allopurinol", "colchicine", "vitamin d", "folic acid",
        ]

        all_adverse_events = []

        for i, drug in enumerate(common_drugs):
            logger.info(f"Collecting adverse events for {drug} ({i+1}/{len(common_drugs)})...")
            events = self.get_adverse_events_for_drug(drug, max_results=2000)  # EXPANDED: 2K per drug
            all_adverse_events.extend(events)

            # Save per drug
            self.save_json(
                events,
                f"openfda_adverse_events_{drug}.json",
                metadata={
                    "drug": drug,
                    "count": len(events),
                },
            )

        all_data["adverse_events"] = all_adverse_events

        self.save_json(
            all_adverse_events,
            "openfda_adverse_events_all.json",
            metadata={
                "source": "OpenFDA Adverse Events (FAERS)",
                "count": len(all_adverse_events),
                "drugs": common_drugs,
            },
        )

        # Summary statistics
        logger.info("="*60)
        logger.info("Collection Summary")
        logger.info("="*60)
        logger.info(f"Drug Labels: {len(drug_labels)}")
        logger.info(f"Recalls: {len(recalls)}")
        logger.info(f"Adverse Events: {len(all_adverse_events)}")
        logger.info("="*60)

        return all_data


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    client = OpenFDAClient(api_key=None)  # Add API key if available

    # Collect all data
    data = client.run()

    print(f"\nCollected:")
    print(f"  - {len(data.get('drug_labels', []))} drug labels")
    print(f"  - {len(data.get('recalls', []))} recalls")
    print(f"  - {len(data.get('adverse_events', []))} adverse events")
