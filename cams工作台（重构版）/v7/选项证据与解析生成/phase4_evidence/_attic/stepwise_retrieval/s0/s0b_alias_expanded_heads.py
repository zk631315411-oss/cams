# -*- coding: utf-8 -*-
"""s0b: P5 alias-hint expansion for retrieval heads.

This step is a controlled variant of s0. It keeps both original and expanded
queries so s1 can compare retrieval with and without P5 alias hints.

P5 remains a term-normalization/alias layer only:
- alias hits are metadata
- evidence_unit_ids are anchors for later inspection only
- no unit is recalled in s0b
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from _common import (
    append_unique,
    load_json,
    load_questions,
    normalize_cjk_term,
    normalize_space,
    select_questions,
    term_in_text,
    write_json,
    write_text,
    P5_ALIAS_INDEX_PATH,
    QUESTIONS_PATH,
    S0_DIR,
)


OUTPUT_DIR = S0_DIR / "output" / "s0b_alias_expanded_heads"

BROAD_CANONICAL_EN = {
    "jurisdiction",
    "regulator",
    "policies and procedures",
}

SUPPRESSED_HINT_TERMS = {
    "地域": "too broad for automatic query expansion",
    "law enforcement": "broader than law enforcement agency",
}

MANUAL_EXTRA_HINTS_BY_GROUP = {
    "p5c_alias_000039": ["Office of Foreign Assets Control"],
}

AUTO_EXPAND_POLICIES = {"strong", "retrieval_equivalent"}


def append_unique_record(records: list[dict[str, Any]], record: dict[str, Any]) -> None:
    hint = normalize_space(record.get("hint", ""))
    if not hint:
        return
    existing = {normalize_space(item.get("hint", "")).lower() for item in records}
    if hint.lower() not in existing:
        records.append(record)


def load_p5_alias_groups(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    groups: list[dict[str, Any]] = []
    for group in data.get("alias_groups", []) or []:
        terms: list[str] = []
        for key in ("canonical_en", "canonical_zh"):
            append_unique(terms, group.get(key, ""))
        for key in ("aliases_en", "aliases_zh", "all_terms"):
            for term in group.get(key, []) or []:
                append_unique(terms, term)
        for term in MANUAL_EXTRA_HINTS_BY_GROUP.get(group.get("alias_group_id", ""), []):
            append_unique(terms, term)
        if not terms:
            continue
        groups.append(
            {
                "alias_group_id": group.get("alias_group_id", ""),
                "canonical_en": group.get("canonical_en", ""),
                "canonical_zh": group.get("canonical_zh", ""),
                "aliases_en": group.get("aliases_en", []) or [],
                "aliases_zh": group.get("aliases_zh", []) or [],
                "manual_extra_hints": MANUAL_EXTRA_HINTS_BY_GROUP.get(group.get("alias_group_id", ""), []),
                "all_terms": sorted(terms, key=len, reverse=True),
                "alias_scope": group.get("alias_scope", ""),
                "evidence_unit_ids": group.get("evidence_unit_ids", []) or [],
                "not_kg_edge": bool(group.get("not_kg_edge", True)),
                "review_note": group.get("review_note", ""),
            }
        )
    return groups


def group_hint_policy(match: dict[str, Any]) -> str:
    canonical_en = normalize_space(match.get("canonical_en", "")).lower()
    scope = normalize_space(match.get("alias_scope", "")).lower()
    if canonical_en in BROAD_CANONICAL_EN:
        return "broad"
    if scope.startswith("retrieval_equivalent"):
        return "retrieval_equivalent"
    if scope in {"abbreviation_full_form", "exact_alias", "spelling_variant", "translation_variant"}:
        return "strong"
    return "weak"


def classify_hint(match: dict[str, Any], hint: str) -> dict[str, Any]:
    hint = normalize_space(hint)
    policy = group_hint_policy(match)
    suppress_reason = ""
    for suppressed, reason in SUPPRESSED_HINT_TERMS.items():
        if hint.lower() == suppressed.lower():
            policy = "suppressed"
            suppress_reason = reason
            break
    return {
        "hint": hint,
        "alias_group_id": match.get("alias_group_id", ""),
        "canonical_en": match.get("canonical_en", ""),
        "canonical_zh": match.get("canonical_zh", ""),
        "matched_term": match.get("matched_term", ""),
        "alias_scope": match.get("alias_scope", ""),
        "hint_policy": policy,
        "include_in_query_expanded": policy in AUTO_EXPAND_POLICIES,
        "suppress_reason": suppress_reason,
    }


def alias_hints_for_match(match: dict[str, Any], original_text: str, max_hints: int = 6) -> list[str]:
    hints: list[str] = []
    candidates: list[str] = []
    for key in ("canonical_en", "canonical_zh"):
        candidates.append(match.get(key, ""))
    candidates.extend(match.get("aliases_en", []) or [])
    candidates.extend(match.get("aliases_zh", []) or [])
    candidates.extend(match.get("manual_extra_hints", []) or [])
    candidates.extend(match.get("all_terms", []) or [])

    matched = normalize_space(match.get("matched_term", "")).lower()
    for candidate in candidates:
        candidate = normalize_space(candidate)
        if not candidate:
            continue
        if candidate.lower() == matched:
            continue
        if term_in_text(candidate, original_text):
            continue
        append_unique(hints, candidate)
        if len(hints) >= max_hints:
            break
    return hints


def alias_hint_records_for_match(match: dict[str, Any], original_text: str) -> list[dict[str, Any]]:
    return [classify_hint(match, hint) for hint in alias_hints_for_match(match, original_text)]


def match_field(text: str, p5_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for group in p5_groups:
        hit_terms = [term for term in group["all_terms"] if term_in_text(term, text)]
        if not hit_terms:
            continue
        best_term = max(hit_terms, key=len)
        match = {
            "alias_group_id": group["alias_group_id"],
            "matched_term": best_term,
            "canonical_en": group["canonical_en"],
            "canonical_zh": group["canonical_zh"],
            "aliases_en": group["aliases_en"],
            "aliases_zh": group["aliases_zh"],
            "manual_extra_hints": group.get("manual_extra_hints", []),
            "all_terms": group["all_terms"],
            "alias_scope": group["alias_scope"],
            "evidence_unit_ids": group["evidence_unit_ids"],
            "not_kg_edge": group["not_kg_edge"],
            "review_note": group["review_note"],
            "use": "query_alias_hint_only",
        }
        match["hint_policy"] = group_hint_policy(match)
        match["query_alias_hint_records"] = alias_hint_records_for_match(match, text)
        match["query_alias_hints"] = [record["hint"] for record in match["query_alias_hint_records"]]
        match["query_expansion_hints"] = [
            record["hint"] for record in match["query_alias_hint_records"] if record["include_in_query_expanded"]
        ]
        match["query_broad_hints"] = [
            record["hint"] for record in match["query_alias_hint_records"] if record["hint_policy"] == "broad"
        ]
        match["query_suppressed_hints"] = [
            record["hint"] for record in match["query_alias_hint_records"] if record["hint_policy"] == "suppressed"
        ]
        matches.append(match)
    matches.sort(key=lambda x: (len(x.get("matched_term", "")), x.get("canonical_en", "")), reverse=True)
    return matches


def build_field(field_id: str, text: str, p5_groups: list[dict[str, Any]]) -> dict[str, Any]:
    alias_hits = match_field(text, p5_groups)
    hints: list[str] = []
    hint_records: list[dict[str, Any]] = []
    expansion_hints: list[str] = []
    broad_hints: list[str] = []
    suppressed_hints: list[str] = []
    for hit in alias_hits:
        for record in hit.get("query_alias_hint_records", []):
            append_unique_record(hint_records, record)
        for hint in hit.get("query_alias_hints", []):
            append_unique(hints, hint)
        for hint in hit.get("query_expansion_hints", []):
            append_unique(expansion_hints, hint)
        for hint in hit.get("query_broad_hints", []):
            append_unique(broad_hints, hint)
        for hint in hit.get("query_suppressed_hints", []):
            append_unique(suppressed_hints, hint)
    return {
        "field_id": field_id,
        "text": text,
        "alias_hits": alias_hits,
        "query_alias_hint_records": hint_records,
        "query_alias_hints": hints,
        "query_expansion_hints": expansion_hints,
        "query_broad_hints": broad_hints,
        "query_suppressed_hints": suppressed_hints,
    }


def join_query(parts: list[str]) -> str:
    return normalize_space(" ".join(part for part in parts if normalize_space(part)))


def build_s0b_doc(question: dict[str, Any], p5_groups: list[dict[str, Any]], include_all_options: bool) -> dict[str, Any]:
    options = question.get("options", {}) or {}
    fields: dict[str, Any] = {"stem": build_field("stem", question.get("stem", ""), p5_groups)}
    for label, text in options.items():
        fields[f"option_{label}"] = build_field(f"option_{label}", text, p5_groups)

    def make_head(head_id: str, head_kind: str, option: str | None, part_ids: list[str]) -> dict[str, Any]:
        original_parts = [fields[part]["text"] for part in part_ids]
        hint_parts: list[str] = []
        expansion_hint_parts: list[str] = []
        broad_hint_parts: list[str] = []
        suppressed_hint_parts: list[str] = []
        hint_records: list[dict[str, Any]] = []
        alias_hits: list[dict[str, Any]] = []
        for part in part_ids:
            hint_parts.extend(fields[part]["query_alias_hints"])
            expansion_hint_parts.extend(fields[part]["query_expansion_hints"])
            broad_hint_parts.extend(fields[part]["query_broad_hints"])
            suppressed_hint_parts.extend(fields[part]["query_suppressed_hints"])
            for record in fields[part]["query_alias_hint_records"]:
                append_unique_record(hint_records, record)
            alias_hits.extend(fields[part]["alias_hits"])
        hints: list[str] = []
        for hint in hint_parts:
            append_unique(hints, hint)
        expansion_hints: list[str] = []
        for hint in expansion_hint_parts:
            append_unique(expansion_hints, hint)
        broad_hints: list[str] = []
        for hint in broad_hint_parts:
            append_unique(broad_hints, hint)
        suppressed_hints: list[str] = []
        for hint in suppressed_hint_parts:
            append_unique(suppressed_hints, hint)
        return {
            "head_id": head_id,
            "head_kind": head_kind,
            "option": option,
            "parts": part_ids,
            "query_original": join_query(original_parts),
            "query_alias_hint_records": hint_records,
            "query_alias_hints": hints,
            "query_expansion_hints": expansion_hints,
            "query_broad_hints": broad_hints,
            "query_suppressed_hints": suppressed_hints,
            "query_expanded": join_query(original_parts + expansion_hints),
            "query_expanded_all_hints": join_query(original_parts + hints),
            "alias_hits": alias_hits,
            "note": "query_expanded appends only strong/retrieval-equivalent P5 hints; broad/suppressed hints are inspection metadata, not evidence",
        }

    heads = [make_head("stem", "stem", None, ["stem"])]
    for label in options:
        heads.append(make_head(f"option_{label}", "option", label, ["stem", f"option_{label}"]))
    if include_all_options:
        all_parts = ["stem"] + [f"option_{label}" for label in options]
        heads.append(make_head("all_options", "all_options_fallback", None, all_parts))

    return {
        "step": "s0b_p5_alias_expanded_heads",
        "question_id": question.get("question_id"),
        "stem": question.get("stem", ""),
        "options": options,
        "p5_policy": {
            "role": "alias_and_abbreviation_query_hints",
            "not_direct_evidence": True,
            "not_kg_edge": True,
            "auto_expand_policies": sorted(AUTO_EXPAND_POLICIES),
            "broad_hints_are_not_auto_expanded": True,
            "suppressed_hints_are_not_auto_expanded": True,
            "compare_in_s1": ["query_original", "query_expanded"],
        },
        "fields": fields,
        "retrieval_heads": heads,
    }


def render_md(doc: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {doc['question_id']} s0b P5别名扩展检索头\n\n")
    lines.append("## P5定位\n\n")
    lines.append("- P5 只提供缩写、别称、翻译变体的 query hints。\n")
    lines.append("- `query_original` 与 `query_expanded` 同时保留，供 s1 对照检索。\n")
    lines.append("- `query_expanded` 只自动追加 strong / retrieval_equivalent hints。\n")
    lines.append("- broad / suppressed hints 只保留为审计字段，不默认进入 s1 检索头。\n")
    lines.append("- P5 不直接召回 evidence_unit_ids，不作为 KG 边或答案依据。\n\n")
    lines.append(f"题干：{doc.get('stem', '')}\n\n")

    lines.append("## 字段级 alias hits\n\n")
    for field_id, field in doc.get("fields", {}).items():
        lines.append(f"### {field_id}\n\n")
        lines.append(f"原文：{field.get('text', '')}\n\n")
        if not field.get("alias_hits"):
            lines.append("alias hits：无\n\n")
        else:
            for hit in field["alias_hits"]:
                lines.append(
                    f"- 命中 `{hit.get('matched_term')}` -> {hit.get('canonical_en')} / {hit.get('canonical_zh')}"
                    f" | scope={hit.get('alias_scope')} | policy={hit.get('hint_policy')}\n"
                )
                lines.append(f"  - all hints: {', '.join(hit.get('query_alias_hints', [])) or '无'}\n")
                lines.append(f"  - auto-expanded hints: {', '.join(hit.get('query_expansion_hints', [])) or '无'}\n")
                lines.append(f"  - broad hints: {', '.join(hit.get('query_broad_hints', [])) or '无'}\n")
                lines.append(f"  - suppressed hints: {', '.join(hit.get('query_suppressed_hints', [])) or '无'}\n")
                lines.append(f"  - anchors later only: {', '.join(hit.get('evidence_unit_ids', [])[:5])}\n")
            lines.append("\n")

    lines.append("## 检索头对照\n\n")
    for head in doc.get("retrieval_heads", []):
        lines.append(f"### {head['head_id']}\n\n")
        lines.append(f"parts: {', '.join(head.get('parts', []))}\n\n")
        lines.append(f"query_original: {head.get('query_original', '')}\n\n")
        lines.append(f"query_alias_hints_all: {', '.join(head.get('query_alias_hints', [])) or '无'}\n\n")
        lines.append(f"query_expansion_hints: {', '.join(head.get('query_expansion_hints', [])) or '无'}\n\n")
        lines.append(f"query_broad_hints: {', '.join(head.get('query_broad_hints', [])) or '无'}\n\n")
        lines.append(f"query_suppressed_hints: {', '.join(head.get('query_suppressed_hints', [])) or '无'}\n\n")
        lines.append(f"query_expanded: {head.get('query_expanded', '')}\n\n")
        lines.append(f"query_expanded_all_hints: {head.get('query_expanded_all_hints', '')}\n\n")
    return "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="s0b: build original and P5 alias-expanded retrieval heads")
    parser.add_argument("--question-id", action="append", default=[])
    parser.add_argument("--all", action="store_true", help="process all questions")
    parser.add_argument("--limit", type=int, default=None, help="process first N questions after sorting by question_id")
    parser.add_argument("--offset", type=int, default=0, help="offset used with --limit or --all")
    parser.add_argument("--include-all-options", action="store_true")
    parser.add_argument("--questions-path", default=str(QUESTIONS_PATH))
    parser.add_argument("--p5-path", default=str(P5_ALIAS_INDEX_PATH))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()

    questions = load_questions(Path(args.questions_path))
    selected = select_questions(questions, args.question_id, args.all, args.limit, args.offset)
    if not selected:
        raise RuntimeError("没有选中任何题目")

    p5_groups = load_p5_alias_groups(Path(args.p5_path))
    output_dir = Path(args.output_dir)
    index_rows: list[dict[str, str]] = []
    for question in selected:
        doc = build_s0b_doc(question, p5_groups, include_all_options=args.include_all_options)
        qid = doc["question_id"]
        json_path = output_dir / f"{qid}.s0b.json"
        md_path = output_dir / f"{qid}.s0b.md"
        write_json(json_path, doc)
        write_text(md_path, render_md(doc))
        index_rows.append({"question_id": qid, "json": str(json_path), "markdown": str(md_path)})
        print(f"[ok] {qid} -> {json_path}")
    write_json(output_dir / "index.json", index_rows)


if __name__ == "__main__":
    main()
