"""Build data/teaching_db_v1.sqlite - the exact table shown on slide p15.

Run:  python data/build_data.py   (regenerates the database; safe to re-run)
"""
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB = HERE / "teaching_db_v1.sqlite"

ROWS = [
    ("EV-104", "CONV-3", "2026-03-18", "replaced cooling fan"),
    ("EV-091", "CONV-3", "2026-02-26", "cleaned ventilation ducts"),
    ("EV-077", "CONV-3", "2026-01-30", "inspected terminal wiring"),
    ("EV-110", "CONV-7", "2026-03-20", "calibrated temp sensor"),
]

def main() -> None:
    DB.unlink(missing_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute(
        "CREATE TABLE maintenance_event ("
        " record_id TEXT PRIMARY KEY, machine_id TEXT,"
        " service_date TEXT, action TEXT)")
    conn.executemany(
        "INSERT INTO maintenance_event VALUES (?,?,?,?)", ROWS)
    conn.commit()
    for row in conn.execute(
            "SELECT record_id, machine_id, service_date, action "
            "FROM maintenance_event ORDER BY service_date DESC"):
        print(row)
    conn.close()
    print(f"\nwrote {DB}")

if __name__ == "__main__":
    main()
