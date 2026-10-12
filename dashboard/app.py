"""Dashboard Streamlit : interface pour le décideur.

Le dashboard NE CALCULE RIEN : il appelle l'API (séparation des responsabilités).
Lancer : API_URL=http://localhost:8000 streamlit run dashboard/app.py
"""
import os

import folium
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

API_URL = os.environ.get("API_URL", "http://localhost:8000")
LEVEL_COLORS = {"faible": "#2ecc71", "modéré": "#f1c40f", "élevé": "#e67e22",
                "très élevé": "#e74c3c", "critique": "#7b0000"}
PRESETS = [50, 80, 100, 120, 150]

st.set_page_config(page_title="MBEUD-mi | Centre de veille", page_icon="🌧️", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
  background: radial-gradient(ellipse at 8% 0%, rgba(17,166,160,.09), transparent 34%),
              linear-gradient(180deg, #f5f8fc 0%, #eef3f8 100%);
}
[data-testid="stHeader"] { background: rgba(245,248,252,.82); }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#10233f 0%,#173b5d 100%); }
[data-testid="stSidebar"] * { color: #f3f7fb; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color:#d9e8f5; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1600px; }
h1,h2,h3 { color: #10233f; letter-spacing: -.025em; }
h1 { font-weight: 800; }
[data-testid="stMetric"] {
  background: rgba(255,255,255,.92); border: 1px solid #e1eaf2;
  border-radius: 16px; padding: 18px 20px; box-shadow: 0 5px 20px rgba(16,35,63,.055);
}
[data-testid="stMetricLabel"] p { color:#64748b; font-weight:600; }
[data-testid="stMetricValue"] { color:#10233f; font-weight:800; }
div[data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; }
.stButton button { border-radius: 10px; font-weight: 650; }
.mb-hero {
  background: linear-gradient(115deg,#10233f 0%,#155b83 58%,#11a6a0 100%);
  color: white; border-radius: 22px; padding: 26px 30px; margin: 0 0 22px 0;
  box-shadow: 0 12px 30px rgba(16,35,63,.14);
}
.mb-hero h1 { color:white; font-size:2.05rem; margin:0 0 .35rem 0; }
.mb-hero p { color:#e5f4fb; margin:0; font-size:1rem; }
.mb-eyebrow { color:#aeece6; text-transform:uppercase; font-size:.76rem; letter-spacing:.13em; font-weight:800; }
.mb-section { color:#64748b; text-transform:uppercase; font-size:.76rem; letter-spacing:.12em; font-weight:800; margin-bottom:.3rem; }
.mb-legend { display:flex; flex-wrap:wrap; gap:9px; margin:.6rem 0 1rem 0; }
.mb-chip { background:white; border:1px solid #e2e8f0; padding:7px 11px; border-radius:999px; color:#334155; font-size:.84rem; }
</style>
""", unsafe_allow_html=True)


def api_get(path: str, **params):
    r = requests.get(f"{API_URL}{path}", params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def api_post(path: str, payload: dict):
    r = requests.post(f"{API_URL}{path}", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=120, show_spinner=False)
def get_risk(rain: float):
    return api_get("/risk", rain_mm=rain)


@st.cache_data(ttl=600, show_spinner=False)
def get_weather_forecast():
    """Prévisions météo réelles depuis le fournisseur, sans fallback synthétique."""
    return api_get("/api/v1/weather/forecast")


@st.cache_data(ttl=120, show_spinner=False)
def get_simulation(rain: float, pumps: int, teams: int, vehicles: int):
    return api_post("/simulation", {"rain_mm": rain, "pumps": pumps, "teams": teams,
                                    "vehicles": vehicles, "top_n": 25})


# --- Barre latérale : scénario de pluie partagé par toutes les pages --------------------
st.sidebar.markdown("""
<div style="padding:8px 2px 18px 2px">
  <div style="font-size:1.7rem;font-weight:850;letter-spacing:-.04em">🌧️ MBEUD-mi</div>
  <div style="font-size:.78rem;opacity:.8">CENTRE GÉOSPATIAL · BÊTA</div>
</div>
""", unsafe_allow_html=True)
page = st.sidebar.radio("Page", ["Overview", "Risk Map", "Forecast", "Zones",
                                 "Simulation", "Resources", "Alerts", "Météo réelle"])
choice = st.sidebar.selectbox("Pluie prévue (24 h)", [f"{p} mm" for p in PRESETS] + ["Personnalisée"], index=2)
if choice == "Personnalisée":
    rain = st.sidebar.number_input("Pluie (mm)", min_value=0.0, max_value=500.0, value=100.0, step=5.0)
else:
    rain = float(choice.split()[0])
st.sidebar.markdown("---")
st.sidebar.caption("MODE DÉMONSTRATION · DONNÉES SYNTHÉTIQUES")
st.sidebar.caption("Les résultats ne sont pas des alertes officielles.")

st.markdown("""
<div class="mb-hero">
  <div class="mb-eyebrow">Sénégal · Prototype expérimental</div>
  <h1>Centre de veille hydro-urbaine</h1>
  <p>Explorer les zones prioritaires, comparer des scénarios de pluie et comprendre les limites des données disponibles.</p>
</div>
""", unsafe_allow_html=True)
st.info("Prototype sur données synthétiques : les niveaux affichés sont des simulations, pas des prévisions officielles. MBEUD-mi ne remplace ni l'ANACIM, ni les autorités, ni les services d'urgence.")

try:
    risk = get_risk(rain)
    sim = get_simulation(rain, 10, 5, 10)
except Exception as exc:  # API pas encore prête, ou arrêtée
    st.error(f"Impossible de joindre l'API ({API_URL}) : {exc}")
    st.stop()

summary = risk["summary"]

if page == "Overview":
    st.markdown('<div class="mb-section">Tableau de situation</div>', unsafe_allow_html=True)
    st.header("Vue générale")
    st.caption(f"Scénario actif : {rain:.0f} mm de pluie cumulée simulée sur 24 h · Données de démonstration")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Niveau de risque global", summary["global_level"], f"score {summary['global_score']}")
    c2.metric("Zones critiques", summary["n_critical"])
    c3.metric("Pluie prévue (mm)", f"{summary['rain_mm']:.0f}")
    c4.metric("Routes à risque (km)", summary["road_km_at_risk"])
    c5, c6, c7 = st.columns(3)
    c5.metric("Population exposée", f"{summary['population_exposed']:,}".replace(",", " "))
    c6.metric("Hôpitaux exposés", summary["hospitals_exposed"])
    c7.metric("Écoles exposées", summary["schools_exposed"])
    st.subheader("Répartition des zones par niveau")
    counts = pd.DataFrame({"niveau": list(summary["level_counts"]), "zones": list(summary["level_counts"].values())})
    st.bar_chart(counts.set_index("niveau"))

elif page == "Risk Map":
    st.markdown('<div class="mb-section">Exploration géospatiale</div>', unsafe_allow_html=True)
    st.header("Carte interactive des zones")
    st.caption("Clique sur une cellule pour consulter ses attributs. Filtre les niveaux pour isoler les zones à examiner.")
    levels = list(LEVEL_COLORS.keys())
    selected_levels = st.multiselect("Niveaux visibles", options=levels, default=levels,
        help="Le filtre modifie uniquement l'affichage de la carte, pas le calcul du score.")
    features = [feature for feature in risk.get("features", [])
        if feature.get("properties", {}).get("level") in selected_levels]
    map_data = {"type": "FeatureCollection", "features": features}
    m = folium.Map(location=[14.745, -17.36], zoom_start=11, tiles=None,
        control_scale=True, prefer_canvas=True)
    folium.TileLayer("CartoDB positron", name="Clair", control=True).add_to(m)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", control=True).add_to(m)
    folium.GeoJson(map_data, name="Niveaux de risque simulés",
        style_function=lambda f: {
            "fillColor": LEVEL_COLORS.get(f["properties"].get("level"), "#94a3b8"),
            "color": "#ffffff", "weight": 0.45, "fillOpacity": 0.68},
        highlight_function=lambda f: {"color": "#10233f", "weight": 2, "fillOpacity": 0.88},
        tooltip=folium.GeoJsonTooltip(
            fields=["zone_id", "sector", "score", "level", "population"],
            aliases=["Identifiant", "Secteur", "Score simulé", "Niveau", "Population"],
            sticky=True, localize=True),
        popup=folium.GeoJsonPopup(
            fields=["zone_id", "sector", "score", "level", "population"],
            aliases=["Zone", "Secteur", "Score simulé", "Niveau", "Population"],
            localize=True, labels=True)).add_to(m)
    folium.LayerControl(collapsed=True, position="topright").add_to(m)
    from folium.plugins import Fullscreen, MousePosition
    Fullscreen(position="topleft", title="Plein écran", title_cancel="Quitter le plein écran").add_to(m)
    MousePosition(position="bottomleft", separator=" | ", prefix="Coordonnées").add_to(m)
    st.markdown('<div class="mb-legend">' + "".join(
        f'<span class="mb-chip"><span style="color:{color}">●</span> {level.title()}</span>'
        for level, color in LEVEL_COLORS.items()) + '</div>', unsafe_allow_html=True)
    st_folium(m, height=690, use_container_width=True, returned_objects=[])
    st.caption(f"{len(features):,} cellules affichées sur {len(risk.get('features', [])):,}. "
        "Les couleurs représentent un scénario de risque synthétique, pas une mesure en temps réel.")

elif page == "Forecast":
    st.header("Évolution du risque dans le temps")
    data = api_get("/forecast", total_mm=rain)
    tl = pd.DataFrame(data["timeline"]).set_index("label")
    st.line_chart(tl[["global_score"]])
    st.line_chart(tl[["cumulative_rain_mm"]])
    st.dataframe(tl, width="stretch")
    st.caption(data["note"])

elif page == "Zones":
    st.header("Classement des zones")
    st.subheader("Par secteur")
    st.dataframe(pd.DataFrame(sim["sectors"]), width="stretch", hide_index=True)
    st.subheader("25 cellules les plus prioritaires")
    st.dataframe(pd.DataFrame(sim["top_zones"]), width="stretch", hide_index=True)

elif page == "Simulation":
    st.header("Comparer des scénarios de pluie")
    rows = []
    for p in PRESETS:
        s = get_simulation(float(p), 10, 5, 10)["summary"]
        rows.append({"pluie (mm)": p, "score global": s["global_score"], "niveau": s["global_level"],
                     "zones critiques": s["n_critical"], "population exposée": s["population_exposed"],
                     "routes à risque (km)": s["road_km_at_risk"]})
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.line_chart(pd.DataFrame(rows).set_index("pluie (mm)")[["zones critiques"]])
    st.info("Change la pluie dans la barre latérale pour voir la carte et le classement évoluer.")

elif page == "Resources":
    st.header("Priorisation des ressources (simulation algorithmique)")
    c1, c2, c3 = st.columns(3)
    pumps = c1.number_input("Pompes", 0, 1000, 10)
    teams = c2.number_input("Équipes de secours", 0, 1000, 5)
    vehicles = c3.number_input("Véhicules", 0, 1000, 10)
    res = get_simulation(rain, int(pumps), int(teams), int(vehicles))["resources"]
    st.dataframe(pd.DataFrame(res["allocation"]), width="stretch", hide_index=True)
    st.write("Restant non affecté :", res["remaining"])
    st.caption(res["note"])

elif page == "Alerts":
    st.header("Alertes")
    data = api_get("/alerts", rain_mm=rain)
    if not data["alerts"]:
        st.success("Aucune zone au niveau « très élevé » ou plus pour ce scénario.")
    for a in data["alerts"]:
        st.markdown(f"**{a['level'].upper()}** — {a['message']}  \n↳ {a['priority_proposed']}")


elif page == "Météo réelle":
    st.header("Prévisions horaires de précipitation — Dakar")
    st.caption(
        "Données du fournisseur Open-Meteo au point de référence configuré pour Dakar. "
        "Cette vue météo est indépendante des scores de risque synthétiques."
    )
    try:
        with st.spinner("Récupération des prévisions horaires…"):
            weather = get_weather_forecast()
    except requests.RequestException as exc:
        st.error(f"Impossible de récupérer les données météo réelles : {exc}")
        st.info(
            "Aucune donnée synthétique n'est utilisée en remplacement. "
            "Réessaie plus tard ou vérifie la connexion de l'API."
        )
    except (KeyError, TypeError, ValueError) as exc:
        st.error(f"La réponse météo reçue n'est pas exploitable : {exc}")
    else:
        st.caption(
            f"Source : {weather['source']} · "
            f"Récupérée le : {weather['retrieved_at_utc']} · "
            f"Origine : {weather['data_origin']}"
        )
        current = weather.get("current", {})
        c1, c2 = st.columns(2)
        precipitation = current.get("precipitation")
        c1.metric(
            "Précipitations actuelles",
            f"{float(precipitation):.1f} mm" if precipitation is not None else "Non disponible",
        )
        c2.metric(
            "Cumul des heures affichées",
            f"{weather['forecast_precipitation_total_mm']:.1f} mm",
        )
        weather_df = pd.DataFrame(weather.get("hourly", []))
        if weather_df.empty:
            st.warning("Le fournisseur n'a retourné aucune heure exploitable.")
        else:
            st.subheader("Précipitations horaires prévues (mm/h)")
            st.line_chart(weather_df.set_index("time")[["precipitation_mm"]])
            if "precipitation_probability_pct" in weather_df.columns:
                st.subheader("Probabilité de précipitation (%)")
                st.line_chart(
                    weather_df.set_index("time")[["precipitation_probability_pct"]]
                )
            st.dataframe(weather_df, width="stretch", hide_index=True)
        st.caption(weather["disclaimer"])
        st.caption("Attribution : Weather data by Open-Meteo (CC BY 4.0).")
