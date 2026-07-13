# P7C：Section Flow Card 抽取

## 状态

P7C当前定位为候选抽取层。

P7C负责生成section-local候选card及覆盖审计，允许保留一定候选噪声。Card只写`candidate_status=candidate`；节点`evidence_strength`和边`derivation`只反映提取依据，不能作为最终程序边放行依据。

正式结构校验和逐边证据审核由P7D完成。生产批处理默认`inline_structure_validation=false`；旧P7C内联校验只作为显式开启的兼容诊断，不是正式审核。

## 定位

P7C 读取 P7B 的 section 材料包，逐 section 抽取 `p7_card`。

P7C 是流程图抽取层：把教材 section 中的可执行内容抽成带 unit 证据的局部执行流程图。

## 输入

Runner加载`../P7B/section_packages/<section_id>/task.json`，但不会把整个task、alias、instructions或旧schema说明发送给LLM。

首次抽取LLM实际接收：

```text
section_id / section_title
完整section_text_with_unit_anchors
allowed_unit_ids
compact_base_kg_summary
```

精简KG摘要只保留CP中英文标题、去重后的covered units及KG role、与去重有关的同section关系类型；不包含内部core_point_id、anchor/key/support三套数组或关系reason。

Coverage是独立无记忆API调用，接收与首次抽取相同的完整section上下文、精简KG摘要、首次抽取完整`original_json`和`review_target_candidate_ids`。它只返回`coverage_adjudication + promoted_cards`补丁，由Runner确定性合并；不能回显或改写首次正本。

## 输出

批处理按run和section保存`outputs/<run_id>/<section_id>/cards.raw.json`；Coverage同时保存原始响应、补丁和合并后的审计产物。

无可执行流程时输出：

```json
{"section_id":"...","section_title":"...","coverage_audit":[],"cards":[],"skip_reason":"基础KG已能充分表达，或当前section不存在证据支持的增量程序性或判断性有向结构。"}
```

## p7_card 最小字段

P7C 每张 card 必须输出：

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

`card_nature` 必填，取值：

```text
execution       严格执行流程：触发、步骤、分支、输出
assessment      评估判断流程：评估对象、判断标准、结果
risk_indicator  风险因素/红旗指标卡：风险场景、指标、风险结论
control         控制措施/治理要求卡：控制动作、控制目标、适用场景、预期效果
```

`execution` / `control` 主要回答“怎么做”；`assessment` / `risk_indicator` 主要回答“怎么判断”。

可选输出：

```text
summary
scenario
trigger
actor
objective
inputs
decision_standard
outputs
steps
review_notes
metadata
```

可选字段不得替代 `flow_nodes` / `flow_edges`。正式触发条件优先由 `trigger` 节点表达。

## Card 粒度

一张card是一个section内局部有向结构，可以是完整闭环，也可以是没有独立出口的开放关系。

判断标准：

```text
至少有一个有证据的process动作或判断
至少有一条有证据的局部有向关系
有独立结果时才建立exit；不得为了闭环补造出口
```

同一 section 可以输出 0..n 张 card。card 不跨 section。

## flow_nodes

允许节点类型（25 种语义节点，与 P7A contract / procedural_schema_v2 一致）：

```text
E1_event_signal
E2_object_entry
E3_state_threshold
E4_handoff
E5_time_cycle
E6_change_exception
E7_external_command
E8_decision_finding
P1_assessment
P2_execution
P3_branch_routing
P4_collection
P5_coordination
P6_feedback
P7_monitoring
P8_constrained_action
P9_planning
P10_sufficiency
X1_classification
X2_product
X3_state_change
X4_handoff
X5_config_change
X6_termination
X7_continuing_obligation
input
standard
```

节点分类（node_category）：

```text
entry       E1–E8 入口类
process     P1–P10 过程类
exit        X1–X7 出口类
auxiliary   input / standard 辅助类
```

必填字段：

```text
node_id
node_category
node_type
label
evidence_unit_ids
evidence_strength
```

规则：

```text
完整闭环应包含有证据的entry；开放式标准/输入约束关系可以不含entry或exit
entry 类节点可作为结构性入口，但不能写入教材没有的业务动作
原文有明确触发条件时，必须建对应的 entry 类节点（如 E1_event_signal / E3_state_threshold）
被 REFERENCES / PRODUCES / FEEDBACK 引用的 input / standard 必须入图
```

## flow_edges

card 内边类型：

```text
PRECEDES
REFERENCES
PRODUCES
DECIDES
FEEDBACK
```

规则：

```text
source / target 必须指向同一 card 内 node_id
条件分支必须用 decision 节点 + DECIDES 边表达
每条 DECIDES 边必须写 condition
不得用 PRECEDES 隐藏条件分支
并列评估维度不得画成时序链，应优先用 action --REFERENCES--> standard 表达
functional_dependency 边必须在 review_notes 中说明是并列维度、条件依赖、结果推导或弱时序重构
```

## relation_type（可选）

每条 flow_edge 可附加 `relation_type` 字段，用于更细粒度地标注边的语义关系。不填时默认按边类型（PRECEDES / REFERENCES / PRODUCES / DECIDES / FEEDBACK）的通用语义理解。

12 种可选值：

```text
clue_supports_identification      线索支持识别
mechanism_explains_risk           机制解释风险
identification_leads_to_conclusion 识别导向结论
conclusion_triggers_response      结论触发应对
branch_condition_routes_path      分支条件路由
component_assembles_product       组件装配产物
standard_constrains_action        标准约束行动
standard_transmits_requirement    标准传导要求
result_handoffs_stage             结果交接下游
feedback_requests_completion      反馈要求补充
cycle_requires_monitoring         周期/持续监控
parallel_alternative_no_sequence  并列替代非时序
```

使用规则：

```text
relation_type 与边类型正交：同一条 PRECEDES 边可以标注 triggers 或 enables
DECIDES 边通常搭配 classifies_into 或 informs
FEEDBACK 边通常搭配 adjusts / monitors / revises
relation_type 不得与边类型语义矛盾（如 PRECEDES + terminates 应改用 X6_termination 节点）
```

## 012 压测结论

第 012 题压测显示：P7C 能把“已实施控制”和“控制被判断有效”拆开，形成可审查的剩余风险判断链。

当前可用口径：

```text
EWRA 识别高固有风险
-> 识别 CDD / EDD / 交易监控等控制
-> 评估控制有效性
-> 使用设计有效性、运行有效性、正确应用/功能性/一致性等并列标准
-> 若控制被判断有效，剩余风险可下降
-> 若剩余风险不在容忍度内，进入 action plan
```

这说明 P7C 已足够进入 card 间连接和场景路径阶段。

## 证据

P7C节点`evidence_strength`只能为`explicit`。P7C边使用独立`derivation`：

```text
explicit_text
llm_inference
```

每个 node / edge 必须绑定当前 section 的 `unit_id`。P5 alias 只能做术语规范化，不能作为证据。

## P7C 不做

```text
不生成 p7_bridge_edge
不跨 section 合并流程
不生成 cluster
不生成 scenario_path
不生成 p7_flow_edge_index.jsonl
不生成 p7_node_index.jsonl
不生成 Mermaid / draw.io
不写考生解析
不读取题目或参考答案
```

## Smoke 验收

```text
card 不跨 section
card 有 title
card 有 flow_nodes / flow_edges
card至少有一个process节点；开放式关系可以没有entry或exit
node / edge 有 unit 证据
flow_edge.source / target 指向同 card 内 node_id
DECIDES 边有 condition
不出现 BRIDGES_TO / cluster / scenario_path / Mermaid / draw.io
```
