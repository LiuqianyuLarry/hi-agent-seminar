"""Create the structured teaching database. Explicit --reset only."""
from __future__ import annotations
import argparse, csv, sqlite3
from common import ROOT,load,utc

def seed_db(path, reset=False):
    from pathlib import Path
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        if not reset: raise FileExistsError(f'{p} exists; use --reset deliberately')
        p.unlink()
    specs=load(ROOT/'data/imported_week05/machine_specs.json')
    con=sqlite3.connect(p)
    try:
        con.executescript((ROOT/'schema.sql').read_text())
        for machine,values in specs['machines'].items():
            con.execute('INSERT INTO machine VALUES (?,?,?,?)',
                (machine,'MX-A' if machine=='CONV-3' else 'MX-B',values['temperature_limit_c'],specs['version']))
        with (ROOT/'data/imported_week05/sensor_readings.csv').open(newline='',encoding='utf-8') as f:
            for i,row in enumerate(csv.DictReader(f),1):
                con.execute('INSERT INTO sensor_reading VALUES (?,?,?,?)',
                    (f'R{i:04d}',row['machine_id'],utc(row['ts']),float(row['temperature_c'])))
        for row in load(ROOT/'data/maintenance_events.json'):
            con.execute('INSERT INTO maintenance_event VALUES (?,?,?,?,?)',
                (row['event_id'],row['machine_id'],utc(row['ts']),row['action'],row['outcome']))
        for row in load(ROOT/'data/fault_records.json'):
            con.execute('INSERT INTO fault_record VALUES (?,?,?,?,?,?)',
                (row['fault_id'],row['machine_id'],utc(row['ts']),row['reported_symptom'],row['confirmation_status'],row['root_cause']))
        con.commit()
    finally: con.close()
    return p
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',default='work/engineering.sqlite');p.add_argument('--reset',action='store_true')
    a=p.parse_args();print(seed_db(a.db,a.reset))
