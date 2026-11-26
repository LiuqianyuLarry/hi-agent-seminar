"""Read-only, parameter-bound SQL. Structured rows are not vector searched."""
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from common import validate_task,sha,canonical

@contextmanager
def readonly(path):
    p=Path(path).resolve()
    con=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
    con.row_factory=sqlite3.Row
    try:
        con.execute('PRAGMA query_only=ON')
        yield con
    finally: con.close()

# W6.1_BEGIN
def readings_query():
    """Return a query with THREE ? parameters: machine, inclusive start, exclusive end."""
    return ("SELECT r.reading_id,r.machine_id,r.ts,r.temperature_c,"
            "m.model_code,m.reference_c,m.spec_version "
            "FROM sensor_reading AS r JOIN machine AS m ON r.machine_id=m.machine_id "
            "WHERE r.machine_id=? AND r.ts>=? AND r.ts<=? ORDER BY r.ts,r.reading_id")
# W6.1_END

def machine_meta(db,machine_id):
    with readonly(db) as con:
        row=con.execute('SELECT * FROM machine WHERE machine_id=?',(machine_id,)).fetchone()
    if row is None: raise ValueError('Unknown machine')
    return dict(row)

def finish_sql(rows,task,kind):
    ids=[r.get('reading_id',r.get('event_id',r.get('fault_id'))) for r in rows]
    result={'kind':kind,'machine_id':task['machine_id'],'window':[task['start'],task['end']],
            'count':len(rows),'row_ids':ids,'rows':rows,
            'provenance':{'dataset':'synthetic-week06','query':kind+'-v1','bound_parameters':[task['machine_id'],task['start'],task['end']]}}
    if kind=='readings' and rows:
        vals=[r['temperature_c'] for r in rows];ref=rows[0]['reference_c']
        k=sum(v>ref for v in vals)
        result['statistics']={'mean_c':sum(vals)/len(vals),'max_c':max(vals),'reference_c':ref,
            'spec_version':rows[0]['spec_version'],'exceed_count':k,'sample_fraction':k/len(vals),
            'meaning':'fraction of observed samples; NOT time fraction or fault probability'}
    else: result['statistics']=None
    return {'id':'sql:'+sha(canonical(result))[:16],'type':'sql','payload':result}

def query_engineering(db,task):
    t=validate_task(task);machine_meta(db,t['machine_id']);kind=t.get('sql_kind','readings')
    params=(t['machine_id'],t['start'],t['end'])
    with readonly(db) as con:
        if kind=='readings': rows=con.execute(readings_query(),params).fetchall()
        elif kind=='maintenance':
            rows=con.execute('SELECT * FROM maintenance_event WHERE machine_id=? AND ts>=? AND ts<? ORDER BY ts,event_id',params).fetchall()
        else:
            rows=con.execute('SELECT * FROM fault_record WHERE machine_id=? AND ts>=? AND ts<? ORDER BY ts,fault_id',params).fetchall()
    return finish_sql([dict(r) for r in rows],t,kind)
