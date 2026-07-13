"""
Build full V6 workbench assets.

Outputs:
- data/exam_points_v6.json: existing Ch2 exam-point candidates remapped from
  old cards_ch2 IDs to full-book sentence-card IDs.
- data/chapters/v6.json: full-book reader structure grouped by sentence-card
  chapter path and source line. The reader text itself is parsed from
  v6教材原文/v6_clean.md, not reconstructed from old sentence cards.

This script does not decide new exam points. It only moves the existing
candidate exam-point layer onto the full V6 sentence-card coordinate system.
"""

from __future__ import annotations

import json
import re
from collections import OrderedDict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "cams工作台" / "data"

OLD_EXAM_POINTS = DATA / "exam_points_ch2.json"
OLD_CARDS = DATA / "cards_ch2.json"
V6_CARDS = DATA / "cards_v6_sentence.json"
V6_TEXT_SOURCE = ROOT / "教材、答疑记录、习题与参考文献" / "教材原文" / "v6" / "v6_clean.md"

OUT_EXAM_POINTS = DATA / "exam_points_v6.json"
OUT_CHAPTER = DATA / "chapters" / "v6.json"
OUT_REVIEW = DATA / "exam_points_v6_mapping_review.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize(text: str) -> str:
    text = re.sub(r"\s+", "", text or "")
    text = re.sub(r"[，。；：、,.!?！？;:()\[\]（）【】\"'“”‘’《》<>•·\-—_/]", "", text)
    return text.lower()


def load_cards(path: Path) -> list[dict[str, Any]]:
    raw = read_json(path)
    if isinstance(raw, dict):
        return raw.get("cards", [])
    return raw if isinstance(raw, list) else []


def score_match(old_card: dict[str, Any], new_card: dict[str, Any]) -> float:
    old_citation = normalize(old_card.get("citation", ""))
    new_citation = normalize(new_card.get("citation", ""))
    old_knowledge = normalize(old_card.get("knowledge", ""))
    new_knowledge = normalize(new_card.get("knowledge", ""))

    if old_citation and new_citation:
        if old_citation == new_citation:
            return 1.0
        if len(new_citation) >= 8 and new_citation in old_citation:
            return min(0.98, 0.82 + len(new_citation) / max(len(old_citation), 1) * 0.16)
        if len(old_citation) >= 8 and old_citation in new_citation:
            return min(0.96, 0.84 + len(old_citation) / max(len(new_citation), 1) * 0.12)

    citation_ratio = SequenceMatcher(None, old_citation, new_citation).ratio() if old_citation and new_citation else 0
    knowledge_ratio = SequenceMatcher(None, old_knowledge, new_knowledge).ratio() if old_knowledge and new_knowledge else 0
    return citation_ratio * 0.75 + knowledge_ratio * 0.25


def map_old_card_to_v6(
    old_card: dict[str, Any],
    v6_cards: list[dict[str, Any]],
    min_score: float = 0.42,
    max_cards: int = 3,
) -> tuple[list[str], list[dict[str, Any]]]:
    scored = []
    for card in v6_cards:
        score = score_match(old_card, card)
        if score >= min_score:
            scored.append((score, card))
    scored.sort(key=lambda item: item[0], reverse=True)

    selected: list[str] = []
    review = []
    for score, card in scored[:max_cards]:
        cid = card.get("card_id")
        if not cid:
            continue
        selected.append(cid)
        review.append(
            {
                "card_id": cid,
                "score": round(score, 4),
                "knowledge": card.get("knowledge", ""),
                "citation": card.get("citation", ""),
                "chapter_path": card.get("chapter_path", ""),
                "source_line_start": card.get("source_line_start"),
            }
        )
        if score >= 0.9:
            break
    return selected, review


