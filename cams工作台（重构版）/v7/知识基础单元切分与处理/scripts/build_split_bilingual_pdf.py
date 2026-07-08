from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import fitz


SCRIPT_DIR = Path(__file__).resolve().parent
V7_DIR = SCRIPT_DIR.parents[1]
ROOT = V7_DIR.parents[1]
SOURCE_PDF = ROOT / "教材、答疑记录、习题与参考文献" / "教材原文" / "v7" / "CAMS英文版7.0（中英对照版）.pdf"
OUT_DIR = V7_DIR / "work" / "sources"


def extract_printed_page(text: str, lang: str) -> str | None:
    if lang == "zh":
        match = re.search(r"第\s*([0-9ivxlcdmIVXLCDM]+)\s*页", text)
    else:
        match = re.search(r"\bPage\s+([0-9ivxlcdmIVXLCDM]+)\b", text)
    return match.group(1) if match else None


def add_cropped_page(target: fitz.Document, source: fitz.Document, page_index: int, clip: fitz.Rect) -> None:
    page = target.new_page(width=clip.width, height=clip.height)
    page.show_pdf_page(fitz.Rect(0, 0, clip.width, clip.height), source, page_index, clip=clip)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    source = fitz.open(SOURCE_PDF)
    zh_doc = fitz.open()
    en_doc = fitz.open()
    page_map = []

    for page_index in range(source.page_count):
        page = source[page_index]
        rect = page.rect
        split_x = rect.width / 2

        zh_clip = fitz.Rect(0, 0, split_x, rect.height)
        en_clip = fitz.Rect(split_x, 0, rect.width, rect.height)

        add_cropped_page(zh_doc, source, page_index, zh_clip)
        add_cropped_page(en_doc, source, page_index, en_clip)

        zh_text = page.get_text("text", clip=zh_clip) or ""
        en_text = page.get_text("text", clip=en_clip) or ""

        page_map.append(
            {
                "source_bilingual_pdf_page": page_index + 1,
                "zh_pdf_page": page_index + 1,
                "en_pdf_page": page_index + 1,
                "zh_printed_page": extract_printed_page(zh_text, "zh"),
                "en_printed_page": extract_printed_page(en_text, "en"),
                "split_x": round(split_x, 2),
                "source_width": round(rect.width, 2),
                "source_height": round(rect.height, 2),
            }
        )

    zh_path = OUT_DIR / "v7_zh_split.pdf"
    en_path = OUT_DIR / "v7_en_split.pdf"
    map_path = OUT_DIR / "v7_split_page_map.json"

    zh_doc.save(zh_path, garbage=4, deflate=True)
    en_doc.save(en_path, garbage=4, deflate=True)
    map_path.write_text(
        json.dumps(
            {
                "schema_version": "v7_split_page_map_v1",
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "source_pdf": str(SOURCE_PDF),
                "method": "crop_left_right_halves",
                "page_count": source.page_count,
                "outputs": {
                    "zh_pdf": str(zh_path),
                    "en_pdf": str(en_path),
                },
                "items": page_map,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    zh_doc.close()
    en_doc.close()
    source.close()

    print(f"wrote: {zh_path}")
    print(f"wrote: {en_path}")
    print(f"wrote: {map_path}")


if __name__ == "__main__":
    main()
