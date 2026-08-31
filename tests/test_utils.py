"""
Unit tests for utility functions.

Tests Requirements: 8.1, 8.2, 8.3, 8.4
"""

import json
import pytest
import logging
from pathlib import Path
from src.scraping.utils import (
    load_team_mapping,
    normalize_team_name,
    parse_season_range,
    format_season_code
)


class TestLoadTeamMapping:
    """Test suite for load_team_mapping function."""
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create temporary config directory for tests."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        return config_dir
    
    def test_load_team_mapping_valid(self, temp_config_dir):
        """Test loading valid team mapping configuration."""
        # Arrange
        mapping = {
            "Man Utd": "Man United",
            "Spurs": "Tottenham",
            "Newcastle": "Newcastle United"
        }
        mapping_file = temp_config_dir / "team_names_mapping.json"
        with open(mapping_file, 'w') as f:
            json.dump(mapping, f)
        
        # Act
        result = load_team_mapping(str(temp_config_dir))
        
        # Assert
        assert result == mapping
        assert result["Man Utd"] == "Man United"
        assert result["Spurs"] == "Tottenham"
    
    def test_load_team_mapping_file_not_found(self, temp_config_dir):
        """Test error handling when team mapping file doesn't exist."""
        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            load_team_mapping(str(temp_config_dir))
        
        assert "team_names_mapping.json" in str(exc_info.value)
    
    def test_load_team_mapping_malformed_json(self, temp_config_dir):
        """Test error handling for malformed JSON."""
        # Arrange
        mapping_file = temp_config_dir / "team_names_mapping.json"
        with open(mapping_file, 'w') as f:
            f.write("{invalid json content")
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            load_team_mapping(str(temp_config_dir))
        
        assert "Invalid JSON" in str(exc_info.value)
    
    def test_load_team_mapping_invalid_structure(self, temp_config_dir):
        """Test error handling when JSON is not a dictionary."""
        # Arrange
        mapping_file = temp_config_dir / "team_names_mapping.json"
        with open(mapping_file, 'w') as f:
            json.dump(["not", "a", "dict"], f)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            load_team_mapping(str(temp_config_dir))
        
        assert "must be a dictionary" in str(exc_info.value)


class TestNormalizeTeamName:
    """Test suite for normalize_team_name function."""
    
    @pytest.fixture
    def sample_mapping(self):
        """Provide sample team name mapping."""
        return {
            "Man Utd": "Man United",
            "Manchester United": "Man United",
            "Spurs": "Tottenham",
            "Tottenham Hotspur": "Tottenham",
            "Newcastle": "Newcastle United",
            "Wolves": "Wolverhampton Wanderers"
        }
    
    def test_normalize_known_variation(self, sample_mapping):
        """Test normalizing a known team name variation."""
        # Act & Assert
        assert normalize_team_name("Man Utd", sample_mapping) == "Man United"
        assert normalize_team_name("Spurs", sample_mapping) == "Tottenham"
        assert normalize_team_name("Wolves", sample_mapping) == "Wolverhampton Wanderers"
    
    def test_normalize_canonical_name(self, sample_mapping):
        """Test normalizing a team name that's already canonical."""
        # Act & Assert
        assert normalize_team_name("Man United", sample_mapping) == "Man United"
        assert normalize_team_name("Tottenham", sample_mapping) == "Tottenham"
    
    def test_normalize_unmapped_name(self, sample_mapping, caplog):
        """Test normalizing an unmapped team name returns original."""
        # Arrange
        caplog.set_level(logging.WARNING)
        
        # Act
        result = normalize_team_name("Unknown Team", sample_mapping)
        
        # Assert
        assert result == "Unknown Team"
        assert "Unmapped team name" in caplog.text
        assert "Unknown Team" in caplog.text
    
    def test_normalize_unmapped_no_warning(self, sample_mapping, caplog):
        """Test unmapped name without warning when warn_unmapped=False."""
        # Arrange
        caplog.set_level(logging.WARNING)
        
        # Act
        result = normalize_team_name("Unknown Team", sample_mapping, warn_unmapped=False)
        
        # Assert
        assert result == "Unknown Team"
        assert "Unmapped team name" not in caplog.text
    
    def test_normalize_empty_mapping(self, caplog):
        """Test normalizing with empty mapping."""
        # Arrange
        caplog.set_level(logging.WARNING)
        empty_mapping = {}
        
        # Act
        result = normalize_team_name("Any Team", empty_mapping)
        
        # Assert
        assert result == "Any Team"
        assert "Unmapped team name" in caplog.text
    
    def test_normalize_case_sensitive(self, sample_mapping):
        """Test that normalization is case-sensitive."""
        # Act & Assert
        # "man utd" (lowercase) should not match "Man Utd"
        result = normalize_team_name("man utd", sample_mapping)
        assert result == "man utd"  # Returns original (unmapped)


