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

section_id: `CH19-S01`

section_title: `Financial Action Task Force > Financial Action Task Force`

section_text_with_unit_anchors:

```text
[v7u_N001303|1303] The G-7 established the Financial Action Task Force (FATF) in 1989 as an international organization to coordinate efforts to combat money laundering.
ZH: FATF于1989年由G7成立，旨在协调打击洗钱

[v7u_N001304|1304] Its original membership included 15 countries and the EU, and it now includes nearly 40 countries as well as a global network of regional groups.
ZH: FATF初始成员包括15国和欧盟，现扩展至近40国及区域网络

[v7u_N001305|1305] Within a year of its founding, FATF issued its original 40 Recommendations setting forth guidance and a comprehensive action plan for fighting money laundering worldwide.
ZH: FATF成立一年内发布40项建议，指导全球反洗钱行动

[v7u_N001306|1306] In the wake of the September 11 terrorist attacks in the US, FATF issued eight Special Recommendations on terrorist financing to supplement the original Recommendations. FATF eventually added a ninth Special Recommendation.
ZH: 9/11后FATF发布关于恐怖融资的八项特别建议，后增至九项

[v7u_N001307|1307] In addition to setting standards through FATF Recommendations, FATF accomplishes its work through:
ZH: FATF除制定标准外，还通过其他方式开展工作

[v7u_N001308|1308] Assessing implementation: FATF conducts periodic formal evaluations and other assessments to determine whether jurisdictions have fully and effectively implemented its standards. If FATF identifies deficiencies, it implements and monitors action plans and publicly reports progress.
ZH: FATF通过定期评估监督各辖区标准实施情况

[v7u_N001309|1309] Monitoring methods and trends: FATF continuously monitors how criminals and terrorists raise, use, and move funds, and publishes reports to raise awareness of the latest techniques and trends. Over 200 countries and jurisdictions have committed to meeting FATF standards, including many that are not full members of the organization.
ZH: FATF持续监控犯罪和恐怖融资手法与趋势，200多辖区承诺遵守标准

[v7u_N001310|1310] Identifying high-risk jurisdictions: Where FATF has determined that a jurisdiction has failed to implement its standards, FATF can designate it as a jurisdiction under increased monitoring on the "grey list" or a high-risk jurisdiction on the "black list." FATF designations on the grey and black lists can have severe consequences since inclusion on these lists might lead to isolation from the global financial system.
ZH: FATF将未达标辖区列入灰名单或黑名单，可能导致金融孤立

[v7u_N001311|1311] FATF-style regional bodies (FSRB) are autonomous regional organizations that assist in implementing FATF’s standards. These bodies closely align with FATF objectives and have similar forms and functions but operate independently of FATF. FSRBs are also considered FATF associate members.
ZH: FATF式区域机构（FSRB）是协助实施FATF标准的自治区域组织

[v7u_N001312|1312] In setting standards, FATF depends on input from the FSRBs. However, FATF remains the only standard-setting body.
ZH: FATF依赖FSRB提供意见，但仍是唯一标准制定机构

[v7u_N001313|1313] FSRBs ensure global AML/CFT efforts remain effective by identifying and addressing threats to the financial system, facilitating regional cooperation, assisting with mutual evaluations, and providing technical assistance to their members.
ZH: FSRB通过识别威胁、促进合作、评估和技术援助确保全球反洗钱/反恐怖融资有效性

[v7u_N001314|1314] Each FSRB adopts and implements FATF’s 40 Recommendations against money laundering and terrorist financing.
ZH: 每个FSRB采纳并实施FATF的40项反洗钱和反恐怖融资建议

[v7u_N001315|1315] The FSRBs work with their respective members to identify regional issues, share their experiences, and develop solutions.
ZH: FSRB与成员合作识别区域问题、分享经验并制定解决方案

[v7u_N001316|1316] Note that the number of members belonging to each FSRB might vary based on political decisions and alliances.
ZH: 各FSRB成员数量因政治决策和联盟而异

[v7u_N001317|1317] Each FSRB has slightly different objectives. However, a common objective is to ensure member compliance with relevant international AML/CFT standards. To meet their objectives, FSRB's functions can include:
ZH: FSRB的共同目标是确保成员遵守国际反洗钱/反恐怖融资标准，其职能包括

[v7u_N001318|1318] Evaluating AML/CFT measures by conducting assessments and issuing recommendations.
ZH: FSRB通过评估和建议评价反洗钱/反恐怖融资措施

[v7u_N001319|1319] Strategizing priorities such as improving financial sector supervision, enhancing private sector compliance, and increasing effectiveness in convictions and asset confiscations.
ZH: FSRB制定优先事项，如改善金融监管、加强私营部门合规及提高定罪和资产没收效率

[v7u_N001320|1320] Publishing reports identifying AML/CFT typologies impacting FATF members.
ZH: FSRB发布报告识别影响FATF成员的反洗钱/反恐怖融资类型学

[v7u_N001321|1321] Collaborating with global institutions to strengthen AML/CFT frameworks.
ZH: 与全球机构合作加强反洗钱/反恐怖融资框架

[v7u_N001322|1322] The FATF Recommendations are among the most important resources that FATF uses to provide guidance and coordination in the fight against financial crime.
ZH: FATF建议是打击金融犯罪的关键指导资源

[v7u_N001323|1323] FATF expects its members to implement the Recommendations in their respective jurisdictions and assesses them on the extent of implementation and the effectiveness of their programs.
ZH: FATF要求成员国实施建议并接受评估

[v7u_N001324|1324] FATF also offers guidance and best practices to jurisdictions on how they should implement the Recommendations.
ZH: FATF提供实施建议的指导和最佳实践

[v7u_N001325|1325] The 40 Recommendations and 9 Special Recommendations address a wide range of topics, from high-level guidance to issues concerning specific sectors and topics. FATF groups the Recommendations into seven broad categories:
ZH: 40+9项建议涵盖广泛主题，FATF将其分为七大类

[v7u_N001326|1326] AML/CFT policies and coordination
ZH: 反洗钱/反恐怖融资政策与协调

[v7u_N001327|1327] Money laundering and confiscation
ZH: 洗钱与没收

[v7u_N001328|1328] Terrorist financing and financing of proliferation
ZH: 恐怖融资与扩散融资

[v7u_N001329|1329] Preventive measures
ZH: 预防措施

[v7u_N001330|1330] Transparency and beneficial ownership
ZH: 透明度与受益所有人

[v7u_N001331|1331] Powers and responsibilities of competent authorities and other institutional measures
ZH: 主管当局的权力与职责及其他制度措施

[v7u_N001332|1332] International cooperation
ZH: 国际合作

[v7u_N001333|1333] FATF intends for their member jurisdictions to implement the Recommendations in the form of legally binding law or regulation, which they can tailor to reflect their respective circumstances and legal structures. As a result, institutions receive the Recommendations as legal and regulatory requirements established within the jurisdictions in which they operate.
ZH: FATF建议以具有法律约束力的法律或法规形式实施，机构据此遵守

[v7u_N001334|1334] To assess member jurisdictions’ compliance with the Recommendations, FATF conducts periodic mutual evaluations through formal reviews by AML/CFT authorities from other jurisdictions.
ZH: FATF通过定期互评估审查成员国合规情况

[v7u_N001335|1335] The resulting mutual evaluation reports are public documents that provide an in-depth assessment of a member jurisdiction’s compliance with each Recommendation.
ZH: 互评估报告为公开文件，深入评估成员国合规情况

[v7u_N001336|1336] For each Recommendation, FATF gives a rating for technical compliance and effectiveness.
ZH: FATF对每项建议给出技术合规性和有效性评级

[v7u_N001337|1337] FATF then requires member jurisdictions to address any deficiencies and subjects them to post-assessment monitoring to ensure they address their issues.
ZH: FATF要求成员国整改缺陷并接受后续监测

[v7u_N001338|1338] Deficiencies can result in a member jurisdiction’s designation on the grey or black lists.
ZH: 缺陷可能导致成员国被列入灰名单或黑名单

[v7u_N001339|1339] These types of designations are likely to result in financial institutions flagging the member jurisdiction as high risk in their internal risk assessments.
ZH: 灰/黑名单认定导致金融机构在内部风险评估中将其标记为高风险
```

