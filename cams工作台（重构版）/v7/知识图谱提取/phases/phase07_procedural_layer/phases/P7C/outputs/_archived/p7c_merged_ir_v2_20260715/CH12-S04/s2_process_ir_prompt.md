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
- `label` 保留原文主体、动作、否定和情态，不写通用占位语。
- `evidence_unit_ids` 非空且只能引用当前 section。
- element 证据必须来自其 `source_candidate_ids` 覆盖 unit 的并集；不得发现 S1 未承接的新证据链。
- `modality` 只允许 `required/permitted/prohibited/risky/optional` 或 `null`。映射规则：`must/shall/required`→`required`，`may/permitted`→`permitted`，`must not/prohibited`→`prohibited`；`should/might/could`等无法无损映射时填 `null`，并在 label 中保留原词。
- **不得输出 `node_type`**——精确 schema 类型由后续 S3 阶段确定。当前阶段只负责语义角色。

### 9.3 relation

使用带角色名的端点字段。六种 kind：

| kind | 端点字段 | 关键约束 |
|---|---|---|
| `trigger` | `trigger_element_id → process_element_id` | 必填 `trigger_mode`（`event` 或 `condition`）；条件触发必须保留 condition |
| `sequence` | `before_element_id → after_element_id` | — |
| `reference` | `process_element_id → auxiliary_element_id` | reference 方向固定为 process→auxiliary |
| `produce` | `process_element_id → outcome_element_id` | 同义出口不得建 relation |
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
| `trigger` | context | action 或 decision | trigger_mode 按上文校验 |
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
- `source_quote` 如存在，必须能在该 relation 的 `evidence_unit_ids` 对应原文中定位。
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

section_id: `CH12-S04`

section_title: `Money laundering risks associated with insurance, securities, brokerage, and custodian services > Securities and brokerage risks`

section_text_with_unit_anchors:

