"""Cache manager component for storing and retrieving HTML pages.

Implements:
- Requirement 5.1: Save downloaded HTML to cache directory
- Requirement 5.2: Check cache validity based on TTL
- Requirement 5.3: Load HTML from cache
- Requirement 5.4: Force refresh to ignore cache
- Requirement 5.5: Maintain cache index with metadata
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import re


class CacheManager:
    """Manages filesystem cache for downloaded HTML pages."""

    def __init__(self, cache_dir: str = "data/external/cache", ttl_days: int = 30):
        """Initialize the cache manager.
        
        Args:
            cache_dir: Base directory for cache storage
            ttl_days: Time-to-live for cached files in days (default 30)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_days = ttl_days
        self.index_file = self.cache_dir / "cache_index.json"
        self._ensure_cache_dir()
        self.index = self._load_index()

    def _ensure_cache_dir(self):
        """Create cache directory structure if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "fbref").mkdir(exist_ok=True)
        (self.cache_dir / "transfermarkt").mkdir(exist_ok=True)

    def get(self, url: str) -> Optional[str]:
        """Retrieve cached HTML if valid.
        
        Args:
            url: URL of the page to retrieve from cache
            
        Returns:
            HTML content as string if valid cache exists, None otherwise
        """
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
        """Save HTML to cache.
        
        Args:
            url: URL of the page being cached
            html: HTML content to save
        """
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
        """Generate cache key from URL using MD5 hash.
        
        Args:
            url: URL to generate key for
            
        Returns:
            MD5 hash of the URL as hex string
        """
        return hashlib.md5(url.encode()).hexdigest()

    def _detect_source(self, url: str) -> str:
        """Detect source website from URL.
        
        Args:
            url: URL to detect source from
            
        Returns:
            Source identifier ('fbref', 'transfermarkt', or 'other')
        """
        if 'fbref' in url:
            return 'fbref'
        elif 'transfermarkt' in url:
            return 'transfermarkt'
        else:
            return 'other'

    def _generate_filename(self, url: str) -> str:
        """Generate readable filename from URL.
        
        Extracts season information from URL patterns:
        - FBref: "2017-2018" -> "2017-2018_schedule.html"
        - Transfermarkt: "saison_id=2017" -> "2017_teams.html"
        
        Args:
            url: URL to generate filename from
            
        Returns:
            Generated filename
        """
        # Try FBref pattern: /comps/9/2017-2018/schedule/
        fbref_match = re.search(r'/comps/9/(\d{4}-\d{4})/schedule', url)
        if fbref_match:
            season = fbref_match.group(1)
            return f"{season}_schedule.html"

        # Try Transfermarkt pattern: saison_id=2017
        tm_match = re.search(r'saison_id=(\d{4})', url)
        if tm_match:
            year = tm_match.group(1)
            return f"{year}_teams.html"

        # Fallback: use URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"page_{url_hash}.html"

    def _load_index(self) -> dict:
        """Load cache index from JSON file.
        
        Returns:
            Dictionary containing cache index, empty dict if file doesn't exist
        """
        if not self.index_file.exists():
            return {}
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If index is corrupted, start fresh
            return {}

    def _save_index(self):
        """Save cache index to JSON file with pretty formatting."""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
