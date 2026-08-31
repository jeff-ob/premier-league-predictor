"""
Script de nettoyage des données football-data.co.uk
Peut être utilisé de manière autonome ou importé dans les notebooks
"""

import pandas as pd
import numpy as np
from pathlib import Path


def fix_season_code(season):
    """Convertit les codes saison en format standardisé 4 chiffres (ex: '0001', '2526')"""
    if pd.isna(season):
        return None
    # Conversion en int puis string pour gérer les float
    season_int = int(season) if isinstance(season, (int, float)) else int(season)
    # Padding à 4 chiffres
    return str(season_int).zfill(4)


def convert_date(date_str, formats=['%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d']):
    """Essaie plusieurs formats de date"""
    if pd.isna(date_str):
        return pd.NaT
    
    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except (ValueError, TypeError):
            continue
    
    # Dernier recours : pandas infer
    try:
        return pd.to_datetime(date_str, dayfirst=True)
    except:
        return pd.NaT


def clean_football_data(input_path, output_path=None):
    """
    Nettoie le CSV football-data.co.uk fusionné
    
    Args:
        input_path: chemin vers pl_all_seasons.csv
        output_path: chemin de sortie (optionnel)
    
    Returns:
        DataFrame nettoyé
    """
    
    # 1. Chargement
    print(f"Chargement depuis {input_path}...")
    df_raw = pd.read_csv(input_path, low_memory=False)
    print(f"Dimensions initiales : {df_raw.shape}")
    
    # 2. Sélection colonnes
    COLS_TO_KEEP = [
        'Date', 'Season', 'HomeTeam', 'AwayTeam', 'Referee',
        'FTHG', 'FTAG', 'FTR', 'HTHG', 'HTAG', 'HTR',
        'HS', 'AS', 'HST', 'AST', 'HC', 'AC', 'HF', 'AF', 'HY', 'AY', 'HR', 'AR',
        'AvgH', 'AvgD', 'AvgA'
    ]
    
    available_cols = [col for col in COLS_TO_KEEP if col in df_raw.columns]
    df = df_raw[available_cols].copy()
    print(f"Après sélection colonnes : {df.shape}")
    
    # 3. Correction codes saison
    print("\nCorrection des codes saison...")
    df['Season'] = df['Season'].apply(fix_season_code)
    
    # 4. Conversion Date
    print("Conversion des dates...")
    df['Date'] = df['Date'].apply(convert_date)
    
    # 5. Conversion types numériques
    print("Conversion types numériques...")
    numeric_cols = ['FTHG', 'FTAG', 'HTHG', 'HTAG', 
                    'HS', 'AS', 'HST', 'AST', 'HC', 'AC', 
                    'HF', 'AF', 'HY', 'AY', 'HR', 'AR',
                    'AvgH', 'AvgD', 'AvgA']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 6. Conversion catégorielles
    print("Conversion types catégoriels...")
    for col in ['FTR', 'HTR']:
        if col in df.columns:
            df[col] = df[col].astype('category')
    
    # 7. Colonnes texte
    text_cols = ['HomeTeam', 'AwayTeam', 'Referee', 'Season']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)
    
    # 8. Vérifications cohérence
    print("\nVérifications de cohérence...")
    
    # Buts mi-temps <= buts finaux
    invalid_ht_home = (df['HTHG'] > df['FTHG']).sum()
    invalid_ht_away = (df['HTAG'] > df['FTAG']).sum()
    print(f"- Matchs HTHG > FTHG : {invalid_ht_home}")
    print(f"- Matchs HTAG > FTAG : {invalid_ht_away}")
    
    # Cohérence FTR
    def check_ftr(row):
        if pd.isna(row['FTHG']) or pd.isna(row['FTAG']) or pd.isna(row['FTR']):
            return True
        if row['FTHG'] > row['FTAG']:
            return row['FTR'] == 'H'
        elif row['FTHG'] < row['FTAG']:
            return row['FTR'] == 'A'
        else:
            return row['FTR'] == 'D'
    
    inconsistent = (~df.apply(check_ftr, axis=1)).sum()
    print(f"- Matchs avec FTR incohérent : {inconsistent}")
    
    # 9. Statistiques finales
    print(f"\n=== RÉSUMÉ ===")
    print(f"Dimensions finales : {df.shape}")
    print(f"Période : {df['Date'].min()} → {df['Date'].max()}")
    print(f"Saisons : {df['Season'].nunique()}")
    print(f"Équipes uniques : {pd.concat([df['HomeTeam'], df['AwayTeam']]).nunique()}")
    
    print(f"\nValeurs manquantes (top 10) :")
    missing = df.isnull().sum().sort_values(ascending=False).head(10)
    missing_pct = (missing / len(df) * 100).round(2)
    for col, count in missing.items():
        print(f"  {col}: {count} ({missing_pct[col]}%)")
    
    # 10. Export
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\n✓ Export réussi : {output_path}")
    
    return df


if __name__ == "__main__":
    # Chemins
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    INPUT = PROJECT_ROOT / "data" / "raw" / "pl_all_seasons.csv"
    OUTPUT = PROJECT_ROOT / "data" / "interim" / "pl_cleaned.csv"
    
    # Nettoyage
    df_clean = clean_football_data(INPUT, OUTPUT)
