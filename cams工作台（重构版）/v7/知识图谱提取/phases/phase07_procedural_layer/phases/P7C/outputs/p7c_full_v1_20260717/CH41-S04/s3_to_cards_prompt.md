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

section_id: `CH41-S04`

section_title: `Governance and oversight > Governance committees and their functions`

section_text_with_unit_anchors:

```text
[v7u_N002930|2930] Governance committees provide strategic oversight, decision-making authority, and accountability in an organization’s financial crime compliance framework. They ensure that AFC policies and procedures are aligned with regulatory requirements and risk management objectives, while supporting effective escalation, review, and enforcement processes.
ZH: 治理委员会在金融犯罪合规框架中提供战略监督、决策权和问责制，确保金融犯罪防控政策与监管要求和风险管理目标一致。

[v7u_N002931|2931] Governance committees must be structured based on an organization’s risk profile, regulatory obligations, and operational needs.
ZH: 治理委员会必须根据组织的风险状况、监管义务和运营需求进行构建。

[v7u_N002932|2932] Each committee must operate under a terms-of-reference document, which outlines its mandate, responsibilities, and authority.
ZH: 每个委员会必须依据职权范围文件运作，该文件概述其任务、职责和权力。

[v7u_N002933|2933] The committee must formally record meeting minutes for regulatory audits and internal governance reviews.
ZH: 委员会必须正式记录会议纪要，以供监管审计和内部治理审查。

[v7u_N002934|2934] Meeting minutes typically include decisions made, objections raised, and how the objections were dealt with.
ZH: 会议纪要通常包括做出的决定、提出的反对意见以及如何处理这些反对意见。

[v7u_N002935|2935] Examples of key committees include the:
ZH: 列举关键委员会的示例。

[v7u_N002936|2936] Board risk committee: This committee is typically led by one or more board members. It provides strategic oversight of AFC risks, ensuring policies align with global and jurisdictional regulations. The terms and the chair may escalate items for the board’s attention.
ZH: 董事会风险委员会由一名或多名董事会成员领导，提供金融犯罪防控风险的战略监督，确保政策符合全球和司法管辖区法规。

[v7u_N002937|2937] AML governance committee: This committee may be led by the second line and oversees enterprise-wide AML/CFT risk management, internal controls, and AML/CFT program effectiveness. It considers progress in reviewing alerts, volumes, and categories of alerts that resulted in SARs, results of audits and assurance reviews, and emerging risks.
ZH: 反洗钱治理委员会由第二道防线领导，监督企业范围内的反洗钱/反恐怖融资风险管理、内部控制及项目有效性。

[v7u_N002938|2938] High-risk customer review committee: This committee assesses onboarding and ongoing due diligence for PEPs, correspondent banks, and other high-risk clients. It is typically led by business leaders, with AFC compliance teams forming part of the quorum.
ZH: 高风险客户审查委员会评估政治敏感人物、代理行及其他高风险客户的准入和持续尽职调查，通常由业务负责人领导，金融犯罪防控合规团队构成法定人数。

[v7u_N002939|2939] Sanctions oversight committee: While AFC committees typically include sanctions oversight, there may be a need for a separate committee based on the organization’s risk exposure. It ensures compliance with global sanctions programs, watchlist screening, and escalation procedures.
ZH: 制裁监督委员会确保遵守全球制裁计划、观察名单筛查和升级程序，可根据风险暴露单独设立。

[v7u_N002940|2940] Quora for governance committees typically include:
ZH: 列举治理委员会的典型法定人数构成。

[v7u_N002941|2941] Board members or senior executives to provide strategic oversight and resource allocation for AFC compliance.
ZH: 董事会或高管为金融犯罪防控提供战略监督和资源分配

[v7u_N002942|2942] The chief compliance officer, MLRO, or their delegates to lead AFC policy execution, risk assessments, and regulatory engagement.
ZH: 首席合规官、MLRO或其代表领导金融犯罪防控政策执行、风险评估和监管沟通

[v7u_N002943|2943] The first line of defense risk owner and operational leaders who implement AFC policies in daily operations.
ZH: 第一道防线的风险负责人和运营负责人负责在日常运营中实施金融犯罪防控政策

[v7u_N002944|2944] The second line of defense to provide independent oversight, policy enforcement, and risk assessments (in addition to the MLRO, if needed).
ZH: 第二道防线提供独立监督、政策执行和风险评估

[v7u_N002945|2945] The third line of defense to report independent audits and ensure compliance effectiveness, where appropriate, while maintaining independence.
ZH: 第三道防线报告独立审计并确保合规有效性，同时保持独立性

[v7u_N002946|2946] By ensuring structured, well-documented, and effective governance committees, financial institutions strengthen AFC compliance, regulatory engagement, and risk management oversight.
ZH: 治理委员会通过结构化、文档化和有效的运作来加强金融犯罪防控合规

[v7u_N002947|2947] During regulatory exams, the robustness of the governance structure demonstrates the strength of the AML programs.
ZH: 治理结构的稳健性可作为反洗钱项目实力的指标

[v7u_N002948|2948] Examiners may request terms of reference and inputs via papers and meeting minutes, and present them as evidence of the effectiveness of the AFC program.
ZH: 监管机构可通过职权范围、会议纪要等文件评估金融犯罪防控项目的有效性
```

