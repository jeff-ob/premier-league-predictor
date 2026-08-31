# Implementation Plan: Scrapers d'enrichissement de données

## Overview

Ce plan implémente deux scrapers web (FBref et Transfermarkt) avec une architecture modulaire basée sur des composants réutilisables. L'implémentation suivra une approche progressive : d'abord les composants de base (rate limiter, cache, validation), ensuite les scrapers concrets, puis les interfaces CLI, et enfin les tests.

## Tasks

- [x] 1. Créer la structure de base et les composants core
  - [x] 1.1 Créer la structure de dossiers et fichiers
    - Créer `src/scraping/__init__.py`
    - Créer les fichiers vides pour tous les modules : `base_scraper.py`, `rate_limiter.py`, `cache_manager.py`, `data_validator.py`, `csv_exporter.py`, `config_parser.py`, `utils.py`
    - Créer les dossiers de configuration : `config/`, `logs/`, `data/external/cache/`
    - _Requirements: 3.1, 4.1, 5.1, 6.1, 7.1_

  - [x] 1.2 Implémenter la classe RateLimiter
    - Écrire la classe `RateLimiter` avec méthode `wait()` appliquant le délai configurable
    - Implémenter le thread-safe locking pour éviter les race conditions
    - Gérer le délai par défaut de 1.0 seconde entre requêtes
    - _Requirements: 3.1, 3.2_

  - [ ]* 1.3 Écrire les tests unitaires pour RateLimiter
    - Tester que le délai est appliqué correctement
    - Tester le comportement thread-safe avec requêtes concurrentes
    - Tester le custom delay parameter
    - _Requirements: 3.1, 3.2_

  - [x] 1.4 Implémenter la classe CacheManager
    - Écrire la classe `CacheManager` avec méthodes `get()`, `save()`, et `_load_index()`
    - Implémenter la logique de vérification de TTL (30 jours par défaut)
    - Générer `cache_index.json` avec métadonnées (URL, file_path, timestamp)
    - Créer la structure de dossiers `data/external/cache/{source}/`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 1.5 Écrire les tests unitaires pour CacheManager
    - Tester cache hit et cache miss scenarios
    - Tester l'expiration du cache basée sur TTL
    - Tester force-refresh flag qui ignore le cache
    - Tester la génération correcte de cache_index.json
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 2. Implémenter les composants de validation et export

  - [x] 2.1 Implémenter la classe DataValidator
    - Écrire la classe `DataValidator` avec méthodes `validate()`, `_validate_fbref()`, `_validate_transfermarkt()`
    - Implémenter les validations FBref : xG range [0.0, 15.0], total xG < 20.0, date dans la saison
    - Implémenter les validations Transfermarkt : Squad_Value range [10.0, 2000.0], coherence temporelle (drop < 40%)
    - Implémenter `generate_report()` pour créer le rapport de validation
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 1.5, 2.6_

  - [ ]* 2.2 Écrire les tests unitaires pour DataValidator
    - Tester validation des xG values (in range, out of range, implausible totals)
    - Tester validation des Squad_Value (range, temporal coherence)
    - Tester génération du rapport de validation
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 2.3 Implémenter la classe CSVExporter
    - Écrire la classe `CSVExporter` avec méthodes `export_fbref()`, `export_transfermarkt()`, `create_readme()`
    - Implémenter le tri chronologique pour FBref (par Date)
    - Implémenter le tri pour Transfermarkt (par Season puis Team)
    - Générer les fichiers CSV avec les colonnes correctes et le format de nommage
    - Créer `README.md` documentant les colonnes, sources, dates
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [ ]* 2.4 Écrire les tests unitaires pour CSVExporter
    - Tester export FBref avec tri chronologique correct
    - Tester export Transfermarkt avec tri par saison et équipe
    - Tester génération du README.md avec métadonnées correctes
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 3. Implémenter le parsing de configuration et les utilitaires

  - [x] 3.1 Implémenter la classe ConfigParser
    - Écrire la classe `ConfigParser` avec méthodes `load_team_mapping()`, `load_selectors()`, `save_json()`
    - Implémenter la validation de la structure JSON (vérifier clés requises)
    - Gérer les erreurs de fichiers manquants ou JSON malformé
    - Implémenter le pretty printing avec indentation de 2 espaces
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [ ]* 3.2 Écrire les tests unitaires pour ConfigParser
    - Tester parsing de fichiers JSON valides
    - Tester détection d'erreurs pour JSON malformé
    - Tester round-trip property: parse → print → parse produit objet équivalent
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [x] 3.3 Créer les fichiers de configuration JSON initiaux
    - Créer `config/team_names_mapping.json` avec mappings des variations de noms d'équipes
    - Créer `config/scraping_selectors.json` avec les CSS selectors pour FBref et Transfermarkt
    - Inclure les dates de vérification (`last_verified`) pour chaque sélecteur
    - _Requirements: 8.1, 8.2, 8.5, 10.5, 10.6_

  - [x] 3.4 Implémenter les fonctions utilitaires dans utils.py
    - Écrire `normalize_team_name()` qui applique le mapping de noms d'équipes
    - Écrire `parse_season_range()` qui convertit "2017-2026" en (2017, 2026)
    - Écrire `format_season_code()` qui convertit 2017 en "1718"
    - Gérer les warnings pour les noms d'équipes non mappés
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ]* 3.5 Écrire les tests unitaires pour utils.py
    - Tester normalize_team_name avec variations connues et inconnues
    - Tester parse_season_range avec formats valides et invalides
    - Tester format_season_code pour différentes années
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 4. Checkpoint - Vérifier que tous les composants de base fonctionnent
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implémenter la classe abstraite BaseScraper

  - [x] 5.1 Créer la classe abstraite BaseScraper
    - Écrire la classe `BaseScraper` avec méthodes abstraites `build_urls()` et `parse_page()`
    - Implémenter `fetch_page()` avec logique de cache et rate limiting
    - Implémenter `_fetch_with_retry()` avec exponential backoff (max 3 tentatives)
    - Implémenter `run()` comme méthode d'exécution principale orchestrant le scraping
    - Implémenter `_setup_logger()` pour créer les loggers avec fichiers timestampés
    - Gérer les HTTP status codes 429/503 avec wait de 60 secondes
    - _Requirements: 3.1, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3_

  - [ ]* 5.2 Écrire les tests unitaires pour BaseScraper
    - Tester fetch_page avec cache hit et cache miss
    - Tester retry logic avec différents status codes (200, 429, 503, 404)
    - Tester exponential backoff timing
    - Tester logging de progression (every 10 items)
    - Mocker les appels HTTP avec `requests`
    - _Requirements: 3.3, 3.4, 4.1, 4.2, 4.3_

