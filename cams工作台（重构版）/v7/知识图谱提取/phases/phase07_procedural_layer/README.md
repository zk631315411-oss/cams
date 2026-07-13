# Phase 07：场景化执行流程图

## 目标

P7 基于 P2-P6 KG 和 unit 证据，生成 CAMS/AFC 场景下的执行流程图：遇到某类情境时，机构应按什么顺序、依据什么标准、由谁执行、在什么条件下分支、产出什么结果。

P7 不是重新抽 KG，也不是直接写考生解析。

## 正本与副本

```text
p7_card.flow_nodes / p7_card.flow_edges = 知识正本
steps / summary = 人读辅助
p7_flow_edge_index.jsonl / p7_node_index.jsonl = 派生索引
Mermaid / draw.io / SVG / PNG = 渲染副本
```

`flow_edges` 永远只在 `p7_card` 内作为正本存在。需要全局查边时，由脚本导出索引。

## 核心对象

P7A 最小 contract 只定义：

```text
p7_card        # section 内局部执行流程图容器
flow_node      # card 内节点
flow_edge      # card 内边
p7_bridge_edge # card 间桥接边
```

后续对象按阶段处理：

```text
p7_cluster       # P7F 组合多个 card
p7_scenario_path # P7G 针对题目或业务场景组装路径
```

派生产物：

```text
p7_flow_edge_index.jsonl
p7_node_index.jsonl
p7_mermaid_preview.md
p7_drawio_preview.drawio
```

## 最小字段

`p7_card` 必填：

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

`summary`、`scenario`、`trigger`、`objective` 可选，只做人读和检索辅助；正式触发条件优先由 `flow_nodes` 中的 `trigger` 节点表达。

`card_nature` 必填，取值为 `execution`、`assessment`、`risk_indicator`、`control`。其中 `execution/control` 主要回答“怎么做”，`assessment/risk_indicator` 主要回答“怎么判断”。

`flow_node` 必填：

```text
node_id
node_category
node_type
label
evidence_unit_ids
evidence_strength
```

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

`flow_edge` 必填：

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

`p7_bridge_edge` 只用于 card 间连接，`edge_type` 固定为 `BRIDGES_TO`。

## 阶段

```text
P7A  定最小流程图 contract
P7B  生成 section 材料包
P7C  逐 section 抽 p7_card（v1 usable / frozen-for-next-stage）
P7D  逐边审核 flow_edges 的证据、方向、条件与限定词
P7E  生成 bridge candidates
P7F  合并 cluster
P7G  生成 scenario path
P7H  导出索引与渲染预览
```

P7C 当前只允许 bugfix、字段口径对齐和小幅 prompt 修补；card 间连接、路径组合和渲染预览交给后续阶段处理。

P7C 执行方式可以是子代理/Codex 阅读抽取，也可以是 DS/API 批量初稿生成；二者读取同一套 P7B section package。当前已有子代理产物不因 DS 小样本测试而覆盖，DS 发现只作为后续批处理和复核策略依据。

P7D先做纯结构校验，再由独立LLM逐边审核证据。P7D不修改P7C正本、不重新抽card、不连接card，也不读取题目或答案。只有P7D `accepted`边可进入最终程序性证明；`pending`边只允许扩展检索，关键`llm_inference`边进入人工队列。

## 规则

1. P7 不修改 P0-P6 正式产物。
2. P5 alias 只做术语规范化，不作为流程边证据。
3. `flow_edge.source` / `flow_edge.target` 必须指向同一 card 内的 `node_id`。
4. `DECIDES` 边必须用 `condition` 写明分支条件。
5. `BRIDGES_TO` 不进入 `flow_edges`，只进入 `p7_bridge_edge`。
6. 渲染文件和派生索引不能作为知识正本。
7. P7C节点的`evidence_strength`只描述节点证据，边的`derivation`只描述提取来源；二者都不是最终审核状态。P7D另存逐边`review_status`和完整history。
