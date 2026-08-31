"""
Logique saison 2026-27 — prédictions, simulation Monte Carlo
Toutes les fonctions validées dans notebooks/08_experimentation_app.ipynb
"""
import re
import time
import random
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import PROJECT_ROOT

# ── Chemins ───────────────────────────────────────────────────────────────────
MODELS_DIR     = PROJECT_ROOT / 'models'
FIXTURES_FILE  = PROJECT_ROOT / 'data' / 'raw' / 'fixtures.csv'
EPL_RAW_FILE   = PROJECT_ROOT / 'data' / 'external' / 'epl_raw.csv'
SV_FILE        = PROJECT_ROOT / 'data' / 'external' / 'kaggle_squad_values_by_season.csv'
ENGLAND_MASTER = PROJECT_ROOT / 'data' / 'raw' / 'england-master' / '2026-27' / '1-premierleague.txt'
CACHE_DIR      = Path(__file__).parent.parent / 'data'
PROBA_CACHE_FILE  = CACHE_DIR / 'proba_cache.pkl'
LAMBDA_CACHE_FILE = CACHE_DIR / 'lambda_cache.pkl'

# Mapping noms england-master -> noms fixtures
NAME_CLEAN = {
    'Arsenal FC':                'Arsenal',
    'Coventry City FC':          'Coventry City',
    'Hull City AFC':             'Hull City',
    'Manchester United FC':      'Manchester United',
    'Ipswich Town FC':           'Ipswich Town',
    'Sunderland AFC':            'Sunderland',
    'Nottingham Forest FC':      'Nottingham Forest',
    'Leeds United FC':           'Leeds United',
    'Everton FC':                'Everton',
    'Crystal Palace FC':         'Crystal Palace',
    'Brentford FC':              'Brentford',
    'Tottenham Hotspur FC':      'Tottenham Hotspur',
    'Manchester City FC':        'Manchester City',
    'AFC Bournemouth':           'AFC Bournemouth',
    'Brighton & Hove Albion FC': 'Brighton & Hove Albion',
    'Aston Villa FC':            'Aston Villa',
    'Newcastle United FC':       'Newcastle United',
    'Liverpool FC':              'Liverpool',
    'Fulham FC':                 'Fulham',
    'Chelsea FC':                'Chelsea',
}

# Mapping noms epl_raw -> noms fixtures
EPL_NAME_MAP = {
    'Bournemouth':                  'AFC Bournemouth',
    'Brighton':                     'Brighton & Hove Albion',
    'Leeds':                        'Leeds United',
    'Tottenham':                    'Tottenham Hotspur',
    'Man City':                     'Manchester City',
    'Man United':                   'Manchester United',
    'Newcastle United':             'Newcastle United',
    "Nott'm Forest":                'Nottingham Forest',
    'Nottingham Forest':            'Nottingham Forest',
    'Wolverhampton Wanderers':      'Wolverhampton Wanderers',
}

# Mapping noms squad_values -> noms fixtures
SV_NAME_MAP = {
    'Arsenal FC':                'Arsenal',
    'Chelsea FC':                'Chelsea',
    'Liverpool FC':              'Liverpool',
    'Brentford FC':              'Brentford',
    'Everton FC':                'Everton',
    'Fulham FC':                 'Fulham',
    'Brighton and Hove Albion':  'Brighton & Hove Albion',
    'Sunderland AFC':            'Sunderland',
}

# Promus sans historique PL récent
PROMOTED_TEAMS = {'Coventry City', 'Hull City', 'Ipswich Town'}


# ── Chargement caches précalculés ────────────────────────────────────────────

def load_precomputed_caches():
    """
    Charger les caches précalculés depuis le notebook.
    Rapide — pas de modèle sklearn à charger.
    """
    import pickle
    with open(PROBA_CACHE_FILE, 'rb') as f:
        proba_cache = pickle.load(f)
    with open(LAMBDA_CACHE_FILE, 'rb') as f:
        lambda_cache = pickle.load(f)
    return proba_cache, lambda_cache


