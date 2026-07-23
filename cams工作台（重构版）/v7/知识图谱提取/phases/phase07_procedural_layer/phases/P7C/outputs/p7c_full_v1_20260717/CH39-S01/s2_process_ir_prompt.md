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

section_id: `CH39-S01`

section_title: `Customer risk assessment versus enterprise-wide risk assessment`

section_text_with_unit_anchors:

```text
[v7u_N002842|2842] The CRA evaluates potential ML/TF risks associated with individual customers and business relationships. In contrast, the EWRA analyzes ML/TF risks that the organization as a whole faces.
ZH: 客户风险评估（CRA）与全机构风险评估（EWRA）的范围区别

[v7u_N002843|2843] According to FinCEN’s Assessing Customer Relationships and Conducting Customer Due Diligence, customer relationships present varying levels of financial crime risks.
ZH: FinCEN指出客户关系存在不同程度的金融犯罪风险

[v7u_N002844|2844] Organizations conduct CRAs to identify risk factors, assign risk ratings to customers, create risk profiles, and decide which level of CDD to apply.
ZH: 客户风险评估（CRA）用于识别风险因素、分配评级并决定客户尽职调查等级

[v7u_N002845|2845] The CRA considers information collected through KYC processes, such as documents, customer business activity, and requested products.
ZH: CRA考虑通过了解你的客户流程收集的客户信息

[v7u_N002846|2846] Higher-risk customers might require EDD, while lower-risk customers might qualify for simplified due diligence (SDD) in some jurisdictions.
ZH: 高风险客户需强化尽职调查（EDD），低风险客户可适用简化尽职调查（SDD）

[v7u_N002847|2847] Due diligence requirements vary depending on the jurisdiction.
ZH: 尽职调查要求因司法管辖区而异

[v7u_N002848|2848] The EWRA identifies inherent risks, assesses controls, and determines the residual risk that the organization faces. The process helps organizations design their AML/CFT framework, guides policy and procedure development, allocates resources toward higher-risk areas, and improves decision-making.
ZH: 全机构风险评估（EWRA）识别固有风险、评估控制并确定剩余风险，指导反洗钱/反恐怖融资框架设计

[v7u_N002849|2849] A product risk assessment helps organizations identify and understand the risks and threats associated with their financial products. It assesses how criminals might use these products to launder illicit funds. After identifying and assessing these risks and threats, organizations can implement measures to mitigate them.
ZH: 产品风险评估帮助识别金融产品相关的洗钱风险并制定缓释措施

[v7u_N002850|2850] To identify and understand risks, organizations should consider factors, including:
ZH: 组织应考虑多种因素以识别和理解风险

[v7u_N002851|2851] Inherent product characteristics: Features or attributes such as crossborder wire payments, third-party payments, anonymity, remote access, third-party access, unusual complexity and structure, minimal transaction oversight, and cash-intensive nature.
ZH: 固有产品特征包括跨境支付、匿名性、远程访问等风险属性

[v7u_N002852|2852] Transactional patterns of the product: Recurring behaviors and trends such as rapid movements, high volumes, frequent transactions, involvement of high-risk or sanctioned jurisdictions, and use by high-risk customers in high-risk sectors.
ZH: 产品交易模式包括快速流动、高交易量、涉及高风险司法管辖区等风险指标

[v7u_N002853|2853] Each product should receive a risk score based on the AML/CFT risks it presents.
ZH: 每个产品应根据其反洗钱/反恐怖融资风险获得风险评分

[v7u_N002854|2854] A clear, documented definition of each product and its risks helps organizations assess them appropriately.
ZH: 清晰记录每个产品的定义和风险有助于适当评估

[v7u_N002855|2855] Identified risks affect the EWRA and the RAS.
ZH: 已识别的风险影响全机构风险评估（EWRA）和风险偏好声明（RAS）

[v7u_N002856|2856] For example, if many products are deemed high-risk, this raises the overall EWRA risk score, prompting additional controls or measures.
ZH: 若多个产品被认定为高风险，将提高EWRA评分并触发额外控制措施

[v7u_N002857|2857] If a product’s risk assessment score exceeds the RAS, the organization might cease offering it.
ZH: 若产品风险评估得分超过风险偏好，组织可能停止提供该产品

[v7u_N002858|2858] A product risk assessment is also very useful in designing controls such as transaction monitoring to ensure adequate coverage of all products.
ZH: 产品风险评估有助于设计交易监控等控制措施以确保充分覆盖

[v7u_N002859|2859] Although the product risk assessment process might vary, depending on the organization’s size, it typically includes:
ZH: 产品风险评估流程因组织规模而异，通常包括以下步骤

[v7u_N002860|2860] Product development: Designs the product and provides specifications.
ZH: 产品开发部门设计产品并提供规格说明

[v7u_N002861|2861] IT: Provides necessary technological infrastructure.
ZH: IT部门为风险评估提供必要的技术基础设施。

[v7u_N002862|2862] Operations: Provides insights about product usage patterns
ZH: 运营部门提供产品使用模式的洞察。

[v7u_N002863|2863] Compliance: Identifies control measures and ensures compliance.
ZH: 合规部门识别控制措施并确保合规。

[v7u_N002864|2864] Legal: Provides legal assistance on applicable laws.
ZH: 法律部门就适用法律提供法律协助。

[v7u_N002865|2865] Compliance officers play an active role in overseeing the product risk assessment. They identify risks, assess relevant controls, and assign appropriate risk scores.
ZH: 合规官在产品风险评估中发挥积极作用，识别风险、评估控制并分配风险评分。

[v7u_N002866|2866] Because risk assessment is an ongoing process, organizations should review both new and existing products regularly. For new products, the assessment should be conducted before they are offered to customers. Once the product becomes available, it should be reviewed periodically and whenever significant product changes occur.
ZH: 组织应定期审查新产品和现有产品，新产品在推出前应进行评估，之后定期审查并在重大变更时审查。

[v7u_N002867|2867] A clear and well-structured risk assessment helps identify vulnerabilities and exposures.
ZH: 清晰且结构良好的风险评估有助于识别漏洞和风险敞口。

[v7u_N002868|2868] Sometimes, organizations might notice previously unidentified risks for a new or existing product.
ZH: 组织可能注意到新产品或现有产品中先前未识别的风险。

[v7u_N002869|2869] For example, a new prepaid card might show high volumes of rapid transactions from high-risk customers.
ZH: 例如，新的预付卡可能显示来自高风险客户的高频交易。

[v7u_N002870|2870] This might require revisiting the product risk assessment and setting thresholds for the number of transactions, volumes, or restricting the product to certain customer sectors.
ZH: 可能需要重新审视产品风险评估并设定交易数量、金额阈值或限制产品面向特定客户群体。
```

