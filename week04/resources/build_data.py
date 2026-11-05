"""Build the local query database from the supplied synthetic CSV. No network calls."""
import csv
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).resolve().parent / 'data'


def build_data():
    manifest = json.loads((DATA / 'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        if hashlib.sha256((DATA / name).read_bytes()).hexdigest() != expected:
            raise ValueError('The supplied data changed: ' + name + '. Keep the edited file and ask your mentor before rebuilding.')
    target = DATA / 'engineering.sqlite'
    if target.exists():
        with sqlite3.connect(target.resolve().as_uri() + '?mode=ro', uri=True) as connection:
            stored = dict(connection.execute('SELECT name, sha256 FROM source_file'))
            count = connection.execute('SELECT count(*) FROM sensor_reading').fetchone()[0]
        if stored != manifest['files']:
            raise ValueError('The existing database has different source versions. It was not overwritten.')
        return {'created': False, 'rows': count, 'database': str(target), 'synthetic': True}
    rows = list(csv.DictReader((DATA / 'sensor_readings.csv').open(encoding='utf-8', newline='')))
    with sqlite3.connect(target) as connection:
        connection.execute('CREATE TABLE sensor_reading(machine_id TEXT NOT NULL, ts TEXT NOT NULL, ts_epoch INTEGER NOT NULL, temperature_c REAL NOT NULL, PRIMARY KEY(machine_id,ts_epoch))')
        connection.execute('CREATE TABLE source_file(name TEXT PRIMARY KEY, sha256 TEXT NOT NULL)')
        connection.executemany('INSERT INTO sensor_reading VALUES (?,?,?,?)', [
            (r['machine_id'], r['ts'], int(datetime.fromisoformat(r['ts']).timestamp()), float(r['temperature_c'])) for r in rows])
        connection.executemany('INSERT INTO source_file VALUES (?,?)', manifest['files'].items())
    return {'created': True, 'rows': len(rows), 'database': str(target), 'synthetic': True}


if __name__ == '__main__':
    print(json.dumps(build_data(), indent=2))
