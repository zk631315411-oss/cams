from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\守正公司工作区\cams考试")
MINERU_DIR = ROOT / r"教材、答疑记录、习题与参考文献\教材原文\v7\mineru提取"
ZH_MD = ROOT / r"核心数据\源文\source\v7_中文.md"
EN_MD = ROOT / r"核心数据\源文\source\v7_英文.md"
OUT_DIR = ROOT / r"cams工作台（重构版）\v7\test\output"
MAX_UNITS_PER_THEME = 14


THEMES = [
    {
        "theme_id": "pep",
        "title_zh": "政治暴露人员风险",
        "start_pattern": r"(?m)^##\s+Politically exposed person risks\s*$",
        "stop_pattern": r"(?m)^Control and ownership play a vital role in AML efforts",
        "keywords": ["politically exposed", "PEP", "PEPs"],
    },
    {
        "theme_id": "bo_ubo",
        "title_zh": "受益所有人/最终受益所有人",
        "start_pattern": r"(?m)^Control and ownership play a vital role in AML efforts",
        "stop_pattern": r"(?m)^A concentration account is a type of account",
        "keywords": ["beneficial owner", "ultimate beneficial owner", "UBO", "BO"],
    },
    {
        "theme_id": "concentration_accounts",
        "title_zh": "集中账户",
        "start_pattern": r"(?m)^A concentration account is a type of account",
        "stop_pattern": r"(?m)^##\s+Money laundering risks associated with retail and commercial banking\s*$",
        "keywords": ["concentration account", "settlement", "sweep", "suspense", "collection account"],
    },
]


