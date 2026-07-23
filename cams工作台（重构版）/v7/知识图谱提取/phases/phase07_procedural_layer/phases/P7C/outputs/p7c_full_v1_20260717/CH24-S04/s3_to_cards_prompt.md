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

section_id: `CH24-S04`

section_title: `US AML/CFT regulatory landscape > Case study: US regulatory enforcement actions`

section_text_with_unit_anchors:

```text
[v7u_N001761|1761] Between 2023 and 2024, Wells Fargo & Company, parent company of Wells Fargo Bank, N.A., and hereafter called Wells Fargo, faced significant enforcement actions from three major US regulatory bodies: the Federal Reserve Board, the SEC, and the OCC. These enforcement actions addressed various compliance deficiencies and misconduct within the bank's operations.
ZH: 2023-2024年富国银行因合规缺陷遭美联储、SEC和OCC重大执法行动

[v7u_N001762|1762] In March of 2023, the Federal Reserve Board imposed a US$67.8 million fine on Wells Fargo for providing a trade finance software platform to a foreign bank. The foreign bank used the platform to conduct transactions involving parties subject to US sanctions. The Federal Reserve Board concluded that Wells Fargo had insufficient policies and procedures to ensure compliance with US sanctions laws, leading to transactions that violated these regulations.
ZH: 2023年3月美联储因富国银行制裁合规失败处以6780万美元罚款

[v7u_N001763|1763] In August of 2023, the SEC charged two non-bank affiliates of Wells Fargo, Wells Fargo Clearing Services LLC and Wells Fargo Advisors Financial Network LLC, for overcharging more than 10,900 investment advisory accounts, amounting to over US$26.8 million in excessive fees.
ZH: 2023年8月SEC指控富国银行附属机构多收10900个投资顾问账户费用逾2680万美元

[v7u_N001764|1764] The SEC's investigation revealed that certain financial advisers had agreed to reduce advisory fees for clients, but did not enter the reductions into the billing system. Consequently, the financial advisers charged the clients higher fees than agreed upon.
ZH: SEC调查发现富国银行顾问未将约定费用减免录入计费系统导致多收费

[v7u_N001765|1765] Wells Fargo consented to pay a US$35 million civil penalty to resolve the issue on behalf of its affiliates.
ZH: 富国银行同意支付3500万美元民事罚款以解决SEC指控

[v7u_N001766|1766] In September of 2024, the OCC issued an enforcement action against Wells Fargo, identifying deficiencies in the bank's financial crimes risk management and AML controls. The OCC's formal agreement highlighted issues in areas such as suspicious activity reporting, currency transaction reporting, CDD, and customer identification programs. While the OCC did not impose monetary penalties, the agreement required Wells Fargo to obtain OCC approval before expanding into new products or services in areas of moderate or high risk.
ZH: 2024年9月OCC对富国银行发出执法行动，指出金融犯罪风险管理及反洗钱控制缺陷
```

allowed_unit_ids:

```json
[
  "v7u_N001761",
  "v7u_N001762",
  "v7u_N001763",
  "v7u_N001764",
  "v7u_N001765",
  "v7u_N001766"
]
```

## S2 Process IR

