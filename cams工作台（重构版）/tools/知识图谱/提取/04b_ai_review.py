"""
Step 4B：AI 对 03a/04a 的 review 项做最终裁决。

对标高代 07a+07b+07d 合并版。收集各章 review 节点和边 →
LLM 逐条输出 accept / reject → 通过的回写 accepted 池，拒绝的归档。

输入：各章的 nodes_review.jsonl + edges_review.jsonl + leaf_sections.jsonl
输出：各章的 nodes_reviewed.jsonl（终裁）+ edges_reviewed.jsonl（终裁）
      同时更新 nodes_accepted.jsonl / edges_accepted.jsonl（追加通过的）
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

from openai import OpenAI

_WORK = Path(__file__).resolve().parent / "work"
_DS_API_KEY = "sk-795628e9d4584fc59545d7abac9d1209"
_MIMO_API_KEY = "tp-cl5nzlniz5bfyk9i3wsdw88d25haf8ghdh6nccojrw1hqgc4"

_TEMPERATURE = 0.0
_MAX_TOKENS = 2048

VALID_DECISIONS = {"accept", "reject"}

PROMPT = """你是CAMS反洗钱教材知识图谱终审员。审阅此前被标记为 review 的节点和边，做最终裁决。

对于每项：accept（通过，可入图）还是 reject（拒绝，不入图）。

审核标准：
- 节点：标题/定义是否准确？evidence_span 是否真实？
- 边：关系方向是否正确？evidence_span 是否支撑该关系？
- 如果有理由 reject，output 中写清原因。
- 如果没有充分理由拒绝，默认 accept。

只输出 JSON 对象。

输出格式：
{
  "node_decisions": [
    {"node_id": "...", "decision": "accept", "reason": ""}
  ],
  "edge_decisions": [
    {"edge_id": "...", "decision": "reject", "reason": "证据句仅提到反洗钱义务，未明确指向制裁合规要求"}
  ]
}

