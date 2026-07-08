from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
ROOT = V7_DIR.parents[1]
WORK_DIR = V7_DIR / "work"
BASE_UNITS_DIR = WORK_DIR / "base_units"
SOURCES_DIR = WORK_DIR / "sources"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compact_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def protect_angle_placeholders(text: str) -> tuple[str, dict[str, str]]:
    placeholders: dict[str, str] = {}

    def repl(match: re.Match[str]) -> str:
        inner = match.group(1).strip()
        if not inner or len(inner) > 80:
            return match.group(0)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 /&._-]*", inner):
            return match.group(0)
        key = f"@@ANGLE_PLACEHOLDER_{len(placeholders)}@@"
        placeholders[key] = f"<{inner}>"
        return key

    return re.sub(r"<([^<>]+)>", repl, text), placeholders


def visible_text_from_md(text: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text, placeholders = protect_angle_placeholders(text)
    text = re.sub(r"<[^>]+>", " ", text)
    for key, value in placeholders.items():
        text = text.replace(key, value)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", text)
    text = html.unescape(text)
    return compact_spaces(text)


def block_kind(raw: str) -> str:
    stripped = raw.strip()
    if re.match(r"^#{1,6}\s+", stripped):
        return "heading"
    if "<table" in stripped.lower():
        return "table"
    if re.match(r"^\s*[-*•]\s+", stripped):
        return "list_item"
    if re.match(r"^\s*\d+[.)]\s+", stripped):
        return "numbered_item"
    return "paragraph"


def heading_level(raw: str) -> int | None:
    match = re.match(r"^(#{1,6})\s+", raw.strip())
    return len(match.group(1)) if match else None


def split_md_blocks(text: str) -> list[dict[str, object]]:
    raw_blocks: list[str] = []
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
    for raw in raw_blocks:
        text_visible = visible_text_from_md(raw)
        if not text_visible:
            continue
        blocks.append(
            {
                "raw": raw,
                "text": text_visible,
                "block_type": block_kind(raw),
                "heading_level": heading_level(raw),
            }
        )
    return blocks


def sentence_split_en(text: str) -> list[str]:
    text = compact_spaces(text)
    if not text:
        return []
    abbreviations = {
        "e.g.",
        "i.e.",
        "u.s.",
        "u.k.",
        "u.n.",
        "mr.",
        "mrs.",
        "dr.",
        "inc.",
        "ltd.",
        "fig.",
        "no.",
        "vs.",
    }
    sentences: list[str] = []
    start = 0
    for i, ch in enumerate(text):
        if ch not in ".!?":
            continue
        tail = text[max(0, i - 10) : i + 1].lower()
        if any(tail.endswith(abbr) for abbr in abbreviations):
            continue
        if i + 1 < len(text) and text[i + 1] not in " \t\n\r\"'”’)]}":
            continue
        end = i + 1
        while end < len(text) and text[end] in "\"'”’)]}":
            end += 1
        nxt = end
        while nxt < len(text) and text[nxt] in " \t\n\r":
            nxt += 1
        if nxt < len(text) and text[nxt].islower():
            continue
        sentence = text[start:end].strip()
        if sentence:
            sentences.append(sentence)
        start = nxt
    rest = text[start:].strip()
    if rest:
        sentences.append(rest)
    return sentences


def is_probably_incomplete_sentence(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    if text.rstrip("\"'”’)]}").endswith((".","!","?","。","！","？",";","；",":")):
        return False
    return len(text.split()) >= 4


def sentence_split_zh(text: str) -> list[str]:
    text = compact_spaces(text)
    if not text:
        return []
    parts = re.split(r"(?<=[。！？；])", text)
    return [p.strip() for p in parts if p.strip()]


def infer_content_status(block: dict[str, object], heading_stack: list[str]) -> str:
    text = str(block["text"]).strip()
    text_l = text.lower()
    headings_l = " / ".join(heading_stack).lower()
    non_content_markers = [
        "credits",
        "copyright",
        "table of contents",
        "目录",
        "致谢",
        "版权",
        "study guide",
    ]
    if any(marker in text_l or marker in headings_l for marker in non_content_markers):
        return "non_content_candidate"
    if len(text) < 12 and block["block_type"] != "heading":
        return "short_candidate"
    return "content_candidate"


def load_matches() -> dict[str, list[dict[str, object]]]:
    data = json.loads(read_text(SOURCES_DIR / "v7_mineru_block_page_matches.json"))
    return {
        "zh": data["zh"]["items"],
        "en": data["en"]["items"],
    }


def find_mineru_merged() -> tuple[Path, Path]:
    zh = sorted(ROOT.rglob("v7_zh_mineru_merged.md"))
    en = sorted(ROOT.rglob("v7_en_mineru_merged.md"))
    zh = [p for p in zh if WORK_DIR not in p.parents]
    en = [p for p in en if WORK_DIR not in p.parents]
    if not zh or not en:
        raise FileNotFoundError("Cannot find merged MinerU markdown files.")
    return zh[-1], en[-1]


def normalize_blocks(lang: str, merged_path: Path, matches: list[dict[str, object]]) -> list[dict[str, object]]:
    blocks = split_md_blocks(read_text(merged_path))
    match_by_index = {int(item["block_index"]): item for item in matches}
    heading_stack: list[tuple[int, str]] = []
    out = []
    for idx, block in enumerate(blocks, start=1):
        h_level = block["heading_level"]
        if block["block_type"] == "heading" and h_level:
            heading_text = re.sub(r"^#{1,6}\s+", "", block["text"]).strip()
            heading_stack = [(lvl, txt) for lvl, txt in heading_stack if lvl < h_level]
            heading_stack.append((h_level, heading_text))

        m = match_by_index.get(idx, {})
        current_headings = [txt for _, txt in heading_stack]
        risk_flags: list[str] = []
        if idx > 1:
            prev_block = blocks[idx - 2]
            prev_text = str(prev_block["text"])
            if prev_block["block_type"] == "paragraph" and is_probably_incomplete_sentence(prev_text):
                risk_flags.append("previous_block_may_continue_here")
        if idx < len(blocks):
            next_text = str(blocks[idx]["text"])
            if block["block_type"] == "paragraph" and is_probably_incomplete_sentence(str(block["text"])):
                risk_flags.append("block_may_continue_next")
            if (
                block["block_type"] == "paragraph"
                and next_text
                and next_text[:1].isupper()
                and is_probably_incomplete_sentence(str(block["text"]))
            ):
                risk_flags.append("cross_block_sentence_candidate")
        previous_output = out[-1] if out else None
        if (
            lang == "en"
            and previous_output
            and block["block_type"] == "paragraph"
            and blocks[idx - 2]["block_type"] == "paragraph"
            and m.get("pdf_page") != previous_output.get("pdf_page")
            and is_probably_incomplete_sentence(str(blocks[idx - 2]["text"]))
        ):
            risk_flags.append("paragraph_continues_across_page_candidate")
        if (
            lang == "en"
            and previous_output
            and block["block_type"] == "paragraph"
            and m.get("pdf_page") != previous_output.get("pdf_page")
            and current_headings == previous_output.get("heading_stack")
        ):
            risk_flags.append("heading_context_reused_across_page")

        item: dict[str, object] = {
            "block_id": f"v7{lang}_b{idx:06d}",
            "source_block_index": idx,
            "lang": lang,
            "block_type": block["block_type"],
            "text": block["text"],
            "raw_md": block["raw"],
            "chars": len(str(block["text"])),
            "pdf_page": m.get("pdf_page"),
            "printed_page": m.get("printed_page"),
            "page_match_method": m.get("match_method"),
            "page_match_score": m.get("match_score"),
            "heading_stack": current_headings,
            "content_status": infer_content_status(block, current_headings),
            "source_file": str(merged_path),
            "risk_flags": risk_flags,
        }
        if idx > 1:
            item["previous_block"] = {
                "block_id": f"v7{lang}_b{idx - 1:06d}",
                "text_tail": str(blocks[idx - 2]["text"])[-220:],
            }
        if idx < len(blocks):
            item["next_block"] = {
                "block_id": f"v7{lang}_b{idx + 1:06d}",
                "text_head": str(blocks[idx]["text"])[:220],
            }
        if lang == "en" and block["block_type"] in {"paragraph", "heading"}:
            sentences = sentence_split_en(str(block["text"]))
            item["sentences"] = [
                {
                    "sentence_id": f"v7en_b{idx:06d}_s{sidx:03d}",
                    "text": sentence,
                    "role": "retrieval_slice",
                    "parent_block_id": f"v7en_b{idx:06d}",
                }
                for sidx, sentence in enumerate(sentences, start=1)
            ]
        elif lang == "zh":
            item["rough_sentences"] = sentence_split_zh(str(block["text"]))
        out.append(item)
    return out


def build_report(zh_blocks: list[dict[str, object]], en_blocks: list[dict[str, object]]) -> str:
    def stats(blocks: list[dict[str, object]]) -> dict[str, object]:
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        unmatched = 0
        for block in blocks:
            by_type[str(block["block_type"])] = by_type.get(str(block["block_type"]), 0) + 1
            by_status[str(block["content_status"])] = by_status.get(str(block["content_status"]), 0) + 1
            if not block.get("pdf_page"):
                unmatched += 1
        return {
            "total": len(blocks),
            "by_type": by_type,
            "by_status": by_status,
            "unmatched": unmatched,
        }

    zh = stats(zh_blocks)
    en = stats(en_blocks)
    en_sentence_count = sum(len(block.get("sentences", [])) for block in en_blocks)
    lines = [
        "# v7 Base Block Normalization Report",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Summary",
        "",
        f"- zh blocks: {zh['total']}",
        f"- en blocks: {en['total']}",
        f"- en sentences: {en_sentence_count}",
        f"- zh unmatched pages: {zh['unmatched']}",
        f"- en unmatched pages: {en['unmatched']}",
        "",
        "## Block Types",
        "",
        f"- zh: {json.dumps(zh['by_type'], ensure_ascii=False)}",
        f"- en: {json.dumps(en['by_type'], ensure_ascii=False)}",
        "",
        "## Content Status",
        "",
        f"- zh: {json.dumps(zh['by_status'], ensure_ascii=False)}",
        f"- en: {json.dumps(en['by_status'], ensure_ascii=False)}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    BASE_UNITS_DIR.mkdir(parents=True, exist_ok=True)
    zh_merged, en_merged = find_mineru_merged()
    matches = load_matches()
    zh_blocks = normalize_blocks("zh", zh_merged, matches["zh"])
    en_blocks = normalize_blocks("en", en_merged, matches["en"])

    write_json(
        BASE_UNITS_DIR / "v7_zh_blocks.json",
        {
            "schema_version": "v7_base_blocks_v1",
            "lang": "zh",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_file": str(zh_merged),
            "items": zh_blocks,
        },
    )
    write_json(
        BASE_UNITS_DIR / "v7_en_blocks.json",
        {
            "schema_version": "v7_base_blocks_v1",
            "lang": "en",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_file": str(en_merged),
            "items": en_blocks,
        },
    )
    (BASE_UNITS_DIR / "block_normalization_report.md").write_text(
        build_report(zh_blocks, en_blocks),
        encoding="utf-8",
    )
    print(f"wrote: {BASE_UNITS_DIR / 'v7_zh_blocks.json'}")
    print(f"wrote: {BASE_UNITS_DIR / 'v7_en_blocks.json'}")
    print(f"wrote: {BASE_UNITS_DIR / 'block_normalization_report.md'}")


if __name__ == "__main__":
    main()
