from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
TEST_DIR = PHASE_DIR / "tests" / "p5c_alias_groups"

DEFAULT_CANDIDATES = TEST_DIR / "outputs" / "p5c_alias_candidate_groups_v3.json"
DEFAULT_REVIEWS = TEST_DIR / "outputs" / "p5c_alias_group_reviews_full_v1.jsonl"
DEFAULT_OUTPUT = PHASE_DIR / "outputs" / "p5c_alias_index.json"
DEFAULT_PREVIEW = PHASE_DIR / "previews" / "p5c_alias_index_preview.md"
DEFAULT_REPORT = PHASE_DIR / "reports" / "p5c_alias_index_report.md"


MANUAL_DECISIONS: dict[str, dict[str, Any]] = {
    "p5c_cand_000001": {
        "action": "accept",
        "canonical_en": "suspicious activity report",
        "canonical_zh": "可疑活动报告",
        "aliases_en": [
            "SAR",
            "STR",
            "suspicious activity reports",
            "suspicious transaction report",
            "suspicious transaction reporting",
            "suspicious transaction reports",
        ],
        "aliases_zh": ["可疑交易报告"],
        "alias_scope": "retrieval_equivalent_report_variant",
        "review_note": "Used only as retrieval aliases for report evidence; not a KG equivalence edge.",
    },
    "p5c_cand_000021": {
        "action": "split_accept",
        "groups": [
            {
                "canonical_en": "risk profile",
                "canonical_zh": "风险状况",
                "aliases_en": [],
                "aliases_zh": ["风险画像"],
                "alias_scope": "translation_variant",
                "review_note": "risk profiling is an activity and is excluded.",
            }
        ],
        "excluded_terms": ["risk profiling"],
    },
    "p5c_cand_000037": {
        "action": "accept",
        "canonical_en": "Immediate Outcome",
        "canonical_zh": "直接目标",
        "aliases_en": [],
        "aliases_zh": ["有效性指标", "立即成果"],
        "alias_scope": "translation_variant",
    },
    "p5c_cand_000042": {"action": "reject", "review_note": "correspondent bank, respondent bank, and correspondent banking are distinct."},
    "p5c_cand_000055": {
        "action": "accept",
        "canonical_en": "Mutual legal assistance treaties",
        "canonical_zh": "司法协助条约",
        "aliases_en": ["MLAT"],
        "aliases_zh": [],
        "alias_scope": "abbreviation_full_form",
    },
    "p5c_cand_000068": {
        "action": "accept",
        "canonical_en": "bribery",
        "canonical_zh": "贿赂",
        "aliases_en": ["bribe"],
        "aliases_zh": [],
        "alias_scope": "retrieval_equivalent",
        "review_note": "Useful for review/evidence retrieval; not strict ontology equivalence.",
    },
    "p5c_cand_000081": {"action": "reject", "review_note": "facial-recognition nodal points and blockchain nodes are distinct."},
    "p5c_cand_000087": {
        "action": "accept",
        "canonical_en": "weapons of mass destruction (WMD)",
        "canonical_zh": "大规模杀伤性武器",
        "aliases_en": ["WMD"],
        "aliases_zh": [],
        "alias_scope": "abbreviation_full_form",
    },
    "p5c_cand_000106": {
        "action": "accept",
        "canonical_en": "money transfer",
        "canonical_zh": "汇款",
        "aliases_en": ["remittance"],
        "aliases_zh": [],
        "alias_scope": "retrieval_equivalent",
        "review_note": "Allowed for option evidence retrieval.",
    },
    "p5c_cand_000107": {"action": "reject", "review_note": "bill of exchange and money order are distinct instruments."},
    "p5c_cand_000110": {"action": "reject", "review_note": "cyber-enabled crime and cybercrime are related but not strict aliases."},
    "p5c_cand_000113": {"action": "reject", "review_note": "validation and verification are distinct processes."},
    "p5c_cand_000189": {"action": "compound_only", "canonical_en": "AML/CFT"},
    "p5c_cand_000190": {"action": "compound_only", "canonical_en": "AML/CTF"},
    "p5c_cand_000191": {"action": "compound_only", "canonical_en": "BSA/AML"},
    "p5c_cand_000192": {"action": "compound_only", "canonical_en": "KYC/CDD"},
    "p5c_cand_000193": {"action": "compound_only", "canonical_en": "MLRO/BSA"},
    "p5c_cand_000194": {
        "action": "split_accept",
        "groups": [
            {
                "canonical_en": "token",
                "canonical_zh": "代币",
                "aliases_en": [],
                "aliases_zh": [],
                "alias_scope": "translation_variant",
                "review_note": "NFT is a subtype/parallel item and is excluded.",
            }
        ],
        "excluded_terms": ["NFT"],
    },
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def input_terms(group: dict[str, Any]) -> set[str]:
    return {str(term.get("text") or "").strip() for term in group.get("terms") or [] if term.get("text")}


def input_terms_lower(group: dict[str, Any]) -> set[str]:
    return {term.lower() for term in input_terms(group)}


def evidence_unit_ids(group: dict[str, Any]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in group.get("evidence_examples") or []:
        unit_id = str(item.get("unit_id") or "")
        if unit_id and unit_id not in seen:
            output.append(unit_id)
            seen.add(unit_id)
    return output


def safe_review_terms(group: dict[str, Any], review: dict[str, Any]) -> dict[str, Any] | None:
    allowed = input_terms_lower(group)
    emitted: list[str] = []
    for key in ("canonical_en", "canonical_zh"):
        value = review.get(key)
        if value and str(value).strip().lower() not in {"none", "null"}:
            emitted.append(str(value).strip())
    for key in ("aliases_en", "aliases_zh"):
        emitted.extend(str(value).strip() for value in review.get(key) or [] if value)
    if any(value.lower() not in allowed for value in emitted):
        return None
    return review


def make_alias_group(
    group: dict[str, Any],
    source_review_id: str,
    canonical_en: str,
    canonical_zh: str,
    aliases_en: list[str],
    aliases_zh: list[str],
    alias_scope: str,
    review_note: str = "",
) -> dict[str, Any]:
    return {
        "alias_group_id": "",
        "index_purpose": "option_evidence_retrieval",
        "not_kg_edge": True,
        "source_review_id": source_review_id,
        "canonical_en": canonical_en,
        "canonical_zh": canonical_zh,
        "aliases_en": aliases_en,
        "aliases_zh": aliases_zh,
        "all_terms": sorted(set([canonical_en, canonical_zh, *aliases_en, *aliases_zh]) - {""}),
        "alias_scope": alias_scope,
        "evidence_unit_ids": evidence_unit_ids(group),
        "review_note": review_note,
    }


def make_from_review(group: dict[str, Any], row: dict[str, Any]) -> dict[str, Any] | None:
    review = row.get("review") or {}
    if review.get("decision") != "merge" or review.get("confidence") != "high":
        return None
    safe = safe_review_terms(group, review)
    if not safe:
        return None
    return make_alias_group(
        group=group,
        source_review_id=row["candidate_group_id"],
        canonical_en=str(safe.get("canonical_en") or ""),
        canonical_zh=str(safe.get("canonical_zh") or ""),
        aliases_en=list(safe.get("aliases_en") or []),
        aliases_zh=list(safe.get("aliases_zh") or []),
        alias_scope=str(safe.get("merge_type") or "alias"),
        review_note=str(safe.get("reason") or ""),
    )


def materialize_manual(group: dict[str, Any], group_id: str, decision: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    aliases: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    compounds: list[dict[str, Any]] = []
    action = decision.get("action")
    if action == "accept":
        aliases.append(
            make_alias_group(
                group,
                group_id,
                decision.get("canonical_en") or "",
                decision.get("canonical_zh") or "",
                list(decision.get("aliases_en") or []),
                list(decision.get("aliases_zh") or []),
                decision.get("alias_scope") or "manual_accept",
                decision.get("review_note") or "manual review accepted",
            )
        )
    elif action == "split_accept":
        for item in decision.get("groups") or []:
            aliases.append(
                make_alias_group(
                    group,
                    group_id,
                    item.get("canonical_en") or "",
                    item.get("canonical_zh") or "",
                    list(item.get("aliases_en") or []),
                    list(item.get("aliases_zh") or []),
                    item.get("alias_scope") or "manual_split_accept",
                    item.get("review_note") or "manual split accepted",
                )
            )
        rejected.append(make_reject_record(group, group_id, decision.get("review_note") or "manual split", decision.get("excluded_terms") or []))
    elif action == "reject":
        rejected.append(make_reject_record(group, group_id, decision.get("review_note") or "manual reject"))
    elif action == "compound_only":
        compounds.append(
            {
                "compound_term_id": "",
                "index_purpose": "option_evidence_retrieval",
                "not_kg_edge": True,
                "source_review_id": group_id,
                "canonical_en": decision.get("canonical_en") or "",
                "component_terms": sorted(input_terms(group) - {decision.get("canonical_en") or ""}),
                "compound_scope": "compound_term_not_component_alias",
                "evidence_unit_ids": evidence_unit_ids(group),
                "review_note": "Kept as a compound retrieval term; components are not merged as aliases.",
            }
        )
    return aliases, rejected, compounds


def make_reject_record(group: dict[str, Any], group_id: str, reason: str, excluded_terms: list[str] | None = None) -> dict[str, Any]:
    return {
        "source_review_id": group_id,
        "input_terms": sorted(input_terms(group)),
        "excluded_terms": excluded_terms or [],
        "reason": reason,
        "not_kg_edge": True,
    }


def preview(alias_groups: list[dict[str, Any]], compound_terms: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> str:
    lines = [
        "# P5C Alias Index Preview",
        "",
        "- index_purpose: option_evidence_retrieval",
        "- not_kg_edge: true",
        f"- alias_groups: {len(alias_groups)}",
        f"- compound_terms: {len(compound_terms)}",
        f"- rejected_or_split_records: {len(rejected)}",
        "",
        "## Alias Groups",
        "",
        "| id | canonical_en | canonical_zh | aliases_en | aliases_zh | scope | units |",
        "|---|---|---|---|---|---|---:|",
    ]
    for item in alias_groups[:120]:
        lines.append(
            f"| {item['alias_group_id']} | {item['canonical_en']} | {item['canonical_zh']} | "
            f"{', '.join(item['aliases_en'])} | {', '.join(item['aliases_zh'])} | {item['alias_scope']} | {len(item['evidence_unit_ids'])} |"
        )
    lines.extend(["", "## Compound Terms", "", "| id | term | components | units |", "|---|---|---|---:|"])
    for item in compound_terms:
        lines.append(f"| {item['compound_term_id']} | {item['canonical_en']} | {', '.join(item['component_terms'])} | {len(item['evidence_unit_ids'])} |")
    lines.extend(["", "## Rejected Or Split", "", "| source | terms | excluded | reason |", "|---|---|---|---|"])
    for item in rejected[:80]:
        lines.append(f"| {item['source_review_id']} | {', '.join(item['input_terms'])} | {', '.join(item['excluded_terms'])} | {item['reason']} |")
    return "\n".join(lines) + "\n"


def report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join(
        [
            "# P5C Alias Index Report",
            "",
            "P5C is an option/evidence retrieval index only. It must not be imported as KG edges.",
            "",
            f"- source_review_count: {summary['source_review_count']}",
            f"- alias_group_count: {summary['alias_group_count']}",
            f"- compound_term_count: {summary['compound_term_count']}",
            f"- rejected_or_split_count: {summary['rejected_or_split_count']}",
            f"- auto_accept_count: {summary['auto_accept_count']}",
            f"- manual_alias_count: {summary['manual_alias_count']}",
            "",
            "Manual review decisions were applied to SAR/STR, bribe/bribery, remittance/money transfer, compound slash abbreviations, and other ambiguous groups.",
        ]
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize P5C alias index for option evidence retrieval.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--reviews", type=Path, default=DEFAULT_REVIEWS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--preview", type=Path, default=DEFAULT_PREVIEW)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    candidates = {group["candidate_group_id"]: group for group in read_json(args.candidates).get("candidate_groups") or []}
    reviews = read_jsonl(args.reviews)
    alias_groups: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    compound_terms: list[dict[str, Any]] = []
    auto_accept_count = 0
    manual_alias_count = 0

    for row in reviews:
        group_id = row["candidate_group_id"]
        group = candidates[group_id]
        if group_id in MANUAL_DECISIONS:
            manual_aliases, manual_rejected, manual_compounds = materialize_manual(group, group_id, MANUAL_DECISIONS[group_id])
            alias_groups.extend(manual_aliases)
            rejected.extend(manual_rejected)
            compound_terms.extend(manual_compounds)
            manual_alias_count += len(manual_aliases)
            continue
        auto_group = make_from_review(group, row)
        if auto_group:
            alias_groups.append(auto_group)
            auto_accept_count += 1
        else:
            review = row.get("review") or {}
            rejected.append(make_reject_record(group, group_id, review.get("reason") or "not auto accepted"))

    for index, group in enumerate(alias_groups, start=1):
        group["alias_group_id"] = f"p5c_alias_{index:06d}"
    for index, group in enumerate(compound_terms, start=1):
        group["compound_term_id"] = f"p5c_compound_{index:06d}"

    payload = {
        "summary": {
            "index_purpose": "option_evidence_retrieval",
            "not_kg_edge": True,
            "source_review_count": len(reviews),
            "alias_group_count": len(alias_groups),
            "compound_term_count": len(compound_terms),
            "rejected_or_split_count": len(rejected),
            "auto_accept_count": auto_accept_count,
            "manual_alias_count": manual_alias_count,
        },
        "alias_groups": alias_groups,
        "compound_terms": compound_terms,
        "rejected_or_split_records": rejected,
    }
    write_json(args.output, payload)
    write_text(args.preview, preview(alias_groups, compound_terms, rejected))
    write_text(args.report, report(payload))
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
