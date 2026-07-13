"""
Build a full-book V6 reader asset without exam-point annotations.

This is the first step for expanding the workbench from the Ch2 reader to the
full CAMS V6 textbook. It preserves sentence-card anchors for future linking,
but deliberately leaves highlight_card_ids empty so no exam points are shown.
"""

from __future__ import annotations

import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parents[1]
ROOT = APP_DIR.parent
DATA = APP_DIR / "data"
TEACHING_ASSETS = DATA / "teaching_assets"

SOURCE_MD = ROOT / "教材、答疑记录、习题与参考文献" / "教材原文" / "v6" / "v6_clean.md"
CARDS_PATH = TEACHING_ASSETS / "cards_v6_sentence.json"
OUT_CHAPTER = TEACHING_ASSETS / "chapters" / "v6_full.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cards(path: Path) -> list[dict[str, Any]]:
    raw = read_json(path)
    if isinstance(raw, dict):
        return raw.get("cards", [])
    return raw if isinstance(raw, list) else []


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


def attach_cards_to_paragraphs(sections: list[dict[str, Any]], cards: list[dict[str, Any]]) -> dict[str, int]:
    matched_cards: set[str] = set()
    paragraphs_with_cards = 0
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
                paragraph["card_ids"] = card_ids
                paragraph["highlight_card_ids"] = []
                if card_ids:
                    paragraphs_with_cards += 1

    return {
        "matched_cards": len(matched_cards),
        "paragraphs_with_cards": paragraphs_with_cards,
        "highlight_instances": 0,
    }


def build_full_reader() -> dict[str, Any]:
    cards = load_cards(CARDS_PATH)
    chapter_title = "CAMS v6.51 教材（中文版）"
    headings: dict[int, str] = {}
    heading_numbers: dict[int, str] = {}
    counters: dict[int, int] = {}
    section_order: OrderedDict[str, dict[str, Any]] = OrderedDict()
    current_section_number = ""
    current_section_title = ""
    current_subsection_key = ""

    for line_no, raw_line in enumerate(SOURCE_MD.read_text(encoding="utf-8").splitlines(), start=1):
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
            section["subsections"].append(
                {
                    "number": subsection["number"],
                    "title": subsection["title"],
                    "display_title": f'{subsection["number"]} {subsection["title"]}',
                    "heading_level": subsection["level"],
                    "paragraphs": subsection["paragraphs"],
                }
            )
        if section["subsections"]:
            sections.append(section)

    attach_stats = attach_cards_to_paragraphs(sections, cards)

    return {
        "chapter": chapter_title,
        "reader_mode": "full_v6_textbook_without_exam_points",
        "asset_note": (
            "Full-book reader structure generated from v6_clean.md. "
            "card_ids are preserved for future linking; highlight_card_ids are intentionally empty."
        ),
        "evidence_scope": "v6_sentence",
        "source_file": str(SOURCE_MD),
        "sections": sections,
        "stats": {
            "source_file": str(SOURCE_MD),
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
    chapter = build_full_reader()
    write_json(OUT_CHAPTER, chapter)
    print(
        json.dumps(
            {
                "out_chapter": str(OUT_CHAPTER),
                "stats": chapter["stats"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
