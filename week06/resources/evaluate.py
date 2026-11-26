"""Retrieval evaluation uses teacher qrels ONLY HERE, never in the retriever or prompt.
Relevant unit: (document, section). Repeated chunks of one section count once.
Precision@k denominator is k; missing slots count as nonrelevant.
"""
from __future__ import annotations
import argparse,os,csv
from pathlib import Path
from common import ROOT,load,save
from documents import load_chunks
from retrieval import Retriever

def measures(evidence,gold,k):
    units=[]
    for e in evidence:
        p=e['payload'];u=p['doc_id']+'#'+p['section']
        if u not in units:units.append(u)
    units=units[:k];g=set(gold);hits=sum(u in g for u in units)
    return {'precision_at_k':hits/k,'recall_at_k':hits/len(g) if g else None,
        'mrr':next((1/(i+1) for i,u in enumerate(units) if u in g),0) if g else None,
        'hits':hits,'ranked_units':units,'gold_units':sorted(g),
        'no_answer_case':not bool(g),'candidates_when_no_answer':len(units) if not g else None}

def evaluate(encoder='tfidf-demo',model_path=None,out='outputs/evaluation',k=3):
    ret=Retriever(load_chunks(),encoder,model_path);rows=[]
    for filtered in (False,True):
        for method in ('keyword','vector','hybrid'):
            for q in load(ROOT/'evaluation/queries.json'):
                ev,tr=ret.search(q['question'],machine_id=q['machine_id'],model_code=q['model_code'],as_of=q['as_of'],k=k,method=method,filter_scope=filtered)
                rows.append({'query_id':q['id'],'filtered_scope':filtered,'method':method,'encoder':encoder,
                            **measures(ev,q['relevant_units'],k),'selected':[e['id'] for e in ev]})
    p=Path(out);p.mkdir(parents=True,exist_ok=True);save(p/'retrieval_results.json',rows)
    fields=['query_id','filtered_scope','method','encoder','precision_at_k','recall_at_k','mrr','hits','no_answer_case']
    with (p/'retrieval_results.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    return rows
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--encoder',choices=['tfidf-demo','local-sentence'],default='tfidf-demo');p.add_argument('--model-path',default=os.getenv('W6_MODEL_PATH'));p.add_argument('--out',default='outputs/evaluation');a=p.parse_args()
    rows=evaluate(a.encoder,a.model_path,a.out);print('Saved',len(rows),'retrieval trials; no LLM correctness inferred.')
