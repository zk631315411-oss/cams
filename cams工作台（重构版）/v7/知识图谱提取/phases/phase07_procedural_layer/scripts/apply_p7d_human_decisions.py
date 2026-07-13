from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def utc_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value)


def edge_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return str(row.get("section_id")), str(row.get("card_id")), str(row.get("edge_id"))


def validate_decisions(decisions: list[dict[str, Any]], known_keys: set[tuple[str, str, str]]) -> list[str]:
    errors: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for index, decision in enumerate(decisions, 1):
        key = edge_key(decision)
        if key in seen:
            errors.append(f"decision #{index} duplicates edge {key}")
        seen.add(key)
        if key not in known_keys:
            errors.append(f"decision #{index} references unknown edge {key}")
        if decision.get("decision") not in {"accepted", "rejected"}:
            errors.append(f"decision #{index} must be accepted or rejected")
        if not str(decision.get("decided_by") or "").strip():
            errors.append(f"decision #{index} missing decided_by")
        if not str(decision.get("reason") or "").strip():
            errors.append(f"decision #{index} missing reason")
    return errors


def rebuild_card_manifests(
    source_manifests: list[dict[str, Any]], edge_reviews: list[dict[str, Any]], decision_run_id: str
) -> list[dict[str, Any]]:
    edges_by_card: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in edge_reviews:
        edges_by_card[(str(row.get("section_id")), str(row.get("card_id")))].append(row)

    rebuilt: list[dict[str, Any]] = []
    for source in source_manifests:
        row = dict(source)
        card_edges = edges_by_card.get((str(row.get("section_id")), str(row.get("card_id"))), [])
        counts = Counter(edge.get("review_status") for edge in card_edges)
        row["decision_run_id"] = decision_run_id
        row["edge_counts"] = {
            "total": len(card_edges),
            "accepted": counts.get("accepted", 0),
            "pending": counts.get("pending", 0),
            "rejected": counts.get("rejected", 0),
        }
        row["answer_eligible_edge_ids"] = [edge["edge_id"] for edge in card_edges if edge.get("review_status") == "accepted"]
        row["retrieval_only_edge_ids"] = [edge["edge_id"] for edge in card_edges if edge.get("review_status") == "pending"]
        row["rejected_edge_ids"] = [edge["edge_id"] for edge in card_edges if edge.get("review_status") == "rejected"]
        row["card_result"] = (
            "pass"
            if row.get("structure_status") == "pass" and card_edges and counts.get("accepted", 0) == len(card_edges)
            else "fail"
        )
        rebuilt.append(row)
    return rebuilt


def apply_decisions(
    edge_reviews: list[dict[str, Any]],
    history: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    decision_run_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_key = {edge_key(row): row for row in edge_reviews}
    for sequence, decision in enumerate(decisions, 1):
        key = edge_key(decision)
        row = by_key[key]
        previous_status = row.get("review_status")
        resulting_status = decision["decision"]
        event = {
            "event_id": f"p7devent_{safe_id(decision_run_id)}_{safe_id(key[1])}_{safe_id(key[2])}_{sequence:03d}",
            "run_id": decision_run_id,
            "reviewed_at": decision.get("decided_at") or utc_now(),
            "actor_type": "human",
            "actor_id": decision["decided_by"],
            "section_id": key[0],
            "card_id": key[1],
            "edge_id": key[2],
            "previous_status": previous_status,
            "resulting_status": resulting_status,
            "derivation": row.get("derivation"),
            "reason": decision["reason"],
        }
        row["review_status"] = resulting_status
        row["retrieval_eligible"] = resulting_status == "accepted"
        row["answer_eligible"] = resulting_status == "accepted"
        row.setdefault("review_history", []).append(event)
        history.append(event)
    return edge_reviews, history


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply human P7D edge decisions without modifying P7C cards.")
    parser.add_argument("--edge-reviews", required=True)
    parser.add_argument("--card-manifest", required=True)
    parser.add_argument("--history", required=True)
    parser.add_argument("--decisions", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    edge_reviews = read_jsonl(Path(args.edge_reviews))
    card_manifests = read_jsonl(Path(args.card_manifest))
    history = read_jsonl(Path(args.history))
    decisions = read_jsonl(Path(args.decisions))
    errors = validate_decisions(decisions, {edge_key(row) for row in edge_reviews})
    if errors:
        raise SystemExit("Invalid human decisions:\n" + "\n".join(f"- {error}" for error in errors))

    edge_reviews, history = apply_decisions(edge_reviews, history, decisions, args.run_id)
    card_manifests = rebuild_card_manifests(card_manifests, edge_reviews, args.run_id)
    output_dir = Path(args.output_dir)
    write_jsonl(output_dir / "p7d_edge_reviews.jsonl", edge_reviews)
    write_jsonl(output_dir / "p7d_review_manifest.jsonl", card_manifests)
    write_jsonl(output_dir / "p7d_review_history.jsonl", history)
    write_jsonl(output_dir / "p7d_human_review_queue.jsonl", [row for row in edge_reviews if row.get("review_status") == "pending"])
    write_jsonl(output_dir / "p7d_rejected_edge_queue.jsonl", [row for row in edge_reviews if row.get("review_status") == "rejected"])

    counts = Counter(row.get("review_status") for row in edge_reviews)
    print(
        f"Applied {len(decisions)} human decisions. accepted={counts.get('accepted', 0)}, "
        f"pending={counts.get('pending', 0)}, rejected={counts.get('rejected', 0)}. Output: {output_dir}"
    )


if __name__ == "__main__":
    main()
