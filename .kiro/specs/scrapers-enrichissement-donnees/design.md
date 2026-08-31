# Technical Design

## 1. Architecture Overview

### 1.1 Vue d'ensemble des modules

Le système de scraping est construit autour d'une architecture modulaire avec composants réutilisables :

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│    scrape_fbref.py CLI  │  scrape_transfermarkt.py CLI       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    Scraper Layer                             │
│  ┌──────────────────┐      ┌──────────────────────────┐    │
│  │  FBrefScraper    │      │ TransfermarktScraper     │    │
│  │  (xG data)       │      │ (Squad values)           │    │
│  └────────┬─────────┘      └──────────┬───────────────┘    │
│           │                            │                     │
│           └───────────┬────────────────┘                     │
│                       │ extends                              │
│           ┌───────────▼────────────┐                         │
│           │    BaseScraper         │                         │
│           │  (abstract class)      │                         │
│           └────────────────────────┘                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Core Components                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Rate    │ │  Cache   │ │  Data    │ │   CSV    │       │
│  │ Limiter  │ │ Manager  │ │Validator │ │ Exporter │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐                                  │
│  │  Config  │ │  Utils   │                                  │
│  │  Parser  │ │          │                                  │
│  └──────────┘ └──────────┘                                  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Flux de données global

```
User Input (CLI)
    │
    ├──> Parse Arguments (seasons, delay, force-refresh)
    │
    ├──> Load Config (team mapping, CSS selectors)
    │
    ├──> Initialize Components (rate limiter, cache, validator)
    │
    ▼
For each season/page:
    │
    ├──> Rate Limiter: Apply delay
    │
    ├──> Cache Manager: Check cache
    │    │
    │    ├─[HIT]──> Load HTML from cache
    │    │
    │    └─[MISS]─> Fetch from web
    │              │
    │              └──> Cache Manager: Save HTML
    │
    ├──> Scraper: Parse HTML → Extract data
    │
    ├──> Data Validator: Verify values
    │    │
    │    ├─[VALID]──> Add to dataset
    │    │
    │    └─[INVALID]─> Log warning, skip row
    │
    └──> Accumulate results
         │
         ▼
End of scraping:
    │
    ├──> CSV Exporter: Write CSV file
    │
    ├──> Generate validation report
    │
    └──> Display summary + output path
```


### 1.3 Organisation des dossiers src/scraping/

```
src/scraping/
├── __init__.py
├── base_scraper.py          # BaseScraper abstract class
├── scrape_fbref.py           # FBrefScraper + CLI entry point
├── scrape_transfermarkt.py   # TransfermarktScraper + CLI entry point
├── rate_limiter.py           # RateLimiter class
├── cache_manager.py          # CacheManager class
├── data_validator.py         # DataValidator class
├── csv_exporter.py           # CSVExporter class
├── config_parser.py          # ConfigParser class
└── utils.py                  # Helper functions (normalize_team_name, etc.)
```

## 2. Core Components

### 2.1 BaseScraper (classe abstraite)

**Responsabilité :** Fournir l'infrastructure commune aux deux scrapers (rate limiting, cache, logging, retry logic).

**Interface :**

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd

