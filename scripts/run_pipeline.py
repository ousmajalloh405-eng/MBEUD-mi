"""Pipeline complet en ligne de commande : charger -> valider -> scorer -> exporter.

Usage : PYTHONPATH=. python scripts/run_pipeline.py --rain 120
"""
import argparse

from src.alerts.generate import generate_alerts
from src.config import resolve, settings
from src.processing.validation import validate_zones
from src.service import load_data
from src.risk_engine.scenarios import run_scenario


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--rain", type=float, default=settings()["weather"]["default_rain_mm"])
    args = p.parse_args()

    df, _ = load_data()
    report = validate_zones(df, settings()["grid"]["bbox"])
    if not report.ok:
        raise SystemExit(f"Données invalides : {report.to_dict()}")

    scored, summary = run_scenario(df, args.rain)
    out_dir = resolve(settings()["paths"]["processed_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"risk_{int(args.rain)}mm.csv"
    scored.drop(columns=["data_origin"], errors="ignore").to_csv(out, index=False)

    print(f"Scénario {args.rain} mm - score global {summary['global_score']} ({summary['global_level']})")
    print(f"Zones par niveau : {summary['level_counts']}")
    print(f"Population exposée (>= élevé) : {summary['population_exposed']}")
    print(f"Alertes (>= très élevé) : {len(generate_alerts(scored))} (top 20)")
    print(f"Écrit : {out}")


if __name__ == "__main__":
    main()