def caches_available():
    """Vérifier si les caches précalculés existent"""
    return PROBA_CACHE_FILE.exists() and LAMBDA_CACHE_FILE.exists()


# ── Chargement modèle ─────────────────────────────────────────────────────────

def load_stacking_model():
    """Charger les 5 composants du modèle stacking v3"""
    return {
        'gb'        : joblib.load(MODELS_DIR / 'stacking_gb_base.pkl'),
        'rf'        : joblib.load(MODELS_DIR / 'stacking_rf_base.pkl'),
        'lr'        : joblib.load(MODELS_DIR / 'stacking_lr_base.pkl'),
        'scaler'    : joblib.load(MODELS_DIR / 'stacking_scaler.pkl'),
        'meta'      : joblib.load(MODELS_DIR / 'stacking_meta_model.pkl'),
    }


FEATURE_NAMES = [
    'Home_Form', 'Home_Rank', 'Home_Streak', 'Home_Goal_Diff',
    'Home_Rolling_GF', 'Home_Rolling_GA', 'Home_Points_Pace', 'Home_Match_Number',
    'Away_Form', 'Away_Rank', 'Away_Streak', 'Away_Goal_Diff',
    'Away_Rolling_GF', 'Away_Rolling_GA', 'Away_Points_Pace', 'Away_Match_Number',
    'Home_Squad_Value', 'Home_Squad_Value_Mean', 'Home_Squad_Size',
    'Away_Squad_Value', 'Away_Squad_Value_Mean', 'Away_Squad_Size',
    'Squad_Value_Delta',
    'Home_npxG', 'Away_npxG',
    'Home_xPoints', 'Away_xPoints',
    'Home_PPDA', 'Away_PPDA',
    'Home_Deep', 'Away_Deep',
    'Home_xG_Form', 'Away_xG_Form',
]


# ── Features statiques 2026-27 ────────────────────────────────────────────────

def build_static_features():
    """
    Construire les features statiques pour chaque équipe 2026-27.
    Squad values depuis kaggle (saison 2627), stats xG depuis epl_raw (saison 2526).
    """
    fixtures = pd.read_csv(FIXTURES_FILE)
    teams    = sorted(set(fixtures['home_team']) | set(fixtures['away_team']))

    # Squad values saison 2627
    sv = pd.read_csv(SV_FILE)
    sv_2627 = sv[sv['Season'] == 2627][['Team_Name', 'Squad_Value_Total',
                                         'Squad_Value_Mean', 'Squad_Size']].copy()
    sv_2627['team'] = sv_2627['Team_Name'].replace(SV_NAME_MAP)
    sv_2627 = sv_2627.set_index('team')

    # Stats xG depuis epl_raw saison 2526
    epl      = pd.read_csv(EPL_RAW_FILE)
    epl_2526 = epl[epl['season'] == 2526].copy()

    # Moyenne ligue pour les promus
    league_avg = {
        'npxG': float(epl_2526[['home_np_xg', 'away_np_xg']].mean().mean()),
        'xPts': float(epl_2526[['home_expected_points', 'away_expected_points']].mean().mean()),
        'ppda': float(epl_2526[['home_ppda', 'away_ppda']].mean().mean()),
        'deep': float(epl_2526[['home_deep_completions', 'away_deep_completions']].mean().mean()),
    }

    # Stats par équipe
    epl_stats = {}
    for team in teams:
        epl_name = EPL_NAME_MAP.get(team, team)
        if team in PROMOTED_TEAMS:
            epl_stats[team] = league_avg.copy()
            continue

        hm = epl_2526[epl_2526['home_team'] == epl_name]
        am = epl_2526[epl_2526['away_team'] == epl_name]

        if len(hm) == 0 and len(am) == 0:
            epl_stats[team] = league_avg.copy()
        else:
            epl_stats[team] = {
                'npxG': float((hm['home_np_xg'].mean() + am['away_np_xg'].mean()) / 2),
                'xPts': float((hm['home_expected_points'].mean() + am['away_expected_points'].mean()) / 2),
                'ppda': float((hm['home_ppda'].mean() + am['away_ppda'].mean()) / 2),
                'deep': float((hm['home_deep_completions'].mean() + am['away_deep_completions'].mean()) / 2),
            }

    # Construire la table finale
    rows = []
    for team in teams:
        sv_row  = sv_2627.loc[team] if team in sv_2627.index else None
        ep      = epl_stats.get(team, league_avg)
        sv_val  = float(sv_row['Squad_Value_Total']) if sv_row is not None else 3e8
        sv_mean = float(sv_row['Squad_Value_Mean'])  if sv_row is not None else 1e7
        sv_size = float(sv_row['Squad_Size'])         if sv_row is not None else 25

        rows.append({
            'team'               : team,
            'Home_Squad_Value'   : sv_val,
            'Home_Squad_Value_Mean': sv_mean,
            'Home_Squad_Size'    : sv_size,
            'Away_Squad_Value'   : sv_val,
            'Away_Squad_Value_Mean': sv_mean,
            'Away_Squad_Size'    : sv_size,
            'Home_npxG'          : ep['npxG'],
            'Away_npxG'          : ep['npxG'],
            'Home_xPoints'       : ep['xPts'],
            'Away_xPoints'       : ep['xPts'],
            'Home_PPDA'          : ep['ppda'],
            'Away_PPDA'          : ep['ppda'],
            'Home_Deep'          : ep['deep'],
            'Away_Deep'          : ep['deep'],
        })

    return pd.DataFrame(rows).set_index('team')


