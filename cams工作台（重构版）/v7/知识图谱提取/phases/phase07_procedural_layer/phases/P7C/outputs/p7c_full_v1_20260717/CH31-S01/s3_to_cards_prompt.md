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

section_id: `CH31-S01`

section_title: `Cooperation between authorities > Roles of regulators, law enforcement, and FIUs`

section_text_with_unit_anchors:

```text
[v7u_N002207|2207] A regulator’s role is to set detailed rules, ensure they are followed, and ensure that the preventative controls in the private sector are effective.
ZH: 监管机构的职责是制定详细规则、确保遵守并保证私营部门预防性控制有效

[v7u_N002208|2208] Regulators authorize regulated businesses via licenses and registrations and then undertake risk-based supervision of these organizations to ensure compliance and identify noncompliance.
ZH: 监管机构通过许可和注册授权受监管实体，并开展风险为本的监督

[v7u_N002209|2209] Regulators have a range of tools to ensure compliance, up to and including issuing fines and enforcement actions for serious cases.
ZH: 监管机构拥有多种合规工具，包括罚款和执法行动

[v7u_N002210|2210] Law enforcement undertakes investigations to bring money launderers to justice, take away their assets, and achieve other disruptive effects.
ZH: 执法部门开展调查以将洗钱者绳之以法并没收资产

[v7u_N002211|2211] Law enforcement investigators work with prosecution authorities to bring court proceedings.
ZH: 执法调查人员与检察机关合作提起刑事诉讼

[v7u_N002212|2212] The relationship between law enforcement and prosecution authorities varies significantly between jurisdictions, depending on the legal system in each jurisdiction.
ZH: 执法与检察机关的关系因司法管辖区法律体系而异

[v7u_N002213|2213] Asset recovery is an important part of AML/CFT systems. Law enforcement and prosecution authorities use asset recovery as a mechanism to ensure that crime does not pay.
ZH: 资产追缴是反洗钱/反恐怖融资体系的重要组成部分，确保犯罪无利可图

[v7u_N002214|2214] Depending on their location, law enforcement agencies have varying scopes of authority for addressing different types of crime.
ZH: 执法机构的权限范围因所在地和犯罪类型而异

[v7u_N002215|2215] For example, local police have different responsibilities compared to national or federal agencies.
ZH: 例如地方警察与国家级或联邦机构的职责不同

[v7u_N002216|2216] Some law enforcement agencies might also have other responsibilities.
ZH: 部分执法机构可能还承担其他职责

[v7u_N002217|2217] For example, tax authorities can be responsible for investigating tax crime as well as setting tax policy.
ZH: 例如税务机关既负责调查税务犯罪也负责制定税收政策

[v7u_N002218|2218] National FIUs receive, analyze, and disseminate financial intelligence.
ZH: 国家金融情报机构接收、分析和传播金融情报

[v7u_N002219|2219] They produce strategic analysis that is used to understand trends, typologies, and threats.
ZH: FIU开展战略分析以了解趋势、类型和威胁

[v7u_N002220|2220] They also produce operational analysis that law enforcement uses to investigate and disrupt money laundering, terrorist financing, and predicate offenses.
ZH: FIU开展操作分析供执法部门调查洗钱、恐怖融资和上游犯罪

[v7u_N002221|2221] In some cases, the same organization can be both a regulator and an FIU, and FIUs can also be part of law enforcement agencies.
ZH: 同一机构可同时承担监管机构、金融情报机构和执法机构的角色

[v7u_N002222|2222] There are many different models, but the main point is that the agencies cooperate and share information when it pertains to each other’s functions.
ZH: 各机构必须合作并共享与各自职能相关的信息

[v7u_N002223|2223] These agencies should also share information with their international counterparts to handle crossborder money laundering and terrorist financing.
ZH: 机构应与国际同行共享信息以打击跨境洗钱和恐怖融资

[v7u_N002224|2224] There are various channels for information sharing, depending on whether it is intelligence, evidence, or regulatory information.
ZH: 信息共享渠道因信息类型（情报、证据或监管信息）而异
```

allowed_unit_ids:

```json
[
  "v7u_N002207",
  "v7u_N002208",
  "v7u_N002209",
  "v7u_N002210",
  "v7u_N002211",
  "v7u_N002212",
  "v7u_N002213",
  "v7u_N002214",
  "v7u_N002215",
  "v7u_N002216",
  "v7u_N002217",
  "v7u_N002218",
  "v7u_N002219",
  "v7u_N002220",
  "v7u_N002221",
  "v7u_N002222",
  "v7u_N002223",
  "v7u_N002224"
]
```