allowed_unit_ids:

```json
[
  "v7u_N002930",
  "v7u_N002931",
  "v7u_N002932",
  "v7u_N002933",
  "v7u_N002934",
  "v7u_N002935",
  "v7u_N002936",
  "v7u_N002937",
  "v7u_N002938",
  "v7u_N002939",
  "v7u_N002940",
  "v7u_N002941",
  "v7u_N002942",
  "v7u_N002943",
  "v7u_N002944",
  "v7u_N002945",
  "v7u_N002946",
  "v7u_N002947",
  "v7u_N002948"
]
```

## S2 Process IR

```json
{
  "section_id": "CH41-S04",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_CH41-S04_1"
      ],
      "focal_question": "如何根据组织风险状况构建治理委员会？",
      "title": "基于风险状况、监管义务和运营需求构建治理委员会",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "组织的风险状况、监管义务和运营需求",
          "evidence_unit_ids": [
            "v7u_N002931"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "构建治理委员会",
          "evidence_unit_ids": [
            "v7u_N002931"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e001",
          "evidence_unit_ids": [
            "v7u_N002931"
          ],
          "source_quote": "Governance committees must be structured based on an organization’s risk profile, regulatory obligations, and operational needs.",
          "qualifier": null
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_CH41-S04_2"
      ],
      "focal_question": "委员会如何确保依据职权范围文件运作？",
      "title": "委员会依据职权范围文件运作",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "职权范围文件（概述任务、职责和权力）",
          "evidence_unit_ids": [
            "v7u_N002932"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "委员会运作",
          "evidence_unit_ids": [
            "v7u_N002932"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e001",
          "relation_type": "standard_constrains_action",
          "evidence_unit_ids": [
            "v7u_N002932"
          ],
          "source_quote": "Each committee must operate under a terms-of-reference document, which outlines its mandate, responsibilities, and authority.",
          "qualifier": null
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_CH41-S04_3"
      ],
      "focal_question": "委员会为何必须记录会议纪要？",
      "title": "记录会议纪要以供监管审计和内部治理审查",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "正式记录会议纪要",
          "evidence_unit_ids": [
            "v7u_N002933"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "供监管审计和内部治理审查",
          "evidence_unit_ids": [
            "v7u_N002933"
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
          "evidence_unit_ids": [
            "v7u_N002933"
          ],
          "source_quote": "The committee must formally record meeting minutes for regulatory audits and internal governance reviews.",
          "qualifier": "aimed_to"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_gap_ch41_s04_sanctions_committee_need"
      ],
      "focal_question": "何时需要单独设立制裁监督委员会？",
      "title": "根据风险暴露决定是否单独设立制裁监督委员会",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "组织风险暴露",
          "evidence_unit_ids": [
            "v7u_N002939"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "可能需要单独设立制裁监督委员会",
          "evidence_unit_ids": [
            "v7u_N002939"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "确保遵守全球制裁计划、观察名单筛查和升级程序",
          "evidence_unit_ids": [
            "v7u_N002939"
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
          "evidence_unit_ids": [
            "v7u_N002939"
          ],
          "source_quote": "While AFC committees typically include sanctions oversight, there may be a need for a separate committee based on the organization’s risk exposure.",
          "qualifier": null
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "evidence_unit_ids": [
            "v7u_N002939"
          ],
          "source_quote": "It ensures compliance with global sanctions programs, watchlist screening, and escalation procedures.",
          "qualifier": "aimed_to"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_gap_ch41_s04_examiner_evidence"
      ],
      "focal_question": "检查人员如何利用治理文件评估AFC项目有效性？",
      "title": "检查人员请求文件并作为有效性证据",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "检查人员请求职权范围文件和会议纪要等输入",
          "evidence_unit_ids": [
            "v7u_N002948"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "将这些文件作为AFC项目有效性的证据",
          "evidence_unit_ids": [
            "v7u_N002948"
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
          "evidence_unit_ids": [
            "v7u_N002948"
          ],
          "source_quote": "Examiners may request terms of reference and inputs via papers and meeting minutes, and present them as evidence of the effectiveness of the AFC program.",
          "qualifier": "aimed_to"
        }
      ],
      "split_reason": null
    }
  ],
  "candidate_audit": [
    {
      "candidate_id": "s1c_CH41-S04_1",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选描述了治理委员会根据风险状况、监管义务和运营需求进行构建的程序性要求，存在动作与输入依据的合格关系。"
    },
    {
      "candidate_id": "s1c_CH41-S04_2",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了委员会必须依据职权范围文件运作的程序性要求，存在动作与标准的合格关系。"
    },
    {
      "candidate_id": "s1c_CH41-S04_3",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述了委员会必须记录会议纪要并供审计审查的程序性产出关系，存在动作与目的的合格关系。"
    },
    {
      "candidate_id": "s1c_gap_ch41_s04_sanctions_committee_need",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选描述了根据风险暴露决定是否单独设立制裁监督委员会的判断性流程，存在决策、输入与产出之间的合格关系。"
    },
    {
      "candidate_id": "s1c_gap_ch41_s04_examiner_evidence",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选描述了检查人员在监管检查中请求文件并作为证据的程序性动作，存在动作与产出的合格关系。"
    }
  ],
  "skip_reason": null
}
```
