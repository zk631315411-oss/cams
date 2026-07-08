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
AUDIT_DIR = BASE_UNITS_DIR / "audit" / "remaining_review_policy_overlay"

DEFAULT_BASE = DRAFT_DIR / "v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock_toobroad_v2.json"
DEFAULT_PLAN = (
    BASE_UNITS_DIR
    / "audit"
    / "review_resolution_plan_crossblock_toobroad_v2"
    / "review_resolution_plan.json"
)
DEFAULT_OUT = DRAFT_DIR / "v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock_toobroad_policy.json"


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
    "list_item": "fact",
    "context_label": "context",
    "heading_anchor": "context",
    "list_parent": "classification",
    "structural_parent": "context",
    "needs_review": "context",
}


PROMOTE_DIRECT: dict[str, dict[str, Any]] = {
    "v7u_tmp_pilot_v2fb_transaction-monitoring_o020_l020_N000001": {
        "unit_type": "risk_indicator",
        "reason": "complete red-flag list item; terminal punctuation is absent because the source is a list label",
        "requires_parent_context": True,
    },
    "v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000034": {
        "unit_type": "process",
        "reason": "colon-form process step with its own explanation",
        "requires_parent_context": True,
    },
    "v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000035": {
        "unit_type": "process",
        "reason": "colon-form process step with its own explanation",
        "requires_parent_context": True,
    },
    "v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000036": {
        "unit_type": "process",
        "reason": "colon-form process step with its own explanation",
        "requires_parent_context": True,
    },
    "v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000037": {
        "unit_type": "process",
        "reason": "colon-form process step with its own explanation",
        "requires_parent_context": True,
    },
    "v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000038": {
        "unit_type": "process",
        "reason": "colon-form process step with its own explanation",
        "requires_parent_context": True,
    },
    "v7u_tmp_pilot_v2fb_types-of-financial-crime_o000_l020_N000007": {
        "unit_type": "definition",
        "reason": "numbered predicate-crime definition; absent period is source list formatting",
        "requires_parent_context": True,
    },
    "v7u_tmp_pilot_v2fb_types-of-risk-assessment_o000_l020_N000005": {
        "unit_type": "fact",
        "reason": "complete statement; prior label only supplies context",
        "requires_parent_context": True,
    },
    "v7u_tmp_pilot_v2fb_private-banking-and-wealth-management-risks_o000_l020_N000044": {
        "unit_type": "risk_indicator",
        "reason": "short risk/red-flag list item that is meaningful under its heading",
        "requires_parent_context": True,
    },
    "v7u_tmp_pilot_v2fb_corporate-and-investment-banking-risks_o000_l020_N000010": {
        "unit_type": "risk_indicator",
        "reason": "short risk/red-flag list item that is meaningful under its heading",
        "requires_parent_context": True,
    },
    "v7u_tmp_prefreeze_qa_ignored_N000001": {
        "unit_type": "risk_indicator",
        "reason": "short red-flag list item; heading supplies the risk domain",
        "requires_parent_context": True,
    },
    "v7u_tmp_prefreeze_qa_ignored_N000002": {
        "unit_type": "risk_indicator",
        "reason": "short red-flag list item; heading supplies the risk domain",
        "requires_parent_context": True,
    },
    "v7u_tmp_prefreeze_qa_ignored_N000005": {
        "unit_type": "risk_indicator",
        "reason": "short red-flag list item; heading supplies the risk domain",
        "requires_parent_context": True,
    },
    "v7u_tmp_prefreeze_qa_ignored_N000006": {
        "unit_type": "risk_indicator",
        "reason": "short red-flag list item; heading supplies the risk domain",
        "requires_parent_context": True,
    },
    "v7u_tmp_prefreeze_qa_ignored_N000008": {
        "unit_type": "risk_indicator",
        "reason": "short list item describing an illicit e-commerce use; heading supplies the risk domain",
        "requires_parent_context": True,
    },
    "v7u_tmp_prefreeze_qa_ignored_N000023": {
        "unit_type": "process",
        "reason": "short implementation/update item; surrounding list supplies the policy-design context",
        "requires_parent_context": True,
    },
    "v7u_tmp_prefreeze_qa_ignored_N000031": {
        "unit_type": "example",
        "reason": "name-matching example under fuzzy logic; direct only with parent context",
        "requires_parent_context": True,
    },
    "v7u_tmp_prefreeze_qa_ignored_N000032": {
        "unit_type": "example",
        "reason": "name-matching example under fuzzy logic; direct only with parent context",
        "requires_parent_context": True,
    },
}


