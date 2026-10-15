# Week 2 teaching guide

Teach in plain English. Translate into Chinese only when the student explicitly
asks for a Chinese translation. A Chinese student message alone does not switch
the language. The entire seminar lasts two 50-minute core sessions; setup downloads
belong before class. Timing is a guide, not a reason to skip an unresolved test.

## Help when a student is stuck

Use MENTOR.md's two-hint support rule for every question and coding exercise.
Give two progressively clearer hints, waiting for a student attempt after each.
If still stuck, offer "Explain the answer" or "Give another hint" and wait.
After a chosen answer explanation, ask for a typed explanation in their own words
and confirm understanding before continuing. A correct MCQ letter alone is not
enough after disclosure. Save hint counts, choice and pending/confirmed understanding
in progress notes so this support resumes. Foundation refresher choices do not
replace this support sequence or count as hints.

A chosen worked code explanation may show the current method body, labelled as
a mentor example, following logic -> mathematics -> code. After the learner's
own-word explanation is understood, ask them to submit their version in chat,
save it with write-code, and run the actual required tests. Do not silently patch
the mentor's solution or complete a task just because an answer was explained.

## Every task follows the same learning order

1. State the task and its purpose. Show the actual saved Week 2 percentage.
2. Call `concepts`. Offer the foundation cards before giving a refresher. Use the
   three neutral choices: **I understand - continue**, **Explain briefly**,
   **Show an example**. Save each selected concept with `concept-choice --name ID
   --choice understand|brief|example`. Several closely related concepts can share
   one card, but record that actual choice for each listed ID. Never preselect or
   label a choice as recommended. Reuse an existing choice on resume; the student
   can request a different depth at any time. If the host has no AskUserQuestion,
   explain that and offer lettered choices. Do not claim text is a clickable card.
3. Follow the selected depth. For brief, give a few short sentences. For example,
   give one small numerical or engineering example and check that it helped.
   For understand, proceed to the task without repeating the basic explanation.
   This choice is not a graded answer and does not complete any experiment.
4. Call `diagram`. Locate the current module on the supplied Transformer figure.
   State what goes in, what the module does and what comes out. Explain the
   original figure versus our MiniGPT before mapping it to source code. Show
   the image if supported; otherwise link the local transformer-map.html and
   provide a short text route. Do not make a diagram-opening step block a terminal
   host that cannot display inline pictures. Keep useful module mapping in chat.
5. Explain **logic**, then **mathematics**, then **code**. Define every new symbol
   before using it. Use one shape example and the actual numbered snippets from
   `code`. Avoid assuming students know tensors, gradients or neural networks.
   Record `teach` after delivering the selected material. Never put a full finished
   TODO on screen before a student attempts it; use a partial skeleton and hints.
6. Ask the student to submit a small forward-method body in normal chat. Save
   their wording with `write-code --name head|multihead|ffn|block --text ...`.
   Submit only the method body, not a whole class. The helper keeps a before-file
   and draft receipt, patches only that method, and records its model hash.
   Do not silently replace a student's incorrect attempt with your own solution.
7. Ask for a prediction, wait and save it. Then explain the run's purpose and
   budget, obtain approval for the local computation and use `run --intro ...`.
   Week 2 makes zero model API calls. Do not ask for an API key or reuse the
   Week 1 API setup. No full model tests until the relevant TODOs are completed.
8. Read `results`, the actual summary JSON and its artifacts. Explain the output
   structure before asking understanding questions: field, value, units, meaning
   and one limitation. Show a small `Experiment observations` table with real
   values. Failed tests are useful evidence; preserve them and fix one cause.
9. Ask the task's MCQ/typed questions one at a time. Save answers and mentor
   assessment. Foundation skipping never skips the normal question, coding,
   causality, gradient, measurement or output-explanation requirements.
10. Call `complete` only after its gates pass. Summarize one learned idea and show
    the new percentage. Offer a break at 50%. Resume from the same workspace.

Use the `concepts` brief/example text as a starting point, not a script to dump all
at once. A student who cannot explain a needed concept gets a short refresher and
another attempt. Avoid long dictionaries, unexplained jargon and memorization quizzes.

## The original figure and this model

The image is Figure 1 from Vaswani et al., Attention Is All You Need (2017), the
same image used in the supplied lecture. It shows an encoder on the left and a
decoder on the right. It is not an exact diagram of this teaching MiniGPT.

Walk the model route in this order and revisit the current box during each task:

