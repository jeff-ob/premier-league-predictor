"""
CSV Exporter Component
Exports scraped data to CSV files with proper sorting and documentation.
Implements: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional


class CSVExporter:
    """Exports validated data to CSV files with documentation."""
    
    def __init__(self, output_dir: str = "data/external"):
        """Initialize CSVExporter with output directory.
        
        Args:
            output_dir: Directory path for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_fbref(self, df: pd.DataFrame, start_season: str, end_season: str) -> str:
        """Export FBref data to CSV with chronological sorting by Date.
        
        Args:
            df: DataFrame containing columns ['Date', 'Season', 'HomeTeam', 'AwayTeam', 'Home_xG', 'Away_xG']
            start_season: Start season in format "2017" or "1718"
            end_season: End season in format "2026" or "2526"
            
        Returns:
            str: Path to the exported CSV file
            
        Requirements: 6.1, 6.2, 6.5
        """
        # Ensure correct column order
        required_columns = ['Date', 'Season', 'HomeTeam', 'AwayTeam', 'Home_xG', 'Away_xG']
        df = df[required_columns].copy()
        
        # Sort chronologically by Date
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Format Date as string (YYYY-MM-DD)
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        
        # Generate output filename
        output_path = self.output_dir / f"fbref_xg_{start_season}_{end_season}.csv"
        
        # Export to CSV
        df.to_csv(output_path, index=False)
        
        return str(output_path)
    
    def export_transfermarkt(self, df: pd.DataFrame, start_season: str, end_season: str) -> str:
        """Export Transfermarkt data to CSV with sorting by Season then Team.
        
        Args:
            df: DataFrame containing columns ['Season', 'Team', 'Squad_Value']
            start_season: Start season in format "2017" or "1718"
            end_season: End season in format "2026" or "2526"
            
        Returns:
            str: Path to the exported CSV file
            
        Requirements: 6.3, 6.4, 6.5
        """
        # Ensure correct column order
        required_columns = ['Season', 'Team', 'Squad_Value']
        df = df[required_columns].copy()
        
        # Sort by Season then Team
        df = df.sort_values(['Season', 'Team'])
        
        # Generate output filename
        output_path = self.output_dir / f"transfermarkt_values_{start_season}_{end_season}.csv"
        
        # Export to CSV
        df.to_csv(output_path, index=False)
        
        return str(output_path)
    
    def create_readme(self, 
                     fbref_info: Optional[dict] = None, 
                     transfermarkt_info: Optional[dict] = None) -> str:
        """Create README.md documenting the scraped data sources and structure.
        
        Args:
            fbref_info: Optional dict with keys 'filename', 'scrape_date', 'start_season', 'end_season'
            transfermarkt_info: Optional dict with same keys as fbref_info
            
        Returns:
            str: Path to the created README.md file
            
        Requirements: 6.6
        """
        readme_path = self.output_dir / "README.md"
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("# External Data Sources\n\n")
            f.write("This directory contains scraped data from external football statistics websites.\n\n")
            
            # FBref section
            if fbref_info:
                f.write("## FBref xG Data\n\n")
                f.write(f"**File:** `{fbref_info['filename']}`\n")
                f.write(f"**Source:** FBref.com\n")
                f.write(f"**Scraped:** {fbref_info['scrape_date']}\n")
                f.write(f"**Coverage:** Seasons {fbref_info['start_season']} to {fbref_info['end_season']}\n\n")
                f.write("**Columns:**\n")
                f.write("- `Date`: Match date (YYYY-MM-DD)\n")
                f.write("- `Season`: Season in 4-digit format (e.g., '1718' for 2017-2018)\n")
                f.write("- `HomeTeam`: Home team name\n")
                f.write("- `AwayTeam`: Away team name\n")
                f.write("- `Home_xG`: Expected goals for home team (float)\n")
                f.write("- `Away_xG`: Expected goals for away team (float)\n\n")
            
            # Transfermarkt section
            if transfermarkt_info:
                f.write("## Transfermarkt Squad Values\n\n")
                f.write(f"**File:** `{transfermarkt_info['filename']}`\n")
                f.write(f"**Source:** Transfermarkt.com\n")
                f.write(f"**Scraped:** {transfermarkt_info['scrape_date']}\n")
                f.write(f"**Coverage:** Seasons {transfermarkt_info['start_season']} to {transfermarkt_info['end_season']}\n\n")
                f.write("**Columns:**\n")
                f.write("- `Season`: Season in 4-digit format (e.g., '1718')\n")
                f.write("- `Team`: Team name (normalized)\n")
                f.write("- `Squad_Value`: Total squad market value in millions € (float)\n\n")
        
        return str(readme_path)
