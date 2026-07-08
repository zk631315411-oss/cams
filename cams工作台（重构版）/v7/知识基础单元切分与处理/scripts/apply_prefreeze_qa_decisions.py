from __future__ import annotations

import argparse
import json
import re
from collections import Counter
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

DEFAULT_COMBINED = DRAFT_DIR / "v7_units_draft.v2_fullbook_all.combined.json"
DEFAULT_BLOCKS = BASE_UNITS_DIR / "patched" / "v7_en_blocks.patched.json"
DEFAULT_IGNORED_AUDIT = AUDIT_DIR / "ignored_routes" / "ignored_route_audit.json"
DEFAULT_TEXT_AUDIT = AUDIT_DIR / "direct_text_quality" / "direct_text_quality_audit.json"
DEFAULT_OUT_DIR = AUDIT_DIR / "pre_freeze_qa"


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

SURFACE_FIXES = {
    "v7u_tmp_pilot_v2fb_data-as-an-input-for-solutions_o000_l020_N000044": [
        {
            "before": "timeconsuming",
            "after": "time-consuming",
            "verification": "pdf_text_page_470",
            "reason": "PDF text layer has line-broken 'time- consuming'; normalize for evidence display/search.",
        }
    ],
    "v7u_tmp_pilot_v2fb_data-as-an-input-for-solutions_o060_l020_N000013": [
        {
            "before": "enduser",
            "after": "end-user",
            "verification": "pdf_text_page_482",
            "reason": "PDF text layer has line-broken 'end- user'; normalize for evidence display/search.",
        }
    ],
    "v7u_tmp_pilot_v2fb_governance-process_o000_l020_N000014": [
        {
            "before": "enduser",
            "after": "end-user",
            "verification": "pdf_text_page_493",
            "reason": "PDF text layer has line-broken 'end- user'; normalize for evidence display/search.",
        }
    ],
    "v7u_tmp_pilot_v2fb_types-of-financial-crime_o020_l020_N000032": [
        {
            "before": "financia account",
            "after": "financial account",
            "verification": "pdf_text_page_33",
            "reason": "PDF text layer reads 'financial account information'.",
        }
    ],
    "v7u_tmp_pilot_v2fb_money-laundering-risks-associated-with-cryptoassets-and-other-fintechs_o020_l020_N000001": [
        {
            "before": "origina funds",
            "after": "original funds",
            "verification": "pdf_text_page_120",
            "reason": "PDF text layer reads 'original funds'.",
        }
    ],
    "v7u_tmp_pilot_v2fb_technology-for-kyc_o020_l020_N000011": [
        {
            "before": "In its , published in March of 2020",
            "after": "In its Guidance on Digital Identity, published in March of 2020",
            "verification": "pdf_text_page_414",
            "reason": "PDF text layer includes the missing publication title.",
        }
    ],
}

MOVE_DIRECT_TO_REVIEW = {
    "v7u_tmp_pilot_v2fb_technology-for-kyc_o080_l020_N000014": {
        "reason": "PDF text layer repeats the same garbled phrase; not reliable enough for direct evidence.",
        "issue": "duplicated_phrase_accommodate",
        "verification": "pdf_text_page_429",
    }
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compact(text: str, limit: int = 500) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def clean_list_marker(text: str) -> str:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"^\s*<\s*sub\s*>\s*o\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\s*[•\-\u2022]\s*", "", cleaned)
    cleaned = re.sub(r"^\s*鈥\?\s*", "", cleaned)
    cleaned = re.sub(r"^\s*o\s+", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9/]+", text))


def is_bullet_like(block: dict[str, Any], cleaned_text: str) -> bool:
    raw = str(block.get("text") or "")
    return (
        block.get("block_type") in {"list_item", "numbered_item"}
        or bool(re.match(r"^\s*(<\s*sub\s*>\s*o|[•\-\u2022]|鈥\?)\s+", raw, re.IGNORECASE))
        or (word_count(cleaned_text) <= 6 and "," not in cleaned_text)
    )


