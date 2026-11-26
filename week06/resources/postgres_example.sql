-- Run after pg_setup.py. These statements ILLUSTRATE core concepts.
-- Actual Python calls bind all parameters; <query vector> below is NOT a literal to execute.
-- PostgreSQL stores exact structured records and source text; pgvector handles vector distance.
-- A teacher should provision a read-only app role separately, without sharing the admin DSN:
-- CREATE ROLE w6_reader LOGIN PASSWORD 'choose-a-local-password';
-- GRANT CONNECT ON DATABASE engineering TO w6_reader;
-- GRANT USAGE ON SCHEMA w6 TO w6_reader;
-- GRANT SELECT ON ALL TABLES IN SCHEMA w6 TO w6_reader;
-- The application additionally opens read-only transactions and sets a statement timeout.

SELECT r.machine_id,COUNT(*) AS n,AVG(r.temperature_c) AS mean_c,
       SUM(CASE WHEN r.temperature_c>m.reference_c THEN 1 ELSE 0 END) AS above_reference
FROM w6.sensor_reading r JOIN w6.machine m USING(machine_id)
WHERE r.machine_id='CONV-3'
  AND r.ts>='2026-03-02T10:00:00+08:00'::timestamptz
  AND r.ts< '2026-03-02T10:25:00+08:00'::timestamptz
GROUP BY r.machine_id;
-- Do NOT join maintenance_event one-to-many before this aggregation: it multiplies readings.

-- An approximate HNSW index can be added in a larger lab. It is deliberately absent here.
-- CREATE INDEX ON w6.document_chunk USING hnsw(embedding vector_cosine_ops);
-- Exact search, approximate search, and restrictive-filter recall should be measured separately.
