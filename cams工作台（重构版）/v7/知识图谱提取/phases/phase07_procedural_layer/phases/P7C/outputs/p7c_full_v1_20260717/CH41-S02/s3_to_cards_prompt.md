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

section_id: `CH41-S02`

section_title: `Governance and oversight > Drafting AFC policies and procedures`

section_text_with_unit_anchors:

```text
[v7u_N002894|2894] AFC policies and procedures form the core of an organization’s AFC compliance framework, ensuring effective risk management, adherence to regulations, and operational integrity.
ZH: 金融犯罪防控政策和程序是组织合规框架的核心，确保风险管理、法规遵守和运营完整性

[v7u_N002895|2895] These policies must be clear, risk-based, and adaptable to evolving business models while aligning with global and jurisdictional AFC standards.
ZH: 金融犯罪防控政策必须清晰、基于风险、适应业务模式变化，并与全球及司法管辖区标准一致

[v7u_N002896|2896] What are AFC policies and procedures?
ZH: 引导性问题：什么是金融犯罪防控政策和程序？

[v7u_N002897|2897] Policies establish the principles, objectives, and regulatory obligations for AFC compliance. They translate legal and regulatory requirements into business-specific commitments.
ZH: 政策确立金融犯罪防控合规的原则、目标和监管义务，将法律法规转化为业务承诺

[v7u_N002898|2898] Procedures provide detailed, step-by-step implementation guidance to ensure policies are applied consistently across different business units and jurisdictions. Separate procedures are often written for a policy to tailor its execution to various business units and jurisdictions.
ZH: 程序提供详细的分步实施指南，确保政策在不同业务单元和司法管辖区一致应用

[v7u_N002899|2899] Why are AFC policies and procedures important?
ZH: 引导性问题：为什么金融犯罪防控政策和程序很重要？

[v7u_N002900|2900] Policies and procedures ensure regulatory compliance. Institutions typically choose to align their policies with FATF Recommendations, Basel Committee on Banking Supervision (BCBS) guidelines, national AML laws, and regulatory expectations.
ZH: 政策和程序确保监管合规，机构通常与FATF建议、巴塞尔委员会指南及国家反洗钱法律保持一致

[v7u_N002901|2901] Policies ensure comprehensive coverage. They should cover all products and services, including future offerings, to prevent compliance gaps.
ZH: 政策应覆盖所有产品和服务，包括未来产品，以防止合规缺口。

[v7u_N002902|2902] To follow a risk-based approach, policies must be tailored to institutional risk exposure, customer profiles, and geographic risk factors.
ZH: 基于风险的方法要求政策根据机构风险敞口、客户概况和地理风险因素量身定制。

[v7u_N002903|2903] To demonstrate proper governance and accountability, a structured policy framework ensures clear roles, responsibilities, and oversight mechanisms for compliance management.
ZH: 结构化政策框架确保合规管理中的明确角色、职责和监督机制。

[v7u_N002904|2904] Organizations should maintain a clearly defined protocol to identify when a new policy must be adopted, as well as the process for drafting, approving, and updating it.
ZH: 机构应维护明确协议，以确定何时采用新政策及其起草、批准和更新流程。

[v7u_N002905|2905] Good policies should include provisions for addressing any exceptions or exemptions and should clearly assign responsibilities to specific people or roles. They should also provide a schedule for reviewing the policy, typically on an annual basis, and stipulate events that would trigger an ad hoc review and update.
ZH: 良好政策应包括例外处理、责任分配和定期审查安排。

[v7u_N002906|2906] Examples include the introduction of a new product or the occurrence of a relevant regulatory event.
ZH: 触发临时审查的事件示例包括新产品推出或相关监管事件。

[v7u_N002907|2907] Detailed implementation guidance is provided in procedures, which are typically tailored to specific business units or other entities. In this way, changes in procedures can be made quickly to reflect changes that do not impact the entire organization.
ZH: 程序提供详细实施指南，可快速调整以适应局部变化。

[v7u_N002908|2908] How are AFC policies designed and implemented?
ZH: 关于金融犯罪防控政策设计与实施的问题引导。

[v7u_N002909|2909] Using a risk-based approach, organizations should customize policies based on customer, product, and transaction risks.
ZH: 基于风险的方法，机构应根据客户、产品和交易风险定制政策。

[v7u_N002910|2910] To ensure jurisdictional compliance, multinational organizations must align policies with country-specific laws, while maintaining global AFC principles. This may result in implementing higher standards in some jurisdictions to maintain global consistency.
ZH: 跨国机构需使政策符合各国法律，同时维持全球金融犯罪防控原则，可能需在部分司法管辖区实施更高标准。

[v7u_N002911|2911] To govern exceptions and dispensations, deviations from policy must be documented, justified, and approved by governance bodies. Where appropriate, dispensation may be provided for a specific time. Any known gaps in implementing policies must be documented and addressed within a reasonable period. A record of issues and policy violations may be centrally maintained for effective governance and oversight.
ZH: 政策偏差需记录、论证并经治理机构批准，已知实施缺口需在合理期限内解决。

[v7u_N002912|2912] When implementing new policies, organizations typically include a transition period, such as six months, to allow for:
ZH: 实施新政策时通常包含过渡期（如六个月），以便进行差距分析和业务风险评估等。

[v7u_N002913|2913] Gap analysis and business risk assessment.
ZH: 过渡期活动包括差距分析和业务风险评估。

[v7u_N002914|2914] System, procedural, and process updates
ZH: 过渡期活动包括系统、程序和流程更新。

[v7u_N002915|2915] Training and staff education.
ZH: 过渡期活动包括培训和员工教育。

[v7u_N002916|2916] By developing clear, enforceable, and adaptable AFC policies, financial institutions strengthen compliance, mitigate financial crime risks, and ensure operational resilience.
ZH: 制定清晰、可执行且适应性强的金融犯罪防控政策有助于加强合规、降低金融犯罪风险并确保运营韧性。
```

