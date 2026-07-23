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

section_id: `CH10-S02`

section_title: `Money Laundering Risks in Nonbank Financial Institutions > Case example: CashBayou's risk management challenges`

section_text_with_unit_anchors:

```text
[v7u_N000768|768] CashBayou is a thriving e-commerce platform, connecting buyers and sellers across the globe. CashBayou’s platform is structured in such a way that they hold buyers’ funds temporarily and convert them into the sellers' preferred currency before transferring them to sellers. Because of this, they are required to have an MSB license.
ZH: 案例：CashBayou 作为电子商务平台因持有并转换资金而需持有 货币服务企业 牌照。

[v7u_N000769|769] CashBayou also works closely with payment service providers, payment aggregators, card issuers, and other financial entities to ensure smooth and efficient transactions and facilitate their ecommerce ecosystem.
ZH: CashBayou 与支付服务商、聚合器、发卡机构等合作以支持电子商务生态。

[v7u_N000770|770] CashBayou has a new head of AML compliance, Emma. On her second day on the job, she receives an alert about unusual transaction patterns. She quickly gathers her team to investigate.
ZH: CashBayou 新任反洗钱合规负责人 Emma 收到异常交易警报并召集团队调查。

[v7u_N000771|771] They discover that a new buyer, using multiple accounts, is making high-frequency, low-value transactions with a network of sellers who are all based in the same jurisdiction.
ZH: 发现新买家使用多个账户向同一司法管辖区的卖家进行高频低额交易。

[v7u_N000772|772] This raises a red flag for money laundering.
ZH: 该交易模式引发洗钱红旗信号信号。

[v7u_N000773|773] While investigating, Emma realizes CashBayou's current KYC governance and execution are inadequate.
ZH: Emma 发现 CashBayou 当前的 了解你的客户 治理和执行存在不足。

[v7u_N000774|774] Insufficient reviews of purchasers and storefront owners could expose the platform to financia crime, fraud risks, and potential regulatory issues, which might result in temporary service suspension.
ZH: 对买家和店主审查不足可能使平台面临金融犯罪、欺诈和监管风险。

[v7u_N000775|775] The company’s current primary payment service provider, PaySecure, which is an E-Money License Institution (EMI) registered in the UK, contacts Emma and requests more information on a series of transactions.
ZH: 主要支付服务商 PaySecure 联系 Emma 要求提供一系列交易的更多信息。

[v7u_N000776|776] Emma notices that the request covers part of the unusual transactions related to the new buyer.
ZH: Emma 注意到该请求涉及部分与新买家相关的异常交易。

[v7u_N000777|777] In addition, based on the frequency of transactions, PaySecure requests a cal with the compliance officer of CashBayou to understand their due diligence process.
ZH: PaySecure 要求与 CashBayou 合规官通话以了解其尽职调查流程。

[v7u_N000778|778] During the meeting, PaySecure expresses their concern on CashBayou’s policies and stresses the need for ongoing collaboration and rigorous monitoring to mitigate risks.
ZH: 会议中 PaySecure 对 CashBayou 的政策表示担忧，强调持续合作和严格监控。

[v7u_N000779|779] Later that week, Emma's team receives a letter from their card issuer partner, CardGuard. The letter states that companies using CardGuard’s services are required to align their due diligence procedures with CardGuard’s standards for referred cardholders. Failure to comply will result in the termination of CardGuard’s partnership with CashBayou.
ZH: 发卡机构 CardGuard 要求 CashBayou 调整尽职调查程序以符合其标准，否则终止合作。

[v7u_N000780|780] This example demonstrates how NBFIs, unlike traditional banks, need to navigate multifaceted relationships with various financial entities, each presenting unique compliance challenges. By proactively identifying and addressing AML and KYC deficiencies and fostering open communication with their partners, Emma aims to create a more secure transaction environment that protects both the platform, its partners, and its users from financial crime.
ZH: 案例说明非银行金融机构需处理多方关系，主动识别反洗钱和 了解你的客户 缺陷以防范金融犯罪。
```

allowed_unit_ids:

```json
[
  "v7u_N000768",
  "v7u_N000769",
  "v7u_N000770",
  "v7u_N000771",
  "v7u_N000772",
  "v7u_N000773",
  "v7u_N000774",
  "v7u_N000775",
  "v7u_N000776",
  "v7u_N000777",
  "v7u_N000778",
  "v7u_N000779",
  "v7u_N000780"
]
```

## S2 Process IR

