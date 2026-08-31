"""
P400 — Simulation & Backtest
Modèle appliqué aux saisons passées : prédiction vs réel
"""
import streamlit as st
import pickle
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="P400 — Simulation",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_file = Path(__file__).parent.parent / "assets" / "style.css"
if css_file.exists():
    st.markdown(f"<style>{css_file.read_text()}</style>", unsafe_allow_html=True)

# ── Constantes ────────────────────────────────────────────────────────────────
BG_PANEL = "#12182A"
C_TEXT   = "#E8E8E8"
C_DIM     = "#9BA4C0"
C_BRAND   = "#2FD9E0"
C_SUCCESS  = "#00C46A"
C_WARNING  = "#FFB100"
C_DANGER    = "#FF3B5C"

CACHE_DIR = Path(__file__).parent.parent / "data"

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
    "Wolverhampton Wanderers":"https://resources.premierleague.com/premierleague/badges/100/t39.png",
    "West Ham United":       "https://resources.premierleague.com/premierleague/badges/100/t21.png",
    "Burnley":               "https://resources.premierleague.com/premierleague/badges/100/t90.png",
    "Leicester City":        "https://resources.premierleague.com/premierleague/badges/100/t13.png",
}
FALLBACK = "https://resources.premierleague.com/premierleague/photos/players/110x140/Photo-Missing.png"

