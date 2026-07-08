from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from audit_fullbook_review_items import classify_review_item, text_damage_hits


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DEFAULT_INPUT = BASE_UNITS_DIR / "draft" / "v2_fullbook" / "v7_units_draft.v2_fullbook_all.prefreeze_qa.json"
DEFAULT_BLOCKS = BASE_UNITS_DIR / "patched" / "v7_en_blocks.patched.json"
DEFAULT_OUT_DIR = BASE_UNITS_DIR / "audit" / "review_resolution_plan"


STRUCTURAL_PARENT_RE = re.compile(
    r"\b(the following|as follows|include the following|includes the following|some key pros and cons are as follows)\b",
    re.IGNORECASE,
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compact(text: str, limit: int = 420) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def block_num(block_id: str | None) -> int | None:
    match = re.search(r"b(\d+)", str(block_id or ""))
    return int(match.group(1)) if match else None


def build_block_index(blocks: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    by_id = {str(block.get("block_id")): block for block in blocks if block.get("block_id")}
    idx_by_id = {str(block.get("block_id")): idx for idx, block in enumerate(blocks) if block.get("block_id")}
    return by_id, idx_by_id


def neighbor_context(blocks: list[dict[str, Any]], idx_by_id: dict[str, int], block_id: str | None) -> dict[str, Any]:
    if not block_id or block_id not in idx_by_id:
        return {}
    idx = idx_by_id[block_id]
    out: dict[str, Any] = {}
    for label, nidx in [("prev", idx - 1), ("current", idx), ("next", idx + 1)]:
        if 0 <= nidx < len(blocks):
            block = blocks[nidx]
            out[label] = {
                "block_id": block.get("block_id"),
                "block_type": block.get("block_type"),
                "content_status": block.get("content_status"),
                "printed_page": block.get("printed_page"),
                "heading_stack": block.get("heading_stack", []),
                "text": compact(block.get("text")),
                "risk_flags": block.get("risk_flags", []),
                "repair_flags": block.get("repair_flags", []),
            }
    return out


def source_block_id(unit: dict[str, Any]) -> str | None:
    source = unit.get("source") or {}
    block_id = source.get("en_block_id")
    if block_id:
        return str(block_id)
    sentence_ids = unit.get("en_sentence_ids") or []
    if sentence_ids:
        match = re.match(r"(v7en_b\d+)", str(sentence_ids[0]))
        if match:
            return match.group(1)
    return None


def ignored_review_class(unit: dict[str, Any]) -> str | None:
    source = unit.get("source") or {}
    if source.get("ignored_review_class"):
        return str(source["ignored_review_class"])
    for flag in unit.get("risk_flags", []):
        if str(flag).startswith("ignored_review_class:"):
            return str(flag).split(":", 1)[1]
    return None


def looks_structural_parent(unit: dict[str, Any]) -> bool:
    quote = str(unit.get("en_quote") or "").strip()
    if not quote:
        return False
    if quote.endswith(":"):
        return True
    return bool(STRUCTURAL_PARENT_RE.search(quote))


def classify_resolution(unit: dict[str, Any], block: dict[str, Any] | None) -> tuple[str, str, str]:
    source = unit.get("source") or {}
    method = source.get("materialization_method")
    flags = set(str(flag) for flag in unit.get("risk_flags", []))
    quote = str(unit.get("en_quote") or "")
    review_class = classify_review_item(unit)

    if method == "prefreeze_qa_ignored_route_recovery_v1":
        ignored_class = ignored_review_class(unit) or "unknown_ignored_review"
        if ignored_class == "non_content_needs_sampling" and block and len(block.get("sentences") or []) >= 2:
            return (
                "ignored_prose_llm_split_candidate",
                "run_sentence_grouping_or_manual_split",
                "ignored block looks like textbook prose; split before direct evidence",
            )
        if ignored_class in {"visual_or_table_label", "visual_fragment_needs_review"}:
            return (
                "ignored_visual_label_group_review",
                "inspect_visual_or_table_group",
                "short visual/table label needs its surrounding figure/table context",
            )
        if ignored_class == "text_damage_fragment":
            return (
                "ignored_text_damage_manual",
                "manual_pdf_source_review",
                "ignored fragment contains extraction damage",
            )
        if ignored_class == "short_context_label":
            return (
                "ignored_short_context_label_review",
                "decide_context_parent_or_discard",
                "short label may be a heading/context node, not direct evidence",
            )
        if ignored_class == "short_sub_bullet_continuation_risk":
            return (
                "ignored_short_bullet_neighbor_context_review",
                "inspect_neighbor_blocks_or_pdf_join",
                "short bullet has continuation risk and needs neighbor context",
            )
        return (
            "ignored_review_other",
            "manual_review",
            "ignored recovery did not match a deterministic promotion rule",
        )

    damage = text_damage_hits(unit)
    if damage or "moved_from_direct_to_review_prefreeze_qa" in flags:
        return (
            "text_damage_manual_source_review",
            "manual_pdf_source_review",
            "direct text showed extraction damage or PDF text-layer damage",
        )
    if "llm_group_too_broad_needs_review" in flags:
        return (
            "too_broad_resplit_candidate",
            "rerun_llm_resplit_on_unit",
            "unit is coherent but exceeds the direct width gate",
        )
    if "source_sentence_may_continue_next_block" in flags or "source_sentence_may_continue_from_previous_block" in flags:
        return (
            "cross_block_join_candidate",
            "inspect_neighbor_blocks_or_pdf_join",
            "source sentence appears split across adjacent blocks",
        )
    if "incomplete_sentence" in flags or "fragment" in flags or review_class == "true_fragment_or_incomplete":
        return (
            "fragment_neighbor_join_or_discard",
            "inspect_neighbor_blocks_then_join_or_discard",
            "unit is a fragment; needs adjacent text or should remain non-direct",
        )
    if looks_structural_parent(unit):
        return (
            "structural_parent_candidate",
            "demote_to_parent_or_context",
            "introductory/list-parent sentence is context rather than direct evidence",
        )
    return (
        "manual_policy_review",
        "manual_review",
        "remaining review item requires policy or source judgment",
    )


def unit_brief(unit: dict[str, Any], block: dict[str, Any] | None, blocks: list[dict[str, Any]], idx_by_id: dict[str, int]) -> dict[str, Any]:
    resolution_class, action, rationale = classify_resolution(unit, block)
    block_id = source_block_id(unit)
    return {
        "unit_id": unit.get("unit_id"),
        "chapter": unit.get("chapter"),
        "unit_type": unit.get("unit_type"),
        "review_class": classify_review_item(unit),
        "resolution_class": resolution_class,
        "recommended_action": action,
        "rationale": rationale,
        "printed_page": unit.get("printed_page"),
        "pdf_page": unit.get("pdf_page"),
        "heading_context": unit.get("heading_context", []),
        "knowledge_en": unit.get("knowledge_en"),
        "en_quote": unit.get("en_quote"),
        "risk_flags": unit.get("risk_flags", []),
        "source": unit.get("source", {}),
        "source_block_id": block_id,
        "source_block_context": neighbor_context(blocks, idx_by_id, block_id),
    }


def build_report(plan: dict[str, Any]) -> str:
    lines = [
        "# v7 Review Resolution Plan",
        "",
        f"Generated at: {plan['generated_at']}",
        f"Input: `{plan['input_file']}`",
        "",
        "## Summary",
        "",
        f"- review items: {plan['review_items']}",
        "",
        "## Resolution Classes",
        "",
    ]
    for name, count in plan["resolution_class_counts"].items():
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Recommended Actions", ""])
    for name, count in plan["recommended_action_counts"].items():
        lines.append(f"- {name}: {count}")
    for name, samples in plan["samples_by_resolution_class"].items():
        lines.extend(["", f"## Samples: {name}", ""])
        for sample in samples[:10]:
            lines.extend(
                [
                    f"### {sample['unit_id']}",
                    "",
                    f"- action: {sample['recommended_action']}",
                    f"- rationale: {sample['rationale']}",
                    f"- chapter: {sample.get('chapter')}",
                    f"- page: {sample.get('printed_page')} / pdf {sample.get('pdf_page')}",
                    f"- heading: {' / '.join(sample.get('heading_context', []))}",
                    f"- knowledge_en: {sample.get('knowledge_en')}",
                    f"- en_quote: {compact(sample.get('en_quote'), 700)}",
                    f"- risk_flags: {json.dumps(sample.get('risk_flags', []), ensure_ascii=False)}",
                    "",
                ]
            )
            ctx = sample.get("source_block_context") or {}
            if ctx:
                lines.extend(["  Neighbor context:", ""])
                for label in ["prev", "current", "next"]:
                    item = ctx.get(label)
                    if item:
                        lines.append(
                            f"  - {label} `{item.get('block_id')}` P{item.get('printed_page')}: {item.get('text')}"
                        )
                lines.append("")
    return "\n".join(lines)


def audit(input_file: Path, blocks_file: Path) -> dict[str, Any]:
    payload = read_json(input_file)
    blocks_payload = read_json(blocks_file)
    blocks = blocks_payload.get("items", [])
    blocks_by_id, idx_by_id = build_block_index(blocks)
    review_items = payload.get("review_items", [])
    decisions = []
    for unit in review_items:
        block_id = source_block_id(unit)
        block = blocks_by_id.get(block_id) if block_id else None
        decisions.append(unit_brief(unit, block, blocks, idx_by_id))

    by_resolution: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in decisions:
        by_resolution[item["resolution_class"]].append(item)

    return {
        "schema_version": "v7_review_resolution_plan_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_file": str(input_file),
        "blocks_file": str(blocks_file),
        "review_items": len(review_items),
        "resolution_class_counts": dict(Counter(item["resolution_class"] for item in decisions).most_common()),
        "recommended_action_counts": dict(Counter(item["recommended_action"] for item in decisions).most_common()),
        "review_class_counts": dict(Counter(item["review_class"] for item in decisions).most_common()),
        "decisions": decisions,
        "samples_by_resolution_class": {
            name: samples[:12]
            for name, samples in sorted(by_resolution.items(), key=lambda item: (-len(item[1]), item[0]))
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan the next resolution step for v7 pre-freeze review items.")
    parser.add_argument("--input-file", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--blocks-file", type=Path, default=DEFAULT_BLOCKS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plan = audit(args.input_file.resolve(), args.blocks_file.resolve())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_json = args.out_dir / "review_resolution_plan.json"
    out_report = args.out_dir / "review_resolution_plan.md"
    write_json(out_json, plan)
    out_report.write_text(build_report(plan), encoding="utf-8")
    print(f"review items: {plan['review_items']}")
    print(f"resolution classes: {json.dumps(plan['resolution_class_counts'], ensure_ascii=False)}")
    print(f"recommended actions: {json.dumps(plan['recommended_action_counts'], ensure_ascii=False)}")
    print(f"wrote: {out_json}")
    print(f"wrote: {out_report}")


if __name__ == "__main__":
    main()
