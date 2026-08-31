"""End-to-end integration tests for FBref and Transfermarkt scrapers.

This test suite verifies that both scrapers work correctly with all dependencies:
- RateLimiter integration
- CacheManager integration
- DataValidator integration
- CSVExporter integration
- Complete workflow: fetch → parse → validate → export

Tests use realistic test data to simulate actual scraping conditions.
"""

import pytest
import pandas as pd
from pathlib import Path
import json
import tempfile
import shutil
from datetime import datetime

from src.scraping.fbref_scraper import FBrefScraper
from src.scraping.transfermarkt_scraper import TransfermarktScraper
from src.scraping.rate_limiter import RateLimiter
from src.scraping.cache_manager import CacheManager
from src.scraping.data_validator import DataValidator
from src.scraping.csv_exporter import CSVExporter
from src.scraping.config_parser import ConfigParser


class TestFBrefScraperEndToEnd:
    """End-to-end tests for FBrefScraper."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_dir = tempfile.mkdtemp()
        cache_dir = Path(temp_dir) / "cache"
        output_dir = Path(temp_dir) / "output"
        config_dir = Path(temp_dir) / "config"
        
        cache_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        config_dir.mkdir(parents=True)
        
        yield {
            'base': temp_dir,
            'cache': str(cache_dir),
            'output': str(output_dir),
            'config': str(config_dir)
        }
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_files(self, temp_dirs):
        """Create test configuration files."""
        config_dir = Path(temp_dirs['config'])
        
        # Team mapping
        team_mapping = {
            "Brighton": "Brighton",
            "Man Utd": "Man United",
            "Spurs": "Tottenham"
        }
        with open(config_dir / "team_names_mapping.json", 'w') as f:
            json.dump(team_mapping, f)
        
        # Selectors
        selectors = {
            "fbref": {
                "xg_table": {
                    "primary": "table.stats_table tbody tr",
                    "fallback": "div.table_container table tr",
                    "generic": "table tr"
                },
                "xg_columns": {
                    "date": "td[data-stat='date']",
                    "home_team": "td[data-stat='home_team']",
                    "away_team": "td[data-stat='away_team']",
                    "home_xg": "td[data-stat='home_xg']",
                    "away_xg": "td[data-stat='away_xg']"
                }
            },
            "transfermarkt": {
                "squad_value": {
                    "primary": "table.items",
                    "fallback": "div.responsive-table table"
                },
                "team_name": {
                    "primary": "td:nth-child(2) a",
                    "fallback": "td:nth-child(2)"
                }
            }
        }
        with open(config_dir / "scraping_selectors.json", 'w') as f:
            json.dump(selectors, f)
        
        return temp_dirs['config']
    
    @pytest.fixture
    def fbref_components(self, temp_dirs, config_files):
        """Initialize all FBref scraper components."""
        # Load config
        config_parser = ConfigParser(config_files)
        team_mapping = config_parser.load_team_mapping()
        selectors = config_parser.load_selectors()
        
        # Create components
        rate_limiter = RateLimiter(delay_seconds=0.1)  # Fast for testing
        cache_manager = CacheManager(cache_dir=temp_dirs['cache'], ttl_days=30)
        validator = DataValidator(source='fbref')
        exporter = CSVExporter(output_dir=temp_dirs['output'])
        
        # Create config dict
        config = {
            'team_mapping': team_mapping,
            'fbref': selectors['fbref'],
            'source': 'fbref'
        }
        
        # Create scraper
        scraper = FBrefScraper(rate_limiter, cache_manager, validator, config)
        
        return {
            'scraper': scraper,
            'rate_limiter': rate_limiter,
            'cache_manager': cache_manager,
            'validator': validator,
            'exporter': exporter,
            'config': config
        }
    
    @pytest.fixture
    def sample_fbref_html(self):
        """Create realistic FBref HTML test data."""
        return """
        <!DOCTYPE html>
        <html>
        <body>
            <table class="stats_table" id="sched_2023-2024_9_1">
                <tbody>
                    <tr>
                        <td data-stat="date">2023-08-11</td>
                        <td data-stat="home_team">Brighton</td>
                        <td data-stat="away_team">Luton Town</td>
                        <td data-stat="home_xg">2.3</td>
                        <td data-stat="away_xg">0.8</td>
                    </tr>
                    <tr>
                        <td data-stat="date">2023-08-12</td>
                        <td data-stat="home_team">Arsenal</td>
                        <td data-stat="away_team">Chelsea</td>
                        <td data-stat="home_xg">1.9</td>
                        <td data-stat="away_xg">1.2</td>
                    </tr>
                    <tr>
                        <td data-stat="date">2023-08-13</td>
                        <td data-stat="home_team">Man Utd</td>
                        <td data-stat="away_team">Spurs</td>
                        <td data-stat="home_xg">2.7</td>
                        <td data-stat="away_xg">1.5</td>
                    </tr>
                </tbody>
            </table>
        </body>
        </html>
        """
    
    def test_fbref_instantiation_with_all_dependencies(self, fbref_components):
        """Test that FBrefScraper can be instantiated with all dependencies."""
        scraper = fbref_components['scraper']
        
        assert scraper is not None
        assert scraper.rate_limiter is not None
        assert scraper.cache_manager is not None
        assert scraper.validator is not None
        assert scraper.team_mapping is not None
        assert scraper.selectors is not None
    
    def test_fbref_url_generation(self, fbref_components):
        """Test URL generation for FBref scraper."""
        scraper = fbref_components['scraper']
        
        # Test valid season range
        urls = scraper.build_urls("2023-2024")
        assert len(urls) == 2  # 2023-2024 and 2024-2025
        assert all("fbref.com" in url for url in urls)
        assert "2023-2024" in urls[0]
        assert "2024-2025" in urls[1]
        
        # Test filtering of seasons before 2017
        urls = scraper.build_urls("2015-2017")
        assert len(urls) == 1  # Only 2017-2018 should be included
        assert "2017-2018" in urls[0]
    
    def test_fbref_html_parsing_realistic_data(self, fbref_components, sample_fbref_html):
        """Test HTML parsing with realistic test data."""
        scraper = fbref_components['scraper']
        
        # Parse the sample HTML
        df = scraper.parse_page(sample_fbref_html, "https://fbref.com/en/comps/9/2023-2024/schedule/")
        
        # Verify data extraction
        assert len(df) == 3
        assert list(df.columns) == ['Date', 'Season', 'HomeTeam', 'AwayTeam', 'Home_xG', 'Away_xG']
        
        # Verify first row
        assert df.iloc[0]['Date'] == '2023-08-11'
        assert df.iloc[0]['Season'] == '2324'
        assert df.iloc[0]['HomeTeam'] == 'Brighton'
        assert df.iloc[0]['AwayTeam'] == 'Luton Town'
        assert df.iloc[0]['Home_xG'] == 2.3
        assert df.iloc[0]['Away_xG'] == 0.8
        
        # Verify team name normalization
        assert df.iloc[2]['HomeTeam'] == 'Man United'  # Mapped from "Man Utd"
        assert df.iloc[2]['AwayTeam'] == 'Tottenham'  # Mapped from "Spurs"
    
    def test_fbref_validation_integration(self, fbref_components, sample_fbref_html):
        """Test integration with DataValidator."""
        scraper = fbref_components['scraper']
        validator = fbref_components['validator']
        
        # Parse HTML
        df = scraper.parse_page(sample_fbref_html, "https://fbref.com/en/comps/9/2023-2024/schedule/")
        
        # Validate
        validated_df = validator.validate(df)
        
        # All data should be valid
        assert len(validated_df) == 3
        assert len(validator.warnings) == 0
    
    def test_fbref_validation_rejects_invalid_data(self, fbref_components):
        """Test that DataValidator rejects invalid xG data."""
        validator = fbref_components['validator']
        
        # Create DataFrame with invalid data
        invalid_data = {
            'Date': ['2023-08-11', '2023-08-12', '2023-08-13'],
            'Season': ['2324', '2324', '2324'],
            'HomeTeam': ['Arsenal', 'Chelsea', 'Liverpool'],
            'AwayTeam': ['Brighton', 'Tottenham', 'Man United'],
            'Home_xG': [2.5, 25.0, 1.8],  # 25.0 is invalid (> 15.0)
            'Away_xG': [1.2, 1.5, -0.5]   # -0.5 is invalid (< 0.0)
        }
        df = pd.DataFrame(invalid_data)
        
        # Validate
        validated_df = validator.validate(df)
        
        # Should reject 2 invalid rows
        assert len(validated_df) == 1  # Only first row is valid
        assert len(validator.warnings) >= 2
    
    def test_fbref_cache_integration(self, fbref_components, sample_fbref_html, monkeypatch):
        """Test integration with CacheManager."""
        scraper = fbref_components['scraper']
        cache_manager = fbref_components['cache_manager']
        
        # Mock HTTP fetch to return sample HTML
        def mock_fetch(self, url, max_retries=3):
            return sample_fbref_html
        
        monkeypatch.setattr('src.scraping.base_scraper.BaseScraper._fetch_with_retry', mock_fetch)
        
        # First fetch - should call HTTP
        url = "https://fbref.com/en/comps/9/2023-2024/schedule/"
        html1 = scraper.fetch_page(url, force_refresh=False)
        
        # Verify HTML was cached
        cached_html = cache_manager.get(url)
        assert cached_html is not None
        assert "Brighton" in cached_html
        
        # Second fetch - should use cache
        html2 = scraper.fetch_page(url, force_refresh=False)
        assert html1 == html2
    
    def test_fbref_export_integration(self, fbref_components, sample_fbref_html):
        """Test integration with CSVExporter."""
        scraper = fbref_components['scraper']
        exporter = fbref_components['exporter']
        validator = fbref_components['validator']
        
        # Parse and validate
        df = scraper.parse_page(sample_fbref_html, "https://fbref.com/en/comps/9/2023-2024/schedule/")
        validated_df = validator.validate(df)
        
        # Export
        output_path = exporter.export_fbref(validated_df, "2023", "2024")
        
        # Verify file exists
        assert Path(output_path).exists()
        
        # Load and verify
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == ['Date', 'Season', 'HomeTeam', 'AwayTeam', 'Home_xG', 'Away_xG']
    
    def test_fbref_complete_workflow(self, fbref_components, sample_fbref_html, monkeypatch):
        """Test complete workflow: fetch → parse → validate → export."""
        scraper = fbref_components['scraper']
        exporter = fbref_components['exporter']
        
        # Mock HTTP fetch
        def mock_fetch(self, url, max_retries=3):
            return sample_fbref_html
        
        monkeypatch.setattr('src.scraping.base_scraper.BaseScraper._fetch_with_retry', mock_fetch)
        
        # Run scraper
        result_df = scraper.run("2023-2024", force_refresh=False)
        
        # Verify results
        assert len(result_df) > 0
        assert 'Home_xG' in result_df.columns
        assert 'Away_xG' in result_df.columns
        
        # Export
        output_path = exporter.export_fbref(result_df, "2023", "2024")
        assert Path(output_path).exists()


class TestTransfermarktScraperEndToEnd:
    """End-to-end tests for TransfermarktScraper."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_dir = tempfile.mkdtemp()
        cache_dir = Path(temp_dir) / "cache"
        output_dir = Path(temp_dir) / "output"
        config_dir = Path(temp_dir) / "config"
        
        cache_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        config_dir.mkdir(parents=True)
        
        yield {
            'base': temp_dir,
            'cache': str(cache_dir),
            'output': str(output_dir),
            'config': str(config_dir)
        }
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_files(self, temp_dirs):
        """Create test configuration files."""
        config_dir = Path(temp_dirs['config'])
        
        # Team mapping
        team_mapping = {
            "Manchester United": "Man United",
            "Tottenham Hotspur": "Tottenham",
            "Brighton & Hove Albion": "Brighton"
        }
        with open(config_dir / "team_names_mapping.json", 'w') as f:
            json.dump(team_mapping, f)
        
        # Selectors
        selectors = {
            "fbref": {
                "xg_table": {
                    "primary": "table.stats_table tbody tr",
                    "fallback": "div.table_container table tr",
                    "generic": "table tr"
                }
            },
            "transfermarkt": {
                "squad_value": {
                    "primary": "table.items",
                    "fallback": "div.responsive-table table"
                },
                "team_name": {
                    "primary": "td:nth-child(2) a",
                    "fallback": "td:nth-child(2)"
                }
            }
        }
        with open(config_dir / "scraping_selectors.json", 'w') as f:
            json.dump(selectors, f)
        
        return temp_dirs['config']
    
    @pytest.fixture
    def transfermarkt_components(self, temp_dirs, config_files):
        """Initialize all Transfermarkt scraper components."""
        # Load config
        config_parser = ConfigParser(config_files)
        team_mapping = config_parser.load_team_mapping()
        selectors = config_parser.load_selectors()
        
        # Create components
        rate_limiter = RateLimiter(delay_seconds=0.1)
        cache_manager = CacheManager(cache_dir=temp_dirs['cache'], ttl_days=30)
        validator = DataValidator(source='transfermarkt')
        exporter = CSVExporter(output_dir=temp_dirs['output'])
        
        # Create config dict
        config = {
            'team_mapping': team_mapping,
            'transfermarkt': selectors['transfermarkt'],
            'source': 'transfermarkt'
        }
        
        # Create scraper
        scraper = TransfermarktScraper(rate_limiter, cache_manager, validator, config)
        
        return {
            'scraper': scraper,
            'rate_limiter': rate_limiter,
            'cache_manager': cache_manager,
            'validator': validator,
            'exporter': exporter,
            'config': config
        }
    
    @pytest.fixture
    def sample_transfermarkt_html(self):
        """Create realistic Transfermarkt HTML test data."""
        return """
        <!DOCTYPE html>
        <html>
        <body>
            <table class="items">
                <tbody>
                    <tr>
                        <td></td>
                        <td><a title="Arsenal FC">Arsenal FC</a></td>
                        <td></td>
                        <td></td>
                        <td></td>
                        <td class="rechts hauptlink">850m €</td>
                    </tr>
                    <tr>
                        <td></td>
                        <td><a title="Manchester United">Manchester United</a></td>
                        <td></td>
                        <td></td>
                        <td></td>
                        <td class="rechts hauptlink">750.5m €</td>
                    </tr>
                    <tr>
                        <td></td>
                        <td><a title="Liverpool FC">Liverpool FC</a></td>
                        <td></td>
                        <td></td>
                        <td></td>
                        <td class="rechts hauptlink">1.2bn €</td>
                    </tr>
                    <tr>
                        <td></td>
                        <td><a title="Brighton & Hove Albion">Brighton & Hove Albion</a></td>
                        <td></td>
                        <td></td>
                        <td></td>
                        <td class="rechts hauptlink">450m €</td>
                    </tr>
                </tbody>
            </table>
        </body>
        </html>
        """
    
    def test_transfermarkt_instantiation_with_all_dependencies(self, transfermarkt_components):
        """Test that TransfermarktScraper can be instantiated with all dependencies."""
        scraper = transfermarkt_components['scraper']
        
        assert scraper is not None
        assert scraper.rate_limiter is not None
        assert scraper.cache_manager is not None
        assert scraper.validator is not None
        assert scraper.team_mapping is not None
        assert scraper.selectors is not None
    
    def test_transfermarkt_url_generation(self, transfermarkt_components):
        """Test URL generation for Transfermarkt scraper."""
        scraper = transfermarkt_components['scraper']
        
        # Test valid season range
        urls = scraper.build_urls("2023-2024")
        assert len(urls) == 2  # 2023 and 2024
        assert all("transfermarkt.com" in url for url in urls)
        assert "saison_id=2023" in urls[0]
        assert "saison_id=2024" in urls[1]
    
    def test_transfermarkt_html_parsing_realistic_data(self, transfermarkt_components, sample_transfermarkt_html):
        """Test HTML parsing with realistic test data."""
        scraper = transfermarkt_components['scraper']
        
        # Parse the sample HTML
        df = scraper.parse_page(
            sample_transfermarkt_html,
            "https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/plus/?saison_id=2023"
        )
        
        # Verify data extraction
        assert len(df) == 4
        assert list(df.columns) == ['Season', 'Team', 'Squad_Value']
        
        # Verify first row
        assert df.iloc[0]['Season'] == '2324'
        assert df.iloc[0]['Team'] == 'Arsenal FC'
        assert df.iloc[0]['Squad_Value'] == 850.0
        
        # Verify value conversion
        assert df.iloc[1]['Squad_Value'] == 750.5  # "750.5m €"
        assert df.iloc[2]['Squad_Value'] == 1200.0  # "1.2bn €" → 1200 millions
        
        # Verify team name normalization
        assert df.iloc[1]['Team'] == 'Man United'  # Mapped from "Manchester United"
        assert df.iloc[3]['Team'] == 'Brighton'  # Mapped from "Brighton & Hove Albion"
    
    def test_transfermarkt_squad_value_conversion(self, transfermarkt_components):
        """Test Squad_Value conversion from various formats."""
        scraper = transfermarkt_components['scraper']
        
        # Test various formats
        assert scraper._convert_squad_value("500m €") == 500.0
        assert scraper._convert_squad_value("45.5m €") == 45.5
        assert scraper._convert_squad_value("1.5bn €") == 1500.0
        assert scraper._convert_squad_value("2bn €") == 2000.0
        assert scraper._convert_squad_value("750.25m €") == 750.25
    
    def test_transfermarkt_validation_integration(self, transfermarkt_components, sample_transfermarkt_html):
        """Test integration with DataValidator."""
        scraper = transfermarkt_components['scraper']
        validator = transfermarkt_components['validator']
        
        # Parse HTML
        df = scraper.parse_page(
            sample_transfermarkt_html,
            "https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/plus/?saison_id=2023"
        )
        
        # Validate
        validated_df = validator.validate(df)
        
        # All data should be valid
        assert len(validated_df) == 4
        assert len(validator.warnings) == 0
    
    def test_transfermarkt_validation_rejects_invalid_data(self, transfermarkt_components):
        """Test that DataValidator rejects invalid Squad_Value data."""
        validator = transfermarkt_components['validator']
        
        # Create DataFrame with invalid data
        invalid_data = {
            'Season': ['2324', '2324', '2324'],
            'Team': ['Arsenal', 'Brighton', 'Chelsea'],
            'Squad_Value': [850.0, 5.0, 3000.0]  # 5.0 and 3000.0 are invalid
        }
        df = pd.DataFrame(invalid_data)
        
        # Validate
        validated_df = validator.validate(df)
        
        # Should reject invalid rows
        assert len(validated_df) < 3
        assert len(validator.warnings) >= 2
    
    def test_transfermarkt_cache_integration(self, transfermarkt_components, sample_transfermarkt_html, monkeypatch):
        """Test integration with CacheManager."""
        scraper = transfermarkt_components['scraper']
        cache_manager = transfermarkt_components['cache_manager']
        
        # Mock HTTP fetch
        def mock_fetch(self, url, max_retries=3):
            return sample_transfermarkt_html
        
        monkeypatch.setattr('src.scraping.base_scraper.BaseScraper._fetch_with_retry', mock_fetch)
        
        # First fetch - should call HTTP
        url = "https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/plus/?saison_id=2023"
        html1 = scraper.fetch_page(url, force_refresh=False)
        
        # Verify HTML was cached
        cached_html = cache_manager.get(url)
        assert cached_html is not None
        assert "Arsenal" in cached_html
        
        # Second fetch - should use cache
        html2 = scraper.fetch_page(url, force_refresh=False)
        assert html1 == html2
    
    def test_transfermarkt_export_integration(self, transfermarkt_components, sample_transfermarkt_html):
        """Test integration with CSVExporter."""
        scraper = transfermarkt_components['scraper']
        exporter = transfermarkt_components['exporter']
        validator = transfermarkt_components['validator']
        
        # Parse and validate
        df = scraper.parse_page(
            sample_transfermarkt_html,
            "https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/plus/?saison_id=2023"
        )
        validated_df = validator.validate(df)
        
        # Export
        output_path = exporter.export_transfermarkt(validated_df, "2023", "2024")
        
        # Verify file exists
        assert Path(output_path).exists()
        
        # Load and verify
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 4
        assert list(loaded_df.columns) == ['Season', 'Team', 'Squad_Value']
    
    def test_transfermarkt_complete_workflow(self, transfermarkt_components, sample_transfermarkt_html, monkeypatch):
        """Test complete workflow: fetch → parse → validate → export."""
        scraper = transfermarkt_components['scraper']
        exporter = transfermarkt_components['exporter']
        
        # Mock HTTP fetch
        def mock_fetch(self, url, max_retries=3):
            return sample_transfermarkt_html
        
        monkeypatch.setattr('src.scraping.base_scraper.BaseScraper._fetch_with_retry', mock_fetch)
        
        # Run scraper
        result_df = scraper.run("2023-2024", force_refresh=False)
        
        # Verify results
        assert len(result_df) > 0
        assert 'Squad_Value' in result_df.columns
        assert 'Team' in result_df.columns
        
        # Export
        output_path = exporter.export_transfermarkt(result_df, "2023", "2024")
        assert Path(output_path).exists()


class TestRateLimiterIntegration:
    """Test rate limiter integration with scrapers."""
    
    def test_rate_limiter_applies_delay(self):
        """Test that rate limiter applies delay between requests."""
        import time
        
        rate_limiter = RateLimiter(delay_seconds=0.2)
        
        # First request
        start_time = time.time()
        rate_limiter.wait()
        first_request_time = time.time()
        
        # Second request (should be delayed)
        rate_limiter.wait()
        second_request_time = time.time()
        
        # Verify delay
        delay = second_request_time - first_request_time
        assert delay >= 0.2, f"Expected delay >= 0.2s, got {delay}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
