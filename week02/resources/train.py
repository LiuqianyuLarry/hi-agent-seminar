"""CPU/CUDA training with explicit timing boundaries and auditable metadata.

Each run starts from the same CPU initialization, uses the same CPU-generated
batch order and performs the same warm-up updates. No automatic CPU fallback.
"""
import argparse, csv, gc, hashlib, json, os, platform, threading, time
from dataclasses import asdict
from pathlib import Path
import psutil
import torch
from torch.nn import functional as F
from data import ROOT, ALPHABET, encode, decode, load_tokens, make_batches, file_hash
from model import MiniGPT, ModelConfig
from preflight import report as environment_report

class RSSSampler:
    """Sample whole-process RSS, not tensor memory. Sampling can miss short peaks."""
    def __init__(self):
        self.proc = psutil.Process(os.getpid())
        self.baseline = self.proc.memory_info().rss
        self.peak = self.baseline
        self.done = threading.Event()
        self.thread = threading.Thread(target=self._sample, daemon=True)
    def _sample(self):
        while not self.done.wait(0.01):
            self.peak = max(self.peak, self.proc.memory_info().rss)
    def start(self): self.thread.start()
    def stop(self):
        self.peak = max(self.peak, self.proc.memory_info().rss)
        self.done.set(); self.thread.join()

def sync(device):
    if device.type == 'cuda': torch.cuda.synchronize(device)

def train_step(model, optimizer, x, y):
    optimizer.zero_grad(set_to_none=True)
    logits = model(x)
    loss = F.cross_entropy(logits.reshape(-1, logits.shape[-1]), y.reshape(-1))
    loss.backward(); optimizer.step()
    return loss.detach()

@torch.no_grad()
def evaluate(model, batches, device):
    model.eval()
    losses = []
    for x, y in batches:
        logits = model(x.to(device))
        losses.append(F.cross_entropy(logits.reshape(-1, logits.shape[-1]),
                                      y.to(device).reshape(-1)))
    value = torch.stack(losses).mean().item()
    model.train()
    return value

