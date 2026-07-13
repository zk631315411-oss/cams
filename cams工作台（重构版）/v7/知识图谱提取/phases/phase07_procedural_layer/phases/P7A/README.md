# P7A：最小流程图 Contract

## 定位

P7A 只冻结 P7 的最小流程图数据结构，让后续阶段能够稳定执行：

```text
P7C 抽图
P7D 校验
P7H 渲染
```

P7A 不负责定义 cluster、scenario path、解析写作策略或渲染实现细节。

## 正本口径

```text
p7_card.flow_nodes / p7_card.flow_edges = 知识正本
steps / summary = 人读辅助
p7_flow_edge_index.jsonl / p7_node_index.jsonl = 派生索引
draw.io / Mermaid / SVG / PNG = 渲染副本
```

## 核心对象

P7A 只定义：

```text
p7_card        # section 内局部执行流程图容器
flow_node      # 只存在于 p7_card.flow_nodes
flow_edge      # 只存在于 p7_card.flow_edges
p7_bridge_edge # card 之间桥接边
```

不再定义 `p7_card_edge`。全局查边时，从 `flow_edges` 导出 `p7_flow_edge_index.jsonl`。

## p7_card

必填字段：

```text
card_id
section_id
card_nature
title
flow_nodes
flow_edges
source_unit_ids
candidate_status
```

可选字段：

```text
summary
scenario
trigger
objective
actor
inputs
decision_standard
outputs
steps
review_notes
metadata
```

`summary` 是一两句话的人读简述，不替代 `scenario` / `trigger` / `objective`。

`scenario` / `trigger` / `objective` 是检索和人读辅助字段，不是知识正本。正式触发条件优先由 `flow_nodes` 中的 `trigger` 节点表达。

`card_nature` 用于说明 card 的知识用途，必填：

```text
execution       严格执行流程：触发、步骤、分支、输出
assessment      评估判断流程：评估对象、判断标准、结果
risk_indicator  风险因素/红旗指标卡：风险场景、指标、风险结论
control         控制措施/治理要求卡：控制动作、控制目标、适用场景、预期效果
```

`execution` / `control` 更适合作为“怎么做”的路径；`assessment` / `risk_indicator` 更适合作为“怎么判断”的标准或触发依据。

## flow_node

必填字段：

```text
node_id
node_category
node_type
label
evidence_unit_ids
evidence_strength
```

可选字段：

```text
actor
description
source_quote
modality
```

旧产物中的节点`review_status`仅作为兼容字段保留，新P7C产物不写入该字段。

节点类型（25 种语义节点，按 `node_category` 分组）：

```text
入口类型（node_category = entry）：
E1_event_signal          事件/信号
E2_object_entry          对象进入
E3_state_threshold       状态/阈值
E4_handoff               上游交接
E5_time_cycle            时间/周期
E6_change_exception      变化/例外
E7_external_command      外部指令/义务
E8_decision_finding      决定/发现

处理类型（node_category = process）：
P1_assessment            评估/分类
P2_execution             执行/转换
P3_branch_routing        条件分支/路由
P4_collection            信息收集/产物装配
P5_coordination          协调/委托
P6_feedback              反馈/补救
P7_monitoring            周期/持续监控
P8_constrained_action    约束型行动
P9_planning              计划/治理
P10_sufficiency          充分性/停止判断

出口类型（node_category = exit）：
X1_classification        分类/判断
X2_product               产物/记录
X3_state_change          状态变化
X4_handoff               交接/升级
X5_config_change         配置/控制变化
X6_termination           终止/无需继续
X7_continuing_obligation 持续义务/受控继续

辅助类型（node_category = auxiliary）：
input                    输入信息
standard                 判断标准
```

`node_type` 前缀含义：`E` = entry（入口）、`P` = process（处理）、`X` = exit（出口）；辅助类型无前缀。`node_category` 与前缀一一对应，用于快速判断节点在流程中的角色。

Card可以是完整entry→process→exit流程，也可以是开放式局部关系；不得为了闭环补造entry或exit。

## flow_edge

必填字段：

```text
edge_id
edge_type
source
target
evidence_unit_ids
derivation
```

可选字段：

```text
relation_type
condition
qualifier
modality
source_quote
```

card 内边类型：

```text
PRECEDES
REFERENCES
PRODUCES
DECIDES
FEEDBACK
```

`source` / `target` 必须指向同一 card 内的 `node_id`。`DECIDES` 边必须用 `condition` 写明分支条件。

## relation_type（业务语义关系）

可选字段，承载考试推理语义。

| 代码 | relation_type | 中文名 | 定义 |
|---|---|---|---|
| R1 | clue_supports_identification | 线索支持识别 | 异常、红旗、事实线索支持考生识别风险 |
| R2 | mechanism_explains_risk | 机制解释风险 | 作案机制解释为什么存在洗钱风险 |
| R3 | identification_leads_to_conclusion | 识别导向结论 | 识别结果导向风险分类或可疑性结论 |
| R4 | conclusion_triggers_response | 结论触发应对 | 风险结论触发加强监控、升级、报告等应对 |
| R5 | branch_condition_routes_path | 分支条件路由 | 判断条件决定进入不同分支路径 |
| R6 | component_assembles_product | 组件装配产物 | 信息组件共同构成正式产物 |
| R7 | standard_constrains_action | 标准约束行动 | 法律、保密等标准限定动作执行 |
| R8 | result_handoffs_stage | 结果交接下游 | 当前结果成为下一阶段的输入 |
| R9 | feedback_requests_completion | 反馈要求补充 | 复核问题要求补充研究或修订 |
| R10 | cycle_requires_monitoring | 周期/持续监控 | 周期或持续义务要求复核或继续观察 |
| R11 | standard_transmits_requirement | 标准传导要求 | 国际标准传导为机构控制要求 |
| R12 | parallel_alternative_no_sequence | 并列替代非时序 | 多个标准或红旗互为并列，不应强制时序 |

与 edge_type 的映射关系见 EDGE_CODEBOOK_V1。

## p7_bridge_edge

必填字段：

```text
bridge_id
edge_type
source_card_id
target_card_id
bridge_basis
review_status
```

可选字段：

```text
source_node_id
target_node_id
evidence_unit_ids
condition
notes
```

`edge_type` 固定为 `BRIDGES_TO`。bridge edge 连接 card 与 card，不放入 `flow_edges`。

## 证据与状态

节点`evidence_strength`最小集合（旧产物可包含后3项，新P7C节点只输出`explicit`）：

```text
explicit
functional_dependency
needs_review
rejected
```

`review_status`由P7D用于逐边审核；P7C新产物不写入最终审核状态。旧产物和`p7_bridge_edge`兼容集合为：

```text
needs_review
accepted
rejected
```

## P7A 不定义

```text
p7_card_edge
card_edges
evidence_strength_summary 必填
p7_cluster 详细 schema
p7_scenario_path 详细 schema
draw.io / Mermaid 渲染细节
```

这些内容交给后续阶段或派生脚本处理。

