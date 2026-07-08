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
BATCH_DIR = BASE_UNITS_DIR / "llm_batches"
DRAFT_DIR = BASE_UNITS_DIR / "draft"

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

ALLOWED_UNIT_TYPES = set(TYPE_MAP)
MAX_DIRECT_SENTENCES = 3
CONTEXT_DEPENDENT_START_RE = re.compile(r"^\s*(they|these|this|those|such|their)\b", re.IGNORECASE)
ENCODING_ARTIFACT_RE = re.compile(r"鈥攑|鈥攃|鈥|濃|�|锛|銆|锟|閳|婵|閿|泑|閵")
MARKUP_ARTIFACT_RE = re.compile(r"<\s*/?\s*(sub|sup|span|p|br|div)\b|<[^>]+>", re.IGNORECASE)
DAMAGED_REFERENCE_RE = re.compile(r"\bIn its\s*,", re.IGNORECASE)
RESIDUAL_SUB_BULLET_RE = re.compile(r"^\s*<\s*sub\s*>\s*o\s+", re.IGNORECASE)
ANGLE_PLACEHOLDER_RE = re.compile(r"<([^<>]{1,80})>")
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
FALSE_ARTIFACT_REVIEW_FLAGS = {
    "encoding_artifact",
    "encoding_mojibake",
    "mojibake",
    "mojibake_text",
    "text_corruption_mojibake",
    "invalid_source_json",
    "source_json_malformed",
}
NON_PROMOTABLE_REVIEW_FLAGS = {
    "teaching_metadata_check",
    "possible_typo_or_ocr_error",
    "possible_ocr_error",
    "ocr_error",
    "source_text_typo",
    "typo_or_ocr_error",
    "residual_markup",
    "html_markup_residue",
    "incomplete_sentence_fragment",
    "cross_block_join_unreviewed",
    "damaged_extraction",
    "damaged_publication_reference",
    "unreliable_extraction",
}


def unique_in_order(values: list) -> list:
    seen = set()
    out = []
    for value in values:
        if value is None or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def request_lookup(batch_rows: list[dict]) -> dict[str, dict]:
    return {str(row.get("request_id")): row for row in batch_rows if row.get("request_id")}


def sentence_lookup(row: dict) -> dict[str, dict]:
    sentences = row.get("payload", {}).get("window", {}).get("sentences", [])
    return {str(item.get("sentence_id")): item for item in sentences if item.get("sentence_id")}


def sentence_ids_in_window_order(row: dict, requested_ids: list[str]) -> list[str]:
    wanted = set(requested_ids)
    ordered = [
        str(item.get("sentence_id"))
        for item in row.get("payload", {}).get("window", {}).get("sentences", [])
        if item.get("sentence_id") in wanted
    ]
    return ordered


def has_terminal_punctuation(text: str) -> bool:
    return text.strip().rstrip("\"')]}”’」』》").endswith((".", "!", "?", ";", ":"))


def is_numbered_definition_item(text: str) -> bool:
    return bool(re.match(r"^\s*\d+\.\s*[^:]{2,80}:\s+\S", text.strip()))


def group_source_text(row: dict, ordered_ids: list[str]) -> str:
    sentence_by_id = sentence_lookup(row)
    return " ".join(clean_extracted_text(str(sentence_by_id[sid].get("text", "")))[0] for sid in ordered_ids if sid in sentence_by_id)


def group_raw_source_text(row: dict, ordered_ids: list[str]) -> str:
    sentence_by_id = sentence_lookup(row)
    return " ".join(str(sentence_by_id[sid].get("text", "")).strip() for sid in ordered_ids if sid in sentence_by_id)


def is_plain_angle_placeholder(inner: str) -> bool:
    value = inner.strip()
    if not value or value.startswith("/") or "=" in value:
        return False
    if value.lower() in HTML_TAG_NAMES:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 /_.-]{0,78}", value))


def text_for_artifact_scan(text: str) -> str:
    def replace_placeholder(match: re.Match) -> str:
        inner = match.group(1)
        return "" if is_plain_angle_placeholder(inner) else match.group(0)

    text = RESIDUAL_SUB_BULLET_RE.sub("", text)
    return ANGLE_PLACEHOLDER_RE.sub(replace_placeholder, text)


