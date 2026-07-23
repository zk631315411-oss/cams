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

section_id: `CH34-S10`

section_title: `Three lines of defense > Third line of defense AFC function`

section_text_with_unit_anchors:

```text
[v7u_N002517|2517] The third LOD in a financial institution's risk management framework is the internal audit function.
ZH: 第三道防线是金融机构风险管理框架中的内部审计职能

[v7u_N002518|2518] This line operates independently of the first two lines.
ZH: 第三道防线独立于前两道防线运作

[v7u_N002519|2519] The first line handles risk ownership and operational management, while the second line focuses on advisory, policy, and compliance monitoring.
ZH: 第一道防线负责风险所有权和运营管理，第二道防线专注于咨询、政策和合规监控

[v7u_N002520|2520] The third line’s primary purpose is to objectively assess the effectiveness of the organization’s AFC risk management, governance, and control processes.
ZH: 第三道防线的主要目的是客观评估组织金融犯罪防控风险管理、治理和控制流程的有效性

[v7u_N002521|2521] The independent audit function is the fourth pillar of an AML program.
ZH: 独立审计职能是反洗钱项目的第四道防线。

[v7u_N002522|2522] This function verifies and validates the organization’s compliance efforts.
ZH: 独立审计职能负责验证和确认组织的合规工作。

[v7u_N002523|2523] In a robust AML program, the independent audit function reports directly to the audit committee or board of directors. This ensures that the findings are independent and not influenced by any other priorities.
ZH: 独立审计职能直接向审计委员会或董事会报告以确保独立性。

[v7u_N002524|2524] The independent audit function acts as a cross-check on the effectiveness of the first and second lines of defense. Independent auditors assess operational and compliance frameworks to ensure the organization’s controls align with regulatory requirements and function effectively.
ZH: 独立审计职能对第一道和第二道防线的有效性进行交叉检查。

[v7u_N002525|2525] Each LOD has different responsibilities and performs specific checks. The first line focuses on daily execution accuracy, with responsibilities including frontline operational management. The checks and controls in this line include:
ZH: 第一道防线负责日常执行准确性，包括一线运营管理。

[v7u_N002526|2526] QC checks to ensure procedures and guidelines are followed.
ZH: 质量控制检查确保遵循程序和指南。

[v7u_N002527|2527] QA checks to evaluate the effectiveness of processes and systems operated by the first line.
ZH: 质量保证检查评估第一道防线流程和系统的有效性。

[v7u_N002528|2528] Control testing to assess the design and operational effectiveness of controls.
ZH: 控制测试评估控制的设计和运行有效性。

[v7u_N002529|2529] The second LOD focuses on framework effectiveness. This line includes compliance functions, ensuring adherence to laws, regulations, and internal policies. The checks in this line include:
ZH: 第二道防线关注框架有效性，包括合规职能。

[v7u_N002530|2530] Compliance monitoring: Ongoing oversight to ensure adherence to policies and regulations.
ZH: 合规监控：持续监督以确保遵守政策和法规。

[v7u_N002531|2531] Testing procedures: Regular compliance tests to verify whether the first line has implemented policies effectively and if controls operate as intended.
ZH: 定期合规测试以验证第一道防线政策实施和控制的运行情况。

[v7u_N002532|2532] QA checks: Evaluate the effectiveness of processes and systems operated by the second line.
ZH: 质量保证检查评估第二道防线流程和系统的有效性。

[v7u_N002533|2533] The third line focuses on systematic issues and governance. The independent audit function carries out its role through:
ZH: 第三道防线关注系统性问题与治理，独立审计职能通过以下方式履行职责。

[v7u_N002534|2534] Independent audits: Assess the effectiveness and efficiency of the firstand second-line controls. Auditors ensure that the AML program meets regulatory requirements and industry standards, identifying and communicating deficiencies.
ZH: 独立审计评估第一、二道防线控制的有效性和效率，确保反洗钱项目符合监管要求。

[v7u_N002535|2535] These distinct checks at each LOD are critical for maintaining an effective risk management system. Collectively, they ensure:
ZH: 各道防线的不同检查对于维持有效的风险管理体系至关重要。

[v7u_N002536|2536] The first line’s operational systems execute policies and follow procedures.
ZH: 第一道防线的运营系统执行政策并遵循程序。

[v7u_N002537|2537] The second line’s compliance functions follow policies, participate in investigations, verify procedure effectiveness, and provide oversight.
ZH: 第二道防线的合规职能遵循政策、参与调查、验证程序有效性并提供监督。

[v7u_N002538|2538] The third line’s independent audit reviews risks and controls, offering an unbiased opinion on the control environment’s effectiveness.
ZH: 第三道防线的独立审计审查风险和控制，提供关于控制环境有效性的客观意见。

[v7u_N002539|2539] In smaller organizations that lack the resources for an internal audit team, or when there are skill or resource limitations, external auditors might perform the independent audit function.
ZH: 在缺乏内部审计资源的小型组织中，可由外部审计师执行独立审计职能。

[v7u_N002540|2540] When well executed, this external perspective enriches the audit process and provides an unbiased assessment of the AFC compliance program and risk management effectiveness.
ZH: 外部视角可丰富审计过程，提供对金融犯罪防控合规项目及风险管理有效性的客观评估。

[v7u_N002541|2541] By maintaining these checks and balances at each LOD, organizations can identify weaknesses and enhance their AFC compliance programs, mitigating financial crime risks.
ZH: 三道防线中的制衡机制有助于识别弱点并加强金融犯罪防控合规计划。
```

