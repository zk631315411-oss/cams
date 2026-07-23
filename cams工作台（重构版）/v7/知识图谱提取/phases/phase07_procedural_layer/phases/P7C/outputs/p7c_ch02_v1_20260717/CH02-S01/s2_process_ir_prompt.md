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
| `trigger` | `trigger_element_id → process_element_id` | 必填 `trigger_mode`（`event` 或 `condition`）；条件触发必须保留 condition |
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

section_id: `CH02-S01`

section_title: `Types of financial crime > Predicate crimes and money laundering`

section_text_with_unit_anchors:

```text
[v7u_N000060|60] Predicate crimes are specified unlawful activities whose proceeds can give rise to prosecution for money laundering.
ZH: 上游犯罪是指其收益可导致洗钱起诉的特定非法活动

[v7u_N000061|61] Individuals or organizations who engage in predicate crimes often want to "clean," or launder the proceeds from these crimes so they can use them legitimately without drawing attention from law enforcement.
ZH: 实施上游犯罪的个人或组织清洗犯罪收益以合法使用

[v7u_N000062|62] FATF has identified 21 categories of predicate offenses that financial institutions must acknowledge and monitor under AML compliance programs.
ZH: FATF 确定了金融机构必须关注的 21 类上游犯罪

[v7u_N000063|63] However, different jurisdictions might classify these offenses differently.
ZH: 不同司法管辖区对上游犯罪的分类存在差异

[v7u_N000064|64] For example, while some countries have strong laws against human trafficking, others do not recognize certain forms of exploitation as criminal offenses.
ZH: 举例：各国对人口贩卖的法律认定不同导致分类差异

[v7u_N000065|65] This variation can complicate AML efforts, with compliance professionals operating in cross-border contexts needing to align risk controls with the laws and regulations of more than one jurisdiction.
ZH: 跨境反洗钱合规需协调多个司法管辖区的法律差异

[v7u_N000066|66] The list of 21 FATF-designated predicate crimes includes:
ZH: FATF 指定的 21 类上游犯罪清单引述

[v7u_N000067|67] 1. Participation in an organized criminal group and racketeering: Engaging in systemic financial crimes
ZH: 参与有组织犯罪集团和敲诈勒索属于上游犯罪

[v7u_N000068|68] 2. Terrorism, including terrorist financing: Providing financial support to these operations
ZH: 恐怖主义及恐怖融资属于上游犯罪

[v7u_N000069|69] 3. Trafficking in human beings and migrant smuggling: Generating illicit profits through human exploitation
ZH: 人口贩卖和偷运移民属于上游犯罪

[v7u_N000070|70] 4. Sexual exploitation, including that of children: Crimes linked to forced prostitution and human trafficking
ZH: 性剥削（包括儿童性剥削）属于上游犯罪

[v7u_N000071|71] 5. Illicit trafficking in narcotic drugs and psychotropic substances: Production, transportation, and sale of illegal substances
ZH: 非法贩运麻醉药品和精神药物属于上游犯罪

[v7u_N000072|72] 6. Illicit arms trafficking: Illegal trade and smuggling of firearms and explosives
ZH: 非法武器贩运属于上游犯罪

[v7u_N000073|73] 7. Illicit trafficking of stolen and other goods: Black market trade of stolen and counterfeit items
ZH: 非法贩运被盗物品及其他货物属于上游犯罪

[v7u_N000074|74] 8. Corruption and bribery: Abuse of power in public or private sectors for financial gain
ZH: 腐败和贿赂属于上游犯罪

[v7u_N000075|75] 9. Fraud: Financial deception, scams, and identity theft schemes
ZH: 欺诈属于上游犯罪

[v7u_N000076|76] 10. Counterfeiting currency: Illegal manufacturing of banknotes
ZH: 伪造货币属于上游犯罪

[v7u_N000077|77] 11. Counterfeiting and piracy of products: Violations of intellectual property, including counterfeit goods
ZH: 假冒和盗版产品属于上游犯罪

[v7u_N000078|78] 12. Environmental crime: Logging, poaching, and waste disposal
ZH: 环境犯罪属于上游犯罪

[v7u_N000079|79] 13. Murder and grievous bodily injury: Violent crimes motivated by financial gain
ZH: 谋杀和严重身体伤害属于上游犯罪

[v7u_N000080|80] 14. Kidnapping, illegal restraint, and hostage-taking: Crimes involving ransom demands
ZH: 绑架、非法拘禁和劫持人质属于上游犯罪

[v7u_N000081|81] 15. Robbery or theft: Large-scale property crimes driven by financial motives
ZH: 抢劫或盗窃：出于财务动机的大规模财产犯罪

[v7u_N000082|82] 16. Smuggling (including in relation to customs and excise duties and taxes): Illegal movement of goods to evade duties
ZH: 走私（包括关税和消费税相关）：为逃避关税而非法移动货物

[v7u_N000083|83] 17. Tax crimes (related to direct and indirect taxes): Tax fraud and false reporting schemes
ZH: 税收犯罪（直接税和间接税）：税务欺诈和虚假申报计划

[v7u_N000084|84] 18. Extortion: Coercing for financial gain through threats or intimidation
ZH: 敲诈勒索：通过威胁或恐吓强迫获取经济利益

[v7u_N000085|85] 19. Forgery: Falsifying documents, financial records, or identities
ZH: 伪造：伪造文件、财务记录或身份信息

[v7u_N000086|86] 20.Piracy: Maritime or cyber-based hijacking for financial gain
ZH: 海盗行为：为获取经济利益而进行的海上或网络劫持

[v7u_N000087|87] 21. Insider trading and market manipulation: Illegal use of nonpublic information to achieve profits
ZH: 内幕交易和市场操纵：利用非公开信息非法获利

[v7u_N000088|88] Economic sanctions, whether asset freezes or sector-specific restrictions, impose high financial, reputational, and operational costs on individuals and entities targeted by them.
ZH: 制裁对目标个人和实体施加高额财务、声誉和运营成本

[v7u_N000089|89] For this reason, sanctions targets often attempt to evade or circumvent sanctions in order to secretly engage in a prohibited activity, such as continuing to use an asset or receive economic benefits.
ZH: 制裁目标常试图规避制裁以秘密从事被禁止的活动

[v7u_N000090|90] For example, a designated individual might evade personal sanctions and continue using his luxury yacht by obscuring its ownership.
ZH: 示例：被制裁个人通过隐藏豪华游艇所有权规避个人制裁

[v7u_N000091|91] Sanctions evasion can be internal, with the help of personnel at an organization, or external, when evaders try to bypass internal controls without assistance from the inside.
ZH: 制裁规避可分为内部规避（借助内部人员）和外部规避

[v7u_N000092|92] Methods of sanctions evasion include payments, trade, and ownership.
ZH: 制裁规避方法包括支付、贸易和所有权相关手段

[v7u_N000093|93] Payment-related evasion occurs when, for example, Bank A attempts to have Bank B process prohibited transactions, with or without help from Bank B insiders.
ZH: 支付相关规避：银行A试图让银行B处理被禁止交易

[v7u_N000094|94] Identifying information is removed, or stripped, from payment instructions to avoid detection.
ZH: 从支付指令中移除识别信息以逃避检测

[v7u_N000095|95] Nested and payable accounts are particularly vulnerable to this evasion typology.
ZH: 嵌套账户和应付账户特别容易受到支付信息剥离的规避手法影响

[v7u_N000096|96] Trade-related evasion involves illegally importing or exporting goods without proper licensing or despite trade bans.
ZH: 贸易相关规避：未经适当许可或违反贸易禁令非法进出口货物

[v7u_N000097|97] Common techniques include the use of shell companies, switching cargo on the open sea (also known as transshipment), and using neutral or opaque jurisdictions for transit.
ZH: 贸易规避常见手法：使用壳公司、公海换货（转运）、利用中立或保密司法管辖区

[v7u_N000098|98] Ownership-related evasion involves obscuring the ownership of an asset by a designated person. This can be achieved by using complex corporate structures, proxies, and bearer shares and by diluting ownership.
ZH: 所有权相关规避：通过复杂公司结构、代理人、不记名股票和稀释所有权隐藏资产所有权

[v7u_N000099|99] Regulated entities must have strong AML and sanctions compliance programs with robust policies, procedures, and internal controls for detecting and preventing sanctions evasion. The penalties for noncompliance and failing to prevent sanctions evasion could include:
ZH: 受监管实体必须建立强大的反洗钱和制裁合规计划，违规处罚包括：

[v7u_N000100|100] Civil monetary penalties against organizations
ZH: 对组织的民事罚款

[v7u_N000101|101] Civil and criminal prosecution of individuals
ZH: 个人可能面临洗钱相关民事和刑事起诉

[v7u_N000102|102] Designations as a sanctions target
ZH: 个人可能被列为制裁目标

[v7u_N000103|103] Businessman Alexei Komarov amassed his fortune through Volkof Industries, a high-tech distribution company with clients worldwide. Though some of his customers were from a wide range of industries (from consumer electronics and automotive to healthcare and industrial manufacturing), most sales went to a foreign government engaged in nuclear weapons development. After UN sanctions targeted this proliferation activity, Volkof Industries faced restrictions, losing its access to global markets.
ZH: Alexei Komarov通过Volkof Industries从事扩散融资的案例

[v7u_N000104|104] Facing financial collapse, Komarov was determined to find a way to continue trading.
ZH: Komarov面临财务崩溃，决心继续交易

[v7u_N000105|105] To evade the sanctions, he created a shell company, RedStar Solutions.
ZH: Komarov创建壳公司RedStar Solutions以规避制裁

[v7u_N000106|106] He incorporated it in a jurisdiction with limited regulatory expectations toward AML and sanctions compliance and masked it as a technical support and maintenance service provider.
ZH: 在监管宽松的司法管辖区注册壳公司并伪装成技术服务商

[v7u_N000107|107] Through RedStar, he resumed exports to the foreign government developing its nuclear weapons program, using transshipment points in permissive jurisdictions and falsified invoices that labeled export-controlled items, such as semiconductors, as “industrial machinery and spare parts.”
ZH: 通过转运点和伪造发票恢复出口受控物品

[v7u_N000108|108] RedStar also employed local distributors in those jurisdictions to further distance Komarov and Volkof Industries from the transactions and paid them to ensure the shipments were received without question.
ZH: 利用当地分销商进一步掩盖交易关联

[v7u_N000109|109] To launder the proceeds back to Volkof Industries, Komarov routed payments through offshore accounts and shell companies. He was thus able to credit Volkof Industries’ accounts using laundered funds from the illegal activities of RedStar.
ZH: 通过离岸账户和壳公司清洗非法收益的示例

[v7u_N000110|110] Komarov’s goal was not just to hide the profits of RedStar, but to keep Volkof Industries trading, as its name still carried weight in industry circles. Despite UN sanctions against Volkof Industries, this strategy helped the company meet loan obligations, retain employees, and strengthen business ties to the foreign government, its main client.
ZH: Komarov的双重目标：隐藏利润并维持Volkof Industries运营

[v7u_N000111|111] The scheme unraveled when a bank’s compliance officer flagged irregular payment flows linked to RedStar. Further investigation exposed the illicit network, revealing Komarov and Volkof Industries’ role in sanctions evasion, proliferation financing, laundering criminal proceeds, and foreign bribery and corruption offences.
ZH: 合规官发现异常支付，揭露制裁规避、扩散融资、洗钱等犯罪
```

