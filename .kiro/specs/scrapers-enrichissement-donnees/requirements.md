# Requirements Document

## Introduction

Ce document définit les exigences pour le développement de deux scrapers web destinés à enrichir le dataset de prédiction de matchs de Premier League. Le modèle baseline actuel (v1) plafonne à 50% d'accuracy avec une incapacité structurelle à prédire les matchs nuls (8% recall). L'objectif est de récupérer des données externes (xG de FBref et valeurs marchandes de Transfermarkt) pour dépasser ce plafond et améliorer significativement la prédiction des draws.

Les deux scrapers fonctionneront de manière autonome, produisant des fichiers CSV compatibles avec le dataset existant (pl_features_v1.csv) pour intégration future dans le notebook 05bis de feature engineering.

## Glossary

- **Scraper**: Programme automatisé qui extrait des données structurées depuis des pages web HTML
- **FBref_Scraper**: Module de scraping ciblant le site FBref.com pour récupérer les statistiques xG
- **Transfermarkt_Scraper**: Module de scraping ciblant le site Transfermarkt.com pour récupérer les valeurs marchandes
- **xG**: Expected Goals, métrique statistique mesurant la probabilité de marquer un but depuis une position donnée
- **Rate_Limiter**: Composant contrôlant le délai entre requêtes HTTP pour respecter les conditions d'utilisation des sites
- **Cache_Manager**: Composant stockant les pages HTML téléchargées pour éviter les requêtes répétées
- **Data_Validator**: Composant vérifiant la cohérence et le format des données extraites
- **CSV_Exporter**: Composant générant les fichiers CSV formatés pour intégration dans le dataset
- **Squad_Value**: Valeur marchande totale de l'effectif d'une équipe à un moment donné (en millions €)
- **Season_Range**: Intervalle de saisons à scraper, spécifié au format "YYYY-YYYY" (ex: "2017-2026")
- **Retry_Handler**: Composant gérant les tentatives de re-connexion en cas d'échec de requête HTTP

## Requirements

### Requirement 1: Récupération des données xG depuis FBref

**User Story:** As a data scientist, I want to scrape xG statistics from FBref, so that I can enrich the prediction dataset with shot quality metrics.

#### Acceptance Criteria

1. WHEN the user executes the FBref_Scraper with a Season_Range parameter, THE FBref_Scraper SHALL retrieve xG home and xG away data for all Premier League matches in the specified seasons
2. THE FBref_Scraper SHALL target the URL pattern `https://fbref.com/en/comps/9/{season}/schedule/` for each season in the range
3. WHEN parsing match data, THE FBref_Scraper SHALL extract Date, HomeTeam, AwayTeam, Home_xG, and Away_xG fields
4. IF a season is not available on FBref (before 2017/18), THEN THE FBref_Scraper SHALL log a warning and skip that season
5. FOR ALL extracted xG values, THE Data_Validator SHALL verify they are numeric values between 0.0 and 15.0
6. WHEN multiple HTML structures are encountered, THE FBref_Scraper SHALL handle parsing variations gracefully and log parsing failures

### Requirement 2: Récupération des valeurs marchandes depuis Transfermarkt

**User Story:** As a data scientist, I want to scrape squad market values from Transfermarkt, so that I can measure the objective strength of teams over time.

#### Acceptance Criteria

1. WHEN the user executes the Transfermarkt_Scraper with a Season_Range parameter, THE Transfermarkt_Scraper SHALL retrieve Squad_Value data for all Premier League teams in the specified seasons
2. THE Transfermarkt_Scraper SHALL target the URL pattern `https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/plus/?saison_id={year}` for each season
3. WHEN parsing team data, THE Transfermarkt_Scraper SHALL extract Season, Team, and Squad_Value fields
4. THE Transfermarkt_Scraper SHALL convert Squad_Value from display format (e.g., "500m €", "45.5m €") to numeric millions (500.0, 45.5)
5. IF a team name differs from the standard dataset naming (e.g., "Man Utd" vs "Man United"), THEN THE Transfermarkt_Scraper SHALL apply name normalization mapping
6. FOR ALL extracted Squad_Value entries, THE Data_Validator SHALL verify values are numeric and between 10.0 and 2000.0 million euros

### Requirement 3: Respect des contraintes de rate limiting

**User Story:** As a responsible developer, I want to implement rate limiting, so that I avoid IP bans and respect the terms of service of scraped websites.

#### Acceptance Criteria

