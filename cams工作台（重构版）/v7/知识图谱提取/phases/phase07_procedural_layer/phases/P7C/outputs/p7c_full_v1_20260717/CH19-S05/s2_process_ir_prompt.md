# P7C Process IR v1

## 角色与唯一职责

你是 P7C Process IR 建模器。输入为 section 原文和 S1 合并候选列表；你的唯一职责是联合识别局部流程的边界、元素和关系，输出完整的 Process IR。

不得读取 KG，不得输出 `kg_only/p7c_candidate`，不得生成 flow_nodes/flow_edges/card_id/edge_id。元素和关系的语义建模由你完成；ID 生成、方向确定和结构编译由后续脚本确定性完成。

## 1. 流程的通用定义

**正向**：流程（episode）是程序性或判断性迁移——它必须说明某个情境、条件、线索、标准、判断结果，或者原文明示的业务识别、调查、审查、分析、决策或控制过程，如何**改变、产生、约束或触发**一个业务判断、行动、发现、结论、分类、义务、分支、产物、状态变化或后续程序。

**反向**：如果一条关系只是在描述知识内容（是什么、包含什么、可能导致什么），而没有改变、产生、约束或触发业务判断或程序，即使它有方向、因果、分类或法律后果，也不是流程。这类内容应走 `excluded_nonprocedural`。

**过程与主体**：流程必须存在原文明示的业务过程、判断或行动。主体可以明确出现，也可以由原文保持未指明；主体未指明时不得由模型补造。核心要求是"过程明确"，不一定是"主体具名"。

## 2. 联合建模规则

你不按"先合并，再识别关系"的严格顺序工作；以下规则必须同时满足：

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
12. **不得重新包装**：不得用"认定""发现""调查"等词重新包装相邻的普通机制或后果，变相把非流程内容伪装成流程。必须先把混合候选拆成不可再分的关系，逐条判断每条是否满足第 1 节的正向定义。

## 3. 开放关系底线

开放关系最低需同时满足：**至少一个业务动作或业务判断 + 至少一个有证据的有向关系**。

"业务判断"包括：风险识别或分类；法律适用、管辖或责任判断；是否满足标准；是否应采取某项行动；调查、审查或分析产生的发现；义务、限制或适用范围判断。不要求具名主体，但原文必须明确存在判断，不能由模型补造。

CH02-S04 c1（英国母公司关联 + 海外贿赂指控 → 引发 UKBA 域外适用关切）应进入 episode，不是 excluded_nonprocedural——原文提供了法律适用标准和判断触发关系，可以没有独立出口，但不是普通事实。

不合格的开放关系：犯罪手法→一般风险、事实→普通损失或处罚、定义→分类、普通案例事实→另一个普通案例事实。

## 4. 被动分类判定

被动语态本身不能决定是否属于流程。被动分类（"被认定""被识别""被归类"等）只有在以下至少一种情况成立时才构成流程元素：

1. 它是原文明示的调查、审查、分析、筛查或标准适用过程的直接输出/结论——原文仅使用"was identified""was found""被认定为"等被动表述但未描述具体调查/审查/分析动作的，不视为"原文明示的过程"，不满足本条件；
2. 它触发了原文明示的后续动作、义务、分支或程序。

否则只是静态分类事实，应走 `excluded_nonprocedural` 或 `support_only`。

## 5. 法律适用优先规则

候选同时涉及法律适用判断（如原文明示"under X Act""依据Y法""regulatory implications under Z"等）的，应优先按法律适用→责任/归责判断路径建模，不因结果包含处罚或责任而直接走 `excluded_nonprocedural`。

## 6. 正反例对照

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

- **UBO 判断**：直接/间接持股、阈值、判断和正反结果属于同一 episode；风险为本设定阈值是另一中心。
- **非法资金还贷**：`怀疑资金非法 -> 不得接受还款` 是合法开放关系。
- **调查发现**：`调查/审查 -> 发现具体安排` 可形成开放关系。
- **并列输入**：多个线索/标准通过 reference 连接共同处理，不串成 sequence。

