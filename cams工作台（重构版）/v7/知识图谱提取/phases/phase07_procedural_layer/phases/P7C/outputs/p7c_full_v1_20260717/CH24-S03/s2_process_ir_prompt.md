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

section_id: `CH24-S03`

section_title: `US AML/CFT regulatory landscape > The Anti-Money Laundering Act of 2020`

section_text_with_unit_anchors:

```text
[v7u_N001710|1710] The main focus of the Anti-Money Laundering Act of 2020 (known as the AML Act in the US) was to modernize US banking laws and regulations for AML compliance.
ZH: 2020年《反洗钱法案》旨在现代化美国银行反洗钱合规法规

[v7u_N001711|1711] The act also broadens the use of AML practices to further national security and intelligence goals through greater transparency and enforcement measures.
ZH: 该法案通过提高透明度和执法措施，扩大反洗钱实践以促进国家安全和情报目标

[v7u_N001712|1712] This included the creation of a national Beneficial Ownership database, which will be updated with ownership information for entities required to register.
ZH: 创建国家受益所有人数据库，要求实体登记所有权信息

[v7u_N001713|1713] Additional rules, such as which financial institutions can access the database and how that information may be used, are anticipated in the future.
ZH: 预计未来将出台关于数据库访问权限和使用规则的补充规定

[v7u_N001714|1714] For example, the act expands AML compliance to include jurisdiction over activities in cryptocurrencies such as Bitcoin, as well as art and antique dealers.
ZH: 反洗钱合规范围扩大至加密货币及艺术品和古董经销商

[v7u_N001715|1715] The AML Act also includes new investigative powers regarding foreign financial institutions, while creating new criminal penalties for hiding transactions related to senior foreign political figures.
ZH: 新增针对外国金融机构的调查权，并对隐藏与外国高级政治人物相关交易的行为设定刑事处罚

[v7u_N001716|1716] The AML Act represents a strategic update to US banking law by including new financial technologies as well as national security priorities in AML compliance.
ZH: 《反洗钱法案》将新金融技术和国家安全优先事项纳入反洗钱合规，是美国银行法的战略更新

[v7u_N001717|1717] For example, the AML Act requires shell companies and other previously unregulated legal entities to disclose their beneficial owners and register ownership structures with FinCEN.
ZH: 要求壳公司等实体向FinCEN披露受益所有人并注册所有权结构

[v7u_N001718|1718] The act also extends protection for whistleblowers who alert authorities of AML regulatory violations.
ZH: 法案扩大对举报反洗钱违规行为的举报人保护

[v7u_N001719|1719] The goal is to broaden investigative powers to outline connections between entities like shell companies and their relationships with correspondent banks around the globe.
ZH: 目标是扩大调查权，以揭示壳公司等实体与全球代理行之间的关系

[v7u_N001720|1720] The AML Act also updates existing AML regulations to include cryptocurrency exchanges. They are considered to be money services businesses and have the same licensing and reporting requirements.
ZH: 法案将加密货币交易所视为货币服务企业，适用相同的许可和报告要求

[v7u_N001721|1721] Another goal of the AML Act is to transform SARs from a simple reporting requirement to a tool for intelligence gathering. SARs are now expected to provide a “high degree of usefulness” for law enforcement and national security agencies.
ZH: 《反洗钱法》将可疑交易报告转变为高价值情报工具

[v7u_N001722|1722] Additionally, there are provisions to facilitate cross-border sharing of SARs within financial institutions.
ZH: 《反洗钱法》允许金融机构内部跨境共享可疑交易报告

[v7u_N001723|1723] The AML Act also requires the development of further regulations to enhance strategic priorities regarding:
ZH: 《反洗钱法》要求制定进一步法规以强化战略优先事项

[v7u_N001724|1724] Corruption and fraud.
ZH: 战略优先事项包括腐败与欺诈

[v7u_N001725|1725] Cybercrime.
ZH: 战略优先事项包括网络犯罪

[v7u_N001726|1726] Terrorist financing.
ZH: 战略优先事项包括恐怖融资

[v7u_N001727|1727] Transnational criminal activity.
ZH: 战略优先事项包括跨国犯罪活动

[v7u_N001728|1728] Drug trafficking.
ZH: 战略优先事项包括毒品贩运

[v7u_N001729|1729] Human trafficking.
ZH: 战略优先事项包括人口贩运

[v7u_N001730|1730] Nuclear proliferation financing.
ZH: 战略优先事项包括核扩散融资

[v7u_N001731|1731] Pursuant to the AML Act, FinCEN has issued several notices of proposed rulemaking to further implement the AML Act. These include:
ZH: FinCEN 根据《反洗钱法》发布多项拟议规则制定通知

[v7u_N001732|1732] The requirement to maintain risk-based AML/CFT programs, such as mandatory risk assessment processes.
ZH: 要求维持基于风险的 反洗钱/反恐怖融资 计划，包括强制性风险评估流程

[v7u_N001733|1733] The incorporation of national priorities in institutions’ AML/CFT programs.
ZH: 要求将国家优先事项纳入机构的 反洗钱/反恐怖融资 计划

[v7u_N001734|1734] Additional rulemaking to further implement the AML Act and its legislative objectives will likely continue.
ZH: 《反洗钱法》的进一步规则制定可能会继续

[v7u_N001735|1735] The Financial Crimes Enforcement Network (FinCEN) is a bureau within the US Department of the Treasury. Its director reports to the Under Secretary for Terrorism and Financial Intelligence. FinCEN’s mission is to protect the financial system from illicit activities, combat financial crimes, and enhance national security.
ZH: FinCEN 是美国财政部下属机构，负责保护金融体系、打击金融犯罪并加强国家安全

[v7u_N001736|1736] The US Congress designates FinCEN as the central authority that collects, analyzes, and disseminates financial transaction data to support law enforcement, regulatory agencies, and policymakers.
ZH: 美国国会指定 FinCEN 为收集、分析和传播金融交易数据的中央权威机构

[v7u_N001737|1737] FinCEN’s analysis of data specifically plays a crucial role in combating AML and CFT as it assists in tracking fraud, tax evasion, narcotics trafficking, and terrorist financing.
ZH: FinCEN 的数据分析在打击洗钱和恐怖融资中发挥关键作用

[v7u_N001738|1738] FinCEN operates under the Bank Secrecy Act, which was amended by the USA PATRIOT Act.
ZH: FinCEN 依据《银行保密法》运作，该法经《爱国者法案》修订

[v7u_N001739|1739] The Bank Secrecy Act and its amendments grant FinCEN the authority to issue regulations, enforce compliance, and oversee AML programs in financial institutions.
ZH: 《银行保密法》授权 FinCEN 发布法规、执行合规并监督金融机构的反洗钱计划

[v7u_N001740|1740] For instance, FinCEN sets the standards for what constitutes suspicious activity and ensures that financial institutions properly file reports that could prove useful in criminal, tax, and counterterrorism investigations.
ZH: FinCEN 设定可疑活动标准并确保金融机构正确提交报告以支持调查

[v7u_N001741|1741] Additionally, FinCEN manages the collection, processing, storage, dissemination, and protection of Bank Secrecy Act data.
ZH: FinCEN 负责管理、保护《银行保密法》数据。

[v7u_N001742|1742] It partners with law enforcement in searching for information to investigate and prosecute entities involved in financial crime.
ZH: FinCEN 与执法部门合作，支持金融犯罪调查与起诉。

[v7u_N001743|1743] As the US FIU, FinCEN collaborates globally with over 100 FIUs within the Egmont Group, sharing financial intelligence to detect illicit financial flows. It also maintains a government-wide access service for financial crime data, helping federal, state, local, and international partners.
ZH: FinCEN 作为美国 FIU，与全球 100 多个 FIU 合作共享金融情报。

[v7u_N001744|1744] FinCEN’s key functions include:
ZH: FinCEN 的主要职能包括以下方面。

[v7u_N001745|1745] Issuing and enforcing AML/CFT regulations.
ZH: FinCEN 负责发布和执行 反洗钱/反恐怖融资 法规。

[v7u_N001746|1746] Supporting law enforcement in investigations and prosecutions.
ZH: FinCEN 支持执法部门的调查和起诉工作。

[v7u_N001747|1747] Managing and protecting Bank Secrecy Act data.
ZH: FinCEN 管理和保护《银行保密法》数据。

[v7u_N001748|1748] Coordinating with foreign FIUs on cross-border financial crime.
ZH: FinCEN 与外国 FIU 协调打击跨境金融犯罪。

[v7u_N001749|1749] Identifying financial crime risks and assisting with resource allocation.
ZH: FinCEN 识别金融犯罪风险并协助资源分配。

[v7u_N001750|1750] US financial regulators work collectively to ensure the financial system’s stability, integrity, and efficiency. The Office of the Comptroller of the Currency (OCC), Federal Reserve System (FRS), Federal Deposit Insurance Corporation (FDIC), and Securities and Exchange Commission (SEC) create a framework that safeguards financial institutions and consumers, mitigating risks that could threaten economic stability. They enforce compliance, promote transparency, and protect investors and depositors, while ensuring trust in financial markets.
ZH: 美国金融监管机构共同维护金融体系的稳定、完整和效率。

[v7u_N001751|1751] The OCC is an independent bureau within the US Department of the Treasury responsible for chartering, regulating, and supervising all national banks, federal savings associations, and US branches of foreign banks.
ZH: OCC 是财政部下属独立机构，负责全国性银行和联邦储蓄协会的监管。

[v7u_N001752|1752] It ensures that financial institutions operate safely and soundly, provide fair access to financial services, treat customers fairly, and comply with laws and regulations.
ZH: OCC 确保金融机构安全稳健运营、公平对待客户并遵守法律法规。

[v7u_N001753|1753] The FRS serves as the central bank of the US, working to ensure financial system stability by minimizing and containing systemic risks.
ZH: FRS 作为美国中央银行，致力于维护金融体系稳定。

[v7u_N001754|1754] It conducts several types of examinations to promote the safety and soundness of financial institutions while enhancing the efficiency and security of payment and settlement systems.
ZH: FRS 开展多种检查以促进金融机构安全稳健及支付结算系统效率。

[v7u_N001755|1755] Additionally, the FRS provides services to the banking industry and the US government, facilitating US dollar transactions and payments.
ZH: FRS 为银行业和美国政府提供美元交易和支付服务。

[v7u_N001756|1756] The FDIC is an independent agency established by Congress to uphold stability and public confidence in the US financial system. It fulfills this mission by insuring deposits, supervising financial institutions for safety, soundness, and consumer protection, and ensuring that financial institutions can be restructured or liquidated in an orderly manner if they fail.
ZH: FDIC 通过存款保险和监管维护金融体系稳定与公众信心。

[v7u_N001757|1757] The SEC oversees all aspects of the securities industry, ensuring investor protection, fair, orderly, and efficient markets, and capital formation.
ZH: SEC 监管证券行业，保护投资者并确保市场公平有序。

[v7u_N001758|1758] The president, with the Senate’s advice and consent, appoints up to five commissioners to lead the agency.
ZH: SEC 由总统任命并经参议院同意的最多五名委员领导。

[v7u_N001759|1759] By overseeing banking operations, managing systemic risks, insuring deposits, and regulating securities, these regulators collectively foster a resilient and well-functioning financial industry.
ZH: 各监管机构共同促进金融业的韧性和良好运作。

[v7u_N001760|1760] If a financial institution is found in violation of US laws and regulations related to financial crime, these regulators can impose civil monetary penalties, forfeiture of proceeds, limitations on future business activities, and criminal charges against the bank or its officers.
ZH: 金融机构违反金融犯罪法规时，监管机构可处以民事罚款、没收收益、限制业务或提起刑事指控。
```

