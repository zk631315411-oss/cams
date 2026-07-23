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

allowed_unit_ids:

```json
[
  "v7u_N000781",
  "v7u_N000782",
  "v7u_N000783",
  "v7u_N000784",
  "v7u_N000785",
  "v7u_N000786",
  "v7u_N000787",
  "v7u_N000788",
  "v7u_N000789",
  "v7u_N000790",
  "v7u_N000791",
  "v7u_N000792",
  "v7u_N000793",
  "v7u_N000794",
  "v7u_N000795",
  "v7u_N000796",
  "v7u_N000797",
  "v7u_N000798",
  "v7u_N000799",
  "v7u_N000800",
  "v7u_N000801",
  "v7u_N000802",
  "v7u_N000803",
  "v7u_N000804",
  "v7u_N000805",
  "v7u_N000806",
  "v7u_N000807",
  "v7u_N000808",
  "v7u_N000809",
  "v7u_N000810",
  "v7u_N000811",
  "v7u_N000812"
]
```

## S2 Process IR

```json
{
  "section_id": "CH11-S01",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "如何通过了解合作伙伴的反金融犯罪控制来降低相关风险",
      "title": "了解合作伙伴AFC控制以降低合作风险",
      "card_nature": "control",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "PSP运营依赖银行、金融机构、卡网络、技术提供商和第三方服务商，合作风险通常更高",
          "evidence_unit_ids": [
            "v7u_N000803"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "PSP必须了解合作伙伴的反金融犯罪控制",
          "evidence_unit_ids": [
            "v7u_N000804"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "降低相关风险",
          "evidence_unit_ids": [
            "v7u_N000804"
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
          "condition": "合作风险通常更高",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000803",
            "v7u_N000804"
          ],
          "source_quote": "In contrast, partnership risks are typically higher due to PSPs' operational reliance on banks, financial institutions, card networks, technology providers, and third-party service providers. It is important for PSPs to understand their partners’ AFC controls in order to mitigate the relevant risks."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "condition": null,
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N000804"
          ],
          "source_quote": "It is important for PSPs to understand their partners’ AFC controls in order to mitigate the relevant risks."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "支付服务商如何确保合作伙伴遵守法规以应对监管合规风险",
      "title": "确保合作伙伴遵守法规和数据保护要求",
      "card_nature": "control",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "监管合规风险是支付服务商面临的一个担忧",
          "evidence_unit_ids": [
            "v7u_N000805"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "PSP必须确保合作伙伴遵守法规和数据保护要求（如欧盟支付服务指令中的强客户认证）",
          "evidence_unit_ids": [
            "v7u_N000806"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": "监管合规风险是支付服务商的一个担忧",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000805",
            "v7u_N000806"
          ],
          "source_quote": "One concern is regulatory compliance risk. PSPs must ensure that their partners adhere to regulations and data protection requirements, such as the EU’s Payment Services Directive for strong customer authentication."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "如何根据服务中断等红旗信号判断合作伙伴的交易监控和合规疏漏",
      "title": "依据服务中断等红旗信号判断合作伙伴合规疏漏",
      "card_nature": "risk_indicator",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "服务中断、响应时间长或客服不足",
          "evidence_unit_ids": [
            "v7u_N000809"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "可能存在合作伙伴的交易监控和合规工作疏漏",
          "evidence_unit_ids": [
            "v7u_N000809"
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
          "relation_type": "clue_supports_identification",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000809"
          ],
          "source_quote": "Service outages and issues, such as long response times or inadequate customer support, are red flags, as they might indicate lapses in the partner’s transaction monitoring and compliance efforts."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "发生数据泄露时支付服务商如何响应",
      "title": "发生泄露时PSP负责客户沟通与损害控制",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "发生泄露",
          "evidence_unit_ids": [
            "v7u_N000811"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "PSP负责客户沟通与损害控制",
          "evidence_unit_ids": [
            "v7u_N000811"
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
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000811"
          ],
          "source_quote": "in the event of a breach, the PSP is often responsible for customer communication and damage control."
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
      "reason": "仅描述客户风险的间接性质和义务，不构成程序性或判断性迁移。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选提供了了解合作伙伴AFC控制以降低风险的程序性关系。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选提供了确保合作伙伴遵守法规的程序性动作。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选提供了从红旗信号判断合规疏漏的判断过程。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选提供了泄露事件触发PSP响应动作的程序性关系。"
    },
    {
      "candidate_id": "s1c_gap_ch11_s01_partner_noncompliance_ml",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述合作伙伴不合规可能助长洗钱的风险因果链，不包含PSP的业务判断或程序性动作。"
    },
    {
      "candidate_id": "s1c_gap_ch11_s01_partner_cyber_failure_ml",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述合作伙伴网络安全失败可能导致未授权访问并助长欺诈洗钱的风险因果链，不包含PSP的业务判断或程序性动作。"
    }
  ],
  "skip_reason": null
}
```
