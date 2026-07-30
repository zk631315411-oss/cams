"""
Step 4C：隐式边发现（跨章语义关系）。

对标 TreeKG HiddenKG/Pred.py。三步：
1. BGE 向量 → 余弦相似度预筛候选对
2. 过滤：已显式连边的跳过 / 同 H2 的跳过 / 相似度过低的跳过
3. LLM 逐对评估 → 判定是否有关系 + 关系类型 + detail

输入：各章的 nodes_accepted.jsonl + edges_for_merge.jsonl（显式边，用于过滤）
输出：edges_hidden.jsonl
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from collections import defaultdict

import numpy as np
from openai import OpenAI

_WORK = Path(__file__).resolve().parent / "work"
_DS_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
_MIMO_API_KEY = os.environ.get("MIMO_API_KEY", "")

_TEMPERATURE = 0.0
_MAX_TOKENS = 1024
_COS_MIN = 0.65       # 余弦相似度阈值
_TOP_K = 300           # 最多候选对数
_PER_NODE_CAP = 8      # 每个节点最多保留 N 个候选
_BATCH_SIZE = 15       # LLM 每批评估的对数
_STRENGTH_MIN = 4      # LLM 评估强度低于此值→舍弃（0-10）

VALID_EDGE_TYPES = {"包含", "并列", "导致", "缓解", "前提", "依据"}

PROMPT = """你是CAMS反洗钱教材知识图谱关系评估助手。评估给定的节点对之间是否存在知识关系。

判断标准：
- 两个节点讨论的是否是同一类知识或存在直接逻辑联系？
- 比如：一个讲"法规"，另一个讲"该法规要求的制度"，可能存在"依据"关系
- 比如：一个讲"洗钱方法"，另一个讲"该方法的应对措施"，可能存在"缓解"关系
- 如果没有明显直接关系，输出 is_relevant: false

## 关系类型（6种）
包含 / 并列 / 导致 / 缓解 / 前提 / 依据

