#!/usr/bin/env python3
"""Run an auditable S2 A/B test over frozen, merged S1 candidates."""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))
from scripts.run_p7c_batch_ds import (  # type: ignore[import-not-found]
    build_s2_prompt,
    call_model,
    parse_json_object,
    read_json,
    validate_s2_boundary_payload,
)


PHASE_DIR = SCRIPT_DIR.parent
PACKAGES_DIR = PHASE_DIR / "phases" / "P7B" / "section_packages"
S2_V1_PROMPT = PHASE_DIR / "phases" / "P7C" / "prompts" / "kg_boundary_adjudication_v1.md"
S2_V2_PROMPT = PHASE_DIR / "phases" / "P7C" / "prompts" / "kg_boundary_adjudication_v2.md"
DEFAULT_EXPECTED = (
    PHASE_DIR / "phases" / "P7C" / "tests" / "s2_kg_projection_v1" / "expected_decisions.json"
)
ALLOWED_DECISIONS = {"p7c_candidate", "kg_only"}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare_output_dir(path: Path) -> None:
    if path.exists():
        if not path.is_dir():
            raise ValueError(f"A/B output path is not a directory: {path}")
        if any(path.iterdir()):
            raise ValueError(f"A/B output directory must be empty: {path}")
    else:
        path.mkdir(parents=True)


def canonical_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def parse_sections(value: str | None) -> set[str] | None:
    if not value:
        return None
    sections = {item.strip() for item in value.split(",") if item.strip()}
    return sections or None


def load_expectations(path: Path) -> tuple[dict[str, dict[str, Any]], int]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise ValueError("expected decisions must use schema_version=1")
    sections = raw.get("sections")
    if not isinstance(sections, dict) or not sections:
        raise ValueError("expected decisions requires a non-empty sections object")
    required_holdout = raw.get("required_holdout_sections", 0)
    if not isinstance(required_holdout, int) or required_holdout < 0:
        raise ValueError("required_holdout_sections must be a non-negative integer")
    return sections, required_holdout


def load_s1_propositions(
    s1_runs: list[str],
    wanted_sections: set[str],
) -> dict[str, list[dict[str, Any]]]:
    """Load one canonical merged S1 artifact per section; conflicts are fatal."""
    result: dict[str, list[dict[str, Any]]] = {}
    sources: dict[str, Path] = {}
    for run_dir in s1_runs:
        run_path = Path(run_dir)
        if not run_path.is_dir():
            raise ValueError(f"S1 run directory does not exist: {run_path}")
        for section_id in sorted(wanted_sections):
            s1_file = run_path / section_id / "s1_propositions.json"
            if not s1_file.exists():
                continue
            data = json.loads(s1_file.read_text(encoding="utf-8"))
            if data.get("section_id") != section_id:
                raise ValueError(f"{s1_file} has mismatched section_id")
            propositions = data.get("propositions")
            if not isinstance(propositions, list):
                raise ValueError(f"{s1_file} requires a propositions list")
            candidate_ids = [
                row.get("candidate_id") if isinstance(row, dict) else None
                for row in propositions
            ]
            if any(not candidate_id for candidate_id in candidate_ids):
                raise ValueError(f"{s1_file} contains a candidate without candidate_id")
            if len(candidate_ids) != len(set(candidate_ids)):
                raise ValueError(f"{s1_file} contains duplicate candidate IDs")
            if section_id in result:
                if canonical_json(result[section_id]) != canonical_json(propositions):
                    raise ValueError(
                        f"conflicting frozen S1 artifacts for {section_id}: "
                        f"{sources[section_id]} vs {s1_file}"
                    )
                continue
            result[section_id] = propositions
            sources[section_id] = s1_file
    return result


def validate_preflight(
    cases: dict[str, dict[str, Any]],
    s1_data: dict[str, list[dict[str, Any]]],
) -> list[str]:
    errors: list[str] = []
    if set(cases) != set(s1_data):
        missing_s1 = set(cases) - set(s1_data)
        extra_s1 = set(s1_data) - set(cases)
        if missing_s1:
            errors.append(f"missing frozen S1 sections: {sorted(missing_s1)}")
        if extra_s1:
            errors.append(f"unexpected frozen S1 sections: {sorted(extra_s1)}")

    observed_labels: set[str] = set()
    for section_id, case in cases.items():
        if not isinstance(case, dict):
            errors.append(f"{section_id} expectation must be an object")
            continue
        if case.get("split") not in {"development", "holdout"}:
            errors.append(f"{section_id} split must be development or holdout")
        decisions = case.get("decisions")
        if not isinstance(decisions, dict) or not decisions:
            errors.append(f"{section_id} requires non-empty decisions")
            continue
        invalid_labels = set(decisions.values()) - ALLOWED_DECISIONS
        if invalid_labels:
            errors.append(f"{section_id} has invalid expected decisions: {sorted(invalid_labels)}")
        observed_labels.update(decisions.values())
        propositions = s1_data.get(section_id)
        if propositions is None:
            continue
        candidate_ids = {str(row.get("candidate_id") or "") for row in propositions}
        expected_ids = set(decisions)
        if candidate_ids != expected_ids:
            errors.append(
                f"{section_id} expected IDs do not match frozen S1: "
                f"missing={sorted(candidate_ids - expected_ids)}, "
                f"extra={sorted(expected_ids - candidate_ids)}"
            )
    if observed_labels != ALLOWED_DECISIONS:
        errors.append("expectations must contain at least one p7c_candidate and one kg_only")
    return errors


