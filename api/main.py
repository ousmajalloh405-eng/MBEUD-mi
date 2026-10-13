"""API FastAPI du Flood Risk Senegal (prototype d'aide à la décision).

Documentation interactive : /docs (Swagger) et /redoc.
Toutes les réponses reposent sur des DONNÉES SYNTHÉTIQUES : voir 'data_origin'.
"""
from fastapi import FastAPI, HTTPException, Query

from api.schemas import SimulationRequest
from src.alerts.generate import generate_alerts
from src.config import settings
from src.risk_engine.recommendations import all_recommendations, recommendations_for
from src.risk_engine.resources import allocate
from src.risk_engine.scenarios import forecast_timeline, sector_ranking, run_scenario
from src.service import load_data, score_for, to_feature_collection

DATA_ORIGIN = "SYNTHETIC DATA — FOR DEMONSTRATION ONLY"
DISCLAIMER = ("Prototype d'aide à la décision sur données synthétiques. "
              "Ne remplace ni l'ANACIM, ni les autorités, ni les services d'urgence.")

app = FastAPI(
    title="Flood Risk Senegal API",
    version="0.1.0",
    description=DISCLAIMER,
)

RAIN = Query(None, ge=0, le=500, description="Pluie cumulée sur 24 h (mm). Défaut : valeur de config.")


def _rain(value: float | None) -> float:
    return float(value) if value is not None else float(settings()["weather"]["default_rain_mm"])


@app.get("/health", tags=["system"])
def health():
    df, _ = load_data()
    return {"status": "ok", "zones": int(len(df)), "data_origin": DATA_ORIGIN}


@app.get("/zones", tags=["zones"])
def zones(limit: int = Query(100, ge=1, le=5000), sector: str | None = None):
    """Liste des zones (sans géométrie) et de leurs attributs."""
    df, _ = load_data()
    if sector:
        df = df[df["sector"] == sector]
    return {"count": int(len(df)), "data_origin": DATA_ORIGIN,
            "zones": df.drop(columns=["data_origin"]).head(limit).to_dict(orient="records")}


@app.get("/risk", tags=["risk"])
def risk(rain_mm: float | None = RAIN):
    """Score de risque de toutes les zones, au format GeoJSON (prêt pour la carte)."""
    rain = _rain(rain_mm)
    scored, summary = score_for(rain)
    _, geoms = load_data()
    fc = to_feature_collection(scored, geoms)
    fc["summary"] = summary
    return fc


@app.get("/risk/{zone_id}", tags=["risk"])
def risk_zone(zone_id: str, rain_mm: float | None = RAIN):
    """Détail du risque d'une zone : les 3 blocs + recommandations."""
    rain = _rain(rain_mm)
    scored, _ = score_for(rain)
    row = scored[scored["zone_id"] == zone_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Zone inconnue : {zone_id}")
    rec = row.iloc[0].drop(labels=["data_origin"]).to_dict()
    rec = {k: (v.item() if hasattr(v, "item") else v) for k, v in rec.items()}
    return {"rain_mm": rain, "zone": rec, "recommendations": recommendations_for(rec["level"]),
            "data_origin": DATA_ORIGIN}


@app.get("/forecast", tags=["forecast"])
def forecast(total_mm: float | None = Query(None, ge=0, le=500, description="Pluie totale de l'épisode (mm)")):
    """Évolution du risque de T-24h à T+6h (courbe de pluie SYNTHÉTIQUE, pas une prévision)."""
    total = _rain(total_mm)
    df, _ = load_data()
    return {"total_mm": total, "timeline": forecast_timeline(df, total),
            "note": "Répartition temporelle de la pluie synthétique : sert à illustrer, pas à prévoir.",
            "data_origin": DATA_ORIGIN}


@app.get("/recommendations", tags=["recommendations"])
def recommendations(level: str | None = None):
    """Recommandations (priorités proposées) par niveau de risque."""
    if level:
        recs = recommendations_for(level)
        if not recs:
            raise HTTPException(status_code=404, detail=f"Niveau inconnu : {level}")
        return {"level": level, "recommendations": recs}
    return {"recommendations": all_recommendations(), "note": "Priorités proposées, pas des ordres."}


@app.get("/alerts", tags=["alerts"])
def alerts(rain_mm: float | None = RAIN, min_level: str = "très élevé", top_n: int = Query(20, ge=1, le=200)):
    rain = _rain(rain_mm)
    scored, _ = score_for(rain)
    return {"rain_mm": rain, "alerts": generate_alerts(scored, min_level, top_n)}


@app.post("/simulation", tags=["simulation"])
def simulation(req: SimulationRequest):
    """Simule un scénario de pluie : résumé, zones prioritaires, secteurs, ressources proposées."""
    df, _ = load_data()
    scored, summary = run_scenario(df, req.rain_mm)
    top = (scored.sort_values(["score", "population"], ascending=False).head(req.top_n)
           [["zone_id", "sector", "score", "level", "population"]].to_dict(orient="records"))
    sectors = sector_ranking(scored).to_dict(orient="records")
    return {
        "summary": summary,
        "top_zones": top,
        "sectors": sectors,
        "resources": allocate(scored, req.pumps, req.teams, req.vehicles),
        "data_origin": DATA_ORIGIN,
        "disclaimer": DISCLAIMER,
    }
