"""Build the English Week 2 lesson definition from its editable teaching design."""
import json
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def concept(id, title, brief, example):
    return {"id":id, "title":title, "brief":brief, "example":example}


FOUNDATIONS = {
    "parameters":concept("parameters", "Model, parameters and training",
        "A model is a numerical rule with adjustable numbers called parameters. Training changes those numbers using examples. Calling an API or editing a prompt does not itself update them.",
        "For y = w*x, w is a parameter. Changing x changes this answer; changing w changes the rule used for future answers."),
    "tensors":concept("tensors", "Scalars, vectors, matrices and tensor shapes",
        "A scalar is one number. A vector is a list of numbers. A matrix has rows and columns. A tensor is an array with one or more axes. [B,T,d] means B sequences, T positions and d features at each position.",
        "[2,8,128] stores two sequences, each with eight token positions, each position holding 128 numbers. These numbers are not temperatures."),
    "embeddings":concept("embeddings", "Token IDs, embeddings and positions",
        "A token is a unit of text. Here it is one character. Its integer ID selects a row from a trainable embedding table; a position vector adds where that character occurs.",
        "The same M has the same token embedding at positions 1 and 17, but different position embeddings. Use encode('M12 ') to see the real IDs."),
    "attention_math":concept("attention_math", "Dot products, scaling and Softmax",
        "A dot product multiplies matching vector entries and adds them. Matrix multiplication repeats row-column dot products; transpose swaps axes. We divide scores by the square root of the head width. Softmax uses exp(score), meaning e raised to that score, then divides by the sum to produce nonnegative weights adding to one.",
        "q=(1,0) and k=(1,1) have dot product 1. Softmax of three equal scores gives 1/3 to each. The weighted sum combines Value vectors."),
    "causality":concept("causality", "Causality and the mask",
        "At position t the model predicts the next token using input positions up to t. A causal mask prevents later inputs from leaking into that prediction. It acts on scores before Softmax.",
        "If inputs begin M12, the output at M predicts 1. That output can read M but cannot read the target 1 from the next input position."),
    "heads":concept("heads", "Heads and feature concatenation",
        "Each head learns separate Query, Key and Value projections of the same input. We join their outputs along the feature axis, then mix features with one output projection.",
        "Four [2,8,32] outputs concatenate to [2,8,128], not [2,32,32]. The model does not assign a guaranteed meaning to each head."),
    "block":concept("block", "Linear layers, GELU, residuals and LayerNorm",
        "A Linear layer applies learned weights and a bias. GELU is a nonlinear transformation. A residual adds a module's change to its input. LayerNorm normalizes each position's feature vector and applies a learned scale and shift.",
        "For features [1,3], the average is 2 and standard deviation is 1; normalization gives approximately [-1,1] before learned scale/shift. This is not a probability distribution. In Pre-LN, update x with the attention residual before the FFN branch."),
    "learning":concept("learning", "Logits, probability, loss, gradients and updates",
        "Logits are scores for the possible next characters. Softmax turns scores into probabilities. Cross-entropy penalizes low probability on the correct next character. A gradient describes how loss changes with a parameter; the optimizer uses gradients to update parameters.",
        "For the correct character, p=0.1 gives -ln(p) about 2.30 and p=0.7 gives about 0.36. ln is the natural logarithm; use a calculator, with no calculus required here. backward() computes gradients; optimizer.step() changes parameters. Cross-entropy takes logits directly."),
    "measurement":concept("measurement", "Warm-up, timing, throughput and device synchronization",
        "Warm-up prepares the computation before timing. Throughput is work divided by measured time. CUDA operations can finish after the CPU launches them, so synchronize at both timing boundaries.",
        "200 steps * 16 sequences * 64 positions = 204800 training positions. Divide that count by the actual measured seconds. This is not generated characters per second."),
    "evaluation":concept("evaluation", "Validation, sampling and memory statistics",
        "Validation uses data that did not update parameters. Sampling picks a next character from probabilities, then repeats. Process RSS measures resident process memory; PyTorch allocated CUDA memory measures allocations tracked by PyTorch on the GPU.",
        "A lower training loss can coexist with poor unseen text. A fluent-looking log is not evidence of correct diagnosis. CPU RSS and CUDA allocated bytes are different statistics."),
}


