from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
DEFAULT_OUTPUT_DIR = PHASE_DIR / "outputs" / "p7e_bridge_candidates"
DEFAULT_REPORT_DIR = PHASE_DIR / "reports" / "p7e_bridge_candidates"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "for", "from", "if", "in", "is",
    "it", "its", "of", "on", "or", "such", "that", "the", "their", "this", "to", "with", "within",
    "customer", "customers", "process", "risk", "risks", "review", "assessment", "assess", "screen",
    "screening", "determine", "determined", "required", "requires", "relationship", "business",
}

NATURE_DIRECTIONS: dict[tuple[str, str], str] = {
    ("risk_indicator", "assessment"): "provides_basis",
    ("risk_indicator", "execution"): "provides_basis",
    ("assessment", "execution"): "proceeds_to",
    ("control", "assessment"): "supports_control",
    ("control", "execution"): "supports_control",
    ("execution", "execution"): "proceeds_to",
    ("assessment", "assessment"): "provides_basis",
}

STRONG_TERMS = {
    "pep", "peps", "high-net-worth", "jurisdiction", "jurisdictions",
    "private", "banking", "wealth", "kyc", "cdd", "edd", "onboarding", "committee", "suitability",
    "beneficial", "owner", "owners", "ubo", "ubos", "sanctions", "adverse", "media", "screening",
    "enhanced", "diligence", "standard", "full",
}

SOURCE_NODE_PRIORITY = {"output": 30, "decision": 20, "end": 10}
TARGET_NODE_PRIORITY = {"trigger": 40, "start": 30, "action": 20, "standard": 10}
CONFIDENCE_PRIORITY = {"strong_candidate": 30, "candidate": 20, "needs_review": 10}

BLOCKING_OUTPUT_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bunsuitable\b",
        r"\bfilter(?:ed)?\s+out\b",
        r"\breject(?:ed)?\b",
        r"\bdeclin(?:e|ed)\b",
    ]
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def collect_cards(payload: Any) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for item in payload:
            cards.extend(collect_cards(item))
    elif isinstance(payload, dict):
        if isinstance(payload.get("cards"), list):
            cards.extend(collect_cards(payload["cards"]))
        elif payload.get("card_id"):
            cards.append(payload)
    return cards


def collect_card_files(card_paths: list[str], card_dirs: list[str]) -> list[Path]:
    files = [Path(path) for path in card_paths]
    for card_dir in card_dirs:
        root = Path(card_dir)
        if root.is_file():
            files.append(root)
        else:
            files.extend(sorted(root.rglob("cards.raw.json")))
    unique: list[Path] = []
    seen: set[Path] = set()
    for file in files:
        resolved = file.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(file)
    return unique


def load_cards(card_files: list[Path], allowed_card_ids: set[str] | None) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for file in card_files:
        for card in collect_cards(read_json(file)):
            if allowed_card_ids is None or card.get("card_id") in allowed_card_ids:
                cards.append(card)
    return cards


def allowed_cards_from_manifest(path: Path | None) -> set[str] | None:
    if path is None:
        return None
    allowed: set[str] = set()
    for row in read_jsonl(path):
        if (row.get("card_result") == "pass" or row.get("review_result") == "pass") and row.get("card_id"):
            allowed.add(row["card_id"])
    return allowed


def tokenize(text: str) -> set[str]:
    normalized = text.lower().replace("/", " ").replace("-", "-")
    tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", normalized)
    kept = {token for token in tokens if len(token) >= 3 and token not in STOPWORDS}
    if "high" in tokens and "net" in tokens and "worth" in tokens:
        kept.add("high-net-worth")
    return kept


def card_standard_text(card: dict[str, Any]) -> str:
    parts: list[str] = []
    for node in card.get("flow_nodes") or []:
        if node.get("node_type") in {"standard", "input"}:
            parts.extend([node.get("label"), node.get("description"), node.get("source_quote")])
    return " ".join(str(part) for part in parts if part)


