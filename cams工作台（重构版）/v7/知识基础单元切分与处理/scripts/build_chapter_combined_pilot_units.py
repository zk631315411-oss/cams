from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DRY_RUN_DIR = BASE_UNITS_DIR / "fullbook_dry_run"
DRAFT_DIR = BASE_UNITS_DIR / "draft"
CONTEXT_DEPENDENT_START_RE = re.compile(r"^\s*(they|these|this|those|such|their)\b", re.IGNORECASE)
ENCODING_ARTIFACT_RE = re.compile(r"鈥|濃|�|锛|銆")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clean_list_text(text: str) -> str:
    text = re.sub(r"^\s*[•*\-]\s*", "", text).strip()
    text = re.sub(r"^o\s+", "", text).strip()
    return text


def compact(text: str, limit: int = 320) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def chapter_of(row: dict) -> str | None:
    heading = row.get("heading_context") or row.get("heading_stack") or []
    return heading[0] if heading else None


def block_num(block_id: str | None) -> int | None:
    match = re.search(r"b(\d+)", str(block_id or ""))
    return int(match.group(1)) if match else None


def is_label_only_list_item(text: str) -> bool:
    clean = clean_list_text(text)
    if not clean.endswith(":"):
        return False
    words = re.findall(r"[A-Za-z0-9/]+", clean)
    return len(words) <= 12


def is_question_like_list_item(text: str) -> bool:
    clean = clean_list_text(text)
    if "?" in clean:
        return True
    return bool(re.match(r"^\s*(what|how|when|where|why|which|who|does|do|can|is|are)\b", clean, re.IGNORECASE))


def infer_direct_list_unit_type(text: str, heading_context: list[str], parent_text: str | None = None) -> str:
    text_l = text.lower()
    heading_l = " / ".join(heading_context).lower()
    parent_l = (parent_text or "").lower()
    if is_question_like_list_item(text):
        return "rule"
    if "should" in parent_l or parent_l.rstrip().endswith("should:"):
        return "obligation"
    if "red flag" in heading_l or "indicator" in text_l or "suspicious" in text_l:
        return "risk_indicator"
    if "might indicate risk" in text_l or "high-risk" in text_l or "unusual" in text_l:
        return "risk_indicator"
    if text_l.startswith(("enhance ", "strengthen ", "monitor ", "review ", "train ", "conduct ", "verify ")):
        return "obligation"
    if "should" in heading_l or text_l.startswith(("must ", "should ")):
        return "obligation"
    return "fact"


def type_for_unit_type(unit_type: str) -> str:
    return {
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
        "list_parent": "classification",
        "list_label": "context",
        "table_cell": "fact",
    }.get(unit_type, "context")


def deterministic_risk_flags(en_quote: str) -> list[str]:
    flags = []
    if CONTEXT_DEPENDENT_START_RE.search(en_quote):
        flags.append("antecedent_requires_prior_context")
    if ENCODING_ARTIFACT_RE.search(en_quote):
        flags.append("possible_encoding_artifact")
    return flags