def chapter_from_heading(heading_context: list[str]) -> str | None:
    return heading_context[0] if heading_context else None


def infer_unit_type(text: str, heading_context: list[str]) -> str:
    text_l = text.lower()
    heading_l = " / ".join(heading_context).lower()
    if any(token in heading_l for token in ("risk", "red flag", "indicator", "high-risk")):
        return "risk_indicator"
    if any(token in text_l for token in ("unusual", "suspicious", "risk", "red flag", "illicit")):
        return "risk_indicator"
    if text_l.startswith(("identify ", "map ", "implement ", "understand ", "review ", "monitor ", "verify ")):
        return "process"
    return "fact"


def sentence_items_for_block(block: dict[str, Any], cleaned_text: str, unit_id: str) -> tuple[list[str], list[dict[str, Any]]]:
    raw_sentences = block.get("sentences") or []
    sentence_ids: list[str] = []
    sentence_items: list[dict[str, Any]] = []
    if raw_sentences:
        for idx, item in enumerate(raw_sentences, start=1):
            sid = str(item.get("sentence_id") or f"{block.get('block_id')}_s{idx:03d}")
            text = clean_list_marker(str(item.get("text") or cleaned_text))
            sentence_ids.append(sid)
            sentence_items.append(
                {
                    "sentence_id": sid,
                    "text": text,
                    "role": "retrieval_slice",
                    "parent_unit_id": unit_id,
                }
            )
    else:
        sid = f"{block.get('block_id')}_qa_block"
        sentence_ids = [sid]
        sentence_items = [
            {
                "sentence_id": sid,
                "text": cleaned_text,
                "role": "retrieval_slice",
                "parent_unit_id": unit_id,
            }
        ]
    return sentence_ids, sentence_items


def make_ignored_unit(
    *,
    serial: int,
    decision: dict[str, Any],
    block: dict[str, Any],
    applied_action: str,
    applied_reason: str,
) -> dict[str, Any]:
    cleaned_text = clean_list_marker(str(block.get("text") or decision.get("cleaned_text") or ""))
    heading_context = block.get("heading_stack") or decision.get("heading_context") or []
    direct = applied_action == "recover_as_direct_list_item"
    unit_id = f"v7u_tmp_prefreeze_qa_ignored_N{serial:06d}"
    sentence_ids, sentence_items = sentence_items_for_block(block, cleaned_text, unit_id)
    unit_type = infer_unit_type(cleaned_text, heading_context) if direct else "needs_review"
    evidence_status = "direct" if direct else "needs_review"
    page_span = [block.get("pdf_page")] if isinstance(block.get("pdf_page"), int) else []
    printed_page_span = [block.get("printed_page")] if block.get("printed_page") is not None else []
    risk_flags = set(str(flag) for flag in decision.get("risk_flags", []) if flag)
    if not direct:
        risk_flags.update(str(flag) for flag in block.get("risk_flags", []) if flag)
    risk_flags.add("recovered_from_ignored_route_prefreeze_qa")
    risk_flags.add(f"ignored_review_class:{decision.get('review_class')}")
    risk_flags.add(f"ignored_original_route:{decision.get('route')}")
    risk_flags.add("zh_subspan_unavailable")
    if not direct:
        risk_flags.add("needs_human_review_before_freeze")

    return {
        "unit_id": unit_id,
        "unit_status": "draft",
        "pilot_slug": "prefreeze_qa_ignored_routes",
        "chapter": chapter_from_heading(heading_context),
        "unit_type": unit_type,
        "type": TYPE_MAP.get(unit_type, "context"),
        "evidence_status": evidence_status,
        "can_be_direct_evidence": direct,
        "en_quote": cleaned_text,
        "en_sentence_ids": sentence_ids if direct else sentence_ids,
        "en_sentences": sentence_items,
        "knowledge_en": cleaned_text.rstrip("."),
        "knowledge_zh": None,
        "zh_display_text": None,
        "zh_display_mode": "knowledge_zh_pending",
        "zh_context_full": None,
        "zh_search_text": None,
        "zh_search_text_status": "not_available",
        "terms": [],
        "pdf_page": block.get("pdf_page"),
        "printed_page": block.get("printed_page"),
        "printed_page_span": printed_page_span,
        "page_span": page_span,
        "heading_context": heading_context,
        "source": {
            "en_block_id": block.get("block_id"),
            "materialization_method": "prefreeze_qa_ignored_route_recovery_v1",
            "original_ignored_route": decision.get("route"),
            "ignored_review_class": decision.get("review_class"),
            "applied_action": applied_action,
            "applied_reason": applied_reason,
        },
        "decision_reason": applied_reason,
        "risk_flags": sorted(flag for flag in risk_flags if flag),
    }


