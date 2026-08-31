"""
Premier League 2026-27 — Page d'accueil
Navigation principale
"""
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="PL 2026-27",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_file = Path(__file__).parent / "assets" / "style.css"
if css_file.exists():
    st.markdown(f"<style>{css_file.read_text()}</style>", unsafe_allow_html=True)

# ── Tokens v2 ─────────────────────────────────────────────────────────────────
BG_MAIN     = "#0B0E14"
BG_PANEL    = "#12182A"
BORDER_DIM  = "rgba(139,146,168,0.15)"
C_TEXT      = "#E8E8E8"
C_DIM       = "#9BA4C0"
C_INK       = "#0B0E14"
C_BRAND     = "#2FD9E0"
C_SUCCESS   = "#00C46A"
C_WARNING   = "#FFB100"
C_DANGER    = "#FF3B5C"


def H(html):
    st.html(html)


def main():
    # En-tête
    H(f"""
    <div style="border-bottom:2px solid {BORDER_DIM};padding-bottom:1.5rem;
                margin-bottom:2rem;">
      <div style="font-family:'Big Shoulders Display',sans-serif;font-size:3rem;
                  font-weight:900;color:{C_TEXT};letter-spacing:-0.02em;
                  text-transform:uppercase;line-height:1;">
        Premier League
      </div>
      <div style="font-family:'IBM Plex Sans',sans-serif;font-size:1.1rem;
                  color:{C_DIM};margin-top:0.3rem;">
        Saison 2026-27 &nbsp;&middot;&nbsp; Prédictions &amp; Analyse
      </div>
    </div>
    """)

    # Index des pages
    pages = [
        ("P100", "Accueil",     "Historique des saisons, palmarès, statistiques"),
        ("P200", "Classement",  "Classement en cours + probabilités LDC via Monte Carlo"),
        ("P300", "Matchs",      "Prédictions journée par journée + résultats réels"),
        ("P400", "Simulation",  "Backtest du modèle sur les saisons passées"),
        ("P500", "Carte",       "Carte interactive des 20 stades"),
    ]

    rows_html = ""
    for code, name, desc in pages:
        rows_html += f"""
        <tr style="border-bottom:1px solid {BORDER_DIM};">
          <td style="padding:1rem 0.8rem;font-family:'IBM Plex Mono',monospace;
                     font-size:0.9rem;color:{C_BRAND};font-weight:600;
                     white-space:nowrap;">{code}</td>
          <td style="padding:1rem 0.8rem;font-family:'IBM Plex Sans',sans-serif;
                     font-weight:700;font-size:0.95rem;color:{C_TEXT};
                     white-space:nowrap;">{name}</td>
          <td style="padding:1rem 0.8rem;font-family:'IBM Plex Sans',sans-serif;
                     font-size:0.9rem;color:{C_DIM};">{desc}</td>
        </tr>"""

    H(f"""
    <div style="background:{BG_PANEL};border:1px solid {BORDER_DIM};
                border-radius:10px;overflow:hidden;max-width:800px;">
      <div style="padding:1rem 1.2rem;border-bottom:2px solid {C_BRAND};
                  background:rgba(47,217,224,0.05);">
        <span style="font-family:'Big Shoulders Display',sans-serif;font-size:1.2rem;
                     font-weight:800;color:{C_TEXT};text-transform:uppercase;">
          Index des pages
        </span>
      </div>
      <table style="width:100%;border-collapse:collapse;">
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """)

    # Info modèle
    H(f"""
    <div style="margin-top:2.5rem;padding:1.2rem 1.5rem;
                background:{BG_PANEL};border:1px solid {BORDER_DIM};
                border-left:4px solid {C_SUCCESS};border-radius:8px;
                max-width:600px;">
      <div style="font-family:'IBM Plex Sans',sans-serif;font-size:0.82rem;
                  color:{C_DIM};margin-bottom:0.3rem;text-transform:uppercase;
                  letter-spacing:0.06em;">Modèle de prédiction</div>
      <div style="font-family:'IBM Plex Sans',sans-serif;font-size:0.95rem;
                  color:{C_TEXT};">
        Stacking v3 &nbsp;&middot;&nbsp;
        <span style="font-weight:700;color:{C_SUCCESS};">59.4% accuracy</span>
        &nbsp;&middot;&nbsp; +16.9 pts vs baseline
        &nbsp;&middot;&nbsp; GB + RF + LR
      </div>
    </div>
    """)

    H(f"""
    <div style="margin-top:1.5rem;font-family:'IBM Plex Sans',sans-serif;
                font-size:0.88rem;color:{C_DIM};">
      Utilisez la barre de navigation à gauche pour accéder aux pages.
    </div>
    """)


if __name__ == "__main__":
    main()