def validate_arm_payload(
    payload: dict[str, Any],
    propositions: list[dict[str, Any]],
    section_id: str,
) -> list[str]:
    errors: list[str] = []
    if payload.get("section_id") != section_id:
        errors.append("S2 section_id mismatch")
    errors.extend(validate_s2_boundary_payload(payload, propositions))
    expected_ids = {str(row.get("candidate_id") or "") for row in propositions}
    decisions = payload.get("boundary_decisions")
    if isinstance(decisions, list):
        actual_ids = {
            str(row.get("candidate_id") or "")
            for row in decisions
            if isinstance(row, dict)
        }
        extra_ids = actual_ids - expected_ids
        if extra_ids:
            errors.append(f"S2 boundary_decisions contains unknown candidate IDs: {sorted(extra_ids)}")
    return errors


def run_s2_arm(
    *,
    arm_dir: Path,
    task: dict[str, Any],
    propositions: list[dict[str, Any]],
    prompt_template: str,
    kg_input_version: str,
    model: str,
    thinking_effort: str,
    max_tokens: int,
    timeout: float,
    retries: int,
) -> dict[str, Any]:
    section_id = str(task.get("section_id") or "")
    arm_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_s2_prompt(
        prompt_template,
        task,
        propositions,
        kg_input_version=kg_input_version,
    )
    (arm_dir / "prompt.md").write_text(prompt, encoding="utf-8")

    attempts: list[dict[str, Any]] = []
    accepted_payload: dict[str, Any] | None = None
    for attempt in range(1, retries + 1):
        attempt_record: dict[str, Any] = {"attempt": attempt, "status": "pending"}
        raw = ""
        try:
            raw, call_meta = call_model(prompt, model, max_tokens, timeout, thinking_effort)
            attempt_record["call_meta"] = call_meta
        except Exception as exc:
            attempt_record["status"] = "api_error"
            attempt_record["error"] = repr(exc)
            attempts.append(attempt_record)
            write_json(arm_dir / f"attempt_{attempt:02d}.json", attempt_record)
            continue

        (arm_dir / f"attempt_{attempt:02d}.raw.txt").write_text(raw, encoding="utf-8")
        parsed = parse_json_object(raw)
        if not isinstance(parsed, dict):
            attempt_record["status"] = "parse_error"
            attempts.append(attempt_record)
            write_json(arm_dir / f"attempt_{attempt:02d}.json", attempt_record)
            continue

        write_json(arm_dir / f"attempt_{attempt:02d}.parsed.json", parsed)
        validation_errors = validate_arm_payload(parsed, propositions, section_id)
        attempt_record["validation_errors"] = validation_errors
        if validation_errors:
            attempt_record["status"] = "contract_error"
            attempts.append(attempt_record)
            write_json(arm_dir / f"attempt_{attempt:02d}.json", attempt_record)
            continue

        attempt_record["status"] = "ok"
        attempts.append(attempt_record)
        write_json(arm_dir / f"attempt_{attempt:02d}.json", attempt_record)
        accepted_payload = parsed
        break

    result = {
        "section_id": section_id,
        "kg_input_version": kg_input_version,
        "status": "ok" if accepted_payload is not None else "failed",
        "attempts": attempts,
        "boundary_decisions": (
            accepted_payload.get("boundary_decisions", []) if accepted_payload else []
        ),
    }
    write_json(arm_dir / "run_result.json", result)
    if accepted_payload is not None:
        write_json(arm_dir / "boundary_decisions.json", accepted_payload)
    return result