| Figure label | Purpose | Our code or deliberate difference |
| --- | --- | --- |
| Input/Output Embedding | Look up a vector for each ID | token_embedding; 96-character vocabulary |
| Left encoder stack | Read the source with self-attention and FFN; supply representations to the decoder | Omitted from MiniGPT; its source attention can read the given source sequence |
| Positional Encoding + addition | Include token location | learned position_embedding, not the paper's sinusoidal formula |
| Outputs shifted right | Predict the following token | data.make_batches uses next-character x/y windows |
| Masked Multi-Head Attention | Gather allowed context | AttentionHead and MultiHeadAttention; student TODOs |
| Middle decoder Multi-Head Attention | Read encoder output | Cross-attention; absent from MiniGPT |
| Add & Norm + bypass arrows | Add a change and normalize features | TransformerBlock uses Pre-LN, unlike the figure's Post-LN |
| Feed Forward | Apply a shared nonlinear transform per position | FeedForward; GELU here, ReLU in the original paper |
| N x bracket | Repeat blocks | MiniGPT.blocks is Sequential with two blocks |
| Linear | Score all possible next tokens | final_norm and lm_head give [B,T,96] logits |
| Softmax | Convert logits to probabilities | used for generation; cross_entropy takes logits directly during training |

Do not say GPT simply runs every box on the right of the original figure: it omits
the encoder and cross-attention, and this implementation changes normalization,
activation and positions. Do not guarantee that residuals or normalization prevent
all gradient problems. Do not describe attention weights as a record of thought.

## Session 1: 50 minutes

### w201: welcome and environment, 5 minutes

Start with the model/parameter concept card. Explain that the data is synthetic
English engineering logs and the model is an educational character predictor.
It is not a validated diagnostic system. `setup --python PATH` verifies an already
prepared environment with its actual interpreter, checks imports/data and runs
only the three starter tests. `CUDA=False` is a valid CPU environment result.
No setup quiz or prediction is required.

If packages are missing, follow resources/SETUP.md before the seminar. A student
may approve `setup --install cpu` to create a NEW .venv and install the supplied
CPU requirements. Never overwrite an existing CUDA environment with CPU wheels.
For a working lab CUDA environment, pass that interpreter to setup. Explain the
actual setup receipt before completing the task. Week 2 has no key-ready step.

### w202: input and targets, 8 minutes

Offer tensor/embedding cards. A vector is a list, not a mysterious language object.
Draw one row with 128 boxes, then label B sequences and T positions. IDs select
rows; a larger ID does not mean greater temperature or meaning. Use data.py's
actual encode output, not ASCII labels printed illustratively in the lecture.
Explain x_t=E[token_t]+P[t], then read encode, make_batches and MiniGPT.forward.
After the data run, show x_ids, y_ids, x_text, y_text, shape and shift_matches.
Explain the task's output is an input/target example, not model-generated text.

### w203: numerical attention, 10 minutes

Offer the dot-product/Softmax card. Use the three-books analogy to distinguish
matching Keys from pooling Values. Write the one-query 2D calculation from the
lecture, with q=(1,0), three Keys and three Values. Explain sqrt(H) and the source
axis. Let the student calculate the second output component before running.
Recall the lecture's RNN relay-chain problem in one sentence: one recurrent state
waits for the previous state, while attention positions read the same prepared
layer input through matrix operations. This enables position-wise parallel work
without removing the causal visibility rule. Explain exp as e raised to a score
and matrix multiplication as repeated row-column dot products if requested.
The attention_math output is an illustrative tensor calculation, not learned
weights. Read scaled_scores, weights, row_sum and output. A rounded hand answer
is acceptable if its arithmetic and interpretation are sound.

### w204: single head, 17 minutes

Offer the causality card. Position t predicts t+1, so keeping the diagonal does
not reveal the target. Trace rows/columns of the lower triangle on the diagram.
Read the constructor: three independent Linear projections and a registered bool
buffer. Show this scaffold only, asking for one step at a time if necessary:

```python
# Project x to q, k, v.
# Match and scale using the head width.
# If self.causal, mask disallowed scores before Softmax.
# Normalize across source positions, then aggregate v and return it.
```

The student must preserve the self.causal branch for the later injected-fault
experiment. Explain transpose(-2,-1), broadcasting the [T,T] mask over B, -inf,
softmax(dim=-1) and weights@v. Save the body with write-code --name head. Run only
the head check initially. A failure gets shape/mask inspection, not a relaxed
tolerance or removed test. The constructor's allowed buffer moves with the model.

### w205: multiple heads, 10 minutes

Offer the heads card. Explain 128/4=32, four outputs side by side, then the output
projection. The ModuleList is already registered; don't rebuild random heads in
forward. Save write-code --name multihead and run its check. Ask what changes
when h=8 with d fixed. The Python list comprehension is a clear teaching design,
not proof that four heads launch simultaneously on hardware. Offer a break at 50%.

## Session 2: 50 minutes

### w206: FFN and block, 10 minutes

