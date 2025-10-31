"""
Base scraper class with ethical scraping practices
Includes rate limiting, retry logic, and error handling
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from data.scrapers.utils.rate_limiter import AdaptiveRateLimiter

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Base class for all scrapers
    Implements ethical scraping practices and data persistence
    """

    def __init__(
        self,
        name: str,
        output_dir: str,
        user_agent: str = "LumenMedicalBot/1.0",
        requests_per_second: float = 1.0,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        """
        Initialize base scraper

        Args:
            name: Scraper name (used for logging and file naming)
            output_dir: Directory to save scraped data
            user_agent: User agent string
            requests_per_second: Rate limit (requests per second)
            max_retries: Maximum number of retries on failure
            timeout: Request timeout in seconds
        """
        self.name = name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.user_agent = user_agent
        self.timeout = timeout

        # Rate limiter
        self.rate_limiter = AdaptiveRateLimiter(
            initial_rps=requests_per_second,
            min_rps=0.1,
            max_rps=min(10.0, requests_per_second * 2),
        )

        # Session with retry logic
        self.session = self._create_session(max_retries)

        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_items": 0,
            "start_time": None,
            "end_time": None,
        }

        logger.info(f"Initialized {self.name} scraper")

    def _create_session(self, max_retries: int) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()

        # Retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=2,  # 2, 4, 8 seconds
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Default headers
        session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

        return session

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Make GET request with rate limiting and error handling

        Args:
            url: URL to request
            **kwargs: Additional arguments for requests.get()

        Returns:
            Response object

        Raises:
            requests.RequestException: On request failure
        """
        self.rate_limiter.acquire()
        self.stats["total_requests"] += 1

        try:
            logger.debug(f"GET {url}")
            response = self.session.get(url, timeout=self.timeout, **kwargs)
            response.raise_for_status()

            self.stats["successful_requests"] += 1
            self.rate_limiter.report_success()

            return response

        except requests.exceptions.HTTPError as e:
            self.stats["failed_requests"] += 1
            self.rate_limiter.report_error(e.response.status_code if e.response else None)
            logger.error(f"HTTP error for {url}: {e}")
            raise

        except requests.exceptions.RequestException as e:
            self.stats["failed_requests"] += 1
            self.rate_limiter.report_error()
            logger.error(f"Request error for {url}: {e}")
            raise

    def post(self, url: str, **kwargs) -> requests.Response:
        """Make POST request with rate limiting"""
        self.rate_limiter.acquire()
        self.stats["total_requests"] += 1

        try:
            logger.debug(f"POST {url}")
            response = self.session.post(url, timeout=self.timeout, **kwargs)
            response.raise_for_status()

            self.stats["successful_requests"] += 1
            self.rate_limiter.report_success()

            return response

        except requests.exceptions.RequestException as e:
            self.stats["failed_requests"] += 1
            self.rate_limiter.report_error()
            logger.error(f"POST error for {url}: {e}")
            raise

    def save_json(self, data: Any, filename: str, metadata: Optional[Dict] = None) -> Path:
        """
        Save data as JSON with metadata

        Args:
            data: Data to save
            filename: Output filename
            metadata: Optional metadata to include

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / filename

        output_data = {
            "metadata": {
                "scraper": self.name,
                "timestamp": datetime.utcnow().isoformat(),
                "source": metadata.get("source") if metadata else None,
                **(metadata or {}),
            },
            "data": data,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved data to {output_path}")
        return output_path

    def save_raw(self, content: bytes, filename: str) -> Path:
        """
        Save raw content (e.g., PDF, XML)

        Args:
            content: Raw bytes to save
            filename: Output filename

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / filename

        with open(output_path, "wb") as f:
            f.write(content)

        logger.info(f"Saved raw data to {output_path}")
        return output_path

    def load_checkpoint(self, checkpoint_file: str = "checkpoint.json") -> Dict:
        """
        Load scraping checkpoint to resume interrupted scraping

        Args:
            checkpoint_file: Checkpoint filename

        Returns:
            Checkpoint data
        """
        checkpoint_path = self.output_dir / checkpoint_file

        if checkpoint_path.exists():
            with open(checkpoint_path, "r") as f:
                checkpoint = json.load(f)
            logger.info(f"Loaded checkpoint from {checkpoint_path}")
            return checkpoint

        return {}

    def save_checkpoint(self, checkpoint_data: Dict, checkpoint_file: str = "checkpoint.json") -> None:
        """
        Save scraping checkpoint

        Args:
            checkpoint_data: Data to save
            checkpoint_file: Checkpoint filename
        """
        checkpoint_path = self.output_dir / checkpoint_file

        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint_data, f, indent=2)

        logger.debug(f"Saved checkpoint to {checkpoint_path}")

    def get_stats(self) -> Dict:
        """Get scraper statistics"""
        stats = self.stats.copy()

        if stats["start_time"] and stats["end_time"]:
            duration = stats["end_time"] - stats["start_time"]
            stats["duration_seconds"] = duration
            if duration > 0:
                stats["requests_per_second"] = stats["total_requests"] / duration
                stats["items_per_second"] = stats["total_items"] / duration

        stats["rate_limiter"] = self.rate_limiter.get_stats()

        return stats

    def print_stats(self) -> None:
        """Print scraping statistics"""
        stats = self.get_stats()

        print(f"\n{'='*60}")
        print(f"{self.name} Scraper Statistics")
        print(f"{'='*60}")
        print(f"Total Requests:      {stats['total_requests']}")
        print(f"Successful:          {stats['successful_requests']}")
        print(f"Failed:              {stats['failed_requests']}")
        print(f"Total Items:         {stats['total_items']}")

        if "duration_seconds" in stats:
            print(f"Duration:            {stats['duration_seconds']:.2f}s")
            print(f"Requests/sec:        {stats.get('requests_per_second', 0):.2f}")
            print(f"Items/sec:           {stats.get('items_per_second', 0):.2f}")

        print(f"{'='*60}\n")

    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method (to be implemented by subclasses)

        Returns:
            List of scraped items
        """
        pass

    def run(self) -> List[Dict[str, Any]]:
        """
        Run the scraper with timing and error handling

        Returns:
            List of scraped items
        """
        logger.info(f"Starting {self.name} scraper")
        self.stats["start_time"] = time.time()

        try:
            results = self.scrape()
            self.stats["total_items"] = len(results)
            logger.info(f"Successfully scraped {len(results)} items")
            return results

        except KeyboardInterrupt:
            logger.warning("Scraping interrupted by user")
            raise

        except Exception as e:
            logger.error(f"Scraping failed: {e}", exc_info=True)
            raise

        finally:
            self.stats["end_time"] = time.time()
            self.print_stats()
            self.session.close()
