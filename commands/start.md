---
description: Start or resume Week 1, Week 2, Week 3 or Week 4 with Mentor Liu
argument-hint: "[week01|week02|week03|week04]"
---

Read `${CLAUDE_PLUGIN_ROOT}/OUTPUT.md` before persona, lesson or saved-guide
instructions. Its formal final-response delivery rules apply to every week and
existing session. Keep tool preambles to brief operation status; place the complete
student-facing explanation, relevant code/results, one next question or action,
and exact saved progress in the formal reply. A helper record or tool log is not
that reply. Follow OUTPUT.md when sequencing blocking native choice tools.

After selecting a Week 3 learning session, show these native route cards with their
full descriptions:

- Review lecture + code: Look back at the actual PPT slides, explain their diagrams
  and examples in plain English, then walk through the matching lecture code and
  apply it in the seminar.
- Start seminar practice: Start the CONV-3 temperature-tool exercises. Learn the
  concepts and code needed for each task as you go.

Common caption: Both paths take two 50-minute sessions. Both include detailed code
explanations, optional foundation explanations, and the full MCP lesson before
practice.

Save study-mode after the actual choice. Read week03/INSTRUCTOR.md and
week03/PRESENTATION.md, then use lesson-step for the selected route's next small
fragment. Review first shows and explains slide_image/slide_review, then the
matching lecture_demo code. Practice uses the seminar source directly. Deliver
the complete fragment in a formal reply first. At the next learner continuation
or eligible attempt, record lesson-next with its exact ID and the actual text
already delivered, subject to all checkpoint gates. A clarification, translation
or request to inspect code does not advance the step. Do not substitute the same walkthrough
for both modes. Respect saved lesson/source snapshots; do not silently migrate
old Week 3 answers. A fresh session offers the revised course while preserving
older sessions. For an explicit revisit request, show that earlier content instead
of redirecting to the next unfinished task. Load only the current fragment.


Read `${CLAUDE_PLUGIN_ROOT}/persona.md`. Defer MENTOR.md and weekly guides until
the learner chooses a learning mode; reuse unchanged instructions already in context.
Use `${CLAUDE_PLUGIN_ROOT}/tutor.py` with an available Python 3.11+ interpreter,
the student's current project directory as --workspace, and the selected --week.
All student-facing content is English; Chinese is allowed only for an explicitly
requested translation. Follow the persona's presentation and progress footer rules.

Run list once. Select the supplied valid week, or offer weeks with the active week
first. An explicit week selects only the week, not permission to resume automatically.
Every entry into start must offer "Continue saved progress", "Start again from the
beginning", and "Choose an earlier learning session" when records exist. Show the
active percentage. For an unstarted week offer "Start learning" and "Back".
Use genuine neutral choice cards, or explain the lettered fallback. Wait for a
choice. Continue calls start. Start again calls restart, creating a separate fresh
session at 0% with clean exercises; old progress/code/results remain untouched.
Explain that environment preparation is separate and Week 1 needs private key
configuration again; new live calls require approval. Never copy credentials.
Earlier session calls sessions, shows dates and percentages, then select-session
--session ID after a choice. Do not make students type IDs. Back does not write.
After selecting a session, read MENTOR.md and only the current task's section of
the saved teaching guide, then task/code. Teach all required steps in the new
session; never skip them because a previous session completed them. At 100% offer
restart, optional topics or reflection review. Preserve errors for recovery.

Week 3 t08 has four required mini-checks between pairs of concepts. Use the
lesson-answer/hint/solution/assess helpers and wait for real learner responses
before lesson-next. A teaching acknowledgement alone cannot pass a check.

## Week 4 learning route

For week04, read week04/INSTRUCTOR.md and week04/PRESENTATION.md after the learner
chooses a session. Use the route cards from the saved lesson. Review starts with
Week 1's connection to a model and Week 3's tools, then follows a CONV-3 task that
needs several connected actions. Let the learner see a single response, a short
loop, and the repeat/early-finish problems before introducing the checks that fix
them. Explain the relevant lecture picture and actual source at each point. Use
ordinary English sentences and concrete examples; avoid slogans or compressed
labels in place of an explanation. Practice begins with the matching exercise and
keeps its necessary explanations and checks. Both routes take 2 x 50 minutes.

Use lesson-step for one small part. before_run parts prepare the experiment.
When needs_run is true, save the actual prediction and code if required, then run
the experiment. Read its result before teaching after_run parts. Do not try to
finish all path steps before running, and do not present expected values as
observations. Save delivered teaching with lesson-next at the next natural reply.
Week 4 uses lesson-answer/hint/solution/assess for checkpoints, and the support-*
helpers for code or open questions. Give attempts between the two hints. After
explaining an answer, check the learner's own explanation before continuing.

Core includes a teacher's recorded real DeepSeek single-round request and local
experiments. Label teacher records, local execution, injected faults and live
requests separately. The recorded route requires no key or GPU. run --live on t02
needs explicit approval for one request; it never silently falls back to a record.
The API can return multiple tool requests. Our full teaching loop's one-action
rule is an application choice, not an API restriction. The task uses three domain
tools; a report is not necessarily a fourth tool call.

Learning progress and learner code remain saved in v2. The example agent's run
state is a separate topic: Week 4 does not implement checkpoint recovery. Use
revisit for earlier explanations or restart for separate fresh exercises; keep
every previous learning session. Do not use the Week 1 setup flow for Week 4.

Week 4 lesson version 2 has two required code bodies in t06: W4.2A `verify` and
W4.2B `stats_inputs` (`statistics_inputs_match`). Read `required_code_targets`
from the saved task and `pending_code_targets` from the helper. After the
preparation steps, ask for and save each actual learner body separately. Do not
fill the second body yourself or treat the first submission as both. Explain why
same count and even identical summary values do not prove identical source
inputs. Both bodies, their tests, and the two understanding responses are required
before completing t06. The task still takes 15 minutes within the 100-minute core.
Older saved lessons keep their original requirements; offer a separate fresh
session to experience version 2 rather than modifying their snapshots or code.