def tensor_hash(tensors):
    h=hashlib.sha256()
    for x in tensors: h.update(x.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()

def run(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if (out/'metrics.json').exists() and not a.overwrite:
        raise ValueError('Output already has metrics.json; choose another --out or use --overwrite')
    if min(a.steps, a.batch_size, a.threads) <= 0 or a.warmup < 0:
        raise ValueError('Invalid training counts')
    torch.set_num_threads(a.threads)
    torch.manual_seed(a.seed)
    if hasattr(torch.backends, 'cuda'):
        torch.backends.cuda.matmul.allow_tf32 = False
    if hasattr(torch.backends, 'cudnn'):
        torch.backends.cudnn.allow_tf32 = False
    config=ModelConfig(block_size=a.block_size, embed_dim=a.embed_dim,
                       num_heads=a.heads, num_layers=a.layers)
    model=MiniGPT(config)  # Always initialize on CPU first.
    initial_hash=tensor_hash(model.parameters())
    train=load_tokens('train'); val=load_tokens('val')
    cpu_batches=make_batches(train,a.batch_size,a.block_size,a.steps+a.warmup,a.seed+1)
    batch_hash=tensor_hash([v for batch in cpu_batches for v in batch])
    eval_train=make_batches(train,a.batch_size,a.block_size,4,a.seed+2)
    eval_val=make_batches(val,a.batch_size,a.block_size,4,a.seed+3)
    metadata={'status':'pending','device':a.device,'config':asdict(config),
              'batch_size':a.batch_size,'steps':a.steps,'warmup_updates':a.warmup,
              'total_updates':a.steps+a.warmup,'seed':a.seed,'threads':a.threads,
              'learning_rate':a.learning_rate,'precision':'FP32, TF32 disabled',
              'initial_weights_sha256':initial_hash,'training_batches_sha256':batch_hash,
              'train_sha256':file_hash(ROOT/'data/train.txt'),
              'val_sha256':file_hash(ROOT/'data/val.txt'),
              'environment':environment_report(),
              'timing_scope':'forward + CE loss + zero_grad + backward + optimizer.step; '
                             'pre-staged batches; excludes I/O, transfer, evaluation, generation, plotting',
              'rss_scope':'sampled process RSS during measured interval; 10 ms sampling',
              'gpu_scope':'peak PyTorch allocated bytes during measured interval; '
                          'includes resident model, optimizer, staged data; not total board memory',
              'synthetic_data':True, 'source_implementation':'explicit multi-head Python implementation'}
    if a.device == 'cuda' and not torch.cuda.is_available():
        metadata.update(status='unavailable', reason='CUDA device not available; no fabricated result')
        (out/'metrics.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        print('CUDA unavailable. Recorded as unavailable, not CPU.'); return 3
    device=torch.device(a.device)
    sampler=None
    try:
        model=model.to(device)
        optimizer=torch.optim.AdamW(model.parameters(),lr=a.learning_rate,weight_decay=0.01,
                                    foreach=False, fused=False)
        batches=[(x.to(device),y.to(device)) for x,y in cpu_batches]
        del cpu_batches; gc.collect()
        prompt=encode('M12 temperature').unsqueeze(0).to(device)
        before=decode(model.generate(prompt,max_new_tokens=100,seed=a.seed+99)[0].cpu())
        initial_train=evaluate(model,eval_train,device)
        initial_val=evaluate(model,eval_val,device)
        model.train()
        for x,y in batches[:a.warmup]: train_step(model,optimizer,x,y)
        optimizer.zero_grad(set_to_none=True)
        sync(device)
        if device.type=='cuda': torch.cuda.reset_peak_memory_stats(device)
        sampler=RSSSampler(); sampler.start()
        start=time.perf_counter()
        losses=[]
        for x,y in batches[a.warmup:]:
            losses.append(train_step(model,optimizer,x,y))  # detached scalar stays on device
        sync(device)
        elapsed=time.perf_counter()-start
        sampler.stop()
        gpu_peak=(torch.cuda.max_memory_allocated(device) if device.type=='cuda' else None)
        numbers=torch.stack(losses).cpu().tolist()  # after timing; avoids per-step .item() sync
        if not all(float('-inf') < n < float('inf') for n in numbers):
            raise FloatingPointError('Non-finite loss')
        final_train=evaluate(model,eval_train,device)
        final_val=evaluate(model,eval_val,device)
        after=decode(model.generate(prompt,max_new_tokens=100,seed=a.seed+99)[0].cpu())
        metadata.update(status='ok',elapsed_seconds=elapsed,
                        tokens_per_second=a.steps*a.batch_size*a.block_size/elapsed,
                        seconds_per_step=elapsed/a.steps,initial_train_eval_loss=initial_train,
                        initial_val_loss=initial_val,final_train_eval_loss=final_train,
                        final_val_loss=final_val,last_measured_step_loss=numbers[-1],
                        measured_tokens=a.steps*a.batch_size*a.block_size,
                        process_rss_baseline_bytes=sampler.baseline,
                        process_rss_sampled_peak_bytes=sampler.peak,
                        gpu_peak_allocated_bytes=gpu_peak,
                        parameter_count=sum(p.numel() for p in model.parameters()))
        with (out/'loss.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f);writer.writerow(['measured_step','total_update','loss'])
            writer.writerows((i+1,a.warmup+i+1,v) for i,v in enumerate(numbers))
        sample_text=('REAL EXECUTION ON SYNTHETIC DATA; NOT AN LLM API RESULT\n'
                     f'Device: {a.device}; generation temperature=0.8, seed={a.seed+99}\n'
                     '\nBEFORE TRAINING\n'+before+'\n\nAFTER TRAINING\n'+after+'\n'
                     '\nThis toy model is not a validated fault diagnosis system.\n')
        (out/'generated_samples.txt').write_text(sample_text,encoding='utf-8')
        if not a.no_checkpoint:
            state={k:v.detach().cpu() for k,v in model.state_dict().items()}
            torch.save({'config':asdict(config),'model':state,'alphabet':ALPHABET},out/'checkpoint.pt')
    except Exception as exc:
        if sampler is not None and sampler.thread.is_alive(): sampler.stop()
        metadata.update(status='error',error_type=type(exc).__name__,message=str(exc))
        (out/'metrics.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        raise
    (out/'metrics.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(json.dumps({k:metadata[k] for k in ['status','elapsed_seconds','tokens_per_second',
                     'initial_train_eval_loss','final_train_eval_loss','final_val_loss']},indent=2))
    return 0

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--device',choices=['cpu','cuda'],default='cpu')
    p.add_argument('--out',default='outputs/cpu')
    for name,default in [('steps',200),('warmup',10),('batch-size',16),('block-size',64),
                         ('embed-dim',128),('heads',4),('layers',2),('threads',2),('seed',4149)]:
        p.add_argument('--'+name,type=int,default=default)
    p.add_argument('--learning-rate',type=float,default=3e-4)
    p.add_argument('--overwrite',action='store_true')
    p.add_argument('--no-checkpoint',action='store_true')
    return p
if __name__=='__main__':
    raise SystemExit(run(parser().parse_args()))
