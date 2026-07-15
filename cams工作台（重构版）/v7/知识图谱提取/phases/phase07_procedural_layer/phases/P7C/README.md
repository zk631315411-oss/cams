# P7C：Section Flow Card 抽取

## 当前定位

P7C是section-local候选流程知识抽取层。它从P7B证据包中发现并构建候选card，允许保留一定候选噪声；P7D才负责正式结构校验和逐边证据审核。

当前主流程在构图前将候选发现拆成S1.1主发现与S1.2独立补漏。P7C card固定写`candidate_status=candidate`。节点`evidence_strength`只说明节点有原文依据；正式构图边不声明`derivation`，该字段和最终审核状态由P7D独立保存。

## 主流程

```text
S1.1 候选卡片框架主发现
  -> S1.2 独立补漏并合并候选
  -> S2 KG边界裁决
  -> S3 正式语义构图
  -> P7D 逐边证据审核
```

P7C不读取题目、选项或参考答案，不跨section合并流程。`flow_nodes + flow_edges`是P7C候选图正本；P7D不回写P7C正本。

### S1.1：候选卡片框架主发现

S1.1高召回地发现可能进入P7的局部流程或判断单元，而不是摘录所有教材事实，也不是输出正式节点和边。它必须独立扫描完整section，不能依赖S1.2替代主发现。

一个候选框架围绕一个中心处理、判断、法律适用或归责，尽量合并其触发/情境、输入/标准、条件、结果、分支或后续行动：

```text
触发 / 情境 / 输入 / 标准 / 条件
                -> 中心处理 / 判断 / 法律适用 / 归责
                -> 结果 / 分支 / 后续行动
```

中心字段必有；原文有入口、依据或出口时应一并保留。原文仅支持“条件或标准 -> 具体处理/判断”时允许开放候选，不得补造出口。纯定义、分类、孤立阈值、普通案例事实和普通机制不是候选框架。

S1.1先在内部逐段扫描完整section，再按中心处理或判断组织候选；已发现一个候选不能成为跳过后续段落的理由。案例中“事实/主体关系/指控 -> 法律适用、责任或监管关切”应作为案例特定法律适用候选，不能被通用法律规则候选替代；具名主体的调查、审查、审计、筛查、分析或跟进产生发现、结论或升级时，应作为“动作/判断 -> 发现/结论”候选。单独的犯罪手法或普通案例事实仍不成候选。

同一判断的输入、计算、标准和正反结果应合并，例如直接与间接持股、适用阈值与UBO认定；风险为本设定阈值和使用既有阈值认定具体UBO属于不同中心，可分别成候选。风险为本规则下针对高风险客户的10%或5%等阈值例外，是“设定或调整适用阈值”的候选，不得降为孤立阈值事实。

S1.1模型只接收：

```text
section_id / section_title
完整 section_text_with_unit_anchors
```

`allowed_unit_ids`由Runner从P7B unit集合保留并在返回后校验，不发送给S1.1模型。S1.1原始产物`s11_propositions.json`保留字段`candidate_id, unit_ids, proposition, source_quotes, relation_cues, induction`，并包含候选框架角色、逐unit原文短引和跨unit归纳依据。

### S1.2：独立补漏

S1.2接收完整带锚点原文和S1.1完整候选列表。它重新扫描section，只增加S1.1未承接的候选，不做KG裁决、不删除或改写S1.1候选，也不构图。S1.2使用与S1.1相同的候选定义和证据合同，并额外说明与哪些S1.1候选比较以及遗漏原因。

Runner在模型返回后校验section、候选ID、unit范围、原文短引、候选框架和`gap_evidence`。S1.2失败时当前section停止，不降级为S1.1-only。成功后，`s1_propositions.json`保存S1.1与S1.2合并后的候选正本，S2只读取该合并集合。

### S2：KG边界裁决

S2读取合并后的S1候选框架、当前section原文和section-local KG表示，只裁决基础KG能否充分表达整张候选框架。S2必须为每个S1候选输出且只输出一条`p7c_candidate`或`kg_only`决定；它不构图、不新增候选、节点或边，也不承担P7D审核职责。

