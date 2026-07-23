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

section_id: `CH41-S03`

section_title: `Governance and oversight > Maintaining effective AFC policies and procedures`

section_text_with_unit_anchors:

```text
[v7u_N002917|2917] Regulated organizations are required to maintain written AFC policies and procedures that mitigate and manage the risks of money laundering and terrorist financing.
ZH: 受监管机构须制定书面金融犯罪防控政策和程序以管理和降低洗钱与恐怖融资风险。

[v7u_N002918|2918] Organizations should regularly review and update these policies and procedures, typically on an annual basis, although the nature of the risks the organization is encountering should drive the frequency.
ZH: 机构应定期（通常每年）审查和更新金融犯罪防控政策，频率应基于风险性质。

[v7u_N002919|2919] Organizations should also conduct reviews in response to events that might change their risk profile, such as a new business or jurisdiction, or the results of an audit or regulatory examination.
ZH: 机构还应在可能改变风险状况的事件（如新业务、新司法管辖区或审计结果）发生后进行审查。

[v7u_N002920|2920] Failure to update policies on a continuous basis might result in a failure to address new risks until the next scheduled review.
ZH: 未能持续更新政策可能导致新风险在下次定期审查前未被处理。

[v7u_N002921|2921] Additionally, organizations need to maintain awareness of emerging issues and regulatory activity. This “horizon scanning” is particularly important because the AFC environment is highly dynamic.
ZH: 由于金融犯罪防控环境高度动态，组织需要进行地平线扫描以关注新兴问题和监管动态。

[v7u_N002922|2922] It could take many months or even years to implement new processes.
ZH: 实施新流程可能需要数月甚至数年时间。

[v7u_N002923|2923] Proactive horizon scanning helps organizations plan, resource, and implement new policies in a timely and effective manner.
ZH: 主动的地平线扫描有助于组织及时有效地规划、资源配置和实施新政策。

[v7u_N002924|2924] The development and approval of policies should include the participation of legal counsel, other internal stakeholders, and external experts where appropriate.
ZH: 政策的制定和批准应包含法律顾问、其他内部利益相关方以及适当的外部专家参与。

[v7u_N002925|2925] Once approved, policies and procedures should be accessible to all employees on an ongoing basis.
ZH: 批准后的政策和程序应持续对所有员工开放可访问。

[v7u_N002926|2926] Organizations should approve, document, and promptly communicate to their staff any changes to policies and procedures.
ZH: 组织应批准、记录并及时向员工传达政策和程序的任何变更。

[v7u_N002927|2927] AFC policies and procedures should be tailored to the specific risk profile, risk appetite, and size of the organization.
ZH: 金融犯罪防控政策和程序应根据组织的具体风险状况、风险偏好和规模量身定制。

[v7u_N002928|2928] Global organizations should conduct gap analyses as part of their review and horizon scanning processes to ensure the policy covers relevant local regulations in the jurisdictions in which they operate.
ZH: 全球性组织应进行差距分析，确保政策涵盖其运营所在司法管辖区的相关当地法规。

[v7u_N002929|2929] This may also require regional or local policies and procedures to reflect the local laws, regulations, and risks, as long as they do not conflict with the organization's global policy.
ZH: 区域或地方政策可反映当地法律、法规和风险，前提是不与组织的全球政策冲突。
```

allowed_unit_ids:

```json
[
  "v7u_N002917",
  "v7u_N002918",
  "v7u_N002919",
  "v7u_N002920",
  "v7u_N002921",
  "v7u_N002922",
  "v7u_N002923",
  "v7u_N002924",
  "v7u_N002925",
  "v7u_N002926",
  "v7u_N002927",
  "v7u_N002928",
  "v7u_N002929"
]
```

## S2 Process IR

