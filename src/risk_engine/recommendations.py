"""Recommandations par niveau (texte lu dans config/recommendations.yaml).

On parle de "recommandation" ou de "priorité proposée" : le système n'émet JAMAIS d'ordre.
"""
from src.config import reco_config


def recommendations_for(level: str) -> list[str]:
    return list(reco_config()["levels"].get(level, []))


def all_recommendations() -> dict:
    return {k: list(v) for k, v in reco_config()["levels"].items()}