def node_text(card: dict[str, Any], node: dict[str, Any]) -> str:
    parts = [
        card.get("title"),
        card.get("summary"),
        card.get("scenario"),
        card.get("trigger"),
        card.get("objective"),
        node.get("label"),
        node.get("description"),
        node.get("source_quote"),
    ]
    if card.get("card_nature") == "risk_indicator" and node.get("node_type") in {"output", "end", "decision"}:
        parts.append(card_standard_text(card))
    return " ".join(str(part) for part in parts if part)


def interfaces(card: dict[str, Any], kinds: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node in card.get("flow_nodes") or []:
        if node.get("node_type") not in kinds:
            continue
        rows.append(
            {
                "card_id": card.get("card_id"),
                "section_id": card.get("section_id"),
                "card_nature": card.get("card_nature"),
                "node_id": node.get("node_id"),
                "node_type": node.get("node_type"),
                "label": node.get("label"),
                "evidence_strength": node.get("evidence_strength"),
                "evidence_unit_ids": node.get("evidence_unit_ids") or [],
                "text": node_text(card, node),
                "terms": tokenize(node_text(card, node)),
            }
        )
    return rows


def section_number(section_id: str | None) -> tuple[int, int]:
    match = re.search(r"CH(\d+)-S(\d+)", section_id or "")
    if not match:
        return 9999, 9999
    return int(match.group(1)), int(match.group(2))


def section_relation(source_section: str | None, target_section: str | None) -> tuple[int, str | None]:
    source_ch, source_s = section_number(source_section)
    target_ch, target_s = section_number(target_section)
    if source_ch == target_ch and source_s == target_s:
        return 2, "same_section"
    if source_ch == target_ch and 0 <= target_s - source_s <= 2:
        return 1, "near_section_order"
    if 0 <= target_ch - source_ch <= 1:
        return 1, "near_chapter_order"
    return 0, None


def shared_units(source: dict[str, Any], target: dict[str, Any]) -> list[str]:
    return sorted(set(source.get("evidence_unit_ids") or []) & set(target.get("evidence_unit_ids") or []))


def is_blocking_output(source: dict[str, Any]) -> bool:
    # Blocking branch detection must look only at the interface node itself.
    # Card-level text may mention every branch and would wrongly block valid outputs.
    text = str(source.get("label") or "")
    return any(pattern.search(text) for pattern in BLOCKING_OUTPUT_PATTERNS)


def bridge_semantics(source_card: dict[str, Any], target_card: dict[str, Any]) -> str | None:
    return NATURE_DIRECTIONS.get((source_card.get("card_nature"), target_card.get("card_nature")))


def confidence(score: int, basis: list[str], source: dict[str, Any], target: dict[str, Any]) -> str:
    if source.get("evidence_strength") == "functional_dependency" or target.get("evidence_strength") == "functional_dependency":
        return "needs_review"
    if score >= 7 and "lexical_signal" in basis and "card_nature_logic" in basis and len(basis) >= 3:
        return "strong_candidate"
    if score >= 4:
        return "candidate"
    return "needs_review"


def review_result(conf: str, basis: list[str], matched_terms: list[str]) -> str:
    if basis == ["lexical_signal"]:
        return "fail"
    if "card_nature_logic" not in basis:
        return "fail"
    if not matched_terms and "shared_unit" not in basis and "section_order" not in basis:
        return "fail"
    if conf == "needs_review" and len(matched_terms) < 2:
        return "fail"
    return "pass"


def make_candidate(
    source_card: dict[str, Any],
    target_card: dict[str, Any],
    source: dict[str, Any],
    target: dict[str, Any],
    index: int,
) -> dict[str, Any] | None:
    semantics = bridge_semantics(source_card, target_card)
    if semantics == "proceeds_to" and target_card.get("card_nature") == "execution" and is_blocking_output(source):
        return None

    basis: list[str] = []
    score = 0
    if semantics:
        basis.append("card_nature_logic")
        score += 2

    matched_terms = sorted((source["terms"] & target["terms"]) & STRONG_TERMS)
    if matched_terms:
        basis.append("lexical_signal")
        score += min(4, len(matched_terms))

    shared = shared_units(source, target)
    if shared:
        basis.append("shared_unit")
        score += 3

    section_score, section_basis = section_relation(source.get("section_id"), target.get("section_id"))
    if section_basis:
        basis.append("section_order")
        score += section_score

    role_ok = source.get("node_type") in {"output", "end", "decision"} and target.get("node_type") in {"trigger", "start", "action", "standard"}
    if role_ok:
        score += 1

    score += SOURCE_NODE_PRIORITY.get(source.get("node_type"), 0) // 10
    score += TARGET_NODE_PRIORITY.get(target.get("node_type"), 0) // 10

    if score < 3 or not basis:
        return None

    conf = confidence(score, basis, source, target)
    review = review_result(conf, basis, matched_terms)
    if not semantics:
        semantics = "may_trigger"
        if review == "pass":
            review = "fail"

    bridge_id = f"p7bridge_{source_card['card_id'].replace('p7card_', '')}__{target_card['card_id'].replace('p7card_', '')}_{index:03d}"
    notes = (
        f"{source_card.get('card_nature')} card output '{source.get('label')}' may connect to "
        f"{target_card.get('card_nature')} card inlet '{target.get('label')}'. "
        f"Semantics: {semantics}. Basis: {', '.join(basis)}."
    )
    if matched_terms:
        notes += f" Matched terms: {', '.join(matched_terms)}."
    if source.get("evidence_strength") == "functional_dependency" or target.get("evidence_strength") == "functional_dependency":
        notes += " Candidate downgraded because at least one interface is functional_dependency."

    return {
        "bridge_id": bridge_id,
        "edge_type": "BRIDGES_TO",
        "source_card_id": source_card.get("card_id"),
        "target_card_id": target_card.get("card_id"),
        "source_node_id": source.get("node_id"),
        "target_node_id": target.get("node_id"),
        "bridge_semantics": semantics,
        "bridge_basis": basis,
        "matched_terms": matched_terms,
        "evidence_unit_ids": sorted(set(source.get("evidence_unit_ids") or []) | set(target.get("evidence_unit_ids") or [])),
        "source_node_strength": source.get("evidence_strength"),
        "target_node_strength": target.get("evidence_strength"),
        "condition": None,
        "confidence": conf,
        "review_status": "needs_review",
        "review_result": review,
        "score": score,
        "interface_score": SOURCE_NODE_PRIORITY.get(source.get("node_type"), 0) + TARGET_NODE_PRIORITY.get(target.get("node_type"), 0),
        "notes": notes,
    }


def candidate_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("review_result") != "pass",
        -CONFIDENCE_PRIORITY.get(row.get("confidence"), 0),
        -int(row.get("score") or 0),
        -int(row.get("interface_score") or 0),
        row.get("source_card_id") or "",
        row.get("target_card_id") or "",
        row.get("source_node_id") or "",
        row.get("target_node_id") or "",
    )


