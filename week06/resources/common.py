"""Shared representations. No external service is silently replaced."""
from __future__ import annotations
import hashlib, json, math, re
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def canonical(x):
    return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
def sha(x):
    return hashlib.sha256((x if isinstance(x,bytes) else str(x).encode('utf-8'))).hexdigest()
def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def utc(text):
    d=datetime.fromisoformat(text.replace('Z','+00:00'))
    if d.tzinfo is None: raise ValueError('Timestamp must include timezone')
    return d.astimezone(timezone.utc).isoformat()
def validate_task(t):
    x=dict(t)
    if x['mode'] not in {'sql','rag','combined'}: raise ValueError('Unknown task mode')
    if x.get('sql_kind','readings') not in {'readings','maintenance','faults'}: raise ValueError('Unknown SQL kind')
    if not re.fullmatch(r'CONV-[1-9][0-9]*',x['machine_id']): raise ValueError('Invalid machine id')
    x['start'],x['end'],x['as_of']=utc(x['start']),utc(x['end']),utc(x['as_of'])
    if x['start']>=x['end']: raise ValueError('start must be earlier than end')
    if not isinstance(x['question'],str) or not x['question'].strip(): raise ValueError('Question required')
    return x

def checked_vector(v):
    out=[float(a) for a in v]
    if not out or not all(math.isfinite(a) for a in out): raise ValueError('Invalid vector')
    return out