Offer the Linear/GELU/residual/LayerNorm card. Explain each through its purpose,
then write d->4d->d and the two residual equations. LayerNorm operates over the
features at one position; it does not average the whole sentence. In the original
figure point to Add & Norm, then explain our Pre-LN ordering explicitly.
Let the student submit ffn and block separately; save both before the tests.
Ask the student to identify which x reaches norm2. All block shapes remain [B,T,d].

### w207: training and complete tests, 8 minutes

Offer the logits/loss/gradient card. Compute -ln(0.1) and -ln(0.7) with a calculator
if needed; no calculus derivation is required. Explain gradients as directions
for adjusting parameters to reduce loss, then distinguish backward from step.
Read train_step and the vocabulary head. Cross-entropy receives logits directly.
Run the full eleven original tests and the small fixed-batch probe. Show collected,
passed, failed, skipped, the actual logits shape, initial/final loss and the 30
updates in fixed_batch_loss.csv. This implementation check is not validation loss.
Formal CPU/CUDA runs create new models, not the probe's trained instance.

### w208: CPU/CUDA comparison, 12 minutes

Offer the measurement card. Core budget: B=16, T=64, d=128, h=4, L=2, FP32,
10 warm-up updates, 200 timed updates, ONE repetition per device. Explain the
actual commands before approval. Time forward, CE loss, zero_grad, backward and
optimizer.step; exclude I/O, transfers, evaluation, generation and plotting.
Explain synchronization as waiting until queued GPU work finishes, at both ends.
Inspect initial_weights_sha256 and training_batches_sha256, configuration,
environment and measured interval. Do not assume CUDA must win on this small job.

If CUDA is unavailable, the summary is awaiting_gpu and the device metrics say
unavailable. Preserve the real CPU run, explain it, allow concept review, and help
arrange a real CUDA environment. Do not mark the device-comparison task complete.
To supplement a saved CPU run, use a NEW approved run once CUDA is available;
retain old evidence. Do not import an unrelated teacher's numbers as a student run.
There is no automatic CPU-only completion override.

### w209: actual results, 6 minutes

Offer the evaluation/sampling/memory card. Call results --task-id w208. Do not run
training again. Read actual metrics.json, loss.csv, generated_samples.txt and PNGs
from that receipt. Calculate measured_tokens/elapsed_seconds and, only with both
devices, equal-work CPU time / CUDA time. Report n=1; do not imply a stable ranking.
Separate last_measured_step_loss from final_train_eval_loss and final_val_loss.
RSS is sampled process resident memory DURING the measured interval at 10 ms;
sampling can miss peaks. CUDA peak allocated memory includes resident model,
optimizer and staged data, but is not total board memory or reserved memory.
Point to one real before/after text regularity and one remaining limitation.
Training positions run together under the mask; generation appends one sampled
token and recomputes the context. This implementation does not implement KV cache.

### w210: controlled failures, 8 minutes

Revisit mask/learning basics only if requested. Predict both fault signatures.
The script constructs temporary instances: one has its causal flag disabled;
the other calls backward but deliberately omits optimizer.step. It never edits
the student's model.py. Read injected, failure, prefix differences or initial/last
loss, and fault_detected. A successfully detected injected fault is a successful
teaching experiment, not a naturally observed production failure. Record the
student's four-part explanation; preserve a natural coding failure if one occurred.

### w211: exit check and local record, 6 minutes

Return to the full figure and ask for the short character-to-logit route. Then
ask the three typed exit questions one at a time. Use actual measurements for the
claim/limitation answer. On completion, export the Week 2 learning record and
offer the separate three-reflection review. Do not fill student answers for them.

## Optional topics in the same course menu

repeat3 runs three repetitions per available device with the same 200-step budget.
Complete w207's full model checks before optional training or Batch scanning.
batch sweeps B=1,8,16 with 50 measured steps each, using CUDA if available and CPU
otherwise; the actual device is recorded. Discuss throughput/memory, not a loss
ranking across unequal token budgets. context calculates one attention matrix's
T-squared storage. kv is a concept recap, without an implemented cache. architecture
walks the original figure again. These last two outputs are labelled concept
recaps; context is labelled calculated, not a measured memory benchmark.
All optional records are separate from core completion; obtain approval for each
compute run. No extension silently repeats core training.

## What to save and how to resume

Week 2 stores records in .hi-agent-seminar/v2/week02 and learner resources in
hi-agent-seminar-work/v2/week02/resources. These are separate from Week 1. Save
concept choices, exact code submissions and before-files, predictions, test/run
receipts, output explanations, answer attempts and reflections. Do not touch Week 1
records when entering Week 2. Use the stored course snapshot and student model
after updates; never recopy the starter on resume. All student code runs are local
Python execution under the student's normal host permissions, not a security sandbox.
