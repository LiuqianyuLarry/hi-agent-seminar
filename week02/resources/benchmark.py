"""Run isolated, equal-work CPU/CUDA repetitions. Unavailable devices are recorded."""
import argparse,csv,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--devices',nargs='+',choices=['cpu','cuda'],default=['cpu','cuda'])
    p.add_argument('--repeats',type=int,default=3)
    p.add_argument('--steps',type=int,default=200)
    p.add_argument('--warmup',type=int,default=10)
    p.add_argument('--batch-size',type=int,default=16)
    p.add_argument('--block-size',type=int,default=64)
    p.add_argument('--threads',type=int,default=2)
    p.add_argument('--out',default='outputs/benchmark')
    a=p.parse_args()
    if a.repeats<1: p.error('repeats must be positive')
    root=Path(a.out).resolve();root.mkdir(parents=True,exist_ok=True)
    rows=[]
    for device in a.devices:
        for rep in range(1,a.repeats+1):
            folder=root/f'{device}_r{rep}'
            command=[sys.executable,str(ROOT/'train.py'),'--device',device,'--out',str(folder),
                     '--steps',str(a.steps),'--warmup',str(a.warmup),'--batch-size',str(a.batch_size),
                     '--block-size',str(a.block_size),'--threads',str(a.threads),'--no-checkpoint']
            proc=subprocess.run(command,cwd=ROOT,check=False)
            metrics_file=folder/'metrics.json'
            # Do not silently re-use old measurements when a subprocess fails.
            if proc.returncode not in (0,3):
                raise RuntimeError(f'{device} run {rep} failed (exit {proc.returncode}); inspect {folder}')
            m=json.loads(metrics_file.read_text())
            rows.append({'device':device,'repeat':rep,'status':m['status'],
                         'batch_size':a.batch_size,'context':a.block_size,
                         'elapsed_seconds':m.get('elapsed_seconds'),
                         'tokens_per_second':m.get('tokens_per_second'),
                         'final_val_loss':m.get('final_val_loss'),
                         'gpu_peak_allocated_bytes':m.get('gpu_peak_allocated_bytes'),
                         'process_rss_sampled_peak_bytes':m.get('process_rss_sampled_peak_bytes'),
                         'initial_weights_sha256':m.get('initial_weights_sha256'),
                         'training_batches_sha256':m.get('training_batches_sha256'),
                         'metrics_path':str(metrics_file.relative_to(root))})
            if m['status']=='unavailable': break
    successful=[r for r in rows if r['status']=='ok']
    for field in ['initial_weights_sha256','training_batches_sha256']:
        if len({r[field] for r in successful})>1:
            raise RuntimeError('Comparison is not equal-work: '+field)
    with (root/'benchmark_results.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    print('Saved',root/'benchmark_results.csv')
if __name__=='__main__': main()
