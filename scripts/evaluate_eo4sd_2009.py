"""Évaluation exploratoire du score MBEUD-mi avec la couche EO4SD 2009.

Cette analyse est descriptive. Elle ne constitue pas une validation
prédictive du risque d'inondation.
"""

import json
from pathlib import Path

import pandas as pd


BASE = Path("data/processed")
SCORES_PATH = BASE / "terrain_score_comparison.csv"
OVERLAP_PATH = BASE / "eo4sd_flood_overlap_2009.csv"

SUMMARY_PATH = BASE / "eo4sd_2009_exploratory_evaluation.json"
GROUPS_PATH = BASE / "eo4sd_2009_score_by_overlap.csv"
CROSSTAB_PATH = BASE / "eo4sd_2009_level_crosstab.csv"

LEVELS = ["faible", "modéré", "élevé", "très élevé", "critique"]


def main():
    for path in [SCORES_PATH, OVERLAP_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {path}")

    scores = pd.read_csv(SCORES_PATH)
    overlap = pd.read_csv(OVERLAP_PATH)

    if not scores["zone_id"].is_unique:
        raise ValueError("Le fichier de scores contient des zone_id en double.")

    if not overlap["zone_id"].is_unique:
        raise ValueError("Le fichier de recouvrement contient des zone_id en double.")

    df = scores.merge(
        overlap[["zone_id", "flooded_overlap_percent"]],
        on="zone_id",
        how="outer",
        validate="one_to_one",
        indicator=True,
    )

    if not (df["_merge"] == "both").all():
        raise ValueError("Les deux fichiers ne contiennent pas les mêmes zones.")

    df = df.drop(columns="_merge")

    if df[["score_mne", "flooded_overlap_percent"]].isna().any().any():
        raise ValueError("Valeur manquante dans les variables d'évaluation.")

    df["overlap_group"] = pd.cut(
        df["flooded_overlap_percent"],
        bins=[-0.000001, 1, 10, 100.000001],
        labels=["< 1 %", "1–<10 %", "≥ 10 %"],
        include_lowest=True,
    )

    # Spearman est calculé comme la corrélation de Pearson entre les rangs.
    spearman = df["score_mne"].rank(method="average").corr(
        df["flooded_overlap_percent"].rank(method="average")
    )

    # Résumé descriptif par seuil, chaque ligne étant une comparaison séparée.
    group_rows = []
    for label, mask in [
        ("< 1 %", df["flooded_overlap_percent"] < 1),
        ("≥ 1 %", df["flooded_overlap_percent"] >= 1),
        ("≥ 10 %", df["flooded_overlap_percent"] >= 10),
    ]:
        group = df.loc[mask]
        group_rows.append({
            "overlap_threshold": label,
            "n_zones": len(group),
            "mean_score_mne": round(float(group["score_mne"].mean()), 3),
            "median_score_mne": round(float(group["score_mne"].median()), 3),
            "mean_overlap_percent": round(
                float(group["flooded_overlap_percent"].mean()), 3
            ),
        })

    group_df = pd.DataFrame(group_rows)
    group_df.to_csv(GROUPS_PATH, index=False)

    # La répartition des niveaux est affichée en effectifs et en proportions.
    df["overlap_at_least_1pct"] = df["flooded_overlap_percent"] >= 1

    counts = pd.crosstab(
        df["overlap_at_least_1pct"].map({
            False: "Overlap < 1 %",
            True: "Overlap ≥ 1 %",
        }),
        df["level_mne"],
    ).reindex(
        index=["Overlap < 1 %", "Overlap ≥ 1 %"],
        columns=LEVELS,
        fill_value=0,
    )

    row_percent = counts.div(counts.sum(axis=1), axis=0) * 100

    # Export au format long afin de conserver les effectifs et les pourcentages.
    crosstab_rows = []
    for group_name in counts.index:
        for level in LEVELS:
            crosstab_rows.append({
                "overlap_group": group_name,
                "risk_level": level,
                "zone_count": int(counts.loc[group_name, level]),
                "within_group_percent": round(
                    float(row_percent.loc[group_name, level]), 2
                ),
            })

    pd.DataFrame(crosstab_rows).to_csv(CROSSTAB_PATH, index=False)

    summary = {
        "analysis": "Exploratory spatial comparison with EO4SD Dakar flood extent 2009",
        "n_zones": int(len(df)),
        "spearman_score_vs_overlap": round(float(spearman), 4),
        "groups": group_rows,
        "risk_level_crosstab": crosstab_rows,
        "interpretation": (
            "Descriptive association only. The score model is not validated "
            "as a predictor of real flood risk. Several input variables remain "
            "synthetic, and the 2009 flood extent is not a complete inventory "
            "of all flooded and non-flooded locations."
        ),
        "outputs": [
            str(SUMMARY_PATH),
            str(GROUPS_PATH),
            str(CROSSTAB_PATH),
        ],
    }

    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("ÉVALUATION EXPLORATOIRE EO4SD — 2009")
    print("Zones comparées :", len(df))
    print("Corrélation de Spearman :", round(float(spearman), 4))
    print("\nScores par groupe de recouvrement :")
    print(group_df.to_string(index=False))
    print("\nFichiers créés :")
    print("-", SUMMARY_PATH)
    print("-", GROUPS_PATH)
    print("-", CROSSTAB_PATH)
    print("\nInterprétation : association descriptive, pas validation prédictive.")


if __name__ == "__main__":
    main()
