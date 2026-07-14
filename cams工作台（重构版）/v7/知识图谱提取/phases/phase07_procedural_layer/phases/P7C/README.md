# P7C：Section Flow Card 抽取

## 当前定位

P7C是section-local候选流程知识抽取层。它从P7B证据包中发现并构建候选card，允许保留一定候选噪声；P7D才负责正式结构校验和逐边证据审核。

三阶段P7C card固定写`candidate_status=candidate`。节点`evidence_strength`只说明节点有原文依据；三阶段边不声明`derivation`，该字段和最终审核状态由P7D独立保存。

## 主流程

```text
S1 候选卡片框架发现
  -> S2 KG边界裁决
  -> S3 正式语义构图
  -> P7D 逐边证据审核
```

P7C不读取题目、选项或参考答案，不跨section合并流程。`flow_nodes + flow_edges`是P7C候选图正本；P7D不回写P7C正本。

### S1：候选卡片框架发现

S1高召回地发现可能进入P7的局部流程或判断单元，而不是摘录所有教材事实，也不是输出正式节点和边。

一个候选框架围绕一个中心处理、判断、法律适用或归责，尽量合并其触发/情境、输入/标准、条件、结果、分支或后续行动：

```text
触发 / 情境 / 输入 / 标准 / 条件
                -> 中心处理 / 判断 / 法律适用 / 归责
                -> 结果 / 分支 / 后续行动
```

中心字段必有；原文有入口、依据或出口时应一并保留。原文仅支持“条件或标准 -> 具体处理/判断”时允许开放候选，不得补造出口。纯定义、分类、孤立阈值、普通案例事实和普通机制不是候选框架。

S1模型只接收：

```text
section_id / section_title
完整 section_text_with_unit_anchors
```

`allowed_unit_ids`由Runner从P7B unit集合保留并在返回后校验，不发送给S1模型。S1产物`s1_propositions.json`保留兼容字段`candidate_id, unit_ids, proposition, source_quotes, relation_cues, induction`，并增加候选框架角色、逐unit原文短引和跨unit归纳依据。

### S2：KG边界裁决

S2读取S1候选框架、当前section原文和KG覆盖摘要，只裁决基础KG能否充分表达整张候选框架。S2不构图、不新增节点或边，也不承担P7D审核职责。S2的详细裁决合同将在S1稳定后单独维护。

### S3：正式语义构图

S3只读取S2保留的候选框架和当前section原文，将其构为`flow_nodes + flow_edges`。S3不重新裁决KG边界，也不输出`derivation`或最终审核状态。

## 输入与产物

Runner读取`../P7B/section_packages/<section_id>/task.json`，但不会将完整task、alias、instructions或内部schema说明整体发送给LLM。

三阶段运行目录为`outputs/<run_id>/<section_id>/`：

```text
s1_propositions.json      S1候选卡片框架
boundary_decisions.json   S2 KG边界裁决
construction_audit.json   S3构图或无法构图记录
cards.raw.json            P7C候选card正本
run_manifest.json         本section运行状态
```

最终`coverage_audit.decision`为：

```text
kg_only          基础KG已能充分表达
p7c_card         已构建一张或多张候选card
p7c_ungraphable  属于P7C增量，但S3无法形成方向可靠的候选图
```

## 历史兼容模式

单阶段抽取、Coverage补丁和`--two-stage`仅为历史兼容模式。它们的旧Prompt和产物可读取、可归档，但不是当前三阶段主流程的行为基线。

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
review_notes
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

允许节点类型（27 种语义节点，与 P7A contract / procedural_schema_v2 一致）：

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
并列评估维度不得画成时序链，应优先用 process --REFERENCES--> input/standard 表达
三阶段边不携带derivation或旧evidence_strength；边的证据类型和审核状态由P7D独立保存
```

`REFERENCES`的正本方向固定为`process -> input/standard`。渲染器可反向显示为`input/standard -> process`，推理器可派生反向邻接，但两者都不得改写P7C正本。反向读法仅为“作为输入、线索、判定标准或规范依据”，不表示该辅助节点导致处理动作。

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
只可使用上列 12 种枚举值；不确定时省略 relation_type
branch_condition_routes_path 只能标注带 condition 的 DECIDES 边
standard_constrains_action 与 standard_transmits_requirement 表示标准对行动或要求的具体作用，不得替代通用时序
relation_type 不得与边类型语义矛盾；终止结果应使用 X6_termination 节点表达，而不是把终止含义伪装成普通时序
```

## 历史记录：012 压测

第 012 题压测显示：P7C 能把“已实施控制”和“控制被判断有效”拆开，形成可审查的剩余风险判断链。

当时的候选链口径：

```text
EWRA 识别高固有风险
-> 识别 CDD / EDD / 交易监控等控制
-> 评估控制有效性
-> 使用设计有效性、运行有效性、正确应用/功能性/一致性等并列标准
-> 若控制被判断有效，剩余风险可下降
-> 若剩余风险不在容忍度内，进入 action plan
```

这只是当时针对第012题的探索记录，不构成P7C已可进入card间连接、场景路径或端到端生产阶段的验收结论。

## 证据

P7C节点`evidence_strength`只能为`explicit`。三阶段P7C边不输出`derivation`；旧单阶段/两阶段产物可兼容：

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
