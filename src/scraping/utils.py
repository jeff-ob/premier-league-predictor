"""Utility functions for scraping.

This module provides helper functions for:
- Team name normalization and mapping
- Season range parsing
- Season code formatting
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def load_team_mapping(config_dir: str = "config") -> Dict[str, str]:
    """Load team name mapping from configuration file.
    
    Args:
        config_dir: Directory containing team_names_mapping.json
        
    Returns:
        Dictionary mapping team name variations to canonical names
        
    Raises:
        FileNotFoundError: If mapping file does not exist
        ValueError: If mapping file is not valid JSON
    """
    mapping_file = Path(config_dir) / "team_names_mapping.json"
    
    if not mapping_file.exists():
        raise FileNotFoundError(f"Team mapping file not found: {mapping_file}")
    
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in team mapping file: {e}")
    
    if not isinstance(mapping, dict):
        raise ValueError("Team mapping must be a dictionary")
    
    return mapping


def normalize_team_name(
    team_name: str,
    mapping: Optional[Dict[str, str]] = None,
    warn_unmapped: bool = True
) -> str:
    """Normalize team name using mapping configuration.
    
    Applies team name mapping to convert variations to canonical names.
    If a team name is not found in the mapping, returns the original name
    and optionally logs a warning.
    
    Args:
        team_name: The team name to normalize
        mapping: Dictionary of team name mappings. If None, loads from config.
        warn_unmapped: If True, log warning for unmapped names
        
    Returns:
        Canonical team name if found in mapping, otherwise original name
        
    Examples:
        >>> normalize_team_name("Man Utd")
        "Man United"
        >>> normalize_team_name("Spurs")
        "Tottenham"
        >>> normalize_team_name("Unknown Team")
        "Unknown Team"  # Returns original, logs warning
    """
    if mapping is None:
        try:
            mapping = load_team_mapping()
        except Exception as e:
            logger.error(f"Failed to load team mapping: {e}")
            return team_name
    
    # Check if team name is in mapping
    if team_name in mapping:
        return mapping[team_name]
    
    # Not found in mapping - log warning if requested
    if warn_unmapped:
        logger.warning(f"Unmapped team name encountered: '{team_name}'")
    
    return team_name


def parse_season_range(season_range: str) -> Tuple[int, int]:
    """Parse season range string to start and end years.
    
    Converts a season range string like "2017-2026" into a tuple
    of (start_year, end_year).
    
    Args:
        season_range: Season range in format "YYYY-YYYY"
        
    Returns:
        Tuple of (start_year, end_year) as integers
        
    Raises:
        ValueError: If season_range is not in expected format
        
    Examples:
        >>> parse_season_range("2017-2026")
        (2017, 2026)
        >>> parse_season_range("2020-2023")
        (2020, 2023)
    """
    try:
        parts = season_range.split('-')
        if len(parts) != 2:
            raise ValueError(f"Expected format 'YYYY-YYYY', got '{season_range}'")
        
        start_year = int(parts[0])
        end_year = int(parts[1])
        
        # Validation
        if start_year < 1900 or start_year > 2100:
            raise ValueError(f"Start year out of reasonable range: {start_year}")
        if end_year < 1900 or end_year > 2100:
            raise ValueError(f"End year out of reasonable range: {end_year}")
        if start_year > end_year:
            raise ValueError(f"Start year ({start_year}) cannot be after end year ({end_year})")
        
        return (start_year, end_year)
    
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid season range format '{season_range}': {e}")


def format_season_code(year: int) -> str:
    """Convert a year to a 4-digit season code.
    
    Converts a season start year to the standard 4-digit format.
    For example, 2017 becomes "1718" (representing season 2017-2018).
    
    Args:
        year: The season start year
        
    Returns:
        4-digit season code string
        
    Raises:
        ValueError: If year is not in reasonable range
        
    Examples:
        >>> format_season_code(2017)
        "1718"
        >>> format_season_code(2020)
        "2021"
        >>> format_season_code(2025)
        "2526"
    """
    if year < 1900 or year > 2100:
        raise ValueError(f"Year out of reasonable range: {year}")
    
    # Extract last 2 digits of start year
    start_code = str(year)[-2:]
    
    # Calculate next year and extract last 2 digits
    next_year = year + 1
    end_code = str(next_year)[-2:]
    
    return f"{start_code}{end_code}"
