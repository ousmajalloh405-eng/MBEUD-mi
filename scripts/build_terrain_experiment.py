"""Construit un jeu expérimental utilisant le relief du MNE de Dakar.

Les variables non liées au relief restent synthétiques.
Ce jeu expérimental ne remplace pas les données du dashboard.
"""

import json

import pandas as pd

from src.config import resolve, settings
from src.processing.io import read_geojson


BASE_PATH = resolve(settings()["paths"]["synthetic_zones"])
COVERAGE_PATH = resolve("data/processed/elevation_coverage.csv")
OUTPUT_PATH = resolve("data/processed/terrain_experimental_zones.csv")
METADATA_PATH = resolve("data/processed/terrain_experimental_metadata.json")


def main():
    # 1. Vérifier la présence des fichiers nécessaires.
    if not BASE_PATH.exists():
        raise FileNotFoundError(
            f"GeoJSON de démonstration introuvable : {BASE_PATH}"
        )

    if not COVERAGE_PATH.exists():
        raise FileNotFoundError(
            f"Diagnostic du MNE introuvable : {COVERAGE_PATH}. "
            "Exécute d'abord scripts/diagnose_elevation.py."
        )

    # 2. Charger les données de démonstration et le diagnostic du MNE.
    base, _ = read_geojson(BASE_PATH)
    terrain = pd.read_csv(COVERAGE_PATH)

    if not base["zone_id"].is_unique:
        raise ValueError("Le GeoJSON contient des zone_id en double.")

    if not terrain["zone_id"].is_unique:
        raise ValueError("Le diagnostic contient des zone_id en double.")

    terrain_columns = [
        "zone_id",
        "lon",
        "lat",
        "elevation_m",
        "elevation_status",
        "slope_deg",
        "slope_status",
    ]

    missing_columns = [
        column for column in terrain_columns
        if column not in terrain.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Colonnes manquantes dans le diagnostic : {missing_columns}"
        )

    # 3. Associer les zones par identifiant.
    merged = base.merge(
        terrain[terrain_columns],
        on="zone_id",
        how="outer",
        suffixes=("_synthetic", "_terrain"),
        indicator=True,
        validate="one_to_one",
    )

    unmatched = merged["_merge"] != "both"
    if unmatched.any():
        raise ValueError(
            f"{int(unmatched.sum())} zones ne correspondent pas "
            "entre le GeoJSON et le diagnostic."
        )

    # 4. Vérifier que les coordonnées correspondent.
    lon_diff = (
        merged["lon_synthetic"] - merged["lon_terrain"]
    ).abs()
    lat_diff = (
        merged["lat_synthetic"] - merged["lat_terrain"]
    ).abs()

    if ((lon_diff > 1e-7) | (lat_diff > 1e-7)).any():
        raise ValueError(
            "Les coordonnées diffèrent entre les deux fichiers."
        )

    # 5. Garder uniquement les zones avec altitude et pente valides.
    valid = (
        (merged["elevation_status"] == "real")
        & (merged["slope_status"] == "real")
        & merged["elevation_m_terrain"].notna()
        & merged["slope_deg_terrain"].notna()
    )

    experiment = merged.loc[valid].copy()

    if experiment.empty:
        raise ValueError(
            "Aucune zone ne possède une altitude et une pente valides."
        )

    # 6. Garder les anciennes valeurs de relief pour comparaison.
    experiment["elevation_m_synthetic_reference"] = (
        experiment["elevation_m_synthetic"]
    )
    experiment["slope_deg_synthetic_reference"] = (
        experiment["slope_deg_synthetic"]
    )

    # Les variables principales de relief utilisent maintenant le MNE.
    experiment["elevation_m"] = experiment["elevation_m_terrain"]
    experiment["slope_deg"] = experiment["slope_deg_terrain"]

    # Conserver les coordonnées originales et nettoyer les colonnes auxiliaires.
    experiment = experiment.rename(
        columns={
            "lon_synthetic": "lon",
            "lat_synthetic": "lat",
        }
    )

    experiment = experiment.drop(
        columns=[
            "lon_terrain",
            "lat_terrain",
            "elevation_m_synthetic",
            "slope_deg_synthetic",
            "elevation_m_terrain",
            "slope_deg_terrain",
            "_merge",
        ]
    )

    # 7. Rendre la provenance visible dans chaque ligne.
    experiment["terrain_source"] = "data/raw/Dakar_MNE_5m.tif"

    experiment["terrain_method"] = (
        "Altitude extraite au centre de la zone ; "
        "pente calculée par différences centrales à partir "
        "des pixels voisins du raster."
    )

    experiment["other_variables_origin"] = (
        "SYNTHETIC DATA — FOR DEMONSTRATION ONLY"
    )

    experiment["data_origin"] = (
        "MIXED DATA — relief issu du MNE ; "
        "autres variables synthétiques ; sous-ensemble expérimental"
    )

    # 8. Enregistrer le jeu expérimental séparément du dashboard.
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    experiment.to_csv(OUTPUT_PATH, index=False)

    # 9. Documenter les sources, les méthodes et les incertitudes.
    metadata = {
        "dataset": str(OUTPUT_PATH),
        "source_raster": "data/raw/Dakar_MNE_5m.tif",
        "synthetic_source": str(BASE_PATH),
        "coverage_diagnostic": str(COVERAGE_PATH),

        "source_provider": (
            "ANAT, organisme indiqué dans le catalogue Géo Sénégal"
        ),
        "source_catalog_title": "Dakar elevation 5 m — Géo Sénégal",
        "source_catalog_url": (
            "https://geosenegal.gouv.sn/Dakar-elevation-5-m.html"
        ),
        "source_product_scale": (
            "1:2000, selon la description du produit consultée ; "
            "à confirmer pour ce fichier précis"
        ),

        "horizontal_crs": "EPSG:32628",
        "nominal_spatial_resolution_m": 5,
        "nodata_value": -9999.0,

        "vertical_units": (
            "Non spécifiées dans les métadonnées intégrées au GeoTIFF ; "
            "à confirmer dans la documentation technique de la source"
        ),
        "vertical_reference": (
            "Non vérifié dans les métadonnées disponibles"
        ),
        "vertical_accuracy": (
            "Non documentée dans les métadonnées consultées"
        ),

        "elevation_extraction_method": (
            "Échantillonnage du pixel du MNE au centre de chaque zone"
        ),
        "slope_calculation_method": (
            "Différences centrales à partir des pixels ouest, est, nord "
            "et sud ; résolution nominale de 5 m ; pente indisponible "
            "si un pixel nécessaire est NoData"
        ),

        "total_grid_zones": int(len(base)),
        "zones_with_valid_elevation_and_slope": int(len(experiment)),
        "zones_excluded": int(len(base) - len(experiment)),
        "coverage_percent": round(
            100 * len(experiment) / len(base), 2
        ),

        "terrain_variables": [
            "elevation_m",
            "slope_deg",
        ],

        "synthetic_variables": [
            "flood_history",
            "drainage_quality",
            "population",
            "hospitals",
            "schools",
            "markets",
            "road_km",
        ],

        "altitude_min_m": float(experiment["elevation_m"].min()),
        "altitude_max_m": float(experiment["elevation_m"].max()),
        "altitude_mean_m": float(experiment["elevation_m"].mean()),

        "slope_min_deg": float(experiment["slope_deg"].min()),
        "slope_max_deg": float(experiment["slope_deg"].max()),
        "slope_mean_deg": float(experiment["slope_deg"].mean()),

        "limitations": [
            "Jeu expérimental limité aux zones avec relief calculable.",
            "Les variables autres que le relief restent synthétiques.",
            "Le référentiel vertical et la précision verticale ne sont "
            "pas confirmés par les métadonnées disponibles.",
            "La résolution spatiale de 5 m ne garantit pas une "
            "précision verticale de 5 m.",
            "La méthode de calcul de pente est une estimation locale "
            "à partir des pixels voisins.",
            "Les scores produits avec ce jeu restent expérimentaux "
            "et ne constituent pas une évaluation officielle du risque.",
        ],
    }

    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 10. Afficher le bilan.
    print(f"Jeu expérimental créé : {OUTPUT_PATH}")
    print(f"Métadonnées créées : {METADATA_PATH}")
    print(f"Zones de la grille : {len(base)}")
    print(f"Zones retenues : {len(experiment)}")
    print(
        "Zones exclues faute de relief complet : "
        f"{len(base) - len(experiment)}"
    )
    print(f"Couverture : {metadata['coverage_percent']:.2f} %")
    print(f"Altitude moyenne : {metadata['altitude_mean_m']:.2f}")
    print(f"Pente moyenne : {metadata['slope_mean_deg']:.3f} degrés")
    print(
        "\nLe GeoJSON de démonstration et les scores du dashboard "
        "n'ont pas été modifiés."
    )


if __name__ == "__main__":
    main()
