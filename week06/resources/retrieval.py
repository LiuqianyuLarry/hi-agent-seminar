"""BM25 + vector retrieval + RRF; optional actual CrossEncoder reranking."""
from __future__ import annotations
from collections import Counter
import math
from common import sha,canonical
from documents import eligible,public_evidence
from embeddings import terms,cosine,make_encoder

def bm25_rank(query,chunks):
    if not chunks:return []
    docs=[terms(c['title']+' '+c['section']+' '+c['text']) for c in chunks]
    avg=sum(map(len,docs))/len(docs);df=Counter(w for d in docs for w in set(d));out=[]
    q=set(terms(query))
    for c,d in zip(chunks,docs):
        tf=Counter(d);score=0.0
        for w in q:
            if tf[w]:
                idf=math.log(1+(len(docs)-df[w]+0.5)/(df[w]+0.5))
                score+=idf*tf[w]*2.5/(tf[w]+1.5*(0.25+0.75*len(d)/max(avg,1)))
        if score>0:out.append((c['chunk_id'],score))
    return sorted(out,key=lambda x:(-x[1],x[0]))

# W6.3_BEGIN
def rrf(rankings,k=60):
    """Fuse ranked IDs, NOT raw BM25/cosine values. Rank starts at one."""
    # Add one contribution for each distinct passage in each list.
    raise NotImplementedError("Write the rank fusion here.")
# W6.3_END

def rerank_local(query,ranked,chunks):
    """Explainable title/section token-coverage heuristic; NOT neural reranking."""
    q=set(terms(query));byid={c['chunk_id']:c for c in chunks}
    order={cid:i for i,cid in enumerate(ranked)}
    return sorted(ranked,key=lambda cid:(-len(q&set(terms(byid[cid]['section']+' '+byid[cid]['title']))),order[cid]))

def rerank_cross_encoder(query,ranked,chunks,model_path):
    from pathlib import Path
    if not model_path or not Path(model_path).is_dir(): raise ValueError('Local reranker directory required')
    from sentence_transformers import CrossEncoder
    model=CrossEncoder(str(model_path),local_files_only=True,device='cpu')
    byid={c['chunk_id']:c for c in chunks}
    scores=model.predict([(query,byid[cid]['text']) for cid in ranked],show_progress_bar=False)
    return [cid for _,cid in sorted(zip(scores,ranked),key=lambda x:(-float(x[0]),x[1]))]

class Retriever:
    def __init__(self,chunks,encoder='tfidf-demo',model_path=None):
        self.chunks=chunks
        texts=[c['title']+' '+c['section']+' '+c['text'] for c in chunks]
        self.encoder=make_encoder(encoder,texts,model_path)
        self.vectors=dict(zip([c['chunk_id'] for c in chunks],self.encoder.encode(texts)))
        self.corpus_hash=sha(canonical(chunks))
    def search(self,query,*,machine_id,model_code,as_of,role='student',k=3,method='hybrid',filter_scope=True,
               reranker='none',reranker_path=None,candidate_k=12):
        if k<1 or candidate_k<k:raise ValueError('Require candidate_k>=k>=1')
        # Even failure experiment keeps the role restriction. filter_scope=False
        # removes only machine/version scope, never grants restricted access.
        candidates=[c for c in self.chunks if (c['access']=='public' or role=='teacher') and
            (not filter_scope or eligible(c,machine_id=machine_id,model_code=model_code,as_of=as_of,role=role))]
        lex=bm25_rank(query,candidates)[:candidate_k]
        q=self.encoder.encode([query])[0]
        vector=sorted([(c['chunk_id'],cosine(q,self.vectors[c['chunk_id']])) for c in candidates],key=lambda x:(-x[1],x[0]))
        vector=[p for p in vector if p[1]>0][:candidate_k]
        if method=='keyword': order=[cid for cid,_ in lex]
        elif method=='vector':order=[cid for cid,_ in vector]
        elif method=='hybrid':order=rrf([[cid for cid,_ in lex],[cid for cid,_ in vector]])
        else: raise ValueError('Unknown retrieval method')
        if reranker=='heuristic':order=rerank_local(query,order,candidates)
        elif reranker=='cross-encoder':order=rerank_cross_encoder(query,order,candidates,reranker_path)
        elif reranker!='none':raise ValueError('Unknown reranker')
        byid={c['chunk_id']:c for c in candidates}
        evidence=[public_evidence(byid[cid]) for cid in order[:k]]
        trace={'backend':'inprocess','encoder':self.encoder.identity,'method':method,'reranker':reranker,
            'filtered_scope':filter_scope,'candidate_count':len(candidates),'corpus_hash':self.corpus_hash,
            'keyword_ranking':lex,'vector_ranking':vector,'returned_ids':[e['id'] for e in evidence]}
        return evidence,trace
