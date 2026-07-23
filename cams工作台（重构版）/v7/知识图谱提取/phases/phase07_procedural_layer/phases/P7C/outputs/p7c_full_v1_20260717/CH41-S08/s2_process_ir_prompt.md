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

section_id: `CH41-S08`

section_title: `Governance and oversight > • United Kingdom:`

section_text_with_unit_anchors:

```text
[v7u_N002978|2978] REP-CRIM report: Describes criminal activities detected within the financial institution.
ZH: REP-CRIM报告描述金融机构内检测到的犯罪活动。

[v7u_N002979|2979] Annual MLRO’s report: Summarizes the organization’s AFC compliance activities, highlighting trends, risks, and mitigation measures.
ZH: 年度MLRO报告总结组织的金融犯罪防控合规活动，突出趋势、风险和缓解措施。

[v7u_N002980|2980] Regulatory reporting requirements include, but are not limited to:
ZH: 监管报告要求的列表引导。

[v7u_N002981|2981] Accuracy and completeness: Reports must contain detailed, verifiable data to prevent errors, regulatory scrutiny, and reporting breaches.
ZH: 可疑活动报告必须包含详细、可验证的数据，以防止错误、监管审查和报告违规。

[v7u_N002982|2982] Timeliness: Filing deadlines differ globally, and institutions must ensure swift and precise submission.
ZH: 全球提交截止日期不同，机构必须确保及时、准确地提交报告。

[v7u_N002983|2983] Confidentiality and anti-tipping off: Disclosure of SAR details is strictly prohibited to prevent interference with law enforcement investigations.
ZH: 严格禁止泄露可疑活动报告细节，以防止干扰执法调查。

[v7u_N002984|2984] By aligning regulatory reporting processes with jurisdictional requirements, institutions strengthen financial integrity, regulatory cooperation, and financial crime prevention efforts.
ZH: 使监管报告流程符合司法管辖区要求，可增强金融诚信、监管合作和金融犯罪预防。

[v7u_N002985|2985] Responding to regulator requests is a crucial element of an organization’s AFC compliance program, underscoring the need for transparency, collaboration, and accountability. Effective engagement with regulators helps to avoid penalties, while demonstrating a culture of compliance that fosters long-term trust and credibility. It is also a key part of the cooperative effort between regulators and industry to combat money laundering, terrorism financing, and other financial crimes.
ZH: 回应监管机构请求是金融犯罪防控合规计划的关键要素，有助于避免处罚并建立信任。

[v7u_N002986|2986] Regulators may conduct routine examinations or targeted investigations, assessing whether institutions adhere to local and global AFC mandates.
ZH: 监管机构可能进行常规检查或专项调查，评估机构是否遵守当地和全球金融犯罪防控规定。

[v7u_N002987|2987] In some cases, a monitorship may be imposed following serious compliance breaches, requiring the institution to correct shortcomings under strict regulatory supervision.
ZH: 严重合规违规后可能实施监管监督，要求机构在严格监管下纠正缺陷。

[v7u_N002988|2988] By cooperating fully and addressing identified gaps promptly, organizations reduce reputational and operational risks.
ZH: 机构应充分合作并及时解决已发现的差距，以降低声誉和运营风险。

[v7u_N002989|2989] Jurisdictions often grant regulators special provisions to obtain relevant records and information. For example, in the UK, Section 166 of the Financial Services and Markets Act 2000 allows regulators to demand data on customer files, transactions, or risk management processes.
ZH: 英国《2000年金融服务与市场法》第166条允许监管机构要求提供客户档案、交易或风险管理流程数据。

[v7u_N002990|2990] Organizations must maintain accurate records and structured governance to quickly comply with such requests and demonstrate robust AFC controls.
ZH: 机构必须维护准确记录和结构化治理，以快速响应监管请求并展示有效的金融犯罪防控控制。

[v7u_N002991|2991] Best practices for engaging with regulators include the following:
ZH: 与监管机构互动的最佳实践包括以下内容。

[v7u_N002992|2992] Preparedness and data integrity: Keep customer due diligence files, transaction logs, and audit trails up to date, facilitating timely and accurate submissions.
ZH: 保持客户尽职调查文件、交易日志和审计线索最新，以便及时准确提交。

[v7u_N002993|2993] Designated liaison: Centralize regulator interactions under a head of compliance or similar role, ensuring efficient and consistent communication.
ZH: 指定合规负责人等角色集中处理监管互动，确保沟通高效一致。

[v7u_N002994|2994] Timely and transparent responses: Provide complete information before deadlines, proactively disclosing potential delays or challenges to build regulatory trust.
ZH: 在截止日期前提供完整信息，主动披露潜在延迟或挑战，以建立监管信任。

[v7u_N002995|2995] Remediation and monitoring: Develop corrective action plans, report progress, and strengthen AFC frameworks to prevent repeat findings.
ZH: 制定纠正行动计划、报告进展并加强金融犯罪防控框架，防止问题再次发生。

[v7u_N002996|2996] By responding promptly to regulator requests, organizations reinforce AFC commitments, mitigate compliance risks, and maintain strong supervisory relationships that bolster financial integrity.
ZH: 及时回应监管请求可强化金融犯罪防控承诺，降低合规风险并维护良好的监管关系。
```