def clean_extracted_text(text: str) -> tuple[str, list[str]]:
    flags: list[str] = []
    cleaned = text.strip()
    if RESIDUAL_SUB_BULLET_RE.search(cleaned):
        cleaned = RESIDUAL_SUB_BULLET_RE.sub("", cleaned).strip()
        flags.append("cleaned_residual_sub_bullet_marker")
    if ANGLE_PLACEHOLDER_RE.search(cleaned):
        placeholders = [
            match.group(1).strip()
            for match in ANGLE_PLACEHOLDER_RE.finditer(cleaned)
            if is_plain_angle_placeholder(match.group(1))
        ]
        if placeholders:
            flags.append("allowed_angle_placeholder")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned, flags


def source_text_cleaning_flags(row: dict, ordered_ids: list[str]) -> list[str]:
    sentence_by_id = sentence_lookup(row)
    flags: list[str] = []
    for sid in ordered_ids:
        if sid not in sentence_by_id:
            continue
        _, sentence_flags = clean_extracted_text(str(sentence_by_id[sid].get("text", "")))
        flags.extend(sentence_flags)
    return sorted(set(flags))


def has_real_text_artifact(text: str) -> bool:
    scan_text = text_for_artifact_scan(text)
    return bool(ENCODING_ARTIFACT_RE.search(scan_text) or MARKUP_ARTIFACT_RE.search(scan_text))


def can_promote_false_artifact_review(group: dict, validation_errors: list[str], too_broad: bool, source_text: str) -> bool:
    if group.get("unit_type") != "needs_review":
        return False
    if validation_errors or too_broad:
        return False
    risk_flags = set(group.get("risk_flags", []))
    if not risk_flags:
        return False
    if risk_flags & NON_PROMOTABLE_REVIEW_FLAGS:
        return False
    if not (risk_flags & FALSE_ARTIFACT_REVIEW_FLAGS):
        return False
    return not has_real_text_artifact(source_text)


def is_citable_cleaned_sub_bullet(cleaned_text: str) -> bool:
    if len(cleaned_text) < 12:
        return False
    if not re.search(r"[A-Za-z]", cleaned_text):
        return False
    return has_terminal_punctuation(cleaned_text)


def can_promote_cleaned_sub_bullet_review(
    group: dict,
    validation_errors: list[str],
    too_broad: bool,
    raw_source_text: str,
    cleaned_source_text: str,
) -> bool:
    if group.get("unit_type") != "needs_review":
        return False
    if validation_errors or too_broad:
        return False
    if not RESIDUAL_SUB_BULLET_RE.search(raw_source_text):
        return False
    if not is_citable_cleaned_sub_bullet(cleaned_source_text):
        return False
    risk_flags = set(group.get("risk_flags", []))
    return not (risk_flags & NON_PROMOTABLE_REVIEW_FLAGS)


def infer_promoted_review_unit_type(en_quote: str, knowledge_hint_en: str | None, row: dict) -> str:
    text_l = en_quote.lower()
    hint_l = str(knowledge_hint_en or "").lower()
    heading_l = " / ".join(row.get("payload", {}).get("heading_stack", [])).lower()
    case_markers = ("case example", "komarov", "redstar", "volkof", "sophie", "fulltechglobal", "marco")
    if is_numbered_definition_item(en_quote):
        return "definition"
    if "definition" in hint_l or re.match(r"^[A-Z][A-Za-z0-9 /&()'’.-]{1,80}\s+(is|are|means|refers to)\b", en_quote):
        return "definition"
    if any(marker in heading_l or marker in text_l or marker in hint_l for marker in case_markers):
        return "case_fact"
    if text_l.startswith("for example"):
        return "example"
    if "include" in text_l or "types" in text_l or "forms" in text_l or "categories" in hint_l or "classification" in hint_l:
        return "classification"
    if "should" in text_l or "must" in text_l or "required" in text_l:
        return "obligation"
    if "red flag" in text_l or "suspicious" in text_l or "vulnerable" in text_l or "risk" in hint_l:
        return "risk_indicator"
    return "fact"


def source_label(en_quote: str, limit: int = 120) -> str:
    label = re.sub(r"\s+", " ", en_quote).strip().rstrip(".")
    return label[:limit] + ("..." if len(label) > limit else "")


