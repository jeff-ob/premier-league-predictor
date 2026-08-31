# Premier League 2026-27 — Prédictions & Analyse LDC

Application de prédiction des résultats de matchs de Premier League avec suivi du classement en temps réel, simulation Monte Carlo des probabilités de qualification en Ligue des Champions, et backtest du modèle sur les saisons passées.

---

## Résultat final du modèle

| Modèle | Accuracy | Gain vs baseline |
|---|---|---|
| **Stacking v3 (GB + RF + LR)** | **59.4%** | **+16.9 pts** |
| Gradient Boosting v3 | 58.7% | +16.2 pts |
| Random Forest v3 | 57.8% | +15.3 pts |
| Logistic Regression v3 | 57.3% | +14.8 pts |
| Baseline (toujours Home) | 42.5% | — |

Le modèle utilise 18 features dynamiques : forme récente, classement, séries, différence de buts, statistiques de tir, et expected Goals (xG) — calculées à partir de données réelles 1993-2026.

---

## Application Streamlit

L'application se compose de 5 pages accessibles depuis une navigation latérale :

| Page | Contenu |
|---|---|
| **P100 — Accueil** | Historique des saisons 2000/01-2025/26 : champion, classement, évolution Top 6 animée, palmarès |
| **P200 — Classement** | Classement 2026-27 en temps réel + probabilités LDC/Titre/Relégation via Monte Carlo (10 000 sims) |
| **P300 — Matchs** | Prédictions journée par journée (H/D/A + score Poisson), résultats réels, accuracy du modèle |
| **P400 — Simulation** | Backtest du modèle : simulation pré-saison vs classement réel (2025/26) |
| **P500 — Carte** | Carte interactive des 20 stades avec logos, capacités et contexte 2026-27 |

### Lancer l'application

```bash
cd app
streamlit run Home.py
```

URL : http://localhost:8501

---

## Structure du projet

```
pl-ldc-prediction/
│
├── app/                          # Application Streamlit
│   ├── Home.py                   # Point d'entrée + navigation
│   ├── pages/
│   │   ├── 1_Accueil.py          # P100 — Historique
│   │   ├── 2_Classement.py       # P200 — Classement + Monte Carlo
│   │   ├── 3_Matchs.py           # P300 — Prédictions journée
│   │   ├── 4_Simulation.py       # P400 — Backtest
│   │   └── 5_Carte.py            # P500 — Carte stades
│   ├── utils/
│   │   ├── historical_data.py    # Classements historiques, top 6, palmarès
│   │   ├── season_2627.py        # Prédictions, Monte Carlo, mise à jour résultats
│   │   └── model_loader.py       # Chargeur modèle stacking
│   ├── assets/style.css          # Design system dark mode
│   └── data/                     # Caches précalculés (proba, lambda, backtest)
│
├── models/                       # Modèles entraînés
│   ├── stacking_gb_base.pkl      # Gradient Boosting
│   ├── stacking_rf_base.pkl      # Random Forest
│   ├── stacking_lr_base.pkl      # Logistic Regression
│   ├── stacking_scaler.pkl       # Scaler pour LR
│   ├── stacking_meta_model.pkl   # Méta-modèle LR
│   └── stacking_v3_metadata.json # Métadonnées (accuracy, features, params)
│
├── notebooks/
│   ├── 01_exploration.ipynb
│   ├── 02_eda_simple.ipynb
│   ├── 03_eda_approfondie.ipynb
│   ├── 04_tests_statistiques.ipynb
│   ├── 05_Feature_Engineering v1.ipynb
│   ├── 05bis_exploration_kaggle.ipynb
│   ├── 06_Modélisation.ipynb
│   ├── 07_SOS_Feature_Engineering.ipynb
│   └── 08_experimentation_app.ipynb  # Validation logique app (classements, Monte Carlo)
│
├── data/
│   ├── raw/
│   │   ├── pl_all_seasons.csv        # Historique PL 1993-2026 (12 279 matchs)
│   │   ├── fixtures.csv              # Calendrier 2026-27 (380 matchs)
│   │   ├── teams_and_stadiums.csv    # Stades + contexte 2026-27
│   │   ├── managers_and_club_info.csv
│   │   └── england-master/           # Résultats 2026-27 (openfootball)
│   ├── external/
│   │   ├── epl_raw.csv               # xG, PPDA, deep completions (2020-2026)
│   │   ├── kaggle_squad_values_by_season.csv
│   │   └── transfermarkt_values_2324_2425.csv
│   └── processed/
│       └── pl_features_v4.csv        # Dataset ML final (12 279 × 46)
│
├── config/
│   ├── team_names_mapping.json
│   └── scraping_selectors.json
│
├── src/                          # Code source (scraping, feature engineering)
├── tests/                        # Tests unitaires
├── FINAL_MODELING_REPORT.md      # Rapport complet de modélisation
├── requirements.txt
└── requirements-scraping.txt
```

