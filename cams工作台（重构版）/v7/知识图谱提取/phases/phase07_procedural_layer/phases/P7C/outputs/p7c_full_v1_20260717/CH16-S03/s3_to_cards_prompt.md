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

section_id: `CH16-S03`

section_title: `High-risk business sectors > Key takeaways`

section_text_with_unit_anchors:

```text
[v7u_N001159|1159] Retailers of high-value items require close monitoring.
ZH: 高价值商品零售商需要密切监控

[v7u_N001160|1160] Large cash or credit transactions outside usual or expected hours of operation might indicate illegal activities.
ZH: 在正常营业时间之外发生的大额现金或信用卡交易可能表明存在非法活动

[v7u_N001161|1161] Negative media coverage or allegations should trigger a refresh of customer review and if appropriate, prompt a refresh of the customer risk assessment tool.
ZH: 负面媒体报道或指控应触发客户审查更新及风险评估工具刷新。

[v7u_N001162|1162] Businesses with diversified operations, particularly in high-value and risky sectors, should be subject to enhanced due diligence to evaluate their activities and risks.
ZH: 多元化经营且涉及高价值高风险行业的企业应接受强化尽职调查。

[v7u_N001163|1163] Trade-based money laundering is a process through which criminals disguise the proceeds of crime and transfer value by using trade transactions to legitimize their illicit origins. Criminals frequently exploit import and export businesses to facilitate financial crime and employ a variety of methods to do so, including:
ZH: 贸易洗钱的定义及犯罪分子利用进出口业务实施金融犯罪的方法概述。

[v7u_N001164|1164] Under-invoicing: This describes invoicing goods or services at a price below the fair market value. The seller can transfer value to the buyer by presenting an invoice that reflects a lower price than what is charged in the market.
ZH: 低开发票：以低于公平市场价的价格开具发票，卖方借此向买方转移价值。

[v7u_N001165|1165] Over-invoicing: In contrast to under-invoicing, goods or services are sold at a price above the fair market value. This allows the seller to receive more from the buyer than the actual worth of the goods or services.
ZH: 高开发票：以高于公平市场价的价格销售，卖方获得超出货物实际价值的付款。

[v7u_N001166|1166] Multiple invoicing: This method involves issuing multiple invoices for the same shipment of goods, enabling the criminal to justify numerous payments based on these invoices.
ZH: 多重发票：对同一批货物开具多张发票，为多次付款提供依据。

[v7u_N001167|1167] Short-shipping: This occurs when the actual quantity of goods shipped is less than the quantity of goods invoiced. The seller can benefit financially from the excess payment made.
ZH: 短装：实际发货数量少于发票数量，卖方从超额付款中获利。

[v7u_N001168|1168] Over-shipping: This occurs when the actual quantity shipped is more than the quantity of goods invoiced. The buyer can benefit financially from the excess payment made.
ZH: 超装：实际发货数量多于发票数量，买方从超额付款中获利。

[v7u_N001169|1169] Ghost-shipping: This describes fictitious trades where either no buyer or seller exists, or collusion occurs to create shipping documents that do not correspond to any actual goods being shipped.
ZH: 幽灵运输：虚构贸易，无真实货物对应的运输单据。

[v7u_N001170|1170] Letters of credit (L/C) fraud: L/C can be misused to transfer money between buyers and sellers by manipulating import and export prices or facilitating payments for nonexistent goods.
ZH: 信用证欺诈：滥用信用证操纵进出口价格或为不存在的货物付款。

[v7u_N001171|1171] The trade of dual-use goods poses unique risks of money laundering.
ZH: 两用物品贸易带来独特的洗钱风险。

[v7u_N001172|1172] Criminals might attempt to evade sanctions by using these goods to facilitate illicit trade and disguise transactions from authorities. The proceeds from these activities would then need to be laundered.
ZH: 犯罪分子可能利用两用物品规避制裁并清洗非法所得。

[v7u_N001173|1173] The source of funds risk affects all businesses; however, the import/export sectors are particularly vulnerable as transactions often span multiple jurisdictions.
ZH: 进出口行业因交易跨多个司法管辖区，资金来源风险尤为突出。

[v7u_N001174|1174] Due to the differing applications of AML regulations globally, criminals might strategically structure their trade activities to exploit jurisdictions with weak, ineffective, or inadequate AML regulations where the source of funds is the point of entry to the financial system via import/export businesses.
ZH: 犯罪分子利用全球反洗钱监管差异，选择薄弱司法管辖区进行贸易洗钱。
```

