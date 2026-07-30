from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import fitz

from .config import settings


@lru_cache(maxsize=1)
def load_kg() -> dict[str, Any]:
    return json.loads(settings.kg_path.read_text(encoding="utf-8"))


def search_kg(
    query: str = "",
    chapter_id: str | None = None,
    section_id: str | None = None,
    core_point_id: str | None = None,
    limit: int = 40,
) -> dict[str, Any]:
    data = load_kg()
    query_cf = query.casefold().strip()
    core_points = data.get("core_points", [])
    units = data.get("units", [])
    cp_unit_ids: set[str] | None = None
    if core_point_id:
        cp = next((item for item in core_points if item.get("core_point_id") == core_point_id), None)
        cp_unit_ids = set((cp or {}).get("anchor_unit_ids", []) + (cp or {}).get("support_unit_ids", []))

    def matches(item: dict[str, Any], fields: list[str]) -> bool:
        if chapter_id and item.get("chapter_id") != chapter_id:
            return False
        if section_id and item.get("section_id") != section_id:
            return False
        if query_cf and not any(query_cf in str(item.get(field, "")).casefold() for field in fields):
            return False
        return True

    matched_cps = [
        item
        for item in core_points
        if matches(item, ["core_point_id", "title_zh", "title_en", "reason"])
    ][:limit]
    matched_units = [
        item
        for item in units
        if (cp_unit_ids is None or item.get("unit_id") in cp_unit_ids)
        and matches(item, ["unit_id", "knowledge_zh", "en_quote", "real_section"])
    ][:limit]
    return {"core_points": matched_cps, "units": matched_units}


def get_unit(unit_id: str) -> dict[str, Any] | None:
    data = load_kg()
    unit = next((item for item in data.get("units", []) if item.get("unit_id") == unit_id), None)
    if not unit:
        return None
    section = next(
        (item for item in data.get("sections", []) if item.get("section_id") == unit.get("section_id")),
        None,
    )
    chapter = next(
        (item for item in data.get("chapters", []) if item.get("chapter_id") == unit.get("chapter_id")),
        None,
    )
    return {**unit, "section": section, "chapter": chapter}


def resolve_textbook_pdf(language: str) -> tuple[Path, int]:
    if language not in {"zh", "en"}:
        raise ValueError("language must be zh or en")
    active = json.loads((settings.textbook_release_root / "textbook-active.json").read_text(encoding="utf-8"))
    release_dir = (settings.textbook_release_root / active["release_path"]).resolve()
    if settings.textbook_release_root not in release_dir.parents:
        raise ValueError("invalid textbook release path")
    manifest = json.loads((release_dir / "manifest.json").read_text(encoding="utf-8"))
    asset = manifest["assets"]["zh_pdf" if language == "zh" else "en_pdf"]
    pdf_path = (release_dir / asset).resolve()
    if release_dir not in pdf_path.parents:
        raise ValueError("invalid textbook asset")
    return pdf_path, int(manifest["counts"]["bilingual_pdf_pages"])


def render_source_page(page: int, language: str = "zh", scale: float = 1.3) -> bytes:
    path, total = resolve_textbook_pdf(language)
    if page < 1 or page > total:
        raise ValueError(f"page must be between 1 and {total}")
    document = fitz.open(path)
    try:
        pixmap = document[page - 1].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        return pixmap.tobytes("png")
    finally:
        document.close()