# ── Résultats réels ───────────────────────────────────────────────────────────

def load_played_results():
    """
    Parser le fichier england-master 2026-27 pour récupérer
    tous les matchs déjà joués.
    """
    if not ENGLAND_MASTER.exists():
        return pd.DataFrame()

    content       = ENGLAND_MASTER.read_text(encoding='utf-8', errors='ignore')
    match_pattern = re.compile(
        r'^\s+(?:\d+:\d+\s+)?(.+?)\s+v\s+(.+?)\s+(\d+)-(\d+)\s+\(\d+-\d+\)',
        re.MULTILINE
    )

    results       = []
    current_md    = None

    for line in content.split('\n'):
        md = re.match(r'^▪ Matchday (\d+)', line)
        if md:
            current_md = int(md.group(1))
            continue
        m = match_pattern.match(line)
        if m:
            home_raw = m.group(1).strip()
            away_raw = m.group(2).strip()
            sh, sa   = int(m.group(3)), int(m.group(4))
            home     = NAME_CLEAN.get(home_raw, home_raw)
            away     = NAME_CLEAN.get(away_raw, away_raw)
            result   = 'H' if sh > sa else ('A' if sh < sa else 'D')
            results.append({
                'matchday' : current_md,
                'home_team': home,
                'away_team': away,
                'score_h'  : sh,
                'score_a'  : sa,
                'result'   : result,
            })

    return pd.DataFrame(results)


# ── Calcul classement depuis les résultats ────────────────────────────────────

