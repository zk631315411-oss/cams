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

section_id: `CH06-S09`

section_title: `Money Laundering Risks in Financial Services > Politically exposed person risks`

section_text_with_unit_anchors:

```text
[v7u_N000457|457] A politically exposed person (PEP) is an individual in a prominent political function, their immediate family, close associates, and any businesses held or controlled by that person.
ZH: 政治敏感人物（政治敏感人物）的定义：担任重要公职的个人及其亲属和密切关联人

[v7u_N000458|458] One challenge in identifying PEPs is the varying guidance and recommendations in each jurisdiction.
ZH: 识别政治敏感人物的挑战在于各司法管辖区指引不同

[v7u_N000459|459] Organizations must adhere to their local regulatory requirements in identifying PEPs.
ZH: 机构必须遵守当地监管要求识别政治敏感人物

[v7u_N000460|460] However, organizations may choose to enforce higher standards based on their risk appetite.
ZH: 机构可根据风险偏好执行更高的政治敏感人物标准

[v7u_N000461|461] According to the Financial Action Task Force (FATF), there are three types of PEPs:
ZH: FATF将政治敏感人物分为三类

[v7u_N000462|462] Foreign PEPs are individuals entrusted with prominent public functions by a foreign country.
ZH: 外国政治敏感人物指受外国委托担任重要公共职能的个人

[v7u_N000463|463] Domestic PEPs are individuals entrusted domestically with prominent public functions.
ZH: 国内政治敏感人物指在国内担任重要公共职能的个人

[v7u_N000464|464] International organization PEPs are individuals from an international organization entrusted with a prominent function such as secretary general, executive director, or president.
ZH: 国际组织政治敏感人物指在国际组织中担任秘书长、执行董事或主席等要职的个人

[v7u_N000465|465] Individuals in high positions and their associates are more vulnerable to corruption.
ZH: 高层职位个人及其关联人更易受腐败影响

[v7u_N000466|466] Corruption might be favors where the PEP directs government contracts to an organization in return for kickbacks. In addition, a PEP might influence legislation for bribes or flee the country with government funds.
ZH: 政治敏感人物腐败示例：以政府合同换取回扣、影响立法收受贿赂或携政府资金潜逃

[v7u_N000467|467] Use a broad definition for defining a PEP.
ZH: 应采用宽泛定义来界定政治敏感人物

[v7u_N000468|468] PEPs can generally be defined as:
ZH: 政治敏感人物的一般定义

[v7u_N000469|469] A person in a prominent decision-making or influential role
ZH: 政治敏感人物指担任重要决策或有影响力角色的人

[v7u_N000470|470] A person within royal, military, legislative, judicial, executive, or similar government positions
ZH: 政治敏感人物包括王室、军事、立法、司法、行政或类似政府职位的人

[v7u_N000471|471] PEPs will often use nominees or businesses they are associated with.
ZH: 政治敏感人物常使用名义人或关联企业

[v7u_N000472|472] Therefore, the definition of PEP can also include:
ZH: 政治敏感人物定义还可包括以下人员

[v7u_N000473|473] Immediate family
ZH: 政治敏感人物的直系亲属

[v7u_N000474|474] Close friends or associates
ZH: 政治敏感人物的密友或关联人

[v7u_N000475|475] Businesses owned or held by those individuals
ZH: 政治敏感人物拥有或持有的企业

[v7u_N000476|476] Under a risk-based approach, PEP risk is manageable.
ZH: 基于风险的方法下，政治敏感人物风险是可控的

[v7u_N000477|477] Some organizations follow a “once a PEP, always a PEP” approach because the individual may remain in the same circles of influence, even if they have stepped down.
ZH: 部分机构采用“一旦是政治敏感人物，永远是政治敏感人物”的方法

[v7u_N000478|478] Other organizations will look at:
ZH: 其他机构会考察以下因素

[v7u_N000479|479] The individual’s influence at the time, such as their ability to award contracts or allocate funds
ZH: 考察个人当时的影响力，如授予合同或分配资金的能力

[v7u_N000480|480] How long the individual has been classified as a PEP
ZH: 考察个人被归类为政治敏感人物的时间长短

[v7u_N000481|481] The purpose of the PEP designation is important.
ZH: 政治敏感人物 认定的目的具有重要意义

[v7u_N000482|482] Organizations must take the necessary steps to adapt transaction monitoring and KYC reviews and escalate based on their risk appetite.
ZH: 机构必须根据风险偏好调整交易监控和 了解你的客户 审查
```

allowed_unit_ids:

