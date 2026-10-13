-- Schéma PostGIS du projet flood-risk-senegal.
-- Exécuté automatiquement au premier démarrage du conteneur db (docker-entrypoint-initdb.d).
-- Toutes les données chargées en démo sont SYNTHETIC DATA — FOR DEMONSTRATION ONLY.

CREATE EXTENSION IF NOT EXISTS postgis;

-- Les cellules de la grille
CREATE TABLE IF NOT EXISTS zones (
    zone_id   TEXT PRIMARY KEY,
    sector    TEXT NOT NULL,
    area_km2  REAL NOT NULL,
    geom      geometry(Polygon, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zones_geom ON zones USING GIST (geom);

-- Attributs par zone (altitude, population, infrastructures...)
CREATE TABLE IF NOT EXISTS zone_features (
    zone_id          TEXT PRIMARY KEY REFERENCES zones(zone_id) ON DELETE CASCADE,
    elevation_m      REAL,
    slope_deg        REAL,
    flood_history    REAL CHECK (flood_history BETWEEN 0 AND 1),
    drainage_quality REAL CHECK (drainage_quality BETWEEN 0 AND 1),
    population       INTEGER CHECK (population >= 0),
    hospitals        INTEGER CHECK (hospitals >= 0),
    schools          INTEGER CHECK (schools >= 0),
    markets          INTEGER CHECK (markets >= 0),
    road_km          REAL CHECK (road_km >= 0),
    data_origin      TEXT NOT NULL DEFAULT 'SYNTHETIC DATA — FOR DEMONSTRATION ONLY'
);

-- Pluie prévue / observée (alimentée par l'ingestion Open-Meteo en V2)
CREATE TABLE IF NOT EXISTS weather_forecast (
    ts               TIMESTAMPTZ NOT NULL,
    latitude         DOUBLE PRECISION NOT NULL,
    longitude        DOUBLE PRECISION NOT NULL,
    precipitation_mm REAL NOT NULL CHECK (precipitation_mm >= 0),
    source           TEXT NOT NULL,
    PRIMARY KEY (ts, latitude, longitude, source)
);

-- Un scénario = une pluie simulée et la méthode utilisée
CREATE TABLE IF NOT EXISTS scenarios (
    scenario_id SERIAL PRIMARY KEY,
    rain_mm     REAL NOT NULL CHECK (rain_mm >= 0),
    method      TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Résultat : on garde les 3 blocs à côté du score final (explicabilité)
CREATE TABLE IF NOT EXISTS risk_scores (
    scenario_id   INTEGER REFERENCES scenarios(scenario_id) ON DELETE CASCADE,
    zone_id       TEXT REFERENCES zones(zone_id) ON DELETE CASCADE,
    hazard        REAL NOT NULL,
    vulnerability REAL NOT NULL,
    exposure      REAL NOT NULL,
    score         REAL NOT NULL CHECK (score BETWEEN 0 AND 100),
    level         TEXT NOT NULL,
    PRIMARY KEY (scenario_id, zone_id)
);

CREATE TABLE IF NOT EXISTS recommendations (
    level   TEXT PRIMARY KEY,
    actions TEXT[] NOT NULL
);

-- Exemple de requête spatiale : population dans les zones critiques d'un scénario
-- SELECT s.sector, SUM(f.population)
-- FROM risk_scores r JOIN zones s USING (zone_id) JOIN zone_features f USING (zone_id)
-- WHERE r.scenario_id = 1 AND r.level = 'critique' GROUP BY s.sector;