def compute_standings_from_results(played_df, all_teams):
    """
    Calculer le classement actuel depuis les matchs joués.
    Inclut la forme des 5 derniers matchs.
    """
    stats = {t: {
        'points': 0, 'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
        'gf': 0, 'ga': 0, 'form': []
    } for t in all_teams}

    # Trier par journée
    for _, r in played_df.sort_values('matchday').iterrows():
        home, away = r['home_team'], r['away_team']
        sh, sa, res = r['score_h'], r['score_a'], r['result']

        if home not in stats or away not in stats:
            continue

        for team, is_home in [(home, True), (away, False)]:
            s  = stats[team]
            gf = sh if is_home else sa
            ga = sa if is_home else sh
            s['played'] += 1
            s['gf']     += gf
            s['ga']     += ga

            if (is_home and res == 'H') or (not is_home and res == 'A'):
                s['points'] += 3
                s['won']    += 1
                s['form'].append('W')
            elif res == 'D':
                s['points'] += 1
                s['drawn']  += 1
                s['form'].append('D')
            else:
                s['lost']   += 1
                s['form'].append('L')

    rows = []
    for t, s in stats.items():
        rows.append({
            'team'    : t,
            'played'  : s['played'],
            'won'     : s['won'],
            'drawn'   : s['drawn'],
            'lost'    : s['lost'],
            'gf'      : s['gf'],
            'ga'      : s['ga'],
            'gd'      : s['gf'] - s['ga'],
            'points'  : s['points'],
            'form'    : s['form'][-5:],
        })

    return (pd.DataFrame(rows)
              .sort_values(['points', 'gd', 'gf'], ascending=False)
              .reset_index(drop=True)
              .assign(pos=lambda df: range(1, len(df) + 1)))


# ── Précalcul des caches ──────────────────────────────────────────────────────

def build_caches(model, static_features):
    """
    Précalculer proba_cache et lambda_cache pour tous les 380 matchs.
    Un seul appel au modèle stacking.
    """
    from scipy.optimize import minimize
    from scipy.stats import poisson

    fixtures = pd.read_csv(FIXTURES_FILE)
    teams    = sorted(set(fixtures['home_team']) | set(fixtures['away_team']))

    init_dyn = {t: {
        'Form': 0, 'Rank': 10, 'Streak': 0, 'Goal_Diff': 0,
        'Rolling_GF': 1.5, 'Rolling_GA': 1.5, 'Points_Pace': 50,
        'xG_Form': float(static_features.loc[t, 'Home_npxG'])
                   if t in static_features.index else 1.5
    } for t in teams}

    all_rows, all_keys = [], []

    for _, match in fixtures.iterrows():
        home = match['home_team']
        away = match['away_team']
        mw   = match['matchweek']

        if home not in static_features.index or away not in static_features.index:
            continue

        hs  = static_features.loc[home]
        as_ = static_features.loc[away]
        h   = init_dyn[home]
        a   = init_dyn[away]

        all_rows.append({
            'Home_Form': h['Form'], 'Home_Rank': h['Rank'],
            'Home_Streak': h['Streak'], 'Home_Goal_Diff': h['Goal_Diff'],
            'Home_Rolling_GF': h['Rolling_GF'], 'Home_Rolling_GA': h['Rolling_GA'],
            'Home_Points_Pace': h['Points_Pace'], 'Home_Match_Number': mw,
            'Away_Form': a['Form'], 'Away_Rank': a['Rank'],
            'Away_Streak': a['Streak'], 'Away_Goal_Diff': a['Goal_Diff'],
            'Away_Rolling_GF': a['Rolling_GF'], 'Away_Rolling_GA': a['Rolling_GA'],
            'Away_Points_Pace': a['Points_Pace'], 'Away_Match_Number': mw,
            'Home_Squad_Value': hs['Home_Squad_Value'],
            'Home_Squad_Value_Mean': hs['Home_Squad_Value_Mean'],
            'Home_Squad_Size': hs['Home_Squad_Size'],
            'Away_Squad_Value': as_['Away_Squad_Value'],
            'Away_Squad_Value_Mean': as_['Away_Squad_Value_Mean'],
            'Away_Squad_Size': as_['Away_Squad_Size'],
            'Squad_Value_Delta': hs['Home_Squad_Value'] - as_['Away_Squad_Value'],
            'Home_npxG': hs['Home_npxG'], 'Away_npxG': as_['Away_npxG'],
            'Home_xPoints': hs['Home_xPoints'], 'Away_xPoints': as_['Away_xPoints'],
            'Home_PPDA': hs['Home_PPDA'], 'Away_PPDA': as_['Away_PPDA'],
            'Home_Deep': hs['Home_Deep'], 'Away_Deep': as_['Away_Deep'],
            'Home_xG_Form': h['xG_Form'], 'Away_xG_Form': a['xG_Form'],
        })
        all_keys.append((home, away))

    # Un seul appel au modèle
    X      = pd.DataFrame(all_rows)[FEATURE_NAMES]
    X_lr   = model['scaler'].transform(X)
    p_gb   = model['gb'].predict_proba(X)
    p_rf   = model['rf'].predict_proba(X)
    p_lr   = model['lr'].predict_proba(X_lr)
    meta   = model['meta'].predict_proba(np.hstack([p_gb, p_rf, p_lr]))
    # classes : A=0, D=1, H=2

    proba_cache = {}
    for i, key in enumerate(all_keys):
        proba_cache[key] = (float(meta[i, 2]),   # prob_H
                            float(meta[i, 1]),   # prob_D
                            float(meta[i, 0]))   # prob_A

    # Lambdas Poisson via optimize
    def find_lambdas(pH, pD, pA, max_g=10):
        def loss(lmb):
            if lmb[0] <= 0 or lmb[1] <= 0:
                return 1e9
            ph = pd_ = pa = 0.0
            for i in range(max_g + 1):
                pi = poisson.pmf(i, lmb[0])
                for j in range(max_g + 1):
                    p  = pi * poisson.pmf(j, lmb[1])
                    if i > j: ph  += p
                    elif i == j: pd_ += p
                    else: pa += p
            return (ph - pH)**2 + (pd_ - pD)**2 + (pa - pA)**2

        res = minimize(loss, [1.5 * pH / 0.45, 1.2 * pA / 0.30],
                       method='Nelder-Mead',
                       options={'xatol': 1e-5, 'fatol': 1e-7, 'maxiter': 5000})
        return float(res.x[0]), float(res.x[1])

    lambda_cache = {}
    for key, (pH, pD, pA) in proba_cache.items():
        lh, la = find_lambdas(pH, pD, pA)
        lambda_cache[key] = (lh, la)

    return proba_cache, lambda_cache