```json
[
  "v7u_N000457",
  "v7u_N000458",
  "v7u_N000459",
  "v7u_N000460",
  "v7u_N000461",
  "v7u_N000462",
  "v7u_N000463",
  "v7u_N000464",
  "v7u_N000465",
  "v7u_N000466",
  "v7u_N000467",
  "v7u_N000468",
  "v7u_N000469",
  "v7u_N000470",
  "v7u_N000471",
  "v7u_N000472",
  "v7u_N000473",
  "v7u_N000474",
  "v7u_N000475",
  "v7u_N000476",
  "v7u_N000477",
  "v7u_N000478",
  "v7u_N000479",
  "v7u_N000480",
  "v7u_N000481",
  "v7u_N000482"
]
```

## S2 Process IR

```json
{
  "section_id": "CH06-S09",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "机构如何在识别政治敏感人物时遵守当地监管要求？",
      "title": "识别政治敏感人物时遵守当地监管要求",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "identifying PEPs",
          "evidence_unit_ids": [
            "v7u_N000459"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "adhere to local regulatory requirements",
          "evidence_unit_ids": [
            "v7u_N000459"
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
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000459"
          ],
          "source_quote": "Organizations must adhere to their local regulatory requirements in identifying PEPs."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "机构如何根据风险偏好执行更高的政治敏感人物标准？",
      "title": "基于风险偏好执行更高政治敏感人物标准",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "enforce higher PEP standards",
          "evidence_unit_ids": [
            "v7u_N000460"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "risk appetite",
          "evidence_unit_ids": [
            "v7u_N000460"
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
            "v7u_N000460"
          ],
          "source_quote": "However, organizations may choose to enforce higher standards based on their risk appetite."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "如何采用宽泛定义界定政治敏感人物？",
      "title": "采用宽泛定义界定政治敏感人物",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "define a PEP",
          "evidence_unit_ids": [
            "v7u_N000467"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "broad definition",
          "evidence_unit_ids": [
            "v7u_N000467"
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
            "v7u_N000467"
          ],
          "source_quote": "Use a broad definition for defining a PEP."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "如何根据“一旦政治敏感人物，永远是政治敏感人物”方法持续视为政治敏感人物？",
      "title": "采用“一旦政治敏感人物，永远是政治敏感人物”方法",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "individual has been a PEP",
          "evidence_unit_ids": [
            "v7u_N000477"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "continue to treat the individual as a PEP",
          "evidence_unit_ids": [
            "v7u_N000477"
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
          "condition": "once a PEP, always a PEP approach",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000477"
          ],
          "source_quote": "Some organizations follow a “once a PEP, always a PEP” approach because the individual may remain in the same circles of influence, even if they have stepped down."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "机构如何考察个人当时的影响力和被归类为政治敏感人物的时长？",
      "title": "考察影响力和时长评估政治敏感人物状态",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "look at the individual’s influence at the time and how long classified as a PEP",
          "evidence_unit_ids": [
            "v7u_N000478",
            "v7u_N000479",
            "v7u_N000480"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "input",
          "label": "individual’s influence at the time (ability to award contracts or allocate funds)",
          "evidence_unit_ids": [
            "v7u_N000479"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "input",
          "label": "length of PEP classification",
          "evidence_unit_ids": [
            "v7u_N000480"
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
            "v7u_N000479"
          ],
          "source_quote": "Other organizations will look at: The individual’s influence at the time, such as their ability to award contracts or allocate funds"
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e001",
          "auxiliary_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N000480"
          ],
          "source_quote": "How long the individual has been classified as a PEP"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "机构如何根据风险偏好调整交易监控和KYC审查并升级？",
      "title": "基于风险偏好调整交易监控和KYC审查",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "adapt transaction monitoring and KYC reviews and escalate",
          "evidence_unit_ids": [
            "v7u_N000482"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "risk appetite",
          "evidence_unit_ids": [
            "v7u_N000482"
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
            "v7u_N000482"
          ],
          "source_quote": "Organizations must take the necessary steps to adapt transaction monitoring and KYC reviews and escalate based on their risk appetite."
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
      "reason": "该候选独立支持一条程序性关系：在识别PEP过程中必须遵守当地监管要求，形成context触发action的合规流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选独立支持一条程序性关系：基于风险偏好可选执行更高PEP标准，构成action引用standard的流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选独立支持一条程序性关系：使用宽泛定义界定PEP，构成action引用standard的流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选独立支持一条程序性关系：根据“once a PEP, always a PEP”方法，个人曾是PEP触发继续视为PEP的决策。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选独立支持程序性关系：机构考察个人影响力和PEP分类时长，action引用多个input形成评估流程。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "该候选独立支持一条程序性关系：机构必须根据风险偏好调整监控和审查，构成action引用standard的合规流程。"
    }
  ],
  "skip_reason": null
}
```
