"""
P200 — Classement 2026-27
Classement en temps réel + probabilités LDC via Monte Carlo
Animation simulation dans la colonne droite uniquement — classement jamais bloqué
"""
import streamlit as st
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.season_2627 import (
    load_played_results,
    compute_standings_from_results,
    run_monte_carlo,
    load_precomputed_caches,
    caches_available,
    fetch_and_update_results,
)
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="P200 — Classement 2026-27",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_file = Path(__file__).parent.parent / "assets" / "style.css"
if css_file.exists():
    st.markdown(f"<style>{css_file.read_text()}</style>", unsafe_allow_html=True)

# ── Constantes ────────────────────────────────────────────────────────────────
BG_MAIN   = "#0B0E14"
BG_PANEL  = "#12182A"
C_TEXT   = "#E8E8E8"
C_DIM     = "#9BA4C0"
C_BRAND   = "#2FD9E0"
C_SUCCESS  = "#00C46A"
C_WARNING  = "#FFB100"
C_DANGER    = "#FF3B5C"

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
FALLBACK    = "https://resources.premierleague.com/premierleague/photos/players/110x140/Photo-Missing.png"
FORM_COLORS = {"W": C_SUCCESS, "D": C_WARNING, "L": C_DANGER}


# ── Helpers ───────────────────────────────────────────────────────────────────
def logo(team):
    return LOGOS.get(team, FALLBACK)


def H(html):
    st.html(html)


def divider():
    H(f'<hr style="border:none;border-top:1px solid rgba(139,146,168,0.15);margin:1rem 0;">')


def section_title(text):
    H(f'<div style="font-family:Big Shoulders Display,sans-serif;font-size:1.6rem;'
      f'font-weight:800;color:{C_BRAND};text-transform:uppercase;margin-bottom:1rem;">'
      f'{text}</div>')


# ── Cache Streamlit ───────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_played():
    return load_played_results()


@st.cache_data(show_spinner=False)
def _load_fixtures():
    from config import PROJECT_ROOT
    return pd.read_csv(PROJECT_ROOT / "data" / "raw" / "fixtures.csv")


@st.cache_data(show_spinner="Chargement des caches...")
def _load_caches():
    return load_precomputed_caches()


