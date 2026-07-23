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

section_id: `CH24-S08`

section_title: `US AML/CFT regulatory landscape > EU AML package`

section_text_with_unit_anchors:

```text
[v7u_N001800|1800] In 2024, the EU adopted a package of AML legislation known as the “Single Rulebook.” The package consists of:
ZH: 2024年欧盟通过反洗钱立法包“单一规则手册”，包含以下内容。

[v7u_N001801|1801] Directive (EU) 2024/1640, also called 6AMLD.
ZH: 欧盟第六反洗钱指令（6反洗钱D）

[v7u_N001802|1802] Regulation (EU) 2024/1624, also called AMLR.
ZH: 欧盟反洗钱条例（反洗钱R）

[v7u_N001803|1803] Regulation (EU) 2024/1620, also called AMLA-R.
ZH: 欧盟反洗钱管理局条例（反洗钱A-R）

[v7u_N001804|1804] Regulation (EU) 2023/1113, also called FTR.
ZH: 欧盟资金转移条例（FTR）

[v7u_N001805|1805] 6AMLD builds on previous AMLDs, such as Directive (EU) 2015/849 (4AMLD).
ZH: 6反洗钱D建立在先前反洗钱指令基础上

[v7u_N001806|1806] The 6AMLD requires financial institutions and other obligated entities to implement comprehensive CDD procedures, maintain central registers of beneficial ownership information, and conduct risk assessments on state and supranational levels.
ZH: 6反洗钱D要求义务实体实施全面的客户尽职调查、维护受益所有人中央登记册并开展风险评估

[v7u_N001807|1807] 6AMLD enhances the role of FIUs and strengthens cooperation between national FIUs and other AML authorities.
ZH: 6反洗钱D强化了金融情报机构（FIU）的作用并加强了合作

[v7u_N001808|1808] The EU requires its member states to transpose 6AMLD provisions into law.
ZH: 欧盟要求成员国将6反洗钱D条款转化为国内法

[v7u_N001809|1809] The goal of AMLR is to harmonize CDD and risk assessment requirements across member states.
ZH: 反洗钱R旨在统一各成员国的客户尽职调查和风险评估要求

[v7u_N001810|1810] This regulation sets a €10,000 limit for cash-based transactions and strengthens rules on PEPs, beneficial ownership, and beneficial owner disclosure obligations for firms in developing nations purchasing high-worth vehicles and real estate assets.
ZH: 反洗钱R设定现金交易1万欧元限额，并加强政治敏感人物、受益所有人及披露规则

[v7u_N001811|1811] AMLR requires obliged entities to assess all AML staff for skills, good repute, honesty, and integrity.
ZH: 反洗钱R要求义务实体评估反洗钱人员的技能、声誉、诚实和正直

[v7u_N001812|1812] It also strengthens rules on SARs and penalties for violations.
ZH: 反洗钱R加强了可疑交易报告（SAR）规则和违规处罚

[v7u_N001813|1813] AMLR expands the perimeter of obliged entities to include soccer agents, professional football clubs, and investment migration operators.
ZH: 反洗钱R将义务实体范围扩展至足球经纪人、职业足球俱乐部和投资移民运营商

[v7u_N001814|1814] Provisions relating to the football sector, the creation of a single access point to real estate information, and the interconnection of bank account registers go into effect after the majority of provisions in AMLR.
ZH: 反洗钱R中关于足球行业、房地产信息单一接入点和银行账户登记互联的条款稍后生效

[v7u_N001815|1815] AMLA-R establishes an EU Anti-Money Laundering Authority (AML Authority, known as AMLA in Europe), which is responsible for the direct supervision of selected obliged entities in the financial sector.
ZH: 反洗钱A-R设立欧盟反洗钱管理局（反洗钱A），负责直接监督部分金融行业义务实体

[v7u_N001816|1816] These obliged entities are selected based on the high residual risk profile.
ZH: 义务实体根据高剩余风险状况被选为直接监督对象

[v7u_N001817|1817] Additionally, AMLA-R coordinates supervision of NCAs and drafts level-2 regulations and guidelines.
ZH: 反洗钱A-R协调国家主管机构（NCA）的监督并起草二级法规和指南

[v7u_N001818|1818] The majority of AMLA-R went into effect in July 2025.
ZH: 反洗钱A-R大部分条款于2025年7月生效

[v7u_N001819|1819] FTR implements FATF’s recommendations on cryptoassets and prohibits anonymous cryptoasset accounts and transactions.
ZH: FTR落实FATF关于加密资产的建议，禁止匿名加密资产账户和交易

[v7u_N001820|1820] FTR is a recast of the Regulation (EU) 2015/847 on information accompanying transfers of funds.
ZH: FTR是对资金转移信息条例（EU 2015/847）的重订

[v7u_N001821|1821] Together with the Markets in Cryptoassets Regulation (MiCA), FTR went into effect in December 2024.
ZH: FTR与MiCA于2024年12月生效
```

allowed_unit_ids:

```json
[
  "v7u_N001800",
  "v7u_N001801",
  "v7u_N001802",
  "v7u_N001803",
  "v7u_N001804",
  "v7u_N001805",
  "v7u_N001806",
  "v7u_N001807",
  "v7u_N001808",
  "v7u_N001809",
  "v7u_N001810",
  "v7u_N001811",
  "v7u_N001812",
  "v7u_N001813",
  "v7u_N001814",
  "v7u_N001815",
  "v7u_N001816",
  "v7u_N001817",
  "v7u_N001818",
  "v7u_N001819",
  "v7u_N001820",
  "v7u_N001821"
]
```