def mcq(id, prompt, options, correct, feedback):
    return {"id":id, "type":"mcq", "prompt":prompt, "options":dict(zip("ABCD", options)), "correct":correct, "feedback":feedback}


def opened(id, prompt, rubric):
    return {"id":id, "type":"open", "prompt":prompt, "rubric":rubric}


def task(id, title, minutes, session, purpose, logic, mathematics, refs, action=None,
         concepts=(), modules=(), targets=(), questions=(), prediction="What do you expect, and why?"):
    return {"id":id, "title":title, "minutes":minutes, "weight":minutes, "session":session,
            "purpose":purpose, "recap":logic, "logic":logic, "mathematics":mathematics,
            "steps":["Offer saved foundation concept cards; follow the requested depth.",
                     "Locate the relevant Transformer box and explain its job in plain English.",
                     "Explain the logical need, then each mathematical symbol and tensor shape.",
                     "Read actual numbered code; let the student write the requested small implementation.",
                     "Record the student's prediction, run the approved local check, then explain actual output fields before questions."],
            "concepts":[FOUNDATIONS[c] for c in concepts], "terms":{FOUNDATIONS[c]["title"]:FOUNDATIONS[c]["brief"] for c in concepts},
            "module_ids":list(modules), "code_targets":list(targets), "code_refs":refs,
            "commands":[["seminar_step.py", "--action", action]] if action else [], "planned_calls":0,
            "requires_teaching":True, "requires_prediction":prediction is not None, "prediction":prediction,
            "requires_setup":id == "w201", "requires_prompt":False, "bind_model":bool(targets) or action in {"full_tests", "benchmark", "failures"},
            "questions":list(questions), "output_guide":"Read this task's week02_result.json and listed stdout/CSV/PNG/XML files. Explain field names, units and limitations using actual values. Status failed or awaiting_gpu is not successful completion."}


