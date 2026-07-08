"""
Step 4：LLM 在定稿节点集上标注关系边。

对标高代 04_extract_explicit_edges.py。按 H2 节批处理，给出当前节原文 + 该节节点 +
全章节点列表，LLM 发现节点间的 6 种关系。

输入：leaf_sections.jsonl + nodes_for_step4.jsonl（03a 产出，含 accept+review）
输出：edges_raw.jsonl
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

VALID_EDGE_TYPES = {"包含", "并列", "导致", "缓解", "前提", "依据"}

PROMPT = """你是CAMS反洗钱教材知识图谱构建助手。你的任务是在给定的节点集上标注关系边。

只输出 JSON 对象，不输出 Markdown 或解释。

## 关系类型（6 种）

- 包含：A 是 B 的上位概念。如"洗钱方法"包含"贸易洗钱"
- 并列：A 和 B 同属一个系列/类别。如"第3号指令"并列"第4号指令"
- 导致：A 引发/加剧 B。如"洗钱"导致"税收损失"
- 缓解：A 降低/对抗风险 B。如"增强尽调"缓解"代理行风险"
- 前提：A 是 B 的前置条件。如"身份识别"前提"风险评估"
- 依据：A 的法律/标准来源是 B。如"KYC制度"依据"FATF建议"

## 规则

- 只能依据当前节原文，不使用外部知识。
- 边的两端节点必须来自给定的节点列表。禁止使用未列出的 node_id。
- 每条边必须有 evidence_span——原文中支撑该关系的句子。
- detail 字段用一句话说明为什么这两个节点有这种关系。
- 空数组是正确答案。不要为了凑数而编造关系。
- 同一节点对之间可以有多条不同类型的边（如 A 同时"包含"B 又"前提"B）。
- 并列边不要滥用：不要把所有同 H2 下的节点都标为并列。

## 输出格式

