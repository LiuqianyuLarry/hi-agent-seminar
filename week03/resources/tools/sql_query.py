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
    # TODO W3.3: Read-only SQL with bound parameters and half-open interval; reject >100 rows
    raise NotImplementedError("TODO W3.3: complete this step before full tests")