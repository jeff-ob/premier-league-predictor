#!/usr/bin/env python3
"""
CLI pour scraper les valeurs marchandes des équipes depuis Transfermarkt.

Usage:
    python -m src.scraping.scrape_transfermarkt --seasons 2023-2024
    python -m src.scraping.scrape_transfermarkt --seasons 2017-2026 --delay 2.0 --force-refresh
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

from src.scraping.rate_limiter import RateLimiter
from src.scraping.cache_manager import CacheManager
from src.scraping.data_validator import DataValidator
from src.scraping.csv_exporter import CSVExporter
from src.scraping.config_parser import ConfigParser
from src.scraping.transfermarkt_scraper import TransfermarktScraper


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Scrape squad market values from Transfermarkt for Premier League teams',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape single season
  python -m src.scraping.scrape_transfermarkt --seasons 2023-2024

  # Scrape multiple seasons with custom delay
  python -m src.scraping.scrape_transfermarkt --seasons 2017-2026 --delay 2.0

  # Force refresh (ignore cache)
  python -m src.scraping.scrape_transfermarkt --seasons 2023-2024 --force-refresh

  # Combine all options
  python -m src.scraping.scrape_transfermarkt --seasons 2020-2024 --delay 1.5 --force-refresh
"""
    )
    
    parser.add_argument(
        '--seasons',
        required=True,
        help='Season range to scrape (format: YYYY-YYYY, e.g., 2023-2024 or 2017-2026)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay in seconds between requests (default: 1.0)'
    )
    
    parser.add_argument(
        '--force-refresh',
        action='store_true',
        help='Force refresh by ignoring cache'
    )
    
    return parser.parse_args()


def validate_season_format(season_range: str) -> tuple[int, int]:
    """
    Validate season range format and return start/end years.
    
    Args:
        season_range: Season range string (e.g., "2023-2024" or "2017-2026")
    
    Returns:
        Tuple of (start_year, end_year)
    
    Raises:
        ValueError: If format is invalid
    """
    if '-' not in season_range:
        raise ValueError(f"Invalid season format: {season_range}. Expected format: YYYY-YYYY")
    
    parts = season_range.split('-')
    if len(parts) != 2:
        raise ValueError(f"Invalid season format: {season_range}. Expected format: YYYY-YYYY")
    
    try:
        start_year = int(parts[0])
        end_year = int(parts[1])
    except ValueError:
        raise ValueError(f"Invalid season format: {season_range}. Years must be numeric")
    
    if start_year < 2000 or end_year > 2100:
        raise ValueError(f"Invalid year range: {season_range}. Years should be between 2000-2100")
    
    if start_year > end_year:
        raise ValueError(f"Invalid season range: {season_range}. Start year must be <= end year")
    
    return start_year, end_year


def estimate_execution_time(start_year: int, end_year: int, delay: float) -> float:
    """
    Estimate execution time based on number of seasons and delay.
    
    Args:
        start_year: Starting year
        end_year: Ending year
        delay: Delay between requests in seconds
    
    Returns:
        Estimated time in seconds
    """
    num_seasons = end_year - start_year + 1
    # Each season requires 1 request
    num_requests = num_seasons
    # Total time = requests * delay (rough estimate)
    return num_requests * delay


def display_confirmation(start_year: int, end_year: int, delay: float, force_refresh: bool):
    """Display confirmation message before starting scrape."""
    num_seasons = end_year - start_year + 1
    estimated_time = estimate_execution_time(start_year, end_year, delay)
    
    print("\n" + "="*70)
    print("Transfermarkt Squad Values Scraper - Configuration")
    print("="*70)
    print(f"Season range:      {start_year}-{end_year}")
    print(f"Number of seasons: {num_seasons}")
    print(f"Delay per request: {delay}s")
    print(f"Force refresh:     {'Yes' if force_refresh else 'No'}")
    print(f"Estimated time:    ~{estimated_time:.1f}s ({estimated_time/60:.1f} minutes)")
    print("="*70)
    print()


def main():
    """Main execution function."""
    # Parse arguments
    args = parse_arguments()
    
    # Validate season format
    try:
        start_year, end_year = validate_season_format(args.seasons)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Display confirmation
    display_confirmation(start_year, end_year, args.delay, args.force_refresh)
    
    # Initialize timestamp for logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Load configuration
        print("Loading configuration...")
        config_parser = ConfigParser()
        team_mapping = config_parser.load_team_mapping()
        selectors = config_parser.load_selectors()
        
        # Initialize components
        print("Initializing components...")
        rate_limiter = RateLimiter(delay_seconds=args.delay)
        cache_manager = CacheManager()
        validator = DataValidator(source='transfermarkt')
        exporter = CSVExporter()
        
        # Create scraper config
        scraper_config = {
            'team_mapping': team_mapping,
            'transfermarkt': selectors['transfermarkt']
        }
        
        # Initialize scraper
        scraper = TransfermarktScraper(
            rate_limiter=rate_limiter,
            cache_manager=cache_manager,
            validator=validator,
            config=scraper_config
        )
        
        print(f"\nStarting scrape for seasons {args.seasons}...")
        print("-" * 70)
        
        # Run scraper
        df = scraper.run(season_range=args.seasons, force_refresh=args.force_refresh)
        
        print("-" * 70)
        print(f"\nScraping complete! Collected {len(df)} team valuations.")
        
        # Export to CSV
        print("\nExporting to CSV...")
        csv_path = exporter.export_transfermarkt(
            df=df,
            start_season=str(start_year)[2:4] + str(start_year + 1)[2:4],
            end_season=str(end_year)[2:4] + str(end_year + 1)[2:4]
        )
        
        # Generate validation report
        print("Generating validation report...")
        report_path = f"data/external/validation_report_transfermarkt_{timestamp}.txt"
        validator.generate_report(report_path)
        
        # Display summary
        print("\n" + "="*70)
        print("Scraping Summary")
        print("="*70)
        print(f"✓ Total team valuations:    {len(df)}")
        print(f"✓ Validation warnings:      {len(validator.warnings)}")
        print(f"✓ CSV output:               {csv_path}")
        print(f"✓ Validation report:        {report_path}")
        print("="*70)
        print("\n✓ Success! Data has been exported.")
        
        sys.exit(0)
        
    except FileNotFoundError as e:
        print(f"\nERROR: Configuration file not found - {e}", file=sys.stderr)
        print("Please ensure config/team_names_mapping.json and config/scraping_selectors.json exist.")
        sys.exit(1)
    
    except Exception as e:
        print(f"\nERROR: Scraping failed - {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
