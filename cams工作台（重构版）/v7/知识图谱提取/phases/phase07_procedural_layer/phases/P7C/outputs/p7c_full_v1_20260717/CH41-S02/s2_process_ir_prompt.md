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

section_id: `CH41-S02`

section_title: `Governance and oversight > Drafting AFC policies and procedures`

section_text_with_unit_anchors:

```text
[v7u_N002894|2894] AFC policies and procedures form the core of an organization’s AFC compliance framework, ensuring effective risk management, adherence to regulations, and operational integrity.
ZH: 金融犯罪防控政策和程序是组织合规框架的核心，确保风险管理、法规遵守和运营完整性

[v7u_N002895|2895] These policies must be clear, risk-based, and adaptable to evolving business models while aligning with global and jurisdictional AFC standards.
ZH: 金融犯罪防控政策必须清晰、基于风险、适应业务模式变化，并与全球及司法管辖区标准一致

[v7u_N002896|2896] What are AFC policies and procedures?
ZH: 引导性问题：什么是金融犯罪防控政策和程序？

[v7u_N002897|2897] Policies establish the principles, objectives, and regulatory obligations for AFC compliance. They translate legal and regulatory requirements into business-specific commitments.
ZH: 政策确立金融犯罪防控合规的原则、目标和监管义务，将法律法规转化为业务承诺

[v7u_N002898|2898] Procedures provide detailed, step-by-step implementation guidance to ensure policies are applied consistently across different business units and jurisdictions. Separate procedures are often written for a policy to tailor its execution to various business units and jurisdictions.
ZH: 程序提供详细的分步实施指南，确保政策在不同业务单元和司法管辖区一致应用

[v7u_N002899|2899] Why are AFC policies and procedures important?
ZH: 引导性问题：为什么金融犯罪防控政策和程序很重要？

[v7u_N002900|2900] Policies and procedures ensure regulatory compliance. Institutions typically choose to align their policies with FATF Recommendations, Basel Committee on Banking Supervision (BCBS) guidelines, national AML laws, and regulatory expectations.
ZH: 政策和程序确保监管合规，机构通常与FATF建议、巴塞尔委员会指南及国家反洗钱法律保持一致

[v7u_N002901|2901] Policies ensure comprehensive coverage. They should cover all products and services, including future offerings, to prevent compliance gaps.
ZH: 政策应覆盖所有产品和服务，包括未来产品，以防止合规缺口。

[v7u_N002902|2902] To follow a risk-based approach, policies must be tailored to institutional risk exposure, customer profiles, and geographic risk factors.
ZH: 基于风险的方法要求政策根据机构风险敞口、客户概况和地理风险因素量身定制。

[v7u_N002903|2903] To demonstrate proper governance and accountability, a structured policy framework ensures clear roles, responsibilities, and oversight mechanisms for compliance management.
ZH: 结构化政策框架确保合规管理中的明确角色、职责和监督机制。

[v7u_N002904|2904] Organizations should maintain a clearly defined protocol to identify when a new policy must be adopted, as well as the process for drafting, approving, and updating it.
ZH: 机构应维护明确协议，以确定何时采用新政策及其起草、批准和更新流程。

[v7u_N002905|2905] Good policies should include provisions for addressing any exceptions or exemptions and should clearly assign responsibilities to specific people or roles. They should also provide a schedule for reviewing the policy, typically on an annual basis, and stipulate events that would trigger an ad hoc review and update.
ZH: 良好政策应包括例外处理、责任分配和定期审查安排。

[v7u_N002906|2906] Examples include the introduction of a new product or the occurrence of a relevant regulatory event.
ZH: 触发临时审查的事件示例包括新产品推出或相关监管事件。

[v7u_N002907|2907] Detailed implementation guidance is provided in procedures, which are typically tailored to specific business units or other entities. In this way, changes in procedures can be made quickly to reflect changes that do not impact the entire organization.
ZH: 程序提供详细实施指南，可快速调整以适应局部变化。

[v7u_N002908|2908] How are AFC policies designed and implemented?
ZH: 关于金融犯罪防控政策设计与实施的问题引导。

[v7u_N002909|2909] Using a risk-based approach, organizations should customize policies based on customer, product, and transaction risks.
ZH: 基于风险的方法，机构应根据客户、产品和交易风险定制政策。

[v7u_N002910|2910] To ensure jurisdictional compliance, multinational organizations must align policies with country-specific laws, while maintaining global AFC principles. This may result in implementing higher standards in some jurisdictions to maintain global consistency.
ZH: 跨国机构需使政策符合各国法律，同时维持全球金融犯罪防控原则，可能需在部分司法管辖区实施更高标准。

[v7u_N002911|2911] To govern exceptions and dispensations, deviations from policy must be documented, justified, and approved by governance bodies. Where appropriate, dispensation may be provided for a specific time. Any known gaps in implementing policies must be documented and addressed within a reasonable period. A record of issues and policy violations may be centrally maintained for effective governance and oversight.
ZH: 政策偏差需记录、论证并经治理机构批准，已知实施缺口需在合理期限内解决。

[v7u_N002912|2912] When implementing new policies, organizations typically include a transition period, such as six months, to allow for:
ZH: 实施新政策时通常包含过渡期（如六个月），以便进行差距分析和业务风险评估等。

[v7u_N002913|2913] Gap analysis and business risk assessment.
ZH: 过渡期活动包括差距分析和业务风险评估。

[v7u_N002914|2914] System, procedural, and process updates
ZH: 过渡期活动包括系统、程序和流程更新。

[v7u_N002915|2915] Training and staff education.
ZH: 过渡期活动包括培训和员工教育。

[v7u_N002916|2916] By developing clear, enforceable, and adaptable AFC policies, financial institutions strengthen compliance, mitigate financial crime risks, and ensure operational resilience.
ZH: 制定清晰、可执行且适应性强的金融犯罪防控政策有助于加强合规、降低金融犯罪风险并确保运营韧性。
```

