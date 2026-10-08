"""Live DeepSeek classroom demonstrations. No offline replies or replay mode."""
from __future__ import annotations
import argparse
import copy
import csv
import json
import sys
import uuid
from pathlib import Path
from typing import Any
from lesson_core import (ROOT, BASE_INSTRUCTIONS, JSON_INSTRUCTIONS, LessonError,
    get_case, read_json, report_input, check_report, print_json, save_record, teaching_validation_case)
from live_client import request_text

DEMO_SLIDES = {"api": [25,26], "prompt": [27,28], "sampling": [21,22], "reasoning": [29],
    "context": [30,31], "memory": [32], "rag": [33], "validation": [34,35,36],
    "failures": [37], "seminar": [20,26,27,30,35,36,37]}

def ask(args: Any, instructions: str, input_data: Any, *, json_output: bool = False):
    return request_text(instructions, input_data, args.temperature, json_output=json_output,
        output_dir=args.output_dir, client=getattr(args, "_client", None), options=getattr(args, "_options", None))

def record(args: Any, mode: str, payload: dict[str, Any]) -> None:
    path = save_record(args.output_dir, mode, {"ppt_slides": DEMO_SLIDES[mode], **payload})
    print("Saved demonstration record:", path)

def generate_report(args: Any, case: dict[str, Any]):
    payload = report_input(case)
    instructions = JSON_INSTRUCTIONS
    if args.instruction_file: instructions = args.instruction_file.read_text(encoding="utf-8")
    result = ask(args, instructions, payload, json_output=True)
    return result, payload, instructions

def run_api(args: Any) -> None:
    case = get_case(args.case or "complete")
    instructions = BASE_INSTRUCTIONS + " Extract known facts and list evidence still needed."
    if args.instruction_file: instructions = args.instruction_file.read_text(encoding="utf-8")
    print("INPUT:\n" + case["input"])
    result = ask(args, instructions, case["input"])
    print("LIVE MODEL OUTPUT:\n" + result.text)
    record(args, "api", {"instructions": instructions, "input": case["input"], "output": result.text, "metadata": result.metadata})

def run_prompt(args: Any) -> None:
    case = get_case(args.case or "complete")
    requirements = [BASE_INSTRUCTIONS + " Extract known facts and list missing evidence.",
                    BASE_INSTRUCTIONS + " Return two known facts, then one item to confirm."]
    if args.instruction_file: requirements[1] = args.instruction_file.read_text(encoding="utf-8")
    records = []
    for label, instruction in zip(["Original requirement", "Changed requirement"], requirements):
        print("\n" + label + ":\n" + instruction)
        result = ask(args, instruction, case["input"])
        print("LIVE MODEL OUTPUT:\n" + result.text)
        records.append({"label": label, "instructions": instruction, "output": result.text, "metadata": result.metadata})
    print("Same supplied evidence; one requirement changed. Both replies are real API responses.")
    record(args, "prompt", {"input": case["input"], "runs": records})

def run_sampling(args: Any) -> None:
    records = []
    for index in range(2):
        result = ask(args, BASE_INSTRUCTIONS + " Summarise the temperature finding in one sentence.", get_case("complete")["input"])
        print(f"LIVE REPLY {index + 1}: {result.text}")
        records.append({"output": result.text, "metadata": result.metadata})
    print("The two replies may be identical. Variation does not prove that a claim is correct.")
    record(args, "sampling", {"runs": records, "identical_text": records[0]["output"] == records[1]["output"], "temperature": args.temperature})

def run_reasoning(args: Any) -> None:
    evidence = (ROOT / "data/reasoning_evidence.txt").read_text(encoding="utf-8")
    result = ask(args, BASE_INSTRUCTIONS + " Cite supplied source IDs and give the simple temperature calculation. State what remains unconfirmed.", evidence)
    print("SUPPLIED EVIDENCE:\n" + evidence); print("LIVE EXPLANATION:\n" + result.text)
    difference = 97 - 85
    print("Python independently recomputed:", difference, "degrees C above the threshold.")
    print("Check the response's numbers and citations. This recomputation does not verify every sentence.")
    record(args, "reasoning", {"evidence": evidence, "output": result.text, "python_difference_c": difference, "metadata": result.metadata})

def run_context(args: Any) -> None:
    sample_id = "LAB-" + uuid.uuid4().hex[:6].upper()
    instructions = "Write in English. Use only the supplied request. If the sample ID is absent, say it is unknown; do not guess."
    first = f"The sample ID is {sample_id}. Reply only: Received."
    question = "What is the sample ID?"
    a = ask(args, instructions, first)
    b = ask(args, instructions, question)
    history = [{"role": "user", "content": first}, {"role": "assistant", "content": a.text}, {"role": "user", "content": question}]
    c = ask(args, instructions, history)
    for label, inp, result in [("A: first request", first, a), ("B: no history", question, b), ("C: history supplied", history, c)]:
        print("\n" + label); print("INPUT:"); print_json(inp); print("LIVE OUTPUT:", result.text)
    print("The program supplies history. Sharing an API key does not automatically provide it.")
    record(args, "context", {"sample_id": sample_id, "A": {"input": first, "output": a.text, "metadata": a.metadata},
        "B": {"input": question, "output": b.text, "metadata": b.metadata}, "C": {"input": history, "output": c.text, "metadata": c.metadata}})

