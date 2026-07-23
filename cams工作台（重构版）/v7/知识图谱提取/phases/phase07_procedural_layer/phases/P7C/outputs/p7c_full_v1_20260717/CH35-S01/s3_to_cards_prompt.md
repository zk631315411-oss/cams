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

section_id: `CH35-S01`

section_title: `Second LOD's AFC role and its interaction with the front office`

section_text_with_unit_anchors:

```text
[v7u_N002569|2569] The second line of defense (LOD) serves as an oversight function within an organization’s governance framework.
ZH: 第二道防线在组织治理框架中承担监督职能

[v7u_N002570|2570] Although the second line operates independently from the front office, effective collaboration with the first line is essential to foster a culture of compliance.
ZH: 第二道防线独立于前台，但需有效协作以培育合规文化

[v7u_N002571|2571] Key aspects of this interaction include:
ZH: 第二道防线与前台互动的关键方面包括

[v7u_N002572|2572] Education and training: The second line approves training on regulatory requirements, risk management practices, and staff responsibilities, ensuring client-facing staff are equipped to identify risks and comply with AFC policies. External specialist providers or internal teams might develop the training.
ZH: 第二道防线审批监管要求与风险管理培训，确保前台人员具备识别风险的能力

[v7u_N002573|2573] Advisory role: The second line offers guidance on best practices, emerging risks, and compliance obligations, allowing front office staff to make informed decisions.
ZH: 第二道防线提供最佳实践、新兴风险与合规义务的咨询指导

[v7u_N002574|2574] Risk awareness: The second line emphasizes the front office’s role as risk owners through policies and procedures. This helps staff to become more vigilant and to understand their part in managing client relationship and transaction risks.
ZH: 第二道防线通过政策与程序强调前台作为风险所有者的角色

[v7u_N002575|2575] An established culture of compliance offers several benefits, including:
ZH: 成熟的合规文化带来的益处包括

[v7u_N002576|2576] Informed decision-making: When front office staff understand their risk ownership responsibilities and are well-supported to manage risk, they can make informed decisions that help protect the organization from the threat of financial crime.
ZH: 前台人员理解风险所有权后能做出明智决策，保护组织免受金融犯罪威胁

[v7u_N002577|2577] Ownership of risk: Supporting front office personnel to understand financial crime risks throughout the client journey ensures that they take ownership of and manage those risks effectively.
ZH: 支持前台人员理解客户旅程中的金融犯罪风险，确保其有效承担风险管理责任

[v7u_N002578|2578] Prevention of issues: Second line and front office collaboration helps prevent compliance violations and associated reputational and financia risks.
ZH: 第二道防线与前台协作有助于预防合规违规及声誉与财务风险

[v7u_N002579|2579] Organizations often use responsible, accountable, consulted, and informed (RACI) matrices to clarify roles and responsibilities in risk ownership. These matrices define the relationships between teams, including those between the first and second lines. The RACI framework assigns specific roles, outlines who is responsible for managing risks, and who should be consulted or informed in risk-related decision-making.
ZH: RACI矩阵用于明确风险所有权中的角色与职责，定义第一道与第二道防线的关系

[v7u_N002580|2580] The RACI matrix reinforces the front office’s role in identifying, assessing, and managing risks.
ZH: RACI矩阵强化前台在识别、评估和管理风险中的角色

[v7u_N002581|2581] While the second line provides advice, guidance, and oversight, final decisions regarding client onboarding or relationship termination usually lie with the front office risk owners or relevant committees.
ZH: 第二道防线提供建议和监督，但客户准入或关系终止的最终决策权通常属于前台风险负责人或相关委员会。

[v7u_N002582|2582] In practice, committees with quorums that include both first- and second-line leaders often make business decisions about regulatory obligations related to business activities.
ZH: 由第一道和第二道防线负责人组成的委员会通常共同做出涉及监管义务的业务决策。

[v7u_N002583|2583] The second line should ensure that front office staff are equipped with the necessary tools to make informed choices, thus reinforcing collaborative decision-making.
ZH: 第二道防线应确保前台人员具备做出知情决策的必要工具，以加强协作决策。
```

allowed_unit_ids:

```json
[
  "v7u_N002569",
  "v7u_N002570",
  "v7u_N002571",
  "v7u_N002572",
  "v7u_N002573",
  "v7u_N002574",
  "v7u_N002575",
  "v7u_N002576",
  "v7u_N002577",
  "v7u_N002578",
  "v7u_N002579",
  "v7u_N002580",
  "v7u_N002581",
  "v7u_N002582",
  "v7u_N002583"
]
```

## S2 Process IR

```json
{
  "section_id": "CH35-S01",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "第二道防线通过审批培训如何确保前台具备识别风险的AFC能力？",
      "title": "第二道防线审批培训以确保前台风险识别能力",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "第二道防线审批培训",
          "evidence_unit_ids": [
            "v7u_N002572"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "前台人员具备识别风险和遵守反金融犯罪政策的能力",
          "evidence_unit_ids": [
            "v7u_N002572"
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
            "v7u_N002572"
          ],
          "source_quote": "Education and training: The second line approves training on regulatory requirements, risk management practices, and staff responsibilities, ensuring client-facing staff are equipped to identify risks and comply with AFC policies. External specialist providers or internal teams might develop the training."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "第二道防线提供咨询指导如何使前台做出知情决策？",
      "title": "第二道防线提供咨询指导以赋能前台知情决策",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "第二道防线提供关于最佳实践、新兴风险和合规义务的咨询指导",
          "evidence_unit_ids": [
            "v7u_N002573"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "前台人员做出知情决策",
          "evidence_unit_ids": [
            "v7u_N002573"
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
            "v7u_N002573"
          ],
          "source_quote": "Advisory role: The second line offers guidance on best practices, emerging risks, and compliance obligations, allowing front office staff to make informed decisions."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "第二道防线如何通过政策程序提升前台的风险意识和职责理解？",
      "title": "第二道防线通过政策程序强化前台风险所有者角色以提高警惕和职责理解",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "第二道防线通过政策和程序强调前台的风险所有者角色",
          "evidence_unit_ids": [
            "v7u_N002574"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "员工更加警惕并理解其在管理客户关系和交易风险中的职责",
          "evidence_unit_ids": [
            "v7u_N002574"
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
          "qualifier": "helps_achieve",
          "evidence_unit_ids": [
            "v7u_N002574"
          ],
          "source_quote": "Risk awareness: The second line emphasizes the front office’s role as risk owners through policies and procedures. This helps staff to become more vigilant and to understand their part in managing client relationship and transaction risks."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "实践中，委员会如何就涉及监管义务的业务活动做出决策？",
      "title": "第一和第二道防线委员会就监管义务业务做出决策",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "涉及监管义务的业务决策",
          "evidence_unit_ids": [
            "v7u_N002582"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "委员会（包括第一道和第二道防线负责人）做出决策",
          "evidence_unit_ids": [
            "v7u_N002582"
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
          "condition": "涉及与业务活动相关的监管义务",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002582"
          ],
          "source_quote": "In practice, committees with quorums that include both first- and second-line leaders often make business decisions about regulatory obligations related to business activities."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "第二道防线通过确保前台配备必要工具如何加强协作决策？",
      "title": "第二道防线确保前台配备工具以加强协作决策",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "第二道防线应确保前台人员具备做出知情决策的必要工具",
          "evidence_unit_ids": [
            "v7u_N002583"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "加强协作决策",
          "evidence_unit_ids": [
            "v7u_N002583"
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
            "v7u_N002583"
          ],
          "source_quote": "The second line should ensure that front office staff are equipped with the necessary tools to make informed choices, thus reinforcing collaborative decision-making."
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
      "reason": "该候选描述了第二道防线审批培训以确保前台能力的程序性动作和目的结果。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了第二道防线提供咨询指导使前台做出知情决策的程序性动作和目的结果。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述了第二道防线通过政策程序强调风险所有者角色以提高警惕和职责理解的程序性动作和目的结果。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "原文明是一个关于第二道防线提供建议与最终决策权归属的静态职责陈述，没有体现程序性迁移或判断过程。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选描述了委员会在涉及监管义务的业务活动中做出决策的程序性动作。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选描述了第二道防线确保前台配备工具以加强协作决策的程序性动作和目的结果。"
    }
  ],
  "skip_reason": null
}
```