def refine_ignored_decision(decision: dict[str, Any], block: dict[str, Any] | None) -> dict[str, Any]:
    refined = dict(decision)
    action = str(decision.get("recommended_action") or "")
    cleaned_text = clean_list_marker(str((block or {}).get("text") or decision.get("cleaned_text") or ""))
    block_type = str((block or {}).get("block_type") or decision.get("block_type") or "")
    heading = " / ".join((block or {}).get("heading_stack") or decision.get("heading_context") or [])

    applied_action = "keep_ignored"
    applied_reason = "ignored route remains outside base units"

    if action == "recover_as_list_item":
        applied_action = "recover_as_direct_list_item"
        applied_reason = "cleaned ignored bullet is a standalone list item"
    elif action in {"move_to_review", "review_ignored_non_content"}:
        if block and action == "review_ignored_non_content" and is_bullet_like(block, cleaned_text):
            if block_type in {"list_item", "numbered_item"} and word_count(cleaned_text) <= 6:
                applied_action = "recover_as_direct_list_item"
                applied_reason = "short ignored list item is valid textbook content under its heading"
            else:
                applied_action = "move_to_review"
                applied_reason = "ignored short label/list fragment needs context review"
        elif block and action == "review_ignored_non_content" and "Special purpose vehicle risks" in heading:
            applied_action = "move_to_review"
            applied_reason = "SPV prose was routed non_content but looks like textbook content; send to review/LLM split"
        elif block and action == "review_ignored_non_content" and "Wire transfer risks" in heading:
            applied_action = "move_to_review"
            applied_reason = "bank transfer prose was routed non_content but looks like textbook content; send to review/LLM split"
        else:
            applied_action = "move_to_review"
            applied_reason = "ignored fragment may be useful but is not safe as direct evidence"
    elif action == "glossary_asset_candidate":
        applied_action = "export_glossary_asset_candidate"
        applied_reason = "glossary/acronym rows are terminology assets, not base evidence units"
    elif action == "keep_heading_context":
        applied_action = "keep_heading_context"
        applied_reason = "heading remains context only"
    elif action == "keep_ignore":
        applied_action = "keep_ignored"
        applied_reason = "non-content/teaching/navigation text remains ignored"
    elif action == "recover_as_table":
        applied_action = "move_to_review"
        applied_reason = "content table recovery should wait for table parser replay"
    elif action.startswith("review"):
        applied_action = "move_to_review"
        applied_reason = "ambiguous ignored route needs review before freeze"

    refined["cleaned_text"] = cleaned_text
    refined["applied_action"] = applied_action
    refined["applied_reason"] = applied_reason
    return refined


def apply_replacements(text: str, replacements: list[dict[str, str]]) -> str:
    fixed = text
    for repl in replacements:
        fixed = fixed.replace(repl["before"], repl["after"])
    return fixed