## S2 Process IR

```json
{
  "section_id": "CH31-S01",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "监管机构如何通过风险为本的监督确保合规？",
      "title": "Risk-Based Supervision by Regulators",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Regulators authorize regulated businesses via licenses and registrations",
          "evidence_unit_ids": [
            "v7u_N002208"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "undertake risk-based supervision of these organizations",
          "evidence_unit_ids": [
            "v7u_N002208"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "ensure compliance",
          "evidence_unit_ids": [
            "v7u_N002208"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "identify noncompliance",
          "evidence_unit_ids": [
            "v7u_N002208"
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
            "v7u_N002208"
          ],
          "source_quote": "Regulators authorize regulated businesses via licenses and registrations and then undertake risk-based supervision of these organizations to ensure compliance and identify noncompliance."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002208"
          ],
          "source_quote": "… undertake risk-based supervision … to ensure compliance …"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002208"
          ],
          "source_quote": "… undertake risk-based supervision … to identify noncompliance."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_gap_ch31_s01_compliance_tools"
      ],
      "focal_question": "监管机构如何针对严重案件使用合规工具？",
      "title": "Compliance Tools for Serious Cases",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "serious cases",
          "evidence_unit_ids": [
            "v7u_N002209"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "use tools to ensure compliance",
          "evidence_unit_ids": [
            "v7u_N002209"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "issuing fines and enforcement actions",
          "evidence_unit_ids": [
            "v7u_N002209"
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
          "condition": "case is serious",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002209"
          ],
          "source_quote": "Regulators have a range of tools to ensure compliance, up to and including issuing fines and enforcement actions for serious cases."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002209"
          ],
          "source_quote": "… up to and including issuing fines and enforcement actions for serious cases."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "执法部门如何通过调查处置洗钱及相关犯罪？",
      "title": "Law Enforcement Investigations",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "undertake investigations",
          "evidence_unit_ids": [
            "v7u_N002210"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "bring money launderers to justice",
          "evidence_unit_ids": [
            "v7u_N002210"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "take away their assets",
          "evidence_unit_ids": [
            "v7u_N002210"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "achieve other disruptive effects",
          "evidence_unit_ids": [
            "v7u_N002210"
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
            "v7u_N002210"
          ],
          "source_quote": "Law enforcement undertakes investigations to bring money launderers to justice, take away their assets, and achieve other disruptive effects."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002210"
          ],
          "source_quote": "Law enforcement undertakes investigations to bring money launderers to justice, take away their assets, and achieve other disruptive effects."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002210"
          ],
          "source_quote": "Law enforcement undertakes investigations to bring money launderers to justice, take away their assets, and achieve other disruptive effects."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "执法调查人员如何与检察机关合作提起刑事诉讼？",
      "title": "Cooperation with Prosecution Authorities",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "work with prosecution authorities",
          "evidence_unit_ids": [
            "v7u_N002211"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "bring court proceedings",
          "evidence_unit_ids": [
            "v7u_N002211"
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
            "v7u_N002211"
          ],
          "source_quote": "Law enforcement investigators work with prosecution authorities to bring court proceedings."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "金融情报机构如何处理金融情报？",
      "title": "FIU Intelligence Processing",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "receive financial intelligence",
          "evidence_unit_ids": [
            "v7u_N002218"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "analyze financial intelligence",
          "evidence_unit_ids": [
            "v7u_N002218"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "disseminate financial intelligence",
          "evidence_unit_ids": [
            "v7u_N002218"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "strategic analysis",
          "evidence_unit_ids": [
            "v7u_N002219"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "operational analysis",
          "evidence_unit_ids": [
            "v7u_N002220"
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
            "v7u_N002218"
          ],
          "source_quote": "National FIUs receive, analyze, and disseminate financial intelligence."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002218"
          ],
          "source_quote": "National FIUs receive, analyze, and disseminate financial intelligence."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002219"
          ],
          "source_quote": "They produce strategic analysis that is used to understand trends, typologies, and threats."
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e005",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002220"
          ],
          "source_quote": "They also produce operational analysis that law enforcement uses to investigate and disrupt money laundering, terrorist financing, and predicate offenses."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "机构在什么条件下进行合作和信息共享？",
      "title": "Domestic Information Sharing",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "information pertains to each other’s functions",
          "evidence_unit_ids": [
            "v7u_N002222"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "agencies cooperate and share information",
          "evidence_unit_ids": [
            "v7u_N002222"
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
          "condition": "information pertains to functions",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002222"
          ],
          "source_quote": "the agencies cooperate and share information when it pertains to each other’s functions."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "机构应如何与国际同行共享信息？",
      "title": "International Information Sharing",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "should share information with international counterparts",
          "evidence_unit_ids": [
            "v7u_N002223"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "handle crossborder money laundering and terrorist financing",
          "evidence_unit_ids": [
            "v7u_N002223"
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
            "v7u_N002223"
          ],
          "source_quote": "These agencies should also share information with their international counterparts to handle crossborder money laundering and terrorist financing."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_008",
      "source_candidate_ids": [
        "s1c_gap_ch31_s01_asset_recovery"
      ],
      "focal_question": "执法和检察机关如何使用资产追缴机制？",
      "title": "Asset Recovery Mechanism",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "use asset recovery as a mechanism",
          "evidence_unit_ids": [
            "v7u_N002213"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "ensure that crime does not pay",
          "evidence_unit_ids": [
            "v7u_N002213"
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
            "v7u_N002213"
          ],
          "source_quote": "Law enforcement and prosecution authorities use asset recovery as a mechanism to ensure that crime does not pay."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_009",
      "source_candidate_ids": [
        "s1c_gap_ch31_s01_info_sharing_channels"
      ],
      "focal_question": "如何根据信息类型选择信息共享渠道？",
      "title": "Information Sharing Channel Selection",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "decision",
          "label": "choose sharing channel based on information type",
          "evidence_unit_ids": [
            "v7u_N002224"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "channel for intelligence",
          "evidence_unit_ids": [
            "v7u_N002224"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "channel for evidence",
          "evidence_unit_ids": [
            "v7u_N002224"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "channel for regulatory information",
          "evidence_unit_ids": [
            "v7u_N002224"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "branch",
          "decision_element_id": "e001",
          "target_element_id": "e002",
          "condition": "information type is intelligence",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002224"
          ],
          "source_quote": "There are various channels for information sharing, depending on whether it is intelligence, evidence, or regulatory information."
        },
        {
          "relation_id": "r002",
          "kind": "branch",
          "decision_element_id": "e001",
          "target_element_id": "e003",
          "condition": "information type is evidence",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002224"
          ],
          "source_quote": "There are various channels for information sharing, depending on whether it is intelligence, evidence, or regulatory information."
        },
        {
          "relation_id": "r003",
          "kind": "branch",
          "decision_element_id": "e001",
          "target_element_id": "e004",
          "condition": "information type is regulatory information",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002224"
          ],
          "source_quote": "There are various channels for information sharing, depending on whether it is intelligence, evidence, or regulatory information."
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
      "reason": "明确描述了监管机构授权后开展风险为本监督以确合规和发现不合规的程序流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "描述了执法部门开展调查并产出将洗钱者绳之以法、没收资产等结果的开放调查流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "给出了执法调查人员与检察机关合作提起刑事诉讼的过程，构成程序性关系。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "包含金融情报机构接收、分析、传播情报并产生战略和操作分析的连续流程。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "定义了在信息涉及各方职能时机构合作共享信息的条件触发流程。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_007"
      ],
      "reason": "规定了机构应与国际同行共享信息以处理跨境洗钱，构成信息共享流程。"
    },
    {
      "candidate_id": "s1c_gap_ch31_s01_regulator_role",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述监管机构的静态角色和职责（制定规则、确保控制有效），不构成原文明示的程序性迁移。"
    },
    {
      "candidate_id": "s1c_gap_ch31_s01_compliance_tools",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "描述了监管机构针对严重案件使用罚款和执法行动等工具确保合规的条件触发性流程。"
    },
    {
      "candidate_id": "s1c_gap_ch31_s01_asset_recovery",
      "disposition": "mapped",
      "episode_ids": [
        "ep_008"
      ],
      "reason": "给出了执法和检察机关使用资产追缴机制以确保犯罪无利可图的流程。"
    },
    {
      "candidate_id": "s1c_gap_ch31_s01_info_sharing_channels",
      "disposition": "mapped",
      "episode_ids": [
        "ep_009"
      ],
      "reason": "定义了根据信息类型（情报、证据、监管）选择不同共享渠道的决策分支流程。"
    }
  ],
  "skip_reason": null
}
```
