#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Migrate legacy chapter-2 card ids to unified V6 sentence-card ids.

This script handles only ch2s_* legacy ids. It does not migrate v6x_* ids.

Dry run:
  python cams工作台/data_pipeline/migrate_ch2_cards_to_v6s.py

Apply:
  python cams工作台/data_pipeline/migrate_ch2_cards_to_v6s.py --apply --archive
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


WORKBENCH = Path(__file__).resolve().parents[1]
DATA = WORKBENCH / "data"
ASSET_DIR = DATA / "teaching_assets"

OLD_CH2 = DATA / "cards_ch2.json"
OLD_COMBINED = DATA / "cards_ch2_plus_v6_except_ch2_sentence.json"
V6_CARDS = DATA / "cards_v6_sentence.json"

OPTION_EVIDENCE_FILES = [
    DATA / "option_evidence_map.json",
    ASSET_DIR / "option_evidence_map.json",
]

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_DIR = WORKBENCH / "考点确认" / "outputs" / "ch2_card_id_migration"
ARCHIVE_DIR = DATA / "archive" / f"legacy_ch2_cards_{RUN_ID}"

MIN_ACCEPT_SCORE = 0.82
MIN_REVIEW_SCORE = 0.72
AMBIGUOUS_MARGIN = 0.02
SUPPLEMENTAL_ID_START = 90000
CH2_ID_RE = re.compile(r"ch2s_\d+")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_cards(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        cards = payload.get("cards", [])
    else:
        cards = payload
    return [card for card in cards if isinstance(card, dict) and card.get("card_id")]


def normalize_text(text: Any) -> str:
    value = re.sub(r"\s+", "", str(text or "")).lower()
    value = re.sub(r"[，。；：、,.!?！？;:()\[\]（）【】\"'“”‘’《》<>•·\-—_/]", "", value)
    return value


def grams(text: str, size: int = 4) -> set[str]:
    value = normalize_text(text)
    if len(value) <= size:
        return {value} if value else set()
    return {value[i : i + size] for i in range(len(value) - size + 1)}


def card_query(card: dict[str, Any]) -> str:
    return str(card.get("citation") or card.get("knowledge") or "")


def card_target(card: dict[str, Any]) -> str:
    return " ".join(
        str(card.get(field) or "")
        for field in ("citation", "knowledge", "chapter_path", "context_before", "context_after")
        if card.get(field)
    )


def sequence_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def path_similarity(old_path: str, new_path: str) -> float:
    if not old_path or not new_path:
        return 0.0
    if old_path in new_path or new_path in old_path:
        return 1.0
    old_parts = {part for part in re.split(r">|/|\s+", old_path) if part}
    new_parts = {part for part in re.split(r">|/|\s+", new_path) if part}
    if not old_parts or not new_parts:
        return 0.0
    return len(old_parts & new_parts) / len(old_parts | new_parts)


def containment_score(needle: str, haystack: str, min_len: int = 4) -> float:
    if not needle or not haystack or len(needle) < min_len:
        return 0.0
    if needle in haystack:
        return min(1.0, 0.80 + min(len(needle), 24) / 120)
    return 0.0


def score_card(old_card: dict[str, Any], new_card: dict[str, Any]) -> tuple[float, str]:
    old_citation = normalize_text(old_card.get("citation"))
    new_citation = normalize_text(new_card.get("citation"))
    old_knowledge = normalize_text(old_card.get("knowledge"))
    new_knowledge = normalize_text(new_card.get("knowledge"))
    old_path = normalize_text(old_card.get("chapter_path"))
    new_path = normalize_text(new_card.get("chapter_path"))
    new_full = normalize_text(card_target(new_card))

    if old_citation and new_citation and old_citation == new_citation:
        return 1.0, "exact_citation"
    if old_knowledge and new_knowledge and old_knowledge == new_knowledge:
        return 0.98, "exact_knowledge"
    if old_citation and new_citation:
        if len(old_citation) >= 4 and old_citation in new_citation:
            return min(0.97, 0.88 + len(old_citation) / max(len(new_citation), 1) * 0.10), "old_citation_in_v6"
        if len(new_citation) >= 6 and new_citation in old_citation:
            return min(0.94, 0.84 + len(new_citation) / max(len(old_citation), 1) * 0.10), "v6_citation_in_old"

    old_best = max(old_citation, old_knowledge, key=len)
    path_bonus = path_similarity(old_path, new_path) * 0.05
    if old_best:
        contained = max(
            containment_score(old_best, new_knowledge, min_len=6),
            containment_score(old_best, new_full, min_len=6),
        )
        if contained and path_bonus:
            return min(0.94, contained + path_bonus), "old_text_in_v6_context"

    citation_ratio = sequence_ratio(old_citation, new_citation)
    knowledge_ratio = sequence_ratio(old_knowledge, new_knowledge)
    path_bonus = path_similarity(old_path, new_path) * 0.04
    return min(1.0, citation_ratio * 0.78 + knowledge_ratio * 0.18 + path_bonus), "text_similarity"


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
        text = card_target(card)
        for gram in grams(text):
            index[gram].append(card)
    return index


def make_supplemental_card(old_card: dict[str, Any], index: int) -> dict[str, Any]:
    """Create a unified-id card for legacy bullet cards missing in v6 extraction."""
    return {
        "card_id": f"v6s_N{SUPPLEMENTAL_ID_START + index:05d}",
        "knowledge": old_card.get("knowledge", ""),
        "citation": old_card.get("citation", ""),
        "context_before": old_card.get("context_before", ""),
        "context_after": old_card.get("context_after", ""),
        "type": old_card.get("type", ""),
        "source_asset": old_card.get("source_asset", ""),
        "source_line_start": old_card.get("source_line_start"),
        "source_line_end": old_card.get("source_line_end"),
        "chapter_path": normalize_chapter_path(str(old_card.get("chapter_path") or "")),
        "evidence_scope": "v6_sentence",
        "migration_origin": {
            "source": "ch2_to_v6s_card_migration_v1",
            "reason": "legacy_ch2_bullet_missing_from_v6_sentence_extraction",
        },
    }


def normalize_chapter_path(path: str) -> str:
    value = path.strip()
    prefix = "洗钱和恐怖融资活动的风险及方法 > "
    if value.startswith(prefix):
        value = value[len(prefix) :]
    return value


def is_context_only_card(old_card: dict[str, Any]) -> bool:
    card_type = str(old_card.get("type") or "").lower()
    citation = normalize_text(old_card.get("citation"))
    knowledge = normalize_text(old_card.get("knowledge"))
    if card_type == "context":
        return True
    if citation and knowledge and knowledge == "原文事实" + citation:
        return True
    return False


def should_create_supplemental(row: dict[str, Any], referenced_ids: set[str]) -> bool:
    if row.get("status") == "mapped":
        return False
    if row.get("old_card_id") not in referenced_ids:
        return False
    old_citation = normalize_text(row.get("old_citation"))
    old_knowledge = normalize_text(row.get("old_knowledge"))
    if len(max(old_citation, old_knowledge, key=len)) < 3:
        return False
    return True


def candidate_cards(
    old_card: dict[str, Any],
    exact_index: dict[str, list[dict[str, Any]]],
    gram_index: dict[str, list[dict[str, Any]]],
    v6_cards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    for field in ("citation", "knowledge"):
        norm = normalize_text(old_card.get(field))
        if norm and norm in exact_index:
            return exact_index[norm]

    hits: Counter[str] = Counter()
    by_id = {card["card_id"]: card for card in v6_cards}
    for gram in grams(card_target(old_card)):
        for card in gram_index.get(gram, []):
            hits[card["card_id"]] += 1
    if hits:
        return [by_id[cid] for cid, _ in hits.most_common(80)]
    return v6_cards


def map_one_card(
    old_card: dict[str, Any],
    exact_index: dict[str, list[dict[str, Any]]],
    gram_index: dict[str, list[dict[str, Any]]],
    v6_cards: list[dict[str, Any]],
) -> dict[str, Any]:
    scored = []
    for new_card in candidate_cards(old_card, exact_index, gram_index, v6_cards):
        score, method = score_card(old_card, new_card)
        if score >= MIN_REVIEW_SCORE:
            scored.append((score, method, new_card))
    scored.sort(key=lambda row: row[0], reverse=True)

    top = scored[0] if scored else None
    second_score = scored[1][0] if len(scored) > 1 else 0.0
    status = "unmatched"
    if top:
        score, method, _ = top
        if score >= MIN_ACCEPT_SCORE and (score - second_score >= AMBIGUOUS_MARGIN or method.startswith("exact")):
            status = "mapped"
        elif score >= MIN_REVIEW_SCORE:
            status = "ambiguous"

    mapped_card = top[2] if top and status == "mapped" else None
    return {
        "old_card_id": old_card.get("card_id"),
        "status": status,
        "canonical_card_id": mapped_card.get("card_id") if mapped_card else "",
        "confidence": round(top[0], 4) if top else 0.0,
        "match_method": top[1] if top else "",
        "old_citation": old_card.get("citation", ""),
        "old_knowledge": old_card.get("knowledge", ""),
        "old_chapter_path": old_card.get("chapter_path", ""),
        "canonical_citation": mapped_card.get("citation", "") if mapped_card else "",
        "canonical_knowledge": mapped_card.get("knowledge", "") if mapped_card else "",
        "canonical_chapter_path": mapped_card.get("chapter_path", "") if mapped_card else "",
        "candidates": [
            {
                "card_id": card.get("card_id"),
                "score": round(score, 4),
                "method": method,
                "citation": card.get("citation", ""),
                "knowledge": card.get("knowledge", ""),
                "chapter_path": card.get("chapter_path", ""),
            }
            for score, method, card in scored[:5]
        ],
    }


def collect_referenced_ch2_ids(payloads: list[Any]) -> set[str]:
    found: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str) and value.startswith("ch2s_"):
            found.add(value)

    for payload in payloads:
        walk(payload)
    return found


def build_mapping() -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    old_cards = normalize_cards(read_json(OLD_CH2))
    v6_cards = normalize_cards(read_json(V6_CARDS))
    exact_index = build_exact_index(v6_cards)
    gram_index = build_gram_index(v6_cards)

    rows = [
        map_one_card(old_card, exact_index, gram_index, v6_cards)
        for old_card in old_cards
    ]
    mapping_by_old = {row["old_card_id"]: row for row in rows}
    v6_by_id = {card["card_id"]: card for card in v6_cards}
    stats = Counter(row["status"] for row in rows)

    payload = {
        "schema_version": "ch2_to_v6s_card_migration_v1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_file": str(OLD_CH2),
        "target_file": str(V6_CARDS),
        "thresholds": {
            "min_accept_score": MIN_ACCEPT_SCORE,
            "min_review_score": MIN_REVIEW_SCORE,
            "ambiguous_margin": AMBIGUOUS_MARGIN,
        },
        "stats": {
            "old_ch2_cards": len(old_cards),
            "v6_cards": len(v6_cards),
            "mapped": stats["mapped"],
            "ambiguous": stats["ambiguous"],
            "unmatched": stats["unmatched"],
        },
        "items": rows,
    }
    return payload, mapping_by_old, v6_by_id


def add_supplemental_mappings(
    mapping_payload: dict[str, Any],
    mapping_by_old: dict[str, dict[str, Any]],
    v6_by_id: dict[str, dict[str, Any]],
    referenced_ids: set[str],
) -> list[dict[str, Any]]:
    old_cards = {card["card_id"]: card for card in normalize_cards(read_json(OLD_CH2))}
    supplementals: list[dict[str, Any]] = []
    next_index = 1
    for row in mapping_payload["items"]:
        if not should_create_supplemental(row, referenced_ids):
            continue
        old_card = old_cards.get(row["old_card_id"])
        if not old_card:
            continue
        supplemental = make_supplemental_card(old_card, next_index)
        next_index += 1
        supplementals.append(supplemental)

        row["status"] = "mapped"
        row["canonical_card_id"] = supplemental["card_id"]
        row["confidence"] = 0.91
        row["match_method"] = "supplemental_v6s_from_legacy_ch2"
        row["canonical_citation"] = supplemental.get("citation", "")
        row["canonical_knowledge"] = supplemental.get("knowledge", "")
        row["canonical_chapter_path"] = supplemental.get("chapter_path", "")
        row["candidates"] = []
        mapping_by_old[row["old_card_id"]] = row
        v6_by_id[supplemental["card_id"]] = supplemental

    stats = Counter(row["status"] for row in mapping_payload["items"])
    mapping_payload["stats"]["mapped"] = stats["mapped"]
    mapping_payload["stats"]["ambiguous"] = stats["ambiguous"]
    mapping_payload["stats"]["unmatched"] = stats["unmatched"]
    mapping_payload["supplemental_cards"] = supplementals
    return supplementals


def migrate_payload(payload: Any, mapping: dict[str, dict[str, Any]], v6_by_id: dict[str, dict[str, Any]]) -> tuple[Any, Counter[str]]:
    stats: Counter[str] = Counter()

    def replace_legacy_ids_in_text(text: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old_id = match.group(0)
            row = mapping.get(old_id)
            if row and row.get("status") == "mapped":
                stats["mapped_inline_text_id"] += 1
                return str(row["canonical_card_id"])
            stats["unresolved_inline_text_id"] += 1
            return old_id

        return CH2_ID_RE.sub(repl, text)

    def migrate(value: Any, parent_key: str = "") -> Any:
        if isinstance(value, dict):
            cid = value.get("card_id")
            if isinstance(cid, str) and cid.startswith("ch2s_"):
                row = mapping.get(cid)
                if row and row.get("status") == "mapped":
                    new_id = row["canonical_card_id"]
                    canonical = v6_by_id.get(new_id, {})
                    value["card_id"] = new_id
                    for old_field, new_field in [
                        ("quote", "citation"),
                        ("citation", "citation"),
                        ("knowledge", "knowledge"),
                        ("chapter_path", "chapter_path"),
                        ("source_line_start", "source_line_start"),
                        ("source_line_end", "source_line_end"),
                        ("type", "type"),
                    ]:
                        if new_field in canonical and canonical.get(new_field) not in (None, ""):
                            value[old_field] = canonical.get(new_field)
                    stats["mapped_dict_card_id"] += 1
                else:
                    value.setdefault("unresolved_legacy_card_id", cid)
                    stats["unresolved_dict_card_id"] += 1

            for key in list(value.keys()):
                if key.startswith("legacy") or key.startswith("original"):
                    continue
                value[key] = migrate(value[key], key)
            return value

        if isinstance(value, list):
            return [migrate(item, parent_key) for item in value]

        if isinstance(value, str) and value.startswith("ch2s_") and not parent_key.startswith(("legacy", "original")):
            row = mapping.get(value)
            if row and row.get("status") == "mapped":
                stats["mapped_string_id"] += 1
                return row["canonical_card_id"]
            stats["unresolved_string_id"] += 1
            return value

        if isinstance(value, str) and "ch2s_" in value and not parent_key.startswith(("legacy", "original")):
            return replace_legacy_ids_in_text(value)

        return value

    migrated = migrate(payload)
    if isinstance(migrated, dict):
        migrations = list(migrated.get("migrations", []))
        migrations.append(
            {
                "name": "ch2_to_v6s_card_migration_v1",
                "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "scope": "ch2s legacy ids migrated to cards_v6_sentence v6s_N ids",
                "stats": dict(stats),
            }
        )
        migrated["migrations"] = migrations
    return migrated, stats


def write_report(
    mapping_payload: dict[str, Any],
    referenced_ids: set[str],
    post_counts: dict[str, Any],
    apply: bool,
    archive: bool,
) -> str:
    by_id = {row["old_card_id"]: row for row in mapping_payload["items"]}
    referenced_rows = [by_id[cid] for cid in sorted(referenced_ids) if cid in by_id]
    ref_stats = Counter(row["status"] for row in referenced_rows)
    lines = [
        "# 第二章旧句卡迁移报告",
        "",
        f"- generated_at: {mapping_payload['generated_at']}",
        f"- apply: {apply}",
        f"- archive_requested: {archive}",
        f"- old_ch2_cards: {mapping_payload['stats']['old_ch2_cards']}",
        f"- all_mapped: {mapping_payload['stats']['mapped']}",
        f"- all_ambiguous: {mapping_payload['stats']['ambiguous']}",
        f"- all_unmatched: {mapping_payload['stats']['unmatched']}",
        f"- referenced_ch2_ids_before: {len(referenced_ids)}",
        f"- referenced_mapped: {ref_stats['mapped']}",
        f"- referenced_ambiguous: {ref_stats['ambiguous']}",
        f"- referenced_unmatched: {ref_stats['unmatched']}",
        "",
        "## 更新后检查",
        "",
    ]
    for name, counts in post_counts.items():
        lines.append(f"- {name}: {counts}")

    problem_rows = [row for row in referenced_rows if row["status"] != "mapped"]
    lines += ["", "## 被活跃资产引用但未稳定映射的 ch2s", ""]
    if not problem_rows:
        lines.append("- 无。")
    for row in problem_rows[:80]:
        lines.append(
            f"- {row['old_card_id']} | {row['status']} | confidence={row['confidence']} | "
            f"old={row['old_citation'][:80]}"
        )
        for cand in row.get("candidates", [])[:3]:
            lines.append(f"  - candidate {cand['card_id']} score={cand['score']} {cand['citation'][:80]}")
    return "\n".join(lines) + "\n"


def count_prefixes(path: Path) -> dict[str, int]:
    if not path.exists():
        return {"missing": 1}
    text = path.read_text(encoding="utf-8")
    return {
        "ch2s": len(re.findall(r'"ch2s_', text)),
        "v6x": len(re.findall(r'"v6x_', text)),
        "v6s": len(re.findall(r'"v6s_', text)),
    }


def append_supplemental_cards(cards_path: Path, supplementals: list[dict[str, Any]]) -> None:
    if not supplementals:
        return
    payload = read_json(cards_path)
    if isinstance(payload, dict):
        cards = payload.setdefault("cards", [])
        existing_ids = {card.get("card_id") for card in cards if isinstance(card, dict)}
        cards.extend(card for card in supplementals if card["card_id"] not in existing_ids)
        migrations = list(payload.get("migrations", []))
        migrations.append(
            {
                "name": "ch2_to_v6s_supplemental_cards_v1",
                "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "scope": "legacy ch2 bullet cards appended with v6s_N9 ids",
                "count": len(supplementals),
            }
        )
        payload["migrations"] = migrations
    else:
        existing_ids = {card.get("card_id") for card in payload if isinstance(card, dict)}
        payload.extend(card for card in supplementals if card["card_id"] not in existing_ids)
    write_json(cards_path, payload)


def archive_old_files(mapping_path: Path, report_path: Path) -> None:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    for path in (OLD_CH2, OLD_COMBINED):
        if path.exists():
            shutil.move(str(path), str(ARCHIVE_DIR / path.name))
    shutil.copy2(mapping_path, ARCHIVE_DIR / mapping_path.name)
    shutil.copy2(report_path, ARCHIVE_DIR / report_path.name)
    readme = f"""# Legacy Chapter-2 Card Archive

Archived at: {datetime.now().astimezone().isoformat(timespec="seconds")}

This folder stores legacy chapter-2 evidence pools after migration to the unified
`cards_v6_sentence.json` coordinate system.

Archived files:

- `cards_ch2.json`: legacy second-chapter sentence cards with `ch2s_...` ids.
- `cards_ch2_plus_v6_except_ch2_sentence.json`: old mixed evidence pool that combined `ch2s_...` and `v6x_...` ids.
- `ch2_old_to_v6s_map.json`: migration table from `ch2s_...` to `v6s_N...`.
- `migration_report.md`: migration summary and unresolved references, if any.

Current static teaching assets should not use `ch2s_...` as final evidence ids.
Use `cards_v6_sentence.json` / `v6s_N...` instead.
"""
    (ARCHIVE_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate ch2s legacy card ids to v6s_N ids.")
    parser.add_argument("--apply", action="store_true", help="Write migrated assets.")
    parser.add_argument("--archive", action="store_true", help="Move legacy ch2 card files into data/archive after applying.")
    args = parser.parse_args()

    mapping_payload, mapping_by_old, v6_by_id = build_mapping()
    input_payloads = [read_json(path) for path in OPTION_EVIDENCE_FILES if path.exists()]
    referenced_ids = collect_referenced_ch2_ids(input_payloads)
    supplemental_cards = add_supplemental_mappings(mapping_payload, mapping_by_old, v6_by_id, referenced_ids)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mapping_path = OUT_DIR / "ch2_old_to_v6s_map.json"
    write_json(mapping_path, mapping_payload)

    referenced_rows = [mapping_by_old[cid] for cid in referenced_ids if cid in mapping_by_old]
    unresolved_referenced = [row for row in referenced_rows if row.get("status") != "mapped"]

    if args.apply and unresolved_referenced:
        print(json.dumps({
            "status": "blocked",
            "reason": "referenced ch2s ids include ambiguous/unmatched rows",
            "unresolved_referenced": len(unresolved_referenced),
            "out_dir": str(OUT_DIR),
        }, ensure_ascii=False, indent=2))
        return 2

    update_stats: dict[str, Any] = {}
    if args.apply:
        append_supplemental_cards(V6_CARDS, supplemental_cards)
        for path in OPTION_EVIDENCE_FILES:
            if not path.exists():
                continue
            payload = read_json(path)
            migrated, stats = migrate_payload(payload, mapping_by_old, v6_by_id)
            write_json(path, migrated)
            update_stats[path.name if path.parent == DATA else f"teaching_assets/{path.name}"] = dict(stats)

    post_counts = {
        str(path.relative_to(WORKBENCH)): count_prefixes(path)
        for path in OPTION_EVIDENCE_FILES
        if path.exists()
    }
    report = write_report(mapping_payload, referenced_ids, post_counts, args.apply, args.archive)
    report_path = OUT_DIR / "migration_report.md"
    report_path.write_text(report, encoding="utf-8")

    if args.apply and args.archive:
        archive_old_files(mapping_path, report_path)

    summary = {
        "apply": args.apply,
        "archive": args.archive,
        "out_dir": str(OUT_DIR),
        "mapping_stats": mapping_payload["stats"],
        "referenced_ch2_ids": len(referenced_ids),
        "referenced_unresolved": len(unresolved_referenced),
        "supplemental_cards": len(supplemental_cards),
        "update_stats": update_stats,
        "post_counts": post_counts,
        "archive_dir": str(ARCHIVE_DIR) if args.apply and args.archive else "",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