## 7. 关键词警告

不得根据"调查""if""must""given these findings"等单个词决定是否构成 episode 或选择 relation kind。必须判断原文是否真实包含第 1 节定义的程序性或判断性迁移。

## 8. Episode 拆合判据

一张 episode 可以包含多个动作和判断。不能仅凭 `focal_question` 相同就合并，也不能因为有不同 action/decision 就拆分。

**合并条件（全部满足）**：

1. 各动作共同服务于同一个最终业务判断或处理结果。
2. 中间结果只在当前判断链中使用，没有独立业务完成意义。
3. 各部分之间存在原文明示的输入、标准、先后、分支或结果关系。
4. 合并后形成一个连通图，不需要补造桥接边。

**拆分条件（满足任一）**：

1. 前一过程产生可独立保存、复用或交接的结果。
2. 后一过程可以在不同时间、主体或业务对象上重复使用该结果。
3. 两部分分别回答不同的业务问题。
4. 连接两部分需要跨 card 桥接语义，而非当前局部流程内部关系。

**总判据**：

> 若中间结果能够作为独立配置、分类、记录、产物或交接状态被后续流程重复使用，则在该结果处切分 episode；若中间动作仅为完成同一最终判断所必需、停止于此不能形成独立业务结果，则保留在同一 episode。

CH06-S10 示例：

- "风险水平 → 机构设定适用阈值 → 产出可复用的阈值配置" → 独立 episode（阈值是独立产物）
- "直接/间接持股 + 已设定阈值 → 比较判断 → 是否认定 UBO" → 另一 episode（阈值是输入标准）
- "合计直接和间接持股" → 不是独立 episode，只是 UBO 判断的内部步骤

## 9. 输出 Contract

只输出严格 JSON。顶层结构：

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

### 9.1 episode

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

- `episode_id` 在 section 内唯一，格式 `ep_NNN`（从 001 开始）。
- `source_candidate_ids` 至少一个，只能引用当前 S1 合并候选。
- 每个 `source_candidate_id` 至少要有一个 unit 被当前 episode 的 element 或 relation 实际引用；不得只为解释合并而挂名。
- `focal_question` 只能表达一个中心问题。它是边界确定后的摘要，不是拆合判据。
- `card_nature` 限定为 `execution/assessment/risk_indicator/control`。
- 至少包含一个 `action` 或 `decision` 元素，以及至少一条关系。
- 所有元素忽略边方向后必须形成一个连通分量。
- 多个 episode 复用同一 candidate 时必须填写 `split_reason`。

### 9.2 element

```json
{
  "element_id": "e001",
  "role": "standard",
  "label": "适用的受益所有权阈值",
  "evidence_unit_ids": ["v7u_N000489"],
  "modality": null
}
```

`role` 只允许 `context / input / standard / action / decision / outcome`，各角色含义：

```text
context   情境、触发事件、状态、发现——流程的起点
input     输入数据、材料、信息——被处理动作参照
standard  标准、阈值、规范——约束处理动作或判断
action    具体业务处理、执行、收集、协调、监控等动作
decision  判断、分支路由、充分性判定——产出决策
outcome   分类、产物、状态变化、交接、配置、终止、持续义务——流程的终点或中间结果
```

约束：

