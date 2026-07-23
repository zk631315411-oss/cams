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

section_id: `CH11-S01`

section_title: `Money laundering risks associated with MSBs, payment service providers, and ecommerce > Payment service providers`

section_text_with_unit_anchors:

```text
[v7u_N000781|781] The payment industry and associated technologies are evolving rapidly, often outpacing the development of licensing frameworks and regulatory oversight. In this dynamic environment, many organizations leverage money services business (MSB) or e-money licenses to expand their operations and carve out a distinct role within the broader payments ecosystem.
ZH: 支付行业快速发展，企业利用货币服务企业或电子货币牌照拓展业务

[v7u_N000782|782] Payment service providers (PSP) play a central role, by enabling digital payments across various industries, offering products and services tailored to their business models and the types of transactions they process.
ZH: 支付服务提供商（PSP）在数字支付中发挥核心作用

[v7u_N000783|783] These services can include payment aggregation, card issuance, mobile wallets, and cross-border payment facilitation.
ZH: PSP服务包括支付聚合、卡片发行、移动钱包和跨境支付

[v7u_N000784|784] In some financial institutions, MSBs and PSPs are collectively referred to as “Third-Party Payment Processors” (TPPP), reflecting their shared function of handling transactions on behalf of other entities.
ZH: 货币服务企业和PSP统称为第三方支付处理商（TPPP）

[v7u_N000785|785] A typical PSP flow that facilitates the processing of a payment transaction between a customer and a merchant includes:
ZH: 典型PSP处理客户与商户间支付交易的流程

[v7u_N000786|786] 1. Verification: The PSP verifies the customer’s payment information with the issuing bank.
ZH: PSP验证客户支付信息与发卡行

[v7u_N000787|787] 2. Approval: The PSP communicates with the issuing bank to receive approval for the transaction.
ZH: PSP与发卡行沟通获取交易批准

[v7u_N000788|788] 3. Transfer: The PSP transfers funds from the customer’s account to the business’s account.
ZH: PSP将资金从客户账户转入商户账户

[v7u_N000789|789] Services include online payment gateways, mobile wallet solutions, and crossborder payment systems.
ZH: PSP服务包括在线支付网关、移动钱包和跨境支付系统

[v7u_N000790|790] A payment gateway is vital for processing payments because it facilitates the actual transfer of funds.
ZH: 支付网关是处理资金转移的关键

[v7u_N000791|791] As demand for digital solutions grows, PSPs are expected to expand product offerings, adapt to customer needs, and comply with changing regulations. This adaptability ensures they stay at the forefront of the payment landscape.
ZH: PSP需扩展产品、适应客户需求并遵守法规以保持领先

[v7u_N000792|792] Examples of PSPs and their offerings:
ZH: PSP及其产品示例列表

[v7u_N000793|793] Managing risks is essential for PSPs due to the complexity and diversity of their services, and because most transactions are conducted remotely.
ZH: 由于服务复杂多样且远程交易，PSP必须进行风险管理

[v7u_N000794|794] The risk landscape for PSPs varies based on their specific product offerings. However, key risks include:
ZH: PSP风险状况因产品而异，关键风险包括

[v7u_N000795|795] Fraud: The potential for deceptive practices that can lead to financial loss.
ZH: 欺诈：可能导致财务损失的欺骗行为

[v7u_N000796|796] Chargebacks: Disputes initiated by customers that can impact revenue.
ZH: 退单：客户发起的争议，影响收入

[v7u_N000797|797] Data breaches: Unauthorized access to sensitive customer information.
ZH: 数据泄露：未经授权访问敏感客户信息

[v7u_N000798|798] Regulatory noncompliance: Risks associated with failing to adhere to legal requirements.
ZH: 监管不合规：未遵守法律要求的风险

[v7u_N000799|799] Operational failures: Disruptions in service delivery that can affect business operations.
ZH: 运营故障：服务交付中断影响业务运营

[v7u_N000800|800] Financial losses: Overall impact on profitability due to various risk factors.
ZH: 财务损失：各种风险因素对盈利能力的整体影响

[v7u_N000801|801] For PSPs, customer risks are primarily indirect.
ZH: 支付服务商的客户风险主要是间接风险

[v7u_N000802|802] Although PSPs usually do not directly engage in the financial or transactional activities of their customers, they still bear the responsibility of ensuring that transactions and AFC program controls comply with regulations. This includes confirming that these transactions are secure and do not lead to financial crimes.
ZH: 支付服务商有责任确保交易合规与安全，防止金融犯罪

[v7u_N000803|803] In contrast, partnership risks are typically higher due to PSPs' operational reliance on banks, financial institutions, card networks, technology providers, and third-party service providers.
ZH: 支付服务商的合作风险通常更高，因其依赖银行、金融机构等合作伙伴

[v7u_N000804|804] It is important for PSPs to understand their partners’ AFC controls in order to mitigate the relevant risks.
ZH: 支付服务商必须了解合作伙伴的金融犯罪防控措施以降低风险

[v7u_N000805|805] One concern is regulatory compliance risk.
ZH: 监管合规风险是支付服务商面临的一个担忧

[v7u_N000806|806] PSPs must ensure that their partners adhere to regulations and data protection requirements, such as the EU’s Payment Services Directive for strong customer authentication.
ZH: 支付服务商必须确保合作伙伴遵守法规和数据保护要求

[v7u_N000807|807] Their noncompliance can lead to repercussions for PSPs because noncompliant partners might inadvertently facilitate money laundering by creating gaps in the controls to detect illicit activities.
ZH: 不合规的合作伙伴可能在控制措施中留下漏洞，无意中助长洗钱

[v7u_N000808|808] Operational risks also present challenges, as many PSPs depend on thirdparty providers for essential infrastructure, including cloud storage.
ZH: 支付服务商依赖第三方提供商提供云存储等关键基础设施，带来运营风险

[v7u_N000809|809] Service outages and issues, such as long response times or inadequate customer support, are red flags, as they might indicate lapses in the partner’s transaction monitoring and compliance efforts.
ZH: 服务中断、响应时间长或客服不足是合作伙伴合规松懈的红旗信号信号

[v7u_N000810|810] Cybersecurity and fraud risks are heightened when collaborating with various institutions.
ZH: 与不同机构合作时，网络安全和欺诈风险会升高

[v7u_N000811|811] Differences in cybersecurity standards can create integration gaps, and in the event of a breach, the PSP is often responsible for customer communication and damage control.
ZH: 网络安全标准差异造成融合阶段缺口，发生泄露时支付服务商常需负责客户沟通与损害控制

[v7u_N000812|812] A partner's failure to maintain robust cybersecurity measures can lead to unauthorized access to sensitive data, facilitating fraudulent activities and money laundering.
ZH: 合作伙伴网络安全措施不力可导致敏感数据被未授权访问，助长欺诈和洗钱
```

