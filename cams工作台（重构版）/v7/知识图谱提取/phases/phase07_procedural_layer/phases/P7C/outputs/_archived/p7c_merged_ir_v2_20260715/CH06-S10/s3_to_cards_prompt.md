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

section_id: `CH06-S10`

section_title: `Money Laundering Risks in Financial Services > Control and ownership for AML compliance`

section_text_with_unit_anchors:

```text
[v7u_N000483|483] Control and ownership play a vital role in AML efforts, as they can often be obscured or concealed, allowing bad actors to disguise criminal activities and facilitate financial crime.
ZH: 控制权和所有权在反洗钱工作中至关重要

[v7u_N000484|484] A beneficial owner (BO) is defined as an individual or entity that possesses ownership of a legal entity, either through shareholding or other means.
ZH: 受益所有人（BO）的定义：通过持股或其他方式拥有法律实体的个人或实体

[v7u_N000485|485] In contrast, the ultimate beneficial owner (UBO) refers specifically to one or more natural persons who ultimately owns a substantial percentage of shareholding.
ZH: 最终受益所有人（UBO）的定义：最终持有重大比例股份的自然人

[v7u_N000486|486] It is important to note that a BO might appear to have ownership of a company but might not control the company. Conversely, a UBO might not directly hold shares but does exert ultimate control over it.
ZH: BO 可能拥有所有权但不控制公司，UBO 可能不直接持股但实施最终控制

[v7u_N000487|487] This distinction is crucial when it comes to regulatory requirements surrounding ownership structures.
ZH: BO 与 UBO 的区别对所有权结构的监管要求至关重要

[v7u_N000488|488] When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer.
ZH: 监管要求审查所有权结构时必须识别客户的 UBO

[v7u_N000489|489] For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more. That means you need to know every entity or individual who owns at least 25% of a customer.
ZH: 多数司法管辖区要求识别持股 25% 或以上的受益所有人

[v7u_N000490|490] Your organization will set the appropriate threshold using a riskbased approach.
ZH: 机构应采用风险为本的方法设定受益所有权阈值

[v7u_N000491|491] For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5% for customers who pose a significantly higher risk.
ZH: 高风险客户的受益所有人阈值可能低至 10% 甚至 5%

[v7u_N000492|492] For example, high-risk financial institutions with correspondent banking relationships in a high-risk jurisdiction might set their threshold at 5%.
ZH: 示例：高风险司法管辖区的代理行关系可能设定 5% 的阈值

[v7u_N000493|493] In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership.
ZH: 识别 UBO 需要同时考虑直接和间接持股

[v7u_N000494|494] Individual D owns 10% of Company A directly. They also own 72% of Company A indirectly, as they own 90% of shares of Company B, which owns 80% of Company A. Individual D is then considered a UBO with 82% shareholding of Company A.
ZH: 示例：个人 D 通过直接和间接持股合计 82%，成为 UBO

[v7u_N000495|495] Individual C, who owns 10% of Company A directly and an additional 8% indirectly via their 10% ownership of Company B, is not a UBO.
ZH: 示例：个人 C 直接持股 10% 加间接持股 8%，未达到 UBO 标准

[v7u_N000496|496] In companies where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified. This allows you to understand who is in control of the decision-making in the company when natural individual UBOs are not present.
ZH: 无自然人受益所有人时，应识别并核实控制人或名义受益所有人

[v7u_N000497|497] For example, for a company that is publicly listed on the stock exchange and has thousands of shareholders, a notional beneficial owner could be the president or chief executive officer, or equivalent.
ZH: 示例：上市公司可将总裁或 CEO 作为名义受益所有人
```

allowed_unit_ids:

```json
[
  "v7u_N000483",
  "v7u_N000484",
  "v7u_N000485",
  "v7u_N000486",
  "v7u_N000487",
  "v7u_N000488",
  "v7u_N000489",
  "v7u_N000490",
  "v7u_N000491",
  "v7u_N000492",
  "v7u_N000493",
  "v7u_N000494",
  "v7u_N000495",
  "v7u_N000496",
  "v7u_N000497"
]
```

## S2 Process IR

