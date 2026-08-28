-- Heatwave EWS — Database Initialization
-- This script runs once when the PostgreSQL container is first created.

-- Enable PostGIS extension for geospatial queries
CREATE EXTENSION IF NOT EXISTS postgis;

-- Ward boundaries table
-- Stores administrative ward polygons for geospatial risk mapping.
CREATE TABLE IF NOT EXISTS wards (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    geom        GEOMETRY(POLYGON, 4326)  -- WGS 84 coordinate system
);

-- Index for spatial queries on ward geometries
CREATE INDEX IF NOT EXISTS idx_wards_geom ON wards USING GIST (geom);