TASKS = [
task("w201", "Welcome, choose refresher depth and check the local environment", 5, 1,
     "Know what this seminar builds and verify the prepared Python/data environment.",
     "Week 1 used a hosted model. This week completes and trains a tiny local model on synthetic logs. No API key is needed.",
     "A parameter is an adjustable number in a rule; training changes parameters. Shapes and equations are introduced only when needed.",
     [["preflight.py", "report"], ["model.py", "ModelConfig"]], concepts=["parameters"], modules=["overview"], prediction=None),
task("w202", "Read characters, embeddings and shifted targets", 8, 1,
     "Trace text to the numbers the model reads and the next character it must predict.",
     "IDs label characters; learned token/position vectors build one representation per position. Targets are shifted by one.",
     "x_t = E[token_t] + P[t]; input IDs [B,T] become vectors [B,T,d]. y[:, :-1] equals x[:, 1:].",
     [["data.py", "encode"], ["data.py", "make_batches"], ["model.py", "MiniGPT.forward"]], "data",
     ["tensors", "embeddings"], ["embedding", "position", "shift"], questions=[mcq("shift", "Why does y start one character after x?",
        ["To hide all input characters", "To train each position to predict its next character", "To make token IDs larger", "To update the data file"], "B", "Each position predicts its following character; the causal mask separately controls which inputs it can read.")],
     prediction="What relationship should hold between x[:,1:] and y[:,:-1]? Are the displayed IDs physical measurements?"),
task("w203", "Calculate one attention output", 10, 1,
     "Turn the three-books analogy into a numerical weighted mixture before coding a head.",
     "A Query matches Keys to decide weights; those weights combine Values into a new vector.",
     "q=(1,0); K=((1,0),(0,1),(1,1)); V=((2,0),(0,2),(2,2)). Compute qK^T/sqrt(2), Softmax, then weights@V.",
     [["seminar_step.py", "attention_math"], ["model.py", "AttentionHead"]], "attention_math", ["attention_math"], ["masked_attention"],
     questions=[opened("weighted_value", "Using the displayed real calculation, give the second output component to two decimal places and explain why weights add to one.",
        "Expect about 1.20, combination of Value components, normalization across readable sources. Accept rounding supported by the actual result.")],
     prediction="Using approximate weights (0.40,0.20,0.40), calculate the second output component before running. Which tensor supplies the content?"),
task("w204", "Write and test one causal attention head", 17, 1,
     "Implement matching, masking and weighted Value aggregation with the right axes.",
     "The answer at a position must not depend on future inputs, even when the whole training window is in memory.",
     "Q,K,V: [B,T,H]; scores=QK^T/sqrt(H): [B,T,T]; A=softmax(scores+M, last axis); O=AV: [B,T,H]. M is 0 when allowed and -infinity in the future.",
     [["model.py", "AttentionHead"], ["tests/test_model.py", "test_head_matches_explicit_reference"]], "head", ["causality"], ["masked_attention"], ["head"],
     [mcq("mask_order", "Where does the causal mask belong?", ["After the final prediction", "Only during generation", "On the scores before Softmax", "On the parameter gradients"], "C", "Mask scores before Softmax so future sources get zero probability; normalize along readable source positions.")],
     "For input [2,8,128] and four heads, what are one head's scores and output shapes? Should future weights be zero?"),
task("w205", "Write and test multiple attention heads", 10, 1,
     "Combine independently learned heads while preserving batch and sequence axes.",
     "Each registered head reads the same x with its own projections. Concatenate feature outputs and apply the existing projection.",
     "H=d/h=128/4=32; concatenate four [2,8,32] outputs along the last axis to get [2,8,128].",
     [["model.py", "MultiHeadAttention"], ["tests/test_model.py", "test_multihead_shape_and_registration"]], "multihead", ["heads"], ["multihead"], ["multihead"],
     [opened("head_width", "If d stays 128 but h becomes 8, give the width of each head and the concatenated width. Which axis must remain unchanged?",
             "Head width 16, concatenated width 128, preserve B and T. No assumption that each head has a fixed human-assigned role.")],
     "What happens to B, T and feature width when the four head outputs are joined?"),
task("w206", "Write the feed-forward network and Pre-LN block", 10, 2,
     "Finish the four TODOs and understand which modules mix positions versus features.",
     "Attention gathers context across positions; FFN transforms each position's features. Residual paths add changes to their input.",
     "FFN(x)=project(GELU(expand(x))), d->4d->d. a=x+Attention(LN1(x)); output=a+FFN(LN2(a)).",
     [["model.py", "FeedForward"], ["model.py", "TransformerBlock"], ["model.py", "MiniGPT"]], "blocks", ["block"], ["ffn", "norm", "stack"], ["ffn", "block"],
     [mcq("residual", "What enters norm2 in the second residual branch?", ["The x already updated by attention", "Only the first head", "The target token IDs", "The original x before either branch"], "A", "The second branch uses the updated representation. Both residual additions keep shape [B,T,d].")],
     "Should a complete block change [B,T,d]? Which module moves information between positions?"),
task("w207", "Connect logits to learning and pass the full model tests", 8, 2,
     "Understand how a next-character score becomes a loss and a parameter update.",
     "Training scores all supplied positions together under the mask. Backward computes gradients; the optimizer changes parameters.",
     "logits: [B,T,V]; mean loss=-mean(log p(target)). p=0.1 -> about 2.30; p=0.7 -> about 0.36. Cross-entropy takes raw logits, flattened to [B*T,V].",
     [["model.py", "MiniGPT.forward"], ["train.py", "train_step"], ["tests/test_model.py", "test_fixed_batch_can_learn"]], "full_tests", ["learning"], ["linear", "softmax", "shift"],
     questions=[opened("parameter_update", "Point to the line that changes parameters. Explain what a falling fixed-batch loss does and does not show.",
        "optimizer.step updates parameters; backward computes gradients. Fixed-batch fitting checks implementation but is not held-out generalization or diagnosis accuracy.")],
     prediction="Which is better for the correct character: probability 0.1 or 0.7? What should happen to loss when the same tiny batch is repeatedly learned?"),
task("w208", "Measure CPU work and compare CPU/CUDA evidence fairly", 12, 2,
     "Measure local CPU work; compare local CPU/CUDA runs or analyse the teacher's real paired measurements when CUDA is unavailable. Follow the installed week02/NO_GPU.md guide for the reference route.",
     "Device comparisons need equal work and correct timing; the device name does not determine the result.",
     "Measured work=200*16*64=204800 training positions. Throughput=positions/elapsed_seconds. Speedup=CPU time/CUDA time for equal work. Ten warm-up updates precede the 200 timed updates.",
     [["train.py", "sync"], ["train.py", "train_step"], ["benchmark.py", "main"]], "benchmark", ["measurement"], ["hardware"],
     questions=[mcq("fairness", "Which comparison is fair?", ["CPU 200 steps versus GPU 20 steps", "Different models with the same filename", "Same initialization, batches, FP32, steps and timing scope", "Include printing only in the CPU timing"], "C", "Hold workload and measurement scope fixed. Check saved initialization and batch hashes; report one repeat per device.")],
     prediction="Do you expect CUDA to be faster for this small model? Give one reason it might not be. Which operations must the timer include?"),
task("w209", "Explain actual metrics and generated text", 6, 2,
     "Read the saved benchmark and samples with honest measurement and learning claims.",
     "Training loss, validation loss, generation quality and hardware speed answer different questions. Generated logs need evidence before anyone treats them as diagnoses.",
     "Use the saved time to calculate 204800/time. One FP32 attention-score matrix uses B*h*T*T*4 bytes. CPU RSS and CUDA allocated bytes have different scopes.",
     [["model.py", "MiniGPT.generate"], ["train.py", "RSSSampler"], ["plot_results.py", "plot_single"]], concepts=["evaluation"], modules=["softmax", "hardware"],
     questions=[opened("results", "Use one actual time to calculate throughput. Give one learned text pattern and one limitation. Name the memory statistic for each device.",
        "Calculation uses the recorded timed positions/seconds. Cite actual generated samples. Distinguish sampled process RSS from PyTorch peak allocated CUDA memory; no claim of validated diagnosis.")],
     prediction="If training loss falls, must validation loss and engineering reliability improve too? Why?") ,
task("w210", "Diagnose two deliberately injected faults", 8, 2,
     "Connect a failed test to an identifiable computation or missing update.",
     "One controlled change should produce a testable symptom. Removing causality leaks future inputs; omitting optimizer.step leaves parameters unchanged.",
     "Compare max absolute difference of unchanged prefix logits before/after changing future inputs. Compare fixed-batch losses when no parameter updates occur.",
     [["failure_demo.py", "run"], ["train.py", "train_step"]], "failures", modules=["masked_attention", "linear"],
     questions=[opened("failure", "Choose one injected case. State the observation, its cause, the correction and the check you would rerun. Is it a naturally observed failure?",
        "Ground answer in recorded JSON. Clearly injected. Mask repair uses causal-prefix check; missing optimizer step uses parameter/update or fixed-batch loss check. Do not invent an OOM event.")],
     prediction="What changes when the mask is removed? What changes when backward runs but optimizer.step never runs?"),
task("w211", "Explain the complete route and save the learning record", 6, 2,
     "Show that the diagram, equations, code and experiment results describe one system.",
     "Trace characters to embeddings, causal blocks, vocabulary scores, updates and measured outputs. Name uncertainty using this seminar's evidence.",
     "Use shapes [B,T], [B,T,d], [B,T,T], [B,T,V] and the work/time calculation to support a short explanation.",
     [["model.py", "MiniGPT.forward"], ["model.py", "MiniGPT.generate"]], modules=["overview", "encoder", "cross_attention"],
     questions=[opened("exit_mask", "Why can position t read its own input but not future inputs?",
                       "At t the target is t+1; the diagonal uses known input, future would expose target information."),
                opened("exit_update", "Which line changes parameters, and how does this differ from changing a prompt in Week 1?",
                       "optimizer.step changes numerical parameters; prompt edits alter input/context without retraining model weights."),
                opened("exit_claim", "State one conclusion supported by this task's actual measurements and one thing still uncertain.",
                       "Use actual data, configuration, timing scope, n=1 limitations and truthful device availability. No universal GPU superiority or validated diagnostic claims.")],
     prediction="Explain the route from a character ID to its next-character scores in one or two sentences.")
]
TASKS[8]["evidence_task"] = "w208"
TASKS[8]["output_guide"] = "Use results --task-id w208 to read the saved benchmark; open the actual loss CSV, plots and before/after samples. No extra training run is needed. Explain measured interval, token positions, n=1, train/validation loss and the memory scopes recorded in metrics.json."
TASKS[0]["output_guide"] = "setup returns actual package versions, CUDA availability, data presence and three starter test results. Missing CUDA does not fail CPU setup. Four TODOs are intentionally unfinished; do not run all model tests before implementing them."

