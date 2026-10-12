"""Routes météo expérimentales alimentées par Open-Meteo."""

from datetime import datetime, timezone

import pandas as pd
import requests
from fastapi import APIRouter, HTTPException

from src.config import settings
from src.ingestion.open_meteo import fetch_rain_window, parse_hourly
from src.processing.validation import validate_weather

router = APIRouter(prefix="/api/v1/weather", tags=["weather"])


@router.get("/forecast")
def rain_forecast():
    """Prévisions horaires au point de référence configuré pour Dakar.

    Cette route sert de première intégration réelle. Elle ne renvoie pas de
    radar animé, de prévision hydrologique ou d'alerte officielle.
    """
    cfg = settings()["weather"]
    latitude = float(cfg["latitude"])
    longitude = float(cfg["longitude"])

    try:
        payload = fetch_rain_window(latitude=latitude, longitude=longitude)
        hourly = parse_hourly(payload)
    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="La source météo n'est pas disponible ou sa réponse est invalide.",
        ) from exc

    validation = validate_weather(hourly)
    if not validation.ok:
        raise HTTPException(
            status_code=502,
            detail="La réponse météo a échoué aux contrôles de qualité.",
        )

    current = payload.get("current") or {}
    try:
        current_time = pd.to_datetime(current["time"])
        future = hourly.loc[hourly["time"] >= current_time].head(24).copy()
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="La réponse météo ne contient pas d'heure courante exploitable.",
        )

    if future.empty:
        raise HTTPException(
            status_code=502,
            detail="La source météo n'a pas fourni d'heures de prévision exploitables.",
        )

    future["time"] = future["time"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    forecast_rows = []
    raw_hourly = payload.get("hourly", {})
    probabilities = raw_hourly.get("precipitation_probability", [])
    rains = raw_hourly.get("rain", [])
    showers = raw_hourly.get("showers", [])

    for index, row in future.iterrows():
        original_index = hourly.index.get_loc(index)
        item = {
            "time": row["time"],
            "precipitation_mm": float(row["precipitation_mm"]),
        }
        if original_index < len(probabilities):
            item["precipitation_probability_pct"] = probabilities[original_index]
        if original_index < len(rains):
            item["rain_mm"] = rains[original_index]
        if original_index < len(showers):
            item["showers_mm"] = showers[original_index]
        forecast_rows.append(item)

    current_summary = {
        key: current[key]
        for key in ("time", "interval", "precipitation", "rain", "showers")
        if key in current
    }

    return {
        "source": "Open-Meteo",
        "attribution": "Weather data by Open-Meteo",
        "data_origin": "LIVE_PROVIDER_DATA",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "location": {
            "name": "Point de référence Dakar",
            "latitude": latitude,
            "longitude": longitude,
            "timezone": payload.get("timezone", "Africa/Dakar"),
        },
        "current": current_summary,
        "hourly": forecast_rows,
        "forecast_hours_available": len(forecast_rows),
        "forecast_precipitation_total_mm": round(
            sum(row["precipitation_mm"] for row in forecast_rows), 2
        ),
        "disclaimer": (
            "Prévision météorologique au point de référence, fournie par un service tiers. "
            "Ce résultat n'est ni une image radar, ni une observation locale garantie, "
            "ni une prévision d'inondation validée, ni une alerte officielle. "
            "Ne pas l'utiliser seul pour décider d'une intervention d'urgence."
        ),
    }
