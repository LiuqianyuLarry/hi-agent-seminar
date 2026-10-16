---
description: Browse seminar weeks, continue learning, or choose optional topics
---

Read `${CLAUDE_PLUGIN_ROOT}/persona.md`. Read MENTOR.md only after the student
chooses learning or practice. Reuse unchanged instructions already in context.
Use `${CLAUDE_PLUGIN_ROOT}/tutor.py` with Python 3.11+, the student's current
project directory as --workspace, and an explicitly selected --week when needed.
All student-facing content is English; Chinese is allowed only for an explicitly
requested translation. Follow the persona and exact saved progress footer.

## Course directory

Call list. Show each available week's title, core duration and exact saved core
percentage, followed by its optional_topics titles, purposes and saved learning_status.
Label optional progress separately; it never contributes to the core percentage.
Do not list week02 as available until it has a lesson.json. Do not reveal rubrics.
If a course has an error, explain it; do not reset it or present it as a fresh course.

Use genuine AskUserQuestion cards: Continue first for unfinished active progress,
available weeks, and Browse only. Paginate within the host's option limit. Map cards
to IDs yourself; students need not type them. If the host lacks AskUserQuestion,
say so and offer lettered choices. Browse only and Back do not write progress.

Selecting a week opens a submenu without starting it: Continue saved progress,
Start again from the beginning, Choose an earlier learning session, Optional topics,
and Back. Paginate if necessary. Unstarted weeks offer Start learning instead.
Always wait for the mode choice; even a top-level Continue shortcut must offer it.
Continue calls start. Start again calls restart to create separate progress and
fresh starter code at 0%, preserving every old session. Earlier session calls
sessions, then select-session --session ID after the learner selects a dated record.
Explain that new sessions need separate setup and Week 1 private key configuration;
never copy credentials or start paid calls just because restart was selected.
For core, read MENTOR.md, task/code and only the current section of the saved guide.
Never skip new-session tasks because an earlier session completed them.
After an update, never clear progress or overwrite student resources.
If records are incompatible, report the preservation/recovery error; do not suggest
starting a new workspace as a way around it. When core is 100%, show
Core complete and offer Start again, optional topics or review.

## Optional topics inside the selected week

Offer the week's optional_topics with separate saved statuses, plus Back and
Browse only; paginate. Use extension --name TOPIC --week WEEK to read its purpose
and learning guide without starting the course. Offer a short concept recap first;
browsing or recapping alone must not mark an experiment as finished.

For live practice, check optional_practice_ready from list. If it is false, explain
that the selected week's environment must be completed first (Week 1 also needs
private API-key setup; Week 2 needs PyTorch and no key). Offer
Start/Continue core to finish setup, or Back. Do not install packages, start the
course or run a model call solely because the student browsed a topic.

If ready, call code --name TOPIC --week WEEK. Explain the task, purpose, simple
terms, actual numbered code, planned API calls and expected output fields. Get the
student's own prediction and approval for calls before run-extension --name TOPIC
--week WEEK --prediction STUDENT_WORDS --intro TASK_AND_PURPOSE. Inspect results
--name TOPIC and actual artifacts; explain actual output structure and limitations,
then save explain-extension. Never report a failed/pending run as completed.
If a successful run is awaiting explanation, explain that saved result without
rerunning it. If a run is pending, follow recovery guidance; do not duplicate it.
A previously discussed topic can be revisited; new live calls require approval.
Offer Back to optional topics, Continue core, or Finish for now after discussion.
Keep the saved core percentage unchanged throughout optional practice.

For Week 2, begin with its saved teaching guide and concept cards. Offer
I understand - continue / Explain briefly / Show an example and save the real
choice with concept-choice. Use diagram for the original Transformer module map,
then teach logic, mathematics and source code in that order. Use write-code for
the student's forward-method body. Week 2 has zero model API calls. Its measured
local CPU/CUDA work still needs the student's approval before execution.
