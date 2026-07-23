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

section_id: `CH12-S04`

section_title: `Money laundering risks associated with insurance, securities, brokerage, and custodian services > Securities and brokerage risks`

section_text_with_unit_anchors:

```text
[v7u_N000912|912] According to FATF, securities providers can range from those that largely interact with retail investors, such as retail stockbrokers, wealth managers, and financial advisors, to those who serve institutional markets such as clearing members, prime brokers, and global custodians.
ZH: FATF指出证券服务商范围从零售投资者到机构市场。

[v7u_N000913|913] Providers offer various services including capital market research, portfolio management, and investment funds distribution.
ZH: 服务商提供资本市场研究、投资组合管理和投资基金分销等服务。

[v7u_N000914|914] The securities and brokerage sector serves direct customers and intermediaries that transact on behalf of their underlying customers.
ZH: 证券和经纪业服务于直接客户和代表其客户交易的中介。

[v7u_N000915|915] Transactions can encompass a wide range of financial instruments, including transferable securities, moneymarket instruments, investment funds, options, futures, swaps, forward rate agreements, and other derivative contracts.
ZH: 交易涵盖多种金融工具，包括可转让证券、货币市场工具、投资基金、期权、期货等。

[v7u_N000916|916] This sector is particularly vulnerable during the layering and integration stages of money laundering.
ZH: 证券业在洗钱的离析阶段和融合阶段尤其脆弱。

[v7u_N000917|917] FATF notes that the sector is unique in that it can be used not only to launder illicit funds but also to generate illicit funds within the industry itself through fraudulent activities.
ZH: FATF指出证券业既可洗钱也可通过欺诈产生非法资金。

[v7u_N000918|918] Characteristics such as high levels of interaction between securities providers and intermediaries such as investors and brokers, substantial transaction volumes, rapid execution speeds, and a degree of anonymity, all create opportunities for criminals to launder proceeds.
ZH: 高互动性、大交易量、快速执行和匿名性为洗钱创造机会。

[v7u_N000919|919] Complex financial products present a risk as they can obscure the source of funds and complicate transaction monitoring.
ZH: 复杂金融产品可能掩盖资金来源并复杂化交易监控。

[v7u_N000920|920] Offshore accounts provide anonymity, which can facilitate money laundering and enable criminals to exploit lax regulatory jurisdictions.
ZH: 离岸账户提供匿名性，便利洗钱并利用监管宽松的司法管辖区。

[v7u_N000921|921] High-risk customers, such as PEPs, and intermediaries require careful risk assessment. PEPs might be susceptible to corruption, while intermediaries might facilitate illicit transactions on behalf of customers.
ZH: 高风险客户如政治敏感人物和中介机构需要仔细的风险评估

[v7u_N000922|922] Additionally, the rise of electronic trading platforms emphasizes speed and high transaction volumes, making it challenging to monitor and apply mitigation controls.
ZH: 电子交易平台的高速度和高交易量增加了监控难度

[v7u_N000923|923] Continuous monitoring of trading activities can help identify unusual patterns or behaviors that might indicate money laundering. Robust transaction monitoring systems that flag suspicious transactions based on predefined criteria can help identify large or unusual trades, rapid trading patterns, highfrequency transactions and transactions involving high-risk jurisdictions.
ZH: 持续监控交易活动以识别异常模式，防范洗钱

[v7u_N000924|924] Conducting CDD helps ensure that the source of funds is legitimate, and that customers are correctly segmented according to their expected and historical trading patterns.
ZH: 客户尽职调查用于验证资金来源和客户细分

[v7u_N000925|925] Asset managers or asset management companies conduct investments and handle assets on behalf of their customers.
ZH: 资产管理公司代表客户进行投资和资产管理

[v7u_N000926|926] Asset managers are required to understand the money laundering risks of their business as they handle large volumes of capital across multiple jurisdictions, in diverse and evolving asset classes, often with anonymity in transactions, using complex financial products and third parties.
ZH: 资产管理公司有义务了解其业务中的洗钱风险

[v7u_N000927|927] Asset managers provide a variety of financial products and services, including:
ZH: 资产管理公司提供的金融产品和服务列表

[v7u_N000928|928] Exchange-traded funds (ETF): These are investment funds traded on stock exchanges, similar to individual stocks. They offer diversification and liquidity but can also obscure the identities of underlying investors.
ZH: 交易所交易基金（ETF）的定义及其洗钱风险

[v7u_N000929|929] Derivatives: These financial instruments, such as options and futures, derive their value from underlying assets. Their complexity and potential for leverage can be exploited for money laundering.
ZH: 衍生品（如期权和期货）的复杂性和杠杆可能被用于洗钱

[v7u_N000930|930] Hedge funds: These pooled investment funds employ various strategies to generate returns. Their often opaque structures and high minimum investment requirements can attract illicit actors.
ZH: 对冲基金的不透明结构和最低投资要求可能吸引非法行为者

[v7u_N000931|931] Private equity: This involves investing directly in private companies or buying out public companies. The lack of transparency in these transactions can pose money laundering challenges.
ZH: 私募股权交易缺乏透明度，带来洗钱挑战

[v7u_N000932|932] Commodity trading advice: Asset managers might provide guidance on trading physical commodities, which can be subject to manipulation and illicit activities.
ZH: 大宗商品交易建议可能被操纵和用于非法活动

[v7u_N000933|933] Real estate investments: Investing in real estate involves various stakeholders, including sellers, buyers, renters, property managers, and agents, all of whom should be thoroughly vetted to mitigate money laundering risks.
ZH: 房地产投资涉及多方利益相关者，需全面审查以降低洗钱风险

[v7u_N000934|934] Crowdfunding: As a relatively new form of asset management, crowdfunding platforms allow individuals to invest in projects or startups. These platforms can be misused for money laundering due to insufficient regulatory oversight and the anonymity they can provide to investors.
ZH: 众筹平台因监管不足和匿名性可能被滥用于洗钱

[v7u_N000935|935] The complexity and variability of these products and services make it increasingly difficult to detect money laundering.
ZH: 产品和服务的复杂性和多样性增加了洗钱检测难度

[v7u_N000936|936] Additionally, asset managers face a complex and evolving CDD process that requires knowledge of all parties involved in the transactions. Those parties include investment fund managers, portfolio managers, and alternative investment fund managers, such as those overseeing hedge funds and private equity.
ZH: 资产管理公司面临复杂的客户尽职调查，需了解所有交易方

[v7u_N000937|937] By adopting a risk-based approach that emphasizes strong CDD controls and continuous monitoring, they can meet regulatory requirements and demonstrate a genuine commitment to the sector’s integrity. This commitment also addresses emerging risks associated with new asset classes, such as cryptocurrencies and novel financial instruments, which might be more susceptible to exploitation by money launderers.
ZH: 基于风险的方法通过强化客户尽职调查和监控应对新兴资产类别的洗钱风险
```

