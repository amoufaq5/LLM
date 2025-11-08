#!/usr/bin/env python3
"""
Quick test script to verify PubMed scraper is working
"""

import logging
import sys

# Add parent directory to path
sys.path.insert(0, '.')

from data.scrapers.medical.pubmed_scraper import PubMedScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

def test_pubmed():
    """Test PubMed scraper with simple query"""

    print("="*60)
    print("TESTING PUBMED SCRAPER")
    print("="*60)

    # Initialize scraper
    scraper = PubMedScraper(
        api_key=None,  # No API key needed for testing
        email="test@example.com",
    )

    # Show comprehensive coverage
    comprehensive_queries = scraper.get_comprehensive_disease_queries()
    print(f"\n📊 Comprehensive Disease Coverage: {len(comprehensive_queries)} diseases")
    print(f"   Expected total articles: {len(comprehensive_queries) * 10000:,} (10K per disease)")
    print(f"   After deduplication: ~500K-2M articles")

    # Test query
    test_query = "diabetes"

    print(f"\n1. Testing search for: '{test_query}'")
    print("-"*60)

    try:
        # Search for 10 articles
        pmids = scraper.search(test_query, max_results=10)

        if not pmids:
            print("❌ FAILED: No results returned")
            print("\nPossible issues:")
            print("  - No internet connection")
            print("  - PubMed API is down")
            print("  - Rate limiting")
            return False

        print(f"✅ SUCCESS: Found {len(pmids)} PMIDs")
        print(f"   Sample PMIDs: {pmids[:5]}")

        # Fetch 2 articles
        print(f"\n2. Fetching first 2 articles...")
        print("-"*60)

        articles = scraper.fetch_articles_batch(pmids[:2])

        if not articles:
            print("❌ FAILED: Could not fetch articles")
            return False

        print(f"✅ SUCCESS: Fetched {len(articles)} articles")

        # Show first article
        if articles:
            article = articles[0]
            print(f"\n3. Sample Article:")
            print("-"*60)
            print(f"   PMID: {article['pmid']}")
            print(f"   Title: {article['title'][:100]}...")
            print(f"   Abstract: {article['abstract'][:200]}...")
            print(f"   Authors: {', '.join(article['authors'][:3])}")
            print(f"   Journal: {article['journal']}")

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED - PUBMED SCRAPER IS WORKING!")
        print("="*60)
        print("\nYou can now run:")
        print("  python data/scrapers/medical/pubmed_scraper.py")
        print("  (This will collect 100K+ articles)")

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pubmed()
    sys.exit(0 if success else 1)