class BaseScraper(ABC):
    def __init__(self, 
                 rate_limiter: RateLimiter,
                 cache_manager: CacheManager,
                 validator: DataValidator,
                 config: Dict[str, Any]):
        self.rate_limiter = rate_limiter
        self.cache_manager = cache_manager
        self.validator = validator
        self.config = config
        self.logger = self._setup_logger()
    
    @abstractmethod
    def build_urls(self, season_range: str) -> List[str]:
        """Generate list of URLs to scrape based on season range."""
        pass
    
    @abstractmethod
    def parse_page(self, html: str, url: str) -> pd.DataFrame:
        """Parse HTML content into structured data."""
        pass
    
    def fetch_page(self, url: str, force_refresh: bool = False) -> str:
        """Fetch page with caching and retry logic."""
        # Check cache first
        if not force_refresh:
            cached_html = self.cache_manager.get(url)
            if cached_html:
                self.logger.debug(f"Cache hit: {url}")
                return cached_html
        
        # Apply rate limiting
        self.rate_limiter.wait()
        
        # Fetch with retry
        html = self._fetch_with_retry(url)
        
        # Save to cache
        self.cache_manager.save(url, html)
        
        return html

    
    def _fetch_with_retry(self, url: str, max_retries: int = 3) -> str:
        """Fetch URL with exponential backoff retry."""
        import requests
        from time import sleep
        
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, headers=self._get_headers(), timeout=30)
                
                if response.status_code == 200:
                    return response.text
                elif response.status_code in [429, 503]:
                    wait_time = 60 if attempt == 1 else 2 ** attempt
                    self.logger.warning(f"HTTP {response.status_code} for {url}, waiting {wait_time}s")
                    sleep(wait_time)
                else:
                    self.logger.error(f"HTTP {response.status_code} for {url}")
                    break
            except Exception as e:
                self.logger.error(f"Request failed (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    sleep(2 ** attempt)
        
        raise Exception(f"Failed to fetch {url} after {max_retries} attempts")
    
    def run(self, season_range: str, force_refresh: bool = False) -> pd.DataFrame:
        """Main execution method."""
        urls = self.build_urls(season_range)
        all_data = []
        
        self.logger.info(f"Starting scrape: {len(urls)} pages to process")
        
        for i, url in enumerate(urls, 1):
            try:
                html = self.fetch_page(url, force_refresh)
                df = self.parse_page(html, url)
                validated_df = self.validator.validate(df)
                all_data.append(validated_df)
                
                if i % 10 == 0:
                    self.logger.info(f"Processed {i}/{len(urls)} pages")
            except Exception as e:
                self.logger.error(f"Failed to process {url}: {e}")
                continue
        
        return pd.concat(all_data, ignore_index=True)
    
    def _get_headers(self) -> Dict[str, str]:
        """Return HTTP headers with polite user agent."""
        return {
            'User-Agent': 'Mozilla/5.0 (research bot; contact@example.com)'
        }
    
    def _setup_logger(self):
        """Setup structured logging."""
        import logging
        # Implementation details...
        pass
```


### 2.2 FBrefScraper

**Responsabilité :** Extraire les données xG depuis FBref.com pour les matchs de Premier League.

**Spécificités :**

- **URL pattern :** `https://fbref.com/en/comps/9/{season}/schedule/` où `{season}` est au format `2017-2018`
- **CSS selectors (config-driven) :**
  - Primary: `table.stats_table tbody tr`
  - Fallback: `div.table_container table tr`
  - Generic: `table tr`
- **Data extraction :** Date, HomeTeam, AwayTeam, Home_xG, Away_xG

**Interface key methods :**

```python
class FBrefScraper(BaseScraper):
    def build_urls(self, season_range: str) -> List[str]:
        """Generate FBref URLs for season range."""
        start_year, end_year = self._parse_season_range(season_range)
        urls = []
        for year in range(start_year, end_year + 1):
            season_str = f"{year}-{year+1}"
            url = f"https://fbref.com/en/comps/9/{season_str}/schedule/"
            urls.append(url)
        return urls
    
    def parse_page(self, html: str, url: str) -> pd.DataFrame:
        """Parse FBref HTML to extract xG data."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try CSS selectors in order
        selectors = self.config['fbref']['xg_table']
        for selector_key in ['primary', 'fallback', 'generic']:
            rows = soup.select(selectors[selector_key])
            if rows:
                self.logger.debug(f"Using {selector_key} selector for {url}")
                break
        else:
            self.logger.error(f"No valid selector found for {url}")
            self._save_failed_html(html, url)
            return pd.DataFrame()
        
        # Extract data from rows
        matches = []
        for row in rows:
            try:
                match_data = self._parse_match_row(row)
                if match_data:
                    matches.append(match_data)
            except Exception as e:
                self.logger.warning(f"Failed to parse row: {e}")
                continue
        
        return pd.DataFrame(matches)
    
    def _parse_match_row(self, row) -> Dict[str, Any]:
        """Extract match data from a table row."""
        # Implementation extracts: Date, Season, HomeTeam, AwayTeam, Home_xG, Away_xG
        pass
```


### 2.3 TransfermarktScraper

**Responsabilité :** Extraire les valeurs marchandes des équipes depuis Transfermarkt.com.

**Spécificités :**

- **URL pattern :** `https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/plus/?saison_id={year}` où `{year}` est l'année de début (ex: 2017 pour la saison 2017-2018)
- **CSS selectors (config-driven) :**
  - Primary: `table.items tbody tr td:nth-child(6)`
  - Fallback: `div.responsive-table td.rechts.hauptlink`
- **Data extraction :** Season, Team, Squad_Value
- **Format conversion :** "500m €" → 500.0, "1.5bn €" → 1500.0

**Interface key methods :**

```python
class TransfermarktScraper(BaseScraper):
    def build_urls(self, season_range: str) -> List[str]:
        """Generate Transfermarkt URLs for season range."""
        start_year, end_year = self._parse_season_range(season_range)
        urls = []
        for year in range(start_year, end_year + 1):
            url = f"https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/plus/?saison_id={year}"
            urls.append(url)
        return urls
    
    def parse_page(self, html: str, url: str) -> pd.DataFrame:
        """Parse Transfermarkt HTML to extract squad values."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try CSS selectors
        selectors = self.config['transfermarkt']['squad_value']
        rows = None
        for selector_key in ['primary', 'fallback']:
            rows = soup.select(selectors[selector_key])
            if rows:
                self.logger.debug(f"Using {selector_key} selector for {url}")
                break
        
        if not rows:
            self.logger.error(f"No valid selector found for {url}")
            self._save_failed_html(html, url)
            return pd.DataFrame()
        
        # Extract data
        teams = []
        for row in rows:
            try:
                team_data = self._parse_team_row(row, url)
                if team_data:
                    teams.append(team_data)
            except Exception as e:
                self.logger.warning(f"Failed to parse row: {e}")
                continue
        
        return pd.DataFrame(teams)

    
    def _parse_team_row(self, row, url: str) -> Dict[str, Any]:
        """Extract team data from a table row."""
        # Implementation extracts: Season, Team, Squad_Value
        # Applies team name normalization
        # Converts value format to numeric
        pass
    
    def _convert_squad_value(self, value_str: str) -> float:
        """Convert squad value string to numeric millions.
        
        Examples:
            "500m €" -> 500.0
            "45.5m €" -> 45.5
            "1.5bn €" -> 1500.0
            "2bn €" -> 2000.0
        """
        import re
        value_str = value_str.strip().lower()
        
        # Extract numeric part and unit
        match = re.match(r'([0-9.]+)\s*(m|bn|b)', value_str)
        if not match:
            raise ValueError(f"Cannot parse squad value: {value_str}")
        
        numeric_value = float(match.group(1))
        unit = match.group(2)
        
        if unit in ['bn', 'b']:
            return numeric_value * 1000  # Convert billions to millions
        else:
            return numeric_value  # Already in millions
```

### 2.4 RateLimiter

**Responsabilité :** Contrôler le délai entre requêtes HTTP pour respecter les ToS des sites.

**Implémentation :**

```python
import time
from threading import Lock

class RateLimiter:
    def __init__(self, delay_seconds: float = 1.0):
        self.delay = delay_seconds
        self.last_request_time = 0
        self.lock = Lock()
    
    def wait(self):
        """Apply rate limiting delay before next request."""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.delay:
                sleep_time = self.delay - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
```


### 2.5 CacheManager

**Responsabilité :** Gérer le cache filesystem pour éviter les requêtes HTTP redondantes.

**Structure du cache :**

```
data/external/cache/
├── fbref/
│   ├── 2017-2018_schedule.html
│   ├── 2018-2019_schedule.html
│   └── ...
├── transfermarkt/
│   ├── 2017_teams.html
│   ├── 2018_teams.html
│   └── ...
└── cache_index.json
```

**Implémentation :**

```python
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

class CacheManager:
    def __init__(self, cache_dir: str = "data/external/cache", ttl_days: int = 30):
        self.cache_dir = Path(cache_dir)
        self.ttl_days = ttl_days
        self.index_file = self.cache_dir / "cache_index.json"
        self._ensure_cache_dir()
        self.index = self._load_index()
    
    def _ensure_cache_dir(self):
        """Create cache directory structure."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "fbref").mkdir(exist_ok=True)
        (self.cache_dir / "transfermarkt").mkdir(exist_ok=True)
    
    def get(self, url: str) -> Optional[str]:
        """Retrieve cached HTML if valid."""
        cache_key = self._url_to_key(url)
        
        if cache_key not in self.index:
            return None
        
        cache_entry = self.index[cache_key]
        cached_time = datetime.fromisoformat(cache_entry['timestamp'])
        
        # Check TTL
        if datetime.now() - cached_time > timedelta(days=self.ttl_days):
            return None
        
        # Load HTML
        cache_path = self.cache_dir / cache_entry['file_path']
        if not cache_path.exists():
            return None
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def save(self, url: str, html: str):
        """Save HTML to cache."""
        cache_key = self._url_to_key(url)
        source = self._detect_source(url)
        file_name = self._generate_filename(url)
        file_path = f"{source}/{file_name}"
        
        full_path = self.cache_dir / file_path
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Update index
        self.index[cache_key] = {
            'url': url,
            'file_path': file_path,
            'timestamp': datetime.now().isoformat()
        }
        self._save_index()

    
    def _url_to_key(self, url: str) -> str:
        """Generate cache key from URL."""
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()
    
    def _detect_source(self, url: str) -> str:
        """Detect source from URL."""
        if 'fbref' in url:
            return 'fbref'
        elif 'transfermarkt' in url:
            return 'transfermarkt'
        else:
            return 'other'
    
    def _generate_filename(self, url: str) -> str:
        """Generate readable filename from URL."""
        # Example: extract season from URL patterns
        # fbref: "2017-2018" -> "2017-2018_schedule.html"
        # transfermarkt: "saison_id=2017" -> "2017_teams.html"
        pass
    
    def _load_index(self) -> dict:
        """Load cache index from JSON."""
        if not self.index_file.exists():
            return {}
        with open(self.index_file, 'r') as f:
            return json.load(f)
    
    def _save_index(self):
        """Save cache index to JSON."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
```

### 2.6 DataValidator

**Responsabilité :** Valider la cohérence et le format des données extraites.

**Validations implémentées :**

1. **FBref xG validations :**
   - xG values in range [0.0, 15.0]
   - Home_xG + Away_xG < 20.0 (sanity check)
   - Date within expected season range (August to May)

2. **Transfermarkt validations :**
   - Squad_Value in range [10.0, 2000.0] millions €
   - Temporal coherence: value drops < 40% between consecutive seasons
   - Season contains 20-22 teams

**Implémentation :**

```python
import pandas as pd
from typing import List, Dict
from datetime import datetime

class DataValidator:
    def __init__(self, source: str):
        self.source = source
        self.warnings = []
        self.errors = []
    
    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate DataFrame and return cleaned version."""
        if self.source == 'fbref':
            return self._validate_fbref(df)
        elif self.source == 'transfermarkt':
            return self._validate_transfermarkt(df)
        else:
            raise ValueError(f"Unknown source: {self.source}")

    
    def _validate_fbref(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate FBref xG data."""
        valid_rows = []
        
        for idx, row in df.iterrows():
            # Validate xG range
            if not (0.0 <= row['Home_xG'] <= 15.0):
                self.warnings.append(f"Invalid Home_xG: {row['Home_xG']} for {row['HomeTeam']} vs {row['AwayTeam']}")
                continue
            
            if not (0.0 <= row['Away_xG'] <= 15.0):
                self.warnings.append(f"Invalid Away_xG: {row['Away_xG']} for {row['HomeTeam']} vs {row['AwayTeam']}")
                continue
            
            # Validate total xG
            total_xg = row['Home_xG'] + row['Away_xG']
            if total_xg >= 20.0:
                self.warnings.append(f"Implausible total xG: {total_xg} for {row['HomeTeam']} vs {row['AwayTeam']}")
                continue
            
            # Validate date range (August to May)
            match_date = pd.to_datetime(row['Date'])
            if match_date.month < 8 and match_date.month > 5:
                self.warnings.append(f"Date outside season range: {row['Date']}")
                continue
            
            valid_rows.append(row)
        
        return pd.DataFrame(valid_rows)
    
    def _validate_transfermarkt(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate Transfermarkt squad values."""
        valid_rows = []
        
        # Sort by team and season for temporal coherence check
        df_sorted = df.sort_values(['Team', 'Season'])
        
        prev_team = None
        prev_value = None
        
        for idx, row in df_sorted.iterrows():
            # Validate value range
            if not (10.0 <= row['Squad_Value'] <= 2000.0):
                self.warnings.append(f"Invalid Squad_Value: {row['Squad_Value']} M€ for {row['Team']} in {row['Season']}")
                continue
            
            # Temporal coherence check
            if prev_team == row['Team'] and prev_value is not None:
                value_change = (prev_value - row['Squad_Value']) / prev_value
                if value_change > 0.4:  # 40% drop
                    self.warnings.append(f"Large value drop: {row['Team']} from {prev_value} to {row['Squad_Value']} M€")
            
            prev_team = row['Team']
            prev_value = row['Squad_Value']
            valid_rows.append(row)
        
        return pd.DataFrame(valid_rows)

    
    def generate_report(self, output_path: str):
        """Generate validation report."""
        with open(output_path, 'w') as f:
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
```

### 2.7 CSVExporter

**Responsabilité :** Exporter les données validées au format CSV avec tri chronologique.

**Formats de sortie :**

1. **FBref CSV** (`fbref_xg_2017_2026.csv`) :
   - Colonnes : `Date`, `Season`, `HomeTeam`, `AwayTeam`, `Home_xG`, `Away_xG`
   - Tri : chronologique par Date

2. **Transfermarkt CSV** (`transfermarkt_values_2009_2026.csv`) :
   - Colonnes : `Season`, `Team`, `Squad_Value`
   - Tri : par Season puis Team

**Implémentation :**

```python
import pandas as pd
from pathlib import Path

class CSVExporter:
    def __init__(self, output_dir: str = "data/external"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_fbref(self, df: pd.DataFrame, start_season: str, end_season: str) -> str:
        """Export FBref data to CSV."""
        # Ensure correct column order
        df = df[['Date', 'Season', 'HomeTeam', 'AwayTeam', 'Home_xG', 'Away_xG']]
        
        # Sort chronologically
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Format Date as string
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        
        # Export
        output_path = self.output_dir / f"fbref_xg_{start_season}_{end_season}.csv"
        df.to_csv(output_path, index=False)
        
        return str(output_path)

    
    def export_transfermarkt(self, df: pd.DataFrame, start_season: str, end_season: str) -> str:
        """Export Transfermarkt data to CSV."""
        # Ensure correct column order
        df = df[['Season', 'Team', 'Squad_Value']]
        
        # Sort by Season then Team
        df = df.sort_values(['Season', 'Team'])
        
        # Export
        output_path = self.output_dir / f"transfermarkt_values_{start_season}_{end_season}.csv"
        df.to_csv(output_path, index=False)
        
        return str(output_path)
    
    def create_readme(self, fbref_info: dict = None, transfermarkt_info: dict = None):
        """Create README.md documenting the scraped data."""
        readme_path = self.output_dir / "README.md"
        
        with open(readme_path, 'w') as f:
            f.write("# External Data Sources\n\n")
            f.write("This directory contains scraped data from external football statistics websites.\n\n")
            
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
```


### 2.8 ConfigParser

**Responsabilité :** Charger et valider les fichiers de configuration JSON.

**Fichiers de configuration :**

1. **`config/team_names_mapping.json`** : Mapping des variations de noms d'équipes
2. **`config/scraping_selectors.json`** : CSS selectors avec dates de vérification

**Implémentation :**

```python
import json
from pathlib import Path
from typing import Dict, Any

class ConfigParser:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
    
    def load_team_mapping(self) -> Dict[str, str]:
        """Load team name mapping configuration."""
        mapping_file = self.config_dir / "team_names_mapping.json"
        
        if not mapping_file.exists():
            raise FileNotFoundError(f"Team mapping file not found: {mapping_file}")
        
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        # Validate structure
        if not isinstance(mapping, dict):
            raise ValueError("Team mapping must be a dictionary")
        
        return mapping
    
    def load_selectors(self) -> Dict[str, Any]:
        """Load CSS selectors configuration."""
        selectors_file = self.config_dir / "scraping_selectors.json"
        
        if not selectors_file.exists():
            raise FileNotFoundError(f"Selectors file not found: {selectors_file}")
        
        with open(selectors_file, 'r', encoding='utf-8') as f:
            selectors = json.load(f)
        
        # Validate structure
        required_sources = ['fbref', 'transfermarkt']
        for source in required_sources:
            if source not in selectors:
                raise ValueError(f"Missing selectors for source: {source}")
        
        return selectors
    
    def save_json(self, data: Dict[str, Any], filename: str):
        """Pretty print JSON configuration to file."""
        output_path = self.config_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
```

## 3. Technical Choices

### 3.1 Librairies Python

**Choix et justifications :**

1. **`requests`** (vs httpx)
   - Raison : Maturité, stabilité, documentation extensive
   - Usage : HTTP requests avec retry logic

2. **`BeautifulSoup4`** (vs lxml)
   - Raison : API simple, tolérant aux HTML mal formés
   - Usage : Parsing HTML avec CSS selectors

3. **`pandas`**
   - Raison : Manipulation de données tabulaires, export CSV intégré
   - Usage : Stockage intermédiaire et validation de données

4. **`argparse`** (vs click)
   - Raison : Bibliothèque standard, pas de dépendance externe
   - Usage : CLI parsing

5. **`logging`**
   - Raison : Bibliothèque standard, logs structurés avec levels
   - Usage : Debugging et monitoring du scraping


### 3.2 Error Handling

**Stratégie de gestion des erreurs :**

1. **Retry avec exponential backoff :**
   - Tentative 1 : 1s delay
   - Tentative 2 : 2s delay
   - Tentative 3 : 4s delay
   - Maximum 3 tentatives avant abandon

2. **HTTP status codes :**
   - 200 : Success, continue
   - 429/503 : Wait 60s, retry
   - 404 : Log error, skip page
   - Other : Log error, retry with backoff

3. **Logging levels :**
   - `DEBUG` : Détails de parsing (selector utilisé, cache hit/miss)
   - `INFO` : Progression (processed 20/380 matches)
   - `WARNING` : Validation issues (valeur hors range, nom d'équipe inconnu)
   - `ERROR` : Échecs critiques (page non récupérable, parsing total failure)

4. **Continuation après erreur :**
   - Une page qui échoue ne doit pas bloquer tout le scraping
   - Log error + continue avec la page suivante
   - Summary final indique succès/échecs

**Exemple de pattern :**

```python
for url in urls:
    try:
        html = self.fetch_page(url)
        df = self.parse_page(html, url)
        all_data.append(df)
    except Exception as e:
        self.logger.error(f"Failed to process {url}: {e}")
        continue  # Continue avec la page suivante
```

### 3.3 Testing Strategy

**Types de tests :**

1. **Tests unitaires (pytest) :**
   - Chaque composant testé isolément
   - Mocking des requêtes HTTP (`requests.get`)
   - Tests offline avec HTML fixtures

2. **Property-based testing (hypothesis) :**
   - Test xG parsing : génère valeurs 0-15, vérifie round-trip
   - Test Squad_Value conversion : génère formats variés, vérifie conversion
   - Test team normalization : génère variations, vérifie mapping
   - Test Date parsing : génère dates ISO, vérifie round-trip

3. **Structure des tests :**

```
tests/
├── __init__.py
├── test_base_scraper.py
├── test_fbref_scraper.py
├── test_transfermarkt_scraper.py
├── test_rate_limiter.py
├── test_cache_manager.py
├── test_data_validator.py
├── test_csv_exporter.py
├── test_config_parser.py
├── test_utils.py
├── fixtures/
│   ├── fbref_sample.html
│   ├── transfermarkt_sample.html
│   └── config_samples.json
└── property_tests/
    ├── test_xg_parsing_properties.py
    ├── test_squad_value_properties.py
    └── test_team_normalization_properties.py
```


## 4. Data Structures

### 4.1 Classes principales

**Hiérarchie complète :**

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd

# Abstract base class
class BaseScraper(ABC):
    def __init__(self, 
                 rate_limiter: RateLimiter,
                 cache_manager: CacheManager,
                 validator: DataValidator,
                 config: Dict[str, Any]):
        self.rate_limiter = rate_limiter
        self.cache_manager = cache_manager
        self.validator = validator
        self.config = config
        self.logger = self._setup_logger()
    
    @abstractmethod
    def build_urls(self, season_range: str) -> List[str]:
        """Generate list of URLs to scrape."""
        pass
    
    @abstractmethod
    def parse_page(self, html: str, url: str) -> pd.DataFrame:
        """Parse HTML into structured data."""
        pass
    
    def fetch_page(self, url: str, force_refresh: bool = False) -> str:
        """Fetch page with caching and retry."""
        pass
    
    def run(self, season_range: str, force_refresh: bool = False) -> pd.DataFrame:
        """Main execution method."""
        pass

# Concrete implementations
class FBrefScraper(BaseScraper):
    def build_urls(self, season_range: str) -> List[str]:
        """Generate FBref URLs."""
        pass
    
    def parse_page(self, html: str, url: str) -> pd.DataFrame:
        """Parse FBref xG data."""
        pass
    
    def _parse_match_row(self, row) -> Dict[str, Any]:
        """Extract match data from table row."""
        return {
            'Date': str,
            'Season': str,  # Format: "1718" for 2017-2018
            'HomeTeam': str,
            'AwayTeam': str,
            'Home_xG': float,
            'Away_xG': float
        }

class TransfermarktScraper(BaseScraper):
    def build_urls(self, season_range: str) -> List[str]:
        """Generate Transfermarkt URLs."""
        pass
    
    def parse_page(self, html: str, url: str) -> pd.DataFrame:
        """Parse Transfermarkt squad values."""
        pass
    
    def _parse_team_row(self, row, url: str) -> Dict[str, Any]:
        """Extract team data from table row."""
        return {
            'Season': str,  # Format: "1718"
            'Team': str,
            'Squad_Value': float  # In millions €
        }
    
    def _convert_squad_value(self, value_str: str) -> float:
        """Convert display format to numeric millions."""
        pass
```


### 4.2 JSON Schemas

**`config/team_names_mapping.json`** :

```json
{
  "Man Utd": "Man United",
  "Manchester United": "Man United",
  "Spurs": "Tottenham",
  "Tottenham Hotspur": "Tottenham",
  "Newcastle": "Newcastle United",
  "Wolves": "Wolverhampton",
  "Nott'ham Forest": "Nottingham Forest",
  "Brighton": "Brighton and Hove Albion",
  "West Ham": "West Ham United",
  "Leicester": "Leicester City"
}
```

**`config/scraping_selectors.json`** :

```json
{
  "fbref": {
    "xg_table": {
      "primary": "table.stats_table tbody tr",
      "fallback": "div.table_container table tr",
      "generic": "table tr",
      "last_verified": "2026-08-05"
    },
    "xg_columns": {
      "date": "td[data-stat='date']",
      "home_team": "td[data-stat='home_team']",
      "away_team": "td[data-stat='away_team']",
      "home_xg": "td[data-stat='home_xg']",
      "away_xg": "td[data-stat='away_xg']"
    }
  },
  "transfermarkt": {
    "squad_value": {
      "primary": "table.items tbody tr td:nth-child(6)",
      "fallback": "div.responsive-table td.rechts.hauptlink",
      "last_verified": "2026-08-05"
    },
    "team_name": {
      "primary": "table.items tbody tr td:nth-child(2) a",
      "fallback": "div.responsive-table td.hauptlink a"
    }
  }
}
```

**`data/external/cache/cache_index.json`** :

```json
{
  "a3f8e9b2c1d4f6e7": {
    "url": "https://fbref.com/en/comps/9/2017-2018/schedule/",
    "file_path": "fbref/2017-2018_schedule.html",
    "timestamp": "2026-08-05T14:30:22"
  },
  "b7c4d1e9f2a8b6c3": {
    "url": "https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/plus/?saison_id=2017",
    "file_path": "transfermarkt/2017_teams.html",
    "timestamp": "2026-08-05T15:01:33"
  }
}
```


## 5. Sequence Diagrams (texte)

### 5.1 Flow nominal scraping (FBref example)

```
User → CLI (python scrape_fbref.py --seasons 2017-2026)
  │
  ├─> Parse arguments (start_year=2017, end_year=2026, delay=1.0)
  │
  ├─> Load config files
  │   ├─> ConfigParser.load_team_mapping() → team_mapping dict
  │   └─> ConfigParser.load_selectors() → selectors dict
  │
  ├─> Initialize components
  │   ├─> RateLimiter(delay=1.0)
  │   ├─> CacheManager(cache_dir, ttl=30)
  │   ├─> DataValidator(source='fbref')
  │   └─> FBrefScraper(rate_limiter, cache_manager, validator, config)
  │
  ├─> FBrefScraper.build_urls("2017-2026")
  │   └─> Returns: [url_2017, url_2018, ..., url_2026]
  │
  └─> For each URL:
      │
      ├─> FBrefScraper.fetch_page(url)
      │   │
      │   ├─> CacheManager.get(url)
      │   │   ├─[MISS]─> Return None
      │   │   └─[HIT]──> Return cached HTML
      │   │
      │   ├─> RateLimiter.wait()
      │   │   └─> Sleep if needed (1s delay)
      │   │
      │   ├─> requests.get(url, headers={'User-Agent': ...})
      │   │   └─> Returns: HTTP 200 + HTML
      │   │
      │   └─> CacheManager.save(url, html)
      │       └─> Write to data/external/cache/fbref/2017-2018_schedule.html
      │
      ├─> FBrefScraper.parse_page(html, url)
      │   │
      │   ├─> BeautifulSoup(html)
      │   │
      │   ├─> Try selector strategies (primary → fallback → generic)
      │   │   └─> soup.select("table.stats_table tbody tr")
      │   │
      │   ├─> For each row:
      │   │   └─> _parse_match_row(row)
      │   │       └─> Returns: {Date, Season, HomeTeam, AwayTeam, Home_xG, Away_xG}
      │   │
      │   └─> Returns: pd.DataFrame(matches)
      │
      ├─> DataValidator.validate(df)
      │   │
      │   ├─> For each row: check xG in [0, 15], total_xg < 20, date valid
      │   │   ├─[VALID]─> Keep row
      │   │   └─[INVALID]─> Log warning, skip row
      │   │
      │   └─> Returns: validated_df
      │
      └─> Append validated_df to all_data list

After all URLs processed:
  │
  ├─> pd.concat(all_data) → final_df
  │
  ├─> CSVExporter.export_fbref(final_df, "2017", "2026")
  │   ├─> Sort by Date
  │   └─> Write to data/external/fbref_xg_2017_2026.csv
  │
  ├─> DataValidator.generate_report()
  │   └─> Write to data/external/validation_report_fbref_20260805.txt
  │
  └─> Display summary:
      "✓ Scraping complete: 380 matches scraped, 378 valid, 2 warnings"
      "Output: data/external/fbref_xg_2017_2026.csv"
```


### 5.2 Flow avec cache hit

```
User → CLI (python scrape_fbref.py --seasons 2017-2026)
  │
  └─> For URL https://fbref.com/.../2017-2018/schedule/:
      │
      ├─> FBrefScraper.fetch_page(url, force_refresh=False)
      │   │
      │   ├─> CacheManager.get(url)
      │   │   │
      │   │   ├─> url_to_key(url) → "a3f8e9b2c1d4f6e7"
      │   │   │
      │   │   ├─> Check cache_index.json
      │   │   │   └─> Entry exists: file_path="fbref/2017-2018_schedule.html"
      │   │   │                     timestamp="2026-08-05T14:30:22"
      │   │   │
      │   │   ├─> Check TTL (now - cached_time < 30 days)
      │   │   │   └─> Valid: 0 days < 30 days
      │   │   │
      │   │   ├─> Read file: data/external/cache/fbref/2017-2018_schedule.html
      │   │   │
      │   │   └─> Return HTML (CACHE HIT)
      │   │
      │   ├─> Log: "Cache hit: https://fbref.com/.../2017-2018/schedule/"
      │   │
      │   └─> Return cached HTML (NO HTTP REQUEST MADE)
      │
      ├─> FBrefScraper.parse_page(html, url)
      │   └─> Parse and extract data as normal
      │
      └─> Continue with validation and export
```

**Performance gain :** Re-run du scraping sur 10 saisons = 10 cache hits = 0 HTTP requests = ~1 seconde au lieu de ~10 secondes.

### 5.3 Flow avec erreur + retry

```
User → CLI (python scrape_transfermarkt.py --seasons 2023-2023)
  │
  └─> For URL https://www.transfermarkt.com/.../saison_id=2023:
      │
      ├─> TransfermarktScraper.fetch_page(url)
      │   │
      │   ├─> CacheManager.get(url) → None (MISS)
      │   │
      │   ├─> RateLimiter.wait() → Sleep 1s
      │   │
      │   └─> _fetch_with_retry(url, max_retries=3)
      │       │
      │       ├─[Attempt 1]─> requests.get(url)
      │       │   └─> Raises: ConnectionError (network issue)
      │       │
      │       ├─> Log: "Request failed (attempt 1/3): ConnectionError"
      │       ├─> Sleep 2^1 = 2 seconds
      │       │
      │       ├─[Attempt 2]─> requests.get(url)
      │       │   └─> Returns: HTTP 503 Service Unavailable
      │       │
      │       ├─> Log: "HTTP 503 for URL, waiting 4s"
      │       ├─> Sleep 2^2 = 4 seconds
      │       │
      │       ├─[Attempt 3]─> requests.get(url)
      │       │   └─> Returns: HTTP 200 OK + HTML
      │       │
      │       └─> Return HTML (SUCCESS)
      │
      ├─> CacheManager.save(url, html)
      │   └─> Write to cache
      │
      └─> Continue with parsing and validation
```

**Résultat :** La page problématique est récupérée après 3 tentatives. Total delay = 2s + 4s = 6s pour cette page.

