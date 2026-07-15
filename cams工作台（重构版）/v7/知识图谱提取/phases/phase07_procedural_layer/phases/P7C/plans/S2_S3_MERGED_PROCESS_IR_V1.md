# P7C S2/S3 合并实验：局部流程 Process IR v1

## 1. 动机与核心假设

### 旧 S2 的问题

旧的 S2（`kg_boundary_adjudication_v2.md`）让 LLM 判断"KG 是否已经表达了这条候选关系"，输出二元标签 `kg_only` / `p7c_candidate`。现有实验中观察到 CH02-S04 等边界案例的裁决不稳定；由于部分轮次没有使用完全相同的 Prompt hash、冻结输入和独立原始产物，这些结果不能用于断言模型上限，也不能证明问题只来自模型或只来自 Prompt。

本次调整的决定性理由不是"LLM 无法做好 KG 对比"，而是业务合同已经改变：既然 KG 与流程图允许合理重叠，"KG 是否已覆盖"就不应继续充当流程内容的排除门。继续保留该职责会增加一次调用，并可能删除局部流程所需的标准、阈值和背景节点。

### 核心假设

1. **不再读 KG**。S2 输入只有 section 原文 + S1 候选，不做任何形式的 KG 对比。问题从"KG 有没有"变为"原文能否构成局部流程"——后者是语义建模，LLM 擅长；前者是跨表征对比，LLM 不擅长。

2. **允许 KG-P7 重叠**。阈值、标准、事实即使已在 KG 中，只要是流程的构成要素，就可以进入 Process IR。P7 和 KG 是同一原文的两套独立视图，互不排斥。

3. **S3 确定性编译**。构图阶段（element→node, relation→edge）不再经过 LLM。LLM 负责语义理解（识别流程元素和关系），编译器负责机械映射、ID 生成、方向确定和结构校验。消除第二轮 LLM 非确定性。

4. **一次调用替代两次**。S2（边界裁决）+ S3（LLM 构图）→ S2（Process IR）+ S3（确定性编译），减少一次 API 调用。

### 目标流水线

```text
S1.1 主发现
  -> S1.2 独立补漏
  -> S2 LLM：联合识别局部流程边界、元素和关系，输出 Process IR
  -> S3 脚本：确定性编译 Process IR 为 flow_nodes + flow_edges
  -> P7D LLM：逐边证据审核
```

"流程边界识别"和"元素/关系识别"不是两个顺序阶段，而是同一次联合语义建模的两个约束侧面。模型直接输出完整 episode，不先输出独立的候选合并决定。

本轮实现隔离实验模式，不删除或覆盖旧 S2/S3 路径。

## 2. 设计原则

1. KG 与流程图允许交集。阈值、标准、输入和事实即使已进入 KG，只要是局部流程不可缺少的角色，也可进入 Process IR。
2. S2 不读取 KG，不输出 `kg_only/p7c_candidate`。
3. 一个 episode 对应一个 section 内的中心处理、判断、法律适用、归责或应对问题。
4. episode 应是证据支持的局部最大单元；开放关系是证据不完整时的合法结果，不是默认最小粒度。
5. 同一中心的输入、标准、动作、条件和结果应进入同一 episode；不同中心不能因主题相近而合并。
6. 不要求三节点两条边；两节点一条边的开放关系可以合法编译。
7. LLM 负责语义理解，脚本负责 ID、边方向、枚举、连通性和结构。
8. P7D 继续独立审核边的证据、方向、条件和限定词。

## 3. 修改范围

### 本轮修改

- 新增 Process IR Prompt。
- 在 P7C Runner 中增加隔离的 `merged-process-ir` 模式。
- 新增 Process IR validator 和 card compiler（纯代码）。
- 新增 merged 模式的产物目录结构、manifest 和确定性测试。
- 更新 P7C README，标明实验流程与旧流程的关系。

### 本轮不修改

- S1.1、S1.2 Prompt、Schema 和召回合同。
- P7B section package。
- P7D Prompt、逐边审核规则和正式输出合同。
- P7E/P7F/P7G。
- 不新增 `card_shape` 字段。
- 不删除旧 `kg_boundary_adjudication_v2.md` 和 `semantic_graph_construction_v1.md`。
- 不覆盖旧实验输出。

## 4. S2 输入

