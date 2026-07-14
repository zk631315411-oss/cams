#!/usr/bin/env python3
"""Summarize P7C 3-stage + P7D into pipeline_availability_summary.jsonl.

Reads P7C boundary_decisions (S2), construction_audit (S3), cards.raw.json,
and P7D edge_reviews + review_manifest. Produces per-candidate pipeline status.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_card_edge_map(edge_reviews: list[dict]) -> dict[str, dict[str, list[dict]]]:
    """card_id -> {edge_id -> [reviews]}."""
    card_map: dict[str, dict[str, list[dict]]] = {}
    for r in edge_reviews:
        cid = r.get("card_id", "")
        eid = r.get("edge_id", "")
        card_map.setdefault(cid, {}).setdefault(eid, []).append(r)
    return card_map


def summarize(
    p7c_run: Path,
    p7d_run: Path,
    output: Path,
) -> None:
    edge_reviews = load_jsonl(p7d_run / "p7d_edge_reviews.jsonl")
    card_edge_map = build_card_edge_map(edge_reviews)
    review_manifests = load_jsonl(p7d_run / "p7d_review_manifest.jsonl")
    card_results: dict[str, dict] = {}
    for rm in review_manifests:
        card_results[rm.get("card_id", "")] = rm

    rows: list[dict] = []
    for section_dir in sorted(p7c_run.iterdir()):
        if not section_dir.is_dir():
            continue
        section_id = section_dir.name

        # S2 boundary decisions
        bd_path = section_dir / "boundary_decisions.json"
        boundary: dict[str, dict] = {}
        if bd_path.exists():
            bd = json.loads(bd_path.read_text(encoding="utf-8"))
            for d in bd.get("boundary_decisions", []):
                boundary[d.get("candidate_id", "")] = d

        # S3 construction audit
        ca_path = section_dir / "construction_audit.json"
        construction: dict[str, dict] = {}
        if ca_path.exists():
            ca = json.loads(ca_path.read_text(encoding="utf-8"))
            for d in ca.get("construction_audit", []):
                construction[d.get("candidate_id", "")] = d

        # Cards
        cards_path = section_dir / "cards.raw.json"
        all_card_ids: set[str] = set()
        if cards_path.exists():
            cards_data = json.loads(cards_path.read_text(encoding="utf-8"))
            for card in cards_data.get("cards", []):
                all_card_ids.add(card.get("card_id", ""))

        # Build per-candidate summary
        all_cids = set(boundary.keys()) | set(construction.keys())
        for cid in sorted(all_cids):
            bd = boundary.get(cid, {})
            ca = construction.get(cid, {})
            decision = bd.get("decision", "unknown")
            const_status = ca.get("construction_status", "unknown")
            card_ids = ca.get("card_ids", [])

            # P7D status for linked cards
            p7d_accepted = 0
            p7d_pending = 0
            p7d_rejected = 0
            missing_p7c_cards: list[str] = []
            missing_p7d_cards: list[str] = []
            for card_id in card_ids:
                if card_id not in all_card_ids:
                    missing_p7c_cards.append(card_id)
                cr = card_results.get(card_id, {})
                if not cr:
                    missing_p7d_cards.append(card_id)
                edge_counts = cr.get("edge_counts") or {}
                p7d_accepted += int(edge_counts.get("accepted", 0) or 0)
                p7d_pending += int(edge_counts.get("pending", 0) or 0)
                p7d_rejected += int(edge_counts.get("rejected", 0) or 0)

            # Determine pipeline_status
            if decision == "kg_only":
                pipeline_status = "kg_only"
                blocking_reason = "S2_routed_to_kg"
            elif const_status == "ungraphable":
                pipeline_status = "ungraphable"
                blocking_reason = "S3_cannot_construct_graph"
            elif missing_p7c_cards:
                pipeline_status = "invalid_card_reference"
                blocking_reason = "S3_references_missing_P7C_cards"
            elif const_status == "unknown" or not card_ids:
                pipeline_status = "not_constructed"
                blocking_reason = "S3_not_executed_or_no_cards"
            elif missing_p7d_cards:
                pipeline_status = "not_reviewed"
                blocking_reason = "P7D_missing_linked_cards"
            elif p7d_rejected > 0:
                pipeline_status = "blocked_by_rejected"
                blocking_reason = "P7D_rejected_edges"
            elif p7d_pending > 0:
                pipeline_status = "pending_human_review"
                blocking_reason = "P7D_pending_edges_need_human_review"
            elif p7d_accepted > 0:
                pipeline_status = "ready"
                blocking_reason = None
            else:
                pipeline_status = "not_reviewed"
                blocking_reason = "P7D_not_executed"

            rows.append({
                "candidate_id": cid,
                "section_id": section_id,
                "pipeline_status": pipeline_status,
                "stages": {
                    "S1": {"status": "discovered"},
                    "S2": {
                        "status": decision,
                        "error_status": "not_observable_without_manual_audit"
                        if decision == "kg_only" else "not_applicable",
                    },
                    "S3": {
                        "status": const_status,
                        "card_ids": card_ids,
                        "missing_card_ids": missing_p7c_cards,
                    },
                    "P7D": {
                        "status": "reviewed" if (p7d_accepted + p7d_pending + p7d_rejected) > 0 else "pending",
                        "accepted": p7d_accepted,
                        "pending": p7d_pending,
                        "rejected": p7d_rejected,
                        "missing_card_ids": missing_p7d_cards,
                    },
                },
                "blocking_reason": blocking_reason,
            })

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} rows to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize P7 pipeline availability")
    parser.add_argument("--p7c-run", required=True, help="P7C output run directory")
    parser.add_argument("--p7d-run", required=True, help="P7D output run directory")
    parser.add_argument("--output", default=None, help="Output path (default: p7c-run/pipeline_availability_summary.jsonl)")
    args = parser.parse_args()

    p7c_run = Path(args.p7c_run)
    p7d_run = Path(args.p7d_run)
    output = Path(args.output) if args.output else p7c_run / "pipeline_availability_summary.jsonl"
    summarize(p7c_run, p7d_run, output)


if __name__ == "__main__":
    main()
