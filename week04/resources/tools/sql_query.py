"""One fixed SELECT, bound parameters, read-only connection, bounded result size."""
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from schemas import QueryArgs,ToolFailure,success
DB_PATH=Path(__file__).resolve().parents[1]/'data'/'engineering.sqlite'
SQL='''
SELECT ts,temperature_c FROM sensor_reading
WHERE machine_id=? AND ts_epoch>=? AND ts_epoch<?
ORDER BY ts_epoch LIMIT 101
'''

def query_temperature(machine_id:str,start:str,end:str)->dict:
    args=QueryArgs.model_validate({'machine_id':machine_id,'start':start,'end':end})
    # BEGIN_SOLUTION W3.3
    if not DB_PATH.is_file():
        raise ToolFailure('DATA_UNAVAILABLE','The classroom database is missing. Run build_data.py to create it from the supplied CSV.')
    begin=int(datetime.fromisoformat(args.start).timestamp())
    finish=int(datetime.fromisoformat(args.end).timestamp())
    try:
        # Context manager for a sqlite connection commits/rolls back, but does not close it.
        with closing(sqlite3.connect(DB_PATH.resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as conn:
            conn.execute('PRAGMA query_only=ON')
            conn.row_factory=sqlite3.Row
            calls=0
            def budget():
                nonlocal calls
                calls+=1
                return int(calls>100)  # At most about 100,000 virtual-machine instructions.
            conn.set_progress_handler(budget,1000)
            rows=conn.execute(SQL,(args.machine_id,begin,finish)).fetchall()
    except sqlite3.Error as exc:
        raise ToolFailure('DATA_UNAVAILABLE','The read-only query failed. No temperature readings were confirmed.') from exc
    if len(rows)>100:
        raise ToolFailure('RESULT_LIMIT','More than 100 rows matched. Use a smaller time window. The result was not silently truncated.')
    records=[{'ts':row['ts'],'temperature_c':float(row['temperature_c'])} for row in rows]
    return success({'machine_id':args.machine_id,'start':args.start,'end':args.end,
                    'interval':'[start,end)','count':len(records),'records':records,'unit':'C'},
                   source='engineering.sqlite/sensor_reading')
    # END_SOLUTION W3.3
