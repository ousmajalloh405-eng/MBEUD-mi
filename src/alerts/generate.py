"""Génération d'alertes : les zones les plus à risque, avec la priorité proposée."""
import pandas as pd

from src.risk_engine.recommendations import recommendations_for
from src.risk_engine.scoring import level_rank


def generate_alerts(scored: pd.DataFrame, min_level: str = "très élevé", top_n: int = 20) -> list[dict]:
    threshold = level_rank(min_level)
    sel = scored[scored["level"].map(level_rank) >= threshold].sort_values(
        ["score", "population"], ascending=False).head(top_n)
    alerts = []
    for rec in sel.to_dict(orient="records"):
        recos = recommendations_for(rec["level"])
        alerts.append({
            "zone_id": rec["zone_id"],
            "sector": rec["sector"],
            "level": rec["level"],
            "score": rec["score"],
            "population": rec["population"],
            "message": f"Zone {rec['zone_id']} ({rec['sector']}) : risque {rec['level']} (score {rec['score']}).",
            "priority_proposed": recos[0] if recos else "",
        })
    return alerts
