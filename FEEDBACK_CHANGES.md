# Changes from the instructor's test feedback

Release: 2.0.2. Existing learning records are preserved across plugin updates.

| Feedback | Implemented change |
| --- | --- |
| 1, setup ownership | Mentor-run setup action creates the venv, installs with that interpreter and checks imports; only private key entry stays with the learner |
| 2, unhelpful setup quiz | Task01 has no prediction or graded questions; actual setup plus the private key handoff gates completion |
| 3, 4, 8, teaching before questions | Required teach checkpoint; terms and dynamically numbered code excerpts before predictions; preparation notes for every task |
| 5, 6, 7, ambiguous response structure | SDK/saved-JSON trees, clearly labelled illustrative JSON, actual post-run JSON, and an explicit code-reading question |
| 9, response presentation | Persona uses a separator, short English titles, labelled code/results/questions and a saved-progress footer; host thinking display is not claimed to be configurable |
| 10, unclear prompt editing | Scaffold replaces the completed template; learner writes in chat; write-prompt saves their exact wording and ties it to the experiment |
| 11, 12, real choices and observations | AskUserQuestion for MCQs/course selection; typed open answers; Experiment observations blocks; honest fallback if selector is unavailable |
| 13, token comparison | Actual prompt/completion/total tokens and time shown together; no guaranteed ordering or vague-prompt cost claim |
| 14, terminology | Schema/evidence definitions and comparison table precede code and questions |
| 15, ownership wording | Questions refer to this task's records and fields, not 'your run' |
| 16, case question | Explicit missing_information counts, diagnosis values and CSV Outcome, with no assumed model result |
| 17, scenario question | Task09 explicitly asks for one-sentence scenarios and requires no execution |
| Empty residual directories | Empty resource directories are reused; nonempty orphan student files are not overwritten |
| Missing manifest/update confusion | Plugin and local marketplace manifests included, versioned installation/update instructions provided |
| Five functions, simplified names | Only menu, start, status, review and help are exposed under /hi-agent-seminar: |
| Optional topics in the course directory | Menu includes each week's topics and saved status, concept recaps, setup checks and approved live practice |
| Incomplete distribution | Five-command and manifest checks plus a hash inventory verify the ZIP and extracted folder |
| Original persona | Mentor Liu, respectful coaching, minimal hints, no answer-key exposure, real selectors, observations blocks and every-response progress footer |
| Language confirmation | All supplied content is English; only an explicit student translation request permits a Chinese explanation |

The full learning flow remains 2 x 50 minutes with optional sampling, reasoning,
memory, RAG, additional cases and workflow/agent practice. New v2 progress saves
normally. No Feishu submission is present. Reflection reviews include learner text
and a source snapshot. Existing learning reports can be exported on request in chat.
Version 2.0.2 keeps fixed record paths and pins each started course's lesson and
teaching notes. Existing compatible v2 records gain snapshots on resume. Student
code, answers, runs, reflections and optional records are not replaced by updates.
Legacy-only or incompatible records stop for recovery/migration, never a reset.
