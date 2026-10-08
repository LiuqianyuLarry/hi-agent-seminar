# Source alignment

Prepared from the instructor-supplied Week 1 files on 8 October 2026:

- `EEEE4149_Week1_Lecture_Enriched_v6.pptx` (43 slides).
- The supplied Week 1 knowledge handout, version 4 (DOCX).
- `EEEE4149_Week1_Code_Resources_DeepSeek_Online_v1` (Python code and synthetic data).
- The existing `hi-agent-lab-main/hi-agent-lab` was inspected as the original plugin
  reference. This package is separate: no original files, webhook or submission
  configuration were changed or carried over.

The slide anchors below refer to **actual order in the PPTX**, not printed slide
numbers. "Who decides what?" is now slide 9, although its old printed number is 38.
The handout still uses some earlier slide references. Follow topic titles when they
disagree. Slide 41 now covers pre-Seminar tool setup. No source deck or DOCX was edited.

| Seminar task | Actual PPT order / topic | Handout topic sections | Resource |
| --- | --- | --- | --- |
| Setup | 25 API/SDK; 26 first call; 41 tool setup | 6 Python/API | configure.py; live_client.py |
| Evidence recap | 7-9 agent/control; 12-15 CONV-3 | 2-4 model/application/agent and tools | data/conv3_log.txt |
| API trace | 25-26 API and first call | 6 Python/API | week1_demo.py --demo api |
| Prompt | 27-28 instruction exercise | 7 prompt and evidence | --demo prompt; student/instructions.txt |
| Context | 30-31 history and workbench | 8 context/history | --demo context |
| Validation | 34-36 checks, JSON, wrong type vs unsupported claim | 9 JSON/Pydantic | --demo validation; lesson_core.py |
| Failure | 37 bounded failure handling | 10 failure and stop decisions | --demo failures |
| Cases | 12 CONV-3; 34-37 checking and failure | 12 exercises | --demo seminar --case ... |
| Future concepts | 21-22 sampling; 32 memory; 33 RAG; 7-9 and 38-40 control | 5 generation; 8 memory/RAG; 11 workflows/graph | Optional sampling, memory, rag, preview_agent.py |
| Exit check | 42 five-question exit check | 13 self-test | student/exit_check.md |

The API code uses DeepSeek's OpenAI-compatible Chat Completions interface. The slide
example uses Responses-style fields. Teach their conceptual correspondence, not
literal interchangeability: `instructions` -> a system message; `input` -> user
messages; `output_text` -> SDK `choices[0].message.content`. In the saved, simplified
API exchange JSON, that content is stored at `response.choices[0].content`.

The provided core code was copied, not rewritten. Defaults and dependency pins are
preserved. Original instructor keys, environments, old run artifacts, Chinese-only
guides and duplicate slide files are excluded. New packaging adds an empty
`.env.example`, ignore rules, the seminar plan and progress layer. Resource tests
retain explicitly labelled mock responses solely for testing; no mock reply is a
production fallback.

Version 2 incorporates the instructor's 8 October test feedback and the original
five command functions and Mentor Liu persona. The student instructions.txt is now
a scaffold; students compose the prompt in chat and the helper saves it. Python
demo logic and dependency pins remain unchanged. The new edition has separate local
progress paths and does not import the earlier test session.

Plugin layout and local loading were checked against the primary
[Claude Code plugin documentation](https://code.claude.com/docs/en/plugins) and
[manifest reference](https://code.claude.com/docs/en/plugins-reference).
