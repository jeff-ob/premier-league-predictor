"""
Composant pour générer les prédictions des matchs
"""
import pandas as pd
import numpy as np

def create_dummy_features(home_team, away_team, historical_data):
    """
    Créer les features pour un match à partir des données historiques
    
    Pour Phase 1 : Features simplifiées (seront calculées dynamiquement en Phase 2)
    """
    # Pour l'instant, on utilise des valeurs moyennes
    # En Phase 2, on calculera les vraies features basées sur les résultats enregistrés
    
    features = {
        # Features domicile
        'Home_Form': 6.0,
        'Home_Rank': 10.0,
        'Home_Streak': 0.0,
        'Home_Goal_Diff': 0.0,
        'Home_Rolling_GF': 1.5,
        'Home_Rolling_GA': 1.2,
        'Home_Points_Pace': 50.0,
        'Home_Match_Number': 1.0,
        
        # Features extérieur
        'Away_Form': 6.0,
        'Away_Rank': 10.0,
        'Away_Streak': 0.0,
        'Away_Goal_Diff': 0.0,
        'Away_Rolling_GF': 1.3,
        'Away_Rolling_GA': 1.5,
        'Away_Points_Pace': 48.0,
        'Away_Match_Number': 1.0,
        
        # xG Form (valeurs moyennes)
        'Home_xG_Form': 1.5,
        'Away_xG_Form': 1.3
    }
    
    return features

def predict_match(predictor, home_team, away_team, historical_data):
    """
    Prédire le résultat d'un match
    
    Args:
        predictor: Instance de StackingPredictor
        home_team: Nom équipe domicile
        away_team: Nom équipe extérieur
        historical_data: DataFrame avec historique (pour calcul features)
    
    Returns:
        dict avec prédiction et probabilités
    """
    # Créer les features
    features = create_dummy_features(home_team, away_team, historical_data)
    
    # Prédire
    prediction, probabilities = predictor.predict_single(features)
    
    return {
        'home_team': home_team,
        'away_team': away_team,
        'prediction': prediction,
        'prob_home': probabilities['H'],
        'prob_draw': probabilities['D'],
        'prob_away': probabilities['A']
    }

def predict_matches_batch(predictor, matches_df, historical_data):
    """
    Prédire plusieurs matchs d'un coup
    
    Args:
        predictor: Instance de StackingPredictor
        matches_df: DataFrame avec colonnes home_team, away_team
        historical_data: DataFrame avec historique
    
    Returns:
        DataFrame avec prédictions ajoutées
    """
    predictions = []
    
    for _, match in matches_df.iterrows():
        pred = predict_match(
            predictor,
            match['home_team'],
            match['away_team'],
            historical_data
        )
        predictions.append(pred)
    
    pred_df = pd.DataFrame(predictions)
    
    # Fusionner avec les matchs originaux
    result = matches_df.copy()
    result['prediction'] = pred_df['prediction'].values
    result['prob_home'] = pred_df['prob_home'].values
    result['prob_draw'] = pred_df['prob_draw'].values
    result['prob_away'] = pred_df['prob_away'].values
    
    return result
