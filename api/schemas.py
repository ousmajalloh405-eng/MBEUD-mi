"""Modèles de données de l'API (validation automatique des entrées)."""
from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    rain_mm: float = Field(..., ge=0, le=500, description="Pluie cumulée sur 24 h (mm)")
    pumps: int = Field(10, ge=0, le=1000, description="Pompes disponibles")
    teams: int = Field(5, ge=0, le=1000, description="Équipes de secours disponibles")
    vehicles: int = Field(10, ge=0, le=1000, description="Véhicules disponibles")
    top_n: int = Field(10, ge=1, le=100, description="Nombre de zones prioritaires à renvoyer")
