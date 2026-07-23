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

section_id: `CH58-S13`

section_title: `Data as an input for solutions > Data preparation`

section_text_with_unit_anchors:

```text
[v7u_N004786|4786] Data preparation is a process that includes collecting, cleaning, transforming, and preparing data for analysis.
ZH: 数据准备包括收集、清洗、转换和准备数据以供分析

[v7u_N004787|4787] Clean, well-structured data enhances system robustness by reducing errors, speeding up processing, and optimizing system performance.
ZH: 干净、结构良好的数据通过减少错误、加快处理速度来增强系统稳健性

[v7u_N004788|4788] When done correctly, data preparation can have a direct impact on the business, as data quality ensures accuracy, consistency, reliability, and compliance with regulatory requirements. Thorough data preparation builds a strong foundation for detecting financial crime and making informed decisions.
ZH: 正确的数据准备直接影响业务，确保准确性、一致性、可靠性和合规性

[v7u_N004789|4789] Although data engineers typically perform data preparation, it is important that members of the AFC team understand each step in the process.
ZH: 金融犯罪防控团队成员应理解数据准备的每个步骤

[v7u_N004790|4790] Data extraction is the process of gathering data from various sources such as customer databases and third-party providers.
ZH: 数据提取是从客户数据库和第三方提供商等来源收集数据的过程

[v7u_N004791|4791] The methods used to collect data include application programming interface calls, extract, transform, load processes, and network traffic analysis.
ZH: 数据收集方法包括API调用、ETL流程和网络流量分析

[v7u_N004792|4792] The more comprehensive the data, the better the chance of identifying suspicious patterns.
ZH: 数据越全面，识别可疑模式的机会越大

[v7u_N004793|4793] Data transformation involves cleaning and converting raw data to improve its quality and usability.
ZH: 数据转换涉及清洗和转换原始数据以提高其质量和可用性

[v7u_N004794|4794] This step removes duplicates, corrects errors, handles missing values, and ensures consistency across the dataset.
ZH: 数据转换步骤包括去重、纠错、处理缺失值和确保一致性

[v7u_N004795|4795] For example, inconsistencies in date formats or currency types could lead to incorrect analyses.
ZH: 日期格式或货币类型不一致可能导致错误分析

[v7u_N004796|4796] Data transformation also converts data into a format suitable for analysis.
ZH: 数据转换还将数据转换为适合分析的格式

[v7u_N004797|4797] This includes normalizing and encoding data, and creating features, such as aggregated data, frequencies, sums, averages, and standard deviations.
ZH: 数据转换包括归一化、编码和创建特征（如聚合数据、频率、总和、平均值和标准差）

[v7u_N004798|4798] Data loading stores the processed data in a database or data warehouse.
ZH: 数据加载将处理后的数据存储到数据库或数据仓库中

[v7u_N004799|4799] Data mining and data matching take the data that has been extracted, prepared, and loaded and apply various algorithms and analytical techniques to it. The purpose is to detect anomalies and recognize patterns and correlations indicative of suspicious behavior.
ZH: 数据挖掘和数据匹配对提取、准备和加载的数据应用算法和分析技术，以检测异常和识别可疑行为模式

[v7u_N004800|4800] Accurate and consistent data makes AFC systems more robust, impactful, and effective, leading to reliable patterns and model classifications.
ZH: 准确一致的数据使金融犯罪防控系统更稳健、有效，产生可靠的模式和模型分类
```

allowed_unit_ids:

```json
[
  "v7u_N004786",
  "v7u_N004787",
  "v7u_N004788",
  "v7u_N004789",
  "v7u_N004790",
  "v7u_N004791",
  "v7u_N004792",
  "v7u_N004793",
  "v7u_N004794",
  "v7u_N004795",
  "v7u_N004796",
  "v7u_N004797",
  "v7u_N004798",
  "v7u_N004799",
  "v7u_N004800"
]
```

## S2 Process IR

```json
{
  "section_id": "CH58-S13",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_gap_ch58_s13_data_mining_detection"
      ],
      "focal_question": "数据挖掘和匹配如何对已准备数据应用算法以检测异常并识别可疑模式？",
      "title": "对已准备数据应用算法以检测异常和识别可疑模式",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "已提取、准备和加载的数据",
          "evidence_unit_ids": [
            "v7u_N004799"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "应用各种算法和分析技术",
          "evidence_unit_ids": [
            "v7u_N004799"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "检测异常",
          "evidence_unit_ids": [
            "v7u_N004799"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "识别指示可疑行为的模式和相关性",
          "evidence_unit_ids": [
            "v7u_N004799"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e002",
          "auxiliary_element_id": "e001",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N004799"
          ],
          "source_quote": "Data mining and data matching take the data that has been extracted, prepared, and loaded and apply various algorithms and analytical techniques to it."
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
            "v7u_N004799"
          ],
          "source_quote": "The purpose is to detect anomalies"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "condition": null,
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N004799"
          ],
          "source_quote": "recognize patterns and correlations indicative of suspicious behavior"
        }
      ],
      "split_reason": null
    }
  ],
  "candidate_audit": [
    {
      "candidate_id": "s1c_gap_ch58_s13_data_prep_impact",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述数据准备正确进行时的益处和影响（确保数据质量、构建检测基础），属于静态因果描述，无具体业务判断或处理动作，不构成流程。"
    },
    {
      "candidate_id": "s1c_gap_ch58_s13_afc_understanding",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "强调AFC团队理解数据准备步骤的重要性，无程序性迁移或业务判断，不构成流程。"
    },
    {
      "candidate_id": "s1c_gap_ch58_s13_data_mining_detection",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选描述数据挖掘和匹配对已准备数据应用算法，旨在检测异常和识别可疑模式，包含明确处理动作和目的，构成检测流程。"
    }
  ],
  "skip_reason": null
}
```