## S1 合并候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001308"
    ],
    "proposition": "FATF conducts periodic formal evaluations to determine implementation; if deficiencies identified, it implements action plans and monitors progress.",
    "source_quotes": [
      "FATF conducts periodic formal evaluations and other assessments to determine whether jurisdictions have fully and effectively implemented its standards. If FATF identifies deficiencies, it implements and monitors action plans and publicly reports progress."
    ],
    "relation_cues": [
      "if",
      "identifies",
      "implements",
      "monitors"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF conducts periodic formal evaluations"
      ],
      "basis_or_condition": [
        "FATF identifies deficiencies"
      ],
      "focal_handling_or_judgment": "FATF implements and monitors action plans and publicly reports progress",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001308",
        "quote": "FATF conducts periodic formal evaluations and other assessments to determine whether jurisdictions have fully and effectively implemented its standards. If FATF identifies deficiencies, it implements and monitors action plans and publicly reports progress."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001310"
    ],
    "proposition": "FATF designates jurisdictions failing to implement standards as grey-listed (increased monitoring) or black-listed (high-risk); such designation may lead to isolation from global financial system.",
    "source_quotes": [
      "Where FATF has determined that a jurisdiction has failed to implement its standards, FATF can designate it as a jurisdiction under increased monitoring on the \"grey list\" or a high-risk jurisdiction on the \"black list.\" FATF designations on the grey and black lists can have severe consequences since inclusion on these lists might lead to isolation from the global financial system."
    ],
    "relation_cues": [
      "where",
      "determined",
      "failed",
      "designate",
      "may lead to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF determines that a jurisdiction has failed to implement its standards"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FATF designates the jurisdiction as grey-listed or black-listed",
      "outcomes_or_paths": [
        "inclusion on these lists might lead to isolation from the global financial system"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001310",
        "quote": "Where FATF has determined that a jurisdiction has failed to implement its standards, FATF can designate it as a jurisdiction under increased monitoring on the \"grey list\" or a high-risk jurisdiction on the \"black list.\" FATF designations on the grey and black lists can have severe consequences since inclusion on these lists might lead to isolation from the global financial system."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001334",
      "v7u_N001335",
      "v7u_N001336",
      "v7u_N001337",
      "v7u_N001338",
      "v7u_N001339"
    ],
    "proposition": "FATF conducts mutual evaluations, rates technical compliance and effectiveness, publishes reports, requires members to address deficiencies, and deficits can lead to grey/black list designation, causing financial institutions to flag the jurisdiction as high risk.",
    "source_quotes": [
      "To assess member jurisdictions’ compliance with the Recommendations, FATF conducts periodic mutual evaluations through formal reviews by AML/CFT authorities from other jurisdictions.",
      "The resulting mutual evaluation reports are public documents that provide an in-depth assessment of a member jurisdiction’s compliance with each Recommendation.",
      "For each Recommendation, FATF gives a rating for technical compliance and effectiveness.",
      "FATF then requires member jurisdictions to address any deficiencies and subjects them to post-assessment monitoring to ensure they address their issues.",
      "Deficiencies can result in a member jurisdiction’s designation on the grey or black lists.",
      "These types of designations are likely to result in financial institutions flagging the member jurisdiction as high risk in their internal risk assessments."
    ],
    "relation_cues": [
      "assess",
      "evaluations",
      "ratings",
      "requires",
      "deficiencies",
      "result in"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF assesses member jurisdictions’ compliance"
      ],
      "basis_or_condition": [
        "deficiencies identified"
      ],
      "focal_handling_or_judgment": "FATF conducts mutual evaluations, rates compliance, publishes reports, requires addressing deficiencies, and post-assessment monitoring",
      "outcomes_or_paths": [
        "designation on grey/black list",
        "financial institutions flag jurisdiction as high risk"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001334",
        "quote": "To assess member jurisdictions’ compliance with the Recommendations, FATF conducts periodic mutual evaluations through formal reviews by AML/CFT authorities from other jurisdictions."
      },
      {
        "unit_id": "v7u_N001335",
        "quote": "The resulting mutual evaluation reports are public documents that provide an in-depth assessment of a member jurisdiction’s compliance with each Recommendation."
      },
      {
        "unit_id": "v7u_N001336",
        "quote": "For each Recommendation, FATF gives a rating for technical compliance and effectiveness."
      },
      {
        "unit_id": "v7u_N001337",
        "quote": "FATF then requires member jurisdictions to address any deficiencies and subjects them to post-assessment monitoring to ensure they address their issues."
      },
      {
        "unit_id": "v7u_N001338",
        "quote": "Deficiencies can result in a member jurisdiction’s designation on the grey or black lists."
      },
      {
        "unit_id": "v7u_N001339",
        "quote": "These types of designations are likely to result in financial institutions flagging the member jurisdiction as high risk in their internal risk assessments."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_gap_ch19_s01_monitoring_trends",
    "unit_ids": [
      "v7u_N001309"
    ],
    "proposition": "FATF持续监控犯罪和恐怖分子筹集、使用和转移资金的方式，并发布报告以提高对最新手法和趋势的认识。",
    "source_quotes": [
      "FATF continuously monitors how criminals and terrorists raise, use, and move funds, and publishes reports to raise awareness of the latest techniques and trends."
    ],
    "relation_cues": [
      "continuously monitors",
      "publishes",
      "to raise awareness"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FATF持续监控资金流动方法与趋势，并发布报告",
      "outcomes_or_paths": [
        "提高对最新手法和趋势的认识"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001309",
        "quote": "FATF continuously monitors how criminals and terrorists raise, use, and move funds, and publishes reports to raise awareness of the latest techniques and trends."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_001",
        "s1c_003"
      ],
      "gap_reason": "S1.1候选覆盖了FATF的评估实施和互评估，但未覆盖FATF持续监控犯罪资金流动方法与趋势并发布报告这一独立链条。"
    }
  },
  {
    "candidate_id": "s1c_gap_ch19_s01_standard_setting_fsrb",
    "unit_ids": [
      "v7u_N001312"
    ],
    "proposition": "FATF在制定标准时依赖FSRB的意见输入，但仍保持唯一标准制定机构的地位。",
    "source_quotes": [
      "In setting standards, FATF depends on input from the FSRBs. However, FATF remains the only standard-setting body."
    ],
    "relation_cues": [
      "depends on",
      "However",
      "remains"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF制定标准"
      ],
      "basis_or_condition": [
        "依赖FSRB的意见输入"
      ],
      "focal_handling_or_judgment": "FATF仍是唯一标准制定机构",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001312",
        "quote": "In setting standards, FATF depends on input from the FSRBs. However, FATF remains the only standard-setting body."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_001",
        "s1c_002",
        "s1c_003"
      ],
      "gap_reason": "S1.1候选均未涉及FATF标准制定过程中与FSRB的关系及FATF的唯一制定权地位这一独立判断。"
    }
  }
]
```