# ── Rendu tableau classement ──────────────────────────────────────────────────
def _render_table(standings_df):
    """Tableau classement seul — rendu immédiat, indépendant de la simulation"""
    rows_html = ""
    for _, r in standings_df.iterrows():
        pos = r["pos"]
        if pos <= 4:    zone_c = C_SUCCESS
        elif pos == 5:  zone_c = C_WARNING
        elif pos >= 18: zone_c = C_DANGER
        else:           zone_c = "transparent"

        zone_dot  = (f'<span style="background:{zone_c};width:8px;height:8px;border-radius:2px;'
                     f'display:inline-block;margin-right:6px;vertical-align:middle;"></span>')
        logo_html = (f'<img src="{logo(r["team"])}" style="width:20px;height:20px;'
                     f'object-fit:contain;margin-right:6px;vertical-align:middle;">')
        form_html = ""
        for res in r["form"]:
            fc = FORM_COLORS.get(res, C_DIM)
            form_html += (f'<span style="background:{fc};color:#0B0E14;font-family:IBM Plex Mono,'
                          f'monospace;font-size:0.6rem;font-weight:700;padding:1px 4px;'
                          f'border-radius:3px;margin-right:2px;">{res}</span>')
        gd = f"+{r['gd']}" if r["gd"] > 0 else str(r["gd"])

        rows_html += f"""
        <tr style="border-bottom:1px solid rgba(139,146,168,0.08);">
          <td style="padding:0.5rem 0.4rem;text-align:center;color:{C_DIM};
                     font-family:IBM Plex Mono,monospace;font-size:0.85rem;">{pos}</td>
          <td style="padding:0.5rem 0.4rem;">
            {zone_dot}{logo_html}
            <span style="font-family:IBM Plex Sans,sans-serif;font-size:0.9rem;
                         color:{C_TEXT};">{r['team']}</span>
          </td>
          <td style="padding:0.5rem 0.4rem;text-align:center;font-family:IBM Plex Mono,monospace;font-size:0.85rem;">{r['played']}</td>
          <td style="padding:0.5rem 0.4rem;text-align:center;font-family:IBM Plex Mono,monospace;font-size:0.85rem;">{r['won']}</td>
          <td style="padding:0.5rem 0.4rem;text-align:center;font-family:IBM Plex Mono,monospace;font-size:0.85rem;">{r['drawn']}</td>
          <td style="padding:0.5rem 0.4rem;text-align:center;font-family:IBM Plex Mono,monospace;font-size:0.85rem;">{r['lost']}</td>
          <td style="padding:0.5rem 0.4rem;text-align:center;font-family:IBM Plex Mono,monospace;font-size:0.85rem;">{r['gf']}</td>
          <td style="padding:0.5rem 0.4rem;text-align:center;font-family:IBM Plex Mono,monospace;font-size:0.85rem;">{r['ga']}</td>
          <td style="padding:0.5rem 0.4rem;text-align:center;color:{C_DIM};
                     font-family:IBM Plex Mono,monospace;font-size:0.85rem;">{gd}</td>
          <td style="padding:0.5rem 0.4rem;text-align:center;font-weight:700;
                     font-family:IBM Plex Mono,monospace;font-size:0.9rem;
                     color:{C_BRAND};">{r['points']}</td>
          <td style="padding:0.5rem 0.6rem;">{form_html}</td>
        </tr>"""

    H(f"""
    <table style="width:100%;border-collapse:collapse;background:{BG_PANEL};
                  border-radius:8px;overflow:hidden;color:{C_TEXT};">
      <thead>
        <tr style="border-bottom:2px solid {C_BRAND};background:rgba(47,217,224,0.05);">
          <th style="padding:0.55rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;font-size:0.75rem;color:{C_DIM};font-weight:600;">#</th>
          <th style="padding:0.55rem 0.4rem;text-align:left;font-family:IBM Plex Sans,sans-serif;font-size:0.75rem;color:{C_DIM};font-weight:600;">Equipe</th>
          <th style="padding:0.55rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;font-size:0.75rem;color:{C_DIM};font-weight:600;">J</th>
          <th style="padding:0.55rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;font-size:0.75rem;color:{C_DIM};font-weight:600;">V</th>
          <th style="padding:0.55rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;font-size:0.75rem;color:{C_DIM};font-weight:600;">N</th>
          <th style="padding:0.55rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;font-size:0.75rem;color:{C_DIM};font-weight:600;">D</th>
          <th style="padding:0.55rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;font-size:0.75rem;color:{C_DIM};font-weight:600;">BP</th>
          <th style="padding:0.55rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;font-size:0.75rem;color:{C_DIM};font-weight:600;">BC</th>
          <th style="padding:0.55rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;font-size:0.75rem;color:{C_DIM};font-weight:600;">+/-</th>
          <th style="padding:0.55rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;font-size:0.75rem;color:{C_DIM};font-weight:600;">Pts</th>
          <th style="padding:0.55rem 0.4rem;text-align:left;font-family:IBM Plex Sans,sans-serif;font-size:0.75rem;color:{C_DIM};font-weight:600;">Forme</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    <div style="margin-top:0.8rem;font-family:IBM Plex Sans,sans-serif;font-size:0.78rem;
                color:{C_DIM};display:flex;flex-wrap:wrap;gap:12px;">
      <span><span style="background:{C_SUCCESS};width:8px;height:8px;border-radius:2px;
            display:inline-block;margin-right:5px;vertical-align:middle;"></span>Top 4 — LDC</span>
      <span><span style="background:{C_WARNING};width:8px;height:8px;border-radius:2px;
            display:inline-block;margin-right:5px;vertical-align:middle;"></span>5e — Europa</span>
      <span><span style="background:{C_DANGER};width:8px;height:8px;border-radius:2px;
            display:inline-block;margin-right:5px;vertical-align:middle;"></span>18e-20e — Relégation</span>
    </div>
    """)


