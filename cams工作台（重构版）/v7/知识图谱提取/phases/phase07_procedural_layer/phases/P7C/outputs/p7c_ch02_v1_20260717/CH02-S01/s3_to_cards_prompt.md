# P7C Process IR to Cards v1

## 角色与唯一职责

你是 P7C-S3 构图器。输入为 S2 输出的 Process IR（带 role 的元素 + 带 kind 的关系）和 section 原文；你的唯一职责是复核 S2 的结构、为每个 element 确定精确的 `node_type`，输出完整的 `flow_nodes + flow_edges`（cards.raw.json）。

不得重新裁决候选边界（S2 已做），不得新增/删除/合并 episode，不得新增/删除 element 或 relation，不得输出 derivation/evidence_strength/review_status。

## 输入

1. section 原文（唯一事实来源）
2. allowed_unit_ids（证据引用白名单）
3. S2 输出的完整 Process IR（episodes、elements、relations、candidate_audit）

## 任务

### 步骤 1：复核 S2 结构

对照原文和 Process IR，检查：
- 每个 episode 内所有 element 是否通过 relation 连通
- 端点角色是否与 relation kind 兼容（见第 2 节矩阵）
- decision 节点如有 branch 出边，是否至少有两条
- 每条 branch/condition trigger 是否有 condition
- evidence_unit_ids 是否在白名单内

发现 S2 错误时在校验说明中记录，但仍尽力完成构图。

### 步骤 2：确定 node_type

为每个 element 从以下类型中精确选择。**依据原文语义和上下文，而非机械查表**。参考 S2 的 role 和 kind，但最终以原文的语义定义为准。

**节点分类（node_category）**：entry（E-）、process（P-）、exit（X-）、auxiliary（input/standard）

**入口类型组（entry，对应 S2 role=context）：**

| node_type | 定义 |
|---|---|
| E1_event_signal | 可定位的业务事件启动处理 |
| E2_object_entry | 某类客户、交易、账户或载体进入处理范围 |
| E3_state_threshold | 已观察状态或阈值结果要求处理 |
| E4_handoff | 上一局部流程的输出成为本流程输入 |
| E5_time_cycle | 固定周期或期限启动/约束处理 |
| E6_change_exception | 环境变化、异常或信息缺口启动调整 |
| E7_external_command | 法律、监管或执法要求启动处理 |
| E8_decision_finding | 前一判断本身触发后续义务 |

**处理类型组（process，对应 S2 role=action 或 decision）：**

| node_type | 定义 |
|---|---|
| P1_assessment | 识别风险信号或异常模式，使用标准形成分类、适宜性或有效性结论 |
| P2_execution | 对业务对象实施动作或应对措施，使其状态发生变化 |
| P3_branch_routing | 根据条件选择关闭、升级、继续、拒绝或其他路径 |
| P4_collection | 汇集信息或部件，形成调查基础或正式产物 |
| P5_coordination | 多角色、多部门或前后台协同完成任务 |
| P6_feedback | 根据缺陷、复核问题或结果返回修改、补充研究或重新设计 |
| P7_monitoring | 按周期重复，或持续观察直到新事件再次触发 |
| P8_constrained_action | 动作必须同时满足保密、禁止泄密、法律、相称性等约束 |
| P9_planning | 将风险处置组织为责任人、期限、措施、复核和升级机制 |
| P10_sufficiency | 判断证据是否足以支持结论并决定继续或停止研究 |

**出口类型组（exit，对应 S2 role=outcome）：**

| node_type | 定义 |
|---|---|
| X1_classification | 形成可疑性、风险、有效性或适宜性结论 |
| X2_product | 形成可识别、可保存或可提交的对象 |
| X3_state_change | 业务对象进入新的稳定状态 |
| X4_handoff | 转交下一角色、层级或局部流程 |
| X5_config_change | 规则、阈值、场景、控制或培训被修改 |
| X6_termination | 当前局部目标结束且无进一步动作 |
| X7_continuing_obligation | 进入持续监控、周期复核或受限制关系 |

