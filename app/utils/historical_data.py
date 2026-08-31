"""
Données historiques Premier League — 2000/01 à 2025/26
Toutes les fonctions ont été validées dans notebooks/08_experimentation_app.ipynb
"""
import re
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import PROJECT_ROOT

# Chemins
PL_ALL_SEASONS = PROJECT_ROOT / 'data' / 'raw' / 'pl_all_seasons.csv'
ENGLAND_MASTER  = PROJECT_ROOT / 'data' / 'raw' / 'england-master'

# Saisons ayant les buteurs dans england-master
SEASONS_WITH_SCORERS = {'2025/26', '2026/27'}


# ── Chargement ────────────────────────────────────────────────────────────────

def _fix_season(raw):
    """Corrige les clés de saison mal encodées vers le format YYYY/YY"""
    s  = str(int(raw)).zfill(4)
    y1 = int(s[:2])
    y2 = s[2:]
    if y1 == 0:
        return f"200{s[1]}/{y2}"
    elif 1 <= y1 <= 29:
        return f"20{s[:2]}/{y2}"
    elif y1 >= 93:
        return f"19{s[:2]}/{y2}"
    return f"UNKNOWN_{s}"


def load_historical_data():
    """
    Charge pl_all_seasons.csv, corrige les saisons et les dates.
    Retourne uniquement les saisons 2000/01 → 2025/26.
    """
    df = pd.read_csv(PL_ALL_SEASONS, low_memory=False)

    # Corriger les clés de saison
    df['Season_display'] = df['Season'].apply(_fix_season)

    # Parser les dates (format mixte %d/%m/%Y et %d/%m/%y)
    dates = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
    mask  = dates.isna()
    dates[mask] = pd.to_datetime(
        df.loc[mask, 'Date'], format='%d/%m/%y', errors='coerce'
    )
    df['Date'] = dates

    # Filtrer 2000/01 → 2025/26
    df = df[df['Season_display'].str.startswith('20')].copy()

    # Supprimer les lignes sans match
    df = df.dropna(subset=['Date', 'HomeTeam', 'AwayTeam']).reset_index(drop=True)

    return df


def get_available_seasons():
    """Liste des saisons disponibles triées chronologiquement"""
    df = load_historical_data()
    return sorted(df['Season_display'].unique(), key=lambda x: int(x[:4]))


# ── Journées ──────────────────────────────────────────────────────────────────

def assign_matchweek(df, season_display):
    """
    Assigne le numéro de journée correct (1-38) basé sur
    le rang du match de chaque équipe (tri par date).
    """
    s = df[df['Season_display'] == season_display].copy()
    s = s.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)

    team_count = {}
    matchweeks = []

    for _, row in s.iterrows():
        h = row['HomeTeam']
        a = row['AwayTeam']
        team_count[h] = team_count.get(h, 0) + 1
        team_count[a] = team_count.get(a, 0) + 1
        matchweeks.append(max(team_count[h], team_count[a]))

    s['matchweek'] = matchweeks
    return s


# ── Classement ────────────────────────────────────────────────────────────────

def get_season_standings(df, season_display):
    """
    Classement final d'une saison.
    Retourne un DataFrame trié : pos, team, played, won, drawn, lost,
    gf, ga, gd, points
    """
    s = df[df['Season_display'] == season_display].copy()
    if s.empty:
        return pd.DataFrame()

    teams = sorted(set(s['HomeTeam'].dropna()) | set(s['AwayTeam'].dropna()))
    rows  = []

    for team in teams:
        hm = s[s['HomeTeam'] == team]
        am = s[s['AwayTeam'] == team]
        w  = len(hm[hm['FTR'] == 'H']) + len(am[am['FTR'] == 'A'])
        d  = len(hm[hm['FTR'] == 'D']) + len(am[am['FTR'] == 'D'])
        l  = len(hm[hm['FTR'] == 'A']) + len(am[am['FTR'] == 'H'])
        gf = int(hm['FTHG'].sum() + am['FTAG'].sum())
        ga = int(hm['FTAG'].sum() + am['FTHG'].sum())
        rows.append(dict(team=team, played=w+d+l, won=w, drawn=d, lost=l,
                         gf=gf, ga=ga, gd=gf-ga, points=w*3+d))

    out = (pd.DataFrame(rows)
             .sort_values(['points', 'gd', 'gf'], ascending=False)
             .reset_index(drop=True))
    out.insert(0, 'pos', range(1, len(out) + 1))
    return out


