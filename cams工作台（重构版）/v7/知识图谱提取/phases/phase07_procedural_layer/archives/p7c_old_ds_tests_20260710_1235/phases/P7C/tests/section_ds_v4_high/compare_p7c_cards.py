from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def collect_cards(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        cards: list[dict[str, Any]] = []
        for item in payload:
            cards.extend(collect_cards(item))
        return cards
    if isinstance(payload, dict):
        if isinstance(payload.get("cards"), list):
            return collect_cards(payload["cards"])
        if payload.get("card_id"):
            return [payload]
    return []


def report_error_count(path: Path | None) -> str:
    if path is None or not path.exists():
        return "n/a"
    text = path.read_text(encoding="utf-8-sig")
    match = re.search(r"error_count:\s*(\d+)", text)
    return match.group(1) if match else "n/a"


def card_summary(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "card_id": card.get("card_id", ""),
        "card_nature": card.get("card_nature", ""),
        "title": card.get("title", ""),
        "review_status": card.get("review_status", ""),
        "node_count": len(card.get("flow_nodes") or []),
        "edge_count": len(card.get("flow_edges") or []),
        "source_unit_count": len(card.get("source_unit_ids") or []),
    }


def write_comparison(
    reference_path: Path,
    candidate_path: Path,
    output_path: Path,
    reference_report: Path | None,
    candidate_report: Path | None,
) -> None:
    reference_cards = collect_cards(read_json(reference_path))
    candidate_cards = collect_cards(read_json(candidate_path))
    reference_errors = report_error_count(reference_report)
    candidate_errors = report_error_count(candidate_report)

    lines = [
        "# P7C Card Comparison",
        "",
        "## Inputs",
        "",
        f"- reference: `{reference_path}`",
        f"- candidate: `{candidate_path}`",
        "",
        "## Summary",
        "",
        "| item | reference | candidate |",
        "|---|---:|---:|",
        f"| card_count | {len(reference_cards)} | {len(candidate_cards)} |",
        f"| validation_error_count | {reference_errors} | {candidate_errors} |",
        "",
        "## Reference Cards",
        "",
        "| # | card_nature | title | nodes | edges | units | review_status |",
        "|---:|---|---|---:|---:|---:|---|",
    ]
    for idx, card in enumerate(reference_cards, 1):
        row = card_summary(card)
        lines.append(
            f"| {idx} | {row['card_nature']} | {row['title']} | {row['node_count']} | {row['edge_count']} | {row['source_unit_count']} | {row['review_status']} |"
        )

    lines.extend([
        "",
        "## Candidate Cards",
        "",
        "| # | card_nature | title | nodes | edges | units | review_status |",
        "|---:|---|---|---:|---:|---:|---|",
    ])
    for idx, card in enumerate(candidate_cards, 1):
        row = card_summary(card)
        lines.append(
            f"| {idx} | {row['card_nature']} | {row['title']} | {row['node_count']} | {row['edge_count']} | {row['source_unit_count']} | {row['review_status']} |"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare a reference P7C cards.raw.json with a candidate cards.raw.json.")
    parser.add_argument("--reference-cards", required=True)
    parser.add_argument("--candidate-cards", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--reference-report")
    parser.add_argument("--candidate-report")
    args = parser.parse_args()

    write_comparison(
        reference_path=Path(args.reference_cards),
        candidate_path=Path(args.candidate_cards),
        output_path=Path(args.output),
        reference_report=Path(args.reference_report) if args.reference_report else None,
        candidate_report=Path(args.candidate_report) if args.candidate_report else None,
    )
    print(f"comparison written: {args.output}")


if __name__ == "__main__":
    main()

