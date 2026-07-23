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

为每个 element 从以下 25 种类型中精确选择。依据：role、relation kind、邻接关系、label 语义、card_nature、原文上下文。

**可用 node_type：**

entry（context role 专用）：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`

process（action/decision role 专用）：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`

exit（outcome role 专用）：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`

auxiliary（input/standard role 专用）：`input, standard`

**role → node_type 兼容规则：**

```text
context   → E1-E8（根据具体语义：事件→E1、对象进入→E2、阈值→E3、交接→E4、周期→E5、异常→E6、命令→E7、发现/判断→E8）
input     → input（唯一）
standard  → standard（唯一）
action    → P1-P2、P4-P10（不可用 P3）
decision  → P1_assessment、P3_branch_routing、P10_sufficiency
outcome   → X1-X7（根据具体语义：分类→X1、产物→X2、状态变更→X3、交接→X4、配置变更→X5、终止→X6、持续义务→X7）
```

**确定性规则（必须遵循）：**
- role=decision 且有 >=2 条 branch 出边 → `P3_branch_routing`
- role=input → `input`
- role=standard → `standard`

### 步骤 3：构建 flow_nodes + flow_edges

**flow_node（每个 element 对应一个 node）：**
- `node_id`：在 episode 内唯一
- `node_category`：entry(E-)、process(P-)、exit(X-)、auxiliary(input/standard)
- `node_type`：步骤 2 确定的值
- `label`：保留 element.label 原文
- `evidence_unit_ids`：element 的 evidence_unit_ids
- `evidence_strength`：固定 `explicit`
- `modality`：element 的 modality（可选）

**flow_edge（每个 relation 对应一条 edge，节点引用 node_id）：**

| relation kind | edge_type |
|---|---|
| `trigger` | `PRECEDES` |
| `sequence` | `PRECEDES` |
| `reference` | `REFERENCES`（process → auxiliary） |
| `produce` | `PRODUCES` |
| `branch` | `DECIDES` |
| `feedback` | `FEEDBACK` |

每条 flow_edge 必填：`edge_id, edge_type, source, target, evidence_unit_ids`。
- `condition`：有则必填（trigger_mode=condition 或 branch 必须有）
- `relation_type`：可选，从 12 种中选择
- `qualifier`：可选，`aimed_to/may_lead_to/helps_achieve`
- `source_quote`：可选

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

section_id: `CH26-S08`

section_title: `Other laws and regulations that impact organizations > ESG regulations`

section_text_with_unit_anchors:

```text
[v7u_N002105|2105] “Environmental, social, and governance” (ESG) refers to a framework organizations use to steer their business practices in accordance with the objectives of sustainable development.
ZH: ESG框架定义：环境、社会和治理

[v7u_N002106|2106] “Environmental” refers to an organization’s impact on the planet.
ZH: ESG中“环境”指组织对地球的影响

[v7u_N002107|2107] “Social” refers to an organization’s relationship with various stakeholders, including employees, customers, and communities within which they operate.
ZH: ESG中“社会”指组织与利益相关者的关系

[v7u_N002108|2108] “Governance” refers to how factors such as leadership, board composition, and transparency govern an organization.
ZH: ESG中“治理”指领导力、董事会构成和透明度

[v7u_N002109|2109] The UN has established a number of initiatives to advance ESG goals on a global basis.
ZH: 联合国设立多项倡议推动全球ESG目标

[v7u_N002110|2110] A widely known initiative is its Sustainable Development Goals, which provide a framework of 17 objectives to address poverty, inequality, and environmental threats while promoting peace and prosperity.
ZH: 联合国可持续发展目标提供17项目标框架

[v7u_N002111|2111] All UN Member States adopted the goals, and many organizations align their strategies with them.
ZH: 所有联合国会员国采纳可持续发展目标

[v7u_N002112|2112] Other ESG-related UN initiatives include the UN Guiding Principles on Business and Human Rights, the UN Environment Program Finance Initiative, and the UN Global Compact, an initiative to encourage businesses to support a wide range of ESG priorities.
ZH: 其他ESG相关联合国倡议包括UNGP、UNEP FI和UNGC

