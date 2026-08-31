"""
P100 — Accueil
Historique Premier League — champion, classement, top 6, stats clés, palmarès
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.historical_data import (
    load_historical_data,
    get_available_seasons,
    get_season_standings,
    get_season_top6_evolution,
    get_season_stats,
    build_animated_top6,
    get_titles_ranking,
)

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="P100 — Accueil",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_file = Path(__file__).parent.parent / "assets" / "style.css"
if css_file.exists():
    st.markdown(f"<style>{css_file.read_text()}</style>", unsafe_allow_html=True)

# ── Constantes ────────────────────────────────────────────────────────────────
ZONE_COLORS = {
    "ucl":        "#00C46A",
    "europa":     "#FFB100",
    "relegation": "#FF3B5C",
}

LOGOS = {
    "Arsenal":               "https://resources.premierleague.com/premierleague/badges/100/t3.png",
    "Aston Villa":           "https://resources.premierleague.com/premierleague/badges/100/t7.png",
    "Chelsea":               "https://resources.premierleague.com/premierleague/badges/100/t8.png",
    "Liverpool":             "https://resources.premierleague.com/premierleague/badges/100/t14.png",
    "Man City":              "https://resources.premierleague.com/premierleague/badges/100/t43.png",
    "Man United":            "https://resources.premierleague.com/premierleague/badges/100/t1.png",
    "Newcastle":             "https://resources.premierleague.com/premierleague/badges/100/t4.png",
    "Newcastle United":      "https://resources.premierleague.com/premierleague/badges/100/t4.png",
    "Tottenham":             "https://resources.premierleague.com/premierleague/badges/100/t6.png",
    "Brighton":              "https://resources.premierleague.com/premierleague/badges/100/t36.png",
    "Brighton & Hove Albion":"https://resources.premierleague.com/premierleague/badges/100/t36.png",
    "Everton":               "https://resources.premierleague.com/premierleague/badges/100/t11.png",
    "Fulham":                "https://resources.premierleague.com/premierleague/badges/100/t54.png",
    "Leicester":             "https://resources.premierleague.com/premierleague/badges/100/t13.png",
    "Leicester City":        "https://resources.premierleague.com/premierleague/badges/100/t13.png",
    "West Ham":              "https://resources.premierleague.com/premierleague/badges/100/t21.png",
    "West Ham United":       "https://resources.premierleague.com/premierleague/badges/100/t21.png",
    "Wolves":                "https://resources.premierleague.com/premierleague/badges/100/t39.png",
    "Wolverhampton Wanderers":"https://resources.premierleague.com/premierleague/badges/100/t39.png",
    "Brentford":             "https://resources.premierleague.com/premierleague/badges/100/t94.png",
    "Crystal Palace":        "https://resources.premierleague.com/premierleague/badges/100/t31.png",
    "Bournemouth":           "https://resources.premierleague.com/premierleague/badges/100/t91.png",
    "Nottm Forest":          "https://resources.premierleague.com/premierleague/badges/100/t17.png",
    "Nott'm Forest":         "https://resources.premierleague.com/premierleague/badges/100/t17.png",
    "Nottingham Forest":     "https://resources.premierleague.com/premierleague/badges/100/t17.png",
    "Southampton":           "https://resources.premierleague.com/premierleague/badges/100/t20.png",
    "Leeds":                 "https://resources.premierleague.com/premierleague/badges/100/t2.png",
    "Leeds United":          "https://resources.premierleague.com/premierleague/badges/100/t2.png",
    "Ipswich":               "https://resources.premierleague.com/premierleague/badges/100/t40.png",
    "Blackburn":             "https://resources.premierleague.com/premierleague/badges/100/t90.png",
    "Sunderland":            "https://resources.premierleague.com/premierleague/badges/100/t56.png",
    "Burnley":               "https://resources.premierleague.com/premierleague/badges/100/t90.png",
}
FALLBACK = "https://resources.premierleague.com/premierleague/photos/players/110x140/Photo-Missing.png"

BG_MAIN   = "#0B0E14"
BG_PANEL  = "#12182A"
C_TEXT    = "#E8E8E8"
C_DIM     = "#9BA4C0"
C_INK     = "#0B0E14"
C_BRAND   = "#2FD9E0"
C_SUCCESS = "#00C46A"
C_WARNING = "#FFB100"
C_DANGER  = "#FF3B5C"
BORDER_DIM = "rgba(139,146,168,0.15)"

# ── Cache ─────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Chargement des données historiques...")
def _load():
    return load_historical_data()


# ── Helpers ───────────────────────────────────────────────────────────────────
def logo(team):
    return LOGOS.get(team, FALLBACK)


def H(html):
    """Rendu HTML via st.html() — Streamlit 1.36+, pas de sanitisation"""
    st.html(html)


def zone_dot(pos):
    if pos <= 4:    c = C_SUCCESS
    elif pos == 5:  c = C_WARNING
    elif pos >= 18: c = C_DANGER
    else:           c = "transparent"
    return f'<span style="background:{c};width:8px;height:8px;border-radius:2px;display:inline-block;margin-right:8px;vertical-align:middle;"></span>'


def section_title(text):
    H(f'<div style="font-family:Big Shoulders Display,sans-serif;font-size:1.6rem;font-weight:800;color:{C_BRAND};text-transform:uppercase;letter-spacing:-0.01em;margin-bottom:1rem;">{text}</div>')


def divider():
    H(f'<hr style="border:none;border-top:1px solid rgba(139,146,168,0.15);margin:1.5rem 0;">')


# ── Section 1 : Bandeau Champion ─────────────────────────────────────────────
def render_champion(df, season):
    s = get_season_standings(df, season)
    if s.empty:
        return
    champ = s.iloc[0]
    H(f"""
    <div style="background:linear-gradient(135deg,{BG_PANEL} 0%,#1A2340 100%);
                border:2px solid {C_SUCCESS};border-radius:8px;
                padding:2.5rem 2rem;text-align:center;margin-bottom:0.5rem;
                position:relative;overflow:hidden;">
        <img src="{logo(champ['team'])}"
             style="width:96px;height:96px;object-fit:contain;margin-bottom:1rem;
                    filter:drop-shadow(0 4px 16px rgba(0,196,106,0.4));">
        <div style="font-family:Big Shoulders Display,sans-serif;font-size:2.8rem;
                    font-weight:900;color:{C_SUCCESS};letter-spacing:-0.02em;">
            {champ['team']}
        </div>
        <div style="font-family:IBM Plex Sans,sans-serif;font-size:1rem;
                    color:{C_DIM};margin-top:0.4rem;">
            Champion &mdash; Saison {season} &mdash; {champ['points']} pts
            &nbsp;|&nbsp; {champ['won']}V {champ['drawn']}N {champ['lost']}D
            &nbsp;|&nbsp; {champ['gf']} buts
        </div>
    </div>
    """)


# ── Section 2 : Classement + Stats côte à côte ───────────────────────────────
def render_standings_and_stats(df, season):
    standings = get_season_standings(df, season)
    stats     = get_season_stats(df, season)

    col_table, col_stats = st.columns([3, 1], gap="large")

    with col_table:
        if standings.empty:
            st.warning("Aucune donnée pour cette saison.")
        else:
            rows = ""
            for _, r in standings.iterrows():
                gd = f"+{r['gd']}" if r['gd'] > 0 else str(r['gd'])
                rows += f"""
                <tr style="border-bottom:1px solid rgba(139,146,168,0.08);">
                  <td style="padding:0.55rem 0.5rem;text-align:center;color:{C_DIM};
                             font-family:IBM Plex Mono,monospace;">{r['pos']}</td>
                  <td style="padding:0.55rem 0.5rem;font-family:IBM Plex Sans,sans-serif;">
                    {zone_dot(r['pos'])}{r['team']}</td>
                  <td style="padding:0.55rem 0.5rem;text-align:center;font-family:IBM Plex Mono,monospace;">{r['played']}</td>
                  <td style="padding:0.55rem 0.5rem;text-align:center;font-family:IBM Plex Mono,monospace;">{r['won']}</td>
                  <td style="padding:0.55rem 0.5rem;text-align:center;font-family:IBM Plex Mono,monospace;">{r['drawn']}</td>
                  <td style="padding:0.55rem 0.5rem;text-align:center;font-family:IBM Plex Mono,monospace;">{r['lost']}</td>
                  <td style="padding:0.55rem 0.5rem;text-align:center;font-family:IBM Plex Mono,monospace;">{r['gf']}</td>
                  <td style="padding:0.55rem 0.5rem;text-align:center;font-family:IBM Plex Mono,monospace;">{r['ga']}</td>
                  <td style="padding:0.55rem 0.5rem;text-align:center;color:{C_DIM};font-family:IBM Plex Mono,monospace;">{gd}</td>
                  <td style="padding:0.55rem 0.5rem;text-align:center;font-weight:700;
                             font-family:IBM Plex Mono,monospace;color:{C_BRAND};">{r['points']}</td>
                </tr>"""

            H(f"""
            <table style="width:100%;border-collapse:collapse;
                          background:{BG_PANEL};border-radius:8px;overflow:hidden;
                          color:{C_TEXT};">
              <thead>
                <tr style="border-bottom:2px solid {C_BRAND};background:rgba(47,217,224,0.05);">
                  <th style="padding:0.6rem 0.5rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                             font-size:0.8rem;color:{C_DIM};font-weight:600;">#</th>
                  <th style="padding:0.6rem 0.5rem;text-align:left;font-family:IBM Plex Sans,sans-serif;
                             font-size:0.8rem;color:{C_DIM};font-weight:600;">Equipe</th>
                  <th style="padding:0.6rem 0.5rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                             font-size:0.8rem;color:{C_DIM};font-weight:600;">J</th>
                  <th style="padding:0.6rem 0.5rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                             font-size:0.8rem;color:{C_DIM};font-weight:600;">V</th>
                  <th style="padding:0.6rem 0.5rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                             font-size:0.8rem;color:{C_DIM};font-weight:600;">N</th>
                  <th style="padding:0.6rem 0.5rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                             font-size:0.8rem;color:{C_DIM};font-weight:600;">D</th>
                  <th style="padding:0.6rem 0.5rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                             font-size:0.8rem;color:{C_DIM};font-weight:600;">BP</th>
                  <th style="padding:0.6rem 0.5rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                             font-size:0.8rem;color:{C_DIM};font-weight:600;">BC</th>
                  <th style="padding:0.6rem 0.5rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                             font-size:0.8rem;color:{C_DIM};font-weight:600;">+/-</th>
                  <th style="padding:0.6rem 0.5rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                             font-size:0.8rem;color:{C_DIM};font-weight:600;">Pts</th>
                </tr>
              </thead>
              <tbody>{rows}</tbody>
            </table>
            <div style="margin-top:0.8rem;font-family:IBM Plex Sans,sans-serif;
                        font-size:0.78rem;color:{C_DIM};display:flex;flex-wrap:wrap;gap:12px;">
              <span><span style="background:{C_SUCCESS};width:8px;height:8px;border-radius:2px;
                    display:inline-block;margin-right:5px;vertical-align:middle;"></span>Top 4 — LDC</span>
              <span><span style="background:{C_WARNING};width:8px;height:8px;border-radius:2px;
                    display:inline-block;margin-right:5px;vertical-align:middle;"></span>5e — Europa</span>
              <span><span style="background:{C_DANGER};width:8px;height:8px;border-radius:2px;
                    display:inline-block;margin-right:5px;vertical-align:middle;"></span>18e-20e — Relégation</span>
            </div>
            """)

    with col_stats:
        if not stats:
            return

        scorer = stats["top_scorer"]
        if scorer["goals"] is not None:
            scorer_detail  = f"{scorer['goals']} buts"
            scorer_note    = "<br><small style='color:#FF3B5C;'>* données incomplètes</small>"
        else:
            scorer_detail  = "Non disponible"
            scorer_note    = ""

        blocks = [
            ("Meilleure Attaque",  stats["best_attack"]["team"],
             f"{stats['best_attack']['goals']} buts &middot; {stats['best_attack']['per_match']}/match", C_SUCCESS),
            ("Pire Attaque",       stats["worst_attack"]["team"],
             f"{stats['worst_attack']['goals']} buts &middot; {stats['worst_attack']['per_match']}/match", C_DANGER),
            ("Meilleure Défense",  stats["best_defense"]["team"],
             f"{stats['best_defense']['goals']} enc. &middot; {stats['best_defense']['per_match']}/match", C_SUCCESS),
            ("Pire Défense",       stats["worst_defense"]["team"],
             f"{stats['worst_defense']['goals']} enc. &middot; {stats['worst_defense']['per_match']}/match", C_DANGER),
            ("Clean Sheets",       stats["best_clean_sheets"]["team"],
             f"{stats['best_clean_sheets']['count']} clean sheets", C_BRAND),
            ("Meilleure Série",    stats["best_win_streak"]["team"],
             f"{stats['best_win_streak']['games']} victoires consécutives", C_WARNING),
            ("Meilleur Buteur",    scorer["name"],
             scorer_detail + scorer_note, C_BRAND),
        ]

        cards_html = ""
        for label, team_name, detail, accent in blocks:
            cards_html += f"""
            <div style="background:{BG_PANEL};border:1px solid rgba(139,146,168,0.15);
                        border-left:3px solid {accent};border-radius:6px;
                        padding:0.75rem 0.9rem;margin-bottom:0.6rem;">
              <div style="font-family:IBM Plex Sans,sans-serif;font-size:0.68rem;
                          color:{C_DIM};text-transform:uppercase;
                          letter-spacing:0.07em;margin-bottom:0.35rem;">{label}</div>
              <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.25rem;">
                <img src="{logo(team_name)}"
                     style="width:24px;height:24px;object-fit:contain;">
                <span style="font-family:IBM Plex Sans,sans-serif;font-weight:600;
                             font-size:0.85rem;color:{C_TEXT};">{team_name}</span>
              </div>
              <div style="font-family:IBM Plex Mono,monospace;font-size:0.76rem;
                          color:{accent};">{detail}</div>
            </div>"""

        H(cards_html)


# ── Section 3 : Graphique animé top 6 ────────────────────────────────────────
def render_top6(df, season):
    evo = get_season_top6_evolution(df, season)
    if evo.empty:
        st.info("Données d'évolution non disponibles pour cette saison.")
        return
    fig = build_animated_top6(evo, season)
    st.plotly_chart(fig, use_container_width=True)


# ── Section 4 : Palmarès ──────────────────────────────────────────────────────
def render_palmares(df):
    titles_df  = get_titles_ranking(df)
    if titles_df.empty:
        return

    max_titles = int(titles_df["titles"].max())
    medals     = {0: ("#FFD700", "1er"), 1: ("#C0C0C0", "2e"), 2: ("#CD7F32", "3e")}

    cards_html = '<div style="display:flex;flex-wrap:wrap;gap:0.9rem;align-items:flex-end;">'

    for i, row in titles_df.iterrows():
        team_name = row["team"]
        n         = int(row["titles"])
        bar_pct   = int(n / max_titles * 100)
        accent, rank_lbl = medals.get(i, (C_DIM, f"{i+1}e"))

        # Points trophées
        dots = "".join(
            f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
            f'background:{accent if j < n else "rgba(139,146,168,0.2)"};margin:1px;"></span>'
            for j in range(max_titles)
        )

        # Hauteur de carte proportionnelle au nombre de titres
        card_height = 140 + int(n / max_titles * 80)

        cards_html += f"""
        <div style="background:{BG_PANEL};
                    border:1px solid rgba(139,146,168,0.15);
                    border-top:3px solid {accent};
                    border-radius:8px;padding:1rem 0.9rem;
                    display:flex;flex-direction:column;align-items:center;
                    gap:0.4rem;min-width:120px;flex:1;
                    min-height:{card_height}px;justify-content:flex-end;">
          <div style="font-family:IBM Plex Mono,monospace;font-size:0.7rem;
                      color:{accent};font-weight:700;letter-spacing:0.05em;">{rank_lbl}</div>
          <img src="{logo(team_name)}"
               style="width:48px;height:48px;object-fit:contain;
                      filter:drop-shadow(0 2px 8px rgba(0,0,0,0.5));">
          <div style="font-family:IBM Plex Sans,sans-serif;font-weight:700;
                      font-size:0.85rem;color:{C_TEXT};text-align:center;
                      line-height:1.2;">{team_name}</div>
          <div style="font-family:Big Shoulders Display,sans-serif;font-size:2.2rem;
                      font-weight:900;color:{accent};line-height:1;">{n}</div>
          <div style="font-family:IBM Plex Sans,sans-serif;font-size:0.7rem;
                      color:{C_DIM};">titre{"s" if n > 1 else ""}</div>
          <div style="margin-top:0.2rem;">{dots}</div>
          <div style="width:100%;background:rgba(139,146,168,0.1);
                      border-radius:4px;height:3px;margin-top:0.3rem;overflow:hidden;">
            <div style="width:{bar_pct}%;height:100%;
                        background:{accent};border-radius:4px;"></div>
          </div>
        </div>"""

    cards_html += "</div>"
    cards_html += f"""
    <div style="margin-top:0.9rem;font-family:IBM Plex Sans,sans-serif;
                font-size:0.78rem;color:{C_DIM};">
        Saisons 2000/01 &rarr; 2025/26 &nbsp;&middot;&nbsp; 24 saisons &nbsp;&middot;&nbsp;
        Les titres avant 2000/01 ne sont pas comptabilisés
    </div>"""

    H(cards_html)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    df = _load()

    H(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.85rem;'
      f'color:{C_DIM};letter-spacing:0.12em;margin-bottom:0.5rem;">P100 — ACCUEIL</div>')

    seasons  = get_available_seasons()
    selected = st.selectbox(
        "Saison",
        options=seasons,
        index=len(seasons) - 1,
        key="season_select",
        label_visibility="collapsed",
    )

    divider()
    render_champion(df, selected)
    divider()

    section_title("Classement Final")
    render_standings_and_stats(df, selected)
    divider()

    section_title("Fluctuation Top 6")
    render_top6(df, selected)
    divider()

    section_title("Palmarès — Titres PL depuis 2000/01")
    render_palmares(df)


if __name__ == "__main__":
    main()
