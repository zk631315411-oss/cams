"""
Build fine-grained V6 textbook sentence cards with DeepSeek Flash.

The script controls sentence boundaries locally. DeepSeek only writes the
knowledge summary and type for each original sentence; citation remains the
exact source sentence from v6_clean.md.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
DATA = ROOT / "cams工作台" / "data"
SOURCE = ROOT / "核心数据" / "源文" / "source" / "v6_clean.md"
OUTPUT = DATA / "cards_v6_sentence.json"
WORK_DIR = BASE / "output" / "v6_sentence_cards"
INPUT_PATH = WORK_DIR / "sentence_inputs.json"
BATCH_DIR = WORK_DIR / "batches"

MODEL = "deepseek-chat"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
VALID_TYPES = {"定义", "分类", "流程", "事实", "案例", "法规", "风险指标", "context"}


def get_deepseek_config() -> tuple[str, str, str]:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            return value, os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL") or DEFAULT_BASE_URL, env_name
    raise RuntimeError("DEEPSEEK_API_KEY / DS_API_KEY / DS_KEY 环境变量均未设置。")


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def is_noise_sentence(text: str) -> bool:
    text = normalize_space(text)
    if len(text) < 8:
        return True
    if re.fullmatch(r"[0-9ivxlcdmIVXLCDM頁页面\s.。．\-—_/]+", text):
        return True
    if "................................................................" in text:
        return True
    if text.startswith(("© ", "ISBN:", "頁面")):
        return True
    return False


def split_sentences_from_line(text: str) -> list[str]:
    text = normalize_space(text)
    if not text:
        return []

    # Treat bullets and list markers as independent sentence boundaries.
    text = re.sub(r"(?<!^)[•●○]", "。•", text)
    text = re.sub(r"(?<!^)([。！？；])\s*", r"\1\n", text)
    text = re.sub(r"(?<!^)(?=\([0-9]+\)\s*)", "\n", text)
    text = re.sub(r"(?<!^)(?=[0-9]+\.\s*[^\d])", "\n", text)

    rows: list[str] = []
    for part in text.splitlines():
        part = normalize_space(part.strip(" •\t"))
        if not part or is_noise_sentence(part):
            continue
        if len(part) <= 420:
            rows.append(part)
            continue

        # Some PDF-extracted lines still contain several clauses without clean
        # punctuation. Split long leftovers conservatively by semicolon/colon.
        subparts = re.split(r"(?<=[：:])|(?<=，)(?=.{120,})", part)
        current = ""
        for sub in subparts:
            sub = normalize_space(sub)
            if not sub:
                continue
            if current and len(current) + len(sub) > 420:
                rows.append(current)
                current = sub
            else:
                current = normalize_space(current + sub)
        if current:
            rows.append(current)
    return rows


def build_sentence_inputs() -> list[dict[str, Any]]:
    text = SOURCE.read_text(encoding="utf-8")
    h2 = ""
    h3 = ""
    rows: list[dict[str, Any]] = []

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if line.startswith("## "):
            h2 = line.lstrip("#").strip()
            h3 = ""
            continue
        if line.startswith("### "):
            h3 = line.lstrip("#").strip()
            continue
        if not h2:
            continue
        if line.startswith("#") or not line:
            continue

        for sentence in split_sentences_from_line(line):
            rows.append(
                {
                    "i": len(rows),
                    "sentence": sentence,
                    "h2": h2,
                    "h3": h3,
                    "line_start": line_no,
                    "line_end": line_no,
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
        f'{item["i"]}. 章节：{item["h2"]} > {item["h3"]}\n原句：{item["sentence"]}'
        for item in batch
    )
    return f"""你是CAMS考试教材句卡标注员。下面每条都是已经切好的教材原文句子。

你的任务：为每条原句生成一个简洁、可检索的 knowledge，并判断 type。

重要规则：
1. 不要改写、合并或拆分原句。
2. 不要输出 citation，citation 将由程序使用原句自动填写。
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
            by_i = {int(item.get("i")): item for item in parsed if isinstance(item, dict) and str(item.get("i", "")).isdigit()}
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


def load_or_create_inputs(force_inputs: bool = False) -> list[dict[str, Any]]:
    if INPUT_PATH.exists() and not force_inputs:
        return json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_sentence_inputs()
    INPUT_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


def batch_path(start: int, size: int) -> Path:
    return BATCH_DIR / f"batch_{start:05d}_{start + size - 1:05d}.json"


def run_batches(rows: list[dict[str, Any]], batch_size: int, workers: int, force: bool) -> None:
    api_key, base_url, env_name = get_deepseek_config()
    from openai import OpenAI

    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    batches = [rows[i : i + batch_size] for i in range(0, len(rows), batch_size)]
    pending = []
    for batch in batches:
        path = batch_path(batch[0]["i"], len(batch))
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
            path, count = future.result()
            completed += 1
            if completed % 10 == 0 or completed == len(pending):
                elapsed = time.time() - start_time
                print(f"  {completed}/{len(pending)} pending batches done, last={path.name}, elapsed={elapsed:.0f}s")


def merge_outputs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels: dict[int, dict[str, Any]] = {}
    for path in sorted(BATCH_DIR.glob("batch_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload.get("items", []):
            if isinstance(item, dict) and isinstance(item.get("i"), int):
                labels[item["i"]] = item

    cards = []
    errors = []
    for row in rows:
        label = labels.get(row["i"])
        if not label:
            errors.append({"i": row["i"], "error": "missing_batch_output"})
            continue
        if not label.get("keep", True):
            continue
        sentence = row["sentence"]
        knowledge = normalize_space(label.get("knowledge", ""))
        if not knowledge:
            knowledge = f"原文事实：{sentence[:80]}"
        typ = label.get("type") if label.get("type") in VALID_TYPES else "context"
        card_id = f"v6s_N{len(cards) + 1:05d}"
        cards.append(
            {
                "card_id": card_id,
                "knowledge": knowledge,
                "citation": sentence,
                "context_before": row.get("context_before", ""),
                "context_after": row.get("context_after", ""),
                "type": typ,
                "source_asset": str(SOURCE),
                "source_line_start": row.get("line_start"),
                "source_line_end": row.get("line_end"),
                "chapter_path": " > ".join(x for x in [row.get("h2", ""), row.get("h3", "")] if x),
                "evidence_scope": "v6_sentence",
            }
        )

    return {
        "asset_note": (
            "Full V6 textbook fine-grained sentence cards. Each citation is an exact source sentence "
            "from v6_clean.md; DeepSeek Flash only generated knowledge/type labels. This is evidence "
            "material, not confirmed exam-point data."
        ),
        "source_file": str(SOURCE),
        "model": MODEL,
        "cards": cards,
        "stats": {
            "source_sentences": len(rows),
            "cards": len(cards),
            "skipped": len(rows) - len(cards) - len(errors),
            "errors": len(errors),
        },
        "errors": errors[:200],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build full V6 fine-grained sentence cards.")
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--workers", type=int, default=30)
    parser.add_argument("--force-inputs", action="store_true")
    parser.add_argument("--force-batches", action="store_true")
    parser.add_argument("--merge-only", action="store_true")
    args = parser.parse_args(argv)

    rows = load_or_create_inputs(force_inputs=args.force_inputs)
    print(f"Prepared sentence inputs: {len(rows)} -> {INPUT_PATH}")
    if not args.merge_only:
        run_batches(rows, batch_size=args.batch_size, workers=args.workers, force=args.force_batches)

    data = merge_outputs(rows)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data["stats"], ensure_ascii=False, indent=2))
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
