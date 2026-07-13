# -*- coding: utf-8 -*-
"""s0a: P5 term normalization and retrieval head construction.

This step deliberately does not run BGE/BM25, KG expansion, or LLM calls.
It creates a normalized question view and retrieval heads that later steps can
consume.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from _common import (
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


OUTPUT_DIR = S0_DIR / "output" / "s0a_p5_heads"


def load_p5_alias_groups(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    groups: list[dict[str, Any]] = []
    for group in data.get("alias_groups", []) or []:
        all_terms = [normalize_space(t) for t in group.get("all_terms", []) or [] if normalize_space(t)]
        if not all_terms:
            terms: list[str] = []
            for key in ("canonical_en", "canonical_zh"):
                if group.get(key):
                    terms.append(group[key])
            terms.extend(group.get("aliases_en", []) or [])
            terms.extend(group.get("aliases_zh", []) or [])
            all_terms = [normalize_space(t) for t in terms if normalize_space(t)]
        all_terms = sorted(set(all_terms), key=len, reverse=True)
        if not all_terms:
            continue
        groups.append(
            {
                "alias_group_id": group.get("alias_group_id", ""),
                "canonical_en": group.get("canonical_en", ""),
                "canonical_zh": group.get("canonical_zh", ""),
                "aliases_en": group.get("aliases_en", []) or [],
                "aliases_zh": group.get("aliases_zh", []) or [],
                "all_terms": all_terms,
                "alias_scope": group.get("alias_scope", ""),
                "evidence_unit_ids": group.get("evidence_unit_ids", []) or [],
                "not_kg_edge": bool(group.get("not_kg_edge", True)),
                "review_note": group.get("review_note", ""),
            }
        )
    return groups


def match_p5_terms(text: str, p5_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for group in p5_groups:
        hit_terms = [term for term in group["all_terms"] if term_in_text(term, text)]
        if not hit_terms:
            continue
        best_term = max(hit_terms, key=len)
        matches.append(
            {
                "alias_group_id": group["alias_group_id"],
                "matched_term": best_term,
                "canonical_en": group["canonical_en"],
                "canonical_zh": group["canonical_zh"],
                "alias_scope": group["alias_scope"],
                "all_terms": group["all_terms"],
                "evidence_unit_ids": group["evidence_unit_ids"],
                "not_kg_edge": group["not_kg_edge"],
                "review_note": group["review_note"],
                "use": "term_normalization_only",
            }
        )
    matches.sort(key=lambda x: (len(x.get("matched_term", "")), x.get("canonical_en", "")), reverse=True)
    return matches


def canonical_terms(matches: list[dict[str, Any]], max_aliases_per_group: int = 4) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for match in matches:
        candidates = [match.get("canonical_en", ""), match.get("canonical_zh", "")]
        candidates.extend(match.get("all_terms", [])[:max_aliases_per_group])
        for term in candidates:
            term = normalize_space(term)
            key = term.lower()
            if term and key not in seen:
                terms.append(term)
                seen.add(key)
    return terms


def build_field_record(field_id: str, text: str, p5_groups: list[dict[str, Any]]) -> dict[str, Any]:
    matches = match_p5_terms(text, p5_groups)
    return {
        "field_id": field_id,
        "text": text,
        "p5_terms": matches,
        "normalized_terms": canonical_terms(matches),
        "normalized_text": normalize_space(" ".join([text] + canonical_terms(matches))),
    }


def build_s0a_doc(question: dict[str, Any], p5_groups: list[dict[str, Any]], include_all_options: bool) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    fields["stem"] = build_field_record("stem", question.get("stem", ""), p5_groups)
    options = question.get("options", {}) or {}
    for label, text in options.items():
        fields[f"option_{label}"] = build_field_record(f"option_{label}", text, p5_groups)

    heads: list[dict[str, Any]] = [
        {
            "head_id": "stem",
            "head_kind": "stem",
            "option": None,
            "parts": ["stem"],
            "query_zh": fields["stem"]["normalized_text"],
            "p5_terms": fields["stem"]["p5_terms"],
            "note": "stem original text plus stem-level P5 normalized terms",
        }
    ]

    for label in options:
        option_field = f"option_{label}"
        combined_terms = fields["stem"]["p5_terms"] + fields[option_field]["p5_terms"]
        heads.append(
            {
                "head_id": option_field,
                "head_kind": "option",
                "option": label,
                "parts": ["stem", option_field],
                "query_zh": normalize_space(
                    f"{fields['stem']['normalized_text']} {fields[option_field]['normalized_text']}"
                ),
                "p5_terms": combined_terms,
                "note": "stem normalized text plus option normalized text; P5 terms remain metadata, not evidence",
            }
        )

    if include_all_options:
        all_parts = ["stem"] + [f"option_{label}" for label in options]
        all_terms: list[dict[str, Any]] = []
        for part in all_parts:
            all_terms.extend(fields[part]["p5_terms"])
        heads.append(
            {
                "head_id": "all_options",
                "head_kind": "all_options_fallback",
                "option": None,
                "parts": all_parts,
                "query_zh": normalize_space(" ".join(fields[part]["normalized_text"] for part in all_parts)),
                "p5_terms": all_terms,
                "note": "fallback only; should not dominate option-specific heads",
            }
        )

    return {
        "step": "s0a_p5_term_normalization_and_head_construction",
        "question_id": question.get("question_id"),
        "stem": question.get("stem", ""),
        "options": options,
        "p5_policy": {
            "role": "term_normalization_layer",
            "not_direct_evidence": True,
            "not_kg_edge": True,
            "evidence_unit_ids_use": "optional_anchor_only_in_later_steps",
        },
        "fields": fields,
        "retrieval_heads": heads,
    }


def render_md(doc: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {doc['question_id']} s0a P5术语规范化与检索头\n\n")
    lines.append("## P5定位\n\n")
    lines.append("- P5 只作为术语规范化层。\n")
    lines.append("- P5 命中的 `evidence_unit_ids` 在 s0 不进入候选池。\n")
    lines.append("- P5 不是 KG 边，也不是答案依据。\n\n")
    lines.append(f"题干：{doc.get('stem', '')}\n\n")
    lines.append("## 字段级术语规范化\n\n")
    for field_id, field in doc.get("fields", {}).items():
        lines.append(f"### {field_id}\n\n")
        lines.append(f"原文：{field.get('text', '')}\n\n")
        terms = field.get("p5_terms", [])
        if not terms:
            lines.append("P5命中：无\n\n")
        else:
            lines.append("P5命中：\n")
            for term in terms:
                lines.append(
                    f"- `{term.get('matched_term')}` -> {term.get('canonical_en')} / {term.get('canonical_zh')}"
                    f" | scope={term.get('alias_scope')} | anchors={', '.join(term.get('evidence_unit_ids', [])[:5])}\n"
                )
            lines.append("\n")
        lines.append(f"规范化追加词：{'; '.join(field.get('normalized_terms', [])) or '无'}\n\n")
        lines.append(f"规范化文本：{field.get('normalized_text', '')}\n\n")

    lines.append("## 检索头\n\n")
    for head in doc.get("retrieval_heads", []):
        lines.append(f"### {head['head_id']}\n\n")
        lines.append(f"parts: {', '.join(head.get('parts', []))}\n\n")
        lines.append(f"query_zh: {head.get('query_zh', '')}\n\n")
        if head.get("p5_terms"):
            lines.append("head P5 terms:\n")
            for term in head["p5_terms"]:
                lines.append(f"- {term.get('matched_term')} -> {term.get('canonical_en')} / {term.get('canonical_zh')}\n")
            lines.append("\n")
    return "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="s0a: P5 normalization and retrieval head construction")
    parser.add_argument("--question-id", action="append", default=[], help="question id, e.g. v7_q_000009")
    parser.add_argument("--all", action="store_true", help="process all questions")
    parser.add_argument("--limit", type=int, default=None, help="process first N questions after sorting by question_id")
    parser.add_argument("--offset", type=int, default=0, help="offset used with --limit or --all")
    parser.add_argument("--include-all-options", action="store_true", help="include all-options fallback head")
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
        doc = build_s0a_doc(question, p5_groups, include_all_options=args.include_all_options)
        qid = doc["question_id"]
        json_path = output_dir / f"{qid}.s0a.json"
        md_path = output_dir / f"{qid}.s0a.md"
        write_json(json_path, doc)
        write_text(md_path, render_md(doc))
        index_rows.append({"question_id": qid, "json": str(json_path), "markdown": str(md_path)})
        print(f"[ok] {qid} -> {json_path}")
    write_json(output_dir / "index.json", index_rows)


if __name__ == "__main__":
    main()
