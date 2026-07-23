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

section_id: `CH36-S03`

section_title: `Types of risk assessment > The risk-based approach`

section_text_with_unit_anchors:

```text
[v7u_N002672|2672] A risk-based approach (RBA) is the process of identifying, assessing, and understanding the ML/TF risks to which organizations are exposed and taking appropriate measures to mitigate those risks effectively.
ZH: 风险为本方法（RBA）定义：识别、评估和理解洗钱/恐怖融资风险并采取适当缓解措施

[v7u_N002673|2673] The concept of an RBA emerged when FATF published the first version of guidance for an RBA in 2007.
ZH: 风险为本方法概念源于FATF 2007年发布的指南

[v7u_N002674|2674] Every organization has its own risk appetite, which determines the type of customers it will accept, the product types it will offer, and the jurisdictions and channels in which it will operate.
ZH: 风险偏好定义：决定组织接受的客户类型、产品类型及运营的司法管辖区和渠道

[v7u_N002675|2675] Once the organization establishes its risk appetite, it establishes boundaries for its business.
ZH: 风险偏好为业务设定边界

[v7u_N002676|2676] For example, a payment processor may decide it is not in a position to offer its service in jurisdictions with elevated risk of sanctions.
ZH: 示例：支付处理商决定不在制裁风险高的司法管辖区提供服务

[v7u_N002677|2677] The risk appetite statement is codified in policies and procedures.
ZH: 风险偏好声明被编入政策和程序

[v7u_N002678|2678] In conducting a CRA, each customer is categorized and risk rated.
ZH: 客户风险评估（CRA）中对每位客户进行分类和风险评级

[v7u_N002679|2679] For example, an individual customer with a regular job and salary who opens a savings account is considered low risk, assuming the source of funds can be corroborated and there is no relevant, negative news.
ZH: 示例：有固定工作和薪水的个人开储蓄账户，资金来源可核实且无负面新闻，视为低风险

[v7u_N002680|2680] A PEP is considered higher risk.
ZH: 政治敏感人物（政治敏感人物）被视为较高风险

[v7u_N002681|2681] Products, jurisdictions, and channels also present varying risk levels.
ZH: 产品、司法管辖区和渠道呈现不同风险水平

[v7u_N002682|2682] A customer representing higher risk may be subject to enhanced due diligence and heightened monitoring, thereby allowing the organization to allocate resources effectively by classifying customers based on their potential financial crime risk.
ZH: 高风险客户需接受强化尽职调查和加强监控

[v7u_N002683|2683] These decisions determine the level and frequency of customer research and updates to customer profiles.
ZH: 风险决策决定客户调查的级别和频率

[v7u_N002684|2684] Risk assessment has become more important as the fight against financial crime has evolved, with regulators emphasizing the need for a risk-based approach in all customer interactions.
ZH: 风险识别在打击金融犯罪中日益重要

[v7u_N002685|2685] Accurately judging a customer’s potential involvement in financial crime is an important prerequisite for the RBA.
ZH: 准确判断客户金融犯罪风险是风险为本方法的前提

[v7u_N002686|2686] Organizations should conduct due diligence on business operations, industries, customer characteristics, and geographic exposure to obtain adequate, complete, and truthful customer information for analysis.
ZH: 机构应对业务、行业、客户特征和地域进行尽职调查

[v7u_N002687|2687] An RBA focuses effort with the greatest need and impact.
ZH: 风险为本方法将精力集中于最需要和影响最大的领域

[v7u_N002688|2688] It requires the full commitment and support of senior management, and the active cooperation of all employees.
ZH: 风险为本方法需要高级管理层承诺和全员配合

[v7u_N002689|2689] Adopting a risk-based approach requires a risk management process to handle financial crime. This process encompasses recognizing the risks, assessing them, and developing control strategies to mitigate and monitor them.
ZH: 采用风险为本方法需要风险管理流程：识别、评估、控制
```

allowed_unit_ids:

```json
[
  "v7u_N002672",
  "v7u_N002673",
  "v7u_N002674",
  "v7u_N002675",
  "v7u_N002676",
  "v7u_N002677",
  "v7u_N002678",
  "v7u_N002679",
  "v7u_N002680",
  "v7u_N002681",
  "v7u_N002682",
  "v7u_N002683",
  "v7u_N002684",
  "v7u_N002685",
  "v7u_N002686",
  "v7u_N002687",
  "v7u_N002688",
  "v7u_N002689"
]
```

