"""Environment check: does not train or download anything."""
import importlib.metadata as md, json, platform, sys
from pathlib import Path

def report():
    out = {'python': sys.version, 'platform': platform.platform(), 'packages': {}}
    for name in ['torch', 'numpy', 'matplotlib', 'pytest', 'psutil']:
        try: out['packages'][name] = md.version(name)
        except md.PackageNotFoundError: out['packages'][name] = 'NOT INSTALLED'
    try:
        import torch
        out.update(cuda_available=torch.cuda.is_available(), cuda_build=torch.version.cuda,
                   cpu_threads=torch.get_num_threads())
        if torch.cuda.is_available():
            out['gpu_name'] = torch.cuda.get_device_name(0)
    except ImportError:
        out['cuda_available'] = False
    root=Path(__file__).resolve().parent
    out['data_present'] = all((root/'data'/f'{s}.txt').exists() for s in ['train','val'])
    return out
if __name__ == '__main__': print(json.dumps(report(), ensure_ascii=False, indent=2))