- `element_id` 在 episode 内唯一，格式 `eNNN`（从 001 开始）。
- `label` 保留原文主体、动作、否定和情态，不写通用占位语。**不得添加原文没有的完成标记**：原文使用"旨在/the purpose is to/以/to mitigate"等目的或意图表述时，outcome label 必须保持目的语态（如"检测异常"），不得加"到/出了/已/已经"等完成标记（如"检测到异常"）。只有原文明示已产生的结果（produces/results in/导致/产生）时才可用结果语态。
- `evidence_unit_ids` 非空且只能引用当前 section。
- element 证据必须来自其 `source_candidate_ids` 覆盖 unit 的并集；不得发现 S1 未承接的新证据链。
- `modality` 只允许 `required/permitted/prohibited/risky/optional` 或 `null`。映射规则：`must/shall/required`→`required`，`may/permitted`→`permitted`，`must not/prohibited`→`prohibited`；`should/might/could`等无法无损映射时填 `null`，并在 label 中保留原词。
- **不得输出 `node_type`**——精确 schema 类型由后续 S3 阶段确定。当前阶段只负责语义角色。

### 9.3 relation

使用带角色名的端点字段。六种 kind：

| kind | 端点字段 | 关键约束 |
|---|---|---|
| `trigger` | `trigger_element_id → process_element_id` | 情境或上一阶段的发现/结果触发后续动作或判断；必填 `trigger_mode`（`event` 或 `condition`）；条件触发必须保留 condition |
| `sequence` | `before_element_id → after_element_id` | — |
| `reference` | `process_element_id → auxiliary_element_id` | reference 方向固定为 process→auxiliary |
| `produce` | `process_element_id → outcome_element_id` | target 必须是独立语义结果；同义出口不得建 relation。原文为"旨在/有助于/可能"等非确定表述时不要求精确——kind 是语义近似，S3 会对照 source_quote 确定精确 edge_type |
| `branch` | `decision_element_id → target_element_id` | P3 至少两个互斥 branch，每条有 condition |
| `feedback` | `result_element_id → process_element_id` | — |

`trigger_mode` 区分：

```text
trigger_mode=event      原文明示事件或发现触发后续动作/判断；condition 可为 null
trigger_mode=condition  原文使用 if/when/unless 等条件门禁；condition 必填
```

不得为了满足字段要求，把普通事件改写为 condition。

**Relation 端点兼容矩阵**：

| kind | 起点 role | 终点 role | 额外约束 |
|---|---|---|---|
| `trigger` | context 或 outcome | action 或 decision | 上一阶段的发现/结果触发后续动作或判断；trigger_mode 按上文校验 |
| `sequence` | action/decision/outcome | action/decision/outcome | 必须是原文明示先后、交接或必要功能先后；context 起点改用 trigger |
| `reference` | action 或 decision | input 或 standard | 终点 role 必须为 input 或 standard |
| `produce` | action 或非 P3 的 decision | outcome | target 必须是独立语义结果；P3 到分支不得伪装为 produce |
| `branch` | decision，且 node_type=P3_branch_routing | action 或 outcome | 至少两个互斥分支；每条 condition 必填 |
| `feedback` | outcome 或 decision | action 或 decision | 原文必须支持复核、补充、更新、调优或再次处理 |

除矩阵允许的组合外一律无效。

```json
{
  "relation_id": "r001",
  "kind": "trigger",
  "trigger_mode": "condition",
  "trigger_element_id": "e001",
  "process_element_id": "e002",
  "condition": "客户被分类为高风险",
  "relation_type": "conclusion_triggers_response",
  "qualifier": null,
  "evidence_unit_ids": ["v7u_N000801"],
  "source_quote": "If the customer is classified as high risk, the institution must apply EDD."
}
```

约束：

- `relation_id` 在 episode 内唯一，格式 `rNNN`（从 001 开始）。
- 所有端点必须引用同一 episode 的 element。
- `evidence_unit_ids` 非空，只能引用当前 section，且必须来自 episode 的 `source_candidate_ids` 所覆盖 unit 并集。
- `relation_type` 必须从以下列表中选择，证据不足时省略：`clue_supports_identification`, `mechanism_explains_risk`, `identification_leads_to_conclusion`, `conclusion_triggers_response`, `branch_condition_routes_path`, `component_assembles_product`, `standard_constrains_action`, `result_handoffs_stage`, `feedback_requests_completion`, `cycle_requires_monitoring`, `standard_transmits_requirement`, `parallel_alternative_no_sequence`。
- `qualifier` 只允许 `aimed_to/may_lead_to/helps_achieve`；不适用时省略或为 null。
- `source_quote` **必填**。每条 relation 必须附带原文明文引文（优先英文原文原文，保留情态动词——can/may/might/helps/purpose is to/produces/results in 等），S3 据此确定精确的 edge_type 和 qualifier。kind 是语义近似，不需要完全精确。
- relation 不使用 `modality`；情态由关联 element 的 label 和 modality 保存。
- 不得输出 `derivation/evidence_strength/review_status/answer_eligible/modality`。

