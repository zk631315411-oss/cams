from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from materialize_stratified_table_units import is_non_content_table, parse_table


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DEFAULT_ROUTING = BASE_UNITS_DIR / "fullbook_dry_run" / "v7_fullbook_routing_dry_run.json"
DEFAULT_BLOCKS = BASE_UNITS_DIR / "patched" / "v7_en_blocks.patched.json"
DEFAULT_OUT_DIR = BASE_UNITS_DIR / "audit" / "ignored_routes"

RESIDUAL_SUB_BULLET_RE = re.compile(r"^\s*<\s*sub\s*>\s*o\s+", re.IGNORECASE)
PAGE_HEADER_FOOTER_RE = re.compile(
    r"certified anti-money laundering specialist|study guide|version 7\.0$",
    re.IGNORECASE,
)
TEXT_DAMAGE_RE = re.compile(r"�|鈥|濃|锟|Íatest|\bfinancia\b|\borigina\b", re.IGNORECASE)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compact(text: str, limit: int = 300) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9/]+", text))


def clean_sub_bullet(text: str) -> str:
    return RESIDUAL_SUB_BULLET_RE.sub("", text).strip()


def classify_ignored(row: dict[str, Any], block: dict[str, Any] | None) -> tuple[str, str, str]:
    route = str(row.get("route") or "")
    text = str((block or {}).get("text") or row.get("text_head") or "").strip()
    clean = clean_sub_bullet(text)
    heading = " / ".join(row.get("heading_context") or [])
    flags = set(str(flag) for flag in row.get("risk_flags", []))

    if route == "ignored_heading_context":
        return "keep_heading_context", "heading_context", "heading should remain context, not direct evidence"
    if route == "ignored_glossary":
        return "glossary_asset_candidate", "glossary", "glossary should be handled by terminology/alias assets, not base units"
    if route == "ignored_learning_objective":
        return "keep_ignore", "teaching_metadata", "learning objectives are teaching metadata"
    if route == "ignored_front_matter_noise":
        return "keep_ignore", "front_matter", "front matter credits/copyright/staff text"
    if route == "ignored_student_note_cross_reference":
        return "keep_ignore", "navigation_text", "cross-reference is navigation, not standalone evidence"
    if route == "ignored_short_context_label":
        return "move_to_review", "short_context_label", "short label may be useful context but is not safe as direct evidence"
    if route == "ignored_non_content_table":
        rows = parse_table(str((block or {}).get("raw_md") or ""))
        if block and rows and len(rows) >= 2 and len(rows[0]) >= 2 and not is_non_content_table(block):
            return "recover_as_table", "content_table", "parseable content table should enter table parser"
        return "review_table_route", "table_route_ambiguous", "ignored table needs route review"
    if route == "ignored_non_content":
        text_l = text.lower()
        if not text:
            return "keep_ignore", "blank_or_empty", "blank block"
        if (
            block
            and block.get("block_type") in {"list_item", "numbered_item"}
            and row.get("content_status") == "short_candidate"
            and word_count(clean) >= 1
        ):
            return "recover_as_list_item", "short_list_item_from_non_content", "short list item was routed non-content only because of short_candidate status"
        if "table of contents" in heading.lower() or "...." in text:
            return "keep_ignore", "table_of_contents", "table of contents text"
        if PAGE_HEADER_FOOTER_RE.search(text):
            return "keep_ignore", "page_header_footer", "page header/footer or version marker"
        return "review_ignored_non_content", "non_content_needs_sampling", "non-content route should be sampled"
    if route == "ignored_visual_text_fragment":
        if PAGE_HEADER_FOOTER_RE.search(text):
            return "keep_ignore", "page_header_footer", "page header/footer fragment"
        if TEXT_DAMAGE_RE.search(text):
            return "move_to_review", "text_damage_fragment", "short fragment contains extraction damage"
        if RESIDUAL_SUB_BULLET_RE.search(text):
            if word_count(clean) >= 2:
                if {"block_may_continue_next", "cross_block_sentence_candidate", "previous_block_may_continue_here"} & flags:
                    return "move_to_review", "short_sub_bullet_continuation_risk", "cleaned short sub-bullet has continuation risk"
                return "recover_as_list_item", "short_sub_bullet", "cleaned short sub-bullet can be materialized as list item"
            return "move_to_review", "too_short_sub_bullet", "cleaned sub-bullet is too short"
        if word_count(clean) <= 6:
            return "move_to_review", "visual_or_table_label", "short visual/table label may be useful but needs context review"
        return "move_to_review", "visual_fragment_needs_review", "visual fragment is not safe to ignore automatically"

    return "review_ignored_route", "unknown_ignored_route", f"unhandled ignored route: {route}"


