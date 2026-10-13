"""Découpage du territoire en cellules (grille régulière).

Pourquoi une grille ? Elle permet de calculer le risque finement, puis de
regrouper par secteur pour l'affichage (voir docs/decisions.md).

ATTENTION : le polygone ``LAND`` ci-dessous est un contour TRÈS APPROXIMATIF
dessiné à la main pour le prototype. Ce n'est PAS une limite administrative
officielle. À remplacer par les vraies limites (HDX / OpenStreetMap) en V3.
"""
import math

from shapely.geometry import Point, Polygon, box

# (longitude, latitude) - contour approximatif de la terre ferme, SYNTHETIC / DEMO
LAND = Polygon([
    (-17.54, 14.745), (-17.48, 14.768), (-17.42, 14.795), (-17.35, 14.82),
    (-17.25, 14.85), (-17.15, 14.85), (-17.15, 14.69), (-17.20, 14.70),
    (-17.27, 14.715), (-17.30, 14.725), (-17.37, 14.74), (-17.40, 14.715),
    (-17.42, 14.69), (-17.43, 14.668), (-17.46, 14.672), (-17.50, 14.70),
])

# Repères INDICATIFS (coordonnées approximatives) pour étiqueter les secteurs.
LOCALITIES = {
    "Dakar-Plateau": (-17.435, 14.675),
    "Ouakam / Ngor": (-17.49, 14.72),
    "Almadies": (-17.52, 14.745),
    "Yoff": (-17.485, 14.765),
    "Parcelles-Assainies": (-17.44, 14.76),
    "Pikine": (-17.39, 14.755),
    "Guédiawaye": (-17.395, 14.775),
    "Thiaroye": (-17.35, 14.745),
    "Keur Massar": (-17.31, 14.78),
    "Malika": (-17.33, 14.80),
    "Rufisque": (-17.27, 14.72),
    "Diamniadio": (-17.18, 14.72),
}

KM_PER_DEG = 111.32


def cell_size_degrees(cell_size_m: float, lat0: float) -> tuple[float, float]:
    """Convertit une taille en mètres en degrés (lon, lat) à la latitude lat0."""
    dlat = cell_size_m / (KM_PER_DEG * 1000)
    dlon = cell_size_m / (KM_PER_DEG * 1000 * math.cos(math.radians(lat0)))
    return dlon, dlat


def cell_area_km2(cell_size_m: float) -> float:
    return (cell_size_m / 1000) ** 2


def nearest_locality(lon: float, lat: float) -> str:
    def dist(item):
        (x, y) = item[1]
        return math.hypot((lon - x) * math.cos(math.radians(lat)), lat - y)

    return min(LOCALITIES.items(), key=dist)[0]


def build_grid(bbox: dict, cell_size_m: float, land: Polygon = LAND) -> list[dict]:
    """Crée les cellules dont le centre est sur la terre ferme.

    Retourne une liste de dicts : zone_id, row, col, lon, lat, sector, geometry.
    """
    lat0 = (bbox["lat_min"] + bbox["lat_max"]) / 2
    dlon, dlat = cell_size_degrees(cell_size_m, lat0)
    n_cols = math.ceil((bbox["lon_max"] - bbox["lon_min"]) / dlon)
    n_rows = math.ceil((bbox["lat_max"] - bbox["lat_min"]) / dlat)

    zones = []
    for r in range(n_rows):
        for c in range(n_cols):
            x0 = bbox["lon_min"] + c * dlon
            y0 = bbox["lat_min"] + r * dlat
            cell = box(x0, y0, x0 + dlon, y0 + dlat)
            centre = cell.centroid
            if land.contains(Point(centre.x, centre.y)):
                zones.append({
                    "zone_id": f"Z-{r:03d}-{c:03d}",
                    "row": r,
                    "col": c,
                    "lon": round(centre.x, 5),
                    "lat": round(centre.y, 5),
                    "sector": nearest_locality(centre.x, centre.y),
                    "geometry": cell,
                })
    return zones
