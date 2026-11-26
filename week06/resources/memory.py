"""Small explicit preference/episode store. Not a checkpoint database."""
from __future__ import annotations
import sqlite3,json
from pathlib import Path
from common import canonical,utc

class MemoryStore:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(self.path) as c:
            c.execute('CREATE TABLE IF NOT EXISTS memory (owner TEXT,key TEXT,kind TEXT,value TEXT,source TEXT,expires TEXT,PRIMARY KEY(owner,key))')
    def put(self,owner,key,value,*,kind='preference',confirmed=False,source='user-confirmed',expires=None):
        if not owner:raise ValueError('Owner required')
        if not confirmed:raise ValueError('This lab requires explicit confirmation to save memory')
        allowed={'report_order':{'summary_first','evidence_first'},'detail':{'short','normal'}}
        if kind=='preference':
            if key not in allowed or value not in allowed[key]:raise ValueError('Only display preferences may be saved')
        elif kind=='episode':
            if not isinstance(value,dict) or not all(k in value for k in ('task_id','summary','evidence_ids')):
                raise ValueError('Episode must retain task and evidence pointers')
        else:raise ValueError('Unknown memory kind')
        ex=utc(expires) if expires else None
        with sqlite3.connect(self.path) as c:
            c.execute('INSERT INTO memory VALUES (?,?,?,?,?,?) ON CONFLICT(owner,key) DO UPDATE SET kind=excluded.kind,value=excluded.value,source=excluded.source,expires=excluded.expires',
                      (owner,key,kind,canonical(value),source,ex))
    def get(self,owner,*,now):
        now=utc(now)
        with sqlite3.connect(self.path) as c:
            rows=c.execute('SELECT key,kind,value,source,expires FROM memory WHERE owner=? AND (expires IS NULL OR expires>?) ORDER BY key',(owner,now)).fetchall()
        return [{'key':k,'kind':kind,'value':json.loads(v),'source':s,'expires':e} for k,kind,v,s,e in rows]
    def delete(self,owner,key):
        with sqlite3.connect(self.path) as c:
            return c.execute('DELETE FROM memory WHERE owner=? AND key=?',(owner,key)).rowcount
