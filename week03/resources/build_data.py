"""Only builds bundled synthetic classroom data, never a production database."""
import argparse,csv,hashlib,json,sqlite3
from contextlib import closing
from datetime import datetime,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def build(force=False):
    folder=ROOT/'data';folder.mkdir(exist_ok=True)
    db=folder/'engineering.sqlite'
    if db.exists() and not force:
        print('Database already exists; use --force only to rebuild classroom files.');return
    values=[80,82,87,91,94,97,99]
    start=datetime.fromisoformat('2026-03-02T09:55:00+08:00')
    rows=[('CONV-3',(start+timedelta(minutes=5*i)).isoformat(),float(v)) for i,v in enumerate(values)]
    rows += [('CONV-7','2026-03-02T10:05:00+08:00',68.0)]
    start2=datetime.fromisoformat('2026-03-03T10:00:00+08:00')
    rows += [('CONV-3',(start2+timedelta(minutes=i)).isoformat(),70.0+i%15) for i in range(101)]
    with (folder/'sensor_readings.csv').open('w',newline='',encoding='utf-8') as f:
        wr=csv.writer(f);wr.writerow(['machine_id','ts','temperature_c']);wr.writerows(rows)
    tmp=folder/'engineering.build.sqlite'
    if tmp.exists():tmp.unlink()
    with closing(sqlite3.connect(tmp)) as conn:
        conn.execute('CREATE TABLE sensor_reading (machine_id TEXT NOT NULL, ts TEXT NOT NULL, '
                     'ts_epoch INTEGER NOT NULL, temperature_c REAL NOT NULL)')
        conn.executemany('INSERT INTO sensor_reading VALUES (?,?,?,?)',
                         [(m,t,int(datetime.fromisoformat(t).timestamp()),v) for m,t,v in rows])
        conn.execute('CREATE INDEX idx_machine_time ON sensor_reading(machine_id,ts_epoch)')
        conn.commit()
    tmp.replace(db)
    spec={'synthetic':True,'version':'classroom-v1','note':'Teaching references; not real equipment limits',
          'machines':{'CONV-3':{'temperature_limit_c':85.0,'unit':'C'},
                      'CONV-7':{'temperature_limit_c':80.0,'unit':'C'}}}
    (folder/'machine_specs.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
    manifest={'synthetic':True,'timezone':'+08:00','query_interval':'[start,end)',
              'purpose':'function tests; not a physical model or actual plant history','files':{}}
    for file in ['engineering.sqlite','sensor_readings.csv','machine_specs.json']:
        manifest['files'][file]=hashlib.sha256((folder/file).read_bytes()).hexdigest()
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Created',db,'with',len(rows),'synthetic rows.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--force',action='store_true');build(p.parse_args().force)
