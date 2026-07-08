"""
Build a cross-chapter fallback sentence-card pool from the cleaned V6 textbook.

This generator excludes the second chapter from v6教材原文/v6_clean.md and writes
cards_v6_except_ch2_sentence.json. It is meant to supplement cards_ch2.json when
a chapter-2 question needs evidence from another chapter. The citation field is
always the exact source sentence; DeepSeek only labels knowledge/type.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
DATA = ROOT / "cams工作台" / "data"
SOURCE = ROOT / "教材、答疑记录、习题与参考文献" / "教材原文" / "v6" / "v6_clean.md"
DEFAULT_OUTPUT = DATA / "cards_v6_except_ch2_sentence.json"
WORK_DIR = BASE / "output" / "v6_except_ch2_sentence_cards"
STAGING_OUTPUT = WORK_DIR / "cards_v6_except_ch2_sentence.json"

MODEL = os.environ.get("DS_CARD_MODEL", "deepseek-chat")
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
EXCLUDED_H2 = "洗钱和恐怖融资活动的风险及方法"
VALID_TYPES = {"定义", "分类", "流程", "事实", "案例", "法规", "风险指标", "context"}
HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$")


def get_deepseek_config() -> tuple[str, str, str]:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            base_url = os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL") or DEFAULT_BASE_URL
            return value, base_url, env_name
    names = " / ".join(API_KEY_ENV_NAMES)
    raise RuntimeError(f"{names} 环境变量均未设置，不能调用 DeepSeek API。")


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def clean_marker(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^[•●▪◆]\s*", "", text)
    text = re.sub(r"^[-]\s+", "", text)
    text = re.sub(r"^\(?([0-9]{1,2})\)?[.、]\s+", r"\1. ", text)
    return normalize_space(text)


def is_noise_sentence(text: str) -> bool:
    text = normalize_space(text)
    if len(text) < 4:
        return True
    if re.fullmatch(r"[0-9ivxlcdmIVXLCDM页页面\s.。？\-—/]+", text):
        return True
    if "................................................................" in text:
        return True
    if text.startswith(("© ", "ISBN:", "页面")):
        return True
    if text.startswith("<") and text.endswith(">"):
        return True
    return False


def split_long_sentence(text: str, max_len: int = 360) -> list[str]:
    text = normalize_space(text)
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    current = ""
    parts = re.split(r"(?<=[；;。！？])", text)
    for part in parts:
        part = normalize_space(part)
        if not part:
            continue
        if current and len(current) + len(part) > max_len:
            chunks.append(current)
            current = part
        else:
            current = normalize_space(current + part)
    if current:
        chunks.append(current)
    return chunks


def split_sentences_from_line(text: str) -> list[str]:
    text = normalize_space(text)
    if not text:
        return []

    text = re.sub(r"(?<!^)\s*[•●▪◆]\s*", "\n• ", text)
    text = re.sub(r"(?<!^)\s+(?=\(?[0-9]{1,2}\)?[.、]\s+\D)", "\n", text)
    text = re.sub(r"(?<!^)([。！？；])\s*", r"\1\n", text)

    rows: list[str] = []
    for part in text.splitlines():
        part = clean_marker(part)
        if not part or is_noise_sentence(part):
            continue
        rows.extend(x for x in split_long_sentence(part) if not is_noise_sentence(x))
    return rows


def build_sentence_inputs(source: Path, excluded_h2: str = EXCLUDED_H2) -> list[dict[str, Any]]:
    heading_stack: dict[int, str] = {}
    rows: list[dict[str, Any]] = []

    for line_no, raw_line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            heading_stack[level] = heading.group(2).strip()
            for old_level in list(heading_stack):
                if old_level > level:
                    del heading_stack[old_level]
            continue
        if not line or line.startswith("#") or not heading_stack:
            continue
        if heading_stack.get(2) == excluded_h2:
            continue
        if (
            heading_stack.get(3) == "巴塞尔银行监管委员会"
            and line.startswith("欧洲议会定期发布欧盟反洗钱指令")
        ):
            heading_stack[3] = "欧洲联盟反洗钱指令"
            for old_level in list(heading_stack):
                if old_level > 3:
                    del heading_stack[old_level]

        path = [heading_stack[level] for level in sorted(heading_stack)]
        for sentence in split_sentences_from_line(line):
            rows.append(
                {
                    "i": len(rows),
                    "sentence": sentence,
                    "line_start": line_no,
                    "line_end": line_no,
                    "chapter_path": " > ".join(path),
                    "section_h2": heading_stack.get(2, ""),
                    "section_h3": heading_stack.get(3, ""),
                    "section_h4": heading_stack.get(4, ""),
                    "section_h5": heading_stack.get(5, ""),
                }
            )

    for index, row in enumerate(rows):
        row["context_before"] = rows[index - 1]["sentence"] if index > 0 else ""
        row["context_after"] = rows[index + 1]["sentence"] if index + 1 < len(rows) else ""
    return rows


def parse_json_array(raw: str) -> list[Any] | None:
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    candidates = [text]
    match = re.search(r"\[[\s\S]*\]", raw)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, list) else None
        except json.JSONDecodeError:
            try:
                import json_repair

                parsed = json.loads(json_repair.repair_json(candidate))
                return parsed if isinstance(parsed, list) else None
            except Exception:
                continue
    return None


def build_prompt(batch: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f'{item["i"]}. 章节：{item["chapter_path"]}\n原句：{item["sentence"]}'
        for item in batch
    )
    return f"""你是 CAMS 考试教材句卡标注员。下面每条都是已经切好的教材原文句子，且已经排除了第二章。