### 9.4 candidate_audit

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

- `mapped`：候选自身独立支持 episode 中至少一条程序性或判断性关系。
- `support_only`：候选自身不能独立支持关系，但为另一 episode 提供必要且有证据的 element；通常是 context/input/standard，也可以是被其他候选关系明确承接的 action/outcome。

**excluded_nonprocedural vs ungraphable**：

- `excluded_nonprocedural`：关系很清楚，但本来就不属于程序或判断图（如贿赂被认定为上游犯罪→导致洗钱——后半段是犯罪机制，不是机构业务流程）。
- `ungraphable`：属于程序内容，但教材没有提供足够信息确定怎么连接。

约束：

- `mapped/support_only` 至少引用一个真实 episode。
- `excluded_nonprocedural/ungraphable` 的 `episode_ids` 为空并写明具体原因。
- 不能使用"KG 已覆盖"作为排除原因。
- candidate 映射到多个 episode 时，audit reason 和 episode `split_reason` 都要解释多个中心。

## 当前section

section_id: `CH19-S05`

section_title: `Financial Action Task Force > FATF 11 Immediate Outcomes`

section_text_with_unit_anchors:

```text
[v7u_N001382|1382] Mutual evaluation reports of member jurisdictions focus on two areas: technical compliance with the FATF Recommendations and the effectiveness of the jurisdiction's overall program.
ZH: FATF互评估报告关注技术合规性和反洗钱体系有效性两大领域。

[v7u_N001383|1383] FATF measures and rates effectiveness using 11 Immediate Outcomes (IOs), with each IO receiving an effectiveness rating of low, moderate, substantial, or high.
ZH: FATF使用11项直接目标（IO）评估有效性，评级分为低、中、显著、高。

[v7u_N001384|1384] For jurisdictions that FATF rates as having low or moderate effectiveness in IOs, FATF provides key recommended actions and tracks the jurisdiction's progress in meeting the recommendations.
ZH: FATF对有效性评级为低或中的司法管辖区提出关键建议并跟踪改进进展。

[v7u_N001385|1385] FATF’s IOs are not meant to be a checklist, but rather a starting point to assist assessors in determining the effectiveness of a jurisdiction's AML/CFT framework. FATF expects assessors to use their judgment and experience in determining their ratings.
ZH: FATF的直接目标并非检查清单，而是评估人员判断反洗钱/反恐怖融资框架有效性的起点。

[v7u_N001386|1386] The table below lists the area of focus and specific outcomes associated with each of the 11 IOs:
ZH: 表格列出了11项直接目标的重点领域和具体成果。

[v7u_N001387|1387] FATF mutual evaluations are peer reviews between FATF member jurisdictions that result in thorough reports that analyze AML procedures and their effectiveness.
ZH: FATF互评估是成员国之间的同行评审，生成分析反洗钱程序及其有效性的详细报告。

[v7u_N001388|1388] A typical report provides an in-depth description and analysis of a jurisdiction’s legal and regulatory framework for preventing criminal abuse of its financial system.
ZH: 典型互评估报告深入描述和分析司法管辖区防止金融系统被犯罪滥用的法律和监管框架。

[v7u_N001389|1389] The report also includes recommendations for jurisdictions to strengthen their capabilities.
ZH: 互评估报告还包括加强司法管辖区能力的建议。

[v7u_N001390|1390] Mutual evaluations are strict, meaning each jurisdiction is only deemed compliant when it can prove the same to other FATF members.
ZH: 互评估要求严格，司法管辖区必须向其他FATF成员证明其合规才能被视为合规。

[v7u_N001391|1391] FATF mutual evaluations have two basic components. The main component is effectiveness and is the focus of an on-site visit to the assessed jurisdiction. During the visit, the assessment team collects evidence demonstrating that the jurisdiction’s measures are operational and deliver the right results.
ZH: FATF互评估有两个基本组成部分，主要部分是有效性，通过现场访问收集证据。

[v7u_N001392|1392] The second component is technical compliance.
ZH: 互评估的第二部分是技术合规性。

[v7u_N001393|1393] The assessed member must provide information on its laws and regulations to combat money laundering and the proliferation of weapons of mass destruction.
ZH: 被评估成员必须提供其打击洗钱和大规模杀伤性武器扩散的法律法规信息。

[v7u_N001394|1394] The goal of technical compliance has been the main focus of FATF.
ZH: 技术合规性曾是FATF的主要关注点。

[v7u_N001395|1395] However, numerous money laundering scandals demonstrated that technical compliance was insufficient, and the main focus was shifted to AML effectiveness.
ZH: 多起洗钱丑闻表明技术合规性不足，FATF重点转向反洗钱有效性。

[v7u_N001396|1396] Expectations about FATF mutual evaluations differ from jurisdiction to jurisdiction, based on AML and other financial crime risks.
ZH: 对FATF互评估的期望因司法管辖区而异，取决于反洗钱及其他金融犯罪风险。

[v7u_N001397|1397] The organization has developed an elaborate assessment methodology to ensure consistent, fair assessments.
ZH: FATF制定了详细的评估方法以确保评估一致、公平。

[v7u_N001398|1398] A complete mutual evaluation takes an average of 18 months.
ZH: 一次完整的互评估平均需要18个月。

[v7u_N001399|1399] The mutual evaluation process has seven stages.
ZH: 互评估流程包含七个阶段。

[v7u_N001400|1400] Getting started:
ZH: 互评估流程的第一个阶段是“开始”。

[v7u_N001401|1401] Assessor training: Training for the experts who will perform assessment
ZH: 评估员培训：为执行评估的专家提供培训

[v7u_N001402|1402] Jurisdiction training: Training for representatives of the evaluated jurisdictions
ZH: 司法管辖区培训：为被评估司法管辖区的代表提供培训

[v7u_N001403|1403] Selection of assessors: Selection of the experts that form the assessment team
ZH: 评估员遴选：选择组成评估团队的专家

[v7u_N001404|1404] Technical review: Assessment team analyzes the jurisdiction’s laws and regulations
ZH: 技术审查：评估团队分析司法管辖区的法律法规

[v7u_N001405|1405] Scoping note: Assessment team identifies areas of focus for the on-site visit
ZH: 范围界定说明：评估团队确定现场访问的重点领域

[v7u_N001406|1406] On-site visit: Assessment team travels to the jurisdiction and reviews the effectiveness of AML regulations
ZH: 现场访问：评估团队前往司法管辖区审查反洗钱法规的有效性

[v7u_N001407|1407] Draft MER: Finalize mutual evaluation report
ZH: 起草互评估报告：完成互评估报告

[v7u_N001408|1408] FATF plenary adoption:
ZH: FATF全体会议通过：互评估报告提交全体会议审议

[v7u_N001409|1409] Plenary discussion: FATF plenary discusses the findings in the report and votes on the ratings
ZH: 全体会议讨论：FATF全体会议讨论报告中的发现并对评级进行投票

[v7u_N001410|1410] Final quality review: All jurisdictions review the report before publishing
ZH: 最终质量审查：所有司法管辖区在报告发布前进行审查

[v7u_N001411|1411] Publication and follow-up: Jurisdiction addresses issues and begins strengthening its AML measures
ZH: 发布与后续行动：司法管辖区解决问题并开始加强反洗钱措施
```