def score_arm(
    result: dict[str, Any],
    expected: dict[str, str],
) -> dict[str, Any]:
    if result.get("status") != "ok":
        return {
            "status": "failed",
            "correct": 0,
            "wrong_kg_only": 0,
            "wrong_p7c_candidate": 0,
            "missing_decisions": sorted(expected),
            "actual": {},
        }
    actual = {
        str(row.get("candidate_id") or ""): row.get("decision")
        for row in result.get("boundary_decisions") or []
        if isinstance(row, dict)
    }
    wrong_kg = [
        candidate_id
        for candidate_id, expected_decision in expected.items()
        if expected_decision == "p7c_candidate" and actual.get(candidate_id) == "kg_only"
    ]
    wrong_p7c = [
        candidate_id
        for candidate_id, expected_decision in expected.items()
        if expected_decision == "kg_only" and actual.get(candidate_id) == "p7c_candidate"
    ]
    missing = sorted(set(expected) - set(actual))
    correct = sum(actual.get(candidate_id) == decision for candidate_id, decision in expected.items())
    return {
        "status": "contract_error" if missing else "ok",
        "correct": correct,
        "wrong_kg_only": len(wrong_kg),
        "wrong_p7c_candidate": len(wrong_p7c),
        "wrong_kg_only_ids": wrong_kg,
        "wrong_p7c_candidate_ids": wrong_p7c,
        "missing_decisions": missing,
        "actual": actual,
    }


