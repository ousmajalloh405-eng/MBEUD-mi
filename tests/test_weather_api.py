from datetime import datetime, timedelta

import pandas as pd
import requests
from fastapi.testclient import TestClient

from api.main import app
import api.weather as weather_api

client = TestClient(app)


def sample_payload():
    start = datetime(2026, 10, 12, 0, 0)
    times = [start + timedelta(hours=i) for i in range(31)]
    return {
        "timezone": "Africa/Dakar",
        "current": {
            "time": "2026-10-12T06:00",
            "interval": 900,
            "precipitation": 0.2,
            "rain": 0.2,
            "showers": 0.0,
        },
        "hourly": {
            "time": [value.strftime("%Y-%m-%dT%H:%M") for value in times],
            "precipitation": [0.5] * len(times),
            "precipitation_probability": [25] * len(times),
            "rain": [0.4] * len(times),
            "showers": [0.1] * len(times),
        },
    }


def test_weather_forecast_returns_provider_data(monkeypatch):
    monkeypatch.setattr(weather_api, "fetch_rain_window", lambda **kwargs: sample_payload())

    response = client.get("/api/v1/weather/forecast")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "Open-Meteo"
    assert body["data_origin"] == "LIVE_PROVIDER_DATA"
    assert body["location"]["name"] == "Point de référence Dakar"
    assert len(body["hourly"]) == 24
    assert body["forecast_precipitation_total_mm"] == 12.0
    assert body["hourly"][0]["time"] == "2026-10-12T06:00:00"
    assert "pas une image radar" in body["disclaimer"]


def test_weather_forecast_returns_502_on_provider_failure(monkeypatch):
    def fail(**kwargs):
        raise requests.Timeout("simulated timeout")

    monkeypatch.setattr(weather_api, "fetch_rain_window", fail)
    response = client.get("/api/v1/weather/forecast")

    assert response.status_code == 502
    assert "source météo" in response.json()["detail"].lower()


def test_weather_forecast_rejects_malformed_provider_response(monkeypatch):
    monkeypatch.setattr(weather_api, "fetch_rain_window", lambda **kwargs: {"hourly": {}})
    response = client.get("/api/v1/weather/forecast")

    assert response.status_code == 502
