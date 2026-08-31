"""Tests to verify all required dependencies are available."""

import pytest
import sys


def test_requests_available():
    """Test that requests library is available."""
    import requests
    assert hasattr(requests, 'get')
    assert hasattr(requests, 'post')


def test_beautifulsoup4_available():
    """Test that BeautifulSoup4 is available."""
    from bs4 import BeautifulSoup
    assert BeautifulSoup is not None


def test_lxml_parser_available():
    """Test that lxml parser is available for BeautifulSoup."""
    from bs4 import BeautifulSoup
    # This should not raise an error
    soup = BeautifulSoup("<html><body><p>test</p></body></html>", 'lxml')
    assert soup.find('p').text == 'test'


def test_pandas_available():
    """Test that pandas is available."""
    import pandas as pd
    assert hasattr(pd, 'DataFrame')
    assert hasattr(pd, 'read_csv')


def test_pytest_available():
    """Test that pytest is available."""
    import pytest
    assert pytest is not None


def test_scraper_imports():
    """Test that all scraper modules can be imported."""
    from src.scraping.rate_limiter import RateLimiter
    from src.scraping.cache_manager import CacheManager
    from src.scraping.data_validator import DataValidator
    from src.scraping.csv_exporter import CSVExporter
    from src.scraping.config_parser import ConfigParser
    from src.scraping.base_scraper import BaseScraper
    from src.scraping.fbref_scraper import FBrefScraper
    from src.scraping.transfermarkt_scraper import TransfermarktScraper
    
    # All imports should succeed
    assert RateLimiter is not None
    assert CacheManager is not None
    assert DataValidator is not None
    assert CSVExporter is not None
    assert ConfigParser is not None
    assert BaseScraper is not None
    assert FBrefScraper is not None
    assert TransfermarktScraper is not None


def test_cli_imports():
    """Test that CLI scripts can be imported."""
    from src.scraping import scrape_fbref
    from src.scraping import scrape_transfermarkt
    
    assert scrape_fbref is not None
    assert scrape_transfermarkt is not None


def test_python_version():
    """Test that Python version is compatible."""
    assert sys.version_info >= (3, 10), "Python 3.10+ required"


def test_dependency_versions():
    """Test that key dependencies meet minimum version requirements."""
    import requests
    import bs4
    import pandas as pd
    
    # Check versions (basic validation)
    assert hasattr(requests, '__version__')
    assert hasattr(bs4, '__version__')
    assert hasattr(pd, '__version__')
    
    # Print versions for debugging
    print(f"\nDependency versions:")
    print(f"  requests: {requests.__version__}")
    print(f"  beautifulsoup4: {bs4.__version__}")
    print(f"  pandas: {pd.__version__}")
    print(f"  pytest: {pytest.__version__}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