## S1 合并候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002986"
    ],
    "proposition": "监管机构可能进行常规检查或专项调查，评估机构是否遵守当地和全球金融犯罪防控规定。",
    "source_quotes": [
      "Regulators may conduct routine examinations or targeted investigations, assessing whether institutions adhere to local and global AFC mandates."
    ],
    "relation_cues": [
      "may",
      "assessing"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "监管机构进行常规检查或专项调查"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "评估机构是否遵守当地和全球金融犯罪防控规定",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002986",
        "quote": "Regulators may conduct routine examinations or targeted investigations, assessing whether institutions adhere to local and global AFC mandates."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002987"
    ],
    "proposition": "严重合规违规后可能实施监管监督，要求机构在严格监管下纠正缺陷。",
    "source_quotes": [
      "In some cases, a monitorship may be imposed following serious compliance breaches, requiring the institution to correct shortcomings under strict regulatory supervision."
    ],
    "relation_cues": [
      "following",
      "may",
      "requiring"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "严重合规违规"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "可能实施监管监督(monitorship)",
      "outcomes_or_paths": [
        "机构在严格监管下纠正缺陷"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002987",
        "quote": "In some cases, a monitorship may be imposed following serious compliance breaches, requiring the institution to correct shortcomings under strict regulatory supervision."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002988"
    ],
    "proposition": "机构充分合作并及时解决已发现的差距，以降低声誉和运营风险。",
    "source_quotes": [
      "By cooperating fully and addressing identified gaps promptly, organizations reduce reputational and operational risks."
    ],
    "relation_cues": [
      "by",
      "reduce"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "机构充分合作并及时解决已发现的差距"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "降低声誉和运营风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002988",
        "quote": "By cooperating fully and addressing identified gaps promptly, organizations reduce reputational and operational risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002989"
    ],
    "proposition": "英国《2000年金融服务与市场法》第166条允许监管机构要求提供客户档案、交易或风险管理流程数据。",
    "source_quotes": [
      "Jurisdictions often grant regulators special provisions to obtain relevant records and information. For example, in the UK, Section 166 of the Financial Services and Markets Act 2000 allows regulators to demand data on customer files, transactions, or risk management processes."
    ],
    "relation_cues": [
      "allows",
      "demand"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "监管机构需要获取相关记录和信息"
      ],
      "basis_or_condition": [
        "英国《2000年金融服务与市场法》第166条"
      ],
      "focal_handling_or_judgment": "监管机构要求提供客户档案、交易或风险管理流程数据",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002989",
        "quote": "Jurisdictions often grant regulators special provisions to obtain relevant records and information. For example, in the UK, Section 166 of the Financial Services and Markets Act 2000 allows regulators to demand data on customer files, transactions, or risk management processes."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002990"
    ],
    "proposition": "机构必须维护准确记录和结构化治理，以快速响应监管请求并展示有效的金融犯罪防控控制。",
    "source_quotes": [
      "Organizations must maintain accurate records and structured governance to quickly comply with such requests and demonstrate robust AFC controls."
    ],
    "relation_cues": [
      "must",
      "to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "监管请求"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "维护准确记录和结构化治理",
      "outcomes_or_paths": [
        "快速遵从请求",
        "展示有效的金融犯罪防控控制"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002990",
        "quote": "Organizations must maintain accurate records and structured governance to quickly comply with such requests and demonstrate robust AFC controls."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_gap_ch41_s08_report_accuracy",
    "unit_ids": [
      "v7u_N002981"
    ],
    "proposition": "报告必须包含详细、可验证的数据，以防止错误、监管审查和报告违规。",
    "source_quotes": [
      "Accuracy and completeness: Reports must contain detailed, verifiable data to prevent errors, regulatory scrutiny, and reporting breaches."
    ],
    "relation_cues": [
      "must",
      "to"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "准确性和完整性要求"
      ],
      "focal_handling_or_judgment": "确保报告包含详细、可验证的数据",
      "outcomes_or_paths": [
        "防止错误",
        "防止监管审查",
        "防止报告违规"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002981",
        "quote": "Accuracy and completeness: Reports must contain detailed, verifiable data to prevent errors, regulatory scrutiny, and reporting breaches."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_005"
      ],
      "gap_reason": "已有候选s1c_005承接了机构需维护准确记录以响应监管请求，但未承接报告本身必须包含详细可验证数据以防止错误、审查和违规这一具体标准。"
    }
  },
  {
    "candidate_id": "s1c_gap_ch41_s08_report_timeliness",
    "unit_ids": [
      "v7u_N002982"
    ],
    "proposition": "全球提交截止日期不同，机构必须确保及时、准确地提交报告。",
    "source_quotes": [
      "Timeliness: Filing deadlines differ globally, and institutions must ensure swift and precise submission."
    ],
    "relation_cues": [
      "and",
      "must"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "全球提交截止日期不同"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "机构必须确保及时、准确地提交报告",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002982",
        "quote": "Timeliness: Filing deadlines differ globally, and institutions must ensure swift and precise submission."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_005"
      ],
      "gap_reason": "已有候选s1c_005涉及响应请求的准备工作，但未承接报告提交时间限制下必须及时准确这一独立处置要求。"
    }
  },
  {
    "candidate_id": "s1c_gap_ch41_s08_report_confidentiality",
    "unit_ids": [
      "v7u_N002983"
    ],
    "proposition": "严格禁止披露可疑活动报告细节，以防止干扰执法调查。",
    "source_quotes": [
      "Confidentiality and anti-tipping off: Disclosure of SAR details is strictly prohibited to prevent interference with law enforcement investigations."
    ],
    "relation_cues": [
      "to"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "保密和反泄密原则"
      ],
      "focal_handling_or_judgment": "禁止披露SAR细节",
      "outcomes_or_paths": [
        "防止干扰执法调查"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002983",
        "quote": "Confidentiality and anti-tipping off: Disclosure of SAR details is strictly prohibited to prevent interference with law enforcement investigations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_005"
      ],
      "gap_reason": "已有候选s1c_005承接了记录维护要求，但未承接SAR保密性这一禁止性的独立合规要求。"
    }
  },
  {
    "candidate_id": "s1c_gap_ch41_s08_align_processes",
    "unit_ids": [
      "v7u_N002984"
    ],
    "proposition": "使监管报告流程符合司法管辖区要求，可增强金融诚信、监管合作和金融犯罪预防。",
    "source_quotes": [
      "By aligning regulatory reporting processes with jurisdictional requirements, institutions strengthen financial integrity, regulatory cooperation, and financial crime prevention efforts."
    ],
    "relation_cues": [
      "By"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "使监管报告流程符合司法管辖区要求",
      "outcomes_or_paths": [
        "增强金融诚信",
        "增强监管合作",
        "增强金融犯罪预防"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002984",
        "quote": "By aligning regulatory reporting processes with jurisdictional requirements, institutions strengthen financial integrity, regulatory cooperation, and financial crime prevention efforts."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_005"
      ],
      "gap_reason": "已有候选s1c_005侧重于维护记录以快速响应请求，未承接主动对齐报告流程与管辖要求所带来的增强效果这一独立处置链。"
    }
  },
  {
    "candidate_id": "s1c_gap_ch41_s08_data_integrity",
    "unit_ids": [
      "v7u_N002992"
    ],
    "proposition": "保持客户尽职调查文件、交易日志和审计线索最新，以便及时、准确地提交报告。",
    "source_quotes": [
      "Preparedness and data integrity: Keep customer due diligence files, transaction logs, and audit trails up to date, facilitating timely and accurate submissions."
    ],
    "relation_cues": [
      "Keep",
      "facilitating"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "准备和数据完整性要求"
      ],
      "focal_handling_or_judgment": "保持客户尽职调查文件、交易日志和审计线索最新",
      "outcomes_or_paths": [
        "便于及时、准确地提交"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002992",
        "quote": "Preparedness and data integrity: Keep customer due diligence files, transaction logs, and audit trails up to date, facilitating timely and accurate submissions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_005"
      ],
      "gap_reason": "已有候选s1c_005承接了维护记录和治理以响应请求，但未具体覆盖保持CDD文件、交易日志等最新以便于提交这一明确的最佳实践动作及其目的。"
    }
  },
  {
    "candidate_id": "s1c_gap_ch41_s08_designated_liaison",
    "unit_ids": [
      "v7u_N002993"
    ],
    "proposition": "将监管互动集中到合规负责人或类似角色，确保沟通高效、一致。",
    "source_quotes": [
      "Designated liaison: Centralize regulator interactions under a head of compliance or similar role, ensuring efficient and consistent communication."
    ],
    "relation_cues": [
      "ensuring"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "指定联络人要求"
      ],
      "focal_handling_or_judgment": "将监管互动集中到合规负责人或类似角色",
      "outcomes_or_paths": [
        "确保沟通高效、一致"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002993",
        "quote": "Designated liaison: Centralize regulator interactions under a head of compliance or similar role, ensuring efficient and consistent communication."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_005"
      ],
      "gap_reason": "已有候选s1c_005涉及响应请求的准备工作，但未承接指定专门联络人以保障沟通效率这一独立的最佳实践处置。"
    }
  },
  {
    "candidate_id": "s1c_gap_ch41_s08_timely_responses",
    "unit_ids": [
      "v7u_N002994"
    ],
    "proposition": "在截止日期前提供完整信息，并主动披露潜在延迟或挑战，以建立监管信任。",
    "source_quotes": [
      "Timely and transparent responses: Provide complete information before deadlines, proactively disclosing potential delays or challenges to build regulatory trust."
    ],
    "relation_cues": [
      "Provide",
      "to build"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "及时透明回应要求"
      ],
      "focal_handling_or_judgment": "在截止日期前提供完整信息，主动披露潜在延迟或挑战",
      "outcomes_or_paths": [
        "建立监管信任"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002994",
        "quote": "Timely and transparent responses: Provide complete information before deadlines, proactively disclosing potential delays or challenges to build regulatory trust."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_005"
      ],
      "gap_reason": "已有候选s1c_005承接了维护记录和治理，但未承接及时透明地提供信息并主动沟通以建立信任这一具体的最佳实践动作。"
    }
  },
  {
    "candidate_id": "s1c_gap_ch41_s08_remediation",
    "unit_ids": [
      "v7u_N002995"
    ],
    "proposition": "制定纠正行动计划，报告进展并加强金融犯罪防控框架，以防止问题再次发生。",
    "source_quotes": [
      "Remediation and monitoring: Develop corrective action plans, report progress, and strengthen AFC frameworks to prevent repeat findings."
    ],
    "relation_cues": [
      "to prevent"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "补救和监控要求"
      ],
      "focal_handling_or_judgment": "制定纠正行动计划，报告进展并加强金融犯罪防控框架",
      "outcomes_or_paths": [
        "防止问题再次发生"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002995",
        "quote": "Remediation and monitoring: Develop corrective action plans, report progress, and strengthen AFC frameworks to prevent repeat findings."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_005"
      ],
      "gap_reason": "已有候选s1c_005承接了维护记录以响应请求，但未承接在发现问题后主动制定补救计划并加强框架以防止重复发生这一独立处置链。"
    }
  },
  {
    "candidate_id": "s1c_gap_ch41_s08_prompt_response_benefits",
    "unit_ids": [
      "v7u_N002996"
    ],
    "proposition": "及时回应监管请求可以强化金融犯罪防控承诺、降低合规风险并维护良好的监管关系。",
    "source_quotes": [
      "By responding promptly to regulator requests, organizations reinforce AFC commitments, mitigate compliance risks, and maintain strong supervisory relationships that bolster financial integrity."
    ],
    "relation_cues": [
      "By"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "及时回应监管请求",
      "outcomes_or_paths": [
        "强化金融犯罪防控承诺",
        "降低合规风险",
        "维护良好的监管关系"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002996",
        "quote": "By responding promptly to regulator requests, organizations reinforce AFC commitments, mitigate compliance risks, and maintain strong supervisory relationships that bolster financial integrity."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_003"
      ],
      "gap_reason": "已有候选s1c_003承接了通过合作和解决差距来降低风险，但未承接及时回应本身直接带来的强化承诺、降低风险和维护关系的独立效果链。"
    }
  }
]
```
