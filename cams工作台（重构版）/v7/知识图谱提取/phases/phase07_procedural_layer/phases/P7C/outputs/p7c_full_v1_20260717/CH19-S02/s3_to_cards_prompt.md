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

section_id: `CH19-S02`

section_title: `Financial Action Task Force > FATF Recommendations 1-8`

section_text_with_unit_anchors:

```text
[v7u_N001340|1340] FATF Recommendations 1 to 8 ensure that member jurisdictions implement comprehensive legal and regulatory frameworks to combat money laundering, terrorist financing, and the proliferation of weapons of mass destruction (WMD). These recommendations fall into three groups.
ZH: FATF建议1-8确保成员国建立全面的法律和监管框架以打击洗钱、恐怖融资和扩散融资

[v7u_N001341|1341] Recommendations 1 and 2 advise jurisdictions to assess and understand their money laundering and terrorist financing risks and take a risk-based approach to implementing measures that effectively mitigate these threats.
ZH: FATF建议1和2要求各国评估洗钱和恐怖融资风险并采取风险为本方法

[v7u_N001342|1342] A riskbased approach ensures that responses are proportionate to the identified risks.
ZH: 风险为本方法确保应对措施与识别出的风险成比例

[v7u_N001343|1343] Additionally, national cooperation and coordination are essential, requiring jurisdictions to establish AML/CFT policies informed by risk assessments.
ZH: 各国需建立基于风险评估的反洗钱/反恐怖融资政策并开展国家合作与协调

[v7u_N001344|1344] Jurisdictions should also designate an authority or mechanism responsible for implementation.
ZH: 各国应指定负责实施反洗钱措施的机关或机制

[v7u_N001345|1345] Effective mechanisms should facilitate coordination and collaboration among relevant authorities.
ZH: 要求建立有效机制促进相关当局之间的协调与合作

[v7u_N001346|1346] Recommendations 3 and 4 advise jurisdictions to criminalize money laundering, ensuring that the offense applies to all serious crimes and encompasses a broad range of predicate offenses.
ZH: FATF建议3和4要求将洗钱定为刑事犯罪并涵盖广泛的上游犯罪

[v7u_N001347|1347] Additionally, jurisdictions should implement measures that empower competent authorities to identify, trace, freeze, seize, and confiscate criminal property and assets of equivalent value.
ZH: 授权主管机关识别、追踪、冻结、扣押和没收犯罪财产及等值资产

[v7u_N001348|1348] These measures ensure effective asset recovery and the prevention of illicit financial gains.
ZH: 资产追缴措施旨在有效追回资产并防止非法资金收益

[v7u_N001349|1349] Recommendations 5 to 8 advise jurisdictions to criminalize terrorist financing in line with the Terrorist Financing Convention, ensuring it covers the financing of terrorist acts, organizations, and individuals, even in the absence of a direct link to a specific act.
ZH: FATF建议5至8要求按照《恐怖融资公约》将恐怖融资定为刑事犯罪

[v7u_N001350|1350] Jurisdictions should also implement targeted financial sanctions in compliance with UN Security Council resolutions; this includes freezing the assets of designated persons or entities without delay to combat the financing of terrorism.
ZH: 各国应实施定向金融制裁，立即冻结涉恐人员或实体的资产

[v7u_N001351|1351] Similarly, jurisdictions should apply targeted financial sanctions to prevent and disrupt the financing of the proliferation of WMDs.
ZH: 各国应实施定向金融制裁以防止和阻断大规模杀伤性武器扩散融资

[v7u_N001352|1352] Additionally, jurisdictions should identify nonprofit organizations at risk of terrorist financing abuse and implement proportionate, risk-based measures to protect them while ensuring that legitimate activities remain unaffected.
ZH: 识别面临恐怖融资滥用风险的非营利组织并采取风险为本的保护措施
```

allowed_unit_ids:

```json
[
  "v7u_N001340",
  "v7u_N001341",
  "v7u_N001342",
  "v7u_N001343",
  "v7u_N001344",
  "v7u_N001345",
  "v7u_N001346",
  "v7u_N001347",
  "v7u_N001348",
  "v7u_N001349",
  "v7u_N001350",
  "v7u_N001351",
  "v7u_N001352"
]
```

## S2 Process IR

