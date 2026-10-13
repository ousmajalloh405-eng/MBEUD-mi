# Airflow — prévu pour la V2 (volontairement vide dans le MVP)

**Pourquoi pas maintenant ?** Airflow sert à planifier et surveiller des tâches récurrentes
(ex. : récupérer la météo toutes les heures). Dans le MVP, tout est lancé à la demande
(`scripts/run_pipeline.py`) : un orchestrateur ajouterait de la complexité sans valeur.

**Quand l'ajouter ?** Dès que l'ingestion Open-Meteo tourne régulièrement (V2).

## DAG prévu

```
ingest_weather -> validate_data -> transform_weather -> calculate_risk -> update_postgis -> generate_alerts
```

| Tâche | Fonction existante dans le projet |
|---|---|
| ingest_weather | `src/ingestion/open_meteo.py` (`fetch_forecast`, `save_raw`) |
| validate_data | `src/processing/validation.py` (`validate_weather`) |
| transform_weather | à écrire (cumul 24 h par zone) |
| calculate_risk | `src/risk_engine/scenarios.py` (`run_scenario`) |
| update_postgis | `scripts/load_to_postgis.py` (à transformer en fonction) |
| generate_alerts | `src/alerts/generate.py` |
