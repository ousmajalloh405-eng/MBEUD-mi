"""Charge zones, attributs, un scénario de risque et les recommandations dans PostGIS.

Prérequis : `docker compose up -d db` puis `pip install -r requirements/etl.txt`.
Usage     : PYTHONPATH=. python scripts/load_to_postgis.py --rain 120

NOTE : ce script n'a pas pu être exécuté contre une vraie base dans l'environnement de
construction (voir README, section Limitations). Teste-le chez toi et corrige si besoin.
"""
import argparse
import json
import os

from sqlalchemy import create_engine, text

from src.config import reco_config, settings
from src.risk_engine.scenarios import run_scenario
from src.service import load_data


def db_url() -> str:
    return "postgresql+psycopg2://{u}:{p}@{h}:{port}/{d}".format(
        u=os.environ.get("POSTGRES_USER", "flood_user"),
        p=os.environ.get("POSTGRES_PASSWORD", "change_me"),
        h=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5433"),
        d=os.environ.get("POSTGRES_DB", "flood_risk"),
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--rain", type=float, default=settings()["weather"]["default_rain_mm"])
    args = p.parse_args()

    df, geoms = load_data()
    scored, summary = run_scenario(df, args.rain)
    engine = create_engine(db_url())

    with engine.begin() as conn:
        for rec in df.to_dict(orient="records"):
            conn.execute(text("""
                INSERT INTO zones (zone_id, sector, area_km2, geom)
                VALUES (:zone_id, :sector, :area_km2, ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326))
                ON CONFLICT (zone_id) DO UPDATE SET sector = EXCLUDED.sector, geom = EXCLUDED.geom
            """), {"zone_id": rec["zone_id"], "sector": rec["sector"], "area_km2": rec["area_km2"],
                   "geom": json.dumps(geoms[rec["zone_id"]])})
            conn.execute(text("""
                INSERT INTO zone_features (zone_id, elevation_m, slope_deg, flood_history, drainage_quality,
                                           population, hospitals, schools, markets, road_km, data_origin)
                VALUES (:zone_id, :elevation_m, :slope_deg, :flood_history, :drainage_quality,
                        :population, :hospitals, :schools, :markets, :road_km, :data_origin)
                ON CONFLICT (zone_id) DO UPDATE SET elevation_m = EXCLUDED.elevation_m,
                    population = EXCLUDED.population, road_km = EXCLUDED.road_km
            """), rec)

        scenario_id = conn.execute(
            text("INSERT INTO scenarios (rain_mm, method) VALUES (:r, :m) RETURNING scenario_id"),
            {"r": args.rain, "m": "weighted_sum"}).scalar_one()
        conn.execute(text("""
            INSERT INTO risk_scores (scenario_id, zone_id, hazard, vulnerability, exposure, score, level)
            VALUES (:sid, :zone_id, :hazard, :vulnerability, :exposure, :score, :level)
        """), [{"sid": scenario_id, **{k: r[k] for k in
                ("zone_id", "hazard", "vulnerability", "exposure", "score", "level")}}
               for r in scored.to_dict(orient="records")])

        for level, actions in reco_config()["levels"].items():
            conn.execute(text("""
                INSERT INTO recommendations (level, actions) VALUES (:l, :a)
                ON CONFLICT (level) DO UPDATE SET actions = EXCLUDED.actions
            """), {"l": level, "a": actions})

    print(f"Chargé : {len(df)} zones, scénario #{scenario_id} ({args.rain} mm), "
          f"{summary['n_critical']} zones critiques.")


if __name__ == "__main__":
    main()
