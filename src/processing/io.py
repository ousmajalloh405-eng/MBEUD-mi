"""Lecture / écriture du fichier GeoJSON des zones."""
import json
from pathlib import Path

import pandas as pd


def write_geojson(df: pd.DataFrame, geoms: dict, path: Path) -> None:
    features = []
    for rec in df.to_dict(orient="records"):
        features.append({
            "type": "Feature",
            "geometry": geoms[rec["zone_id"]],
            "properties": rec,
        })
    fc = {
        "type": "FeatureCollection",
        "name": "zones",
        "metadata": {"data_origin": "SYNTHETIC DATA — FOR DEMONSTRATION ONLY"},
        "features": features,
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")


def read_geojson(path: Path) -> tuple[pd.DataFrame, dict]:
    fc = json.loads(Path(path).read_text(encoding="utf-8"))
    rows, geoms = [], {}
    for feat in fc["features"]:
        rows.append(feat["properties"])
        geoms[feat["properties"]["zone_id"]] = feat["geometry"]
    return pd.DataFrame(rows), geoms