```json
{
  "section_id": "CH06-S10",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001",
        "s1c_002"
      ],
      "focal_question": "如何依据持股比例和阈值识别最终受益所有人（UBO）？",
      "title": "依据直接和间接持股及适用阈值认定 UBO",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "审查所有权结构",
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "合计直接和间接持股比例",
          "evidence_unit_ids": [
            "v7u_N000493",
            "v7u_N000494",
            "v7u_N000495"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "input",
          "label": "直接和间接持股数据",
          "evidence_unit_ids": [
            "v7u_N000493",
            "v7u_N000494",
            "v7u_N000495"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "standard",
          "label": "受益所有权识别阈值（通常为25%或以上）",
          "evidence_unit_ids": [
            "v7u_N000489"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "decision",
          "label": "判断合计持股比例是否达到阈值",
          "evidence_unit_ids": [
            "v7u_N000494",
            "v7u_N000495"
          ],
          "modality": null
        },
        {
          "element_id": "e006",
          "role": "outcome",
          "label": "认定为最终受益所有人（UBO）",
          "evidence_unit_ids": [
            "v7u_N000494"
          ],
          "modality": null
        },
        {
          "element_id": "e007",
          "role": "outcome",
          "label": "不认定为最终受益所有人（UBO）",
          "evidence_unit_ids": [
            "v7u_N000495"
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
          "condition": "审查所有权结构时",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "source_quote": "When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000493",
            "v7u_N000494",
            "v7u_N000495"
          ],
          "source_quote": "In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership."
        },
        {
          "relation_id": "r003",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000489"
          ],
          "source_quote": "For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more."
        },
        {
          "relation_id": "r004",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e005",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000494",
            "v7u_N000495"
          ],
          "source_quote": "Individual D owns 10% of Company A directly. They also own 72% of Company A indirectly... Individual D is then considered a UBO with 82% shareholding of Company A."
        },
        {
          "relation_id": "r005",
          "kind": "reference",
          "process_element_id": "e005",
          "auxiliary_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000489"
          ],
          "source_quote": "For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more."
        },
        {
          "relation_id": "r006",
          "kind": "branch",
          "decision_element_id": "e005",
          "target_element_id": "e006",
          "condition": "合计持股比例达到阈值",
          "relation_type": "branch_condition_routes_path",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000494"
          ],
          "source_quote": "Individual D owns 10% of Company A directly. They also own 72% of Company A indirectly... Individual D is then considered a UBO with 82% shareholding of Company A."
        },
        {
          "relation_id": "r007",
          "kind": "branch",
          "decision_element_id": "e005",
          "target_element_id": "e007",
          "condition": "合计持股比例未达到阈值",
          "relation_type": "branch_condition_routes_path",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000495"
          ],
          "source_quote": "Individual C, who owns 10% of Company A directly and an additional 8% indirectly... is not a UBO."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "机构如何采用风险为本方法设定受益所有权阈值？",
      "title": "采用风险为本方法设定受益所有权阈值",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e201",
          "role": "action",
          "label": "设定受益所有权阈值",
          "evidence_unit_ids": [
            "v7u_N000490"
          ],
          "modality": "required"
        },
        {
          "element_id": "e202",
          "role": "standard",
          "label": "风险为本方法",
          "evidence_unit_ids": [
            "v7u_N000490"
          ],
          "modality": null
        },
        {
          "element_id": "e203",
          "role": "decision",
          "label": "根据客户风险水平确定适用阈值",
          "evidence_unit_ids": [
            "v7u_N000491",
            "v7u_N000492"
          ],
          "modality": null
        },
        {
          "element_id": "e204",
          "role": "outcome",
          "label": "高风险客户适用阈值10%",
          "evidence_unit_ids": [
            "v7u_N000491"
          ],
          "modality": "risky"
        },
        {
          "element_id": "e205",
          "role": "outcome",
          "label": "显著更高风险客户适用阈值5%",
          "evidence_unit_ids": [
            "v7u_N000491"
          ],
          "modality": "risky"
        }
      ],
      "relations": [
        {
          "relation_id": "r201",
          "kind": "reference",
          "process_element_id": "e201",
          "auxiliary_element_id": "e202",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000490"
          ],
          "source_quote": "Your organization will set the appropriate threshold using a riskbased approach."
        },
        {
          "relation_id": "r202",
          "kind": "sequence",
          "before_element_id": "e201",
          "after_element_id": "e203",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000490",
            "v7u_N000491"
          ],
          "source_quote": "Your organization will set the appropriate threshold using a riskbased approach. For certain high-risk customers, the beneficial ownership threshold might be as low as 10%..."
        },
        {
          "relation_id": "r203",
          "kind": "branch",
          "decision_element_id": "e203",
          "target_element_id": "e204",
          "condition": "客户被分类为高风险",
          "relation_type": "branch_condition_routes_path",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000491"
          ],
          "source_quote": "For certain high-risk customers, the beneficial ownership threshold might be as low as 10%..."
        },
        {
          "relation_id": "r204",
          "kind": "branch",
          "decision_element_id": "e203",
          "target_element_id": "e205",
          "condition": "客户被分类为显著更高风险",
          "relation_type": "branch_condition_routes_path",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000491"
          ],
          "source_quote": "...and could go as low as 5% for customers who pose a significantly higher risk."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "当公司中不存在自然人受益所有人时，如何识别控制人或名义受益所有人？",
      "title": "无自然人 UBO 时识别控制人或名义受益所有人",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e301",
          "role": "context",
          "label": "公司中不存在自然人受益所有人",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "modality": null
        },
        {
          "element_id": "e302",
          "role": "action",
          "label": "识别并核实控制人或名义受益所有人",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "modality": "required"
        },
        {
          "element_id": "e303",
          "role": "outcome",
          "label": "了解公司决策的控制者",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r301",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e301",
          "process_element_id": "e302",
          "condition": "公司中不存在自然人受益所有人",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "source_quote": "In companies where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified."
        },
        {
          "relation_id": "r302",
          "kind": "produce",
          "process_element_id": "e302",
          "outcome_element_id": "e303",
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "source_quote": "This allows you to understand who is in control of the decision-making in the company when natural individual UBOs are not present."
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
      "reason": "该候选提供了审查所有权结构时识别UBO的义务，构成流程的触发和动作部分。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选提供了识别UBO的具体输入、标准、判断和结果，构成流程的核心判断部分。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了机构采用风险为本方法设定受益所有权阈值的过程，构成独立的阈值设定流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述了无自然人受益所有人时识别控制人的流程，构成独立的分支流程。"
    }
  ],
  "skip_reason": null
}
```
