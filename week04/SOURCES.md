# Week 4 material sources

The instructor supplied these three source artifacts. The seminar keeps their
main task, tools and four coding groups, with the adaptations below.

| Source artifact | SHA-256 |
| --- | --- |
| EEEE4149_Week4_Lecture_Building_an_Agent_from_First_Principles.pdf | `5f53a7029579d4c8308c707e1961d5ffdf2a31b6a32c9226bbf38bbe36b634b2` |
| EEEE4149_Week04_Teaching_Pack.zip | `d95a0a93b08fd67d9243317894366a317b70fff2200b6754b7d30c44c49a3c69` |
| EEEE4149_Seminar4_Student_Pack.zip | `d22d479e3c8df31e383d85dd435be71a6663b5251f9c829359aa7c507c91aaf3` |

The PDF has 40 pages. Its page numbers, not the older 36-page slide-design draft
inside the teaching ZIP, are used in lesson cards. Original page images and their
source checks are kept in `slides/`. They are visual sources, not claims that every
shortened code fragment is executable as displayed.

## Adaptations for this plugin

- The case identifier is CONV-3 instead of M12. Tasks, validation, data, tests and
  explanations use the adapted identifier together. The original PDF images keep
  their original labels; Mentor explains the mapping once.
- Student-visible prompts, reports, comments and teaching content use English.
  The explanations begin with a concrete problem and use ordinary words.
- The live model connection uses the same DeepSeek Chat Completions pattern as
  the earlier plugin weeks. This is a course consistency choice, not a claim that
  other API formats cannot support tool use.
- The four coding groups use small function bodies. W4.2 now has two required
  parts: the goal checklist in `verify` (page 9) and the argument comparison in
  `statistics_inputs_match` (page 14). A case with different input values but
  identical summary statistics prevents a count-only check from being enough.
  W4.4 connects one tool step in
  `complete_tool_step` while the supplied runtime retains the other control and
  error branches.
- A one-request experiment and bounded weak-loop demonstrations precede the
  exercises. Completed reference demonstrations remain separate from student
  files with TODOs.
- Tests and later comparisons use the student's saved code. The execution gate,
  observation recording, evidence verification and limits have separate roles.
- Databases are prepared from supplied synthetic data in the learning workspace;
  generated databases and experiment outputs are not source-code substitutes.

The original tools and data have been adapted. Do not describe these files as
byte-for-byte reuse of the old Week 3 package. Their current data manifest and
source notes describe the adapted files.

## What each kind of evidence means

`teacher-data/single_round.json` is a real saved DeepSeek opening experiment.
`teacher-data/SOURCE.json` records its provenance and integrity information.
Reading it in the seminar makes no new model request. A separate live choice
performs a new bounded request and records its own result.

The supplied teacher record contains one API request and no follow-up request.
The actual response proposed a specification lookup and a temperature query;
after local execution the statistics evidence was still missing. This is an
observation from that capture, not a rule that future responses return two tools.

Fault injections use scripted proposals so that the control problem can be
reproduced. The local tools may really execute. These records do not measure a
model's planning accuracy or natural error frequency. Earlier validation reports
inside the source ZIP remain historical evidence; they do not prove the adapted
plugin passed its own tests.

All temperature and reference data are synthetic classroom material. The reported
fraction counts readings above a reference. It does not establish a duration or
diagnose a real equipment fault.

## Supporting references

- [DeepSeek tool calls](https://api-docs.deepseek.com/guides/tool_calls/): the model
  requests a function, the application executes it, and matching tool results
  are returned in the conversation.
- [DeepSeek Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/):
  the response and tool-message fields used by this course adapter.
- [ReAct paper](https://arxiv.org/abs/2210.03629): interleaving action with returned
  observations. Plan-Act-Observe-Verify and the course's gates, budgets and task
  checker are a teaching implementation, not a claim that those are the paper's
  canonical four stages.
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html): separate
  mutable defaults through default factories.
- [Python subprocess timeouts](https://docs.python.org/3/library/subprocess.html):
  local process timeout behaviour. Ending a local wait does not prove that remote
  provider work or billing was cancelled.

The agent example has no cross-process checkpoint recovery. The seminar's saved
learning progress is a separate feature. Week 5 covers execution-state recovery.
