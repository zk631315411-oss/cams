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

为每个 element 从以下类型中精确选择。**依据原文语义和上下文，**。参考 S2 的 role 和 kind，但最终以原文的语义定义为准。

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

section_id: `CH15-S03`

section_title: `Money laundering risks associated with DNFBPs > Real estate sector risks`

section_text_with_unit_anchors:

```text
[v7u_N001092|1092] The real estate sector is inherently susceptible to money laundering due to the substantial sums involved in property transactions and the tangible nature of these assets.
ZH: 房地产行业因交易金额大和资产有形性而固有洗钱风险

[v7u_N001093|1093] Criminals can utilize real estate to integrate illicit funds into the legitimate economy by purchasing tangible assets, typically of significant value.
ZH: 犯罪分子通过购买高价值房地产将非法资金融入合法经济

[v7u_N001094|1094] The gains or profits are realized upon the sale of the asset, which, by then, is fully supported and legitimized in the paper trail of sale documentation, allowing money launderers to benefit from it.
ZH: 出售房地产时通过完整的文件记录使非法收益合法化

[v7u_N001095|1095] Real estate transactions often involve lawyers and other third parties, further legitimizing the movement of funds.
ZH: 房地产交易中律师等第三方的参与进一步使资金流动合法化

[v7u_N001096|1096] Buying, selling, or renting properties presents opportunities for criminals to disguise the origin of funds through obscured ownership structures.
ZH: 买卖或租赁房地产为犯罪分子通过模糊所有权结构掩饰资金来源提供机会

[v7u_N001097|1097] For example, properties acquired by corporate entities, trusts, or nominees without a clear justification as to why they were not purchased directly by an individual are red flags.
ZH: 由公司、信托或代名人购买房产且无合理解释是红旗信号信号

[v7u_N001098|1098] The lack of justification raises further concerns if the entity has minimal business activity.
ZH: 购买实体业务活动极少且无合理解释进一步引起担忧

[v7u_N001099|1099] It is also a concern if the entity is based in a jurisdiction known for its corporate secrecy for example, the Cayman Islands or the Bahamas.
ZH: 实体位于公司保密司法管辖区（如开曼群岛或巴哈马）也是风险信号

[v7u_N001100|1100] The global nature of the real estate market further complicates detection efforts. International buyers and cross-border transactions can mask illicit activities.
ZH: 房地产市场的全球性使检测工作更加复杂

[v7u_N001101|1101] A buyer from a high-risk or uncooperative jurisdiction, one lacking an established local presence or legitimate reason for purchasing property, poses an additional risk.
ZH: 来自高风险或未合作司法管辖区的买家构成额外洗钱风险

[v7u_N001102|1102] Cash transactions remain relatively common in some markets and increase the potential for money laundering, as cash is more challenging to trace than payments made through financial institutions.
ZH: 现金交易因难以追踪而增加洗钱风险

[v7u_N001103|1103] Red flags include buyers who pay entirely or primarily in cash, particularly in regions where bank financing is the norm.
ZH: 全部或主要用现金支付的买家是房地产洗钱红旗信号信号

[v7u_N001104|1104] Other red flags include buyers who exhibit little concern for the property's specifics, such as its condition or location, prioritizing the swift completion of the transaction instead.
ZH: 买家对房产细节漠不关心、只求快速成交是洗钱红旗信号信号

[v7u_N001105|1105] Properties that frequently change ownership or are involved in a series of rapid transactions should also raise suspicions.
ZH: 频繁或快速转手的房产应引起洗钱怀疑

[v7u_N001106|1106] Real estate professionals should collaborate with other DNFBPs to identify and prevent money laundering.
ZH: 房地产专业人士应与其他DNFBP合作预防洗钱

[v7u_N001107|1107] Lawyers and notaries can confirm the legitimacy of property ownership, ensure the validity of contracts, and examine the legality of the source of funds. They review transaction structures and the legitimacy of corporate buyers.
ZH: 律师和公证人可确认产权、合同有效性及资金来源合法性

[v7u_N001108|1108] Accountants can evaluate buyers' financial backgrounds, offering insights into the legitimacy of their wealth and compliance with local tax obligations.
ZH: 会计师可评估买家财务背景，判断财富合法性与税务合规

[v7u_N001109|1109] This collaboration enhances market integrity and transparency, supporting the mitigation of money laundering risks in the real estate sector.
ZH: DNFBP之间的合作可增强市场诚信与透明度，降低洗钱风险

[v7u_N001110|1110] Money laundering poses substantial risks in the accounting and auditing sectors due to professionals' access to sensitive financial information and their roles in financial management, reporting, and advising.
ZH: 会计与审计行业因接触敏感财务信息而面临重大洗钱风险

[v7u_N001111|1111] Accountants frequently find themselves in a position to detect suspicious activities, but they should remain vigilant to ensure they do not inadvertently facilitate illegal practices.
ZH: 会计师有责任发现可疑活动并避免无意中协助非法行为

[v7u_N001112|1112] Their involvement in handling financial records provides easy access to data, and their inability to detect suspicious activity might lead them to unwittingly create complex structures that enable illegal activities, such as structuring.
ZH: 会计师可能无意中创建复杂结构为非法活动（如拆分交易）提供便利

[v7u_N001113|1113] If an accountant designs overly complex or opaque transactions, it might raise a red flag for money laundering.
ZH: 会计师设计过于复杂或不透明的交易可能是洗钱红旗信号信号

[v7u_N001114|1114] One consequential risk for accountants is inadvertently supporting tax evasion, with subsequent transactions potentially serving as a conduit for money laundering.
ZH: 会计师可能无意中协助逃税，后续交易可能成为洗钱渠道

[v7u_N001115|1115] Tax avoidance involves legally minimizing tax liabilities, while tax evasion includes illegal actions, such as falsifying records or concealing income.
ZH: 税务规避是合法减少税负，逃税是非法行为如伪造记录或隐瞒收入

[v7u_N001116|1116] If accountants become complicit in illegal tax evasion schemes, they might also inadvertently assist in money laundering, as illicit funds are often concealed through fraudulent tax practices.
ZH: 会计师若参与非法逃税计划，可能无意中协助洗钱

[v7u_N001117|1117] Accountants provide various services, some of which are listed below. These services have corresponding money laundering risks.
ZH: 会计师提供的各类服务对应不同的洗钱风险

[v7u_N001118|1118] Money laundering is a prominent concern in the legal sector due to the influential role lawyers and notaries play in managing financial transactions, providing legal advice, and knowing their clients. Criminals often exploit the services of legal professionals to conceal illicit funds, facilitate fraudulent transactions, or structure deals in ways that obscure the origin of money.
ZH: 法律行业因律师和公证人管理金融交易而面临显著洗钱风险

[v7u_N001119|1119] Legal professionals provide various services, some of which are listed below. These services have corresponding money laundering risks.
ZH: 法律专业人士提供的各类服务对应不同的洗钱风险
```