[v7u_N002113|2113] Although ESG regulations vary across jurisdictions, trends include increased mandatory disclosure, accountability, and transparency in organizational practices. The scope of ESG ranges from climate change to corporate governance to human rights. ESG considerations intersect with AML/CFT with respect to:
ZH: ESG法规趋势与反洗钱/反恐怖融资交叉领域概述

[v7u_N002114|2114] Environmental crime: This includes, for example, noncompliance with antipollution rules to achieve economic benefits or the exploitation of illegal mining. Financial crime such as bribery and corruption of local officials might be involved as part of the enterprise.
ZH: 环境犯罪涉及违反环保规则和非法采矿，常伴随贿赂和腐败

[v7u_N002115|2115] Social impact: This includes the exploitation of forced labor and corruption to achieve business objectives.
ZH: 社会影响包括强迫劳动和腐败以实现商业目标

[v7u_N002116|2116] Governance and compliance: This includes governance failures that result in a failure to prevent financial crime within organizations; regulatory enforcement actions all over the world have demonstrated their impact.
ZH: 治理失败导致未能预防金融犯罪，全球监管执法行动已显示其影响

[v7u_N002117|2117] ESG and AML/CFT regulations are converging as global regulatory frameworks continue to evolve to include sustainable business practices and financial crime prevention.
ZH: ESG与反洗钱/反恐怖融资法规正趋于融合

[v7u_N002118|2118] Strong governance frameworks under ESG regulation help prevent and deter corruption, fraud, and other illicit financial activity.
ZH: ESG治理框架有助于预防和阻止腐败、欺诈等金融犯罪

[v7u_N002119|2119] In addition, ESG’s emphasis on social responsibility can help identify certain threats to human rights that might have links to financial crimes.
ZH: ESG社会责任有助于识别与金融犯罪相关的人权威胁

[v7u_N002120|2120] For example, money laundering often involves the proceeds of human trafficking and modern slavery.
ZH: 洗钱常涉及人口贩运和现代奴隶制的收益

[v7u_N002121|2121] By integrating ESG principles into AML/CFT compliance, organizations are better suited to identify and mitigate such risks.
ZH: 将ESG原则融入反洗钱/反恐怖融资合规有助于识别和缓解风险

[v7u_N002122|2122] Both ESG and AML/CFT compliance frameworks depend on a risk-based approach to enable effective compliance and risk mitigation.
ZH: ESG与反洗钱/反恐怖融资均依赖风险为本方法实现有效合规

[v7u_N002123|2123] For ESG regulation, organizations should identify, assess, and manage risks particular to the elements of ESG, such as environmental impact, social responsibility, and organizational governance integrity.
ZH: 组织应识别、评估和管理ESG相关风险，包括环境影响、社会责任和治理诚信

[v7u_N002124|2124] The risk-based approach helps organizations prioritize resources, focus, and efforts on high-risk areas, such as industries with very high carbon emissions or locations vulnerable to human rights violations.
ZH: 风险为本方法帮助组织将资源优先投入高风险领域，如高碳排放行业或人权风险地区

[v7u_N002125|2125] Similarly, AML/CFT regulations require organizations to assess and manage risks particular to money laundering and terrorist financing.
ZH: 反洗钱/反恐怖融资法规要求组织评估和管理洗钱与恐怖融资风险

[v7u_N002126|2126] The adoption of a risk-based approach enables organizations to prioritize resources on high-risk clients, jurisdictions, and services, ensuring that compliance levels are proportionate to the level of risk.
ZH: 采用风险为本方法使组织能够优先对高风险客户、司法管辖区和服务投入资源