```json
{
  "section_id": "CH41-S03",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001",
        "s1c_005",
        "s1c_008"
      ],
      "focal_question": "机构如何制定和维护有效的金融犯罪防控政策？",
      "title": "制定和维护适合机构风险的AFC政策",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "制定与维护书面金融犯罪防控政策和程序",
          "evidence_unit_ids": [
            "v7u_N002917"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "降低和管理洗钱与恐怖融资风险",
          "evidence_unit_ids": [
            "v7u_N002917"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "standard",
          "label": "政策的制定和批准应包括法律顾问、其他内部利益相关方及适当的外部专家参与",
          "evidence_unit_ids": [
            "v7u_N002924"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "standard",
          "label": "金融犯罪防控政策和程序应根据组织的具体风险状况、风险偏好和规模量身定制",
          "evidence_unit_ids": [
            "v7u_N002927"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e001",
          "auxiliary_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002924"
          ],
          "source_quote": "The development and approval of policies should include the participation of legal counsel, other internal stakeholders, and external experts where appropriate."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e001",
          "auxiliary_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002927"
          ],
          "source_quote": "AFC policies and procedures should be tailored to the specific risk profile, risk appetite, and size of the organization."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e002",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002917"
          ],
          "source_quote": "Regulated organizations are required to maintain written AFC policies and procedures that mitigate and manage the risks of money laundering and terrorist financing."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002",
        "s1c_003",
        "s1c_009",
        "s1c_010"
      ],
      "focal_question": "机构如何通过审查和差距分析保持AFC政策的有效性与合规？",
      "title": "定期/事件触发审查与差距分析以保持政策合规",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "审查频率应由组织面临的风险性质驱动",
          "evidence_unit_ids": [
            "v7u_N002918"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "context",
          "label": "可能改变风险状况的事件，如新业务、新司法管辖区、审计或监管检查结果",
          "evidence_unit_ids": [
            "v7u_N002919"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "审查和更新金融犯罪防控政策和程序",
          "evidence_unit_ids": [
            "v7u_N002918",
            "v7u_N002919"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "进行差距分析以确保政策涵盖运营所在司法管辖区的相关当地法规",
          "evidence_unit_ids": [
            "v7u_N002928"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "政策涵盖相关当地法规",
          "evidence_unit_ids": [
            "v7u_N002928"
          ],
          "modality": null
        },
        {
          "element_id": "e006",
          "role": "outcome",
          "label": "可能需要区域或地方政策（前提是不与组织的全球政策冲突）",
          "evidence_unit_ids": [
            "v7u_N002929"
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
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002918"
          ],
          "source_quote": "the nature of the risks the organization is encountering should drive the frequency."
        },
        {
          "relation_id": "r002",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e002",
          "process_element_id": "e003",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002919"
          ],
          "source_quote": "Organizations should also conduct reviews in response to events that might change their risk profile, such as a new business or jurisdiction, or the results of an audit or regulatory examination."
        },
        {
          "relation_id": "r003",
          "kind": "sequence",
          "before_element_id": "e003",
          "after_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002928"
          ],
          "source_quote": "Global organizations should conduct gap analyses as part of their review and horizon scanning processes to ensure the policy covers relevant local regulations in the jurisdictions in which they operate."
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e004",
          "outcome_element_id": "e005",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002928"
          ],
          "source_quote": "to ensure the policy covers relevant local regulations in the jurisdictions in which they operate."
        },
        {
          "relation_id": "r005",
          "kind": "produce",
          "process_element_id": "e004",
          "outcome_element_id": "e006",
          "relation_type": null,
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N002929"
          ],
          "source_quote": "This may also require regional or local policies and procedures to reflect the local laws, regulations, and risks, as long as they do not conflict with the organization's global policy."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "机构如何进行地平线扫描以支持及时的政策规划？",
      "title": "动态环境下的地平线扫描驱动新政策实施",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "金融犯罪防控环境高度动态",
          "evidence_unit_ids": [
            "v7u_N002921"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "进行地平线扫描，关注新兴问题和监管动态",
          "evidence_unit_ids": [
            "v7u_N002921",
            "v7u_N002923"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "及时有效地规划、资源配置和实施新政策",
          "evidence_unit_ids": [
            "v7u_N002923"
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
            "v7u_N002921"
          ],
          "source_quote": "This “horizon scanning” is particularly important because the AFC environment is highly dynamic."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "helps_achieve",
          "evidence_unit_ids": [
            "v7u_N002923"
          ],
          "source_quote": "Proactive horizon scanning helps organizations plan, resource, and implement new policies in a timely and effective manner."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "批准后的政策如何确保对员工的持续可访问？",
      "title": "批准后政策与程序的持续可访问性",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "政策和程序获得批准后",
          "evidence_unit_ids": [
            "v7u_N002925"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "机构应确保政策和程序持续对所有员工开放可访问",
          "evidence_unit_ids": [
            "v7u_N002925"
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
            "v7u_N002925"
          ],
          "source_quote": "Once approved, policies and procedures should be accessible to all employees on an ongoing basis."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_007"
      ],
      "focal_question": "政策变更时如何进行批准、记录和沟通？",
      "title": "政策变更的批准、记录与沟通流程",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "批准、记录并及时向员工传达政策和程序的任何变更",
          "evidence_unit_ids": [
            "v7u_N002926"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "变更已传达给员工",
          "evidence_unit_ids": [
            "v7u_N002926"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002926"
          ],
          "source_quote": "Organizations should approve, document, and promptly communicate to their staff any changes to policies and procedures."
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
      "reason": "候选描述了机构须制定政策以降低风险的程序性要求，作为核心动作。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "候选提供了定期审查政策的程序，包括基于风险的频率标准。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "候选补充了事件驱动的审查触发条件。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "候选独立描述了地平线扫描过程及其对新政策实施的帮助，形成独立episode。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "support_only",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选自身不构成独立流程，但为政策制定与批准动作提供必要的专家参与标准。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "候选构成一个独立的小流程：批准后确保政策可访问。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "候选描述了一个明确的变更管理流程：批准、记录和沟通。"
    },
    {
      "candidate_id": "s1c_008",
      "disposition": "support_only",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选提供了政策定制标准，不单独构成流程，作为制定维护动作的参考标准。"
    },
    {
      "candidate_id": "s1c_009",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "候选明确了在审查中进行差距分析的步骤，并产出确保法规覆盖的结果。"
    },
    {
      "candidate_id": "s1c_010",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "候选延展了差距分析的可能产出（区域政策需求），条件是避免冲突，作为审查流程的一部分。"
    },
    {
      "candidate_id": "s1c_gap_ch41_s03_failure_to_update_risk",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "候选仅描述未持续更新政策可能带来的风险后果，不包含任何业务过程或判断。"
    }
  ],
  "skip_reason": null
}
```