**发送**：

```text
section_id
section_title
完整 section_text_with_unit_anchors
S1.1 + S1.2 合并后的完整候选列表
```

**不发送**：

```text
base_kg_section_summary
kg_projection
KG capability profile
allowed_unit_ids
旧 boundary_decisions
旧 S3 cards/construction_audit
P7D 审核结果
题目、选项或参考答案
```

`allowed_unit_ids`、unit 原文和 S1 candidate ID 集合由 Runner 内部保留，用于返回后的确定性校验。

## 5. Process IR 合同

顶层：

```json
{
  "section_id": "CH06-S10",
  "episodes": [],
  "candidate_audit": [],
  "skip_reason": null
}
```

顶层一致性约束：

- `episodes` 非空时，`skip_reason` 必须为 `null`。
- `episodes` 为空时，`skip_reason` 必须为非空中文说明。
- 即使 `episodes` 为空，`candidate_audit` 仍必须覆盖全部 S1 candidate。

### 5.1 episode

```json
{
  "episode_id": "ep_001",
  "source_candidate_ids": ["s1c_003", "s1c_gap_001"],
  "focal_question": "如何依据持股比例认定 UBO",
  "title": "依据直接和间接持股及适用阈值认定 UBO",
  "card_nature": "assessment",
  "elements": [],
  "relations": [],
  "split_reason": null
}
```

**基本约束**：

- `episode_id` 在 section 内唯一，格式 `ep_NNN`。
- `source_candidate_ids` 至少一个，只能引用当前 S1 合并候选。
- `focal_question` 只能表达一个中心问题。它是边界确定后的摘要，不是拆合判据。
- `card_nature` 限定为 `execution/assessment/risk_indicator/control`。
- 至少包含一个 `action` 或 `decision` 元素，以及至少一条关系。
- 所有元素忽略边方向后必须形成一个连通分量。
- 多个 episode 复用同一 candidate 时必须填写 `split_reason`。

**Episode 拆合判据：独立完成与接口测试**：

一张 episode 可以包含多个动作和判断。不能仅凭 `focal_question` 相同就合并，也不能因为有不同 action/decision 就拆分。

合并条件（全部满足）：

1. 各动作共同服务于同一个最终业务判断或处理结果。
2. 中间结果只在当前判断链中使用，没有独立业务完成意义。
3. 各部分之间存在原文明示的输入、标准、先后、分支或结果关系。
4. 合并后形成一个连通图，不需要补造桥接边。

拆分条件（满足任一）：

1. 前一过程产生可独立保存、复用或交接的结果。
2. 后一过程可以在不同时间、主体或业务对象上重复使用该结果。
3. 两部分分别回答不同的业务问题。
4. 连接两部分需要跨 card 桥接语义，而非当前局部流程内部关系。

总判据：

> 若中间结果能够作为独立配置、分类、记录、产物或交接状态被后续流程重复使用，则在该结果处切分 episode；若中间动作仅为完成同一最终判断所必需、停止于此不能形成独立业务结果，则保留在同一 episode。

CH06-S10 示例：

- "风险水平 → 机构设定适用阈值 → 产出可复用的阈值配置" → 独立 episode（阈值是独立产物）
- "直接/间接持股 + 已设定阈值 → 比较判断 → 是否认定 UBO" → 另一 episode（阈值是输入标准）
- "合计直接和间接持股" → 不是独立 episode，只是 UBO 判断的内部步骤

**split_reason 定位**：它是 S2 的异常恢复和审计机制，不是正常粒度设计。大量候选被拆分意味着问题在 S1。典型触发场景包括 S1 因共享关键词把"设定阈值"和"使用阈值判断"合并、把"调查→发现""归责""应对"压成一条链、把不同主体/业务目标的动作放入同一候选。`induction=cross_unit` 不等于需要拆分。

### 5.2 element

```json
{
  "element_id": "e001",
  "role": "standard",
  "node_type": "standard",
  "label": "适用的受益所有权阈值",
  "evidence_unit_ids": ["v7u_N000489"],
  "modality": null
}
```

`role` 只允许 `context / input / standard / action / decision / outcome`。

`role/node_type` 兼容关系：

```text
context   -> E1-E8
input     -> input
standard  -> standard
action    -> P1-P2、P4-P10
decision  -> P1_assessment、P3_branch_routing、P10_sufficiency
outcome   -> X1-X7
```