def update_unit_text(unit: dict[str, Any], replacements: list[dict[str, str]]) -> dict[str, Any]:
    updated = deepcopy(unit)
    before = str(updated.get("en_quote") or "")
    after = apply_replacements(before, replacements)
    updated["en_quote"] = after
    updated["knowledge_en"] = apply_replacements(str(updated.get("knowledge_en") or ""), replacements)
    for sentence in updated.get("en_sentences") or []:
        sentence["text"] = apply_replacements(str(sentence.get("text") or ""), replacements)
        sentence.setdefault("source_text_cleanup_flags", []).append("prefreeze_qa_surface_fix")
    source = updated.setdefault("source", {})
    source.setdefault("text_cleanup_decisions", []).extend(replacements)
    flags = set(str(flag) for flag in updated.get("risk_flags", []) if flag)
    flags.add("source_text_surface_fixed_prefreeze_qa")
    flags.update(f"surface_fix:{repl['before']}->{repl['after']}" for repl in replacements)
    updated["risk_flags"] = sorted(flags)
    return updated


def build_text_cleanup_decisions(text_audit: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = []
    for item in text_audit.get("issue_items", []):
        unit_id = item.get("unit_id")
        if unit_id in SURFACE_FIXES:
            decisions.append(
                {
                    "unit_id": unit_id,
                    "original_action": item.get("recommended_actions"),
                    "applied_action": "apply_pdf_verified_surface_fix",
                    "replacements": SURFACE_FIXES[unit_id],
                    "before": item.get("en_quote"),
                }
            )
        elif unit_id in MOVE_DIRECT_TO_REVIEW:
            decisions.append(
                {
                    "unit_id": unit_id,
                    "original_action": item.get("recommended_actions"),
                    "applied_action": "move_direct_to_review",
                    "review_reason": MOVE_DIRECT_TO_REVIEW[unit_id],
                    "before": item.get("en_quote"),
                }
            )
        else:
            decisions.append(
                {
                    "unit_id": unit_id,
                    "original_action": item.get("recommended_actions"),
                    "applied_action": "keep_direct_needs_manual_decision",
                    "before": item.get("en_quote"),
                }
            )
    return decisions


def duplicate_values(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def recompute_audit(payload: dict[str, Any], prefreeze_audit: dict[str, Any]) -> dict[str, Any]:
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
            "prefreeze_qa": prefreeze_audit,
        }
    )
    return audit


def build_report(payload: dict[str, Any], ignored_decisions: list[dict[str, Any]], text_decisions: list[dict[str, Any]]) -> str:
    qa = payload["audit"]["prefreeze_qa"]
    lines = [
        "# v7 Pre-freeze QA Combined Draft",
        "",
        f"Generated at: {payload['generated_at']}",
        "",
        "## Summary",
        "",
        f"- direct items: {len(payload.get('items', []))}",
        f"- review items: {len(payload.get('review_items', []))}",
        f"- parent/context items: {len(payload.get('parent_items', []))}",
        f"- recovered ignored direct items: {qa['recovered_ignored_direct_items']}",
        f"- recovered ignored review items: {qa['recovered_ignored_review_items']}",
        f"- direct surface fixes: {qa['direct_surface_fixes']}",
        f"- direct items moved to review: {qa['direct_items_moved_to_review']}",
        f"- duplicate unit_ids: {len(payload['audit'].get('duplicate_unit_ids', []))}",
        f"- duplicate direct sentence_ids: {len(payload['audit'].get('duplicate_direct_sentence_ids', []))}",
        "",
        "## Ignored Route Decisions",
        "",
    ]
    for action, count in Counter(item["applied_action"] for item in ignored_decisions).most_common():
        lines.append(f"- {action}: {count}")
    lines.extend(["", "### Recovered Direct Examples", ""])
    for item in [d for d in ignored_decisions if d["applied_action"] == "recover_as_direct_list_item"][:12]:
        lines.extend(
            [
                f"- `{item['block_id']}` P{item.get('printed_page')} / pdf {item.get('pdf_page')}: {item.get('cleaned_text')}",
            ]
        )
    lines.extend(["", "### Moved To Review Examples", ""])
    for item in [d for d in ignored_decisions if d["applied_action"] == "move_to_review"][:12]:
        lines.extend(
            [
                f"- `{item['block_id']}` P{item.get('printed_page')} / pdf {item.get('pdf_page')}: {item.get('cleaned_text')} ({item.get('applied_reason')})",
            ]
        )

    lines.extend(["", "## Text Cleanup Decisions", ""])
    for action, count in Counter(item["applied_action"] for item in text_decisions).most_common():
        lines.append(f"- {action}: {count}")
    for item in text_decisions:
        lines.extend(["", f"### {item['unit_id']}", ""])
        lines.append(f"- action: {item['applied_action']}")
        if item["applied_action"] == "apply_pdf_verified_surface_fix":
            for repl in item["replacements"]:
                lines.append(f"- `{repl['before']}` -> `{repl['after']}` ({repl['verification']})")
        if item["applied_action"] == "move_direct_to_review":
            lines.append(f"- reason: {item['review_reason']['reason']}")
        lines.append(f"- before: {compact(str(item.get('before') or ''), 420)}")
    return "\n".join(lines)