MODULES = [
    {"id":"overview", "figure_box":"The whole encoder-decoder figure", "purpose":"See how the original 2017 Transformer connects input and output sequences.", "math":"A representation is a vector at each position; N x repeats blocks.", "code":"MiniGPT", "difference":"Our decoder-only model has no encoder and no cross-attention. Its blocks use Pre-LN; the original figure shows Add & Norm after sublayers."},
    {"id":"encoder", "figure_box":"Left encoder stack and its Multi-Head Attention", "purpose":"Read the given source sequence and produce representations for the decoder to consult.", "math":"Encoder self-attention gets Q,K,V from the source sequence; decoder cross-attention uses its output for K,V.", "code":"No corresponding MiniGPT encoder", "difference":"The original encoder can attend across the supplied source sequence. This causal decoder-only MiniGPT does not implement that encoder or its unmasked source-attention branch."},
    {"id":"embedding", "figure_box":"Input Embedding / Output Embedding", "purpose":"Turn discrete character IDs into trainable vectors.", "math":"E: [V,d]; lookup -> [B,T,d].", "code":"MiniGPT.token_embedding; MiniGPT.forward", "difference":"The local input uses 96 character symbols, not a commercial tokenizer. IDs come from data.py."},
    {"id":"position", "figure_box":"Positional Encoding and plus sign", "purpose":"Provide the position of each token.", "math":"x_t=E[token_t]+P[t].", "code":"MiniGPT.position_embedding; MiniGPT.forward", "difference":"The original paper uses sinusoidal positions; this model learns a position table."},
    {"id":"shift", "figure_box":"Outputs (shifted right)", "purpose":"Supply known characters while the target is the following character.", "math":"x=tokens[s:s+T]; y=tokens[s+1:s+T+1].", "code":"data.make_batches", "difference":"The supplied character windows express next-token shifting without adding a special translation start token."},
    {"id":"masked_attention", "figure_box":"Masked Multi-Head Attention", "purpose":"Gather only permitted past/current context.", "math":"A=softmax(QK^T/sqrt(H)+M); O=AV.", "code":"AttentionHead.forward", "difference":"Our causal switch is used only for the controlled failure demo; normal attention stays causal."},
    {"id":"multihead", "figure_box":"Multi-Head Attention inside the masked decoder sublayer", "purpose":"Learn several mixtures of the same input features.", "math":"concat(head_1,...,head_h) W_O; h*H=d.", "code":"MultiHeadAttention.forward", "difference":"A Python list comprehension is explicit teaching code; it does not imply automatic simultaneous kernel execution."},
    {"id":"cross_attention", "figure_box":"Middle decoder Multi-Head Attention with arrows from encoder", "purpose":"Read encoder information using decoder queries in translation.", "math":"Q from decoder; K,V from encoder.", "code":"No corresponding MiniGPT module", "difference":"Omitted in this decoder-only model. Do not call the middle decoder box another copy of its masked self-attention."},
    {"id":"norm", "figure_box":"Add & Norm and residual arrows", "purpose":"Add a computed change to the representation and normalize features.", "math":"a=x+Attention(LN1(x)); z=a+FFN(LN2(a)).", "code":"TransformerBlock.forward; norm1; norm2", "difference":"Pre-LN is an intentional difference from the original Post-LN diagram. These operations help training; they do not guarantee gradients can never vanish or explode."},
    {"id":"ffn", "figure_box":"Feed Forward", "purpose":"Apply the same nonlinear feature transform separately at each position.", "math":"project(GELU(expand(x))); d -> 4d -> d.", "code":"FeedForward.forward", "difference":"This MiniGPT uses GELU. The 2017 paper uses ReLU. FFN itself does not mix token positions."},
    {"id":"stack", "figure_box":"N x bracket", "purpose":"Repeat blocks to build deeper representations.", "math":"[B,T,d] -> block -> [B,T,d], repeated L times.", "code":"MiniGPT.blocks; nn.Sequential", "difference":"L=2 here. Heads are registered with ModuleList; blocks with Sequential so the optimizer can find their parameters."},
    {"id":"linear", "figure_box":"Linear above decoder", "purpose":"Score every possible next character.", "math":"[B,T,d] -> [B,T,V].", "code":"MiniGPT.final_norm; MiniGPT.lm_head", "difference":"forward returns raw logits; the added final norm is part of this MiniGPT implementation."},
    {"id":"softmax", "figure_box":"Softmax / Output Probabilities", "purpose":"Convert scores to probabilities when sampling the next character.", "math":"p_i=exp(z_i)/sum_j exp(z_j); cross-entropy=-ln p_target.", "code":"MiniGPT.generate; train.train_step", "difference":"Generation applies Softmax for sampling. F.cross_entropy handles logits directly in training; do not apply Softmax twice."},
    {"id":"hardware", "figure_box":"Matrix computations throughout the figure", "purpose":"Relate repeated matrix work to measured CPU/CUDA performance.", "math":"tokens/s=steps*B*T/time; one score matrix has B*h*T*T elements.", "code":"train.run; train.sync; benchmark.main", "difference":"The device comparison measures a fixed training interval. It excludes I/O, transfer, evaluation, generation and plotting."},
]

