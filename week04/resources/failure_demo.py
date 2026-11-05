"""Bounded loop experiment with an independent, parent-process watchdog.
Never sends a live model request. Still bounded when a student's runtime is wrong.
"""
import argparse,csv,json,subprocess,sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='outputs/failure_compare')
    a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for label,scenario,guard in [('step_cap_only','repeat',0),('progress_guard','repeat',2),
                                 ('stop_when_complete','after_complete',2)]:
        destination=out/label
        cmd=[sys.executable,str(Path(__file__).with_name('app.py')),
             '--mode','scripted','--scenario',scenario,'--max-steps','6',
             '--max-no-progress',str(guard),'--total-seconds','10',
             '--out',str(destination)]
        try:
            p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=20)
            destination.mkdir(parents=True,exist_ok=True)
            (destination/'console.txt').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
            if not (destination/'run.json').exists() or p.returncode not in (0,1):
                raise ValueError('No valid run report was produced. Check the unfinished exercise or loop.')
            d=json.loads((destination/'run.json').read_text(encoding='utf-8'))
            rows.append({'condition':label,'mode':d['mode'],'status':d['status'],
                         'reason':d['reason'],'decisions':d['steps'],
                         'tool_attempts':d['tool_attempts'],'external_watchdog':False})
        except subprocess.TimeoutExpired:
            rows.append({'condition':label,'mode':'scripted','status':'test_failed',
                         'reason':'external_watchdog','decisions':'unknown',
                         'tool_attempts':'unknown','external_watchdog':True})
        except (OSError,ValueError) as exc:
            rows.append({'condition':label,'mode':'scripted','status':'test_failed',
                         'reason':str(exc),'decisions':'unknown',
                         'tool_attempts':'unknown','external_watchdog':False})
    with (out/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    print(json.dumps(rows,ensure_ascii=False,indent=2))
    return 1 if any(r['status']=='test_failed' for r in rows) else 0
if __name__=='__main__':raise SystemExit(main())
