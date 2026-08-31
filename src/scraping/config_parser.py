"""
Configuration parser component for scraping configuration files.

Implements: Requirements 11.1, 11.2, 11.3, 11.4

This module provides the ConfigParser class which:
- Loads and validates team name mapping configurations (team_names_mapping.json)
- Loads and validates CSS selector configurations (scraping_selectors.json)
- Saves JSON configurations with pretty printing (2-space indentation)
- Handles missing files and malformed JSON errors
"""

import json
from pathlib import Path
from typing import Dict, Any


class ConfigParser:
    """
    Parser for scraping configuration files.
    
    Responsibilities:
    - Load team name mapping from JSON
    - Load CSS selectors configuration from JSON
    - Validate JSON structure (check required keys)
    - Save JSON configurations with pretty printing
    - Handle file not found and malformed JSON errors
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize ConfigParser.
        
        Args:
            config_dir: Path to configuration directory (default: "config")
        """
        self.config_dir = Path(config_dir)
    
    def load_team_mapping(self) -> Dict[str, str]:
        """
        Load team name mapping configuration.
        
        Returns:
            Dictionary mapping source team name variations to canonical names.
            Example: {"Man Utd": "Man United", "Spurs": "Tottenham"}
        
        Raises:
            FileNotFoundError: If team_names_mapping.json doesn't exist
            ValueError: If JSON structure is invalid (not a dictionary)
            json.JSONDecodeError: If JSON is malformed
        """
        mapping_file = self.config_dir / "team_names_mapping.json"
        
        if not mapping_file.exists():
            raise FileNotFoundError(
                f"Team mapping file not found: {mapping_file}"
            )
        
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Malformed JSON in {mapping_file}: {e.msg}",
                e.doc,
                e.pos
            )
        
        # Validate structure
        if not isinstance(mapping, dict):
            raise ValueError(
                f"Team mapping must be a dictionary, got {type(mapping).__name__}"
            )
        
        return mapping
    
    def load_selectors(self) -> Dict[str, Any]:
        """
        Load CSS selectors configuration.
        
        Returns:
            Dictionary containing selectors for each source (fbref, transfermarkt).
            Example: {
                "fbref": {
                    "xg_table": {
                        "primary": "table.stats_table tbody tr",
                        "fallback": "div.table_container table tr"
                    }
                },
                "transfermarkt": {...}
            }
        
        Raises:
            FileNotFoundError: If scraping_selectors.json doesn't exist
            ValueError: If required sources are missing
            json.JSONDecodeError: If JSON is malformed
        """
        selectors_file = self.config_dir / "scraping_selectors.json"
        
        if not selectors_file.exists():
            raise FileNotFoundError(
                f"Selectors file not found: {selectors_file}"
            )
        
        try:
            with open(selectors_file, 'r', encoding='utf-8') as f:
                selectors = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Malformed JSON in {selectors_file}: {e.msg}",
                e.doc,
                e.pos
            )
        
        # Validate structure - check required sources
        required_sources = ['fbref', 'transfermarkt']
        for source in required_sources:
            if source not in selectors:
                raise ValueError(
                    f"Missing required selectors for source: {source}"
                )
        
        return selectors
    
    def save_json(self, data: Dict[str, Any], filename: str) -> None:
        """
        Pretty print JSON configuration to file with 2-space indentation.
        
        Args:
            data: Dictionary to save as JSON
            filename: Name of the file (will be saved in config_dir)
        
        Raises:
            OSError: If file cannot be written
            TypeError: If data is not JSON serializable
        """
        output_path = self.config_dir / filename
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            # Add trailing newline for better git diffs
            f.write('\n')
