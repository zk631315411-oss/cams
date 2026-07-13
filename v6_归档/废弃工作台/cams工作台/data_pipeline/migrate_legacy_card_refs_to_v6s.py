#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Audit and migrate legacy card references to unified v6s sentence cards.

This script targets downstream references that still mention legacy ids such as
v6x_* or ch2s_* after the legacy card pools were archived.

Default mode is dry-run. Use --apply only after reviewing the generated reports.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


WORKBENCH = Path(__file__).resolve().parents[1]
DATA = WORKBENCH / "data"
ASSET_DIR = DATA / "teaching_assets"
OUT_DIR = WORKBENCH / "\u8003\u70b9\u786e\u8ba4" / "outputs" / "old_id_reference_migration"

CANONICAL_CARD_FILES = [
    ASSET_DIR / "cards_v6_sentence.json",
    DATA / "cards_v6_sentence.json",
]

TARGET_FILES = [
    ASSET_DIR / "option_evidence_map.json",
    ASSET_DIR / "exam_points_from_option_evidence_mvp.json",
    ASSET_DIR / "exam_points_teaching_mvp.json",
    ASSET_DIR / "sentence_exam_point_map.json",
    DATA / "option_evidence_map.json",
    DATA / "exam_points_from_option_evidence_mvp.json",
    DATA / "exam_points_teaching_mvp.json",
    DATA / "sentence_exam_point_map.json",
]

LEGACY_ID_RE = re.compile(r"\b(?:v6x_\d+|ch2s_\d+)\b")
ACCEPT_SCORE = 0.88
REVIEW_SCORE = 0.70
AMBIGUOUS_MARGIN = 0.03
TRACEABILITY_KEYS = {"from_original_card_id"}
TRACEABILITY_PARENT_FIELDS = {"card_id_migration"}
TRACEABILITY_CHILD_KEYS = {"from"}
MANUAL_APPROVED_MAPPINGS = {
    "v6x_00294": {
        "canonical_card_id": "v6s_N02174",
        "confidence": 1.0,
        "note": "User approved: old card missed document titles; canonical card completes the same sentence.",
    },
    "v6x_00380": {
        "canonical_card_id": "v6s_N90025",
        "confidence": 1.0,
        "note": "User approved standalone supplemental card because the sentence was only present in adjacent-card context.",
    },
    "v6x_01136": {
        "canonical_card_id": "v6s_N90024",
        "confidence": 1.0,
        "note": "User approved standalone supplemental card because the official extracted card had a truncated sentence start.",
    },
    "v6x_01882": {
        "canonical_card_id": "v6s_N03581",
        "confidence": 1.0,
        "note": "User approved: table-extracted canonical card preserves the same CDD element.",
    },
    "v6x_02473": {
        "canonical_card_id": "v6s_N04143",
        "confidence": 1.0,
        "note": "User corrected mapping to the actual red-flag sentence about large cash asset purchases/transactions.",
    },
    "v6x_03053": {
        "canonical_card_id": "v6s_N04701",
        "confidence": 1.0,
        "note": "User approved: canonical card preserves the FIU suspicious-transaction-report distribution point.",
    },
}


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_cards(payload: Any) -> list[dict[str, Any]]:
    cards = payload.get("cards", []) if isinstance(payload, dict) else payload
    return [card for card in cards if isinstance(card, dict) and card.get("card_id")]


def normalize_text(text: Any) -> str:
    value = re.sub(r"\s+", "", str(text or "")).lower()
    value = re.sub(r"[，。；：、,.!?！？;:()\[\]（）【】\"'“”‘’《》<>•·\-—_/\\|]", "", value)
    return value


def card_text(card: dict[str, Any]) -> str:
    fields = [
        "quote",
        "citation",
        "knowledge",
        "text",
        "chapter_path",
        "context_before",
        "context_after",
    ]
    return " ".join(str(card.get(field) or "") for field in fields if card.get(field))


