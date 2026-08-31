"""
Gestionnaire de base de données SQLite pour la saison en cours
"""
import sqlite3
import pandas as pd
from pathlib import Path

class SeasonDB:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.init_db()
    
    def init_db(self):
        """Initialiser la base de données avec les tables nécessaires"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        # Table des matchs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                match_id INTEGER PRIMARY KEY,
                matchweek INTEGER NOT NULL,
                date TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_goals INTEGER,
                away_goals INTEGER,
                result TEXT,
                played BOOLEAN DEFAULT 0,
                pred_home REAL,
                pred_draw REAL,
                pred_away REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table du classement
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS standings (
                team TEXT PRIMARY KEY,
                played INTEGER DEFAULT 0,
                won INTEGER DEFAULT 0,
                drawn INTEGER DEFAULT 0,
                lost INTEGER DEFAULT 0,
                goals_for INTEGER DEFAULT 0,
                goals_against INTEGER DEFAULT 0,
                goal_diff INTEGER DEFAULT 0,
                points INTEGER DEFAULT 0,
                form TEXT DEFAULT '',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def load_fixtures(self, fixtures_df):
        """Charger le calendrier complet de la saison"""
        cursor = self.conn.cursor()
        
        for _, row in fixtures_df.iterrows():
            cursor.execute('''
                INSERT OR IGNORE INTO matches 
                (match_id, matchweek, date, home_team, away_team)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                row['match_number'],
                row['matchweek'],
                row['date'],
                row['home_team'],
                row['away_team']
            ))
        
        self.conn.commit()
    
    def get_all_matches(self):
        """Récupérer tous les matchs"""
        return pd.read_sql_query('SELECT * FROM matches ORDER BY match_id', self.conn)
    
    def get_matches_by_matchweek(self, matchweek):
        """Récupérer les matchs d'une journée"""
        query = 'SELECT * FROM matches WHERE matchweek = ? ORDER BY match_id'
        return pd.read_sql_query(query, self.conn, params=(matchweek,))
    
    def get_next_unplayed_matches(self, limit=10):
        """Récupérer les prochains matchs non joués"""
        query = '''
            SELECT * FROM matches 
            WHERE played = 0 
            ORDER BY match_id 
            LIMIT ?
        '''
        return pd.read_sql_query(query, self.conn, params=(limit,))
    
    def record_result(self, match_id, home_goals, away_goals):
        """Enregistrer le résultat d'un match"""
        cursor = self.conn.cursor()
        
        # Déterminer le résultat
        if home_goals > away_goals:
            result = 'H'
        elif home_goals < away_goals:
            result = 'A'
        else:
            result = 'D'
        
        cursor.execute('''
            UPDATE matches 
            SET home_goals = ?, away_goals = ?, result = ?, played = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE match_id = ?
        ''', (home_goals, away_goals, result, match_id))
        
        self.conn.commit()
        return result
    
    def store_prediction(self, match_id, pred_home, pred_draw, pred_away):
        """Stocker les probabilités prédites pour un match"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE matches 
            SET pred_home = ?, pred_draw = ?, pred_away = ?
            WHERE match_id = ?
        ''', (pred_home, pred_draw, pred_away, match_id))
        self.conn.commit()
    
    def init_standings(self, teams):
        """Initialiser le classement avec toutes les équipes"""
        cursor = self.conn.cursor()
        for team in teams:
            cursor.execute('''
                INSERT OR IGNORE INTO standings (team)
                VALUES (?)
            ''', (team,))
        self.conn.commit()
    
    def get_standings(self):
        """Récupérer le classement actuel"""
        query = '''
            SELECT * FROM standings 
            ORDER BY points DESC, goal_diff DESC, goals_for DESC
        '''
        return pd.read_sql_query(query, self.conn)
    
    def update_standings_after_match(self, match_id):
        """Mettre à jour le classement après un match enregistré"""
        cursor = self.conn.cursor()
        
        # Récupérer le match
        match = pd.read_sql_query(
            'SELECT * FROM matches WHERE match_id = ?', 
            self.conn, 
            params=(match_id,)
        ).iloc[0]
        
        if not match['played']:
            return
        
        home_team = match['home_team']
        away_team = match['away_team']
        home_goals = match['home_goals']
        away_goals = match['away_goals']
        result = match['result']
        
        # Mettre à jour équipe domicile
        if result == 'H':
            home_points, home_won = 3, 1
        elif result == 'D':
            home_points, home_won = 1, 0
        else:
            home_points, home_won = 0, 0
        
        cursor.execute('''
            UPDATE standings SET
                played = played + 1,
                won = won + ?,
                drawn = drawn + ?,
                lost = lost + ?,
                goals_for = goals_for + ?,
                goals_against = goals_against + ?,
                goal_diff = goal_diff + ?,
                points = points + ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE team = ?
        ''', (
            home_won,
            1 if result == 'D' else 0,
            1 if result == 'A' else 0,
            home_goals,
            away_goals,
            home_goals - away_goals,
            home_points,
            home_team
        ))
        
        # Mettre à jour équipe extérieur
        if result == 'A':
            away_points, away_won = 3, 1
        elif result == 'D':
            away_points, away_won = 1, 0
        else:
            away_points, away_won = 0, 0
        
        cursor.execute('''
            UPDATE standings SET
                played = played + 1,
                won = won + ?,
                drawn = drawn + ?,
                lost = lost + ?,
                goals_for = goals_for + ?,
                goals_against = goals_against + ?,
                goal_diff = goal_diff + ?,
                points = points + ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE team = ?
        ''', (
            away_won,
            1 if result == 'D' else 0,
            1 if result == 'H' else 0,
            away_goals,
            home_goals,
            away_goals - home_goals,
            away_points,
            away_team
        ))
        
        self.conn.commit()
    
    def close(self):
        """Fermer la connexion à la base de données"""
        if self.conn:
            self.conn.close()