KEEP_REVIEW: dict[str, str] = {
    "v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o020_l020_N000049": (
        "orphan sentence fragment; needs source-neighbor repair before it can be evidence"
    ),
    "v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000014": (
        "publication title is missing from source extraction"
    ),
    "v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000016": (
        "publication title is missing from source extraction"
    ),
    "v7u_tmp_pilot_v2fb_ongoing-afc-controls_o000_l020_N000026": (
        "starts mid-phrase and cannot stand alone as evidence"
    ),
    "v7u_tmp_pilot_v2fb_afc-guidance-from-other-organizations_o000_l020_N000008": (
        "sentence is visibly split at 'international' and needs a source join decision"
    ),
    "v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000021": (
        "publication title is missing from source extraction"
    ),
    "v7u_tmp_pilot_v2fb_private-banking-and-wealth-management-risks_o020_l020_N000009": (
        "starts mid-phrase and lacks the subject needed for a direct evidence unit"
    ),
    "v7u_tmp_pilot_v2fb_money-laundering-risks-associated-with-retail-and-commercial-banking_o000_l020_N000033": (
        "starts mid-phrase and lacks the subject needed for a direct evidence unit"
    ),
    "v7u_tmp_pilot_v2fb_technology-for-kyc_o080_l020_N000014": (
        "source text has unresolved extraction damage around 'of varying to accommodate'"
    ),
    "v7u_tmp_prefreeze_qa_ignored_N000018": (
        "source text contains mojibake/typo 'Íatest'; keep for manual source repair"
    ),
}


