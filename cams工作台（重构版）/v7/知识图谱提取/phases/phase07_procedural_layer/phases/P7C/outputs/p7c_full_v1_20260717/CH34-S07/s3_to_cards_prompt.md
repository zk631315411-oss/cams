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

section_id: `CH34-S07`

section_title: `Three lines of defense > Compliance monitoring and testing`

section_text_with_unit_anchors:

```text
[v7u_N002472|2472] Compliance monitoring and testing assess the effectiveness of organizational processes, particularly in terms of compliance and risk management. This function is meant to ensure that policies and procedures are properly executed and continuously improved. Its primary responsibilities include reviewing the execution of policies and procedures and identifying any gaps and improvement areas across both the first and second lines.
ZH: 合规监控与测试职能评估组织流程的有效性，确保政策和程序得到正确执行并持续改进。

[v7u_N002473|2473] QA audits actions to ensure alignment with guidelines and regulatory requirements. These reviews confirm that departments follow internal controls and risk management strategies, identifying any deviations from expected practices.
ZH: 质量保证（QA）审计确保行动符合指南和监管要求，确认部门遵循内部控制与风险管理策略。

[v7u_N002474|2474] QA serves as a checks-and-balances function, seeking gaps or deficiencies in policies and procedures execution.
ZH: QA作为制衡职能，发现政策和程序执行中的差距或缺陷。

[v7u_N002475|2475] This helps mitigate risks from insufficient adherence to standards.
ZH: QA有助于缓释因标准遵循不足而产生的风险。

[v7u_N002476|2476] Through periodic assessments and audits, QA identifies trends that signify underlying issues, which may require policy adjustments or additional staff training.
ZH: QA通过定期评估和审计识别趋势，发现潜在问题，可能需要调整政策或加强培训。

[v7u_N002477|2477] QA monitors backlogs of tasks or cases that should be resolved within specific timelines. It evaluates whether these backlogs indicate process inefficiencies or resource constraints. Analyzing performance data against benchmarks allows QA to determine whether processes are effective or need reengineering to improve efficiency.
ZH: QA监控任务积压情况，评估流程效率或资源限制，分析绩效数据以确定是否需要流程再造。

[v7u_N002478|2478] QA maintains thorough documentation of audit, assessment, and review findings. This documentation serves as a compliance record and a resource for continuous improvement.
ZH: QA维护审计、评估和审查结果的详细文档，作为合规记录和持续改进的资源。

[v7u_N002479|2479] Regular reports to leadership highlight trends, compliance gaps, and corrective actions, providing decision-making information.
ZH: QA定期向领导层报告趋势、合规差距和纠正措施，提供决策信息。

[v7u_N002480|2480] QA helps identify areas needing improvement and guides the development of targeted staff training programs.
ZH: QA帮助识别需要改进的领域，并指导制定有针对性的员工培训计划。

[v7u_N002481|2481] QA promotes communication between departments on compliance issues, procedural discrepancies, and best practices. This collaborative environment enables departments to share insights and develop strategies to improve processes.
ZH: 质量保证促进部门间合规沟通与协作

[v7u_N002482|2482] QA plays a critical role in enhancing organizational integrity and efficiency. Specifically, QA functions aim to:
ZH: 质量保证在提升组织诚信与效率方面发挥关键作用，其功能旨在：

[v7u_N002483|2483] Enhance compliance: By verifying adherence to regulations and internal policies, QA helps avoid legal penalties and reputational damage.
ZH: 质量保证通过验证合规性帮助避免法律处罚和声誉损害

[v7u_N002484|2484] Improve efficiency: By identifying operational inefficiencies to streamline processes, QA optimizes resource allocation and improves service delivery.
ZH: 质量保证通过识别运营低效来优化资源配置和服务交付

[v7u_N002485|2485] Boost accountability: By introducing oversight to foster a culture of accountability. QA helps employees understand the importance of their roles within the broader context of compliance.
ZH: 质量保证通过监督促进问责文化，帮助员工理解其角色在合规中的重要性

[v7u_N002486|2486] Drive continuous improvement: The iterative nature of QA assessments supports ongoing improvements, ensuring that policies remain relevant and effective in managing emerging risks.
ZH: 质量保证的迭代评估推动持续改进，确保政策有效管理新兴风险
```

allowed_unit_ids:

```json
[
  "v7u_N002472",
  "v7u_N002473",
  "v7u_N002474",
  "v7u_N002475",
  "v7u_N002476",
  "v7u_N002477",
  "v7u_N002478",
  "v7u_N002479",
  "v7u_N002480",
  "v7u_N002481",
  "v7u_N002482",
  "v7u_N002483",
  "v7u_N002484",
  "v7u_N002485",
  "v7u_N002486"
]
```

## S2 Process IR

