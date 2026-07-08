"""
Step 4A：LLM 审核 Step 4 产出的关系边候选。

对标高代 04c_audit_edges_and_rule_cases.py。按节批处理，给 LLM 原文 + 该节产出的边 →
LLM 逐条输出 accept / review。

输入：leaf_sections.jsonl + edges_raw.jsonl
输出：edges_accepted.jsonl + edges_review.jsonl + edges_for_merge.jsonl（全量）
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path
from collections import Counter

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

_WORK = Path(__file__).resolve().parent / "work"
_DS_API_KEY = "sk-795628e9d4584fc59545d7abac9d1209"
_MIMO_API_KEY = "tp-cl5nzlniz5bfyk9i3wsdw88d25haf8ghdh6nccojrw1hqgc4"

_TEMPERATURE = 0.0
_MAX_TOKENS = 1024

VALID_EDGE_TYPES = {"包含", "并列", "导致", "缓解", "前提", "依据"}
VALID_DECISIONS = {"accept", "review"}

PROMPT = """你是CAMS反洗钱教材知识图谱审核员。审核当前小节中提出的关系边候选。

每条边需判断 accept（通过）还是 review（需人工复核）。

审核标准：
1. 边的两端节点是否正确？（direction 方向是否合理）
2. relation_type 是否匹配本文内容？
3. evidence_span 是否真实存在于原文并支撑该关系？
4. detail 是否准确描述了节点间的关系？

只输出 JSON 对象。

输出格式：
{
  "decisions": [
    {"edge_id": "...:E000", "decision": "accept", "reason": ""},
    {"edge_id": "...:E001", "decision": "review", "reason": "证据句仅提到反洗钱制度，未明确指向FATF作为依据"}
  ]
}

## 当前输入"""


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
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


def build_payload(section: dict, edges: list[dict]) -> dict:
    compact = []
    for e in edges:
        compact.append({
            "edge_id": e["edge_id"],
            "source": e.get("source_node_id", ""),
            "target": e.get("target_node_id", ""),
            "type": e.get("type", ""),
            "detail": e.get("detail", ""),
            "evidence_span": (e.get("evidence_span") or "")[:200],
        })
    return {
        "section_metadata": {
            "section_node_id": section["section_node_id"],
            "chapter": section.get("chapter", ""),
            "section": section.get("section", ""),
            "subsection": section.get("subsection", ""),
        },
        "section_text": section.get("text", ""),
        "edge_candidates": compact,
    }


def try_llm(client: OpenAI, model: str, payload_str: str) -> dict:
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你只输出合法 JSON 对象。"},
            {"role": "user", "content": PROMPT + "\n\n" + payload_str},
        ],
        temperature=_TEMPERATURE,
    )
    content = resp.choices[0].message.content or ""
    if not content.strip():
        raise ValueError("empty_response")
    return parse_json_response(content)


def call_llm_composite(section: dict, edges: list[dict]) -> tuple[dict, str]:
    payload_str = json.dumps(build_payload(section, edges), ensure_ascii=False)
    chain = [
        ("mimo-v2.5", "https://token-plan-cn.xiaomimimo.com/v1", _MIMO_API_KEY),
        ("deepseek-chat", "https://api.deepseek.com/v1", _DS_API_KEY),
    ]
    for model, base_url, api_key in chain:
        client = OpenAI(api_key=api_key, base_url=base_url)
        retries = 1 if "mimo" in model.lower() else 2
        for attempt in range(retries):
            try:
                result = try_llm(client, model, payload_str)
                return result, model
            except Exception:
                if attempt < retries - 1:
                    time.sleep(0.5)
    return {"decisions": []}, "all_failed"