allowed_unit_ids:

```json
[
  "v7u_N002894",
  "v7u_N002895",
  "v7u_N002896",
  "v7u_N002897",
  "v7u_N002898",
  "v7u_N002899",
  "v7u_N002900",
  "v7u_N002901",
  "v7u_N002902",
  "v7u_N002903",
  "v7u_N002904",
  "v7u_N002905",
  "v7u_N002906",
  "v7u_N002907",
  "v7u_N002908",
  "v7u_N002909",
  "v7u_N002910",
  "v7u_N002911",
  "v7u_N002912",
  "v7u_N002913",
  "v7u_N002914",
  "v7u_N002915",
  "v7u_N002916"
]
```

## S2 Process IR

```json
{
  "section_id": "CH41-S02",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "如何识别新政策采用时机并管理起草、批准和更新流程？",
      "title": "根据协议识别新政策采用时机并执行生命周期流程",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "新政策必须被采用时",
          "evidence_unit_ids": [
            "v7u_N002904"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "识别新政策采用时机并执行起草、批准和更新流程",
          "evidence_unit_ids": [
            "v7u_N002904"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "新政策被采用或更新",
          "evidence_unit_ids": [
            "v7u_N002904"
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
          "condition": "新政策必须被采用时",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002904"
          ],
          "source_quote": "identify when a new policy must be adopted, as well as the process for drafting, approving, and updating it."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "trigger_element_id": null,
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": "component_assembles_product",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002904"
          ],
          "source_quote": "the process for drafting, approving, and updating it."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "如何确保管辖合规并维持全球原则？",
      "title": "使政策符合管辖法律同时维持全球标准",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "确保管辖合规的需求",
          "evidence_unit_ids": [
            "v7u_N002910"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "使政策与各国法律保持一致",
          "evidence_unit_ids": [
            "v7u_N002910"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "standard",
          "label": "全球AFC原则",
          "evidence_unit_ids": [
            "v7u_N002910"
          ],
          "modality": "required"
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "可能在部分司法管辖区实施更高标准",
          "evidence_unit_ids": [
            "v7u_N002910"
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
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002910"
          ],
          "source_quote": "To ensure jurisdictional compliance, multinational organizations must align policies with country-specific laws"
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e003",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002910"
          ],
          "source_quote": "while maintaining global AFC principles"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "relation_type": "component_assembles_product",
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N002910"
          ],
          "source_quote": "This may result in implementing higher standards in some jurisdictions to maintain global consistency."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "如何管理政策偏差？",
      "title": "处理政策偏差的流程",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "出现政策偏差",
          "evidence_unit_ids": [
            "v7u_N002911"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "记录、论证并提交治理机构批准偏差",
          "evidence_unit_ids": [
            "v7u_N002911"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "豁免可能被给予特定时间",
          "evidence_unit_ids": [
            "v7u_N002911"
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
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002911"
          ],
          "source_quote": "deviations from policy must be documented, justified, and approved by governance bodies"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": "component_assembles_product",
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N002911"
          ],
          "source_quote": "Where appropriate, dispensation may be provided for a specific time."
        }
      ],
      "split_reason": "candidate s1c_004包含两个独立中心：政策偏差处理和政策实施缺口处理，因此拆分为两个episode"
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "如何处理政策实施缺口？",
      "title": "处理政策实施缺口的流程",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "已知政策实施缺口",
          "evidence_unit_ids": [
            "v7u_N002911"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "记录并在合理期限内解决缺口",
          "evidence_unit_ids": [
            "v7u_N002911"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "缺口在合理期限内被解决",
          "evidence_unit_ids": [
            "v7u_N002911"
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
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002911"
          ],
          "source_quote": "Any known gaps in implementing policies must be documented and addressed within a reasonable period."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": "component_assembles_product",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002911"
          ],
          "source_quote": "addressed within a reasonable period."
        }
      ],
      "split_reason": "candidate s1c_004包含两个独立中心：政策偏差处理和政策实施缺口处理，因此拆分为两个episode"
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "实施新政策时如何完成过渡期准备？",
      "title": "实施新政策的过渡期活动",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "实施新政策时",
          "evidence_unit_ids": [
            "v7u_N002912"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "包含过渡期（如六个月）",
          "evidence_unit_ids": [
            "v7u_N002912"
          ],
          "modality": "optional"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "进行差距分析和业务风险评估",
          "evidence_unit_ids": [
            "v7u_N002913"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "执行系统、程序和流程更新",
          "evidence_unit_ids": [
            "v7u_N002914"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "实施培训和员工教育",
          "evidence_unit_ids": [
            "v7u_N002915"
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
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002912"
          ],
          "source_quote": "When implementing new policies, organizations typically include a transition period, such as six months, to allow for:"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": "component_assembles_product",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002912",
            "v7u_N002913"
          ],
          "source_quote": "Gap analysis and business risk assessment."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "relation_type": "component_assembles_product",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002912",
            "v7u_N002914"
          ],
          "source_quote": "System, procedural, and process updates"
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e005",
          "relation_type": "component_assembles_product",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002912",
            "v7u_N002915"
          ],
          "source_quote": "Training and staff education."
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
      "reason": "该候选描述了根据协议识别新政策采用时机并执行起草、批准、更新流程的程序性过程，构成独立episode。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述良好政策应包含的审查安排要求，属于静态政策内容设计，未构成程序性或判断性迁移，不是流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "描述了机构必须使政策符合管辖法律并维持全球原则的动作，构成一个完整的管辖合规调整流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003",
        "ep_004"
      ],
      "reason": "候选包含两个独立的程序性流程：政策偏差处理和政策实施缺口处理，各自有触发、动作和结果，因此拆为两个episode映射。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "描述了实施新政策时设定过渡期并进行准备活动的步骤，构成一个实施流程。"
    },
    {
      "candidate_id": "s1c_gap_ch41_s02_comprehensive_coverage",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述政策全面覆盖的要求，属于政策内容原则，未描述具体的程序性过程，不是流程。"
    },
    {
      "candidate_id": "s1c_gap_ch41_s02_risk_based_customization",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述基于风险定制政策的要求，是政策制定原则，未形成具体的程序性或判断性迁移，不是流程。"
    }
  ],
  "skip_reason": null
}
```