# ── Top 6 évolution ───────────────────────────────────────────────────────────

def get_season_top6_evolution(df, season_display):
    """
    Points cumulés du top 6 final, journée par journée (J1-J38).
    Retourne un DataFrame : [matchweek, team, pts]
    """
    final = get_season_standings(df, season_display)
    if final.empty:
        return pd.DataFrame()

    top6 = final.head(6)['team'].tolist()
    s    = assign_matchweek(df, season_display)

    pts  = {t: 0 for t in top6}
    rows = []

    for mw, grp in s.groupby('matchweek'):
        for _, match in grp.iterrows():
            h, a, r = match['HomeTeam'], match['AwayTeam'], match['FTR']
            if h in pts:
                pts[h] += 3 if r == 'H' else (1 if r == 'D' else 0)
            if a in pts:
                pts[a] += 3 if r == 'A' else (1 if r == 'D' else 0)
        for t in top6:
            rows.append({'matchweek': mw, 'team': t, 'pts': pts[t]})

    return pd.DataFrame(rows)


# ── 5 derniers champions ──────────────────────────────────────────────────────

def get_last_5_champions(df, season_display):
    """
    Retourne les 5 derniers champions avant et incluant la saison donnée.
    Gère le cas où moins de 5 saisons sont disponibles (limite 2000/01).
    """
    FIRST_SEASON = '2000/01'
    available    = get_available_seasons()

    if season_display not in available:
        return [], f"Saison {season_display} non trouvée dans la base."

    idx    = available.index(season_display)
    window = available[max(0, idx - 4) : idx + 1]

    warning = None
    if len(window) < 5:
        warning = f"Données limitées à {FIRST_SEASON} — {len(window)}/5 saisons disponibles."

    results = []
    for season in reversed(window):
        s = get_season_standings(df, season)
        if s.empty:
            continue
        c = s.iloc[0]
        results.append({
            'saison'  : season,
            'champion': c['team'],
            'points'  : c['points'],
            'won'     : c['won'],
            'gf'      : c['gf'],
            'ga'      : c['ga'],
        })

    return results, warning


# ── Stats clés ────────────────────────────────────────────────────────────────

def get_season_stats(df, season_display):
    """
    Stats clés d'une saison :
    - Best Attack  (buts marqués + ratio/match)
    - Best Defense (buts encaissés + ratio/match)
    - Best Clean Sheets
    - Best Win Streak
    - Top Scorer   (uniquement si données disponibles)
    """
    s = df[df['Season_display'] == season_display].copy()
    if s.empty:
        return {}

    standings = get_season_standings(df, season_display)
    if standings.empty:
        return {}

    team_rows = []
    for _, row in standings.iterrows():
        team   = row['team']
        hm     = s[s['HomeTeam'] == team]
        am     = s[s['AwayTeam'] == team]
        played = row['played']
        gf     = row['gf']
        ga     = row['ga']

        # Clean sheets
        cs = len(hm[hm['FTAG'] == 0]) + len(am[am['FTHG'] == 0])

        # Win streak max
        results = []
        for _, m in hm.iterrows():
            results.append((m['Date'], 'W' if m['FTR'] == 'H' else ('D' if m['FTR'] == 'D' else 'L')))
        for _, m in am.iterrows():
            results.append((m['Date'], 'W' if m['FTR'] == 'A' else ('D' if m['FTR'] == 'D' else 'L')))
        results.sort(key=lambda x: x[0])

        max_streak = cur = 0
        for _, r in results:
            if r == 'W':
                cur       += 1
                max_streak = max(max_streak, cur)
            else:
                cur = 0

        team_rows.append({
            'team'        : team,
            'played'      : played,
            'gf'          : gf,
            'ga'          : ga,
            'gf_per_match': round(gf / played, 2) if played else 0,
            'ga_per_match': round(ga / played, 2) if played else 0,
            'clean_sheets': cs,
            'max_streak'  : max_streak,
        })

    tdf = pd.DataFrame(team_rows)

    stats = {
        'best_attack': {
            'team'     : tdf.loc[tdf['gf'].idxmax(), 'team'],
            'goals'    : int(tdf['gf'].max()),
            'per_match': tdf.loc[tdf['gf'].idxmax(), 'gf_per_match'],
        },
        'worst_attack': {
            'team'     : tdf.loc[tdf['gf'].idxmin(), 'team'],
            'goals'    : int(tdf['gf'].min()),
            'per_match': tdf.loc[tdf['gf'].idxmin(), 'gf_per_match'],
        },
        'best_defense': {
            'team'     : tdf.loc[tdf['ga'].idxmin(), 'team'],
            'goals'    : int(tdf['ga'].min()),
            'per_match': tdf.loc[tdf['ga'].idxmin(), 'ga_per_match'],
        },
        'worst_defense': {
            'team'     : tdf.loc[tdf['ga'].idxmax(), 'team'],
            'goals'    : int(tdf['ga'].max()),
            'per_match': tdf.loc[tdf['ga'].idxmax(), 'ga_per_match'],
        },
        'best_clean_sheets': {
            'team' : tdf.loc[tdf['clean_sheets'].idxmax(), 'team'],
            'count': int(tdf['clean_sheets'].max()),
        },
        'best_win_streak': {
            'team' : tdf.loc[tdf['max_streak'].idxmax(), 'team'],
            'games': int(tdf['max_streak'].max()),
        },
        'top_scorer': get_top_scorer(season_display),
    }

    return stats


