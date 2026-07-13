from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from run_p7c_batch_ds import call_model, parse_json_object
from validate_and_route_cards import (
    collect_allowed_unit_ids,
    collect_card_files,
    load_section_package,
    read_cards_file,
    read_json,
    validate_card_structure,
    write_jsonl,
)


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
P7D_DIR = PHASE_DIR / "phases" / "P7D"
DEFAULT_PACKAGES_DIR = PHASE_DIR / "phases" / "P7B" / "section_packages"
DEFAULT_SCHEMA_PATH = PHASE_DIR / "inputs" / "procedural_schema_v2.json"
DEFAULT_REVIEW_SCHEMA_PATH = P7D_DIR / "inputs" / "p7d_edge_review_schema_v1.json"
DEFAULT_PROMPT_PATH = P7D_DIR / "prompts" / "edge_evidence_review_v1.md"
DEFAULT_OUTPUT_DIR = P7D_DIR / "outputs"

CHECK_NAMES = (
    "source_node_support",
    "target_node_support",
    "direction_support",
    "condition_support",
    "qualifier_support",
    "parallel_or_correlation_check",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value)


def declared_derivation(edge: dict[str, Any]) -> str:
    if edge.get("derivation") == "explicit_text":
        return "explicit_text"
    if edge.get("derivation") == "llm_inference":
        return "llm_inference"
    strength = edge.get("evidence_strength")
    if strength == "explicit":
        return "explicit_text"
    if strength in {"functional_dependency", "needs_review"}:
        return "llm_inference"
    if strength == "rejected":
        return "unsupported"
    return "llm_inference"


def build_llm_card_snapshot(card: dict[str, Any]) -> dict[str, Any]:
    """Expose business graph claims while withholding extraction-time review hints."""
    card_snapshot = {
        key: card[key]
        for key in ("card_id", "section_id", "title", "card_nature", "source_unit_ids")
        if key in card
    }
    node_fields = (
        "node_id",
        "node_category",
        "node_type",
        "label",
        "actor",
        "description",
        "modality",
        "evidence_unit_ids",
    )
    edge_fields = (
        "edge_id",
        "edge_type",
        "source",
        "target",
        "relation_type",
        "condition",
        "qualifier",
        "modality",
        "evidence_unit_ids",
    )
    card_snapshot["flow_nodes"] = [
        {key: node[key] for key in node_fields if key in node}
        for node in card.get("flow_nodes") or []
        if isinstance(node, dict)
    ]
    card_snapshot["flow_edges"] = [
        {key: edge[key] for key in edge_fields if key in edge}
        for edge in card.get("flow_edges") or []
        if isinstance(edge, dict)
    ]
    return card_snapshot


def build_prompt(template: str, card: dict[str, Any], package: dict[str, Any]) -> str:
    replacements = {
        "<section_id>": str(package.get("section_id") or card.get("section_id") or ""),
        "<section_title>": str(package.get("section_title") or ""),
        "<SECTION_TEXT>": str(package.get("section_text_with_unit_anchors") or ""),
        "<SECTION_UNITS>": "",
        "<ALLOWED_UNIT_IDS>": json.dumps(sorted(collect_allowed_unit_ids(package)), ensure_ascii=False, indent=2),
        "<P7C_CARD>": json.dumps(build_llm_card_snapshot(card), ensure_ascii=False, indent=2),
    }
    prompt = template
    for marker, value in replacements.items():
        prompt = prompt.replace(marker, value)
    return prompt