**辅助类型组（auxiliary，对应 S2 role=input 或 standard）：**
- `input`：输入数据、材料、信息
- `standard`：标准、阈值、规范

role→node_category 是固定的（context→entry, action/decision→process, outcome→exit, input/standard→auxiliary），但 node_type 必须根据上述定义和原文语义选择最精确的一个。

### 步骤 3：构建 flow_nodes + flow_edges

**flow_node（每个 element 对应一个 node）：**
- `node_id`：在 episode 内唯一
- `node_category`：entry/process/exit/auxiliary
- `node_type`：步骤 2 确定的值（27 种之一）
- `label`：保留 element.label 原文
- `evidence_unit_ids`：element 的 evidence_unit_ids
- `evidence_strength`：固定 `explicit`
- `modality`：element 的 modality（可选）

**flow_edge（每个 relation 对应一条 edge，节点引用 node_id）：**

根据 S2 relation 的 kind 和原文语义选择 edge_type。**以原文为准——kind 是建议，不是命令**：

| edge_type | 定义 | S2 kind 的对应关系 |
|---|---|---|
| PRECEDES | 主流程先后关系；表示一个节点在流程上先于另一个节点，或存在明确/强暗示的处理顺序 | trigger、sequence 通常映射为此 |
| REFERENCES | 非时序辅助关联；表示处理节点关联一个输入、线索、标准、判断维度或组成要素，不表示先后、产出或条件分支 | reference 通常映射为此 |
| PRODUCES | 产出关系；表示处理节点产生一个出口节点，如判断、记录、状态变化、交接或持续义务 | produce 通常映射为此，但须确认原文确有产出语义 |
| DECIDES | 条件分流关系；表示根据条件进入不同路径，必须填写 condition | branch 通常映射为此 |
| FEEDBACK | 反馈回流关系；表示结果、复核问题或缺口要求补充、修正、更新或重新处理 | feedback 通常映射为此 |

每条 flow_edge 必填：`edge_id, edge_type, source, target, evidence_unit_ids`。
- `condition`：有则必填（trigger_mode=condition 或 DECIDES 必须有）
- `relation_type`：可选，从 12 种中选择（见下方定义）
- `qualifier`：当 PRODUCES 的原文强度不是"确定产生"时必填：`may_lead_to`（can/may/might 等非确定）、`helps_achieve`（helps/有助于）、`aimed_to`（purpose is to/旨在/以）。原文明确是 produces/results in/导致/产生时省略
- `source_quote`：可选

**12 种 relation_type 定义（可选附加在 edge 上）：**

| relation_type | 定义 |
|---|---|
| clue_supports_identification | 异常、红旗、事实线索支持考生识别风险、可疑性或高风险模式 |
| mechanism_explains_risk | 作案机制、结构安排或产品特征解释为什么存在洗钱/恐融风险 |
| identification_leads_to_conclusion | 识别或评估结果导向风险分类、可疑性、充分性或适宜性结论 |
| conclusion_triggers_response | 风险、可疑、缺陷或合规结论触发加强监控、升级、报告、补救或拒绝等要求 |
| branch_condition_routes_path | 分支条件把流程路由到某条路径；只能用于 DECIDES 边且必须有 condition |
| component_assembles_product | 信息字段、证据、叙述组件或记录要素共同构成正式产物 |
| standard_constrains_action | 法律、保密、相称性、准确性、监管期限等标准限定动作如何执行 |
| result_handoffs_stage | 当前处理结果成为下一角色、层级、系统或外部机构继续处理的输入 |
| feedback_requests_completion | 复核问题、缺失信息或叙述不足要求补充研究、修订或重新处理 |
| cycle_requires_monitoring | 周期、持续义务、后评估或 ongoing monitoring 关系要求复核或继续观察 |
| standard_transmits_requirement | 国际标准、监管原则、指南或评估结果传导为辖区或机构控制要求 |
| parallel_alternative_no_sequence | 多个 typology、标准、组件或案例点互为并列，不应强制串成时间先后边 |

**不得输出**：`derivation`、边级 `evidence_strength`、`review_status`。

## 2. Relation 端点兼容矩阵