def run_memory(args: Any) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / "memory.json"
    if not path.exists(): path.write_text(json.dumps(read_json("memory.json"), indent=2), encoding="utf-8")
    memory = json.loads(path.read_text(encoding="utf-8")); preference = memory.get("cite")
    if not isinstance(preference, str): raise LessonError("memory.json needs a string field named cite.")
    evidence = {"alarm": read_json("alarm_log.json"), "manual": retrieve_manual()}
    instructions = BASE_INSTRUCTIONS + " Summarise these supplied sources. " + preference
    result = ask(args, instructions, evidence)
    print("MEMORY FILE:", path); print_json(memory); print("CURRENT INSTRUCTIONS:", instructions)
    print("LIVE OUTPUT:", result.text)
    print("Edit the memory file and rerun to make a new model request. Model parameters do not change.")
    record(args, "memory", {"memory": memory, "instructions": instructions, "evidence": evidence, "output": result.text, "metadata": result.metadata})

def retrieve_manual(keyword: str = "overcurrent", equipment: str = "CONV-3") -> dict[str, Any]:
    for passage in read_json("manual_entries.json"):
        if passage["equipment_id"] == equipment and passage["current"] and keyword in passage["keywords"]: return passage
    raise LessonError("No current matching manual passage was found.")

def check_retrieval(passage: dict[str, Any], keyword: str = "overcurrent") -> list[str]:
    issues = []
    if passage["equipment_id"] != "CONV-3": issues.append("Wrong equipment model.")
    if not passage["current"]: issues.append("Outdated manual revision.")
    if keyword not in passage["keywords"]: issues.append("Irrelevant passage.")
    return issues

def run_rag(args: Any) -> None:
    entries = read_json("manual_entries.json")
    index = {"correct": 0, "wrong-equipment": 2, "outdated": 3, "irrelevant": 4}[args.retrieval_case]
    passage = entries[index] if index else retrieve_manual()
    print("RETRIEVED LOCAL SOURCE:"); print_json(passage)
    issues = check_retrieval(passage)
    if issues:
        print("SOURCE BLOCKED:", "; ".join(issues)); print("No generation request was made for this rejected source.")
        record(args, "rag", {"source": passage, "issues": issues, "model_calls": 0, "status": "blocked_before_generation"}); return
    result = ask(args, BASE_INSTRUCTIONS + " Answer the question from this passage and cite its source ID and section.",
                 {"question": "Which checks follow an overcurrent trip?", "passage": passage})
    print("LIVE ANSWER:", result.text)
    record(args, "rag", {"source": passage, "output": result.text, "metadata": result.metadata})

def mutate_report(report: dict[str, Any], name: str) -> dict[str, Any]:
    changed = copy.deepcopy(report)
    if name == "wrong_type": changed["observations"] = "Deliberately changed from a list to a string."
    elif name == "unsupported_claim": changed["diagnosis"] = "Confirmed bearing failure"
    elif name == "missing_field": changed.pop("missing_information", None)
    elif name == "extra_field": changed["confidence"] = 0.99
    else: raise LessonError(f"Unknown deliberate mutation: {name}")
    return changed

def run_validation(args: Any) -> None:
    case = teaching_validation_case()
    baseline, payload, instructions = generate_report(args, case)
    print("EXTENDED EVIDENCE WAS SUPPLIED:"); print_json(payload)
    print("ACTUAL BASELINE RESPONSE:\n" + baseline.text)
    checks = {"actual_baseline": check_report(baseline.text, case)}; variants = {}
    if checks["actual_baseline"]["valid_format"]:
        parsed = checks["actual_baseline"]["report"]
        for name in ["wrong_type", "unsupported_claim", "missing_field", "extra_field"]:
            raw = json.dumps(mutate_report(parsed, name))
            print("\nTEACHER MUTATION OF REAL RESPONSE:", name); print(raw)
            variants[name] = raw; checks[name] = check_report(raw, case)
        variants["malformed_json"] = baseline.text[:-1] + ","
        print("\nTEACHER MUTATION: malformed_json")
        checks["malformed_json"] = check_report(variants["malformed_json"], case)
    else: print("Baseline is invalid. Keep this actual failure; no prepared report was substituted.")
    record(args, "validation", {"input": payload, "instructions": instructions, "actual_model_output": baseline.text,
        "metadata": baseline.metadata, "deliberate_mutations": variants, "checks": checks})