{
  "edges": [
    {
      "source_node_id": "cams_v6:C02:S01:U01:N000",
      "target_node_id": "cams_v6:C02:S02:U01:N003",
      "type": "导致",
      "detail": "洗钱活动导致政府税收缩水",
      "evidence_span": "洗钱使政府税收缩水，从而间接危害诚实的纳税人。"
    }
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


def compact_node(n: dict) -> dict:
    return {
        "node_id": n.get("node_id", ""),
        "title": n.get("title", ""),
        "node_type": n.get("node_type", ""),
        "definition": n.get("definition", ""),
    }


def build_payload(section: dict, section_nodes: list[dict], all_nodes: list[dict]) -> dict:
    return {
        "section_metadata": {
            "section_node_id": section["section_node_id"],
            "chapter": section.get("chapter", ""),
            "section": section.get("section", ""),
            "subsection": section.get("subsection", ""),
        },
        "section_text": section.get("text", ""),
        "section_nodes": [compact_node(n) for n in section_nodes],
        "global_node_pool": [compact_node(n) for n in all_nodes],
        "allowed_edge_types": sorted(VALID_EDGE_TYPES),
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


def call_llm_composite(section: dict, section_nodes: list[dict], all_nodes: list[dict]) -> tuple[dict, str]:
    payload_str = json.dumps(build_payload(section, section_nodes, all_nodes), ensure_ascii=False)
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
    return {"edges": []}, "all_failed"


def validate_edge(edge: dict, all_node_ids: set[str], section_text: str) -> list[str]:
    warnings = []
    src = edge.get("source_node_id", "")
    tgt = edge.get("target_node_id", "")
    typ = edge.get("type", "")
    detail = edge.get("detail", "")
    evidence = edge.get("evidence_span", "")

    if not src or src not in all_node_ids:
        warnings.append(f"invalid_source:{src}")
    if not tgt or tgt not in all_node_ids:
        warnings.append(f"invalid_target:{tgt}")
    if typ not in VALID_EDGE_TYPES:
        warnings.append(f"invalid_type:{typ}")
    if not detail:
        warnings.append("empty_detail")
    if not evidence or len(evidence.strip()) < 8:
        warnings.append("empty_or_short_evidence")
    else:
        clean_ev = re.sub(r"\s+", "", evidence)
        clean_text = re.sub(r"\s+", "", section_text)
        if len(clean_ev) >= 10 and clean_ev[:10] not in clean_text:
            warnings.append("evidence_not_found_in_text")
    if src == tgt:
        warnings.append("self_loop")
    return warnings


def main(chapter: int | None = None, limit: int = 0, mock: bool = False, append: bool = False, workers: int = 4) -> int:
    chapters = [chapter] if chapter else [2, 3, 4, 5]
    total_edges = 0
    total_accepted = 0
    total_rejected = 0
    model_stats: dict[str, int] = {}

    for ch in chapters:
        leaf_path = _WORK / f"ch{ch}" / "leaf_sections.jsonl"
        nodes_path = _WORK / f"ch{ch}" / "nodes_for_step4.jsonl"
        if not leaf_path.exists() or not nodes_path.exists():
            print(f"跳过 ch{ch}: 缺 leaf_sections 或 nodes_for_step4")
            continue

        sections = {s["section_node_id"]: s for s in read_jsonl(leaf_path)}
        all_nodes = read_jsonl(nodes_path)
        all_node_ids = {n["node_id"] for n in all_nodes}
        if limit > 0:
            all_nodes = all_nodes[:limit]

        # 按 H3 节分组节点
        nodes_by_section: dict[str, list[dict]] = {}
        for n in all_nodes:
            sid = n.get("section_node_id", "")
            nodes_by_section.setdefault(sid, []).append(n)

        out_path = _WORK / f"ch{ch}" / "edges_raw.jsonl"
        warn_path = _WORK / f"ch{ch}" / "edge_extraction_warnings.jsonl"

        # 已写入的边去重 key：source|target|type
        seen_edge_keys: set[str] = set()
        done_sids: set[str] = set()
        if append and out_path.exists():
            with out_path.open("r", encoding="utf-8") as f:
                for line in f:
                    d = json.loads(line)
                    done_sids.add(d.get("section_node_id", ""))
                    key = f'{d.get("source_node_id","")}|{d.get("target_node_id","")}|{d.get("type","")}'
                    seen_edge_keys.add(key)

        print(f"\n===== 第{ch}章: {len(nodes_by_section)} 节有节点 =====")
        if done_sids:
            print(f"续跑: {len(done_sids)} 节已完成, 去重池: {len(seen_edge_keys)} 条边")
        fmode = "a" if append else "w"

        write_lock = threading.Lock()

        def _process_section(sec: dict, sec_nodes: list[dict]) -> tuple[list[dict], list[dict], str]:
            """返回 (edges_with_metadata, warnings, model)"""
            if mock:
                return [], [], "mock"
            raw, mode = call_llm_composite(sec, sec_nodes, all_nodes)
            edges = raw.get("edges") if isinstance(raw.get("edges"), list) else []
            result: list[dict] = []
            warns: list[dict] = []
            for idx, e in enumerate(edges):
                e["edge_id"] = f'{sec["section_node_id"]}:E{idx:03d}'
                e["section_node_id"] = sec["section_node_id"]
                e["model"] = mode
                e["generated_at"] = datetime.now().isoformat(timespec="seconds")
                w = validate_edge(e, all_node_ids, sec.get("text", ""))
                if w:
                    warns.append({"edge_id": e["edge_id"], "warnings": w})
                else:
                    result.append(e)
            return result, warns, mode

        pending = [(sid, sn) for sid, sn in sorted(nodes_by_section.items()) if sid not in done_sids and sn]
        print(f"\n===== 第{ch}章: {len(nodes_by_section)} 节有节点, 待处理 {len(pending)}, workers={workers} =====")

        with out_path.open(fmode, encoding="utf-8") as out_f, \
             warn_path.open(fmode, encoding="utf-8") as warn_f:

            if workers <= 1 or mock:
                for sid, sec_nodes in pending:
                    sec = sections.get(sid)
                    if not sec: continue
                    edges, warns, mode = _process_section(sec, sec_nodes)
                    with write_lock:
                        for w in warns:
                            warn_f.write(json.dumps(w, ensure_ascii=False) + "\n")
                            total_rejected += 1
                        for e in edges:
                            key = f'{e.get("source_node_id","")}|{e.get("target_node_id","")}|{e.get("type","")}'
                            if key in seen_edge_keys: continue
                            seen_edge_keys.add(key)
                            out_f.write(json.dumps(e, ensure_ascii=False) + "\n")
                            total_accepted += 1
                    model_stats[mode] = model_stats.get(mode, 0) + 1
                    total_edges += len(edges) + len(warns)
                    print(f"  [{sid}] {mode} edges={len(edges)+len(warns)} accepted={len(edges)-len(warns)}")
            else:
                t0 = time.time()
                with ThreadPoolExecutor(max_workers=workers) as ex:
                    futures = {}
                    for sid, sec_nodes in pending:
                        sec = sections.get(sid)
                        if sec:
                            futures[ex.submit(_process_section, sec, sec_nodes)] = sid
                    for i, future in enumerate(as_completed(futures)):
                        edges, warns, mode = future.result()
                        with write_lock:
                            for w in warns:
                                warn_f.write(json.dumps(w, ensure_ascii=False) + "\n")
                                total_rejected += 1
                            for e in edges:
                                key = f'{e.get("source_node_id","")}|{e.get("target_node_id","")}|{e.get("type","")}'
                                if key in seen_edge_keys: continue
                                seen_edge_keys.add(key)
                                out_f.write(json.dumps(e, ensure_ascii=False) + "\n")
                                total_accepted += 1
                        model_stats[mode] = model_stats.get(mode, 0) + 1
                        total_edges += len(edges) + len(warns)
                        if (i + 1) % 10 == 0:
                            print(f"  {i+1}/{len(pending)} acc={total_accepted} rej={total_rejected} ({time.time()-t0:.0f}s)")

    print(f"\n总计: 候选边={total_edges}, 通过={total_accepted}, 驳回={total_rejected}")
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
    print(f"提取策略: MiMo优先 → DS降级  workers={workers}")
    raise SystemExit(main(chapter=ch, limit=limit, mock=mock, append=append, workers=workers))