class TestParseSeasonRange:
    """Test suite for parse_season_range function."""
    
    def test_parse_valid_range(self):
        """Test parsing valid season range formats."""
        # Act & Assert
        assert parse_season_range("2017-2026") == (2017, 2026)
        assert parse_season_range("2020-2023") == (2020, 2023)
        assert parse_season_range("2000-2010") == (2000, 2010)
    
    def test_parse_single_season(self):
        """Test parsing a single season (start == end)."""
        # Act & Assert
        assert parse_season_range("2023-2023") == (2023, 2023)
    
    def test_parse_invalid_format_no_dash(self):
        """Test error handling for invalid format without dash."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            parse_season_range("20172026")
        
        assert "Expected format 'YYYY-YYYY'" in str(exc_info.value)
    
    def test_parse_invalid_format_multiple_dashes(self):
        """Test error handling for invalid format with multiple dashes."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            parse_season_range("2017-2020-2026")
        
        assert "Expected format 'YYYY-YYYY'" in str(exc_info.value)
    
    def test_parse_invalid_format_non_numeric(self):
        """Test error handling for non-numeric years."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            parse_season_range("2017-abcd")
        
        assert "Invalid season range format" in str(exc_info.value)
    
    def test_parse_year_out_of_range_too_low(self):
        """Test error handling for years before 1900."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            parse_season_range("1800-2020")
        
        assert "out of reasonable range" in str(exc_info.value)
    
    def test_parse_year_out_of_range_too_high(self):
        """Test error handling for years after 2100."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            parse_season_range("2020-2150")
        
        assert "out of reasonable range" in str(exc_info.value)
    
    def test_parse_start_after_end(self):
        """Test error handling when start year is after end year."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            parse_season_range("2026-2017")
        
        assert "cannot be after end year" in str(exc_info.value)
    
    def test_parse_empty_string(self):
        """Test error handling for empty string."""
        # Act & Assert
        with pytest.raises(ValueError):
            parse_season_range("")
    
    def test_parse_whitespace(self):
        """Test error handling for whitespace input."""
        # Act & Assert
        with pytest.raises(ValueError):
            parse_season_range("   ")


class TestFormatSeasonCode:
    """Test suite for format_season_code function."""
    
    def test_format_valid_years(self):
        """Test formatting valid years to season codes."""
        # Act & Assert
        assert format_season_code(2017) == "1718"
        assert format_season_code(2020) == "2021"
        assert format_season_code(2025) == "2526"
        assert format_season_code(2000) == "0001"
        assert format_season_code(1999) == "9900"
    
    def test_format_century_boundary(self):
        """Test formatting years at century boundaries."""
        # Act & Assert
        assert format_season_code(1999) == "9900"
        assert format_season_code(2000) == "0001"
        assert format_season_code(2099) == "9900"
    
    def test_format_early_2000s(self):
        """Test formatting years in early 2000s with leading zeros."""
        # Act & Assert
        assert format_season_code(2003) == "0304"
        assert format_season_code(2009) == "0910"
    
    def test_format_year_too_low(self):
        """Test error handling for year before 1900."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            format_season_code(1800)
        
        assert "out of reasonable range" in str(exc_info.value)
    
    def test_format_year_too_high(self):
        """Test error handling for year after 2100."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            format_season_code(2150)
        
        assert "out of reasonable range" in str(exc_info.value)
    
    def test_format_2099_to_2100_transition(self):
        """Test formatting the year 2099 (transitions to 2100)."""
        # 2099-2100 season should be "9900"
        # Act & Assert
        assert format_season_code(2099) == "9900"


class TestIntegration:
    """Integration tests combining multiple utility functions."""
    
    def test_season_range_to_codes(self):
        """Test parsing season range and formatting to codes."""
        # Arrange
        season_range = "2017-2020"
        
        # Act
        start_year, end_year = parse_season_range(season_range)
        codes = [format_season_code(year) for year in range(start_year, end_year + 1)]
        
        # Assert
        assert codes == ["1718", "1819", "1920", "2021"]
    
    def test_normalize_multiple_teams(self):
        """Test normalizing multiple team names at once."""
        # Arrange
        mapping = {
            "Man Utd": "Man United",
            "Spurs": "Tottenham",
            "Wolves": "Wolverhampton Wanderers"
        }
        team_names = ["Man Utd", "Arsenal", "Spurs", "Chelsea", "Wolves"]
        
        # Act
        normalized = [normalize_team_name(name, mapping, warn_unmapped=False) for name in team_names]
        
        # Assert
        assert normalized == [
            "Man United",
            "Arsenal",
            "Tottenham",
            "Chelsea",
            "Wolverhampton Wanderers"
        ]
