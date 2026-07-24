# Phase 07：场景化执行流程图

## 目标

P7 基于 P2-P6 KG 和 unit 证据，生成 CAMS/AFC 场景下的执行流程图：遇到某类情境时，机构应按什么顺序、依据什么标准、由谁执行、在什么条件下分支、产出什么结果。

P7 不是重新抽 KG，也不是直接写考生解析。

## 当前状态

| 子阶段 | 状态 | 说明 |
|---|---|---|
| P7A | 完成 | 最小流程图 contract（p7_card / flow_node / flow_edge / p7_bridge_edge） |
| P7B | 完成 | Section 材料包生成（section_packages） |
| P7C | 进行中 | Section Flow Card 抽取，全书分批执行（batch v8/v9/v10） |
| P7D | **暂时弃用** | Flow Edge 证据审核（2026-07-16 标记弃用，P7G 直接使用 P7C 正本） |
| P7E | 进行中 | 跨 Section Card 桥接 |
| P7G | 进行中 | 按题生成证明路径（card内最小路径运行时，跨card路径待P7E桥接完成后支持） |

## 核心对象

P7A 最小 contract：

```text
p7_card        # section 内局部执行流程图容器
flow_node      # card 内节点（25种语义节点，entry/process/exit/auxiliary 四类）
flow_edge      # card 内边（PRECEDES/REFERENCES/PRODUCES/DECIDES/FEEDBACK）
p7_bridge_edge # card 间桥接边（BRIDGES_TO）
```

派生产物：

```text
p7_flow_edge_index.jsonl
p7_node_index.jsonl
p7_mermaid_preview.md
p7_drawio_preview.drawio
```

## P7C Batch 产物

```text
phases/P7C/outputs/
├── p7c_batch2_v8/   # 第2批 v8
├── p7c_batch3_v8/   # 第3批 v8
├── p7c_batch4_v8/   # 第4批 v8
├── p7c_b2_v9/       # 第2批 v9
├── p7c_b2_v10/      # 第2批 v10（最新）
├── p7c_b3_v10/
├── p7c_b4_v10/
├── p7c_b5_v10/
└── p7c_b6_v10/
```

每个 card 产物包含：cards.raw.json、coverage_adjudication.*、run_manifest.json、prompt.md、raw_response.txt。

## 最小字段

`p7_card` 必填：card_id、section_id、card_nature、title、flow_nodes、flow_edges、source_unit_ids、candidate_status。

`card_nature` 取值：`execution`、`assessment`、`risk_indicator`、`control`。

`flow_node` 必填：node_id、node_category、node_type、label、evidence_unit_ids、evidence_strength。
节点类型见 [完整节点类型表](#节点类型)（共 25 种，按 entry/process/exit/auxiliary 分组）。

`flow_edge` 必填：edge_id、edge_type、source、target、evidence_unit_ids。
边类型：PRECEDES / REFERENCES / PRODUCES / DECIDES / FEEDBACK。
可选：derivation、relation_type、condition、qualifier、modality、source_quote。

## relation_type（业务语义关系）

12 种业务语义关系（R1-R12），从 clue_supports_identification 到 parallel_alternative_no_sequence，承载考试推理语义。详见 `EDGE_CODEBOOK_V1`。

## P7G 证明路径

P7G 是当前最活跃的下游消费端：按题号输入，沿 P7C 正本的 flow_edges 遍历，按 P7D 门禁规则逐边校验，输出最小证明路径。当前支持 card内路径，跨card路径待 P7E 桥接完成后支持。

入口：`scripts/p7_edge_runtime.py`（`--cards` + `--edge-reviews` + `--card-id` + `--start-node` + `--target-node` + `--mode final`）

## 规则

1. P7 不修改 P0-P6 正式产物。
2. P5 alias 只做术语规范化，不作为流程边证据。
3. `flow_edge.source` / `flow_edge.target` 必须指向同一 card 内的 `node_id`。
4. `DECIDES` 边必须用 `condition` 写明分支条件。
5. `BRIDGES_TO` 不进入 `flow_edges`，只进入 `p7_bridge_edge`。
6. 渲染文件和派生索引不能作为知识正本。
7. explicit / strong_inference / weak_inference 必须分层；weak_inference 不进入正式层。
