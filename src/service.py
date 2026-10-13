"""Couche de service : charge les données et calcule les scénarios pour l'API.

MVP : les données viennent du fichier GeoJSON (data/synthetic). Le chargement vers
PostGIS est fourni (scripts/load_to_postgis.py) ; l'API lira PostGIS en V3.
"""
from functools import lru_cache

import pandas as pd

from src.config import resolve, settings
from src.processing.io import read_geojson, write_geojson
from src.processing.synthetic import build_dataset
from src.risk_engine.scenarios import run_scenario


@lru_cache
def load_data() -> tuple[pd.DataFrame, dict]:
    path = resolve(settings()["paths"]["synthetic_zones"])
    if not path.exists():  # première exécution : on génère les données de démo
        df, geoms = build_dataset()
        write_geojson(df, geoms, path)
    return read_geojson(path)


def score_for(rain_mm: float) -> tuple[pd.DataFrame, dict]:
    df, _ = load_data()
    return run_scenario(df, rain_mm)


def to_feature_collection(scored: pd.DataFrame, geoms: dict) -> dict:
    cols = ["zone_id", "sector", "hazard", "vulnerability", "exposure", "score", "level",
            "population", "hospitals", "schools", "markets", "road_km", "elevation_m"]
    features = [{
        "type": "Feature",
        "geometry": geoms[rec["zone_id"]],
        "properties": rec,
    } for rec in scored[cols].to_dict(orient="records")]
    return {"type": "FeatureCollection", "features": features,
            "metadata": {"data_origin": "SYNTHETIC DATA — FOR DEMONSTRATION ONLY"}}
