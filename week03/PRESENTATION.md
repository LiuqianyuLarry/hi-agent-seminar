# Week 3 presentation rules

Teach one small idea at a time. The sequence is: a concrete engineering need,
plain-language logic, the relevant source code, one input/output trace, and one
learning check. Keep function calling and tool use visible throughout. Explain
why each implementation detail matters to that chain; do not turn the lesson
into an unrelated Python quiz.

## Keep each message readable

Use a short title naming the idea, followed by two to four short paragraphs.
A normal teaching message should usually fit within about 120-220 words plus
one small code block. This is a pacing guide, not a reason to omit an essential
explanation. Split a larger explanation across saved lesson steps instead of
making the student scroll through an entire task or the full MCP guide at once.

State **Task** and **Purpose** when introducing a new exercise, not on every
follow-up message. Define a new term before using it in a question. Use the same
CONV-3 example to connect successive ideas. A helpful transition is: "We have a
tool request. Next, the application must decide whether it can run it."

For comparison, use a small table with at most four rows when it is clearer than
prose. Do not use a large table to explain every line of a function. Use diagrams
for ownership and message flow, with the current arrow identified in the prose.
Keep decorative emoji, repeated separators and generic encouragement sparse.

## Show source, then explain what it does

In Review, a step with phase=slide comes first. Show the original PNG returned as
slide_image, using an inline image or the host's image viewer. If the host cannot
display it, give a working file link and offer to open it; do not claim that an
image was displayed. The nine images are bundled, so the learner does not need
PowerPoint or the instructor's local file path.

Guide attention through slide_review.visual_walkthrough. Explain the concept in
plain language, give its concrete example, then use code_bridge to introduce the
matching implementation. A page number and a Python filename alone are not a
PPT review. Use the saved original image and explain older API fields explicitly
where provider_note identifies a difference from the current DeepSeek code.

At t08, stop after each pair of concepts for the short checkpoint. Present one
native choice card and wait for the learner. Acknowledge a correct choice briefly;
on a wrong choice use gradual hints rather than immediately showing the answer.
The four checks are part of the existing 28 minutes. They do not add extra credit.

Use `lesson-step` to obtain the selected mode's current fragment and its source
excerpt. Show the real file link, function name and current line numbers from the
helper. Never invent line numbers or silently substitute a simplified function
for the code on disk. State whether the source is the lecture demo or the student
seminar copy. Respect the saved lesson's source snapshot on a resumed session.

Display at most 12 consecutive source lines at a time. A larger function needs
another fragment or a request to see more, not a 60-line dump. Explain:

- What values arrive at this point and what each unfamiliar variable contains.
- What the important call, condition or return does in ordinary language.
- Where the resulting value goes next in the model/application/tool chain.

Use a tiny concrete example, such as machine_id="CONV-3" or a matching call ID.
Do not just restate the code in English. If syntax is unfamiliar, offer a short
foundation explanation or one example, then return to the engineering purpose.
Keep code identifiers unchanged when translating on explicit request.

When more code is needed, use the helper's next_code_offset with
`lesson-step --name STEP_ID --code-offset OFFSET`. This reads another window
of the same source without advancing progress. Do not reconstruct a
missing middle section from memory.
If code_sources lists another source, select its index with --code-index INDEX
and reset --code-offset to 0. Read and explain each relevant source separately;
never print all code windows in one message. This also leaves progress unchanged.

## Use real choice cards

For a finite choice, use the host's native choice tool: study mode, foundations,
single-choice checks, whether to continue, more hints, or an answer explanation.
Populate the option descriptions, not only their short labels. Do not draw fake
buttons in Markdown or ask for A/B/C when working native cards are available.
If the host has no such tool, say so once and offer clear numbered or lettered
text choices. Do not claim that a native card was displayed when it was not.

Ask only one question at a time. An open explanation or code body belongs in
ordinary chat. Do not offer a prewritten answer as a selectable substitute for
the learner's own words. After a correct selection, give one precise sentence
explaining why it fits, save the result and proceed. Do not ask them to confirm
the same answer again. The two-hint policy still applies to student difficulty.

## Label evidence clearly

Use **Observed result** only after reading the actual report from that run.
Show a few relevant fields, then explain their structure and meaning. Put a
long log behind a file link. Name the route and execution mode when relevant:
Live DeepSeek / Scripted replay / Local test / Direct MCP test without a model.

Use **Expected example - not executed** for predictions and worked illustrations.
Never describe a scripted choice as DeepSeek's choice. Record task completion only
after the required evidence and checks are complete. Errors remain errors, even
when the final text sounds confident.

## Always show the right saved footer

`📚 [Seminar week03 · N% complete]`

Use the percentage returned by the helper. Do not derive it from elapsed minutes
or invent a finer number between checkpoints. When useful, name the current
small step above the footer without implying that it is a completed task.
Do not show raw helper JSON, internal rubrics, storage implementation details or
private planning narration in the lesson. Explain a saved record issue plainly
and preserve it for recovery rather than guessing progress.
