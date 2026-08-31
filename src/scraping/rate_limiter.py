"""Rate limiter component for controlling request delays.

This module implements rate limiting to respect website terms of service
and avoid IP bans.

Implements: Requirement 3.1, 3.2
"""

import time
from threading import Lock


class RateLimiter:
    """Controls the delay between consecutive HTTP requests.
    
    This class implements thread-safe rate limiting with configurable delay
    to ensure responsible web scraping practices.
    
    Attributes:
        delay (float): Minimum delay in seconds between consecutive requests
        last_request_time (float): Timestamp of the last request
        lock (Lock): Thread lock for thread-safe operation
    
    Example:
        >>> limiter = RateLimiter(delay_seconds=1.5)
        >>> limiter.wait()  # Waits if needed before making next request
        >>> # Make HTTP request here
    """
    
    def __init__(self, delay_seconds: float = 1.0):
        """Initialize the RateLimiter.
        
        Args:
            delay_seconds (float): Minimum delay in seconds between requests.
                                  Default is 1.0 second.
        
        Raises:
            ValueError: If delay_seconds is negative
        """
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be non-negative")
        
        self.delay = delay_seconds
        self.last_request_time = 0.0
        self.lock = Lock()
    
    def wait(self):
        """Apply rate limiting delay before next request.
        
        This method ensures that at least `delay` seconds have passed since
        the last request. If not enough time has passed, it will sleep for
        the remaining duration.
        
        Thread-safe: Multiple threads can call this method safely.
        """
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.delay:
                sleep_time = self.delay - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
