# -*- coding: utf-8 -*-
"""s0c: canonical-inline retrieval heads.

This variant keeps the original question text but inserts strict P5 full-form
annotations next to matched abbreviation/full-form terms, for example:
FATF -> FATF（Financial Action Task Force，金融行动特别工作组）.

s0c does not retrieve units, use P5 evidence anchors, expand KG, or call an LLM.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from _common import (
    append_unique,
    load_json,
    load_questions,
    normalize_space,
    select_questions,
    write_json,
    write_text,
    P5_ALIAS_INDEX_PATH,
    QUESTIONS_PATH,
    S0_DIR,
)


OUTPUT_DIR = S0_DIR / "output" / "s0c_canonical_inline_heads"

INLINE_SCOPES = {"abbreviation_full_form"}
MANUAL_FULL_FORM_EN = {"p5c_alias_000039": "Office of Foreign Assets Control"}
STANDALONE_ZH_BLOCKLIST = {"执法机构"}


def is_abbreviation_like(text: str) -> bool:
    text = normalize_space(text)
    if not re.fullmatch(r"[A-Za-z0-9]{2,12}", text):
        return False
    return sum(1 for ch in text if ch.isupper()) >= 2


def is_standalone_zh_allowed(text: str) -> bool:
    text = normalize_space(text)
    return bool(text) and text not in STANDALONE_ZH_BLOCKLIST and len(text) >= 5


def load_p5_groups(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    groups: list[dict[str, Any]] = []
    for group in data.get("alias_groups", []) or []:
        terms: list[str] = []
        for key in ("canonical_en", "canonical_zh"):
            append_unique(terms, group.get(key, ""))
        for key in ("aliases_en", "aliases_zh", "all_terms"):
            for term in group.get(key, []) or []:
                append_unique(terms, term)
        full_form_en = select_full_form_en(group)
        append_unique(terms, full_form_en)
        if not terms:
            continue
        groups.append(
            {
                "alias_group_id": group.get("alias_group_id", ""),
                "canonical_en": group.get("canonical_en", ""),
                "canonical_zh": group.get("canonical_zh", ""),
                "full_form_en": full_form_en,
                "aliases_en": group.get("aliases_en", []) or [],
                "aliases_zh": group.get("aliases_zh", []) or [],
                "all_terms": terms,
                "alias_scope": group.get("alias_scope", ""),
                "evidence_unit_ids": group.get("evidence_unit_ids", []) or [],
                "not_kg_edge": bool(group.get("not_kg_edge", True)),
                "review_note": group.get("review_note", ""),
            }
        )
    return groups


def select_full_form_en(group: dict[str, Any]) -> str:
    manual = MANUAL_FULL_FORM_EN.get(group.get("alias_group_id", ""))
    if manual:
        return manual
    canonical_en = normalize_space(group.get("canonical_en", ""))
    if canonical_en and not is_abbreviation_like(canonical_en):
        return canonical_en
    for alias in group.get("aliases_en", []) or []:
        alias = normalize_space(alias)
        if alias and not is_abbreviation_like(alias):
            return alias
    return canonical_en


def exact_spans(term: str, text: str) -> list[tuple[int, int, str]]:
    term = normalize_space(term)
    if not term:
        return []
    if re.fullmatch(r"[a-z0-9][a-z0-9_\-/. ]*", term, flags=re.IGNORECASE):
        escaped = re.escape(term).replace(r"\ ", r"\s+")
        pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
        return [(m.start(), m.end(), m.group(0)) for m in re.finditer(pattern, text, flags=re.IGNORECASE)]
    return [(m.start(), m.end(), m.group(0)) for m in re.finditer(re.escape(term), text)]


def abbreviation_terms(group: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for term in [group.get("canonical_en", "")] + list(group.get("aliases_en", []) or []):
        if is_abbreviation_like(str(term or "")):
            append_unique(terms, str(term))
    return terms


def zh_terms_for_inline(group: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for term in [group.get("canonical_zh", "")] + list(group.get("aliases_zh", []) or []):
        if is_standalone_zh_allowed(str(term or "")):
            append_unique(terms, str(term))
    return terms


def canonical_inline_text(group: dict[str, Any], matched_text: str, abbrev: str | None = None) -> str:
    label = normalize_space(matched_text)
    components: list[str] = []
    append_unique(components, group.get("full_form_en", ""))
    if label != normalize_space(group.get("canonical_zh", "")):
        append_unique(components, group.get("canonical_zh", ""))
    if abbrev:
        append_unique(components, abbrev)
    else:
        for term in abbreviation_terms(group):
            if term.lower() != label.lower():
                append_unique(components, term)
                break
    return f"{label}（{'，'.join(components[:3])}）"


def parenthetical_abbrev_text(group: dict[str, Any], abbrev: str) -> str:
    components: list[str] = []
    append_unique(components, abbrev)
    append_unique(components, group.get("full_form_en", ""))
    append_unique(components, group.get("canonical_zh", ""))
    return f"（{'，'.join(components[:3])}）"


def make_hit(group: dict[str, Any], matched_text: str, start: int, end: int, inline_text: str) -> dict[str, Any]:
    return {
        "alias_group_id": group.get("alias_group_id", ""),
        "matched_term": matched_text,
        "span": [start, end],
        "canonical_en": group.get("full_form_en", ""),
        "canonical_zh": group.get("canonical_zh", ""),
        "alias_scope": group.get("alias_scope", ""),
        "inline_note": inline_text,
        "inline_text": inline_text,
        "evidence_unit_ids": group.get("evidence_unit_ids", []),
        "not_kg_edge": group.get("not_kg_edge", True),
        "review_note": group.get("review_note", ""),
    }


def parenthetical_zh_abbrev_hit(group: dict[str, Any], text: str) -> dict[str, Any] | None:
    for zh in zh_terms_for_inline(group):
        for abbr in abbreviation_terms(group):
            pattern = rf"{re.escape(zh)}\s*[（(]\s*{re.escape(abbr)}\s*[）)]"
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if not match:
                continue
            return make_hit(
                group=group,
                matched_text=match.group(0),
                start=match.start(),
                end=match.end(),
                inline_text=canonical_inline_text(group, zh, abbrev=abbr),
            )
    return None


def abbreviation_hit(group: dict[str, Any], text: str) -> dict[str, Any] | None:
    for abbr in abbreviation_terms(group):
        spans = exact_spans(abbr, text)
        if not spans:
            continue
        start, end, matched_text = spans[0]
        inline_text = canonical_inline_text(group, matched_text)
        if start > 0 and end < len(text) and text[start - 1] in "（(" and text[end] in "）)":
            start -= 1
            end += 1
            matched_text = text[start:end]
            inline_text = parenthetical_abbrev_text(group, abbr)
        return make_hit(
            group=group,
            matched_text=matched_text,
            start=start,
            end=end,
            inline_text=inline_text,
        )
    return None


def standalone_zh_hit(group: dict[str, Any], text: str) -> dict[str, Any] | None:
    for zh in zh_terms_for_inline(group):
        spans = exact_spans(zh, text)
        if not spans:
            continue
        start, end, matched_text = spans[0]
        return make_hit(
            group=group,
            matched_text=matched_text,
            start=start,
            end=end,
            inline_text=canonical_inline_text(group, matched_text),
        )
    return None


def choose_inline_hit(group: dict[str, Any], text: str) -> dict[str, Any] | None:
    if group.get("alias_scope") not in INLINE_SCOPES:
        return None
    return parenthetical_zh_abbrev_hit(group, text) or abbreviation_hit(group, text) or standalone_zh_hit(group, text)


def apply_inline_hits(text: str, hits: list[dict[str, Any]]) -> str:
    accepted: list[dict[str, Any]] = []
    occupied: list[tuple[int, int]] = []
    for hit in sorted(hits, key=lambda item: (item["span"][0], -(item["span"][1] - item["span"][0]))):
        start, end = hit["span"]
        if any(start < used_end and end > used_start for used_start, used_end in occupied):
            continue
        accepted.append(hit)
        occupied.append((start, end))

    out = text
    for hit in sorted(accepted, key=lambda item: item["span"][0], reverse=True):
        start, end = hit["span"]
        out = out[:start] + hit["inline_text"] + out[end:]
    return normalize_space(out)


def build_field(field_id: str, text: str, p5_groups: list[dict[str, Any]]) -> dict[str, Any]:
    hits = [hit for group in p5_groups if (hit := choose_inline_hit(group, text))]
    return {
        "field_id": field_id,
        "text": text,
        "canonical_text": apply_inline_hits(text, hits),
        "canonical_inline_hits": hits,
    }


def join_query(parts: list[str]) -> str:
    return normalize_space(" ".join(part for part in parts if normalize_space(part)))


def build_s0c_doc(question: dict[str, Any], p5_groups: list[dict[str, Any]], include_all_options: bool) -> dict[str, Any]:
    options = question.get("options", {}) or {}
    fields: dict[str, Any] = {"stem": build_field("stem", question.get("stem", ""), p5_groups)}
    for label, text in options.items():
        fields[f"option_{label}"] = build_field(f"option_{label}", text, p5_groups)

    def make_head(head_id: str, head_kind: str, option: str | None, part_ids: list[str]) -> dict[str, Any]:
        inline_hits: list[dict[str, Any]] = []
        for part in part_ids:
            inline_hits.extend(fields[part]["canonical_inline_hits"])
        return {
            "head_id": head_id,
            "head_kind": head_kind,
            "option": option,
            "parts": part_ids,
            "query_original": join_query([fields[part]["text"] for part in part_ids]),
            "query_canonical": join_query([fields[part]["canonical_text"] for part in part_ids]),
            "canonical_inline_hits": inline_hits,
            "note": "query_canonical inserts strict abbreviation/full-form annotations only; P5 hits are not evidence",
        }

    heads = [make_head("stem", "stem", None, ["stem"])]
    for label in options:
        heads.append(make_head(f"option_{label}", "option", label, ["stem", f"option_{label}"]))
    if include_all_options:
        all_parts = ["stem"] + [f"option_{label}" for label in options]
        heads.append(make_head("all_options", "all_options_fallback", None, all_parts))

    return {
        "step": "s0c_p5_canonical_inline_heads",
        "question_id": question.get("question_id"),
        "stem": question.get("stem", ""),
        "options": options,
        "p5_policy": {
            "role": "strict_abbreviation_full_form_inline_normalization",
            "inline_scopes": sorted(INLINE_SCOPES),
            "not_direct_evidence": True,
            "not_kg_edge": True,
            "compare_in_s1": ["query_original", "query_canonical"],
        },
        "fields": fields,
        "retrieval_heads": heads,
    }


def render_md(doc: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {doc['question_id']} s0c P5内嵌规范化检索头\n\n")
    lines.append("## s0c定位\n\n")
    lines.append("- 只对严格缩写-全称关系做内嵌规范化。\n")
    lines.append("- `query_original` 保留原文，`query_canonical` 保留原词并插入标准释义。\n")
    lines.append("- 不处理 SAR/STR、jurisdiction 等检索等价或宽泛上下文词。\n")
    lines.append("- P5 命中不是证据，不直接召回 evidence_unit_ids。\n\n")
    lines.append(f"题干：{doc.get('stem', '')}\n\n")

    lines.append("## 字段级 inline hits\n\n")
    for field_id, field in doc.get("fields", {}).items():
        lines.append(f"### {field_id}\n\n")
        lines.append(f"原文：{field.get('text', '')}\n\n")
        lines.append(f"canonical：{field.get('canonical_text', '')}\n\n")
        hits = field.get("canonical_inline_hits", []) or []
        if not hits:
            lines.append("inline hits：无\n\n")
            continue
        for hit in hits:
            lines.append(
                f"- `{hit.get('matched_term')}` -> {hit.get('inline_text')} "
                f"| scope={hit.get('alias_scope')} | group={hit.get('alias_group_id')}\n"
            )
        lines.append("\n")

    lines.append("## 检索头对照\n\n")
    for head in doc.get("retrieval_heads", []):
        lines.append(f"### {head['head_id']}\n\n")
        lines.append(f"parts: {', '.join(head.get('parts', []))}\n\n")
        lines.append(f"query_original: {head.get('query_original', '')}\n\n")
        lines.append(f"query_canonical: {head.get('query_canonical', '')}\n\n")
    return "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="s0c: build P5 canonical-inline retrieval heads")
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

    p5_groups = load_p5_groups(Path(args.p5_path))
    output_dir = Path(args.output_dir)
    index_rows: list[dict[str, str]] = []
    for question in selected:
        doc = build_s0c_doc(question, p5_groups, include_all_options=args.include_all_options)
        qid = doc["question_id"]
        json_path = output_dir / f"{qid}.s0c.json"
        md_path = output_dir / f"{qid}.s0c.md"
        write_json(json_path, doc)
        write_text(md_path, render_md(doc))
        index_rows.append({"question_id": qid, "json": str(json_path), "markdown": str(md_path)})
        print(f"[ok] {qid} -> {json_path}")
    write_json(output_dir / "index.json", index_rows)


if __name__ == "__main__":
    main()
