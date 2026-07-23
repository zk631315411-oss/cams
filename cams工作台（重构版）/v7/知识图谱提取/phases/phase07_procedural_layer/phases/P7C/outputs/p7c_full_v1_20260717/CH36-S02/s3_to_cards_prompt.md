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

section_id: `CH36-S02`

section_title: `Types of risk assessment > Types of risk assessment within an organization`

section_text_with_unit_anchors:

```text
[v7u_N002654|2654] There are different types of risk assessments within organizations. The assessments vary, depending on the individual entity type, but their aim is to identify, assess, and mitigate various risks and apply appropriate controls.
ZH: 组织内部存在不同类型的风险评估，其目标均为识别、评估和缓解风险并应用适当控制

[v7u_N002655|2655] The purpose of the AFC risk assessments is to help organizations ensure compliance, enhance risk management, and maintain healthy, sustainable businesses.
ZH: 金融犯罪防控风险评估旨在确保合规、加强风险管理并维持健康可持续的业务

[v7u_N002656|2656] One main risk assessment is an EWRA, which assesses all types of risk an organization faces.
ZH: 企业全面风险评估是主要的风险评估类型，评估组织面临的所有风险

[v7u_N002657|2657] We will focus on the AFC portion of the EWRA, which considers financial crimes—money laundering, terrorism financing, sanctions, tax evasion, and bribery and corruption.
ZH: 企业全面风险评估中的金融犯罪防控部分涵盖洗钱、恐怖融资、制裁、逃税、贿赂与腐败

[v7u_N002658|2658] The anti-bribery and corruption (ABC) risk assessment aims to prevent, detect, and report bribery and corruption while identifying areas of higher risk.
ZH: 反贿赂与腐败风险评估旨在预防、发现和报告贿赂与腐败，并识别高风险领域

[v7u_N002659|2659] In 2023, the Wolfsberg Group updated its , which helps entities mitigate ABC risks.
ZH: 2023年沃尔夫斯堡集团更新了其反贿赂与腐败风险评估指引

[v7u_N002660|2660] The security risk assessment focuses on security threats and risks that could affect both the physical and digital assets of an entity.
ZH: 安全风险评估关注可能影响实体物理和数字资产的安全威胁与风险

[v7u_N002661|2661] The operational risk assessment focuses on risks derived from the failures of internal processes, disruptions of integrated systems, internal or external events, and staff misconduct.
ZH: 操作风险定义：关注内部流程、系统中断、内外部事件及员工不当行为导致的失败

[v7u_N002662|2662] It concentrates on business and operational continuity.
ZH: 操作风险评估侧重于业务和运营连续性

[v7u_N002663|2663] It helps entities to identify, assess, and mitigate these risks, and apply measures to sustain a continuing business, while minimizing disruptions.
ZH: 操作风险评估帮助实体识别、评估和缓解风险，维持业务持续运营

[v7u_N002664|2664] Fraud risks can be part of the operational risk assessment in some organizations.
ZH: 欺诈风险可纳入操作风险评估

[v7u_N002665|2665] With examiners increasingly requesting to see results of the fraud risk assessment, execution may be centralized with AML risk assessment.
ZH: 监管机构要求欺诈风险评估结果，可与反洗钱风险评估集中执行

[v7u_N002666|2666] The customer risk assessment (CRA) helps entities understand the AML/CTF risks inherent in a particular business relationship with a customer.
ZH: 客户风险评估（CRA）帮助实体理解与客户业务关系中的反洗钱/反恐怖融资风险

[v7u_N002667|2667] Based on the type of organization and risk exposure, an organization may need to carry out specific risk assessments, such as assessing exposure to proliferation financing.
ZH: 根据组织类型和风险暴露，可能需要进行特定风险评估，如扩散融资风险评估

[v7u_N002668|2668] In 2020, FATF revised its Recommendation 1 and its Interpretive Note, requiring countries and obliged entities to identify, assess, understand, and mitigate their proliferation financing risks. FATF also published guidance in June 2021 to assist countries and obliged entities to conduct effective proliferation financing risk assessments.
ZH: FATF修订建议1，要求各国和义务实体识别、评估并缓解扩散融资风险，并发布指南

[v7u_N002669|2669] Proliferation financing refers to the transfer and export of nuclear, chemical, or biological weapons, their delivery means, and related materials.
ZH: 扩散融资指核、化学或生物武器及其运载工具和相关材料的转让和出口

[v7u_N002670|2670] Non-proliferation risk refers to contributing to the proliferation of these weapons of mass destruction (WMD) wittingly or unwittingly.
ZH: 防扩散风险指有意或无意助长大规模杀伤性武器扩散的风险

[v7u_N002671|2671] Managing non-proliferation risk is important because it poses a significant threat to international peace and security.
ZH: 管理防扩散风险对国际和平与安全至关重要
```

allowed_unit_ids:

```json
[
  "v7u_N002654",
  "v7u_N002655",
  "v7u_N002656",
  "v7u_N002657",
  "v7u_N002658",
  "v7u_N002659",
  "v7u_N002660",
  "v7u_N002661",
  "v7u_N002662",
  "v7u_N002663",
  "v7u_N002664",
  "v7u_N002665",
  "v7u_N002666",
  "v7u_N002667",
  "v7u_N002668",
  "v7u_N002669",
  "v7u_N002670",
  "v7u_N002671"
]
```

## S2 Process IR

