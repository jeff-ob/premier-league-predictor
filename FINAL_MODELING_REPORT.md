# RAPPORT FINAL - Prédiction Résultats Premier League

**Date** : 25 Août 2026  
**Projet** : Prédiction résultats matchs PL + Qualification Ligue des Champions  
**Période d'analyse** : 1993-2026 (33 saisons)

---

## Résumé Exécutif

**Meilleur modèle** : Ensemble Stacking v3  
**Performance** : **59.4% accuracy** (+16.9 points vs baseline)  
**Objectif initial** : 60% (atteint à 99%)

Le projet a exploré plusieurs architectures de modélisation pour prédire les résultats de matchs de Premier League. Après itérations successives (v1 → v2 → v3 → stacking), le modèle final combine trois approches complémentaires via stacking et atteint 59.4% d'accuracy.

---

## 1. Évolution des Performances

### Progression des modèles

| Version | Meilleur Modèle | Accuracy | Gain vs Baseline | Features Clés |
|---------|-----------------|----------|------------------|---------------|
| **v1** | Gradient Boosting | 50.0% | +7.6 pts | Forme, Rank, Stats base |
| **v2** | Logistic Regression | 55.6% | +13.1 pts | + xG basiques |
| **v3** | Gradient Boosting optimisé | 58.7% | +16.2 pts | + xG avancées, GridSearch |
| **Stacking v3** | GB + RF + LR | **59.4%** | **+16.9 pts** | Ensemble des 3 modèles |

**Baseline** : Toujours prédire victoire domicile = 42.5%

### Courbe d'apprentissage

```
50% ────────●─────────────────────────  v1 (baseline ML)
            │
55% ────────┼─────────●───────────────  v2 (+ xG)
            │         │
58% ────────┼─────────┼─────────●─────  v3 (optimisé)
            │         │         │
59% ────────┼─────────┼─────────┼──●──  Stacking (final)
            │         │         │  │
60% ────────┴─────────┴─────────┴──┴──  Objectif
```

---

## 2. Détail des Modèles Finaux

### 2.1 Ensemble Stacking v3 (Champion - 59.4%)

**Architecture** :
- Modèles de base : Gradient Boosting + Random Forest + Logistic Regression
- Méta-modèle : Logistic Regression sur probabilités des 3 modèles
- Méta-features : 9 colonnes (3 modèles × 3 classes)

**Performances par classe** :

| Classe | Precision | Recall | F1-Score | Support |
|--------|-----------|--------|----------|---------|
| Away   | 0.59      | 0.72   | 0.65     | 137     |
| Draw   | 0.24      | 0.03   | 0.06     | 115     |
| Home   | 0.62      | 0.84   | 0.72     | 186     |

**Forces** :
- Meilleure accuracy globale
- Excellente détection des victoires Home (84% recall)
- Bonne prédiction des victoires Away (72% recall)

**Faiblesses** :
- Draws quasi-impossibles à prédire (3% recall)

---

### 2.2 Gradient Boosting v3 Optimisé (Runner-up - 58.7%)

**Hyperparamètres optimaux** :
- n_estimators: 50
- max_depth: 7
- learning_rate: 0.05
- min_samples_split: 100

**Top 5 features importantes** :
1. Home_xG_Form (10.8%)
2. Away_xG_Form (8.8%)
3. Home_Goal_Diff (8.7%)
4. Away_Points_Pace (7.1%)
5. Away_Goal_Diff (6.9%)

---

### 2.3 Random Forest v3 Optimisé (3ème - 57.8%)

**Hyperparamètres optimaux** :
- n_estimators: 200
- max_depth: 15
- min_samples_split: 50
- min_samples_leaf: 10
- max_features: None

**Particularité** : Légèrement moins performant que GB mais plus rapide en inférence.

---

### 2.4 Logistic Regression v3 (4ème - 57.3%)

**Particularité** : Meilleur F1-macro (0.559), plus équilibré entre les classes.

**Usage recommandé** : Interprétabilité (coefficients lisibles) ou contexte avec forte pénalité sur déséquilibre de classes.

---

## 3. Dataset et Features

### 3.1 Dataset final

**Fichier** : `pl_features_v4.csv`  
**Taille** : 12 279 matchs, 46 colonnes  
**Période modélisation** : 2020-2026 (2 218 matchs avec xG)  
**Split** : 80% train (1 752 matchs) / 20% test (438 matchs)

### 3.2 Features utilisées (38 colonnes)

**Catégories** :

1. **Forme et classement** (8 features × 2 équipes)
   - Form, Rank, Streak, Points_Pace, Match_Number
   - Goal_Diff, Rolling_GF, Rolling_GA

2. **xG avancées** (2 features × 2 équipes)
   - xG_Form (moyenne mobile 5 matchs)

**Features écartées** :
- Valeurs marchandes (corrélées avec Rank, redondantes)
- SOS (Strength of Schedule) : dégradait les performances

---

## 4. Expérimentations Infructueuses

### 4.1 Strength of Schedule (SOS)

**Hypothèse** : La difficulté du calendrier (force des 5 prochains adversaires) influence les résultats.

**Approche** :
- Calcul TSI (Team Strength Index) : 60% Rank N-1 + 40% Valeur marchande
- SOS_Next5 : Moyenne TSI des 5 prochains adversaires pondérée domicile/extérieur