# ── Simulation Monte Carlo ────────────────────────────────────────────────────

def run_monte_carlo(fixtures_df, proba_cache, lambda_cache,
                    played_df=None, n_simulations=10000,
                    progress_callback=None):
    """
    Simulation Monte Carlo vectorisée.
    progress_callback(done, total, partial_results) — appelé tous les 500 sims
    Retourne DataFrame : team, prob_title, prob_top4, prob_releg, avg_points
    """
    teams = sorted(set(fixtures_df['home_team']) | set(fixtures_df['away_team']))

    def init_stats():
        return {t: {'points': 0, 'played': 0, 'gf': 0, 'ga': 0,
                    'Goal_Diff': 0} for t in teams}

    def update(ts, home, away, result, sh, sa):
        for team, is_home in [(home, True), (away, False)]:
            s  = ts[team]
            s['played'] += 1
            gf = sh if is_home else sa
            ga = sa if is_home else sh
            s['gf']        += gf
            s['ga']        += ga
            s['Goal_Diff']  = s['gf'] - s['ga']
            if (is_home and result == 'H') or (not is_home and result == 'A'):
                s['points'] += 3
            elif result == 'D':
                s['points'] += 1

    # Matchs restants
    played_set = set()
    if played_df is not None and len(played_df) > 0:
        for _, r in played_df.iterrows():
            played_set.add((r['home_team'], r['away_team']))

    remaining = fixtures_df[~fixtures_df.apply(
        lambda r: (r['home_team'], r['away_team']) in played_set, axis=1
    )].reset_index(drop=True)

    rem_home   = remaining['home_team'].values
    rem_away   = remaining['away_team'].values
    n_rem      = len(remaining)

    prob_H_arr = np.array([proba_cache.get((h, a), (0.45, 0.25, 0.30))[0]
                           for h, a in zip(rem_home, rem_away)])
    prob_D_arr = np.array([proba_cache.get((h, a), (0.45, 0.25, 0.30))[1]
                           for h, a in zip(rem_home, rem_away)])
    lh_arr     = np.array([lambda_cache.get((h, a), (1.5, 1.2))[0]
                           for h, a in zip(rem_home, rem_away)])
    la_arr     = np.array([lambda_cache.get((h, a), (1.5, 1.2))[1]
                           for h, a in zip(rem_home, rem_away)])

    top4_count  = {t: 0 for t in teams}
    title_count = {t: 0 for t in teams}
    releg_count = {t: 0 for t in teams}
    pts_sum     = {t: 0 for t in teams}

    BATCH = 500  # callback tous les 500 sims

    for sim in range(n_simulations):
        ts = init_stats()

        if played_df is not None and len(played_df) > 0:
            for _, r in played_df.iterrows():
                update(ts, r['home_team'], r['away_team'],
                       r['result'], r['score_h'], r['score_a'])

        rands   = np.random.random(n_rem)
        results = np.where(rands < prob_H_arr, 'H',
                  np.where(rands < prob_H_arr + prob_D_arr, 'D', 'A'))
        sh_arr  = np.random.poisson(lh_arr)
        sa_arr  = np.random.poisson(la_arr)

        for i in range(n_rem):
            r  = results[i]
            sh = int(sh_arr[i])
            sa = int(sa_arr[i])
            if r == 'H' and sh <= sa: sh = sa + 1
            elif r == 'A' and sa <= sh: sa = sh + 1
            elif r == 'D': sa = sh
            update(ts, rem_home[i], rem_away[i], r, sh, sa)

        final = sorted(teams,
                       key=lambda t: (ts[t]['points'], ts[t]['Goal_Diff'], ts[t]['gf']),
                       reverse=True)

        for i, t in enumerate(final):
            pos = i + 1
            pts_sum[t] += ts[t]['points']
            if pos == 1:  title_count[t] += 1
            if pos <= 4:  top4_count[t]  += 1
            if pos >= 18: releg_count[t] += 1

        # Callback progression
        if progress_callback and (sim + 1) % BATCH == 0:
            partial = _build_results(teams, title_count, top4_count,
                                     releg_count, pts_sum, sim + 1)
            progress_callback(sim + 1, n_simulations, partial)

    return _build_results(teams, title_count, top4_count,
                          releg_count, pts_sum, n_simulations)