- [x] 6. Implémenter le scraper FBref

  - [x] 6.1 Créer la classe FBrefScraper
    - Écrire la classe `FBrefScraper` héritant de `BaseScraper`
    - Implémenter `build_urls()` générant les URLs FBref pour le season range
    - Implémenter `parse_page()` avec stratégie de CSS selectors (primary → fallback → generic)
    - Implémenter `_parse_match_row()` extrayant Date, Season, HomeTeam, AwayTeam, Home_xG, Away_xG
    - Gérer les échecs de parsing en sauvegardant le HTML problématique dans `data/external/failed_parses/`
    - Logger quel sélecteur a réussi pour chaque page
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 10.1, 10.2, 10.3, 10.4_

  - [ ]* 6.2 Écrire les tests unitaires pour FBrefScraper
    - Tester build_urls pour différents season ranges
    - Tester parse_page avec fixtures HTML réalistes
    - Tester fallback de CSS selectors lorsque primary échoue
    - Tester extraction correcte des données xG
    - Tester gestion des warnings pour saisons non disponibles (avant 2017/18)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6_

- [x] 7. Implémenter le scraper Transfermarkt

  - [x] 7.1 Créer la classe TransfermarktScraper
    - Écrire la classe `TransfermarktScraper` héritant de `BaseScraper`
    - Implémenter `build_urls()` générant les URLs Transfermarkt pour le season range
    - Implémenter `parse_page()` avec stratégie de CSS selectors
    - Implémenter `_parse_team_row()` extrayant Season, Team, Squad_Value
    - Implémenter `_convert_squad_value()` convertissant formats "500m €", "1.5bn €" en numeric millions
    - Appliquer la normalisation de noms d'équipes via `normalize_team_name()`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 8.3, 10.1, 10.2, 10.3_

  - [ ]* 7.2 Écrire les tests unitaires pour TransfermarktScraper
    - Tester build_urls pour différents season ranges
    - Tester parse_page avec fixtures HTML
    - Tester _convert_squad_value avec différents formats ("45.5m €", "500m €", "1.5bn €")
    - Tester application correcte de normalize_team_name
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 8. Checkpoint - Vérifier que les scrapers fonctionnent de bout en bout
  - Ensure all tests pass, ask the user if questions arise.

