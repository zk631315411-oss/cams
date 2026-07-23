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

section_id: `CH19-S03`

section_title: `Financial Action Task Force > FATF Recommendations 9-23`

section_text_with_unit_anchors:

```text
[v7u_N001353|1353] FATF Recommendations 9 to 23 seek to ensure the effectiveness of member jurisdictions' measures to detect and prevent illicit financial activities.
ZH: FATF建议9至23旨在确保成员国有效检测和预防非法金融活动

[v7u_N001354|1354] Recommendation 9 advises jurisdictions to ensure that financial institution secrecy laws do not inhibit the implementation of FATF Recommendations.
ZH: FATF建议9要求金融机构保密法不得阻碍FATF建议的实施

[v7u_N001355|1355] Recommendations 10 and 11 require financial institutions to conduct CDD when initiating business relationships, processing occasional transactions above a set threshold, suspecting money laundering or terrorist financing, or questioning the accuracy of previously obtained customer identification data.
ZH: FATF建议10和11规定客户尽职调查的触发情形

[v7u_N001356|1356] Financial institutions should also retain transaction records and CDD information for at least five years to ensure timely compliance with requests from relevant authorities.
ZH: 金融机构应将交易记录和客户尽职调查信息保存至少五年

[v7u_N001357|1357] Recommendations 12 to 16 provide additional measures for specific customers and activities.
ZH: FATF建议12至16针对特定客户和活动规定了额外措施

[v7u_N001358|1358] For instance, financial institutions should identify PEPs, obtain senior management approval to establish a business relationship with a PEP, and verify their sources of wealth and funds.
ZH: 金融机构需识别政治敏感人物并验证其财富和资金来源

[v7u_N001359|1359] Financial institutions should assess respondent institutions’ AML/CFT controls before initiating a correspondent relationship.
ZH: 金融机构在建立代理行关系前应评估代理行的反洗钱/反恐怖融资管控措施

[v7u_N001360|1360] Money or value transfer service providers should be licensed and monitored.
ZH: 货币或价值转移服务提供商须获得许可并接受监管

[v7u_N001361|1361] Financial institutions should assess risks from new technologies and ensure accurate originator and beneficiary data in wire transfers.
ZH: 金融机构需评估新技术风险并确保电汇中发端人和受益人数据准确

[v7u_N001362|1362] Recommendations 17 to 19 advise jurisdictions to allow financial institutions to rely on third-party CDD if it meets certain criteria.
ZH: FATF建议17-19允许金融机构在满足条件时依赖第三方客户尽职调查

[v7u_N001363|1363] Financial institutions should implement AML/CFT programs, facilitate the sharing of information for AML/CFT purposes, and apply enhanced due diligence to business relationships and transactions with persons and institutions from jurisdictions FATF identifies as higher risk.
ZH: 金融机构应实施反洗钱/反恐怖融资计划并对高风险辖区强化尽职调查

[v7u_N001364|1364] Recommendations 20 to 23 discuss the obligation to report suspicious transactions. Financial institutions should report suspicious transactions to the relevant Financial Intelligence Unit (FIU).
ZH: 金融机构有义务向金融情报机构报告可疑交易

[v7u_N001365|1365] Laws should protect financial institutions and their employees from liability and prohibit them from disclosing suspicious transactions.
ZH: 法律应保护金融机构及其员工免于责任并禁止披露可疑交易

[v7u_N001366|1366] Designated nonfinancial businesses and professions (DNFBP) should implement internal controls, report suspicious transactions, and be subject to regulatory and supervisory measures to ensure compliance with AML/CFT requirements.
ZH: 指定非金融行业和职业需实施内部控制、报告可疑交易并接受监管
```

allowed_unit_ids:

```json
[
  "v7u_N001353",
  "v7u_N001354",
  "v7u_N001355",
  "v7u_N001356",
  "v7u_N001357",
  "v7u_N001358",
  "v7u_N001359",
  "v7u_N001360",
  "v7u_N001361",
  "v7u_N001362",
  "v7u_N001363",
  "v7u_N001364",
  "v7u_N001365",
  "v7u_N001366"
]
```

## S2 Process IR

