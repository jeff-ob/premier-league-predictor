"""
Script d'ingestion : télécharge et fusionne toutes les saisons Premier League
depuis football-data.co.uk en un seul CSV.
"""

import pandas as pd
import requests
from io import StringIO
from pathlib import Path

BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/E0.csv"
OUTPUT_PATH = Path("data/raw/pl_all_seasons.csv")

# Génère les codes saison au format attendu par le site (ex: 9394, 9495, ..., 2526)
def generate_season_codes(start_year: int = 1993, end_year: int = 2025) -> list[str]:
    return [f"{y % 100:02d}{(y + 1) % 100:02d}" for y in range(start_year, end_year + 1)]


def download_season(season_code: str) -> pd.DataFrame | None:
    url = BASE_URL.format(season=season_code)
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text), encoding="latin1")
        df["Season"] = season_code
        return df
    except Exception as e:
        print(f"[ATTENTION] Saison {season_code} non récupérée : {e}")
        return None


def main():
    seasons = generate_season_codes()
    all_dfs = []

    for season in seasons:
        df = download_season(season)
        if df is not None:
            all_dfs.append(df)
            print(f"[OK] Saison {season} chargée ({len(df)} matchs)")

    if not all_dfs:
        print("Aucune donnée récupérée. Arrêt.")
        return

    merged = pd.concat(all_dfs, ignore_index=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUTPUT_PATH, index=False)
    print(f"\nFusion terminée : {len(merged)} matchs au total -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()