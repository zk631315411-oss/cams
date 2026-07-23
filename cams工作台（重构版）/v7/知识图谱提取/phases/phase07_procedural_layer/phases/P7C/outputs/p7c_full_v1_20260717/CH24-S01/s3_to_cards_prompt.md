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

section_id: `CH24-S01`

section_title: `US AML/CFT regulatory landscape > Bank Secrecy Act`

section_text_with_unit_anchors:

```text
[v7u_N001682|1682] The Bank Secrecy Act (BSA) is the US’s most important AML regulation.
ZH: 《银行保密法》是美国最重要的反洗钱法规

[v7u_N001683|1683] The US implemented it in 1970 in response to criminals using US banks and the financial system for money laundering and other illicit activities.
ZH: 《银行保密法》于1970年实施，旨在打击利用美国银行和金融系统进行的洗钱活动

[v7u_N001684|1684] The BSA introduced significant recordkeeping and reporting obligations for US banks and financial institutions. For instance, the BSA required banks to collect information on customers and their transactions.
ZH: 《银行保密法》为美国银行和金融机构引入了重要的记录保存和报告义务

[v7u_N001685|1685] These obligations helped ensure that law enforcement and supervisory agencies received the financial information and evidence they needed for their investigations and prosecutions.
ZH: 《银行保密法》义务旨在确保执法和监管机构获得调查和起诉所需的金融信息与证据

[v7u_N001686|1686] In 2001, the US extended the scope of the BSA to include counter-terrorist financing obligations introduced by the USA PATRIOT Act.
ZH: 2001年美国通过《爱国者法案》将《银行保密法》范围扩展至反恐怖融资义务

[v7u_N001687|1687] The BSA introduced several reporting requirements:
ZH: 《银行保密法》引入了多项报告要求

[v7u_N001688|1688] Currency transaction reports
ZH: 货币交易报告

[v7u_N001689|1689] Suspicious activity reports
ZH: 可疑活动报告

[v7u_N001690|1690] Foreign bank account reports for US citizens holding foreign accounts
ZH: 持有外国账户的美国公民需提交外国银行账户报告

[v7u_N001691|1691] Currency and monetary instrument reports for cash purchases of monetary instruments
ZH: 现金购买货币工具需提交货币与货币工具报告

[v7u_N001692|1692] The BSA requires obliged entities to develop, implement, and maintain an effective AML program based on five pillars:
ZH: 《银行保密法》要求义务实体基于五大支柱制定、实施和维护有效的反洗钱计划

[v7u_N001693|1693] Incorporate policies, procedures, and internal controls reasonably designed to assure compliance with regulatory requirements.
ZH: 制定合理设计的政策、程序和内部控制以确保合规

[v7u_N001694|1694] Designate an AML officer responsible for the day-to-day activities of the program.
ZH: 指定一名反洗钱官负责计划的日常活动

[v7u_N001695|1695] Provide education and training of employees concerning their responsibilities under the program.
ZH: 为员工提供关于其计划职责的教育和培训

[v7u_N001696|1696] Ensure independent audit to monitor and maintain an adequate program with a risk-based frequency.
ZH: 确保基于风险频率进行独立审计以监控和维护充分计划

[v7u_N001697|1697] Develop an ongoing CDD program using a risk-based approach.
ZH: 使用基于风险的方法制定持续的客户尽职调查计划

[v7u_N001698|1698] The BSA extends to non-US banks, MSBs, and cryptocurrency firms that deal with US customers or utilize the US financial system.
ZH: 《银行保密法》适用于与美国客户交易或使用美国金融体系的非美国银行、货币服务企业和加密货币公司

[v7u_N001699|1699] It requires US-based branches of foreign banks to comply with BSA requirements, as well as MSBs or cryptocurrency firms that engage in transactions with US customers.
ZH: 外国银行美国分行、与美国客户交易的货币服务企业和加密货币公司须遵守《银行保密法》要求

[v7u_N001700|1700] Foreign financial institutions that maintain correspondent bank accounts with US banks are subject to some BSA requirements, including recordkeeping and the obligation to provide records in response to requests from US authorities.
ZH: 在美国银行持有代理账户的外国金融机构须遵守部分《银行保密法》要求，包括记录保存和应要求提供记录
```

