"""Test d'intégration : génération -> validation -> scoring -> API, bout en bout."""
from fastapi.testclient import TestClient

from api.main import app
from src.config import settings
from src.processing.synthetic import build_dataset
from src.processing.validation import validate_zones
from src.risk_engine.scenarios import run_scenario


def test_pipeline_end_to_end():
    df, geoms = build_dataset()
    assert validate_zones(df, settings()["grid"]["bbox"]).ok
    assert set(df["zone_id"]) == set(geoms)

    scored, summary = run_scenario(df, 120)
    assert summary["n_zones"] == len(df)

    client = TestClient(app)
    api_summary = client.post("/simulation", json={"rain_mm": 120}).json()["summary"]
    assert api_summary["n_critical"] == summary["n_critical"]  # même moteur, même résultat
    assert api_summary["population_exposed"] == summary["population_exposed"]


def test_synthetic_data_is_labelled():
    df, _ = build_dataset()
    assert (df["data_origin"] == "SYNTHETIC DATA — FOR DEMONSTRATION ONLY").all()
    assert client_label()


def client_label():
    return TestClient(app).get("/health").json()["data_origin"].startswith("SYNTHETIC DATA")