- [-] 9. Implémenter les interfaces CLI

  - [x] 9.1 Créer le CLI pour FBref (scrape_fbref.py)
    - Écrire le script CLI `src/scraping/scrape_fbref.py` avec argparse
    - Ajouter les arguments : `--seasons` (required), `--delay` (optional, default 1.0), `--force-refresh` (optional flag)
    - Implémenter la validation du format de saison (error exit code 1 si invalide)
    - Implémenter `--help` avec descriptions et exemples
    - Afficher une confirmation avec nombre de saisons et temps estimé
    - Orchestrer l'exécution : load config → initialize components → run scraper → export CSV → generate report
    - Afficher le résumé final avec path du fichier CSV de sortie (exit code 0 si succès)
    - _Requirements: 7.1, 7.3, 7.4, 7.5, 7.6_

  - [x] 9.2 Créer le CLI pour Transfermarkt (scrape_transfermarkt.py)
    - Écrire le script CLI `src/scraping/scrape_transfermarkt.py` avec la même structure que FBref
    - Implémenter les mêmes arguments CLI et validations
    - Orchestrer l'exécution complète du TransfermarktScraper
    - _Requirements: 7.2, 7.3, 7.4, 7.5, 7.6_

  - [ ]* 9.3 Écrire les tests d'intégration pour les CLIs
    - Tester execution end-to-end du CLI FBref avec arguments valides
    - Tester execution end-to-end du CLI Transfermarkt
    - Tester gestion d'erreurs pour arguments invalides
    - Tester flag --help affiche les instructions
    - Vérifier que les fichiers CSV et rapports sont générés correctement
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [ ] 10. Implémenter les tests de propriétés (property-based tests)

  - [ ]* 10.1 Écrire les property tests pour le parsing xG
    - Créer `tests/property_tests/test_xg_parsing_properties.py`
    - **Property 1: Round-trip pour xG values**
    - **Valide: Requirements 12.1**
    - Utiliser hypothesis pour générer xG values dans [0.0, 15.0]
    - Tester que parse → format → parse retourne la valeur originale (tolérance 0.01)
    - _Requirements: 12.1_

  - [ ]* 10.2 Écrire les property tests pour la conversion Squad_Value
    - Créer `tests/property_tests/test_squad_value_properties.py`
    - **Property 2: Conversion correcte des formats Squad_Value**
    - **Valide: Requirements 12.2**
    - Utiliser hypothesis pour générer strings variés : "X.Xm €", "XXXm €", "X.XXbn €"
    - Tester que _convert_squad_value() convertit correctement en numeric millions
    - _Requirements: 12.2_

  - [ ]* 10.3 Écrire les property tests pour la normalisation de noms d'équipes
    - Créer `tests/property_tests/test_team_normalization_properties.py`
    - **Property 3: Consistance de la normalisation de noms**
    - **Valide: Requirements 12.3**
    - Utiliser hypothesis pour générer variations de noms d'équipes
    - Tester que normalize_team_name() mappe toujours au même canonical name
    - Tester que les noms non mappés sont retournés inchangés
    - _Requirements: 12.3_

  - [ ]* 10.4 Écrire les property tests pour le parsing de dates
    - Créer `tests/property_tests/test_date_parsing_properties.py`
    - **Property 4: Round-trip pour Date parsing**
    - **Valide: Requirements 12.4**
    - Utiliser hypothesis pour générer dates ISO format
    - Tester que parse → format → parse retourne la date originale
    - _Requirements: 12.4_

  - [ ]* 10.5 Écrire les property tests pour les selectors CSS
    - Créer `tests/property_tests/test_css_selector_properties.py`
    - **Property 5: Extraction réussie avec selectors variés**
    - **Valide: Requirements 12.5**
    - Générer structures HTML avec xG data à différentes positions de table
    - Tester que la stratégie de fallback des CSS selectors extrait toujours les valeurs xG
    - _Requirements: 12.5_

- [x] 11. Finalisation et documentation

  - [x] 11.1 Créer le fichier requirements.txt
    - Lister toutes les dépendances : `requests`, `beautifulsoup4`, `pandas`, `lxml`, `hypothesis`, `pytest`
    - Inclure les versions spécifiques pour reproducibilité
    - _Requirements: ALL_

  - [x] 11.2 Créer la documentation README pour les scrapers
    - Créer `src/scraping/README.md` expliquant l'architecture et l'utilisation
    - Documenter les commandes CLI avec exemples
    - Documenter la structure des fichiers de configuration
    - Inclure des exemples d'utilisation pour les deux scrapers
    - _Requirements: 7.1, 7.2, 8.1, 10.5_

  - [x] 11.3 Checkpoint final - Tester l'exécution complète
    - Exécuter le scraper FBref pour une petite plage (ex: 2023-2024)
    - Exécuter le scraper Transfermarkt pour la même plage
    - Vérifier que les fichiers CSV sont générés correctement
    - Vérifier que les rapports de validation sont créés
    - Vérifier que le cache fonctionne en ré-exécutant les scrapers
    - Ensure all tests pass, ask the user if questions arise.

## Notes

- Les tâches marquées avec `*` sont optionnelles et peuvent être sautées pour un MVP plus rapide
- Chaque tâche référence les requirements spécifiques pour traçabilité
- Les checkpoints permettent de valider le progrès incrémental
- Les property tests valident les propriétés universelles de transformation de données
- Les tests unitaires valident les exemples spécifiques et cas limites
- L'architecture modulaire permet de tester chaque composant isolément avant intégration

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.4", "3.1", "3.3", "3.4"] },
    { "id": 2, "tasks": ["1.3", "1.5", "2.1", "3.2", "3.5"] },
    { "id": 3, "tasks": ["2.2", "2.3", "5.1"] },
    { "id": 4, "tasks": ["2.4", "5.2", "6.1"] },
    { "id": 5, "tasks": ["6.2", "7.1"] },
    { "id": 6, "tasks": ["7.2", "9.1", "9.2"] },
    { "id": 7, "tasks": ["9.3", "10.1", "10.2", "10.3", "10.4", "10.5", "11.1", "11.2"] }
  ]
}
```