def build_exam_points_v6() -> tuple[dict[str, Any], dict[str, Any]]:
    old_points = read_json(OLD_EXAM_POINTS)
    old_cards = {card["card_id"]: card for card in load_cards(OLD_CARDS) if card.get("card_id")}
    v6_cards = load_cards(V6_CARDS)
    valid_v6 = {card["card_id"] for card in v6_cards if card.get("card_id")}

    card_mapping: dict[str, list[str]] = {}
    mapping_review: dict[str, Any] = {}

    unique_old_ids = []
    for ep in old_points.get("exam_points", []):
      for cid in ep.get("source_card_ids", []):
        if cid and cid not in unique_old_ids:
          unique_old_ids.append(cid)

    for old_id in unique_old_ids:
        old_card = old_cards.get(old_id)
        if not old_card:
            card_mapping[old_id] = []
            mapping_review[old_id] = {"old_card_id": old_id, "status": "missing_old_card", "matches": []}
            continue
        mapped, matches = map_old_card_to_v6(old_card, v6_cards)
        card_mapping[old_id] = mapped
        mapping_review[old_id] = {
            "old_card_id": old_id,
            "old_knowledge": old_card.get("knowledge", ""),
            "old_citation": old_card.get("citation", ""),
            "mapped_card_ids": mapped,
            "matches": matches,
        }

    converted = []
    unmapped_exam_points = []
    for ep in old_points.get("exam_points", []):
        row = dict(ep)
        old_ids = list(ep.get("source_card_ids", []))
        new_ids = []
        for old_id in old_ids:
            for new_id in card_mapping.get(old_id, []):
                if new_id in valid_v6 and new_id not in new_ids:
                    new_ids.append(new_id)
        row["source_card_ids_old_ch2"] = old_ids
        row["source_card_ids"] = new_ids
        row["evidence_scope"] = "v6_sentence"
        row["mapping_note"] = "source_card_ids 已从 cards_ch2.json 旧句卡映射到 cards_v6_sentence.json 全书句级卡。"
        if old_ids and not new_ids:
            row["needs"] = sorted(set(row.get("needs", []) + ["v6_mapping_review"]))
            unmapped_exam_points.append(row.get("id"))
        converted.append(row)

    data = {
        "version": "0.2",
        "asset_note": (
            "从 exam_points_ch2.json 迁移到 V6 全书句级证据池的候选考试考点。"
            "source_card_ids 引用 cards_v6_sentence.json；source_card_ids_old_ch2 保留旧 cards_ch2.json ID 便于追溯。"
        ),
        "source_scope": old_points.get("source_scope", "qa_37"),
        "evidence_scope": "v6_sentence",
        "exam_points": converted,
        "stats": {
            "exam_points": len(converted),
            "old_unique_source_cards": len(unique_old_ids),
            "mapped_old_source_cards": sum(1 for ids in card_mapping.values() if ids),
            "unmapped_old_source_cards": sum(1 for ids in card_mapping.values() if not ids),
            "exam_points_without_v6_source_cards": sum(1 for ep in converted if not ep.get("source_card_ids")),
        },
    }

    review = {
        "version": "0.1",
        "stats": data["stats"],
        "unmapped_exam_points": unmapped_exam_points,
        "card_mapping": mapping_review,
    }
    return data, review


def split_chapter_path(path: str) -> tuple[str, str]:
    parts = [part.strip() for part in (path or "").split(">") if part.strip()]
    if not parts:
        return "未分组", "正文"
    if len(parts) == 1:
        return parts[0], "正文"
    return parts[0], " > ".join(parts[1:])


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def markdown_heading(line: str) -> tuple[int, str] | None:
    match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
    if not match:
        return None
    return len(match.group(1)), match.group(2).strip()


def build_heading_number(counters: dict[int, int], level: int) -> str:
    return ".".join(str(counters[i]) for i in range(2, level + 1) if counters.get(i))


def card_matches_paragraph(card: dict[str, Any], paragraph_text: str) -> bool:
    citation = normalize_text(card.get("citation", ""))
    if len(citation) < 8:
        return False
    text = normalize_text(paragraph_text)
    if citation in text:
        return True
    if len(citation) > 30 and citation[:30] in text:
        return True
    return False


def attach_cards_to_paragraphs(
    sections: list[dict[str, Any]],
    cards: list[dict[str, Any]],
    exam_card_ids: set[str],
) -> dict[str, int]:
    matched_cards: set[str] = set()
    paragraphs_with_cards = 0
    highlight_instances = 0

    searchable_cards = [
        card
        for card in cards
        if card.get("card_id") and len(normalize_text(card.get("citation", ""))) >= 8
    ]

    for section in sections:
        for subsection in section["subsections"]:
            for paragraph in subsection["paragraphs"]:
                card_ids = []
                for card in searchable_cards:
                    cid = card.get("card_id")
                    if cid and card_matches_paragraph(card, paragraph["text"]):
                        card_ids.append(cid)
                        matched_cards.add(cid)
                highlight_ids = [cid for cid in card_ids if cid in exam_card_ids]
                paragraph["card_ids"] = card_ids
                paragraph["highlight_card_ids"] = highlight_ids
                if card_ids:
                    paragraphs_with_cards += 1
                highlight_instances += len(highlight_ids)

    return {
        "matched_cards": len(matched_cards),
        "paragraphs_with_cards": paragraphs_with_cards,
        "highlight_instances": highlight_instances,
    }


