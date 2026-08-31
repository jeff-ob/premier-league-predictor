"""
Configuration centrale de l'application Streamlit
"""
from pathlib import Path

# Chemins projet
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / 'data' / 'raw'
DATA_PROCESSED = PROJECT_ROOT / 'data' / 'processed'
MODELS_DIR = PROJECT_ROOT / 'models'
DB_DIR = PROJECT_ROOT / 'app' / 'database'

# Fichiers de données
FIXTURES_FILE = DATA_RAW / 'fixtures.csv'
TEAMS_STADIUMS_FILE = DATA_RAW / 'teams_and_stadiums.csv'
MANAGERS_FILE = DATA_RAW / 'managers_and_club_info.csv'
FEATURES_FILE = DATA_PROCESSED / 'pl_features_v4.csv'

# Modèles
MODEL_GB = MODELS_DIR / 'stacking_gb_base.pkl'
MODEL_RF = MODELS_DIR / 'stacking_rf_base.pkl'
MODEL_LR = MODELS_DIR / 'stacking_lr_base.pkl'
MODEL_SCALER = MODELS_DIR / 'stacking_scaler.pkl'
MODEL_META = MODELS_DIR / 'stacking_meta_model.pkl'

# Base de données
DB_FILE = DB_DIR / 'season_2026_27.db'

# Configuration application
APP_TITLE = "⚽ Premier League 2026-27 - Prédictions & Qualification LDC"
SEASON = "2026-27"
N_TEAMS = 20

# Feature names (doivent correspondre au modèle)
FEATURE_COLS = [
    'Home_Form', 'Home_Rank', 'Home_Streak', 'Home_Goal_Diff',
    'Home_Rolling_GF', 'Home_Rolling_GA', 'Home_Points_Pace', 'Home_Match_Number',
    'Away_Form', 'Away_Rank', 'Away_Streak', 'Away_Goal_Diff',
    'Away_Rolling_GF', 'Away_Rolling_GA', 'Away_Points_Pace', 'Away_Match_Number',
    'Home_xG_Form', 'Away_xG_Form'
]

# Classes de prédiction
CLASSES = ['A', 'D', 'H']
CLASS_NAMES = {'A': 'Away', 'D': 'Draw', 'H': 'Home'}