def validate_llm_review_payload(
    payload: dict[str, Any] | None,
    card: dict[str, Any],
    allowed_unit_ids: set[str],
    review_schema: dict[str, Any],
) -> list[str]:
    if not isinstance(payload, dict):
        return ["response is not a JSON object"]
    errors: list[str] = []
    if payload.get("section_id") != card.get("section_id"):
        errors.append("section_id does not match input card")
    if payload.get("card_id") != card.get("card_id"):
        errors.append("card_id does not match input card")

    source_edges = card.get("flow_edges") or []
    expected_edge_ids = [edge.get("edge_id") for edge in source_edges if isinstance(edge, dict)]
    reviews = payload.get("edge_reviews")
    if not isinstance(reviews, list):
        return errors + ["edge_reviews must be a list"]
    actual_edge_ids = [row.get("edge_id") for row in reviews if isinstance(row, dict)]
    if actual_edge_ids != expected_edge_ids:
        errors.append(f"edge_reviews must match input edge order and IDs: expected={expected_edge_ids}, actual={actual_edge_ids}")
    if len(actual_edge_ids) != len(set(actual_edge_ids)):
        errors.append("edge_reviews contains duplicate edge_id values")

    derivations = set(review_schema.get("derivations", []))
    recommendations = set(review_schema.get("llm_recommendations", []))
    check_statuses = set(review_schema.get("check_statuses", []))
    for index, row in enumerate(reviews, 1):
        owner = f"edge_reviews[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{owner} is not an object")
            continue
        if row.get("derivation") not in derivations:
            errors.append(f"{owner} invalid derivation {row.get('derivation')}")
        if row.get("llm_recommendation") not in recommendations:
            errors.append(f"{owner} invalid llm_recommendation {row.get('llm_recommendation')}")
        checks = row.get("checks")
        if not isinstance(checks, dict):
            errors.append(f"{owner}.checks must be an object")
        else:
            for check_name in CHECK_NAMES:
                check = checks.get(check_name)
                if not isinstance(check, dict):
                    errors.append(f"{owner}.checks.{check_name} must be an object")
                    continue
                if check.get("status") not in check_statuses:
                    errors.append(f"{owner}.checks.{check_name} invalid status {check.get('status')}")
                if not str(check.get("reason") or "").strip():
                    errors.append(f"{owner}.checks.{check_name} missing reason")
        evidence_ids = row.get("evidence_unit_ids")
        if not isinstance(evidence_ids, list):
            errors.append(f"{owner}.evidence_unit_ids must be a list")
        else:
            for unit_id in evidence_ids:
                if unit_id not in allowed_unit_ids:
                    errors.append(f"{owner} uses out-of-section evidence {unit_id}")
        if not isinstance(row.get("source_quotes"), list):
            errors.append(f"{owner}.source_quotes must be a list")
        if not str(row.get("reason") or "").strip():
            errors.append(f"{owner} missing reason")
    return errors


def determine_review_status(edge: dict[str, Any], llm_review: dict[str, Any]) -> str:
    declared = declared_derivation(edge)
    reviewed = llm_review.get("derivation")
    recommendation = llm_review.get("llm_recommendation")
    check_statuses = {
        check.get("status")
        for check in (llm_review.get("checks") or {}).values()
        if isinstance(check, dict)
    }
    if reviewed == "unsupported" or recommendation == "rejected" or "unsupported" in check_statuses:
        return "rejected"
    if (
        declared == "llm_inference"
        or reviewed == "llm_inference"
        or recommendation == "pending"
        or "pending" in check_statuses
    ):
        return "pending"
    if reviewed == "explicit_text" and recommendation == "accepted":
        return "accepted"
    return "pending"


def pending_checks(reason: str) -> dict[str, dict[str, str]]:
    return {name: {"status": "pending", "reason": reason} for name in CHECK_NAMES}


