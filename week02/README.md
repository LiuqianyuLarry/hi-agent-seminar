# Week 2: reserved for the next seminar

No lesson is published here yet, so the chooser does not offer an empty course.

To add a week, create lesson.json with its own week ID, version, tasks and optional
extensions; add a clean resources directory and English teaching/source notes.
Core task weights must total 100. Use the Week 1 task schema, including terms,
code_refs, requires_teaching, requires_prediction, requires_setup and requires_prompt.
Questions use mcq options/correct/feedback or open prompt/rubric. Private rubrics
must not be displayed to students. A function code reference is [file, symbol];
a whole short text reference uses [file, null].

Each course uses its own v2 state and student resource paths. Current runner entry
scripts are explicitly limited to week1_demo.py and preview_agent.py; extend that
allowlist when a later course needs another script. Experiment scripts must accept
--output-dir and must not print credentials. Revisit setup/prompt requirements when
designing a different course. Give every prediction and check sufficient teaching
context. Add meaningful regression coverage for the new behaviour.

Update the plugin version for distribution, never the fixed PROGRESS_NAMESPACE.
Existing students continue their saved lesson/teaching snapshots and resource copy.
Keep the helper backward-compatible with those definitions and script entry points.
Use stable week/task IDs. A breaking record schema change needs an explicit tested,
backup-first migration; it must not reset progress or silently remap old answers.
New lesson versions apply to new learners, not already-started courses.
