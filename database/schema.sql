-- ClimateTwin Bharat - PostgreSQL + PostGIS Schema
-- Run: psql -U postgres -f schema.sql

-- ── Setup ─────────────────────────────────────────────────────────────────────
CREATE DATABASE climatetwin_bharat;
\c climatetwin_bharat;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE USER climatetwin WITH PASSWORD 'climatetwin';
GRANT ALL PRIVILEGES ON DATABASE climatetwin_bharat TO climatetwin;

-- ── Historical Climate Records ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS climate_records (
    id          BIGSERIAL PRIMARY KEY,
    date        DATE          NOT NULL,
    latitude    REAL          NOT NULL,
    longitude   REAL          NOT NULL,
    rainfall    REAL,
    max_temp    REAL,
    min_temp    REAL,
    geom        GEOMETRY(Point, 4326) GENERATED ALWAYS AS (
                    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
                ) STORED
);

CREATE INDEX idx_climate_date        ON climate_records (date);
CREATE INDEX idx_climate_lat_lon     ON climate_records (latitude, longitude);
CREATE INDEX idx_climate_date_lat    ON climate_records (date, latitude, longitude);
CREATE INDEX idx_climate_geom        ON climate_records USING GIST (geom);

-- Partition hint (optional, for large ingestion)
-- CREATE INDEX idx_climate_date_brin ON climate_records USING BRIN (date);

-- ── Forecast Records ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS forecast_records (
    id              BIGSERIAL PRIMARY KEY,
    forecast_date   DATE          NOT NULL,
    target_date     DATE          NOT NULL,
    latitude        REAL          NOT NULL,
    longitude       REAL          NOT NULL,
    rainfall_pred   REAL,
    max_temp_pred   REAL,
    min_temp_pred   REAL,
    confidence      REAL,
    model_type      VARCHAR(50)   DEFAULT 'ensemble',
    geom            GEOMETRY(Point, 4326) GENERATED ALWAYS AS (
                        ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
                    ) STORED
);

CREATE INDEX idx_forecast_dates      ON forecast_records (forecast_date, target_date);
CREATE INDEX idx_forecast_geom       ON forecast_records USING GIST (geom);

-- ── Scenario Records ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scenario_records (
    id              BIGSERIAL PRIMARY KEY,
    scenario_id     VARCHAR(100)  NOT NULL,
    scenario_type   VARCHAR(100)  NOT NULL,
    date            DATE          NOT NULL,
    latitude        REAL          NOT NULL,
    longitude       REAL          NOT NULL,
    rainfall        REAL,
    max_temp        REAL,
    min_temp        REAL,
    delta_rainfall  REAL,
    delta_max_temp  REAL,
    delta_min_temp  REAL,
    geom            GEOMETRY(Point, 4326) GENERATED ALWAYS AS (
                        ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
                    ) STORED
);

CREATE INDEX idx_scenario_id         ON scenario_records (scenario_id);
CREATE INDEX idx_scenario_type_date  ON scenario_records (scenario_type, date);
CREATE INDEX idx_scenario_geom       ON scenario_records USING GIST (geom);

-- ── Analytics Results ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analytics_results (
    id              BIGSERIAL PRIMARY KEY,
    analysis_type   VARCHAR(100)  NOT NULL,
    variable        VARCHAR(50),
    region          VARCHAR(200),
    start_date      DATE,
    end_date        DATE,
    result_json     JSONB,
    created_at      TIMESTAMPTZ   DEFAULT NOW()
);

CREATE INDEX idx_analytics_type      ON analytics_results (analysis_type);
CREATE INDEX idx_analytics_created   ON analytics_results (created_at);

-- ── Dataset Metadata ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dataset_meta (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200)  UNIQUE NOT NULL,
    source_path     TEXT,
    total_rows      INTEGER,
    date_start      DATE,
    date_end        DATE,
    lat_min         REAL,
    lat_max         REAL,
    lon_min         REAL,
    lon_max         REAL,
    status          VARCHAR(50)   DEFAULT 'pending',
    ingested_at     TIMESTAMPTZ   DEFAULT NOW(),
    metadata_json   JSONB
);

-- ── Useful Views ──────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_daily_national_avg AS
SELECT
    date,
    ROUND(AVG(rainfall)::numeric, 3)  AS avg_rainfall,
    ROUND(MAX(rainfall)::numeric, 3)  AS max_rainfall,
    ROUND(AVG(max_temp)::numeric, 3)  AS avg_max_temp,
    ROUND(MAX(max_temp)::numeric, 3)  AS peak_max_temp,
    ROUND(AVG(min_temp)::numeric, 3)  AS avg_min_temp,
    COUNT(*)                           AS grid_points
FROM climate_records
GROUP BY date
ORDER BY date;

CREATE OR REPLACE VIEW v_monthly_summary AS
SELECT
    EXTRACT(MONTH FROM date)::INT      AS month,
    ROUND(AVG(rainfall)::numeric, 3)   AS avg_rainfall,
    ROUND(SUM(rainfall)::numeric, 3)   AS total_rainfall,
    ROUND(AVG(max_temp)::numeric, 3)   AS avg_max_temp,
    ROUND(AVG(min_temp)::numeric, 3)   AS avg_min_temp
FROM climate_records
GROUP BY month
ORDER BY month;

-- ── Initial Dataset Meta Insert ───────────────────────────────────────────────
INSERT INTO dataset_meta (name, source_path, total_rows, date_start, date_end,
                          lat_min, lat_max, lon_min, lon_max, status)
VALUES ('IMD India 2025',
        'processed/csv/master_climate_dataset.csv',
        2106050,
        '2025-01-01', '2025-12-31',
        8.25, 37.25, 68.0, 100.0,
        'registered')
ON CONFLICT (name) DO NOTHING;

GRANT ALL ON ALL TABLES    IN SCHEMA public TO climatetwin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO climatetwin;
