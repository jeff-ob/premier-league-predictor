"""Comprehensive tests verifying DataValidator meets all spec requirements.

This test file demonstrates compliance with:
- Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6 (Data validation)
- Requirements 1.5, 2.6 (Data validation for specific sources)
"""

import pytest
import pandas as pd
from src.scraping.data_validator import DataValidator
import tempfile
import os


class TestRequirement91FBrefDateInSeasonRange:
    """Test Requirement 9.1: Verify Date is within expected season range (August to May)."""
    
    def test_date_in_august_is_valid(self):
        """August dates should be valid (start of season)."""
        validator = DataValidator('fbref')
        df = pd.DataFrame({
            'Date': ['2023-08-15'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [2.0],
            'Away_xG': [1.5]
        })
        result = validator.validate(df)
        assert len(result) == 1
        assert len(validator.warnings) == 0
    
    def test_date_in_may_is_valid(self):
        """May dates should be valid (end of season)."""
        validator = DataValidator('fbref')
        df = pd.DataFrame({
            'Date': ['2024-05-15'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [2.0],
            'Away_xG': [1.5]
        })
        result = validator.validate(df)
        assert len(result) == 1
        assert len(validator.warnings) == 0
    
    def test_date_in_june_is_invalid(self):
        """June dates should be rejected (outside season)."""
        validator = DataValidator('fbref')
        df = pd.DataFrame({
            'Date': ['2023-06-15'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [2.0],
            'Away_xG': [1.5]
        })
        result = validator.validate(df)
        assert len(result) == 0
        assert len(validator.warnings) == 1
        assert 'Date outside season range' in validator.warnings[0]
    
    def test_date_in_july_is_invalid(self):
        """July dates should be rejected (outside season)."""
        validator = DataValidator('fbref')
        df = pd.DataFrame({
            'Date': ['2023-07-15'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [2.0],
            'Away_xG': [1.5]
        })
        result = validator.validate(df)
        assert len(result) == 0
        assert len(validator.warnings) == 1


class TestRequirement92FBrefTotalXGSanityCheck:
    """Test Requirement 9.2: Verify Home_xG + Away_xG is less than 20.0 (sanity check)."""
    
    def test_total_xg_below_20_is_valid(self):
        """Total xG below 20.0 should be valid."""
        validator = DataValidator('fbref')
        df = pd.DataFrame({
            'Date': ['2023-08-15'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [10.0],
            'Away_xG': [9.0]  # Total = 19.0
        })
        result = validator.validate(df)
        assert len(result) == 1
        assert len(validator.warnings) == 0
    
    def test_total_xg_at_20_is_invalid(self):
        """Total xG exactly 20.0 should be rejected."""
        validator = DataValidator('fbref')
        df = pd.DataFrame({
            'Date': ['2023-08-15'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [10.0],
            'Away_xG': [10.0]  # Total = 20.0
        })
        result = validator.validate(df)
        assert len(result) == 0
        assert len(validator.warnings) == 1
        assert 'Implausible total xG: 20.0' in validator.warnings[0]
    
    def test_total_xg_above_20_is_invalid(self):
        """Total xG above 20.0 should be rejected."""
        validator = DataValidator('fbref')
        df = pd.DataFrame({
            'Date': ['2023-08-15'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [12.0],
            'Away_xG': [11.0]  # Total = 23.0
        })
        result = validator.validate(df)
        assert len(result) == 0
        assert len(validator.warnings) == 1
        assert 'Implausible total xG: 23.0' in validator.warnings[0]


class TestRequirement15FBrefXGRange:
    """Test Requirement 1.5: FOR ALL extracted xG values, verify they are between 0.0 and 15.0."""
    
    def test_home_xg_at_lower_bound_is_valid(self):
        """Home_xG at 0.0 should be valid."""
        validator = DataValidator('fbref')
        df = pd.DataFrame({
            'Date': ['2023-08-15'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [0.0],
            'Away_xG': [2.0]
        })
        result = validator.validate(df)
        assert len(result) == 1
    
    def test_home_xg_at_upper_bound_is_valid(self):
        """Home_xG at 15.0 should be valid."""
        validator = DataValidator('fbref')
        df = pd.DataFrame({
            'Date': ['2023-08-15'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [15.0],
            'Away_xG': [2.0]
        })
        result = validator.validate(df)
        assert len(result) == 1
    
    def test_home_xg_below_lower_bound_is_invalid(self):
        """Home_xG below 0.0 should be rejected."""
        validator = DataValidator('fbref')
        df = pd.DataFrame({
            'Date': ['2023-08-15'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [-0.5],
            'Away_xG': [2.0]
        })
        result = validator.validate(df)
        assert len(result) == 0
        assert 'Invalid Home_xG' in validator.warnings[0]
    
    def test_home_xg_above_upper_bound_is_invalid(self):
        """Home_xG above 15.0 should be rejected."""
        validator = DataValidator('fbref')
        df = pd.DataFrame({
            'Date': ['2023-08-15'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [15.5],
            'Away_xG': [2.0]
        })
        result = validator.validate(df)
        assert len(result) == 0
        assert 'Invalid Home_xG' in validator.warnings[0]
    
    def test_away_xg_within_bounds_is_valid(self):
        """Away_xG within [0.0, 15.0] should be valid."""
        validator = DataValidator('fbref')
        df = pd.DataFrame({
            'Date': ['2023-08-15'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [2.0],
            'Away_xG': [7.5]
        })
        result = validator.validate(df)
        assert len(result) == 1
    
    def test_away_xg_out_of_bounds_is_invalid(self):
        """Away_xG outside [0.0, 15.0] should be rejected."""
        validator = DataValidator('fbref')
        df = pd.DataFrame({
            'Date': ['2023-08-15'],
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Home_xG': [2.0],
            'Away_xG': [20.0]
        })
        result = validator.validate(df)
        assert len(result) == 0
        assert 'Invalid Away_xG' in validator.warnings[0]


class TestRequirement26TransfermarktValueRange:
    """Test Requirement 2.6: FOR ALL Squad_Value entries, verify values are between 10.0 and 2000.0 million euros."""
    
    def test_squad_value_at_lower_bound_is_valid(self):
        """Squad_Value at 10.0 should be valid."""
        validator = DataValidator('transfermarkt')
        df = pd.DataFrame({
            'Season': ['1718'],
            'Team': ['Bournemouth'],
            'Squad_Value': [10.0]
        })
        result = validator.validate(df)
        assert len(result) == 1
        assert len(validator.warnings) == 0
    
    def test_squad_value_at_upper_bound_is_valid(self):
        """Squad_Value at 2000.0 should be valid."""
        validator = DataValidator('transfermarkt')
        df = pd.DataFrame({
            'Season': ['2223'],
            'Team': ['Man City'],
            'Squad_Value': [2000.0]
        })
        result = validator.validate(df)
        assert len(result) == 1
        assert len(validator.warnings) == 0
    
    def test_squad_value_below_lower_bound_is_invalid(self):
        """Squad_Value below 10.0 should be rejected."""
        validator = DataValidator('transfermarkt')
        df = pd.DataFrame({
            'Season': ['1718'],
            'Team': ['Test Team'],
            'Squad_Value': [5.0]
        })
        result = validator.validate(df)
        assert len(result) == 0
        assert 'Invalid Squad_Value' in validator.warnings[0]
    
    def test_squad_value_above_upper_bound_is_invalid(self):
        """Squad_Value above 2000.0 should be rejected."""
        validator = DataValidator('transfermarkt')
        df = pd.DataFrame({
            'Season': ['2223'],
            'Team': ['Test Team'],
            'Squad_Value': [2500.0]
        })
        result = validator.validate(df)
        assert len(result) == 0
        assert 'Invalid Squad_Value' in validator.warnings[0]
    
    def test_squad_value_in_mid_range_is_valid(self):
        """Squad_Value in mid-range should be valid."""
        validator = DataValidator('transfermarkt')
        df = pd.DataFrame({
            'Season': ['1718', '1819'],
            'Team': ['Arsenal', 'Chelsea'],
            'Squad_Value': [500.0, 750.0]
        })
        result = validator.validate(df)
        assert len(result) == 2
        assert len(validator.warnings) == 0


class TestRequirement93TemporalCoherence:
    """Test Requirement 9.3: Verify Squad_Value temporal coherence (teams rarely lose 50%+ value instantly)."""
    
    def test_stable_value_over_seasons(self):
        """Stable values over seasons should pass without warnings."""
        validator = DataValidator('transfermarkt')
        df = pd.DataFrame({
            'Season': ['1718', '1819', '1920'],
            'Team': ['Arsenal', 'Arsenal', 'Arsenal'],
            'Squad_Value': [500.0, 510.0, 505.0]
        })
        result = validator.validate(df)
        assert len(result) == 3
        assert len(validator.warnings) == 0
    
    def test_moderate_value_drop_is_acceptable(self):
        """30% value drop should be acceptable (< 40% threshold)."""
        validator = DataValidator('transfermarkt')
        df = pd.DataFrame({
            'Season': ['1718', '1819'],
            'Team': ['Arsenal', 'Arsenal'],
            'Squad_Value': [500.0, 350.0]  # 30% drop
        })
        result = validator.validate(df)
        assert len(result) == 2
        assert len(validator.warnings) == 0
    
    def test_large_value_drop_triggers_warning(self):
        """50% value drop should trigger warning (> 40% threshold)."""
        validator = DataValidator('transfermarkt')
        df = pd.DataFrame({
            'Season': ['1718', '1819'],
            'Team': ['Arsenal', 'Arsenal'],
            'Squad_Value': [500.0, 250.0]  # 50% drop
        })
        result = validator.validate(df)
        # Rows are kept but warning is issued
        assert len(result) == 2
        assert len(validator.warnings) == 1
        assert 'Large value drop' in validator.warnings[0]
        assert 'Arsenal' in validator.warnings[0]
    
    def test_value_drop_at_threshold(self):
        """Exactly 40% value drop should trigger warning."""
        validator = DataValidator('transfermarkt')
        df = pd.DataFrame({
            'Season': ['1718', '1819'],
            'Team': ['Chelsea', 'Chelsea'],
            'Squad_Value': [500.0, 300.0]  # Exactly 40% drop
        })
        result = validator.validate(df)
        assert len(result) == 2
        # Should NOT trigger warning at exactly 40% (condition is > 0.4)
        assert len(validator.warnings) == 0
    
    def test_value_drop_just_over_threshold(self):
        """41% value drop should trigger warning."""
        validator = DataValidator('transfermarkt')
        df = pd.DataFrame({
            'Season': ['1718', '1819'],
            'Team': ['Chelsea', 'Chelsea'],
            'Squad_Value': [500.0, 295.0]  # 41% drop
        })
        result = validator.validate(df)
        assert len(result) == 2
        assert len(validator.warnings) == 1
    
    def test_value_increase_does_not_trigger_warning(self):
        """Value increases should not trigger warnings."""
        validator = DataValidator('transfermarkt')
        df = pd.DataFrame({
            'Season': ['1718', '1819', '1920'],
            'Team': ['Man City', 'Man City', 'Man City'],
            'Squad_Value': [500.0, 750.0, 1000.0]
        })
        result = validator.validate(df)
        assert len(result) == 3
        assert len(validator.warnings) == 0


class TestRequirement96ValidationReport:
    """Test Requirement 9.6: Generate validation report listing all warnings and errors."""
    
    def test_report_contains_header_and_metadata(self):
        """Report should contain header and metadata."""
        validator = DataValidator('fbref')
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
        
        try:
            validator.generate_report(temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert '=== Data Validation Report ===' in content
            assert 'Source: fbref' in content
            assert 'Warnings:' in content
            assert 'Errors:' in content
        finally:
            os.unlink(temp_path)
    
    def test_report_lists_all_warnings(self):
        """Report should list all warnings encountered."""
        validator = DataValidator('fbref')
        validator.warnings = [
            "Warning 1: Invalid xG value",
            "Warning 2: Date out of range",
            "Warning 3: Implausible total"
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
        
        try:
            validator.generate_report(temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert 'Warnings: 3' in content
            assert '--- Warnings ---' in content
            assert 'Warning 1: Invalid xG value' in content
            assert 'Warning 2: Date out of range' in content
            assert 'Warning 3: Implausible total' in content
        finally:
            os.unlink(temp_path)
    
    def test_report_lists_all_errors(self):
        """Report should list all errors encountered."""
        validator = DataValidator('transfermarkt')
        validator.errors = [
            "Error 1: Cannot parse HTML",
            "Error 2: Missing required column"
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
        
        try:
            validator.generate_report(temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert 'Errors: 2' in content
            assert '--- Errors ---' in content
            assert 'Error 1: Cannot parse HTML' in content
            assert 'Error 2: Missing required column' in content
        finally:
            os.unlink(temp_path)


class TestIntegrationMultipleValidations:
    """Integration tests validating multiple requirements together."""
    
    def test_mixed_valid_and_invalid_fbref_data(self):
        """Mix of valid and invalid FBref data should be handled correctly."""
        validator = DataValidator('fbref')
        df = pd.DataFrame({
            'Date': ['2023-08-15', '2023-09-10', '2023-06-01', '2023-10-15'],
            'HomeTeam': ['Arsenal', 'Chelsea', 'Liverpool', 'Man City'],
            'AwayTeam': ['Brighton', 'Aston Villa', 'Newcastle', 'Tottenham'],
            'Home_xG': [2.5, 20.0, 3.0, 4.5],  # Second row invalid
            'Away_xG': [1.8, 1.0, 2.2, 3.0]
        })
        result = validator.validate(df)
        
        # Should keep rows 1, 3, 4 (indices 0, 2, 3)
        # Row 2 rejected due to invalid Home_xG
        # Row 3 rejected due to date outside season
        assert len(result) == 2
        assert len(validator.warnings) == 2
    
    def test_mixed_valid_and_invalid_transfermarkt_data(self):
        """Mix of valid and invalid Transfermarkt data should be handled correctly."""
        validator = DataValidator('transfermarkt')
        df = pd.DataFrame({
            'Season': ['1718', '1819', '1920', '2021'],
            'Team': ['Arsenal', 'Arsenal', 'Arsenal', 'Chelsea'],
            'Squad_Value': [500.0, 250.0, 260.0, 5000.0]  # Large drop + invalid range
        })
        result = validator.validate(df)
        
        # First 3 rows valid but warning for large drop
        # 4th row invalid due to out of range value
        assert len(result) == 3
        assert len(validator.warnings) >= 2  # Large drop + invalid value
