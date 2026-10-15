# Week 2 inside the model

Start with /hi-agent-seminar:start week02 or choose Week 2 in the course menu.
The core lasts 2 x 50 minutes. Beginner concept cards let learners continue, request
a brief explanation or see an example. The mentor teaches logic, mathematics and
actual code, maps the original Transformer figure to the MiniGPT implementation,
and saves student code attempts before running real tests.

See TEACHING.md for the turn-by-turn guide, INSTRUCTOR.md for timing and hardware
requirements, SOURCES.md for source alignment, and resources/SETUP.md for pre-class
environment preparation. Core CPU/CUDA uses one repetition per device; repeat3,
Batch scanning, context cost, KV-cache concepts and architecture review are optional.

Progress uses the existing fixed v2 storage namespace with a separate week02 folder.
Week 1 remains intact. Existing courses keep saved lesson snapshots after updates.

To maintain the lesson, edit scripts/build-week02.py, regenerate lesson.json and
the local visual guide, then run the upgrade/workflow tests and release audit.
Do not move completed test-fixture implementations into learner resources. Future
weeks need their own tested runtime adapters; do not copy Week 2 hardware assumptions.
