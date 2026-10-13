"""Chargement de la configuration (fichiers YAML du dossier config/).

Pourquoi ? Pour que les paramètres (poids du score, seuils, taille de grille...)
soient modifiables SANS toucher au code.
"""
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


def _load(name: str) -> dict:
    with open(CONFIG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache
def settings() -> dict:
    return _load("settings.yaml")


@lru_cache
def risk_config() -> dict:
    return _load("risk.yaml")


@lru_cache
def reco_config() -> dict:
    return _load("recommendations.yaml")


def resolve(relative_path: str) -> Path:
    """Chemin absolu à partir d'un chemin relatif à la racine du projet."""
    return ROOT / relative_path
