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

section_id: `CH11-S02`

section_title: `Money laundering risks associated with MSBs, payment service providers, and ecommerce > Money services business`

section_text_with_unit_anchors:

```text
[v7u_N000813|813] A money service business (MSB) is a type of nonbank financial institution that provides financial services involving the transfer of money or value.
ZH: 货币服务企业是提供货币或价值转移服务的非银行金融机构

[v7u_N000814|814] An entity is an MSB if it holds funds on behalf of another person or entity.
ZH: 若实体代他人持有资金，则被视为货币服务企业

[v7u_N000815|815] In many jurisdictions, MSBs are required to comply with local regulatory AML and CFT requirements. These requirements can include registering with local regulators and establishing an AML compliance program.
ZH: 许多司法辖区要求货币服务企业遵守反洗钱和反恐怖融资规定，包括注册和建立合规计划

[v7u_N000816|816] MSB services vary according to their licensing requirement. Examples of MSB services include:
ZH: 货币服务企业的服务因牌照要求而异，以下为示例列表

[v7u_N000817|817] Currency exchange
ZH: 货币服务企业的服务包括货币兑换

[v7u_N000818|818] Money transfers
ZH: 货币服务企业的服务包括汇款

[v7u_N000819|819] Money orders
ZH: 货币服务企业的服务包括汇票

[v7u_N000820|820] Stored-value products, such as prepaid cards or gift cards
ZH: 货币服务企业的服务包括储值产品，如预付卡或礼品卡

[v7u_N000821|821] Bill payment services
ZH: 货币服务企业提供的账单支付服务

[v7u_N000822|822] These services can be delivered through online platforms, mobile apps, or physical branches.
ZH: 货币服务企业服务可通过在线平台、移动应用或实体网点提供

[v7u_N000823|823] MSBs originally required licensing mainly for currency exchange, but the scope has expanded to include cross-border money transfers and additional services.
ZH: 货币服务企业许可范围从货币兑换扩展到跨境汇款及其他服务

[v7u_N000824|824] If a business participates in activities categorized as MSB services, it must obtain a license to operate legally.
ZH: 从事货币服务企业服务的企业必须获得许可才能合法运营

[v7u_N000825|825] Historically, MSBs were mainly used to serve individual customers’ crossborder transactions more quickly and cheaply.
ZH: 历史上货币服务企业主要用于为个人客户提供更快更便宜的跨境交易

[v7u_N000826|826] Today, MSBs also serve small and medium-sized businesses that are not served by larger financial institutions.
ZH: 如今货币服务企业也为大型金融机构服务不足的中小企业提供服务

[v7u_N000827|827] The changes in the usage of MSB licenses also bring stringent jurisdictional registration requirements and regulations.
ZH: 货币服务企业许可使用变化带来严格的司法注册要求和法规

[v7u_N000828|828] According to FinCEN, hawala is an informal value transfer system (IVTS), which is classified under the money transmitter category of MSBs.
ZH: FinCEN将哈瓦拉归类为非正式价值转移系统和货币服务企业中的货币转移商

[v7u_N000829|829] However, hawala differs from other, more traditional, MSBs in several ways. The primary distinction is that MSBs are regulated by the banking system, while hawala operates as an informal and largely unregulated method of money transfer.
ZH: 哈瓦拉与传统货币服务企业的主要区别在于监管：货币服务企业受银行体系监管，哈瓦拉为非正规且基本不受监管

[v7u_N000830|830] MSBs face complex jurisdictional licensing requirements, including varying fees and compliance obligations. Each jurisdiction may impose different AML regulations, which can create operational burdens and increase regulatory scrutiny. This complexity can lead to difficulties in maintaining compliance across multiple borders.
ZH: 货币服务企业面临复杂的司法许可要求，包括不同费用和反洗钱合规义务

[v7u_N000831|831] Noncompliance, intentional or accidental, might lead to severe penalties, including regulatory fines, consent orders, and even loss of business licenses.
ZH: 货币服务企业不合规可能导致监管罚款、同意令甚至吊销营业执照

[v7u_N000832|832] MSBs often serve customers or engage in business activities less likely to be supported by traditional financial institutions. These customers include individuals lacking access to mainstream banking services. However, customers without access to traditional banking services can pose challenges when assessing money laundering and terrorist financing risks. Some of these risks include:
ZH: 货币服务企业服务无银行账户客户带来的洗钱和恐怖融资风险

[v7u_N000833|833] Lack of financial history: Unbanked customers often lack financial records, making it difficult for MSBs to assess the legitimacy of their transactions.
ZH: 无银行账户客户缺乏财务记录，货币服务企业难以评估交易合法性

[v7u_N000834|834] Cash transactions: Unbanked individuals rely on cash, which can create vulnerabilities for MSBs, such as difficulty in tracking a high volume of transactions and ascertaining the source of these funds.
ZH: 无银行账户者依赖现金交易，给货币服务企业带来追踪和资金来源确认困难

[v7u_N000835|835] These risks typically fall outside the risk appetite of traditional financial institutions, particularly due to the substantial volume of cross-border remittances.
ZH: 这些风险通常超出传统金融机构的风险偏好，尤其是大量跨境汇款

[v7u_N000836|836] MSBs need to implement additional strategic money laundering and operational controls, such as enhanced due diligence. They should also limit the exposure to high-risk customers.
ZH: 货币服务企业需实施额外洗钱和运营控制，如强化尽职调查，并限制高风险客户敞口

[v7u_N000837|837] Cross-border transactions complicate compliance efforts. Different jurisdictions enforce varying laws regarding fund movement, currency controls, sanctions, and regulatory and tax reporting. Some countries implement strict restrictions on remittances, while others are more lenient.
ZH: 跨境交易因不同司法管辖区的资金流动、货币管制、制裁和税务报告法律而复杂化

[v7u_N000838|838] Establishing long-term and trusted relationships with correspondent banks can mitigate money laundering and compliance risks.
ZH: 与代理行建立长期信任关系可降低洗钱和合规风险

[v7u_N000839|839] A correspondent bank serves as an intermediary in international transactions, aiding the MSB in accessing banking services that might not be directly available to it because of its higher-risk customer base.
ZH: 代理行作为国际交易中介，帮助货币服务企业获得因高风险客户群而无法直接获得的银行服务

[v7u_N000840|840] Correspondent banks are required to assess the soundness of the MSB’s compliance program and ensure that the MSB’s activities align with the correspondent bank’s risk appetite.
ZH: 代理行需评估货币服务企业合规计划的健全性，并确保其活动符合代理行的风险偏好
```