你的任务：为每条原句生成一个简洁、可检索的 knowledge，并判断 type。

重要规则：
1. 不要改写、合并或拆分原句。
2. 不要输出 citation，citation 将由程序使用原句自动填入。
3. knowledge 必须忠实于原句，不能添加原句没有的信息。
4. 如果原句只是目录、页码、版权、乱码、残缺标题或没有教材证据价值，keep=false。
5. type 只能是：定义 / 分类 / 流程 / 事实 / 案例 / 法规 / 风险指标 / context。
6. 每个输入 i 必须返回一个对象，不要漏项。

输出严格 JSON 数组，不要 Markdown：
[
  {{"i": 0, "keep": true, "knowledge": "一句话知识点", "type": "事实"}},
  {{"i": 1, "keep": false, "knowledge": "", "type": "context"}}
]

输入：
{rows}"""


def call_batch(client: Any, batch: list[dict[str, Any]], retries: int = 3) -> list[dict[str, Any]]:
    prompt = build_prompt(batch)
    last_error = ""
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=4096,
            )
            raw = (resp.choices[0].message.content or "").strip()
            parsed = parse_json_array(raw)
            if parsed is None:
                raise ValueError("LLM output is not a JSON array")
            by_i = {
                int(item.get("i")): item
                for item in parsed
                if isinstance(item, dict) and str(item.get("i", "")).isdigit()
            }
            rows = []
            for item in batch:
                got = by_i.get(item["i"], {})
                typ = got.get("type") if got.get("type") in VALID_TYPES else "context"
                rows.append(
                    {
                        "i": item["i"],
                        "keep": bool(got.get("keep", True)),
                        "knowledge": normalize_space(str(got.get("knowledge", ""))),
                        "type": typ,
                    }
                )
            return rows
        except Exception as exc:
            last_error = str(exc)
            if attempt < retries - 1:
                time.sleep(2 + attempt * 2)
    return [
        {
            "i": item["i"],
            "keep": True,
            "knowledge": "",
            "type": "context",
            "error": last_error[:300],
        }
        for item in batch
    ]


def infer_type(sentence: str) -> str:
    if any(token in sentence for token in ("案例", "例如", "示例")):
        return "案例"
    if any(token in sentence for token in ("危险信号", "红旗", "风险", "可疑", "异常")):
        return "风险指标"
    if any(token in sentence for token in ("法案", "法律", "法规", "指令", "公约", "建议", "监管", "制裁", "处罚")):
        return "法规"
    if any(token in sentence for token in ("包括", "分为", "类型", "类别", "可分", "主要有")):
        return "分类"
    if any(token in sentence for token in ("是指", "定义为", "指的是", "是一个", "是一种")):
        return "定义"
    if any(token in sentence for token in ("流程", "步骤", "首先", "然后", "之后", "最后", "应当", "必须", "需要")):
        return "流程"
    return "事实"


def build_local_label(row: dict[str, Any]) -> dict[str, Any]:
    sentence = normalize_space(row.get("sentence", ""))
    knowledge = sentence if len(sentence) <= 160 else sentence[:157] + "..."
    return {
        "i": row["i"],
        "keep": not is_noise_sentence(sentence),
        "knowledge": knowledge,
        "type": infer_type(sentence),
        "local_label": True,
    }


def write_local_batches(rows: list[dict[str, Any]], batch_dir: Path, batch_size: int, force: bool) -> None:
    batch_dir.mkdir(parents=True, exist_ok=True)
    batches = [rows[i : i + batch_size] for i in range(0, len(rows), batch_size)]
    pending = 0
    for batch in batches:
        path = batch_path(batch_dir, batch[0]["i"], len(batch))
        if path.exists() and not force:
            continue
        payload = {
            "batch_start": batch[0]["i"],
            "items": [build_local_label(row) for row in batch],
            "label_source": "local_rules",
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        pending += 1
    print(f"Local labels written: {pending}/{len(batches)} batches -> {batch_dir}")


def scoped_paths(work_dir: Path, sample_name: str) -> tuple[Path, Path]:
    root = work_dir / sample_name if sample_name else work_dir
    return root / "sentence_inputs.json", root / "batches"


def load_or_create_inputs(source: Path, input_path: Path, force_inputs: bool, excluded_h2: str) -> list[dict[str, Any]]:
    if input_path.exists() and not force_inputs:
        return json.loads(input_path.read_text(encoding="utf-8"))
    input_path.parent.mkdir(parents=True, exist_ok=True)
    rows = build_sentence_inputs(source, excluded_h2=excluded_h2)
    input_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


def batch_path(batch_dir: Path, start: int, size: int) -> Path:
    return batch_dir / f"batch_{start:05d}_{start + size - 1:05d}.json"


def run_batches(rows: list[dict[str, Any]], batch_dir: Path, batch_size: int, workers: int, force: bool) -> None:
    api_key, base_url, env_name = get_deepseek_config()
    from openai import OpenAI

    batch_dir.mkdir(parents=True, exist_ok=True)
    batches = [rows[i : i + batch_size] for i in range(0, len(rows), batch_size)]
    pending = []
    for batch in batches:
        path = batch_path(batch_dir, batch[0]["i"], len(batch))
        if path.exists() and not force:
            continue
        pending.append((batch, path))

    print(f"DeepSeek key source: {env_name}, model={MODEL}, base_url={base_url}")
    print(f"Sentences: {len(rows)}, batches: {len(batches)}, pending: {len(pending)}, workers: {workers}")
    if not pending:
        return

    def work(batch: list[dict[str, Any]], path: Path) -> tuple[Path, int]:
        client = OpenAI(api_key=api_key, base_url=base_url)
        result = call_batch(client, batch)
        payload = {"batch_start": batch[0]["i"], "items": result}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path, len(result)

    completed = 0
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(work, batch, path): path for batch, path in pending}
        for future in as_completed(futures):
            path, _count = future.result()
            completed += 1
            if completed % 10 == 0 or completed == len(pending):
                elapsed = time.time() - start_time
                print(f"  {completed}/{len(pending)} pending batches done, last={path.name}, elapsed={elapsed:.0f}s")


def merge_outputs(rows: list[dict[str, Any]], batch_dir: Path, source: Path, excluded_h2: str) -> dict[str, Any]:
    labels: dict[int, dict[str, Any]] = {}
    for path in sorted(batch_dir.glob("batch_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload.get("items", []):
            if isinstance(item, dict) and isinstance(item.get("i"), int):
                labels[item["i"]] = item

    cards = []
    errors = []
    model_skipped_kept = []
    for row in rows:
        label = labels.get(row["i"])
        if not label:
            errors.append({"i": row["i"], "error": "missing_batch_output"})
            continue
        sentence = row["sentence"]
        if not label.get("keep", True):
            model_skipped_kept.append(row["i"])
        knowledge = normalize_space(label.get("knowledge", ""))
        if not knowledge:
            knowledge = f"原文事实：{sentence[:80]}"
        typ = label.get("type") if label.get("type") in VALID_TYPES else "context"
        card_id = f"v6x_{len(cards) + 1:05d}"
        cards.append(
            {
                "card_id": card_id,
                "knowledge": knowledge,
                "citation": sentence,
                "context_before": row.get("context_before", ""),
                "context_after": row.get("context_after", ""),
                "type": typ,
                "source_asset": str(source),
                "source_line_start": row.get("line_start"),
                "source_line_end": row.get("line_end"),
                "chapter_path": row.get("chapter_path", ""),
                "section_h2": row.get("section_h2", ""),
                "section_h3": row.get("section_h3", ""),
                "section_h4": row.get("section_h4", ""),
                "section_h5": row.get("section_h5", ""),
                "evidence_scope": "v6_except_ch2_sentence",
            }
        )

    return {
        "asset_note": (
            "CAMS v6.51 textbook cross-chapter fallback sentence cards, generated from "
            "v6教材原文/v6_clean.md with the second chapter excluded. Each citation is an exact "
            "source sentence; DeepSeek only generated knowledge/type labels. This is supplemental "
            "textbook evidence for chapter-2 MVP question analysis, not confirmed exam-point data."
        ),
        "schema_version": "v6_except_ch2_sentence_cards_v1",
        "source_file": str(source),
        "excluded_h2": excluded_h2,
        "model": MODEL,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "cards": cards,
        "stats": {
            "source_sentences": len(rows),
            "cards": len(cards),
            "skipped": len(rows) - len(cards) - len(errors),
            "errors": len(errors),
            "model_skipped_kept": len(model_skipped_kept),
        },
        "model_skipped_kept": model_skipped_kept[:200],
        "errors": errors[:200],
    }


def audit_cards(data: dict[str, Any]) -> tuple[dict[str, Any], str]:
    cards = data.get("cards", [])
    citation_lengths = [len(card.get("citation", "")) for card in cards]
    missing = []
    dirty = []
    excluded_leaks = []
    for card in cards:
        citation = card.get("citation", "")
        if not card.get("knowledge") or not citation or not card.get("chapter_path"):
            missing.append(card.get("card_id"))
        if any(token in citation for token in ("![image]", "<table", "页面", "......")):
            dirty.append(card.get("card_id"))
        if card.get("section_h2") == data.get("excluded_h2"):
            excluded_leaks.append(card.get("card_id"))
    stats = {
        "cards": len(cards),
        "missing_required": len(missing),
        "dirty_citations": len(dirty),
        "excluded_h2_leaks": len(excluded_leaks),
        "max_citation_len": max(citation_lengths) if citation_lengths else 0,
        "over_180": sum(1 for value in citation_lengths if value > 180),
        "over_260": sum(1 for value in citation_lengths if value > 260),
        "sample_cards": cards[:8],
        "long_cards": sorted(cards, key=lambda c: len(c.get("citation", "")), reverse=True)[:8],
    }
    report = [
        "# v6 except ch2 sentence cards audit",
        "",
        f"- cards: {stats['cards']}",
        f"- missing_required: {stats['missing_required']}",
        f"- dirty_citations: {stats['dirty_citations']}",
        f"- excluded_h2_leaks: {stats['excluded_h2_leaks']}",
        f"- max_citation_len: {stats['max_citation_len']}",
        f"- over_180: {stats['over_180']}",
        f"- over_260: {stats['over_260']}",
        "",
        "## First Samples",
    ]
    for card in stats["sample_cards"]:
        report.append(f"- {card.get('card_id')} | {card.get('type')} | {card.get('chapter_path')}")
        report.append(f"  - citation: {card.get('citation')}")
        report.append(f"  - knowledge: {card.get('knowledge')}")
    report.append("")
    report.append("## Longest Citations")
    for card in stats["long_cards"]:
        report.append(f"- {card.get('card_id')} | len={len(card.get('citation', ''))} | {card.get('chapter_path')}")
        report.append(f"  - citation: {card.get('citation')}")
    return stats, "\n".join(report) + "\n"


def backup_existing(path: Path, backup_dir: Path) -> Path | None:
    if not path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = backup_dir / f"{path.stem}.bak_{stamp}{path.suffix}"
    shutil.copy2(path, target)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build V6 sentence cards excluding chapter 2.")
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=STAGING_OUTPUT)
    parser.add_argument("--work-dir", type=Path, default=WORK_DIR)
    parser.add_argument("--sample-name", default="")
    parser.add_argument("--excluded-h2", default=EXCLUDED_H2)
    parser.add_argument("--limit", type=int, default=0, help="Only process the first N selected sentence inputs.")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--force-inputs", action="store_true")
    parser.add_argument("--force-batches", action="store_true")
    parser.add_argument("--merge-only", action="store_true")
    parser.add_argument("--local-labels", action="store_true", help="Use rule-based knowledge/type labels without API calls.")
    parser.add_argument("--dry-run", action="store_true", help="Only build inputs and print split stats; no API calls.")
    parser.add_argument("--replace-final", action="store_true", help="Copy generated file into cams工作台/data.")
    args = parser.parse_args(argv)

    input_path, batch_dir = scoped_paths(args.work_dir, args.sample_name)
    rows = load_or_create_inputs(args.source, input_path, force_inputs=args.force_inputs, excluded_h2=args.excluded_h2)
    selected_rows = rows[args.offset :]
    if args.limit:
        selected_rows = selected_rows[: args.limit]

    print(f"Prepared sentence inputs: {len(rows)} -> {input_path}")
    print(f"Excluded H2: {args.excluded_h2}")
    print(f"Selected sentence inputs: {len(selected_rows)} offset={args.offset} limit={args.limit or 'all'}")

    if args.dry_run:
        lengths = [len(row["sentence"]) for row in selected_rows]
        by_h2: dict[str, int] = {}
        for row in selected_rows:
            by_h2[row.get("section_h2", "")] = by_h2.get(row.get("section_h2", ""), 0) + 1
        print(
            json.dumps(
                {
                    "selected": len(selected_rows),
                    "by_h2": by_h2,
                    "max_len": max(lengths) if lengths else 0,
                    "over_180": sum(1 for value in lengths if value > 180),
                    "over_260": sum(1 for value in lengths if value > 260),
                    "samples": selected_rows[:10],
                    "longest": sorted(selected_rows, key=lambda row: len(row["sentence"]), reverse=True)[:10],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.local_labels:
        write_local_batches(selected_rows, batch_dir=batch_dir, batch_size=args.batch_size, force=args.force_batches)
    elif not args.merge_only:
        run_batches(
            selected_rows,
            batch_dir=batch_dir,
            batch_size=args.batch_size,
            workers=args.workers,
            force=args.force_batches,
        )

    data = merge_outputs(selected_rows, batch_dir=batch_dir, source=args.source, excluded_h2=args.excluded_h2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    stats, report = audit_cards(data)
    audit_path = args.output.with_suffix(".audit.md")
    audit_path.write_text(report, encoding="utf-8")
    print(json.dumps(data["stats"], ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in stats.items() if k not in {"sample_cards", "long_cards"}}, ensure_ascii=False, indent=2))
    print(f"Wrote {args.output}")
    print(f"Wrote {audit_path}")

    if args.replace_final:
        backup = backup_existing(DEFAULT_OUTPUT, args.work_dir / "backups")
        shutil.copy2(args.output, DEFAULT_OUTPUT)
        print(f"Replaced {DEFAULT_OUTPUT}")
        if backup:
            print(f"Backup {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