```json
{
  "section_id": "CH34-S07",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "QA如何通过审计确保合规并识别偏差以缓释风险？",
      "title": "QA审计与审查确保合规并识别偏差以缓释风险",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "QA执行审计与审查",
          "evidence_unit_ids": [
            "v7u_N002473"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "指南、监管要求、内部控制与风险管理策略",
          "evidence_unit_ids": [
            "v7u_N002473"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "识别出预期做法的偏差及政策程序执行中的差距或缺陷",
          "evidence_unit_ids": [
            "v7u_N002473",
            "v7u_N002474"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "缓释标准遵循不足产生的风险",
          "evidence_unit_ids": [
            "v7u_N002475"
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
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002473"
          ],
          "source_quote": "QA audits actions to ensure alignment with guidelines and regulatory requirements."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002473",
            "v7u_N002474"
          ],
          "source_quote": "QA audits actions to ensure alignment with guidelines and regulatory requirements. These reviews confirm that departments follow internal controls and risk management strategies, identifying any deviations from expected practices."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": "conclusion_triggers_response",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002475"
          ],
          "source_quote": "This helps mitigate risks from insufficient adherence to standards."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "QA如何通过定期评估识别趋势并推动政策调整或培训？",
      "title": "QA通过定期评估识别趋势推动政策调整与培训",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "定期评估与审计",
          "evidence_unit_ids": [
            "v7u_N002476"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "QA识别出指示潜在问题的趋势",
          "evidence_unit_ids": [
            "v7u_N002476"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "可能需要政策调整或增加员工培训",
          "evidence_unit_ids": [
            "v7u_N002476"
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
            "v7u_N002476"
          ],
          "source_quote": "Through periodic assessments and audits, QA identifies trends that signify underlying issues"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N002476"
          ],
          "source_quote": "Through periodic assessments and audits, QA identifies trends that signify underlying issues, which may require policy adjustments or additional staff training."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "QA如何通过监控积压和分析绩效数据确定流程再造需求？",
      "title": "QA监控积压与分析绩效数据确定流程再造需求",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "应在规定时限内解决的任务或案例出现积压",
          "evidence_unit_ids": [
            "v7u_N002477"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "QA监控积压并评估是否指示流程低效或资源限制",
          "evidence_unit_ids": [
            "v7u_N002477"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "对照基准分析绩效数据",
          "evidence_unit_ids": [
            "v7u_N002477"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "decision",
          "label": "确定流程是否有效或是否需要再造以提升效率",
          "evidence_unit_ids": [
            "v7u_N002477"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "识别出需要流程再造",
          "evidence_unit_ids": [
            "v7u_N002477"
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
            "v7u_N002477"
          ],
          "source_quote": "QA monitors backlogs of tasks or cases that should be resolved within specific timelines."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002477"
          ],
          "source_quote": "It evaluates whether these backlogs indicate process inefficiencies or resource constraints. Analyzing performance data against benchmarks allows QA to determine whether processes are effective or need reengineering to improve efficiency."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002477"
          ],
          "source_quote": "Analyzing performance data against benchmarks allows QA to determine whether processes are effective or need reengineering to improve efficiency."
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e004",
          "outcome_element_id": "e005",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002477"
          ],
          "source_quote": "determine whether processes are effective or need reengineering"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "QA如何将审计发现记录为文档并服务于合规与持续改进？",
      "title": "QA维护审计发现文档作为合规记录与改进资源",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "审计、评估和审查发现",
          "evidence_unit_ids": [
            "v7u_N002478"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "QA维护审计、评估和审查发现的详细文档",
          "evidence_unit_ids": [
            "v7u_N002478"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "文档作为合规记录和持续改进的资源",
          "evidence_unit_ids": [
            "v7u_N002478"
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
            "v7u_N002478"
          ],
          "source_quote": "QA maintains thorough documentation of audit, assessment, and review findings."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": "component_assembles_product",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002478"
          ],
          "source_quote": "This documentation serves as a compliance record and a resource for continuous improvement."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "QA如何通过定期报告为领导层提供决策信息？",
      "title": "QA定期报告向领导层提供决策信息",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "QA定期向领导层报告",
          "evidence_unit_ids": [
            "v7u_N002479"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "报告突出趋势、合规差距和纠正措施，提供决策信息",
          "evidence_unit_ids": [
            "v7u_N002479"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002479"
          ],
          "source_quote": "Regular reports to leadership highlight trends, compliance gaps, and corrective actions, providing decision-making information."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "QA如何识别需改进领域并指导制定针对性培训计划？",
      "title": "QA识别改进领域并指导制定员工培训计划",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "QA帮助识别需要改进的领域",
          "evidence_unit_ids": [
            "v7u_N002480"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "QA指导制定有针对性的员工培训计划",
          "evidence_unit_ids": [
            "v7u_N002480"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "有针对性的员工培训计划",
          "evidence_unit_ids": [
            "v7u_N002480"
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
            "v7u_N002480"
          ],
          "source_quote": "QA helps identify areas needing improvement and guides the development of targeted staff training programs."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002480"
          ],
          "source_quote": "guides the development of targeted staff training programs."
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
      "reason": "候选提供了QA审计确保合规、识别偏差并缓释风险的完整程序性关系。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "候选描述了QA通过定期评估识别趋势并可能触发政策调整或培训的程序性路径。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "候选包含QA监控积压、分析绩效并确定流程再造需求的判断性过程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "候选构成QA维护文档并将审计发现转化为合规记录与改进资源的动作-结果链。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "候选明确了QA通过定期报告向领导层传递趋势、差距和纠正措施并提供决策信息的流程。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "候选呈现了QA识别改进领域并指导培训计划制定的顺序动作与产出。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "候选描述QA促进部门沟通与协作，形成协作环境，未构成具体的程序性判断或处理过程，属于一般性职能或益处描述。"
    }
  ],
  "skip_reason": null
}
```
