"""Fixed character vocabulary; validation records are never used for optimization."""
from pathlib import Path
import hashlib
import torch

ROOT = Path(__file__).resolve().parent
ALPHABET = ''.join(chr(i) for i in range(32, 127)) + '\n'
STOI = {c: i for i, c in enumerate(ALPHABET)}

def encode(text: str) -> torch.Tensor:
    unknown = sorted(set(text) - set(ALPHABET))
    if unknown:
        raise ValueError(f'Unsupported characters: {unknown[:10]!r}; use provided ASCII logs')
    return torch.tensor([STOI[c] for c in text], dtype=torch.long)

def decode(ids) -> str:
    return ''.join(ALPHABET[int(i)] for i in ids)

def load_tokens(split: str) -> torch.Tensor:
    if split not in {'train', 'val'}:
        raise ValueError('split must be train or val')
    return encode((ROOT / 'data' / f'{split}.txt').read_text(encoding='utf-8'))

def make_batches(tokens, batch_size, context, count, seed):
    if min(batch_size, context, count) < 1 or len(tokens) <= context:
        raise ValueError('Invalid batch settings or insufficient text')
    gen = torch.Generator().manual_seed(seed)
    offsets = torch.arange(context)
    batches = []
    for _ in range(count):
        starts = torch.randint(len(tokens) - context, (batch_size,), generator=gen)
        indices = starts[:, None] + offsets
        batches.append((tokens[indices], tokens[indices + 1]))
    return batches

def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
