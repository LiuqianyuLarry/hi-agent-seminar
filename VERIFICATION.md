# Release verification

Date: 15 October 2026. Plugin version: 2.1.0. Fixed storage namespace/schema: v2 / 2.

## Week 2 checks performed

- All 60 plugin workflow/distribution tests passed, including real local PyTorch
  integration with WEEK02_TEST_PYTHON set. Standard-library-only runs explicitly
  skip that integration when no test interpreter is supplied.
- Actual torch 2.10.0+cpu/Python 3.12 validation ran the three starter tests,
  numerical attention, student-code patching, head/multihead/FFN/block checks,
  all eleven original model tests and the thirty-update fixed-batch probe.
- A separate recorded CPU benchmark used B=16, T=64, d=128, h=4, L=2, FP32,
  ten warm-up updates, 200 measured steps and one repetition. Measured time was
  4.2313 seconds (about 48,401 training positions/s); final train-side evaluation
  loss was 0.83464 and validation loss 0.86944. Actual parameter count: 428,800.
  These are this validation machine's measurements, not classroom performance promises.
- CUDA was unavailable to the CPU-only validation interpreter. Its record remained
  unavailable and the comparison awaiting_gpu at 68% core completion. There are
  no fabricated GPU timings, memory numbers or speedup. Live CUDA needs lab testing.
- Both actual injected-failure demos detected the deliberate faults: causal prefix
  max difference was 0 with the mask and about 0.06984 after removing it; omitting
  optimizer.step kept fixed-batch loss at about 4.41224. This is injected evidence,
  not a report of naturally occurring hardware failure.
- Actual CPU Batch sweep completed B=1,8,16 at fifty measured steps each. Context
  arithmetic and the KV/architecture concept adapters completed with correct labels.
  The optional three-repetition adapter also completed three actual CPU runs and
  retained CUDA unavailable. It remained awaiting_gpu; this release does not claim
  a real three-repeat CPU/CUDA comparison.
- Temporary-workspace tests verify saved concept depth, code before-files, wrong
  attempts, model/test hash matching, failed setup receipts, missing-GPU gates,
  full 0-to-100 mock workflow, separate optional progress, output reuse, reflections,
  Week 2 snapshot upgrades and byte-preserved Week 1 records/student files.
- The original Transformer PNG matches its reviewed source hash. The local HTML
  guide loaded that image, displayed fourteen module sections and passed desktop
  overflow checks. Top and selected Add & Norm views were visually inspected.
  The guide explicitly distinguishes encoder-decoder/Post-LN/ReLU/sinusoidal
  positions from this decoder-only Pre-LN/GELU/learned-position implementation.

The real-compute validation harness used explicit instructor answer/code fixtures;
it was not a live student or mentor conversation. Clickable concept cards and the
quality of each live mentor explanation still need observation in the classroom
host. No paid model API requests were made. No real student records were modified.

## Earlier Week 1 and distribution checks

- 38 workflow regression tests passed with mocked process calls: fresh state,
  restart/resume, empty leftover directories, nonempty student file preservation,
  Mentor-run venv setup, failed setup, private key handoff without reading it,
  no Task01 quiz, teaching before predictions, current source line numbers,
  exact chat-prompt saving, scaffold rejection, changed-prompt/run association,
  global-Python rejection, genuine result table interpretation, MCQ/open retries,
  hidden rubrics, 100% completion, optional progress, reflection drafts and bounded
  snapshots that exclude private/generated files.
- Six additional regressions cover the exact five commands, reflection routing,
  read-only browsing, per-week topic selection, setup readiness, missing interpreter,
  saved topic status, failed/pending/interrupted runs, corrupt records and unchanged
  core completion. Existing v2 records retain their schema and storage paths.
- Eight upgrade regressions verify byte-preserved learning files across plugin
  directory/version changes, new curricula versus pinned existing courses,
  teaching-note snapshots, adoption of existing 2.0.1 records, retired-course
  discovery, legacy-only protection, incompatible schemas/lessons, corrupt
  snapshots, and retained optional results and completed reflection reports.
  No real student records were modified by these tests; all use temporary workspaces.
- Six distribution tests verify that Git directory/worktree metadata and Claude
  runtime markers are ignored, while missing, changed and extra commands are
  reported. Total: 44 tests.
  GitHub installation/update instructions and release auditing were added in 2.0.3;
  the teaching helper and classroom examples are unchanged from 2.0.2.
- A clean GitHub clone passed the hash check and tests. The actual GitHub marketplace
  add/install commands succeeded in an isolated temporary Claude configuration;
  version 2.0.3 installed as enabled with all five commands. That test exposed the
  host-created .in_use marker directory, now excluded from verification in 2.0.4.
- The original classroom resources are unchanged from the v2.0.0 build, which
  passed 31 classroom-code tests using mocked HTTP responses. No live DeepSeek
  requests were made in this release check.
- The installed Claude Code validator accepted plugin.json and marketplace.json with
  `Validation passed`, without warnings.
- The package contains exactly five command files: menu, start, status, review,
  help. Optional practice is integrated into menu. English text, syntax and JSON
  checks passed. ZIP entries are compared byte-for-byte with the build, including
  hidden manifests. SHA256SUMS.json and verify-package.py detect missing/changed
  files after extraction; no learning records or API keys are distributed.
- Both core blocks total 50 minutes. Weights total 100. Core planned calls total 11.

## What these checks do not prove

Automated checks do not prove how every live mentor turn will be worded, whether
the host exposes AskUserQuestion in a particular mode, or the result of a future
model call. The actual clickable-choice interaction and live conversation were not
replayed during this build. The instructor's earlier feedback documents their own
live v1 testing; that is not represented as a live v2 test.

The setup tests mock installation rather than downloading packages into a student's
environment. Source code verifies the venv with an import/prefix check when setup
is actually run. Open answers use mentor rubric review. The helper records order
and evidence; it cannot prove the semantic quality of every explanation.
