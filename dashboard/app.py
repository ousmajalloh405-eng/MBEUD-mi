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

st.set_page_config(page_title="Flood Risk Senegal", page_icon="🌧️", layout="wide")


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
st.sidebar.title("🌧️ MBEUD-mi")
page = st.sidebar.radio("Page", ["Overview", "Risk Map", "Forecast", "Zones",
                                 "Simulation", "Resources", "Alerts", "Météo réelle"])
choice = st.sidebar.selectbox("Pluie prévue (24 h)", [f"{p} mm" for p in PRESETS] + ["Personnalisée"], index=2)
if choice == "Personnalisée":
    rain = st.sidebar.number_input("Pluie (mm)", min_value=0.0, max_value=500.0, value=100.0, step=5.0)
else:
    rain = float(choice.split()[0])
st.sidebar.caption("SYNTHETIC DATA — FOR DEMONSTRATION ONLY")

st.warning("Prototype pédagogique d'aide à la décision, sur données synthétiques. "
           "Ne remplace pas l'ANACIM, les autorités ni les services d'urgence. "
           "Les résultats sont des simulations, pas des prévisions officielles.")

try:
    risk = get_risk(rain)
    sim = get_simulation(rain, 10, 5, 10)
except Exception as exc:  # API pas encore prête, ou arrêtée
    st.error(f"Impossible de joindre l'API ({API_URL}) : {exc}")
    st.stop()

summary = risk["summary"]

if page == "Overview":
    st.header("Vue générale")
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
    st.header("Carte du risque")
    m = folium.Map(location=[14.745, -17.36], zoom_start=11, tiles="OpenStreetMap")
    folium.GeoJson(
        risk,
        style_function=lambda f: {"fillColor": LEVEL_COLORS.get(f["properties"]["level"], "#999"),
                                  "color": "none", "fillOpacity": 0.6},
        tooltip=folium.GeoJsonTooltip(fields=["zone_id", "sector", "score", "level", "population"],
                                      aliases=["Zone", "Secteur", "Score", "Niveau", "Population"]),
    ).add_to(m)
    st_folium(m, height=600, use_container_width=True, returned_objects=[])
    st.caption("Légende : " + " · ".join(f"**{k}**" for k in LEVEL_COLORS) + " (du plus faible au plus critique)")

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
