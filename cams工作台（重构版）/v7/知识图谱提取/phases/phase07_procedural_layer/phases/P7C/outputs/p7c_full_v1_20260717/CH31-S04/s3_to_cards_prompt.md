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

section_id: `CH31-S04`

section_title: `Cooperation between authorities > Cooperation between regulatory authorities`

section_text_with_unit_anchors:

```text
[v7u_N002237|2237] In some cases, multiple regulators supervise a single organization. This occurs when an organization offers a range of regulated products or operates across international or domestic borders.
ZH: 当机构提供多种受监管产品或跨境运营时，可能受多个监管机构监督

[v7u_N002238|2238] Therefore, regulators coordinate when conducting regulatory examinations and other activities.
ZH: 监管机构在进行监管检查和其他活动时应进行协调

[v7u_N002239|2239] Regulators clarify their area or scope of authority so that examinations and supervisory activities do not overlap. All parties need to be clear about their respective responsibilities.
ZH: 监管机构应明确各自权限范围，避免检查和监管活动重叠

[v7u_N002240|2240] Regulators coordinate at a policy level to ensure there are no gaps that create opportunities for noncompliance. They compare risk assessments and risk-based approaches to ensure integrated supervision.
ZH: 监管机构在政策层面协调，比较风险评估和基于风险的方法，确保一体化监管

[v7u_N002241|2241] Regulators also share information.
ZH: 监管机构之间共享信息

[v7u_N002242|2242] Coordinating scheduled work allows for complementary scheduling among regulators.
ZH: 协调安排工作使监管机构能够互补排期

[v7u_N002243|2243] Regulators might consider joint examinations for areas that warrant it to reduce the impact on an organization.
ZH: 监管机构可进行联合检查以减少对机构的影响

[v7u_N002244|2244] If an examination identifies issues or weaknesses, the regulator informs any other relevant regulators. In some instances, regulators can pursue joint action, resulting in combined enforcement action.
ZH: 检查发现问题时监管机构相互通报并可采取联合行动

[v7u_N002245|2245] Regulators cooperate both within a jurisdiction and internationally.
ZH: 监管机构在境内和国际层面开展合作

[v7u_N002246|2246] Many financial institutions have international footprints.
ZH: 许多金融机构拥有国际业务布局

[v7u_N002247|2247] Problems or risks in one jurisdiction might warrant scrutiny from regulators in another jurisdiction.
ZH: 一个司法辖区的问题或风险可能引发另一司法辖区的审查

[v7u_N002248|2248] In Europe, AML/CFT colleges are permanent structures that enhance cooperation between different regulators that supervise cross-border institutions.
ZH: 欧洲的反洗钱/反恐怖融资学院是促进跨境机构监管合作的常设机构

[v7u_N002249|2249] In addition, the EU’s new AML Authority will coordinate supervision among EU regulators and undertake direct supervision for the most high-risk entities.
ZH: 欧盟新反洗钱机构将协调监管并对高风险实体直接监管
```

allowed_unit_ids:

```json
[
  "v7u_N002237",
  "v7u_N002238",
  "v7u_N002239",
  "v7u_N002240",
  "v7u_N002241",
  "v7u_N002242",
  "v7u_N002243",
  "v7u_N002244",
  "v7u_N002245",
  "v7u_N002246",
  "v7u_N002247",
  "v7u_N002248",
  "v7u_N002249"
]
```

## S2 Process IR