# ── Meilleur buteur ───────────────────────────────────────────────────────────

def get_top_scorer(season_display):
    """
    Retourne le meilleur buteur d'une saison.
    Données disponibles uniquement pour 2025/26 et 2026/27.
    """
    if season_display not in SEASONS_WITH_SCORERS:
        return {'name': 'Données non disponibles', 'goals': None}

    # Convertir "2025/26" -> "2025-26"
    folder = season_display.replace('/', '-')[:4] + '-' + season_display[-2:]
    txt_file = ENGLAND_MASTER / folder / '1-premierleague.txt'

    if not txt_file.exists():
        return {'name': 'Données non disponibles', 'goals': None}

    content      = txt_file.read_text(encoding='utf-8', errors='ignore')
    goal_pattern = re.compile(r'\(([^)]*\d+\'[^)]*)\)', re.DOTALL)
    scorer_count = {}

    for match in goal_pattern.finditer(content):
        for team_part in match.group(1).split(';'):
            for goal in team_part.split(','):
                goal = goal.strip()
                if not goal or '(og)' in goal:
                    continue
                name = re.sub(r"\s+\d+\+?\d*'.*$", '', goal).strip()
                if name and len(name) > 1:
                    scorer_count[name] = scorer_count.get(name, 0) + 1

    if not scorer_count:
        return {'name': 'Données non disponibles', 'goals': None}

    top_name, top_goals = max(scorer_count.items(), key=lambda x: x[1])
    return {'name': top_name, 'goals': top_goals}


# ── Graphique animé Top 6 ─────────────────────────────────────────────────────

TEAM_COLORS = ['#00C46A', '#2FD9E0', '#FFB100', '#FF3B5C', '#9B59B6', '#E67E22']


