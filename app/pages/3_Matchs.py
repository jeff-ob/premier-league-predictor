"""
P300 — Prochains Matchs & Prédictions
Journée par journée avec prédictions stacking + score Poisson + résultats réels
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.season_2627 import (
    load_played_results,
    get_matchday_fixtures,
    get_matchday_stats,
    get_current_matchday,
    caches_available,
    fetch_and_update_results,
)
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="P300 — Matchs 2026-27",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_file = Path(__file__).parent.parent / "assets" / "style.css"
if css_file.exists():
    st.markdown(f"<style>{css_file.read_text()}</style>", unsafe_allow_html=True)

# ── Constantes ────────────────────────────────────────────────────────────────
BG_MAIN  = "#0B0E14"
BG_PANEL = "#12182A"
C_TEXT   = "#E8E8E8"
C_DIM    = "#9BA4C0"
C_INK    = "#0B0E14"
C_BRAND  = "#2FD9E0"
C_SUCCESS = "#00C46A"
C_WARNING = "#FFB100"
C_DANGER  = "#FF3B5C"

LOGOS = {
    "Arsenal":               "https://resources.premierleague.com/premierleague/badges/100/t3.png",
    "Aston Villa":           "https://resources.premierleague.com/premierleague/badges/100/t7.png",
    "Chelsea":               "https://resources.premierleague.com/premierleague/badges/100/t8.png",
    "Liverpool":             "https://resources.premierleague.com/premierleague/badges/100/t14.png",
    "Manchester City":       "https://resources.premierleague.com/premierleague/badges/100/t43.png",
    "Manchester United":     "https://resources.premierleague.com/premierleague/badges/100/t1.png",
    "Newcastle United":      "https://resources.premierleague.com/premierleague/badges/100/t4.png",
    "Tottenham Hotspur":     "https://resources.premierleague.com/premierleague/badges/100/t6.png",
    "Brighton & Hove Albion":"https://resources.premierleague.com/premierleague/badges/100/t36.png",
    "Everton":               "https://resources.premierleague.com/premierleague/badges/100/t11.png",
    "Fulham":                "https://resources.premierleague.com/premierleague/badges/100/t54.png",
    "Brentford":             "https://resources.premierleague.com/premierleague/badges/100/t94.png",
    "Crystal Palace":        "https://resources.premierleague.com/premierleague/badges/100/t31.png",
    "AFC Bournemouth":       "https://resources.premierleague.com/premierleague/badges/100/t91.png",
    "Nottingham Forest":     "https://resources.premierleague.com/premierleague/badges/100/t17.png",
    "Leeds United":          "https://resources.premierleague.com/premierleague/badges/100/t2.png",
    "Sunderland":            "https://resources.premierleague.com/premierleague/badges/100/t56.png",
    "Ipswich Town":          "https://resources.premierleague.com/premierleague/badges/100/t40.png",
    "Coventry City":         "https://upload.wikimedia.org/wikipedia/en/8/8a/Coventry_City_FC_logo.png",
    "Hull City":             "https://upload.wikimedia.org/wikipedia/en/5/54/Hull_City_A.F.C._logo.svg",
}
FALLBACK = "https://resources.premierleague.com/premierleague/photos/players/110x140/Photo-Missing.png"


# ── Helpers ───────────────────────────────────────────────────────────────────
def logo(team):
    return LOGOS.get(team, FALLBACK)


def H(html):
    st.html(html)


def divider():
    H('<hr style="border:none;border-top:1px solid rgba(139,146,168,0.15);margin:1rem 0;">')


# ── Cache ─────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_played():
    return load_played_results()


@st.cache_data(show_spinner=False)
def _load_fixtures():
    from config import PROJECT_ROOT
    return pd.read_csv(PROJECT_ROOT / "data" / "raw" / "fixtures.csv")


@st.cache_data(show_spinner="Calcul des prédictions...", ttl=300)
def _get_matchday(matchday):
    return get_matchday_fixtures(matchday)


# ── Rendu d'un match ──────────────────────────────────────────────────────────
def render_match_card(m):
    """Carte pour un match avec prédictions et résultat réel"""
    home     = m['home']
    away     = m['away']
    pH       = m['prob_H']
    pD       = m['prob_D']
    pA       = m['prob_A']
    played   = m['played']
    correct  = m['correct']

    # Couleur de la bordure selon statut
    if not played:
        border_color = "rgba(139,146,168,0.2)"
        status_html  = (f'<span style="font-family:IBM Plex Mono,monospace;'
                        f'font-size:0.72rem;color:{C_DIM};">Non joué</span>')
    elif correct:
        border_color = C_SUCCESS
        status_html  = (f'<span style="background:{C_SUCCESS};color:{C_INK};'
                        f'font-family:IBM Plex Mono,monospace;font-size:0.72rem;'
                        f'font-weight:700;padding:2px 8px;border-radius:4px;">Correct</span>')
    else:
        border_color = C_DANGER
        status_html  = (f'<span style="background:{C_DANGER};color:{C_INK};'
                        f'font-family:IBM Plex Mono,monospace;font-size:0.72rem;'
                        f'font-weight:700;padding:2px 8px;border-radius:4px;">Incorrect</span>')

    # Score réel ou point d'interrogation
    if played:
        score_html = (
            f'<div style="font-family:Big Shoulders Display,sans-serif;'
            f'font-size:2.2rem;font-weight:900;color:{C_TEXT};'
            f'letter-spacing:-0.02em;line-height:1;">'
            f'{m["real_sh"]} &ndash; {m["real_sa"]}'
            f'</div>'
        )
    else:
        score_html = (
            f'<div style="font-family:Big Shoulders Display,sans-serif;'
            f'font-size:2.2rem;font-weight:900;color:{C_DIM};'
            f'letter-spacing:-0.02em;line-height:1;">vs</div>'
        )

    # Barres de probabilité
    # Équipe favorite en cyan, autres en gris
    fav     = 'H' if pH > pD and pH > pA else ('D' if pD > pA else 'A')
    c_h     = C_BRAND  if fav == 'H' else "rgba(139,146,168,0.35)"
    c_d     = C_BRAND  if fav == 'D' else "rgba(139,146,168,0.35)"
    c_a     = C_BRAND  if fav == 'A' else "rgba(139,146,168,0.35)"

    def prob_bar(label, pct, color, align="left"):
        w = int(pct * 100)
        return f"""
        <div style="text-align:{align};">
          <div style="font-family:IBM Plex Mono,monospace;font-size:0.7rem;
                      color:{C_DIM};margin-bottom:3px;">{label} {pct:.0%}</div>
          <div style="background:rgba(139,146,168,0.1);border-radius:3px;
                      height:5px;overflow:hidden;">
            <div style="width:{w}%;height:100%;background:{color};
                        border-radius:3px;"></div>
          </div>
        </div>"""

    # Score prédit
    pred_score_html = (
        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.78rem;'
        f'color:{C_DIM};">Prédit : '
        f'<span style="color:{C_BRAND};">{m["pred_sh"]}-{m["pred_sa"]}</span>'
        f'</span>'
    )

    # Date + heure
    date_html = (
        f'<span style="font-family:IBM Plex Sans,sans-serif;font-size:0.75rem;'
        f'color:{C_DIM};">{m["date"]} {m["kickoff"]}</span>'
    )

    H(f"""
    <div style="background:{BG_PANEL};
                border:1px solid {border_color};
                border-radius:10px;
                padding:1.2rem 1.4rem;
                margin-bottom:1rem;">

      <!-- Header : date + statut -->
      <div style="display:flex;justify-content:space-between;
                  align-items:center;margin-bottom:0.9rem;">
        {date_html}
        {status_html}
      </div>

      <!-- Corps : logo domicile | score | logo extérieur -->
      <div style="display:grid;grid-template-columns:1fr auto 1fr;
                  align-items:center;gap:1rem;margin-bottom:1rem;">

        <!-- Équipe domicile -->
        <div style="display:flex;flex-direction:column;align-items:flex-start;gap:0.4rem;">
          <img src="{logo(home)}"
               style="width:44px;height:44px;object-fit:contain;">
          <div style="font-family:IBM Plex Sans,sans-serif;font-weight:700;
                      font-size:0.9rem;color:{C_TEXT};line-height:1.2;">{home}</div>
        </div>

        <!-- Score central -->
        <div style="text-align:center;">
          {score_html}
          <div style="margin-top:0.3rem;">{pred_score_html}</div>
        </div>

        <!-- Équipe extérieure -->
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:0.4rem;">
          <img src="{logo(away)}"
               style="width:44px;height:44px;object-fit:contain;">
          <div style="font-family:IBM Plex Sans,sans-serif;font-weight:700;
                      font-size:0.9rem;color:{C_TEXT};text-align:right;
                      line-height:1.2;">{away}</div>
        </div>
      </div>

      <!-- Barres de probabilité -->
      <div style="display:grid;grid-template-columns:1fr 0.6fr 1fr;gap:0.8rem;">
        {prob_bar("Domicile", pH, c_h, "left")}
        {prob_bar("Nul", pD, c_d, "center")}
        {prob_bar("Extérieur", pA, c_a, "right")}
      </div>

    </div>
    """)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    H(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.85rem;'
      f'color:{C_DIM};letter-spacing:0.12em;margin-bottom:0.5rem;">'
      f'P300 — MATCHS 2026-27</div>')

    if not caches_available():
        st.warning("Caches de prédiction non disponibles — relancer le notebook 08.")
        return

    fixtures_df = _load_fixtures()
    played_df   = _load_played()
    n_matchdays = int(fixtures_df['matchweek'].max())
    current_md  = get_current_matchday(played_df, fixtures_df)

    # ── Bouton mise à jour ────────────────────────────────────────────────────
    col_upd, col_upd_info = st.columns([2, 6])
    with col_upd:
        update_btn = st.button(
            "Mettre à jour les résultats",
            help="Télécharge les derniers résultats depuis GitHub",
            use_container_width=True,
        )
    with col_upd_info:
        if update_btn:
            with st.spinner("Téléchargement..."):
                n_new, n_total, msg = fetch_and_update_results()
            if msg == "OK":
                if n_new > 0:
                    st.success(f"{n_new} nouveau(x) résultat(s) — {n_total} matchs joués")
                    _load_played.clear()
                    _get_matchday.clear()
                    st.rerun()
                else:
                    st.info("Déjà à jour.")
            else:
                st.error(msg)

    divider()

    # Session state pour la journée affichée
    if 'matchday' not in st.session_state:
        st.session_state.matchday = current_md

    # ── Navigation ────────────────────────────────────────────────────────────
    col_prev, col_title, col_next, col_drop = st.columns([1, 3, 1, 3])

    with col_prev:
        if st.button("◀", use_container_width=True,
                     disabled=st.session_state.matchday <= 1):
            st.session_state.matchday -= 1
            st.rerun()

    with col_title:
        H(f'<div style="font-family:Big Shoulders Display,sans-serif;'
          f'font-size:1.8rem;font-weight:900;color:{C_TEXT};'
          f'text-align:center;letter-spacing:-0.01em;">'
          f'Journée {st.session_state.matchday}</div>')

    with col_next:
        if st.button("▶", use_container_width=True,
                     disabled=st.session_state.matchday >= n_matchdays):
            st.session_state.matchday += 1
            st.rerun()

    with col_drop:
        options = list(range(1, n_matchdays + 1))
        jump    = st.selectbox(
            "Aller à",
            options=options,
            index=st.session_state.matchday - 1,
            format_func=lambda x: f"Journée {x}",
            label_visibility="collapsed",
        )
        if jump != st.session_state.matchday:
            st.session_state.matchday = jump
            st.rerun()

    divider()

    # ── Matchs de la journée ──────────────────────────────────────────────────
    matchday_data = _get_matchday(st.session_state.matchday)

    if not matchday_data:
        st.info("Aucun match pour cette journée.")
        return

    # Stats de précision si des matchs sont joués
    stats = get_matchday_stats(matchday_data)
    if stats and stats['played'] > 0:
        accuracy_color = C_SUCCESS if stats['accuracy'] >= 60 else (
                         C_WARNING if stats['accuracy'] >= 40 else C_DANGER)
        H(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.82rem;'
          f'color:{C_DIM};margin-bottom:1rem;">'
          f'{stats["played"]}/{stats["total"]} matchs joués &nbsp;·&nbsp; '
          f'<span style="color:{accuracy_color};font-weight:700;">'
          f'{stats["correct"]}/{stats["played"]} prédictions correctes '
          f'({stats["accuracy"]}%)</span></div>')

    # Grille de matchs — 2 colonnes
    left_col, right_col = st.columns(2, gap="medium")
    for i, match in enumerate(matchday_data):
        with (left_col if i % 2 == 0 else right_col):
            render_match_card(match)


if __name__ == "__main__":
    main()
