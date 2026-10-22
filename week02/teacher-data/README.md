# Real teacher CPU/CUDA reference experiment

Measured on 22 October 2026 (Asia/Shanghai), at the instructor's request.
Hardware: Intel Core i9-13900K and NVIDIA GeForce RTX 4090, same Windows machine.
Environment: dedicated Python 3.12 / PyTorch 2.10.0+cu128 environment. Existing
system CUDA and Conda environments were not modified. The official PyTorch wheel
was checked against its published download-server SHA256 before installation.

| Device | Timed seconds | Training positions/s |
| --- | ---: | ---: |
| CPU | 3.6691393 | 55816.9051 |
| CUDA | 1.4046646 | 145799.9298 |

CPU time / CUDA time = 2.6121 for this pair. B=16, T=64, d=128, 4 heads,
2 blocks, FP32, 10 warmup updates and 200 timed updates, 204800 positions.
Both runs use identical initial weights and batch hashes. Timing includes forward,
loss, gradient clearing, backward and optimizer update; it excludes file I/O,
transfers, evaluation, generation and plotting. See the raw metrics for memory
scopes and environment. Do not confuse training throughput with generation speed.

There is one observation per device. Background applications and Windows WDDM can
affect timing. These results do not promise speedup on other computers or models.
Never divide a student's CPU time by this teacher CUDA time as a local speedup.

cpu_r1 and cuda_r1 contain unmodified metrics.json, loss.csv and generated_samples.txt
from real execution. benchmark_results.csv is the paired runner's raw summary.
provenance.json records attribution, source hashes and driver information.
The 11 original model tests passed before these measurements. The completed
instructor model remains outside the distributed plugin; student TODOs remain.