EXTENSIONS = []
for id, title, purpose, action, prediction in [
    ("repeat3", "Repeat each device three times", "Compare measured medians and variation with n=3 on each actual device.", "repeat3", "Will repeated timings be identical? Why report n and the spread?"),
    ("batch", "Sweep B=1,8,16", "Compare throughput and memory while holding model, context, precision and steps fixed.", "batch", "How might larger batches change throughput and memory? Why are final losses not a fair learning comparison here?"),
    ("context", "Calculate the context-length cost", "Separate the T-squared score-matrix cost from total measured training memory.", "context_math", "What happens to this one matrix when T doubles?"),
    ("kv", "Review KV cache", "Understand inference-time reuse, its memory cost and how it differs from user memory.", "kv_concept", "What can be reused at the next generation step, and why?"),
    ("architecture", "Revisit encoder, decoder and cross-attention", "Walk the original figure and identify what our MiniGPT keeps, changes and omits.", "architecture", "Does this model contain the original paper's encoder or middle cross-attention box?")]:
    EXTENSIONS.append({"id":id, "title":title, "purpose":purpose, "prediction":prediction,
                       "planned_calls":0, "commands":[["seminar_step.py", "--action", action]],
                       "code_refs":[["model.py", "MiniGPT"], ["benchmark.py", "main"]] if id in {"repeat3", "batch"} else [["model.py", "MiniGPT"]],
                       "output_guide":"Explain whether the output is measured, calculated or a concept recap. Use actual files, preserve unavailable devices, and do not change the core completion percentage."})