SPLIT_PROSE: dict[str, list[dict[str, Any]]] = {
    "v7u_tmp_prefreeze_qa_ignored_N000003": [
        {
            "sentence_ids": ["v7en_b000589_s001"],
            "unit_type": "definition",
            "knowledge_en": "SPVs are legal entities created for specific and limited purposes",
        },
        {
            "sentence_ids": ["v7en_b000589_s002"],
            "unit_type": "fact",
            "knowledge_en": "SPVs can be used for mergers, acquisitions, joint ventures, real estate, infrastructure, and energy projects",
        },
        {
            "sentence_ids": ["v7en_b000589_s003"],
            "unit_type": "fact",
            "knowledge_en": "SPVs can manage and protect intellectual property assets",
        },
        {
            "sentence_ids": ["v7en_b000589_s004"],
            "unit_type": "fact",
            "knowledge_en": "SPVs are often used in complex financial transactions and asset-backed financing",
        },
    ],
    "v7u_tmp_prefreeze_qa_ignored_N000004": [
        {
            "sentence_ids": ["v7en_b000615_s001", "v7en_b000615_s002"],
            "unit_type": "definition",
            "knowledge_en": "A bank transfer electronically transfers funds between two banks and is usually domestic",
        },
        {
            "sentence_ids": ["v7en_b000615_s003", "v7en_b000615_s004"],
            "unit_type": "process",
            "knowledge_en": "Bank transfers use ACH settlement to support bank credit and debit transfers",
        },
    ],
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compact(text: str, limit: int = 360) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def duplicate_values(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def strip_review_flags(flags: list[Any]) -> list[str]:
    removed = {
        "needs_human_review_before_freeze",
        "incomplete_sentence",
        "fragment",
        "source_sentence_may_continue_next_block",
        "source_sentence_may_continue_from_previous_block",
    }
    return sorted(
        str(flag)
        for flag in flags
        if flag and str(flag) not in removed and not str(flag).startswith("ignored_review_class:")
    )


def as_direct(unit: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(unit)
    unit_type = str(policy["unit_type"])
    out["unit_type"] = unit_type
    out["type"] = TYPE_MAP.get(unit_type, "fact")
    out["evidence_status"] = "direct"
    out["can_be_direct_evidence"] = True
    out["decision_reason"] = str(policy["reason"])
    for sentence in out.get("en_sentences") or []:
        sentence["parent_unit_id"] = out.get("unit_id")
    source = out.setdefault("source", {})
    source["policy_overlay_action"] = "promote_to_direct"
    source["policy_overlay_reason"] = str(policy["reason"])
    flags = set(strip_review_flags(out.get("risk_flags", [])))
    flags.add("policy_promoted_from_review")
    flags.add("zh_subspan_unavailable")
    if policy.get("requires_parent_context"):
        flags.add("requires_parent_context_for_display")
        flags.add("source_list_item_without_terminal_punctuation_allowed")
    out["risk_flags"] = sorted(flags)
    return out


def infer_parent_kind(unit: dict[str, Any], resolution_class: str) -> tuple[str, str, str]:
    quote = str(unit.get("en_quote") or "").strip()
    lower = quote.lower()
    if lower.startswith(("what ", "why ", "how ")):
        return "heading_anchor", "heading_only", "question/heading anchor; not direct evidence"
    if quote.endswith(":") or re.search(r"\b(the following|as follows|include[s]? the following)\b", quote, re.I):
        return "list_parent", "structural_context", "list/table lead-in; useful as parent/context only"
    if resolution_class == "ignored_visual_label_group_review":
        return "context_label", "auxiliary_context", "visual/table label; auxiliary context, not a direct knowledge unit"
    if resolution_class in {"ignored_short_context_label_review", "ignored_review_other"}:
        return "context_label", "auxiliary_context", "short label; keep as context/asset rather than direct evidence"
    return "structural_parent", "structural_context", "instructional or structural context; not direct evidence"


def as_parent(unit: dict[str, Any], resolution_class: str, reason_override: str | None = None) -> dict[str, Any]:
    out = deepcopy(unit)
    unit_type, evidence_status, reason = infer_parent_kind(unit, resolution_class)
    if reason_override:
        reason = reason_override
    out["unit_type"] = unit_type
    out["type"] = TYPE_MAP.get(unit_type, "context")
    out["evidence_status"] = evidence_status
    out["can_be_direct_evidence"] = False
    out["decision_reason"] = reason
    source = out.setdefault("source", {})
    source["policy_overlay_action"] = "move_to_parent_context"
    source["policy_overlay_reason"] = reason
    flags = set(str(flag) for flag in out.get("risk_flags", []) if flag)
    flags.discard("needs_human_review_before_freeze")
    flags.add("policy_moved_to_parent_context")
    flags.add("not_direct_evidence")
    flags.add("zh_subspan_unavailable")
    out["risk_flags"] = sorted(flags)
    return out


def as_review(unit: dict[str, Any], reason: str) -> dict[str, Any]:
    out = deepcopy(unit)
    out["unit_type"] = "needs_review"
    out["type"] = "context"
    out["evidence_status"] = "needs_review"
    out["can_be_direct_evidence"] = False
    out["decision_reason"] = reason
    source = out.setdefault("source", {})
    source["policy_overlay_action"] = "keep_review"
    source["policy_overlay_reason"] = reason
    flags = set(str(flag) for flag in out.get("risk_flags", []) if flag)
    flags.add("policy_retained_review")
    flags.add("needs_human_review_before_freeze")
    flags.add("zh_subspan_unavailable")
    out["risk_flags"] = sorted(flags)
    return out


def split_prose_units(unit: dict[str, Any], split_specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sentence_by_id = {str(item.get("sentence_id")): item for item in unit.get("en_sentences", [])}
    out_units = []
    for idx, spec in enumerate(split_specs, start=1):
        sentence_ids = [str(sentence_id) for sentence_id in spec["sentence_ids"]]
        sentences = [deepcopy(sentence_by_id[sentence_id]) for sentence_id in sentence_ids if sentence_id in sentence_by_id]
        en_quote = " ".join(str(sentence.get("text") or "").strip() for sentence in sentences).strip()
        new_unit = deepcopy(unit)
        new_unit["unit_id"] = f"{unit['unit_id']}_policy_split_N{idx:06d}"
        new_unit["unit_type"] = str(spec["unit_type"])
        new_unit["type"] = TYPE_MAP.get(str(spec["unit_type"]), "fact")
        new_unit["evidence_status"] = "direct"
        new_unit["can_be_direct_evidence"] = True
        new_unit["en_quote"] = en_quote
        new_unit["en_sentence_ids"] = sentence_ids
        new_unit["en_sentences"] = sentences
        new_unit["knowledge_en"] = str(spec["knowledge_en"])
        new_unit["decision_reason"] = "ignored prose block was deterministically split by existing sentence_ids"
        for sentence in new_unit["en_sentences"]:
            sentence["parent_unit_id"] = new_unit["unit_id"]
        source = new_unit.setdefault("source", {})
        source["policy_overlay_action"] = "split_ignored_prose_to_direct"
        source["policy_overlay_reason"] = "ignored prose block contains textbook assertions and existing sentence_ids allow deterministic split"
        source["original_review_unit_id"] = unit["unit_id"]
        flags = set(strip_review_flags(new_unit.get("risk_flags", [])))
        flags.add("policy_split_from_ignored_prose")
        flags.add("zh_subspan_unavailable")
        new_unit["risk_flags"] = sorted(flags)
        out_units.append(new_unit)
    return out_units


def recompute_audit(payload: dict[str, Any], policy_audit: dict[str, Any]) -> dict[str, Any]:
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
            "remaining_review_policy_overlay": policy_audit,
        }
    )
    return audit


def decision_lookup(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("unit_id")): item for item in plan.get("decisions", [])}


def apply_overlay(base_file: Path, plan_file: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = deepcopy(read_json(base_file))
    plan = read_json(plan_file)
    plan_by_id = decision_lookup(plan)

    base_review = payload.get("review_items", [])
    new_direct: list[dict[str, Any]] = []
    new_parent: list[dict[str, Any]] = []
    new_review: list[dict[str, Any]] = []
    manifest_items: list[dict[str, Any]] = []

    for unit in base_review:
        unit_id = str(unit.get("unit_id"))
        plan_item = plan_by_id.get(unit_id, {})
        resolution_class = str(plan_item.get("resolution_class") or "")

        if unit_id in SPLIT_PROSE:
            split_units = split_prose_units(unit, SPLIT_PROSE[unit_id])
            new_direct.extend(split_units)
            manifest_items.append(
                {
                    "unit_id": unit_id,
                    "action": "split_to_direct",
                    "new_unit_ids": [item["unit_id"] for item in split_units],
                    "reason": "ignored prose block contains textbook assertions and can be split by existing sentence_ids",
                }
            )
        elif unit_id in PROMOTE_DIRECT:
            new_direct.append(as_direct(unit, PROMOTE_DIRECT[unit_id]))
            manifest_items.append(
                {
                    "unit_id": unit_id,
                    "action": "promote_to_direct",
                    "reason": PROMOTE_DIRECT[unit_id]["reason"],
                }
            )
        elif unit_id in KEEP_REVIEW:
            new_review.append(as_review(unit, KEEP_REVIEW[unit_id]))
            manifest_items.append({"unit_id": unit_id, "action": "keep_review", "reason": KEEP_REVIEW[unit_id]})
        else:
            reason = None
            if unit_id == "v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o040_l020_N000040":
                reason = "statutory-provision list lead-in; parent/context only until child provisions are parsed"
            parent_unit = as_parent(unit, resolution_class, reason_override=reason)
            new_parent.append(parent_unit)
            manifest_items.append(
                {
                    "unit_id": unit_id,
                    "action": "move_to_parent_context",
                    "reason": parent_unit.get("decision_reason"),
                }
            )

    payload["items"] = [*payload.get("items", []), *new_direct]
    payload["parent_items"] = [*payload.get("parent_items", []), *new_parent]
    payload["review_items"] = new_review
    payload["schema_version"] = "v7_units_draft_fullbook_ds_v2_prefreeze_qa_crossblock_toobroad_policy_overlay_v1"
    payload["status"] = "draft_prefreeze_policy_overlay_not_for_downstream_binding"
    payload["generated_at"] = datetime.now().isoformat(timespec="seconds")
    payload.setdefault("sources", {})["remaining_review_policy_base"] = str(base_file.relative_to(BASE_UNITS_DIR))
    payload.setdefault("sources", {})["remaining_review_policy_plan"] = str(plan_file.relative_to(BASE_UNITS_DIR))
    payload.setdefault("notes", []).append(
        "Remaining review policy overlay applied user-confirmed rules for labels, structural parents, short bullets, and damaged fragments; IDs remain temporary."
    )

    action_counts = Counter(item["action"] for item in manifest_items)
    policy_audit = {
        "base_file": str(base_file.relative_to(BASE_UNITS_DIR)),
        "plan_file": str(plan_file.relative_to(BASE_UNITS_DIR)),
        "processed_review_items": len(base_review),
        "direct_units_added": len(new_direct),
        "parent_context_units_added": len(new_parent),
        "review_units_retained": len(new_review),
        "action_counts": dict(action_counts.most_common()),
    }
    payload["audit"] = recompute_audit(payload, policy_audit)

    manifest = {
        "schema_version": "v7_remaining_review_policy_overlay_manifest_v1",
        "generated_at": payload["generated_at"],
        "policy_basis": [
            "Visual/table labels are auxiliary context by default, not direct evidence.",
            "Teaching/navigation/module-intro text is context unless it states a testable knowledge assertion.",
            "Short bullets may be direct when the parent heading supplies the missing domain.",
            "Term: explanation, red-flag list items, and process/list steps may be direct even without terminal punctuation.",
            "Table/list lead-ins become parent/context, not direct evidence.",
            "Residual damaged fragments may remain in review when the source problem is explicit.",
        ],
        **policy_audit,
        "items": manifest_items,
    }
    return payload, manifest


def build_report(payload: dict[str, Any], manifest: dict[str, Any]) -> str:
    lines = [
        "# v7 Remaining Review Policy Overlay",
        "",
        f"Generated at: {manifest['generated_at']}",
        "",
        "## Summary",
        "",
        f"- processed review items: {manifest['processed_review_items']}",
        f"- direct items: {len(payload.get('items', []))}",
        f"- review items: {len(payload.get('review_items', []))}",
        f"- parent/context items: {len(payload.get('parent_items', []))}",
        f"- direct units added: {manifest['direct_units_added']}",
        f"- parent/context units added: {manifest['parent_context_units_added']}",
        f"- review units retained: {manifest['review_units_retained']}",
        f"- duplicate unit_ids: {len(payload['audit'].get('duplicate_unit_ids', []))}",
        f"- duplicate direct sentence_ids: {len(payload['audit'].get('duplicate_direct_sentence_ids', []))}",
        "",
        "## Action Counts",
        "",
    ]
    for action, count in manifest["action_counts"].items():
        lines.append(f"- {action}: {count}")
    lines.extend(["", "## Policy Basis", ""])
    for item in manifest["policy_basis"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Direct Samples", ""])
    promoted = [
        unit
        for unit in payload.get("items", [])
        if "policy_promoted_from_review" in set(unit.get("risk_flags", []))
        or "policy_split_from_ignored_prose" in set(unit.get("risk_flags", []))
    ]
    for unit in promoted[:24]:
        lines.extend(
            [
                f"### {unit.get('unit_id')}",
                "",
                f"- type: {unit.get('unit_type')}",
                f"- page: {unit.get('printed_page')} / pdf {unit.get('pdf_page')}",
                f"- heading: {' / '.join(unit.get('heading_context', []))}",
                f"- knowledge_en: {unit.get('knowledge_en')}",
                f"- en_quote: {compact(unit.get('en_quote'), 520)}",
                f"- reason: {unit.get('decision_reason')}",
                "",
            ]
        )

    lines.extend(["", "## Retained Review Items", ""])
    for unit in payload.get("review_items", []):
        lines.extend(
            [
                f"### {unit.get('unit_id')}",
                "",
                f"- page: {unit.get('printed_page')} / pdf {unit.get('pdf_page')}",
                f"- heading: {' / '.join(unit.get('heading_context', []))}",
                f"- en_quote: {compact(unit.get('en_quote'), 520)}",
                f"- reason: {unit.get('decision_reason')}",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply user-confirmed policy decisions to remaining v7 review items.")
    parser.add_argument("--base-file", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--plan-file", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--out-file", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--out-dir", type=Path, default=AUDIT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, manifest = apply_overlay(args.base_file.resolve(), args.plan_file.resolve())
    write_json(args.out_file, payload)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out_dir / "remaining_review_policy_manifest.json"
    report_path = args.out_dir / "remaining_review_policy_report.md"
    write_json(manifest_path, manifest)
    report_path.write_text(build_report(payload, manifest), encoding="utf-8")

    print(f"direct items: {len(payload.get('items', []))}")
    print(f"review items: {len(payload.get('review_items', []))}")
    print(f"parent/context items: {len(payload.get('parent_items', []))}")
    print(f"direct units added: {manifest['direct_units_added']}")
    print(f"parent/context units added: {manifest['parent_context_units_added']}")
    print(f"review units retained: {manifest['review_units_retained']}")
    print(f"duplicate unit_ids: {len(payload['audit'].get('duplicate_unit_ids', []))}")
    print(f"duplicate direct sentence_ids: {len(payload['audit'].get('duplicate_direct_sentence_ids', []))}")
    print(f"wrote: {args.out_file}")
    print(f"wrote: {manifest_path}")
    print(f"wrote: {report_path}")


if __name__ == "__main__":
    main()
