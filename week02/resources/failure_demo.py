"""Deliberately injected failures, not naturally observed model failures."""
import argparse,json
from pathlib import Path
import torch
from torch.nn import functional as F
from model import ModelConfig,MiniGPT,AttentionHead

def run(kind):
    torch.set_num_threads(1);torch.manual_seed(4149)
    cfg=ModelConfig(block_size=12,embed_dim=32,num_heads=4,num_layers=1)
    m=MiniGPT(cfg)
    x=torch.randint(0,96,(2,12));y=torch.randint(0,96,(2,12))
    if kind=='no_causal_mask':
        m.eval();other=x.clone();other[:,8:]=(other[:,8:]+17)%96
        good=(m(x)[:,:8]-m(other)[:,:8]).abs().max().item()
        for module in m.modules():
            if isinstance(module,AttentionHead): module.causal=False
        bad=(m(x)[:,:8]-m(other)[:,:8]).abs().max().item()
        return {'injected':True,'failure':kind,'causal_prefix_max_difference':good,
                'unmasked_prefix_max_difference':bad,'fault_detected':bad>1e-6}
    opt=torch.optim.AdamW(m.parameters(),lr=0.01)
    losses=[]
    for _ in range(15):
        opt.zero_grad(set_to_none=True)
        loss=F.cross_entropy(m(x).reshape(-1,96),y.reshape(-1));loss.backward()
        # Deliberately omit opt.step().
        losses.append(loss.item())
    return {'injected':True,'failure':kind,'initial_loss':losses[0],'last_loss':losses[-1],
            'fault_detected':abs(losses[0]-losses[-1])<1e-9}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',choices=['no_causal_mask','no_optimizer_step'],required=True)
    p.add_argument('--out',default='outputs/injected_failure.json');a=p.parse_args()
    result=run(a.case);path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