def apply_prefreeze_qa(
    combined_file: Path,
    blocks_file: Path,
    ignored_audit_file: Path,
    text_audit_file: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    payload = deepcopy(read_json(combined_file))
    blocks = {block["block_id"]: block for block in read_json(blocks_file)["items"]}
    ignored_audit = read_json(ignored_audit_file)
    text_audit = read_json(text_audit_file)

    ignored_decisions = [
        refine_ignored_decision(decision, blocks.get(decision.get("block_id")))
        for decision in ignored_audit.get("decisions", [])
    ]
    text_decisions = build_text_cleanup_decisions(text_audit)

    recovered_direct: list[dict[str, Any]] = []
    recovered_review: list[dict[str, Any]] = []
    serial = 1
    for decision in ignored_decisions:
        action = decision["applied_action"]
        if action not in {"recover_as_direct_list_item", "move_to_review"}:
            continue
        block = blocks.get(decision.get("block_id"))
        if not block:
            continue
        unit = make_ignored_unit(
            serial=serial,
            decision=decision,
            block=block,
            applied_action=action,
            applied_reason=decision["applied_reason"],
        )
        serial += 1
        if action == "recover_as_direct_list_item":
            recovered_direct.append(unit)
        else:
            recovered_review.append(unit)

    item_by_id = {unit.get("unit_id"): idx for idx, unit in enumerate(payload.get("items", []))}
    moved_to_review: list[dict[str, Any]] = []
    surface_fixed = 0
    for decision in text_decisions:
        unit_id = decision["unit_id"]
        idx = item_by_id.get(unit_id)
        if idx is None:
            continue
        if decision["applied_action"] == "apply_pdf_verified_surface_fix":
            payload["items"][idx] = update_unit_text(payload["items"][idx], decision["replacements"])
            decision["after"] = payload["items"][idx].get("en_quote")
            surface_fixed += 1
        elif decision["applied_action"] == "move_direct_to_review":
            unit = deepcopy(payload["items"][idx])
            unit["evidence_status"] = "needs_review"
            unit["can_be_direct_evidence"] = False
            flags = set(str(flag) for flag in unit.get("risk_flags", []) if flag)
            flags.add("moved_from_direct_to_review_prefreeze_qa")
            flags.add(str(decision["review_reason"]["issue"]))
            flags.add("needs_human_review_before_freeze")
            unit["risk_flags"] = sorted(flags)
            unit.setdefault("source", {}).setdefault("text_cleanup_decisions", []).append(decision["review_reason"])
            moved_to_review.append(unit)

    moved_ids = {unit["unit_id"] for unit in moved_to_review}
    payload["items"] = [unit for unit in payload.get("items", []) if unit.get("unit_id") not in moved_ids]
    payload["items"].extend(recovered_direct)
    payload["review_items"].extend(moved_to_review)
    payload["review_items"].extend(recovered_review)
    payload["generated_at"] = datetime.now().isoformat(timespec="seconds")
    payload["schema_version"] = "v7_units_draft_fullbook_ds_v2_prefreeze_qa_v1"
    payload["status"] = "draft_prefreeze_qa_not_for_downstream_binding"
    payload.setdefault("sources", {})["prefreeze_qa_base_combined"] = str(combined_file.relative_to(BASE_UNITS_DIR))
    payload.setdefault("notes", []).append(
        "Pre-freeze QA layer applied ignored-route recovery and PDF-verified surface text fixes; IDs remain temporary."
    )

    prefreeze_audit = {
        "base_combined": str(combined_file.relative_to(BASE_UNITS_DIR)),
        "ignored_audit": str(ignored_audit_file.relative_to(BASE_UNITS_DIR)),
        "text_audit": str(text_audit_file.relative_to(BASE_UNITS_DIR)),
        "recovered_ignored_direct_items": len(recovered_direct),
        "recovered_ignored_review_items": len(recovered_review),
        "direct_surface_fixes": surface_fixed,
        "direct_items_moved_to_review": len(moved_to_review),
        "ignored_decision_counts": dict(Counter(item["applied_action"] for item in ignored_decisions).most_common()),
        "text_decision_counts": dict(Counter(item["applied_action"] for item in text_decisions).most_common()),
    }
    payload["audit"] = recompute_audit(payload, prefreeze_audit)
    return payload, ignored_decisions, text_decisions, [*recovered_direct, *recovered_review, *moved_to_review]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply reversible pre-freeze QA decisions to the v7 fullbook draft.")
    parser.add_argument("--combined-file", type=Path, default=DEFAULT_COMBINED)
    parser.add_argument("--blocks-file", type=Path, default=DEFAULT_BLOCKS)
    parser.add_argument("--ignored-audit-file", type=Path, default=DEFAULT_IGNORED_AUDIT)
    parser.add_argument("--text-audit-file", type=Path, default=DEFAULT_TEXT_AUDIT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--draft-out-dir", type=Path, default=DRAFT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, ignored_decisions, text_decisions, recovered_units = apply_prefreeze_qa(
        args.combined_file.resolve(),
        args.blocks_file.resolve(),
        args.ignored_audit_file.resolve(),
        args.text_audit_file.resolve(),
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.draft_out_dir.mkdir(parents=True, exist_ok=True)

    out_json = args.draft_out_dir / "v7_units_draft.v2_fullbook_all.prefreeze_qa.json"
    out_audit = args.draft_out_dir / "v7_units_draft.v2_fullbook_all.prefreeze_qa_audit.json"
    out_report = args.draft_out_dir / "v7_units_draft.v2_fullbook_all.prefreeze_qa_report.md"
    ignored_decisions_json = args.out_dir / "ignored_route_decisions.json"
    text_decisions_json = args.out_dir / "text_cleanup_decisions.json"
    recovered_units_json = args.out_dir / "recovered_or_review_units.json"

    write_json(out_json, payload)
    write_json(out_audit, payload["audit"])
    out_report.write_text(build_report(payload, ignored_decisions, text_decisions), encoding="utf-8")
    write_json(ignored_decisions_json, ignored_decisions)
    write_json(text_decisions_json, text_decisions)
    write_json(recovered_units_json, recovered_units)

    qa = payload["audit"]["prefreeze_qa"]
    print(f"direct items: {len(payload['items'])}")
    print(f"review items: {len(payload['review_items'])}")
    print(f"parent/context items: {len(payload['parent_items'])}")
    print(f"recovered ignored direct items: {qa['recovered_ignored_direct_items']}")
    print(f"recovered ignored review items: {qa['recovered_ignored_review_items']}")
    print(f"direct surface fixes: {qa['direct_surface_fixes']}")
    print(f"direct items moved to review: {qa['direct_items_moved_to_review']}")
    print(f"duplicate unit_ids: {len(payload['audit']['duplicate_unit_ids'])}")
    print(f"duplicate direct sentence_ids: {len(payload['audit']['duplicate_direct_sentence_ids'])}")
    print(f"wrote: {out_json}")
    print(f"wrote: {out_report}")
    print(f"wrote: {ignored_decisions_json}")
    print(f"wrote: {text_decisions_json}")


if __name__ == "__main__":
    main()
