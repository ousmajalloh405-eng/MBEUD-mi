"""Lecture du modèle numérique d'élévation (MNE) de Dakar."""
import math
import numpy as np
from rasterio.windows import Window
from pathlib import Path

import rasterio
from rasterio.warp import transform


DEFAULT_RASTER_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
    / "Dakar_MNE_5m.tif"
)


def get_elevation(lon: float, lat: float, raster_path: str | Path | None = None) -> float | None:
    """Retourne l'altitude d'un point, ou None si aucune donnée valide."""
    path = Path(raster_path) if raster_path else DEFAULT_RASTER_PATH

    if not path.exists():
        raise FileNotFoundError(f"Raster MNE introuvable : {path}")

    with rasterio.open(path) as raster:
        x, y = transform(
            "EPSG:4326",
            raster.crs,
            [lon],
            [lat],
        )

        px, py = x[0], y[0]

        if not (
            raster.bounds.left <= px < raster.bounds.right
            and raster.bounds.bottom < py <= raster.bounds.top
        ):
            return None

        value = next(raster.sample([(px, py)]))[0]

        if value == raster.nodata:
            return None

        return float(value)
def get_slope(
    lon: float,
    lat: float,
    raster_path: str | Path | None = None,
) -> float | None:
    """Estime la pente locale en degrés à partir des pixels voisins du MNE."""
    path = Path(raster_path) if raster_path else DEFAULT_RASTER_PATH

    if not path.exists():
        raise FileNotFoundError(f"Raster MNE introuvable : {path}")

    with rasterio.open(path) as raster:
        x, y = transform("EPSG:4326", raster.crs, [lon], [lat])
        px, py = x[0], y[0]

        if not (
            raster.bounds.left <= px < raster.bounds.right
            and raster.bounds.bottom < py <= raster.bounds.top
        ):
            return None

        row, col = raster.index(px, py)

        # Il faut disposer des pixels voisins dans les quatre directions.
        if (
            row < 1
            or row >= raster.height - 1
            or col < 1
            or col >= raster.width - 1
        ):
            return None

        window = Window(col - 1, row - 1, 3, 3)
        pixels = raster.read(1, window=window, masked=True)

        # Centre, ouest, est, nord et sud doivent tous être valides.
        required = [
            pixels[1, 1],
            pixels[1, 0],
            pixels[1, 2],
            pixels[0, 1],
            pixels[2, 1],
        ]

        if any(
            np.ma.is_masked(value)
            or not math.isfinite(float(value))
            for value in required
        ):
            return None

        west = float(pixels[1, 0])
        east = float(pixels[1, 2])
        north = float(pixels[0, 1])
        south = float(pixels[2, 1])

        dx = abs(raster.res[0])
        dy = abs(raster.res[1])

        if dx == 0 or dy == 0:
            raise ValueError("Résolution du raster invalide.")

        dzdx = (east - west) / (2 * dx)
        dzdy = (south - north) / (2 * dy)

        slope = math.degrees(math.atan(math.hypot(dzdx, dzdy)))
        return float(slope)