```text
[v7u_N000912|912] According to FATF, securities providers can range from those that largely interact with retail investors, such as retail stockbrokers, wealth managers, and financial advisors, to those who serve institutional markets such as clearing members, prime brokers, and global custodians.
ZH: FATF指出证券服务商范围从零售投资者到机构市场。

[v7u_N000913|913] Providers offer various services including capital market research, portfolio management, and investment funds distribution.
ZH: 服务商提供资本市场研究、投资组合管理和投资基金分销等服务。

[v7u_N000914|914] The securities and brokerage sector serves direct customers and intermediaries that transact on behalf of their underlying customers.
ZH: 证券和经纪业服务于直接客户和代表其客户交易的中介。

[v7u_N000915|915] Transactions can encompass a wide range of financial instruments, including transferable securities, moneymarket instruments, investment funds, options, futures, swaps, forward rate agreements, and other derivative contracts.
ZH: 交易涵盖多种金融工具，包括可转让证券、货币市场工具、投资基金、期权、期货等。

[v7u_N000916|916] This sector is particularly vulnerable during the layering and integration stages of money laundering.
ZH: 证券业在洗钱的离析阶段和融合阶段尤其脆弱。

[v7u_N000917|917] FATF notes that the sector is unique in that it can be used not only to launder illicit funds but also to generate illicit funds within the industry itself through fraudulent activities.
ZH: FATF指出证券业既可洗钱也可通过欺诈产生非法资金。

[v7u_N000918|918] Characteristics such as high levels of interaction between securities providers and intermediaries such as investors and brokers, substantial transaction volumes, rapid execution speeds, and a degree of anonymity, all create opportunities for criminals to launder proceeds.
ZH: 高互动性、大交易量、快速执行和匿名性为洗钱创造机会。

[v7u_N000919|919] Complex financial products present a risk as they can obscure the source of funds and complicate transaction monitoring.
ZH: 复杂金融产品可能掩盖资金来源并复杂化交易监控。

[v7u_N000920|920] Offshore accounts provide anonymity, which can facilitate money laundering and enable criminals to exploit lax regulatory jurisdictions.
ZH: 离岸账户提供匿名性，便利洗钱并利用监管宽松的司法管辖区。

[v7u_N000921|921] High-risk customers, such as PEPs, and intermediaries require careful risk assessment. PEPs might be susceptible to corruption, while intermediaries might facilitate illicit transactions on behalf of customers.
ZH: 高风险客户如政治敏感人物和中介机构需要仔细的风险评估

[v7u_N000922|922] Additionally, the rise of electronic trading platforms emphasizes speed and high transaction volumes, making it challenging to monitor and apply mitigation controls.
ZH: 电子交易平台的高速度和高交易量增加了监控难度

[v7u_N000923|923] Continuous monitoring of trading activities can help identify unusual patterns or behaviors that might indicate money laundering. Robust transaction monitoring systems that flag suspicious transactions based on predefined criteria can help identify large or unusual trades, rapid trading patterns, highfrequency transactions and transactions involving high-risk jurisdictions.
ZH: 持续监控交易活动以识别异常模式，防范洗钱

[v7u_N000924|924] Conducting CDD helps ensure that the source of funds is legitimate, and that customers are correctly segmented according to their expected and historical trading patterns.
ZH: 客户尽职调查用于验证资金来源和客户细分

[v7u_N000925|925] Asset managers or asset management companies conduct investments and handle assets on behalf of their customers.
ZH: 资产管理公司代表客户进行投资和资产管理

[v7u_N000926|926] Asset managers are required to understand the money laundering risks of their business as they handle large volumes of capital across multiple jurisdictions, in diverse and evolving asset classes, often with anonymity in transactions, using complex financial products and third parties.
ZH: 资产管理公司有义务了解其业务中的洗钱风险

[v7u_N000927|927] Asset managers provide a variety of financial products and services, including:
ZH: 资产管理公司提供的金融产品和服务列表

[v7u_N000928|928] Exchange-traded funds (ETF): These are investment funds traded on stock exchanges, similar to individual stocks. They offer diversification and liquidity but can also obscure the identities of underlying investors.
ZH: 交易所交易基金（ETF）的定义及其洗钱风险

[v7u_N000929|929] Derivatives: These financial instruments, such as options and futures, derive their value from underlying assets. Their complexity and potential for leverage can be exploited for money laundering.
ZH: 衍生品（如期权和期货）的复杂性和杠杆可能被用于洗钱

[v7u_N000930|930] Hedge funds: These pooled investment funds employ various strategies to generate returns. Their often opaque structures and high minimum investment requirements can attract illicit actors.
ZH: 对冲基金的不透明结构和最低投资要求可能吸引非法行为者

[v7u_N000931|931] Private equity: This involves investing directly in private companies or buying out public companies. The lack of transparency in these transactions can pose money laundering challenges.
ZH: 私募股权交易缺乏透明度，带来洗钱挑战

[v7u_N000932|932] Commodity trading advice: Asset managers might provide guidance on trading physical commodities, which can be subject to manipulation and illicit activities.
ZH: 大宗商品交易建议可能被操纵和用于非法活动

[v7u_N000933|933] Real estate investments: Investing in real estate involves various stakeholders, including sellers, buyers, renters, property managers, and agents, all of whom should be thoroughly vetted to mitigate money laundering risks.
ZH: 房地产投资涉及多方利益相关者，需全面审查以降低洗钱风险

[v7u_N000934|934] Crowdfunding: As a relatively new form of asset management, crowdfunding platforms allow individuals to invest in projects or startups. These platforms can be misused for money laundering due to insufficient regulatory oversight and the anonymity they can provide to investors.
ZH: 众筹平台因监管不足和匿名性可能被滥用于洗钱

[v7u_N000935|935] The complexity and variability of these products and services make it increasingly difficult to detect money laundering.
ZH: 产品和服务的复杂性和多样性增加了洗钱检测难度

[v7u_N000936|936] Additionally, asset managers face a complex and evolving CDD process that requires knowledge of all parties involved in the transactions. Those parties include investment fund managers, portfolio managers, and alternative investment fund managers, such as those overseeing hedge funds and private equity.
ZH: 资产管理公司面临复杂的客户尽职调查，需了解所有交易方

[v7u_N000937|937] By adopting a risk-based approach that emphasizes strong CDD controls and continuous monitoring, they can meet regulatory requirements and demonstrate a genuine commitment to the sector’s integrity. This commitment also addresses emerging risks associated with new asset classes, such as cryptocurrencies and novel financial instruments, which might be more susceptible to exploitation by money launderers.
ZH: 基于风险的方法通过强化客户尽职调查和监控应对新兴资产类别的洗钱风险
```