# Saisons avec backtest disponible
AVAILABLE_BACKTESTS = {
    "2025/26": {
        "comparison": CACHE_DIR / "backtest_2526_comparison.pkl",
        "metrics":    CACHE_DIR / "backtest_2526_metrics.pkl",
        "features_from": "2024/25",
    }
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def logo(team):
    return LOGOS.get(team, FALLBACK)


def H(html):
    st.html(html)


def divider():
    H('<hr style="border:none;border-top:1px solid rgba(139,146,168,0.15);margin:1.2rem 0;">')


def section_title(text):
    H(f'<div style="font-family:Big Shoulders Display,sans-serif;font-size:1.6rem;'
      f'font-weight:800;color:{C_BRAND};text-transform:uppercase;margin-bottom:1rem;">'
      f'{text}</div>')


# ── Cache ─────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_backtest(season):
    cfg  = AVAILABLE_BACKTESTS[season]
    with open(cfg["comparison"], "rb") as f:
        comparison = pickle.load(f)
    with open(cfg["metrics"], "rb") as f:
        metrics = pickle.load(f)
    return comparison, metrics


# ── Rendu tableau comparaison ──────────────────────────────────────────────────
def render_comparison(comparison, metrics, season):
    """Tableau côte à côte : simulation vs classement réel"""

    import pandas as pd

    col_sim, col_sep, col_real = st.columns([5, 1, 5], gap="small")

    # ── Colonne simulation ────────────────────────────────────────────────────
    with col_sim:
        H(f'<div style="font-family:Big Shoulders Display,sans-serif;font-size:1.2rem;'
          f'font-weight:800;color:{C_BRAND};text-transform:uppercase;margin-bottom:0.8rem;">'
          f'Simulation (pré-saison)</div>')

        sim_sorted = comparison.sort_values("sim_pos")
        rows_sim   = ""
        for _, r in sim_sorted.iterrows():
            pos = int(r["sim_pos"])
            if pos <= 4:    zone_c = C_SUCCESS
            elif pos == 5:  zone_c = C_WARNING
            elif pos <= 7:  zone_c = C_BRAND
            elif pos >= 18: zone_c = C_DANGER
            else:           zone_c = "transparent"

            dot = (f'<span style="background:{zone_c};width:7px;height:7px;'
                   f'border-radius:2px;display:inline-block;margin-right:6px;'
                   f'vertical-align:middle;"></span>')

            rows_sim += f"""
            <tr style="border-bottom:1px solid rgba(139,146,168,0.08);">
              <td style="padding:0.45rem 0.4rem;text-align:center;color:{C_DIM};
                         font-family:IBM Plex Mono,monospace;font-size:0.82rem;">{pos}</td>
              <td style="padding:0.45rem 0.4rem;">
                {dot}<img src="{logo(r['team'])}"
                     style="width:18px;height:18px;object-fit:contain;
                            margin-right:5px;vertical-align:middle;">
                <span style="font-family:IBM Plex Sans,sans-serif;font-size:0.85rem;
                             color:{C_TEXT};">{r['team']}</span>
              </td>
              <td style="padding:0.45rem 0.4rem;text-align:center;
                         font-family:IBM Plex Mono,monospace;font-size:0.82rem;
                         color:{C_BRAND};">{r['avg_points']:.0f}</td>
              <td style="padding:0.45rem 0.4rem;text-align:center;
                         font-family:IBM Plex Mono,monospace;font-size:0.78rem;
                         color:{C_SUCCESS if r['prob_top4'] > 50 else
                                C_WARNING if r['prob_top4'] > 20 else C_DIM};">{r['prob_top4']:.0f}%</td>
            </tr>"""

        H(f"""
        <table style="width:100%;border-collapse:collapse;background:{BG_PANEL};
                      border-radius:8px;overflow:hidden;color:{C_TEXT};">
          <thead>
            <tr style="border-bottom:2px solid {C_BRAND};background:rgba(47,217,224,0.05);">
              <th style="padding:0.5rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                         font-size:0.72rem;color:{C_DIM};">#</th>
              <th style="padding:0.5rem 0.4rem;font-family:IBM Plex Sans,sans-serif;
                         font-size:0.72rem;color:{C_DIM};">Equipe</th>
              <th style="padding:0.5rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                         font-size:0.72rem;color:{C_DIM};">Pts moy</th>
              <th style="padding:0.5rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                         font-size:0.72rem;color:{C_DIM};">LDC%</th>
            </tr>
          </thead>
          <tbody>{rows_sim}</tbody>
        </table>
        """)

    # ── Séparateur ────────────────────────────────────────────────────────────
    with col_sep:
        H(f'<div style="width:1px;background:rgba(139,146,168,0.2);'
          f'min-height:600px;margin:2.5rem auto 0;"></div>')

    # ── Colonne réelle ────────────────────────────────────────────────────────
    with col_real:
        H(f'<div style="font-family:Big Shoulders Display,sans-serif;font-size:1.2rem;'
          f'font-weight:800;color:{C_WARNING};text-transform:uppercase;margin-bottom:0.8rem;">'
          f'Classement Réel {season}</div>')

        real_sorted = comparison.sort_values("real_pos")
        rows_real   = ""
        for _, r in real_sorted.iterrows():
            if pd.isna(r["real_pos"]):
                continue
            pos = int(r["real_pos"])
            rpts = int(r["real_pts"]) if not pd.isna(r["real_pts"]) else 0

            if pos <= 4:    zone_c = C_SUCCESS
            elif pos == 5:  zone_c = C_WARNING
            elif pos <= 7:  zone_c = C_BRAND
            elif pos >= 18: zone_c = C_DANGER
            else:           zone_c = "transparent"

            dot = (f'<span style="background:{zone_c};width:7px;height:7px;'
                   f'border-radius:2px;display:inline-block;margin-right:6px;'
                   f'vertical-align:middle;"></span>')

            # Indicateur écart de position
            diff      = int(r["sim_pos"] - pos) if not pd.isna(r["sim_pos"]) else 0
            if diff < 0:
                diff_html = (f'<span style="color:{C_SUCCESS};font-family:IBM Plex Mono,'
                             f'monospace;font-size:0.72rem;">▲{abs(diff)}</span>')
            elif diff > 0:
                diff_html = (f'<span style="color:{C_DANGER};font-family:IBM Plex Mono,'
                             f'monospace;font-size:0.72rem;">▼{diff}</span>')
            else:
                diff_html = f'<span style="color:{C_DIM};font-size:0.72rem;">=</span>'

            rows_real += f"""
            <tr style="border-bottom:1px solid rgba(139,146,168,0.08);">
              <td style="padding:0.45rem 0.4rem;text-align:center;color:{C_DIM};
                         font-family:IBM Plex Mono,monospace;font-size:0.82rem;">{pos}</td>
              <td style="padding:0.45rem 0.4rem;">
                {dot}<img src="{logo(r['team'])}"
                     style="width:18px;height:18px;object-fit:contain;
                            margin-right:5px;vertical-align:middle;">
                <span style="font-family:IBM Plex Sans,sans-serif;font-size:0.85rem;
                             color:{C_TEXT};">{r['team']}</span>
              </td>
              <td style="padding:0.45rem 0.4rem;text-align:center;
                         font-family:IBM Plex Mono,monospace;font-size:0.82rem;
                         color:{C_WARNING};">{rpts}</td>
              <td style="padding:0.45rem 0.4rem;text-align:center;">{diff_html}</td>
            </tr>"""

        H(f"""
        <table style="width:100%;border-collapse:collapse;background:{BG_PANEL};
                      border-radius:8px;overflow:hidden;color:{C_TEXT};">
          <thead>
            <tr style="border-bottom:2px solid {C_WARNING};background:rgba(255,177,0,0.05);">
              <th style="padding:0.5rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                         font-size:0.72rem;color:{C_DIM};">#</th>
              <th style="padding:0.5rem 0.4rem;font-family:IBM Plex Sans,sans-serif;
                         font-size:0.72rem;color:{C_DIM};">Equipe</th>
              <th style="padding:0.5rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                         font-size:0.72rem;color:{C_DIM};">Pts réels</th>
              <th style="padding:0.5rem 0.4rem;text-align:center;font-family:IBM Plex Sans,sans-serif;
                         font-size:0.72rem;color:{C_DIM};">Ecart</th>
            </tr>
          </thead>
          <tbody>{rows_real}</tbody>
        </table>
        <div style="margin-top:0.6rem;font-family:IBM Plex Sans,sans-serif;font-size:0.75rem;
                    color:{C_DIM};">
          ▲ = mieux prédit &nbsp;·&nbsp; ▼ = moins bien prédit &nbsp;·&nbsp; = exact
        </div>
        """)


# ── Métriques ─────────────────────────────────────────────────────────────────
def render_metrics(metrics, comparison):
    import pandas as pd

    mae        = metrics["mae"]
    top4_acc   = metrics["top4_acc"]
    top4_sim   = set(metrics["top4_sim"])
    top4_real  = set(metrics["top4_real"])
    top4_ok    = top4_sim & top4_real
    top4_missed = top4_real - top4_sim
    top4_wrong  = top4_sim - top4_real

    # Meilleure et pire prédiction
    valid     = comparison.dropna(subset=["real_pos", "sim_pos"])
    valid     = valid.copy()
    valid["abs_diff"] = abs(valid["sim_pos"] - valid["real_pos"])
    best_rows = valid.nsmallest(3, "abs_diff")
    worst_rows= valid.nlargest(3, "abs_diff")

    # Cartes métriques
    acc_color = C_SUCCESS if top4_acc >= 3 else (C_WARNING if top4_acc >= 2 else C_DANGER)
    mae_color = C_SUCCESS if mae <= 3 else (C_WARNING if mae <= 5 else C_DANGER)

    cards_html = f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.5rem;">

      <div style="background:{BG_PANEL};border:1px solid rgba(139,146,168,0.15);
                  border-top:3px solid {acc_color};border-radius:8px;
                  padding:1rem;text-align:center;">
        <div style="font-family:IBM Plex Sans,sans-serif;font-size:0.72rem;
                    color:{C_DIM};text-transform:uppercase;margin-bottom:0.4rem;">Top 4 Correct</div>
        <div style="font-family:Big Shoulders Display,sans-serif;font-size:2.5rem;
                    font-weight:900;color:{acc_color};line-height:1;">{top4_acc}/4</div>
        <div style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;
                    color:{C_DIM};margin-top:0.3rem;">{top4_acc/4:.0%}</div>
      </div>

      <div style="background:{BG_PANEL};border:1px solid rgba(139,146,168,0.15);
                  border-top:3px solid {mae_color};border-radius:8px;
                  padding:1rem;text-align:center;">
        <div style="font-family:IBM Plex Sans,sans-serif;font-size:0.72rem;
                    color:{C_DIM};text-transform:uppercase;margin-bottom:0.4rem;">Ecart Moyen</div>
        <div style="font-family:Big Shoulders Display,sans-serif;font-size:2.5rem;
                    font-weight:900;color:{mae_color};line-height:1;">{mae:.1f}</div>
        <div style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;
                    color:{C_DIM};margin-top:0.3rem;">places</div>
      </div>

      <div style="background:{BG_PANEL};border:1px solid rgba(139,146,168,0.15);
                  border-top:3px solid {C_SUCCESS};border-radius:8px;
                  padding:1rem;">
        <div style="font-family:IBM Plex Sans,sans-serif;font-size:0.72rem;
                    color:{C_DIM};text-transform:uppercase;margin-bottom:0.5rem;">Top 4 Trouvés</div>
        {''.join(f'<div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.3rem;"><img src="{logo(t)}" style="width:16px;height:16px;object-fit:contain;"><span style="font-family:IBM Plex Sans,sans-serif;font-size:0.78rem;color:{C_SUCCESS};">{t}</span></div>' for t in top4_ok)}
      </div>

      <div style="background:{BG_PANEL};border:1px solid rgba(139,146,168,0.15);
                  border-top:3px solid {C_DANGER};border-radius:8px;
                  padding:1rem;">
        <div style="font-family:IBM Plex Sans,sans-serif;font-size:0.72rem;
                    color:{C_DIM};text-transform:uppercase;margin-bottom:0.5rem;">Surprises Ratées</div>
        {''.join(f'<div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.3rem;"><img src="{logo(t)}" style="width:16px;height:16px;object-fit:contain;"><span style="font-family:IBM Plex Sans,sans-serif;font-size:0.78rem;color:{C_DANGER};">{t}</span></div>' for t in top4_missed)}
      </div>

    </div>
    """
    H(cards_html)

    # Meilleures et pires prédictions individuelles
    col_best, col_worst = st.columns(2, gap="large")

    with col_best:
        H(f'<div style="font-family:IBM Plex Sans,sans-serif;font-size:0.85rem;'
          f'font-weight:600;color:{C_SUCCESS};margin-bottom:0.5rem;">Meilleures prédictions</div>')
        for _, r in best_rows.iterrows():
            diff = int(r["sim_pos"] - r["real_pos"])
            label = "Exact" if diff == 0 else f"Écart {diff:+d}"
            H(f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem;">'
              f'<img src="{logo(r["team"])}" style="width:20px;height:20px;object-fit:contain;">'
              f'<span style="font-family:IBM Plex Sans,sans-serif;font-size:0.85rem;color:{C_TEXT};">'
              f'{r["team"]}</span>'
              f'<span style="margin-left:auto;font-family:IBM Plex Mono,monospace;'
              f'font-size:0.78rem;color:{C_SUCCESS};">{label}</span>'
              f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.75rem;color:{C_DIM};">'
              f'Sim:{int(r["sim_pos"])} → Réel:{int(r["real_pos"])}</span>'
              f'</div>')

    with col_worst:
        H(f'<div style="font-family:IBM Plex Sans,sans-serif;font-size:0.85rem;'
          f'font-weight:600;color:{C_DANGER};margin-bottom:0.5rem;">Plus grandes erreurs</div>')
        for _, r in worst_rows.iterrows():
            diff = int(r["sim_pos"] - r["real_pos"])
            H(f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem;">'
              f'<img src="{logo(r["team"])}" style="width:20px;height:20px;object-fit:contain;">'
              f'<span style="font-family:IBM Plex Sans,sans-serif;font-size:0.85rem;color:{C_TEXT};">'
              f'{r["team"]}</span>'
              f'<span style="margin-left:auto;font-family:IBM Plex Mono,monospace;'
              f'font-size:0.78rem;color:{C_DANGER};">Écart {diff:+d}</span>'
              f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.75rem;color:{C_DIM};">'
              f'Sim:{int(r["sim_pos"])} → Réel:{int(r["real_pos"])}</span>'
              f'</div>')


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    H(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.85rem;'
      f'color:{C_DIM};letter-spacing:0.12em;margin-bottom:0.5rem;">'
      f'P400 — SIMULATION & BACKTEST</div>')

    H(f'<div style="font-family:IBM Plex Sans,sans-serif;font-size:0.95rem;'
      f'color:{C_DIM};margin-bottom:1.5rem;">'
      f'Le modèle Stacking v3 appliqué aux saisons passées &mdash; '
      f'prédiction pré-saison vs classement réel.</div>')

    # Sélecteur de saison
    available = list(AVAILABLE_BACKTESTS.keys())
    selected  = st.selectbox(
        "Saison",
        options=available,
        index=0,
        format_func=lambda s: f"Saison {s}  (features depuis {AVAILABLE_BACKTESTS[s]['features_from']})",
        label_visibility="collapsed",
    )

    cfg = AVAILABLE_BACKTESTS[selected]
    if not cfg["comparison"].exists() or not cfg["metrics"].exists():
        st.warning(f"Données backtest non disponibles pour {selected}. "
                   f"Relancer le notebook 08.")
        return

    comparison, metrics = _load_backtest(selected)

    divider()

    # Métriques en haut
    section_title(f"Métriques — {selected}")
    render_metrics(metrics, comparison)

    divider()

    # Tableaux côte à côte
    section_title("Simulation vs Classement Réel")
    H(f'<div style="font-family:IBM Plex Sans,sans-serif;font-size:0.82rem;'
      f'color:{C_DIM};margin-bottom:1rem;">'
      f'10,000 simulations pré-saison avec les données de '
      f'{cfg["features_from"]} &mdash; '
      f'écart ▲/▼ = différence entre position simulée et position réelle</div>')
    render_comparison(comparison, metrics, selected)


if __name__ == "__main__":
    main()
