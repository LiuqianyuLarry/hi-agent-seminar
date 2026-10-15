"""Plot only measurements that actually exist. Never synthesize a GPU bar."""
import argparse,csv,json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def plot_single(root):
    with (root/'loss.csv').open() as f: rows=list(csv.DictReader(f))
    fig,ax=plt.subplots(figsize=(8,4.5))
    ax.plot([int(r['total_update']) for r in rows],[float(r['loss']) for r in rows])
    ax.set(xlabel='Total training updates (includes warm-up)',ylabel='Cross-entropy loss',
           title='Measured training steps; synthetic logs')
    fig.tight_layout();fig.savefig(root/'loss_curve.png',dpi=160);plt.close(fig)

def main():
    p=argparse.ArgumentParser();p.add_argument('folder');a=p.parse_args();root=Path(a.folder)
    if (root/'loss.csv').exists(): plot_single(root)
    elif (root/'benchmark_results.csv').exists():
        with (root/'benchmark_results.csv').open() as f: rows=list(csv.DictReader(f))
        valid=[r for r in rows if r['status']=='ok']
        if not valid: raise ValueError('No successful measurements to plot')
        groups={}
        for r in valid:
            groups.setdefault(r['device'],[]).append(float(r['tokens_per_second']))
            plot_single(root/Path(r['metrics_path']).parent)
        fig,ax=plt.subplots(figsize=(7,4.5))
        names=list(groups)
        medians=[statistics.median(groups[n]) for n in names]
        ax.bar(names,medians)
        for i,n in enumerate(names): ax.text(i,medians[i],f'n={len(groups[n])}',ha='center',va='bottom')
        ax.set(xlabel='Measured device',ylabel='Training token positions / second',
               title='Median training throughput; unavailable devices omitted')
        fig.tight_layout();fig.savefig(root/'throughput_comparison.png',dpi=160);plt.close(fig)
    else: raise ValueError('Expected loss.csv or benchmark_results.csv')
    print('Plots saved to',root)
if __name__=='__main__': main()
