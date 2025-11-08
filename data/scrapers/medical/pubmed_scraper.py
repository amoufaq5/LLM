"""
PubMed Central (PMC) scraper using E-utilities API - FIXED
Collects medical research articles for training data
"""

import logging
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, quote

from data.scrapers.utils.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class PubMedScraper(BaseScraper):
    """
    Scraper for PubMed using NCBI E-utilities API

    API Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25500/
    Rate Limit: 3 requests/second without API key, 10 requests/second with key
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(
        self,
        output_dir: str = "data/raw/pubmed",
        api_key: Optional[str] = None,
        email: str = "research@lumen-medical.ai",
        requests_per_second: float = 2.5,
    ):
        """
        Initialize PubMed scraper

        Args:
            output_dir: Directory to save scraped data
            api_key: NCBI API key (optional but recommended)
            email: Your email (required by NCBI)
            requests_per_second: Rate limit
        """
        if api_key:
            requests_per_second = 9.0

        super().__init__(
            name="PubMed",
            output_dir=output_dir,
            user_agent=f"LumenMedicalBot/1.0 ({email})",
            requests_per_second=requests_per_second,
        )

        self.api_key = api_key
        self.email = email

    def _build_url(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Build API URL with parameters"""
        params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.BASE_URL}/{endpoint}.fcgi?{urlencode(params)}"
        return url

    def search(
        self,
        query: str,
        max_results: int = 10000,
        retstart: int = 0,
        retmax: int = 500,
    ) -> List[str]:
        """
        Search PubMed for articles matching query

        Args:
            query: Search query
            max_results: Maximum total results
            retstart: Starting index
            retmax: Results per request

        Returns:
            List of PubMed IDs (PMIDs)
        """
        all_ids = []

        logger.info(f"Searching PubMed: '{query}'")

        while retstart < max_results:
            params = {
                "db": "pubmed",
                "term": query,
                "retstart": retstart,
                "retmax": min(retmax, max_results - retstart),
                "retmode": "json",
                "usehistory": "y",
            }

            url = self._build_url("esearch", params)

            try:
                response = self.get(url)
                data = response.json()

                esearch_result = data.get("esearchresult", {})

                # Extract IDs
                id_list = esearch_result.get("idlist", [])
                all_ids.extend(id_list)

                # Get total count
                count = int(esearch_result.get("count", 0))

                logger.info(f"Query has {count} total results, retrieved {len(all_ids)} so far...")

                # Check if we got any results
                if count == 0:
                    logger.warning(f"No results for query: {query}")
                    break

                # Check if we're done
                if len(id_list) < retmax or len(all_ids) >= count:
                    logger.info(f"Retrieved all available results: {len(all_ids)}")
                    break

                retstart += retmax

            except Exception as e:
                logger.error(f"Search failed at offset {retstart}: {e}")
                break

        logger.info(f"Search completed: {len(all_ids)} articles found")
        return all_ids

    def fetch_article(self, pmid: str) -> Optional[Dict[str, Any]]:
        """Fetch single article by PMID"""
        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml",
        }

        url = self._build_url("efetch", params)

        try:
            response = self.get(url)
            article_data = self._parse_article_xml(response.content, pmid)
            return article_data

        except Exception as e:
            logger.error(f"Failed to fetch article {pmid}: {e}")
            return None

    def fetch_articles_batch(self, pmids: List[str], batch_size: int = 200) -> List[Dict[str, Any]]:
        """Fetch multiple articles in batches"""
        articles = []

        for i in range(0, len(pmids), batch_size):
            batch = pmids[i : i + batch_size]
            batch_str = ",".join(batch)

            params = {
                "db": "pubmed",
                "id": batch_str,
                "retmode": "xml",
            }

            url = self._build_url("efetch", params)

            try:
                response = self.get(url)
                batch_articles = self._parse_articles_xml(response.content)
                articles.extend(batch_articles)

                logger.info(f"Fetched {len(batch_articles)} articles (batch {i//batch_size + 1})")

            except Exception as e:
                logger.error(f"Failed to fetch batch at index {i}: {e}")
                continue

        return articles

    def _parse_article_xml(self, xml_content: bytes, pmid: str) -> Dict[str, Any]:
        """Parse single article from XML"""
        root = ET.fromstring(xml_content)
        article_elem = root.find(".//PubmedArticle")

        if article_elem is None:
            return {"pmid": pmid, "error": "Article not found"}

        return self._extract_article_data(article_elem)

    def _parse_articles_xml(self, xml_content: bytes) -> List[Dict[str, Any]]:
        """Parse multiple articles from XML"""
        root = ET.fromstring(xml_content)
        articles = []

        for article_elem in root.findall(".//PubmedArticle"):
            article_data = self._extract_article_data(article_elem)
            articles.append(article_data)

        return articles

    def _extract_article_data(self, article_elem: ET.Element) -> Dict[str, Any]:
        """Extract relevant data from article XML element"""
        try:
            # PMID
            pmid = article_elem.findtext(".//PMID", "")

            # Title
            title = article_elem.findtext(".//ArticleTitle", "")

            # Abstract
            abstract_texts = article_elem.findall(".//AbstractText")
            abstract = " ".join([elem.text or "" for elem in abstract_texts])

            # Authors
            authors = []
            for author in article_elem.findall(".//Author"):
                last_name = author.findtext("LastName", "")
                fore_name = author.findtext("ForeName", "")
                if last_name or fore_name:
                    authors.append(f"{fore_name} {last_name}".strip())

            # Journal
            journal = article_elem.findtext(".//Journal/Title", "")

            # Publication date
            pub_date = article_elem.find(".//PubDate")
            year = pub_date.findtext("Year", "") if pub_date is not None else ""
            month = pub_date.findtext("Month", "") if pub_date is not None else ""

            # MeSH terms
            mesh_terms = []
            for mesh in article_elem.findall(".//MeshHeading/DescriptorName"):
                if mesh.text:
                    mesh_terms.append(mesh.text)

            # Keywords
            keywords = []
            for keyword in article_elem.findall(".//Keyword"):
                if keyword.text:
                    keywords.append(keyword.text)

            # Article type
            pub_types = []
            for pub_type in article_elem.findall(".//PublicationType"):
                if pub_type.text:
                    pub_types.append(pub_type.text)

            return {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "journal": journal,
                "year": year,
                "month": month,
                "mesh_terms": mesh_terms,
                "keywords": keywords,
                "publication_types": pub_types,
            }

        except Exception as e:
            logger.error(f"Error extracting article data: {e}")
            return {"pmid": "", "error": str(e)}

    def scrape(
        self,
        queries: Optional[List[str]] = None,
        max_articles_per_query: int = 10000,
    ) -> List[Dict[str, Any]]:
        """
        Main scraping method - FIXED QUERIES

        Args:
            queries: List of search queries
            max_articles_per_query: Maximum articles per query

        Returns:
            List of article dictionaries
        """
        # FIXED: Simplified, working queries
        if queries is None:
            queries = [
                # General medical topics (broad)
                'medicine',
                'treatment',
                'therapy',
                'diagnosis',

                # Clinical trials
                '"Clinical Trial"[Publication Type]',
                '"Randomized Controlled Trial"[Publication Type]',

                # Reviews
                '"Review"[Publication Type] AND medicine',
                '"Systematic Review"[Publication Type]',

                # Major diseases
                'diabetes',
                'cancer',
                'cardiovascular disease',
                'heart disease',
                'hypertension',
                'stroke',
                'asthma',
                'COPD',
                'pneumonia',
                'infection',

                # Drugs and pharmacology
                'drug therapy',
                'pharmacology',
                'antibiotics',
                'chemotherapy',
                'immunotherapy',

                # Mental health
                'depression',
                'anxiety',
                'mental health',

                # Recent publications (last 5 years)
                '("2020"[Date - Publication] : "2025"[Date - Publication])',
            ]

        logger.info(f"Starting PubMed scraping with {len(queries)} queries")

        all_articles = []
        all_pmids = set()

        for i, query in enumerate(queries, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Query {i}/{len(queries)}: {query}")
            logger.info(f"{'='*60}")

            try:
                # Search for articles
                pmids = self.search(query, max_results=max_articles_per_query)

                if not pmids:
                    logger.warning(f"No results for query: {query}")
                    continue

                # Remove duplicates
                new_pmids = [pmid for pmid in pmids if pmid not in all_pmids]
                all_pmids.update(new_pmids)

                logger.info(f"Found {len(new_pmids)} new unique articles")

                # Fetch articles in batches
                articles = self.fetch_articles_batch(new_pmids)
                all_articles.extend(articles)

                # Save checkpoint
                self.save_checkpoint({
                    "completed_queries": i,
                    "total_queries": len(queries),
                    "total_articles": len(all_articles),
                    "last_query": query,
                })

                # Save batch results
                if articles:
                    self.save_json(
                        articles,
                        f"pubmed_batch_{i:02d}.json",
                        metadata={
                            "query": query,
                            "count": len(articles),
                            "batch_number": i,
                        },
                    )

                logger.info(f"Total unique articles so far: {len(all_articles)}")

            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
                continue

        # Save all results
        logger.info(f"\n{'='*60}")
        logger.info("SAVING FINAL RESULTS")
        logger.info(f"{'='*60}")

        self.save_json(
            all_articles,
            "pubmed_all_articles.json",
            metadata={
                "total_queries": len(queries),
                "total_articles": len(all_articles),
                "unique_pmids": len(all_pmids),
            },
        )

        return all_articles


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Test with simple query first
    scraper = PubMedScraper(
        api_key=None,  # Add your API key if available
        email="your-email@example.com",
    )

    # Test search
    logger.info("Testing PubMed search...")
    test_query = "diabetes"
    results = scraper.search(test_query, max_results=10)

    if results:
        logger.info(f"✅ Success! Found {len(results)} articles for test query")
        logger.info("Running full scraping...")
        articles = scraper.run()
        print(f"\n✅ Scraped {len(articles)} articles from PubMed")
    else:
        logger.error("❌ Test query returned 0 results. Check your connection or API key.")