@dataclass
class PageBlock:
    page: int
    text: str
    normalized: str
    tokens: set[str] | None = None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def normalize(text: str) -> str:
    text = re.sub(r"!\[image\]\([^)]+\)", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[•·●]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def zh_ratio(text: str) -> float:
    chars = [ch for ch in text if not ch.isspace()]
    if not chars:
        return 0.0
    zh = sum(1 for ch in chars if "\u4e00" <= ch <= "\u9fff")
    return zh / len(chars)


def looks_like_english(text: str) -> bool:
    stripped = normalize(text)
    if len(stripped) < 20:
        return False
    ascii_letters = sum(1 for ch in stripped if ("a" <= ch.lower() <= "z"))
    letters_or_zh = ascii_letters + sum(1 for ch in stripped if "\u4e00" <= ch <= "\u9fff")
    if letters_or_zh == 0:
        return False
    return ascii_letters / letters_or_zh >= 0.65 and zh_ratio(stripped) < 0.08


def split_md_blocks(text: str) -> list[str]:
    blocks = []
    current: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        if line.startswith("![image]"):
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        if line.startswith("## "):
            if current:
                blocks.append("\n".join(current).strip())
            blocks.append(line)
            current = []
            continue
        if line.startswith("• ") or line.startswith("<sub>o</sub>"):
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            blocks.append(line)
            continue
        current.append(line)
    if current:
        blocks.append("\n".join(current).strip())
    return blocks


def load_mineru_text() -> tuple[str, list[Path]]:
    files = sorted(MINERU_DIR.glob("*.md"))
    joined = []
    for path in files:
        joined.append(f"\n\n<!-- MINERU_FILE {path.name} -->\n\n")
        joined.append(read_text(path))
    return "".join(joined), files


def find_theme_region(mineru_text: str, start_pattern: str, stop_pattern: str) -> str:
    start_match = re.search(start_pattern, mineru_text)
    if not start_match:
        return ""
    start = start_match.start()
    stop_match = re.search(stop_pattern, mineru_text[start_match.end() :])
    end = start_match.end() + stop_match.start() if stop_match else len(mineru_text)
    return mineru_text[start:end]


def extract_english_units(region: str, keywords: list[str]) -> list[dict]:
    blocks = split_md_blocks(region)
    units = []
    for block in blocks:
        if block.startswith("## "):
            continue
        clean = normalize(block)
        if not looks_like_english(clean):
            continue
        if not any(k.lower() in clean.lower() for k in keywords) and len(units) == 0:
            # Keep the first definition/intro paragraph only when it belongs to the section.
            pass
        if len(clean) < 30:
            continue
        unit_type = "list_item" if block.lstrip().startswith("• ") or block.lstrip().startswith("<sub>o</sub>") else "paragraph"
        units.append(
            {
                "unit_type": unit_type,
                "en_quote": clean,
                "source_block": block,
            }
        )
    return units


def parse_paged_md(path: Path) -> list[PageBlock]:
    text = read_text(path)
    matches = list(re.finditer(r"<!-- PAGE (\d+) -->", text))
    pages: list[PageBlock] = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        page = int(match.group(1))
        body = text[start:end].strip()
        normalized = normalize(body)
        pages.append(PageBlock(page=page, text=body, normalized=normalized, tokens=english_tokens(normalized)))
    return pages


TOKEN_RE = re.compile(r"[A-Za-z]{3,}|[A-Z]{2,}")


def english_tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def overlap_score(query_tokens: set[str], candidate_tokens: set[str]) -> float:
    q_tokens = query_tokens
    c_tokens = candidate_tokens
    if not q_tokens or not c_tokens:
        return 0.0
    return len(q_tokens & c_tokens) / len(q_tokens)


def find_best_pages(en_quote: str, en_pages: list[PageBlock], limit: int = 3) -> list[dict]:
    query = normalize(en_quote)
    query_tokens = english_tokens(query)
    scored = []
    query_short = query[:160]
    for page in en_pages:
        page_text = page.normalized
        contains = query_short in page_text or query[:80] in page_text
        score = overlap_score(query_tokens, page.tokens or set())
        if contains:
            score += 1.0
        if score > 0:
            scored.append(
                {
                    "page": page.page,
                    "score": round(score, 4),
                    "contains_exact_prefix": contains,
                    "en_page_sample": page_text[:420],
                }
            )
    scored.sort(key=lambda row: (-row["score"], row["page"]))
    return scored[:limit]


def get_zh_context(page: int, zh_pages_by_num: dict[int, PageBlock]) -> dict:
    page_block = zh_pages_by_num.get(page)
    if not page_block:
        return {"page": page, "zh_context": "", "found": False}
    return {
        "page": page,
        "found": True,
        "zh_context": normalize(page_block.text)[:900],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mineru_text, mineru_files = load_mineru_text()
    en_pages = parse_paged_md(EN_MD)
    zh_pages = parse_paged_md(ZH_MD)
    zh_pages_by_num = {page.page: page for page in zh_pages}

    results = {
        "schema_version": "v7_mineru_unit_alignment_test_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "inputs": {
            "mineru_files": [str(path) for path in mineru_files],
            "en_md": str(EN_MD),
            "zh_md": str(ZH_MD),
        },
        "summary": {},
        "themes": [],
    }

    total_units = 0
    matched_units = 0
    for theme in THEMES:
        region = find_theme_region(mineru_text, theme["start_pattern"], theme["stop_pattern"])
        units = extract_english_units(region, theme["keywords"])[:MAX_UNITS_PER_THEME]
        theme_rows = []
        for index, unit in enumerate(units, start=1):
            best_pages = find_best_pages(unit["en_quote"], en_pages)
            best_page = best_pages[0]["page"] if best_pages else None
            zh_context = get_zh_context(best_page, zh_pages_by_num) if best_page else {"found": False, "zh_context": ""}
            total_units += 1
            if best_page:
                matched_units += 1
            theme_rows.append(
                {
                    "temp_unit_id": f"{theme['theme_id']}_u{index:02d}",
                    "unit_type": unit["unit_type"],
                    "en_quote": unit["en_quote"],
                    "page_candidates": best_pages,
                    "best_page": best_page,
                    "zh_context_candidate": zh_context,
                }
            )
        results["themes"].append(
            {
                "theme_id": theme["theme_id"],
                "title_zh": theme["title_zh"],
                "start_pattern": theme["start_pattern"],
                "stop_pattern": theme["stop_pattern"],
                "region_found": bool(region),
                "region_chars": len(region),
                "unit_count": len(theme_rows),
                "units": theme_rows,
            }
        )

    results["summary"] = {
        "theme_count": len(THEMES),
        "total_units": total_units,
        "matched_units": matched_units,
        "page_match_rate": round(matched_units / total_units, 4) if total_units else 0,
        "mineru_file_count": len(mineru_files),
        "en_page_count": len(en_pages),
        "zh_page_count": len(zh_pages),
    }

    sample_json = OUT_DIR / "sample_units.json"
    sample_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(results, OUT_DIR / "sample_alignment_report.md")
    print(json.dumps(results["summary"], ensure_ascii=False, indent=2))
    print(f"wrote: {sample_json}")
    print(f"wrote: {OUT_DIR / 'sample_alignment_report.md'}")


def write_report(results: dict, path: Path) -> None:
    lines = [
        "# MinerU v7 Unit Alignment Test",
        "",
        f"Generated at: `{results['generated_at']}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key, value in results["summary"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Theme Samples", ""])
    for theme in results["themes"]:
        lines.extend(
            [
                f"### {theme['theme_id']}｜{theme['title_zh']}",
                "",
                f"- region_found: `{theme['region_found']}`",
                f"- region_chars: `{theme['region_chars']}`",
                f"- unit_count: `{theme['unit_count']}`",
                "",
            ]
        )
        for unit in theme["units"][:8]:
            page = unit["best_page"] or "not_found"
            zh_context = unit["zh_context_candidate"].get("zh_context", "")
            lines.extend(
                [
                    f"#### {unit['temp_unit_id']}｜{unit['unit_type']}｜page {page}",
                    "",
                    "**EN**",
                    "",
                    f"> {unit['en_quote'][:700]}",
                    "",
                    "**ZH context candidate**",
                    "",
                    f"> {zh_context[:700] if zh_context else 'NOT FOUND'}",
                    "",
                ]
            )
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