## S1 合并候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001384"
    ],
    "proposition": "FATF对IOs有效性评级低或中的司法管辖区提供关键建议并跟踪其改进进展。",
    "source_quotes": [
      "For jurisdictions that FATF rates as having low or moderate effectiveness in IOs, FATF provides key recommended actions and tracks the jurisdiction's progress in meeting the recommendations."
    ],
    "relation_cues": [
      "rates",
      "provides",
      "tracks"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF对司法管辖区IOs有效性评级为低或中"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FATF提供关键建议并跟踪该司法管辖区在满足建议方面的进展。",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001384",
        "quote": "For jurisdictions that FATF rates as having low or moderate effectiveness in IOs, FATF provides key recommended actions and tracks the jurisdiction's progress in meeting the recommendations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001385"
    ],
    "proposition": "FATF的直接目标作为起点，评估者使用判断和经验确定司法管辖区AML/CFT框架的有效性评级。",
    "source_quotes": [
      "FATF’s IOs are not meant to be a checklist, but rather a starting point to assist assessors in determining the effectiveness of a jurisdiction's AML/CFT framework. FATF expects assessors to use their judgment and experience in determining their ratings."
    ],
    "relation_cues": [
      "not meant",
      "starting point",
      "assist",
      "expects",
      "use"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF的IOs作为评估起点"
      ],
      "basis_or_condition": [
        "评估者的判断和经验"
      ],
      "focal_handling_or_judgment": "评估者确定司法管辖区AML/CFT框架的有效性评级",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001385",
        "quote": "FATF’s IOs are not meant to be a checklist, but rather a starting point to assist assessors in determining the effectiveness of a jurisdiction's AML/CFT framework. FATF expects assessors to use their judgment and experience in determining their ratings."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001390"
    ],
    "proposition": "司法管辖区只有向其他FATF成员证明其合规，才被视为合规。",
    "source_quotes": [
      "Mutual evaluations are strict, meaning each jurisdiction is only deemed compliant when it can prove the same to other FATF members."
    ],
    "relation_cues": [
      "strict",
      "only",
      "when"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "司法管辖区能够向其他FATF成员证明其合规"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "该司法管辖区被视为合规",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001390",
        "quote": "Mutual evaluations are strict, meaning each jurisdiction is only deemed compliant when it can prove the same to other FATF members."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001391"
    ],
    "proposition": "现场访问期间，评估团队收集证据以证明司法管辖区的措施已运行并产生正确结果。",
    "source_quotes": [
      "During the visit, the assessment team collects evidence demonstrating that the jurisdiction’s measures are operational and deliver the right results."
    ],
    "relation_cues": [
      "during",
      "collects",
      "demonstrating"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "现场访问期间"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "评估团队收集证据证明司法管辖区的措施已运行并产生正确结果",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001391",
        "quote": "During the visit, the assessment team collects evidence demonstrating that the jurisdiction’s measures are operational and deliver the right results."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001404"
    ],
    "proposition": "技术审查阶段，评估团队分析司法管辖区的法律法规。",
    "source_quotes": [
      "Technical review: Assessment team analyzes the jurisdiction’s laws and regulations"
    ],
    "relation_cues": [
      "analyzes"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "司法管辖区的法律法规"
      ],
      "focal_handling_or_judgment": "评估团队进行分析",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001404",
        "quote": "Technical review: Assessment team analyzes the jurisdiction’s laws and regulations"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N001405"
    ],
    "proposition": "范围界定说明中，评估团队确定现场访问的重点领域。",
    "source_quotes": [
      "Scoping note: Assessment team identifies areas of focus for the on-site visit"
    ],
    "relation_cues": [
      "identifies"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "评估团队确定重点领域",
      "outcomes_or_paths": [
        "现场访问的重点领域"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001405",
        "quote": "Scoping note: Assessment team identifies areas of focus for the on-site visit"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N001406"
    ],
    "proposition": "现场访问中，评估团队前往司法管辖区并审查反洗钱法规的有效性。",
    "source_quotes": [
      "On-site visit: Assessment team travels to the jurisdiction and reviews the effectiveness of AML regulations"
    ],
    "relation_cues": [
      "travels",
      "reviews"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "现场访问"
      ],
      "basis_or_condition": [
        "反洗钱法规"
      ],
      "focal_handling_or_judgment": "评估团队前往并审查有效性",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001406",
        "quote": "On-site visit: Assessment team travels to the jurisdiction and reviews the effectiveness of AML regulations"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_008",
    "unit_ids": [
      "v7u_N001407"
    ],
    "proposition": "起草MER阶段完成互评估报告。",
    "source_quotes": [
      "Draft MER: Finalize mutual evaluation report"
    ],
    "relation_cues": [
      "Finalize"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "完成互评估报告",
      "outcomes_or_paths": [
        "互评估报告"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001407",
        "quote": "Draft MER: Finalize mutual evaluation report"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_009",
    "unit_ids": [
      "v7u_N001409"
    ],
    "proposition": "全体会议讨论报告发现并对评级投票。",
    "source_quotes": [
      "Plenary discussion: FATF plenary discusses the findings in the report and votes on the ratings"
    ],
    "relation_cues": [
      "discusses",
      "votes on"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF全体会议"
      ],
      "basis_or_condition": [
        "报告中的发现"
      ],
      "focal_handling_or_judgment": "讨论发现并对评级投票",
      "outcomes_or_paths": [
        "评级结果"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001409",
        "quote": "Plenary discussion: FATF plenary discusses the findings in the report and votes on the ratings"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_010",
    "unit_ids": [
      "v7u_N001410"
    ],
    "proposition": "最终质量审查阶段，所有司法管辖区在报告发布前进行审查。",
    "source_quotes": [
      "Final quality review: All jurisdictions review the report before publishing"
    ],
    "relation_cues": [
      "review",
      "before publishing"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "报告发布前"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "所有司法管辖区审查报告",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001410",
        "quote": "Final quality review: All jurisdictions review the report before publishing"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_011",
    "unit_ids": [
      "v7u_N001411"
    ],
    "proposition": "发布与后续行动阶段，司法管辖区解决问题并开始加强反洗钱措施。",
    "source_quotes": [
      "Publication and follow-up: Jurisdiction addresses issues and begins strengthening its AML measures"
    ],
    "relation_cues": [
      "addresses",
      "begins strengthening"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "报告发布后"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "司法管辖区解决问题并加强反洗钱措施",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001411",
        "quote": "Publication and follow-up: Jurisdiction addresses issues and begins strengthening its AML measures"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_gap_ch19_s05_fatf_rates_effectiveness",
    "unit_ids": [
      "v7u_N001383"
    ],
    "proposition": "FATF使用11项直接目标衡量和评级有效性，每个IO获得低、中、显著或高评级。",
    "source_quotes": [
      "FATF measures and rates effectiveness using 11 Immediate Outcomes (IOs), with each IO receiving an effectiveness rating of low, moderate, substantial, or high."
    ],
    "relation_cues": [
      "using",
      "receiving"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "使用11项直接目标(IOs)"
      ],
      "focal_handling_or_judgment": "衡量和评级有效性",
      "outcomes_or_paths": [
        "每个IO获得有效性评级（低、中、显著、高）"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001383",
        "quote": "FATF measures and rates effectiveness using 11 Immediate Outcomes (IOs), with each IO receiving an effectiveness rating of low, moderate, substantial, or high."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_002"
      ],
      "gap_reason": "已有候选只承接了评估者使用IO作为起点并运用判断确定评级，未承接FATF作为主体使用IO衡量和评级有效性这一独立处理链。"
    }
  }
]
```
