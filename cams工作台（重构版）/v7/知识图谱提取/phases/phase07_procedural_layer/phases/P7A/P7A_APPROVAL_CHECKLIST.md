# P7A v2.1 复核审批清单

## 复核目标

P7A v2.1 的目标是冻结 P7 的流程图 contract。冻结后，P7B 重新生成任务包，P7C 重新跑 smoke，P7D 按本 contract 校验，不再混用旧的 card/steps 口径。

P7 的目的定义为：

> 在 CAMS/AFC 框架下，写出遇到各类业务情境时，机构应该按什么顺序、依据什么标准、由谁执行、在什么条件下分支、产出什么结果的可审计处理流程图。

## 待审批决策

| 编号 | 决策项 | 建议冻结口径 | 状态 |
| --- | --- | --- | --- |
| A1 | P7 总目标 | P7 是场景化执行流程图层，不是重新抽 KG，不是直接写解析。 | 待审批 |
| A2 | card 定义 | `p7card_*` = section 内局部执行流程图容器，card 不跨 section。 | 待审批 |
| A3 | 正本定义 | JSON 中的 `flow_nodes` / `flow_edges` 是知识正本；draw.io / Mermaid / SVG / PNG 是渲染副本。 | 待审批 |
| A4 | steps 定义 | `steps` 是从流程图派生的人读摘要，不参与机器路径推理。 | 待审批 |
| A5 | card 必填字段 | `card_id`、`section_id`、`title`、8 个摘要字段、`flow_nodes`、`flow_edges`、`source_unit_ids`、`evidence_strength_summary`、`review_status`。 | 待审批 |
| A6 | 节点类型 | 只保留 9 类：`start` / `trigger` / `action` / `decision` / `input` / `standard` / `output` / `state` / `end`。 | 待审批 |
| A7 | start 定义 | 当前 card 的局部流程入口，不是全书或客户生命周期起点。 | 待审批 |
| A8 | end 定义 | 当前 card 的局部流程出口、稳定结果或交接点，不代表业务彻底结束。 | 待审批 |
| A9 | decision 定义 | 条件分支必须用 `decision` 节点 + `DECIDES` 边表达。 | 待审批 |
| A10 | edge 类型 | `flow_edges` 是 card 内部边，source/target 指向同 card 内 node_id；`bridge_edges` 是 card 间桥接边，source/target 指向 card 或 card output/trigger。 | 待审批 |
| A11 | DECIDES 条件 | 每条 `DECIDES` 边必须写 `condition`，如 yes/no/if needed/if explainable。 | 待审批 |
| A12 | evidence 规则 | 字段、step、branch、flow_node、flow_edge 都必须引用 unit 证据。 | 待审批 |
| A13 | 证据强度 | `weak_inference` / `no_relation` 不进入正式 flow_edge；边正式层只允许 `explicit` / `functional_dependency`。 | 待审批 |
| A14 | P5 alias | P5 只做术语规范化和别名识别，不作为流程边证据。 | 待审批 |
| A15 | 派生产物 | `p7_flow_edge_index.jsonl`、`p7_node_index.jsonl`、`p7_mermaid_preview.md`、`p7_drawio_preview.drawio` 是派生产物，不进入对象层级。 | 待审批 |
| A16 | 旧产物 | 旧格式 P7C smoke 归档，不参与新版 P7C/P7D。 | 待审批 |

## 需要特别确认的问题

以下问题会影响后续 schema 和 prompt，建议在 P7A 冻结前明确：

1. `title` 是否保持必填？
2. `flow_node.description` 是否保持可选，而不是必填？
3. `start` / `end` 是否允许无直接教材句子，只用同 card 的首尾节点作 `functional_dependency` 证据？
4. `input` / `standard` 是否必须作为节点进入 `flow_nodes`，还是允许只作为摘要字段存在？当前建议：只要被 `USES` 边引用，就必须进入 `flow_nodes`。
5. `accepted` 是否允许 LLM 在 P7C raw 阶段输出？当前建议：允许，但正式接受必须以 P7D/P7 人工复核为准。
6. `evidence_strength_summary` 是否继续作为 card 必填，还是改为 P7D 派生字段？当前建议：改为 P7D 派生字段。

## 冻结后的执行顺序

```text
P7A v2.1 审批冻结
  -> P7B 重新生成 section task/package
  -> P7C 重跑 CH47-S01 smoke
  -> P7D 校验新版 card
  -> P7H 最小 Mermaid/draw.io 渲染验证
```

## 当前建议

建议先批准 A1-A16 的主 contract，再在 P7C smoke 中观察第 1-6 个特别问题是否需要微调。P7A 不是为了追求一次定义完美，而是防止后续阶段继续混用旧口径。
