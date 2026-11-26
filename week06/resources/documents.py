"""Heading-aware chunks, source checksums and exact line spans."""
from __future__ import annotations
from pathlib import Path
from common import ROOT,load,sha,canonical,utc

def chunk_document(meta,root=None,max_words=110,overlap_words=20):
    if max_words<10 or overlap_words<0 or overlap_words>=max_words:
        raise ValueError('Require max_words>=10 and 0<=overlap<max_words')
    root=Path(root or ROOT/'data').resolve()
    path=(root/meta['path']).resolve()
    if not path.is_relative_to(root): raise ValueError('Document path outside corpus')
    raw=path.read_bytes()
    if sha(raw)!=meta['sha256']: raise ValueError('Source changed; update manifest and rebuild index')
    lines=raw.decode('utf-8').splitlines()
    starts=[i for i,line in enumerate(lines) if line.startswith('## ')]
    chunks=[]
    for sec,a in enumerate(starts):
        b=starts[sec+1] if sec+1<len(starts) else len(lines)
        body_lines=[i for i in range(a+1,b) if lines[i].strip()]
        if not body_lines: continue
        tokens=[]
        for i in body_lines:
            tokens.extend((word,i+1) for word in lines[i].split())
        step=max_words-overlap_words
        for offset in range(0,len(tokens),step):
            part=tokens[offset:offset+max_words]
            body=' '.join(w for w,_ in part)
            anchor=f"{meta['doc_id']}:{meta['version']}:{sec}:{offset}:{meta['sha256']}"
            chunks.append({**meta,'chunk_id':'chunk:'+sha(anchor)[:18],
                'section':lines[a][3:].strip(),'text':body,
                'line_start':part[0][1],'line_end':part[-1][1],
                'source_ref':f"{meta['path']}:L{part[0][1]}-L{part[-1][1]}",
                'word_offset':offset})
            if offset+max_words>=len(tokens): break
    return chunks

def load_chunks(root=None,max_words=110,overlap_words=20):
    root=Path(root or ROOT/'data')
    return [c for meta in load(root/'documents.json')
            for c in chunk_document(meta,root,max_words,overlap_words)]

# W6.2_BEGIN
def eligible(chunk, *, machine_id,model_code,as_of,role='student'):
    """Hard applicability checks happen BEFORE top-k, not in a prompt afterwards."""
    if chunk['machine_id']!=machine_id or chunk['model_code']!=model_code: return False
    if chunk['access']!='public' and role!='teacher': return False
    when=utc(as_of)
    return utc(chunk['valid_from'])<=when and (chunk['valid_to'] is None or when<=utc(chunk['valid_to']))
# W6.2_END

def public_evidence(c):
    return {'id':c['chunk_id'],'type':'document','payload':{k:c[k] for k in
        ('doc_id','machine_id','model_code','title','section','version','valid_from','valid_to','source_ref','sha256','text')}}
