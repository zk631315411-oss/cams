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

section_id: `CH47-S04`

section_title: `Transaction monitoring > Transaction monitoring system tuning`

section_text_with_unit_anchors:

```text
[v7u_N003272|3272] TM system tuning is the process of refining and adjusting parameters and thresholds of specific detection logic rules, or scenarios. Scenarios are designed to detect suspicious activities and abnormal transaction behaviors, such as money laundering, fraud, or other illicit activities. Tuning is important because it:
ZH: 交易监控系统调优是调整检测规则参数和阈值的过程。

[v7u_N003273|3273] Ensures the TM system effectively detects suspicious activity.
ZH: 调优确保交易监控系统有效检测可疑活动。

[v7u_N003274|3274] Reduces false positives.
ZH: 调优减少误报。

[v7u_N003275|3275] Ensures efficient resource use.
ZH: 调优确保资源高效利用。

[v7u_N003276|3276] Allows organizations to manage changes in financial crime and in their business operations.
ZH: 调优使组织能够应对金融犯罪和业务运营的变化。

[v7u_N003277|3277] Ensures regulatory compliance.
ZH: 调优确保监管合规。

[v7u_N003278|3278] Tuning involves four key components: scenario setting, customer segmentation, threshold setting, and frequency.
ZH: 调优包括场景设置、客户细分、阈值设置和频率四个关键组成部分。

[v7u_N003279|3279] Scenario setting involves creating, modifying, or removing detection rules and scenarios based on previous experiences with suspicious activity and actual incidents.
ZH: 场景设置是基于以往经验创建、修改或移除检测规则和场景。

[v7u_N003280|3280] Threshold setting defines the minimum level of activity required for a transaction to trigger an alert.
ZH: 阈值设置定义了触发警报所需的最低活动水平。

[v7u_N003281|3281] For example, the threshold for reporting a CTR might be any currency transaction that exceeds US$10,000.
ZH: 货币交易报告（CTR）阈值示例：超过10,000美元的任何货币交易

[v7u_N003282|3282] Adjusting thresholds refines sensitivity and accuracy.
ZH: 调整阈值可提高交易监控系统的灵敏度和准确性

[v7u_N003283|3283] Reducing the number of false positives is a key goal in setting thresholds to make the most efficient use of resources.
ZH: 减少误报是设定阈值的关键目标，以高效利用资源

[v7u_N003284|3284] The frequency determines how often tuning should occur.
ZH: 调优频率决定了交易监控系统应多久进行一次调整

[v7u_N003285|3285] The frequency might also be influenced by changes in business strategy, anomalies, regulatory updates, or market changes.
ZH: 调优频率受业务策略变化、异常、监管更新或市场变化影响

[v7u_N003286|3286] Tuning should be dynamic, with special assessments triggered by significant events or trends.
ZH: 调优应是动态的，重大事件或趋势应触发专项评估
```

allowed_unit_ids:

```json
[
  "v7u_N003272",
  "v7u_N003273",
  "v7u_N003274",
  "v7u_N003275",
  "v7u_N003276",
  "v7u_N003277",
  "v7u_N003278",
  "v7u_N003279",
  "v7u_N003280",
  "v7u_N003281",
  "v7u_N003282",
  "v7u_N003283",
  "v7u_N003284",
  "v7u_N003285",
  "v7u_N003286"
]
```

## S2 Process IR

```json
{
  "section_id": "CH47-S04",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "重大事件或趋势如何触发调优中的专项评估",
      "title": "重大事件或趋势触发专项评估",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "重大事件或趋势",
          "evidence_unit_ids": [
            "v7u_N003286"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "专项评估",
          "evidence_unit_ids": [
            "v7u_N003286"
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
          "condition": "significant events or trends occur",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N003286"
          ],
          "source_quote": "Tuning should be dynamic, with special assessments triggered by significant events or trends."
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
      "reason": "该候选描述了重大事件或趋势触发专项评估的程序性关系，构成有效流程。"
    }
  ],
  "skip_reason": null
}
```
