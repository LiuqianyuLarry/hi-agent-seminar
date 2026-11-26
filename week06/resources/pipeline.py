"""Explicit teaching workflow: task route is provided, not an LLM planning score."""
from __future__ import annotations
import os,time
from datetime import datetime,timezone
from common import validate_task,ROOT,sha,canonical
from database import query_engineering,machine_meta
from documents import load_chunks
from retrieval import Retriever
from memory import MemoryStore
from context import select_context,evidence_hash
from answers import template_answer,live_answer,check_citations

def run_task(task,*,db='work/engineering.sqlite',memory_db='work/memory.sqlite',backend='sqlite',
             encoder='tfidf-demo',model_path=None,method='hybrid',filter_scope=True,
             reranker='none',reranker_path=None,budget_bytes=10000,k=3,generation='template',model=None,
             owner='student01',role='student',chunks=None):
    t=validate_task(task);start=time.perf_counter();ev=[];trace=[]
    if backend=='sqlite':
        meta=machine_meta(db,t['machine_id'])
        sql_call=lambda:query_engineering(db,t)
    elif backend=='postgres':
        from postgres_backend import PgBackend
        pg=PgBackend();meta=pg.machine_meta(t['machine_id']);sql_call=lambda:pg.query(t)
    else:raise ValueError('Unknown backend; no fallback')
    if t['mode'] in {'sql','combined'}:
        evidence=sql_call();ev.append(evidence)
        trace.append({'stage':'sql','id':evidence['id'],'count':evidence['payload']['count']})
    if t['mode'] in {'rag','combined'}:
        collection=chunks if chunks is not None else load_chunks()
        retriever=Retriever(collection,encoder,model_path)
        settings=dict(machine_id=t['machine_id'],model_code=meta['model_code'],as_of=t['as_of'],role=role,k=k,
                      method=method,filter_scope=filter_scope,reranker=reranker,reranker_path=reranker_path)
        if backend=='postgres': docs,rtrace=pg.search(retriever,t['question'],**settings)
        else:docs,rtrace=retriever.search(t['question'],**settings)
        ev.extend(docs);trace.append({'stage':'retrieval',**rtrace})
    now=datetime.now(timezone.utc).isoformat()
    memories=MemoryStore(memory_db).get(owner,now=now)
    packet,dropped=select_context(t,ev,memories,budget_bytes=budget_bytes)
    used=packet['evidence'];has_docs=any(e['type']=='document' for e in used)
    sql=next((e for e in used if e['type']=='sql'),None)
    missing=[]
    if t['mode'] in {'rag','combined'} and not has_docs:missing.append('document_evidence')
    if t['mode']=='combined' and (sql is None or sql['payload']['count']==0):missing.append('observed_readings')
    if missing:
        answer={'claims':[],'limitations':['Insufficient evidence: '+', '.join(missing)],
                'generation_mode':generation,'semantic_support_verified':False}
    elif generation=='template':answer=template_answer(packet)
    elif generation=='live':answer=live_answer(packet,model or os.getenv('DEEPSEEK_MODEL'))
    else:raise ValueError('Unknown generation mode')
    return {'status':'insufficient_evidence' if missing else 'ready_for_review',
        'task':t,'task_routing':'explicit task mode; not autonomous planning',
        'backend':backend,'encoder':encoder if t['mode']!='sql' else 'not_used',
        'generation':generation,'owner':owner,'trace':trace,'context':packet,'excluded':dropped,
        'evidence_hash':evidence_hash(packet),'answer':answer,'citation_check':check_citations(answer,packet),
        'elapsed_seconds':time.perf_counter()-start,
        'limitations':['Citation checks establish ID existence, not semantic support.',
          'tfidf-demo is lexical, not a neural semantic encoder.','All source data are synthetic.']}
