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

section_id: `CH30-S01`

section_title: `Using reports, guidance notes, and policy papers in your AML/CFT controls`

section_text_with_unit_anchors:

```text
[v7u_N002151|2151] Reports, guidance notes, and policy papers vary in how they can be used for improving AML/CFT controls. Organizations take the following steps to assess the guidance from these sources and apply it to their AML/CFT controls.
ZH: 报告、指引说明和政策文件在改进反洗钱/反恐怖融资控制中的使用方式各异

[v7u_N002152|2152] Review the document in question to identify information relevant to the business’s sector, products, geography, customer base, and delivery channels.
ZH: 审查文件以识别与业务行业、产品、地域、客户群和交付渠道相关的信息

[v7u_N002153|2153] Some information in these documents might not be relevant and can be disregarded.
ZH: 文件中的某些信息可能不相关，可以忽略

[v7u_N002154|2154] Assess whether appropriate controls already exist.
ZH: 评估是否已存在适当的控制措施

[v7u_N002155|2155] For areas where appropriate controls do not exist, conduct further analysis to understand the impact of introducing such controls.
ZH: 对于缺乏适当控制的领域，进行进一步分析以了解引入控制的影响

[v7u_N002156|2156] Distinguish simple changes, with minimum business impact, from more substantial changes that could require resources to deliver, such as internal IT and product resources.
ZH: 区分简单变更（业务影响小）与需要资源（如IT和产品资源）的重大变更

[v7u_N002157|2157] Some changes can impact customer experience or have cost implications, which your organization needs to understand and plan for.
ZH: 某些变更可能影响客户体验或产生成本，组织需了解并规划

[v7u_N002158|2158] Consult with all relevant stakeholders before making a change. Ensure approval for the change from the appropriate person, such as the money laundering reporting officer. Depending on the scope and impact of the change, your organization may need to implement a communication plan and training.
ZH: 变更前需咨询利益相关方、获得适当人员批准，并可能实施沟通计划和培训

[v7u_N002159|2159] Your organization should document that it has applied information from an external report and changed its controls, policies, or procedures.
ZH: 组织应记录已应用外部报告信息并更改控制、政策或程序

[v7u_N002160|2160] Your organization can document changes to policies and procedures within the change log or elsewhere.
ZH: 组织可在变更日志或其他位置记录政策和程序的变更

[v7u_N002161|2161] This allows others, including regulators, to understand why a control exists and allows your organization to demonstrate compliance.
ZH: 合规文档有助于向监管机构证明控制措施的存在与合理性。

[v7u_N002162|2162] The enterprise-wide risk assessment (EWRA) could need adjusting to reflect newly identified risks.
ZH: 企业范围风险评估（EWRA）可能需要根据新识别的风险进行调整。

[v7u_N002163|2163] For example, imagine that a relevant authority issues a report describing a product as high risk and your organization provides this product.
ZH: 监管机构发布报告将某产品描述为高风险，而机构正提供该产品。

[v7u_N002164|2164] The EWRA should reflect this, refer to the source document, and show how your organization has applied controls to mitigate this risk.
ZH: EWRA 必须反映新风险、引用来源文件并展示控制措施。
```

allowed_unit_ids:

```json
[
  "v7u_N002151",
  "v7u_N002152",
  "v7u_N002153",
  "v7u_N002154",
  "v7u_N002155",
  "v7u_N002156",
  "v7u_N002157",
  "v7u_N002158",
  "v7u_N002159",
  "v7u_N002160",
  "v7u_N002161",
  "v7u_N002162",
  "v7u_N002163",
  "v7u_N002164"
]
```

## S2 Process IR