def main(chapter: int | None = None, limit: int = 0, mock: bool = False, append: bool = False, workers: int = 4) -> int:
    chapters = [chapter] if chapter else [2, 3, 4, 5]
    total_accept = 0
    total_review = 0
    model_stats: dict[str, int] = {}

    for ch in chapters:
        leaf_path = _WORK / f"ch{ch}" / "leaf_sections.jsonl"
        edges_path = _WORK / f"ch{ch}" / "edges_raw.jsonl"
        if not leaf_path.exists() or not edges_path.exists():
            print(f"跳过 ch{ch}")
            continue

        sections = {s["section_node_id"]: s for s in read_jsonl(leaf_path)}
        edges = read_jsonl(edges_path)
        if limit > 0:
            edges = edges[:limit]

        # 按节分组边
        edges_by_section: dict[str, list[dict]] = {}
        for e in edges:
            sid = e.get("section_node_id", "")
            edges_by_section.setdefault(sid, []).append(e)

        out_acc = _WORK / f"ch{ch}" / "edges_accepted.jsonl"
        out_rev = _WORK / f"ch{ch}" / "edges_review.jsonl"
        out_merge = _WORK / f"ch{ch}" / "edges_for_merge.jsonl"

        done_sids: set[str] = set()
        if append and out_merge.exists():
            with out_merge.open("r", encoding="utf-8") as f:
                for line in f:
                    d = json.loads(line)
                    done_sids.add(d.get("section_node_id", ""))

        print(f"\n===== 第{ch}章: {len(edges_by_section)} 节有边 =====")
        if done_sids:
            print(f"续跑: {len(done_sids)} 节已完成")
        fmode = "a" if append else "w"

        write_lock = threading.Lock()

        def _process_section(sec: dict, batch: list[dict]) -> tuple[list[dict], list[dict], list[dict], str]:
            if mock:
                decisions = [{"edge_id": e["edge_id"], "decision": "accept", "reason": ""} for e in batch]
                mode = "mock"
            else:
                raw, mode = call_llm_composite(sec, batch)
                decisions = raw.get("decisions") if isinstance(raw.get("decisions"), list) else []
            dec_by_id = {d.get("edge_id", ""): d for d in decisions}
            accepted: list[dict] = []
            reviewed: list[dict] = []
            merge_all: list[dict] = []
            for e in batch:
                dec = dec_by_id.get(e["edge_id"], {})
                decision = dec.get("decision", "accept")
                if decision not in VALID_DECISIONS: decision = "accept"
                e["audit_decision"] = decision
                e["audit_reason"] = dec.get("reason", "")
                e["audit_model"] = mode
                e["audited_at"] = datetime.now().isoformat(timespec="seconds")
                merge_all.append(e)
                if decision == "accept": accepted.append(e)
                else: reviewed.append(e)
            return accepted, reviewed, merge_all, mode

        pending = [(sid, batch) for sid, batch in sorted(edges_by_section.items()) if sid not in done_sids and batch]
        print(f"\n===== 第{ch}章: {len(edges_by_section)} 节有边, 待处理 {len(pending)}, workers={workers} =====")

        with out_acc.open(fmode, encoding="utf-8") as fa, \
             out_rev.open(fmode, encoding="utf-8") as fr, \
             out_merge.open(fmode, encoding="utf-8") as fm:

            if workers <= 1 or mock:
                for sid, batch in pending:
                    sec = sections.get(sid)
                    if not sec: continue
                    acc, rev, merge, mode = _process_section(sec, batch)
                    with write_lock:
                        for e in acc: fa.write(json.dumps(e, ensure_ascii=False) + "\n")
                        for e in rev: fr.write(json.dumps(e, ensure_ascii=False) + "\n")
                        for e in merge: fm.write(json.dumps(e, ensure_ascii=False) + "\n")
                    total_accept += len(acc); total_review += len(rev)
                    model_stats[mode] = model_stats.get(mode, 0) + 1
                    print(f"  [{sid}] {mode} accept={len(acc)} review={len(rev)}")
            else:
                t0 = time.time()
                with ThreadPoolExecutor(max_workers=workers) as ex:
                    futures = {}
                    for sid, batch in pending:
                        sec = sections.get(sid)
                        if sec: futures[ex.submit(_process_section, sec, batch)] = sid
                    for i, future in enumerate(as_completed(futures)):
                        acc, rev, merge, mode = future.result()
                        with write_lock:
                            for e in acc: fa.write(json.dumps(e, ensure_ascii=False) + "\n")
                            for e in rev: fr.write(json.dumps(e, ensure_ascii=False) + "\n")
                            for e in merge: fm.write(json.dumps(e, ensure_ascii=False) + "\n")
                        total_accept += len(acc); total_review += len(rev)
                        model_stats[mode] = model_stats.get(mode, 0) + 1
                        if (i + 1) % 10 == 0:
                            print(f"  {i+1}/{len(pending)} acc={total_accept} rev={total_review} ({time.time()-t0:.0f}s)")

    print(f"\n总计: accept={total_accept}, review={total_review}")
    print(f"模型分布: {model_stats}")
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
    print(f"审核策略: MiMo优先 → DS降级  workers={workers}")
    raise SystemExit(main(chapter=ch, limit=limit, mock=mock, append=append, workers=workers))
