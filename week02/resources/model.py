"""Week 2: a small causal, character-level GPT. Student starter with four TODOs.

Shapes: B=batch size, T=context length, C=embedding width, H=head width.
This intentionally explicit implementation is for learning, not peak throughput.
"""
from dataclasses import dataclass
import torch
from torch import nn

@dataclass(frozen=True)
class ModelConfig:
    vocab_size: int = 96
    block_size: int = 64
    embed_dim: int = 128
    num_heads: int = 4
    num_layers: int = 2

    def __post_init__(self):
        for name in ('vocab_size', 'block_size', 'embed_dim', 'num_heads', 'num_layers'):
            if getattr(self, name) < 1:
                raise ValueError(f'{name} must be positive')
        if self.embed_dim % self.num_heads:
            raise ValueError('embed_dim must be divisible by num_heads')

class AttentionHead(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        head_dim = config.embed_dim // config.num_heads
        self.query = nn.Linear(config.embed_dim, head_dim, bias=False)
        self.key = nn.Linear(config.embed_dim, head_dim, bias=False)
        self.value = nn.Linear(config.embed_dim, head_dim, bias=False)
        self.register_buffer('allowed', torch.ones(config.block_size, config.block_size,
                                                    dtype=torch.bool).tril())
        self.causal = True  # Only failure_demo.py disables this deliberately.

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # TODO W2.1: q/k/v -> scaled scores -> causal mask -> softmax over sources -> weighted values
        raise NotImplementedError("TODO W2.1: complete this step before full tests")
class MultiHeadAttention(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.heads = nn.ModuleList([AttentionHead(config) for _ in range(config.num_heads)])
        self.proj = nn.Linear(config.embed_dim, config.embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # TODO W2.2: Run each registered head; concatenate features; apply output projection
        raise NotImplementedError("TODO W2.2: complete this step before full tests")
class FeedForward(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.expand = nn.Linear(config.embed_dim, 4 * config.embed_dim)
        self.activation = nn.GELU()
        self.project = nn.Linear(4 * config.embed_dim, config.embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # TODO W2.3: expand -> GELU activation -> project
        raise NotImplementedError("TODO W2.3: complete this step before full tests")
class TransformerBlock(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.norm1 = nn.LayerNorm(config.embed_dim)
        self.attention = MultiHeadAttention(config)
        self.norm2 = nn.LayerNorm(config.embed_dim)
        self.feed_forward = FeedForward(config)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # TODO W2.4: Two pre-LayerNorm residual updates; use updated x for the second branch
        raise NotImplementedError("TODO W2.4: complete this step before full tests")
class MiniGPT(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.token_embedding = nn.Embedding(config.vocab_size, config.embed_dim)
        self.position_embedding = nn.Embedding(config.block_size, config.embed_dim)
        self.blocks = nn.Sequential(*[TransformerBlock(config) for _ in range(config.num_layers)])
        self.final_norm = nn.LayerNorm(config.embed_dim)
        self.lm_head = nn.Linear(config.embed_dim, config.vocab_size, bias=False)

    def forward(self, ids: torch.Tensor) -> torch.Tensor:
        if ids.ndim != 2 or ids.dtype != torch.long:
            raise ValueError('Expected a LongTensor of shape [B,T]')
        T = ids.size(1)
        if T < 1 or T > self.config.block_size:
            raise ValueError('Sequence length is outside the configured context window')
        positions = torch.arange(T, device=ids.device)
        x = self.token_embedding(ids) + self.position_embedding(positions)
        return self.lm_head(self.final_norm(self.blocks(x)))

    @torch.no_grad()
    def generate(self, ids: torch.Tensor, max_new_tokens: int = 100,
                 temperature: float = 0.8, seed: int = 100) -> torch.Tensor:
        if temperature <= 0 or max_new_tokens < 0:
            raise ValueError('temperature must be >0 and max_new_tokens must be >=0')
        was_training = self.training
        self.eval()
        gen = torch.Generator(device=ids.device).manual_seed(seed)
        try:
            for _ in range(max_new_tokens):
                context = ids[:, -self.config.block_size:]
                logits = self(context)[:, -1, :] / temperature
                new = torch.multinomial(logits.softmax(-1), 1, generator=gen)
                ids = torch.cat((ids, new), dim=1)
            return ids
        finally:
            self.train(was_training)