def sanitize_promoted_knowledge_hint(knowledge_hint_en: str | None, en_quote: str) -> str:
    hint = str(knowledge_hint_en or "").strip()
    if not hint:
        return source_label(en_quote)
    hint_l = hint.lower()
    if any(
        token in hint_l
        for token in (
            "corrupted",
            "corruption",
            "damaged",
            "mojibake",
            "encoding",
            "malformed source",
            "source sentence",
            "fragment",
            "metadata",
            "incomplete",
            "continuation",
        )
    ):
        return source_label(en_quote)
    return hint


def normalize_group(group: dict) -> dict:
    unit_type = str(group.get("unit_type") or "fact").strip()
    if unit_type not in ALLOWED_UNIT_TYPES:
        unit_type = "needs_review"
    return {
        "sentence_ids": [str(sid) for sid in group.get("sentence_ids", []) if sid],
        "unit_type": unit_type,
        "knowledge_hint_en": group.get("knowledge_hint_en"),
        "reason": group.get("reason"),
        "risk_flags": sorted(set(str(flag) for flag in group.get("risk_flags", []) if flag)),
    }


def deterministic_risk_flags(en_quote: str) -> list[str]:
    flags = []
    if CONTEXT_DEPENDENT_START_RE.search(en_quote):
        flags.append("antecedent_requires_prior_context")
    if ENCODING_ARTIFACT_RE.search(en_quote):
        flags.append("possible_encoding_artifact")
    if DAMAGED_REFERENCE_RE.search(en_quote):
        flags.append("damaged_publication_reference")
    return flags


def is_reviewed_join_sentence(sentence: dict) -> bool:
    repair_flags = set(str(flag) for flag in sentence.get("repair_flags", []) if flag)
    sentence_id = str(sentence.get("sentence_id") or "")
    return sentence_id.startswith("v7en_join_") or "cross_block_sentence_join_reviewed" in repair_flags


def group_validation_errors(group: dict, row: dict) -> list[str]:
    lookup = sentence_lookup(row)
    sentence_ids = group["sentence_ids"]
    ordered_ids = sentence_ids_in_window_order(row, sentence_ids)
    window_ids = [
        str(item.get("sentence_id"))
        for item in row.get("payload", {}).get("window", {}).get("sentences", [])
        if item.get("sentence_id")
    ]
    block_risk_flags = set(row.get("payload", {}).get("block_risk_flags", []))
    errors = []
    if not sentence_ids:
        errors.append("empty_sentence_ids")
    unknown = [sid for sid in sentence_ids if sid not in lookup]
    if unknown:
        errors.append("unknown_sentence_ids:" + ",".join(unknown))
    if len(sentence_ids) != len(set(sentence_ids)):
        errors.append("duplicate_sentence_ids_in_group")
    if ordered_ids:
        first_id = window_ids[0] if window_ids else None
        last_id = window_ids[-1] if window_ids else None
        sentence_by_id = lookup
        reviewed_join_group = any(is_reviewed_join_sentence(sentence_by_id.get(sid, {})) for sid in ordered_ids)
        if (
            ordered_ids[0] == first_id
            and not reviewed_join_group
            and {"previous_block_may_continue_here", "paragraph_continues_across_page_candidate"} & block_risk_flags
        ):
            errors.append("source_sentence_may_continue_from_previous_block")
        if (
            ordered_ids[-1] == last_id
            and not reviewed_join_group
            and {"block_may_continue_next", "cross_block_sentence_candidate"} & block_risk_flags
        ):
            errors.append("source_sentence_may_continue_next_block")
        group_text = " ".join(clean_extracted_text(str(sentence_by_id[sid].get("text", "")))[0] for sid in ordered_ids if sid in sentence_by_id)
        if group_text and has_real_text_artifact(group_text):
            errors.append("source_text_contains_artifact")
        if group_text and not has_terminal_punctuation(group_text):
            errors.append("source_text_lacks_terminal_punctuation")
        if (
            "list_item_without_terminal_punctuation" in set(group.get("risk_flags", []))
            and group_text
            and is_numbered_definition_item(group_text)
        ):
            errors = [
                error
                for error in errors
                if error not in {"source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation"}
            ]
    return errors


