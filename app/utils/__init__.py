"""
Module utilitaires
"""
from .model_loader import StackingPredictor
from .historical_data import (
    load_historical_data,
    get_available_seasons,
    get_season_standings,
    get_season_top6_evolution,
    get_last_5_champions,
    get_season_stats,
    get_top_scorer,
    assign_matchweek,
    build_animated_top6,
    get_titles_ranking,
)

__all__ = [
    'StackingPredictor',
    'load_historical_data',
    'get_available_seasons',
    'get_season_standings',
    'get_season_top6_evolution',
    'get_last_5_champions',
    'get_season_stats',
    'get_top_scorer',
    'assign_matchweek',
    'build_animated_top6',
    'get_titles_ranking',
]