## S2 Process IR

```json
{
  "section_id": "CH24-S08",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "6AMLD要求义务实体采取哪些核心措施？",
      "title": "6AMLD对义务实体的核心要求",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "6AMLD requirements",
          "evidence_unit_ids": [
            "v7u_N001806"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Implement comprehensive CDD procedures",
          "evidence_unit_ids": [
            "v7u_N001806"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "Maintain central registers of beneficial ownership information",
          "evidence_unit_ids": [
            "v7u_N001806"
          ],
          "modality": "required"
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "Conduct risk assessments on state and supranational levels",
          "evidence_unit_ids": [
            "v7u_N001806"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001806"
          ],
          "source_quote": "The 6AMLD requires financial institutions and other obligated entities to implement comprehensive CDD procedures, maintain central registers of beneficial ownership information, and conduct risk assessments on state and supranational levels."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e001",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001806"
          ],
          "source_quote": "The 6AMLD requires financial institutions and other obligated entities to implement comprehensive CDD procedures, maintain central registers of beneficial ownership information, and conduct risk assessments on state and supranational levels."
        },
        {
          "relation_id": "r003",
          "kind": "reference",
          "process_element_id": "e004",
          "auxiliary_element_id": "e001",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001806"
          ],
          "source_quote": "The 6AMLD requires financial institutions and other obligated entities to implement comprehensive CDD procedures, maintain central registers of beneficial ownership information, and conduct risk assessments on state and supranational levels."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "成员国如何履行6AMLD的法律转化义务？",
      "title": "成员国将6AMLD条款转化为国内法",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "EU's requirement to transpose 6AMLD into law",
          "evidence_unit_ids": [
            "v7u_N001808"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Member states transpose 6AMLD provisions into national law",
          "evidence_unit_ids": [
            "v7u_N001808"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001808"
          ],
          "source_quote": "The EU requires its member states to transpose 6AMLD provisions into law."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "AMLR对义务实体评估反洗钱人员有何要求？",
      "title": "AMLR要求评估反洗钱人员",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "AMLR requirements for staff assessment",
          "evidence_unit_ids": [
            "v7u_N001811"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Assess all AML staff for skills, good repute, honesty, and integrity",
          "evidence_unit_ids": [
            "v7u_N001811"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001811"
          ],
          "source_quote": "AMLR requires obliged entities to assess all AML staff for skills, good repute, honesty, and integrity."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "AMLA如何选择直接监督对象并实施监督？",
      "title": "AMLA基于高剩余风险选择并直接监督义务实体",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "High residual risk profile",
          "evidence_unit_ids": [
            "v7u_N001816"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "Select obliged entities in the financial sector",
          "evidence_unit_ids": [
            "v7u_N001815",
            "v7u_N001816"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "Directly supervise selected obliged entities",
          "evidence_unit_ids": [
            "v7u_N001815"
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
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001816"
          ],
          "source_quote": "These obliged entities are selected based on the high residual risk profile."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001815"
          ],
          "source_quote": "AMLA-R establishes an EU Anti-Money Laundering Authority ... which is responsible for the direct supervision of selected obliged entities in the financial sector."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_007"
      ],
      "focal_question": "FTR对加密资产匿名性有何禁令？",
      "title": "FTR禁止匿名加密资产账户和交易",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "FTR regulation (implementing FATF recommendations)",
          "evidence_unit_ids": [
            "v7u_N001819"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Prohibit anonymous cryptoasset accounts and transactions",
          "evidence_unit_ids": [
            "v7u_N001819"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001819"
          ],
          "source_quote": "FTR implements FATF’s recommendations on cryptoassets and prohibits anonymous cryptoasset accounts and transactions."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_gap_ch24_s08_amla_coordination"
      ],
      "focal_question": "AMLA如何履行协调监督与规则制定职责？",
      "title": "AMLA协调国家监管和起草二级法规",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "AMLA-R requirements",
          "evidence_unit_ids": [
            "v7u_N001817"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Coordinate supervision of NCAs",
          "evidence_unit_ids": [
            "v7u_N001817"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "Draft level-2 regulations and guidelines",
          "evidence_unit_ids": [
            "v7u_N001817"
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
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001817"
          ],
          "source_quote": "Additionally, AMLA-R coordinates supervision of NCAs and drafts level-2 regulations and guidelines."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e001",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001817"
          ],
          "source_quote": "Additionally, AMLA-R coordinates supervision of NCAs and drafts level-2 regulations and guidelines."
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
      "reason": "候选描述了6AMLD对义务实体的要求，构成了法规驱动业务动作的流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "候选描述了欧盟要求成员国转化指令的过程，为要求驱动的流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "候选仅陈述法规设定的静态限额和规则加强，未包含业务处理或判断过程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "候选描述了AMLR要求义务实体评估人员的过程。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "候选仅陈述义务实体范围扩展，属静态事实，无流程。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "候选包含了基于风险状况选择义务实体并直接监督的决策与执行流程。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "候选描述了FTR禁止匿名加密资产账户的监管要求流程。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s08_fiu_role",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "候选仅陈述6AMLD增强FIU角色的效果，无具体业务处理过程。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s08_sar_penalties",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "候选仅陈述AMLR加强可疑交易报告规则，无业务处理过程。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s08_amla_coordination",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "候选描述了AMLA协调监督与起草规则的执行职责。"
    }
  ],
  "skip_reason": null
}
```