LESSON = {"id":"week02", "version":1, "title":"Inside the model: build, test and measure a MiniGPT",
          "language":"English; Chinese translation only when explicitly requested", "requires_api_key":False,
          "teaching_order":["logic", "mathematics", "code", "student attempt", "test", "actual output explanation", "understanding check"],
          "code_targets":{"head":"AttentionHead", "multihead":"MultiHeadAttention", "ffn":"FeedForward", "block":"TransformerBlock"},
          "transformer_modules":MODULES, "tasks":TASKS, "extensions":EXTENSIONS}
assert [sum(t["minutes"] for t in TASKS if t["session"] == s) for s in [1,2]] == [50,50]
assert sum(t["weight"] for t in TASKS) == 100
(ROOT / "week02" / "lesson.json").write_text(json.dumps(LESSON, indent=2)+"\n", encoding="utf-8")
panels = "\n".join(
    '<section id="'+html.escape(m['id'])+'"><h2>'+html.escape(m['figure_box'])+'</h2>'
    '<p>'+html.escape(m['purpose'])+'</p><p class="math">'+html.escape(m['math'])+'</p>'
    '<p><strong>Code:</strong> <code>'+html.escape(m['code'])+'</code></p>'
    '<p><strong>MiniGPT:</strong> '+html.escape(m['difference'])+'</p></section>'
    for m in MODULES)
