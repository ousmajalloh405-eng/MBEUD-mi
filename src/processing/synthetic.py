"""Génération de données SYNTHÉTIQUES pour la démonstration.

SYNTHETIC DATA — FOR DEMONSTRATION ONLY.

Ces données ne sont PAS des mesures. Elles imitent grossièrement la forme d'une
ville côtière (altitude qui monte vers l'intérieur, cuvettes, population dense
au centre) pour que le pipeline soit démontrable avant d'avoir les vraies données.
Les cuvettes sont placées à des endroits souvent cités comme sensibles : c'est
une indication générale, pas un jeu de données.
"""
import math

import numpy as np
import pandas as pd
from shapely.geometry import Point, mapping

from src.config import settings
from src.geospatial.grid import (KM_PER_DEG, LAND, build_grid, cell_area_km2)

DATA_LABEL = "SYNTHETIC DATA — FOR DEMONSTRATION ONLY"

# (lon, lat, profondeur en m, rayon en km)
BASINS = [
    (-17.39, 14.76, 9.0, 2.0),
    (-17.35, 14.745, 7.0, 1.8),
    (-17.31, 14.78, 8.0, 2.2),
    (-17.28, 14.72, 5.0, 1.5),
]
# (lon, lat, densité max hab/km2, échelle km)
URBAN_CORES = [(-17.40, 14.76, 22000, 9.0), (-17.27, 14.72, 9000, 3.0)]


def _dist_km(lon1, lat1, lon2, lat2) -> float:
    dx = (lon1 - lon2) * KM_PER_DEG * math.cos(math.radians(lat1))
    dy = (lat1 - lat2) * KM_PER_DEG
    return math.hypot(dx, dy)


def clean_elevation(lon: float, lat: float) -> float:
    """Altitude synthétique sans bruit : monte avec la distance à la côte, creusée par les cuvettes."""
    d_coast_km = LAND.exterior.distance(Point(lon, lat)) * KM_PER_DEG
    elev = 2.0 + 4.0 * d_coast_km
    for (bx, by, depth, sigma) in BASINS:
        d = _dist_km(lon, lat, bx, by)
        elev -= depth * math.exp(-(d ** 2) / (2 * sigma ** 2))
    return max(elev, 0.5)


def slope_deg(lon: float, lat: float, step: float = 0.0025) -> float:
    """Pente en degrés par différences finies sur l'altitude propre."""
    m_per_deg_lon = KM_PER_DEG * 1000 * math.cos(math.radians(lat))
    m_per_deg_lat = KM_PER_DEG * 1000
    dzdx = (clean_elevation(lon + step, lat) - clean_elevation(lon - step, lat)) / (2 * step * m_per_deg_lon)
    dzdy = (clean_elevation(lon, lat + step) - clean_elevation(lon, lat - step)) / (2 * step * m_per_deg_lat)
    return math.degrees(math.atan(math.hypot(dzdx, dzdy)))


def _density(lon: float, lat: float) -> float:
    dens = 400.0
    for (cx, cy, peak, scale) in URBAN_CORES:
        dens += peak * math.exp(-_dist_km(lon, lat, cx, cy) / scale)
    return dens


def build_dataset(cfg: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Construit (DataFrame des zones + attributs, dict zone_id -> géométrie GeoJSON)."""
    cfg = cfg or settings()
    rng = np.random.default_rng(cfg["synthetic"]["seed"])
    cell_m = cfg["grid"]["cell_size_m"]
    area = cell_area_km2(cell_m)
    zones = build_grid(cfg["grid"]["bbox"], cell_m)

    rows, geoms = [], {}
    for z in zones:
        lon, lat = z["lon"], z["lat"]
        elev = clean_elevation(lon, lat) + rng.normal(0, 0.8)
        elev = max(elev, 0.3)
        lowness = 1 - min(elev / 30.0, 1.0)
        history = float(np.clip(0.7 * lowness * rng.uniform(0.5, 1.0) + 0.1 * rng.random(), 0, 1))
        drainage = float(np.clip(0.75 - 0.5 * lowness + rng.normal(0, 0.12), 0, 1))
        density = _density(lon, lat) * float(rng.lognormal(0, 0.25))
        pop = int(density * area)
        rows.append({
            "zone_id": z["zone_id"], "row": z["row"], "col": z["col"],
            "lon": lon, "lat": lat, "sector": z["sector"],
            "area_km2": round(area, 4),
            "elevation_m": round(elev, 2),
            "slope_deg": round(slope_deg(lon, lat), 3),
            "flood_history": round(history, 3),
            "drainage_quality": round(drainage, 3),
            "population": pop,
            "hospitals": int(rng.poisson(pop / 40000)),
            "schools": int(rng.poisson(pop / 1500)),
            "markets": int(rng.poisson(pop / 6000)),
            "road_km": round(float(0.3 + 3.5 * (1 - math.exp(-density / 6000)) + rng.normal(0, 0.1)), 2),
            "data_origin": DATA_LABEL,
        })
        geoms[z["zone_id"]] = mapping(z["geometry"])
    df = pd.DataFrame(rows)
    df["road_km"] = df["road_km"].clip(lower=0)
    return df, geoms
