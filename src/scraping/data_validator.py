# Data validator component
# Implements: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 1.5, 2.6

import pandas as pd
from typing import List, Dict
from datetime import datetime


class DataValidator:
    """Validates scraped data for consistency and format.
    
    Performs source-specific validations:
    - FBref: xG range [0.0, 15.0], total xG < 20.0, date within season
    - Transfermarkt: Squad_Value range [10.0, 2000.0], temporal coherence (drop < 40%)
    """
    
    def __init__(self, source: str):
        """Initialize validator for a specific data source.
        
        Args:
            source: Data source identifier ('fbref' or 'transfermarkt')
        """
        self.source = source
        self.warnings = []
        self.errors = []
    
    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate DataFrame and return cleaned version.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            DataFrame with only valid rows
            
        Raises:
            ValueError: If source is unknown
        """
        if self.source == 'fbref':
            return self._validate_fbref(df)
        elif self.source == 'transfermarkt':
            return self._validate_transfermarkt(df)
        else:
            raise ValueError(f"Unknown source: {self.source}")
    
    def _validate_fbref(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate FBref xG data.
        
        Validations:
        - Home_xG and Away_xG in range [0.0, 15.0]
        - Home_xG + Away_xG < 20.0 (sanity check)
        - Date within expected season range (August to May)
        
        Args:
            df: DataFrame with FBref match data
            
        Returns:
            DataFrame with only valid rows
        """
        valid_rows = []
        
        for idx, row in df.iterrows():
            # Validate Home_xG range
            if not (0.0 <= row['Home_xG'] <= 15.0):
                self.warnings.append(
                    f"Invalid Home_xG: {row['Home_xG']} for {row['HomeTeam']} vs {row['AwayTeam']}"
                )
                continue
            
            # Validate Away_xG range
            if not (0.0 <= row['Away_xG'] <= 15.0):
                self.warnings.append(
                    f"Invalid Away_xG: {row['Away_xG']} for {row['HomeTeam']} vs {row['AwayTeam']}"
                )
                continue
            
            # Validate total xG (sanity check)
            total_xg = row['Home_xG'] + row['Away_xG']
            if total_xg >= 20.0:
                self.warnings.append(
                    f"Implausible total xG: {total_xg} for {row['HomeTeam']} vs {row['AwayTeam']}"
                )
                continue
            
            # Validate date range (August to May for football season)
            match_date = pd.to_datetime(row['Date'])
            if match_date.month < 8 and match_date.month > 5:
                self.warnings.append(
                    f"Date outside season range: {row['Date']}"
                )
                continue
            
            valid_rows.append(row)
        
        return pd.DataFrame(valid_rows)
    
    def _validate_transfermarkt(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate Transfermarkt squad values.
        
        Validations:
        - Squad_Value in range [10.0, 2000.0] millions €
        - Temporal coherence: value drops < 40% between consecutive seasons
        
        Args:
            df: DataFrame with Transfermarkt team data
            
        Returns:
            DataFrame with only valid rows
        """
        valid_rows = []
        
        # Sort by team and season for temporal coherence check
        df_sorted = df.sort_values(['Team', 'Season'])
        
        prev_team = None
        prev_value = None
        
        for idx, row in df_sorted.iterrows():
            # Validate value range
            if not (10.0 <= row['Squad_Value'] <= 2000.0):
                self.warnings.append(
                    f"Invalid Squad_Value: {row['Squad_Value']} M€ for {row['Team']} in {row['Season']}"
                )
                continue
            
            # Temporal coherence check (teams rarely lose 50%+ value instantly)
            if prev_team == row['Team'] and prev_value is not None:
                value_change = (prev_value - row['Squad_Value']) / prev_value
                if value_change > 0.4:  # 40% drop threshold
                    self.warnings.append(
                        f"Large value drop: {row['Team']} from {prev_value} to {row['Squad_Value']} M€"
                    )
            
            prev_team = row['Team']
            prev_value = row['Squad_Value']
            valid_rows.append(row)
        
        return pd.DataFrame(valid_rows)
    
    def generate_report(self, output_path: str):
        """Generate validation report with warnings and errors.
        
        Args:
            output_path: Path to save the validation report
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== Data Validation Report ===\n\n")
            f.write(f"Source: {self.source}\n")
            f.write(f"Warnings: {len(self.warnings)}\n")
            f.write(f"Errors: {len(self.errors)}\n\n")
            
            if self.warnings:
                f.write("--- Warnings ---\n")
                for warning in self.warnings:
                    f.write(f"  - {warning}\n")
            
            if self.errors:
                f.write("\n--- Errors ---\n")
                for error in self.errors:
                    f.write(f"  - {error}\n")
