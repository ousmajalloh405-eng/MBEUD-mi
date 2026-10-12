"""Ingestion de la météo depuis Open-Meteo (API gratuite, usage non commercial, CC BY 4.0).

Source : https://open-meteo.com  (attribution : "Weather data by Open-Meteo").
Données : précipitations horaires prévues (mm).

NOTE : ce module n'a pas pu être testé en conditions réelles dans l'environnement de
construction (pas d'accès à api.open-meteo.com). Seul `parse_hourly` est testé, avec
un exemple de réponse. Teste `fetch_forecast` toi-même sur ta machine.
Principe d'ingestion : on SAUVEGARDE la réponse brute dans data/raw, sans la modifier.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from src.config import resolve, settings

API_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_forecast(latitude: float | None = None, longitude: float | None = None,
                   forecast_days: int = 2, timeout: int = 20) -> dict:
    cfg = settings()["weather"]
    params = {
        "latitude": latitude if latitude is not None else cfg["latitude"],
        "longitude": longitude if longitude is not None else cfg["longitude"],
        "hourly": "precipitation",
        "forecast_days": forecast_days,
        "timezone": "UTC",
    }
    resp = requests.get(API_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def save_raw(payload: dict) -> Path:
    raw_dir = resolve(settings()["paths"]["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = raw_dir / f"open_meteo_{stamp}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def parse_hourly(payload: dict) -> pd.DataFrame:
    """Réponse JSON -> DataFrame (time, precipitation_mm)."""
    hourly = payload["hourly"]
    return pd.DataFrame({"time": pd.to_datetime(hourly["time"]),
                         "precipitation_mm": hourly["precipitation"]})


def total_next_24h(df: pd.DataFrame) -> float:
    """Cumul de pluie sur les 24 premières heures de la série."""
    return float(df["precipitation_mm"].head(24).sum())


def fetch_rain_window(latitude: float | None = None, longitude: float | None = None,
                      forecast_hours: int = 24, past_hours: int = 6,
                      timeout: int = 20) -> dict:
    """Récupère le contexte pluviométrique récent et les prochaines heures.

    Les valeurs passées proviennent des données météorologiques du fournisseur,
    pas d'une image radar. Elles ne constituent pas une observation locale garantie.
    """
    if not 1 <= forecast_hours <= 48:
        raise ValueError("forecast_hours doit être compris entre 1 et 48")
    if not 0 <= past_hours <= 24:
        raise ValueError("past_hours doit être compris entre 0 et 24")

    cfg = settings()["weather"]
    params = {
        "latitude": latitude if latitude is not None else cfg["latitude"],
        "longitude": longitude if longitude is not None else cfg["longitude"],
        "current": "precipitation,rain,showers",
        "hourly": "precipitation,precipitation_probability,rain,showers",
        "forecast_hours": forecast_hours,
        "past_hours": past_hours,
        "timezone": "Africa/Dakar",
    }
    resp = requests.get(API_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