links = " ".join('<a href="#'+m['id']+'">'+html.escape(m['figure_box'])+'</a>' for m in MODULES)
page = '''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Transformer modules and our MiniGPT</title>
<style>
body{margin:0;background:#fff;color:#192834;font:16px/1.6 Arial,sans-serif}header{padding:28px 5%;border-bottom:1px solid #ddd}
h1{font-size:28px;margin:0 0 8px}h2{font-size:20px;margin:0 0 8px}p{margin:8px 0}nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
nav a{border:1px solid #bbb;padding:5px 9px;color:#173e63;text-decoration:none;font-size:13px}a:focus,a:hover{background:#f3f0e5}
main{max-width:1500px;margin:auto;display:grid;grid-template-columns:minmax(320px,48%) 1fr;gap:36px;padding:32px 5%}
figure{margin:0;position:sticky;top:12px;align-self:start}img{display:block;width:100%;height:auto}figcaption{font-size:13px;color:#555;margin-top:12px}
section{padding:16px 0;border-bottom:1px solid #ddd;scroll-margin-top:16px}section:target{background:#fff8dd;outline:2px solid #bd922a;padding:16px}
.math{font-family:Consolas,monospace;background:#f4f5f6;padding:10px}code{overflow-wrap:anywhere}strong{color:#132f4b}
@media(max-width:800px){main{grid-template-columns:1fr}figure{position:static;max-width:600px;margin:auto}}
</style>
<header><h1>Transformer modules and our MiniGPT</h1>
<p>Read the original diagram from bottom to top. Choose a module below, explain its job, follow the equation, then find it in the code.</p>
<p>The left column is the encoder. The right column is the decoder. Our MiniGPT keeps a causal decoder route, with the differences explained beside each module.</p><nav>'''+links+'''</nav></header>
<main><figure><img src="assets/transformer-original.png" alt="Original Transformer Figure 1: encoder on the left, decoder with masked self-attention and cross-attention on the right">
<figcaption>Vaswani et al. (2017), Attention Is All You Need, Figure 1. Supplied lecture figure. Original encoder-decoder architecture; our MiniGPT uses Pre-LN, learned positions and GELU, and omits the encoder and cross-attention. <a href="https://arxiv.org/abs/1706.03762">Paper</a></figcaption>
</figure><div>'''+panels+'''</div></main></html>'''
(ROOT / "week02" / "resources" / "transformer-map.html").write_text(page, encoding="utf-8")
print("Built Week 2: 11 tasks, 100 minutes, 100 progress points, 5 optional topics.")