1. THE Rate_Limiter SHALL enforce a minimum delay of 1.0 second between consecutive HTTP requests to the same domain
2. WHERE the user specifies a custom delay via CLI parameter, THE Rate_Limiter SHALL apply that delay instead of the default
3. WHEN a request returns HTTP 429 (Too Many Requests) or 503 (Service Unavailable), THE Retry_Handler SHALL wait 60 seconds before retrying
4. THE Retry_Handler SHALL attempt a maximum of 3 retries for failed requests before logging an error and continuing to the next item
5. WHEN the FBref_Scraper or Transfermarkt_Scraper completes execution, THE scraper SHALL log the total number of requests made and total execution time

### Requirement 4: Gestion robuste des erreurs et logging

**User Story:** As a developer, I want comprehensive error handling and logging, so that I can diagnose issues and monitor scraping progress.

#### Acceptance Criteria

1. WHEN any HTTP request fails with a network error, THE Retry_Handler SHALL log the error details and attempt retry according to Requirement 3
2. WHEN HTML parsing fails for a specific page, THE scraper SHALL log the failure with page URL and continue processing remaining pages
3. THE FBref_Scraper and Transfermarkt_Scraper SHALL log progress information every 10 processed items (e.g., "Processed 20/380 matches")
4. IF the Data_Validator detects invalid data (out of range, wrong format), THEN THE Data_Validator SHALL log a warning with the problematic value and exclude that row from export
5. WHEN scraping completes, THE scraper SHALL log a summary including: total items processed, successful extractions, failed extractions, and validation errors
6. THE FBref_Scraper and Transfermarkt_Scraper SHALL write logs to files in `logs/scraping_fbref_{timestamp}.log` and `logs/scraping_transfermarkt_{timestamp}.log`

### Requirement 5: Système de cache pour éviter le re-scraping

**User Story:** As a developer, I want to cache downloaded HTML pages, so that I can re-run parsing logic without making redundant HTTP requests.

#### Acceptance Criteria

1. WHEN the FBref_Scraper or Transfermarkt_Scraper downloads an HTML page successfully, THE Cache_Manager SHALL save the raw HTML to `data/external/cache/{source}/{season}_{identifier}.html`
2. WHEN a scraper attempts to fetch a page, THE Cache_Manager SHALL check if a cached version exists and is less than 30 days old
3. IF a valid cache file exists, THEN THE Cache_Manager SHALL load HTML from cache instead of making an HTTP request
4. WHERE the user specifies a `--force-refresh` CLI flag, THE Cache_Manager SHALL ignore cache and re-download all pages
5. THE Cache_Manager SHALL create a metadata file `data/external/cache/cache_index.json` recording cached files with timestamps and source URLs

### Requirement 6: Export CSV formaté et documenté

**User Story:** As a data scientist, I want clean CSV outputs with documentation, so that I can easily integrate scraped data into the existing pipeline.

#### Acceptance Criteria

1. WHEN FBref_Scraper completes, THE CSV_Exporter SHALL write data to `data/external/fbref_xg_{start_season}_{end_season}.csv`
2. THE FBref CSV file SHALL contain columns: Date (YYYY-MM-DD), Season (4-digit format, e.g., "1718"), HomeTeam, AwayTeam, Home_xG (float), Away_xG (float)
3. WHEN Transfermarkt_Scraper completes, THE CSV_Exporter SHALL write data to `data/external/transfermarkt_values_{start_season}_{end_season}.csv`
4. THE Transfermarkt CSV file SHALL contain columns: Season (4-digit format), Team (normalized name), Squad_Value (float, millions €)
5. THE CSV_Exporter SHALL sort rows chronologically by Date (FBref) or Season then Team (Transfermarkt)
6. THE CSV_Exporter SHALL create a README file `data/external/README.md` documenting column definitions, data sources, scraping date, and season coverage

### Requirement 7: Interface en ligne de commande (CLI)

**User Story:** As a user, I want a simple command-line interface, so that I can easily execute scrapers with custom parameters.

#### Acceptance Criteria

1. THE FBref_Scraper SHALL accept CLI arguments: `--seasons` (required, format "YYYY-YYYY"), `--delay` (optional, default 1.0), `--force-refresh` (optional flag)
2. THE Transfermarkt_Scraper SHALL accept the same CLI arguments as FBref_Scraper
3. WHEN the user provides invalid season format, THE scraper SHALL display an error message and exit with code 1
4. WHEN the user provides `--help` flag, THE scraper SHALL display usage instructions including parameter descriptions and examples
5. THE scraper SHALL display a confirmation prompt showing the number of seasons to scrape and estimated execution time before starting
6. WHEN scraping completes successfully, THE scraper SHALL exit with code 0 and print the output CSV file path

