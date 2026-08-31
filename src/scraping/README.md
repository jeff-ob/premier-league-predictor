# Web Scrapers for Premier League Data Enrichment

This module provides two production-ready web scrapers for enriching Premier League match prediction datasets with external data sources.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Output Files](#output-files)
- [Components](#components)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

This scraping module extracts two types of data:

1. **FBref Scraper**: Expected Goals (xG) statistics for Premier League matches
2. **Transfermarkt Scraper**: Squad market values for Premier League teams

Both scrapers are designed to:
- Respect website terms of service with rate limiting
- Cache downloaded pages to avoid redundant requests
- Validate extracted data for quality assurance
- Export clean CSV files ready for machine learning pipelines

## Features

### Core Capabilities

✅ **Rate Limiting** - Configurable delays between requests (default: 1.0s)  
✅ **Intelligent Caching** - 30-day TTL cache system to minimize HTTP requests  
✅ **Data Validation** - Automatic detection of invalid or implausible values  
✅ **Error Handling** - Robust retry logic with exponential backoff  
✅ **Progress Logging** - Detailed logs saved to timestamped files  
✅ **CLI Interface** - User-friendly command-line tools  
✅ **CSV Export** - Clean, sorted CSV output with documentation  

### Data Quality

- xG values validated to be within realistic ranges [0.0, 15.0]
- Squad values checked for temporal coherence (no sudden 40%+ drops)
- Team name normalization for consistency across sources
- Automatic generation of validation reports

## Architecture

```
src/scraping/
├── CLI Scripts
│   ├── scrape_fbref.py              # FBref CLI entry point
│   └── scrape_transfermarkt.py      # Transfermarkt CLI entry point
│
├── Scrapers
│   ├── base_scraper.py              # Abstract base class
│   ├── fbref_scraper.py             # FBref implementation
│   └── transfermarkt_scraper.py     # Transfermarkt implementation
│
├── Core Components
│   ├── rate_limiter.py              # Request throttling
│   ├── cache_manager.py             # Filesystem cache
│   ├── data_validator.py            # Data quality checks
│   ├── csv_exporter.py              # CSV generation
│   └── config_parser.py             # Configuration loading
│
└── Utilities
    └── utils.py                     # Helper functions
```

### Design Patterns

- **Template Method**: BaseScraper defines workflow, subclasses implement specifics
- **Strategy Pattern**: CSS selector fallback strategies
- **Dependency Injection**: Components injected into scrapers
- **Single Responsibility**: Each component has one clear purpose

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Install Dependencies

**Full project:**
```bash
pip install -r requirements.txt
```

**Scraping module only:**
```bash
pip install -r requirements-scraping.txt
```

### Verify Installation

```bash
python -m pytest tests/test_dependencies.py -v
```

Expected output:
```
✓ All core dependencies available
requests: 2.32.4
beautifulsoup4: 4.11.1
pandas: 2.3.1
pytest: 7.1.2
```

## Quick Start

### FBref - Scrape xG Data

```bash
# Scrape xG data for 2023-2024 season
python -m src.scraping.scrape_fbref --seasons 2023-2024
```

Output:
```
✓ Total matches collected:  380
✓ CSV output:               data/external/fbref_xg_2324_2425.csv
```

### Transfermarkt - Scrape Squad Values

```bash
# Scrape squad values for 2023-2024 season
python -m src.scraping.scrape_transfermarkt --seasons 2023-2024
```

Output:
```
✓ Total team valuations:    20
✓ CSV output:               data/external/transfermarkt_values_2324_2425.csv
```

## Usage

### FBref Scraper

#### Basic Usage

```bash
python -m src.scraping.scrape_fbref --seasons 2023-2024
```

#### Advanced Options

```bash
# Multiple seasons with custom delay
python -m src.scraping.scrape_fbref --seasons 2017-2026 --delay 2.0

# Force refresh (ignore cache)
python -m src.scraping.scrape_fbref --seasons 2023-2024 --force-refresh

# Combine all options
python -m src.scraping.scrape_fbref --seasons 2020-2024 --delay 1.5 --force-refresh
```

#### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--seasons` | str | Yes | - | Season range (format: YYYY-YYYY) |
| `--delay` | float | No | 1.0 | Delay in seconds between requests |
| `--force-refresh` | flag | No | False | Ignore cache and re-download |

#### Help

```bash
python -m src.scraping.scrape_fbref --help
```

### Transfermarkt Scraper

#### Basic Usage

```bash
python -m src.scraping.scrape_transfermarkt --seasons 2023-2024
```

#### Advanced Options

Same as FBref scraper - see above.

#### Arguments

Identical to FBref scraper arguments.

### Python API Usage

You can also use the scrapers programmatically:

```python
from src.scraping.rate_limiter import RateLimiter
from src.scraping.cache_manager import CacheManager
from src.scraping.data_validator import DataValidator
from src.scraping.csv_exporter import CSVExporter
from src.scraping.config_parser import ConfigParser
from src.scraping.fbref_scraper import FBrefScraper

# Load configuration
config_parser = ConfigParser()
team_mapping = config_parser.load_team_mapping()
selectors = config_parser.load_selectors()

# Initialize components
rate_limiter = RateLimiter(delay_seconds=1.0)
cache_manager = CacheManager()
validator = DataValidator(source='fbref')
exporter = CSVExporter()

# Create scraper config
scraper_config = {
    'team_mapping': team_mapping,
    'fbref': selectors['fbref']
}

# Initialize and run scraper
scraper = FBrefScraper(
    rate_limiter=rate_limiter,
    cache_manager=cache_manager,
    validator=validator,
    config=scraper_config
)

# Run scraping
df = scraper.run(season_range="2023-2024", force_refresh=False)

# Export to CSV
csv_path = exporter.export_fbref(df, start_season="2324", end_season="2425")
print(f"Exported to: {csv_path}")
```

## Configuration

### Configuration Files

Located in `config/` directory:

#### 1. team_names_mapping.json

Maps team name variations to canonical names:

```json
{
  "Man Utd": "Man United",
  "Man City": "Manchester City",
  "Spurs": "Tottenham",
  "Brighton": "Brighton and Hove Albion",
  ...
}
```

**Purpose:** Ensure consistency across different data sources.

#### 2. scraping_selectors.json

CSS selectors for HTML parsing:

```json
{
  "fbref": {
    "xg_table": {
      "primary": "table.stats_table tbody tr",
      "fallback": "div.table_container table tr",
      "generic": "table tr"
    },
    "last_verified": "2026-08-13"
  },
  "transfermarkt": {
    "squad_value": {
      "primary": "table.items tbody tr td:nth-child(6)",
      "fallback": "div.responsive-table td.rechts.hauptlink"
    },
    "last_verified": "2026-08-13"
  }
}
```

**Purpose:** Adapt to website structure changes without code modifications.

### Modifying Configuration

#### Add Team Name Mapping

Edit `config/team_names_mapping.json`:

```json
{
  "New Variation": "Canonical Name",
  ...
}
```

#### Update CSS Selectors

Edit `config/scraping_selectors.json`:

```json
{
  "fbref": {
    "xg_table": {
      "primary": "new.selector",
      ...
    }
  }
}
```

Update `last_verified` date after verification.

## Output Files

### FBref CSV Format

**Filename:** `data/external/fbref_xg_{start}_{end}.csv`

**Columns:**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Date | string | Match date (YYYY-MM-DD) | 2023-08-12 |
| Season | string | Season code (4 digits) | 2324 |
| HomeTeam | string | Home team name | Arsenal |
| AwayTeam | string | Away team name | Chelsea |
| Home_xG | float | Home team expected goals | 2.5 |
| Away_xG | float | Away team expected goals | 1.3 |

**Sorting:** Chronological by Date

**Example:**
```csv
Date,Season,HomeTeam,AwayTeam,Home_xG,Away_xG
2023-08-12,2324,Arsenal,Chelsea,2.5,1.3
2023-08-13,2324,Liverpool,Man United,3.2,0.8
```

### Transfermarkt CSV Format

**Filename:** `data/external/transfermarkt_values_{start}_{end}.csv`

**Columns:**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Season | string | Season code (4 digits) | 2324 |
| Team | string | Team name (normalized) | Arsenal |
| Squad_Value | float | Total squad value (millions €) | 850.5 |

**Sorting:** By Season, then Team

**Example:**
```csv
Season,Team,Squad_Value
2324,Arsenal,850.5
2324,Chelsea,725.3
2324,Liverpool,920.0
```

### Validation Reports

**Location:** `data/external/validation_report_{source}_{timestamp}.txt`

**Contents:**
- Number of warnings and errors
- List of invalid data points
- Reason for rejection

**Example:**
```
=== Data Validation Report ===

Source: fbref
Warnings: 2
Errors: 0

--- Warnings ---
  - Invalid Home_xG: 16.5 for Arsenal vs Chelsea
  - Date outside season range: 2023-07-15
```

### Cache Files

**Location:** `data/external/cache/{source}/{identifier}.html`

**Structure:**
```
data/external/cache/
├── fbref/
│   ├── 2023-2024_schedule.html
│   └── 2024-2025_schedule.html
├── transfermarkt/
│   ├── 2023_teams.html
│   └── 2024_teams.html
└── cache_index.json
```

**Cache TTL:** 30 days (configurable in `CacheManager`)

### Log Files

**Location:** `logs/scraping_{source}_{timestamp}.log`

**Contents:**
- Timestamped log entries
- Progress updates
- Error messages
- Performance metrics

## Components

### BaseScraper (Abstract Class)

**Purpose:** Provides common infrastructure for all scrapers

**Key Methods:**
- `fetch_page(url, force_refresh)`: Fetch with caching and retries
- `run(season_range, force_refresh)`: Main execution workflow
- `_fetch_with_retry(url)`: HTTP with exponential backoff

**Implemented by:** FBrefScraper, TransfermarktScraper

### FBrefScraper

**Purpose:** Extract xG data from FBref.com

**Data Source:** https://fbref.com/en/comps/9/

**Key Features:**
- CSS selector fallback strategy
- xG range validation [0.0, 15.0]
- Team name normalization
- Date validation (season range)

**URL Pattern:**
```
https://fbref.com/en/comps/9/{season}/schedule/
```
Example: `https://fbref.com/en/comps/9/2023-2024/schedule/`

### TransfermarktScraper

**Purpose:** Extract squad market values from Transfermarkt

**Data Source:** https://www.transfermarkt.com/

**Key Features:**
- Squad value format conversion (e.g., "500m €" → 500.0)
- Temporal coherence validation
- Team name normalization
- Value range validation [10.0, 2000.0] million €

**URL Pattern:**
```
https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/plus/?saison_id={year}
```
Example: `https://www.transfermarkt.com/.../saison_id=2023`

### RateLimiter

**Purpose:** Control request frequency to respect ToS

**Features:**
- Thread-safe locking
- Configurable delay
- Automatic timing

**Usage:**
```python
rate_limiter = RateLimiter(delay_seconds=2.0)
rate_limiter.wait()  # Blocks until delay elapsed
```

### CacheManager

**Purpose:** Store and retrieve cached HTML pages

**Features:**
- Filesystem-based cache
- TTL expiration (30 days default)
- Cache index tracking
- Force refresh support

**Cache Strategy:**
1. Check cache index for URL
2. Verify TTL not expired
3. Load from disk if valid
4. Otherwise, fetch and cache

### DataValidator

**Purpose:** Validate extracted data quality

**Validations:**

**FBref:**
- xG values in range [0.0, 15.0]
- Total xG < 20.0 (sanity check)
- Dates within season (August-May)

**Transfermarkt:**
- Squad values in range [10.0, 2000.0] million €
- No sudden drops >40% between seasons
- Expected team count (20-22 per season)

### CSVExporter

**Purpose:** Export validated data to CSV files

**Features:**
- Column ordering
- Chronological sorting
- Filename generation
- README creation

### ConfigParser

**Purpose:** Load and validate JSON configuration files

**Features:**
- Team mapping loading
- CSS selector loading
- Structure validation
- Pretty printing (2-space indent)

### Utility Functions

**normalize_team_name(name, mapping):**
- Applies team name normalization
- Returns canonical name or original if not found
- Logs warning for unmapped names

**parse_season_range(season_range):**
- Parses "YYYY-YYYY" format
- Returns (start_year, end_year) tuple
- Validates year ranges

**format_season_code(year):**
- Converts year to 4-digit code
- Example: 2023 → "2324"

## Testing

### Run All Tests

```bash
python -m pytest tests/ -v
```

Expected: 147 tests passing

### Run Specific Test Suites

```bash
# Component tests
python -m pytest tests/test_rate_limiter.py -v
python -m pytest tests/test_cache_manager.py -v
python -m pytest tests/test_data_validator.py -v

# Scraper tests
python -m pytest tests/test_scrapers_end_to_end.py -v

# CLI tests
python -m pytest tests/test_scrape_fbref_cli.py -v
python -m pytest tests/test_scrape_transfermarkt_cli.py -v

# Dependency tests
python -m pytest tests/test_dependencies.py -v
```

### Test Coverage

```bash
python -m pytest tests/ --cov=src.scraping --cov-report=html
```

View coverage report: `htmlcov/index.html`

### Property-Based Tests (Optional)

If hypothesis is installed:

```bash
python -m pytest tests/property_tests/ -v
```

## Troubleshooting

### HTTP 403 Forbidden

**Cause:** Website blocking requests

**Solutions:**
1. Increase delay: `--delay 2.0`
2. Check user agent in `BaseScraper._get_headers()`
3. Verify you're not banned (wait 24h)

### HTML Parsing Failures

**Cause:** Website structure changed

**Solutions:**
1. Check logs for failed selectors
2. Inspect saved HTML in `data/external/failed_parses/`
3. Update CSS selectors in `config/scraping_selectors.json`
4. Test selectors using browser DevTools

### Invalid Data Warnings

**Cause:** Data quality issues or validation too strict

**Solutions:**
1. Review validation report in `data/external/validation_report_*.txt`
2. Adjust validation thresholds in `DataValidator`
3. Inspect problematic rows in saved HTML

### Cache Not Working

**Cause:** Cache index corruption or permissions

**Solutions:**
1. Delete cache: `rm -rf data/external/cache/`
2. Run with `--force-refresh`
3. Check file permissions on cache directory

### Import Errors

**Cause:** Missing dependencies

**Solutions:**
```bash
pip install -r requirements-scraping.txt
python -m pytest tests/test_dependencies.py -v
```

### Rate Limiting Too Slow

**Cause:** Conservative default delay

**Solutions:**
- Reduce delay (risky): `--delay 0.5`
- Use cached data (no new requests)
- Run overnight for large ranges

## Best Practices

### Ethical Scraping

1. **Respect robots.txt**: Check website policies
2. **Rate limiting**: Use reasonable delays (≥1.0s)
3. **Caching**: Reuse downloaded data
4. **User agent**: Identify yourself properly
5. **Off-peak hours**: Run scrapers during low traffic times

### Production Deployment

1. **Schedule with cron**: Run weekly for fresh data
2. **Monitor logs**: Check for parsing failures
3. **Alert on errors**: Set up notifications
4. **Backup cache**: Preserve downloaded HTML
5. **Version control**: Track selector changes

### Data Integration

1. **Verify dates**: Match date formats with existing data
2. **Normalize names**: Use consistent team naming
3. **Validate ranges**: Check xG and value ranges
4. **Handle missing**: Decide on imputation strategy
5. **Document joins**: Explain merge keys

## Performance

### Benchmarks

**FBref (10 seasons, 1.0s delay):**
- Time: ~10 seconds
- Requests: 10 (1 per season)
- Matches: ~3,800
- Cache hits: 100% on re-run

**Transfermarkt (10 seasons, 1.0s delay):**
- Time: ~10 seconds
- Requests: 10 (1 per season)
- Teams: ~200
- Cache hits: 100% on re-run

### Optimization Tips

1. **Use cache**: Don't force refresh unnecessarily
2. **Batch seasons**: Scrape multiple seasons at once
3. **Parallel execution**: Run both scrapers simultaneously
4. **Minimize delay**: Balance speed vs. politeness

## Contributing

### Adding a New Scraper

1. Create `my_scraper.py` inheriting from `BaseScraper`
2. Implement `build_urls()` and `parse_page()`
3. Add CSS selectors to `config/scraping_selectors.json`
4. Create validator in `DataValidator`
5. Add export method in `CSVExporter`
6. Create CLI script `scrape_my_source.py`
7. Write tests in `tests/test_my_scraper.py`

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings
- Add tests for new features
- Update this README

### Submitting Changes

1. Fork repository
2. Create feature branch
3. Run tests: `pytest tests/ -v`
4. Commit with clear message
5. Open pull request

## License

This scraping module is part of the pl-ldc-prediction project.

## Credits

**Data Sources:**
- FBref.com for xG statistics
- Transfermarkt.com for squad values

**Libraries:**
- requests for HTTP
- BeautifulSoup4 for parsing
- pandas for data manipulation
- pytest for testing

## Support

For issues or questions:
1. Check this README
2. Review logs in `logs/`
3. Check validation reports
4. Open an issue on GitHub

## Changelog

### Version 1.0.0 (2026-08-13)
- Initial release
- FBref scraper with xG data
- Transfermarkt scraper with squad values
- Complete CLI interfaces
- 147 tests passing
- Comprehensive documentation
