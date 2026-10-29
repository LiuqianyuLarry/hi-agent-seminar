"""Small task set. Replay is pipeline verification, never model tool-selection accuracy."""
import argparse,asyncio,csv,json
from pathlib import Path
from types import SimpleNamespace
from app import execute,ROOT

async def main(a):
    cases=json.loads((ROOT/'cases/tasks.json').read_text(encoding='utf-8'))
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True);rows=[]
    for case in cases:
        trace=await execute(SimpleNamespace(mode=a.mode,route=a.route,case=case['id'],
                                question=None,out=str(out/f"{case['id']}.json")))
        calls=trace.get('calls',[])
        actual=calls[0]['name'] if len(calls)==1 else None
        observed=trace.get('tool_result',{}).get('status','no_tool' if trace.get('status')=='no_tool' else 'pipeline_error')
        choice_match=actual==case['expected_tool']
        rows.append({'case':case['id'],'mode':a.mode,'route':a.route,
                     'expected_tool':case['expected_tool'],'actual_tool':actual,
                     'model_selection_match':choice_match if a.mode=='live' else 'NOT_APPLICABLE_SCRIPTED_REPLAY',
                     'expected_result_status':case['expected_status'],'observed_result_status':observed,
                     'pipeline_contract_matches':choice_match and observed==case['expected_status'],
                     'answer_factual_review':'PENDING_MANUAL_REVIEW' if a.mode=='live' else 'NOT_LLM_OUTPUT'})
    with (out/'evaluation.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    summary={'mode':a.mode,'count':len(rows),
             'pipeline_contract_matches':sum(r['pipeline_contract_matches'] for r in rows),
             'model_selection_match_fraction':(sum(r['model_selection_match'] for r in rows)/len(rows)
                                               if a.mode=='live' else None),
             'note':'Seven classroom tasks are not a general reliability benchmark; inspect arguments and answers separately.'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['replay','live'],required=True)
    p.add_argument('--route',choices=['local','mcp'],default='local');p.add_argument('--out',required=True)
    asyncio.run(main(p.parse_args()))
