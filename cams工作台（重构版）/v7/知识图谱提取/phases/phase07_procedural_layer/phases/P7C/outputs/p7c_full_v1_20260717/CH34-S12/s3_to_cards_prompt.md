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

section_id: `CH34-S12`

section_title: `Three lines of defense > Functions of board of directors and management oversight`

section_text_with_unit_anchors:

```text
[v7u_N002556|2556] The board of directors plays a critical role in the governance and oversight of a financial institution’s AFC program. It approves the risk appetite, the scope, objectives, and responsibilities of the AFC compliance function.
ZH: 董事会在金融机构金融犯罪防控计划的治理和监督中发挥关键作用。

[v7u_N002557|2557] To demonstrate commitment to compliance and managing financial crime risks, the board must endorse the AFC program.
ZH: 董事会必须批准金融犯罪防控计划以展示对合规和风险管理的承诺。

[v7u_N002558|2558] This endorsement emphasizes AFC initiatives throughout the organization and fosters a culture of compliance.
ZH: 董事会的认可强调金融犯罪防控举措并培养合规文化。

[v7u_N002559|2559] The board should establish a dedicated AML or risk management committee with knowledgeable members to monitor implementation, review policies, and ensure adequate resources for compliance.
ZH: 董事会应设立专门的反洗钱或风险管理委员会，配备有知识的成员以监督实施和审查政策。

[v7u_N002560|2560] In addition, the board provides strategic direction for the AFC program, aligning it with the organization’s risk appetite. It assesses emerging risks and AFC control effectiveness, guiding management on any necessary adjustments. Ultimately, the board is accountable for the program's effectiveness and must ensure that any deficiencies are addressed promptly.
ZH: 董事会为金融犯罪防控计划提供战略方向，评估新兴风险，并确保及时解决缺陷。

[v7u_N002561|2561] The board and senior management play complementary roles in the effectiveness of an AFC program. Their collaboration, supported by a strong governance structure, is critical for mitigating financial crime risks and ensuring organizational integrity.
ZH: 董事会与高级管理层在金融犯罪防控中发挥互补作用

[v7u_N002562|2562] Business and operational leaders are ultimately responsible for implementing and overseeing the AFC program. They execute the program, ensure policies and procedures are integrated into operational areas, and communicate all expectations to the staff.
ZH: 业务和运营负责人负责实施和监督金融犯罪防控计划

[v7u_N002563|2563] Senior managers, often through risk management committees, are expected to monitor compliance with AFC policies and regulations.
ZH: 高级管理人员通过风险管理委员会监控金融犯罪防控合规情况

[v7u_N002564|2564] They must ensure regular reports on the program’s status, including risk assessments and any significant incidents, are submitted to the board and relevant committees.
ZH: 高级管理人员须确保向董事会定期提交金融犯罪防控计划状态报告

[v7u_N002565|2565] Management committees might review and approve reports on key performance and risk indicators, high-risk onboarding and exits, and compliance assessments, ensuring accuracy and transparency.
ZH: 管理委员会审查并批准关键绩效指标、高风险准入与退出及合规评估报告

[v7u_N002566|2566] Senior managers are responsible for any failures in the AFC program, addressing compliance deficiencies, ensuring that corrective actions are implemented, and reporting progress to the board.
ZH: 高级管理人员对金融犯罪防控计划的任何失败负责，并落实整改措施

[v7u_N002567|2567] A robust governance structure is essential for an effective AFC program.
ZH: 稳健的治理结构是有效金融犯罪防控计划的基础

[v7u_N002568|2568] Key benefits include clarity of roles and responsibilities, enhanced accountability, effective oversight and monitoring, promoting a culture of compliance, and adaptability to regulatory changes.
ZH: 稳健治理的关键益处包括职责清晰、问责增强、有效监督及合规文化
```

allowed_unit_ids:

