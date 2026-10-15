# Week 2 instructor guide

For struggling learners, use MENTOR.md's two-hint support rule: two progressive
hints with separate attempts, then a choice of answer explanation or further hints.
After explanation, require and assess a restatement in the student's own words
before continuing. Record assistance honestly and retain all required code tests.

Two core sessions of 50 minutes. Environment downloads are pre-class preparation.
No deep-learning background is assumed. Offer neutral concept cards and save the
chosen refresher depth. Skipping a refresher never removes code/test/check gates.

| Session | Task | Minutes | Saved core percentage after completion |
| --- | --- | --- | --- |
| 1 | w201 welcome and environment | 5 | 5 |
| 1 | w202 characters, embeddings and shifted labels | 8 | 13 |
| 1 | w203 numerical attention | 10 | 23 |
| 1 | w204 single head | 17 | 40 |
| 1 | w205 multiple heads | 10 | 50 |
| 2 | w206 FFN and residual block | 10 | 60 |
| 2 | w207 learning and complete tests | 8 | 68 |
| 2 | w208 CPU/CUDA comparison | 12 | 80 |
| 2 | w209 actual outputs and memory | 6 | 86 |
| 2 | w210 injected failures | 8 | 94 |
| 2 | w211 exit check | 6 | 100 |

Default benchmark: one CPU and one CUDA run; B=16, T=64, d=128, 4 heads, 2 blocks,
FP32, AdamW 3e-4, ten warm-up updates and 200 timed updates. Calibrate classroom
hardware before class. No GPU winner is assumed. The supplied CPU validation is
not evidence about a classroom GPU. Missing CUDA keeps comparison pending until
real GPU evidence is obtained. Do not call a CPU-only result a completed comparison.

Full model checks: eleven original tests, plus a recorded thirty-update fixed-batch
probe. Do not run the complete test suite before the four student TODOs are filled.
If time runs short, save the actual checkpoint and continue later rather than
providing an unexplained complete answer or marking unfinished work complete.

The visual guide uses the supplied Transformer figure. Explain its encoder,
cross-attention and Post-LN placement before tracing the MiniGPT route. This code
uses learned positions, GELU, Pre-LN and no encoder/cross-attention. Its explicit
Python head list is educational code, not a performance-optimized attention kernel.

Review questions and assessments are local. No Feishu submission. Public repository
contents are inspectable; mentor rubrics are coaching criteria, not secret exam keys.
Week 1 files, record paths and course definition must remain unchanged by this release.