| kind | 起点 role | 终点 role | 额外约束 |
|---|---|---|---|
| `trigger` | context | action 或 decision | trigger_mode 必须为 event 或 condition |
| `sequence` | action/decision/outcome | action/decision/outcome | 原文明示先后；context 起点应改用 trigger |
| `reference` | action 或 decision | input 或 standard | 固定 process→auxiliary |
| `produce` | action 或非 P3 的 decision | outcome | target 必须是独立语义结果 |
| `branch` | decision | action 或 outcome | 至少两个互斥分支；每条 condition 必填 |
| `feedback` | outcome 或 decision | action 或 decision | 原文支持复核、补充、更新或调优 |

## 输出 Contract

```json
{
  "section_id": "CH06-S10",
  "cards": [
    {
      "card_id": "p7card_CH06-S10_001",
      "section_id": "CH06-S10",
      "card_nature": "assessment",
      "title": "依据直接和间接持股及适用阈值认定UBO",
      "flow_nodes": [
        {
          "node_id": "n001",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "直接持股比例",
          "evidence_unit_ids": ["v7u_N000477"],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_001",
          "edge_type": "REFERENCES",
          "source": "n004",
          "target": "n001",
          "evidence_unit_ids": ["v7u_N000477"]
        }
      ],
      "source_unit_ids": ["v7u_N000477", "v7u_N000478"],
      "candidate_status": "candidate",
      "review_notes": "局部命题：...；证据范围：...；待P7D逐边审核。"
    }
  ],
  "coverage_audit": [
    {
      "candidate_id": "s1c_001",
      "disposition": "mapped",
      "card_ids": ["p7card_CH06-S10_001"],
      "reason": "..."
    }
  ],
  "node_type_reasons": {
    "ep_001": {
      "e001": "input role → node_type=input",
      "e005": "decision role + 2 branch relations → P3_branch_routing"
    }
  },
  "skip_reason": null
}
```

- 一个 episode 对应一张 card
- card_id 格式 `p7card_{section_id}_{NNN}`
- 每个 flow_node 有 `node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`
- 每条 flow_edge 有 `edge_id, edge_type, source, target, evidence_unit_ids`
- 条件必填 `condition`，不输出 `derivation`
- candidate_status 固定 `candidate`
- review_notes 中文说明增量命题、证据范围、待 P7D 审核
- `node_type_reasons` 记录每个 element 的 node_type 选择理由（至少记录非平凡选择）

`coverage_audit` 沿用 S2 的 `candidate_audit.disposition`，映射规则：
- `mapped/support_only` → `decision: "p7c_card"`，card_ids 至少一张
- `excluded_nonprocedural` → `decision: "kg_only"`，card_ids 为空
- `ungraphable` → `decision: "p7c_ungraphable"`，card_ids 为空

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

allowed_unit_ids:

```json
[
  "v7u_N000060",
  "v7u_N000061",
  "v7u_N000062",
  "v7u_N000063",
  "v7u_N000064",
  "v7u_N000065",
  "v7u_N000066",
  "v7u_N000067",
  "v7u_N000068",
  "v7u_N000069",
  "v7u_N000070",
  "v7u_N000071",
  "v7u_N000072",
  "v7u_N000073",
  "v7u_N000074",
  "v7u_N000075",
  "v7u_N000076",
  "v7u_N000077",
  "v7u_N000078",
  "v7u_N000079",
  "v7u_N000080",
  "v7u_N000081",
  "v7u_N000082",
  "v7u_N000083",
  "v7u_N000084",
  "v7u_N000085",
  "v7u_N000086",
  "v7u_N000087",
  "v7u_N000088",
  "v7u_N000089",
  "v7u_N000090",
  "v7u_N000091",
  "v7u_N000092",
  "v7u_N000093",
  "v7u_N000094",
  "v7u_N000095",
  "v7u_N000096",
  "v7u_N000097",
  "v7u_N000098",
  "v7u_N000099",
  "v7u_N000100",
  "v7u_N000101",
  "v7u_N000102",
  "v7u_N000103",
  "v7u_N000104",
  "v7u_N000105",
  "v7u_N000106",
  "v7u_N000107",
  "v7u_N000108",
  "v7u_N000109",
  "v7u_N000110",
  "v7u_N000111"
]
```