allowed_unit_ids:

```json
[
  "v7u_N001682",
  "v7u_N001683",
  "v7u_N001684",
  "v7u_N001685",
  "v7u_N001686",
  "v7u_N001687",
  "v7u_N001688",
  "v7u_N001689",
  "v7u_N001690",
  "v7u_N001691",
  "v7u_N001692",
  "v7u_N001693",
  "v7u_N001694",
  "v7u_N001695",
  "v7u_N001696",
  "v7u_N001697",
  "v7u_N001698",
  "v7u_N001699",
  "v7u_N001700"
]
```

## S2 Process IR

```json
{
  "section_id": "CH24-S01",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "义务实体如何基于五大支柱制定和实施有效的反洗钱计划？",
      "title": "基于五大支柱的AML计划要求",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "制定、实施和维护有效的反洗钱计划 (develop, implement, and maintain an effective AML program)",
          "evidence_unit_ids": [
            "v7u_N001692"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "input",
          "label": "制定合理设计的政策、程序和内部控制以确保合规 (Incorporate policies, procedures, and internal controls reasonably designed to assure compliance)",
          "evidence_unit_ids": [
            "v7u_N001693"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "input",
          "label": "指定一名反洗钱官负责计划的日常活动 (Designate an AML officer responsible for day-to-day activities)",
          "evidence_unit_ids": [
            "v7u_N001694"
          ],
          "modality": "required"
        },
        {
          "element_id": "e004",
          "role": "input",
          "label": "为员工提供关于其计划职责的教育和培训 (Provide education and training of employees)",
          "evidence_unit_ids": [
            "v7u_N001695"
          ],
          "modality": "required"
        },
        {
          "element_id": "e005",
          "role": "input",
          "label": "确保基于风险频率进行独立审计以监控和维护充分计划 (Ensure independent audit to monitor and maintain an adequate program with a risk-based frequency)",
          "evidence_unit_ids": [
            "v7u_N001696"
          ],
          "modality": "required"
        },
        {
          "element_id": "e006",
          "role": "input",
          "label": "使用基于风险的方法制定持续的客户尽职调查计划 (Develop an ongoing CDD program using a risk-based approach)",
          "evidence_unit_ids": [
            "v7u_N001697"
          ],
          "modality": "required"
        },
        {
          "element_id": "e007",
          "role": "outcome",
          "label": "有效的反洗钱计划 (effective AML program)",
          "evidence_unit_ids": [
            "v7u_N001692"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e001",
          "auxiliary_element_id": "e002",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001693"
          ],
          "source_quote": "Incorporate policies, procedures, and internal controls reasonably designed to assure compliance with regulatory requirements."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e001",
          "auxiliary_element_id": "e003",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001694"
          ],
          "source_quote": "Designate an AML officer responsible for the day-to-day activities of the program."
        },
        {
          "relation_id": "r003",
          "kind": "reference",
          "process_element_id": "e001",
          "auxiliary_element_id": "e004",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001695"
          ],
          "source_quote": "Provide education and training of employees concerning their responsibilities under the program."
        },
        {
          "relation_id": "r004",
          "kind": "reference",
          "process_element_id": "e001",
          "auxiliary_element_id": "e005",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001696"
          ],
          "source_quote": "Ensure independent audit to monitor and maintain an adequate program with a risk-based frequency."
        },
        {
          "relation_id": "r005",
          "kind": "reference",
          "process_element_id": "e001",
          "auxiliary_element_id": "e006",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001697"
          ],
          "source_quote": "Develop an ongoing CDD program using a risk-based approach."
        },
        {
          "relation_id": "r006",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e007",
          "relation_type": "component_assembles_product",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001692"
          ],
          "source_quote": "The BSA requires obliged entities to develop, implement, and maintain an effective AML program based on five pillars:"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002",
        "s1c_003"
      ],
      "focal_question": "哪些非美国实体须受BSA管辖并遵守其要求？",
      "title": "BSA对非美国实体的适用",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "decision",
          "label": "受BSA管辖并须遵守其要求 (Subject to BSA and must comply with BSA requirements)",
          "evidence_unit_ids": [
            "v7u_N001698",
            "v7u_N001699"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "context",
          "label": "非美国银行、货币服务企业、加密货币公司 (Non-US banks, MSBs, and cryptocurrency firms)",
          "evidence_unit_ids": [
            "v7u_N001698"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "context",
          "label": "外国银行美国分行 (US-based branches of foreign banks)",
          "evidence_unit_ids": [
            "v7u_N001699"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "context",
          "label": "与美国客户交易的货币服务企业或加密货币公司 (MSBs or cryptocurrency firms engaging in transactions with US customers)",
          "evidence_unit_ids": [
            "v7u_N001699"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e002",
          "process_element_id": "e001",
          "condition": "dealing with US customers or utilizing the US financial system",
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001698"
          ],
          "source_quote": "The BSA extends to non-US banks, MSBs, and cryptocurrency firms that deal with US customers or utilize the US financial system."
        },
        {
          "relation_id": "r002",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e003",
          "process_element_id": "e001",
          "condition": null,
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001699"
          ],
          "source_quote": "It requires US-based branches of foreign banks to comply with BSA requirements, as well as MSBs or cryptocurrency firms that engage in transactions with US customers."
        },
        {
          "relation_id": "r003",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e004",
          "process_element_id": "e001",
          "condition": "engaging in transactions with US customers",
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001699"
          ],
          "source_quote": "It requires ... MSBs or cryptocurrency firms that engage in transactions with US customers to comply with BSA requirements."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "持有美国银行代理账户的外国金融机构承担哪些BSA义务？",
      "title": "持有代理账户的外国金融机构的部分BSA义务",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "在美国银行持有代理账户的外国金融机构 (Foreign financial institutions that maintain correspondent bank accounts with US banks)",
          "evidence_unit_ids": [
            "v7u_N001700"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "受部分BSA要求约束 (subject to some BSA requirements)",
          "evidence_unit_ids": [
            "v7u_N001700"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "包括记录保存和应要求提供记录的义务 (including recordkeeping and the obligation to provide records in response to requests)",
          "evidence_unit_ids": [
            "v7u_N001700"
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
          "condition": "maintains correspondent bank accounts with US banks",
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001700"
          ],
          "source_quote": "Foreign financial institutions that maintain correspondent bank accounts with US banks are subject to some BSA requirements, including recordkeeping and the obligation to provide records in response to requests from US authorities."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": "standard_transmits_requirement",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001700"
          ],
          "source_quote": "including recordkeeping and the obligation to provide records in response to requests from US authorities."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_gap_ch24_s01_recordkeeping_obligation"
      ],
      "focal_question": "BSA如何通过报告义务确保执法机构获取信息？",
      "title": "BSA引入的记录保存和报告义务及执法获取信息目的",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "要求美国银行收集客户和交易信息 (required US banks to collect information on customers and their transactions)",
          "evidence_unit_ids": [
            "v7u_N001684"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "旨在确保执法和监管机构获得调查和起诉所需的金融信息与证据 (helped ensure that law enforcement and supervisory agencies received the financial information and evidence needed for investigations and prosecutions)",
          "evidence_unit_ids": [
            "v7u_N001685"
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
          "relation_type": "standard_transmits_requirement",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001685"
          ],
          "source_quote": "These obligations helped ensure that law enforcement and supervisory agencies received the financial information and evidence they needed for their investigations and prosecutions."
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
      "reason": "该候选描述了基于五大支柱的AML计划要求，构成执行程序。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "候选提供了非美国实体受BSA管辖的条件判断，构成法律适用判断。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "候选包括外国银行美国分行及MSB等实体的合规要求，合并至非美国实体适用判断episode。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "候选描述了持有代理账户的外国金融机构的部分BSA义务，构成法律适用和具体义务判断。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s01_recordkeeping_obligation",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "候选描述了BSA引入的记录保存和报告义务，要求银行收集信息，旨在确保执法获取信息，构成程序性动作和目的。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s01_reporting_requirements",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "候选仅列出报告类型，是静态知识分类，不包含任何业务过程或判断。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s01_extension_ctf",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "候选描述BSA立法范围的历史扩展，不涉及机构的业务程序或判断。"
    }
  ],
  "skip_reason": null
}
```
