"""Calcul du Flood Risk Score (0-100).

Logique en 3 blocs (voir docs/risk_model.md) :
    Hazard         : l'aléa (pluie)
    Vulnerability  : la sensibilité de la zone (altitude, pente, historique, drainage)
    Exposure       : ce qui peut être touché (population, infrastructures, routes)

Chaque variable est d'abord NORMALISÉE entre 0 et 1 (0 = favorable, 1 = défavorable),
puis combinée avec des poids lus dans config/risk.yaml.
"""
import copy

import numpy as np
import pandas as pd

from src.config import risk_config


def normalize_weights(weights: dict) -> dict:
    """Ramène des poids relatifs à une somme de 1 (permet de modifier les poids sans calcul)."""
    total = float(sum(weights.values()))
    if total <= 0:
        raise ValueError("La somme des poids doit être strictement positive.")
    return {k: v / total for k, v in weights.items()}


def _robust_minmax(s: pd.Series) -> pd.Series:
    """Min-max entre le minimum et le 95e centile (évite qu'une valeur extrême écrase tout)."""
    lo, hi = s.min(), s.quantile(0.95)
    if hi <= lo:
        return pd.Series(0.0, index=s.index)
    return ((s - lo) / (hi - lo)).clip(0, 1)


def hazard_index(rain_mm: float, cfg: dict | None = None) -> float:
    """Aléa entre 0 et 1 : 0 mm -> 0 ; pluie de référence (ex. 150 mm) -> 1."""
    cfg = cfg or risk_config()
    if rain_mm < 0:
        raise ValueError("La pluie ne peut pas être négative.")
    return float(np.clip(rain_mm / cfg["rain_ref_mm"], 0, 1))


def vulnerability_components(df: pd.DataFrame, cfg: dict | None = None) -> pd.DataFrame:
    cfg = cfg or risk_config()
    ref = cfg["reference"]
    return pd.DataFrame({
        "low_elevation": 1 - (df["elevation_m"] / ref["elevation_max_m"]).clip(0, 1),
        "low_slope": 1 - (df["slope_deg"] / ref["slope_max_deg"]).clip(0, 1),
        "flood_history": df["flood_history"].clip(0, 1),
        "poor_drainage": 1 - df["drainage_quality"].clip(0, 1),
    }, index=df.index)


def exposure_components(df: pd.DataFrame, cfg: dict | None = None) -> pd.DataFrame:
    cfg = cfg or risk_config()
    iw = cfg["infrastructure_weights"]
    infra_raw = df["hospitals"] * iw["hospitals"] + df["schools"] * iw["schools"] + df["markets"] * iw["markets"]
    return pd.DataFrame({
        "population": _robust_minmax(df["population"]),
        "infrastructure": _robust_minmax(infra_raw),
        "roads": _robust_minmax(df["road_km"]),
    }, index=df.index)


def _weighted(components: pd.DataFrame, weights: dict) -> pd.Series:
    w = normalize_weights(weights)
    return sum(components[k] * w[k] for k in w)


def classify(score: float, cfg: dict | None = None) -> str:
    """Convertit un score 0-100 en niveau (seuils illustratifs, voir config/risk.yaml)."""
    cfg = cfg or risk_config()
    for lvl in cfg["levels"]:
        if score <= lvl["max_score"]:
            return lvl["name"]
    return cfg["levels"][-1]["name"]


def level_names(cfg: dict | None = None) -> list[str]:
    cfg = cfg or risk_config()
    return [lvl["name"] for lvl in cfg["levels"]]


def level_rank(name: str, cfg: dict | None = None) -> int:
    return level_names(cfg).index(name)


def compute_risk(df: pd.DataFrame, rain_mm: float, cfg: dict | None = None) -> pd.DataFrame:
    """Retourne une copie de df avec hazard, vulnerability, exposure, score, level."""
    cfg = copy.deepcopy(cfg) if cfg else risk_config()
    h = hazard_index(rain_mm, cfg)
    v = _weighted(vulnerability_components(df, cfg), cfg["vulnerability_weights"])
    e = _weighted(exposure_components(df, cfg), cfg["exposure_weights"])
    bw = normalize_weights(cfg["block_weights"])

    method = cfg.get("method", "weighted_sum")
    if method == "weighted_sum":
        raw = bw["hazard"] * h + bw["vulnerability"] * v + bw["exposure"] * e
    elif method == "multiplicative":
        w_ve = bw["vulnerability"] + bw["exposure"]
        raw = h * (bw["vulnerability"] * v + bw["exposure"] * e) / w_ve
    else:
        raise ValueError(f"Méthode inconnue : {method}")

    score = (100 * raw).clip(0, 100)
    if rain_mm < cfg["min_rain_mm"]:
        score = score * 0  # pas d'aléa -> pas de risque d'inondation pluviale

    out = df.copy()
    out["hazard"] = round(h, 3)
    out["vulnerability"] = v.round(3)
    out["exposure"] = e.round(3)
    out["score"] = score.round(1)
    out["level"] = out["score"].map(lambda s: classify(s, cfg))
    return out
