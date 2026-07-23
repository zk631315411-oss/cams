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

section_id: `CH02-S05`

section_title: `Types of financial crime > Key takeaways`

section_text_with_unit_anchors:

```text
[v7u_N000145|145] Multinationals using intermediaries in high-risk areas face increased bribery risks.
ZH: 在高风险地区使用中介的跨国公司面临更高的贿赂风险

[v7u_N000146|146] Corporate bribery often involves third parties, shell companies, and false invoicing.
ZH: 企业贿赂常涉及第三方、壳公司和虚假发票

[v7u_N000147|147] Illicit funds are frequently laundered to conceal their origin.
ZH: 非法资金常被洗钱以掩盖其来源

[v7u_N000148|148] Financial institutions should:
ZH: 金融机构应采取以下措施

[v7u_N000149|149] Conduct audits to identify control deficiencies.
ZH: 进行审计以识别控制缺陷

[v7u_N000150|150] Enhance transaction monitoring for suspicious activities, especially regarding “consultancy fees” to individuals or intermediaries located in high-risk jurisdictions.
ZH: 加强对高风险地区咨询费的可疑交易监控

[v7u_N000151|151] Include anti-bribery clauses for customers engaging in intermediary models.
ZH: 对采用中介模式的客户加入反贿赂条款

[v7u_N000152|152] Tax avoidance, or tax planning, is not illegal. It is the activity of legitimately reducing the amount of tax owed to government by legal or natural persons.
ZH: 避税是合法减少税负的行为

[v7u_N000153|153] Some jurisdictions encourage tax avoidance by allowing pre-tax savings.
ZH: 一些司法管辖区通过允许税前储蓄来鼓励避税

[v7u_N000154|154] Tax evasion is the use of illegal practices to avoid paying a tax liability.
ZH: 逃税是使用非法手段逃避纳税义务

[v7u_N000155|155] This could include not declaring taxable income or hiding taxable assets from the authorities.
ZH: 逃税示例：不申报应税收入或隐藏应税资产

[v7u_N000156|156] Tax evasion is illegal and those caught are generally subject to criminal charges and substantial penalties.
ZH: 逃税违法，将面临刑事指控和重大处罚

[v7u_N000157|157] While tax avoidance is legal and causes financial services firms no concerns, aggressive tax avoidance is defined as the aggressive legal interpretation of the law without adequately considering its intent or spirit.
ZH: 激进避税是激进地解释法律而不考虑其意图或精神

[v7u_N000158|158] An example of aggressive tax avoidance is a multinational company requiring its subsidiaries to pay a royalty fee for the use of its intellectual property. This reduces the profitability of the overseas unit and therefore reduces the tax they pay in that jurisdiction.
ZH: 激进避税示例：跨国公司要求子公司支付知识产权使用费以减少利润和税款

[v7u_N000159|159] AFC professionals should be satisfied that a customer’s activities across an account fall within avoidance parameters.
ZH: 金融犯罪防控专业人员应确保客户活动在避税参数范围内

[v7u_N000160|160] Tax evasion is illegal and is considered a predicate offense for money laundering.
ZH: 逃税是洗钱的上游犯罪

[v7u_N000161|161] A predicate offense is a component part of a more serious crime.
ZH: 上游犯罪是更严重犯罪的组成部分。

[v7u_N000162|162] Information gathered at onboarding and during transaction monitoring should inform the activity the organization should expect across the customer’s account.
ZH: 开户和交易监控数据应告知机构对客户账户的预期活动。

[v7u_N000163|163] Unusual activity such as excessive personal expense claims across a small business account might be a warning signal that a customer is evading tax.
ZH: 小企业账户中过度的个人费用报销可能是逃税的警告信号。

[v7u_N000164|164] The Common Reporting Standard (CRS), developed in response to the G-20 countries' request and approved by the OECD (Organization for Economic Cooperation and Development) Council, calls on jurisdictions to obtain information from their financial institutions and automatically exchange that information with other jurisdictions on an annual basis. It sets out the financial account information to be exchanged, the financial institutions required to report, the different types of accounts and taxpayers covered, as well as common due diligence procedures to be followed by financial institutions. Its purpose is to combat tax evasion.
ZH: 共同申报准则（CRS）要求司法管辖区每年自动交换金融账户信息以打击逃税。

[v7u_N000165|165] Fraud is an intentional act of criminal deception in order to obtain an unjust or illegal advantage. Typically, fraud results in financial or personal gain. Notice that fraud is intentional and uses deception to achieve the goal.
ZH: 欺诈是为获取不正当利益而故意进行的欺骗行为。

[v7u_N000166|166] Fraud can be committed by one or more individuals—from low-level employees, to management, to government officials. It can be found in every country and every type of business.
ZH: 欺诈可由个人或多人实施，存在于各国和各行业。

[v7u_N000167|167] Knowing the common features of fraud, as well as typical motivations and red flags, will help you combat this crime.
ZH: 了解欺诈的常见特征、动机和红旗信号信号有助于打击此类犯罪。

[v7u_N000168|168] People commit fraud for three major reasons: pressure, opportunity, and rationalization. This three-sided model is referred to as the “Fraud Triangle.”
ZH: 欺诈三角模型指出欺诈的三个主要原因：压力、机会和合理化。

[v7u_N000169|169] Pressure is sometimes called "incentive." It can be a financial problem that drives a person to commit fraud, such as gambling or other debt. This can create the pressure to commit fraud.
ZH: 压力（或诱因）是驱动个人实施欺诈的财务问题，如赌博债务。

[v7u_N000170|170] Opportunity is often provided by a lack of effective internal controls within an institution. For example, confidential documents are left unattended in the office.
ZH: 机会通常由机构内部缺乏有效的内部控制提供。

[v7u_N000171|171] Rationalization is when the fraudster convinces herself that what she is doing does not really matter or that the fraud is justified.
ZH: 合理化是欺诈者说服自己行为无关紧要或正当的过程。

[v7u_N000172|172] There are many different types of fraud, or schemes, each of which has its own unique red flags. Common red flags of fraud include:
ZH: 欺诈有多种类型，每种都有独特的红旗信号信号，常见红旗信号包括：

[v7u_N000173|173] Something sounds too good to be true
ZH: 听起来好得令人难以置信。

[v7u_N000174|174] A promise of high returns for low investment
ZH: 承诺低投资高回报。

[v7u_N000175|175] Demand for upfront payments
ZH: 要求预先付款。

[v7u_N000176|176] Deliberate creation of an artificial shortage of opportunities
ZH: 故意制造人为的机会稀缺。

[v7u_N000177|177] Element of secrecy
ZH: 保密元素。

[v7u_N000178|178] Sense of urgency
ZH: 紧迫感。

[v7u_N000179|179] Pressure to act...right now!
ZH: 立即行动的压力。
```

