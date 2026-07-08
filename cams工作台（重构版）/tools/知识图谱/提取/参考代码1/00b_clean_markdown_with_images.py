"""
Prepare a MinerU structured markdown file for the v4.3 KG pipeline.

This script is intentionally conservative:
- the original markdown/PDF are not modified;
- image URLs are localized into an asset directory and described in a manifest;
- the cleaned markdown keeps only lightweight image placeholders;
- known duplicated OCR/MinerU overlap ranges can be skipped with a report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\((https?://[^)]+)\)")
CHAPTER_RE = re.compile(r"^#\s*第\s*([一二三四五六七八九十百\d]+)\s*章\s*(.*?)\s*$")
SECTION_RE = re.compile(r"^#{2,3}\s*(\*)?\s*第\s*([一二三四五六七八九十百\d]+)\s*节\s*(.*?)\s*$")
SUBSECTION_RE = re.compile(r"^([一二三四五六七八九十]+)、\s*(.+?)\s*$")
ANCHOR_TITLE_RE = re.compile(r"^(定义|定理|推论|命题|引理|性质|公式|例)\s*")
FIGURE_RE = re.compile(r"图\s*\d+\s*[-－]\s*\d+")

CN_DIGITS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}

DISCARD_HINTS = (
    "二维码",
    "动画视频",
    "微课视频",
    "扫码",
    "习题答案",
    "自测题答案",
    "名人简介",
    "作者简介",
    "李大潜简介",
    "本书资源",
    "封面",
    "内容简介",
    "总序",
    "前言",
)

RESOURCE_LABELS = {
    "二维码",
    "动画视频",
    "微课视频",
    "名人简介",
    "作者简介",
}

TEACHING_HINTS = (
    "如图",
    "见图",
    "图形",
    "曲线",
    "坐标",
    "面积",
    "体积",
    "弧长",
    "旋转体",
    "切线",
    "法线",
    "渐近线",
    "拐点",
    "极坐标",
    "曲边梯形",
    "知识框图",
)

KNOWN_DROP_RANGES = {
    "高等数学上册_structured.md": [
        (10449, 11099, "drop duplicated/overlapped Chapter 4 section 4-5 block; keep the later cleaner copy"),
    ],
}


@dataclass
class ImageItem:
    image_id: str
    source_line: int
    source_url: str
    local_path: str
    sha256: str
    bytes: int
    figure_no: str
    category: str
    keep_in_clean: bool
    prev_text: str
    next_text: str
    visual_note: str
    download_status: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean structured markdown and localize image assets.")
    parser.add_argument("--input", type=Path, required=True, help="Input MinerU structured markdown.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for clean md, manifest, assets.")
    parser.add_argument("--clean-name", default=None, help="Clean markdown filename.")
    parser.add_argument("--manifest-name", default="image_manifest.jsonl")
    parser.add_argument("--report-name", default=None)
    parser.add_argument("--textbook-id", default="gaoshu_shang")
    parser.add_argument("--textbook-name", default="高等数学上册")
    parser.add_argument("--no-download", action="store_true", help="Do not download image URLs.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing generated files.")
    return parser.parse_args()


def chinese_number_to_int(text: str) -> int:
    text = text.strip()
    if text.isdigit():
        return int(text)
    if text == "十":
        return 10
    if "十" in text:
        left, _, right = text.partition("十")
        tens = CN_DIGITS.get(left, 1) if left else 1
        ones = CN_DIGITS.get(right, 0) if right else 0
        return tens * 10 + ones
    return CN_DIGITS.get(text, 0)


def clean_title(title: str) -> str:
    title = title.strip()
    title = re.sub(r"^[*·\-\s]+", "", title).strip()
    title = re.sub(r"\s*[.…·]{2,}\s*\d+\s*$", "", title).strip()
    title = re.sub(r"\s*\(\s*\d+\s*\)\s*$", "", title).strip()
    if "习题" not in title:
        title = re.sub(r"\s+\d+\s*$", "", title).strip()
    return title


def normalize_heading_title(line: str) -> str:
    match = HEADING_RE.match(line.strip())
    return clean_title(match.group(2)) if match else clean_title(line)


def previous_nonblank(lines: list[str], index: int) -> str:
    for pos in range(index - 1, -1, -1):
        text = lines[pos].strip()
        if text:
            return text
    return ""


def next_nonblank(lines: list[str], index: int) -> str:
    for pos in range(index + 1, len(lines)):
        text = lines[pos].strip()
        if text:
            return text
    return ""


def context_text(lines: list[str], index: int, radius: int = 5) -> str:
    start = max(0, index - radius)
    end = min(len(lines), index + radius + 1)
    return " ".join(line.strip() for line in lines[start:end] if line.strip())


def find_figure_no(lines: list[str], index: int) -> str:
    ctx = context_text(lines, index, radius=6)
    match = FIGURE_RE.search(ctx)
    if not match:
        return ""
    return re.sub(r"\s+", "", match.group(0)).replace("－", "-")


def classify_image(lines: list[str], index: int) -> str:
    ctx = context_text(lines, index, radius=6)
    if any(hint in ctx for hint in DISCARD_HINTS):
        return "discard_or_archive"
    if FIGURE_RE.search(ctx) or any(hint in ctx for hint in TEACHING_HINTS):
        return "teaching_figure"
    if re.search(r"例\s*\d|例题|求|证明|解\s", ctx):
        return "example_related"
    return "review"


def visual_note(lines: list[str], index: int, figure_no: str, category: str) -> str:
    prev_text = re.sub(r"\s+", " ", previous_nonblank(lines, index)).strip()
    next_text = re.sub(r"\s+", " ", next_nonblank(lines, index)).strip()
    if category == "discard_or_archive":
        return ""
    note_base = prev_text if prev_text and not prev_text.startswith("![") else next_text
    note_base = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", note_base).strip()
    if len(note_base) > 180:
        note_base = note_base[:177].rstrip() + "..."
    if figure_no:
        return f"{figure_no}: {note_base}" if note_base else figure_no
    return note_base


def url_extension(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    ext = Path(path).suffix.lower()
    return ext if ext in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_url(url: str, dest: Path, retries: int = 2) -> str:
    if dest.exists() and dest.stat().st_size > 0:
        return "exists"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    last_error = ""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                with dest.open("wb") as fh:
                    shutil.copyfileobj(response, fh)
            return "downloaded"
        except Exception as exc:  # pragma: no cover - network dependent
            last_error = f"{type(exc).__name__}: {exc}"
            time.sleep(0.5 * (attempt + 1))
    return f"failed: {last_error}"


def find_body_start(lines: list[str]) -> int:
    chapters: list[tuple[int, int]] = []
    for idx, line in enumerate(lines):
        match = CHAPTER_RE.match(line.strip())
        if match:
            chapters.append((idx, chinese_number_to_int(match.group(1))))
    for pos in range(1, len(chapters)):
        prev_number = chapters[pos - 1][1]
        current_number = chapters[pos][1]
        if current_number <= prev_number:
            return chapters[pos][0]
    for idx, line in enumerate(lines):
        if idx > 200 and re.match(r"^#\s*第\s*[一二三四五六七八九十百\d]+\s*章(?:\s|$)", line.strip()):
            return idx
    for idx, line in enumerate(lines):
        if re.match(r"^#\s*第一章(?:\s|$)", line.strip()):
            return idx
    return 0


def in_drop_ranges(line_no: int, ranges: Iterable[tuple[int, int, str]]) -> bool:
    return any(start <= line_no <= end for start, end, _ in ranges)


def make_image_placeholder(item: ImageItem) -> str:
    figure = f" figure={item.figure_no}" if item.figure_no else ""
    note = f" note={item.visual_note}" if item.visual_note else ""
    return f"[IMAGE id={item.image_id}{figure} type={item.category}{note}]"


def process_markdown(
    lines: list[str],
    input_path: Path,
    output_dir: Path,
    textbook_id: str,
    no_download: bool,
) -> tuple[list[str], list[ImageItem], list[str], dict[str, int]]:
    body_start = find_body_start(lines)
    drop_ranges = KNOWN_DROP_RANGES.get(input_path.name, [])
    asset_dir = output_dir / "assets" / "images"
    asset_dir.mkdir(parents=True, exist_ok=True)

    cleaned: list[str] = []
    images: list[ImageItem] = []
    dropped_notes: list[str] = [f"{start}-{end}: {reason}" for start, end, reason in drop_ranges]
    counters = {
        "chapter_headings": 0,
        "section_headings": 0,
        "subsection_headings": 0,
        "anchor_demotions": 0,
        "images_total": 0,
        "images_kept_in_clean": 0,
        "images_omitted_from_clean": 0,
        "lines_skipped_before_body": body_start,
        "lines_skipped_known_overlap": 0,
        "answer_label_lines_removed": 0,
    }

    current_chapter = 0
    current_section = 0
    subsection_counter = 0
    pending_chapter: int | None = None
    pending_section: tuple[int, bool] | None = None
    image_counter = 0

    idx = body_start
    while idx < len(lines):
        line_no = idx + 1
        raw = lines[idx].rstrip("\n")
        stripped = raw.strip()

        if in_drop_ranges(line_no, drop_ranges):
            counters["lines_skipped_known_overlap"] += 1
            idx += 1
            continue

        if stripped in {"习题答案", "自测题答案"}:
            counters["answer_label_lines_removed"] += 1
            idx += 1
            continue

        if stripped in RESOURCE_LABELS:
            idx += 1
            continue

        image_match = IMAGE_RE.search(stripped)
        if image_match:
            image_counter += 1
            counters["images_total"] += 1
            url = image_match.group(1)
            category = classify_image(lines, idx)
            figure_no = find_figure_no(lines, idx)
            keep = category != "discard_or_archive"
            ext = url_extension(url)
            image_id = f"{textbook_id}_img_{image_counter:04d}"
            local_file = asset_dir / f"{image_id}_line{line_no:05d}{ext}"
            status = "skipped"
            if not no_download:
                status = download_url(url, local_file)
            file_hash = sha256_file(local_file) if local_file.exists() and local_file.stat().st_size else ""
            file_bytes = local_file.stat().st_size if local_file.exists() else 0
            rel_path = local_file.relative_to(output_dir).as_posix()
            item = ImageItem(
                image_id=image_id,
                source_line=line_no,
                source_url=url,
                local_path=rel_path,
                sha256=file_hash,
                bytes=file_bytes,
                figure_no=figure_no,
                category=category,
                keep_in_clean=keep,
                prev_text=previous_nonblank(lines, idx),
                next_text=next_nonblank(lines, idx),
                visual_note=visual_note(lines, idx, figure_no, category),
                download_status=status,
            )
            images.append(item)
            if keep:
                cleaned.append(make_image_placeholder(item))
                counters["images_kept_in_clean"] += 1
            else:
                counters["images_omitted_from_clean"] += 1
            idx += 1
            continue

        if pending_chapter is not None:
            if not stripped:
                idx += 1
                continue
            title = normalize_heading_title(stripped)
            current_chapter = pending_chapter
            current_section = 0
            subsection_counter = 0
            cleaned.append(f"# 第{current_chapter}章 {title}")
            counters["chapter_headings"] += 1
            pending_chapter = None
            idx += 1
            continue

        if pending_section is not None:
            if not stripped:
                idx += 1
                continue
            section_no, optional = pending_section
            title = normalize_heading_title(stripped)
            current_section = section_no
            subsection_counter = 0
            marker = " *" if optional else ""
            cleaned.append(f"## {current_chapter}.{current_section}{marker} {title}")
            counters["section_headings"] += 1
            pending_section = None
            idx += 1
            continue

        chapter_match = CHAPTER_RE.match(stripped)
        if chapter_match:
            number = chinese_number_to_int(chapter_match.group(1))
            title = clean_title(chapter_match.group(2))
            if title:
                current_chapter = number
                current_section = 0
                subsection_counter = 0
                cleaned.append(f"# 第{current_chapter}章 {title}")
                counters["chapter_headings"] += 1
            else:
                pending_chapter = number
            idx += 1
            continue

        section_match = SECTION_RE.match(stripped)
        if section_match:
            optional = bool(section_match.group(1))
            number = chinese_number_to_int(section_match.group(2))
            title = clean_title(section_match.group(3))
            if title:
                current_section = number
                subsection_counter = 0
                marker = " *" if optional else ""
                cleaned.append(f"## {current_chapter}.{current_section}{marker} {title}")
                counters["section_headings"] += 1
            else:
                pending_section = (number, optional)
            idx += 1
            continue

        heading_match = HEADING_RE.match(stripped)
        if heading_match:
            hashes, title = heading_match.groups()
            title = clean_title(title)
            level = len(hashes)

            if level == 3 and ANCHOR_TITLE_RE.match(title):
                cleaned.append(f"##### {title}")
                counters["anchor_demotions"] += 1
                idx += 1
                continue

            if level == 3:
                normalized_exercise = re.sub(r"^[·\-\s]+", "", title)
                subsection_match = SUBSECTION_RE.match(normalized_exercise)
                if subsection_match and current_chapter and current_section:
                    subsection_counter += 1
                    subsection_title = clean_title(subsection_match.group(2))
                    cleaned.append(f"### {current_chapter}.{current_section}.{subsection_counter} {subsection_title}")
                    counters["subsection_headings"] += 1
                elif re.match(r"^[（(][0-9一二三四五六七八九十]+[）)]", normalized_exercise):
                    cleaned.append(f"#### {normalized_exercise}")
                else:
                    cleaned.append(f"### {normalized_exercise}")
                idx += 1
                continue

            cleaned.append(stripped)
            idx += 1
            continue

        cleaned.append(raw.rstrip())
        idx += 1

    return cleaned, images, dropped_notes, counters


def write_report(
    report_path: Path,
    input_path: Path,
    clean_path: Path,
    manifest_path: Path,
    images: list[ImageItem],
    dropped_notes: list[str],
    counters: dict[str, int],
) -> None:
    image_counts: dict[str, int] = {}
    for image in images:
        image_counts[image.category] = image_counts.get(image.category, 0) + 1
    failed = [image for image in images if image.download_status.startswith("failed")]

    lines = [
        "# Clean Markdown Report",
        "",
        f"- input: `{input_path}`",
        f"- clean_markdown: `{clean_path}`",
        f"- image_manifest: `{manifest_path}`",
        "",
        "## Counters",
    ]
    for key in sorted(counters):
        lines.append(f"- {key}: {counters[key]}")
    lines.extend(["", "## Image Categories"])
    for category, count in sorted(image_counts.items()):
        lines.append(f"- {category}: {count}")
    lines.extend(["", "## Dropped Source Ranges"])
    if dropped_notes:
        lines.extend(f"- {note}" for note in dropped_notes)
    else:
        lines.append("- none")
    lines.extend(["", "## Download Failures"])
    if failed:
        lines.extend(f"- {image.image_id} line={image.source_line}: {image.download_status}" for image in failed)
    else:
        lines.append("- none")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    input_path = args.input.resolve()
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    output_dir = (args.output_dir or input_path.parent).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    clean_name = args.clean_name or input_path.name.replace("_structured.md", "_clean.md")
    report_name = args.report_name or clean_name.replace(".md", "_report.md")
    clean_path = output_dir / clean_name
    manifest_path = output_dir / args.manifest_name
    report_path = output_dir / report_name

    for path in (clean_path, manifest_path, report_path):
        if path.exists() and not args.overwrite:
            raise FileExistsError(f"{path} exists. Use --overwrite to replace it.")

    lines = input_path.read_text(encoding="utf-8").splitlines()
    cleaned, images, dropped_notes, counters = process_markdown(
        lines=lines,
        input_path=input_path,
        output_dir=output_dir,
        textbook_id=args.textbook_id,
        no_download=args.no_download,
    )

    clean_path.write_text("\n".join(cleaned).rstrip() + "\n", encoding="utf-8")
    with manifest_path.open("w", encoding="utf-8") as fh:
        for image in images:
            fh.write(json.dumps(asdict(image), ensure_ascii=False) + "\n")
    write_report(report_path, input_path, clean_path, manifest_path, images, dropped_notes, counters)

    print(f"[OK] clean markdown -> {clean_path}")
    print(f"[OK] image manifest -> {manifest_path}")
    print(f"[OK] report -> {report_path}")
    print(f"[INFO] images={len(images)} kept_in_clean={counters['images_kept_in_clean']}")


if __name__ == "__main__":
    main()
