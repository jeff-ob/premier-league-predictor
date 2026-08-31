"""
Unit tests for CSVExporter
Tests: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""

import pytest
import pandas as pd
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from src.scraping.csv_exporter import CSVExporter


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def csv_exporter(temp_output_dir):
    """Create a CSVExporter instance with temp directory."""
    return CSVExporter(output_dir=temp_output_dir)


@pytest.fixture
def sample_fbref_data():
    """Create sample FBref data for testing."""
    return pd.DataFrame({
        'Date': ['2023-08-15', '2023-08-12', '2023-08-20'],
        'Season': ['2324', '2324', '2324'],
        'HomeTeam': ['Arsenal', 'Chelsea', 'Liverpool'],
        'AwayTeam': ['Chelsea', 'Liverpool', 'Arsenal'],
        'Home_xG': [2.3, 1.5, 3.1],
        'Away_xG': [1.2, 2.0, 0.9]
    })


@pytest.fixture
def sample_transfermarkt_data():
    """Create sample Transfermarkt data for testing."""
    return pd.DataFrame({
        'Season': ['2324', '2223', '2324', '2223'],
        'Team': ['Liverpool', 'Arsenal', 'Arsenal', 'Liverpool'],
        'Squad_Value': [850.5, 780.0, 920.3, 800.0]
    })


class TestCSVExporter:
    """Test suite for CSVExporter class."""
    
    def test_init_creates_output_directory(self, temp_output_dir):
        """Test that initialization creates the output directory."""
        new_dir = Path(temp_output_dir) / "new_output"
        exporter = CSVExporter(output_dir=str(new_dir))
        
        assert new_dir.exists()
        assert new_dir.is_dir()
    
    def test_export_fbref_correct_columns(self, csv_exporter, sample_fbref_data, temp_output_dir):
        """Test FBref export contains correct columns in correct order.
        
        Requirements: 6.2
        """
        output_path = csv_exporter.export_fbref(sample_fbref_data, "2023", "2024")
        
        # Read exported CSV
        df = pd.read_csv(output_path)
        
        # Verify columns
        expected_columns = ['Date', 'Season', 'HomeTeam', 'AwayTeam', 'Home_xG', 'Away_xG']
        assert list(df.columns) == expected_columns
    
    def test_export_fbref_chronological_sorting(self, csv_exporter, sample_fbref_data, temp_output_dir):
        """Test FBref export is sorted chronologically by Date.
        
        Requirements: 6.5
        """
        output_path = csv_exporter.export_fbref(sample_fbref_data, "2023", "2024")
        
        # Read exported CSV
        df = pd.read_csv(output_path)
        
        # Verify sorting - dates should be in ascending order
        dates = pd.to_datetime(df['Date'])
        assert dates.is_monotonic_increasing
        
        # Verify specific order
        assert df.iloc[0]['Date'] == '2023-08-12'
        assert df.iloc[1]['Date'] == '2023-08-15'
        assert df.iloc[2]['Date'] == '2023-08-20'
    
    def test_export_fbref_filename_format(self, csv_exporter, sample_fbref_data, temp_output_dir):
        """Test FBref export filename follows correct format.
        
        Requirements: 6.1
        """
        output_path = csv_exporter.export_fbref(sample_fbref_data, "2017", "2026")
        
        expected_filename = "fbref_xg_2017_2026.csv"
        assert Path(output_path).name == expected_filename
    
    def test_export_fbref_date_format(self, csv_exporter, sample_fbref_data, temp_output_dir):
        """Test FBref export formats dates as YYYY-MM-DD strings.
        
        Requirements: 6.2
        """
        output_path = csv_exporter.export_fbref(sample_fbref_data, "2023", "2024")
        
        # Read exported CSV
        df = pd.read_csv(output_path)
        
        # Verify date format (should be string, not datetime)
        assert df['Date'].dtype == 'object'
        
        # Verify date format pattern
        for date_str in df['Date']:
            # Should be parseable as YYYY-MM-DD
            parsed = datetime.strptime(date_str, '%Y-%m-%d')
            assert parsed is not None
    
    def test_export_transfermarkt_correct_columns(self, csv_exporter, sample_transfermarkt_data, temp_output_dir):
        """Test Transfermarkt export contains correct columns in correct order.
        
        Requirements: 6.4
        """
        output_path = csv_exporter.export_transfermarkt(sample_transfermarkt_data, "2022", "2024")
        
        # Read exported CSV
        df = pd.read_csv(output_path)
        
        # Verify columns
        expected_columns = ['Season', 'Team', 'Squad_Value']
        assert list(df.columns) == expected_columns
    
    def test_export_transfermarkt_sorting(self, csv_exporter, sample_transfermarkt_data, temp_output_dir):
        """Test Transfermarkt export is sorted by Season then Team.
        
        Requirements: 6.5
        """
        output_path = csv_exporter.export_transfermarkt(sample_transfermarkt_data, "2022", "2024")
        
        # Read exported CSV
        df = pd.read_csv(output_path)
        
        # Convert Season to string for comparison (pandas may read as int)
        df['Season'] = df['Season'].astype(str)
        
        # Verify sorting by Season then Team
        assert df.iloc[0]['Season'] == '2223'
        assert df.iloc[0]['Team'] == 'Arsenal'
        
        assert df.iloc[1]['Season'] == '2223'
        assert df.iloc[1]['Team'] == 'Liverpool'
        
        assert df.iloc[2]['Season'] == '2324'
        assert df.iloc[2]['Team'] == 'Arsenal'
        
        assert df.iloc[3]['Season'] == '2324'
        assert df.iloc[3]['Team'] == 'Liverpool'
    
    def test_export_transfermarkt_filename_format(self, csv_exporter, sample_transfermarkt_data, temp_output_dir):
        """Test Transfermarkt export filename follows correct format.
        
        Requirements: 6.3
        """
        output_path = csv_exporter.export_transfermarkt(sample_transfermarkt_data, "2009", "2026")
        
        expected_filename = "transfermarkt_values_2009_2026.csv"
        assert Path(output_path).name == expected_filename
    
    def test_create_readme_with_fbref_only(self, csv_exporter, temp_output_dir):
        """Test README creation with only FBref information.
        
        Requirements: 6.6
        """
        fbref_info = {
            'filename': 'fbref_xg_2023_2024.csv',
            'scrape_date': '2024-01-15',
            'start_season': '2023',
            'end_season': '2024'
        }
        
        readme_path = csv_exporter.create_readme(fbref_info=fbref_info)
        
        # Verify file exists
        assert Path(readme_path).exists()
        
        # Read and verify content
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify key sections
        assert "# External Data Sources" in content
        assert "## FBref xG Data" in content
        assert "fbref_xg_2023_2024.csv" in content
        assert "FBref.com" in content
        assert "2024-01-15" in content
        assert "2023 to 2024" in content
        assert "Date" in content
        assert "Home_xG" in content
        assert "Away_xG" in content
    
    def test_create_readme_with_transfermarkt_only(self, csv_exporter, temp_output_dir):
        """Test README creation with only Transfermarkt information.
        
        Requirements: 6.6
        """
        transfermarkt_info = {
            'filename': 'transfermarkt_values_2022_2024.csv',
            'scrape_date': '2024-01-15',
            'start_season': '2022',
            'end_season': '2024'
        }
        
        readme_path = csv_exporter.create_readme(transfermarkt_info=transfermarkt_info)
        
        # Read and verify content
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify key sections
        assert "## Transfermarkt Squad Values" in content
        assert "transfermarkt_values_2022_2024.csv" in content
        assert "Transfermarkt.com" in content
        assert "Squad_Value" in content
        assert "millions €" in content
    
    def test_create_readme_with_both_sources(self, csv_exporter, temp_output_dir):
        """Test README creation with both FBref and Transfermarkt information.
        
        Requirements: 6.6
        """
        fbref_info = {
            'filename': 'fbref_xg_2023_2024.csv',
            'scrape_date': '2024-01-15',
            'start_season': '2023',
            'end_season': '2024'
        }
        
        transfermarkt_info = {
            'filename': 'transfermarkt_values_2023_2024.csv',
            'scrape_date': '2024-01-15',
            'start_season': '2023',
            'end_season': '2024'
        }
        
        readme_path = csv_exporter.create_readme(
            fbref_info=fbref_info,
            transfermarkt_info=transfermarkt_info
        )
        
        # Read and verify content
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify both sections exist
        assert "## FBref xG Data" in content
        assert "## Transfermarkt Squad Values" in content
        assert "fbref_xg_2023_2024.csv" in content
        assert "transfermarkt_values_2023_2024.csv" in content
    
    def test_create_readme_empty(self, csv_exporter, temp_output_dir):
        """Test README creation with no information (edge case).
        
        Requirements: 6.6
        """
        readme_path = csv_exporter.create_readme()
        
        # Verify file exists with basic structure
        assert Path(readme_path).exists()
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "# External Data Sources" in content
        assert "This directory contains scraped data" in content
    
    def test_export_fbref_returns_correct_path(self, csv_exporter, sample_fbref_data, temp_output_dir):
        """Test that export_fbref returns the correct file path.
        
        Requirements: 6.1
        """
        output_path = csv_exporter.export_fbref(sample_fbref_data, "2023", "2024")
        
        # Verify path is string
        assert isinstance(output_path, str)
        
        # Verify file exists at that path
        assert Path(output_path).exists()
        
        # Verify path contains expected directory
        assert temp_output_dir in output_path
    
    def test_export_transfermarkt_returns_correct_path(self, csv_exporter, sample_transfermarkt_data, temp_output_dir):
        """Test that export_transfermarkt returns the correct file path.
        
        Requirements: 6.3
        """
        output_path = csv_exporter.export_transfermarkt(sample_transfermarkt_data, "2022", "2024")
        
        # Verify path is string
        assert isinstance(output_path, str)
        
        # Verify file exists at that path
        assert Path(output_path).exists()
        
        # Verify path contains expected directory
        assert temp_output_dir in output_path
    
    def test_export_fbref_with_extra_columns(self, csv_exporter, temp_output_dir):
        """Test FBref export handles DataFrames with extra columns."""
        df_with_extra = pd.DataFrame({
            'Date': ['2023-08-15'],
            'Season': ['2324'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [2.3],
            'Away_xG': [1.2],
            'ExtraColumn': ['should_be_removed']
        })
        
        output_path = csv_exporter.export_fbref(df_with_extra, "2023", "2024")
        df = pd.read_csv(output_path)
        
        # Verify extra column is not in output
        assert 'ExtraColumn' not in df.columns
        assert len(df.columns) == 6
    
    def test_export_transfermarkt_with_extra_columns(self, csv_exporter, temp_output_dir):
        """Test Transfermarkt export handles DataFrames with extra columns."""
        df_with_extra = pd.DataFrame({
            'Season': ['2324'],
            'Team': ['Arsenal'],
            'Squad_Value': [920.3],
            'ExtraColumn': ['should_be_removed']
        })
        
        output_path = csv_exporter.export_transfermarkt(df_with_extra, "2023", "2024")
        df = pd.read_csv(output_path)
        
        # Verify extra column is not in output
        assert 'ExtraColumn' not in df.columns
        assert len(df.columns) == 3