### Requirement 8: Normalisation des noms d'équipes

**User Story:** As a data scientist, I want consistent team naming, so that I can merge scraped data with the existing dataset without manual corrections.

#### Acceptance Criteria

1. THE FBref_Scraper and Transfermarkt_Scraper SHALL load a team name mapping file from `config/team_names_mapping.json`
2. THE mapping file SHALL contain key-value pairs mapping source variations to canonical names (e.g., `{"Man Utd": "Man United", "Spurs": "Tottenham"}`)
3. WHEN a scraped team name matches a mapping key, THE scraper SHALL replace it with the canonical name before export
4. IF a scraped team name is not found in mapping and not in the canonical list, THEN THE scraper SHALL log a warning with the unmapped name
5. THE team_names_mapping.json file SHALL be created with initial mappings for common FBref and Transfermarkt variations based on the existing pl_features_v1.csv team list

### Requirement 9: Validation de cohérence des données

**User Story:** As a data scientist, I want automatic data validation, so that I can trust the quality of scraped data without manual inspection.

#### Acceptance Criteria

1. FOR ALL scraped matches (FBref), THE Data_Validator SHALL verify that Date is within the expected season range (August to May)
2. FOR ALL xG values, THE Data_Validator SHALL verify Home_xG + Away_xG is less than 20.0 (sanity check for implausible values)
3. FOR ALL scraped Squad_Value entries, THE Data_Validator SHALL verify that values are monotonically increasing or stable over consecutive seasons for the same team (teams rarely lose 50%+ value instantly)
4. IF a team's Squad_Value drops by more than 40% between consecutive seasons, THEN THE Data_Validator SHALL log a warning for manual review
5. THE Data_Validator SHALL verify that each season contains between 340-400 matches (FBref) or 20-22 teams (Transfermarkt)
6. WHEN validation completes, THE Data_Validator SHALL generate a validation report `data/external/validation_report_{source}_{timestamp}.txt` listing all warnings and errors

### Requirement 10: Gestion des structures HTML changeantes

**User Story:** As a maintainer, I want robust HTML parsing, so that the scrapers continue working when website structures change.

#### Acceptance Criteria

1. THE FBref_Scraper SHALL attempt multiple CSS selector strategies in order of preference (primary, fallback, generic) for locating xG data in tables
2. THE Transfermarkt_Scraper SHALL attempt multiple CSS selector strategies for locating Squad_Value data
3. WHEN the primary CSS selector fails to find expected data, THE scraper SHALL try the next fallback selector and log which strategy succeeded
4. IF all selector strategies fail for a page, THEN THE scraper SHALL save the problematic HTML to `data/external/failed_parses/{source}_{timestamp}.html` for manual inspection
5. THE scraper SHALL include CSS selectors as configuration in `config/scraping_selectors.json` to allow updates without code changes
6. THE scraping_selectors.json file SHALL document the last verified date for each selector pattern

### Requirement 11: Parsing et Pretty Printing de configurations

**User Story:** As a developer, I want to parse scraper configuration files, so that I can customize behavior without modifying code.

#### Acceptance Criteria

1. WHEN the FBref_Scraper or Transfermarkt_Scraper starts, THE Config_Parser SHALL parse the JSON configuration files (team_names_mapping.json, scraping_selectors.json)
2. WHEN a configuration file is malformed or missing required fields, THE Config_Parser SHALL return a descriptive error message indicating the problematic field
3. THE Pretty_Printer SHALL format configuration objects back into valid JSON files with 2-space indentation
4. FOR ALL valid configuration objects, parsing then printing then parsing SHALL produce an equivalent object (round-trip property)

### Requirement 12: Tests de propriétés pour parsers et validators

**User Story:** As a developer, I want property-based tests, so that I can verify scraper components handle edge cases correctly.

#### Acceptance Criteria

1. FOR ALL generated xG values in range [0.0, 15.0], parsing then formatting then parsing SHALL return equivalent numeric values within 0.01 tolerance
2. FOR ALL generated Squad_Value strings in formats ("X.Xm €", "XXXm €", "X.XXbn €"), THE Transfermarkt_Scraper SHALL correctly convert to numeric millions
3. FOR ALL generated team name variations, THE team name normalizer SHALL consistently map to the same canonical name or return the original if unmapped
4. FOR ALL generated Date strings in ISO format, THE FBref_Scraper SHALL correctly parse to datetime objects and back to ISO strings (round-trip)
5. FOR ALL generated HTML structures with xG data in different table positions, THE CSS selector fallback strategy SHALL successfully extract xG values