allowed_unit_ids:

```json
[
  "v7u_N000912",
  "v7u_N000913",
  "v7u_N000914",
  "v7u_N000915",
  "v7u_N000916",
  "v7u_N000917",
  "v7u_N000918",
  "v7u_N000919",
  "v7u_N000920",
  "v7u_N000921",
  "v7u_N000922",
  "v7u_N000923",
  "v7u_N000924",
  "v7u_N000925",
  "v7u_N000926",
  "v7u_N000927",
  "v7u_N000928",
  "v7u_N000929",
  "v7u_N000930",
  "v7u_N000931",
  "v7u_N000932",
  "v7u_N000933",
  "v7u_N000934",
  "v7u_N000935",
  "v7u_N000936",
  "v7u_N000937"
]
```

## S2 Process IR

```json
{
  "section_id": "CH12-S04",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "如何通过持续监控和交易监控系统识别洗钱异常模式？",
      "title": "通过持续监控和系统标记识别异常交易",
      "card_nature": "control",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "交易活动",
          "evidence_unit_ids": [
            "v7u_N000923"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "预定义标准",
          "evidence_unit_ids": [
            "v7u_N000923"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "实施持续的交易监控，并使用基于预定义标准标记可疑交易的稳健交易监控系统",
          "evidence_unit_ids": [
            "v7u_N000923"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "识别可能表明洗钱的异常模式或行为",
          "evidence_unit_ids": [
            "v7u_N000923"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "识别大额交易、异常交易、快速交易模式、高频交易或涉及高风险司法管辖区的交易",
          "evidence_unit_ids": [
            "v7u_N000923"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "relation_type": "standard_constrains_action",
          "evidence_unit_ids": [
            "v7u_N000923"
          ],
          "source_quote": "Robust transaction monitoring systems that flag suspicious transactions based on predefined criteria"
        },
        {
          "relation_id": "r002",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e001",
          "process_element_id": "e003",
          "condition": null,
          "relation_type": "clue_supports_identification",
          "evidence_unit_ids": [
            "v7u_N000923"
          ],
          "source_quote": "Continuous monitoring of trading activities can help identify unusual patterns or behaviors"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": "identification_leads_to_conclusion",
          "evidence_unit_ids": [
            "v7u_N000923"
          ],
          "source_quote": "can help identify unusual patterns or behaviors that might indicate money laundering"
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e005",
          "relation_type": "identification_leads_to_conclusion",
          "evidence_unit_ids": [
            "v7u_N000923"
          ],
          "source_quote": "Robust transaction monitoring systems ... can help identify large or unusual trades, rapid trading patterns, highfrequency transactions and transactions involving high-risk jurisdictions."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "如何通过进行客户尽职调查确保资金来源合法和客户正确细分？",
      "title": "进行客户尽职调查以确保合法性和客户细分",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "客户",
          "evidence_unit_ids": [
            "v7u_N000924"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "预期和历史交易模式",
          "evidence_unit_ids": [
            "v7u_N000924"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "进行客户尽职调查",
          "evidence_unit_ids": [
            "v7u_N000924"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "确保资金来源合法",
          "evidence_unit_ids": [
            "v7u_N000924"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "客户根据预期和历史交易模式正确细分",
          "evidence_unit_ids": [
            "v7u_N000924"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "relation_type": "standard_constrains_action",
          "evidence_unit_ids": [
            "v7u_N000924"
          ],
          "source_quote": "according to their expected and historical trading patterns"
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e001",
          "relation_type": null,
          "evidence_unit_ids": [
            "v7u_N000924"
          ],
          "source_quote": "Conducting CDD helps ensure that the source of funds is legitimate, and that customers are correctly segmented"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": "identification_leads_to_conclusion",
          "evidence_unit_ids": [
            "v7u_N000924"
          ],
          "source_quote": "helps ensure that the source of funds is legitimate"
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e005",
          "relation_type": "identification_leads_to_conclusion",
          "evidence_unit_ids": [
            "v7u_N000924"
          ],
          "source_quote": "customers are correctly segmented according to their expected and historical trading patterns"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "如何通过对房地产投资利益相关者审查以减轻洗钱风险？",
      "title": "审查房地产投资利益相关者以减轻洗钱风险",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "房地产投资涉及的利益相关者（卖方、买方、租户、物业经理、代理）",
          "evidence_unit_ids": [
            "v7u_N000933"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "should 彻底审查（vetted）",
          "evidence_unit_ids": [
            "v7u_N000933"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "减轻洗钱风险",
          "evidence_unit_ids": [
            "v7u_N000933"
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
          "condition": "当进行房地产投资并涉及这些利益相关者时",
          "relation_type": null,
          "evidence_unit_ids": [
            "v7u_N000933"
          ],
          "source_quote": "Investing in real estate involves various stakeholders, including sellers, buyers, renters, property managers, and agents, all of whom should be thoroughly vetted"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": "conclusion_triggers_response",
          "evidence_unit_ids": [
            "v7u_N000933"
          ],
          "source_quote": "to mitigate money laundering risks"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "如何通过采用风险为本方法满足监管要求、展现诚信承诺并应对新兴风险？",
      "title": "采用风险为本方法以实现合规与风险应对",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "采用风险为本的方法",
          "evidence_unit_ids": [
            "v7u_N000937"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "强调强大的客户尽职调查控制和持续监控",
          "evidence_unit_ids": [
            "v7u_N000937"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "满足监管要求",
          "evidence_unit_ids": [
            "v7u_N000937"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "展现对行业诚信的承诺",
          "evidence_unit_ids": [
            "v7u_N000937"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "应对新兴资产类别（如加密货币和新型金融工具）的风险",
          "evidence_unit_ids": [
            "v7u_N000937"
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
          "evidence_unit_ids": [
            "v7u_N000937"
          ],
          "source_quote": "a risk-based approach that emphasizes strong CDD controls and continuous monitoring"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "relation_type": "conclusion_triggers_response",
          "evidence_unit_ids": [
            "v7u_N000937"
          ],
          "source_quote": "can meet regulatory requirements"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e004",
          "relation_type": "conclusion_triggers_response",
          "evidence_unit_ids": [
            "v7u_N000937"
          ],
          "source_quote": "demonstrate a genuine commitment to the sector’s integrity"
        },
        {
          "relation_id": "r004",
          "kind": "sequence",
          "before_element_id": "e004",
          "after_element_id": "e005",
          "relation_type": "result_handoffs_stage",
          "evidence_unit_ids": [
            "v7u_N000937"
          ],
          "source_quote": "This commitment also addresses emerging risks associated with new asset classes, such as cryptocurrencies and novel financial instruments"
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
      "reason": "仅陈述高风险客户和中介需要仔细风险评估，未描述任何业务处理或判断过程，不满足流程定义。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "描述了通过持续监控和交易监控系统识别异常交易的程序，构成可建模的流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "描述了通过进行客户尽职调查以确保资金来源合法和客户细分的处理过程，构成流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "仅说明资产管理公司有义务了解洗钱风险，无具体的处理或判断动作，不构成流程。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "描述了对房地产投资利益相关者进行审查以减轻洗钱风险的过程，构成流程。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "描述了采用风险为本方法以实现满足监管要求、展现承诺和应对新风险的宏观流程。"
    }
  ],
  "skip_reason": null
}
```