## S2 Process IR

```json
{
  "section_id": "CH02-S01",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "金融机构如何处理FATF确定的21类上游犯罪？",
      "title": "依据FATF分类承认并监控上游犯罪",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "FATF has identified 21 categories of predicate offenses",
          "evidence_unit_ids": [
            "v7u_N000062"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "financial institutions must acknowledge and monitor these offenses under AML compliance programs",
          "evidence_unit_ids": [
            "v7u_N000062"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e001",
          "evidence_unit_ids": [
            "v7u_N000062"
          ],
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "source_quote": "FATF has identified 21 categories of predicate offenses that financial institutions must acknowledge and monitor under AML compliance programs."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "受监管实体如何应对制裁规避风险？",
      "title": "建立反洗钱和制裁合规计划以检测和预防制裁规避",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "need for detecting and preventing sanctions evasion",
          "evidence_unit_ids": [
            "v7u_N000099"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "regulated entities must have strong AML and sanctions compliance programs with robust policies, procedures, and internal controls",
          "evidence_unit_ids": [
            "v7u_N000099"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": null,
          "evidence_unit_ids": [
            "v7u_N000099"
          ],
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "source_quote": "Regulated entities must have strong AML and sanctions compliance programs with robust policies, procedures, and internal controls for detecting and preventing sanctions evasion."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "银行合规官如何通过调查揭露非法活动？",
      "title": "调查异常支付流并揭露非法网络",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "compliance officer flagged irregular payment flows linked to RedStar",
          "evidence_unit_ids": [
            "v7u_N000111"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "further investigation",
          "evidence_unit_ids": [
            "v7u_N000111"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "exposed the illicit network, revealing Komarov and Volkof Industries' role in sanctions evasion, proliferation financing, laundering criminal proceeds, and foreign bribery and corruption offences",
          "evidence_unit_ids": [
            "v7u_N000111"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": null,
          "evidence_unit_ids": [
            "v7u_N000111"
          ],
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "source_quote": "The scheme unraveled when a bank’s compliance officer flagged irregular payment flows linked to RedStar. Further investigation exposed the illicit network..."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "evidence_unit_ids": [
            "v7u_N000111"
          ],
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "source_quote": "Further investigation exposed the illicit network, revealing Komarov and Volkof Industries’ role in sanctions evasion, proliferation financing, laundering criminal proceeds, and foreign bribery and corruption offences."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_gap_ch02_s01_crossborder_risk_control"
      ],
      "focal_question": "跨境背景下如何协调风险控制与多法域法律？",
      "title": "协调风险控制以适应跨境法律差异",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "variation in classification of predicate offenses across jurisdictions can complicate AML efforts",
          "evidence_unit_ids": [
            "v7u_N000065"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "compliance professionals operating in cross-border contexts need to align risk controls with the laws and regulations of more than one jurisdiction",
          "evidence_unit_ids": [
            "v7u_N000065"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": null,
          "evidence_unit_ids": [
            "v7u_N000065"
          ],
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "source_quote": "This variation can complicate AML efforts, with compliance professionals operating in cross-border contexts needing to align risk controls with the laws and regulations of more than one jurisdiction."
        }
      ],
      "split_reason": null
    }
  ],
  "candidate_audit": [
    {
      "candidate_id": "s1c_001",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选提供了金融机构必须根据FATF分类承认并监控上游犯罪这一程序性要求，已建模为参考标准动作。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选的核心是受监管实体必须建立合规计划这一程序性要求，已建模；所列处罚为静态法律后果，不构成业务流程，未建模。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选的核心是合规官通过调查揭露非法网络的过程，符合流程定义；案例背景细节未作为独立流程建模。"
    },
    {
      "candidate_id": "s1c_gap_ch02_s01_crossborder_risk_control",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选提供了跨境背景下合规专业人士必须协调风险控制这一过程要求，已建模。"
    }
  ],
  "skip_reason": null
}
```
