#!/usr/bin/env python3
"""Publish the bilingual V7 textbook independently from question evidence."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_release import RELEASE_SCHEMA, ReleaseError, build_chapters, compact_unit, read_json, sha256_file, write_json


TEXTBOOK_SCHEMA = "cams-v7-textbook-release/v1"


def normalize_english_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def toc_entries(text: str, language: str) -> list[tuple[str, str]]:
    if language == "en":
        text = re.sub(r"^.*?Page\s+[ivxlcdm]+\s+", "", text, count=1, flags=re.IGNORECASE)
        text = text.split("Table of Contents", 1)[-1]
    else:
        text = re.sub(r"^.*?\u7b2c\s*[ivxlcdm]+\s*\u9875\s*", "", text, count=1, flags=re.IGNORECASE)
        text = text.split("\u76ee\u5f55", 1)[-1]
    return [(re.sub(r"\s+", " ", title).strip(), page) for title, page in re.findall(r"(.+?)\.{4,}\s*(\d+)", text)]


def bilingual_chapter_titles(aligned_path: Path, chapters: list[dict[str, Any]]) -> dict[str, str]:
    aligned = read_json(aligned_path)
    zh_entries: list[tuple[str, str]] = []
    en_entries: list[tuple[str, str]] = []
    in_toc = False
    for item in aligned.get("items") or []:
        zh_text = item.get("zh_text") or ""
        en_text = item.get("en_text") or ""
        toc_start = "\u76ee\u5f55" in zh_text and "Table of Contents" in en_text
        if toc_start:
            in_toc = True
        if not in_toc:
            continue

        zh_page = str(item.get("zh_printed_page") or "")
        en_page = str(item.get("en_printed_page") or "")
        roman_page = bool(re.fullmatch(r"[ivxlcdm]+", zh_page, re.IGNORECASE)) and bool(
            re.fullmatch(r"[ivxlcdm]+", en_page, re.IGNORECASE)
        )
        dot_leader_page = "." * 4 in zh_text and "." * 4 in en_text
        if not dot_leader_page or not (toc_start or roman_page):
            if zh_entries:
                break
            continue
        zh_entries.extend(toc_entries(zh_text, "zh"))
        en_entries.extend(toc_entries(en_text, "en"))
    if not zh_entries or len(zh_entries) != len(en_entries):
        raise ReleaseError("The aligned bilingual table of contents is incomplete")
    titles: dict[str, str] = {}
    for (en_title, en_page), (zh_title, zh_page) in zip(en_entries, zh_entries):
        if en_page != zh_page:
            raise ReleaseError(f"Bilingual table-of-contents page mismatch: {en_title!r}")
        titles[normalize_english_title(en_title)] = zh_title
    missing = [chapter["title"] for chapter in chapters if normalize_english_title(chapter["title"]) not in titles]
    if missing:
        raise ReleaseError("Missing bilingual chapter titles: " + "; ".join(missing))
    return titles


def validate_page_map(page_map: dict[str, Any], units: list[dict[str, Any]]) -> int:
    items = page_map.get("items") or []
    if not items:
        raise ReleaseError("The bilingual page map contains no pages")
    pages = set()
    for item in items:
        zh_page = item.get("zh_pdf_page")
        en_page = item.get("en_pdf_page")
        if not isinstance(zh_page, int) or not isinstance(en_page, int) or zh_page != en_page:
            raise ReleaseError("Each bilingual page-map entry must have matching zh_pdf_page and en_pdf_page")
        pages.add(zh_page)
    for unit in units:
        page = unit.get("pdf_page")
        if not isinstance(page, int) or page not in pages:
            raise ReleaseError(f"{unit.get('unit_id')}: pdf_page {page!r} is absent from the bilingual page map")
    return len(pages)


def read_explicit_chapters(path: Path, unit_ids: set[str]) -> list[dict[str, Any]]:
    payload = read_json(path)
    chapters = payload.get("items") or []
    if not chapters:
        raise ReleaseError("The explicit chapter tree contains no chapters")

    seen: set[str] = set()

    def validate_node(node: dict[str, Any]) -> None:
        direct_ids = node.get("direct_unit_ids") if "direct_unit_ids" in node else node.get("unit_ids")
        for unit_id in direct_ids or []:
            if unit_id not in unit_ids:
                raise ReleaseError(f"Chapter tree references unknown unit {unit_id!r}")
            if unit_id in seen:
                raise ReleaseError(f"Chapter tree assigns unit more than once: {unit_id}")
            seen.add(unit_id)
        for child in node.get("children") or []:
            if not isinstance(child, dict):
                raise ReleaseError("Chapter tree children must be objects")
            validate_node(child)

    for chapter in chapters:
        if not isinstance(chapter, dict) or not chapter.get("chapter_id"):
            raise ReleaseError("Each explicit chapter must have a chapter_id")
        validate_node(chapter)
    missing = unit_ids - seen
    if missing:
        raise ReleaseError(f"Chapter tree omits units: {', '.join(sorted(missing)[:5])}")
    return chapters


def create_textbook_release(args: argparse.Namespace) -> dict[str, Any]:
    units_path = Path(args.units).resolve()
    zh_pdf = Path(args.zh_pdf).resolve()
    en_pdf = Path(args.en_pdf).resolve()
    page_map_path = Path(args.page_map).resolve()
    aligned_path = Path(args.aligned_pages).resolve()
    output = Path(args.output_dir).resolve()
    for path in (zh_pdf, en_pdf):
        if not path.is_file() or path.suffix.lower() != ".pdf":
            raise ReleaseError(f"Missing bilingual textbook PDF: {path}")

    raw_units = (read_json(units_path).get("units") or [])
    if not raw_units:
        raise ReleaseError("The frozen unit source contains no units")
    units = [compact_unit(unit) for unit in raw_units]
    page_map = read_json(page_map_path)
    page_count = validate_page_map(page_map, units)

    release_id = args.release_id or datetime.now(timezone.utc).strftime("v7-textbook-%Y%m%dT%H%M%SZ")
    if not release_id.startswith("v7-textbook-"):
        raise ReleaseError("Textbook release IDs must start with 'v7-textbook-'")
    if output.exists():
        if not args.overwrite:
            raise ReleaseError(f"Textbook release output already exists: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)

    shutil.copy2(zh_pdf, output / "textbook-zh.pdf")
    shutil.copy2(en_pdf, output / "textbook-en.pdf")
    if args.chapters:
        chapters = read_explicit_chapters(Path(args.chapters).resolve(), {unit["unit_id"] for unit in units})
    else:
        chapters = build_chapters(units)
        titles = bilingual_chapter_titles(aligned_path, chapters)
        for chapter in chapters:
            chapter["title_en"] = chapter["title"]
            chapter["title_zh"] = titles[normalize_english_title(chapter["title"])]
    write_json(output / "units.json", {"schema_version": RELEASE_SCHEMA, "items": units})
    write_json(output / "chapters.json", {"schema_version": RELEASE_SCHEMA, "items": chapters})
    write_json(output / "page-map.json", page_map)

    files = {}
    for name in ("textbook-zh.pdf", "textbook-en.pdf", "units.json", "chapters.json", "page-map.json"):
        path = output / name
        files[name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    manifest = {
        "schema_version": TEXTBOOK_SCHEMA,
        "release_id": release_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "published",
        "source": {
            "units": {"path": str(units_path), "sha256": sha256_file(units_path), "freeze_manifest": args.freeze_manifest},
            "page_map": {"path": str(page_map_path), "sha256": sha256_file(page_map_path)},
            "aligned_pages": {"path": str(aligned_path), "sha256": sha256_file(aligned_path)},
            "zh_pdf": {"path": str(zh_pdf), "sha256": sha256_file(zh_pdf)},
            "en_pdf": {"path": str(en_pdf), "sha256": sha256_file(en_pdf)},
        },
        "counts": {"units": len(units), "bilingual_pdf_pages": page_count},
        "assets": {"zh_pdf": "textbook-zh.pdf", "en_pdf": "textbook-en.pdf", "page_map": "page-map.json"},
        "validation": {"valid": True, "errors": []},
        "files": files,
    }
    if args.chapters:
        chapter_path = Path(args.chapters).resolve()
        manifest["source"]["chapters"] = {"path": str(chapter_path), "sha256": sha256_file(chapter_path)}
    if args.structure_snapshot:
        snapshot_path = Path(args.structure_snapshot).resolve()
        manifest["source"]["structure_snapshot"] = {"path": str(snapshot_path), "sha256": sha256_file(snapshot_path)}
    write_json(output / "manifest.json", manifest)
    if args.activate:
        write_json(output.parent.parent / "textbook-active.json", {"schema_version": TEXTBOOK_SCHEMA, "release_id": release_id, "release_path": f"textbook/{output.name}", "manifest": f"textbook/{output.name}/manifest.json"})
    return manifest


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--units", required=True)
    parser.add_argument("--zh-pdf", required=True)
    parser.add_argument("--en-pdf", required=True)
    parser.add_argument("--page-map", required=True)
    parser.add_argument("--aligned-pages", required=True, help="v7_page_aligned_text.json containing the bilingual table of contents")
    parser.add_argument("--chapters", help="Optional explicit bilingual chapter tree JSON")
    parser.add_argument("--structure-snapshot", help="Optional source snapshot emitted by the structural remapper")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--release-id")
    parser.add_argument("--freeze-manifest", default="")
    parser.add_argument("--activate", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        result = create_textbook_release(parse_args(argv or sys.argv[1:]))
    except ReleaseError as exc:
        print(f"Textbook release failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"release_id": result["release_id"], "counts": result["counts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
