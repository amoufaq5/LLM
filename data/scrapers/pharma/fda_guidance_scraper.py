"""
FDA Guidance Documents scraper
Collects regulatory guidance for pharmaceutical manufacturing, GMP, quality, etc.

Source: https://www.fda.gov/regulatory-information/search-fda-guidance-documents
License: Public domain (U.S. government)
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from data.scrapers.utils.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class FDAGuidanceScraper(BaseScraper):
    """
    Scraper for FDA guidance documents
    """

    BASE_URL = "https://www.fda.gov"
    GUIDANCE_SEARCH_URL = f"{BASE_URL}/regulatory-information/search-fda-guidance-documents"

    # Guidance categories relevant to pharma
    CATEGORIES = [
        "drugs",
        "biologics",
        "combination-products",
        "manufacturing",
        "quality",
    ]

    def __init__(self, output_dir: str = "data/raw/fda_guidance"):
        """
        Initialize FDA guidance scraper

        Args:
            output_dir: Directory to save guidance documents
        """
        super().__init__(
            name="FDA_Guidance",
            output_dir=output_dir,
            user_agent="LumenMedicalBot/1.0 (research@lumen-medical.ai)",
            requests_per_second=1.0,  # Be respectful to FDA servers
        )

        # Create PDFs subdirectory
        self.pdf_dir = Path(output_dir) / "pdfs"
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

    def search_guidance(
        self,
        search_term: str = "",
        category: str = "",
        page: int = 0,
    ) -> Dict[str, Any]:
        """
        Search FDA guidance documents

        Args:
            search_term: Search query
            category: Guidance category
            page: Page number

        Returns:
            Search results with guidance list
        """
        params = {
            "s": search_term,
            "page": page,
        }

        if category:
            params["f[0]"] = f"audience:{category}"

        # Build query string
        query_parts = [f"{k}={v}" for k, v in params.items() if v]
        query_string = "&".join(query_parts)

        url = f"{self.GUIDANCE_SEARCH_URL}?{query_string}" if query_string else self.GUIDANCE_SEARCH_URL

        try:
            response = self.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            guidance_items = self._parse_guidance_list(soup)

            return {
                "search_term": search_term,
                "category": category,
                "page": page,
                "count": len(guidance_items),
                "items": guidance_items,
            }

        except Exception as e:
            logger.error(f"Error searching guidance (page {page}): {e}")
            return {"items": []}

    def _parse_guidance_list(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse guidance items from search results page"""
        guidance_items = []

        # Find guidance articles (adjust selector based on actual HTML structure)
        articles = soup.find_all("article", class_="fda-search-result")

        for article in articles:
            try:
                # Title and link
                title_elem = article.find("h3")
                if not title_elem:
                    continue

                link_elem = title_elem.find("a")
                if not link_elem:
                    continue

                title = link_elem.get_text(strip=True)
                relative_url = link_elem.get("href", "")
                url = urljoin(self.BASE_URL, relative_url) if relative_url else ""

                # Date
                date_elem = article.find("time")
                date = date_elem.get("datetime", "") if date_elem else ""

                # Description/snippet
                desc_elem = article.find("div", class_="fda-search-result__desc")
                description = desc_elem.get_text(strip=True) if desc_elem else ""

                # Document number
                doc_num_elem = article.find("div", class_="fda-document-number")
                doc_number = doc_num_elem.get_text(strip=True) if doc_num_elem else ""

                guidance_items.append({
                    "title": title,
                    "url": url,
                    "date": date,
                    "description": description,
                    "document_number": doc_number,
                })

            except Exception as e:
                logger.error(f"Error parsing guidance item: {e}")
                continue

        return guidance_items

    def get_guidance_details(self, guidance_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information from a guidance document page

        Args:
            guidance_url: URL to guidance document page

        Returns:
            Guidance details including PDF link
        """
        try:
            response = self.get(guidance_url)
            soup = BeautifulSoup(response.content, "html.parser")

            # Find PDF link
            pdf_link = None
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if href.endswith(".pdf") or "/media/" in href:
                    pdf_link = urljoin(self.BASE_URL, href)
                    break

            # Get full content
            content_div = soup.find("div", class_="main-content") or soup.find("main")
            content = content_div.get_text(strip=True) if content_div else ""

            # Extract metadata
            metadata = {}

            # Look for issued date
            date_patterns = [
                r"Date Issued:\s*(\d{1,2}/\d{1,2}/\d{4})",
                r"Issue Date:\s*(\d{1,2}/\d{1,2}/\d{4})",
            ]

            for pattern in date_patterns:
                match = re.search(pattern, content)
                if match:
                    metadata["issued_date"] = match.group(1)
                    break

            return {
                "url": guidance_url,
                "pdf_url": pdf_link,
                "content": content[:5000],  # First 5000 chars
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Error getting guidance details from {guidance_url}: {e}")
            return None

    def download_pdf(self, pdf_url: str, filename: str) -> Optional[Path]:
        """
        Download guidance PDF

        Args:
            pdf_url: URL to PDF file
            filename: Output filename

        Returns:
            Path to downloaded PDF
        """
        try:
            response = self.get(pdf_url)

            # Ensure .pdf extension
            if not filename.endswith(".pdf"):
                filename += ".pdf"

            pdf_path = self.pdf_dir / filename

            # Save PDF
            self.save_raw(response.content, f"pdfs/{filename}")

            logger.info(f"Downloaded PDF: {filename}")
            return pdf_path

        except Exception as e:
            logger.error(f"Error downloading PDF from {pdf_url}: {e}")
            return None

    def scrape_category(
        self,
        category: str,
        max_pages: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Scrape all guidance in a category

        Args:
            category: Guidance category
            max_pages: Maximum pages to scrape

        Returns:
            List of guidance documents
        """
        all_guidance = []
        page = 0

        logger.info(f"Scraping category: {category}")

        while page < max_pages:
            results = self.search_guidance(category=category, page=page)
            items = results.get("items", [])

            if not items:
                break

            logger.info(f"Page {page}: Found {len(items)} guidance documents")

            # Get details for each guidance
            for item in items:
                details = self.get_guidance_details(item["url"])

                if details:
                    item.update(details)

                    # Download PDF if available
                    if details.get("pdf_url"):
                        # Create safe filename
                        doc_num = item.get("document_number", "").replace("/", "-")
                        safe_title = re.sub(r'[^\w\-_]', '_', item["title"][:50])
                        filename = f"{doc_num}_{safe_title}.pdf" if doc_num else f"{safe_title}.pdf"

                        pdf_path = self.download_pdf(details["pdf_url"], filename)
                        item["pdf_path"] = str(pdf_path) if pdf_path else None

                all_guidance.append(item)

                # Save checkpoint
                if len(all_guidance) % 10 == 0:
                    self.save_checkpoint({
                        "category": category,
                        "page": page,
                        "total_documents": len(all_guidance),
                    })

            page += 1

        return all_guidance

    def scrape(
        self,
        categories: Optional[List[str]] = None,
        search_terms: Optional[List[str]] = None,
        max_pages_per_category: int = 5,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Main scraping method

        Args:
            categories: Categories to scrape (uses defaults if None)
            search_terms: Additional search terms
            max_pages_per_category: Max pages per category

        Returns:
            Dictionary of guidance documents by category
        """
        all_guidance = {}

        # Use default categories if none provided
        if categories is None:
            categories = self.CATEGORIES

        # Scrape each category
        for category in categories:
            guidance_list = self.scrape_category(category, max_pages=max_pages_per_category)
            all_guidance[category] = guidance_list

            # Save category results
            self.save_json(
                guidance_list,
                f"fda_guidance_{category}.json",
                metadata={
                    "category": category,
                    "count": len(guidance_list),
                },
            )

        # Additional search terms (GMP, validation, etc.)
        if search_terms is None:
            search_terms = [
                "GMP",
                "Good Manufacturing Practice",
                "validation",
                "quality systems",
                "pharmaceutical quality",
                "CGMP",
                "process validation",
                "cleaning validation",
            ]

        for search_term in search_terms:
            logger.info(f"Searching for: {search_term}")
            guidance_list = []

            for page in range(max_pages_per_category):
                results = self.search_guidance(search_term=search_term, page=page)
                items = results.get("items", [])

                if not items:
                    break

                for item in items:
                    details = self.get_guidance_details(item["url"])
                    if details:
                        item.update(details)
                        guidance_list.append(item)

            if guidance_list:
                safe_term = re.sub(r'[^\w\-_]', '_', search_term)
                self.save_json(
                    guidance_list,
                    f"fda_guidance_search_{safe_term}.json",
                    metadata={
                        "search_term": search_term,
                        "count": len(guidance_list),
                    },
                )

                all_guidance[f"search_{search_term}"] = guidance_list

        # Save all guidance
        total_docs = sum(len(docs) for docs in all_guidance.values())

        self.save_json(
            all_guidance,
            "fda_guidance_all.json",
            metadata={
                "total_documents": total_docs,
                "categories": list(all_guidance.keys()),
            },
        )

        return all_guidance


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    scraper = FDAGuidanceScraper()

    # Scrape FDA guidance
    guidance = scraper.run()

    total = sum(len(docs) for docs in guidance.values())
    print(f"\nScraped {total} FDA guidance documents")
    print(f"Categories: {list(guidance.keys())}")