```json
{
  "section_id": "CH10-S02",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_gap_ch10_s02_msb_license"
      ],
      "focal_question": "CashBayou 的业务模式是否触发 MSB 牌照要求？",
      "title": "因平台持有并转换资金需持有 MSB 牌照",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "CashBayou 平台暂时持有买家资金并转换为卖家偏好的货币",
          "evidence_unit_ids": [
            "v7u_N000768"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "必须持有 MSB 牌照",
          "evidence_unit_ids": [
            "v7u_N000768"
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
          "condition": "平台持有并转换资金",
          "relation_type": "standard_transmits_requirement",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000768"
          ],
          "source_quote": "Because of this, they are required to have an MSB license."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "Emma 如何响应异常交易警报并识别洗钱风险和 KYC 缺陷？",
      "title": "调查异常交易警报并识别洗钱红旗及 KYC 缺陷",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "收到异常交易警报",
          "evidence_unit_ids": [
            "v7u_N000770"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Emma 召集团队调查",
          "evidence_unit_ids": [
            "v7u_N000770"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "发现新买家使用多个账户向同辖区卖家进行高频低额交易",
          "evidence_unit_ids": [
            "v7u_N000771"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "decision",
          "label": "交易模式引发洗钱红旗",
          "evidence_unit_ids": [
            "v7u_N000772"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "意识到当前 KYC 治理和执行不足",
          "evidence_unit_ids": [
            "v7u_N000773"
          ],
          "modality": null
        },
        {
          "element_id": "e006",
          "role": "decision",
          "label": "对买家和店主审查不足可能使平台面临金融犯罪、欺诈和监管风险，可能导致服务暂停",
          "evidence_unit_ids": [
            "v7u_N000774"
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
            "v7u_N000770"
          ],
          "source_quote": "she receives an alert about unusual transaction patterns. She quickly gathers her team to investigate."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000771"
          ],
          "source_quote": "They discover that a new buyer, using multiple accounts, is making high-frequency, low-value transactions with a network of sellers who are all based in the same jurisdiction."
        },
        {
          "relation_id": "r003",
          "kind": "sequence",
          "before_element_id": "e003",
          "after_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000772"
          ],
          "source_quote": "This raises a red flag for money laundering."
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e005",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000773"
          ],
          "source_quote": "While investigating, Emma realizes CashBayou's current KYC governance and execution are inadequate."
        },
        {
          "relation_id": "r005",
          "kind": "sequence",
          "before_element_id": "e005",
          "after_element_id": "e006",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000774"
          ],
          "source_quote": "Insufficient reviews of purchasers and storefront owners could expose the platform to financia crime, fraud risks, and potential regulatory issues, which might result in temporary service suspension."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "PaySecure 如何与 CashBayou 互动并表达对其合规政策的担忧？",
      "title": "PaySecure 因异常交易要求信息并沟通尽职调查",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "PaySecure 联系 Emma 要求提供一系列交易的更多信息",
          "evidence_unit_ids": [
            "v7u_N000775"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "Emma 注意到该请求涵盖部分与新买家相关的异常交易",
          "evidence_unit_ids": [
            "v7u_N000776"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "基于交易频率，PaySecure 要求与 CashBayou 合规官通话了解尽职调查流程",
          "evidence_unit_ids": [
            "v7u_N000777"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "会议中 PaySecure 表达对 CashBayou 政策的担忧并强调需要持续合作和严格监控以降低风险",
          "evidence_unit_ids": [
            "v7u_N000778"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "sequence",
          "before_element_id": "e001",
          "after_element_id": "e002",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000776"
          ],
          "source_quote": "Emma notices that the request covers part of the unusual transactions related to the new buyer."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e001",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000777"
          ],
          "source_quote": "In addition, based on the frequency of transactions, PaySecure requests a cal with the compliance officer of CashBayou to understand their due diligence process."
        },
        {
          "relation_id": "r003",
          "kind": "sequence",
          "before_element_id": "e003",
          "after_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000778"
          ],
          "source_quote": "During the meeting, PaySecure expresses their concern on CashBayou’s policies and stresses the need for ongoing collaboration and rigorous monitoring to mitigate risks."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "CardGuard 对 CashBayou 的尽职调查程序有何要求及不遵守的后果？",
      "title": "CardGuard 要求 CashBayou 调整尽职调查程序以符合标准否则终止合作",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "CardGuard 对推荐持卡人的尽职调查标准",
          "evidence_unit_ids": [
            "v7u_N000779"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "CashBayou 被要求调整尽职调查程序以符合 CardGuard 标准",
          "evidence_unit_ids": [
            "v7u_N000779"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "decision",
          "label": "是否满足 CardGuard 标准",
          "evidence_unit_ids": [
            "v7u_N000779"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "合作关系继续",
          "evidence_unit_ids": [
            "v7u_N000779"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "合作关系终止",
          "evidence_unit_ids": [
            "v7u_N000779"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e001",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000779"
          ],
          "source_quote": "are required to align their due diligence procedures with CardGuard’s standards for referred cardholders"
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000779"
          ],
          "source_quote": "required to align their due diligence procedures with CardGuard’s standards (compliance assessment follows)"
        },
        {
          "relation_id": "r003",
          "kind": "branch",
          "decision_element_id": "e003",
          "target_element_id": "e004",
          "condition": "满足 CardGuard 标准",
          "relation_type": "branch_condition_routes_path",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000779"
          ],
          "source_quote": "(implied compliant path)"
        },
        {
          "relation_id": "r004",
          "kind": "branch",
          "decision_element_id": "e003",
          "target_element_id": "e005",
          "condition": "未满足 CardGuard 标准",
          "relation_type": "branch_condition_routes_path",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000779"
          ],
          "source_quote": "Failure to comply will result in the termination of CardGuard’s partnership with CashBayou."
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
        "ep_002"
      ],
      "reason": "该候选描述了从接收异常交易警报到调查、发现交易模式、引发洗钱红旗、意识到KYC不足及风险评估的完整调查流程，构成一个程序性 episode。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述了PaySecure联系CashBayou要求信息、要求了解尽职调查及会议表达担忧的互动流程，构成一个沟通与合规要求的 episode。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选描述了CardGuard要求CashBayou调整尽职调查程序以符合标准，否则终止合作的条件性义务，构成一个合规要求与后果的 episode。"
    },
    {
      "candidate_id": "s1c_gap_ch10_s02_msb_license",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选描述了因业务模式触发MSB牌照要求的法律适用判断，构成一个义务产生的 episode。"
    }
  ],
  "skip_reason": null
}
```