# ── Cartes probabilités (HTML pur) ────────────────────────────────────────────
def _build_proba_cards(standings_df, sim_df):
    """HTML des cartes probabilités alignées sur l'ordre du classement"""
    if sim_df is None or sim_df.empty:
        return (f'<div style="background:{BG_PANEL};border:1px solid rgba(139,146,168,0.2);'
                f'border-radius:8px;padding:1.5rem;text-align:center;color:{C_DIM};'
                f'font-family:IBM Plex Sans,sans-serif;">'
                f'Lancez la simulation Monte Carlo<br>pour voir les probabilités</div>')

    order       = standings_df["team"].tolist()
    sim_ordered = sim_df.set_index("team").reindex(order).reset_index()

    def bar(pct, color):
        w = min(100, max(0, pct))
        return (f'<div style="background:rgba(139,146,168,0.12);border-radius:3px;'
                f'height:5px;overflow:hidden;margin-top:2px;">'
                f'<div style="width:{w}%;height:100%;background:{color};'
                f'border-radius:3px;"></div></div>')

    cards = ""
    for _, row in sim_ordered.iterrows():
        team    = row["team"]
        p_top4  = row["prob_top4"]
        p_title = row["prob_title"]
        p_releg = row["prob_releg"]
        avg_pts = row["avg_points"]
        top4_c  = C_SUCCESS if p_top4  > 50 else (C_WARNING if p_top4  > 20 else C_DIM)
        title_c = C_SUCCESS if p_title > 20 else (C_WARNING if p_title > 5  else C_DIM)
        releg_c = C_DANGER   if p_releg > 30 else (C_WARNING if p_releg > 10 else C_DIM)

        cards += f"""
        <div style="background:{BG_PANEL};border:1px solid rgba(139,146,168,0.15);
                    border-radius:6px;padding:0.65rem 0.8rem;margin-bottom:0.4rem;">
          <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem;">
            <img src="{logo(team)}" style="width:18px;height:18px;object-fit:contain;">
            <span style="font-family:IBM Plex Sans,sans-serif;font-weight:600;
                         font-size:0.8rem;color:{C_TEXT};">{team}</span>
            <span style="margin-left:auto;font-family:IBM Plex Mono,monospace;
                         font-size:0.72rem;color:{C_DIM};">{avg_pts} pts</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.4rem;">
            <div>
              <div style="font-family:IBM Plex Mono,monospace;font-size:0.62rem;color:{C_DIM};">LDC</div>
              <div style="font-family:IBM Plex Mono,monospace;font-weight:700;font-size:0.82rem;color:{top4_c};">{p_top4:.0f}%</div>
              {bar(p_top4, top4_c)}
            </div>
            <div>
              <div style="font-family:IBM Plex Mono,monospace;font-size:0.62rem;color:{C_DIM};">Titre</div>
              <div style="font-family:IBM Plex Mono,monospace;font-weight:700;font-size:0.82rem;color:{title_c};">{p_title:.0f}%</div>
              {bar(p_title, title_c)}
            </div>
            <div>
              <div style="font-family:IBM Plex Mono,monospace;font-size:0.62rem;color:{C_DIM};">Relég.</div>
              <div style="font-family:IBM Plex Mono,monospace;font-weight:700;font-size:0.82rem;color:{releg_c};">{p_releg:.0f}%</div>
              {bar(p_releg, releg_c)}
            </div>
          </div>
        </div>"""

    return cards