约束：

- `element_id` 在 episode 内唯一。
- `label` 保留原文主体、动作、否定和情态，不写通用占位语。
- `evidence_unit_ids` 非空且只能引用当前 section。
- element 证据必须来自其 `source_candidate_ids` 覆盖 unit 的并集；S2 不得发现 S1 未承接的新证据链。
- `modality` 可为 `null` 或原文明确支持的简短情态值，不得补造强度。
- `node_type` 必须从现行 `procedural_schema_v2.json` 动态读取并校验，不在 compiler 中维护第二份漂移枚举。

### 5.3 relation

Process IR 使用带角色名的端点字段，不让 LLM 直接决定 `flow_edge.source/target`。六种 kind：

| kind | 端点字段 | 编译为 | 关键约束 |
|---|---|---|---|
| `trigger` | `trigger_element_id → process_element_id` | `PRECEDES` | 必填 `trigger_mode`；条件触发必须保留 condition |
| `sequence` | `before_element_id → after_element_id` | `PRECEDES` | — |
| `reference` | `process_element_id → auxiliary_element_id` | `REFERENCES` | 编译固定方向 process→auxiliary |
| `produce` | `process_element_id → outcome_element_id` | `PRODUCES` | 同义出口不得建 relation |
| `branch` | `decision_element_id → target_element_id` | `DECIDES` | P3 至少两个互斥 branch，每条有 condition |
| `feedback` | `result_element_id → process_element_id` | `FEEDBACK` | — |

`trigger` 和 `sequence` 分开是为防止模型混淆触发与时序先后；编译后都进入 `PRECEDES`。trigger 进一步区分：

```text
trigger_mode=event      原文明示事件或发现触发后续动作/判断；condition 可为 null
trigger_mode=condition  原文使用 if/when/unless 等条件门禁；condition 必填
```

不得为了满足字段要求，把普通事件改写为 condition。P7G 会把所有非空 condition 当作路径门禁。

**Relation 端点兼容矩阵**：

| kind | 起点/角色 | 终点/角色 | 额外约束 |
|---|---|---|---|
| `trigger` | context | action 或 decision | trigger_mode 按上文校验 |
| `sequence` | action/decision/outcome | action/decision/outcome | 必须是原文明示先后、交接或必要功能先后；context 起点改用 trigger |
| `reference` | action 或 decision | input 或 standard | `reference_role` 必须与 auxiliary role 一致 |
| `produce` | action 或非 P3 的 decision | outcome | target 必须是独立语义结果；P3 到分支不得伪装为 produce |
| `branch` | decision，且 node_type=P3_branch_routing | action 或 outcome | 至少两个互斥分支；每条 condition 必填 |
| `feedback` | outcome 或 decision | action 或 decision | 原文必须支持复核、补充、更新、调优或再次处理 |

除矩阵允许的组合外一律 validator 失败，不由 compiler 猜测修复。

当前正式 schema 只有五种 flow_edge：PRECEDES、REFERENCES、PRODUCES、DECIDES、FEEDBACK。六种 kind 到五种 edge 是多对一，没有遗漏现行类型。

**三层分离**：IR kind（结构语义）≠ node_type（节点角色）≠ relation_type（业务含义）。例如"升级处理"表示为 process 节点 + X4_handoff 结果 + PRECEDES/PRODUCES/DECIDES + `conclusion_triggers_response` 等 relation_type——不存在 P4_procedure_step 或 P9_escalation 边类型。

relation 可选携带 `relation_type/qualifier/source_quote`，不得输出 `derivation/evidence_strength/review_status/answer_eligible`。

- `relation_id` 在 episode 内唯一，所有端点必须引用同一 episode 的 element。
- `evidence_unit_ids` 非空，只能引用当前 section，且必须来自 episode 的 `source_candidate_ids` 所覆盖 unit 并集。
- `relation_type` 必须从现行 schema 的 12 种枚举动态读取；证据不足时省略。
- `qualifier` 只允许现行合同支持的 `aimed_to/may_lead_to/helps_achieve`；不适用时省略或为 null。
- `source_quote` 如存在，必须能在该 relation 的 `evidence_unit_ids` 对应原文中定位。