## S1 合并候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001717"
    ],
    "proposition": "AML Act要求壳公司等实体向FinCEN披露受益所有人并注册所有权结构。",
    "source_quotes": [
      "For example, the AML Act requires shell companies and other previously unregulated legal entities to disclose their beneficial owners and register ownership structures with FinCEN."
    ],
    "relation_cues": [
      "requires",
      "disclose",
      "register"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "壳公司及其他未受监管的法律实体"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "向FinCEN披露受益所有人并注册所有权结构",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001717",
        "quote": "For example, the AML Act requires shell companies and other previously unregulated legal entities to disclose their beneficial owners and register ownership structures with FinCEN."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001720"
    ],
    "proposition": "AML Act将加密货币交易所视为货币服务企业，适用相同的许可和报告要求。",
    "source_quotes": [
      "The AML Act also updates existing AML regulations to include cryptocurrency exchanges. They are considered to be money services businesses and have the same licensing and reporting requirements."
    ],
    "relation_cues": [
      "considered",
      "same"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "加密货币交易所"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "视为货币服务企业，适用相同许可和报告要求",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001720",
        "quote": "The AML Act also updates existing AML regulations to include cryptocurrency exchanges. They are considered to be money services businesses and have the same licensing and reporting requirements."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001721"
    ],
    "proposition": "AML Act将可疑交易报告转变为情报工具，要求提供“高度有用性”。",
    "source_quotes": [
      "Another goal of the AML Act is to transform SARs from a simple reporting requirement to a tool for intelligence gathering. SARs are now expected to provide a “high degree of usefulness” for law enforcement and national security agencies."
    ],
    "relation_cues": [
      "transform",
      "expected"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "可疑交易报告（SARs）"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "转变为情报工具，要求提供高度有用性",
      "outcomes_or_paths": [
        "对执法和国家安全机构提供高度有用性"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001721",
        "quote": "Another goal of the AML Act is to transform SARs from a simple reporting requirement to a tool for intelligence gathering. SARs are now expected to provide a “high degree of usefulness” for law enforcement and national security agencies."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001722"
    ],
    "proposition": "AML Act允许金融机构内部跨境共享可疑交易报告。",
    "source_quotes": [
      "Additionally, there are provisions to facilitate cross-border sharing of SARs within financial institutions."
    ],
    "relation_cues": [
      "facilitate",
      "cross-border sharing"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构内部"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "跨境共享可疑交易报告",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001722",
        "quote": "Additionally, there are provisions to facilitate cross-border sharing of SARs within financial institutions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001731",
      "v7u_N001732"
    ],
    "proposition": "FinCEN根据AML Act发布拟议规则通知，要求金融机构维持基于风险的AML/CFT计划，包括强制性风险评估流程。",
    "source_quotes": [
      "Pursuant to the AML Act, FinCEN has issued several notices of proposed rulemaking to further implement the AML Act. These include:",
      "The requirement to maintain risk-based AML/CFT programs, such as mandatory risk assessment processes."
    ],
    "relation_cues": [
      "pursuant to",
      "requirement"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "AML Act"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FinCEN发布拟议规则通知，要求维持基于风险的AML/CFT计划及强制性风险评估",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001731",
        "quote": "Pursuant to the AML Act, FinCEN has issued several notices of proposed rulemaking to further implement the AML Act. These include:"
      },
      {
        "unit_id": "v7u_N001732",
        "quote": "The requirement to maintain risk-based AML/CFT programs, such as mandatory risk assessment processes."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N001740"
    ],
    "proposition": "FinCEN设定可疑活动标准并确保金融机构正确提交报告以支持调查。",
    "source_quotes": [
      "For instance, FinCEN sets the standards for what constitutes suspicious activity and ensures that financial institutions properly file reports that could prove useful in criminal, tax, and counterterrorism investigations."
    ],
    "relation_cues": [
      "sets",
      "ensures"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FinCEN设定可疑活动标准并确保金融机构正确提交报告",
      "outcomes_or_paths": [
        "报告可用于刑事、税务和反恐调查"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001740",
        "quote": "For instance, FinCEN sets the standards for what constitutes suspicious activity and ensures that financial institutions properly file reports that could prove useful in criminal, tax, and counterterrorism investigations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N001760"
    ],
    "proposition": "金融机构违反金融犯罪法规时，监管机构可处以民事罚款、没收收益、限制业务或提起刑事指控。",
    "source_quotes": [
      "If a financial institution is found in violation of US laws and regulations related to financial crime, these regulators can impose civil monetary penalties, forfeiture of proceeds, limitations on future business activities, and criminal charges against the bank or its officers."
    ],
    "relation_cues": [
      "if",
      "can impose"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构违反金融犯罪相关法律法规"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "监管机构施加处罚",
      "outcomes_or_paths": [
        "民事罚款",
        "没收收益",
        "限制未来业务活动",
        "对银行或高管提起刑事指控"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001760",
        "quote": "If a financial institution is found in violation of US laws and regulations related to financial crime, these regulators can impose civil monetary penalties, forfeiture of proceeds, limitations on future business activities, and criminal charges against the bank or its officers."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_gap_001",
    "unit_ids": [
      "v7u_N001715"
    ],
    "proposition": "AML Act 对隐藏与外国高级政治人物相关交易的行为设定新的刑事处罚。",
    "source_quotes": [
      "creating new criminal penalties for hiding transactions related to senior foreign political figures"
    ],
    "relation_cues": [
      "creating",
      "for"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "隐藏与外国高级政治人物相关的交易"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "设定新的刑事处罚",
      "outcomes_or_paths": [
        "面临刑事处罚"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001715",
        "quote": "creating new criminal penalties for hiding transactions related to senior foreign political figures"
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_007"
      ],
      "gap_reason": "已有候选只承接了金融机构违反金融犯罪法规时监管机构可处的民事罚款等处罚，未承接针对个人隐藏与外国高级政治人物相关交易的新刑事处罚这一独立刑事规定。"
    }
  },
  {
    "candidate_id": "s1c_gap_002",
    "unit_ids": [
      "v7u_N001718"
    ],
    "proposition": "AML Act 扩大对举报反洗钱违规行为的举报人的保护。",
    "source_quotes": [
      "extends protection for whistleblowers who alert authorities of AML regulatory violations"
    ],
    "relation_cues": [
      "extends",
      "who"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "举报人向当局举报反洗钱违规行为"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "扩大举报人保护",
      "outcomes_or_paths": [
        "提供保护"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001718",
        "quote": "extends protection for whistleblowers who alert authorities of AML regulatory violations"
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_006"
      ],
      "gap_reason": "已有候选承接了FinCEN对可疑活动标准和报告的要求，但未包含对举报反洗钱违规行为的举报人的保护扩大这一独立法定保护措施。"
    }
  },
  {
    "candidate_id": "s1c_gap_003",
    "unit_ids": [
      "v7u_N001731",
      "v7u_N001733"
    ],
    "proposition": "根据 AML Act，FinCEN 发布拟议规则要求机构将国家优先事项纳入其 AML/CFT 计划。",
    "source_quotes": [
      "Pursuant to the AML Act, FinCEN has issued several notices of proposed rulemaking to further implement the AML Act. These include:",
      "The incorporation of national priorities in institutions’ AML/CFT programs."
    ],
    "relation_cues": [
      "pursuant to",
      "incorporation"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "AML Act"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FinCEN 要求将国家优先事项纳入机构的 AML/CFT 计划",
      "outcomes_or_paths": [
        "机构的 AML/CFT 计划包含国家优先事项"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001731",
        "quote": "Pursuant to the AML Act, FinCEN has issued several notices of proposed rulemaking to further implement the AML Act. These include:"
      },
      {
        "unit_id": "v7u_N001733",
        "quote": "The incorporation of national priorities in institutions’ AML/CFT programs."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_005"
      ],
      "gap_reason": "已有候选承接了 FinCEN 拟议规则中关于风险为本计划和强制性风险评估的要求，但未包含将国家优先事项纳入机构 AML/CFT 计划这一独立要求。"
    }
  }
]
```