## S1 合并候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002904"
    ],
    "proposition": "机构应维护明确协议，以确定何时必须采用新政策，以及起草、批准和更新流程。",
    "source_quotes": [
      "Organizations should maintain a clearly defined protocol to identify when a new policy must be adopted, as well as the process for drafting, approving, and updating it."
    ],
    "relation_cues": [
      "should",
      "must",
      "as well as"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "需要采用新政策时"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "通过协议识别新政策采用时机，并执行起草、批准和更新流程",
      "outcomes_or_paths": [
        "新政策被采用或更新"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002904",
        "quote": "Organizations should maintain a clearly defined protocol to identify when a new policy must be adopted, as well as the process for drafting, approving, and updating it."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002905",
      "v7u_N002906"
    ],
    "proposition": "良好政策应包括定期审查安排（通常每年一次），并规定触发临时审查和更新的事件（如新产品或监管事件）。",
    "source_quotes": [
      "Good policies should include provisions for addressing any exceptions or exemptions and should clearly assign responsibilities to specific people or roles. They should also provide a schedule for reviewing the policy, typically on an annual basis, and stipulate events that would trigger an ad hoc review and update.",
      "Examples include the introduction of a new product or the occurrence of a relevant regulatory event."
    ],
    "relation_cues": [
      "should",
      "typically",
      "trigger",
      "examples include"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "政策需要定期审查或出现触发事件（新产品、监管事件）"
      ],
      "basis_or_condition": [
        "年度审查计划",
        "触发事件"
      ],
      "focal_handling_or_judgment": "对政策进行定期或临时审查，并视需要更新",
      "outcomes_or_paths": [
        "政策更新"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002905",
        "quote": "Good policies should include provisions for addressing any exceptions or exemptions and should clearly assign responsibilities to specific people or roles. They should also provide a schedule for reviewing the policy, typically on an annual basis, and stipulate events that would trigger an ad hoc review and update."
      },
      {
        "unit_id": "v7u_N002906",
        "quote": "Examples include the introduction of a new product or the occurrence of a relevant regulatory event."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002910"
    ],
    "proposition": "跨国机构必须使政策符合各国法律，同时维持全球金融犯罪防控原则，可能因此在部分司法管辖区实施更高标准。",
    "source_quotes": [
      "To ensure jurisdictional compliance, multinational organizations must align policies with country-specific laws, while maintaining global AFC principles. This may result in implementing higher standards in some jurisdictions to maintain global consistency."
    ],
    "relation_cues": [
      "must",
      "while",
      "may result in"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "跨国机构需要确保符合各司法管辖区法规"
      ],
      "basis_or_condition": [
        "各国法律",
        "全球金融犯罪防控原则"
      ],
      "focal_handling_or_judgment": "调整政策以符合当地法律，并维持全球原则",
      "outcomes_or_paths": [
        "可能在部分司法管辖区实施更高标准"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002910",
        "quote": "To ensure jurisdictional compliance, multinational organizations must align policies with country-specific laws, while maintaining global AFC principles. This may result in implementing higher standards in some jurisdictions to maintain global consistency."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002911"
    ],
    "proposition": "政策偏差必须记录、论证并经治理机构批准；在适当情况下可给予有时间限制的豁免。已知实施缺口需在合理期限内记录并解决。",
    "source_quotes": [
      "To govern exceptions and dispensations, deviations from policy must be documented, justified, and approved by governance bodies. Where appropriate, dispensation may be provided for a specific time. Any known gaps in implementing policies must be documented and addressed within a reasonable period."
    ],
    "relation_cues": [
      "must",
      "where appropriate",
      "may",
      "and"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "出现政策偏差或实施缺口"
      ],
      "basis_or_condition": [
        "治理机构要求"
      ],
      "focal_handling_or_judgment": "记录、论证并批准偏差，或记录并解决缺口",
      "outcomes_or_paths": [
        "偏差被批准或豁免",
        "缺口被记录并解决"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002911",
        "quote": "To govern exceptions and dispensations, deviations from policy must be documented, justified, and approved by governance bodies. Where appropriate, dispensation may be provided for a specific time. Any known gaps in implementing policies must be documented and addressed within a reasonable period."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002912",
      "v7u_N002913",
      "v7u_N002914",
      "v7u_N002915"
    ],
    "proposition": "实施新政策时通常包含过渡期（如六个月），以便进行差距分析、业务风险评估、系统/程序/流程更新以及培训。",
    "source_quotes": [
      "When implementing new policies, organizations typically include a transition period, such as six months, to allow for:",
      "Gap analysis and business risk assessment.",
      "System, procedural, and process updates",
      "Training and staff education."
    ],
    "relation_cues": [
      "When",
      "typically",
      "to allow for"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "实施新政策"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "包含过渡期（如六个月）以完成必要准备工作",
      "outcomes_or_paths": [
        "完成差距分析、业务风险评估",
        "系统/程序/流程更新",
        "培训和员工教育"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002912",
        "quote": "When implementing new policies, organizations typically include a transition period, such as six months, to allow for:"
      },
      {
        "unit_id": "v7u_N002913",
        "quote": "Gap analysis and business risk assessment."
      },
      {
        "unit_id": "v7u_N002914",
        "quote": "System, procedural, and process updates"
      },
      {
        "unit_id": "v7u_N002915",
        "quote": "Training and staff education."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_gap_ch41_s02_comprehensive_coverage",
    "unit_ids": [
      "v7u_N002901"
    ],
    "proposition": "政策应覆盖所有产品和服务，包括未来产品，以防止合规缺口。",
    "source_quotes": [
      "Policies ensure comprehensive coverage. They should cover all products and services, including future offerings, to prevent compliance gaps."
    ],
    "relation_cues": [
      "should",
      "to"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "防止合规缺口"
      ],
      "focal_handling_or_judgment": "确保政策覆盖所有产品和服务，包括未来产品",
      "outcomes_or_paths": [
        "合规缺口被防止"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002901",
        "quote": "Policies ensure comprehensive coverage. They should cover all products and services, including future offerings, to prevent compliance gaps."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_001"
      ],
      "gap_reason": "已有候选s1c_001只承接了政策协议流程，没有承接政策必须全面覆盖所有产品和服务（包括未来产品）以防止合规缺口这一要求。"
    }
  },
  {
    "candidate_id": "s1c_gap_ch41_s02_risk_based_customization",
    "unit_ids": [
      "v7u_N002902",
      "v7u_N002909"
    ],
    "proposition": "基于风险的方法要求政策必须根据机构风险敞口、客户概况、地理风险因素或客户、产品、交易风险进行定制。",
    "source_quotes": [
      "To follow a risk-based approach, policies must be tailored to institutional risk exposure, customer profiles, and geographic risk factors.",
      "Using a risk-based approach, organizations should customize policies based on customer, product, and transaction risks."
    ],
    "relation_cues": [
      "must",
      "should",
      "based on"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "遵循或采用基于风险的方法"
      ],
      "basis_or_condition": [
        "机构风险敞口、客户概况、地理因素、产品及交易风险"
      ],
      "focal_handling_or_judgment": "定制政策以反映风险因素",
      "outcomes_or_paths": [
        "政策与风险相匹配"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002902",
        "quote": "To follow a risk-based approach, policies must be tailored to institutional risk exposure, customer profiles, and geographic risk factors."
      },
      {
        "unit_id": "v7u_N002909",
        "quote": "Using a risk-based approach, organizations should customize policies based on customer, product, and transaction risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_003"
      ],
      "gap_reason": "已有候选s1c_003只承接了根据司法管辖区调整政策，没有承接基于风险因素（如机构风险敞口、客户、产品、交易风险）定制政策的要求。"
    }
  }
]
```