allowed_unit_ids:

```json
[
  "v7u_N002517",
  "v7u_N002518",
  "v7u_N002519",
  "v7u_N002520",
  "v7u_N002521",
  "v7u_N002522",
  "v7u_N002523",
  "v7u_N002524",
  "v7u_N002525",
  "v7u_N002526",
  "v7u_N002527",
  "v7u_N002528",
  "v7u_N002529",
  "v7u_N002530",
  "v7u_N002531",
  "v7u_N002532",
  "v7u_N002533",
  "v7u_N002534",
  "v7u_N002535",
  "v7u_N002536",
  "v7u_N002537",
  "v7u_N002538",
  "v7u_N002539",
  "v7u_N002540",
  "v7u_N002541"
]
```

## S2 Process IR

```json
{
  "section_id": "CH34-S10",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "独立审计职能如何评估第一、二道防线控制的有效性并产生意见？",
      "title": "独立审计评估控制有效性并识别缺陷",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "独立审计评估第一、二道防线控制的有效性和效率，确保组织控制符合监管要求并有效运行",
          "evidence_unit_ids": [
            "v7u_N002524",
            "v7u_N002534"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "监管要求和行业标准",
          "evidence_unit_ids": [
            "v7u_N002524",
            "v7u_N002534"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "识别并沟通缺陷",
          "evidence_unit_ids": [
            "v7u_N002534"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "提供关于控制环境有效性的无偏见意见",
          "evidence_unit_ids": [
            "v7u_N002538"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002524"
          ],
          "source_quote": "ensure the organization’s controls align with regulatory requirements and function effectively."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002534"
          ],
          "source_quote": "identifying and communicating deficiencies"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e004",
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002538"
          ],
          "source_quote": "Independent auditors assess operational and compliance frameworks ... offering an unbiased opinion on the control environment’s effectiveness."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "在缺乏内部审计资源时，如何执行独立审计职能？",
      "title": "外部审计替代内部审计执行独立审计职能",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "组织缺乏内部审计团队资源，或存在技能/资源限制",
          "evidence_unit_ids": [
            "v7u_N002539"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "外部审计师可能执行独立审计职能",
          "evidence_unit_ids": [
            "v7u_N002539"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "提供对AFC合规计划和风险管理有效性的客观评估，并丰富审计过程（当执行得当时）",
          "evidence_unit_ids": [
            "v7u_N002540"
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
          "condition": "组织缺乏内部审计资源或技能",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002539"
          ],
          "source_quote": "In smaller organizations that lack the resources for an internal audit team, or when there are skill or resource limitations, external auditors might perform the independent audit function."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N002540"
          ],
          "source_quote": "When well executed, this external perspective enriches the audit process and provides an unbiased assessment of the AFC compliance program and risk management effectiveness."
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
      "reason": "描述独立审计职能向审计委员会/董事会报告以确保独立性的静态安排，属于职能描述而非程序性或判断性流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "独立审计对第一、二道防线控制进行评估、识别缺陷并提供无偏见意见，构成明确的判断性流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "在缺乏内部资源时由外部审计执行职能并提供客观评估，触发条件明确，构成程序性流程。"
    }
  ],
  "skip_reason": null
}
```
