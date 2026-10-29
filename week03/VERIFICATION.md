# Student release verification: 2.7.0

Date: 2026-10-29.

The complete plugin regression suite passed: 100 tests, no failures and no
skips, including the real Week 2 CPU training integration. Tests used disposable
workspaces, not existing learner records.

Coverage includes:

- Both formal Week 3 learning routes, original slide-first review and actual
  source-code excerpts with bounded, read-only pagination.
- Four MCP checkpoints between concept pairs. Incorrect answers cannot advance;
  two hints precede an optional answer explanation, followed by a new own-words
  response and mentor assessment.
- Existing lesson snapshots, original slide images, saved code, replay learning
  sessions and exact code-history backups remain intact after an update.
- The student CLI has no teacher walkthrough command or reveal-and-advance mode.
  Unsupported actions are rejected without changing learner records.
- Five public slash commands and valid Claude plugin/marketplace manifests.

The unchanged Week 3 source pack was also tested in a disposable copy populated
with instructor reference bodies: 45 tests passed. The distributed student source
retains all four intentional TODOs. These tests include real MCP SDK 2.2.0
subprocess/stdio discovery, structured results, missing-device errors, argument
validation and resource reading. Scripted model responses are labelled as such.

The nine original PPT images were exported read-only and visually inspected.
Titles, diagram explanations and source-code bridges were checked against the
lecture deck. The current DeepSeek API mapping is explained wherever the lecture
image uses older API fields.

No paid DeepSeek request was made during release validation. Live tasks t06,
t07 and t09 still depend on the student's privately configured account and network.
Natural-language teaching quality and host-specific choice-card rendering need
an interactive classroom check; automated tests do not claim a host UI test.

Package audits check English text, the five commands, syntax, forbidden private
files, secret patterns and pinned image hashes. A fresh GitHub checkout is
verified against SHA256SUMS.json after publication. These checks do not upload
learner progress or credentials.
