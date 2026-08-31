"""FBref scraper for extracting xG (expected goals) data.

This module implements the FBrefScraper class that scrapes xG statistics
from FBref.com for Premier League matches.

Implements: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 10.1, 10.2, 10.3, 10.4
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

from .base_scraper import BaseScraper
from .utils import parse_season_range, format_season_code, normalize_team_name


class FBrefScraper(BaseScraper):
    """Scraper for FBref.com xG (expected goals) data.
    
    Extracts match-level xG statistics from FBref's Premier League schedule pages.
    Uses CSS selector fallback strategy to handle HTML structure changes.
    
    URL Pattern:
        https://fbref.com/en/comps/9/{season}/schedule/
        where {season} is in format "YYYY-YYYY" (e.g., "2017-2018")
    
    Extracted Data:
        - Date: Match date (YYYY-MM-DD)
        - Season: Season code in 4-digit format (e.g., "1718")
        - HomeTeam: Home team name (normalized)
        - AwayTeam: Away team name (normalized)
        - Home_xG: Expected goals for home team (float)
        - Away_xG: Expected goals for away team (float)
    
    Attributes:
        team_mapping: Dictionary for normalizing team names
        selectors: CSS selectors configuration for xG table parsing
    """
    
    def __init__(
        self,
        rate_limiter,
        cache_manager,
        validator,
        config: Dict[str, Any]
    ):
        """Initialize the FBref scraper.
        
        Args:
            rate_limiter: RateLimiter instance
            cache_manager: CacheManager instance
            validator: DataValidator instance
            config: Configuration dictionary with 'fbref' and 'team_mapping' keys
        """
        super().__init__(rate_limiter, cache_manager, validator, config)
        
        # Load team name mapping
        self.team_mapping = config.get('team_mapping', {})
        
        # Extract FBref-specific config
        self.selectors = config.get('fbref', {})
        
        # Minimum season for xG data (before 2017/18 not available on FBref)
        self.min_season_year = 2017
    
    def build_urls(self, season_range: str) -> List[str]:
        """Generate FBref URLs for season range.
        
        Implements: Requirement 1.2
        
        Creates URLs for each season in the range following the pattern:
        https://fbref.com/en/comps/9/YYYY-YYYY/schedule/
        
        Logs warnings for seasons before 2017/18 as xG data is not available.
        
        Args:
            season_range: Season range string (e.g., "2017-2026")
            
        Returns:
            List of FBref schedule URLs to scrape
            
        Raises:
            ValueError: If season_range format is invalid
        """
        start_year, end_year = parse_season_range(season_range)
        urls = []
        
        for year in range(start_year, end_year + 1):
            # Check if season has xG data (Requirement 1.4)
            if year < self.min_season_year:
                self.logger.warning(
                    f"Season {year}-{year+1} is before 2017/18 - "
                    f"xG data not available on FBref, skipping"
                )
                continue
            
            season_str = f"{year}-{year+1}"
            url = f"https://fbref.com/en/comps/9/{season_str}/schedule/"
            urls.append(url)
        
        self.logger.info(
            f"Generated {len(urls)} FBref URLs for seasons "
            f"{max(start_year, self.min_season_year)}-{end_year+1}"
        )
        
        return urls
    
    def parse_page(self, html: str, url: str) -> pd.DataFrame:
        """Parse FBref HTML to extract xG data.
        
        Implements: Requirements 1.3, 1.6, 10.1, 10.2, 10.3, 10.4
        
        Uses CSS selector fallback strategy:
        1. Try primary selector (table.stats_table tbody tr)
        2. If no data, try fallback selector (div.table_container table tr)
        3. If no data, try generic selector (table tr)
        4. If all fail, save HTML for manual inspection
        
        Logs which selector succeeded for each page.
        
        Args:
            html: HTML content of FBref schedule page
            url: Source URL (for logging and error handling)
            
        Returns:
            DataFrame with columns: Date, Season, HomeTeam, AwayTeam, Home_xG, Away_xG
            Returns empty DataFrame if parsing fails
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract season from URL for data labeling
        season_year = self._extract_season_from_url(url)
        season_code = format_season_code(season_year) if season_year else "UNKNOWN"
        
        # Try CSS selectors in order of preference (Requirement 10.1, 10.2, 10.3)
        selectors = self.selectors.get('xg_table', {})
        rows = None
        used_selector = None
        
        for selector_key in ['primary', 'fallback', 'generic']:
            selector = selectors.get(selector_key)
            if not selector:
                continue
            
            rows = soup.select(selector)
            if rows:
                used_selector = selector_key
                self.logger.debug(
                    f"Using {selector_key} selector ('{selector}') for {url}"
                )
                break
        
        # If all selectors failed (Requirement 10.4)
        if not rows:
            self.logger.error(f"No valid selector found for {url}")
            self._save_failed_html(html, url)
            return pd.DataFrame()
        
        # Extract data from rows
        matches = []
        for row in rows:
            try:
                match_data = self._parse_match_row(row, season_code)
                if match_data:
                    matches.append(match_data)
            except Exception as e:
                self.logger.debug(f"Failed to parse row: {e}")
                continue
        
        if matches:
            self.logger.info(
                f"Extracted {len(matches)} matches from {url} "
                f"using {used_selector} selector"
            )
        else:
            self.logger.warning(f"No valid matches extracted from {url}")
        
        return pd.DataFrame(matches)
    
    def _parse_match_row(self, row, season_code: str) -> Optional[Dict[str, Any]]:
        """Extract match data from a table row.
        
        Implements: Requirement 1.3
        
        Extracts the following fields:
        - Date: Match date in YYYY-MM-DD format
        - Season: 4-digit season code
        - HomeTeam: Home team name (normalized)
        - AwayTeam: Away team name (normalized)
        - Home_xG: Expected goals for home team (float)
        - Away_xG: Expected goals for away team (float)
        
        Args:
            row: BeautifulSoup Tag representing a table row
            season_code: 4-digit season code (e.g., "1718")
            
        Returns:
            Dictionary with match data, or None if row doesn't contain valid data
        """
        # Get column selectors from config
        col_selectors = self.selectors.get('xg_columns', {})
        
        # Extract date
        date_cell = row.select_one(col_selectors.get('date', 'td[data-stat="date"]'))
        if not date_cell or not date_cell.text.strip():
            return None
        
        date_str = date_cell.text.strip()
        
        # Parse date - FBref uses format like "2017-08-11"
        try:
            match_date = datetime.strptime(date_str, '%Y-%m-%d')
            date_formatted = match_date.strftime('%Y-%m-%d')
        except ValueError:
            # Try alternative formats if needed
            self.logger.debug(f"Could not parse date: {date_str}")
            return None
        
        # Extract team names
        home_cell = row.select_one(col_selectors.get('home_team', 'td[data-stat="home_team"]'))
        away_cell = row.select_one(col_selectors.get('away_team', 'td[data-stat="away_team"]'))
        
        if not home_cell or not away_cell:
            return None
        
        home_team = home_cell.text.strip()
        away_team = away_cell.text.strip()
        
        if not home_team or not away_team:
            return None
        
        # Normalize team names using mapping
        home_team = normalize_team_name(home_team, self.team_mapping, warn_unmapped=False)
        away_team = normalize_team_name(away_team, self.team_mapping, warn_unmapped=False)
        
        # Extract xG values
        home_xg_cell = row.select_one(col_selectors.get('home_xg', 'td[data-stat="home_xg"]'))
        away_xg_cell = row.select_one(col_selectors.get('away_xg', 'td[data-stat="away_xg"]'))
        
        if not home_xg_cell or not away_xg_cell:
            return None
        
        home_xg_str = home_xg_cell.text.strip()
        away_xg_str = away_xg_cell.text.strip()
        
        # Convert xG to float
        try:
            home_xg = float(home_xg_str) if home_xg_str else None
            away_xg = float(away_xg_str) if away_xg_str else None
        except ValueError:
            # xG might be missing for upcoming matches
            return None
        
        # Skip rows with missing xG data
        if home_xg is None or away_xg is None:
            return None
        
        return {
            'Date': date_formatted,
            'Season': season_code,
            'HomeTeam': home_team,
            'AwayTeam': away_team,
            'Home_xG': home_xg,
            'Away_xG': away_xg
        }
    
    def _extract_season_from_url(self, url: str) -> Optional[int]:
        """Extract season start year from FBref URL.
        
        Args:
            url: FBref URL (e.g., "https://fbref.com/en/comps/9/2017-2018/schedule/")
            
        Returns:
            Season start year as integer, or None if extraction fails
        """
        import re
        
        # Match pattern like "2017-2018"
        match = re.search(r'/(\d{4})-(\d{4})/', url)
        if match:
            return int(match.group(1))
        
        return None
