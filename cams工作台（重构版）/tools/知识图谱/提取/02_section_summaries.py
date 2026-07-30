"""
Step 2：为每个叶子节生成梗概。

对标高代 02_generate_section_summaries.py。只做导航信息，不做节点抽取。
每个 H3 独立处理，LLM 单次调用只出 summary + skip_reason。

输入：leaf_sections.jsonl
输出：section_summaries.jsonl
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from openai import OpenAI

_WORK = Path(__file__).resolve().parent / "work"
_DS_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
_MIMO_API_KEY = os.environ.get("MIMO_API_KEY", "")
_TEMPERATURE = 0.0
_MAX_TOKENS = 512

PROMPT = """你是一位CAMS反洗钱教材知识图谱构建助手。你的任务只是为当前小节写一段梗概，帮助后续步骤快速了解本小节主题。

只输出 JSON 对象，不输出 Markdown 或解释性文字。

## 任务边界

- 只能依据当前小节原文，不使用外部知识。
- 当前步骤只写梗概，不做节点抽取，不做关系抽取。
- 不输出任何候选概念、候选关系、证据原文。
- 如果当前小节是案例（标题含"案例"），正常概括该案例说明了什么。

## 输出格式

{
  "summary": "150-300 字的概括，说明本小节讲什么、在章节中承担什么作用。",
  "skip_reason": ""
}

## 字段要求

- summary 不能加入当前小节没有出现的专有名词。
- summary 不要复制长段原文。
- skip_reason 仅对完全无实质内容的小节填写非空值（如纯目录），其他为空字符串。

## 当前输入"""


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def parse_json_response(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise RuntimeError(f"无效 JSON: {text[:300]}")


def call_llm_composite(section: dict) -> tuple[dict, str]:
    """MiMo 优先 → DS 降级"""
    payload = json.dumps({
        "section_metadata": {
            "section_node_id": section["section_node_id"],
            "chapter": section.get("chapter", ""),
            "section": section.get("section", ""),
            "subsection": section.get("subsection", ""),
            "source_scope": section.get("source_scope", ""),
        },
        "section_text": section.get("text", ""),
    }, ensure_ascii=False)

    chain = [
        ("mimo-v2.5", "https://token-plan-cn.xiaomimimo.com/v1", _MIMO_API_KEY),
        ("deepseek-chat", "https://api.deepseek.com/v1", _DS_API_KEY),
    ]
    for model, base_url, api_key in chain:
        client = OpenAI(api_key=api_key, base_url=base_url)
        for attempt in range(2):
            try:
                resp = client.chat.completions.create(
                    model=model, messages=[
                        {"role": "system", "content": "你只输出合法 JSON 对象。"},
                        {"role": "user", "content": PROMPT + "\n\n" + payload},
                    ], temperature=_TEMPERATURE)
                return parse_json_response(resp.choices[0].message.content or "{}"), model
            except Exception:
                if attempt < 1:
                    time.sleep(0.5)
    return {"summary": "", "skip_reason": "llm_error"}, "all_failed"


from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def _process_one(sec: dict, mock: bool) -> dict:
    """单个节的 LLM 调用，在线程中执行"""
    sid = sec["section_node_id"]
    if mock:
        raw, model = {"summary": sec.get("text", "")[:200]}, "mock"
    else:
        raw, model = call_llm_composite(sec)
    return {
        "summary_id": f"{sid}:summary",
        "section_node_id": sid,
        "chapter": sec.get("chapter", ""),
        "section": sec.get("section", ""),
        "subsection": sec.get("subsection", ""),
        "source_scope": sec.get("source_scope", ""),
        "summary": (raw.get("summary") or "").strip(),
        "skip_reason": (raw.get("skip_reason") or "").strip(),
        "model": model,
        "mode": "mock" if mock else "llm",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def main(chapter: int | None = None, limit: int = 0, mock: bool = False,
         append: bool = False, workers: int = 4) -> int:
    chapters = [chapter] if chapter else [2, 3, 4, 5]
    total = 0
    write_lock = threading.Lock()

    for ch in chapters:
        in_path = _WORK / f"ch{ch}" / "leaf_sections.jsonl"
        if not in_path.exists():
            print(f"跳过 ch{ch}: 无 leaf_sections.jsonl")
            continue

        sections = read_jsonl(in_path)
        if limit > 0:
            sections = sections[:limit]

        out_path = _WORK / f"ch{ch}" / "section_summaries.jsonl"
        warn_path = _WORK / f"ch{ch}" / "section_summary_warnings.jsonl"

        done_sids: set[str] = set()
        if append and out_path.exists():
            with out_path.open("r", encoding="utf-8") as f:
                for line in f:
                    done_sids.add(json.loads(line).get("section_node_id", ""))
            print(f"续跑: {len(done_sids)} 节已完成，跳过")

        pending = [s for s in sections if s["section_node_id"] not in done_sids]
        print(f"\n===== 第{ch}章: {len(sections)} 节, 待处理 {len(pending)}, workers={workers} =====")

        fmode = "a" if append else "w"
        with out_path.open(fmode, encoding="utf-8") as out_f, \
             warn_path.open(fmode, encoding="utf-8") as warn_f:

            if workers <= 1 or mock:
                for sec in pending:
                    row = _process_one(sec, mock)
                    with write_lock:
                        out_f.write(json.dumps(row, ensure_ascii=False) + "\n")
                        out_f.flush()
                        if row["source_scope"] != "case" and not row["summary"]:
                            warn_f.write(json.dumps({"section_node_id": row["section_node_id"],
                                       "warnings": ["missing_summary"]}, ensure_ascii=False) + "\n")
                    total += 1
                    print(f"  [{row['section_node_id']}] {row['model']} summary={len(row['summary'])}chars")
            else:
                t0 = time.time()
                with ThreadPoolExecutor(max_workers=workers) as ex:
                    futures = {ex.submit(_process_one, sec, mock): sec for sec in pending}
                    for i, future in enumerate(as_completed(futures)):
                        row = future.result()
                        with write_lock:
                            out_f.write(json.dumps(row, ensure_ascii=False) + "\n")
                            out_f.flush()
                            if row["source_scope"] != "case" and not row["summary"]:
                                warn_f.write(json.dumps({"section_node_id": row["section_node_id"],
                                           "warnings": ["missing_summary"]}, ensure_ascii=False) + "\n")
                        total += 1
                        if (i + 1) % 10 == 0:
                            elapsed = time.time() - t0
                            print(f"  {i+1}/{len(pending)} ({elapsed:.0f}s)")

    print(f"\n总计: {total} 节")
    return 0


if __name__ == "__main__":
    import sys
    ch = None; limit = 0; mock = False; append = False; workers = 4
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--mock": mock = True
        elif a == "--append": append = True
        elif a.startswith("--workers="): workers = int(a.split("=", 1)[1])
        elif a.startswith("--limit="): limit = int(a.split("=", 1)[1])
        else:
            try: ch = int(a)
            except ValueError: pass
        i += 1
    raise SystemExit(main(chapter=ch, limit=limit, mock=mock, append=append, workers=workers))
