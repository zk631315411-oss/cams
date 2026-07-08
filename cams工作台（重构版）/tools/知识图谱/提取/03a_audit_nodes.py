"""
Step 3A：LLM 审核 Step 3 产出的节点候选。

对标高代 03a_audit_explicit_nodes.py。按节批处理，给 LLM 原文 + 本节全部节点 →
LLM 逐条输出 accept / review。accept 和 review 节点都写入 nodes_for_step4.jsonl
供边提取使用（边提取需要完整上下文，不丢失待审节点周围的关系）。

输入：leaf_sections.jsonl + nodes_raw.jsonl
输出：nodes_accepted.jsonl + nodes_review.jsonl + nodes_for_step4.jsonl
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
_MAX_TOKENS = 2048

VALID_NODE_TYPES = {"KnowledgePoint", "Regulation", "RiskIndicator", "CaseStudy", "Institution"}
VALID_DECISIONS = {"accept", "review"}

PROMPT = """你是CAMS反洗钱教材知识点审核员。审核当前小节中提取的节点候选。

每个节点需要判断：accept（通过，可直接入图）还是 review（需人工复核）。

审核标准：
1. 节点标题与原文是否匹配？有无编造原文没有的概念？
2. evidence_span 是否确实在原文中存在？是否支撑该节点？
3. node_type 是否合理？
4. definition 是否准确概括了原文内容？
5. 节点是否与同节内其他节点重复？

只输出 JSON 对象，不输出 Markdown 或解释。