```json
{
  "section_id": "CH19-S03",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "何时需要进行客户尽职调查？",
      "title": "触发客户尽职调查的情形",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Initiating business relationships, processing occasional transactions above a set threshold, suspecting money laundering or terrorist financing, or questioning the accuracy of previously obtained customer identification data",
          "evidence_unit_ids": [
            "v7u_N001355"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Financial institutions should conduct CDD",
          "evidence_unit_ids": [
            "v7u_N001355"
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
          "condition": "when any of the triggering events occur",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001355"
          ],
          "source_quote": "Recommendations 10 and 11 require financial institutions to conduct CDD when initiating business relationships, processing occasional transactions above a set threshold, suspecting money laundering or terrorist financing, or questioning the accuracy of previously obtained customer identification data."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "金融机构应如何处理交易记录和CDD信息？",
      "title": "保留交易记录和CDD信息以确保响应合规",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "Financial institutions should retain transaction records and CDD information for at least five years",
          "evidence_unit_ids": [
            "v7u_N001356"
          ],
          "modality": "optional"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "To ensure timely compliance with requests from relevant authorities",
          "evidence_unit_ids": [
            "v7u_N001356"
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
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001356"
          ],
          "source_quote": "to ensure timely compliance with requests from relevant authorities"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "针对PEP应采取哪些强化措施？",
      "title": "PEP识别、批准和验证流程",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "Financial institutions should identify PEPs",
          "evidence_unit_ids": [
            "v7u_N001358"
          ],
          "modality": "optional"
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Financial institutions should obtain senior management approval to establish a business relationship with a PEP",
          "evidence_unit_ids": [
            "v7u_N001358"
          ],
          "modality": "optional"
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "Financial institutions should verify PEPs' sources of wealth and funds",
          "evidence_unit_ids": [
            "v7u_N001358"
          ],
          "modality": "optional"
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
            "v7u_N001358"
          ],
          "source_quote": "financial institutions should identify PEPs, obtain senior management approval to establish a business relationship with a PEP, and verify their sources of wealth and funds."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001358"
          ],
          "source_quote": "financial institutions should identify PEPs, obtain senior management approval to establish a business relationship with a PEP, and verify their sources of wealth and funds."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "建立代理行关系前应如何评估对方？",
      "title": "评估代理行AML/CFT控制",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Before initiating a correspondent relationship",
          "evidence_unit_ids": [
            "v7u_N001359"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Financial institutions should assess respondent institutions’ AML/CFT controls",
          "evidence_unit_ids": [
            "v7u_N001359"
          ],
          "modality": "optional"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": "before initiating a correspondent relationship",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001359"
          ],
          "source_quote": "before initiating a correspondent relationship"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_007"
      ],
      "focal_question": "新技术带来了哪些风险？",
      "title": "评估新技术风险",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "New technologies",
          "evidence_unit_ids": [
            "v7u_N001361"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Financial institutions should assess risks from new technologies",
          "evidence_unit_ids": [
            "v7u_N001361"
          ],
          "modality": "optional"
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
            "v7u_N001361"
          ],
          "source_quote": "assess risks from new technologies"
        }
      ],
      "split_reason": "Candidate s1c_007 mentions two independent obligations: assessing new technology risks and ensuring accurate wire transfer data. They are split into separate episodes as they address different business questions."
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_007"
      ],
      "focal_question": "如何确保电汇数据的准确性？",
      "title": "确保电汇数据准确",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Wire transfers",
          "evidence_unit_ids": [
            "v7u_N001361"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Financial institutions should ensure accurate originator and beneficiary data in wire transfers",
          "evidence_unit_ids": [
            "v7u_N001361"
          ],
          "modality": "optional"
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
            "v7u_N001361"
          ],
          "source_quote": "ensure accurate originator and beneficiary data in wire transfers"
        }
      ],
      "split_reason": "Candidate s1c_007 mentions two independent obligations: assessing new technology risks and ensuring accurate wire transfer data. They are split into separate episodes as they address different business questions."
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_008"
      ],
      "focal_question": "何时可以依赖第三方CDD？",
      "title": "依赖第三方CDD的条件",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Third-party CDD meets certain criteria",
          "evidence_unit_ids": [
            "v7u_N001362"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Financial institutions may rely on third-party CDD",
          "evidence_unit_ids": [
            "v7u_N001362"
          ],
          "modality": "permitted"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": "if it meets certain criteria",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001362"
          ],
          "source_quote": "if it meets certain criteria"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_008",
      "source_candidate_ids": [
        "s1c_009"
      ],
      "focal_question": "对高风险辖区的客户应如何处置？",
      "title": "对高风险辖区强化尽职调查",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Business relationships and transactions with persons and institutions from jurisdictions FATF identifies as higher risk",
          "evidence_unit_ids": [
            "v7u_N001363"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Financial institutions should apply enhanced due diligence",
          "evidence_unit_ids": [
            "v7u_N001363"
          ],
          "modality": "optional"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": "when dealing with persons and institutions from higher-risk jurisdictions",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001363"
          ],
          "source_quote": "apply enhanced due diligence to business relationships and transactions with persons and institutions from jurisdictions FATF identifies as higher risk"
        }
      ],
      "split_reason": "Candidate s1c_009 covers multiple obligations; this episode captures the enhanced due diligence requirement. Other obligations (implement AML/CFT programs, facilitate information sharing) are excluded as they lack procedural specificity to form a standalone episode."
    },
    {
      "episode_id": "ep_009",
      "source_candidate_ids": [
        "s1c_010"
      ],
      "focal_question": "发现可疑交易时应如何处理？",
      "title": "报告可疑交易给金融情报机构",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Suspicious transactions identified",
          "evidence_unit_ids": [
            "v7u_N001364"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Financial institutions should report suspicious transactions to the relevant Financial Intelligence Unit (FIU)",
          "evidence_unit_ids": [
            "v7u_N001364"
          ],
          "modality": "optional"
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
            "v7u_N001364"
          ],
          "source_quote": "report suspicious transactions to the relevant Financial Intelligence Unit (FIU)"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_010",
      "source_candidate_ids": [
        "s1c_012"
      ],
      "focal_question": "DNFBP应如何确保AML/CFT合规？",
      "title": "DNFBP的AML/CFT合规要求",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "DNFBP should implement internal controls",
          "evidence_unit_ids": [
            "v7u_N001366"
          ],
          "modality": "optional"
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "DNFBP should report suspicious transactions",
          "evidence_unit_ids": [
            "v7u_N001366"
          ],
          "modality": "optional"
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "DNFBP should be subject to regulatory and supervisory measures",
          "evidence_unit_ids": [
            "v7u_N001366"
          ],
          "modality": "optional"
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "To ensure compliance with AML/CFT requirements",
          "evidence_unit_ids": [
            "v7u_N001366"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001366"
          ],
          "source_quote": "to ensure compliance with AML/CFT requirements"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001366"
          ],
          "source_quote": "to ensure compliance with AML/CFT requirements"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001366"
          ],
          "source_quote": "to ensure compliance with AML/CFT requirements"
        }
      ],
      "split_reason": null
    }
  ],
  "candidate_audit": [
    {
      "candidate_id": "s1c_001",
      "disposition": "ungraphable",
      "episode_ids": [],
      "reason": "原文建议司法管辖区确保保密法不阻碍FATF建议实施，但未提供具体程序步骤或判断过程，无法构建连通流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "候选提供了明确的触发条件和动作，构成了CDD触发流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "保留记录的动作并有确保合规的目的，构成流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "针对PEP的一系列措施构成清晰的流程。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "建立代理行关系前的评估动作构成流程。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "对货币或价值转移服务提供商的许可和监控要求是静态义务，没有描述具体业务程序或判断。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005",
        "ep_006"
      ],
      "reason": "候选包含两个独立义务：评估新技术风险和确保电汇数据准确，分别构成独立流程，因此拆分。"
    },
    {
      "candidate_id": "s1c_008",
      "disposition": "mapped",
      "episode_ids": [
        "ep_007"
      ],
      "reason": "条件性允许依赖第三方CDD构成判断流程。"
    },
    {
      "candidate_id": "s1c_009",
      "disposition": "mapped",
      "episode_ids": [
        "ep_008"
      ],
      "reason": "候选中的强化尽职调查部分构成流程，其余（实施计划、信息共享）为静态义务，被排除。"
    },
    {
      "candidate_id": "s1c_010",
      "disposition": "mapped",
      "episode_ids": [
        "ep_009"
      ],
      "reason": "报告可疑交易的义务构成流程。"
    },
    {
      "candidate_id": "s1c_011",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "法律保护免于责任和禁止披露的要求属于法律层面的保护规定，不是机构执行的业务流程。"
    },
    {
      "candidate_id": "s1c_012",
      "disposition": "mapped",
      "episode_ids": [
        "ep_010"
      ],
      "reason": "针对DNFBP的AML合规措施构成流程。"
    }
  ],
  "skip_reason": null
}
```
