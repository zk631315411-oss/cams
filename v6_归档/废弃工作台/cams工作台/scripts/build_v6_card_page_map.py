from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PAGE_MARK_RE = re.compile(r"(?:页面|頁面)\s*(\d+)")


@dataclass(frozen=True)
class PageText:
    physical_page: int
    text: str
    normalized: str
    extracted_textbook_page: int | None


def normalize_for_match(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    return "".join(ch for ch in text if ch.isalnum())


def short_text(value: str, limit: int = 120) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def merge_card_payloads(paths: list[Path]) -> dict[str, Any]:
    cards: list[dict[str, Any]] = []
    seen: set[str] = set()
    sources: list[str] = []
    duplicate_count = 0
    for path in paths:
        if not path.exists():
            continue
        payload = read_json(path)
        sources.append(str(path))
        for card in payload.get("cards") or []:
            cid = str(card.get("card_id") or "")
            if not cid:
                continue
            if cid in seen:
                duplicate_count += 1
                continue
            seen.add(cid)
            cards.append(card)
    return {
        "source_files": sources,
        "duplicate_count": duplicate_count,
        "cards": cards,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def extract_textbook_page(text: str) -> int | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    head = "\n".join(lines[:12])
    match = PAGE_MARK_RE.search(head)
    if not match:
        return None
    return int(match.group(1))


def load_pdf_pages(pdf_path: Path) -> list[PageText]:
    try:
        import fitz  # type: ignore
    except Exception as exc:  # pragma: no cover - environment guard
        raise RuntimeError("PyMuPDF is required. Install package 'pymupdf'.") from exc

    doc = fitz.open(pdf_path)
    pages: list[PageText] = []
    for index, page in enumerate(doc, start=1):
        text = page.get_text()
        pages.append(
            PageText(
                physical_page=index,
                text=text,
                normalized=normalize_for_match(text),
                extracted_textbook_page=extract_textbook_page(text),
            )
        )
    return pages


def build_pdf_page_map(pages: list[PageText], pdf_path: Path) -> dict[str, Any]:
    detected_offsets = [
        page.physical_page - page.extracted_textbook_page
        for page in pages
        if page.extracted_textbook_page is not None
    ]
    offset_counts = Counter(detected_offsets)
    common_offset = offset_counts.most_common(1)[0][0] if offset_counts else None
    common_offset_count = offset_counts.most_common(1)[0][1] if offset_counts else 0

    page_items: list[dict[str, Any]] = []
    for page in pages:
        textbook_page = page.extracted_textbook_page
        method = "header"
        if textbook_page is None and common_offset is not None:
            inferred = page.physical_page - common_offset
            if inferred > 0:
                textbook_page = inferred
                method = "offset_inferred"
        page_items.append(
            {
                "physical_page": page.physical_page,
                "textbook_page": textbook_page,
                "page_label": f"P{textbook_page}" if textbook_page else "",
                "extracted_textbook_page": page.extracted_textbook_page,
                "method": method if textbook_page else "unmapped",
            }
        )

    rules = collapse_offset_rules(page_items)
    return {
        "asset_note": "PDF physical page to textbook page mapping for CAMS V6.51. Physical pages are 1-based.",
        "pdf_name": pdf_path.name,
        "pdf_path": str(pdf_path),
        "page_base": "physical_page_1_based",
        "page_count": len(pages),
        "common_offset_physical_minus_textbook": common_offset,
        "common_offset_detection_count": common_offset_count,
        "rules": rules,
        "pages": page_items,
    }


def collapse_offset_rules(page_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for item in page_items:
        physical = item["physical_page"]
        textbook = item.get("textbook_page")
        if not textbook:
            if current:
                rules.append(current)
                current = None
            continue
        offset = physical - textbook
        if current and current["offset"] == offset and physical == current["physical_end"] + 1:
            current["physical_end"] = physical
            current["textbook_end"] = textbook
            continue
        if current:
            rules.append(current)
        current = {
            "physical_start": physical,
            "physical_end": physical,
            "textbook_start": textbook,
            "textbook_end": textbook,
            "offset": offset,
        }
    if current:
        rules.append(current)
    return rules


def page_label_for_pages(physical_pages: list[int], page_lookup: dict[int, dict[str, Any]]) -> str:
    textbook_pages: list[int] = []
    for physical in physical_pages:
        textbook = page_lookup.get(physical, {}).get("textbook_page")
        if isinstance(textbook, int) and textbook > 0:
            textbook_pages.append(textbook)
    textbook_pages = sorted(set(textbook_pages))
    if not textbook_pages:
        return ""
    if len(textbook_pages) == 1:
        return f"P{textbook_pages[0]}"
    if textbook_pages == list(range(textbook_pages[0], textbook_pages[-1] + 1)):
        return f"P{textbook_pages[0]}-P{textbook_pages[-1]}"
    return "/".join(f"P{page}" for page in textbook_pages)


def make_chunks(text: str, chunk_len: int = 22, stride: int = 14) -> list[str]:
    if len(text) < 10:
        return []
    if len(text) <= chunk_len:
        return [text]
    chunks = [text[index : index + chunk_len] for index in range(0, len(text) - chunk_len + 1, stride)]
    tail = text[-chunk_len:]
    if tail not in chunks:
        chunks.append(tail)
    return chunks


def context_score(card: dict[str, Any], page: PageText) -> int:
    score = 0
    citation = normalize_for_match(card.get("citation"))
    if citation and citation in page.normalized:
        score += 100 + min(len(citation), 80)
    for field in ("context_before", "context_after"):
        context = normalize_for_match(card.get(field))
        if len(context) >= 12 and context in page.normalized:
            score += 35 + min(len(context) // 4, 20)
    for chunk in make_chunks(citation):
        if chunk in page.normalized:
            score += 12
    return score


def locate_card(card: dict[str, Any], pages: list[PageText], page_lookup: dict[int, dict[str, Any]]) -> dict[str, Any]:
    citation = str(card.get("citation") or "").strip()
    citation_norm = normalize_for_match(citation)
    if not citation_norm:
        return empty_card_page_result(card, "empty_citation")

    direct_hits = [page.physical_page for page in pages if citation_norm in page.normalized]
    if len(direct_hits) == 1:
        confidence = "high" if len(citation_norm) >= 16 else "medium"
        return card_page_result(card, direct_hits, page_lookup, "citation_normalized_exact", confidence)
    if len(direct_hits) > 1:
        scored_hits = sorted(
            ((physical, context_score(card, pages[physical - 1])) for physical in direct_hits),
            key=lambda item: item[1],
            reverse=True,
        )
        best_physical, best_score = scored_hits[0]
        second_score = scored_hits[1][1] if len(scored_hits) > 1 else 0
        if best_score >= second_score + 30:
            return card_page_result(card, [best_physical], page_lookup, "citation_exact_context_disambiguated", "medium")
        return card_page_result(
            card,
            [best_physical],
            page_lookup,
            "citation_exact_multiple_pages",
            "low",
            candidate_only=True,
            issues=[f"multiple_direct_hits:{direct_hits[:8]}"],
        )

    adjacent_hits: list[list[int]] = []
    for index in range(len(pages) - 1):
        combined = pages[index].normalized + pages[index + 1].normalized
        if citation_norm in combined:
            adjacent_hits.append([pages[index].physical_page, pages[index + 1].physical_page])
    if len(adjacent_hits) == 1:
        return card_page_result(card, adjacent_hits[0], page_lookup, "split_citation_adjacent_pages", "medium")
    if len(adjacent_hits) > 1:
        return card_page_result(
            card,
            adjacent_hits[0],
            page_lookup,
            "split_citation_multiple_candidates",
            "low",
            candidate_only=True,
            issues=[f"multiple_adjacent_hits:{adjacent_hits[:5]}"],
        )

    scored_pages = sorted(
        ((page.physical_page, context_score(card, page)) for page in pages),
        key=lambda item: item[1],
        reverse=True,
    )
    best_physical, best_score = scored_pages[0]
    second_score = scored_pages[1][1] if len(scored_pages) > 1 else 0
    if best_score >= 36 and best_score >= second_score + 18:
        return card_page_result(card, [best_physical], page_lookup, "chunk_context_score", "medium")
    if best_score >= 24 and best_score >= second_score + 8:
        return card_page_result(
            card,
            [best_physical],
            page_lookup,
            "weak_chunk_context_score",
            "low",
            candidate_only=True,
            issues=[f"weak_score:{best_score};second:{second_score}"],
        )
    return empty_card_page_result(card, "unmatched", issues=[f"best_score:{best_score};second:{second_score}"])


def card_page_result(
    card: dict[str, Any],
    physical_pages: list[int],
    page_lookup: dict[int, dict[str, Any]],
    method: str,
    confidence: str,
    candidate_only: bool = False,
    issues: list[str] | None = None,
) -> dict[str, Any]:
    physical_pages = sorted(set(physical_pages))
    label = page_label_for_pages(physical_pages, page_lookup)
    textbook_pages = sorted(
        {
            page_lookup.get(physical, {}).get("textbook_page")
            for physical in physical_pages
            if isinstance(page_lookup.get(physical, {}).get("textbook_page"), int)
        }
    )
    return {
        "card_id": card.get("card_id"),
        "physical_pages": physical_pages,
        "textbook_pages": textbook_pages,
        "page_label": "" if candidate_only else label,
        "candidate_page_label": label if candidate_only else "",
        "match_method": method,
        "confidence": confidence,
        "chapter_path": card.get("chapter_path", ""),
        "source_line_start": card.get("source_line_start"),
        "source_line_end": card.get("source_line_end"),
        "citation": card.get("citation", ""),
        "issues": issues or [],
    }


def empty_card_page_result(card: dict[str, Any], method: str, issues: list[str] | None = None) -> dict[str, Any]:
    return {
        "card_id": card.get("card_id"),
        "physical_pages": [],
        "textbook_pages": [],
        "page_label": "",
        "candidate_page_label": "",
        "match_method": method,
        "confidence": "none",
        "chapter_path": card.get("chapter_path", ""),
        "source_line_start": card.get("source_line_start"),
        "source_line_end": card.get("source_line_end"),
        "citation": card.get("citation", ""),
        "issues": issues or [],
    }


def add_sequence_inference(results: list[dict[str, Any]], page_lookup: dict[int, dict[str, Any]]) -> None:
    good = {"high", "medium"}
    for index, result in enumerate(results):
        if result.get("confidence") != "none":
            continue
        prev_result = next((r for r in reversed(results[:index]) if r.get("confidence") in good), None)
        next_result = next((r for r in results[index + 1 :] if r.get("confidence") in good), None)
        if not prev_result or not next_result:
            continue
        prev_pages = prev_result.get("physical_pages") or []
        next_pages = next_result.get("physical_pages") or []
        if not prev_pages or not next_pages:
            continue
        prev_page = max(prev_pages)
        next_page = min(next_pages)
        if prev_page > next_page or next_page - prev_page > 2:
            continue
        inferred_page = prev_page if prev_page == next_page else next_page
        label = page_label_for_pages([inferred_page], page_lookup)
        result["physical_pages"] = [inferred_page]
        textbook = page_lookup.get(inferred_page, {}).get("textbook_page")
        result["textbook_pages"] = [textbook] if isinstance(textbook, int) else []
        result["candidate_page_label"] = label
        result["match_method"] = "sequence_inferred_between_neighbor_cards"
        result["confidence"] = "low"
        result["issues"] = (result.get("issues") or []) + [
            f"inferred_between:{prev_result.get('card_id')}->{next_result.get('card_id')}"
        ]


def build_card_page_map(cards_payload: dict[str, Any], pages: list[PageText], pdf_page_map: dict[str, Any]) -> dict[str, Any]:
    cards = cards_payload.get("cards") or []
    page_lookup = {item["physical_page"]: item for item in pdf_page_map["pages"]}
    results = [locate_card(card, pages, page_lookup) for card in cards]
    add_sequence_inference(results, page_lookup)
    mapped = {str(result["card_id"]): result for result in results if result.get("card_id")}
    confidence_counts = Counter(result.get("confidence", "none") for result in results)
    method_counts = Counter(result.get("match_method", "") for result in results)
    display_ready_count = sum(1 for result in results if result.get("page_label"))
    return {
        "asset_note": "CAMS V6 sentence-card page mapping. Frontend should display page_label only; candidate_page_label is for audit only.",
        "source_cards": cards_payload.get("source_files") or cards_payload.get("source_file") or cards_payload.get("source_asset") or "cards_v6_sentence.json",
        "duplicate_count": cards_payload.get("duplicate_count", 0),
        "card_count": len(cards),
        "display_ready_count": display_ready_count,
        "confidence_counts": dict(confidence_counts),
        "method_counts": dict(method_counts),
        "cards": mapped,
    }


def choose_samples(results: list[dict[str, Any]], limit: int = 30) -> list[dict[str, Any]]:
    buckets: list[dict[str, Any]] = []
    for confidence in ("high", "medium", "low", "none"):
        bucket = [item for item in results if item.get("confidence") == confidence]
        if not bucket:
            continue
        step = max(1, len(bucket) // max(1, limit // 4))
        buckets.extend(bucket[::step][: max(3, limit // 4)])
    return buckets[:limit]


def write_report(
    report_path: Path,
    pdf_page_map: dict[str, Any],
    card_page_map: dict[str, Any],
) -> None:
    results = list(card_page_map["cards"].values())
    confidence_counts = Counter(item.get("confidence", "none") for item in results)
    method_counts = Counter(item.get("match_method", "") for item in results)
    display_ready = [item for item in results if item.get("page_label")]
    candidate_only = [item for item in results if item.get("candidate_page_label") and not item.get("page_label")]
    unmatched = [item for item in results if item.get("confidence") == "none"]
    physical_pages = [page for item in display_ready for page in item.get("physical_pages", [])]

    lines: list[str] = []
    lines.append("# V6 教材句卡页码映射报告")
    lines.append("")
    lines.append("## 总览")
    lines.append("")
    lines.append(f"- PDF 文件：`{pdf_page_map.get('pdf_name')}`")
    lines.append(f"- PDF 物理页数：{pdf_page_map.get('page_count')}")
    lines.append(f"- 常见换算偏移 physical - textbook：{pdf_page_map.get('common_offset_physical_minus_textbook')}")
    lines.append(f"- 句卡总数：{card_page_map.get('card_count')}")
    lines.append(f"- 合并时跳过重复 card_id：{card_page_map.get('duplicate_count', 0)}")
    lines.append(f"- 可直接展示页码的句卡：{card_page_map.get('display_ready_count')}")
    if results:
        ratio = card_page_map.get("display_ready_count", 0) / len(results)
        lines.append(f"- 可展示比例：{ratio:.2%}")
    lines.append(f"- 候选但不展示：{len(candidate_only)}")
    lines.append(f"- 未命中：{len(unmatched)}")
    if physical_pages:
        lines.append(f"- 可展示句卡物理页范围：{min(physical_pages)}-{max(physical_pages)}")
    lines.append("")
    lines.append("## 置信度分布")
    lines.append("")
    for key in ("high", "medium", "low", "none"):
        lines.append(f"- {key}: {confidence_counts.get(key, 0)}")
    lines.append("")
    lines.append("## 匹配方法分布")
    lines.append("")
    for method, count in method_counts.most_common():
        lines.append(f"- {method}: {count}")
    lines.append("")
    lines.append("## PDF 页码规则")
    lines.append("")
    for rule in pdf_page_map.get("rules", [])[:20]:
        lines.append(
            f"- 物理页 {rule['physical_start']}-{rule['physical_end']} => "
            f"教材 P{rule['textbook_start']}-P{rule['textbook_end']} "
            f"(offset={rule['offset']})"
        )
    lines.append("")
    lines.append("## 抽样核验")
    lines.append("")
    for item in choose_samples(results):
        label = item.get("page_label") or item.get("candidate_page_label") or "未定位"
        lines.append(f"### {item.get('card_id')} · {label} · {item.get('confidence')}")
        lines.append("")
        lines.append(f"- 匹配方法：{item.get('match_method')}")
        lines.append(f"- 物理页：{item.get('physical_pages')}")
        lines.append(f"- 教材页：{item.get('textbook_pages')}")
        lines.append(f"- 章节：{item.get('chapter_path') or '未记录'}")
        if item.get("issues"):
            lines.append(f"- 注意：{'; '.join(map(str, item.get('issues') or []))}")
        lines.append(f"- 原文：{short_text(item.get('citation', ''), 180)}")
        lines.append("")
    lines.append("## 未命中样例")
    lines.append("")
    for item in unmatched[:50]:
        lines.append(f"- `{item.get('card_id')}` · {item.get('chapter_path') or '未记录'} · {short_text(item.get('citation', ''), 120)}")
    lines.append("")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def default_paths() -> dict[str, Path]:
    workbench_root = Path(__file__).resolve().parents[1]
    project_root = workbench_root.parent
    return {
        "pdf": project_root / "教材、答疑记录、习题与参考文献" / "教材原文" / "v6" / "CAMS中文版教材-V6.51.pdf",
        "cards": workbench_root / "data" / "teaching_assets" / "cards_v6_sentence.json",
        "extra_cards": workbench_root / "data" / "cards_ch2_plus_v6_except_ch2_sentence.json",
        "pdf_page_map": workbench_root / "data" / "page_maps" / "pdf_page_map_v6.json",
        "card_page_map": workbench_root / "data" / "page_maps" / "card_page_map_v6.json",
        "report": workbench_root / "reports" / "page_maps" / "v6_card_page_map_report.md",
    }


def parse_args() -> argparse.Namespace:
    paths = default_paths()
    parser = argparse.ArgumentParser(description="Build CAMS V6 sentence-card to textbook-page mapping.")
    parser.add_argument("--pdf", type=Path, default=paths["pdf"])
    parser.add_argument("--cards", type=Path, default=paths["cards"])
    parser.add_argument("--extra-cards", type=Path, action="append", default=[paths["extra_cards"]])
    parser.add_argument("--pdf-page-map", type=Path, default=paths["pdf_page_map"])
    parser.add_argument("--card-page-map", type=Path, default=paths["card_page_map"])
    parser.add_argument("--report", type=Path, default=paths["report"])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.pdf.exists():
        raise FileNotFoundError(args.pdf)
    if not args.cards.exists():
        raise FileNotFoundError(args.cards)

    pages = load_pdf_pages(args.pdf)
    card_paths = [args.cards] + [path for path in (args.extra_cards or []) if path]
    cards_payload = merge_card_payloads(card_paths)
    pdf_page_map = build_pdf_page_map(pages, args.pdf)
    card_page_map = build_card_page_map(cards_payload, pages, pdf_page_map)
    write_json(args.pdf_page_map, pdf_page_map)
    write_json(args.card_page_map, card_page_map)
    write_report(args.report, pdf_page_map, card_page_map)

    confidence = card_page_map.get("confidence_counts", {})
    print(f"PDF pages: {pdf_page_map.get('page_count')}")
    print(f"Cards: {card_page_map.get('card_count')}")
    print(f"Display-ready: {card_page_map.get('display_ready_count')}")
    print(f"Confidence: {confidence}")
    print(f"Wrote: {args.pdf_page_map}")
    print(f"Wrote: {args.card_page_map}")
    print(f"Wrote: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