def _build_results(teams, title_count, top4_count, releg_count, pts_sum, n):
    rows = []
    for t in teams:
        rows.append({
            'team'       : t,
            'prob_title' : round(title_count[t] / n * 100, 1),
            'prob_top4'  : round(top4_count[t]  / n * 100, 1),
            'prob_releg' : round(releg_count[t]  / n * 100, 1),
            'avg_points' : round(pts_sum[t]       / n, 1),
        })
    return (pd.DataFrame(rows)
              .sort_values('prob_top4', ascending=False)
              .reset_index(drop=True))


# ── Données P300 ──────────────────────────────────────────────────────────────

def get_matchday_fixtures(matchday):
    """
    Retourner les matchs d'une journée avec prédictions et résultats réels.
    """
    import pickle

    fixtures  = pd.read_csv(FIXTURES_FILE)
    played_df = load_played_results()
    mw_df     = fixtures[fixtures['matchweek'] == matchday].copy()

    # Charger les caches
    with open(PROBA_CACHE_FILE, 'rb') as f:
        proba_cache = pickle.load(f)
    with open(LAMBDA_CACHE_FILE, 'rb') as f:
        lambda_cache = pickle.load(f)

    # Résultats réels indexés
    played_index = {}
    if len(played_df) > 0:
        for _, r in played_df.iterrows():
            played_index[(r['home_team'], r['away_team'])] = r

    results = []
    for _, match in mw_df.iterrows():
        home = match['home_team']
        away = match['away_team']
        key  = (home, away)

        # Probas stacking
        pH, pD, pA = proba_cache.get(key, (0.45, 0.25, 0.30))
        pred_result = 'H' if pH > pD and pH > pA else ('D' if pD > pA else 'A')

        # Score prédit via Poisson
        lh, la  = lambda_cache.get(key, (1.5, 1.2))
        pred_sh, pred_sa = _most_likely_score(lh, la)

        # Résultat réel
        real = played_index.get(key)
        real_sh    = int(real['score_h'])  if real is not None else None
        real_sa    = int(real['score_a'])  if real is not None else None
        real_result = real['result']       if real is not None else None
        played      = real is not None

        # Prédiction correcte ?
        correct = (real_result == pred_result) if played else None

        results.append({
            'home'       : home,
            'away'       : away,
            'date'       : match['date'],
            'kickoff'    : match.get('kickoff_time_uk', ''),
            'prob_H'     : round(pH, 3),
            'prob_D'     : round(pD, 3),
            'prob_A'     : round(pA, 3),
            'pred_result': pred_result,
            'pred_sh'    : pred_sh,
            'pred_sa'    : pred_sa,
            'played'     : played,
            'real_sh'    : real_sh,
            'real_sa'    : real_sa,
            'real_result': real_result,
            'correct'    : correct,
        })

    return results


