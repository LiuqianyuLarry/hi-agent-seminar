---
description: Show the active seminar and saved progress
argument-hint: "[week01]"
---

Read `${CLAUDE_PLUGIN_ROOT}/persona.md` and `${CLAUDE_PLUGIN_ROOT}/MENTOR.md`.
Use `${CLAUDE_PLUGIN_ROOT}/tutor.py` with an available Python 3.11+ interpreter,
the student's current project directory as --workspace, and the selected --week.
All student-facing content is English; Chinese is allowed only for an explicitly
requested translation. Follow the persona's presentation and progress footer rules.

Run list for the current student workspace. If $ARGUMENTS supplies a valid week with progress, use it; if an explicit week is invalid or unstarted, explain that without silently switching courses. Otherwise use active_week from list. If none has started, invite the student to use /hi-agent-seminar:menu. Otherwise run status and report the exact percentage, current task, optional-topic records and next step in English. Do not start or advance any task.
