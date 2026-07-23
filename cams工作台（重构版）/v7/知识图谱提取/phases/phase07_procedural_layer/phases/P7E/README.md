# P7E：跨 Section Card 桥接

## 定位

P7E 读取 P7C 产出的 `cards.raw.json`，生成跨 section 的 card 桥接候选（`p7_bridge_edge`），并通过 LLM 审核筛选出业务逻辑上成立的桥接。

P7E 不修改 card 内部的 `flow_nodes` / `flow_edges`，不合并 cluster，不生成 scenario path。

## 流程

```
cards.raw.json (P7C)
       │
       ▼
generate_bridge_candidates.py    ── 规则生成：双层配对 + outlet/inlet 节点匹配
       │
       ▼
p7e_bridge_candidates.jsonl      ── 候选清单（263 条，47 pass）
       │
       ▼
run_p7e_bridge_review_ds.py      ── LLM 审核：读 card 完整内容，判 accept/reject
       │
       ▼
p7e_bridge_reviews.jsonl         ── 审核结果
p7e_accepted_bridges.jsonl       ── 仅 accepted（可直接使用）
```

## 步骤 1：规则生成

```bash
python scripts/generate_bridge_candidates.py \
  --cards-dir phases/P7C/outputs/<run_id> \
  --dual-layer \
  --packages-dir phases/P7B/section_packages \
  --kg-graph ../phase06_kg_views/outputs/kg_retrieval_graph.json \
  --output-dir outputs/p7e_bridge_v4
```

### 双层配对策略

**Layer 1 — KG 引导**（当前命中 0，等 P4C 补数据）：通过 P6 全局图的 `same_chapter_core_point` + `cross_chapter_core_point` 边，找到存在 KG 关系的 CP 对，再反查覆盖这些 CP 的 card 对。

**Layer 2 — 拓扑匹配**（当前主力）：所有 card 的出口 × 入口做笛卡尔积，5 种信号评分。

### Outlet / Inlet 节点类型（27 种 node_type 体系）

出口（source_card 的 outlet）：
`X1_classification` `X2_product` `X3_state_change` `X4_handoff` `X5_config_change` `X7_continuing_obligation`
`P3_branch_routing`（有 >=2 DECIDES）、`P1_assessment`（有 PRODUCES 到 exit）

入口（target_card 的 inlet）：
`E1_event_signal` `E3_state_threshold` `E8_decision_finding`
`P1_assessment` `P2_execution` `standard` `input`

### 评分信号

| 信号 | 权重 |
|---|---|
| `card_nature_logic` | +2（7 对 nature 方向映射） |
| `label_similarity` | +1~3（节点 label Jaccard 相似度） |
| `lexical_signal` | +1~4（STRONG_TERMS 精确命中） |
| `shared_unit` | +3（card 级 unit 交集） |
| `shared_node_unit` | +3（节点级 unit 交集） |
| `cp_shared_unit` | +2（CP 间共享 unit，跨 section） |
| `section_order` | +1~2（同章邻 section） |

### 输出

`p7e_bridge_candidates.jsonl`，每条候选：
```json
{
  "bridge_id": "p7bridge_CH02-S04_001__CH02-S04_003_001",
  "bridge_semantics": "proceeds_to",
  "bridge_basis": {
    "source": "topology_match",
    "signals": ["card_nature_logic", "label_similarity", "section_order"],
    "topology_match": { "outlet_type": "X1_classification", "inlet_type": "E1_event_signal" }
  },
  "review_status": "needs_review",
  "score": 14,
  "confidence": "candidate"
}
```

## 步骤 2：LLM 审核

```bash
python scripts/run_p7e_bridge_review_ds.py \
  --candidates outputs/p7e_bridge_v4/p7e_bridge_candidates.jsonl \
  --cards-dir phases/P7C/outputs/<run_id> \
  --run-id p7e_review_v1 \
  --model deepseek-v4-pro \
  --thinking-effort none \
  --concurrency 10
```

LLM 收到 source card + target card 的完整 `flow_nodes` + `flow_edges`，以及桥接候选的出口/入口节点，判断：

1. **业务连续性**：source 的出口是否是 target 入口的业务前提？
2. **逻辑方向**：桥接方向是否与业务因果关系一致？
3. **跨 section 合理性**：两个 card 是否属于同一业务领域？

输出 `accepted` / `rejected` + 理由。

## 非目标

- 不生成 cluster
- 不生成 scenario path
- 不把 bridge 写进 card.flow_edges
- 不直接用于答题裁判