## S1 合并候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002844",
      "v7u_N002845",
      "v7u_N002846"
    ],
    "proposition": "组织进行客户风险评估（CRA）以识别风险因素、分配风险评级并决定适用的客户尽职调查（CDD）等级：高风险客户可能需要强化尽职调查（EDD），低风险客户可能适用简化尽职调查（SDD）。",
    "source_quotes": [
      "Organizations conduct CRAs to identify risk factors, assign risk ratings to customers, create risk profiles, and decide which level of CDD to apply.",
      "The CRA considers information collected through KYC processes, such as documents, customer business activity, and requested products.",
      "Higher-risk customers might require EDD, while lower-risk customers might qualify for simplified due diligence (SDD) in some jurisdictions."
    ],
    "relation_cues": [
      "to",
      "decide",
      "might require",
      "might qualify"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "客户关系存在不同程度的金融犯罪风险"
      ],
      "basis_or_condition": [
        "通过KYC流程收集的信息"
      ],
      "focal_handling_or_judgment": "进行客户风险评估，识别风险因素并分配风险评级",
      "outcomes_or_paths": [
        "高风险客户需EDD",
        "低风险客户可适用SDD"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002844",
        "quote": "Organizations conduct CRAs to identify risk factors, assign risk ratings to customers, create risk profiles, and decide which level of CDD to apply."
      },
      {
        "unit_id": "v7u_N002845",
        "quote": "The CRA considers information collected through KYC processes, such as documents, customer business activity, and requested products."
      },
      {
        "unit_id": "v7u_N002846",
        "quote": "Higher-risk customers might require EDD, while lower-risk customers might qualify for simplified due diligence (SDD) in some jurisdictions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002848"
    ],
    "proposition": "全机构风险评估（EWRA）识别固有风险、评估控制并确定剩余风险，进而指导AML/CFT框架设计、政策程序开发、资源分配和改进决策。",
    "source_quotes": [
      "The EWRA identifies inherent risks, assesses controls, and determines the residual risk that the organization faces. The process helps organizations design their AML/CFT framework, guides policy and procedure development, allocates resources toward higher-risk areas, and improves decision-making."
    ],
    "relation_cues": [
      "identifies",
      "assesses",
      "determines",
      "helps",
      "guides",
      "allocates",
      "improves"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织面临固有风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "进行全机构风险评估，识别固有风险、评估控制并确定剩余风险",
      "outcomes_or_paths": [
        "设计AML/CFT框架",
        "指导政策程序开发",
        "向高风险领域分配资源",
        "改进决策"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002848",
        "quote": "The EWRA identifies inherent risks, assesses controls, and determines the residual risk that the organization faces. The process helps organizations design their AML/CFT framework, guides policy and procedure development, allocates resources toward higher-risk areas, and improves decision-making."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002849",
      "v7u_N002853",
      "v7u_N002854",
      "v7u_N002858",
      "v7u_N002865"
    ],
    "proposition": "产品风险评估识别和理解产品风险与威胁，对每个产品基于AML/CFT风险分配风险评分，合规官识别风险、评估控制并分配评分，并据此设计交易监控等控制措施。",
    "source_quotes": [
      "A product risk assessment helps organizations identify and understand the risks and threats associated with their financial products. It assesses how criminals might use these products to launder illicit funds. After identifying and assessing these risks and threats, organizations can implement measures to mitigate them.",
      "Each product should receive a risk score based on the AML/CFT risks it presents.",
      "A clear, documented definition of each product and its risks helps organizations assess them appropriately.",
      "A product risk assessment is also very useful in designing controls such as transaction monitoring to ensure adequate coverage of all products.",
      "Compliance officers play an active role in overseeing the product risk assessment. They identify risks, assess relevant controls, and assign appropriate risk scores."
    ],
    "relation_cues": [
      "helps",
      "should receive",
      "useful in designing",
      "assign"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融产品存在风险与威胁"
      ],
      "basis_or_condition": [
        "产品定义及风险文档"
      ],
      "focal_handling_or_judgment": "进行产品风险评估，识别风险、分配风险评分",
      "outcomes_or_paths": [
        "实施风险缓释措施",
        "设计交易监控等控制措施"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002849",
        "quote": "A product risk assessment helps organizations identify and understand the risks and threats associated with their financial products. It assesses how criminals might use these products to launder illicit funds. After identifying and assessing these risks and threats, organizations can implement measures to mitigate them."
      },
      {
        "unit_id": "v7u_N002853",
        "quote": "Each product should receive a risk score based on the AML/CFT risks it presents."
      },
      {
        "unit_id": "v7u_N002854",
        "quote": "A clear, documented definition of each product and its risks helps organizations assess them appropriately."
      },
      {
        "unit_id": "v7u_N002858",
        "quote": "A product risk assessment is also very useful in designing controls such as transaction monitoring to ensure adequate coverage of all products."
      },
      {
        "unit_id": "v7u_N002865",
        "quote": "Compliance officers play an active role in overseeing the product risk assessment. They identify risks, assess relevant controls, and assign appropriate risk scores."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002855",
      "v7u_N002856"
    ],
    "proposition": "产品风险评估中若许多产品被认定为高风险，则提高全机构风险评估（EWRA）评分，并触发额外控制措施。",
    "source_quotes": [
      "Identified risks affect the EWRA and the RAS.",
      "For example, if many products are deemed high-risk, this raises the overall EWRA risk score, prompting additional controls or measures."
    ],
    "relation_cues": [
      "affect",
      "if",
      "raises",
      "prompting"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "产品风险评估中多个产品被认定为高风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "多个产品高风险时提高EWRA风险评分",
      "outcomes_or_paths": [
        "触发额外控制或措施"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002855",
        "quote": "Identified risks affect the EWRA and the RAS."
      },
      {
        "unit_id": "v7u_N002856",
        "quote": "For example, if many products are deemed high-risk, this raises the overall EWRA risk score, prompting additional controls or measures."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002857"
    ],
    "proposition": "若产品风险评估得分超过风险偏好声明（RAS），组织可能停止提供该产品。",
    "source_quotes": [
      "If a product’s risk assessment score exceeds the RAS, the organization might cease offering it."
    ],
    "relation_cues": [
      "If",
      "exceeds",
      "might"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "产品风险评估得分超过RAS"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "判断产品是否因风险过高而需停止提供",
      "outcomes_or_paths": [
        "可能停止提供该产品"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002857",
        "quote": "If a product’s risk assessment score exceeds the RAS, the organization might cease offering it."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002866"
    ],
    "proposition": "组织应定期审查新产品和现有产品：新产品在推出前应进行评估，之后定期审查，并在发生重大产品变更时审查。",
    "source_quotes": [
      "Because risk assessment is an ongoing process, organizations should review both new and existing products regularly. For new products, the assessment should be conducted before they are offered to customers. Once the product becomes available, it should be reviewed periodically and whenever significant product changes occur."
    ],
    "relation_cues": [
      "should review",
      "should be conducted",
      "should be reviewed"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "新产品推出前或产品发生重大变更时"
      ],
      "basis_or_condition": [
        "风险评估是一个持续过程"
      ],
      "focal_handling_or_judgment": "对产品进行定期审查与评估",
      "outcomes_or_paths": [
        "新产品在推出前评估",
        "现有产品定期审查",
        "重大变更时审查"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002866",
        "quote": "Because risk assessment is an ongoing process, organizations should review both new and existing products regularly. For new products, the assessment should be conducted before they are offered to customers. Once the product becomes available, it should be reviewed periodically and whenever significant product changes occur."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N002868",
      "v7u_N002869",
      "v7u_N002870"
    ],
    "proposition": "若发现新产品或现有产品存在先前未识别的风险（如高风险客户的高频交易），可能需要重新审视产品风险评估并设定交易数量、金额阈值或限制产品面向特定客户群体。",
    "source_quotes": [
      "Sometimes, organizations might notice previously unidentified risks for a new or existing product.",
      "For example, a new prepaid card might show high volumes of rapid transactions from high-risk customers.",
      "This might require revisiting the product risk assessment and setting thresholds for the number of transactions, volumes, or restricting the product to certain customer sectors."
    ],
    "relation_cues": [
      "might notice",
      "might require",
      "revisiting",
      "setting"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "发现新产品或现有产品存在先前未识别的风险"
      ],
      "basis_or_condition": [
        "例如高风险客户的高频交易"
      ],
      "focal_handling_or_judgment": "重新审视产品风险评估并调整阈值或限制",
      "outcomes_or_paths": [
        "设定交易数量/金额阈值",
        "限制产品面向特定客户群体"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002868",
        "quote": "Sometimes, organizations might notice previously unidentified risks for a new or existing product."
      },
      {
        "unit_id": "v7u_N002869",
        "quote": "For example, a new prepaid card might show high volumes of rapid transactions from high-risk customers."
      },
      {
        "unit_id": "v7u_N002870",
        "quote": "This might require revisiting the product risk assessment and setting thresholds for the number of transactions, volumes, or restricting the product to certain customer sectors."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
