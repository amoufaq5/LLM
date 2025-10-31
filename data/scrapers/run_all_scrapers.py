"""
Master script to run all data collection scrapers
Orchestrates data collection from all sources
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.scrapers.medical.dailymed_scraper import DailyMedScraper
from data.scrapers.medical.drugbank_parser import DrugBankParser
from data.scrapers.medical.openfda_client import OpenFDAClient
from data.scrapers.medical.pubmed_scraper import PubMedScraper
from data.scrapers.medical.rxnorm_client import RxNormClient
from data.scrapers.pharma.fda_guidance_scraper import FDAGuidanceScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("data/scrapers/scraping.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def main():
    """Run all scrapers"""

    logger.info("="*80)
    logger.info("LUMEN MEDICAL LLM - DATA COLLECTION")
    logger.info("="*80)

    scrapers_to_run = []

    # Ask user which scrapers to run
    print("\nAvailable scrapers:")
    print("1. PubMed (Medical literature)")
    print("2. OpenFDA (Drug labels, adverse events, recalls)")
    print("3. DailyMed (FDA-approved drug labels)")
    print("4. RxNorm (Drug name normalization)")
    print("5. DrugBank (Comprehensive drug database - requires manual download)")
    print("6. FDA Guidance (Regulatory documents)")
    print("7. ALL (Run all scrapers)")
    print("0. Exit")

    while True:
        choice = input("\nEnter scraper number (or 'done' to start): ").strip()

        if choice.lower() == "done":
            break
        elif choice == "0":
            return
        elif choice == "7":
            scrapers_to_run = ["1", "2", "3", "4", "6"]  # Skip DrugBank (manual)
            break
        elif choice in ["1", "2", "3", "4", "5", "6"]:
            if choice not in scrapers_to_run:
                scrapers_to_run.append(choice)
                print(f"Added scraper {choice}")
        else:
            print("Invalid choice")

    if not scrapers_to_run:
        print("No scrapers selected. Exiting.")
        return

    # Run selected scrapers
    results = {}

    # 1. PubMed
    if "1" in scrapers_to_run:
        logger.info("\n" + "="*80)
        logger.info("RUNNING: PubMed Scraper")
        logger.info("="*80)
        try:
            scraper = PubMedScraper()
            results["pubmed"] = scraper.run()
        except Exception as e:
            logger.error(f"PubMed scraper failed: {e}", exc_info=True)

    # 2. OpenFDA
    if "2" in scrapers_to_run:
        logger.info("\n" + "="*80)
        logger.info("RUNNING: OpenFDA Client")
        logger.info("="*80)
        try:
            client = OpenFDAClient()
            results["openfda"] = client.run()
        except Exception as e:
            logger.error(f"OpenFDA client failed: {e}", exc_info=True)

    # 3. DailyMed
    if "3" in scrapers_to_run:
        logger.info("\n" + "="*80)
        logger.info("RUNNING: DailyMed Scraper")
        logger.info("="*80)
        try:
            scraper = DailyMedScraper()
            results["dailymed"] = scraper.run()
        except Exception as e:
            logger.error(f"DailyMed scraper failed: {e}", exc_info=True)

    # 4. RxNorm
    if "4" in scrapers_to_run:
        logger.info("\n" + "="*80)
        logger.info("RUNNING: RxNorm Client")
        logger.info("="*80)
        try:
            client = RxNormClient()
            results["rxnorm"] = client.run()
        except Exception as e:
            logger.error(f"RxNorm client failed: {e}", exc_info=True)

    # 5. DrugBank (requires manual download)
    if "5" in scrapers_to_run:
        logger.info("\n" + "="*80)
        logger.info("RUNNING: DrugBank Parser")
        logger.info("="*80)
        print("\nDrugBank requires manual download:")
        print("1. Go to: https://go.drugbank.com/releases/latest")
        print("2. Create free account")
        print("3. Download 'All full database' XML file")
        print("4. Place at: data/raw/drugbank/full_database.xml")

        xml_path = input("\nEnter path to DrugBank XML (or press Enter to skip): ").strip()

        if xml_path and Path(xml_path).exists():
            try:
                parser = DrugBankParser()
                results["drugbank"] = parser.run()
            except Exception as e:
                logger.error(f"DrugBank parser failed: {e}", exc_info=True)
        else:
            logger.warning("Skipping DrugBank (file not found)")

    # 6. FDA Guidance
    if "6" in scrapers_to_run:
        logger.info("\n" + "="*80)
        logger.info("RUNNING: FDA Guidance Scraper")
        logger.info("="*80)
        try:
            scraper = FDAGuidanceScraper()
            results["fda_guidance"] = scraper.run()
        except Exception as e:
            logger.error(f"FDA Guidance scraper failed: {e}", exc_info=True)

    # Summary
    logger.info("\n" + "="*80)
    logger.info("DATA COLLECTION SUMMARY")
    logger.info("="*80)

    for scraper_name, data in results.items():
        if isinstance(data, list):
            logger.info(f"{scraper_name}: {len(data)} items")
        elif isinstance(data, dict):
            total = sum(len(v) if isinstance(v, list) else 1 for v in data.values())
            logger.info(f"{scraper_name}: {total} items")
        else:
            logger.info(f"{scraper_name}: completed")

    logger.info("="*80)
    logger.info("DATA COLLECTION COMPLETE")
    logger.info("="*80)

    print("\n✅ All selected scrapers completed!")
    print(f"📁 Data saved to: data/raw/")
    print(f"📋 Logs saved to: data/scrapers/scraping.log")


if __name__ == "__main__":
    main()