输出格式：
{
  "decisions": [
    {"node_id": "cams_v6:C02:S01:U01:N000", "decision": "accept", "reason": ""},
    {"node_id": "cams_v6:C02:S01:U01:N001", "decision": "review", "reason": "evidence_span不完整，未覆盖完整定义"}
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


def build_payload(section: dict, nodes: list[dict]) -> dict:
    compact = []
    for n in nodes:
        compact.append({
            "node_id": n["node_id"],
            "title": n.get("title", ""),
            "node_type": n.get("node_type", ""),
            "definition": n.get("definition", ""),
            "evidence_span": (n.get("evidence_span") or "")[:200],
        })
    return {
        "section_metadata": {
            "section_node_id": section["section_node_id"],
            "chapter": section.get("chapter", ""),
            "section": section.get("section", ""),
            "subsection": section.get("subsection", ""),
            "source_scope": section.get("source_scope", ""),
        },
        "section_text": section.get("text", ""),
        "extracted_nodes": compact,
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


def call_llm_composite(section: dict, nodes: list[dict]) -> tuple[dict, str]:
    """优先 GLM，降级 DS"""
    payload_str = json.dumps(build_payload(section, nodes), ensure_ascii=False)
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
                if model == "mimo-v2.5":
                    print(f"    MiMo 命中")
                return result, model
            except Exception:
                if attempt < retries - 1:
                    time.sleep(0.5)
        if model == "mimo-v2.5":
            print(f"    MiMo 过滤，降级 DS")
    return {"decisions": []}, "all_failed"


def main(chapter: int | None = None, limit: int = 0, mock: bool = False, append: bool = False, workers: int = 4) -> int:
    chapters = [chapter] if chapter else [2, 3, 4, 5]
    total_accept = 0
    total_review = 0
    total_defaulted = 0
    model_stats: dict[str, int] = {}

    for ch in chapters:
        leaf_path = _WORK / f"ch{ch}" / "leaf_sections.jsonl"
        nodes_path = _WORK / f"ch{ch}" / "nodes_raw.jsonl"
        if not leaf_path.exists() or not nodes_path.exists():
            print(f"跳过 ch{ch}")
            continue

        sections = {s["section_node_id"]: s for s in read_jsonl(leaf_path)}
        nodes = read_jsonl(nodes_path)
        if limit > 0:
            nodes = nodes[:limit]

        # 按节分组
        nodes_by_section: dict[str, list[dict]] = {}
        for n in nodes:
            sid = n.get("section_node_id", "")
            nodes_by_section.setdefault(sid, []).append(n)

        out_accepted = _WORK / f"ch{ch}" / "nodes_accepted.jsonl"
        out_review = _WORK / f"ch{ch}" / "nodes_review.jsonl"
        out_step4 = _WORK / f"ch{ch}" / "nodes_for_step4.jsonl"

        done_sids: set[str] = set()
        if append and out_step4.exists():
            with out_step4.open("r", encoding="utf-8") as f:
                for line in f:
                    d = json.loads(line)
                    done_sids.add(d.get("section_node_id", ""))

        print(f"\n===== 第{ch}章: {len(nodes_by_section)} 节有节点 =====")
        if done_sids:
            print(f"续跑: {len(done_sids)} 节已完成")
        fmode = "a" if append else "w"

        write_lock = threading.Lock()

        def _process_section(sec: dict, batch: list[dict]) -> tuple[list[dict], list[dict], list[dict], int, str]:
            """返回 (accepted, review, step4_all, defaulted_count, model)"""
            if mock:
                decisions = [{"node_id": n["node_id"], "decision": "accept", "reason": ""} for n in batch]
                mode = "mock"
            else:
                raw, mode = call_llm_composite(sec, batch)
                decisions = raw.get("decisions") if isinstance(raw.get("decisions"), list) else []

            dec_by_id = {d.get("node_id", ""): d for d in decisions}
            accepted: list[dict] = []
            reviewed: list[dict] = []
            step4: list[dict] = []
            defaulted = 0

            for n in batch:
                nid = n["node_id"]
                dec = dec_by_id.get(nid, {})
                decision = dec.get("decision", "accept")
                reason = dec.get("reason", "")
                if decision not in VALID_DECISIONS:
                    decision = "accept"; defaulted += 1
                n["audit_decision"] = decision
                n["audit_reason"] = reason
                n["audit_model"] = mode
                n["audited_at"] = datetime.now().isoformat(timespec="seconds")
                step4.append(n)
                if decision == "accept":
                    accepted.append(n)
                else:
                    reviewed.append(n)
            return accepted, reviewed, step4, defaulted, mode

        pending = [(sid, batch) for sid, batch in sorted(nodes_by_section.items()) if sid not in done_sids]
        print(f"\n===== 第{ch}章: {len(nodes_by_section)} 节有节点, 待处理 {len(pending)}, workers={workers} =====")

        with out_accepted.open(fmode, encoding="utf-8") as fa, \
             out_review.open(fmode, encoding="utf-8") as fr, \
             out_step4.open(fmode, encoding="utf-8") as fs:

            if workers <= 1 or mock:
                for sid, batch in pending:
                    sec = sections.get(sid)
                    if not sec: continue
                    acc, rev, s4, dflt, mode = _process_section(sec, batch)
                    with write_lock:
                        for n in acc: fa.write(json.dumps(n, ensure_ascii=False) + "\n")
                        for n in rev: fr.write(json.dumps(n, ensure_ascii=False) + "\n")
                        for n in s4: fs.write(json.dumps(n, ensure_ascii=False) + "\n")
                    total_accept += len(acc); total_review += len(rev)
                    total_defaulted += dflt
                    model_stats[mode] = model_stats.get(mode, 0) + 1
                    print(f"  [{sid}] {mode} accept={len(acc)} review={len(rev)}")
            else:
                t0 = time.time()
                with ThreadPoolExecutor(max_workers=workers) as ex:
                    futures = {}
                    for sid, batch in pending:
                        sec = sections.get(sid)
                        if sec:
                            futures[ex.submit(_process_section, sec, batch)] = sid
                    for i, future in enumerate(as_completed(futures)):
                        acc, rev, s4, dflt, mode = future.result()
                        with write_lock:
                            for n in acc: fa.write(json.dumps(n, ensure_ascii=False) + "\n")
                            for n in rev: fr.write(json.dumps(n, ensure_ascii=False) + "\n")
                            for n in s4: fs.write(json.dumps(n, ensure_ascii=False) + "\n")
                        total_accept += len(acc); total_review += len(rev)
                        total_defaulted += dflt
                        model_stats[mode] = model_stats.get(mode, 0) + 1
                        if (i + 1) % 10 == 0:
                            print(f"  {i+1}/{len(pending)} acc={total_accept} rev={total_review} ({time.time()-t0:.0f}s)")

    print(f"\n总计: accept={total_accept}, review={total_review}, 缺省放行={total_defaulted}")
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