## S2 Process IR

```json
{
  "section_id": "CH36-S03",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_gap_001"
      ],
      "focal_question": "如何基于风险偏好设定业务边界并将其政策化",
      "title": "确立风险偏好并设定业务边界与政策化",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "组织确立其风险偏好",
          "evidence_unit_ids": [
            "v7u_N002674"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "基于风险偏好设定业务边界",
          "evidence_unit_ids": [
            "v7u_N002675"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "将风险偏好声明编入政策和程序",
          "evidence_unit_ids": [
            "v7u_N002677"
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
            "v7u_N002674",
            "v7u_N002675"
          ],
          "source_quote": "Once the organization establishes its risk appetite, it establishes boundaries for its business."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e001",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002674",
            "v7u_N002677"
          ],
          "source_quote": "The risk appetite statement is codified in policies and procedures."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "如何进行客户风险评估并对客户分类评级",
      "title": "执行客户风险评估以分类和风险评级",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "进行客户风险评估，对每位客户进行分类和风险评级",
          "evidence_unit_ids": [
            "v7u_N002678"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "客户分类和风险评级结果",
          "evidence_unit_ids": [
            "v7u_N002678"
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
            "v7u_N002678"
          ],
          "source_quote": "In conducting a CRA, each customer is categorized and risk rated."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_005",
        "s1c_gap_002"
      ],
      "focal_question": "客户被判定为高风险后采取何种措施并如何决定后续监控",
      "title": "高风险客户触发强化尽职调查与监控并确定后续行动",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "客户呈现较高风险",
          "evidence_unit_ids": [
            "v7u_N002682"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "实施强化尽职调查和加强监控",
          "evidence_unit_ids": [
            "v7u_N002682"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "有效分配资源",
          "evidence_unit_ids": [
            "v7u_N002682"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "确定客户调查的级别和频率及更新客户档案",
          "evidence_unit_ids": [
            "v7u_N002683"
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
          "condition": "客户被分类为高风险或代表较高风险",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002682"
          ],
          "source_quote": "A customer representing higher risk may be subject to enhanced due diligence and heightened monitoring"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "helps_achieve",
          "evidence_unit_ids": [
            "v7u_N002682"
          ],
          "source_quote": "thereby allowing the organization to allocate resources effectively by classifying customers based on their potential financial crime risk"
        },
        {
          "relation_id": "r003",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e002",
          "process_element_id": "e004",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002682",
            "v7u_N002683"
          ],
          "source_quote": "These decisions determine the level and frequency of customer research and updates to customer profiles."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "机构如何通过尽职调查获取充分的客户分析信息",
      "title": "尽职调查获取完整客户信息用于分析",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "对业务、行业、客户特征和地域进行尽职调查",
          "evidence_unit_ids": [
            "v7u_N002686"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "获取充分、完整、真实的客户信息用于分析",
          "evidence_unit_ids": [
            "v7u_N002686"
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
            "v7u_N002686"
          ],
          "source_quote": "Organizations should conduct due diligence on business operations, industries, customer characteristics, and geographic exposure to obtain adequate, complete, and truthful customer information for analysis"
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
      "reason": "为解释风险偏好设定业务边界的具体示例，未单独形成程序性流程，而是对通用流程的举例说明。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了执行客户风险评估并进行分类和风险评级的明确流程，构成独立的评估程序。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "被动分类“视为低风险”仅给出静态判定条件，无原文明示的调查或分析过程，也未触发后续程序。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "同 s1c_003，被动分类“被视为较高风险”仅为静态事实陈述，不构成程序性流程。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "描述了高风险客户触发强化尽职调查和监控的条件性程序，并与后续调查决策共同形成完整的风险响应链。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "明确提出尽职调查的动作及目的，构成获取客户信息的执行流程。"
    },
    {
      "candidate_id": "s1c_gap_001",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "提供了从确立风险偏好到设定业务边界并政策化的完整管理流程，是独立的策略执行过程。"
    },
    {
      "candidate_id": "s1c_gap_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "承接高风险客户的处置决策，进一步确定后续调查和监控的具体要求，与 s1c_005 共同构成完整闭环。"
    }
  ],
  "skip_reason": null
}
```