```json
{
  "section_id": "CH19-S02",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_gap_ch19_s02_risk_based_approach"
      ],
      "focal_question": "如何通过风险评估和风险为本方法缓解洗钱与恐怖融资威胁？",
      "title": "依据风险评估和风险为本方法实施有效措施",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "评估和理解洗钱和恐怖融资风险",
          "evidence_unit_ids": [
            "v7u_N001341"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "风险为本方法",
          "evidence_unit_ids": [
            "v7u_N001341"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "实施有效措施",
          "evidence_unit_ids": [
            "v7u_N001341"
          ],
          "modality": "required"
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "有效缓解威胁",
          "evidence_unit_ids": [
            "v7u_N001341"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "sequence",
          "before_element_id": "e001",
          "after_element_id": "e003",
          "evidence_unit_ids": [
            "v7u_N001341"
          ],
          "source_quote": "assess and understand their money laundering and terrorist financing risks and take a risk-based approach to implementing measures"
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "evidence_unit_ids": [
            "v7u_N001341"
          ],
          "source_quote": "take a risk-based approach to implementing measures"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001341"
          ],
          "source_quote": "implementing measures that effectively mitigate these threats"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_gap_ch19_s02_aml_cft_policy"
      ],
      "focal_question": "如何基于风险评估建立 AML/CFT 政策以满足国家合作与协调需求？",
      "title": "基于风险评估建立反洗钱/反恐怖融资政策",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "国家合作与协调必不可少",
          "evidence_unit_ids": [
            "v7u_N001343"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "风险评估",
          "evidence_unit_ids": [
            "v7u_N001343"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "建立 AML/CFT 政策",
          "evidence_unit_ids": [
            "v7u_N001343"
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
          "process_element_id": "e003",
          "condition": null,
          "evidence_unit_ids": [
            "v7u_N001343"
          ],
          "source_quote": "national cooperation and coordination are essential, requiring jurisdictions to establish AML/CFT policies"
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "evidence_unit_ids": [
            "v7u_N001343"
          ],
          "source_quote": "establish AML/CFT policies informed by risk assessments"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_gap_ch19_s02_effective_mechanism"
      ],
      "focal_question": "如何建立有效机制促进相关当局协调合作？",
      "title": "建立有效机制促进协调合作",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "建立有效机制",
          "evidence_unit_ids": [
            "v7u_N001345"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "促进相关当局之间的协调与合作",
          "evidence_unit_ids": [
            "v7u_N001345"
          ],
          "modality": "required"
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
            "v7u_N001345"
          ],
          "source_quote": "Effective mechanisms should facilitate coordination and collaboration among relevant authorities"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_gap_ch19_s02_criminalize_ml"
      ],
      "focal_question": "如何将洗钱刑事化并确保覆盖广泛上游犯罪？",
      "title": "将洗钱刑事化并确保广泛适用",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "将洗钱定为刑事犯罪",
          "evidence_unit_ids": [
            "v7u_N001346"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "洗钱犯罪适用于所有严重犯罪和广泛上游犯罪",
          "evidence_unit_ids": [
            "v7u_N001346"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e002",
          "evidence_unit_ids": [
            "v7u_N001346"
          ],
          "source_quote": "ensuring that the offense applies to all serious crimes and encompasses a broad range of predicate offenses"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_gap_ch19_s02_asset_recovery"
      ],
      "focal_question": "如何通过实施授权措施实现有效资产追回？",
      "title": "实施授权措施追缴资产并防止非法收益",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "实施措施",
          "evidence_unit_ids": [
            "v7u_N001347"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "主管机关被授权识别、追踪、冻结、扣押和没收犯罪财产及等值资产",
          "evidence_unit_ids": [
            "v7u_N001347"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "有效资产追回和防止非法收益",
          "evidence_unit_ids": [
            "v7u_N001348"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e002",
          "evidence_unit_ids": [
            "v7u_N001347"
          ],
          "source_quote": "implement measures that empower competent authorities to identify, trace, freeze, seize, and confiscate criminal property and assets of equivalent value"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "evidence_unit_ids": [
            "v7u_N001348"
          ],
          "source_quote": "These measures ensure effective asset recovery and the prevention of illicit financial gains"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_gap_ch19_s02_criminalize_tf"
      ],
      "focal_question": "如何根据《恐怖融资公约》将恐怖融资刑事化并确保广泛覆盖？",
      "title": "依据公约将恐怖融资刑事化并确保覆盖范围",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "《恐怖融资公约》",
          "evidence_unit_ids": [
            "v7u_N001349"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "将恐怖融资刑事化",
          "evidence_unit_ids": [
            "v7u_N001349"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "覆盖恐怖行为、组织和个人，即使无直接联系",
          "evidence_unit_ids": [
            "v7u_N001349"
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
            "v7u_N001349"
          ],
          "source_quote": "criminalize terrorist financing in line with the Terrorist Financing Convention"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "evidence_unit_ids": [
            "v7u_N001349"
          ],
          "source_quote": "ensuring it covers the financing of terrorist acts, organizations, and individuals, even in the absence of a direct link to a specific act"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_gap_ch19_s02_targeted_sanctions_tf"
      ],
      "focal_question": "如何根据安理会决议实施定向金融制裁打击恐怖融资？",
      "title": "依据安理会决议实施定向金融制裁打击恐怖融资",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "联合国安理会决议",
          "evidence_unit_ids": [
            "v7u_N001350"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "实施定向金融制裁，包括立即冻结指定人员或实体的资产",
          "evidence_unit_ids": [
            "v7u_N001350"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "打击恐怖融资",
          "evidence_unit_ids": [
            "v7u_N001350"
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
            "v7u_N001350"
          ],
          "source_quote": "implement targeted financial sanctions in compliance with UN Security Council resolutions"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001350"
          ],
          "source_quote": "freezing the assets of designated persons or entities without delay to combat the financing of terrorism"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_008",
      "source_candidate_ids": [
        "s1c_gap_ch19_s02_targeted_sanctions_wmd"
      ],
      "focal_question": "如何实施定向金融制裁预防和阻断 WMD 扩散融资？",
      "title": "实施定向金融制裁防止 WMD 扩散融资",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "实施定向金融制裁",
          "evidence_unit_ids": [
            "v7u_N001351"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "预防和阻断 WMD 扩散融资",
          "evidence_unit_ids": [
            "v7u_N001351"
          ],
          "modality": "required"
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
            "v7u_N001351"
          ],
          "source_quote": "apply targeted financial sanctions to prevent and disrupt the financing of the proliferation of WMDs"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_009",
      "source_candidate_ids": [
        "s1c_gap_ch19_s02_npo_protection"
      ],
      "focal_question": "如何识别并保护面临恐怖融资滥用风险的非营利组织同时确保合法活动不受影响？",
      "title": "识别并保护面临风险的非营利组织",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "识别面临恐怖融资滥用风险的非营利组织",
          "evidence_unit_ids": [
            "v7u_N001352"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "实施相称的、基于风险的措施",
          "evidence_unit_ids": [
            "v7u_N001352"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "standard",
          "label": "风险为本的方法",
          "evidence_unit_ids": [
            "v7u_N001352"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "保护非营利组织",
          "evidence_unit_ids": [
            "v7u_N001352"
          ],
          "modality": "required"
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "确保合法活动不受影响",
          "evidence_unit_ids": [
            "v7u_N001352"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "sequence",
          "before_element_id": "e001",
          "after_element_id": "e002",
          "evidence_unit_ids": [
            "v7u_N001352"
          ],
          "source_quote": "identify nonprofit organizations at risk of terrorist financing abuse and implement proportionate, risk-based measures"
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e003",
          "evidence_unit_ids": [
            "v7u_N001352"
          ],
          "source_quote": "implement proportionate, risk-based measures"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001352"
          ],
          "source_quote": "implement ... measures to protect them"
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e005",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001352"
          ],
          "source_quote": "while ensuring that legitimate activities remain unaffected"
        }
      ],
      "split_reason": null
    }
  ],
  "candidate_audit": [
    {
      "candidate_id": "s1c_gap_ch19_s02_risk_based_approach",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选描述了完整的风险评估与风险为本实施流程，独立支持程序性迁移。"
    },
    {
      "candidate_id": "s1c_gap_ch19_s02_aml_cft_policy",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选提供了建立AML/CFT政策的触发条件、标准和动作，构成合规程序。"
    },
    {
      "candidate_id": "s1c_gap_ch19_s02_designate_authority",
      "disposition": "ungraphable",
      "episode_ids": [],
      "reason": "该候选仅包含单个动作元素，无法形成至少一条关系，不足以构建流程episode。"
    },
    {
      "candidate_id": "s1c_gap_ch19_s02_effective_mechanism",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选明确了建立机制及其目的，构成有目的的业务动作与结果关系。"
    },
    {
      "candidate_id": "s1c_gap_ch19_s02_criminalize_ml",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选描述了将洗钱刑事化并确保适用范围的程序，包含动作与结果关系。"
    },
    {
      "candidate_id": "s1c_gap_ch19_s02_asset_recovery",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选提供了完整的资产追缴措施实施流程，从授权到最终追回与防止非法收益。"
    },
    {
      "candidate_id": "s1c_gap_ch19_s02_criminalize_tf",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "该候选描述了依据公约将恐怖融资刑事化并确保覆盖的流程。"
    },
    {
      "candidate_id": "s1c_gap_ch19_s02_targeted_sanctions_tf",
      "disposition": "mapped",
      "episode_ids": [
        "ep_007"
      ],
      "reason": "该候选给出了依据安理会决议实施定向金融制裁打击恐怖融资的完整程序。"
    },
    {
      "candidate_id": "s1c_gap_ch19_s02_targeted_sanctions_wmd",
      "disposition": "mapped",
      "episode_ids": [
        "ep_008"
      ],
      "reason": "该候选描述了实施定向金融制裁以防止WMD扩散融资的动作与目的关系。"
    },
    {
      "candidate_id": "s1c_gap_ch19_s02_npo_protection",
      "disposition": "mapped",
      "episode_ids": [
        "ep_009"
      ],
      "reason": "该候选提供了识别NPO、实施风险为本保护措施并确保合法活动不受影响的完整流程。"
    }
  ],
  "skip_reason": null
}
```
