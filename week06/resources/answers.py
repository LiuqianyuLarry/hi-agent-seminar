"""Evidence rendering and optional LLM wording. Citation existence is not entailment."""
from __future__ import annotations
from typing import Literal
from common import canonical

def template_answer(packet):
    """Deterministic extraction, NOT an LLM/RAG generation accuracy result."""
    claims=[]
    for e in packet['evidence']:
        p=e['payload']
        if e['type']=='document':
            claims.append({'kind':'quotation','text':p['text'],'evidence_ids':[e['id']]})
        elif p.get('statistics'):
            s=p['statistics']
            claims.append({'kind':'measurement','text':
                f"{p['machine_id']}: {p['count']} samples; mean {s['mean_c']:.1f} C; maximum {s['max_c']:.1f} C; "
                f"{s['exceed_count']}/{p['count']} ({100*s['sample_fraction']:.1f}%) strictly above {s['reference_c']:.1f} C. "
                'This is a sample fraction, not a time fraction or a fault probability.',
                'evidence_ids':[e['id']]})
        else:
            claims.append({'kind':'record','text':canonical(p),'evidence_ids':[e['id']]})
    if any(m['key']=='report_order' and m['value']=='evidence_first' for m in packet.get('preferences',[])):
        claims.sort(key=lambda c: 0 if c['kind']=='quotation' else 1)
    return {'claims':claims,'limitations':['Synthetic classroom data. Document applicability and claim support require review.'],
            'generation_mode':'template','semantic_support_verified':False}

def check_citations(answer,packet):
    ids={e['id'] for e in packet['evidence']};errors=[]
    for i,c in enumerate(answer.get('claims',[])):
        if not c.get('evidence_ids'):errors.append(f'claim {i}: missing evidence ID')
        for eid in c.get('evidence_ids',[]):
            if eid not in ids:errors.append(f'claim {i}: unknown evidence ID {eid}')
    return {'citations_resolve':not errors,'errors':errors,
            'scope':'ID existence only; NOT semantic support, correctness or source authenticity'}

def live_answer(packet,model):
    if not model:raise ValueError('Set DEEPSEEK_MODEL')
    from openai import OpenAI
    from pydantic import BaseModel,ConfigDict
    class Claim(BaseModel):
        model_config=ConfigDict(extra='forbid')
        kind:Literal['measurement','record','quotation','interpretation']
        text:str
        evidence_ids:list[str]
    class Answer(BaseModel):
        model_config=ConfigDict(extra='forbid')
        claims:list[Claim]
        limitations:list[str]
    import json
    import os
    client = OpenAI(base_url="https://api.deepseek.com", api_key=os.environ["DEEPSEEK_API_KEY"],
                    timeout=30, max_retries=0)
    schema = canonical(Answer.model_json_schema())
    response = client.chat.completions.create(
        model=model, response_format={"type": "json_object"}, max_tokens=1800,
        messages=[{"role": "system", "content": packet["rules"] + " Return JSON following this schema: " + schema},
                  {"role": "user", "content": canonical(packet)}])
    choice = response.choices[0]
    if choice.finish_reason != "stop" or not choice.message.content:
        raise ValueError("No complete answer was returned.")
    out = Answer.model_validate(json.loads(choice.message.content)).model_dump()
    if not out["claims"] or not check_citations(out, packet)["citations_resolve"]:
        raise ValueError("The answer needs claims with citations from this packet.")
    out.update(generation_mode="live", semantic_support_verified=False)
    return out