def build_edge_review(
    *,
    run_id: str,
    card: dict[str, Any],
    edge: dict[str, Any],
    llm_review: dict[str, Any],
    actor_type: str,
    actor_id: str,
    reviewed_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    status = determine_review_status(edge, llm_review)
    card_id = str(card.get("card_id"))
    edge_id = str(edge.get("edge_id"))
    review_id = f"p7dreview_{safe_id(run_id)}_{safe_id(card_id)}_{safe_id(edge_id)}"
    event_id = f"p7devent_{safe_id(run_id)}_{safe_id(card_id)}_{safe_id(edge_id)}_001"
    event = {
        "event_id": event_id,
        "run_id": run_id,
        "reviewed_at": reviewed_at,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "section_id": card.get("section_id"),
        "card_id": card_id,
        "edge_id": edge_id,
        "previous_status": None,
        "resulting_status": status,
        "derivation": llm_review.get("derivation"),
        "reason": llm_review.get("reason"),
    }
    review = {
        "review_id": review_id,
        "run_id": run_id,
        "section_id": card.get("section_id"),
        "card_id": card_id,
        "edge_id": edge_id,
        "edge_type": edge.get("edge_type"),
        "source": edge.get("source"),
        "target": edge.get("target"),
        "declared_derivation": declared_derivation(edge),
        "derivation": llm_review.get("derivation"),
        "review_status": status,
        "llm_recommendation": llm_review.get("llm_recommendation"),
        "checks": llm_review.get("checks"),
        "evidence_unit_ids": llm_review.get("evidence_unit_ids") or [],
        "source_quotes": llm_review.get("source_quotes") or [],
        "reason": llm_review.get("reason"),
        "retrieval_eligible": status in {"accepted", "pending"},
        "answer_eligible": status == "accepted",
        "source_edge_snapshot": edge,
        "review_history": [event],
    }
    return review, event


def fallback_edge_reviews(
    run_id: str,
    card: dict[str, Any],
    reason: str,
    actor_type: str,
    actor_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    reviewed_at = utc_now()
    reviews: list[dict[str, Any]] = []
    history: list[dict[str, Any]] = []
    for edge in card.get("flow_edges") or []:
        llm_review = {
            "derivation": "llm_inference",
            "llm_recommendation": "pending",
            "checks": pending_checks(reason),
            "evidence_unit_ids": [],
            "source_quotes": [],
            "reason": reason,
        }
        review, event = build_edge_review(
            run_id=run_id,
            card=card,
            edge=edge,
            llm_review=llm_review,
            actor_type=actor_type,
            actor_id=actor_id,
            reviewed_at=reviewed_at,
        )
        reviews.append(review)
        history.append(event)
    return reviews, history


def build_card_manifest(
    run_id: str,
    card: dict[str, Any],
    package: dict[str, Any] | None,
    structure: dict[str, Any],
    edge_reviews: list[dict[str, Any]],
    review_execution_status: str,
) -> dict[str, Any]:
    counts = Counter(row["review_status"] for row in edge_reviews)
    all_accepted = bool(edge_reviews) and counts.get("accepted", 0) == len(edge_reviews)
    card_result = "pass" if structure.get("structure_status") == "pass" and all_accepted else "fail"
    return {
        "run_id": run_id,
        "section_id": card.get("section_id"),
        "card_id": card.get("card_id"),
        "title": card.get("title"),
        "source_cards_path": card.get("__source_path"),
        "section_package_path": (package or {}).get("__package_path"),
        "structure_status": structure.get("structure_status"),
        "structure_errors": structure.get("structure_errors") or [],
        "derived_graph_shape": structure.get("derived_graph_shape"),
        "has_entry_process_exit_path": structure.get("has_entry_process_exit_path", False),
        "has_terminal_process": structure.get("has_terminal_process", False),
        "review_execution_status": review_execution_status,
        "card_result": card_result,
        "edge_counts": {
            "total": len(edge_reviews),
            "accepted": counts.get("accepted", 0),
            "pending": counts.get("pending", 0),
            "rejected": counts.get("rejected", 0),
        },
        "answer_eligible_edge_ids": [row["edge_id"] for row in edge_reviews if row["review_status"] == "accepted"],
        "retrieval_only_edge_ids": [row["edge_id"] for row in edge_reviews if row["review_status"] == "pending"],
        "rejected_edge_ids": [row["edge_id"] for row in edge_reviews if row["review_status"] == "rejected"],
    }


def review_card(
    *,
    run_id: str,
    card: dict[str, Any],
    package: dict[str, Any] | None,
    structure: dict[str, Any],
    prompt_template: str,
    review_schema: dict[str, Any],
    model: str,
    thinking_effort: str,
    max_tokens: int,
    timeout: float,
    retries: int,
    retry_delay: float,
    artifact_dir: Path,
    call_model_fn: Callable[[str, str, int, float, str], tuple[str, dict[str, Any]]] = call_model,
) -> dict[str, Any]:
    if structure.get("structure_status") != "pass" or package is None:
        reason = "P7D结构校验未通过，未执行语义审核。"
        reviews, history = fallback_edge_reviews(run_id, card, reason, "rule_validator", "p7d_structure_v2")
        return {
            "edge_reviews": reviews,
            "history": history,
            "card_manifest": build_card_manifest(run_id, card, package, structure, reviews, "skipped_structure_failure"),
            "call_record": {"card_id": card.get("card_id"), "status": "skipped_structure_failure", "attempts": []},
        }

    prompt = build_prompt(prompt_template, card, package)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "prompt.md").write_text(prompt, encoding="utf-8")
    attempts: list[dict[str, Any]] = []
    accepted_payload: dict[str, Any] | None = None
    actor_id = model

    for attempt in range(1, retries + 2):
        try:
            raw, meta = call_model_fn(prompt, model, max_tokens, timeout, thinking_effort)
            (artifact_dir / f"raw_response.attempt_{attempt}.txt").write_text(raw, encoding="utf-8")
            parsed = parse_json_object(raw)
            contract_errors = validate_llm_review_payload(parsed, card, collect_allowed_unit_ids(package), review_schema)
            attempts.append({"attempt": attempt, "status": "accepted" if not contract_errors else "contract_failed", "contract_errors": contract_errors, "call_meta": meta})
            if not contract_errors and parsed is not None:
                accepted_payload = parsed
                write_json(artifact_dir / "review_response.json", parsed)
                break
        except Exception as exc:  # noqa: BLE001 - every failed LLM call becomes an auditable pending review.
            attempts.append({"attempt": attempt, "status": "api_failed", "error": str(exc)})
        if attempt <= retries:
            time.sleep(retry_delay)

    if accepted_payload is None:
        reason = "独立LLM审核失败或输出合同不完整，边保持pending。"
        reviews, history = fallback_edge_reviews(run_id, card, reason, "system", "p7d_review_runner")
        execution_status = "review_failed"
    else:
        reviewed_at = utc_now()
        edge_review_by_id = {row["edge_id"]: row for row in accepted_payload["edge_reviews"]}
        reviews = []
        history = []
        for edge in card.get("flow_edges") or []:
            review, event = build_edge_review(
                run_id=run_id,
                card=card,
                edge=edge,
                llm_review=edge_review_by_id[edge["edge_id"]],
                actor_type="llm",
                actor_id=actor_id,
                reviewed_at=reviewed_at,
            )
            reviews.append(review)
            history.append(event)
        execution_status = "reviewed"

    return {
        "edge_reviews": reviews,
        "history": history,
        "card_manifest": build_card_manifest(run_id, card, package, structure, reviews, execution_status),
        "call_record": {"card_id": card.get("card_id"), "status": execution_status, "attempts": attempts, "prompt_sha256": sha256_text(prompt)},
    }


def write_report(path: Path, card_rows: list[dict[str, Any]], edge_rows: list[dict[str, Any]]) -> None:
    card_counts = Counter(row["card_result"] for row in card_rows)
    edge_counts = Counter(row["review_status"] for row in edge_rows)
    lines = [
        "# P7D Edge Evidence Review Report",
        "",
        f"card_count: {len(card_rows)}",
        f"card_pass: {card_counts.get('pass', 0)}",
        f"card_fail: {card_counts.get('fail', 0)}",
        f"edge_count: {len(edge_rows)}",
        f"edge_accepted: {edge_counts.get('accepted', 0)}",
        f"edge_pending: {edge_counts.get('pending', 0)}",
        f"edge_rejected: {edge_counts.get('rejected', 0)}",
        "",
        "Only accepted edges are answer eligible. Pending edges are retrieval-only.",
    ]
    non_pass = [row for row in card_rows if row["card_result"] != "pass"]
    if non_pass:
        lines.extend(["", "## Non-passing Cards", ""])
        for row in non_pass:
            counts = row["edge_counts"]
            lines.append(
                f"- {row['section_id']} | {row['card_id']} | structure={row['structure_status']} | "
                f"accepted={counts['accepted']} pending={counts['pending']} rejected={counts['rejected']}"
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run independent P7D edge-level evidence review.")
    parser.add_argument("--cards", action="append", default=[])
    parser.add_argument("--input-dir", action="append", default=[])
    parser.add_argument("--packages-dir", default=str(DEFAULT_PACKAGES_DIR))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA_PATH))
    parser.add_argument("--review-schema", default=str(DEFAULT_REVIEW_SCHEMA_PATH))
    parser.add_argument("--prompt", default=str(DEFAULT_PROMPT_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--thinking-effort", choices=["none", "low", "medium", "high"], default="none")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-delay", type=float, default=5.0)
    args = parser.parse_args()

    started_at = utc_now()
    input_files = collect_card_files(args.cards, args.input_dir)
    if not input_files:
        raise SystemExit("No cards.raw.json inputs found. Use --cards or --input-dir.")
    cards: list[dict[str, Any]] = []
    for path in input_files:
        loaded, errors = read_cards_file(path)
        if errors:
            raise SystemExit(f"Cannot review malformed cards file {path}: {errors}")
        cards.extend(loaded)

    schema = read_json(Path(args.schema))
    review_schema = read_json(Path(args.review_schema))
    prompt_template = Path(args.prompt).read_text(encoding="utf-8")
    packages_dir = Path(args.packages_dir)
    card_id_counts = Counter(card.get("card_id") for card in cards if card.get("card_id"))
    run_dir = Path(args.output_dir) / args.run_id
    artifact_root = run_dir / "artifacts"

    work_items: list[tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any], Path]] = []
    structure_rows: list[dict[str, Any]] = []
    for card in cards:
        package = load_section_package(packages_dir, card.get("section_id"))
        structure = validate_card_structure(
            card,
            package,
            schema,
            duplicate_card_id=card_id_counts.get(card.get("card_id"), 0) > 1,
        )
        structure_rows.append(structure)
        artifact_dir = artifact_root / safe_id(str(card.get("section_id"))) / safe_id(str(card.get("card_id")))
        work_items.append((card, package, structure, artifact_dir))

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        futures = [
            executor.submit(
                review_card,
                run_id=args.run_id,
                card=card,
                package=package,
                structure=structure,
                prompt_template=prompt_template,
                review_schema=review_schema,
                model=args.model,
                thinking_effort=args.thinking_effort,
                max_tokens=args.max_tokens,
                timeout=args.timeout,
                retries=args.retries,
                retry_delay=args.retry_delay,
                artifact_dir=artifact_dir,
            )
            for card, package, structure, artifact_dir in work_items
        ]
        for future in as_completed(futures):
            results.append(future.result())

    card_rows = sorted((result["card_manifest"] for result in results), key=lambda row: (str(row.get("section_id")), str(row.get("card_id"))))
    edge_rows = sorted((row for result in results for row in result["edge_reviews"]), key=lambda row: (str(row.get("section_id")), str(row.get("card_id")), str(row.get("edge_id"))))
    history_rows = sorted((row for result in results for row in result["history"]), key=lambda row: (str(row.get("section_id")), str(row.get("card_id")), str(row.get("edge_id"))))
    call_records = sorted((result["call_record"] for result in results), key=lambda row: str(row.get("card_id")))

    write_jsonl(run_dir / "p7d_structure_manifest.jsonl", structure_rows)
    write_jsonl(run_dir / "p7d_edge_reviews.jsonl", edge_rows)
    write_jsonl(run_dir / "p7d_review_manifest.jsonl", card_rows)
    write_jsonl(run_dir / "p7d_review_history.jsonl", history_rows)
    write_jsonl(run_dir / "p7d_human_review_queue.jsonl", [row for row in edge_rows if row["review_status"] == "pending"])
    write_jsonl(run_dir / "p7d_rejected_edge_queue.jsonl", [row for row in edge_rows if row["review_status"] == "rejected"])
    write_report(run_dir / "p7d_edge_review_report.md", card_rows, edge_rows)
    write_json(
        run_dir / "p7d_run_manifest.json",
        {
            "run_id": args.run_id,
            "started_at": started_at,
            "finished_at": utc_now(),
            "model": args.model,
            "thinking_effort": args.thinking_effort,
            "prompt_path": Path(args.prompt).resolve().as_posix(),
            "prompt_sha256": sha256_text(prompt_template),
            "review_schema_path": Path(args.review_schema).resolve().as_posix(),
            "source_cards_paths": [path.resolve().as_posix() for path in input_files],
            "card_count": len(card_rows),
            "edge_count": len(edge_rows),
            "call_records": call_records,
        },
    )

    card_counts = Counter(row["card_result"] for row in card_rows)
    edge_counts = Counter(row["review_status"] for row in edge_rows)
    print(
        f"P7D edge review complete: cards={len(card_rows)} (pass={card_counts.get('pass', 0)}, fail={card_counts.get('fail', 0)}), "
        f"edges={len(edge_rows)} (accepted={edge_counts.get('accepted', 0)}, pending={edge_counts.get('pending', 0)}, rejected={edge_counts.get('rejected', 0)}). "
        f"Output: {run_dir}"
    )


if __name__ == "__main__":
    main()