def build_rule_unit(block: dict, route_row: dict, serial: int, slug: str, parent_row: dict | None = None) -> dict:
    text = str(block.get("text", ""))
    heading_context = block.get("heading_stack") or route_row.get("heading_context") or []
    route = route_row.get("route")
    clean = clean_list_text(text)
    parent_text = str(parent_row.get("text_head", "")) if parent_row else None

    if route == "direct_list_parent_candidate":
        unit_type = "list_parent"
        evidence_status = "structural_context"
        can_be_direct = False
        en_quote = text.strip()
        knowledge_en = clean.rstrip(":")
        risk_flags = ["structural_list_parent_not_direct_evidence", "zh_subspan_unavailable"]
    elif route == "direct_list_item_candidate" and is_label_only_list_item(text):
        unit_type = "list_label"
        evidence_status = "structural_context"
        can_be_direct = False
        en_quote = clean
        knowledge_en = clean.rstrip(":")
        risk_flags = ["list_label_only_not_direct_evidence", "zh_subspan_unavailable"]
    else:
        unit_type = infer_direct_list_unit_type(clean, heading_context, parent_text)
        evidence_status = "direct"
        can_be_direct = True
        en_quote = clean
        knowledge_en = clean.rstrip(".")
        risk_flags = ["derived_from_rule_list_block", "synthetic_sentence_id_from_list_block", "zh_subspan_unavailable"]
        if is_question_like_list_item(clean):
            risk_flags.append("question_list_item_checklist")

    unit_id = f"v7u_tmp_pilot_{slug}_rule_N{serial:06d}"
    sentence_id = f"{block.get('block_id')}_list_block"
    return {
        "unit_id": unit_id,
        "unit_status": "draft",
        "pilot_slug": slug,
        "chapter": chapter_of({"heading_context": heading_context}),
        "unit_type": unit_type,
        "type": type_for_unit_type(unit_type),
        "evidence_status": evidence_status,
        "can_be_direct_evidence": can_be_direct,
        "en_quote": en_quote,
        "en_sentence_ids": [] if not can_be_direct else [sentence_id],
        "en_sentences": [
            {
                "sentence_id": sentence_id,
                "text": en_quote,
                "role": "retrieval_slice",
                "parent_unit_id": unit_id,
            }
        ]
        if can_be_direct
        else [],
        "knowledge_en": knowledge_en,
        "knowledge_zh": None,
        "zh_display_text": None,
        "zh_display_mode": "knowledge_zh_pending",
        "zh_context_full": None,
        "zh_search_text": None,
        "zh_search_text_status": "not_available",
        "terms": [],
        "pdf_page": block.get("pdf_page"),
        "printed_page": block.get("printed_page"),
        "printed_page_span": [block.get("printed_page")] if block.get("printed_page") else [],
        "page_span": [block.get("pdf_page")] if isinstance(block.get("pdf_page"), int) else [],
        "heading_context": heading_context,
        "source": {
            "en_block_id": block.get("block_id"),
            "route": route,
            "list_parent_block_id": parent_row.get("block_id") if parent_row else None,
            "list_parent_text": parent_text,
            "materialization_method": "chapter_rule_list_pilot_v1",
        },
        "decision_reason": route_row.get("reason"),
        "risk_flags": sorted(set([*risk_flags, *route_row.get("risk_flags", []), *deterministic_risk_flags(en_quote)])),
    }


def build_rule_units(
    chapter: str,
    slug: str,
    allowed_printed_pages: set[str] | None = None,
    allowed_block_span: tuple[int, int] | None = None,
) -> tuple[list[dict], list[dict], dict]:
    dry_run = read_json(DRY_RUN_DIR / "v7_fullbook_routing_dry_run.json")["items"]
    blocks = read_json(BASE_UNITS_DIR / "patched" / "v7_en_blocks.patched.json")["items"]
    blocks_by_id = {block["block_id"]: block for block in blocks}
    chapter_rows = [row for row in dry_run if chapter_of(row) == chapter]
    scoped_chapter_rows = [
        row
        for row in chapter_rows
        if (allowed_printed_pages is None or str(row.get("printed_page")) in allowed_printed_pages)
        and (
            allowed_block_span is None
            or (
                block_num(row.get("block_id")) is not None
                and allowed_block_span[0] <= block_num(row.get("block_id")) <= allowed_block_span[1]
            )
        )
    ]
    direct_route_rows = [row for row in scoped_chapter_rows if row.get("evidence_status") == "direct_candidate"]

    direct_units: list[dict] = []
    parent_items: list[dict] = []
    serial = 1
    current_parent_row: dict | None = None
    for row in direct_route_rows:
        block = blocks_by_id.get(row.get("block_id"))
        if not block:
            continue
        if current_parent_row and row.get("heading_context") != current_parent_row.get("heading_context"):
            current_parent_row = None
        parent_for_unit = None if row.get("route") == "direct_list_parent_candidate" else current_parent_row
        unit = build_rule_unit(block, row, serial, slug, parent_for_unit)
        serial += 1
        if row.get("route") == "direct_list_parent_candidate":
            current_parent_row = row
        if unit.get("evidence_status") == "direct":
            direct_units.append(unit)
        else:
            parent_items.append(unit)

    route_counts = Counter(row.get("route") for row in chapter_rows)
    scoped_route_counts = Counter(row.get("route") for row in scoped_chapter_rows)
    return direct_units, parent_items, {
        "chapter_rows": len(chapter_rows),
        "chapter_route_counts": dict(route_counts),
        "scoped_chapter_rows": len(scoped_chapter_rows),
        "scoped_chapter_route_counts": dict(scoped_route_counts),
        "allowed_printed_pages": sorted(allowed_printed_pages) if allowed_printed_pages is not None else None,
        "allowed_block_span": list(allowed_block_span) if allowed_block_span is not None else None,
        "direct_candidate_rows": len(direct_route_rows),
        "rule_direct_units": len(direct_units),
        "rule_parent_items": len(parent_items),
    }


