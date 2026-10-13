"""Génère data/synthetic/zones.geojson (SYNTHETIC DATA — FOR DEMONSTRATION ONLY).

Usage : PYTHONPATH=. python scripts/generate_synthetic.py
"""
from src.config import resolve, settings
from src.processing.io import write_geojson
from src.processing.synthetic import build_dataset
from src.processing.validation import validate_zones


def main() -> None:
    cfg = settings()
    df, geoms = build_dataset(cfg)
    report = validate_zones(df, cfg["grid"]["bbox"])
    print(f"{len(df)} zones générées - validation OK : {report.ok}")
    for issue in report.issues:
        print(f"  [{issue.severity}] {issue.check} ({issue.column}): {issue.detail}")
    path = resolve(cfg["paths"]["synthetic_zones"])
    write_geojson(df, geoms, path)
    print(f"Écrit : {path}")


if __name__ == "__main__":
    main()
