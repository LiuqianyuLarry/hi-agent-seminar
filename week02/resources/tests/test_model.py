import pytest,torch
from torch.nn import functional as F
from model import ModelConfig,AttentionHead,MultiHeadAttention,FeedForward,TransformerBlock,MiniGPT
from data import ALPHABET,encode,decode,load_tokens,make_batches,ROOT

@pytest.fixture(autouse=True)
def setup():
    torch.set_num_threads(1);torch.manual_seed(7)

@pytest.fixture
def cfg(): return ModelConfig(block_size=12,embed_dim=32,num_heads=4,num_layers=1)

def test_vocabulary_and_round_trip():
    assert len(ALPHABET)==96
    assert decode(encode('M12 temperature=97 C.\n'))=='M12 temperature=97 C.\n'

def test_data_disjoint_and_shift():
    train=set((ROOT/'data/train.txt').read_text().splitlines())
    val=set((ROOT/'data/val.txt').read_text().splitlines())
    assert train and val and not train.intersection(val)
    x,y=make_batches(load_tokens('train'),2,12,1,5)[0]
    assert torch.equal(x[:,1:],y[:,:-1])

def test_config_rejects_nondivisible_width():
    with pytest.raises(ValueError):ModelConfig(embed_dim=33,num_heads=4)

def test_head_matches_explicit_reference(cfg):
    h=AttentionHead(cfg);x=torch.randn(2,12,32)
    q,k,v=h.query(x),h.key(x),h.value(x)
    expected=F.scaled_dot_product_attention(q,k,v,dropout_p=0.0,is_causal=True)
    torch.testing.assert_close(h(x),expected,atol=1e-6,rtol=1e-5)

def test_multihead_shape_and_registration(cfg):
    m=MultiHeadAttention(cfg)
    assert m(torch.randn(2,12,32)).shape==(2,12,32)
    assert any('heads.3.query.weight' in n for n,_ in m.named_parameters())

def test_feedforward(cfg):
    m=FeedForward(cfg);x=torch.randn(2,12,32)
    torch.testing.assert_close(m(x),m.project(m.activation(m.expand(x))))

def test_block_residual_order(cfg):
    m=TransformerBlock(cfg);x=torch.randn(2,12,32)
    a=x+m.attention(m.norm1(x));expected=a+m.feed_forward(m.norm2(a))
    torch.testing.assert_close(m(x),expected)

def test_full_model_shape_and_causality(cfg):
    m=MiniGPT(cfg).eval();x=torch.randint(96,(2,12));z=x.clone();z[:,8:]=(z[:,8:]+1)%96
    assert m(x).shape==(2,12,96)
    torch.testing.assert_close(m(x)[:,:8],m(z)[:,:8],rtol=1e-5,atol=1e-6)

def test_finite_gradients(cfg):
    m=MiniGPT(cfg);x=torch.randint(96,(2,12));y=torch.randint(96,(2,12))
    loss=F.cross_entropy(m(x).reshape(-1,96),y.reshape(-1));loss.backward()
    assert torch.isfinite(loss)
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in m.parameters())

def test_fixed_batch_can_learn(cfg):
    m=MiniGPT(cfg);x=torch.randint(96,(2,12));y=torch.randint(96,(2,12))
    opt=torch.optim.AdamW(m.parameters(),lr=0.01)
    initial=F.cross_entropy(m(x).reshape(-1,96),y.reshape(-1)).item()
    for _ in range(30):
        opt.zero_grad(set_to_none=True)
        loss=F.cross_entropy(m(x).reshape(-1,96),y.reshape(-1));loss.backward();opt.step()
    final=F.cross_entropy(m(x).reshape(-1,96),y.reshape(-1)).item()
    assert final < initial*0.65

def test_generation_and_context_limit(cfg):
    m=MiniGPT(cfg);x=torch.randint(96,(1,6));out=m.generate(x,5,seed=1)
    assert out.shape==(1,11)
    with pytest.raises(ValueError):m(torch.randint(96,(1,13)))