def build_v6_chapter(exam_points: dict[str, Any]) -> dict[str, Any]:
    cards = load_cards(V6_CARDS)
    exam_card_ids = {
        cid
        for ep in exam_points.get("exam_points", [])
        for cid in ep.get("source_card_ids", [])
    }

    chapter_title = "CAMS v6.51 教材（中文版）"
    headings: dict[int, str] = {}
    heading_numbers: dict[int, str] = {}
    counters: dict[int, int] = {}
    section_order: OrderedDict[str, dict[str, Any]] = OrderedDict()
    current_section_number = ""
    current_section_title = ""
    current_subsection_key = ""

    for line_no, raw_line in enumerate(V6_TEXT_SOURCE.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        heading = markdown_heading(line)
        if heading:
            level, title = heading
            if level == 1:
                chapter_title = title
            else:
                counters[level] = counters.get(level, 0) + 1
                for lower_level in range(level + 1, 7):
                    counters.pop(lower_level, None)
                headings[level] = title
                heading_numbers[level] = build_heading_number(counters, level)
                for lower_level in range(level + 1, 7):
                    headings.pop(lower_level, None)
                    heading_numbers.pop(lower_level, None)
                if level == 2:
                    current_section_number = heading_numbers[level]
                    current_section_title = title
                    section_order.setdefault(
                        current_section_number,
                        {
                            "number": current_section_number,
                            "title": current_section_title,
                            "subsections": OrderedDict(),
                        },
                    )
                    current_subsection_key = ""
                elif level >= 3 and current_section_number:
                    current_subsection_key = heading_numbers[level]
                    section = section_order.setdefault(
                        current_section_number,
                        {
                            "number": current_section_number,
                            "title": current_section_title or "未分组",
                            "subsections": OrderedDict(),
                        },
                    )
                    section["subsections"].setdefault(
                        current_subsection_key,
                        {
                            "number": current_subsection_key,
                            "title": title,
                            "level": level,
                            "paragraphs": [],
                        },
                    )
            continue
        if line.startswith("![") or line.startswith("[") or not current_section_number:
            continue

        text = normalize_text(line)
        if not text:
            continue
        section = section_order.setdefault(
            current_section_number,
            {
                "number": current_section_number,
                "title": current_section_title or headings.get(2, "未分组"),
                "subsections": OrderedDict(),
            },
        )
        if not current_subsection_key:
            current_subsection_key = f"{current_section_number}.0"
            section["subsections"].setdefault(
                current_subsection_key,
                {
                    "number": current_subsection_key,
                    "title": "正文",
                    "level": 3,
                    "paragraphs": [],
                },
            )
        subsection = section["subsections"][current_subsection_key]
        subsection["paragraphs"].append(
            {
                "text": text,
                "card_ids": [],
                "highlight_card_ids": [],
                "source_line_start": line_no,
                "source_line_end": line_no,
            }
        )

    sections = []
    for section_number, section_data in section_order.items():
        section = {
            "section_id": section_number,
            "number": section_number,
            "section_title": section_data["title"],
            "display_title": f'{section_number} {section_data["title"]}',
            "subsections": [],
        }
        for subsection in section_data["subsections"].values():
            if not subsection["paragraphs"]:
                continue
            display_title = f'{subsection["number"]} {subsection["title"]}'
            section["subsections"].append(
                {
                    "number": subsection["number"],
                    "title": subsection["title"],
                    "display_title": display_title,
                    "heading_level": subsection["level"],
                    "paragraphs": subsection["paragraphs"],
                }
            )
        if section["subsections"]:
            sections.append(section)

    attach_stats = attach_cards_to_paragraphs(sections, cards, exam_card_ids)

    return {
        "chapter": chapter_title,
        "asset_note": (
            "Full-book reader structure generated from v6教材原文/v6_clean.md. "
            "card_ids/highlight_card_ids are best-effort matches against the current cards_v6_sentence.json."
        ),
        "evidence_scope": "v6_sentence",
        "source_file": str(V6_TEXT_SOURCE),
        "sections": sections,
        "stats": {
            "source_file": str(V6_TEXT_SOURCE),
            "sections": len(sections),
            "subsections": sum(len(section["subsections"]) for section in sections),
            "paragraphs": sum(
                len(subsection["paragraphs"])
                for section in sections
                for subsection in section["subsections"]
            ),
            **attach_stats,
        },
    }


def main() -> int:
    exam_points, review = build_exam_points_v6()
    chapter = build_v6_chapter(exam_points)

    write_json(OUT_EXAM_POINTS, exam_points)
    write_json(OUT_REVIEW, review)
    write_json(OUT_CHAPTER, chapter)

    highlight_count = sum(
        len(paragraph.get("highlight_card_ids", []))
        for section in chapter["sections"]
        for subsection in section["subsections"]
        for paragraph in subsection["paragraphs"]
    )
    print(json.dumps({
        "exam_points": exam_points["stats"],
        "chapter_sections": len(chapter["sections"]),
        "chapter_paragraphs": sum(
            len(subsection["paragraphs"])
            for section in chapter["sections"]
            for subsection in section["subsections"]
        ),
        "highlight_instances": highlight_count,
        "out_exam_points": str(OUT_EXAM_POINTS),
        "out_chapter": str(OUT_CHAPTER),
        "out_review": str(OUT_REVIEW),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