```json
{
  "section_id": "CH31-S04",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "机构提供多种受监管产品或跨境运营时，如何触发监管机构协调检查等活动",
      "title": "多重监管情境触发监管机构协调检查等活动",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "机构提供多种受监管产品或跨境运营，受多个监管机构监督",
          "evidence_unit_ids": [
            "v7u_N002237"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "监管机构协调进行检查和其他活动",
          "evidence_unit_ids": [
            "v7u_N002238"
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
          "condition": "当机构提供多种受监管产品或跨境运营时（多个监管机构监督）",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002237",
            "v7u_N002238"
          ],
          "source_quote": "In some cases, multiple regulators supervise a single organization. This occurs when an organization offers a range of regulated products or operates across international or domestic borders. Therefore, regulators coordinate when conducting regulatory examinations and other activities."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "监管机构如何通过明确权限范围避免检查与监管活动重叠",
      "title": "明确权限范围以避免监管活动重叠",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "监管机构明确各自权限范围",
          "evidence_unit_ids": [
            "v7u_N002239"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "避免检查和监管活动重叠",
          "evidence_unit_ids": [
            "v7u_N002239"
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
            "v7u_N002239"
          ],
          "source_quote": "Regulators clarify their area or scope of authority so that examinations and supervisory activities do not overlap."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "监管机构如何在政策层面协调以确保一体化监管并避免漏洞",
      "title": "政策层面协调与风险评估比较以确保一体化监管",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "监管机构在政策层面协调并比较风险评估和风险为本方法",
          "evidence_unit_ids": [
            "v7u_N002240"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "确保无漏洞（避免不合规机会）",
          "evidence_unit_ids": [
            "v7u_N002240"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "确保一体化监管",
          "evidence_unit_ids": [
            "v7u_N002240"
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
            "v7u_N002240"
          ],
          "source_quote": "Regulators coordinate at a policy level to ensure there are no gaps that create opportunities for noncompliance."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002240"
          ],
          "source_quote": "They compare risk assessments and risk-based approaches to ensure integrated supervision."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "协调安排工作如何使监管机构实现互补排期",
      "title": "协调安排工作实现互补排期",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "协调安排工作",
          "evidence_unit_ids": [
            "v7u_N002242"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "实现互补排期",
          "evidence_unit_ids": [
            "v7u_N002242"
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
            "v7u_N002242"
          ],
          "source_quote": "Coordinating scheduled work allows for complementary scheduling among regulators."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "监管机构如何基于领域必要性考虑联合检查以减少对机构的影响",
      "title": "基于领域必要性考虑联合检查以减少影响",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "存在值得联合检查的领域",
          "evidence_unit_ids": [
            "v7u_N002243"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "监管机构可能考虑联合检查",
          "evidence_unit_ids": [
            "v7u_N002243"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "减少对机构的影响",
          "evidence_unit_ids": [
            "v7u_N002243"
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
          "condition": "areas that warrant it",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002243"
          ],
          "source_quote": "Regulators might consider joint examinations for areas that warrant it to reduce the impact on an organization."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002243"
          ],
          "source_quote": "Regulators might consider joint examinations for areas that warrant it to reduce the impact on an organization."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "检查发现问题后监管机构如何通知其他机构并可采取联合执法行动",
      "title": "检查发现问题后的通知与联合执法",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "检查发现问题或弱点",
          "evidence_unit_ids": [
            "v7u_N002244"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "监管机构通知其他相关监管机构",
          "evidence_unit_ids": [
            "v7u_N002244"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "在某些情况下可采取联合行动",
          "evidence_unit_ids": [
            "v7u_N002244"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "合并执法行动",
          "evidence_unit_ids": [
            "v7u_N002244"
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
          "condition": "检查发现 issues or weaknesses",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002244"
          ],
          "source_quote": "If an examination identifies issues or weaknesses, the regulator informs any other relevant regulators."
        },
        {
          "relation_id": "r002",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e003",
          "condition": "在某些实例下 (in some instances)",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002244"
          ],
          "source_quote": "In some instances, regulators can pursue joint action, resulting in combined enforcement action."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002244"
          ],
          "source_quote": "In some instances, regulators can pursue joint action, resulting in combined enforcement action."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_007"
      ],
      "focal_question": "一个司法辖区的问题或风险如何引发另一司法辖区的审查",
      "title": "跨辖区问题或风险触发其他辖区审查",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "一个司法辖区出现的问题或风险",
          "evidence_unit_ids": [
            "v7u_N002247"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "另一辖区监管机构可能进行审查",
          "evidence_unit_ids": [
            "v7u_N002247"
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
            "v7u_N002247"
          ],
          "source_quote": "Problems or risks in one jurisdiction might warrant scrutiny from regulators in another jurisdiction."
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
      "reason": "该候选描述了因多重监管情境触发协调检查的因果流程，包含明确的触发条件和协调动作。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了监管机构明确权限以避免重叠的程序，包含动作和目的性结果。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述了政策层面协调与比较以确保一体化监管的流程，包含动作和两个目的性结果。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选描述了协调工作安排以达成互补排期的执行流程。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选描述了基于领域必要性考虑联合检查并旨在减少影响的流程，包含触发条件和可选动作。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "该候选描述了检查发现问题后通知其他监管机构并可采取联合执法行动的条件性流程。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "mapped",
      "episode_ids": [
        "ep_007"
      ],
      "reason": "该候选描述了跨辖区问题或风险可能引发其他辖区审查的触发关系，构成一个开放流程。"
    },
    {
      "candidate_id": "s1c_008",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选描述的是欧盟新AML机构的职能设定，属于静态制度描述，没有原文明示的程序性触发、判断或迁移，不构成流程。"
    }
  ],
  "skip_reason": null
}
```