allowed_unit_ids:

```json
[
  "v7u_N001159",
  "v7u_N001160",
  "v7u_N001161",
  "v7u_N001162",
  "v7u_N001163",
  "v7u_N001164",
  "v7u_N001165",
  "v7u_N001166",
  "v7u_N001167",
  "v7u_N001168",
  "v7u_N001169",
  "v7u_N001170",
  "v7u_N001171",
  "v7u_N001172",
  "v7u_N001173",
  "v7u_N001174"
]
```

## S2 Process IR

```json
{
  "section_id": "CH16-S03",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "当出现负面媒体报道或指控时，如何触发审查与风险评估工具更新？",
      "title": "负面媒体报道或指控触发的客户审查与风险评估工具更新",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "负面媒体报道或指控",
          "evidence_unit_ids": [
            "v7u_N001161"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "客户审查更新",
          "evidence_unit_ids": [
            "v7u_N001161"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "在适当情况下提示风险评估工具刷新",
          "evidence_unit_ids": [
            "v7u_N001161"
          ],
          "modality": "required"
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
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001161"
          ],
          "source_quote": "Negative media coverage or allegations should trigger a refresh of customer review"
        },
        {
          "relation_id": "r002",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e003",
          "condition": "if appropriate",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001161"
          ],
          "source_quote": "if appropriate, prompt a refresh of the customer risk assessment tool"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "对于多元化经营且涉及高价值高风险行业的企业，应如何实施尽职调查？",
      "title": "多元化高风险企业的强化尽职调查流程",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "多元化经营且涉及高价值高风险行业的企业",
          "evidence_unit_ids": [
            "v7u_N001162"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "接受强化尽职调查",
          "evidence_unit_ids": [
            "v7u_N001162"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "评估其活动和风险",
          "evidence_unit_ids": [
            "v7u_N001162"
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
          "condition": "企业多元化经营且涉及高价值高风险行业",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001162"
          ],
          "source_quote": "Businesses with diversified operations, particularly in high-value and risky sectors, should be subject to enhanced due diligence"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001162"
          ],
          "source_quote": "to evaluate their activities and risks"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_gap_ch16_s03_retailer_monitoring"
      ],
      "focal_question": "高价值商品零售商需要何种监控？",
      "title": "高价值商品零售商的密切监控要求",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "高价值商品零售商",
          "evidence_unit_ids": [
            "v7u_N001159"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "需要密切监控",
          "evidence_unit_ids": [
            "v7u_N001159"
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
          "condition": "为高价值商品零售商",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001159"
          ],
          "source_quote": "Retailers of high-value items require close monitoring."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_gap_ch16_s03_offhour_txn_indicator"
      ],
      "focal_question": "非正常时间的大额交易是否可能指示非法活动？",
      "title": "非正常时间大额交易作为非法活动指标",
      "card_nature": "risk_indicator",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "大额现金或信用卡交易发生在正常营业时间之外",
          "evidence_unit_ids": [
            "v7u_N001160"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "可能表明非法活动",
          "evidence_unit_ids": [
            "v7u_N001160"
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
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N001160"
          ],
          "source_quote": "Large cash or credit transactions outside usual or expected hours of operation might indicate illegal activities."
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
      "reason": "该候选描述了负面媒体报道或指控触发客户审查更新和风险评估工具刷新的完整程序，具备明确的触发-动作关系。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选提供了多元化高风险企业应接受强化尽职调查并评估活动风险的业务流程，包含动作与目的关系。"
    },
    {
      "candidate_id": "s1c_gap_ch16_s03_retailer_monitoring",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选虽然简短，但包含了针对高价值商品零售商需要密切监控的程序性要求，可独立表达为条件触发关系。"
    },
    {
      "candidate_id": "s1c_gap_ch16_s03_offhour_txn_indicator",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选将交易特征与非法活动指示联系起来，构成一个判断关系，可作为风险指标独立建模。"
    }
  ],
  "skip_reason": null
}
```
