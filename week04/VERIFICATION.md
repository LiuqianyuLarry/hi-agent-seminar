# Week 4 student release verification

Version 2.8.2 contains Week 4 lesson version 2. The instructor approved student publication after the W4.2 review. This distribution has no teacher-preview entry or shortcut.

## What was checked

- The complete plugin suite passed 130 tests, including the real Week 2 CPU integration and a real version-1 Week 4 archive upgrade check.
- The Week 4 tests cover both complete routes, separate required W4.2A/W4.2B submissions, support gates and retained version-1 snapshots.
- The completed Week 4 reference passed all 72 offline resource tests.
- Both Review and Practice completed tasks t01-t10 through the real helper in isolated learner workspaces. Tests used simulated learner responses and saved all five required function bodies across the four exercise groups through the same code-saving action used for chat submissions. They ran the actual local experiments and tests, read the results, and reached 100%.
- The checks cover saved answers, two gradual hints with learner attempts, an answer explanation followed by the learner's own explanation, before/after experiment gates, repeat acknowledgements, source/data changes, replay sessions and retained course snapshots.
- Existing Weeks 1-4 records, code and snapshots remained byte-for-byte unchanged in preservation tests. A new independent session receives lesson version 2; existing version-1 sessions do not acquire extra requirements. The shared storage schema and v2 namespace are unchanged.
- The original lecture PDF supplied 25 rendered pages. The images were visually checked and their hashes are pinned in the package audit. The teaching script explains where an old diagram simplifies the actual implementation.

## W4.2 input comparison

The same-summary counterexample uses `[82, 88, 90, 94, 97]` instead of the observed `[82, 87, 91, 94, 97]`. Both have five readings, mean 90.2, maximum 97 and four readings above the limit of 85. The returned statistics can all match while the input record is wrong.

Tests run the actual local tools on separate cases and check the argument comparison as well as the final verifier result. Replacing only `statistics_inputs_match` with `return True` makes the same-summary end-to-end test fail, while all numerical checks remain in place. The task cannot be tested or completed until both learner code bodies have been saved.

The release audit checks internal data hashes as well as package hashes and rejects instructor-only files, state and command routes. Final ZIP validation builds the database and runs preflight from the actual extracted bytes.

## Real API evidence

One real DeepSeek request was captured on 5 November 2026. The public response proposed both `get_machine_spec` and `query_temperature`. Those allowed local tools ran. The verifier then reported `stats` as missing; no second model request was sent.

The capture and its source hash are in `teacher-data`. Student analysis of this saved record makes zero API requests and is labelled `recorded_live`. The deliberately scripted failure experiments are labelled separately. A failed sandbox connection before the successful capture produced no usable response and is not presented as teaching evidence.

## What these checks do not establish

Automated helper tests do not prove how every host will display a formal reply or a choice card. The instructor has reviewed the interaction; automated checks still do not establish how every host renders each reply. The full optional live-model loop was not used to claim a measured model success rate. Offline API contract tests use explicit fake responses and are not teacher data.

The two 50-minute blocks are teaching targets. Extra explanations may take longer; the plugin does not mark unfinished work complete to meet a timer.