```json
{
  "section_id": "CH24-S04",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "美联储如何因富国银行制裁合规不足处以罚款？",
      "title": "美联储因富国银行制裁政策和程序不足处以罚款",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Wells Fargo 提供了贸易金融软件平台，外国银行使用该平台进行涉及美国制裁方的交易",
          "evidence_unit_ids": [
            "v7u_N001762"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "美国制裁法律法规",
          "evidence_unit_ids": [
            "v7u_N001762"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "decision",
          "label": "美联储认定 Wells Fargo 的政策和程序不足以确保遵守美国制裁法，导致违规交易",
          "evidence_unit_ids": [
            "v7u_N001762"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "美联储对 Wells Fargo 处以 67.8 million 罚款",
          "evidence_unit_ids": [
            "v7u_N001762"
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
          "process_element_id": "e003",
          "condition": null,
          "relation_type": "clue_supports_identification",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001762"
          ],
          "source_quote": "In March of 2023, the Federal Reserve Board imposed a US$67.8 million fine on Wells Fargo for providing a trade finance software platform to a foreign bank. The foreign bank used the platform to conduct transactions involving parties subject to US sanctions. The Federal Reserve Board concluded that Wells Fargo had insufficient policies and procedures to ensure compliance with US sanctions laws, leading to transactions that violated these regulations."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001762"
          ],
          "source_quote": "The Federal Reserve Board concluded that Wells Fargo had insufficient policies and procedures to ensure compliance with US sanctions laws."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001762"
          ],
          "source_quote": "The Federal Reserve Board imposed a US$67.8 million fine on Wells Fargo for providing a trade finance software platform... concluded that Wells Fargo had insufficient policies and procedures... leading to transactions that violated these regulations."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "SEC如何因富国银行附属机构多收费用而采取执法行动？",
      "title": "SEC因富国银行附属机构多收费用指控并处罚",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "某些财务顾问同意降低咨询费但未录入计费系统，导致客户被多收费用",
          "evidence_unit_ids": [
            "v7u_N001764"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "SEC调查并发现多收费用行为",
          "evidence_unit_ids": [
            "v7u_N001764"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "SEC指控富国银行附属机构多收超过10,900个投资顾问账户费用，超额逾26.8 million",
          "evidence_unit_ids": [
            "v7u_N001763"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "富国银行代表附属机构同意支付35 million民事罚款以解决指控",
          "evidence_unit_ids": [
            "v7u_N001765"
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
          "relation_type": "clue_supports_identification",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001764"
          ],
          "source_quote": "The SEC's investigation revealed that certain financial advisers had agreed to reduce advisory fees for clients, but did not enter the reductions into the billing system."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001763",
            "v7u_N001764"
          ],
          "source_quote": "In August of 2023, the SEC charged two non-bank affiliates of Wells Fargo... for overcharging... The SEC's investigation revealed that certain financial advisers had agreed to reduce advisory fees for clients, but did not enter the reductions into the billing system."
        },
        {
          "relation_id": "r003",
          "kind": "sequence",
          "before_element_id": "e003",
          "after_element_id": "e004",
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001763",
            "v7u_N001765"
          ],
          "source_quote": "In August of 2023, the SEC charged... Wells Fargo consented to pay a US$35 million civil penalty to resolve the issue on behalf of its affiliates."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "OCC如何因富国银行反洗钱控制缺陷发出执法行动？",
      "title": "OCC因富国银行金融犯罪风险管理和反洗钱控制缺陷发出执法行动",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "富国银行在可疑活动报告、货币交易报告、客户尽职调查和客户身份识别项目等方面存在缺陷",
          "evidence_unit_ids": [
            "v7u_N001766"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "OCC对富国银行发出执法行动，正式协议指出具体缺陷",
          "evidence_unit_ids": [
            "v7u_N001766"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "富国银行在向中高风险新业务扩展前必须获得OCC批准",
          "evidence_unit_ids": [
            "v7u_N001766"
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
          "relation_type": "clue_supports_identification",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001766"
          ],
          "source_quote": "In September of 2024, the OCC issued an enforcement action against Wells Fargo, identifying deficiencies in the bank's financial crimes risk management and AML controls. The OCC's formal agreement highlighted issues in areas such as suspicious activity reporting, currency transaction reporting, CDD, and customer identification programs."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001766"
          ],
          "source_quote": "While the OCC did not impose monetary penalties, the agreement required Wells Fargo to obtain OCC approval before expanding into new products or services in areas of moderate or high risk."
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
      "reason": "该候选独立支持程序性关系：美联储认定富国银行制裁合规不足，并处以罚款，构成有判断和行动的业务流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选独立支持程序性关系：SEC调查发现多收费行为，随后指控并导致罚款，构成完整的执法行动流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选独立支持程序性关系：OCC识别反洗钱控制缺陷，发出执法行动并要求业务扩张前审批，构成有判断和要求的业务流程。"
    }
  ],
  "skip_reason": null
}
```
