"""Explicit alternatives: lexical TF-IDF demo OR a real local neural encoder.
The TF-IDF path is NOT a semantic model and never silently replaces one.
"""
from __future__ import annotations
from collections import Counter
import math,re
from pathlib import Path
from common import sha,canonical,checked_vector

STOP={'the','a','an','and','or','of','for','to','in','is','are','be','what','which','should','do','does','this','that','with','by','it','as','on','from','before'}
def terms(text):
    return [w for w in re.findall(r"[a-z0-9]+",text.lower()) if w not in STOP]

def cosine(a,b):
    if len(a)!=len(b): raise ValueError('Vector dimensions do not match')
    aa=sum(x*x for x in a);bb=sum(x*x for x in b)
    return sum(x*y for x,y in zip(a,b))/math.sqrt(aa*bb) if aa and bb else 0.0

class TfidfDemo:
    """Auditable non-neural lexical baseline for an offline classroom."""
    name='tfidf-demo'
    def fit(self,texts):
        self.vocab=sorted({w for text in texts for w in terms(text)})
        n=len(texts);df=Counter(w for text in texts for w in set(terms(text)))
        self.idf={w:math.log((1+n)/(1+df[w]))+1 for w in self.vocab}
        self.dimension=len(self.vocab)
        self.identity={'kind':self.name,'dimension':self.dimension,
            'space_hash':sha(canonical([self.vocab,self.idf]))}
        return self
    def encode(self,texts):
        out=[]
        for text in texts:
            counts=Counter(terms(text));v=[counts[w]*self.idf[w] for w in self.vocab]
            norm=math.sqrt(sum(x*x for x in v));out.append([x/norm for x in v] if norm else v)
        return out

class LocalSentenceEncoder:
    name='local-sentence'
    def __init__(self,model_path):
        p=Path(model_path or '').expanduser().resolve()
        if not model_path or not p.is_dir():
            raise ValueError('Set --model-path to a PRE-DOWNLOADED SentenceTransformer directory')
        from sentence_transformers import SentenceTransformer
        self.model=SentenceTransformer(str(p),local_files_only=True,device='cpu')
        self.dimension=self.model.get_sentence_embedding_dimension()
        # Bind vector space to local model bytes; do not mix different snapshots.
        hashes=[(str(f.relative_to(p)),sha(f.read_bytes())) for f in sorted(p.rglob('*')) if f.is_file() and '.cache' not in f.parts]
        self.identity={'kind':self.name,'dimension':self.dimension,'space_hash':sha(canonical(hashes))}
    def fit(self,texts): return self
    def encode(self,texts):
        vals=self.model.encode(texts,normalize_embeddings=True,show_progress_bar=False)
        return [checked_vector(v.tolist()) for v in vals]

def make_encoder(kind,texts,model_path=None):
    if kind=='tfidf-demo':return TfidfDemo().fit(texts)
    if kind=='local-sentence':return LocalSentenceEncoder(model_path).fit(texts)
    raise ValueError('Unknown encoder; no automatic fallback')