---

## Installation

```bash
git clone https://github.com/<username>/pl-ldc-prediction.git
cd pl-ldc-prediction
pip install -r requirements.txt
```

Dépendances principales :

```
streamlit>=1.28
pandas>=2.0
numpy>=1.24
scikit-learn>=1.3
plotly>=5.0
folium>=0.17
streamlit-folium>=0.22
joblib>=1.3
scipy>=1.10
```

---

## Comment ça marche

### Prédictions (P300)

Pour chaque match, le modèle stacking calcule :
1. Les probabilités H/D/A via GB + RF + LR
2. Le méta-modèle LR combine les 9 sorties (3 modèles × 3 classes)
3. Le score le plus probable est estimé via un modèle de Poisson calibré sur les probabilités du stacking

Les probabilités sont précalculées une fois pour tous les 380 matchs de la saison (un seul appel au modèle — performances optimisées).

### Monte Carlo (P200)

La simulation tourne en ~75 secondes pour 10 000 itérations. Pour chaque simulation :
- Les matchs restants sont tirés selon les probabilités précalculées
- Le classement final est calculé
- On compte pour chaque équipe combien de fois elle finit dans le Top 4

### Mise à jour des résultats

Le bouton "Mettre à jour les résultats" sur P200 et P300 télécharge automatiquement le fichier de résultats officiel depuis GitHub ([openfootball/england](https://github.com/openfootball/england)).

---

## Features du modèle

18 features dynamiques recalculées après chaque match :

| Catégorie | Features |
|---|---|
| Forme | `Home_Form`, `Away_Form` (points sur 5 derniers matchs) |
| Classement | `Home_Rank`, `Away_Rank` |
| Séries | `Home_Streak`, `Away_Streak` |
| Buts | `Home_Goal_Diff`, `Away_Goal_Diff`, `Home_Rolling_GF/GA`, `Away_Rolling_GF/GA` |
| Rythme | `Home_Points_Pace`, `Away_Points_Pace` |
| xG | `Home_xG_Form`, `Away_xG_Form` |

Plus 15 features statiques issues de la saison précédente (squad values, npxG, PPDA, deep completions).

---

## Backtest 2025/26 (P400)

Résultat de la simulation pré-saison sur la saison 2025/26 :

- **Top 4 correct** : 2/4 (Man City + Arsenal)
- **Écart moyen de position** : 4.0 places
- **Surprises non anticipées** : Man United (3e réel, 12e simulé), Sunderland (7e réel, 17e simulé)

---

## Notebooks

| Notebook | Contenu |
|---|---|
| 01_exploration | Première exploration du dataset historique |
| 02_eda_simple | Analyse descriptive |
| 03_eda_approfondie | Corrélations, distributions, visualisations |
| 04_tests_statistiques | Tests Kruskal-Wallis, significativité des features |
| 05_Feature_Engineering | Création des 18 features dynamiques |
| 05bis_exploration_kaggle | Exploration données Kaggle squad values |
| 06_Modélisation | Entraînement GB/RF/LR + stacking, évaluation |
| 07_SOS_Feature_Engineering | Expérimentation Strength of Schedule (résultat : rejeté) |
| 08_experimentation_app | Validation de toute la logique métier de l'application |

---

## Rapport de modélisation

Voir [FINAL_MODELING_REPORT.md](FINAL_MODELING_REPORT.md) pour :
- Évolution complète des performances (v1 → v2 → v3 → stacking)
- Importance des features
- Expérimentations infructueuses (SOS)
- Comparaison avec l'état de l'art académique
- Limites et perspectives

---

## Sources de données

- **Historique matchs PL** : [football-data.co.uk](https://www.football-data.co.uk)
- **xG, PPDA, deep completions** : [understat.com](https://understat.com) via dataset Kaggle
- **Squad values** : [Transfermarkt](https://www.transfermarkt.com) via dataset Kaggle
- **Résultats 2026-27** : [openfootball/england](https://github.com/openfootball/england)
- **Logos clubs** : Premier League CDN

---

## Licence

MIT
