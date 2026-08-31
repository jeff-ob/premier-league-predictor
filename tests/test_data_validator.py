"""Unit tests for DataValidator class.

Tests validation logic for both FBref and Transfermarkt data sources.
"""

import pytest
import pandas as pd
from src.scraping.data_validator import DataValidator
import tempfile
import os


class TestDataValidatorFBref:
    """Test cases for FBref data validation."""
    
    def test_validate_fbref_valid_data(self):
        """Test validation passes for valid FBref data."""
        validator = DataValidator('fbref')
        
        data = {
            'Date': ['2023-08-12', '2023-08-19'],
            'HomeTeam': ['Arsenal', 'Man City'],
            'AwayTeam': ['Nottingham', 'Newcastle'],
            'Home_xG': [2.5, 1.8],
            'Away_xG': [0.9, 1.2]
        }
        df = pd.DataFrame(data)
        
        result = validator.validate(df)
        
        assert len(result) == 2
        assert len(validator.warnings) == 0
        assert len(validator.errors) == 0
    
    def test_validate_fbref_invalid_home_xg(self):
        """Test validation rejects invalid Home_xG values."""
        validator = DataValidator('fbref')
        
        data = {
            'Date': ['2023-08-12'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Nottingham'],
            'Home_xG': [20.0],  # Out of range
            'Away_xG': [1.0]
        }
        df = pd.DataFrame(data)
        
        result = validator.validate(df)
        
        assert len(result) == 0
        assert len(validator.warnings) == 1
        assert 'Invalid Home_xG' in validator.warnings[0]
    
    def test_validate_fbref_invalid_away_xg(self):
        """Test validation rejects invalid Away_xG values."""
        validator = DataValidator('fbref')
        
        data = {
            'Date': ['2023-08-12'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Nottingham'],
            'Home_xG': [2.5],
            'Away_xG': [-1.0]  # Negative value, out of range
        }
        df = pd.DataFrame(data)
        
        result = validator.validate(df)
        
        assert len(result) == 0
        assert len(validator.warnings) == 1
        assert 'Invalid Away_xG' in validator.warnings[0]
    
    def test_validate_fbref_implausible_total_xg(self):
        """Test validation rejects implausible total xG values."""
        validator = DataValidator('fbref')
        
        data = {
            'Date': ['2023-08-12'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Nottingham'],
            'Home_xG': [12.0],
            'Away_xG': [10.0]  # Total = 22.0, > 20.0
        }
        df = pd.DataFrame(data)
        
        result = validator.validate(df)
        
        assert len(result) == 0
        assert len(validator.warnings) == 1
        assert 'Implausible total xG' in validator.warnings[0]
    
    def test_validate_fbref_date_outside_season(self):
        """Test validation rejects dates outside season range."""
        validator = DataValidator('fbref')
        
        data = {
            'Date': ['2023-06-12'],  # June, outside Aug-May range
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Nottingham'],
            'Home_xG': [2.5],
            'Away_xG': [1.0]
        }
        df = pd.DataFrame(data)
        
        result = validator.validate(df)
        
        assert len(result) == 0
        assert len(validator.warnings) == 1
        assert 'Date outside season range' in validator.warnings[0]


class TestDataValidatorTransfermarkt:
    """Test cases for Transfermarkt data validation."""
    
    def test_validate_transfermarkt_valid_data(self):
        """Test validation passes for valid Transfermarkt data."""
        validator = DataValidator('transfermarkt')
        
        data = {
            'Season': ['1718', '1819'],
            'Team': ['Arsenal', 'Arsenal'],
            'Squad_Value': [500.0, 520.0]
        }
        df = pd.DataFrame(data)
        
        result = validator.validate(df)
        
        assert len(result) == 2
        assert len(validator.warnings) == 0
        assert len(validator.errors) == 0
    
    def test_validate_transfermarkt_invalid_value_range(self):
        """Test validation rejects Squad_Value outside valid range."""
        validator = DataValidator('transfermarkt')
        
        data = {
            'Season': ['1718'],
            'Team': ['Arsenal'],
            'Squad_Value': [5000.0]  # Out of range [10.0, 2000.0]
        }
        df = pd.DataFrame(data)
        
        result = validator.validate(df)
        
        assert len(result) == 0
        assert len(validator.warnings) == 1
        assert 'Invalid Squad_Value' in validator.warnings[0]
    
    def test_validate_transfermarkt_large_value_drop(self):
        """Test validation warns about large value drops between seasons."""
        validator = DataValidator('transfermarkt')
        
        data = {
            'Season': ['1718', '1819'],
            'Team': ['Arsenal', 'Arsenal'],
            'Squad_Value': [500.0, 250.0]  # 50% drop
        }
        df = pd.DataFrame(data)
        
        result = validator.validate(df)
        
        # Both rows should be kept, but warning issued
        assert len(result) == 2
        assert len(validator.warnings) == 1
        assert 'Large value drop' in validator.warnings[0]
    
    def test_validate_transfermarkt_acceptable_value_drop(self):
        """Test validation accepts moderate value drops."""
        validator = DataValidator('transfermarkt')
        
        data = {
            'Season': ['1718', '1819'],
            'Team': ['Arsenal', 'Arsenal'],
            'Squad_Value': [500.0, 350.0]  # 30% drop, acceptable
        }
        df = pd.DataFrame(data)
        
        result = validator.validate(df)
        
        assert len(result) == 2
        assert len(validator.warnings) == 0


class TestDataValidatorGenerateReport:
    """Test cases for report generation."""
    
    def test_generate_report_with_warnings(self):
        """Test report generation includes warnings."""
        validator = DataValidator('fbref')
        
        # Add some warnings
        validator.warnings.append("Warning 1")
        validator.warnings.append("Warning 2")
        
        # Generate report to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
        
        try:
            validator.generate_report(temp_path)
            
            # Read and verify report content
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert '=== Data Validation Report ===' in content
            assert 'Source: fbref' in content
            assert 'Warnings: 2' in content
            assert 'Warning 1' in content
            assert 'Warning 2' in content
        finally:
            os.unlink(temp_path)
    
    def test_generate_report_with_errors(self):
        """Test report generation includes errors."""
        validator = DataValidator('transfermarkt')
        
        # Add some errors
        validator.errors.append("Error 1")
        
        # Generate report to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
        
        try:
            validator.generate_report(temp_path)
            
            # Read and verify report content
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert '=== Data Validation Report ===' in content
            assert 'Source: transfermarkt' in content
            assert 'Errors: 1' in content
            assert 'Error 1' in content
        finally:
            os.unlink(temp_path)


class TestDataValidatorUnknownSource:
    """Test error handling for unknown data sources."""
    
    def test_validate_unknown_source_raises_error(self):
        """Test validation raises ValueError for unknown source."""
        validator = DataValidator('unknown_source')
        
        df = pd.DataFrame({'col': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="Unknown source"):
            validator.validate(df)