### 5.4 candidate_audit

每个 S1 candidate 必须恰好有一条 audit：

```json
{
  "candidate_id": "s1c_003",
  "disposition": "mapped",
  "episode_ids": ["ep_001"],
  "reason": "该候选提供 UBO 判断的输入、标准和正反结果。"
}
```

`disposition` 决策树：

```text
1. 候选自身是否独立支持一条合格的程序性或判断性关系？
   是 → 进入第 2 步
   否 → 它是否能为其他 episode 提供至少一个必要且有证据的 element？
        是 → support_only
        否 → excluded_nonprocedural

2. 该合格关系能否在不补造端点、方向或条件的情况下用 Process IR 表达？
   是 → mapped
   否 → ungraphable
```

**mapped vs support_only**：

- `mapped`：候选自身独立支持 episode 中至少一条程序性或判断性关系（如"高风险客户→必须实施 EDD""调查→发现控制缺陷""达到阈值→认定为 UBO""具有英国关联→UKBA 适用"）。
- `support_only`：候选自身不能独立支持关系，但为另一 episode 提供必要且有证据的 element；通常是 context/input/standard，也可以是被其他候选关系明确承接的 action/outcome（如"适用阈值为 25%"仅提供 standard）。

**excluded_nonprocedural vs ungraphable**：

- `excluded_nonprocedural`：关系很清楚，但本来就不属于程序或判断图。如 CH02-S04 c5"贿赂被认定为上游犯罪→导致洗钱"——后半段是犯罪机制，不是机构业务流程。
- `ungraphable`：属于程序内容，但教材没有提供足够信息确定怎么连接。如"原文明确要求审查和升级，但没有说明二者方向、条件或先后关系"。

约束：

- `mapped/support_only` 至少引用一个真实 episode。
- `excluded_nonprocedural/ungraphable` 的 `episode_ids` 为空并写明具体原因。
- 不能使用"KG 已覆盖"作为排除原因。
- candidate 映射到多个 episode 时，audit reason 和 episode `split_reason` 都要解释多个中心。

## 6. Prompt 设计规则

### 6.1 流程的通用定义

新 Prompt 必须以以下正向和反向定义开篇，作为所有后续规则的判据：

**正向**：流程（episode）是程序性或判断性迁移——它必须说明某个情境、条件、线索、标准、判断结果，或者原文明示的业务识别、调查、审查、分析、决策或控制过程，如何**改变、产生、约束或触发**一个业务判断、行动、发现、结论、分类、义务、分支、产物、状态变化或后续程序。

**反向**：如果一条关系只是在描述知识内容（是什么、包含什么、可能导致什么），而没有改变、产生、约束或触发业务判断或程序，即使它有方向、因果、分类或法律后果，也不是流程。这类内容应走 `excluded_nonprocedural`。

**过程与主体**：流程必须存在原文明示的业务过程、判断或行动。主体可以明确出现，也可以由原文保持未指明；主体未指明时不得由模型补造。核心要求是"过程明确"，不一定是"主体具名"。

### 6.2 联合建模规则

Prompt 不写成"先合并，再识别关系"的严格顺序，要求同时满足：

1. 每个 episode 只有一个中心处理、判断、法律适用、归责或应对问题。
2. 每个 element 必须通过 relation 直接或间接连接到中心 action/decision。
3. 多个候选共同描述同一中心的输入、标准、动作、条件或结果时，组成一个 episode。
4. 一个候选包含两个独立中心或两个不连通关系簇时，拆成不同 episode。
5. 相邻、同主题、同 CP 或共享关键词不能单独证明应合并。
6. 原文已有入口、输入、标准、结果或分支时必须保留，不得只抽最显眼的一条边。
7. 原文只支持开放关系时如实输出，不补造通用入口、出口或持续义务。
8. 静态阈值、定义或事实可以作为合格 episode 的 input/standard/context，但不能在没有处理或判断关系时独立成图。
9. 案例保持案例限定，不从单一案例推广一般规则。
10. 保留 if/when/unless/must/should/may/might/could/only/not 等限定词。
11. 不读取其他 section，不连接 card，不生成 bridge，不读取题目或答案。
12. **不得重新包装**：不得用"认定""发现""调查"等词重新包装相邻的普通机制或后果，变相把非流程内容伪装成流程。必须先把混合候选拆成不可再分的关系，逐条判断每条是否满足 6.1 的正向定义。

