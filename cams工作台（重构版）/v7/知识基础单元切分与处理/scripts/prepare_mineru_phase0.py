from __future__ import annotations

import html
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import fitz


V7_DIR = Path(__file__).resolve().parents[2]
ROOT = V7_DIR.parents[1]
WORK_DIR = V7_DIR / "work"
SOURCES_DIR = WORK_DIR / "sources"
AUDIT_DIR = WORK_DIR / "audit"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compact_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def visible_text_from_md(text: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", text)
    text = text.replace("|", " ")
    text = html.unescape(text)
    return compact_spaces(text)


def normalize_for_match(text: str) -> str:
    text = visible_text_from_md(text).lower()
    return "".join(ch for ch in text if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def ngrams(text: str, n: int = 8) -> set[str]:
    if len(text) < n:
        return {text} if text else set()
    step = 2 if len(text) > 300 else 1
    return {text[i : i + n] for i in range(0, len(text) - n + 1, step)}


def language_stats(text: str) -> dict[str, int | float]:
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    letters = sum(1 for ch in text if ("A" <= ch <= "Z") or ("a" <= ch <= "z"))
    chars = len(text)
    return {
        "chars": chars,
        "cjk": cjk,
        "letters": letters,
        "cjk_ratio": round(cjk / max(chars, 1), 4),
        "letter_ratio": round(letters / max(chars, 1), 4),
    }


def find_mineru_files() -> tuple[Path, list[Path], list[Path]]:
    zh_files = sorted(ROOT.rglob("MinerU_markdown_v7_zh_split_*.md"))
    en_files = sorted(ROOT.rglob("MinerU_markdown_v7_en_split_*.md"))
    zh_files = [p for p in zh_files if WORK_DIR not in p.parents]
    en_files = [p for p in en_files if WORK_DIR not in p.parents]
    if not zh_files or not en_files:
        raise FileNotFoundError("Cannot find v7 zh/en MinerU markdown files.")

    zh_roots = {p.parent.parent for p in zh_files}
    en_roots = {p.parent.parent for p in en_files}
    common_roots = zh_roots & en_roots
    if not common_roots:
        raise RuntimeError(f"Cannot infer shared MinerU root: zh={zh_roots}, en={en_roots}")
    if len(common_roots) > 1:
        # Prefer the newest root by markdown mtime if multiple extractions exist.
        common_roots = {
            max(
                common_roots,
                key=lambda root: max(p.stat().st_mtime for p in list(root.rglob("*.md"))),
            )
        }
    mineru_root = next(iter(common_roots))
    zh_files = [p for p in zh_files if p.parent.parent == mineru_root]
    en_files = [p for p in en_files if p.parent.parent == mineru_root]
    return mineru_root, sorted(zh_files), sorted(en_files)


def merge_markdown(files: list[Path], out_path: Path, lang: str) -> dict[str, object]:
    parts = []
    source_items = []
    for index, path in enumerate(files, start=1):
        text = read_text(path)
        source_items.append(
            {
                "index": index,
                "path": str(path),
                "name": path.name,
                "chars": len(text),
                "headings": len(re.findall(r"(?m)^#{1,6}\s+", text)),
                "html_tables": text.count("<table"),
                "mtime": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
            }
        )
        parts.append(
            "\n\n".join(
                [
                    f"<!-- MINERU_MERGE_SOURCE lang={lang} index={index} file={path.name} -->",
                    text.strip(),
                ]
            )
        )
    merged = "\n\n".join(parts).strip() + "\n"
    out_path.write_text(merged, encoding="utf-8")
    stats = language_stats(merged)
    stats.update(
        {
            "output_path": str(out_path),
            "source_count": len(files),
            "sources": source_items,
            "headings": len(re.findall(r"(?m)^#{1,6}\s+", merged)),
            "html_tables": merged.count("<table"),
            "markdown_page_markers": len(re.findall(r"<!--\s*PAGE\s*\d+\s*-->", merged)),
        }
    )
    return stats


def extract_pdf_pages(pdf_path: Path, lang: str, page_map: list[dict[str, object]]) -> list[dict[str, object]]:
    try:
        fitz.TOOLS.mupdf_display_errors(False)
    except Exception:
        pass
    doc = fitz.open(str(pdf_path))
    pages = []
    for page_index, page in enumerate(doc):
        raw = page.get_text("text") or ""
        text = compact_spaces(raw)
        map_item = page_map[page_index] if page_index < len(page_map) else {}
        printed_key = f"{lang}_printed_page"
        pages.append(
            {
                "lang": lang,
                "pdf_page": page_index + 1,
                "printed_page": map_item.get(printed_key),
                "text": text,
                "norm": normalize_for_match(text),
                "chars": len(text),
                **language_stats(text),
            }
        )
    doc.close()
    return pages


def split_md_blocks(text: str, lang: str) -> list[dict[str, object]]:
    raw_blocks = []
    current: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        is_heading = bool(re.match(r"^#{1,6}\s+", stripped))
        if is_heading and current:
            raw_blocks.append("\n".join(current).strip())
            current = []
        if not stripped:
            if current:
                raw_blocks.append("\n".join(current).strip())
                current = []
            continue
        current.append(line)
    if current:
        raw_blocks.append("\n".join(current).strip())

    blocks = []
    for block in raw_blocks:
        visible = visible_text_from_md(block)
        norm = normalize_for_match(block)
        if not visible:
            continue
        block_type = "heading" if re.match(r"^#{1,6}\s+", block.strip()) else "table" if "<table" in block else "text"
        blocks.append(
            {
                "block_index": len(blocks) + 1,
                "lang": lang,
                "block_type": block_type,
                "text": visible,
                "norm": norm,
                "chars": len(visible),
            }
        )
    return blocks


def align_blocks_to_pages(blocks: list[dict[str, object]], pages: list[dict[str, object]]) -> dict[str, object]:
    page_sets = {int(p["pdf_page"]): ngrams(str(p["norm"])) for p in pages}
    page_lookup = {int(p["pdf_page"]): p for p in pages}
    current_page = 1
    results = []
    direct = inherited = unmatched = 0

    for block in blocks:
        norm = str(block["norm"])
        visible = str(block["text"])
        result = {
            "block_index": block["block_index"],
            "block_type": block["block_type"],
            "chars": block["chars"],
            "text_sample": visible[:160],
            "pdf_page": None,
            "printed_page": None,
            "match_method": "unmatched",
            "match_score": 0.0,
        }

        if len(norm) < 24:
            if current_page:
                p = page_lookup[current_page]
                result.update(
                    {
                        "pdf_page": current_page,
                        "printed_page": p.get("printed_page"),
                        "match_method": "inherit_short_block",
                        "match_score": 0.2,
                    }
                )
                inherited += 1
            else:
                unmatched += 1
            results.append(result)
            continue

        # Short labels/headings are common in tables, figures, and flow diagrams.
        # They should not be allowed to jump dozens of pages based on weak n-gram
        # overlap; otherwise the sequential matcher loses the real page position.
        if len(norm) < 90:
            candidate_start = max(1, current_page - 2)
            candidate_end = min(len(pages), current_page + 8)
            exact_hits = []
            for page_no in range(candidate_start, candidate_end + 1):
                page_norm = str(page_lookup[page_no]["norm"])
                if norm in page_norm:
                    exact_hits.append(page_no)
            if exact_hits:
                best_page = min(exact_hits, key=lambda page_no: abs(page_no - current_page))
                p = page_lookup[best_page]
                result.update(
                    {
                        "pdf_page": best_page,
                        "printed_page": p.get("printed_page"),
                        "match_method": "short_exact_nearby",
                        "match_score": 0.88,
                    }
                )
                current_page = best_page
                direct += 1
            elif current_page:
                p = page_lookup[current_page]
                result.update(
                    {
                        "pdf_page": current_page,
                        "printed_page": p.get("printed_page"),
                        "match_method": "inherit_short_unmatched",
                        "match_score": 0.18,
                    }
                )
                inherited += 1
            else:
                unmatched += 1
            results.append(result)
            continue

        candidate_start = max(1, current_page - 2)
        candidate_end = min(len(pages), current_page + 35)
        block_grams = ngrams(norm)
        best_page = None
        best_score = 0.0
        first_anchor = norm[: min(80, len(norm))]
        mid_start = max(0, len(norm) // 2 - 40)
        mid_anchor = norm[mid_start : mid_start + 80]

        for page_no in range(candidate_start, candidate_end + 1):
            page_norm = str(page_lookup[page_no]["norm"])
            score = 0.0
            if first_anchor and first_anchor in page_norm:
                score = max(score, 0.96)
            if mid_anchor and len(mid_anchor) >= 30 and mid_anchor in page_norm:
                score = max(score, 0.9)
            if score < 0.9 and block_grams:
                overlap = len(block_grams & page_sets[page_no])
                score = max(score, overlap / max(len(block_grams), 1))
            if score > best_score:
                best_page = page_no
                best_score = score

        if best_page is not None and best_score >= 0.28:
            p = page_lookup[best_page]
            result.update(
                {
                    "pdf_page": best_page,
                    "printed_page": p.get("printed_page"),
                    "match_method": "direct_ngram_or_anchor",
                    "match_score": round(best_score, 4),
                }
            )
            current_page = best_page
            direct += 1
        else:
            unmatched += 1
        results.append(result)

    return {
        "items": results,
        "stats": {
            "total_blocks": len(blocks),
            "direct_matches": direct,
            "inherited_short_blocks": inherited,
            "unmatched": unmatched,
            "direct_match_rate": round(direct / max(len(blocks), 1), 4),
            "usable_match_rate": round((direct + inherited) / max(len(blocks), 1), 4),
        },
    }


def build_inventory(
    mineru_root: Path,
    zh_files: list[Path],
    en_files: list[Path],
    zh_merge_stats: dict[str, object],
    en_merge_stats: dict[str, object],
    zh_pages: list[dict[str, object]],
    en_pages: list[dict[str, object]],
    page_map: dict[str, object],
) -> dict[str, object]:
    def page_stats(pages: list[dict[str, object]]) -> dict[str, object]:
        chars = [int(p["chars"]) for p in pages]
        low = [p["pdf_page"] for p in pages if int(p["chars"]) < 50]
        return {
            "page_count": len(pages),
            "chars_min": min(chars),
            "chars_max": max(chars),
            "chars_median": sorted(chars)[len(chars) // 2],
            "low_text_pages": low,
        }

    return {
        "schema_version": "v7_mineru_inventory_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mineru_root": str(mineru_root),
        "source_files": {
            "zh": [str(p) for p in zh_files],
            "en": [str(p) for p in en_files],
        },
        "merged_markdown": {
            "zh": zh_merge_stats,
            "en": en_merge_stats,
        },
        "split_pdfs": {
            "zh_pdf": str(SOURCES_DIR / "v7_zh_split.pdf"),
            "en_pdf": str(SOURCES_DIR / "v7_en_split.pdf"),
            "page_map": str(SOURCES_DIR / "v7_split_page_map.json"),
            "page_map_count": page_map.get("page_count"),
        },
        "pdf_text_stats": {
            "zh": page_stats(zh_pages),
            "en": page_stats(en_pages),
        },
    }


def write_report(
    path: Path,
    inventory: dict[str, object],
    zh_align: dict[str, object],
    en_align: dict[str, object],
) -> None:
    zh_stats = zh_align["stats"]
    en_stats = en_align["stats"]
    lines = [
        "# v7 MinerU Phase 0/1 Quality Report",
        "",
        f"Generated at: {inventory['generated_at']}",
        "",
        "## Conclusion",
        "",
        "- The split zh/en PDFs are usable as page anchors.",
        "- The new MinerU markdown files are usable as structured text sources.",
        "- MinerU markdown contains no page markers, so page attribution must come from split PDF page text matching.",
        "- No term replacement has been applied in this phase; zh text remains raw MinerU output.",
        "",
        "## Outputs",
        "",
        f"- zh merged md: `{inventory['merged_markdown']['zh']['output_path']}`",
        f"- en merged md: `{inventory['merged_markdown']['en']['output_path']}`",
        f"- page aligned text: `{SOURCES_DIR / 'v7_page_aligned_text.json'}`",
        f"- block-page matches: `{SOURCES_DIR / 'v7_mineru_block_page_matches.json'}`",
        "",
        "## MinerU Markdown",
        "",
        "| Lang | Source files | Chars | Headings | HTML tables | PAGE markers |",
        "|---|---:|---:|---:|---:|---:|",
        f"| zh | {inventory['merged_markdown']['zh']['source_count']} | {inventory['merged_markdown']['zh']['chars']} | {inventory['merged_markdown']['zh']['headings']} | {inventory['merged_markdown']['zh']['html_tables']} | {inventory['merged_markdown']['zh']['markdown_page_markers']} |",
        f"| en | {inventory['merged_markdown']['en']['source_count']} | {inventory['merged_markdown']['en']['chars']} | {inventory['merged_markdown']['en']['headings']} | {inventory['merged_markdown']['en']['html_tables']} | {inventory['merged_markdown']['en']['markdown_page_markers']} |",
        "",
        "## PDF Page Text",
        "",
        "| Lang | Pages | Median chars | Low text pages |",
        "|---|---:|---:|---|",
        f"| zh | {inventory['pdf_text_stats']['zh']['page_count']} | {inventory['pdf_text_stats']['zh']['chars_median']} | {inventory['pdf_text_stats']['zh']['low_text_pages']} |",
        f"| en | {inventory['pdf_text_stats']['en']['page_count']} | {inventory['pdf_text_stats']['en']['chars_median']} | {inventory['pdf_text_stats']['en']['low_text_pages']} |",
        "",
        "## MinerU Block Page Matching",
        "",
        "| Lang | Blocks | Direct | Inherited short | Unmatched | Usable rate |",
        "|---|---:|---:|---:|---:|---:|",
        f"| zh | {zh_stats['total_blocks']} | {zh_stats['direct_matches']} | {zh_stats['inherited_short_blocks']} | {zh_stats['unmatched']} | {zh_stats['usable_match_rate']} |",
        f"| en | {en_stats['total_blocks']} | {en_stats['direct_matches']} | {en_stats['inherited_short_blocks']} | {en_stats['unmatched']} | {en_stats['usable_match_rate']} |",
        "",
        "## Decision",
        "",
        "Phase 1 should use `resplit_from_md`: English MinerU markdown is the main unit-cutting anchor, Chinese MinerU markdown is the display/alignment source, and split PDF page text is the page attribution source.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    mineru_root, zh_files, en_files = find_mineru_files()
    zh_merged_path = mineru_root / "v7_zh_mineru_merged.md"
    en_merged_path = mineru_root / "v7_en_mineru_merged.md"

    zh_merge_stats = merge_markdown(zh_files, zh_merged_path, "zh")
    en_merge_stats = merge_markdown(en_files, en_merged_path, "en")

    page_map_path = SOURCES_DIR / "v7_split_page_map.json"
    page_map = json.loads(read_text(page_map_path))
    page_items = list(page_map.get("items", []))

    zh_pages = extract_pdf_pages(SOURCES_DIR / "v7_zh_split.pdf", "zh", page_items)
    en_pages = extract_pdf_pages(SOURCES_DIR / "v7_en_split.pdf", "en", page_items)
    page_aligned_text = {
        "schema_version": "v7_page_aligned_text_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": {
            "zh_pdf": str(SOURCES_DIR / "v7_zh_split.pdf"),
            "en_pdf": str(SOURCES_DIR / "v7_en_split.pdf"),
            "page_map": str(page_map_path),
        },
        "items": [
            {
                "pdf_page": zh_pages[i]["pdf_page"],
                "zh_printed_page": zh_pages[i]["printed_page"],
                "en_printed_page": en_pages[i]["printed_page"],
                "zh_text": zh_pages[i]["text"],
                "en_text": en_pages[i]["text"],
                "zh_chars": zh_pages[i]["chars"],
                "en_chars": en_pages[i]["chars"],
            }
            for i in range(min(len(zh_pages), len(en_pages)))
        ],
    }
    write_json(SOURCES_DIR / "v7_page_aligned_text.json", page_aligned_text)

    zh_blocks = split_md_blocks(read_text(zh_merged_path), "zh")
    en_blocks = split_md_blocks(read_text(en_merged_path), "en")
    zh_align = align_blocks_to_pages(zh_blocks, zh_pages)
    en_align = align_blocks_to_pages(en_blocks, en_pages)
    write_json(
        SOURCES_DIR / "v7_mineru_block_page_matches.json",
        {
            "schema_version": "v7_mineru_block_page_matches_v1",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "method": "sequential_anchor_ngram_match_against_split_pdf_page_text",
            "zh": zh_align,
            "en": en_align,
        },
    )

    inventory = build_inventory(
        mineru_root,
        zh_files,
        en_files,
        zh_merge_stats,
        en_merge_stats,
        zh_pages,
        en_pages,
        page_map,
    )
    write_json(AUDIT_DIR / "v7_mineru_inventory.json", inventory)

    decision = {
        "schema_version": "v7_granularity_decision_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "decision": "resplit_from_md",
        "existing_card_granularity": "mixed",
        "reason": "New split MinerU markdown provides better zh/en separated structure, but has no page markers. Use English MinerU markdown as the unit-cutting anchor, Chinese MinerU markdown as the display source, and split PDF text for page attribution.",
        "phase1_input": "source_md",
        "risk_flags": ["mineru_md_has_no_page_markers", "zh_terms_not_corrected_yet"],
    }
    write_json(AUDIT_DIR / "v7_granularity_decision.json", decision)
    write_report(AUDIT_DIR / "v7_mineru_quality_report.md", inventory, zh_align, en_align)

    print(f"mineru_root: {mineru_root}")
    print(f"wrote: {zh_merged_path}")
    print(f"wrote: {en_merged_path}")
    print(f"wrote: {SOURCES_DIR / 'v7_page_aligned_text.json'}")
    print(f"wrote: {SOURCES_DIR / 'v7_mineru_block_page_matches.json'}")
    print(f"wrote: {AUDIT_DIR / 'v7_mineru_inventory.json'}")
    print(f"wrote: {AUDIT_DIR / 'v7_granularity_decision.json'}")
    print(f"wrote: {AUDIT_DIR / 'v7_mineru_quality_report.md'}")
    print("zh_match:", zh_align["stats"])
    print("en_match:", en_align["stats"])


if __name__ == "__main__":
    main()