def build_unit(
    *,
    serial: int,
    slug: str,
    row: dict,
    decision_idx: int,
    group_idx: int,
    group: dict,
    evidence_status: str,
    validation_errors: list[str],
    window_risk_flags: list[str],
    decisions_file: Path,
    batch_file: Path,
) -> dict:
    sentence_by_id = sentence_lookup(row)
    ordered_ids = sentence_ids_in_window_order(row, group["sentence_ids"])
    sentence_items = [sentence_by_id[sid] for sid in ordered_ids if sid in sentence_by_id]
    cleaned_sentence_items = []
    cleaning_flags: list[str] = []
    for item in sentence_items:
        cleaned_text, sentence_flags = clean_extracted_text(str(item.get("text", "")))
        cleaned_item = dict(item)
        cleaned_item["text"] = cleaned_text
        if sentence_flags:
            cleaned_item["source_text_cleaning_flags"] = sentence_flags
        cleaned_sentence_items.append(cleaned_item)
        cleaning_flags.extend(sentence_flags)
    en_quote = " ".join(str(item.get("text", "")).strip() for item in cleaned_sentence_items).strip()
    unit_id = f"v7u_tmp_pilot_{slug}_N{serial:06d}"
    payload = row.get("payload", {})
    fallback_pdf_page = row.get("pdf_page") or payload.get("pdf_page")
    fallback_printed_page = row.get("printed_page") or payload.get("printed_page")
    page_span = unique_in_order(
        [
            page
            for item in sentence_items
            for page in (item.get("page_span") or [item.get("pdf_page") or fallback_pdf_page])
            if isinstance(page, int)
        ]
    )
    if not page_span and isinstance(fallback_pdf_page, int):
        page_span = [fallback_pdf_page]
    printed_page_span = unique_in_order(
        [
            page
            for item in sentence_items
            for page in (item.get("printed_page_span") or [item.get("printed_page") or fallback_printed_page])
            if page is not None
        ]
    )
    if not printed_page_span and fallback_printed_page:
        printed_page_span = [fallback_printed_page]

    risk_flags = set(group.get("risk_flags", []))
    risk_flags.update(payload.get("block_risk_flags", []))
    risk_flags.update(deterministic_risk_flags(en_quote))
    risk_flags.update(cleaning_flags)
    risk_flags.update(validation_errors)
    risk_flags.add("zh_subspan_unavailable")
    risk_flags.add("derived_from_fullbook_llm_grouping")
    if len(ordered_ids) > MAX_DIRECT_SENTENCES:
        risk_flags.add("llm_group_too_broad_needs_review")

    return {
        "unit_id": unit_id,
        "unit_status": "draft",
        "pilot_slug": slug,
        "chapter": row.get("chapter"),
        "unit_type": group["unit_type"],
        "type": TYPE_MAP.get(group["unit_type"], "fact"),
        "evidence_status": evidence_status,
        "can_be_direct_evidence": evidence_status == "direct",
        "en_quote": en_quote,
        "en_sentence_ids": ordered_ids,
        "en_sentences": [
            {
                "sentence_id": item.get("sentence_id"),
                "text": item.get("text"),
                "role": "retrieval_slice",
                "parent_unit_id": unit_id,
            }
            for item in cleaned_sentence_items
        ],
        "knowledge_en": group.get("knowledge_hint_en"),
        "knowledge_zh": None,
        "zh_display_text": None,
        "zh_display_mode": "knowledge_zh_pending",
        "zh_context_full": None,
        "zh_search_text": None,
        "zh_search_text_status": "not_available",
        "terms": [],
        "pdf_page": page_span[0] if page_span else fallback_pdf_page,
        "printed_page": printed_page_span[0] if printed_page_span else fallback_printed_page,
        "printed_page_span": printed_page_span,
        "page_span": page_span,
        "heading_context": payload.get("heading_stack", []),
        "source": {
            "en_block_id": row.get("block_id") or payload.get("block_id"),
            "materialization_method": "fullbook_llm_sentence_grouping_pilot_v1",
            "decision_ids": [f"pilot_fullbook_llm:{decision_idx}:{group_idx}"],
            "request_id": row.get("request_id"),
            "batch_file": str(batch_file.relative_to(BASE_UNITS_DIR)),
            "decisions_file": str(decisions_file.relative_to(BASE_UNITS_DIR)),
            "route_reason": payload.get("route_reason"),
            "window_risk_flags": window_risk_flags,
            "source_text_cleaning_flags": sorted(set(cleaning_flags)),
        },
        "decision_reason": group.get("reason"),
        "risk_flags": sorted(flag for flag in risk_flags if flag),
    }


