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

section_id: `CH02-S04`

section_title: `Types of financial crime > Case example: FullTechGlobal corruption scandal`

section_text_with_unit_anchors:

```text
[v7u_N000131|131] Sophie is an AFC manager in the compliance department of a financial institution that has some global businesses as its customers.
ZH: Sophie 是金融机构合规部的金融犯罪防控经理。

[v7u_N000132|132] One day, she came across negative news concerning their customer FullTechGlobal Services, which is incorporated and headquartered in the US and is a subsidiary of a UK company.
ZH: Sophie 发现客户 FullTechGlobal Services 的负面新闻。

[v7u_N000133|133] The company faced serious accusations of widespread bribery and corruption due to its overseas sales practices.
ZH: 该公司因海外销售行为面临广泛贿赂和腐败的严重指控。

[v7u_N000134|134] This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010.
ZH: 此事引发对《英国反贿赂法》域外条款的关切。

[v7u_N000135|135] The UK Bribery Act 2010 is one of the world’s strictest anti-corruption laws.
ZH: 《英国反贿赂法》是全球最严格的反腐败法律之一。

[v7u_N000136|136] It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location.
ZH: 该法适用于任何与英国有关联的公司，母公司需对子公司腐败行为负责。

[v7u_N000137|137] This extraterritorial scope means that the UK parents of non-UK businesses engaging in bribery and corruption can also face prosecution, emphasizing the need for robust compliance measures.
ZH: 域外管辖意味着非英国企业的英国母公司也可能因贿赂腐败被起诉。

[v7u_N000138|138] Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts.
ZH: FullTechGlobal 在高风险司法管辖区战略性地雇佣中间人获取合同。

[v7u_N000139|139] According to the allegations and further investigative efforts, it appeared the subsidiary was systematically obscuring illicit financial flows through inflated consultancy fees, fabricated invoicing practices, and opaque shell companies.
ZH: 子公司通过虚增咨询费、伪造发票和壳公司掩盖非法资金流动。

[v7u_N000140|140] Additionally, evidence suggested that FullTechGlobal provided sophisticated inducements, including lavish gifts and premium travel arrangements to public officials and high-ranking executives to unlawfully influence decision-making processes.
ZH: FullTechGlobal 向公职人员和高级管理人员提供奢华礼品和旅行安排以影响决策。

[v7u_N000141|141] She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities.
ZH: FullTechGlobal腐败案审计发现内部控制缺陷和监管不足

[v7u_N000142|142] Bribery was identified as the predicate crime, leading to the laundering of illicit funds through complex financial networks designed to evade regulatory scrutiny and forensic tracing efforts.
ZH: 贿赂作为上游犯罪，通过复杂金融网络洗钱

[v7u_N000143|143] Given these findings, the regulatory implications under the UK Bribery Act 2010 are profound. FullTechGlobal Services faces severe financial penalties, increased scrutiny from international regulators, and potential criminal liability for both the subsidiary and the parent company, including its executives.
ZH: FullTechGlobal面临英国《反贿赂法》下的严厉处罚和监管审查

[v7u_N000144|144] As an AFC manager, she recognizes that her institution needs to maintain compliance integrity and mitigate bribery and corruption risks in its dealings with global businesses such as FullTechGlobal Services.
ZH: 金融犯罪防控经理有义务维护合规诚信并降低贿赂风险
```

allowed_unit_ids:

```json
[
  "v7u_N000131",
  "v7u_N000132",
  "v7u_N000133",
  "v7u_N000134",
  "v7u_N000135",
  "v7u_N000136",
  "v7u_N000137",
  "v7u_N000138",
  "v7u_N000139",
  "v7u_N000140",
  "v7u_N000141",
  "v7u_N000142",
  "v7u_N000143",
  "v7u_N000144"
]
```

## S2 Process IR

```json
{
  "section_id": "CH02-S04",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "FullTechGlobal的海外贿赂指控是否引发英国反贿赂法域外适用及母公司责任？",
      "title": "英国反贿赂法域外条款适用关切与法律后果",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "FullTechGlobal面临海外贿赂指控（引发域外条款关切）",
          "evidence_unit_ids": [
            "v7u_N000134"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "英国《2010年反贿赂法》域外条款：适用于任何有英国关联的公司，母公司对子公司腐败行为负责，不论地点",
          "evidence_unit_ids": [
            "v7u_N000136",
            "v7u_N000137"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "decision",
          "label": "引发英国反贿赂法域外条款的适用关切",
          "evidence_unit_ids": [
            "v7u_N000134"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "英国母公司可能面临起诉，需要加强合规措施",
          "evidence_unit_ids": [
            "v7u_N000137"
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
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000134"
          ],
          "source_quote": "This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000136",
            "v7u_N000137"
          ],
          "source_quote": "It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000137"
          ],
          "source_quote": "This extraterritorial scope means that the UK parents of non-UK businesses engaging in bribery and corruption can also face prosecution, emphasizing the need for robust compliance measures."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "Sophie的初步调查发现了哪些贿赂行为？",
      "title": "初步调查发现FullTechGlobal的贿赂行为",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "Sophie的初步调查",
          "evidence_unit_ids": [
            "v7u_N000138"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "发现FullTechGlobal战略性地雇佣高风险司法管辖区中间人以获取合同",
          "evidence_unit_ids": [
            "v7u_N000138"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "子公司通过虚增咨询费、伪造发票和壳公司系统性地掩盖非法资金流动",
          "evidence_unit_ids": [
            "v7u_N000139"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "FullTechGlobal向公职人员和高管提供奢华礼品和旅行安排以不当影响决策",
          "evidence_unit_ids": [
            "v7u_N000140"
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
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000138"
          ],
          "source_quote": "Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000139"
          ],
          "source_quote": "According to the allegations and further investigative efforts, it appeared the subsidiary was systematically obscuring illicit financial flows through inflated consultancy fees, fabricated invoicing practices, and opaque shell companies."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e004",
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000140"
          ],
          "source_quote": "Additionally, evidence suggested that FullTechGlobal provided sophisticated inducements, including lavish gifts and premium travel arrangements to public officials and high-ranking executives to unlawfully influence decision-making processes."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "Sophie的后续审计发现了哪些内部控制缺陷？",
      "title": "审计发现FullTechGlobal内部控制缺陷",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "Sophie的后续调查与审计",
          "evidence_unit_ids": [
            "v7u_N000141"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "审计发现FullTechGlobal的ABC框架和内部控制存在缺陷：内控机制不足和监督不力，导致腐败活动长期未被发现",
          "evidence_unit_ids": [
            "v7u_N000141"
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
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000141"
          ],
          "source_quote": "She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities."
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
      "reason": "该候选提供了触发域外法律适用关切的指控、适用标准和法律后果，构成法律适用判断流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了Sophie的初步调查过程及发现的多种贿赂行为，构成调查发现流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述了Sophie后续审计发现内控缺陷的过程，构成审查发现流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选描述贿赂被认定为上游犯罪导致洗钱，是犯罪机制描述，不涉及机构的业务判断或程序。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选描述FullTechGlobal面临的法律后果，是静态法律后果陈述，没有触发业务程序。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选描述Sophie主观认识到机构需要维护合规，没有原文明示的业务动作或判断过程。"
    }
  ],
  "skip_reason": null
}
```
