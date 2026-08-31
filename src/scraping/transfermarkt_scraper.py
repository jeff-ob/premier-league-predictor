"""Transfermarkt scraper for extracting squad market values.

This module implements the TransfermarktScraper class that scrapes squad
market value data from Transfermarkt.com for Premier League teams.

Implements: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 8.3, 10.1, 10.2, 10.3
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from bs4 import BeautifulSoup
import re

from .base_scraper import BaseScraper
from .utils import parse_season_range, format_season_code, normalize_team_name


class TransfermarktScraper(BaseScraper):
    """Scraper for Transfermarkt.com squad market value data.
    
    Extracts squad market values for all Premier League teams by season.
    Uses CSS selector fallback strategy to handle HTML structure changes.
    
    URL Pattern:
        https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/plus/?saison_id={year}
        where {year} is the season start year (e.g., 2017 for 2017-2018)
    
    Extracted Data:
        - Season: Season code in 4-digit format (e.g., "1718")
        - Team: Team name (normalized)
        - Squad_Value: Total squad market value in millions € (float)
    
    Attributes:
        team_mapping: Dictionary for normalizing team names
        selectors: CSS selectors configuration for squad value parsing
    """
    
    def __init__(
        self,
        rate_limiter,
        cache_manager,
        validator,
        config: Dict[str, Any]
    ):
        """Initialize the Transfermarkt scraper.
        
        Args:
            rate_limiter: RateLimiter instance
            cache_manager: CacheManager instance
            validator: DataValidator instance
            config: Configuration dictionary with 'transfermarkt' and 'team_mapping' keys
        """
        super().__init__(rate_limiter, cache_manager, validator, config)
        
        # Load team name mapping
        self.team_mapping = config.get('team_mapping', {})
        
        # Extract Transfermarkt-specific config
        self.selectors = config.get('transfermarkt', {})
    
    def build_urls(self, season_range: str) -> List[str]:
        """Generate Transfermarkt URLs for season range.
        
        Implements: Requirement 2.2
        
        Creates URLs for each season in the range following the pattern:
        https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/plus/?saison_id={year}
        
        Args:
            season_range: Season range string (e.g., "2017-2026")
            
        Returns:
            List of Transfermarkt URLs to scrape
            
        Raises:
            ValueError: If season_range format is invalid
        """
        start_year, end_year = parse_season_range(season_range)
        urls = []
        
        for year in range(start_year, end_year + 1):
            url = (
                f"https://www.transfermarkt.com/premier-league/startseite/"
                f"wettbewerb/GB1/plus/?saison_id={year}"
            )
            urls.append(url)
        
        self.logger.info(
            f"Generated {len(urls)} Transfermarkt URLs for seasons "
            f"{start_year}-{end_year+1}"
        )
        
        return urls
    
    def parse_page(self, html: str, url: str) -> pd.DataFrame:
        """Parse Transfermarkt HTML to extract squad values.
        
        Implements: Requirements 2.3, 10.1, 10.2, 10.3
        
        Uses CSS selector fallback strategy:
        1. Try primary selector
        2. If no data, try fallback selector
        3. If all fail, save HTML for manual inspection
        
        Logs which selector succeeded for each page.
        
        Args:
            html: HTML content of Transfermarkt page
            url: Source URL (for logging and error handling)
            
        Returns:
            DataFrame with columns: Season, Team, Squad_Value
            Returns empty DataFrame if parsing fails
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract season from URL for data labeling
        season_year = self._extract_season_from_url(url)
        season_code = format_season_code(season_year) if season_year else "UNKNOWN"
        
        # Try CSS selectors in order of preference (Requirement 10.1, 10.2)
        selectors = self.selectors.get('squad_value', {})
        team_name_selectors = self.selectors.get('team_name', {})
        
        # We need to find the table rows, not just the value cells
        # Try to find the main table first
        table = None
        for selector_key in ['primary', 'fallback']:
            if selector_key == 'primary':
                table = soup.select_one('table.items')
            elif selector_key == 'fallback':
                table = soup.select_one('div.responsive-table table')
            
            if table:
                self.logger.debug(f"Found table using {selector_key} selector for {url}")
                break
        
        # If no table found (Requirement 10.4)
        if not table:
            self.logger.error(f"No valid table selector found for {url}")
            self._save_failed_html(html, url)
            return pd.DataFrame()
        
        # Extract rows from table
        rows = table.select('tbody tr')
        if not rows:
            self.logger.warning(f"No rows found in table for {url}")
            self._save_failed_html(html, url)
            return pd.DataFrame()
        
        # Extract data from rows
        teams = []
        for row in rows:
            try:
                team_data = self._parse_team_row(row, season_code)
                if team_data:
                    teams.append(team_data)
            except Exception as e:
                self.logger.debug(f"Failed to parse row: {e}")
                continue
        
        if teams:
            self.logger.info(
                f"Extracted {len(teams)} teams from {url}"
            )
        else:
            self.logger.warning(f"No valid teams extracted from {url}")
        
        return pd.DataFrame(teams)
    
    def _parse_team_row(self, row, season_code: str) -> Optional[Dict[str, Any]]:
        """Extract team data from a table row.
        
        Implements: Requirements 2.3, 2.4, 2.5, 8.3
        
        Extracts the following fields:
        - Season: 4-digit season code
        - Team: Team name (normalized using mapping)
        - Squad_Value: Squad market value in millions € (float)
        
        Applies team name normalization using normalize_team_name().
        Converts Squad_Value from display format (e.g., "500m €", "1.5bn €")
        to numeric millions.
        
        Args:
            row: BeautifulSoup Tag representing a table row
            season_code: 4-digit season code (e.g., "1718")
            
        Returns:
            Dictionary with team data, or None if row doesn't contain valid data
        """
        # Extract team name
        # Transfermarkt typically has team name in column 2 (td:nth-child(2))
        team_cell = row.select_one('td:nth-child(2)')
        if not team_cell:
            return None
        
        # Team name is usually in an <a> tag within the cell
        # Prefer the text content over the title attribute
        team_link = team_cell.select_one('a')
        if team_link:
            team_name = team_link.text.strip()
            # If text is empty, try title attribute as fallback
            if not team_name:
                team_name = team_link.get('title', '').strip()
        else:
            team_name = team_cell.text.strip()
        
        if not team_name:
            return None
        
        # Normalize team name using mapping (Requirement 8.3)
        team_name = normalize_team_name(team_name, self.team_mapping, warn_unmapped=True)
        
        # Extract squad value
        # Squad value is typically in column 6 (td:nth-child(6)) or a cell with specific class
        value_cell = row.select_one('td:nth-child(6)')
        if not value_cell:
            # Try alternative: look for cell with 'rechts hauptlink' classes
            value_cell = row.select_one('td.rechts.hauptlink')
        
        if not value_cell:
            return None
        
        value_str = value_cell.text.strip()
        if not value_str:
            return None
        
        # Convert squad value to numeric (Requirement 2.4)
        try:
            squad_value = self._convert_squad_value(value_str)
        except ValueError as e:
            self.logger.debug(f"Failed to convert squad value '{value_str}': {e}")
            return None
        
        return {
            'Season': season_code,
            'Team': team_name,
            'Squad_Value': squad_value
        }
    
    def _convert_squad_value(self, value_str: str) -> float:
        """Convert squad value string to numeric millions.
        
        Implements: Requirement 2.4
        
        Converts various display formats to numeric millions:
        - "500m €" → 500.0
        - "45.5m €" → 45.5
        - "1.5bn €" → 1500.0
        - "2bn €" → 2000.0
        
        Args:
            value_str: Squad value string in Transfermarkt format
            
        Returns:
            Squad value in millions € as float
            
        Raises:
            ValueError: If value_str cannot be parsed
            
        Examples:
            >>> _convert_squad_value("500m €")
            500.0
            >>> _convert_squad_value("45.5m €")
            45.5
            >>> _convert_squad_value("1.5bn €")
            1500.0
            >>> _convert_squad_value("2bn €")
            2000.0
        """
        # Clean and normalize the string
        value_str = value_str.strip().lower()
        
        # Remove currency symbols and extra spaces
        value_str = value_str.replace('€', '').replace('$', '').strip()
        
        # Extract numeric part and unit using regex
        # Pattern: captures number (with optional decimal) and unit (m, bn, b, mill, mrd)
        match = re.match(r'([0-9.,]+)\s*(m|bn|b|mill|mrd)', value_str)
        if not match:
            raise ValueError(f"Cannot parse squad value: {value_str}")
        
        numeric_str = match.group(1)
        unit = match.group(2)
        
        # Handle different decimal separators (some locales use comma)
        # Convert comma to dot for float parsing
        numeric_str = numeric_str.replace(',', '.')
        
        try:
            numeric_value = float(numeric_str)
        except ValueError:
            raise ValueError(f"Cannot parse numeric value: {numeric_str}")
        
        # Convert to millions based on unit
        if unit in ['bn', 'b', 'mrd']:  # billion / milliard
            return numeric_value * 1000  # Convert billions to millions
        elif unit in ['m', 'mill']:  # million
            return numeric_value  # Already in millions
        else:
            raise ValueError(f"Unknown unit: {unit}")
    
    def _extract_season_from_url(self, url: str) -> Optional[int]:
        """Extract season start year from Transfermarkt URL.
        
        Args:
            url: Transfermarkt URL (e.g., "...?saison_id=2017")
            
        Returns:
            Season start year as integer, or None if extraction fails
        """
        # Match pattern like "saison_id=2017"
        match = re.search(r'saison_id=(\d{4})', url)
        if match:
            return int(match.group(1))
        
        return None