def sequence_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def char_grams(text: Any, size: int = 4) -> set[str]:
    value = normalize_text(text)
    if len(value) <= size:
        return {value} if value else set()
    return {value[i : i + size] for i in range(len(value) - size + 1)}


def jaccard(a: Any, b: Any) -> float:
    aa = char_grams(a)
    bb = char_grams(b)
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


def load_canonical_cards() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    seen: set[str] = set()
    cards: list[dict[str, Any]] = []
    for path in CANONICAL_CARD_FILES:
        if not path.exists():
            continue
        for card in normalize_cards(read_json(path)):
            cid = str(card.get("card_id") or "")
            if cid and cid not in seen:
                seen.add(cid)
                cards.append(card)
    return cards, {str(card["card_id"]): card for card in cards}


def existing_target_files() -> list[Path]:
    seen: set[Path] = set()
    files: list[Path] = []
    for path in TARGET_FILES:
        if path.exists() and path not in seen:
            seen.add(path)
            files.append(path)
    return files


def path_to_str(path: list[Any]) -> str:
    parts = []
    for part in path:
        if isinstance(part, int):
            parts.append(f"[{part}]")
        else:
            if parts:
                parts.append(".")
            parts.append(str(part))
    return "".join(parts)


def is_traceability_path(path: list[Any]) -> bool:
    if not path:
        return False
    leaf = path[-1]
    if leaf in TRACEABILITY_KEYS:
        return True
    return len(path) >= 2 and path[-2] in TRACEABILITY_PARENT_FIELDS and leaf in TRACEABILITY_CHILD_KEYS


def is_actionable_ref(ref: dict[str, Any]) -> bool:
    return ref.get("kind") in {"dict_card_id", "string_value"}


def scan_legacy_refs(value: Any, file_path: Path) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    refs: list[dict[str, Any]] = []
    evidence_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def walk(node: Any, path: list[Any]) -> None:
        if isinstance(node, dict):
            cid = node.get("card_id")
            if isinstance(cid, str) and LEGACY_ID_RE.fullmatch(cid):
                evidence_by_id[cid].append(copy.deepcopy(node))
                refs.append(
                    {
                        "file": str(file_path),
                        "path": path_to_str(path + ["card_id"]),
                        "legacy_id": cid,
                        "kind": "dict_card_id",
                        "context": compact_context(node),
                    }
                )
            for key, child in node.items():
                if key == "card_id" and isinstance(child, str) and LEGACY_ID_RE.fullmatch(child):
                    continue
                walk(child, path + [key])
        elif isinstance(node, list):
            for index, child in enumerate(node):
                walk(child, path + [index])
        elif isinstance(node, str):
            kind_prefix = "traceability_" if is_traceability_path(path) else ""
            if LEGACY_ID_RE.fullmatch(node):
                refs.append(
                    {
                        "file": str(file_path),
                        "path": path_to_str(path),
                        "legacy_id": node,
                        "kind": f"{kind_prefix}string_value",
                        "context": node,
                    }
                )
            else:
                for match in LEGACY_ID_RE.finditer(node):
                    refs.append(
                        {
                            "file": str(file_path),
                            "path": path_to_str(path),
                            "legacy_id": match.group(0),
                            "kind": f"{kind_prefix}embedded_string_ref",
                            "context": node[:300],
                        }
                    )

    walk(value, [])
    return refs, evidence_by_id


def compact_context(node: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "card_id",
        "quote",
        "citation",
        "knowledge",
        "chapter_path",
        "reason",
        "support_type",
        "relevance",
    ]
    return {field: node.get(field) for field in fields if node.get(field) not in (None, "")}