```json
{
  "section_id": "CH36-S02",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_gap_ch36_s02_operational_risk_assessment"
      ],
      "focal_question": "如何通过操作风险评估识别并缓解操作风险以维持业务连续性",
      "title": "操作风险评估：识别、缓解风险并维持业务连续性",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "源自内部流程失败、系统中断、内外部事件及员工不当行为的操作风险",
          "evidence_unit_ids": [
            "v7u_N002661"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "执行操作风险评估：识别、评估和缓解这些风险并应用措施",
          "evidence_unit_ids": [
            "v7u_N002661",
            "v7u_N002663"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "采取措施维持业务持续运营并最小化中断",
          "evidence_unit_ids": [
            "v7u_N002662",
            "v7u_N002663"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002661"
          ],
          "source_quote": "The operational risk assessment focuses on risks derived from the failures of internal processes, disruptions of integrated systems, internal or external events, and staff misconduct."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "qualifier": "helps_achieve",
          "evidence_unit_ids": [
            "v7u_N002663"
          ],
          "source_quote": "It helps entities to identify, assess, and mitigate these risks, and apply measures to sustain a continuing business, while minimizing disruptions."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_gap_ch36_s02_abc_risk_assessment"
      ],
      "focal_question": "如何通过ABC风险评估预防贿赂与腐败并识别高风险领域",
      "title": "ABC风险评估：预防、发现、报告贿赂并识别高风险领域",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "反贿赂与腐败（ABC）风险评估",
          "evidence_unit_ids": [
            "v7u_N002658"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "预防、发现和报告贿赂与腐败",
          "evidence_unit_ids": [
            "v7u_N002658"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "识别高风险领域",
          "evidence_unit_ids": [
            "v7u_N002658"
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
            "v7u_N002658"
          ],
          "source_quote": "The anti-bribery and corruption (ABC) risk assessment aims to prevent, detect, and report bribery and corruption while identifying areas of higher risk."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002658"
          ],
          "source_quote": "The anti-bribery and corruption (ABC) risk assessment aims to prevent, detect, and report bribery and corruption while identifying areas of higher risk."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_gap_ch36_s02_fraud_risk_assessment_centralization"
      ],
      "focal_question": "在监管要求下，如何决定欺诈风险评估的执行方式",
      "title": "监管要求下欺诈风险评估执行的集中化决策",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "监管机构日益要求查看欺诈风险评估结果",
          "evidence_unit_ids": [
            "v7u_N002665"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "欺诈风险评估的执行可能与反洗钱风险评估集中",
          "evidence_unit_ids": [
            "v7u_N002665"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002665"
          ],
          "source_quote": "With examiners increasingly requesting to see results of the fraud risk assessment, execution may be centralized with AML risk assessment."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_gap_ch36_s02_customer_risk_assessment"
      ],
      "focal_question": "如何通过客户风险评估理解固有AML/CTF风险",
      "title": "客户风险评估（CRA）：理解固有AML/CTF风险",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "客户风险评估（CRA）",
          "evidence_unit_ids": [
            "v7u_N002666"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "理解与客户业务关系中的固有AML/CTF风险",
          "evidence_unit_ids": [
            "v7u_N002666"
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
          "qualifier": "helps_achieve",
          "evidence_unit_ids": [
            "v7u_N002666"
          ],
          "source_quote": "The customer risk assessment (CRA) helps entities understand the AML/CTF risks inherent in a particular business relationship with a customer."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_gap_ch36_s02_specific_risk_assessment_needed",
        "s1c_gap_ch36_s02_fatf_proliferation_financing_requirement"
      ],
      "focal_question": "依据组织类型、风险暴露及FATF要求，如何判断是否需进行特定风险评估（如扩散融资）",
      "title": "依据组织与风险因素及FATF要求判断特定风险评估的必要性",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "组织类型与风险暴露",
          "evidence_unit_ids": [
            "v7u_N002667"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "FATF建议1及其释义要求识别、评估、理解和缓解扩散融资风险",
          "evidence_unit_ids": [
            "v7u_N002668"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "decision",
          "label": "组织可能需要进行特定风险评估（如扩散融资风险评估）",
          "evidence_unit_ids": [
            "v7u_N002667"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e001",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002667"
          ],
          "source_quote": "Based on the type of organization and risk exposure, an organization may need to carry out specific risk assessments, such as assessing exposure to proliferation financing."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002668"
          ],
          "source_quote": "In 2020, FATF revised its Recommendation 1 and its Interpretive Note, requiring countries and obliged entities to identify, assess, understand, and mitigate their proliferation financing risks."
        }
      ],
      "split_reason": null
    }
  ],
  "candidate_audit": [
    {
      "candidate_id": "s1c_gap_ch36_s02_operational_risk_assessment",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选提供了操作风险评估的输入、动作和结果，构成完整的评估流程。"
    },
    {
      "candidate_id": "s1c_gap_ch36_s02_abc_risk_assessment",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选提供了ABC风险评估的动作和目的（预防/发现/报告贿赂及识别高风险领域），构成流程。"
    },
    {
      "candidate_id": "s1c_gap_ch36_s02_fraud_risk_assessment_centralization",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选提供了监管要求触发下的欺诈风险评估执行集中化决策流程。"
    },
    {
      "candidate_id": "s1c_gap_ch36_s02_customer_risk_assessment",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选提供了客户风险评估的动作和结果（理解固有AML/CTF风险），构成流程。"
    },
    {
      "candidate_id": "s1c_gap_ch36_s02_specific_risk_assessment_needed",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选提供了基于组织类型和风险暴露判断特定风险评估必要性的决策流程。"
    },
    {
      "candidate_id": "s1c_gap_ch36_s02_fatf_proliferation_financing_requirement",
      "disposition": "support_only",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选为特定风险评估必要性判断提供了监管标准（FATF要求），自身不构成独立流程。"
    }
  ],
  "skip_reason": null
}
```