allowed_unit_ids:

```json
[
  "v7u_N000145",
  "v7u_N000146",
  "v7u_N000147",
  "v7u_N000148",
  "v7u_N000149",
  "v7u_N000150",
  "v7u_N000151",
  "v7u_N000152",
  "v7u_N000153",
  "v7u_N000154",
  "v7u_N000155",
  "v7u_N000156",
  "v7u_N000157",
  "v7u_N000158",
  "v7u_N000159",
  "v7u_N000160",
  "v7u_N000161",
  "v7u_N000162",
  "v7u_N000163",
  "v7u_N000164",
  "v7u_N000165",
  "v7u_N000166",
  "v7u_N000167",
  "v7u_N000168",
  "v7u_N000169",
  "v7u_N000170",
  "v7u_N000171",
  "v7u_N000172",
  "v7u_N000173",
  "v7u_N000174",
  "v7u_N000175",
  "v7u_N000176",
  "v7u_N000177",
  "v7u_N000178",
  "v7u_N000179"
]
```

## S2 Process IR

```json
{
  "section_id": "CH02-S05",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "如何识别控制缺陷？",
      "title": "通过审计识别控制缺陷",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "Conduct audits",
          "evidence_unit_ids": [
            "v7u_N000149"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "Identification of control deficiencies",
          "evidence_unit_ids": [
            "v7u_N000149"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e002",
          "condition": null,
          "relation_type": "component_assembles_product",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N000149"
          ],
          "source_quote": "Conduct audits to identify control deficiencies."
        }
      ],
      "split_reason": "s1c_001包含三个独立措施；本episode为审计部分。"
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "如何监控可疑交易？",
      "title": "加强交易监控以检测可疑活动",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "Enhance transaction monitoring for suspicious activities, especially regarding “consultancy fees” to individuals or intermediaries located in high-risk jurisdictions",
          "evidence_unit_ids": [
            "v7u_N000150"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "Detection of suspicious activities",
          "evidence_unit_ids": [
            "v7u_N000150"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e002",
          "condition": null,
          "relation_type": "component_assembles_product",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N000150"
          ],
          "source_quote": "Enhance transaction monitoring for suspicious activities, especially regarding “consultancy fees” to individuals or intermediaries located in high-risk jurisdictions."
        }
      ],
      "split_reason": "s1c_001包含三个独立措施；本episode为交易监控部分。"
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "如何约束中介模式客户？",
      "title": "对中介模式客户加入反贿赂条款",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "Include anti-bribery clauses for customers engaging in intermediary models",
          "evidence_unit_ids": [
            "v7u_N000151"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "Anti-bribery clauses are included in contracts",
          "evidence_unit_ids": [
            "v7u_N000151"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e002",
          "condition": null,
          "relation_type": "component_assembles_product",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000151"
          ],
          "source_quote": "Include anti-bribery clauses for customers engaging in intermediary models."
        }
      ],
      "split_reason": "s1c_001包含三个独立措施；本episode为合同条款部分。"
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "如何确保客户活动在避税参数内？",
      "title": "AFC专业人员评估客户活动以确认在避税参数内",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "decision",
          "label": "AFC professionals should be satisfied that a customer’s activities across an account fall within avoidance parameters",
          "evidence_unit_ids": [
            "v7u_N000159"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "Customer activities are confirmed to be within avoidance parameters",
          "evidence_unit_ids": [
            "v7u_N000159"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e002",
          "condition": null,
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N000159"
          ],
          "source_quote": "AFC professionals should be satisfied that a customer’s activities across an account fall within avoidance parameters."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "如何形成客户预期活动？",
      "title": "基于开户和交易监控信息形成客户预期活动",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "Information gathered at onboarding and during transaction monitoring",
          "evidence_unit_ids": [
            "v7u_N000162"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Use onboarding and transaction monitoring information to inform expected activity",
          "evidence_unit_ids": [
            "v7u_N000162"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "Expected activity across the customer’s account",
          "evidence_unit_ids": [
            "v7u_N000162"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e001",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000162"
          ],
          "source_quote": "Information gathered at onboarding and during transaction monitoring should inform the activity the organization should expect across the customer’s account."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "condition": null,
          "relation_type": "component_assembles_product",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N000162"
          ],
          "source_quote": "Information gathered at onboarding and during transaction monitoring should inform the activity the organization should expect across the customer’s account."
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
        "ep_001",
        "ep_002",
        "ep_003"
      ],
      "reason": "该候选包含三个独立程序措施（审计、交易监控、反贿赂条款），各自形成流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "候选描述了AFC专业人员评估客户活动是否符合避税参数的判断流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "候选描述了利用开户和交易监控信息形成预期活动的流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "候选仅指出过度个人费用可能是逃税警告信号，属于静态风险线索，不包含流程或判断动作。"
    }
  ],
  "skip_reason": null
}
```
