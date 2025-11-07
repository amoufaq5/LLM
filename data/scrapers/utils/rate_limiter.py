"""
Rate limiter for ethical web scraping
Ensures we don't overwhelm servers
"""

import time
from collections import deque
from threading import Lock
from typing import Optional


class RateLimiter:
    """
    Token bucket rate limiter
    Limits requests per second with burst capability
    """

    def __init__(
        self,
        requests_per_second: float = 1.0,
        burst_size: Optional[int] = None,
    ):
        """
        Initialize rate limiter

        Args:
            requests_per_second: Maximum requests per second
            burst_size: Maximum burst size (defaults to requests_per_second)
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.burst_size = burst_size or int(requests_per_second)

        self.tokens = float(self.burst_size)
        self.last_update = time.time()
        self.lock = Lock()

        # Track recent requests for statistics
        self.request_times: deque = deque(maxlen=1000)

    def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens, blocking if necessary

        Args:
            tokens: Number of tokens to acquire (default: 1)
        """
        with self.lock:
            while True:
                now = time.time()

                # Refill tokens based on time passed
                time_passed = now - self.last_update
                self.tokens = min(
                    self.burst_size,
                    self.tokens + time_passed * self.requests_per_second,
                )
                self.last_update = now

                # Check if we have enough tokens
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    self.request_times.append(now)
                    return

                # Calculate wait time
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.requests_per_second
                time.sleep(wait_time)

    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        with self.lock:
            now = time.time()
            recent_requests = [t for t in self.request_times if now - t < 60]

            return {
                "requests_last_minute": len(recent_requests),
                "requests_per_second": len(recent_requests) / 60.0,
                "available_tokens": self.tokens,
                "max_tokens": self.burst_size,
            }


class AdaptiveRateLimiter(RateLimiter):
    """
    Rate limiter that adapts based on server responses
    Reduces rate on errors, increases on success
    """

    def __init__(
        self,
        initial_rps: float = 1.0,
        min_rps: float = 0.1,
        max_rps: float = 10.0,
    ):
        super().__init__(requests_per_second=initial_rps)
        self.min_rps = min_rps
        self.max_rps = max_rps
        self.success_count = 0
        self.error_count = 0

    def report_success(self) -> None:
        """Report successful request"""
        with self.lock:
            self.success_count += 1
            # Increase rate after 10 successful requests
            if self.success_count >= 10:
                new_rps = min(self.max_rps, self.requests_per_second * 1.1)
                self.requests_per_second = new_rps
                self.min_interval = 1.0 / new_rps
                self.success_count = 0

    def report_error(self, status_code: Optional[int] = None) -> None:
        """Report failed request"""
        with self.lock:
            self.error_count += 1

            # Reduce rate on rate limit errors (429)
            if status_code == 429:
                new_rps = max(self.min_rps, self.requests_per_second * 0.5)
                self.requests_per_second = new_rps
                self.min_interval = 1.0 / new_rps
                self.error_count = 0
            # Reduce rate after 3 errors
            elif self.error_count >= 3:
                new_rps = max(self.min_rps, self.requests_per_second * 0.8)
                self.requests_per_second = new_rps
                self.min_interval = 1.0 / new_rps
                self.error_count = 0
