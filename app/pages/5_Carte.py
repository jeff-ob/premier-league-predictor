"""
P500 — Carte des Stades
Carte interactive des 20 stades Premier League 2026-27
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="P500 — Carte des Stades",
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

from config import PROJECT_ROOT
TEAMS_FILE = PROJECT_ROOT / "data" / "raw" / "teams_and_stadiums.csv"

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

# Coordonnées GPS des stades
COORDS = {
    "Arsenal":               (51.5549,  -0.1084),
    "Aston Villa":           (52.5090,  -1.8847),
    "AFC Bournemouth":       (50.7352,  -1.8383),
    "Brentford":             (51.4882,  -0.3087),
    "Brighton & Hove Albion":(50.8618,  -0.0837),
    "Chelsea":               (51.4816,  -0.1910),
    "Coventry City":         (52.4483,  -1.4979),
    "Crystal Palace":        (51.3983,  -0.0854),
    "Everton":               (53.4388,  -3.0635),
    "Fulham":                (51.4749,  -0.2217),
    "Hull City":             (53.7461,  -0.3674),
    "Ipswich Town":          (52.0546,   1.1449),
    "Leeds United":          (53.7774,  -1.5722),
    "Liverpool":             (53.4308,  -2.9608),
    "Manchester City":       (53.4831,  -2.2004),
    "Manchester United":     (53.4631,  -2.2913),
    "Newcastle United":      (54.9755,  -1.6217),
    "Nottingham Forest":     (52.9400,  -1.1326),
    "Sunderland":            (54.9146,  -1.3880),
    "Tottenham Hotspur":     (51.6043,  -0.0665),
}

# Couleur par statut
STATUS_COLORS = {
    "Stayed up": C_BRAND,
    "Promoted":  C_SUCCESS,
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def logo(team):
    return LOGOS.get(team, FALLBACK)


def H(html):
    st.html(html)


def divider():
    H('<hr style="border:none;border-top:1px solid rgba(139,146,168,0.15);margin:1.2rem 0;">')


def status_color(status):
    if "Promoted" in status:
        return C_SUCCESS
    return C_BRAND


# ── Cache ─────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_teams():
    return pd.read_csv(TEAMS_FILE)


# ── Carte Folium ──────────────────────────────────────────────────────────────
def build_map(teams_df, highlight=None):
    import folium

    m = folium.Map(
        location=[52.5, -1.5],
        zoom_start=6,
        tiles="OpenStreetMap",
    )

    # Surcouche style stadia — tuile Stamen Terrain (libre, vivante)
    folium.TileLayer(
        tiles="https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
        attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>, '
             'under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. '
             'Data by <a href="http://openstreetmap.org">OpenStreetMap</a>',
        name="Terrain",
        max_zoom=18,
    ).add_to(m)

    folium.LayerControl().add_to(m)

    for _, row in teams_df.iterrows():
        team   = row["team"]
        coords = COORDS.get(team)
        if not coords:
            continue

        is_highlight = (team == highlight)
        sc           = status_color(row.get("status_for_2026_27", ""))
        color        = C_WARNING if is_highlight else sc
        cap          = f"{row['capacity_2026_27']:,}" if pd.notna(row["capacity_2026_27"]) else "N/A"
        logo_url     = logo(team)
        size         = 42 if is_highlight else 34

        # Icône personnalisée avec le logo du club
        icon_html = f"""
        <div style="
            width:{size}px;height:{size}px;
            background:white;
            border:3px solid {color};
            border-radius:50%;
            box-shadow:0 2px 8px rgba(0,0,0,0.5);
            display:flex;align-items:center;justify-content:center;
            overflow:hidden;">
          <img src="{logo_url}"
               style="width:{size-10}px;height:{size-10}px;object-fit:contain;">
        </div>"""

        icon = folium.DivIcon(
            html=icon_html,
            icon_size=(size, size),
            icon_anchor=(size // 2, size // 2),
        )

        # Popup HTML
        popup_html = f"""
        <div style="background:#12182A;border:2px solid {color};border-radius:10px;
                    padding:14px;min-width:240px;font-family:Arial,sans-serif;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <img src="{logo_url}" style="width:40px;height:40px;object-fit:contain;
                 background:white;border-radius:50%;padding:3px;">
            <div>
              <div style="font-weight:800;font-size:1rem;color:#E8E8E8;">{team}</div>
              <div style="font-size:0.75rem;color:{color};font-weight:600;">
                {row.get('status_for_2026_27','')}
              </div>
            </div>
          </div>
          <div style="background:rgba(255,255,255,0.05);border-radius:6px;
                      padding:8px;margin-bottom:8px;">
            <div style="font-size:0.85rem;font-weight:700;color:#E8E8E8;">{row['stadium']}</div>
            <div style="font-size:0.78rem;color:#8B92A8;">{row['city']}</div>
          </div>
          <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
            <div style="text-align:center;background:rgba(255,255,255,0.05);
                        border-radius:6px;padding:6px 10px;">
              <div style="font-size:0.65rem;color:#8B92A8;">CAPACITE</div>
              <div style="font-size:0.9rem;font-weight:700;color:{color};">{cap}</div>
            </div>
            <div style="text-align:center;background:rgba(255,255,255,0.05);
                        border-radius:6px;padding:6px 10px;">
              <div style="font-size:0.65rem;color:#8B92A8;">FONDÉ</div>
              <div style="font-size:0.9rem;font-weight:700;color:#E8E8E8;">{row.get('founded_year','')}</div>
            </div>
          </div>
          <div style="font-size:0.72rem;color:#8B92A8;border-top:1px solid rgba(139,146,168,0.2);
                      padding-top:8px;line-height:1.4;">
            {str(row.get('previous_season_context',''))[:100]}{'...' if len(str(row.get('previous_season_context',''))) > 100 else ''}
          </div>
        </div>
        """

        folium.Marker(
            location=coords,
            icon=icon,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{team} — {row['stadium']} ({cap})",
        ).add_to(m)

    return m


# ── Grille d'info stades ──────────────────────────────────────────────────────
def render_stadium_grid(teams_df, selected_team=None):
    """Grille de cartes stades — 4 colonnes"""
    cols    = st.columns(4, gap="small")
    teams   = teams_df.sort_values("team").to_dict("records")

    for i, row in enumerate(teams):
        team = row["team"]
        with cols[i % 4]:
            is_sel  = (team == selected_team)
            sc      = status_color(row.get("status_for_2026_27", ""))
            border  = C_WARNING if is_sel else f"rgba(139,146,168,0.15)"
            cap     = f"{int(row['capacity_2026_27']):,}" if pd.notna(row["capacity_2026_27"]) else "N/A"

            H(f"""
            <div style="background:{BG_PANEL};border:1px solid {border};
                        border-top:2px solid {sc};border-radius:8px;
                        padding:0.8rem;margin-bottom:0.6rem;text-align:center;">
              <img src="{logo(team)}"
                   style="width:36px;height:36px;object-fit:contain;margin-bottom:0.4rem;">
              <div style="font-family:IBM Plex Sans,sans-serif;font-weight:700;
                          font-size:0.82rem;color:{C_TEXT};margin-bottom:0.2rem;">{team}</div>
              <div style="font-family:IBM Plex Sans,sans-serif;font-size:0.72rem;
                          color:{C_DIM};margin-bottom:0.2rem;">{row['stadium']}</div>
              <div style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;
                          color:{sc};">{cap}</div>
            </div>
            """)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    H(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.85rem;'
      f'color:{C_DIM};letter-spacing:0.12em;margin-bottom:0.5rem;">'
      f'P500 — CARTE DES STADES 2026-27</div>')

    teams_df = _load_teams()

    # Sélecteur d'équipe
    col_sel, col_info = st.columns([2, 5])
    with col_sel:
        team_options = ["Toutes les équipes"] + sorted(teams_df["team"].tolist())
        selected     = st.selectbox(
            "Équipe",
            options=team_options,
            label_visibility="collapsed",
        )

    selected_team = None if selected == "Toutes les équipes" else selected

    # Info équipe sélectionnée
    if selected_team:
        row = teams_df[teams_df["team"] == selected_team].iloc[0]
        sc  = status_color(row.get("status_for_2026_27", ""))
        with col_info:
            H(f'<div style="font-family:IBM Plex Sans,sans-serif;font-size:0.9rem;'
              f'color:{C_DIM};margin-top:0.4rem;">'
              f'<b style="color:{C_TEXT};">{row["stadium"]}</b> &nbsp;·&nbsp; '
              f'{row["city"]} &nbsp;·&nbsp; '
              f'<span style="color:{sc};">{row.get("status_for_2026_27","")}</span> &nbsp;·&nbsp; '
              f'Capacité : <b style="color:{sc};">{int(row["capacity_2026_27"]):,}</b>'
              f'</div>')

    # Légende
    H(f'<div style="font-family:IBM Plex Sans,sans-serif;font-size:0.8rem;'
      f'color:{C_DIM};margin:0.5rem 0 1rem;">'
      f'<span style="color:{C_BRAND};">●</span> Équipe établie &nbsp;&nbsp;'
      f'<span style="color:{C_SUCCESS};">●</span> Promu 2025/26 &nbsp;&nbsp;'
      f'<span style="color:{C_WARNING};">●</span> Équipe sélectionnée'
      f'</div>')

    # Carte
    try:
        import folium
        from streamlit_folium import st_folium

        fmap = build_map(teams_df, highlight=selected_team)
        st_folium(fmap, width=None, height=550, returned_objects=[])

    except ImportError:
        st.warning("Folium non installé. Lance : `pip install folium streamlit-folium`")
        H(f'<div style="background:{BG_PANEL};border:1px solid rgba(139,146,168,0.2);'
          f'border-radius:8px;padding:2rem;text-align:center;'
          f'font-family:IBM Plex Sans,sans-serif;color:{C_DIM};">'
          f'Carte non disponible — installer folium et streamlit-folium</div>')

    divider()

    # Grille des stades
    H(f'<div style="font-family:Big Shoulders Display,sans-serif;font-size:1.4rem;'
      f'font-weight:800;color:{C_BRAND};text-transform:uppercase;margin-bottom:1rem;">'
      f'Tous les Stades</div>')
    render_stadium_grid(teams_df, selected_team)


if __name__ == "__main__":
    main()
