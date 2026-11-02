# Release verification: 2.7.1

Date: 2026-11-02. Publication authorized by the instructor after local review.

The complete plugin regression suite passed during local validation: 107 tests, no failures or skips,
including the real Week 2 CPU training integration. Tests used disposable
workspaces. No existing learner record was used for testing.

Release preparation repeated the seven delivery tests successfully and validated
both Claude manifests. These tests verify that:

- Every successful helper CLI action carries the current formal-response policy.
- Saved progress comes from course status or the active catalogue entry, not
  fields that merely resemble progress inside experiment data.
- Older Week 1, Week 2 and Week 3 lessons use the current OUTPUT.md policy while
  their progress, course snapshots, teaching snapshots and student source bytes
  remain unchanged.
- Reading code and lesson fragments does not advance learning progress.
- Response instructions are not written into learner notes or state.
- Adding delivery metadata leaves nested observations and artifact data intact.

The four MCP checks, two-hint support, own-words assessment, source/slide
snapshots, five commands and removed teacher shortcut remain covered by the
existing student-release regression tests. No storage namespace, record schema,
course task weight or saved curriculum was migrated for this presentation fix.

Each command now reads the installed OUTPUT.md policy. Helper output includes a
response_contract linking that same current file, including when old lesson
snapshots are resumed. Complete relevant teaching belongs in the formal reply;
process updates contain only brief operational status. Actual results must be
explained outside tool logs. Saved teaching acknowledgements refer to a prior
visible explanation and must not bypass task or checkpoint gates.

No paid model call or new dependency download was made in this revision. The
Week 3 tool source and its intentional TODOs were not changed.

Automated checks establish metadata delivery and record preservation. They do
not establish that Claude or Codex rendered a message in a particular UI area.
The plugin cannot control the host's thinking panel or verify that a learner
read a message. The instructor authorized this release; these checks make no
claim of automated host UI verification.