## S1 合并候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000921"
    ],
    "proposition": "高风险客户（如政治敏感人物）和中介需要仔细的风险评估。",
    "source_quotes": [
      "High-risk customers, such as PEPs, and intermediaries require careful risk assessment."
    ],
    "relation_cues": [
      "require"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "高风险客户和中介"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "需要仔细风险评估",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000921",
        "quote": "High-risk customers, such as PEPs, and intermediaries require careful risk assessment."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000923"
    ],
    "proposition": "持续监控交易活动和稳健的交易监控系统可帮助识别异常模式，表明可能洗钱。",
    "source_quotes": [
      "Continuous monitoring of trading activities can help identify unusual patterns or behaviors that might indicate money laundering. Robust transaction monitoring systems that flag suspicious transactions based on predefined criteria can help identify large or unusual trades, rapid trading patterns, highfrequency transactions and transactions involving high-risk jurisdictions."
    ],
    "relation_cues": [
      "can help",
      "indicate",
      "flag",
      "identify"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "交易活动"
      ],
      "basis_or_condition": [
        "基于预定义标准"
      ],
      "focal_handling_or_judgment": "持续监控和稳健的监控系统",
      "outcomes_or_paths": [
        "识别异常模式或行为，表明可能洗钱",
        "识别大额、异常、快速、高频或高风险司法管辖区的交易"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000923",
        "quote": "Continuous monitoring of trading activities can help identify unusual patterns or behaviors that might indicate money laundering. Robust transaction monitoring systems that flag suspicious transactions based on predefined criteria can help identify large or unusual trades, rapid trading patterns, highfrequency transactions and transactions involving high-risk jurisdictions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000924"
    ],
    "proposition": "进行客户尽职调查有助于确保资金来源合法以及客户正确细分。",
    "source_quotes": [
      "Conducting CDD helps ensure that the source of funds is legitimate, and that customers are correctly segmented according to their expected and historical trading patterns."
    ],
    "relation_cues": [
      "helps ensure"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "客户"
      ],
      "basis_or_condition": [
        "根据预期和历史交易模式"
      ],
      "focal_handling_or_judgment": "进行客户尽职调查",
      "outcomes_or_paths": [
        "确保资金来源合法",
        "客户正确细分"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000924",
        "quote": "Conducting CDD helps ensure that the source of funds is legitimate, and that customers are correctly segmented according to their expected and historical trading patterns."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N000926"
    ],
    "proposition": "资产管理公司有义务了解其业务中的洗钱风险。",
    "source_quotes": [
      "Asset managers are required to understand the money laundering risks of their business as they handle large volumes of capital across multiple jurisdictions, in diverse and evolving asset classes, often with anonymity in transactions, using complex financial products and third parties."
    ],
    "relation_cues": [
      "are required to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "资产管理公司处理大量资本、跨司法管辖区、多样资产类别、匿名交易、复杂金融产品和第三方"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "有义务了解洗钱风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000926",
        "quote": "Asset managers are required to understand the money laundering risks of their business as they handle large volumes of capital across multiple jurisdictions, in diverse and evolving asset classes, often with anonymity in transactions, using complex financial products and third parties."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N000933"
    ],
    "proposition": "房地产投资中的各方应彻底审查以减轻洗钱风险。",
    "source_quotes": [
      "Investing in real estate involves various stakeholders, including sellers, buyers, renters, property managers, and agents, all of whom should be thoroughly vetted to mitigate money laundering risks."
    ],
    "relation_cues": [
      "should be"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "房地产投资"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "所有利益相关者应彻底审查",
      "outcomes_or_paths": [
        "减轻洗钱风险"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000933",
        "quote": "Investing in real estate involves various stakeholders, including sellers, buyers, renters, property managers, and agents, all of whom should be thoroughly vetted to mitigate money laundering risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N000937"
    ],
    "proposition": "采用风险为本的方法，强调强大的客户尽职调查控制和持续监控，可以满足监管要求，展现对行业诚信的承诺，并应对新兴资产类别的风险。",
    "source_quotes": [
      "By adopting a risk-based approach that emphasizes strong CDD controls and continuous monitoring, they can meet regulatory requirements and demonstrate a genuine commitment to the sector’s integrity. This commitment also addresses emerging risks associated with new asset classes, such as cryptocurrencies and novel financial instruments, which might be more susceptible to exploitation by money launderers."
    ],
    "relation_cues": [
      "can meet",
      "demonstrate",
      "addresses"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "采用风险为本方法"
      ],
      "basis_or_condition": [
        "强调强大的客户尽职调查控制和持续监控"
      ],
      "focal_handling_or_judgment": "满足监管要求并展现承诺",
      "outcomes_or_paths": [
        "满足监管要求",
        "展现对行业诚信的承诺",
        "应对新兴资产类别的风险"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000937",
        "quote": "By adopting a risk-based approach that emphasizes strong CDD controls and continuous monitoring, they can meet regulatory requirements and demonstrate a genuine commitment to the sector’s integrity. This commitment also addresses emerging risks associated with new asset classes, such as cryptocurrencies and novel financial instruments, which might be more susceptible to exploitation by money launderers."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