def brief(row: dict[str, Any], block: dict[str, Any] | None, action: str, class_name: str, rationale: str) -> dict[str, Any]:
    text = str((block or {}).get("text") or row.get("text_head") or "")
    return {
        "block_id": row.get("block_id"),
        "route": row.get("route"),
        "recommended_action": action,
        "review_class": class_name,
        "rationale": rationale,
        "printed_page": row.get("printed_page"),
        "pdf_page": row.get("pdf_page"),
        "block_type": row.get("block_type"),
        "content_status": row.get("content_status"),
        "heading_context": row.get("heading_context", []),
        "text": compact(text, 600),
        "cleaned_text": compact(clean_sub_bullet(text), 600),
        "risk_flags": row.get("risk_flags", []),
    }


def build_report(audit: dict[str, Any]) -> str:
    lines = [
        "# v7 Ignored Route Audit",
        "",
        f"Generated at: {audit['generated_at']}",
        "",
        "## Summary",
        "",
        f"- ignored rows: {audit['ignored_rows']}",
        "",
        "## Recommended Actions",
        "",
    ]
    for name, count in audit["recommended_action_counts"].items():
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Review Classes", ""])
    for name, count in audit["review_class_counts"].items():
        lines.append(f"- {name}: {count}")
    for action, samples in audit["samples_by_action"].items():
        lines.extend(["", f"## Samples: {action}", ""])
        for sample in samples[:12]:
            lines.extend(
                [
                    f"### {sample['block_id']} · {sample['review_class']}",
                    "",
                    f"- route: {sample['route']}",
                    f"- page: {sample['printed_page']} / pdf {sample['pdf_page']}",
                    f"- heading: {' / '.join(sample.get('heading_context', []))}",
                    f"- rationale: {sample['rationale']}",
                    f"- text: {sample['text']}",
                    f"- cleaned_text: {sample['cleaned_text']}",
                    f"- risk_flags: {json.dumps(sample.get('risk_flags', []), ensure_ascii=False)}",
                    "",
                ]
            )
    return "\n".join(lines)


def audit_ignored(routing_file: Path, blocks_file: Path) -> dict[str, Any]:
    routing = read_json(routing_file)["items"]
    blocks = {block["block_id"]: block for block in read_json(blocks_file)["items"]}
    ignored = [row for row in routing if str(row.get("route") or "").startswith("ignored_")]
    decisions = []
    for row in ignored:
        block = blocks.get(row.get("block_id"))
        action, class_name, rationale = classify_ignored(row, block)
        decisions.append(brief(row, block, action, class_name, rationale))

    by_action: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in decisions:
        by_action[item["recommended_action"]].append(item)

    return {
        "schema_version": "v7_ignored_route_audit_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "routing_file": str(routing_file),
        "blocks_file": str(blocks_file),
        "ignored_rows": len(ignored),
        "recommended_action_counts": dict(Counter(item["recommended_action"] for item in decisions).most_common()),
        "review_class_counts": dict(Counter(item["review_class"] for item in decisions).most_common()),
        "decisions": decisions,
        "samples_by_action": {action: samples[:20] for action, samples in sorted(by_action.items())},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit ignored_* routing decisions before freezing v7 base units.")
    parser.add_argument("--routing-file", type=Path, default=DEFAULT_ROUTING)
    parser.add_argument("--blocks-file", type=Path, default=DEFAULT_BLOCKS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    audit = audit_ignored(args.routing_file.resolve(), args.blocks_file.resolve())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_json = args.out_dir / "ignored_route_audit.json"
    out_report = args.out_dir / "ignored_route_audit_report.md"
    write_json(out_json, audit)
    out_report.write_text(build_report(audit), encoding="utf-8")
    print(f"ignored rows: {audit['ignored_rows']}")
    print(f"actions: {json.dumps(audit['recommended_action_counts'], ensure_ascii=False)}")
    print(f"classes: {json.dumps(audit['review_class_counts'], ensure_ascii=False)}")
    print(f"wrote: {out_json}")
    print(f"wrote: {out_report}")


if __name__ == "__main__":
    main()
