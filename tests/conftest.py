import pandas as pd
import pytest

from src.processing.synthetic import build_dataset


@pytest.fixture(scope="session")
def dataset():
    df, geoms = build_dataset()
    return df, geoms


@pytest.fixture
def three_zones():
    """3 zones faites à la main : sûre, moyenne, très exposée (calculs vérifiables)."""
    return pd.DataFrame([
        {"zone_id": "A", "lon": -17.4, "lat": 14.7, "sector": "S", "elevation_m": 25, "slope_deg": 0.6,
         "flood_history": 0.0, "drainage_quality": 1.0, "population": 100, "hospitals": 0,
         "schools": 0, "markets": 0, "road_km": 0.5},
        {"zone_id": "B", "lon": -17.4, "lat": 14.7, "sector": "S", "elevation_m": 10, "slope_deg": 0.2,
         "flood_history": 0.4, "drainage_quality": 0.5, "population": 3000, "hospitals": 0,
         "schools": 2, "markets": 1, "road_km": 2.0},
        {"zone_id": "C", "lon": -17.4, "lat": 14.7, "sector": "S", "elevation_m": 1, "slope_deg": 0.0,
         "flood_history": 0.9, "drainage_quality": 0.1, "population": 9000, "hospitals": 2,
         "schools": 8, "markets": 4, "road_km": 4.0},
    ])