allowed_unit_ids:

```json
[
  "v7u_N000813",
  "v7u_N000814",
  "v7u_N000815",
  "v7u_N000816",
  "v7u_N000817",
  "v7u_N000818",
  "v7u_N000819",
  "v7u_N000820",
  "v7u_N000821",
  "v7u_N000822",
  "v7u_N000823",
  "v7u_N000824",
  "v7u_N000825",
  "v7u_N000826",
  "v7u_N000827",
  "v7u_N000828",
  "v7u_N000829",
  "v7u_N000830",
  "v7u_N000831",
  "v7u_N000832",
  "v7u_N000833",
  "v7u_N000834",
  "v7u_N000835",
  "v7u_N000836",
  "v7u_N000837",
  "v7u_N000838",
  "v7u_N000839",
  "v7u_N000840"
]
```

## S2 Process IR

```json
{
  "section_id": "CH11-S02",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "MSB如何满足当地AML/CFT要求？",
      "title": "MSB遵守AML/CFT要求并建立合规计划",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "MSBs (money services businesses)",
          "evidence_unit_ids": [
            "v7u_N000815"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Comply with local regulatory AML and CFT requirements",
          "evidence_unit_ids": [
            "v7u_N000815"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "Register with local regulators",
          "evidence_unit_ids": [
            "v7u_N000815"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "Establish an AML compliance program",
          "evidence_unit_ids": [
            "v7u_N000815"
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
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000815"
          ],
          "source_quote": "In many jurisdictions, MSBs are required to comply with local regulatory AML and CFT requirements."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000815"
          ],
          "source_quote": "These requirements can include registering with local regulators"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000815"
          ],
          "source_quote": "and establishing an AML compliance program."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "从事MSB服务如何获得合法运营许可？",
      "title": "参与MSB服务必须获得许可才能合法运营",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Business participates in activities categorized as MSB services",
          "evidence_unit_ids": [
            "v7u_N000824"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Obtain a license to operate legally",
          "evidence_unit_ids": [
            "v7u_N000824"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "Legal operation",
          "evidence_unit_ids": [
            "v7u_N000824"
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
          "condition": "If a business participates in activities categorized as MSB services",
          "relation_type": "branch_condition_routes_path",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000824"
          ],
          "source_quote": "If a business participates in activities categorized as MSB services, it must obtain a license to operate legally."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000824"
          ],
          "source_quote": "obtain a license to operate legally"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "MSB如何实施额外的洗钱和运营控制？",
      "title": "MSB实施额外控制并限制高风险客户敞口",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "MSBs (money services businesses)",
          "evidence_unit_ids": [
            "v7u_N000836"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "Money laundering and operational risks",
          "evidence_unit_ids": [
            "v7u_N000836"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "Implement additional strategic money laundering and operational controls",
          "evidence_unit_ids": [
            "v7u_N000836"
          ],
          "modality": "required"
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "Limit the exposure to high-risk customers",
          "evidence_unit_ids": [
            "v7u_N000836"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "Enhanced due diligence implemented",
          "evidence_unit_ids": [
            "v7u_N000836"
          ],
          "modality": null
        },
        {
          "element_id": "e006",
          "role": "outcome",
          "label": "Exposure to high-risk customers limited",
          "evidence_unit_ids": [
            "v7u_N000836"
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
          "process_element_id": "e003",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000836"
          ],
          "source_quote": "MSBs need to implement additional strategic money laundering and operational controls"
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000836"
          ],
          "source_quote": "MSBs need to implement additional strategic money laundering and operational controls"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e005",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000836"
          ],
          "source_quote": "such as enhanced due diligence"
        },
        {
          "relation_id": "r004",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e001",
          "process_element_id": "e004",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000836"
          ],
          "source_quote": "They should also limit the exposure to high-risk customers."
        },
        {
          "relation_id": "r005",
          "kind": "produce",
          "process_element_id": "e004",
          "outcome_element_id": "e006",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000836"
          ],
          "source_quote": "They should also limit the exposure to high-risk customers."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_007"
      ],
      "focal_question": "代理行如何评估MSB的合规计划并确保风险偏好一致？",
      "title": "代理行评估MSB合规计划并确保与风险偏好一致",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Correspondent bank relationship with MSB",
          "evidence_unit_ids": [
            "v7u_N000840"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Assess the soundness of the MSB’s compliance program",
          "evidence_unit_ids": [
            "v7u_N000840"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "Ensure that the MSB’s activities align with the correspondent bank’s risk appetite",
          "evidence_unit_ids": [
            "v7u_N000840"
          ],
          "modality": "required"
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "Alignment with risk appetite",
          "evidence_unit_ids": [
            "v7u_N000840"
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
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000840"
          ],
          "source_quote": "Correspondent banks are required to assess the soundness of the MSB’s compliance program"
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000840"
          ],
          "source_quote": "assess the soundness of the MSB’s compliance program and ensure that the MSB’s activities align with the correspondent bank’s risk appetite."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000840"
          ],
          "source_quote": "ensure that the MSB’s activities align with the correspondent bank’s risk appetite."
        }
      ],
      "split_reason": null
    }
  ],
  "candidate_audit": [
    {
      "candidate_id": "s1c_001",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选仅为MSB的定义条件（若代他人持有资金则为MSB），属静态分类事实，无程序性迁移。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选原文明示MSB须遵守当地AML/CFT要求并可能包括注册和建立合规计划，构成明确的合规执行流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选包含条件性许可要求：若参与MSB服务则必须获得许可，形成完整的许可获取流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选描述不合规可能导致的处罚（罚款、同意令等），属风险后果描述，非业务执行或判断流程。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选明确要求MSB实施额外控制（如EDD）和限制高风险客户敞口，为可执行的程序性动作。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选描述与代理行建立长期信任关系可缓解风险，属策略效果陈述，未包含具体判定或行动步骤。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选要求代理行评估MSB合规计划并确保风险偏好一致，包含强制评估和确保动作，构成评估流程。"
    },
    {
      "candidate_id": "s1c_gap_ch11_s02_hawala_classification",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选为FinCEN将哈瓦拉归类为MSB货币转移商的静态分类描述，无过程性判断或触发后续动作。"
    }
  ],
  "skip_reason": null
}
```
