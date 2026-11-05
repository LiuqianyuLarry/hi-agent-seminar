"""Create a screenshot-ready HTML trace from REAL run.json; no simulated success images."""
import argparse,json,html
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('run_json');a=p.parse_args()
    path=Path(a.run_json);data=json.loads(path.read_text(encoding='utf-8'))
    esc=lambda value:html.escape(str(value))
    rows=[]
    for e in data['trace']:
        if e['event'] not in {'decision','observation','verify','retry','stop','human_request'}:continue
        details={k:v for k,v in e.items() if k not in {'event_id','step','event','elapsed_s'}}
        rows.append(f"<tr><td>{e['step']}</td><td>{esc(e['event'])}</td><td><pre>{esc(json.dumps(details,ensure_ascii=False,indent=2))}</pre></td></tr>")
    body=f"""<!doctype html><html lang="zh"><meta charset="utf-8"><title>Week 4 Trace</title>
    <style>body{{font:18px system-ui;max-width:1200px;margin:35px auto;padding:20px;line-height:1.5}}
    table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid;padding:10px;vertical-align:top}}
    pre{{white-space:pre-wrap;overflow-wrap:anywhere;margin:0;font-size:15px}}</style>
    <h1>Week 4 | {esc(data['status'])} / {esc(data['reason'])}</h1>
    <p>Mode: <b>{esc(data['mode'])}</b> · Run: {esc(data['run_id'])}</p><p>{esc(data['warning'])}</p>
    <p>{esc(data['task']['question'])}</p><table><tr><th>Step</th><th>Event</th><th>Recorded data</th></tr>{''.join(rows)}</table></html>"""
    out=path.with_name('trace.html');out.write_text(body,encoding='utf-8');print(out)
if __name__=='__main__':main()
