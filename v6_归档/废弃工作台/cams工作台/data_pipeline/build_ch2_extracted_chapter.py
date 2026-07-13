"""
Build the workbench reader chapter from v6教材原文/ch2_extracted.md.

The frontend renders chapter JSON, so this script converts the Markdown source
into the same data/chapters/*.json shape used by the reader. It also best-effort
attaches existing v6 sentence cards to paragraphs so the right panel, search,
and exam-point highlighting can keep working.
"""

from __future__ import annotations

import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
WORKBENCH = ROOT / "cams工作台"
DATA = WORKBENCH / "data"

SOURCE_MD = ROOT / "教材、答疑记录、习题与参考文献" / "教材原文" / "v6" / "ch2_extracted.md"
V6_CARDS = DATA / "cards_v6_sentence.json"
V6_CHAPTER = DATA / "chapters" / "v6.json"
EXAM_POINTS = DATA / "exam_points_v6.json"
OUT_CHAPTER = DATA / "chapters" / "ch2_extracted.json"


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
    text = re.sub(r"\s+", "", text or "")
    text = re.sub(r"[，。；：、,.!?！？;:()\[\]（）【】\"'“”‘’《》<>•·\-—_/]", "", text)
    return text.lower()


def markdown_heading(line: str) -> tuple[int, str] | None:
    match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
    if not match:
        return None
    return len(match.group(1)), match.group(2).strip()


def clean_paragraph(line: str) -> str:
    line = line.strip()
    if not line:
        return ""
    line = re.sub(r"\s+", " ", line)
    return line


def card_matches_paragraph(card_norm: str, paragraph_norm: str) -> bool:
    if len(card_norm) < 8 or not paragraph_norm:
        return False
    if card_norm in paragraph_norm:
        return True
    return len(card_norm) > 30 and card_norm[:30] in paragraph_norm


def attach_cards_to_paragraphs(
    sections: list[dict[str, Any]],
    cards: list[dict[str, Any]],
    exam_card_ids: set[str],
) -> dict[str, int]:
    searchable_cards = [
        {
            "card_id": card.get("card_id"),
            "citation_norm": normalize_text(card.get("citation", "")),
        }
        for card in cards
        if card.get("card_id") and len(normalize_text(card.get("citation", ""))) >= 8
    ]

    matched_cards: set[str] = set()
    paragraphs_with_cards = 0
    highlight_instances = 0

    for section in sections:
        for subsection in section["subsections"]:
            for paragraph in subsection["paragraphs"]:
                paragraph_norm = normalize_text(paragraph["text"])
                card_ids = []
                for card in searchable_cards:
                    cid = card["card_id"]
                    if cid and card_matches_paragraph(card["citation_norm"], paragraph_norm):
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


def find_matching_card_ids(cards: list[dict[str, Any]], title: str, text: str) -> list[str]:
    title_norm = normalize_text(title)
    text_norm = normalize_text(text)
    combined_norm = normalize_text(f"{title} {text}")
    ids: list[str] = []
    for card in cards:
        cid = card.get("card_id")
        if not cid:
            continue
        citation_norm = normalize_text(card.get("citation", ""))
        knowledge_norm = normalize_text(card.get("knowledge", ""))
        if not citation_norm and not knowledge_norm:
            continue
        matched = False
        if citation_norm and (
            citation_norm in combined_norm
            or combined_norm in citation_norm
            or citation_norm in text_norm
            or text_norm in citation_norm
        ):
            matched = True
        if not matched and knowledge_norm and (
            knowledge_norm in combined_norm
            or combined_norm in knowledge_norm
            or knowledge_norm in text_norm
            or text_norm in knowledge_norm
        ):
            matched = True
        if matched:
            ids.append(cid)
    return ids