```json
[
  "v7u_N002556",
  "v7u_N002557",
  "v7u_N002558",
  "v7u_N002559",
  "v7u_N002560",
  "v7u_N002561",
  "v7u_N002562",
  "v7u_N002563",
  "v7u_N002564",
  "v7u_N002565",
  "v7u_N002566",
  "v7u_N002567",
  "v7u_N002568"
]
```

## S2 Process IR

```json
{
  "section_id": "CH34-S12",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "董事会如何通过批准AFC计划展示合规承诺并培养文化？",
      "title": "批准AFC计划以展示承诺及强化举措与文化",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "董事会必须批准AFC计划",
          "evidence_unit_ids": [
            "v7u_N002557"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "展示对合规和风险管理的承诺",
          "evidence_unit_ids": [
            "v7u_N002557"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "强调整个组织的AFC举措",
          "evidence_unit_ids": [
            "v7u_N002558"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "培养合规文化",
          "evidence_unit_ids": [
            "v7u_N002558"
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
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002557"
          ],
          "source_quote": "To demonstrate commitment to compliance and managing financial crime risks, the board must endorse the AFC program.",
          "trigger_mode": null,
          "condition": null,
          "trigger_element_id": null,
          "before_element_id": null,
          "after_element_id": null,
          "auxiliary_element_id": null,
          "decision_element_id": null,
          "target_element_id": null,
          "result_element_id": null
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002558"
          ],
          "source_quote": "This endorsement emphasizes AFC initiatives throughout the organization",
          "trigger_mode": null,
          "condition": null,
          "trigger_element_id": null,
          "before_element_id": null,
          "after_element_id": null,
          "auxiliary_element_id": null,
          "decision_element_id": null,
          "target_element_id": null,
          "result_element_id": null
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e004",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002558"
          ],
          "source_quote": "and fosters a culture of compliance.",
          "trigger_mode": null,
          "condition": null,
          "trigger_element_id": null,
          "before_element_id": null,
          "after_element_id": null,
          "auxiliary_element_id": null,
          "decision_element_id": null,
          "target_element_id": null,
          "result_element_id": null
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "董事会如何设立专门委员会以加强实施监督与资源保障？",
      "title": "设立专门AML/风险管理委员会以监督审查和确保资源",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "董事会应设立专门AML或风险管理委员会",
          "evidence_unit_ids": [
            "v7u_N002559"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "委员会由有知识成员组成",
          "evidence_unit_ids": [
            "v7u_N002559"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "监督实施",
          "evidence_unit_ids": [
            "v7u_N002559"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "审查政策",
          "evidence_unit_ids": [
            "v7u_N002559"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "确保充足的合规资源",
          "evidence_unit_ids": [
            "v7u_N002559"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002559"
          ],
          "source_quote": "with knowledgeable members",
          "trigger_mode": null,
          "condition": null,
          "trigger_element_id": null,
          "before_element_id": null,
          "after_element_id": null,
          "outcome_element_id": null,
          "decision_element_id": null,
          "target_element_id": null,
          "result_element_id": null
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002559"
          ],
          "source_quote": "to monitor implementation",
          "trigger_mode": null,
          "condition": null,
          "trigger_element_id": null,
          "before_element_id": null,
          "after_element_id": null,
          "auxiliary_element_id": null,
          "decision_element_id": null,
          "target_element_id": null,
          "result_element_id": null
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e004",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002559"
          ],
          "source_quote": "review policies",
          "trigger_mode": null,
          "condition": null,
          "trigger_element_id": null,
          "before_element_id": null,
          "after_element_id": null,
          "auxiliary_element_id": null,
          "decision_element_id": null,
          "target_element_id": null,
          "result_element_id": null
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e005",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002559"
          ],
          "source_quote": "ensure adequate resources for compliance",
          "trigger_mode": null,
          "condition": null,
          "trigger_element_id": null,
          "before_element_id": null,
          "after_element_id": null,
          "auxiliary_element_id": null,
          "decision_element_id": null,
          "target_element_id": null,
          "result_element_id": null
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "高级管理人员如何确保状态报告提交给董事会？",
      "title": "确保定期提交AFC计划状态报告至董事会",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "高级管理人员必须确保定期提交AFC计划状态报告",
          "evidence_unit_ids": [
            "v7u_N002564"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "提交报告给董事会和相关委员会，报告包含风险评估和重大事件",
          "evidence_unit_ids": [
            "v7u_N002564"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002564"
          ],
          "source_quote": "They must ensure regular reports on the program’s status, including risk assessments and any significant incidents, are submitted to the board and relevant committees.",
          "trigger_mode": null,
          "condition": null,
          "trigger_element_id": null,
          "before_element_id": null,
          "after_element_id": null,
          "auxiliary_element_id": null,
          "decision_element_id": null,
          "target_element_id": null,
          "result_element_id": null
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_007"
      ],
      "focal_question": "管理委员会如何审查批准报告以确保准确性？",
      "title": "管理委员会审查批准报告并确保准确透明",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "管理委员会可能审查和批准关键绩效、风险指标、高风险准入/退出及合规评估报告",
          "evidence_unit_ids": [
            "v7u_N002565"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "确保报告的准确性和透明度",
          "evidence_unit_ids": [
            "v7u_N002565"
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
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002565"
          ],
          "source_quote": "Management committees might review and approve reports on key performance and risk indicators, high-risk onboarding and exits, and compliance assessments, ensuring accuracy and transparency.",
          "trigger_mode": null,
          "condition": null,
          "trigger_element_id": null,
          "before_element_id": null,
          "after_element_id": null,
          "auxiliary_element_id": null,
          "decision_element_id": null,
          "target_element_id": null,
          "result_element_id": null
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_008"
      ],
      "focal_question": "高级管理人员如何处理AFC计划失败并报告进展？",
      "title": "处理合规缺陷、实施纠正措施并向董事会报告进展",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "处理合规缺陷",
          "evidence_unit_ids": [
            "v7u_N002566"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "确保实施纠正措施",
          "evidence_unit_ids": [
            "v7u_N002566"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "向董事会报告进展",
          "evidence_unit_ids": [
            "v7u_N002566"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002566"
          ],
          "source_quote": "addressing compliance deficiencies, ensuring that corrective actions are implemented",
          "trigger_mode": null,
          "condition": null,
          "trigger_element_id": null,
          "outcome_element_id": null,
          "auxiliary_element_id": null,
          "decision_element_id": null,
          "target_element_id": null,
          "result_element_id": null
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002566"
          ],
          "source_quote": "ensuring that corrective actions are implemented, and reporting progress to the board.",
          "trigger_mode": null,
          "condition": null,
          "trigger_element_id": null,
          "outcome_element_id": null,
          "auxiliary_element_id": null,
          "decision_element_id": null,
          "target_element_id": null,
          "result_element_id": null
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
      "reason": "董事会必须批准AFC计划以展示承诺、强调举措并培养文化，构成程序性动作和结果。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "董事会应设立委员会以监督、审查和确保资源，包含设立动作及多个目的性产出。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "ungraphable",
      "episode_ids": [],
      "reason": "候选包含董事会的多项战略职责（提供方向、评估风险、指导调整、确保缺陷解决），但各项之间缺乏明确的程序性连接关系，无法构建连通流程图。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述业务负责人的静态职责清单，无流程性的触发、产生或判断关系，不构成程序性流程。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "单一的监控合规动作，无前后关系或结果，仅为职责描述，不构成流程。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "高级管理人员必须确保报告提交，有强制动作及明确产出，构成流程。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "管理委员会审查批准报告并确保准确透明，构成审查流程。"
    },
    {
      "candidate_id": "s1c_008",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "高级管理人员应对失败的处理、纠正和报告，构成序列流程。"
    },
    {
      "candidate_id": "s1c_gap_ch34_s12_board_approval_risk_appetite",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "董事会批准风险偏好等是单一治理动作，无上下文或结果关系，不构成流程。"
    }
  ],
  "skip_reason": null
}
```
