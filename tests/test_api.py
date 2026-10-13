import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok" and r.json()["zones"] > 0


def test_zones_listing_and_limit():
    r = client.get("/zones", params={"limit": 5})
    assert r.status_code == 200 and len(r.json()["zones"]) == 5


def test_risk_geojson():
    r = client.get("/risk", params={"rain_mm": 100})
    body = r.json()
    assert r.status_code == 200 and body["type"] == "FeatureCollection"
    props = body["features"][0]["properties"]
    assert {"score", "level", "hazard", "vulnerability", "exposure"} <= set(props)
    assert body["summary"]["rain_mm"] == 100


def test_risk_zone_detail_and_404():
    zone_id = client.get("/zones", params={"limit": 1}).json()["zones"][0]["zone_id"]
    ok = client.get(f"/risk/{zone_id}", params={"rain_mm": 120})
    assert ok.status_code == 200 and ok.json()["recommendations"]
    assert client.get("/risk/NOPE").status_code == 404


@pytest.mark.parametrize("bad", [-5, 9999])
def test_rain_out_of_bounds_rejected(bad):
    assert client.get("/risk", params={"rain_mm": bad}).status_code == 422
    assert client.post("/simulation", json={"rain_mm": bad}).status_code == 422


def test_simulation_changes_with_rain():
    low = client.post("/simulation", json={"rain_mm": 50}).json()["summary"]
    high = client.post("/simulation", json={"rain_mm": 150}).json()["summary"]
    assert high["n_critical"] >= low["n_critical"]
    assert high["global_score"] > low["global_score"]


def test_simulation_resources_within_stock():
    body = client.post("/simulation", json={"rain_mm": 150, "pumps": 4, "teams": 2, "vehicles": 3}).json()
    alloc = body["resources"]["allocation"]
    assert sum(a["pumps"] for a in alloc) <= 4
    assert "ne remplace" in body["disclaimer"].lower()


def test_forecast_and_recommendations_and_alerts():
    tl = client.get("/forecast", params={"total_mm": 100}).json()["timeline"]
    assert len(tl) == 7
    assert "critique" in client.get("/recommendations").json()["recommendations"]
    assert client.get("/recommendations", params={"level": "inconnu"}).status_code == 404
    assert client.get("/alerts", params={"rain_mm": 150}).json()["alerts"]