allowed_unit_ids:

```json
[
  "v7u_N001092",
  "v7u_N001093",
  "v7u_N001094",
  "v7u_N001095",
  "v7u_N001096",
  "v7u_N001097",
  "v7u_N001098",
  "v7u_N001099",
  "v7u_N001100",
  "v7u_N001101",
  "v7u_N001102",
  "v7u_N001103",
  "v7u_N001104",
  "v7u_N001105",
  "v7u_N001106",
  "v7u_N001107",
  "v7u_N001108",
  "v7u_N001109",
  "v7u_N001110",
  "v7u_N001111",
  "v7u_N001112",
  "v7u_N001113",
  "v7u_N001114",
  "v7u_N001115",
  "v7u_N001116",
  "v7u_N001117",
  "v7u_N001118",
  "v7u_N001119"
]
```

## S2 Process IR

```json
{
  "section_id": "CH15-S03",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "What property transactions should raise money laundering suspicions?",
      "title": "Frequent or rapid property transactions raise suspicions of money laundering",
      "card_nature": "risk_indicator",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Properties that frequently change ownership or are involved in a series of rapid transactions",
          "evidence_unit_ids": [
            "v7u_N001105"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "should raise suspicions of money laundering",
          "evidence_unit_ids": [
            "v7u_N001105"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": "Properties that frequently change ownership or are involved in a series of rapid transactions",
          "relation_type": "clue_supports_identification",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001105"
          ],
          "source_quote": "Properties that frequently change ownership or are involved in a series of rapid transactions should also raise suspicions."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "How should real estate professionals collaborate with other DNFBPs to identify and prevent money laundering?",
      "title": "Real estate professionals should collaborate with other DNFBPs to identify and prevent money laundering",
      "card_nature": "control",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "should collaborate with other DNFBPs",
          "evidence_unit_ids": [
            "v7u_N001106"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "identify and prevent money laundering",
          "evidence_unit_ids": [
            "v7u_N001106"
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
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001106"
          ],
          "source_quote": "Real estate professionals should collaborate with other DNFBPs to identify and prevent money laundering."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "How should accountants remain vigilant to avoid inadvertently facilitating illegal practices?",
      "title": "Accountants should remain vigilant to ensure they do not inadvertently facilitate illegal practices",
      "card_nature": "control",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "should remain vigilant",
          "evidence_unit_ids": [
            "v7u_N001111"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "ensure they do not inadvertently facilitate illegal practices",
          "evidence_unit_ids": [
            "v7u_N001111"
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
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001111"
          ],
          "source_quote": "they should remain vigilant to ensure they do not inadvertently facilitate illegal practices."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "Does an accountant designing overly complex or opaque transactions raise a red flag for money laundering?",
      "title": "Accountant designing overly complex or opaque transactions might raise a red flag for money laundering",
      "card_nature": "risk_indicator",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Accountant designs overly complex or opaque transactions",
          "evidence_unit_ids": [
            "v7u_N001113"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "might raise a red flag for money laundering",
          "evidence_unit_ids": [
            "v7u_N001113"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": "If an accountant designs overly complex or opaque transactions",
          "relation_type": "clue_supports_identification",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001113"
          ],
          "source_quote": "If an accountant designs overly complex or opaque transactions, it might raise a red flag for money laundering."
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
      "reason": "该候选陈述了频繁转手房产应引起怀疑的判断，满足程序性迁移定义。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选明确要求房地产专业人士与其他DNFBP合作，是一道可执行的程序。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选要求会计师保持警惕以防止无意协助非法活动，构成控制程序。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选给出了设计复杂交易可能引发洗钱红旗的触发判断，符合风险指标流程。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述会计师参与逃税可能协助洗钱的因果风险机制，无业务判断或程序。"
    },
    {
      "candidate_id": "s1c_gap_ch15_s03_entity_purchase_red_flag",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "列举公司实体购买等红旗信号，属静态风险分类，非流程性判断。"
    },
    {
      "candidate_id": "s1c_gap_ch15_s03_high_risk_buyer",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "陈述高风险辖区买家构成额外风险的静态风险属性。"
    },
    {
      "candidate_id": "s1c_gap_ch15_s03_cash_payment_red_flag",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "将现金支付列为红旗信号的静态分类。"
    },
    {
      "candidate_id": "s1c_gap_ch15_s03_speed_red_flag",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "将漠视房产细节、快速成交列为红旗信号的静态分类。"
    },
    {
      "candidate_id": "s1c_gap_ch15_s03_accountant_inability_structure",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述会计师疏忽可能导致创建复杂结构的风险机制，非业务程序。"
    },
    {
      "candidate_id": "s1c_gap_ch15_s03_accountant_tax_evasion_ml",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述协助逃税后交易成为洗钱渠道的因果链，非业务程序。"
    }
  ],
  "skip_reason": null
}
```
