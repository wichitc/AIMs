-- Runs once via docker-entrypoint-initdb.d on first container boot, before any Alembic migration.
-- Both extensions are required by the schema: timescaledb for sensor_data (Database.md §9.1),
-- vector for document_embedding (AI-Copilot-Design.md §7).

CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS vector;