### 6.3 开放关系底线

开放关系最低需同时满足：**至少一个业务动作或业务判断 + 至少一个有证据的有向关系**。

"业务判断"包括：风险识别或分类；法律适用、管辖或责任判断；是否满足标准；是否应采取某项行动；调查、审查或分析产生的发现；义务、限制或适用范围判断。不要求具名主体，但原文必须明确存在判断，不能由模型补造。

CH02-S04 c1（英国母公司关联 + 海外贿赂指控 → 引发 UKBA 域外适用关切）应进入 episode，不是 excluded_nonprocedural——原文提供了法律适用标准和判断触发关系，可以没有独立出口，但不是普通事实。

不合格的开放关系：犯罪手法→一般风险、事实→普通损失或处罚、定义→分类、普通案例事实→另一个普通案例事实。

### 6.4 被动分类判定

被动语态本身不能决定是否属于流程。被动分类（"被认定""被识别""被归类"等）只有在以下至少一种情况成立时才构成流程元素：

1. 它是原文明示的调查、审查、分析、筛查或标准适用过程的直接输出/结论——原文仅使用"was identified""was found""被认定为"等被动表述但未描述具体调查/审查/分析动作的，不视为"原文明示的过程"，不满足本条件；
2. 它触发了原文明示的后续动作、义务、分支或程序。

否则只是静态分类事实，应走 `excluded_nonprocedural` 或 `support_only`。

### 6.5 法律适用优先规则

候选同时涉及法律适用判断（如原文明示"under X Act""依据Y法""regulatory implications under Z"等）的，应优先按法律适用→责任/归责判断路径建模，不因结果包含处罚或责任而直接走 `excluded_nonprocedural`。

### 6.6 正反例对照

Prompt 必须包含以下成对正反例（改编自旧 S2 的 7 对对照表）：

| 不构成 episode（走 excluded_nonprocedural 或 support_only） | 构成 episode（mapped） |
|---|---|
| 高风险客户的阈值可能为 10% | 根据客户风险水平，选择适用 25%、10% 或 5% 的阈值 |
| 公司使用中间人实施贿赂 | 调查人员审查交易后，发现公司使用中间人实施贿赂 |
| 内控不足可能增加腐败风险 | 审计发现内控不足后，机构必须整改并重新验证 |
| 某法律是严格的反贿赂法律 | 公司具有该法域联系，因此法律适用并产生母公司责任 |
| EDD 有助于降低金融犯罪风险 | 处理 SPV 时，机构必须实施 EDD，并识别 UBO 和真实目的 |
| 提前还贷可被用于掩盖非法资金来源 | 若银行怀疑还贷资金非法，则不得接受该笔还款 |
| 根据案件事实，公司可能面临处罚 | 监管机构作出高风险分类后，机构必须升级审查并持续监控 |

此外至少包含以下结构示例：

- UBO：直接/间接持股、阈值、判断和正反结果属于同一 episode；风险为本设定阈值是另一中心。
- 非法资金还贷：`怀疑资金非法 -> 不得接受还款` 是合法开放关系。
- 调查发现：`调查/审查 -> 发现具体安排` 可形成开放关系。
- 并列输入：多个线索/标准通过 reference 连接共同处理，不串成 sequence。

### 6.7 关键词警告

不得根据"调查""if""must""given these findings"等单个词决定是否构成 episode 或选择 relation kind。必须判断原文是否真实包含 6.1 定义的程序性或判断性迁移。

## 7. S3 确定性编译器

新增纯代码函数：

```python
validate_process_ir_payload(...)
compile_process_ir_to_cards(...)
```

编译器负责：

1. 每个 episode 生成一张 card，不在编译阶段重新合并或拆分。
2. 稳定生成 `card_id/node_id/edge_id`。
3. element 映射为 flow_node，固定 `evidence_strength=explicit`。
4. 按 5.3 节映射表编译 relation：trigger/sequence→PRECEDES、reference→REFERENCES、produce→PRODUCES、branch→DECIDES、feedback→FEEDBACK。REFERENCES 固定方向 process→auxiliary。
5. 聚合证据生成 `source_unit_ids`。
6. 固定 `candidate_status=candidate`。
7. 生成中文 `review_notes`，但不声明审核结论。新模式不读取 KG，因此不得再写"KG 不足"或声称 KG 未覆盖；固定包含"局部命题、证据范围、可支持判断、待 P7D 逐边审核"。
8. 不写 edge `derivation/evidence_strength/review_status`。
9. 调用现有 card 结构校验器；失败则 section 失败，不自动改写语义结果。