## S1 合并候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000801",
      "v7u_N000802"
    ],
    "proposition": "支付服务商的客户风险主要是间接风险；尽管支付服务商通常不直接参与客户的金融或交易活动，但他们仍有责任确保交易和反金融犯罪控制合规。",
    "source_quotes": [
      "For PSPs, customer risks are primarily indirect.",
      "Although PSPs usually do not directly engage in the financial or transactional activities of their customers, they still bear the responsibility of ensuring that transactions and AFC program controls comply with regulations."
    ],
    "relation_cues": [
      "primarily",
      "indirect",
      "Although",
      "still bear the responsibility"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "PSP通常不直接参与客户的金融或交易活动"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "PSP负有确保交易和反金融犯罪控制合规的责任",
      "outcomes_or_paths": [
        "确保交易安全，防止金融犯罪"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000801",
        "quote": "For PSPs, customer risks are primarily indirect."
      },
      {
        "unit_id": "v7u_N000802",
        "quote": "Although PSPs usually do not directly engage in the financial or transactional activities of their customers, they still bear the responsibility of ensuring that transactions and AFC program controls comply with regulations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000803",
      "v7u_N000804"
    ],
    "proposition": "支付服务商的合作风险通常更高，因依赖银行等合作伙伴；支付服务商必须了解合作伙伴的反金融犯罪控制以降低相关风险。",
    "source_quotes": [
      "In contrast, partnership risks are typically higher due to PSPs' operational reliance on banks, financial institutions, card networks, technology providers, and third-party service providers.",
      "It is important for PSPs to understand their partners’ AFC controls in order to mitigate the relevant risks."
    ],
    "relation_cues": [
      "In contrast",
      "typically higher",
      "due to",
      "it is important",
      "in order to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "PSP运营依赖银行、金融机构、卡网络、技术提供商和第三方服务商"
      ],
      "basis_or_condition": [
        "合作风险通常更高"
      ],
      "focal_handling_or_judgment": "PSP必须了解合作伙伴的反金融犯罪控制",
      "outcomes_or_paths": [
        "降低相关风险"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000803",
        "quote": "In contrast, partnership risks are typically higher due to PSPs' operational reliance on banks, financial institutions, card networks, technology providers, and third-party service providers."
      },
      {
        "unit_id": "v7u_N000804",
        "quote": "It is important for PSPs to understand their partners’ AFC controls in order to mitigate the relevant risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000805",
      "v7u_N000806"
    ],
    "proposition": "监管合规风险是支付服务商的担忧；支付服务商必须确保其合作伙伴遵守法规和数据保护要求，例如欧盟支付服务指令中的强客户认证。",
    "source_quotes": [
      "One concern is regulatory compliance risk.",
      "PSPs must ensure that their partners adhere to regulations and data protection requirements, such as the EU’s Payment Services Directive for strong customer authentication."
    ],
    "relation_cues": [
      "concern",
      "must ensure",
      "such as"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "监管合规风险"
      ],
      "basis_or_condition": [
        "欧盟支付服务指令等法规和数据保护要求"
      ],
      "focal_handling_or_judgment": "PSP必须确保合作伙伴遵守法规和数据保护要求",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000805",
        "quote": "One concern is regulatory compliance risk."
      },
      {
        "unit_id": "v7u_N000806",
        "quote": "PSPs must ensure that their partners adhere to regulations and data protection requirements, such as the EU’s Payment Services Directive for strong customer authentication."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N000809"
    ],
    "proposition": "服务中断、响应时间长或客服不足是红旗信号，可能表明合作伙伴的交易监控和合规工作存在疏漏。",
    "source_quotes": [
      "Service outages and issues, such as long response times or inadequate customer support, are red flags, as they might indicate lapses in the partner’s transaction monitoring and compliance efforts."
    ],
    "relation_cues": [
      "are red flags",
      "as",
      "might indicate"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "服务中断、响应时间长或客服不足"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "判断合作伙伴的交易监控和合规工作存在疏漏",
      "outcomes_or_paths": [
        "被识别为红旗信号"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000809",
        "quote": "Service outages and issues, such as long response times or inadequate customer support, are red flags, as they might indicate lapses in the partner’s transaction monitoring and compliance efforts."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N000810",
      "v7u_N000811"
    ],
    "proposition": "与不同机构合作时，网络安全和欺诈风险升高；发生泄露时，支付服务商通常负责客户沟通与损害控制。",
    "source_quotes": [
      "Cybersecurity and fraud risks are heightened when collaborating with various institutions.",
      "Differences in cybersecurity standards can create integration gaps, and in the event of a breach, the PSP is often responsible for customer communication and damage control."
    ],
    "relation_cues": [
      "heightened",
      "when",
      "in the event of",
      "often responsible"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "与不同机构合作",
        "发生泄露"
      ],
      "basis_or_condition": [
        "网络安全标准差异造成融合缺口"
      ],
      "focal_handling_or_judgment": "PSP负责客户沟通与损害控制",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000810",
        "quote": "Cybersecurity and fraud risks are heightened when collaborating with various institutions."
      },
      {
        "unit_id": "v7u_N000811",
        "quote": "Differences in cybersecurity standards can create integration gaps, and in the event of a breach, the PSP is often responsible for customer communication and damage control."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_gap_ch11_s01_partner_noncompliance_ml",
    "unit_ids": [
      "v7u_N000807"
    ],
    "proposition": "不合规的合作伙伴可能在控制措施中留下漏洞，无意中助长洗钱，给支付服务商带来后果。",
    "source_quotes": [
      "Their noncompliance can lead to repercussions for PSPs because noncompliant partners might inadvertently facilitate money laundering by creating gaps in the controls to detect illicit activities."
    ],
    "relation_cues": [
      "because",
      "might inadvertently",
      "creating gaps"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "合作伙伴不合规"
      ],
      "basis_or_condition": [
        "可能在检测非法活动的控制措施中留下漏洞"
      ],
      "focal_handling_or_judgment": "评估合作伙伴不合规可能助长洗钱并给支付服务商带来后果",
      "outcomes_or_paths": [
        "可能无意助长洗钱",
        "导致对支付服务商的后果"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000807",
        "quote": "Their noncompliance can lead to repercussions for PSPs because noncompliant partners might inadvertently facilitate money laundering by creating gaps in the controls to detect illicit activities."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_003"
      ],
      "gap_reason": "已有候选只承接了PSP必须确保合作伙伴遵守法规，没有承接合作伙伴不合规可能通过制造控制漏洞助长洗钱并给PSP带来后果这一风险判断链。"
    }
  },
  {
    "candidate_id": "s1c_gap_ch11_s01_partner_cyber_failure_ml",
    "unit_ids": [
      "v7u_N000812"
    ],
    "proposition": "合作伙伴未能维护稳健网络安全措施可能导致未授权访问敏感数据，助长欺诈和洗钱。",
    "source_quotes": [
      "A partner's failure to maintain robust cybersecurity measures can lead to unauthorized access to sensitive data, facilitating fraudulent activities and money laundering."
    ],
    "relation_cues": [
      "can lead to",
      "facilitating"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "合作伙伴未能维护稳健网络安全措施"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "评估合作伙伴网络安全失败可能导致的未授权访问和金融犯罪风险",
      "outcomes_or_paths": [
        "未授权访问敏感数据",
        "助长欺诈和洗钱"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000812",
        "quote": "A partner's failure to maintain robust cybersecurity measures can lead to unauthorized access to sensitive data, facilitating fraudulent activities and money laundering."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_005"
      ],
      "gap_reason": "已有候选只承接了网络安全风险升高时PSP负责沟通和损害控制，没有承接合作伙伴自身网络安全措施失败直接导致未授权访问并助长欺诈洗钱这一独立风险链。"
    }
  }
]
```