def build_glossary_appendix(cards: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not V6_CHAPTER.exists():
        return None
    chapter = read_json(V6_CHAPTER)
    glossary = next(
        (
            section
            for section in chapter.get("sections", [])
            if str(section.get("section_title", "")).strip() in {"詞彙", "词汇", "术语", "術語"}
        ),
        None,
    )
    if not glossary:
        return None

    appendix_section = {
        "section_id": "appendix-glossary",
        "number": "A",
        "section_title": "附录：术语表",
        "display_title": "附录：术语表",
        "is_appendix": True,
        "appendix_type": "glossary",
        "source_section_id": glossary.get("section_id", ""),
        "subsections": [],
    }

    for index, subsection in enumerate(glossary.get("subsections", []), start=1):
        paragraphs = []
        title = subsection.get("title", "") or subsection.get("display_title", "") or f"术语 {index}"
        for paragraph in subsection.get("paragraphs", []):
            text = clean_paragraph(paragraph.get("text", ""))
            if not text:
                continue
            card_ids = paragraph.get("card_ids", []) or find_matching_card_ids(cards, title, text)
            paragraphs.append(
                {
                    "text": text,
                    "card_ids": card_ids,
                    "highlight_card_ids": [],
                    "source_line_start": paragraph.get("source_line_start", ""),
                    "source_line_end": paragraph.get("source_line_end", ""),
                    "is_appendix": True,
                }
            )
        if not paragraphs:
            continue
        appendix_section["subsections"].append(
            {
                "number": f"A.{index}",
                "title": title,
                "display_title": f"A.{index} {title}",
                "heading_level": subsection.get("heading_level", 4),
                "is_appendix": True,
                "paragraphs": paragraphs,
            }
        )

    return appendix_section if appendix_section["subsections"] else None


def new_subsection(section_number: str, title: str, level: int, index: int) -> dict[str, Any]:
    number = f"{section_number}.{index}"
    return {
        "number": number,
        "title": title,
        "display_title": f"{number} {title}",
        "heading_level": level,
        "paragraphs": [],
    }


def build_chapter() -> dict[str, Any]:
    if not SOURCE_MD.exists():
        raise FileNotFoundError(SOURCE_MD)

    cards = load_cards(V6_CARDS)
    exam_points = read_json(EXAM_POINTS) if EXAM_POINTS.exists() else {"exam_points": []}
    exam_card_ids = {
        cid
        for ep in exam_points.get("exam_points", [])
        for cid in ep.get("source_card_ids", [])
    }

    chapter_title = "洗钱和恐怖融资活动的风险及方法"
    sections: OrderedDict[str, dict[str, Any]] = OrderedDict()
    current_section: dict[str, Any] | None = None
    current_subsection: dict[str, Any] | None = None
    section_count = 0
    subsection_count = 0

    for line_no, raw_line in enumerate(SOURCE_MD.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        heading = markdown_heading(line)
        if heading:
            level, title = heading
            if level == 2:
                chapter_title = title
                continue
            if level == 3:
                section_count += 1
                subsection_count = 0
                section_number = f"2.{section_count}"
                current_section = {
                    "section_id": section_number,
                    "number": section_number,
                    "section_title": title,
                    "display_title": f"{section_number} {title}",
                    "subsections": [],
                }
                sections[section_number] = current_section
                current_subsection = None
                continue
            if level >= 4:
                if current_section is None:
                    section_count += 1
                    section_number = f"2.{section_count}"
                    current_section = {
                        "section_id": section_number,
                        "number": section_number,
                        "section_title": "未分组",
                        "display_title": f"{section_number} 未分组",
                        "subsections": [],
                    }
                    sections[section_number] = current_section
                subsection_count += 1
                current_subsection = new_subsection(current_section["number"], title, level, subsection_count)
                current_section["subsections"].append(current_subsection)
                continue

        text = clean_paragraph(line)
        if not text:
            continue
        if current_section is None:
            section_count += 1
            section_number = f"2.{section_count}"
            current_section = {
                "section_id": section_number,
                "number": section_number,
                "section_title": "正文",
                "display_title": f"{section_number} 正文",
                "subsections": [],
            }
            sections[section_number] = current_section
        if current_subsection is None:
            subsection_count += 1
            current_subsection = new_subsection(current_section["number"], "正文", 4, subsection_count)
            current_section["subsections"].append(current_subsection)
        current_subsection["paragraphs"].append(
            {
                "text": text,
                "card_ids": [],
                "highlight_card_ids": [],
                "source_line_start": line_no,
                "source_line_end": line_no,
            }
        )

    section_list = []
    for section in sections.values():
        section["subsections"] = [
            subsection for subsection in section["subsections"] if subsection["paragraphs"]
        ]
        if section["subsections"]:
            section_list.append(section)

    attach_stats = attach_cards_to_paragraphs(section_list, cards, exam_card_ids)
    appendix = build_glossary_appendix(cards)
    if appendix:
        section_list.append(appendix)

    return {
        "chapter": chapter_title,
        "asset_note": (
            "Reader structure generated from v6教材原文/ch2_extracted.md. "
            "card_ids/highlight_card_ids are best-effort matches against the current cards_v6_sentence.json."
        ),
        "evidence_scope": "v6_sentence",
        "source_file": str(SOURCE_MD),
        "sections": section_list,
        "stats": {
            "source_file": str(SOURCE_MD),
            "sections": len(section_list),
            "subsections": sum(len(section["subsections"]) for section in section_list),
            "paragraphs": sum(
                len(subsection["paragraphs"])
                for section in section_list
                for subsection in section["subsections"]
            ),
            **attach_stats,
        },
    }


def main() -> int:
    chapter = build_chapter()
    write_json(OUT_CHAPTER, chapter)
    print(
        "Saved {path} | sections={sections} subsections={subsections} paragraphs={paragraphs} "
        "matched_cards={matched_cards} highlights={highlights}".format(
            path=OUT_CHAPTER,
            sections=chapter["stats"]["sections"],
            subsections=chapter["stats"]["subsections"],
            paragraphs=chapter["stats"]["paragraphs"],
            matched_cards=chapter["stats"]["matched_cards"],
            highlights=chapter["stats"]["highlight_instances"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