合法结构包括开放关系、完整流程和条件分支。必须拒绝：孤立节点、未知端点、role/node_type 不兼容、P3 单分支、DECIDES 缺 condition、不连通子图、越界 unit。

### 7.1 稳定 ID 与 compile_audit

稳定映射规则：

```text
episode_id  -> card_id
element_id  -> node_id
relation_id -> edge_id
```

同一 section、相同 Process IR 和相同 compiler 版本必须生成相同 ID。不得依赖字典遍历顺序或运行时随机值。

`compile_audit.json` 至少保存：

```json
{
  "section_id": "CH06-S10",
  "compiler_version": "process_ir_compiler_v1",
  "source_process_ir_sha256": "<sha256>",
  "episodes": [
    {
      "episode_id": "ep_001",
      "card_id": "p7card_CH06-S10_001",
      "element_node_map": {"e001": "n001"},
      "relation_edge_map": {"r001": "edge_001"},
      "compile_status": "compiled",
      "errors": []
    }
  ]
}
```

该映射是 Process IR、cards 和 P7D edge review 之间的追溯桥梁。compiler 重跑后如映射或 hash 改变，旧 P7D 审核不得复用。

## 8. Runner 实验模式

在 `scripts/run_p7c_batch_ds.py` 增加隔离参数：

```text
--pipeline-mode merged-process-ir
--process-ir-prompt <path>
```

启用后：运行 S1.1 → S1.2 → 构造 Process IR Prompt → LLM 调用并校验 → 确定性编译 cards → 结构校验 → 写入独立输出目录。

不得自动回退旧 S2/S3，不得在同一 section 混合新旧产物。失败时 manifest 记录 `process_ir_failed` 或 `compile_failed`。旧 `--s2-prompt/--s3-prompt` 路径继续保留。

每个 section 产物：

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

新模式不生成旧 `boundary_decisions.json` 和 LLM 版 `construction_audit.json`。

manifest 至少记录：

```text
pipeline_mode=merged_process_ir_v1
process_ir_episode_count
candidate_audit_count
excluded_nonprocedural_count
ungraphable_count
split_candidate_count
split_candidate_rate
compiled_card_count
process_ir_validation_errors
compile_validation_errors
prompt_sha256
model
thinking_effort
```

`split_candidate_count/rate` 用作 S1 过度合并的诊断指标。

## 9. 确定性测试

新增目录 `phases/P7C/tests/merged_process_ir_v1/`，至少覆盖：

1. Prompt 不含 KG、allowed_unit_ids 和旧裁决。
2. 每个 S1 candidate 恰好有一条 audit。
3. 未知 candidate、episode、element 引用失败。
4. element/relation 越界 unit 失败。
5. element 证据超出 source candidate unit 并集失败。
6. role/node_type 不兼容失败。
7. reference 编译为 process→auxiliary REFERENCES。
8. 五类其他 relation 映射正确（含 trigger 保留 condition）。
9. P3 少于两个分支或缺 condition 失败。
10. 合法两节点开放关系通过。
11. 合法 UBO 多输入、标准、判断和正反分支通过。
12. 孤立元素或不连通 episode 失败。
13. 多 candidate→单 episode 反向映射一致。
14. 单 candidate→多 episode 必须有 split_reason。
15. 编译边不含 derivation、evidence_strength、review_status。
16. 编译 cards 通过现有 P7C/P7D 结构合同。
17. event trigger 允许 condition=null；condition trigger 缺 condition 失败。
18. 六种 relation 的端点 role/node_type 兼容矩阵逐项通过和失败测试。
19. relation_type、qualifier 和 source_quote 使用未知值或越界引文时失败。
20. compile_audit 完整记录 IR→card/node/edge 映射和 source hash。
21. episodes/skip_reason 顶层一致性通过校验。
22. merged 模式新增后，现有旧 S2/S3 Runner、Prompt 渲染和回归测试全部继续通过。