def run_section_pair(
    *,
    output_dir: Path,
    section_id: str,
    propositions: list[dict[str, Any]],
    expected_case: dict[str, Any],
    v1_prompt: str,
    v2_prompt: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    task = read_json(PACKAGES_DIR / section_id / "task.json")
    section_dir = output_dir / section_id
    a_result = run_s2_arm(
        arm_dir=section_dir / "A_summary_v1",
        task=task,
        propositions=propositions,
        prompt_template=v1_prompt,
        kg_input_version="summary_v1",
        model=args.model,
        thinking_effort=args.thinking_effort,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
        retries=args.retries,
    )
    b_result = run_s2_arm(
        arm_dir=section_dir / "B_projection_v1",
        task=task,
        propositions=propositions,
        prompt_template=v2_prompt,
        kg_input_version="projection_v1",
        model=args.model,
        thinking_effort=args.thinking_effort,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
        retries=args.retries,
    )
    expected = expected_case["decisions"]
    a_score = score_arm(a_result, expected)
    b_score = score_arm(b_result, expected)
    regressions = [
        candidate_id
        for candidate_id, expected_decision in expected.items()
        if a_score["actual"].get(candidate_id) == expected_decision
        and b_score["actual"].get(candidate_id) != expected_decision
    ]
    comparison = {
        "section_id": section_id,
        "split": expected_case["split"],
        "expected": expected,
        "A_summary_v1": a_score,
        "B_projection_v1": b_score,
        "regressions": regressions,
    }
    write_json(section_dir / "comparison.json", comparison)
    return comparison


def evaluate(
    comparisons: list[dict[str, Any]],
    required_holdout_sections: int,
) -> dict[str, Any]:
    arm_failures = [
        f"{row['section_id']}:{arm}"
        for row in comparisons
        for arm in ("A_summary_v1", "B_projection_v1")
        if row[arm]["status"] != "ok"
    ]
    wrong_kg = sum(row["B_projection_v1"]["wrong_kg_only"] for row in comparisons)
    wrong_p7c = sum(row["B_projection_v1"]["wrong_p7c_candidate"] for row in comparisons)
    regressions = [
        f"{row['section_id']}:{candidate_id}"
        for row in comparisons
        for candidate_id in row["regressions"]
    ]
    holdout_sections = sorted(
        row["section_id"] for row in comparisons if row.get("split") == "holdout"
    )

    if arm_failures:
        verdict = "inconclusive"
        summary = "At least one A/B arm failed API, parsing, or contract validation."
    elif wrong_kg or wrong_p7c or regressions:
        verdict = "reject"
        summary = "The projection variant violated a semantic accuracy or regression gate."
    elif len(holdout_sections) < required_holdout_sections:
        verdict = "inconclusive"
        summary = "Development gates passed, but the required holdout sample is incomplete."
    else:
        verdict = "accept"
        summary = "The projection variant passed semantic, regression, and holdout gates."

    return {
        "verdict": verdict,
        "summary": summary,
        "primary_results": {
            "wrong_kg_only": wrong_kg,
            "wrong_p7c_candidate": wrong_p7c,
            "regressions": regressions,
            "arm_failures": arm_failures,
        },
        "holdout_result": {
            "required_sections": required_holdout_sections,
            "observed_sections": holdout_sections,
            "passed": len(holdout_sections) >= required_holdout_sections,
        },
        "promotion_requires_human_approval": True,
        "next_action": (
            "Add frozen holdout cases before promotion."
            if verdict == "inconclusive" and not arm_failures
            else None
        ),
    }


def write_markdown_summary(
    path: Path,
    comparisons: list[dict[str, Any]],
    evaluation: dict[str, Any],
) -> None:
    lines = [
        "# S2 KG Boundary A/B",
        "",
        f"verdict: `{evaluation['verdict']}`",
        "",
        "| section | split | A correct | A wrong KG | A wrong P7C | B correct | B wrong KG | B wrong P7C | regressions |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in sorted(comparisons, key=lambda item: item["section_id"]):
        a = row["A_summary_v1"]
        b = row["B_projection_v1"]
        lines.append(
            f"| {row['section_id']} | {row['split']} | {a['correct']} | "
            f"{a['wrong_kg_only']} | {a['wrong_p7c_candidate']} | {b['correct']} | "
            f"{b['wrong_kg_only']} | {b['wrong_p7c_candidate']} | "
            f"{', '.join(row['regressions'])} |"
        )
    lines.extend(["", evaluation["summary"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Auditable A/B test for S2 KG boundary adjudication")
    parser.add_argument("--s1-runs", nargs="+", required=True)
    parser.add_argument("--expected", default=str(DEFAULT_EXPECTED))
    parser.add_argument("--sections", default=None, help="Optional comma-separated subset")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--thinking-effort", default="none", choices=["none", "low", "medium", "high"])
    parser.add_argument("--max-tokens", type=int, default=20000)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    prepare_output_dir(output_dir)
    try:
        cases, required_holdout = load_expectations(Path(args.expected))
        selected = parse_sections(args.sections)
        if selected is not None:
            unknown = selected - set(cases)
            if unknown:
                raise ValueError(f"selected sections are absent from expectations: {sorted(unknown)}")
            cases = {section_id: cases[section_id] for section_id in cases if section_id in selected}
        wanted_sections = set(cases)
        s1_data = load_s1_propositions(args.s1_runs, wanted_sections)
        preflight_errors = validate_preflight(cases, s1_data)
    except Exception as exc:
        preflight_errors = [repr(exc)]
        cases = {}
        s1_data = {}
        required_holdout = 0

    run_plan = {
        "planned_at": datetime.now().isoformat(timespec="seconds"),
        "s1_runs": args.s1_runs,
        "expected": str(Path(args.expected)),
        "sections": sorted(cases),
        "model": args.model,
        "thinking_effort": args.thinking_effort,
        "max_tokens": args.max_tokens,
        "timeout": args.timeout,
        "retries": args.retries,
        "concurrency": args.concurrency,
        "required_holdout_sections": required_holdout,
        "A": {"prompt": str(S2_V1_PROMPT), "kg_input_version": "summary_v1"},
        "B": {"prompt": str(S2_V2_PROMPT), "kg_input_version": "projection_v1"},
    }
    write_json(output_dir / "run_plan.json", run_plan)
    if preflight_errors:
        evaluation = {
            "verdict": "inconclusive",
            "summary": "Preflight contract failed.",
            "issues": preflight_errors,
            "promotion_requires_human_approval": True,
        }
        write_json(output_dir / "evaluation.json", evaluation)
        for error in preflight_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)

    v1_prompt = S2_V1_PROMPT.read_text(encoding="utf-8-sig")
    v2_prompt = S2_V2_PROMPT.read_text(encoding="utf-8-sig")
    comparisons: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        futures = {
            executor.submit(
                run_section_pair,
                output_dir=output_dir,
                section_id=section_id,
                propositions=s1_data[section_id],
                expected_case=case,
                v1_prompt=v1_prompt,
                v2_prompt=v2_prompt,
                args=args,
            ): section_id
            for section_id, case in cases.items()
        }
        for future in as_completed(futures):
            section_id = futures[future]
            try:
                comparison = future.result()
            except Exception as exc:
                comparison = {
                    "section_id": section_id,
                    "split": cases[section_id]["split"],
                    "expected": cases[section_id]["decisions"],
                    "A_summary_v1": {"status": "failed", "correct": 0, "wrong_kg_only": 0, "wrong_p7c_candidate": 0, "actual": {}},
                    "B_projection_v1": {"status": "failed", "correct": 0, "wrong_kg_only": 0, "wrong_p7c_candidate": 0, "actual": {}},
                    "regressions": [],
                    "runner_error": repr(exc),
                }
                write_json(output_dir / section_id / "comparison.json", comparison)
            comparisons.append(comparison)

    comparisons.sort(key=lambda item: item["section_id"])
    evaluation = evaluate(comparisons, required_holdout)
    write_json(output_dir / "comparison.json", comparisons)
    write_json(output_dir / "evaluation.json", evaluation)
    write_markdown_summary(output_dir / "run_summary.md", comparisons, evaluation)
    print(f"S2 A/B verdict: {evaluation['verdict']}")
    print(f"Artifacts: {output_dir}")
    if evaluation["verdict"] != "accept":
        raise SystemExit(1 if evaluation["verdict"] == "reject" else 2)


if __name__ == "__main__":
    main()
