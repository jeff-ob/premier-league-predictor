"""Base scraper abstract class providing common scraping infrastructure.

This module provides the BaseScraper abstract class that implements:
- HTTP fetching with caching and retry logic
- Rate limiting integration
- Logging setup with timestamped files
- Error handling for HTTP status codes
- Main execution orchestration

Implements: Requirements 3.1, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd
import requests
from time import sleep
import logging
from pathlib import Path
from datetime import datetime


class BaseScraper(ABC):
    """Abstract base class for web scrapers.
    
    Provides common infrastructure for scraping operations including:
    - Rate limiting
    - Caching with CacheManager
    - Data validation with DataValidator
    - Retry logic with exponential backoff
    - Structured logging
    
    Subclasses must implement:
    - build_urls(): Generate list of URLs to scrape
    - parse_page(): Parse HTML content into structured data
    
    Attributes:
        rate_limiter: RateLimiter instance for controlling request delays
        cache_manager: CacheManager instance for HTML caching
        validator: DataValidator instance for data validation
        config: Configuration dictionary
        logger: Logger instance for structured logging
    """
    
    def __init__(
        self,
        rate_limiter,
        cache_manager,
        validator,
        config: Dict[str, Any]
    ):
        """Initialize the base scraper.
        
        Args:
            rate_limiter: RateLimiter instance
            cache_manager: CacheManager instance
            validator: DataValidator instance
            config: Configuration dictionary with scraper-specific settings
        """
        self.rate_limiter = rate_limiter
        self.cache_manager = cache_manager
        self.validator = validator
        self.config = config
        self.logger = self._setup_logger()
        self.request_count = 0
        self.start_time = None
    
    @abstractmethod
    def build_urls(self, season_range: str) -> List[str]:
        """Generate list of URLs to scrape based on season range.
        
        Args:
            season_range: Season range string (e.g., "2017-2026")
            
        Returns:
            List of URLs to scrape
        """
        pass
    
    @abstractmethod
    def parse_page(self, html: str, url: str) -> pd.DataFrame:
        """Parse HTML content into structured data.
        
        Args:
            html: HTML content to parse
            url: Source URL (for logging/debugging)
            
        Returns:
            DataFrame with extracted data
        """
        pass
    
    def fetch_page(self, url: str, force_refresh: bool = False) -> str:
        """Fetch page with caching and retry logic.
        
        Implements:
        - Cache checking (unless force_refresh=True)
        - Rate limiting before HTTP requests
        - Retry logic with exponential backoff
        - Cache saving on successful fetch
        
        Args:
            url: URL to fetch
            force_refresh: If True, ignore cache and re-download
            
        Returns:
            HTML content as string
            
        Raises:
            Exception: If fetching fails after all retry attempts
        """
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_html = self.cache_manager.get(url)
            if cached_html:
                self.logger.debug(f"Cache hit: {url}")
                return cached_html
        
        # Apply rate limiting
        self.rate_limiter.wait()
        
        # Fetch with retry logic
        html = self._fetch_with_retry(url)
        
        # Save to cache
        self.cache_manager.save(url, html)
        
        # Increment request counter
        self.request_count += 1
        
        return html
    
    def _fetch_with_retry(self, url: str, max_retries: int = 3) -> str:
        """Fetch URL with exponential backoff retry.
        
        Implements retry logic:
        - HTTP 200: Success, return content
        - HTTP 429/503: Wait 60s, then retry with exponential backoff
        - Other errors: Log and retry with exponential backoff (2^attempt seconds)
        - Max 3 attempts total
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts (default 3)
            
        Returns:
            HTML content as string
            
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    timeout=30
                )
                
                if response.status_code == 200:
                    self.logger.debug(f"Successfully fetched {url}")
                    return response.text
                
                elif response.status_code in [429, 503]:
                    # Rate limit or service unavailable - wait 60s
                    wait_time = 60 if attempt == 1 else 60 + (2 ** attempt)
                    self.logger.warning(
                        f"HTTP {response.status_code} for {url}, "
                        f"waiting {wait_time}s (attempt {attempt}/{max_retries})"
                    )
                    sleep(wait_time)
                
                else:
                    self.logger.error(
                        f"HTTP {response.status_code} for {url} "
                        f"(attempt {attempt}/{max_retries})"
                    )
                    if attempt < max_retries:
                        sleep(2 ** attempt)
                    else:
                        break
            
            except requests.exceptions.RequestException as e:
                self.logger.error(
                    f"Request failed for {url}: {e} "
                    f"(attempt {attempt}/{max_retries})"
                )
                if attempt < max_retries:
                    sleep(2 ** attempt)
        
        raise Exception(f"Failed to fetch {url} after {max_retries} attempts")
    
    def run(self, season_range: str, force_refresh: bool = False) -> pd.DataFrame:
        """Main execution method orchestrating the scraping process.
        
        Execution flow:
        1. Build list of URLs from season_range
        2. For each URL:
           - Fetch page (with cache/retry logic)
           - Parse HTML to DataFrame
           - Validate data
           - Accumulate results
        3. Log progress every 10 pages
        4. Return concatenated DataFrame
        
        Args:
            season_range: Season range string (e.g., "2017-2026")
            force_refresh: If True, ignore cache and re-download all pages
            
        Returns:
            DataFrame with all scraped and validated data
        """
        self.start_time = datetime.now()
        urls = self.build_urls(season_range)
        all_data = []
        
        self.logger.info(
            f"Starting scrape: {len(urls)} pages to process "
            f"(force_refresh={force_refresh})"
        )
        
        for i, url in enumerate(urls, 1):
            try:
                # Fetch and parse page
                html = self.fetch_page(url, force_refresh)
                df = self.parse_page(html, url)
                
                # Validate data
                if not df.empty:
                    validated_df = self.validator.validate(df)
                    if not validated_df.empty:
                        all_data.append(validated_df)
                
                # Log progress every 10 pages
                if i % 10 == 0:
                    self.logger.info(f"Processed {i}/{len(urls)} pages")
            
            except Exception as e:
                self.logger.error(f"Failed to process {url}: {e}")
                # Continue to next page instead of failing completely
                continue
        
        # Log final statistics
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        self.logger.info(
            f"Scraping complete: {len(urls)} pages processed, "
            f"{self.request_count} HTTP requests made, "
            f"{elapsed_time:.1f}s elapsed"
        )
        
        if not all_data:
            self.logger.warning("No valid data extracted from any page")
            return pd.DataFrame()
        
        return pd.concat(all_data, ignore_index=True)
    
    def _get_headers(self) -> Dict[str, str]:
        """Return HTTP headers with polite user agent.
        
        Returns:
            Dictionary with User-Agent header
        """
        return {
            'User-Agent': 'Mozilla/5.0 (research bot; contact@example.com)'
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logging with timestamped log files.
        
        Creates a logger that writes to both console and a timestamped file
        in the logs/ directory. Log file naming pattern:
        - logs/scraping_{source}_{timestamp}.log
        
        Returns:
            Configured logger instance
        """
        # Get source name from config or use class name
        source = self.config.get('source', self.__class__.__name__.lower())
        
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"scraping_{source}_{timestamp}.log"
        
        # Create logger
        logger = logging.getLogger(f"{source}_scraper")
        logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        logger.handlers = []
        
        # File handler (DEBUG level)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console handler (INFO level)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        logger.info(f"Logger initialized. Log file: {log_file}")
        
        return logger
    
    def _save_failed_html(self, html: str, url: str):
        """Save problematic HTML to file for manual inspection.
        
        Used when parsing fails for a page. Saves the HTML to
        data/external/failed_parses/{source}_{timestamp}.html
        
        Args:
            html: HTML content that failed to parse
            url: Source URL (included in filename if possible)
        """
        # Create failed_parses directory
        failed_dir = Path("data/external/failed_parses")
        failed_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        source = self.config.get('source', 'unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Try to extract meaningful identifier from URL
        url_hash = url.split('/')[-1][:20] if url else "unknown"
        filename = f"{source}_{timestamp}_{url_hash}.html"
        
        filepath = failed_dir / filename
        
        # Save HTML
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Source URL: {url} -->\n")
            f.write(html)
        
        self.logger.warning(f"Saved failed HTML to {filepath}")