## S1 合并候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000062"
    ],
    "proposition": "金融机构必须承认并监控FATF确定的21类上游犯罪。",
    "source_quotes": [
      "FATF has identified 21 categories of predicate offenses that financial institutions must acknowledge and monitor under AML compliance programs."
    ],
    "relation_cues": [
      "must",
      "acknowledge and monitor"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构的AML合规项目"
      ],
      "basis_or_condition": [
        "FATF确定的21类上游犯罪"
      ],
      "focal_handling_or_judgment": "承认并监控这些犯罪类别",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000062",
        "quote": "FATF has identified 21 categories of predicate offenses that financial institutions must acknowledge and monitor under AML compliance programs."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000099",
      "v7u_N000100",
      "v7u_N000101",
      "v7u_N000102"
    ],
    "proposition": "受监管实体必须建立强大的反洗钱和制裁合规计划，否则可能面临民事罚款、个人刑事起诉以及被列为制裁目标等处罚。",
    "source_quotes": [
      "Regulated entities must have strong AML and sanctions compliance programs with robust policies, procedures, and internal controls for detecting and preventing sanctions evasion. The penalties for noncompliance and failing to prevent sanctions evasion could include:",
      "Civil monetary penalties against organizations",
      "Civil and criminal prosecution of individuals",
      "Designations as a sanctions target"
    ],
    "relation_cues": [
      "must",
      "penalties",
      "noncompliance"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "存在制裁规避风险或需要检测和预防制裁规避"
      ],
      "basis_or_condition": [
        "未能遵守规定或未能预防制裁规避"
      ],
      "focal_handling_or_judgment": "建立强大的反洗钱和制裁合规计划",
      "outcomes_or_paths": [
        "民事罚款",
        "个人民事和刑事起诉",
        "被列为制裁目标"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000099",
        "quote": "Regulated entities must have strong AML and sanctions compliance programs with robust policies, procedures, and internal controls for detecting and preventing sanctions evasion. The penalties for noncompliance and failing to prevent sanctions evasion could include:"
      },
      {
        "unit_id": "v7u_N000100",
        "quote": "Civil monetary penalties against organizations"
      },
      {
        "unit_id": "v7u_N000101",
        "quote": "Civil and criminal prosecution of individuals"
      },
      {
        "unit_id": "v7u_N000102",
        "quote": "Designations as a sanctions target"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000103",
      "v7u_N000104",
      "v7u_N000105",
      "v7u_N000106",
      "v7u_N000107",
      "v7u_N000108",
      "v7u_N000109",
      "v7u_N000110",
      "v7u_N000111"
    ],
    "proposition": "银行的合规官通过标记异常支付流并进一步调查，揭露了Komarov和Volkof Industries在制裁规避、扩散融资、洗钱及贿赂等犯罪中的角色。",
    "source_quotes": [
      "After UN sanctions targeted this proliferation activity, Volkof Industries faced restrictions, losing its access to global markets.",
      "Facing financial collapse, Komarov was determined to find a way to continue trading.",
      "To evade the sanctions, he created a shell company, RedStar Solutions.",
      "He incorporated it in a jurisdiction with limited regulatory expectations toward AML and sanctions compliance and masked it as a technical support and maintenance service provider.",
      "Through RedStar, he resumed exports to the foreign government developing its nuclear weapons program, using transshipment points in permissive jurisdictions and falsified invoices that labeled export-controlled items, such as semiconductors, as “industrial machinery and spare parts.”",
      "RedStar also employed local distributors in those jurisdictions to further distance Komarov and Volkof Industries from the transactions and paid them to ensure the shipments were received without question.",
      "To launder the proceeds back to Volkof Industries, Komarov routed payments through offshore accounts and shell companies. He was thus able to credit Volkof Industries’ accounts using laundered funds from the illegal activities of RedStar.",
      "Komarov’s goal was not just to hide the profits of RedStar, but to keep Volkof Industries trading, as its name still carried weight in industry circles. Despite UN sanctions against Volkof Industries, this strategy helped the company meet loan obligations, retain employees, and strengthen business ties to the foreign government, its main client.",
      "The scheme unraveled when a bank’s compliance officer flagged irregular payment flows linked to RedStar. Further investigation exposed the illicit network, revealing Komarov and Volkof Industries’ role in sanctions evasion, proliferation financing, laundering criminal proceeds, and foreign bribery and corruption offences."
    ],
    "relation_cues": [
      "flagged",
      "further investigation",
      "exposed",
      "unraveled"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "联合国制裁针对扩散活动，Volkof Industries面临限制",
        "Komarov创建壳公司并采取各种手段规避制裁并洗钱"
      ],
      "basis_or_condition": [
        "合规官标记了与RedStar相关的异常支付流"
      ],
      "focal_handling_or_judgment": "银行合规官进行调查揭露了非法网络",
      "outcomes_or_paths": [
        "揭露了Komarov和Volkof Industries在制裁规避、扩散融资、洗钱和贿赂中的角色"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000103",
        "quote": "After UN sanctions targeted this proliferation activity, Volkof Industries faced restrictions, losing its access to global markets."
      },
      {
        "unit_id": "v7u_N000104",
        "quote": "Facing financial collapse, Komarov was determined to find a way to continue trading."
      },
      {
        "unit_id": "v7u_N000105",
        "quote": "To evade the sanctions, he created a shell company, RedStar Solutions."
      },
      {
        "unit_id": "v7u_N000106",
        "quote": "He incorporated it in a jurisdiction with limited regulatory expectations toward AML and sanctions compliance and masked it as a technical support and maintenance service provider."
      },
      {
        "unit_id": "v7u_N000107",
        "quote": "Through RedStar, he resumed exports to the foreign government developing its nuclear weapons program, using transshipment points in permissive jurisdictions and falsified invoices that labeled export-controlled items, such as semiconductors, as “industrial machinery and spare parts.”"
      },
      {
        "unit_id": "v7u_N000108",
        "quote": "RedStar also employed local distributors in those jurisdictions to further distance Komarov and Volkof Industries from the transactions and paid them to ensure the shipments were received without question."
      },
      {
        "unit_id": "v7u_N000109",
        "quote": "To launder the proceeds back to Volkof Industries, Komarov routed payments through offshore accounts and shell companies. He was thus able to credit Volkof Industries’ accounts using laundered funds from the illegal activities of RedStar."
      },
      {
        "unit_id": "v7u_N000110",
        "quote": "Komarov’s goal was not just to hide the profits of RedStar, but to keep Volkof Industries trading, as its name still carried weight in industry circles. Despite UN sanctions against Volkof Industries, this strategy helped the company meet loan obligations, retain employees, and strengthen business ties to the foreign government, its main client."
      },
      {
        "unit_id": "v7u_N000111",
        "quote": "The scheme unraveled when a bank’s compliance officer flagged irregular payment flows linked to RedStar. Further investigation exposed the illicit network, revealing Komarov and Volkof Industries’ role in sanctions evasion, proliferation financing, laundering criminal proceeds, and foreign bribery and corruption offences."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_gap_ch02_s01_crossborder_risk_control",
    "unit_ids": [
      "v7u_N000065"
    ],
    "proposition": "由于各司法管辖区对上游犯罪的分类差异可能复杂化反洗钱工作，跨境合规专业人士需要将风险控制与多个司法管辖区的法律法规相协调。",
    "source_quotes": [
      "This variation can complicate AML efforts, with compliance professionals operating in cross-border contexts needing to align risk controls with the laws and regulations of more than one jurisdiction."
    ],
    "relation_cues": [
      "with",
      "needing",
      "complicate"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "各司法管辖区对上游犯罪的分类差异可能复杂化反洗钱工作"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "跨境合规专业人士需要将风险控制与多个司法管辖区的法律法规相协调",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000065",
        "quote": "This variation can complicate AML efforts, with compliance professionals operating in cross-border contexts needing to align risk controls with the laws and regulations of more than one jurisdiction."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_001"
      ],
      "gap_reason": "已有候选 s1c_001 只要求金融机构承认并监控FATF 21类上游犯罪，但没有涉及因司法管辖区分类差异导致反洗钱工作复杂化时，跨境合规专业人士需要协调多个司法管辖区法律法规以调整风险控制的独立处理要求。"
    }
  }
]
```