## 当前输入"""


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, items: list[dict]) -> None:
    with path.open("a", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


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


def build_payload(section: dict, review_nodes: list[dict], review_edges: list[dict]) -> dict:
    return {
        "section_metadata": {
            "section_node_id": section["section_node_id"],
            "chapter": section.get("chapter", ""),
            "section": section.get("section", ""),
            "subsection": section.get("subsection", ""),
        },
        "section_text": section.get("text", ""),
        "review_nodes": [
            {
                "node_id": n["node_id"],
                "title": n.get("title", ""),
                "node_type": n.get("node_type", ""),
                "definition": n.get("definition", ""),
                "evidence_span": (n.get("evidence_span") or "")[:200],
                "audit_reason": n.get("audit_reason", ""),
            }
            for n in review_nodes
        ],
        "review_edges": [
            {
                "edge_id": e["edge_id"],
                "source": e.get("source_node_id", ""),
                "target": e.get("target_node_id", ""),
                "type": e.get("type", ""),
                "detail": e.get("detail", ""),
                "evidence_span": (e.get("evidence_span") or "")[:200],
                "audit_reason": e.get("audit_reason", ""),
            }
            for e in review_edges
        ],
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


def call_llm_composite(section: dict, review_nodes: list[dict], review_edges: list[dict]) -> tuple[dict, str]:
    payload_str = json.dumps(build_payload(section, review_nodes, review_edges), ensure_ascii=False)
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
    return {"node_decisions": [], "edge_decisions": []}, "all_failed"


def main(chapter: int | None = None, limit: int = 0, mock: bool = False) -> int:
    chapters = [chapter] if chapter else [2, 3, 4, 5]
    total_node_accept = 0
    total_node_reject = 0
    total_edge_accept = 0
    total_edge_reject = 0

    for ch in chapters:
        leaf_path = _WORK / f"ch{ch}" / "leaf_sections.jsonl"
        nrev_path = _WORK / f"ch{ch}" / "nodes_review.jsonl"
        erev_path = _WORK / f"ch{ch}" / "edges_review.jsonl"

        if not leaf_path.exists():
            print(f"跳过 ch{ch}: 无 leaf_sections")
            continue

        sections = {s["section_node_id"]: s for s in read_jsonl(leaf_path)}
        review_nodes = read_jsonl(nrev_path)
        review_edges = read_jsonl(erev_path)

        if not review_nodes and not review_edges:
            print(f"ch{ch}: 无 review 项，跳过")
            continue

        # 按节分组
        items_by_section: dict[str, dict] = {}
        for n in review_nodes:
            sid = n.get("section_node_id", "")
            items_by_section.setdefault(sid, {"nodes": [], "edges": []})["nodes"].append(n)
        for e in review_edges:
            sid = e.get("section_node_id", "")
            items_by_section.setdefault(sid, {"nodes": [], "edges": []})["edges"].append(e)

        print(f"\n===== 第{ch}章: {len(review_nodes)} 个 review 节点, {len(review_edges)} 条 review 边, {len(items_by_section)} 节 =====")

        node_decisions: dict[str, str] = {}
        edge_decisions: dict[str, str] = {}

        for sid, items in sorted(items_by_section.items()):
            sec = sections.get(sid)
            if not sec:
                continue
            if limit and len(node_decisions) + len(edge_decisions) >= limit:
                break

            if mock:
                raw, mode = {
                    "node_decisions": [{"node_id": n["node_id"], "decision": "accept", "reason": ""} for n in items["nodes"]],
                    "edge_decisions": [{"edge_id": e["edge_id"], "decision": "accept", "reason": ""} for e in items["edges"]],
                }, "mock"
                elapsed = 0.0
            else:
                t0 = time.time()
                raw, mode = call_llm_composite(sec, items["nodes"], items["edges"])
                elapsed = time.time() - t0

            for d in raw.get("node_decisions", []):
                nid = d.get("node_id", "")
                dec = d.get("decision", "accept")
                if nid and dec in VALID_DECISIONS:
                    node_decisions[nid] = dec
            for d in raw.get("edge_decisions", []):
                eid = d.get("edge_id", "")
                dec = d.get("decision", "accept")
                if eid and dec in VALID_DECISIONS:
                    edge_decisions[eid] = dec

            print(f"  [{sid}] {elapsed:.1f}s {mode} node_decisions={len(items['nodes'])} edge_decisions={len(items['edges'])}")

        # 分流
        accepted_nodes = [n for n in review_nodes if node_decisions.get(n["node_id"], "accept") == "accept"]
        rejected_nodes = [n for n in review_nodes if node_decisions.get(n["node_id"]) == "reject"]
        accepted_edges = [e for e in review_edges if edge_decisions.get(e["edge_id"], "accept") == "accept"]
        rejected_edges = [e for e in review_edges if edge_decisions.get(e["edge_id"]) == "reject"]

        now = datetime.now().isoformat(timespec="seconds")
        for n in accepted_nodes:
            n["review_final"] = "accept"; n["reviewed_at"] = now
        for n in rejected_nodes:
            n["review_final"] = "reject"; n["reviewed_at"] = now
        for e in accepted_edges:
            e["review_final"] = "accept"; e["reviewed_at"] = now
        for e in rejected_edges:
            e["review_final"] = "reject"; e["reviewed_at"] = now

        # 写回
        append_jsonl(_WORK / f"ch{ch}" / "nodes_accepted.jsonl", accepted_nodes)
        append_jsonl(_WORK / f"ch{ch}" / "nodes_rejected_final.jsonl", rejected_nodes)
        append_jsonl(_WORK / f"ch{ch}" / "edges_accepted.jsonl", accepted_edges)
        append_jsonl(_WORK / f"ch{ch}" / "edges_rejected_final.jsonl", rejected_edges)

        # 更新 for_step4 / for_merge（把通过的 review 边也加入）
        append_jsonl(_WORK / f"ch{ch}" / "nodes_for_step4.jsonl", accepted_nodes)
        append_jsonl(_WORK / f"ch{ch}" / "edges_for_merge.jsonl", accepted_edges)

        total_node_accept += len(accepted_nodes)
        total_node_reject += len(rejected_nodes)
        total_edge_accept += len(accepted_edges)
        total_edge_reject += len(rejected_edges)

        print(f"  节点: +{len(accepted_nodes)} accept, {len(rejected_nodes)} reject")
        print(f"  边:   +{len(accepted_edges)} accept, {len(rejected_edges)} reject")

    print(f"\n总计 节点: +{total_node_accept} accept, {total_node_reject} reject")
    print(f"总计 边:   +{total_edge_accept} accept, {total_edge_reject} reject")
    return 0


if __name__ == "__main__":
    import sys
    ch = None; limit = 0; mock = False
    for a in sys.argv[1:]:
        if a == "--mock": mock = True
        elif a.startswith("--limit="): limit = int(a.split("=", 1)[1])
        else:
            try: ch = int(a)
            except ValueError: pass
    print("终审策略: MiMo优先 → DS降级")
    raise SystemExit(main(chapter=ch, limit=limit, mock=mock))
