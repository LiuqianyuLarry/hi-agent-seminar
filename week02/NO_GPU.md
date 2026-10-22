# Week 2 without a GPU

Two equally valid learning paths share the same 100-minute core and 100% endpoint:
local CPU plus local CUDA, or local CPU plus teacher reference analysis. Both keep
the existing code, prediction, actual-output explanation and understanding gates.
The second path is for unavailable CUDA; a failed CPU experiment is not eligible.

## Mentor workflow

1. Explain the task and purpose. Ask whether the student has a working CUDA GPU.
   If not, explain that they will measure their CPU and study the teacher's real
   paired measurements. Run the normal benchmark with approval: it records one
   CPU run and CUDA unavailable. Reuse a saved awaiting_gpu run with the current
   model; do not rerun simply to attach teacher data.
2. Read results and verify that CPU measurement and plotting succeeded. Obtain
   the instructor-approved benchmark directory with cpu_r1/metrics.json and
   cuda_r1/metrics.json, produced by the supplied training code. Do not substitute
   tutorial timings, invented values, test fixtures or an unrelated model.
3. Call `reference-data --week week02` to use the bundled measured teacher pair
   and its provenance. For a replacement instructor-approved dataset, use
   `reference-data --reference-dir PATH --text "Instructor name, measurement
   date, hardware identification and source/provenance" --week week02`. This copies
   the two JSON records into the student's session, records their hash and source,
   checks equal workload and units, and binds them to the saved local CPU run.
   File checks establish consistency, not independent proof of authentic execution.
4. Present separate labelled tables: "Local CPU experiment" and "Teacher reference
   CPU/CUDA experiment". Explain time in seconds, throughput in training positions
   per second, equal work, n=1, RSS and allocated CUDA memory. Save the discussion
   with explain AFTER attachment. Use the teacher pair for speedup; never mix a
   student's CPU time with a teacher's CUDA time to claim local acceleration.
5. Ask the question returned by reference-data. Wait for the student's own typed
   explanation. Use reference-answer --text STUDENT_WORDS, then evaluate using the
   returned private rubric and reference-assess --verdict pass|retry --text FEEDBACK.
   Apply the two-hint/optional-answer-explanation/own-word-restatement rule as usual.
   A pending or retry answer blocks completion. Complete the ordinary fairness MCQ
   as well. Do not submit a mentor's worked answer as the student's explanation.
6. Call complete only after all requirements pass. Progress moves from 68% to 80%.
   Continue w209 using local CPU loss/samples and labelled teacher device metrics,
   then w210 and w211. Normal checks take progress to 100%. The local raw run remains
   awaiting_gpu; the learning path records why educational completion is valid.

New benchmark runs, changed model code or changed reference files invalidate the
binding; attach evidence and assess again when needed. Replacing teacher evidence
keeps older files and attempts. Updates do not reset progress, modify existing
lesson snapshots or copy over student resources. No new slash command is added.
Optional repeat3 is still a real-device experiment; this exception is core w208 only.

## Instructor data requirement

Supply a successful paired run of the supplied completed MiniGPT on CPU/CUDA with
B=16, T=64, d=128, 4 heads, 2 blocks, FP32, 10 warmup and 200 timed updates. Retain
both metrics.json files, environment and hardware identifiers, initialization/data
hashes, timing scope and memory scopes. Record your name and measurement date.
The original files can be provided locally; no internet connection is needed to
read the attached session copy afterwards.

The bundled teacher-data directory contains actual measurements made on 22 October
2026 on the same i9-13900K / RTX 4090 Windows workstation, using PyTorch 2.10.0+cu128.
CPU: 3.6691393 seconds; CUDA: 1.4046646 seconds; CPU time / CUDA time: 2.6121.
Both processed 204800 training positions, with matching initialization and batch
hashes. Eleven model tests passed before execution. Raw metrics, loss curves and
generated samples are included, together with provenance and source-code hashes.
These are single runs on an active WDDM workstation, not universal performance
claims. The instructor implementation is not copied into student exercises.
Synthetic unit-test fixtures are separate and never used as teacher measurements.