def build_animated_top6(evo_df, season_display):
    """
    Graphique Plotly animé avec frames natives (play/pause/slider intégrés).
    Annotations nom d'équipe en bout de courbe sur chaque frame.
    Validé dans notebooks/08_experimentation_app.ipynb
    """
    import plotly.graph_objects as go

    if evo_df.empty:
        return go.Figure()

    teams      = evo_df['team'].unique().tolist()
    matchweeks = sorted(evo_df['matchweek'].unique())
    max_mw     = matchweeks[-1]
    max_pts    = int(evo_df['pts'].max()) + 8

    # ── Traces initiales (frame complète) ────────────────────────────────────
    traces = []
    for i, team in enumerate(teams):
        td = evo_df[evo_df['team'] == team]
        traces.append(go.Scatter(
            x    = td['matchweek'].tolist(),
            y    = td['pts'].tolist(),
            name = team,
            mode = 'lines+markers',
            line = dict(color=TEAM_COLORS[i % len(TEAM_COLORS)], width=2.5),
            marker = dict(size=4, color=TEAM_COLORS[i % len(TEAM_COLORS)]),
            hovertemplate = f'<b>{team}</b><br>J%{{x}} — %{{y}} pts<extra></extra>',
        ))

    def _annotations(mw):
        """Annotations texte en bout de courbe pour une journée donnée"""
        annots = []
        for i, team in enumerate(teams):
            td = evo_df[(evo_df['team'] == team) & (evo_df['matchweek'] <= mw)]
            if td.empty:
                continue
            last_pts = td['pts'].iloc[-1]
            annots.append(dict(
                x         = mw + 0.8,
                y         = last_pts,
                xref      = 'x', yref = 'y',
                text      = f'<b>{team}</b>',
                showarrow = False,
                font      = dict(color=TEAM_COLORS[i % len(TEAM_COLORS)],
                                 size=11, family='IBM Plex Sans'),
                xanchor   = 'left',
                yanchor   = 'middle',
            ))
        return annots

    # ── Frames ───────────────────────────────────────────────────────────────
    frames = []
    for mw in matchweeks:
        frame_data = []
        for team in teams:
            td = evo_df[(evo_df['team'] == team) & (evo_df['matchweek'] <= mw)]
            frame_data.append(go.Scatter(
                x = td['matchweek'].tolist(),
                y = td['pts'].tolist(),
            ))
        frames.append(go.Frame(
            data   = frame_data,
            name   = str(mw),
            layout = go.Layout(annotations=_annotations(mw)),
        ))

    # ── Layout ───────────────────────────────────────────────────────────────
    layout = go.Layout(
        plot_bgcolor  = '#0B0E14',
        paper_bgcolor = '#12182A',
        font          = dict(family='IBM Plex Mono', color='#E8E8E8', size=12),
        xaxis = dict(
            title     = 'Journée',
            range     = [0, max_mw + 10],
            gridcolor = 'rgba(155,164,192,0.1)',
            color     = '#9BA4C0',
            dtick     = 5,
        ),
        yaxis = dict(
            title     = 'Points cumulés',
            range     = [0, max_pts],
            gridcolor = 'rgba(155,164,192,0.1)',
            color     = '#9BA4C0',
        ),
        hovermode   = 'x unified',
        showlegend  = False,
        height      = 520,
        margin      = dict(l=10, r=140, t=60, b=10),
        annotations = _annotations(max_mw),

        updatemenus = [dict(
            type        = 'buttons',
            showactive  = False,
            x=0.0, y=1.15, xanchor='left', yanchor='top',
            buttons = [
                dict(
                    label  = 'Lancer',
                    method = 'animate',
                    args   = [None, dict(
                        frame       = dict(duration=80, redraw=True),
                        fromcurrent = True,
                        transition  = dict(duration=40, easing='linear'),
                        mode        = 'immediate',
                    )],
                ),
                dict(
                    label  = 'Pause',
                    method = 'animate',
                    args   = [[None], dict(
                        frame      = dict(duration=0, redraw=False),
                        mode       = 'immediate',
                        transition = dict(duration=0),
                    )],
                ),
            ],
            bgcolor     = '#12182A',
            bordercolor = '#2FD9E0',
            font        = dict(color='#E8E8E8', family='IBM Plex Sans'),
        )],

        sliders = [dict(
            active       = len(matchweeks) - 1,
            currentvalue = dict(
                prefix  = 'Journée ',
                font    = dict(color='#2FD9E0', family='IBM Plex Mono'),
                visible = True,
                xanchor = 'center',
            ),
            pad   = dict(t=50),
            steps = [
                dict(
                    method = 'animate',
                    label  = str(mw),
                    args   = [[str(mw)], dict(
                        mode       = 'immediate',
                        frame      = dict(duration=0, redraw=True),
                        transition = dict(duration=0),
                    )],
                )
                for mw in matchweeks
            ],
            bgcolor     = '#12182A',
            bordercolor = '#8B92A8',
            tickcolor   = '#8B92A8',
            font        = dict(color='#8B92A8'),
        )],
    )

    return go.Figure(data=traces, layout=layout, frames=frames)


# ── Palmarès ──────────────────────────────────────────────────────────────────

def get_titles_ranking(df):
    """
    Nombre de titres PL remportés par équipe depuis 2000/01.
    Retourne un DataFrame trié : team, titles
    """
    counts = {}
    for season in sorted(df['Season_display'].unique()):
        s = get_season_standings(df, season)
        if s.empty:
            continue
        champ = s.iloc[0]['team']
        counts[champ] = counts.get(champ, 0) + 1

    import pandas as pd
    return (pd.DataFrame(list(counts.items()), columns=['team', 'titles'])
              .sort_values('titles', ascending=False)
              .reset_index(drop=True))
