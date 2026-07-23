from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def classify_error(text: str) -> str:
    if "429" in text:
        return "429"
    if "empty content" in text or "empty_output" in text:
        return "empty"
    if "JSON" in text or "parse" in text:
        return "parse"
    return "other"


def question_stage_errors(result: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for field, stage in (("planner_error", "planner"), ("adjudicator_error", "adjudicator")):
        value = str(result.get(field, "") or "").strip()
        if value:
            errors.append({"stage": stage, "kind": classify_error(value), "detail": value[:300]})

    raw_outputs = result.get("pipeline", {}).get("judge_answer", {}).get("raw_adjudicator_outputs", [])
    if isinstance(raw_outputs, list):
        for item in raw_outputs:
            if not isinstance(item, dict):
                continue
            if item.get("parsed_ok") is False and not result.get("adjudicator_error"):
                raw = str(item.get("raw", "") or "").strip()
                kind = "parse" if raw else "empty"
                errors.append({"stage": "adjudicator", "kind": kind, "detail": f"round={item.get('round', '')}"})

    review = result.get("pipeline", {}).get("review_answer", {})
    if isinstance(review, dict) and review.get("review_status") == "error":
        value = str(review.get("review_error", "") or "").strip()
        errors.append({"stage": "reviewer", "kind": classify_error(value), "detail": value[:300]})

    disagreement_review = result.get("pipeline", {}).get("answer_disagreement_llm_review", {})
    if isinstance(disagreement_review, dict) and disagreement_review.get("review_status") == "error":
        value = str(disagreement_review.get("error", "") or "").strip()
        errors.append({"stage": "disagreement_reviewer", "kind": classify_error(value), "detail": value[:300]})

    return errors


def build_report(output_dir: Path) -> dict[str, Any]:
    summary_path = output_dir / "summary.json"
    summary = read_json(summary_path) if summary_path.exists() else {}
    outputs = summary.get("outputs", []) if isinstance(summary.get("outputs", []), list) else []

    question_dir = output_dir / "questions"
    question_paths = sorted(question_dir.glob("q_*.json")) if question_dir.exists() else []
    questions = [read_json(path) for path in question_paths]

    stage_error_counts: dict[str, int] = {}
    stage_error_questions: set[str] = set()
    stage_error_examples: list[dict[str, str]] = []
    for result in questions:
        qid = str(result.get("question_id", ""))
        for error in question_stage_errors(result):
            key = f"{error['stage']}:{error['kind']}"
            stage_error_counts[key] = stage_error_counts.get(key, 0) + 1
            stage_error_questions.add(qid)
            if len(stage_error_examples) < 12:
                stage_error_examples.append({"question_id": qid, **error})

    done_outputs = [item for item in outputs if item.get("status") == "done"]
    passed_outputs = [item for item in done_outputs if item.get("validation_status") == "passed"]
    empty_answer_outputs = [item for item in done_outputs if not item.get("ai_answer")]
    matched_outputs = [
        item
        for item in done_outputs
        if sorted(item.get("ai_answer") or []) == sorted(item.get("key_answer") or [])
    ]

    rows = load_jsonl(output_dir / "question_option_card_bindings.jsonl")
    evidence_by_question: dict[str, set[str]] = {}
    for result in questions:
        qid = str(result.get("question_id", ""))
        evidence_by_question[qid] = {
            item.get("card_id")
            for item in result.get("pipeline", {}).get("retrieve_evidence", {}).get("evidence", [])
            if item.get("card_id")
        }
    outside_candidate = []
    for row in rows:
        candidates = set(row.get("candidate_card_ids") or [])
        global_evidence = evidence_by_question.get(str(row.get("question_id", "")), set())
        for cid in row.get("evidence_card_ids") or []:
            if cid not in candidates and cid not in global_evidence:
                outside_candidate.append(
                    {
                        "question_id": row.get("question_id", ""),
                        "option": row.get("option", ""),
                        "card_id": cid,
                    }
                )

    retry_outputs = [item for item in done_outputs if item.get("stage_retries_used")]
    recovered = [item for item in retry_outputs if item.get("stage_retry_recovered") is True]
    unrecovered = [item for item in retry_outputs if item.get("stage_retry_recovered") is False]
    blind_repair_outputs = [item for item in done_outputs if item.get("blind_repair_rounds_used")]

    total_done = len(done_outputs)
    effective_model_plan = summary.get("effective_model_plan") or summary.get("llm_stage_models", {})
    return {
        "output_dir": str(output_dir),
        "model": summary.get("model", ""),
        "model_field_note": summary.get(
            "model_field_note",
            "legacy compatibility field; use effective_model_plan/llm_stage_models for actual per-stage calls",
        ),
        "effective_model_plan": effective_model_plan,
        "llm_stage_models": summary.get("llm_stage_models", {}),
        "blind_repair": summary.get("blind_repair", {}),
        "concurrency": summary.get("concurrency"),
        "stage_retries": summary.get("stage_retries"),
        "stage_retry_concurrency": summary.get("stage_retry_concurrency"),
        "started_at": summary.get("started_at", ""),
        "finished_at": summary.get("finished_at", ""),
        "selected": summary.get("selected", 0),
        "done": total_done,
        "question_files": len(question_paths),
        "binding_rows": len(rows),
        "passed": len(passed_outputs),
        "needs_review": total_done - len(passed_outputs),
        "answer_match": len(matched_outputs),
        "empty_answers": len(empty_answer_outputs),
        "stage_error_questions": len(stage_error_questions),
        "stage_error_counts": stage_error_counts,
        "stage_error_examples": stage_error_examples,
        "retry_questions": len(retry_outputs),
        "retry_recovered": len(recovered),
        "retry_unrecovered": len(unrecovered),
        "blind_repair_questions": len(blind_repair_outputs),
        "blind_repair_examples": [
            {
                "question_id": item.get("question_id", ""),
                "rounds_used": item.get("blind_repair_rounds_used", 0),
                "trigger_reasons": item.get("blind_repair_trigger_reasons", []),
            }
            for item in blind_repair_outputs[:12]
        ],
        "evidence_rows": sum(1 for row in rows if row.get("evidence_card_ids")),
        "outside_candidate_evidence": len(outside_candidate),
        "outside_candidate_examples": outside_candidate[:12],
        "rates": {
            "passed": round(len(passed_outputs) / total_done, 4) if total_done else 0.0,
            "answer_match": round(len(matched_outputs) / total_done, 4) if total_done else 0.0,
            "empty_answers": round(len(empty_answer_outputs) / total_done, 4) if total_done else 0.0,
            "stage_error_questions": round(len(stage_error_questions) / total_done, 4) if total_done else 0.0,
        },
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Formal Quality Report",
        "",
        f"- output_dir: `{report['output_dir']}`",
        f"- effective_model_plan: `{json.dumps(report.get('effective_model_plan', {}), ensure_ascii=False)}`",
        f"- model: `{report.get('model', '')}` ({report.get('model_field_note', '')})",
        f"- llm_stage_models: `{json.dumps(report.get('llm_stage_models', {}), ensure_ascii=False)}`",
        f"- done: {report['done']} / selected {report.get('selected', 0)}",
        f"- passed: {report['passed']} ({report['rates']['passed']:.1%})",
        f"- answer_match: {report['answer_match']} ({report['rates']['answer_match']:.1%})",
        f"- empty_answers: {report['empty_answers']} ({report['rates']['empty_answers']:.1%})",
        f"- stage_error_questions: {report['stage_error_questions']} ({report['rates']['stage_error_questions']:.1%})",
        f"- blind_repair_questions: {report.get('blind_repair_questions', 0)}",
        f"- binding_rows: {report['binding_rows']}",
        f"- evidence_rows: {report['evidence_rows']}",
        f"- outside_candidate_evidence: {report['outside_candidate_evidence']}",
        "",
        "## Stage Errors",
        "",
    ]
    if report["stage_error_counts"]:
        for key, value in sorted(report["stage_error_counts"].items()):
            lines.append(f"- `{key}`: {value}")
    else:
        lines.append("- none")
    lines.extend(["", "## Error Examples", ""])
    if report["stage_error_examples"]:
        for item in report["stage_error_examples"]:
            lines.append(
                f"- {item['question_id']} `{item['stage']}:{item['kind']}` {item.get('detail', '')}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Blind Repair", ""])
    if report.get("blind_repair_examples"):
        for item in report["blind_repair_examples"]:
            lines.append(
                f"- {item['question_id']} rounds={item.get('rounds_used', 0)} reasons={','.join(item.get('trigger_reasons', []))}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Outside Candidate Evidence", ""])
    if report["outside_candidate_examples"]:
        for item in report["outside_candidate_examples"]:
            lines.append(f"- {item['question_id']} option {item['option']} card {item['card_id']}")
    else:
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize formal binding output quality.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    report = build_report(args.output_dir)
    if args.write_report:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "formal_quality_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        write_markdown(report, args.output_dir / "formal_quality_report.md")
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