def materialize(batch_rows: list[dict], decisions: list[dict], decisions_file: Path, batch_file: Path, slug: str) -> dict:
    requests = request_lookup(batch_rows)
    direct_units = []
    review_items = []
    audit_items = []
    seen_groups = set()
    serial = 1

    for decision_idx, decision in enumerate(decisions, start=1):
        request_id = str(decision.get("request_id") or "")
        row = requests.get(request_id)
        if not row:
            audit_items.append({"request_id": request_id, "issue": "decision_without_matching_request"})
            continue

        window_risk_flags = [str(flag) for flag in decision.get("window_risk_flags", []) if flag]
        covered_sentence_ids: set[str] = set()
        for group_idx, raw_group in enumerate(decision.get("sentence_groups", []), start=1):
            group = normalize_group(raw_group)
            errors = group_validation_errors(group, row)
            ordered_ids = sentence_ids_in_window_order(row, group["sentence_ids"])
            covered_sentence_ids.update(ordered_ids)
            group_key = (request_id, tuple(ordered_ids))
            if group_key in seen_groups:
                errors.append("duplicate_group_in_request")
            seen_groups.add(group_key)

            too_broad = len(ordered_ids) > MAX_DIRECT_SENTENCES
            raw_source_text = group_raw_source_text(row, ordered_ids)
            source_text = group_source_text(row, ordered_ids)
            promoted_review = can_promote_false_artifact_review(group, errors, too_broad, source_text)
            promoted_cleaned_sub_bullet = can_promote_cleaned_sub_bullet_review(
                group,
                errors,
                too_broad,
                raw_source_text,
                source_text,
            )
            if promoted_review or promoted_cleaned_sub_bullet:
                group["unit_type"] = infer_promoted_review_unit_type(source_text, group.get("knowledge_hint_en"), row)
                group["knowledge_hint_en"] = sanitize_promoted_knowledge_hint(group.get("knowledge_hint_en"), source_text)
                group["risk_flags"] = sorted(
                    flag
                    for flag in set(group.get("risk_flags", []))
                    if flag not in FALSE_ARTIFACT_REVIEW_FLAGS
                )
                if promoted_review:
                    group["risk_flags"].append("promoted_from_false_artifact_review")
                if promoted_cleaned_sub_bullet:
                    group["risk_flags"].append("promoted_from_cleaned_residual_sub_bullet")
            needs_review = bool(errors) or too_broad or group["unit_type"] == "needs_review"
            evidence_status = "needs_review" if needs_review else "direct"
            unit = build_unit(
                serial=serial,
                slug=slug,
                row=row,
                decision_idx=decision_idx,
                group_idx=group_idx,
                group=group,
                evidence_status=evidence_status,
                validation_errors=errors,
                window_risk_flags=window_risk_flags,
                decisions_file=decisions_file,
                batch_file=batch_file,
            )
            serial += 1
            if evidence_status == "direct":
                direct_units.append(unit)
            else:
                review_items.append(unit)

        expected_sentence_ids = set(sentence_lookup(row))
        missing_sentence_ids = sorted(expected_sentence_ids - covered_sentence_ids)
        if missing_sentence_ids:
            audit_items.append(
                {
                    "request_id": request_id,
                    "issue": "sentences_not_covered_by_decision_groups",
                    "sentence_ids": missing_sentence_ids,
                }
            )

    decided_request_ids = {str(decision.get("request_id") or "") for decision in decisions}
    missing_requests = sorted(set(requests) - decided_request_ids)
    duplicate_decisions = [
        request_id for request_id, count in Counter(str(decision.get("request_id") or "") for decision in decisions).items() if count > 1
    ]

    return {
        "schema_version": "v7_units_draft_fullbook_llm_pilot_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "draft_pilot_units_not_for_downstream_binding",
        "pilot_slug": slug,
        "source_batch": str(batch_file.relative_to(BASE_UNITS_DIR)),
        "source_decisions": str(decisions_file.relative_to(BASE_UNITS_DIR)),
        "notes": [
            "This pilot materializes only LLM sentence-grouping outputs for one chapter batch.",
            "It does not freeze v7u_N IDs.",
            "It does not merge rule-direct list/table units yet.",
            "zh_search_text intentionally remains null unless reliable aligned subspans exist.",
        ],
        "items": direct_units,
        "review_items": review_items,
        "audit": {
            "batch_requests": len(batch_rows),
            "decision_rows": len(decisions),
            "missing_request_decisions": missing_requests,
            "duplicate_decision_request_ids": duplicate_decisions,
            "issues": audit_items,
        },
    }


