"""Proposition d'allocation de ressources (SIMULATION ALGORITHMIQUE).

Principe (volontairement simple et explicable) :
1. On ne considère que les zones de niveau "élevé" ou plus.
2. On les classe par score décroissant (puis par population).
3. Chaque niveau a un plafond par zone (config/recommendations.yaml).
4. On distribue dans l'ordre jusqu'à épuisement du stock.

Ce n'est PAS un système d'optimisation opérationnel : c'est une proposition à discuter.
"""
import pandas as pd

from src.config import reco_config
from src.risk_engine.scoring import level_rank

KINDS = ("pumps", "teams", "vehicles")


def allocate(scored: pd.DataFrame, pumps: int, teams: int, vehicles: int) -> dict:
    caps = reco_config()["resources_caps"]
    stock = {"pumps": int(pumps), "teams": int(teams), "vehicles": int(vehicles)}
    if min(stock.values()) < 0:
        raise ValueError("Les quantités de ressources doivent être positives ou nulles.")

    threshold = level_rank("élevé")
    candidates = scored[scored["level"].map(level_rank) >= threshold]
    candidates = candidates.sort_values(["score", "population"], ascending=False)

    remaining = dict(stock)
    allocation = []
    for rec in candidates.to_dict(orient="records"):
        if not any(remaining.values()):
            break
        cap = caps.get(rec["level"], {})
        give = {k: min(int(cap.get(k, 0)), remaining[k]) for k in KINDS}
        if not any(give.values()):
            continue
        for k in KINDS:
            remaining[k] -= give[k]
        allocation.append({
            "zone_id": rec["zone_id"], "sector": rec["sector"], "level": rec["level"],
            "score": rec["score"], **give,
        })
    return {
        "allocation": allocation,
        "stock": stock,
        "remaining": remaining,
        "note": "Simulation algorithmique : proposition à valider par les services compétents, pas un ordre.",
    }