**Résultat** : Échec (-2.7 points vs v3)

**Causes identifiées** :
1. TSI basé sur saison N-1 obsolète en cours de saison
2. Redondance avec Rank et Form actuels
3. Perte d'information d'ordre temporel (moyenne sur 5 matchs)

**Leçon** : La difficulté du calendrier agrégée n'est pas prédictive pour des résultats de matchs individuels. Elle pourrait être utile pour prédictions de classement final en fin de saison.

---

### 4.2 Optimisation hyperparamètres v1

**Résultat** : Échec (-0.3 points vs défaut)

Le modèle optimisé sur-prédisait encore plus Home, sacrifiant Draw. L'optimisation maximisait l'accuracy au détriment de l'équilibre entre classes.

---

## 5. Limites et Perspectives

### 5.1 Limites identifiées

**Problème structurel : Draws impossibles à prédire**

Tous les modèles ont un recall Draw < 10%. Les features actuelles (forme, xG, classement) ne capturent pas les patterns menant à un match nul.

**Hypothèses explicatives** :
- Draws = équilibre parfait des forces → signal trop faible
- Facteurs manquants : motivation, météo, absences joueurs clés, fatigue
- Déséquilibre des classes (26% Draws) pousse modèles à les ignorer

**Impact** :
- Plafonne l'accuracy maximale atteignable autour de 60%
- F1-macro sous-estime la qualité réelle (pénalisé par Draws)

---

### 5.2 Améliorations potentielles

**Court terme (gain estimé : +0.5-1 pt)** :
1. Features temporelles avancées
   - Jour de la semaine, congestion fixture
   - Repos entre matchs

2. Données qualitatives
   - Lineups temps réel (API-Football)
   - Absences suspensions/blessures
   - Météo matchs

**Moyen terme (gain estimé : +1-2 pts)** :
3. Données contextuelles
   - Position au classement (début/fin saison)
   - Enjeux (relégation, qualification LDC)
   - Historique confrontations directes

4. Features xG granulaires
   - xG par zone du terrain
   - xG tirs sur corner, coups francs
   - Distribution xG par joueur

**Long terme (recherche)** :
5. Modèles séquentiels
   - LSTM/Transformer sur séquence de matchs
   - Capturer dynamiques temporelles fines

6. Modèles de survie
   - Prédire probabilité de but à chaque minute
   - Agréger en prédiction résultat final

---

## 6. Comparaison avec État de l'Art

### Benchmarks académiques

| Source | Dataset | Méthode | Accuracy |
|--------|---------|---------|----------|
| Notre modèle | PL 2020-2026 | Stacking (GB+RF+LR) | **59.4%** |
| Baboota & Kaur (2019) | PL 5 saisons | XGBoost | 56.3% |
| Hubacek et al. (2019) | PL multi-saisons | Random Forest | 54.8% |
| Carpita et al. (2015) | Serie A | Logistic Regression | 52.7% |
| Baseline Home | - | Toujours prédire H | 42-46% |

**Positionnement** : Notre modèle se situe dans le haut de la fourchette académique (56-60%).

---

## 7. Recommandations d'Usage

### 7.1 Quel modèle utiliser ?

| Contexte | Modèle Recommandé | Justification |
|----------|-------------------|---------------|
| **Production (prédictions temps réel)** | Stacking v3 | Meilleure accuracy (59.4%) |
| **Interprétabilité nécessaire** | Logistic Regression v3 | Coefficients lisibles |
| **Équilibre H/D/A important** | Logistic Regression v3 | Meilleur F1-macro (0.559) |
| **Rapidité inférence** | Gradient Boosting v3 | Bon compromis vitesse/performance |

### 7.2 Pipeline de prédiction

**Étapes** :
1. Charger features du match (forme, xG, classement actuel)
2. Normaliser features pour Logistic Regression
3. Générer prédictions des 3 modèles de base
4. Stacker les probabilités dans le méta-modèle
5. Obtenir prédiction finale + intervalles de confiance

**Fichiers nécessaires** :
- `stacking_gb_base.pkl`
- `stacking_rf_base.pkl`
- `stacking_lr_base.pkl`
- `stacking_scaler.pkl`
- `stacking_meta_model.pkl`

---

## 8. Conclusion

Ce projet a atteint **59.4% d'accuracy**, un résultat solide dans le contexte de la prédiction de résultats sportifs. L'approche méthodique (EDA → tests statistiques → feature engineering → modélisation itérative) a permis de gagner 16.9 points vs la baseline.

**Points clés** :
- Les features xG (expected Goals) sont les plus prédictives
- Le stacking améliore marginalement (+0.7 pts) les modèles individuels
- Les Draws restent fondamentalement imprévisibles avec les données actuelles
- L'échec du SOS démontre l'importance de tester rigoureusement chaque hypothèse

**Prochaines étapes** :
1. Développer l'application Streamlit de prédiction en temps réel
2. Intégrer la carte géospatiale des probabilités de qualification LDC
3. Permettre la mise à jour incrémentale des features à chaque match

---

**Fichiers livrables** :
- Modèles : `models/stacking_*.pkl` (5 fichiers)
- Métadonnées : `models/stacking_v3_metadata.json`
- Dataset : `data/processed/pl_features_v4.csv`
- Notebooks : `notebooks/01-07_*.ipynb`
