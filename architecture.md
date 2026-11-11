# Architecture — MBEUD-mi

## Objectif

Système d’aide à la décision pour prioriser les interventions face aux inondations à Dakar.

## Flux principal

```
Sources (Open-Meteo + synthétique / géospatial)
        │
        ▼
   Ingestion + Validation
        │
        ▼
 Traitement + Grille géospatiale
        │
        ▼
     Risk Engine (score 0-100)
        │
        ▼
     API FastAPI
        │
        ▼
  Dashboard Streamlit (carte + alertes + simulation)
```

## Couches

| Couche | Rôle | Fichiers clés |
|--------|------|----------------|
| Ingestion | Récupérer météo et données brutes | `src/ingestion/` |
| Traitement | Normaliser, griller, valider | `src/processing/`, `src/geospatial/` |
| Risk Engine | Calculer score, niveaux, ressources | `src/risk_engine/` |
| API | Exposer les résultats | `api/` |
| Dashboard | Visualiser pour le décideur | `dashboard/` |
| Stockage | GeoJSON (MVP) + PostGIS (prêt) | `data/`, `sql/` |

## Technologies

- Python, FastAPI, Streamlit, Folium
- Shapely (géométries)
- PostgreSQL + PostGIS (optionnel)
- Docker Compose

## Points forts actuels

- Séparation claire des responsabilités
- Score explicable (hazard / vulnerability / exposure)
- Tests unitaires nombreux
- Documentation détaillée et honnête sur les limites

## Améliorations prioritaires

1. Intégration plus forte des données météo réelles dans le flux principal
2. Dashboard plus réactif (rafraîchissement live)
3. Version courte du README pour les recruteurs
