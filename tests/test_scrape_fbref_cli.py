"""Tests for scrape_fbref CLI script."""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from pathlib import Path


def test_cli_help_displays():
    """Test that --help flag works."""
    with patch('sys.argv', ['scrape_fbref.py', '--help']):
        with pytest.raises(SystemExit) as exc_info:
            from src.scraping import scrape_fbref
            scrape_fbref.main()
        assert exc_info.value.code == 0


def test_validate_season_format_valid():
    """Test validation of valid season formats."""
    from src.scraping.scrape_fbref import validate_season_format
    
    start, end = validate_season_format("2023-2024")
    assert start == 2023
    assert end == 2024
    
    start, end = validate_season_format("2017-2026")
    assert start == 2017
    assert end == 2026


def test_validate_season_format_invalid():
    """Test validation rejects invalid season formats."""
    from src.scraping.scrape_fbref import validate_season_format
    
    # Invalid format - no dash
    with pytest.raises(ValueError, match="Invalid season format"):
        validate_season_format("20232024")
    
    # Invalid format - not numeric
    with pytest.raises(ValueError, match="Years must be numeric"):
        validate_season_format("abc-def")
    
    # Invalid range - start > end
    with pytest.raises(ValueError, match="Start year must be <= end year"):
        validate_season_format("2025-2023")
    
    # Invalid year range
    with pytest.raises(ValueError, match="Years should be between 2000-2100"):
        validate_season_format("1990-2000")


def test_estimate_execution_time():
    """Test execution time estimation."""
    from src.scraping.scrape_fbref import estimate_execution_time
    
    # 2 seasons, 1.0s delay
    time = estimate_execution_time(2023, 2024, 1.0)
    assert time == 2.0
    
    # 10 seasons, 2.0s delay
    time = estimate_execution_time(2017, 2026, 2.0)
    assert time == 20.0


def test_cli_with_valid_arguments(tmp_path):
    """Test CLI execution with valid arguments (mocked)."""
    # Mock all the components
    with patch('src.scraping.scrape_fbref.ConfigParser') as mock_config, \
         patch('src.scraping.scrape_fbref.RateLimiter') as mock_rate, \
         patch('src.scraping.scrape_fbref.CacheManager') as mock_cache, \
         patch('src.scraping.scrape_fbref.DataValidator') as mock_validator, \
         patch('src.scraping.scrape_fbref.CSVExporter') as mock_exporter, \
         patch('src.scraping.scrape_fbref.FBrefScraper') as mock_scraper:
        
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.load_team_mapping.return_value = {}
        mock_config_instance.load_selectors.return_value = {'fbref': {}}
        mock_config.return_value = mock_config_instance
        
        mock_validator_instance = Mock()
        mock_validator_instance.warnings = []
        mock_validator.return_value = mock_validator_instance
        
        # Mock scraper run to return sample data
        sample_df = pd.DataFrame({
            'Date': ['2023-08-12'],
            'Season': ['2324'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [2.5],
            'Away_xG': [1.3]
        })
        mock_scraper_instance = Mock()
        mock_scraper_instance.run.return_value = sample_df
        mock_scraper.return_value = mock_scraper_instance
        
        # Mock exporter
        mock_exporter_instance = Mock()
        mock_exporter_instance.export_fbref.return_value = str(tmp_path / "test_output.csv")
        mock_exporter.return_value = mock_exporter_instance
        
        # Run CLI
        with patch('sys.argv', ['scrape_fbref.py', '--seasons', '2023-2024', '--delay', '0.1']):
            from src.scraping import scrape_fbref
            
            with pytest.raises(SystemExit) as exc_info:
                scrape_fbref.main()
            
            # Should exit with success
            assert exc_info.value.code == 0
            
            # Verify scraper was called
            mock_scraper_instance.run.assert_called_once()
            mock_exporter_instance.export_fbref.assert_called_once()


def test_cli_missing_required_argument():
    """Test that CLI fails when required --seasons argument is missing."""
    with patch('sys.argv', ['scrape_fbref.py']):
        with pytest.raises(SystemExit) as exc_info:
            from src.scraping import scrape_fbref
            scrape_fbref.parse_arguments()
        assert exc_info.value.code == 2  # argparse error code


def test_cli_force_refresh_flag():
    """Test that force-refresh flag is parsed correctly."""
    with patch('sys.argv', ['scrape_fbref.py', '--seasons', '2023-2024', '--force-refresh']):
        from src.scraping import scrape_fbref
        args = scrape_fbref.parse_arguments()
        assert args.force_refresh is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