## 10. DS/API 语义测试

确定性测试通过后运行。

固定参数：model=deepseek-v4-pro, thinking=none, temperature=0。先对开发集和回归集共六个 section 六并发；Prompt 冻结后再独立运行真正盲测集。每轮使用全新目录，保存完整 Prompt、原始响应、解析结果、manifest 和 Prompt hash。

**开发集**：

| Section | 验证重点 |
|---|---|
| CH06-S10 | 同中心合并；阈值设定与使用分开；UBO 正反分支完整 |
| CH07-S03 | 非法资金还贷与退出客户核销审批分开；开放关系合法 |

**回归集**（均参与过历史规则讨论，不得称为盲测或留出集）：

| Section | 验证重点 |
|---|---|
| CH02-S04 | 法律适用、调查发现与一般后果边界 |
| CH08-S05 | EDD、UBO、真实目的和控制结果 |
| CH12-S04 | 资产管理、CDD、风险评估和持续监控 |
| CH47-S04 | 动态调优、变化触发和反馈 |

**真正盲测集**：

- 新 Prompt、Schema 和确定性测试冻结后，再从未参与规则设计和历史问题诊断的 section 中随机抽取 2-4 个。
- 抽样前不阅读原文、不按预期流程类型定向挑选。
- 抽样清单、随机方法和 Prompt hash 写入 run manifest。
- 盲测失败不得回写同一轮 Prompt 后继续称为盲测；修改后应重新抽取新的未见 section。

## 11. 验收标准

成功不以 card 数量衡量。逐 section 对照原文检查：

1. S1 已发现的程序/判断信息全部进入 episode 或有可辩护的排除记录。
2. 同一中心未被错误拆碎，不同中心未被错误合并。
3. KG 已保存的阈值、标准或事实在流程需要时未被排除。
4. 没有把纯定义、普通机制或一般后果包装成流程。
5. 没有补造入口、出口、顺序、主体、条件或义务。
6. condition、否定和情态完整保留。
7. Process IR 全部通过确定性编译和结构校验。
8. P7D 可以正常逐边审核。
9. 相比旧 S2+S3，少一次 API 调用，且召回、局部完整性和 P7D 通过率不下降。
10. 真正盲测 section 未出现开发集规则未覆盖的系统性碎片化、误合并或程序信息遗漏。

固定期望：

- CH06-S10："直接/间接持股 + 适用阈值 → 判断 → UBO 正反结果"是一张局部完整 card；"风险为本设定阈值"与"使用阈值判断 UBO"保持不同中心。
- CH07-S03："怀疑非法资金还贷 → 不得接受还款"允许两节点开放关系。

## 12. 晋级与回滚

只有确定性测试全过、六个开发/回归 section 和真正盲测集均无明确程序遗漏、无明显碎片化/误合并、P7D 正常审核且成本下降时，才讨论切换默认流程。

若失败：

- Prompt 问题只修改新 Prompt，在新目录重跑。
- IR 合同问题修改 validator/compiler 并补回归测试。
- 模型不稳定时冻结 Prompt hash 和输入后重复运行。
- 合并模式未达标时继续使用旧 S2/S3，不部分切换生产目录。

## 13. 实施顺序

```text
1. 新建 Process IR Prompt 和 Schema 示例
2. 实现 validate_process_ir_payload()
3. 实现 compile_process_ir_to_cards()
4. 编写 validator/compiler 确定性测试
5. Runner 增加隔离 merged-process-ir 模式
6. 更新 P7C README
7. 运行编译检查和聚焦测试
8. 六个开发/回归 section 六并发运行 DS/API
9. 修正开发问题并冻结 Prompt、Schema、compiler 和测试
10. 随机抽取 2-4 个未见 section，独立运行真正盲测
11. 对照原文、Process IR、cards 和 P7D 结果人工验收
12. 单独提交是否切换默认流程的结论
```

## 14. 完成定义

必须同时交付：

```text
新 Prompt
Process IR validator
Process IR -> card compiler
隔离 Runner 模式
确定性测试
README 更新
六个开发/回归 section API 产物
2-4 个真正盲测 section API 产物
逐 section 人工验收报告
是否晋级默认流程的明确建议
```

只完成 Prompt 或只跑出 JSON 不视为完成。
