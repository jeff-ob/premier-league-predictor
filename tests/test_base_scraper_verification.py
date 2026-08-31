"""Verification test for BaseScraper implementation.

This test verifies that the BaseScraper class is properly implemented
and works correctly with its dependencies.
"""

import pytest
from src.scraping.base_scraper import BaseScraper
from src.scraping.rate_limiter import RateLimiter
from src.scraping.cache_manager import CacheManager
from src.scraping.data_validator import DataValidator
import pandas as pd
from pathlib import Path


class TestScraper(BaseScraper):
    """Concrete implementation of BaseScraper for testing."""
    
    def build_urls(self, season_range: str) -> list:
        """Test implementation that returns a single test URL."""
        return ["http://example.com/test"]
    
    def parse_page(self, html: str, url: str) -> pd.DataFrame:
        """Test implementation that returns a simple DataFrame."""
        return pd.DataFrame({
            'Date': ['2023-08-15'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [1.5],
            'Away_xG': [2.0]
        })


def test_base_scraper_initialization():
    """Test that BaseScraper can be initialized with required components."""
    rate_limiter = RateLimiter(delay_seconds=0.1)
    cache_manager = CacheManager()
    validator = DataValidator(source='fbref')
    config = {'source': 'test'}
    
    scraper = TestScraper(rate_limiter, cache_manager, validator, config)
    
    assert scraper.rate_limiter is not None
    assert scraper.cache_manager is not None
    assert scraper.validator is not None
    assert scraper.config == {'source': 'test'}
    assert scraper.logger is not None
    assert scraper.request_count == 0


def test_base_scraper_build_urls():
    """Test that abstract method build_urls is properly defined."""
    rate_limiter = RateLimiter(delay_seconds=0.1)
    cache_manager = CacheManager()
    validator = DataValidator(source='fbref')
    config = {'source': 'test'}
    
    scraper = TestScraper(rate_limiter, cache_manager, validator, config)
    urls = scraper.build_urls("2023-2024")
    
    assert isinstance(urls, list)
    assert len(urls) == 1
    assert urls[0] == "http://example.com/test"


def test_base_scraper_parse_page():
    """Test that abstract method parse_page is properly defined."""
    rate_limiter = RateLimiter(delay_seconds=0.1)
    cache_manager = CacheManager()
    validator = DataValidator(source='fbref')
    config = {'source': 'test'}
    
    scraper = TestScraper(rate_limiter, cache_manager, validator, config)
    df = scraper.parse_page("<html>test</html>", "http://example.com/test")
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert 'HomeTeam' in df.columns
    assert 'AwayTeam' in df.columns


def test_base_scraper_get_headers():
    """Test that _get_headers returns proper User-Agent."""
    rate_limiter = RateLimiter(delay_seconds=0.1)
    cache_manager = CacheManager()
    validator = DataValidator(source='fbref')
    config = {'source': 'test'}
    
    scraper = TestScraper(rate_limiter, cache_manager, validator, config)
    headers = scraper._get_headers()
    
    assert 'User-Agent' in headers
    assert 'Mozilla' in headers['User-Agent']


def test_base_scraper_setup_logger():
    """Test that logger is properly configured."""
    rate_limiter = RateLimiter(delay_seconds=0.1)
    cache_manager = CacheManager()
    validator = DataValidator(source='fbref')
    config = {'source': 'test'}
    
    scraper = TestScraper(rate_limiter, cache_manager, validator, config)
    
    assert scraper.logger is not None
    assert scraper.logger.name == "test_scraper"
    assert len(scraper.logger.handlers) == 2  # File + Console handlers
    
    # Verify log file was created
    log_files = list(Path("logs").glob("scraping_test_*.log"))
    assert len(log_files) > 0


def test_base_scraper_save_failed_html():
    """Test that failed HTML is saved correctly."""
    rate_limiter = RateLimiter(delay_seconds=0.1)
    cache_manager = CacheManager()
    validator = DataValidator(source='fbref')
    config = {'source': 'test'}
    
    scraper = TestScraper(rate_limiter, cache_manager, validator, config)
    
    test_html = "<html><body>Failed parsing test</body></html>"
    test_url = "http://example.com/failed"
    
    scraper._save_failed_html(test_html, test_url)
    
    # Verify file was created in failed_parses directory
    failed_dir = Path("data/external/failed_parses")
    assert failed_dir.exists()
    
    failed_files = list(failed_dir.glob("test_*.html"))
    assert len(failed_files) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