def collect_legacy_refs(files: list[Path]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    all_refs: list[dict[str, Any]] = []
    evidence_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    payloads: dict[str, Any] = {}
    for path in files:
        payload = read_json(path)
        payloads[str(path)] = payload
        refs, evidence = scan_legacy_refs(payload, path)
        all_refs.extend(refs)
        for legacy_id, rows in evidence.items():
            evidence_by_id[legacy_id].extend(rows)
    return all_refs, evidence_by_id, payloads


def representative_legacy_card(legacy_id: str, evidence_by_id: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    rows = evidence_by_id.get(legacy_id) or []
    if rows:
        return max(rows, key=lambda row: len(normalize_text(card_text(row))))
    return {"card_id": legacy_id}


def build_exact_index(cards: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        for field in ("citation", "knowledge"):
            norm = normalize_text(card.get(field))
            if norm:
                index[norm].append(card)
    return index


def build_gram_index(cards: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        for gram in char_grams(card_text(card)):
            index[gram].append(card)
    return index


def candidate_cards(
    legacy_card: dict[str, Any],
    canonical_cards: list[dict[str, Any]],
    exact_index: dict[str, list[dict[str, Any]]],
    gram_index: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    for field in ("quote", "citation", "knowledge"):
        norm = normalize_text(legacy_card.get(field))
        if norm and norm in exact_index:
            return exact_index[norm]

    hits: Counter[str] = Counter()
    by_id = {card["card_id"]: card for card in canonical_cards}
    for gram in char_grams(card_text(legacy_card)):
        for card in gram_index.get(gram, []):
            hits[str(card["card_id"])] += 1
    if hits:
        return [by_id[cid] for cid, _ in hits.most_common(120)]
    return canonical_cards


def score_candidate(legacy_card: dict[str, Any], canonical_card: dict[str, Any]) -> tuple[float, str]:
    legacy_texts = [
        normalize_text(legacy_card.get("quote")),
        normalize_text(legacy_card.get("citation")),
        normalize_text(legacy_card.get("knowledge")),
    ]
    canonical_citation = normalize_text(canonical_card.get("citation"))
    canonical_knowledge = normalize_text(canonical_card.get("knowledge"))
    canonical_full = normalize_text(card_text(canonical_card))

    for text in legacy_texts:
        if not text:
            continue
        if text == canonical_citation or text == canonical_knowledge:
            return 1.0, "exact_quote"
        if len(text) >= 4 and text in canonical_citation:
            coverage = len(text) / max(len(canonical_citation), 1)
            return min(0.99, 0.93 + coverage * 0.05), "substring_quote"
        if len(text) >= 4 and text in canonical_full:
            coverage = len(text) / max(len(canonical_full), 1)
            return min(0.97, 0.90 + coverage * 0.05), "normalized_substring"

    legacy_best = max((text for text in legacy_texts if text), key=len, default="")
    if not legacy_best:
        return 0.0, "no_legacy_text"

    citation_ratio = sequence_ratio(legacy_best, canonical_citation)
    knowledge_ratio = sequence_ratio(legacy_best, canonical_knowledge)
    gram_score = max(jaccard(legacy_best, canonical_citation), jaccard(legacy_best, canonical_knowledge))
    score = max(citation_ratio * 0.75 + gram_score * 0.20, knowledge_ratio * 0.75 + gram_score * 0.20)
    return min(0.96, score), "text_similarity"


def map_legacy_id(
    legacy_id: str,
    legacy_card: dict[str, Any],
    canonical_cards: list[dict[str, Any]],
    exact_index: dict[str, list[dict[str, Any]]],
    gram_index: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    canonical_by_id = {str(card.get("card_id")): card for card in canonical_cards}
    manual = MANUAL_APPROVED_MAPPINGS.get(legacy_id)
    if manual:
        canonical = canonical_by_id.get(manual["canonical_card_id"])
        if not canonical:
            return {
                "legacy_id": legacy_id,
                "status": "unmapped",
                "canonical_card_id": "",
                "confidence": 0.0,
                "match_method": "manual_approved_missing_canonical",
                "manual_note": manual.get("note", ""),
                "legacy_card": compact_context(legacy_card),
                "canonical_card": {},
                "candidates": [],
            }
        return {
            "legacy_id": legacy_id,
            "status": "mapped",
            "canonical_card_id": canonical.get("card_id"),
            "confidence": manual.get("confidence", 1.0),
            "match_method": "manual_approved",
            "manual_note": manual.get("note", ""),
            "legacy_card": compact_context(legacy_card),
            "canonical_card": compact_context(canonical),
            "candidates": [
                {
                    "card_id": canonical.get("card_id"),
                    "score": manual.get("confidence", 1.0),
                    "method": "manual_approved",
                    "citation": canonical.get("citation", ""),
                    "knowledge": canonical.get("knowledge", ""),
                    "chapter_path": canonical.get("chapter_path", ""),
                }
            ],
        }

    scored: list[tuple[float, str, dict[str, Any]]] = []
    for candidate in candidate_cards(legacy_card, canonical_cards, exact_index, gram_index):
        score, method = score_candidate(legacy_card, candidate)
        if score >= REVIEW_SCORE:
            scored.append((score, method, candidate))
    scored.sort(key=lambda row: row[0], reverse=True)

    top = scored[0] if scored else None
    second_score = scored[1][0] if len(scored) > 1 else 0.0
    status = "unmapped"
    if top:
        score, method, _ = top
        if method in {"exact_quote", "substring_quote", "normalized_substring"} and score >= ACCEPT_SCORE:
            status = "mapped"
        elif score >= ACCEPT_SCORE and score - second_score >= AMBIGUOUS_MARGIN:
            status = "mapped"
        elif score >= REVIEW_SCORE:
            status = "manual_review"

    canonical = top[2] if top and status == "mapped" else None
    return {
        "legacy_id": legacy_id,
        "status": status,
        "canonical_card_id": canonical.get("card_id") if canonical else "",
        "confidence": round(top[0], 4) if top else 0.0,
        "match_method": top[1] if top else "",
        "legacy_card": compact_context(legacy_card),
        "canonical_card": compact_context(canonical) if canonical else {},
        "candidates": [
            {
                "card_id": card.get("card_id"),
                "score": round(score, 4),
                "method": method,
                "citation": card.get("citation", ""),
                "knowledge": card.get("knowledge", ""),
                "chapter_path": card.get("chapter_path", ""),
            }
            for score, method, card in scored[:8]
        ],
    }


def build_mapping(
    refs: list[dict[str, Any]],
    evidence_by_id: dict[str, list[dict[str, Any]]],
    canonical_cards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    exact_index = build_exact_index(canonical_cards)
    gram_index = build_gram_index(canonical_cards)
    legacy_ids = sorted({ref["legacy_id"] for ref in refs if is_actionable_ref(ref)})
    return [
        map_legacy_id(
            legacy_id,
            representative_legacy_card(legacy_id, evidence_by_id),
            canonical_cards,
            exact_index,
            gram_index,
        )
        for legacy_id in legacy_ids
    ]


def migration_lookup(mapping_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["legacy_id"]: row for row in mapping_rows if row.get("status") == "mapped" and row.get("canonical_card_id")}


def migrate_payload(payload: Any, mapping: dict[str, dict[str, Any]], canonical_by_id: dict[str, dict[str, Any]]) -> tuple[Any, list[dict[str, Any]]]:
    changed_refs: list[dict[str, Any]] = []

    def migrate(node: Any, path: list[Any], parent_key: str = "") -> Any:
        if isinstance(node, dict):
            new_node = {}
            for key, value in node.items():
                new_node[key] = migrate(value, path + [key], key)

            cid = node.get("card_id")
            if isinstance(cid, str) and cid in mapping:
                row = mapping[cid]
                new_id = row["canonical_card_id"]
                canonical = canonical_by_id.get(new_id, {})
                new_node["card_id"] = new_id
                new_node.setdefault("from_original_card_id", cid)
                new_node.setdefault(
                    "card_id_migration",
                    {
                        "from": cid,
                        "to": new_id,
                        "match_method": row.get("match_method"),
                        "confidence": row.get("confidence"),
                    },
                )
                if canonical:
                    for field in ("citation", "knowledge", "chapter_path", "type", "source_line_start", "source_line_end"):
                        if canonical.get(field) not in (None, ""):
                            new_node[field] = canonical.get(field)
                    if canonical.get("citation"):
                        new_node["quote"] = canonical.get("citation")
                changed_refs.append({"path": path_to_str(path + ["card_id"]), "from": cid, "to": new_id, "kind": "dict_card_id"})
            return new_node

        if isinstance(node, list):
            migrated = [migrate(item, path + [index], parent_key) for index, item in enumerate(node)]
            if parent_key in {"card_ids", "source_card_ids", "source_cards", "core_card_ids", "supporting_card_ids", "background_card_ids"}:
                deduped = []
                seen = set()
                for item in migrated:
                    key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else item
                    if key in seen:
                        continue
                    seen.add(key)
                    deduped.append(item)
                migrated = deduped
            elif migrated and all(isinstance(item, dict) and item.get("card_id") for item in migrated):
                deduped_dicts = []
                seen_ids = set()
                for item in migrated:
                    cid = item.get("card_id")
                    if cid in seen_ids:
                        continue
                    seen_ids.add(cid)
                    deduped_dicts.append(item)
                migrated = deduped_dicts
            return migrated

        if isinstance(node, str):
            if parent_key == "card_id":
                return node
            if node in mapping:
                new_id = mapping[node]["canonical_card_id"]
                changed_refs.append({"path": path_to_str(path), "from": node, "to": new_id, "kind": "string_value"})
                return new_id
            return node

        return node

    return migrate(payload, []), changed_refs


def build_reports(files: list[Path], refs: list[dict[str, Any]], mapping_rows: list[dict[str, Any]], dry_run_changes: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    actionable_refs = [ref for ref in refs if is_actionable_ref(ref)]
    traceability_refs = [ref for ref in refs if not is_actionable_ref(ref)]
    ref_counter = Counter(ref["legacy_id"] for ref in actionable_refs)
    traceability_counter = Counter(ref["legacy_id"] for ref in traceability_refs)
    status_counter = Counter(row["status"] for row in mapping_rows)
    file_counter = Counter(ref["file"] for ref in refs)
    kind_counter = Counter(ref["kind"] for ref in refs)
    return {
        "generated_at": now(),
        "mode": "dry-run",
        "target_files": [str(path) for path in files],
        "stats": {
            "all_legacy_ref_occurrences": len(refs),
            "legacy_ref_occurrences": len(actionable_refs),
            "traceability_ref_occurrences": len(traceability_refs),
            "unique_legacy_ids": len(ref_counter),
            "traceability_unique_legacy_ids": len(traceability_counter),
            "mapped_ids": status_counter["mapped"],
            "manual_review_ids": status_counter["manual_review"],
            "unmapped_ids": status_counter["unmapped"],
            "dry_run_changed_refs": sum(len(rows) for rows in dry_run_changes.values()),
        },
        "refs_by_file": dict(file_counter),
        "refs_by_kind": dict(kind_counter),
        "refs_by_legacy_id": dict(ref_counter),
        "traceability_refs_by_legacy_id": dict(traceability_counter),
    }


def write_markdown_report(summary: dict[str, Any], mapping_rows: list[dict[str, Any]], dry_run_changes: dict[str, list[dict[str, Any]]]) -> None:
    lines = [
        "# 旧 ID 引用清理 dry-run 报告",
        "",
        f"- generated_at: {summary['generated_at']}",
        f"- legacy_ref_occurrences: {summary['stats']['legacy_ref_occurrences']}",
        f"- unique_legacy_ids: {summary['stats']['unique_legacy_ids']}",
        f"- mapped_ids: {summary['stats']['mapped_ids']}",
        f"- manual_review_ids: {summary['stats']['manual_review_ids']}",
        f"- unmapped_ids: {summary['stats']['unmapped_ids']}",
        f"- dry_run_changed_refs: {summary['stats']['dry_run_changed_refs']}",
        f"- refs_by_kind: {json.dumps(summary.get('refs_by_kind', {}), ensure_ascii=False)}",
        "- embedded_string_ref 只报告不自动替换，避免改变考点 id、说明文字或历史审计描述。",
        "",
        "## 自动映射样例",
        "",
    ]
    mapped = [row for row in mapping_rows if row["status"] == "mapped"]
    if not mapped:
        lines.append("- 无。")
    for row in mapped[:30]:
        lines.append(
            f"- `{row['legacy_id']}` -> `{row['canonical_card_id']}` "
            f"({row['match_method']}, {row['confidence']})"
        )

    review = [row for row in mapping_rows if row["status"] == "manual_review"]
    lines += ["", "## 需人工确认", ""]
    if not review:
        lines.append("- 无。")
    for row in review[:30]:
        candidate = row.get("candidates", [{}])[0] if row.get("candidates") else {}
        lines.append(
            f"- `{row['legacy_id']}` best=`{candidate.get('card_id', '')}` "
            f"({row.get('match_method')}, {row.get('confidence')})"
        )

    unmapped = [row for row in mapping_rows if row["status"] == "unmapped"]
    lines += ["", "## 未映射", ""]
    if not unmapped:
        lines.append("- 无。")
    for row in unmapped[:30]:
        lines.append(f"- `{row['legacy_id']}`")

    lines += ["", "## 文件 dry-run 变更数", ""]
    for file_path, rows in dry_run_changes.items():
        lines.append(f"- `{file_path}`: {len(rows)}")

    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(apply: bool = False) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    canonical_cards, canonical_by_id = load_canonical_cards()
    files = existing_target_files()
    refs, evidence_by_id, payloads = collect_legacy_refs(files)
    mapping_rows = build_mapping(refs, evidence_by_id, canonical_cards)
    mapped_lookup = migration_lookup(mapping_rows)

    dry_run_changes: dict[str, list[dict[str, Any]]] = {}
    migrated_payloads: dict[str, Any] = {}
    for file_path, payload in payloads.items():
        migrated, changes = migrate_payload(payload, mapped_lookup, canonical_by_id)
        dry_run_changes[file_path] = changes
        migrated_payloads[file_path] = migrated

    summary = build_reports(files, refs, mapping_rows, dry_run_changes)
    summary["mode"] = "apply" if apply else "dry-run"
    summary["stats"]["written_files"] = 0

    write_json(OUT_DIR / "legacy_refs_report.json", summary)
    write_json(OUT_DIR / "mapping_candidates.json", {"generated_at": now(), "items": mapping_rows})
    write_json(OUT_DIR / "manual_review_old_ids.json", {"generated_at": now(), "items": [row for row in mapping_rows if row["status"] == "manual_review"]})
    write_json(OUT_DIR / "unmapped_old_ids.json", {"generated_at": now(), "items": [row for row in mapping_rows if row["status"] == "unmapped"]})
    write_json(OUT_DIR / "dry_run_changed_refs.json", {"generated_at": now(), "items": dry_run_changes})
    write_markdown_report(summary, mapping_rows, dry_run_changes)

    if apply:
        written = 0
        for file_path, migrated in migrated_payloads.items():
            if dry_run_changes.get(file_path):
                Path(file_path).write_text(json.dumps(migrated, ensure_ascii=False, indent=2), encoding="utf-8")
                written += 1
        summary["stats"]["written_files"] = written
        write_json(OUT_DIR / "legacy_refs_report.json", summary)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy card references to v6s ids.")
    parser.add_argument("--apply", action="store_true", help="Write mapped references back to target JSON files.")
    args = parser.parse_args()
    print(json.dumps(run(apply=args.apply), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
