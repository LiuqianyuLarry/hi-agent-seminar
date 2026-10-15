"""Throughput sweep: different B means different token budgets; do not rank learning by loss."""
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--device',choices=['cpu','cuda'],default='cpu')
    p.add_argument('--out',default='outputs/batch_sweep');p.add_argument('--steps',type=int,default=50)
    a=p.parse_args()
    for b in [1,8,16]:
        subprocess.run([sys.executable,str(ROOT/'benchmark.py'),'--devices',a.device,'--repeats','1',
                        '--steps',str(a.steps),'--batch-size',str(b),'--out',str(Path(a.out)/f'B{b}')],check=True)
