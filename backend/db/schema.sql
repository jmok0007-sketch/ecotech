-- EcoTech PostgreSQL schema.
-- Run once against the target database (local Postgres or AWS RDS).

DROP TABLE IF EXISTS health_merged CASCADE;
DROP TABLE IF EXISTS heavy_metal_state CASCADE;
DROP TABLE IF EXISTS heavy_metal_facility CASCADE;
DROP TABLE IF EXISTS ewaste_facilities CASCADE;

CREATE TABLE health_merged (
    id              SERIAL PRIMARY KEY,
    year            INTEGER NOT NULL,
    sex             TEXT,
    cancer_type     TEXT,
    cancer_cases    DOUBLE PRECISION,
    cancer_deaths   DOUBLE PRECISION,
    fatality_ratio  DOUBLE PRECISION
);
CREATE INDEX idx_health_year       ON health_merged (year);
CREATE INDEX idx_health_sex        ON health_merged (sex);
CREATE INDEX idx_health_cancer     ON health_merged (cancer_type);

CREATE TABLE heavy_metal_state (
    id                       SERIAL PRIMARY KEY,
    report_year              INTEGER NOT NULL,
    state                    TEXT NOT NULL,
    metal                    TEXT NOT NULL,
    total_air_emission_kg    DOUBLE PRECISION,
    total_water_emission_kg  DOUBLE PRECISION,
    total_land_emission_kg   DOUBLE PRECISION,
    facility_count           INTEGER
);
CREATE INDEX idx_state_year   ON heavy_metal_state (report_year);
CREATE INDEX idx_state_state  ON heavy_metal_state (state);
CREATE INDEX idx_state_metal  ON heavy_metal_state (metal);

CREATE TABLE heavy_metal_facility (
    id                       SERIAL PRIMARY KEY,
    report_year              INTEGER NOT NULL,
    facility_id              TEXT,
    facility_name            TEXT,
    state                    TEXT,
    postcode                 TEXT,
    latitude                 DOUBLE PRECISION,
    longitude                DOUBLE PRECISION,
    metal                    TEXT,
    total_air_emission_kg    DOUBLE PRECISION,
    total_water_emission_kg  DOUBLE PRECISION,
    total_land_emission_kg   DOUBLE PRECISION
);
CREATE INDEX idx_fac_year     ON heavy_metal_facility (report_year);
CREATE INDEX idx_fac_state    ON heavy_metal_facility (state);
CREATE INDEX idx_fac_postcode ON heavy_metal_facility (postcode);

CREATE TABLE ewaste_facilities (
    id              SERIAL PRIMARY KEY,
    facility_name   TEXT NOT NULL,
    address         TEXT,
    suburb          TEXT,
    postcode        TEXT,
    state           TEXT,
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    coord_source    TEXT,
    verified        BOOLEAN DEFAULT FALSE
);
CREATE INDEX idx_disp_postcode ON ewaste_facilities (postcode);
CREATE INDEX idx_disp_state    ON ewaste_facilities (state);
CREATE INDEX idx_disp_geo      ON ewaste_facilities (latitude, longitude);
