"""Initialize ONLY the classroom w6 schema. Use a dedicated admin DSN."""
from __future__ import annotations
import argparse,os,json
from database import readonly
from documents import load_chunks
from retrieval import Retriever
from common import canonical

def initialize(sqlite_db,encoder,model_path,reset=False):
    import psycopg
    from psycopg.types.json import Jsonb
    url=os.getenv('W6_ADMIN_DATABASE_URL')
    if not url:raise ValueError('Set W6_ADMIN_DATABASE_URL to a dedicated classroom database')
    ret=Retriever(load_chunks(),encoder,model_path);dim=ret.encoder.dimension
    if not isinstance(dim,int) or not 1<=dim<=16000:raise ValueError('Unsupported dimension')
    with psycopg.connect(url,connect_timeout=5) as con:
        con.execute('CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public')
        exists=con.execute("SELECT 1 FROM pg_namespace WHERE nspname='w6'").fetchone()
        if exists and not reset:raise ValueError('w6 schema exists. --reset deletes ONLY the classroom w6 schema.')
        if exists:con.execute('DROP SCHEMA w6 CASCADE')
        con.execute('CREATE SCHEMA w6');con.execute('SET LOCAL search_path=w6,public')
        con.execute('CREATE TABLE machine(machine_id TEXT PRIMARY KEY,model_code TEXT NOT NULL,reference_c DOUBLE PRECISION NOT NULL,spec_version TEXT NOT NULL)')
        con.execute('CREATE TABLE sensor_reading(reading_id TEXT PRIMARY KEY,machine_id TEXT REFERENCES machine(machine_id),ts TIMESTAMPTZ NOT NULL,temperature_c DOUBLE PRECISION NOT NULL,UNIQUE(machine_id,ts))')
        con.execute('CREATE INDEX sensor_window ON sensor_reading(machine_id,ts)')
        con.execute('CREATE TABLE maintenance_event(event_id TEXT PRIMARY KEY,machine_id TEXT REFERENCES machine(machine_id),ts TIMESTAMPTZ NOT NULL,action TEXT NOT NULL,outcome TEXT NOT NULL)')
        con.execute("CREATE TABLE fault_record(fault_id TEXT PRIMARY KEY,machine_id TEXT REFERENCES machine(machine_id),ts TIMESTAMPTZ NOT NULL,reported_symptom TEXT NOT NULL,confirmation_status TEXT CHECK(confirmation_status IN ('reported','confirmed','ruled_out')),root_cause TEXT)")
        # Table names are a fixed developer allowlist; values always bound.
        with readonly(sqlite_db) as sq:
            for table in ('machine','sensor_reading','maintenance_event','fault_record'):
                rows=sq.execute('SELECT * FROM '+table).fetchall()
                if rows:
                    marks=','.join(['%s']*len(rows[0]))
                    with con.cursor() as cur:cur.executemany('INSERT INTO '+table+' VALUES ('+marks+')',[tuple(r) for r in rows])
        con.execute('CREATE TABLE index_meta(key TEXT PRIMARY KEY,value JSONB NOT NULL)')
        con.execute('CREATE TABLE document_chunk(chunk_id TEXT PRIMARY KEY,doc_id TEXT NOT NULL,machine_id TEXT NOT NULL,model_code TEXT NOT NULL,valid_from TIMESTAMPTZ NOT NULL,valid_to TIMESTAMPTZ,access TEXT NOT NULL,content JSONB NOT NULL,search_text TSVECTOR NOT NULL,embedding vector('+str(dim)+') NOT NULL)')
        for c in ret.chunks:
            text=c['title']+' '+c['section']+' '+c['text']
            con.execute("INSERT INTO document_chunk VALUES (%s,%s,%s,%s,%s,%s,%s,%s,to_tsvector('simple',%s),%s::vector)",
                (c['chunk_id'],c['doc_id'],c['machine_id'],c['model_code'],c['valid_from'],c['valid_to'],c['access'],Jsonb(c),text,canonical(ret.vectors[c['chunk_id']])))
        con.execute('CREATE INDEX doc_fts ON document_chunk USING gin(search_text)')
        con.execute('CREATE INDEX doc_scope ON document_chunk(machine_id,model_code,valid_from)')
        con.execute('INSERT INTO index_meta VALUES (%s,%s)',('manifest',Jsonb({'encoder':ret.encoder.identity,'corpus_hash':ret.corpus_hash})))
        # Exact vector search intentionally used for this tiny corpus. HNSW is not mandatory.
    return {'chunks':len(ret.chunks),'dimension':dim,'encoder':ret.encoder.identity}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',default='work/engineering.sqlite');p.add_argument('--encoder',choices=['tfidf-demo','local-sentence'],default='local-sentence');p.add_argument('--model-path',default=os.getenv('W6_MODEL_PATH'));p.add_argument('--reset',action='store_true')
    a=p.parse_args();print(initialize(a.db,a.encoder,a.model_path,a.reset))