```json
{
  "section_id": "CH30-S01",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001",
        "s1c_002",
        "s1c_003",
        "s1c_004",
        "s1c_005",
        "s1c_006",
        "s1c_007",
        "s1c_008",
        "s1c_009"
      ],
      "focal_question": "如何将外部报告、指引和政策文件应用于AML/CFT控制？",
      "title": "将外部报告、指引和政策文件应用于AML/CFT控制的流程",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "Review the document to identify information relevant to the business’s sector, products, geography, customer base, and delivery channels",
          "evidence_unit_ids": [
            "v7u_N002152"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Disregard information that might not be relevant",
          "evidence_unit_ids": [
            "v7u_N002153"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "Assess whether appropriate controls already exist",
          "evidence_unit_ids": [
            "v7u_N002154"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "For areas where appropriate controls do not exist, conduct further analysis to understand the impact of introducing such controls",
          "evidence_unit_ids": [
            "v7u_N002155"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "action",
          "label": "Distinguish simple changes with minimum business impact from substantial changes that could require resources to deliver (such as internal IT and product resources)",
          "evidence_unit_ids": [
            "v7u_N002156"
          ],
          "modality": null
        },
        {
          "element_id": "e006",
          "role": "action",
          "label": "Understand and plan for changes that could impact customer experience or have cost implications",
          "evidence_unit_ids": [
            "v7u_N002157"
          ],
          "modality": "required"
        },
        {
          "element_id": "e007",
          "role": "action",
          "label": "Before making a change, consult with all relevant stakeholders, ensure approval from the appropriate person (such as the money laundering reporting officer), and depending on scope and impact, implement a communication plan and training",
          "evidence_unit_ids": [
            "v7u_N002158"
          ],
          "modality": null
        },
        {
          "element_id": "e008",
          "role": "action",
          "label": "Document that external report information has been applied and controls, policies, or procedures changed",
          "evidence_unit_ids": [
            "v7u_N002159",
            "v7u_N002160"
          ],
          "modality": "required"
        },
        {
          "element_id": "e009",
          "role": "outcome",
          "label": "Demonstrate compliance to regulators and others",
          "evidence_unit_ids": [
            "v7u_N002161"
          ],
          "modality": null
        },
        {
          "element_id": "e010",
          "role": "action",
          "label": "Adjust the enterprise-wide risk assessment (EWRA) to reflect newly identified risks, refer to the source document, and show how controls mitigate the risk",
          "evidence_unit_ids": [
            "v7u_N002162",
            "v7u_N002164"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "sequence",
          "before_element_id": "e001",
          "after_element_id": "e002",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002152",
            "v7u_N002153"
          ],
          "source_quote": "Review the document in question to identify information... Some information in these documents might not be relevant and can be disregarded."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002153",
            "v7u_N002154"
          ],
          "source_quote": "Some information... can be disregarded. Assess whether appropriate controls already exist."
        },
        {
          "relation_id": "r003",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e003",
          "process_element_id": "e004",
          "condition": "For areas where appropriate controls do not exist",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002155"
          ],
          "source_quote": "For areas where appropriate controls do not exist, conduct further analysis to understand the impact of introducing such controls."
        },
        {
          "relation_id": "r004",
          "kind": "sequence",
          "before_element_id": "e004",
          "after_element_id": "e005",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002155",
            "v7u_N002156"
          ],
          "source_quote": "conduct further analysis... Distinguish simple changes, with minimum business impact, from more substantial changes..."
        },
        {
          "relation_id": "r005",
          "kind": "sequence",
          "before_element_id": "e005",
          "after_element_id": "e006",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002156",
            "v7u_N002157"
          ],
          "source_quote": "Distinguish simple changes... Some changes can impact customer experience or have cost implications, which your organization needs to understand and plan for."
        },
        {
          "relation_id": "r006",
          "kind": "sequence",
          "before_element_id": "e006",
          "after_element_id": "e007",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002157",
            "v7u_N002158"
          ],
          "source_quote": "understand and plan for. Consult with all relevant stakeholders before making a change."
        },
        {
          "relation_id": "r007",
          "kind": "sequence",
          "before_element_id": "e007",
          "after_element_id": "e008",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002158",
            "v7u_N002159"
          ],
          "source_quote": "Consult... before making a change. Your organization should document that it has applied information from an external report and changed its controls..."
        },
        {
          "relation_id": "r008",
          "kind": "produce",
          "process_element_id": "e008",
          "outcome_element_id": "e009",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002161"
          ],
          "source_quote": "This allows others, including regulators, to understand why a control exists and allows your organization to demonstrate compliance."
        },
        {
          "relation_id": "r009",
          "kind": "sequence",
          "before_element_id": "e008",
          "after_element_id": "e010",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002159",
            "v7u_N002162"
          ],
          "source_quote": "Your organization should document... The enterprise-wide risk assessment (EWRA) could need adjusting to reflect newly identified risks."
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
      "reason": "提供审查文件识别相关信息的动作，是流程的起点。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "提供忽略不相关信息的动作，构成筛选步骤。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "提供评估现有控制的动作，并触发后续针对缺失控制的进一步分析。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "提供对控制缺失领域进行影响分析的动作。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "提供区分简单与重大变更的动作。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "提供了解和规划变更影响的动作。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "提供变更前咨询、批准和沟通培训的动作。"
    },
    {
      "candidate_id": "s1c_008",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "提供记录应用和变更的动作，并引出证明合规的结果。"
    },
    {
      "candidate_id": "s1c_009",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "提供调整EWRA以反映新风险的动作。"
    }
  ],
  "skip_reason": null
}
```
