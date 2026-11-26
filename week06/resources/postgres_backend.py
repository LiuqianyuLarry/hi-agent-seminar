"""Real PostgreSQL + pgvector path. No SQLite fallback when connection fails."""
from __future__ import annotations
import os,json
from contextlib import contextmanager
from datetime import datetime
from common import canonical,validate_task,utc
from database import finish_sql
from documents import public_evidence
from embeddings import terms
from retrieval import rrf,rerank_local,rerank_cross_encoder

@contextmanager
def pg_connection(dsn=None,readonly=True):
    import psycopg
    from psycopg.rows import dict_row
    url=dsn or os.getenv('DATABASE_URL')
    if not url:raise ValueError('Set DATABASE_URL for the classroom database')
    con=psycopg.connect(url,row_factory=dict_row,connect_timeout=5)
    try:
        if readonly:con.execute('SET TRANSACTION READ ONLY')
        con.execute('SET LOCAL search_path = w6, public')
        con.execute("SET LOCAL statement_timeout = '8000ms'")
        yield con
        con.commit()
    except Exception:
        con.rollback();raise
    finally:con.close()

def rows_json(rows):
    return [{k:utc(v.isoformat()) if isinstance(v,datetime) else v for k,v in r.items()} for r in rows]

class PgBackend:
    def __init__(self,dsn=None):self.dsn=dsn
    def machine_meta(self,machine_id):
        with pg_connection(self.dsn) as con:
            row=con.execute('SELECT * FROM machine WHERE machine_id=%s',(machine_id,)).fetchone()
        if not row:raise ValueError('Unknown machine')
        return row
    def query(self,task):
        t=validate_task(task);self.machine_meta(t['machine_id']);kind=t.get('sql_kind','readings')
        params=(t['machine_id'],t['start'],t['end'])
        with pg_connection(self.dsn) as con:
            if kind=='readings':
                rows=con.execute('SELECT r.reading_id,r.machine_id,r.ts,r.temperature_c,m.model_code,m.reference_c,m.spec_version FROM sensor_reading r JOIN machine m ON r.machine_id=m.machine_id WHERE r.machine_id=%s AND r.ts>=%s::timestamptz AND r.ts<%s::timestamptz ORDER BY r.ts,r.reading_id',params).fetchall()
            elif kind=='maintenance':rows=con.execute('SELECT * FROM maintenance_event WHERE machine_id=%s AND ts>=%s::timestamptz AND ts<%s::timestamptz ORDER BY ts,event_id',params).fetchall()
            else:rows=con.execute('SELECT * FROM fault_record WHERE machine_id=%s AND ts>=%s::timestamptz AND ts<%s::timestamptz ORDER BY ts,fault_id',params).fetchall()
        return finish_sql(rows_json(rows),t,kind)
    def search(self,retriever,query,*,machine_id,model_code,as_of,role='student',k=3,method='hybrid',
               filter_scope=True,reranker='none',reranker_path=None,candidate_k=12):
        if candidate_k<k or k<1:raise ValueError('Invalid retrieval limits')
        where="(access='public' OR %s='teacher')";params=[role]
        if filter_scope:
            where+=' AND machine_id=%s AND model_code=%s AND valid_from<=%s::timestamptz AND (valid_to IS NULL OR %s::timestamptz<valid_to)'
            params += [machine_id,model_code,utc(as_of),utc(as_of)]
        vector=canonical(retriever.encoder.encode([query])[0])
        search_terms=' | '.join(sorted(set(terms(query))))
        with pg_connection(self.dsn) as con:
            meta=con.execute("SELECT value FROM index_meta WHERE key='manifest'").fetchone()
            expected={'encoder':retriever.encoder.identity,'corpus_hash':retriever.corpus_hash}
            if meta is None or meta['value']!=expected:raise ValueError('Postgres index/model/corpus mismatch. Rebuild explicitly.')
            vec=con.execute('SELECT chunk_id, 1-(embedding <=> %s::vector) AS score FROM document_chunk WHERE '+where+' ORDER BY embedding <=> %s::vector,chunk_id LIMIT %s',
                            [vector]+params+[vector,candidate_k]).fetchall()
            vec=[(r['chunk_id'],float(r['score'])) for r in vec if r['score'] is not None and r['score']>0]
            lex=[]
            if search_terms:
                rows=con.execute("SELECT chunk_id,ts_rank_cd(search_text,to_tsquery('simple',%s)) AS score FROM document_chunk WHERE "+where+" AND search_text @@ to_tsquery('simple',%s) ORDER BY score DESC,chunk_id LIMIT %s",
                    [search_terms]+params+[search_terms,candidate_k]).fetchall()
                lex=[(r['chunk_id'],float(r['score'])) for r in rows]
            if method=='vector':order=[cid for cid,_ in vec]
            elif method=='keyword':order=[cid for cid,_ in lex]
            elif method=='hybrid':order=rrf([[cid for cid,_ in lex],[cid for cid,_ in vec]])
            else:raise ValueError('Unknown retrieval method')
            if reranker=='heuristic':order=rerank_local(query,order,retriever.chunks)
            elif reranker=='cross-encoder':order=rerank_cross_encoder(query,order,retriever.chunks,reranker_path)
            elif reranker!='none':raise ValueError('Unknown reranker')
            byid={c['chunk_id']:c for c in retriever.chunks}
            evidence=[public_evidence(byid[cid]) for cid in order[:k]]
        return evidence,{'backend':'postgres-pgvector','keyword_algorithm':'PostgreSQL ts_rank_cd; not BM25',
             'encoder':retriever.encoder.identity,'corpus_hash':retriever.corpus_hash,'method':method,
             'reranker':reranker,'filtered_scope':filter_scope,'keyword_ranking':lex,'vector_ranking':vec,
             'returned_ids':[e['id'] for e in evidence]}
