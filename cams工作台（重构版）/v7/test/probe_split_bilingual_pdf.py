from __future__ import annotations

from pathlib import Path

import fitz


ROOT = Path(r"D:\守正公司工作区\cams考试")
PDF_PATH = ROOT / r"教材、答疑记录、习题与参考文献\教材原文\v7\CAMS英文版7.0（中英对照版）.pdf"
OUT_DIR = ROOT / r"cams工作台（重构版）\v7\test\output\split_pdf_probe"

# 1-based physical PDF pages. Covers cover, acknowledgements, TOC, normal text,
# list-heavy pages, late glossary-like pages, and technology pages.
SAMPLE_PAGES = [1, 2, 9, 15, 51, 62, 63, 64, 65, 66, 251, 403, 547]


def add_cropped_page(target: fitz.Document, source_doc: fitz.Document, page_index: int, clip: fitz.Rect) -> None:
    width = clip.width
    height = clip.height
    page = target.new_page(width=width, height=height)
    page.show_pdf_page(fitz.Rect(0, 0, width, height), source_doc, page_index, clip=clip)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source = fitz.open(PDF_PATH)

    zh_doc = fitz.open()
    en_doc = fitz.open()
    map_rows = []

    for physical_page in SAMPLE_PAGES:
        page_index = physical_page - 1
        page = source[page_index]
        rect = page.rect

        # The bilingual PDF uses a very stable two-column layout:
        # left half Chinese, right half English. Keep headers/footers for page numbers.
        split_x = rect.width / 2
        zh_clip = fitz.Rect(0, 0, split_x, rect.height)
        en_clip = fitz.Rect(split_x, 0, rect.width, rect.height)

        add_cropped_page(zh_doc, source, page_index, zh_clip)
        add_cropped_page(en_doc, source, page_index, en_clip)

        map_rows.append(
            {
                "source_physical_page": physical_page,
                "zh_probe_page": len(zh_doc),
                "en_probe_page": len(en_doc),
                "split_x": round(split_x, 2),
                "source_width": round(rect.width, 2),
                "source_height": round(rect.height, 2),
            }
        )

    zh_path = OUT_DIR / "v7_zh_split_probe.pdf"
    en_path = OUT_DIR / "v7_en_split_probe.pdf"
    map_path = OUT_DIR / "split_probe_page_map.json"
    zh_doc.save(zh_path)
    en_doc.save(en_path)
    map_path.write_text(
        __import__("json").dumps(
            {
                "schema_version": "v7_split_pdf_probe_v1",
                "source_pdf": str(PDF_PATH),
                "sample_pages": SAMPLE_PAGES,
                "method": "crop_left_right_halves",
                "items": map_rows,
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
