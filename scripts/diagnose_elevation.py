"""Diagnostic de couverture de l'altitude et de la pente du MNE."""

from collections import Counter
from math import atan, degrees, hypot

import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import transform
from rasterio.windows import Window

from src.config import resolve, settings
from src.geospatial.grid import build_grid


RASTER_PATH = resolve("data/raw/Dakar_MNE_5m.tif")
OUTPUT_PATH = resolve("data/processed/elevation_coverage.csv")


def is_valid(value, nodata):
    """Vérifie qu'un pixel contient une valeur numérique valide."""
    if np.ma.is_masked(value):
        return False

    value = float(value)

    if not np.isfinite(value):
        return False

    return nodata is None or value != nodata


def main():
    cfg = settings()
    zones = build_grid(
        cfg["grid"]["bbox"],
        cfg["grid"]["cell_size_m"],
    )

    rows = []

    with rasterio.open(RASTER_PATH) as raster:
        for zone in zones:
            lon, lat = zone["lon"], zone["lat"]

            x, y = transform(
                "EPSG:4326",
                raster.crs,
                [lon],
                [lat],
            )
            px, py = x[0], y[0]

            result = {
                "zone_id": zone["zone_id"],
                "lon": lon,
                "lat": lat,
                "elevation_m": None,
                "elevation_status": None,
                "slope_deg": None,
                "slope_status": None,
            }

            inside = (
                raster.bounds.left <= px < raster.bounds.right
                and raster.bounds.bottom < py <= raster.bounds.top
            )

            if not inside:
                result["elevation_status"] = "outside_coverage"
                result["slope_status"] = "outside_coverage"
                rows.append(result)
                continue

            sample = next(
                raster.sample([(px, py)], masked=True)
            )[0]

            if not is_valid(sample, raster.nodata):
                result["elevation_status"] = "nodata"
                result["slope_status"] = "nodata"
                rows.append(result)
                continue

            result["elevation_m"] = float(sample)
            result["elevation_status"] = "real"

            row_idx, col_idx = raster.index(px, py)

            # Une pente centrale nécessite un pixel de chaque côté.
            if (
                row_idx < 1
                or row_idx >= raster.height - 1
                or col_idx < 1
                or col_idx >= raster.width - 1
            ):
                result["slope_status"] = "edge_of_raster"
                rows.append(result)
                continue

            pixels = raster.read(
                1,
                window=Window(col_idx - 1, row_idx - 1, 3, 3),
                masked=True,
            )

            neighbors = {
                "west": pixels[1, 0],
                "east": pixels[1, 2],
                "north": pixels[0, 1],
                "south": pixels[2, 1],
            }

            if not all(
                is_valid(value, raster.nodata)
                for value in neighbors.values()
            ):
                result["slope_status"] = "nodata_neighbors"
                rows.append(result)
                continue

            west = float(neighbors["west"])
            east = float(neighbors["east"])
            north = float(neighbors["north"])
            south = float(neighbors["south"])

            dx = abs(raster.res[0])
            dy = abs(raster.res[1])

            if dx == 0 or dy == 0:
                raise ValueError("Résolution du raster invalide.")

            dzdx = (east - west) / (2 * dx)
            dzdy = (south - north) / (2 * dy)

            slope = degrees(atan(hypot(dzdx, dzdy)))

            result["slope_deg"] = float(slope)
            result["slope_status"] = "real"
            rows.append(result)

    df = pd.DataFrame(rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Rapport créé : {OUTPUT_PATH}")
    print(f"Nombre total de zones : {len(df)}")

    print("\nStatuts des altitudes :")
    for status, count in Counter(df["elevation_status"]).items():
        print(f"  {status}: {count}")

    print("\nStatuts des pentes :")
    for status, count in Counter(df["slope_status"]).items():
        print(f"  {status}: {count}")

    for column, status_column, label in [
        ("elevation_m", "elevation_status", "Altitudes"),
        ("slope_deg", "slope_status", "Pentes"),
    ]:
        values = df.loc[
            df[status_column] == "real",
            column,
        ]

        if not values.empty:
            print(f"\nStatistiques des {label.lower()} valides :")
            print(f"  Nombre : {len(values)}")
            print(f"  Minimum : {values.min():.3f}")
            print(f"  Maximum : {values.max():.3f}")
            print(f"  Moyenne : {values.mean():.3f}")


if __name__ == "__main__":
    main()