def validate_payload(payload: dict) -> dict:
    issues = []
    all_units = [*payload["items"], *payload["review_items"], *payload["parent_items"]]
    unit_ids = [unit.get("unit_id") for unit in all_units]
    duplicates = [unit_id for unit_id, count in Counter(unit_ids).items() if count > 1]
    if duplicates:
        issues.append({"issue": "duplicate_unit_ids", "unit_ids": duplicates})

    for unit in payload["items"]:
        if unit.get("evidence_status") != "direct":
            issues.append({"issue": "non_direct_unit_in_items", "unit_id": unit.get("unit_id")})
        if not unit.get("can_be_direct_evidence"):
            issues.append({"issue": "direct_item_not_marked_direct_evidence", "unit_id": unit.get("unit_id")})
        if not str(unit.get("en_quote") or "").strip():
            issues.append({"issue": "direct_item_empty_en_quote", "unit_id": unit.get("unit_id")})
        if unit.get("zh_search_text"):
            issues.append({"issue": "zh_search_text_should_be_empty_in_pilot", "unit_id": unit.get("unit_id")})

    for unit in payload["parent_items"]:
        if unit.get("can_be_direct_evidence"):
            issues.append({"issue": "parent_item_marked_direct_evidence", "unit_id": unit.get("unit_id")})

    return {
        "direct_units": len(payload["items"]),
        "review_items": len(payload["review_items"]),
        "parent_items": len(payload["parent_items"]),
        "issues": issues,
    }


def llm_printed_pages(llm_payload: dict) -> set[str]:
    pages = set()
    for unit in [*llm_payload.get("items", []), *llm_payload.get("review_items", [])]:
        page = unit.get("printed_page")
        if page is not None:
            pages.add(str(page))
    return pages


def llm_block_span(llm_payload: dict) -> tuple[int, int] | None:
    nums = []
    for unit in [*llm_payload.get("items", []), *llm_payload.get("review_items", [])]:
        source = unit.get("source") or {}
        num = block_num(source.get("en_block_id"))
        if num is not None:
            nums.append(num)
    return (min(nums), max(nums)) if nums else None


def build_payload(
    chapter: str,
    slug: str,
    llm_pilot_file: Path,
    scope_from_llm_pages: bool = False,
    scope_from_llm_block_span: bool = False,
) -> dict:
    llm_payload = read_json(llm_pilot_file)
    allowed_printed_pages = llm_printed_pages(llm_payload) if scope_from_llm_pages else None
    allowed_block_span = llm_block_span(llm_payload) if scope_from_llm_block_span else None
    rule_direct, parent_items, rule_audit = build_rule_units(chapter, slug, allowed_printed_pages, allowed_block_span)
    llm_items = llm_payload.get("items", [])
    llm_review = llm_payload.get("review_items", [])

    payload = {
        "schema_version": "v7_units_draft_chapter_combined_pilot_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "draft_chapter_combined_pilot_not_for_downstream_binding",
        "chapter": chapter,
        "pilot_slug": slug,
        "sources": {
            "llm_pilot": str(llm_pilot_file.relative_to(BASE_UNITS_DIR)),
            "routing_dry_run": "fullbook_dry_run/v7_fullbook_routing_dry_run.json",
            "patched_blocks": "patched/v7_en_blocks.patched.json",
        },
        "notes": [
            "items contains direct LLM leaf units plus complete direct rule/list units.",
            "parent_items contains structural list parents and label-only list bullets; they are not direct evidence.",
            "review_items contains LLM needs_review outputs and should not enter downstream binding.",
            "If scope_from_llm_pages is true, rule/list units are limited to the printed pages present in the LLM pilot.",
            "If scope_from_llm_block_span is true, rule/list units are limited to the source block_id span present in the LLM pilot.",
            "No v7u_N IDs are frozen by this pilot.",
        ],
        "items": [*llm_items, *rule_direct],
        "review_items": llm_review,
        "parent_items": parent_items,
        "audit": {
            "llm_direct_units": len(llm_items),
            "llm_review_items": len(llm_review),
            **rule_audit,
        },
    }
    payload["audit"].update(validate_payload(payload))
    return payload