def compact_candidates(candidates: list[dict[str, Any]], max_per_pair_semantics: int = 2) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for candidate in candidates:
        key = (
            candidate.get("source_card_id") or "",
            candidate.get("target_card_id") or "",
            candidate.get("bridge_semantics") or "",
        )
        grouped.setdefault(key, []).append(candidate)

    compacted: list[dict[str, Any]] = []
    for rows in grouped.values():
        rows.sort(key=candidate_sort_key)
        pass_rows = [row for row in rows if row.get("review_result") == "pass"]
        kept = pass_rows[:max_per_pair_semantics] if pass_rows else rows[:1]
        for rank, row in enumerate(kept, 1):
            row["candidate_rank"] = rank
            row["candidate_group_size"] = len(rows)
            compacted.append(row)
    compacted.sort(key=candidate_sort_key)
    return compacted


def generate_candidates(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {card.get("card_id"): card for card in cards}
    outlets = {card["card_id"]: interfaces(card, {"output", "end", "decision"}) for card in cards}
    inlets = {card["card_id"]: interfaces(card, {"trigger", "start", "action", "standard"}) for card in cards}
    raw_candidates: list[dict[str, Any]] = []
    idx = 1
    for source_id, source_card in by_id.items():
        for target_id, target_card in by_id.items():
            if source_id == target_id:
                continue
            for source in outlets[source_id]:
                for target in inlets[target_id]:
                    candidate = make_candidate(source_card, target_card, source, target, idx)
                    if candidate:
                        raw_candidates.append(candidate)
                        idx += 1
    return compact_candidates(raw_candidates)


def write_report(path: Path, candidates: list[dict[str, Any]], card_count: int) -> None:
    confidence_counts = Counter(row["confidence"] for row in candidates)
    review_counts = Counter(row["review_result"] for row in candidates)
    semantic_counts = Counter(row["bridge_semantics"] for row in candidates)
    lines = [
        "# P7E Bridge Candidate Report",
        "",
        "P7E generates conservative bridge candidates only. It does not create confirmed bridges or modify p7_card.flow_edges.",
        "",
        "## Summary",
        "",
        f"card_count: {card_count}",
        f"candidate_count: {len(candidates)}",
        f"review_result_pass: {review_counts.get('pass', 0)}",
        f"review_result_fail: {review_counts.get('fail', 0)}",
        "",
        "## Confidence",
        "",
    ]
    for name in ["strong_candidate", "candidate", "needs_review"]:
        lines.append(f"- {name}: {confidence_counts.get(name, 0)}")
    lines.extend(["", "## Bridge Semantics", ""])
    for name, count in semantic_counts.most_common():
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Candidates", ""])
    for row in candidates[:200]:
        lines.append(
            f"- {row['review_result']} | {row['confidence']} | {row['bridge_semantics']} | "
            f"{row['source_card_id']}:{row['source_node_id']} -> {row['target_card_id']}:{row['target_node_id']}"
        )
        lines.append(f"  - basis: {', '.join(row['bridge_basis'])}")
        if row.get("matched_terms"):
            lines.append(f"  - matched_terms: {', '.join(row['matched_terms'])}")
        lines.append(f"  - notes: {row['notes']}")
    if len(candidates) > 200:
        lines.append(f"- ... truncated {len(candidates) - 200} additional candidates")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate P7E bridge candidates from reviewed P7 cards.")
    parser.add_argument("--cards", action="append", default=[], help="Path to one cards.raw.json file. Can be repeated.")
    parser.add_argument("--cards-dir", action="append", default=[], help="Directory containing cards.raw.json files. Can be repeated.")
    parser.add_argument(
        "--p7d-manifest",
        help="P7D review manifest. Only card_result=pass cards are used; legacy review_result=pass remains readable.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    args = parser.parse_args()

    card_files = collect_card_files(args.cards, args.cards_dir)
    if not card_files:
        raise SystemExit("No cards.raw.json inputs found.")
    allowed = allowed_cards_from_manifest(Path(args.p7d_manifest)) if args.p7d_manifest else None
    cards = load_cards(card_files, allowed)
    candidates = generate_candidates(cards)

    output_path = Path(args.output_dir) / "p7e_bridge_candidates.jsonl"
    report_path = Path(args.report_dir) / "p7e_bridge_candidate_report.md"
    write_jsonl(output_path, candidates)
    write_report(report_path, candidates, len(cards))
    review_counts = Counter(row["review_result"] for row in candidates)
    print(
        f"Generated {len(candidates)} candidates from {len(cards)} cards. "
        f"pass={review_counts.get('pass', 0)}, fail={review_counts.get('fail', 0)}. "
        f"Report: {report_path}"
    )


if __name__ == "__main__":
    main()
