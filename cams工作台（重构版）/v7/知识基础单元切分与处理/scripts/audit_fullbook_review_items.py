from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DEFAULT_INPUT = BASE_UNITS_DIR / "draft" / "v2_fullbook" / "v7_units_draft.v2_fullbook_all.combined.json"
DEFAULT_OUT_DIR = BASE_UNITS_DIR / "audit" / "v2_fullbook_review"

RESIDUAL_SUB_BULLET_RE = re.compile(r"^\s*<\s*sub\s*>\s*o\s+", re.IGNORECASE)
ANGLE_PLACEHOLDER_RE = re.compile(r"<([^<>]{1,80})>")
TEXT_DAMAGE_PATTERNS = {
    "duplicated_phrase_accommodate": re.compile(r"\bof varying to accommodate\b", re.IGNORECASE),
    "broken_financia": re.compile(r"\bfinancia account\b", re.IGNORECASE),
    "missing_space_timeconsuming": re.compile(r"\btimeconsuming\b", re.IGNORECASE),
    "missing_space_enduser": re.compile(r"\benduser\b", re.IGNORECASE),
    "damaged_publication_reference": re.compile(r"\bIn its\s*,", re.IGNORECASE),
}

HTML_TAG_NAMES = {
    "a",
    "body",
    "br",
    "div",
    "em",
    "font",
    "html",
    "img",
    "li",
    "ol",
    "p",
    "span",
    "strong",
    "sub",
    "sup",
    "table",
    "td",
    "th",
    "tr",
    "ul",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def is_plain_angle_placeholder(inner: str) -> bool:
    value = inner.strip()
    if not value or value.startswith("/") or "=" in value:
        return False
    if value.lower() in HTML_TAG_NAMES:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 /_.-]{0,78}", value))


def contains_allowed_placeholder(text: str) -> bool:
    return any(is_plain_angle_placeholder(match.group(1)) for match in ANGLE_PLACEHOLDER_RE.finditer(text))


def classify_review_item(unit: dict[str, Any]) -> str:
    quote = str(unit.get("en_quote") or "")
    flags = set(str(flag) for flag in unit.get("risk_flags", []))
    if RESIDUAL_SUB_BULLET_RE.search(quote):
        if "source_text_lacks_terminal_punctuation" in flags or "source_sentence_may_continue_next_block" in flags:
            return "residual_sub_bullet_needs_sentence_review"
        return "residual_sub_bullet_cleanable"
    if contains_allowed_placeholder(quote) and "source_text_contains_artifact" in flags:
        return "allowed_angle_placeholder_false_artifact"
    if "llm_group_too_broad_needs_review" in flags:
        return "too_broad_but_coherent_candidate"
    if "incomplete_sentence" in flags or "fragment" in flags:
        return "true_fragment_or_incomplete"
    if "source_sentence_may_continue_next_block" in flags or "source_sentence_may_continue_from_previous_block" in flags:
        return "cross_block_continuation_review"
    if "source_text_contains_artifact" in flags:
        return "source_artifact_other"
    return "other_review"


def text_damage_hits(unit: dict[str, Any]) -> list[str]:
    quote = str(unit.get("en_quote") or "")
    return [name for name, pattern in TEXT_DAMAGE_PATTERNS.items() if pattern.search(quote)]


def unit_brief(unit: dict[str, Any]) -> dict[str, Any]:
    return {
        "unit_id": unit.get("unit_id"),
        "chapter": unit.get("chapter"),
        "unit_type": unit.get("unit_type"),
        "evidence_status": unit.get("evidence_status"),
        "printed_page": unit.get("printed_page"),
        "knowledge_en": unit.get("knowledge_en"),
        "en_quote": unit.get("en_quote"),
        "risk_flags": unit.get("risk_flags", []),
        "source": unit.get("source", {}),
    }


