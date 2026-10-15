# Week 2 source alignment

Teaching inputs supplied by the instructor:

- EEEE4149_Week2_Lecture_Inside_the_Model_v3.pptx: 56 slides; lecture labels
  L01-L38 and seminar labels S01-S16. Relevant lecture topics include L06-L16
  attention, L17-L19 input representations, L22-L29 block/training, and L31-L37
  hardware/measurement. Seminar tasks S01-S16 supply the four-TODO experiment route.
- EEEE4149_Seminar2_Student_Guide.docx and EEEE4149_Seminar2_Student_Pack.zip:
  student starter model, eleven tests, synthetic data and measurement scripts.
  Chinese source teaching text was rewritten into English for this plugin.
- The user approved two 50-minute sessions, one repetition per device in core,
  optional three-repetition and Batch-sweep work, and saved learning records.
- The user requested beginner concepts, logic/mathematics/code ordering, a module
  walk through the Transformer figure, and skippable concept-refresher cards.

The figure assets/transformer-original.png is the supplied rendering of Figure 1
from Vaswani et al., Attention Is All You Need (2017):
https://arxiv.org/abs/1706.03762 . It is reused as the original encoder-decoder
figure, not represented as a diagram of our exact MiniGPT implementation.

Alignment corrections: preflight.py is the supplied environment script, not the
slide's illustrative check_env.py. train.py saves real before/after generation;
there is no standalone sample.py. Fixed-batch tests/probe use thirty updates.
Token IDs come from the 96-character table, not illustrative ASCII labels. Parameter
counts come from the actual model. RSS scope follows train.py's measured-interval
sampling, not a claim of whole-run or whole-device memory. Reference architecture
and MiniGPT differences are explicit in the teaching and visual guides.

Official technical references used by the supplied code:

- https://docs.pytorch.org/docs/2.10/generated/torch.nn.functional.scaled_dot_product_attention.html
- https://docs.pytorch.org/docs/2.10/notes/cuda.html
- https://docs.pytorch.org/tutorials/recipes/recipes/benchmark.html
- https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html