def build_report(payload: dict) -> str:
    items = payload["items"]
    review_items = payload["review_items"]
    parent_items = payload["parent_items"]
    by_type = Counter(unit.get("unit_type") for unit in items)
    by_method = Counter(unit.get("source", {}).get("materialization_method") for unit in items)
    by_parent_type = Counter(unit.get("unit_type") for unit in parent_items)
    lines = [
        f"# v7 Chapter Combined Pilot: {payload['chapter']}",
        "",
        f"Generated at: {payload['generated_at']}",
        "",
        "## Summary",
        "",
        f"- direct units: {len(items)}",
        f"- review items: {len(review_items)}",
        f"- parent/context items: {len(parent_items)}",
        f"- by direct unit_type: {json.dumps(dict(by_type), ensure_ascii=False)}",
        f"- by direct materialization_method: {json.dumps(dict(by_method), ensure_ascii=False)}",
        f"- by parent/context unit_type: {json.dumps(dict(by_parent_type), ensure_ascii=False)}",
        f"- chapter routes: {json.dumps(payload['audit'].get('chapter_route_counts', {}), ensure_ascii=False)}",
        f"- audit issues: {len(payload['audit'].get('issues', []))}",
        "",
        "## Direct Rule/List Units",
        "",
    ]
    for unit in [u for u in items if u.get("source", {}).get("materialization_method") == "chapter_rule_list_pilot_v1"]:
        lines.extend(
            [
                f"### {unit['unit_id']} · {unit['unit_type']}",
                "",
                f"- page: {unit.get('printed_page')} / pdf {unit.get('pdf_page')}",
                f"- heading: {' / '.join(unit.get('heading_context', []))}",
                f"- en_quote: {unit.get('en_quote')}",
                f"- risk_flags: {json.dumps(unit.get('risk_flags', []), ensure_ascii=False)}",
                "",
            ]
        )

    lines.extend(["## Direct LLM Examples", ""])
    for unit in [u for u in items if u.get("source", {}).get("materialization_method") == "fullbook_llm_sentence_grouping_pilot_v1"][:20]:
        lines.extend(
            [
                f"### {unit['unit_id']} · {unit['unit_type']}",
                "",
                f"- page: {unit.get('printed_page')} / pdf {unit.get('pdf_page')}",
                f"- knowledge_en: {unit.get('knowledge_en')}",
                f"- en_quote: {compact(str(unit.get('en_quote', '')), 500)}",
                "",
            ]
        )

    if parent_items:
        lines.extend(["## Parent / Context Items", ""])
        for unit in parent_items:
            lines.extend(
                [
                    f"### {unit['unit_id']} · {unit['unit_type']} · {unit['evidence_status']}",
                    "",
                    f"- page: {unit.get('printed_page')} / pdf {unit.get('pdf_page')}",
                    f"- heading: {' / '.join(unit.get('heading_context', []))}",
                    f"- en_quote: {unit.get('en_quote')}",
                    f"- risk_flags: {json.dumps(unit.get('risk_flags', []), ensure_ascii=False)}",
                    "",
                ]
            )

    if review_items:
        lines.extend(["## Review Items", ""])
        for unit in review_items:
            lines.extend(
                [
                    f"### {unit['unit_id']} · {unit.get('unit_type')} · {unit.get('evidence_status')}",
                    "",
                    f"- page: {unit.get('printed_page')} / pdf {unit.get('pdf_page')}",
                    f"- knowledge_en: {unit.get('knowledge_en')}",
                    f"- en_quote: {unit.get('en_quote')}",
                    f"- risk_flags: {json.dumps(unit.get('risk_flags', []), ensure_ascii=False)}",
                    "",
                ]
            )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--llm-pilot-file", required=True, type=Path)
    parser.add_argument("--out-dir", type=Path, default=DRAFT_DIR)
    parser.add_argument("--scope-from-llm-pages", action="store_true")
    parser.add_argument("--scope-from-llm-block-span", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    llm_pilot_file = args.llm_pilot_file.resolve()
    payload = build_payload(
        args.chapter,
        args.slug,
        llm_pilot_file,
        args.scope_from_llm_pages,
        args.scope_from_llm_block_span,
    )
    out_json = args.out_dir / f"v7_units_draft.pilot_{args.slug}.combined.json"
    out_report = args.out_dir / f"v7_units_draft.pilot_{args.slug}.combined_report.md"
    out_audit = args.out_dir / f"v7_units_draft.pilot_{args.slug}.combined_audit.json"
    write_json(out_json, payload)
    out_report.write_text(build_report(payload), encoding="utf-8")
    write_json(out_audit, payload["audit"])
    print(f"direct units: {len(payload['items'])}")
    print(f"review items: {len(payload['review_items'])}")
    print(f"parent/context items: {len(payload['parent_items'])}")
    print(f"audit issues: {len(payload['audit'].get('issues', []))}")
    print(f"wrote: {out_json}")
    print(f"wrote: {out_report}")
    print(f"wrote: {out_audit}")


if __name__ == "__main__":
    main()