def run_failures(args: Any) -> None:
    case = teaching_validation_case()
    baseline, payload, _ = generate_report(args, case)
    first = check_report(baseline.text, case)
    if first["valid_format"]:
        damaged = json.dumps(mutate_report(first["report"], "wrong_type"))
        origin = "Teacher deliberately damaged a real model response."
    else: damaged = baseline.text; origin = "Actual model format failure; no deliberate mutation."
    print(origin); failure = check_report(damaged, case)
    instructions = JSON_INSTRUCTIONS + " Repair the supplied format/type error once using only the supplied evidence."
    repaired = ask(args, instructions, {**payload, "invalid_output": damaged, "check_errors": failure.get("errors", [])}, json_output=True)
    print("REAL MODEL REPAIR:\n" + repaired.text); repair_check = check_report(repaired.text, case)
    if repair_check["valid_format"]:
        unsupported = json.dumps(mutate_report(repair_check["report"], "unsupported_claim"))
        print("TEACHER MUTATION: add an unsupported diagnosis to the repaired response.")
        unsupported_check = check_report(unsupported, case)
    else: unsupported_check = None
    print("Repair budget: one model attempt. Unsupported causes require evidence or human review.")
    print("Real network failures use the bounded SDK retry policy; no simulated network event is displayed.")
    record(args, "failures", {"input": payload, "actual_baseline": baseline.text, "baseline_metadata": baseline.metadata,
        "mutation_origin": origin, "damaged_output": damaged, "actual_repair": repaired.text,
        "repair_metadata": repaired.metadata, "repair_check": repair_check, "unsupported_mutation_check": unsupported_check})

def run_seminar(args: Any) -> None:
    names = [args.case] if args.case else ["complete", "missing_evidence", "contradictory", "ambiguous", "invalid_format"]
    if args.include_injection and "injection" not in names: names.append("injection")
    rows = []; records = []
    for name in names:
        case = get_case("complete" if name == "invalid_format" else name)
        result, payload, instructions = generate_report(args, case)
        displayed = result.text; origin = "actual_model_response"
        if name == "invalid_format":
            try:
                parsed = json.loads(displayed)
                if not isinstance(parsed, dict): raise ValueError("Object required")
                displayed = json.dumps(mutate_report(parsed, "wrong_type"))
                origin = "teacher_mutation_of_actual_response"
            except (ValueError, TypeError): origin = "actual_invalid_response_mutation_skipped"
        print("\nSEMINAR CASE:", name, "| ORIGIN:", origin); print(displayed)
        checks = check_report(displayed, case)
        status = "needs_format_repair" if not checks["valid_format"] else ("draft_for_review" if checks["evidence_check_passed"] else "needs_source_review")
        rows.append({"Case": name, "Valid format": checks["valid_format"], "Source checks": checks["evidence_check_passed"], "Origin": origin, "Outcome": status})
        records.append({"case": name, "input": payload, "instructions": instructions, "actual_model_output": result.text,
            "displayed_output": displayed, "origin": origin, "metadata": result.metadata, "checks": checks})
        # Save each completed case even if a later API request fails.
        save_record(args.output_dir, "seminar_case", records[-1])
    path = save_record(args.output_dir, "seminar", {"ppt_slides": DEMO_SLIDES["seminar"], "cases": records})
    with path.with_suffix(".csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print_json(rows); print("Saved actual inputs/outputs:", path); print("Saved test table:", path.with_suffix(".csv"))
    print("The deliberately damaged format row is not evidence that DeepSeek made that mistake.")

RUNNERS = {"api": run_api, "prompt": run_prompt, "sampling": run_sampling, "reasoning": run_reasoning,
    "context": run_context, "memory": run_memory, "rag": run_rag, "validation": run_validation,
    "failures": run_failures, "seminar": run_seminar}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", choices=RUNNERS, default="api")
    parser.add_argument("--case", choices=["complete","missing_evidence","contradictory","ambiguous","injection","invalid_format"])
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--instruction-file", type=Path)
    parser.add_argument("--retrieval-case", choices=["correct","wrong-equipment","outdated","irrelevant"], default="correct")
    parser.add_argument("--include-injection", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    print("LIVE DEEPSEEK MODE. Responses and decisions are generated by the API; no replay is available.")
    print("PPT pages:", DEMO_SLIDES[args.demo])
    try:
        if args.temperature is not None and not 0 <= args.temperature <= 2: raise LessonError("Use a temperature between 0 and 2.")
        if args.case == "invalid_format" and args.demo != "seminar": raise LessonError("invalid_format is a seminar mutation case.")
        RUNNERS[args.demo](args); return 0
    except (LessonError, ValueError, OSError) as exc:
        print("DEMONSTRATION STOPPED:", exc, file=sys.stderr); return 1
    except Exception as exc:
        print(f"DEMONSTRATION STOPPED: unexpected {type(exc).__name__}; no example reply was substituted.", file=sys.stderr); return 1

if __name__ == "__main__": raise SystemExit(main())