[v7u_N002127|2127] Both ESG and AML/CFT frameworks require ongoing due diligence, monitoring, and responsiveness to emerging risks.
ZH: ESG与反洗钱/反恐怖融资框架均要求持续尽职调查、监控和应对新兴风险
```

allowed_unit_ids:

```json
[
  "v7u_N002105",
  "v7u_N002106",
  "v7u_N002107",
  "v7u_N002108",
  "v7u_N002109",
  "v7u_N002110",
  "v7u_N002111",
  "v7u_N002112",
  "v7u_N002113",
  "v7u_N002114",
  "v7u_N002115",
  "v7u_N002116",
  "v7u_N002117",
  "v7u_N002118",
  "v7u_N002119",
  "v7u_N002120",
  "v7u_N002121",
  "v7u_N002122",
  "v7u_N002123",
  "v7u_N002124",
  "v7u_N002125",
  "v7u_N002126",
  "v7u_N002127"
]
```

## S2 Process IR

```json
{
  "section_id": "CH26-S08",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "如何通过整合ESG原则提高风险识别和缓释能力？",
      "title": "整合ESG原则至AML/CFT合规以增强风险识别与缓释",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "organizations integrate ESG principles into AML/CFT compliance",
          "evidence_unit_ids": [
            "v7u_N002121"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "organizations are better suited to identify and mitigate such risks",
          "evidence_unit_ids": [
            "v7u_N002121"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "relation_type": null,
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e001",
          "outcome_element_id": "e002",
          "condition": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002121"
          ],
          "source_quote": "By integrating ESG principles into AML/CFT compliance, organizations are better suited to identify and mitigate such risks."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "根据ESG法规，组织应如何管理ESG风险？",
      "title": "ESG法规要求组织识别、评估和管理ESG相关风险",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "ESG regulation",
          "evidence_unit_ids": [
            "v7u_N002123"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "organizations should identify, assess, and manage risks particular to the elements of ESG",
          "evidence_unit_ids": [
            "v7u_N002123"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "relation_type": "standard_constrains_action",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e002",
          "auxiliary_element_id": "e001",
          "condition": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002123"
          ],
          "source_quote": "For ESG regulation, organizations should identify, assess, and manage risks particular to the elements of ESG..."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "根据AML/CFT法规，组织应如何管理洗钱和恐怖融资风险？",
      "title": "AML/CFT法规要求组织评估和管理洗钱与恐怖融资风险",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "AML/CFT regulations",
          "evidence_unit_ids": [
            "v7u_N002125"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "organizations are required to assess and manage risks particular to money laundering and terrorist financing",
          "evidence_unit_ids": [
            "v7u_N002125"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "relation_type": "standard_constrains_action",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e002",
          "auxiliary_element_id": "e001",
          "condition": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002125"
          ],
          "source_quote": "Similarly, AML/CFT regulations require organizations to assess and manage risks particular to money laundering and terrorist financing."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "ESG和AML/CFT框架要求组织如何持续管理新兴风险？",
      "title": "ESG和AML/CFT框架要求持续尽职调查、监控和应对新兴风险",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "ESG and AML/CFT frameworks",
          "evidence_unit_ids": [
            "v7u_N002127"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "organizations are required to perform ongoing due diligence, monitoring, and responsiveness to emerging risks",
          "evidence_unit_ids": [
            "v7u_N002127"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "relation_type": "standard_constrains_action",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e002",
          "auxiliary_element_id": "e001",
          "condition": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002127"
          ],
          "source_quote": "Both ESG and AML/CFT frameworks require ongoing due diligence, monitoring, and responsiveness to emerging risks."
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
      "reason": "描述ESG治理框架预防和阻止金融犯罪的机制性作用，非组织执行的程序或判断。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述ESG社会责任强调识别人权威胁的因果关系，无明确业务动作或流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "包含明确的业务动作（整合ESG原则）及其结果（增强风险识别缓释能力），构成流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "包含ESG法规规定的风险识别、评估和管理义务，属于程序性要求。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "包含AML/CFT法规要求的风险评估和管理义务，为明确程序。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "提出持续尽职调查、监控和应对的合规要求，构成持续性程序。"
    },
    {
      "candidate_id": "s1c_gap_ch26_s08_rba_dependency",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "仅陈述ESG与AML/CFT框架与风险为本方法的依赖关系，无机构可执行的流程。"
    },
    {
      "candidate_id": "s1c_gap_ch26_s08_esg_prioritize",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述风险为本方法帮助组织优先投入资源的一般性益处，非具体程序。"
    },
    {
      "candidate_id": "s1c_gap_ch26_s08_aml_prioritize",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述采用风险为本方法使组织能优先资源和确保比例的能力，未规定具体执行动作。"
    }
  ],
  "skip_reason": null
}
```
