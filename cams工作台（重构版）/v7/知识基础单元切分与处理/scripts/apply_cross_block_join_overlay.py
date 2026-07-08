from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DRAFT_DIR = BASE_UNITS_DIR / "draft" / "v2_fullbook"
AUDIT_DIR = BASE_UNITS_DIR / "audit"

DEFAULT_INPUT = DRAFT_DIR / "v7_units_draft.v2_fullbook_all.prefreeze_qa.json"
DEFAULT_PLAN = AUDIT_DIR / "review_resolution_plan" / "review_resolution_plan.json"
DEFAULT_BLOCKS = BASE_UNITS_DIR / "patched" / "v7_en_blocks.patched.json"
DEFAULT_OUT_DIR = AUDIT_DIR / "cross_block_join_overlay"

TERMINAL_RE = re.compile(r"[.!?;:]\s*$")
BULLET_RE = re.compile(r"^\s*(<\s*sub\s*>\s*o|[•\-\u2022]|鈥\?)\s+", re.IGNORECASE)
CONTEXT_DEPENDENT_START_RE = re.compile(r"^\s*(they|these|this|those|such|their)\b", re.IGNORECASE)


TYPE_MAP = {
    "definition": "definition",
    "classification": "classification",
    "rule": "rule",
    "obligation": "rule",
    "process": "process",
    "red_flag": "risk_indicator",
    "risk_indicator": "risk_indicator",
    "case_fact": "case",
    "example": "case",
    "fact": "fact",
    "needs_review": "context",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compact(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def has_terminal(text: str) -> bool:
    return bool(TERMINAL_RE.search(str(text or "").strip().rstrip("\"'”’)]}")))


def is_bullet_or_list_block(block: dict[str, Any] | None) -> bool:
    if not block:
        return False
    if block.get("block_type") in {"list_item", "numbered_item"}:
        return True
    return bool(BULLET_RE.search(str(block.get("text") or "")))


def source_block_id(unit: dict[str, Any]) -> str | None:
    source = unit.get("source") or {}
    if source.get("en_block_id"):
        return str(source["en_block_id"])
    for sid in unit.get("en_sentence_ids") or []:
        match = re.match(r"(v7en_b\d+)", str(sid))
        if match:
            return match.group(1)
    return None


def block_num(block_id: str | None) -> int | None:
    match = re.search(r"b(\d+)", str(block_id or ""))
    return int(match.group(1)) if match else None


def unique(values: list[Any]) -> list[Any]:
    out = []
    seen = set()
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True)
        if value is None or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def merge_sentence_text(left: str, right: str) -> str:
    left = re.sub(r"\s+", " ", str(left or "")).strip()
    right = re.sub(r"\s+", " ", str(right or "")).strip()
    if not left:
        return right
    if not right:
        return left
    if left.endswith("-"):
        return left[:-1] + right
    return f"{left} {right}"


def infer_join_unit_type(left_unit: dict[str, Any], right_unit: dict[str, Any], text: str) -> str:
    for unit in [left_unit, right_unit]:
        unit_type = unit.get("unit_type")
        if unit_type and unit_type != "needs_review":
            return str(unit_type)
    text_l = text.lower()
    if any(token in text_l for token in ["must", "should", "required", "obligation"]):
        return "obligation"
    if any(token in text_l for token in ["risk", "suspicious", "red flag", "unusual"]):
        return "risk_indicator"
    if any(token in text_l for token in ["case", "example"]):
        return "example"
    return "fact"


def page_values(unit: dict[str, Any], key: str, fallback_key: str) -> list[Any]:
    values = unit.get(key)
    if isinstance(values, list):
        return values
    value = unit.get(fallback_key)
    return [value] if value is not None else []


def make_sentence_item(sentence: dict[str, Any], unit_id: str, text: str | None = None) -> dict[str, Any]:
    return {
        "sentence_id": sentence.get("sentence_id"),
        "text": text if text is not None else sentence.get("text"),
        "role": "retrieval_slice",
        "parent_unit_id": unit_id,
    }


def make_join_unit(serial: int, left_unit: dict[str, Any], right_unit: dict[str, Any]) -> dict[str, Any]:
    left_sentence = (left_unit.get("en_sentences") or [])[-1]
    right_sentence = (right_unit.get("en_sentences") or [])[0]
    joined_text = merge_sentence_text(str(left_sentence.get("text") or ""), str(right_sentence.get("text") or ""))
    unit_id = f"v7u_tmp_prefreeze_crossblock_join_N{serial:06d}"
    unit_type = infer_join_unit_type(left_unit, right_unit, joined_text)
    page_span = unique(page_values(left_unit, "page_span", "pdf_page") + page_values(right_unit, "page_span", "pdf_page"))
    printed_page_span = unique(
        page_values(left_unit, "printed_page_span", "printed_page")
        + page_values(right_unit, "printed_page_span", "printed_page")
    )
    flags = {
        "cross_block_sentence_joined_prefreeze_qa",
        "derived_from_review_resolution_plan",
        "zh_subspan_unavailable",
    }
    if CONTEXT_DEPENDENT_START_RE.search(joined_text):
        flags.add("antecedent_requires_prior_context")
    return {
        "unit_id": unit_id,
        "unit_status": "draft",
        "pilot_slug": "prefreeze_cross_block_join_overlay",
        "chapter": left_unit.get("chapter") or right_unit.get("chapter"),
        "unit_type": unit_type,
        "type": TYPE_MAP.get(unit_type, "fact"),
        "evidence_status": "direct",
        "can_be_direct_evidence": True,
        "en_quote": joined_text,
        "en_sentence_ids": [left_sentence.get("sentence_id"), right_sentence.get("sentence_id")],
        "en_sentences": [
            {
                "sentence_id": f"{left_sentence.get('sentence_id')}__{right_sentence.get('sentence_id')}__joined",
                "text": joined_text,
                "role": "retrieval_slice",
                "parent_unit_id": unit_id,
                "source_sentence_ids": [left_sentence.get("sentence_id"), right_sentence.get("sentence_id")],
            }
        ],
        "knowledge_en": compact(joined_text, 160).rstrip("."),
        "knowledge_zh": None,
        "zh_display_text": None,
        "zh_display_mode": "knowledge_zh_pending",
        "zh_context_full": None,
        "zh_search_text": None,
        "zh_search_text_status": "not_available",
        "terms": [],
        "pdf_page": page_span[0] if page_span else left_unit.get("pdf_page") or right_unit.get("pdf_page"),
        "printed_page": printed_page_span[0] if printed_page_span else left_unit.get("printed_page") or right_unit.get("printed_page"),
        "printed_page_span": printed_page_span,
        "page_span": page_span,
        "heading_context": left_unit.get("heading_context") or right_unit.get("heading_context") or [],
        "source": {
            "materialization_method": "prefreeze_cross_block_join_overlay_v1",
            "left_unit_id": left_unit.get("unit_id"),
            "right_unit_id": right_unit.get("unit_id"),
            "left_block_id": source_block_id(left_unit),
            "right_block_id": source_block_id(right_unit),
            "source_sentence_ids": [left_sentence.get("sentence_id"), right_sentence.get("sentence_id")],
        },
        "decision_reason": "Joined high-confidence adjacent cross-block sentence fragments.",
        "risk_flags": sorted(flags),
    }


def make_remainder_unit(
    serial: int,
    source_unit: dict[str, Any],
    sentence: dict[str, Any],
    *,
    side: str,
) -> dict[str, Any]:
    text = str(sentence.get("text") or "").strip()
    unit_id = f"v7u_tmp_prefreeze_crossblock_remainder_N{serial:06d}"
    unit_type = source_unit.get("unit_type")
    if not unit_type or unit_type == "needs_review":
        unit_type = "fact"
    flags = {
        "cross_block_remainder_recovered_prefreeze_qa",
        f"recovered_from_{side}_review_unit",
        "zh_subspan_unavailable",
    }
    if CONTEXT_DEPENDENT_START_RE.search(text):
        flags.add("antecedent_requires_prior_context")
    return {
        "unit_id": unit_id,
        "unit_status": "draft",
        "pilot_slug": "prefreeze_cross_block_join_overlay",
        "chapter": source_unit.get("chapter"),
        "unit_type": unit_type,
        "type": TYPE_MAP.get(str(unit_type), "fact"),
        "evidence_status": "direct",
        "can_be_direct_evidence": True,
        "en_quote": text,
        "en_sentence_ids": [sentence.get("sentence_id")],
        "en_sentences": [make_sentence_item(sentence, unit_id, text)],
        "knowledge_en": compact(text, 160).rstrip("."),
        "knowledge_zh": None,
        "zh_display_text": None,
        "zh_display_mode": "knowledge_zh_pending",
        "zh_context_full": None,
        "zh_search_text": None,
        "zh_search_text_status": "not_available",
        "terms": [],
        "pdf_page": source_unit.get("pdf_page"),
        "printed_page": source_unit.get("printed_page"),
        "printed_page_span": source_unit.get("printed_page_span", []),
        "page_span": source_unit.get("page_span", []),
        "heading_context": source_unit.get("heading_context", []),
        "source": {
            "materialization_method": "prefreeze_cross_block_remainder_recovery_v1",
            "source_unit_id": source_unit.get("unit_id"),
            "source_block_id": source_block_id(source_unit),
            "source_sentence_id": sentence.get("sentence_id"),
            "side": side,
        },
        "decision_reason": "Recovered complete sentence left over after cross-block join.",
        "risk_flags": sorted(flags),
    }


def direct_sentence_owners(items: list[dict[str, Any]]) -> dict[str, str]:
    owners = {}
    for unit in items:
        for sid in unit.get("en_sentence_ids") or []:
            owners.setdefault(str(sid), str(unit.get("unit_id")))
    return owners


def build_pair_candidates(
    plan: dict[str, Any],
    review_items: list[dict[str, Any]],
    blocks_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_unit_id = {str(unit.get("unit_id")): unit for unit in review_items}
    by_block_next: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_block_prev: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in plan.get("decisions", []):
        if item.get("resolution_class") != "cross_block_join_candidate":
            continue
        unit = by_unit_id.get(str(item.get("unit_id")))
        if not unit:
            continue
        flags = set(unit.get("risk_flags", []))
        block_id = source_block_id(unit)
        if not block_id:
            continue
        if "source_sentence_may_continue_next_block" in flags:
            by_block_next[block_id].append(unit)
        if "source_sentence_may_continue_from_previous_block" in flags:
            by_block_prev[block_id].append(unit)

    candidates = []
    skipped = []
    for left_block_id, left_units in sorted(by_block_next.items(), key=lambda item: block_num(item[0]) or 0):
        left_block_num = block_num(left_block_id)
        if left_block_num is None:
            continue
        right_block_id = f"v7en_b{left_block_num + 1:06d}"
        right_units = by_block_prev.get(right_block_id) or []
        if not right_units:
            skipped.append({"left_block_id": left_block_id, "reason": "no_matching_right_review_unit"})
            continue
        left_unit = left_units[-1]
        right_unit = right_units[0]
        left_block = blocks_by_id.get(left_block_id)
        right_block = blocks_by_id.get(right_block_id)
        left_sents = left_unit.get("en_sentences") or []
        right_sents = right_unit.get("en_sentences") or []
        reason = None
        if not left_sents or not right_sents:
            reason = "missing_sentence_items"
        elif is_bullet_or_list_block(right_block):
            reason = "bullet_or_list_sequence_not_sentence_join"
        elif has_terminal(str(left_sents[-1].get("text") or "")):
            reason = "left_fragment_has_terminal_punctuation"
        elif not has_terminal(merge_sentence_text(str(left_sents[-1].get("text") or ""), str(right_sents[0].get("text") or ""))):
            reason = "joined_text_still_lacks_terminal_punctuation"
        if reason:
            skipped.append(
                {
                    "left_unit_id": left_unit.get("unit_id"),
                    "right_unit_id": right_unit.get("unit_id"),
                    "left_block_id": left_block_id,
                    "right_block_id": right_block_id,
                    "reason": reason,
                    "left_quote": left_unit.get("en_quote"),
                    "right_quote": right_unit.get("en_quote"),
                }
            )
            continue
        candidates.append(
            {
                "left_unit": left_unit,
                "right_unit": right_unit,
                "left_block_id": left_block_id,
                "right_block_id": right_block_id,
                "joined_preview": merge_sentence_text(str(left_sents[-1].get("text") or ""), str(right_sents[0].get("text") or "")),
            }
        )
    return candidates, skipped


def duplicate_values(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def recompute_audit(payload: dict[str, Any], overlay_audit: dict[str, Any]) -> dict[str, Any]:
    items = payload.get("items", [])
    review_items = payload.get("review_items", [])
    parent_items = payload.get("parent_items", [])
    all_units = [*items, *review_items, *parent_items]
    unit_ids = [str(unit.get("unit_id")) for unit in all_units if unit.get("unit_id")]
    direct_sentence_ids = [
        str(sentence_id)
        for unit in items
        for sentence_id in unit.get("en_sentence_ids", [])
        if sentence_id
    ]
    audit = dict(payload.get("audit") or {})
    audit.update(
        {
            "direct_items": len(items),
            "review_items": len(review_items),
            "parent_items": len(parent_items),
            "duplicate_unit_ids": duplicate_values(unit_ids),
            "duplicate_direct_sentence_ids": duplicate_values(direct_sentence_ids),
            "cross_block_join_overlay": overlay_audit,
        }
    )
    return audit


def apply_overlay(input_file: Path, plan_file: Path, blocks_file: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = deepcopy(read_json(input_file))
    plan = read_json(plan_file)
    blocks = read_json(blocks_file).get("items", [])
    blocks_by_id = {str(block.get("block_id")): block for block in blocks if block.get("block_id")}
    review_items = payload.get("review_items", [])
    items = payload.get("items", [])
    direct_owners = direct_sentence_owners(items)

    candidates, skipped = build_pair_candidates(plan, review_items, blocks_by_id)
    removed_review_ids: set[str] = set()
    new_direct: list[dict[str, Any]] = []
    join_records: list[dict[str, Any]] = []
    remainder_records: list[dict[str, Any]] = []
    join_serial = 1
    remainder_serial = 1
    used_join_source_sids: set[str] = set()

    for candidate in candidates:
        left_unit = candidate["left_unit"]
        right_unit = candidate["right_unit"]
        left_sents = left_unit.get("en_sentences") or []
        right_sents = right_unit.get("en_sentences") or []
        join_unit = make_join_unit(join_serial, left_unit, right_unit)
        join_serial += 1
        new_direct.append(join_unit)
        removed_review_ids.add(str(left_unit.get("unit_id")))
        removed_review_ids.add(str(right_unit.get("unit_id")))
        used_join_source_sids.update(str(sid) for sid in join_unit.get("en_sentence_ids") or [])
        join_records.append(
            {
                "join_unit_id": join_unit["unit_id"],
                "left_unit_id": left_unit.get("unit_id"),
                "right_unit_id": right_unit.get("unit_id"),
                "left_block_id": candidate["left_block_id"],
                "right_block_id": candidate["right_block_id"],
                "joined_text": join_unit["en_quote"],
            }
        )

        for side, unit, sentences in [("left", left_unit, left_sents[:-1]), ("right", right_unit, right_sents[1:])]:
            for sentence in sentences:
                sid = str(sentence.get("sentence_id") or "")
                if not sid or sid in direct_owners or sid in used_join_source_sids:
                    continue
                text = str(sentence.get("text") or "").strip()
                if not text or not has_terminal(text):
                    skipped.append(
                        {
                            "source_unit_id": unit.get("unit_id"),
                            "sentence_id": sid,
                            "reason": "remainder_not_direct_safe",
                            "text": text,
                        }
                    )
                    continue
                remainder = make_remainder_unit(remainder_serial, unit, sentence, side=side)
                remainder_serial += 1
                new_direct.append(remainder)
                direct_owners[sid] = remainder["unit_id"]
                remainder_records.append(
                    {
                        "remainder_unit_id": remainder["unit_id"],
                        "source_unit_id": unit.get("unit_id"),
                        "sentence_id": sid,
                        "text": text,
                    }
                )

    payload["items"] = [*items, *new_direct]
    payload["review_items"] = [
        unit for unit in review_items if str(unit.get("unit_id")) not in removed_review_ids
    ]
    payload["schema_version"] = "v7_units_draft_fullbook_ds_v2_prefreeze_qa_crossblock_overlay_v1"
    payload["status"] = "draft_prefreeze_qa_crossblock_overlay_not_for_downstream_binding"
    payload["generated_at"] = datetime.now().isoformat(timespec="seconds")
    payload.setdefault("sources", {})["cross_block_overlay_base"] = str(input_file.relative_to(BASE_UNITS_DIR))
    payload.setdefault("notes", []).append(
        "Cross-block join overlay applied high-confidence adjacent sentence joins; IDs remain temporary."
    )

    overlay_audit = {
        "input_file": str(input_file.relative_to(BASE_UNITS_DIR)),
        "plan_file": str(plan_file.relative_to(BASE_UNITS_DIR)),
        "candidate_pairs": len(candidates),
        "skipped_pairs_or_remainders": len(skipped),
        "review_items_removed": len(removed_review_ids),
        "join_direct_units_added": len(join_records),
        "remainder_direct_units_added": len(remainder_records),
        "join_records": join_records,
        "remainder_records": remainder_records,
        "skipped": skipped,
    }
    payload["audit"] = recompute_audit(payload, overlay_audit)
    manifest = {
        "schema_version": "v7_cross_block_join_overlay_manifest_v1",
        "generated_at": payload["generated_at"],
        **overlay_audit,
    }
    return payload, manifest


def build_report(payload: dict[str, Any], manifest: dict[str, Any]) -> str:
    lines = [
        "# v7 Cross-block Join Overlay",
        "",
        f"Generated at: {manifest['generated_at']}",
        "",
        "## Summary",
        "",
        f"- direct items: {len(payload.get('items', []))}",
        f"- review items: {len(payload.get('review_items', []))}",
        f"- parent/context items: {len(payload.get('parent_items', []))}",
        f"- candidate pairs joined: {manifest['candidate_pairs']}",
        f"- review items removed: {manifest['review_items_removed']}",
        f"- joined direct units added: {manifest['join_direct_units_added']}",
        f"- remainder direct units added: {manifest['remainder_direct_units_added']}",
        f"- skipped pairs/remainders: {manifest['skipped_pairs_or_remainders']}",
        f"- duplicate unit_ids: {len(payload['audit'].get('duplicate_unit_ids', []))}",
        f"- duplicate direct sentence_ids: {len(payload['audit'].get('duplicate_direct_sentence_ids', []))}",
        "",
        "## Joined Samples",
        "",
    ]
    for record in manifest["join_records"][:30]:
        lines.extend(
            [
                f"### {record['join_unit_id']}",
                "",
                f"- blocks: `{record['left_block_id']}` -> `{record['right_block_id']}`",
                f"- text: {record['joined_text']}",
                "",
            ]
        )
    if manifest["skipped"]:
        lines.extend(["## Skipped Samples", ""])
        for item in manifest["skipped"][:30]:
            lines.append(f"- {json.dumps(item, ensure_ascii=False)}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply high-confidence cross-block sentence joins as a reversible overlay.")
    parser.add_argument("--input-file", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--plan-file", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--blocks-file", type=Path, default=DEFAULT_BLOCKS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--draft-out-dir", type=Path, default=DRAFT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, manifest = apply_overlay(args.input_file.resolve(), args.plan_file.resolve(), args.blocks_file.resolve())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.draft_out_dir.mkdir(parents=True, exist_ok=True)

    out_json = args.draft_out_dir / "v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock.json"
    out_audit = args.draft_out_dir / "v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock_audit.json"
    out_report = args.draft_out_dir / "v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock_report.md"
    manifest_json = args.out_dir / "cross_block_join_manifest.json"
    manifest_report = args.out_dir / "cross_block_join_manifest.md"

    write_json(out_json, payload)
    write_json(out_audit, payload["audit"])
    out_report.write_text(build_report(payload, manifest), encoding="utf-8")
    write_json(manifest_json, manifest)
    manifest_report.write_text(build_report(payload, manifest), encoding="utf-8")

    print(f"direct items: {len(payload['items'])}")
    print(f"review items: {len(payload['review_items'])}")
    print(f"parent/context items: {len(payload['parent_items'])}")
    print(f"candidate pairs joined: {manifest['candidate_pairs']}")
    print(f"review items removed: {manifest['review_items_removed']}")
    print(f"joined direct units added: {manifest['join_direct_units_added']}")
    print(f"remainder direct units added: {manifest['remainder_direct_units_added']}")
    print(f"skipped pairs/remainders: {manifest['skipped_pairs_or_remainders']}")
    print(f"duplicate unit_ids: {len(payload['audit']['duplicate_unit_ids'])}")
    print(f"duplicate direct sentence_ids: {len(payload['audit']['duplicate_direct_sentence_ids'])}")
    print(f"wrote: {out_json}")
    print(f"wrote: {manifest_json}")


if __name__ == "__main__":
    main()