def _most_likely_score(lh, la, max_goals=6):
    """Score le plus probable selon les lambdas Poisson"""
    from scipy.stats import poisson
    best_p = -1
    best   = (1, 0)
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = poisson.pmf(i, lh) * poisson.pmf(j, la)
            if p > best_p:
                best_p = p
                best   = (i, j)
    return best


def get_matchday_stats(matchday_results):
    """Stats de précision pour une journée donnée"""
    played   = [r for r in matchday_results if r['played']]
    if not played:
        return None
    correct  = sum(1 for r in played if r['correct'])
    return {
        'played'   : len(played),
        'total'    : len(matchday_results),
        'correct'  : correct,
        'accuracy' : round(correct / len(played) * 100, 1) if played else 0,
    }


def get_current_matchday(played_df, fixtures_df):
    """
    Retourner la journée en cours :
    - Si des matchs sont joués : la première journée avec des matchs non joués
    - Sinon : journée 1
    """
    if len(played_df) == 0:
        return 1

    played_set = set(zip(played_df['home_team'], played_df['away_team']))
    for mw in sorted(fixtures_df['matchweek'].unique()):
        mw_matches = fixtures_df[fixtures_df['matchweek'] == mw]
        unplayed   = [(r['home_team'], r['away_team'])
                      for _, r in mw_matches.iterrows()
                      if (r['home_team'], r['away_team']) not in played_set]
        if unplayed:
            return int(mw)

    return int(fixtures_df['matchweek'].max())


# ── Mise à jour depuis GitHub ──────────────────────────────────────────────────

GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/openfootball/england"
    "/master/2026-27/1-premierleague.txt"
)


def fetch_and_update_results():
    """
    Télécharger le fichier depuis GitHub, le sauvegarder localement,
    et retourner (n_nouveaux, n_total, message).
    """
    import urllib.request

    # Charger les résultats actuels
    old_results = load_played_results()
    old_set     = set()
    if len(old_results) > 0:
        old_set = set(zip(old_results['home_team'], old_results['away_team']))

    # Télécharger le fichier
    try:
        with urllib.request.urlopen(GITHUB_RAW_URL, timeout=15) as r:
            content = r.read().decode('utf-8')
    except Exception as e:
        return 0, len(old_results), f"Erreur de téléchargement : {e}"

    # Sauvegarder localement
    ENGLAND_MASTER.parent.mkdir(parents=True, exist_ok=True)
    ENGLAND_MASTER.write_text(content, encoding='utf-8')

    # Parser les nouveaux résultats
    new_results = load_played_results()
    new_set     = set(zip(new_results['home_team'], new_results['away_team']))

    n_nouveaux = len(new_set - old_set)
    n_total    = len(new_results)

    return n_nouveaux, n_total, "OK"
