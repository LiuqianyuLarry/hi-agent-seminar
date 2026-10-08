# Version 2 verification

Date: 9 October 2026. Plugin version: 2.0.3. Fixed storage namespace/schema: v2 / 2.

## Checks performed

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
- Five distribution tests verify that Git directory/worktree metadata is ignored,
  while missing, changed and extra command files are reported. Total: 43 tests.
  GitHub installation/update instructions and release auditing were added in 2.0.3;
  the teaching helper and classroom examples are unchanged from 2.0.2.
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