## 输出格式
只输出 JSON 对象：
{
  "pairs": [
    {"pair_id": 0, "is_relevant": true, "type": "包含", "strength": 8, "detail": "贸易洗钱是洗钱方法的一种具体形式"},
    {"pair_id": 1, "is_relevant": false, "type": "", "strength": 0, "detail": ""}
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


def build_prompt(pairs: list[dict]) -> str:
    lines = []
    for p in pairs:
        lines.append(
            f'[{p["pair_id"]}] "{p["u_title"]}" vs "{p["v_title"]}"\n'
            f'  u_def: {p["u_def"]}\n  v_def: {p["v_def"]}'
        )
    return PROMPT + "\n\n" + "\n\n".join(lines)


def main(limit: int = 0, mock: bool = False) -> int:
    # ---- 1. 加载全部通过节点 + 显式边 ----
    all_nodes: list[dict] = []
    explicit_pairs: set[tuple[str, str]] = set()
    node_h2: dict[str, str] = {}

    for ch in [2, 3, 4, 5]:
        nodes = read_jsonl(_WORK / f"ch{ch}" / "nodes_accepted.jsonl")
        edges = read_jsonl(_WORK / f"ch{ch}" / "edges_for_merge.jsonl")
        all_nodes.extend(nodes)
        for e in edges:
            src = e.get("source_node_id", "")
            tgt = e.get("target_node_id", "")
            if src and tgt:
                explicit_pairs.add((src, tgt))
                explicit_pairs.add((tgt, src))
        for n in nodes:
            node_h2[n["node_id"]] = n.get("section", "")

    print(f"节点: {len(all_nodes)}, 显式边: {len(explicit_pairs)//2}")

    if len(all_nodes) < 2:
        print("节点不足，跳过")
        return 0

    # ---- 2. BGE 向量 + 余弦相似度预筛 ----
    print("计算 BGE 向量...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)
    except Exception:
        print("[FAIL] BGE 模型加载失败，请先下载到本地")
        return 1

    node_ids = [n["node_id"] for n in all_nodes]
    node_texts = [n.get("definition", "") + " " + n.get("title", "") for n in all_nodes]
    embeddings = model.encode(node_texts, normalize_embeddings=True)
    N = len(node_ids)

    cos_matrix = embeddings @ embeddings.T
    print(f"余弦矩阵: {N}x{N}")

    # 上三角候选对
    iu, ju = np.triu_indices(N, k=1)
    cos_values = cos_matrix[iu, ju]
    mask = cos_values > _COS_MIN
    print(f"余弦预筛: {mask.sum()} 对 (cos > {_COS_MIN})")

    # ---- 3. 过滤 ----
    candidates: list[tuple[int, int, float]] = []
    for idx in range(len(mask)):
        if not mask[idx]:
            continue
        i, j = int(iu[idx]), int(ju[idx])
        uid, vid = node_ids[i], node_ids[j]

        # 已有显式边 → 跳过
        if (uid, vid) in explicit_pairs:
            continue
        # 同 H2 节 → 跳过（step4 应该已覆盖）
        if node_h2.get(uid) == node_h2.get(vid):
            continue

        candidates.append((i, j, float(cos_values[idx])))

    # 按余弦相似度排序，每节点限 N 个
    candidates.sort(key=lambda x: -x[2])
    per_node_count: dict[int, int] = defaultdict(int)
    filtered: list[tuple[int, int, float]] = []
    for i, j, c in candidates:
        if per_node_count[i] >= _PER_NODE_CAP or per_node_count[j] >= _PER_NODE_CAP:
            continue
        per_node_count[i] += 1
        per_node_count[j] += 1
        filtered.append((i, j, c))

    filtered = filtered[:_TOP_K]
    print(f"最终候选: {len(filtered)} 对 (per_node_cap={_PER_NODE_CAP}, topk={_TOP_K})")

    if not filtered:
        print("无候选对，跳过")
        return 0

    if limit:
        filtered = filtered[:limit]

    # ---- 4. LLM 逐批评估（MiMo 优先 → DS 降级）----
    hidden_edges: list[dict] = []
    total_evaluated = 0
    total_relevant = 0
    model_stats: dict[str, int] = {}

    for batch_start in range(0, len(filtered), _BATCH_SIZE):
        batch = filtered[batch_start:batch_start + _BATCH_SIZE]
        pairs = []
        for idx, (i, j, cos) in enumerate(batch):
            u = all_nodes[i]
            v = all_nodes[j]
            pairs.append({
                "pair_id": idx,
                "u_node_id": u["node_id"], "u_title": u.get("title", ""),
                "u_def": u.get("definition", "")[:80],
                "v_node_id": v["node_id"], "v_title": v.get("title", ""),
                "v_def": v.get("definition", "")[:80],
                "cosine": round(cos, 4),
            })

        if mock:
            raw = {"pairs": [{"pair_id": p["pair_id"], "is_relevant": False, "type": "", "strength": 0, "detail": ""} for p in pairs]}
            mode = "mock"
        else:
            prompt = build_prompt(pairs)
            chain = [
                ("mimo-v2.5", "https://token-plan-cn.xiaomimimo.com/v1", _MIMO_API_KEY),
                ("deepseek-chat", "https://api.deepseek.com/v1", _DS_API_KEY),
            ]
            raw, mode = {"pairs": []}, "all_failed"
            for model, base_url, api_key in chain:
                client = OpenAI(api_key=api_key, base_url=base_url)
                try:
                    resp = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "你只输出合法 JSON 对象。"},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=_TEMPERATURE,
                    )
                    raw = parse_json_response(resp.choices[0].message.content or "{}")
                    mode = model
                    break
                except Exception:
                    pass
            model_stats[mode] = model_stats.get(mode, 0) + 1

        results = raw.get("pairs") if isinstance(raw.get("pairs"), list) else []
        for r in results:
            pid = r.get("pair_id", -1)
            if pid < 0 or pid >= len(pairs):
                continue
            p = pairs[pid]
            is_rel = r.get("is_relevant", False)
            strength = int(r.get("strength", 0))

            if is_rel and strength >= _STRENGTH_MIN:
                rel_type = r.get("type", "")
                if rel_type not in VALID_EDGE_TYPES:
                    rel_type = "导致"  # 默认
                hidden_edges.append({
                    "edge_id": f"hidden:{p['u_node_id']}|{p['v_node_id']}",
                    "source_node_id": p["u_node_id"],
                    "target_node_id": p["v_node_id"],
                    "type": rel_type,
                    "detail": r.get("detail", ""),
                    "evidence_span": "",
                    "source": "hidden",
                    "cosine": p["cosine"],
                    "strength": strength,
                })
                total_relevant += 1

            total_evaluated += 1

        print(f"  batch {batch_start//_BATCH_SIZE + 1}: evaluated={len(pairs)} relevant={sum(1 for r in results if r.get('is_relevant') and int(r.get('strength',0)) >= _STRENGTH_MIN)}")
        time.sleep(0.3)

    # ---- 5. 写入 ----
    out_path = _WORK / "edges_hidden.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for e in hidden_edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"\n总计: {total_evaluated} 对评估, {len(hidden_edges)} 条隐式边 → {out_path}")
    print(f"模型分布: {model_stats}")
    return 0


if __name__ == "__main__":
    import sys
    limit = 0; mock = "--mock" in sys.argv
    for a in sys.argv[1:]:
        if a.startswith("--limit="):
            limit = int(a.split("=", 1)[1])
    print("隐式边发现: BGE预筛 + LLM评估")
    raise SystemExit(main(limit=limit, mock=mock))