def build_report(payload: dict[str, Any], audit: dict[str, Any]) -> str:
    lines = [
        "# v7 Fullbook Review Audit",
        "",
        f"Generated at: {audit['generated_at']}",
        f"Input: `{audit['input']}`",
        "",
        "## Summary",
        "",
        f"- direct items: {audit['direct_items']}",
        f"- review items: {audit['review_items']}",
        f"- parent/context items: {audit['parent_items']}",
        "",
        "## Review Classes",
        "",
    ]
    for name, count in audit["review_class_counts"].items():
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Direct Text Damage Candidates", ""])
    for name, count in audit["direct_text_damage_counts"].items():
        lines.append(f"- {name}: {count}")
    lines.append("")
    for name, samples in audit["review_class_samples"].items():
        lines.extend([f"## Samples: {name}", ""])
        for sample in samples[:8]:
            lines.extend(
                [
                    f"### {sample.get('unit_id')} · {sample.get('unit_type')}",
                    "",
                    f"- chapter: {sample.get('chapter')}",
                    f"- page: {sample.get('printed_page')}",
                    f"- knowledge_en: {sample.get('knowledge_en')}",
                    f"- en_quote: {sample.get('en_quote')}",
                    f"- risk_flags: {json.dumps(sample.get('risk_flags', []), ensure_ascii=False)}",
                    "",
                ]
            )
    if audit["direct_text_damage_samples"]:
        lines.extend(["## Samples: direct text damage", ""])
        for sample in audit["direct_text_damage_samples"][:12]:
            lines.extend(
                [
                    f"### {sample.get('unit_id')} · {', '.join(sample.get('text_damage_hits', []))}",
                    "",
                    f"- chapter: {sample.get('chapter')}",
                    f"- page: {sample.get('printed_page')}",
                    f"- knowledge_en: {sample.get('knowledge_en')}",
                    f"- en_quote: {sample.get('en_quote')}",
                    "",
                ]
            )
    return "\n".join(lines)


def audit_file(input_file: Path) -> dict[str, Any]:
    payload = read_json(input_file)
    review_items = payload.get("review_items", [])
    direct_items = payload.get("items", [])
    parent_items = payload.get("parent_items", [])

    review_classes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in review_items:
        review_classes[classify_review_item(unit)].append(unit)

    direct_damage: list[dict[str, Any]] = []
    direct_damage_counts: Counter[str] = Counter()
    for unit in direct_items:
        hits = text_damage_hits(unit)
        if hits:
            sample = unit_brief(unit)
            sample["text_damage_hits"] = hits
            direct_damage.append(sample)
            direct_damage_counts.update(hits)

    return {
        "schema_version": "v7_fullbook_review_audit_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input": str(input_file),
        "direct_items": len(direct_items),
        "review_items": len(review_items),
        "parent_items": len(parent_items),
        "review_class_counts": dict(Counter({name: len(items) for name, items in review_classes.items()}).most_common()),
        "review_class_samples": {
            name: [unit_brief(unit) for unit in units[:12]]
            for name, units in sorted(review_classes.items(), key=lambda item: (-len(item[1]), item[0]))
        },
        "direct_text_damage_counts": dict(direct_damage_counts.most_common()),
        "direct_text_damage_samples": direct_damage[:24],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify v7 fullbook draft review items before freeze.")
    parser.add_argument("--input-file", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_file = args.input_file.resolve()
    audit = audit_file(input_file)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_json = args.out_dir / "review_audit.json"
    out_report = args.out_dir / "review_audit_report.md"
    write_json(out_json, audit)
    out_report.write_text(build_report(read_json(input_file), audit), encoding="utf-8")
    print(f"review items: {audit['review_items']}")
    print(f"review classes: {json.dumps(audit['review_class_counts'], ensure_ascii=False)}")
    print(f"direct text damage: {json.dumps(audit['direct_text_damage_counts'], ensure_ascii=False)}")
    print(f"wrote: {out_json}")
    print(f"wrote: {out_report}")


if __name__ == "__main__":
    main()