当前保留两套可对照的KG输入：

```text
summary_v1     旧版KG覆盖摘要，仍是生产默认
projection_v1  从P7B task.json逐字段投影的section-local KG事实
```

`projection_v1`只包含以下字段，并保持P7B原始顺序和值：

```text
units: unit_id, type
core_points: core_point_id, title_zh, title_en
core_point_unit_edges: source_id, target_id, relation_type
same_section_core_point_edges: source_id, target_id, relation_type
```

投影不携带`reason`、`source_phase`、证据摘要、alias、任务说明或schema说明。其能力合同为`base_kg_atomic_cp_v1`：KG保存unit、unit类型、CP及section内成员/CP关系，但不因此自动拥有unit内部或unit之间的条件、动作、判断和结果有向图。

`projection_v1`目前只作为隔离的S2 v2 A/B变体。A/B必须读取冻结的合并产物`s1_propositions.json`，保存Prompt、原始响应、解析响应、调用元数据和逐候选对照；缺候选、未知ID、调用/解析/合同失败均使实验无效。当前样本均为开发集，尚无足够真实留出集，因此不得据此切换`summary_v1`默认值；任何晋级还需留出验证和人工批准。

### S3：正式语义构图

S3只读取S2保留的候选框架和当前section原文，将其构为`flow_nodes + flow_edges`。S3不重新裁决KG边界，也不输出`derivation`或最终审核状态。

## 输入与产物

Runner读取`../P7B/section_packages/<section_id>/task.json`，但不会将完整task、alias、instructions或内部schema说明整体发送给LLM。

四阶段运行目录为`outputs/<run_id>/<section_id>/`：

```text
s11_propositions.json     S1.1主发现原始候选
s12_gap_propositions.json S1.2补漏候选
s1_propositions.json      S1.1与S1.2合并候选正本
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

单阶段抽取、Coverage补丁、`--two-stage`和不含S1.2的`--three-stage`仅为历史兼容模式。它们的旧Prompt和产物可读取、可归档，但不是当前四阶段主流程的行为基线。

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

## 实验模式：Merged Process IR v1

`--pipeline-mode merged-process-ir` 启用新的 S2/S3 合并实验流水线，将 KG 边界裁决（旧 S2）和语义构图（旧 S3）替换为：

```text
S1.1 主发现
  -> S1.2 独立补漏
  -> S2 LLM：联合识别局部流程边界、元素和关系，输出 Process IR
  -> S3 脚本：确定性编译 Process IR 为 flow_nodes + flow_edges
  -> P7D LLM：逐边证据审核
```

### 与旧流程的关键差异

1. **S2 不读 KG**。输入只有 section 原文 + S1 候选，不做 KG 对比。问题从"KG 有没有"变为"原文能否构成局部流程"。
2. **允许 KG-P7 重叠**。阈值、标准、事实即使已在 KG 中，只要是流程的构成要素，就可以进入 Process IR。
3. **S3 确定性编译**。构图阶段不再经过 LLM，编译器负责机械映射、ID 生成、方向确定和结构校验。
4. **一次调用替代两次**。S2 + S3 → S2 Process IR（一次 LLM）+ S3 编译器（纯代码）。

### 使用方式

```bash
python scripts/run_p7c_batch_ds.py \
  --pipeline-mode merged-process-ir \
  --process-ir-prompt phases/P7C/prompts/process_ir_v1.md \
  --sections CH06-S10,CH07-S03 \
  --run-id p7c_merged_ir_v1_test
```

### 产物

```text
s11_propositions.json
s12_gap_propositions.json
s1_propositions.json
s2_process_ir_prompt.md
s2_process_ir_raw_response.txt
process_ir.json
compile_audit.json
cards.raw.json
run_manifest.json
```

### 旧 S2/S3 路径

旧 `--four-stage` / `--three-stage` / `--two-stage` 路径继续保留。merged 模式仅在 `--pipeline-mode merged-process-ir` 启用时生效，不删除或覆盖旧 Prompt 和旧产物。

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
