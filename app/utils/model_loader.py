"""
Chargement et gestion des modèles de prédiction
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

class StackingPredictor:
    def __init__(self, model_gb_path, model_rf_path, model_lr_path, 
                 scaler_path, meta_model_path):
        """Charger le modèle stacking et ses composants"""
        self.gb_model = joblib.load(model_gb_path)
        self.rf_model = joblib.load(model_rf_path)
        self.lr_model = joblib.load(model_lr_path)
        self.scaler = joblib.load(scaler_path)
        self.meta_model = joblib.load(meta_model_path)
        
        print("Modèles chargés avec succès")
        print(f"  - Gradient Boosting")
        print(f"  - Random Forest")
        print(f"  - Logistic Regression")
        print(f"  - Meta-model (Stacking)")
    
    def predict(self, X):
        """
        Prédire le résultat d'un ou plusieurs matchs
        
        Args:
            X: DataFrame ou array avec les features (18 colonnes)
        
        Returns:
            predictions: array des classes prédites ('A', 'D', 'H')
            probabilities: array des probabilités (n_samples, 3)
        """
        # Convertir en DataFrame si nécessaire
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X)
        
        # Remplir les NaN
        X_clean = X.fillna(0)
        
        # Prédictions des modèles de base
        proba_gb = self.gb_model.predict_proba(X_clean)
        proba_rf = self.rf_model.predict_proba(X_clean)
        
        # LR nécessite normalisation
        X_scaled = self.scaler.transform(X_clean)
        proba_lr = self.lr_model.predict_proba(X_scaled)
        
        # Stacker les probabilités
        X_meta = np.hstack([proba_gb, proba_rf, proba_lr])
        
        # Prédiction finale
        predictions = self.meta_model.predict(X_meta)
        probabilities = self.meta_model.predict_proba(X_meta)
        
        return predictions, probabilities
    
    def predict_single(self, features_dict):
        """
        Prédire un seul match à partir d'un dictionnaire de features
        
        Args:
            features_dict: dict avec clés = noms des features
        
        Returns:
            prediction: classe prédite ('A', 'D', 'H')
            probabilities: dict {'A': prob, 'D': prob, 'H': prob}
        """
        # Créer DataFrame avec une ligne
        X = pd.DataFrame([features_dict])
        
        # Prédire
        pred, proba = self.predict(X)
        
        # Convertir en format simple
        prediction = pred[0]
        probabilities = {
            'A': float(proba[0][0]),
            'D': float(proba[0][1]),
            'H': float(proba[0][2])
        }
        
        return prediction, probabilities
