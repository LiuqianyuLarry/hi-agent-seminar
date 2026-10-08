# Week 1 instructor guide: version 2

## Two teaching blocks

The break is outside the 100 minutes. Python and Claude Code should be installed
before class. Mentor Liu handles venv creation, package installation and import
checking; the student performs only the private key step. If setup or discussion
takes longer, save and resume rather than skipping the learning tasks.

| Block | Task | Minutes | Completion |
| --- | --- | ---: | ---: |
| 1 | Mentor-assisted environment setup; no quiz | 8 | 8% |
| 1 | Facts, causes and the CONV-3 task | 7 | 15% |
| 1 | Read the request/response code; make one API call | 15 | 30% |
| 1 | Student chat prompt, output comparison and token counts | 10 | 40% |
| 1 | Context A/B/C | 10 | 50% |
| 2 | Schema and source checks | 12 | 62% |
| 2 | One repair and a short failure note | 12 | 74% |
| 2 | Complete versus missing-evidence cases | 12 | 86% |
| 2 | Sampling, memory, RAG and agent scenarios; no execution | 7 | 93% |
| 2 | Five typed exit answers and recap | 7 | 100% |

Core experiments still plan 11 model generations. Service retries, learner-approved
reruns, mentor conversation and optional topics are additional. Do not promise a
fixed bill. The reflection-and-code review is available after class or on request;
it is not another condition for completing the 100-minute core.

## Changes that matter in class

Use TEACHING.md before each task. Show the task/purpose, define new terms and show
numbered source excerpts before asking a prediction. tutor.py code locates current
lines by function name. For theory tasks explain the relevant example before asking.
Use a horizontal rule and clear English labels to distinguish the response body.
The host's private thinking panel is not controlled by this plugin.

Do not ask students to edit a file or install packages during the normal sequence.
For Task04 they write the prompt in chat. The helper writes those words into the
working copy, remembers the draft and associates its hash with the resulting run.
The bundled file is a scaffold, so the activity is no longer an edit of an already
finished answer. Give a partial example, not a complete response to copy.

Show actual experiments in an Experiment observations block. Read field names and
values before asking students to locate them. Multiple-choice checks use the host's
real selector; open answers and reflections require the learner's own typed words.
Use meaningful hints, not internal rubric text. Preserve wrong attempts for learning.

## Interpretation

Teach the SDK message.content layer and the saved public_response content field as
two distinct structures. The shape of public_response can be read from the code
before execution. After running, use actual JSON fragments rather than the example.
The prompt token table must allow either result: the student's shorter requested
format is not guaranteed to yield fewer tokens. Discuss observed input/output counts
and requested length. Do not equate token counts with money or infer a universal rule.

Define schema and evidence checks before predicting outcomes. Teacher alterations
must be labelled. A schema pass does not prove a cause. A missing-evidence report can
honestly pass both demo checks with a null diagnosis. Count missing_information
entries from each actual report and read the corresponding CSV Outcome. If a real
report fails parsing, teach that actual failure instead of filling in an expected table.

Task09 asks for short scenario descriptions; it does not require code. Later seminars
will develop sampling, memory, RAG and full agent control. Their live extensions
remain optional. The graph/pause preview is not a durable workflow engine.

## Classroom checks after loading

Verify the host exposes exactly five namespaced commands (menu, start, status,
review, help) and AskUserQuestion, then try
the main chooser and a multiple-choice card. Start v2 in a student folder and confirm
0%, Mentor Liu, English presentation and no setup quiz. Have a learner submit their
own prompt in chat and check the file it saves. After a pause, resume in the same
folder. The code and workflow tests cannot prove the wording of every live mentor
turn; observe this behaviour in the actual classroom host. In menu, browse optional
topics before setup without starting a course, then revisit after setup and check
the saved topic status. Optional practice must not change the core percentage.
