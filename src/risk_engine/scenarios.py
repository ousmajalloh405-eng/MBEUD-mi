"""Scénarios de pluie : résumé chiffré, classement des secteurs, évolution temporelle."""
import math

import pandas as pd

from src.risk_engine.scoring import classify, compute_risk, level_names, level_rank

HIGH_FROM = "élevé"  # à partir de ce niveau, une zone compte comme "à risque"
TIMELINE_OFFSETS = (-24, -12, -6, -3, 0, 3, 6)


def summarize(scored: pd.DataFrame, rain_mm: float, cfg: dict | None = None) -> dict:
    """Chiffres clés pour le décideur."""
    names = level_names(cfg)
    counts = {n: int((scored["level"] == n).sum()) for n in names}
    at_risk = scored[scored["level"].map(lambda l: level_rank(l, cfg)) >= level_rank(HIGH_FROM, cfg)]
    pop_total = float(scored["population"].sum())
    gscore = float((scored["score"] * scored["population"]).sum() / pop_total) if pop_total else 0.0
    return {
        "rain_mm": float(rain_mm),
        "n_zones": int(len(scored)),
        "level_counts": counts,
        "n_critical": counts[names[-1]],
        "global_score": round(gscore, 1),
        "global_level": classify(gscore, cfg),
        "population_exposed": int(at_risk["population"].sum()),
        "hospitals_exposed": int(at_risk["hospitals"].sum()),
        "schools_exposed": int(at_risk["schools"].sum()),
        "markets_exposed": int(at_risk["markets"].sum()),
        "road_km_at_risk": round(float(at_risk["road_km"].sum()), 1),
        "disclaimer": "Simulation de prototype sur données synthétiques - pas une prévision officielle.",
    }


def run_scenario(df: pd.DataFrame, rain_mm: float, cfg: dict | None = None) -> tuple[pd.DataFrame, dict]:
    scored = compute_risk(df, rain_mm, cfg)
    return scored, summarize(scored, rain_mm, cfg)


def sector_ranking(scored: pd.DataFrame) -> pd.DataFrame:
    """Regroupe les cellules par secteur (pour un affichage lisible par un décideur)."""
    g = scored.groupby("sector")
    out = pd.DataFrame({
        "score_moyen": g.apply(lambda d: (d["score"] * d["population"]).sum() / max(d["population"].sum(), 1),
                               include_groups=False).round(1),
        "score_max": g["score"].max(),
        "population": g["population"].sum(),
        "zones_critiques": g["level"].apply(lambda s: int((s == level_names()[-1]).sum())),
        "zones": g["zone_id"].count(),
    }).sort_values("score_moyen", ascending=False)
    out["niveau"] = out["score_moyen"].map(classify)
    return out.reset_index()


def _norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def forecast_timeline(df: pd.DataFrame, total_mm: float, offsets=TIMELINE_OFFSETS,
                      mu_h: float = 3.0, sigma_h: float = 4.0, cfg: dict | None = None) -> list[dict]:
    """Évolution du risque à T-24h ... T+6h pour un épisode de pluie de `total_mm`.

    ATTENTION : la répartition de la pluie dans le temps est une COURBE SYNTHÉTIQUE
    (loi normale cumulée), pas une prévision. Elle sert à montrer comment le risque
    monte quand la pluie cumulée augmente.
    """
    rows = []
    for t in offsets:
        cumul = total_mm * _norm_cdf((t - mu_h) / sigma_h)
        scored = compute_risk(df, cumul, cfg)
        s = summarize(scored, cumul, cfg)
        rows.append({
            "label": "T0" if t == 0 else f"T{t:+d}h",
            "offset_h": t,
            "cumulative_rain_mm": round(cumul, 1),
            "global_score": s["global_score"],
            "n_critical": s["n_critical"],
            "population_exposed": s["population_exposed"],
        })
    return rows