# ── Animation simulation (HTML pur) ──────────────────────────────────────────
def _build_anim_html(done, total, speed, eta, partial_df):
    """HTML de l'animation en cours — affiché dans le placeholder colonne droite"""
    pct  = int(done / total * 100)
    top5 = partial_df.head(5)

    bars = ""
    for _, r in top5.iterrows():
        w = min(100, r["prob_top4"])
        bars += (
            f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem;">'
            f'<span style="font-family:IBM Plex Sans,sans-serif;font-size:0.78rem;'
            f'color:{C_TEXT};width:140px;flex-shrink:0;">{r["team"]}</span>'
            f'<div style="flex:1;background:rgba(139,146,168,0.1);border-radius:3px;'
            f'height:5px;overflow:hidden;">'
            f'<div style="width:{w}%;height:100%;background:{C_SUCCESS};border-radius:3px;"></div>'
            f'</div>'
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.78rem;'
            f'color:{C_SUCCESS};width:36px;text-align:right;">{r["prob_top4"]:.0f}%</span>'
            f'</div>'
        )

    return f"""
    <div style="background:{BG_PANEL};border:1px solid rgba(47,217,224,0.3);
                border-radius:8px;padding:1rem;">
      <div style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;
                  color:{C_DIM};margin-bottom:0.4rem;">
        {done:,} / {total:,} &nbsp;·&nbsp; {speed:.0f} sim/s &nbsp;·&nbsp; ETA {eta:.0f}s
      </div>
      <div style="background:rgba(139,146,168,0.1);border-radius:4px;
                  height:6px;overflow:hidden;margin-bottom:0.8rem;">
        <div style="width:{pct}%;height:100%;background:{C_BRAND};border-radius:4px;"></div>
      </div>
      <div style="font-family:IBM Plex Sans,sans-serif;font-size:0.7rem;
                  color:{C_DIM};margin-bottom:0.5rem;">TOP 5 LDC — APERCU EN DIRECT</div>
      {bars}
    </div>"""


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    H(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.85rem;'
      f'color:{C_DIM};letter-spacing:0.12em;margin-bottom:0.5rem;">'
      f'P200 — CLASSEMENT 2026-27</div>')

    fixtures_df  = _load_fixtures()
    played_df    = _load_played()
    n_played     = len(played_df)
    all_teams    = sorted(set(fixtures_df["home_team"]) | set(fixtures_df["away_team"]))
    standings_df = compute_standings_from_results(played_df, all_teams)

    if n_played > 0:
        last_md = int(played_df["matchday"].max())
        H(f'<div style="font-family:IBM Plex Sans,sans-serif;font-size:0.9rem;'
          f'color:{C_DIM};margin-bottom:1rem;">'
          f'{n_played} matchs joués &nbsp;·&nbsp; Dernière journée : J{last_md}</div>')
    else:
        H(f'<div style="font-family:IBM Plex Sans,sans-serif;font-size:0.9rem;'
          f'color:{C_DIM};margin-bottom:1rem;">Saison non commencée</div>')

    # ── Bouton mise à jour ────────────────────────────────────────────────────
    col_upd, col_upd_info = st.columns([2, 6])
    with col_upd:
        update_btn = st.button(
            "Mettre à jour les résultats",
            help="Télécharge les derniers résultats depuis GitHub (openfootball)",
            use_container_width=True,
        )
    with col_upd_info:
        if update_btn:
            with st.spinner("Téléchargement en cours..."):
                n_new, n_total, msg = fetch_and_update_results()
            if msg == "OK":
                if n_new > 0:
                    st.success(
                        f"{n_new} nouveau(x) résultat(s) ajouté(s) — "
                        f"{n_total} matchs joués au total"
                    )
                    # Vider le cache pour forcer le rechargement
                    _load_played.clear()
                    st.rerun()
                else:
                    st.info("Déjà à jour — aucun nouveau résultat disponible.")
            else:
                st.error(msg)

    # Session state
    if "sim_results"   not in st.session_state: st.session_state.sim_results   = None
    if "sim_timestamp" not in st.session_state: st.session_state.sim_timestamp = None
    if "sim_n"         not in st.session_state: st.session_state.sim_n         = None

    divider()

    # ── Layout : classement (gauche) | probas (droite) ───────────────────────
    col_table, col_proba = st.columns([13, 7], gap="large")

    # Classement — rendu immédiat, jamais touché par la simulation
    with col_table:
        section_title("Classement")
        _render_table(standings_df)

    # Colonne droite — bouton + animation + résultats
    with col_proba:
        section_title("Probabilités")

        # Bouton + sélecteur
        c1, c2 = st.columns([3, 2])
        with c1:
            run_btn = st.button(
                "Lancer Monte Carlo", type="primary",
                disabled=not caches_available(),
                use_container_width=True
            )
        with c2:
            n_sims = st.selectbox("N", [1000, 5000, 10000], index=2,
                                  label_visibility="collapsed")

        # Info dernière simulation
        if not caches_available():
            H(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.75rem;'
              f'color:{C_DANGER};">Caches non disponibles</div>')
        elif st.session_state.sim_timestamp:
            elapsed = int(time.time() - st.session_state.sim_timestamp)
            mins, secs = elapsed // 60, elapsed % 60
            H(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;'
              f'color:{C_DIM};margin-bottom:0.5rem;">'
              f'Dernière : {mins}m {secs}s &nbsp;·&nbsp; {st.session_state.sim_n:,} sims</div>')

        # Placeholder unique pour animation ET résultats finaux
        placeholder = st.empty()

        # Afficher résultats existants si simulation déjà faite
        if st.session_state.sim_results is not None and not run_btn:
            placeholder.html(_build_proba_cards(standings_df, st.session_state.sim_results))

        # Simulation — tout dans le placeholder, classement intact
        if run_btn:
            proba_cache, lambda_cache = _load_caches()
            t0 = time.time()

            def on_progress(done, total, partial):
                elapsed = time.time() - t0
                speed   = done / elapsed if elapsed > 0 else 0
                eta     = (elapsed / done) * (total - done) if done > 0 else 0
                placeholder.html(_build_anim_html(done, total, speed, eta, partial))

            sim_results = run_monte_carlo(
                fixtures_df, proba_cache, lambda_cache,
                played_df=played_df if n_played > 0 else None,
                n_simulations=n_sims,
                progress_callback=on_progress
            )

            elapsed = time.time() - t0
            st.session_state.sim_results   = sim_results
            st.session_state.sim_timestamp = time.time()
            st.session_state.sim_n         = n_sims

            # Remplacer animation par résultats finaux
            placeholder.html(_build_proba_cards(standings_df, sim_results))
            st.toast(f"Terminé en {elapsed:.0f}s", icon="✅")


if __name__ == "__main__":
    main()
