"""
Unit tests for ConfigParser class.

Tests Requirements: 11.1, 11.2, 11.3, 11.4
"""

import json
import pytest
from pathlib import Path
from src.scraping.config_parser import ConfigParser


class TestConfigParser:
    """Test suite for ConfigParser class."""
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create temporary config directory for tests."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        return config_dir
    
    @pytest.fixture
    def parser(self, temp_config_dir):
        """Create ConfigParser instance with temporary directory."""
        return ConfigParser(str(temp_config_dir))
    
    # Tests for load_team_mapping()
    
    def test_load_team_mapping_valid(self, parser, temp_config_dir):
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
        result = parser.load_team_mapping()
        
        # Assert
        assert result == mapping
        assert result["Man Utd"] == "Man United"
        assert result["Spurs"] == "Tottenham"
    
    def test_load_team_mapping_file_not_found(self, parser):
        """Test error handling when team mapping file doesn't exist."""
        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.load_team_mapping()
        
        assert "team_names_mapping.json" in str(exc_info.value)
    
    def test_load_team_mapping_malformed_json(self, parser, temp_config_dir):
        """Test error handling for malformed JSON."""
        # Arrange
        mapping_file = temp_config_dir / "team_names_mapping.json"
        with open(mapping_file, 'w') as f:
            f.write("{invalid json content")
        
        # Act & Assert
        with pytest.raises(json.JSONDecodeError):
            parser.load_team_mapping()
    
    def test_load_team_mapping_invalid_structure(self, parser, temp_config_dir):
        """Test error handling when JSON is not a dictionary."""
        # Arrange
        mapping_file = temp_config_dir / "team_names_mapping.json"
        with open(mapping_file, 'w') as f:
            json.dump(["not", "a", "dict"], f)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            parser.load_team_mapping()
        
        assert "must be a dictionary" in str(exc_info.value)
    
    # Tests for load_selectors()
    
    def test_load_selectors_valid(self, parser, temp_config_dir):
        """Test loading valid selectors configuration."""
        # Arrange
        selectors = {
            "fbref": {
                "xg_table": {
                    "primary": "table.stats_table tbody tr",
                    "fallback": "div.table_container table tr"
                },
                "last_verified": "2024-01-15"
            },
            "transfermarkt": {
                "squad_value": {
                    "primary": "table.items tbody tr",
                    "fallback": "div.responsive-table td"
                },
                "last_verified": "2024-01-15"
            }
        }
        selectors_file = temp_config_dir / "scraping_selectors.json"
        with open(selectors_file, 'w') as f:
            json.dump(selectors, f)
        
        # Act
        result = parser.load_selectors()
        
        # Assert
        assert result == selectors
        assert "fbref" in result
        assert "transfermarkt" in result
        assert result["fbref"]["xg_table"]["primary"] == "table.stats_table tbody tr"
    
    def test_load_selectors_file_not_found(self, parser):
        """Test error handling when selectors file doesn't exist."""
        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.load_selectors()
        
        assert "scraping_selectors.json" in str(exc_info.value)
    
    def test_load_selectors_malformed_json(self, parser, temp_config_dir):
        """Test error handling for malformed JSON."""
        # Arrange
        selectors_file = temp_config_dir / "scraping_selectors.json"
        with open(selectors_file, 'w') as f:
            f.write('{"fbref": invalid}')
        
        # Act & Assert
        with pytest.raises(json.JSONDecodeError):
            parser.load_selectors()
    
    def test_load_selectors_missing_required_source(self, parser, temp_config_dir):
        """Test error handling when required sources are missing."""
        # Arrange - only include fbref, missing transfermarkt
        selectors = {
            "fbref": {
                "xg_table": {"primary": "table tr"}
            }
        }
        selectors_file = temp_config_dir / "scraping_selectors.json"
        with open(selectors_file, 'w') as f:
            json.dump(selectors, f)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            parser.load_selectors()
        
        assert "transfermarkt" in str(exc_info.value)
    
    # Tests for save_json()
    
    def test_save_json_valid(self, parser, temp_config_dir):
        """Test saving JSON configuration with pretty printing."""
        # Arrange
        data = {
            "team1": "Arsenal",
            "team2": "Chelsea",
            "nested": {
                "key": "value"
            }
        }
        filename = "test_config.json"
        
        # Act
        parser.save_json(data, filename)
        
        # Assert
        output_file = temp_config_dir / filename
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == data
    
    def test_save_json_indentation(self, parser, temp_config_dir):
        """Test that saved JSON has 2-space indentation."""
        # Arrange
        data = {"key": "value", "nested": {"inner": "data"}}
        filename = "indented.json"
        
        # Act
        parser.save_json(data, filename)
        
        # Assert
        output_file = temp_config_dir / filename
        with open(output_file, 'r') as f:
            content = f.read()
        
        # Check for 2-space indentation
        assert '  "key"' in content
        assert '  "nested"' in content
        # Should NOT have 4-space indentation
        assert '    "key"' not in content
    
    def test_save_json_creates_directory(self, tmp_path):
        """Test that save_json creates config directory if it doesn't exist."""
        # Arrange
        config_dir = tmp_path / "new_config"
        parser = ConfigParser(str(config_dir))
        data = {"test": "data"}
        
        # Act
        parser.save_json(data, "test.json")
        
        # Assert
        assert config_dir.exists()
        assert (config_dir / "test.json").exists()
    
    def test_save_json_unicode_characters(self, parser, temp_config_dir):
        """Test saving JSON with non-ASCII characters."""
        # Arrange
        data = {
            "team": "São Paulo",
            "city": "München",
            "emoji": "⚽"
        }
        filename = "unicode.json"
        
        # Act
        parser.save_json(data, filename)
        
        # Assert
        output_file = temp_config_dir / filename
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        assert loaded == data
        assert loaded["team"] == "São Paulo"
    
    # Round-trip property test (Requirements 11.4)
    
    def test_round_trip_property(self, parser, temp_config_dir):
        """
        Test round-trip property: parse → save → parse produces equivalent object.
        
        Tests Requirement 11.4: Round-trip property for configuration objects.
        """
        # Arrange - Create initial config
        original = {
            "Man Utd": "Man United",
            "Spurs": "Tottenham",
            "nested": {
                "key": "value",
                "number": 42
            }
        }
        
        # Act - Save, load, save again, load again
        parser.save_json(original, "round_trip.json")
        loaded1 = None
        with open(temp_config_dir / "round_trip.json", 'r') as f:
            loaded1 = json.load(f)
        
        parser.save_json(loaded1, "round_trip2.json")
        loaded2 = None
        with open(temp_config_dir / "round_trip2.json", 'r') as f:
            loaded2 = json.load(f)
        
        # Assert - All three should be equivalent
        assert original == loaded1
        assert loaded1 == loaded2
        assert original == loaded2
