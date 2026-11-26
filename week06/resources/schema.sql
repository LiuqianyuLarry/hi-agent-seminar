PRAGMA foreign_keys=ON;
CREATE TABLE machine (
 machine_id TEXT PRIMARY KEY, model_code TEXT NOT NULL,
 reference_c REAL NOT NULL, spec_version TEXT NOT NULL
);
CREATE TABLE sensor_reading (
 reading_id TEXT PRIMARY KEY, machine_id TEXT NOT NULL REFERENCES machine(machine_id),
 ts TEXT NOT NULL, temperature_c REAL NOT NULL,
 UNIQUE(machine_id, ts)
);
CREATE INDEX reading_time ON sensor_reading(machine_id,ts);
CREATE TABLE maintenance_event (
 event_id TEXT PRIMARY KEY, machine_id TEXT NOT NULL REFERENCES machine(machine_id),
 ts TEXT NOT NULL, action TEXT NOT NULL, outcome TEXT NOT NULL
);
CREATE TABLE fault_record (
 fault_id TEXT PRIMARY KEY, machine_id TEXT NOT NULL REFERENCES machine(machine_id),
 ts TEXT NOT NULL, reported_symptom TEXT NOT NULL,
 confirmation_status TEXT NOT NULL CHECK(confirmation_status IN ('reported','confirmed','ruled_out')),
 root_cause TEXT
);