def build_report(payload: dict) -> str:
    items = payload["items"]
    review_items = payload["review_items"]
    all_units = [*items, *review_items]
    by_type = Counter(unit.get("unit_type") for unit in all_units)
    by_status = Counter(unit.get("evidence_status") for unit in all_units)
    by_page = Counter(unit.get("printed_page") for unit in all_units)
    lines = [
        f"# v7 Fullbook LLM Pilot Units: {payload['pilot_slug']}",
        "",
        f"Generated at: {payload['generated_at']}",
        "",
        "## Summary",
        "",
        f"- batch requests: {payload['audit']['batch_requests']}",
        f"- decision rows: {payload['audit']['decision_rows']}",
        f"- direct units: {len(items)}",
        f"- review items: {len(review_items)}",
        f"- by unit_type: {json.dumps(dict(by_type), ensure_ascii=False)}",
        f"- by evidence_status: {json.dumps(dict(by_status), ensure_ascii=False)}",
        f"- by printed_page: {json.dumps(dict(by_page), ensure_ascii=False)}",
        f"- missing request decisions: {len(payload['audit']['missing_request_decisions'])}",
        f"- duplicate decision request_ids: {len(payload['audit']['duplicate_decision_request_ids'])}",
        f"- audit issues: {len(payload['audit']['issues'])}",
        "",
        "## Direct Unit Examples",
        "",
    ]
    for unit in items[:20]:
        lines.extend(
            [
                f"### {unit['unit_id']} · {unit['unit_type']}",
                "",
                f"- page: {unit.get('printed_page')} / pdf {unit.get('pdf_page')}",
                f"- heading: {' / '.join(unit.get('heading_context', []))}",
                f"- knowledge_en: {unit.get('knowledge_en')}",
                f"- sentence_ids: {', '.join(unit.get('en_sentence_ids', []))}",
                f"- en_quote: {unit.get('en_quote')}",
                f"- reason: {unit.get('decision_reason')}",
                f"- risk_flags: {json.dumps(unit.get('risk_flags', []), ensure_ascii=False)}",
                "",
            ]
        )
    if review_items:
        lines.extend(["## Review Items", ""])
        for unit in review_items[:30]:
            lines.extend(
                [
                    f"### {unit['unit_id']} · {unit['unit_type']} · {unit['evidence_status']}",
                    "",
                    f"- page: {unit.get('printed_page')} / pdf {unit.get('pdf_page')}",
                    f"- knowledge_en: {unit.get('knowledge_en')}",
                    f"- sentence_ids: {', '.join(unit.get('en_sentence_ids', []))}",
                    f"- en_quote: {unit.get('en_quote')}",
                    f"- risk_flags: {json.dumps(unit.get('risk_flags', []), ensure_ascii=False)}",
                    "",
                ]
            )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-file", required=True, type=Path)
    parser.add_argument("--decisions-file", required=True, type=Path)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--out-dir", type=Path, default=DRAFT_DIR)
    parser.add_argument(
        "--max-direct-sentences",
        type=int,
        default=MAX_DIRECT_SENTENCES,
        help="Maximum sentence count allowed for a direct LLM unit before it is moved to needs_review.",
    )
    return parser.parse_args()


def main() -> None:
    global MAX_DIRECT_SENTENCES
    args = parse_args()
    MAX_DIRECT_SENTENCES = args.max_direct_sentences
    batch_file = args.batch_file.resolve()
    decisions_file = args.decisions_file.resolve()
    batch_rows = read_jsonl(batch_file)
    decisions = read_jsonl(decisions_file)
    payload = materialize(batch_rows, decisions, decisions_file, batch_file, args.slug)

    out_json = args.out_dir / f"v7_units_draft.pilot_{args.slug}.llm.json"
    out_report = args.out_dir / f"v7_units_draft.pilot_{args.slug}.llm_report.md"
    out_audit = args.out_dir / f"v7_units_draft.pilot_{args.slug}.llm_audit.json"
    write_json(out_json, payload)
    out_report.write_text(build_report(payload), encoding="utf-8")
    write_json(out_audit, payload["audit"])
    print(f"direct units: {len(payload['items'])}")
    print(f"review items: {len(payload['review_items'])}")
    print(f"wrote: {out_json}")
    print(f"wrote: {out_report}")
    print(f"wrote: {out_audit}")


if __name__ == "__main__":
    main()
