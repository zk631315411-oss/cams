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

section_id: `CH42-S01`

section_title: `Onboarding AFC controls > The KYC process`

section_text_with_unit_anchors:

```text
[v7u_N003011|3011] With evolving global regulatory frameworks, financial institutions must implement risk-based due diligence to prevent financial crime.
ZH: 金融机构必须实施基于风险的尽职调查以防止金融犯罪

[v7u_N003012|3012] The KYC process is a core requirement in AFC compliance, ensuring financial institutions identify, verify, and assess customer risks before establishing or maintaining business relationships.
ZH: 了解你的客户流程是金融犯罪合规的核心要求，用于识别、验证和评估客户风险

[v7u_N003013|3013] For specific customer profiles, such as PEPs, high-net-worth individuals, and customers from high-risk jurisdictions, a pre-KYC onboarding committee might assess suitability before formal identification.
ZH: 对于政治敏感人物等特定客户，在正式了解你的客户前由委员会评估其适宜性

[v7u_N003014|3014] The committee typically includes compliance experts, risk managers, legal advisors, and business unit leaders, who collectively evaluate jurisdictional risks, business activities, and strategic fit.
ZH: 委员会由合规、风险、法务及业务部门代表组成，评估司法管辖区风险等

[v7u_N003015|3015] The outcome determines whether customers proceed to full KYC and what level of due diligence—standard or enhanced—is required.
ZH: 委员会评估结果决定客户是否进入完整了解你的客户及所需尽职调查级别

[v7u_N003016|3016] This step ensures efficient resource use, early risk mitigation, and regulatory alignment by filtering out unsuitable clients early in the process.
ZH: 了解你的客户前步骤旨在早期过滤不合适客户，确保资源高效利用和监管合规

[v7u_N003017|3017] The typical KYC/CDD process consists of the following steps:
ZH: 典型的了解你的客户/客户尽职调查流程包含以下步骤

[v7u_N003018|3018] Identity and verification (ID&V):
ZH: 身份识别与验证步骤

[v7u_N003019|3019] Identification is the collection of personal and business details, including name, date of birth, nationality, address, tax identification number, and company registration data.
ZH: 身份识别是收集个人和企业的详细信息

[v7u_N003020|3020] Verification is the authentication of provided information using government-issued documents, biometric authentication, AI-driven verification tools, and forensic analysis of identification records.
ZH: 验证是通过政府文件、生物识别等技术对信息进行认证

[v7u_N003021|3021] Organizations must understand and obtain information, as appropriate, on the purpose and intended nature of the customer’s relationship with the organization.
ZH: 机构必须了解客户关系的预期目的和性质

[v7u_N003022|3022] Enhanced regulations require organizations to determine the ultimate beneficial owners (UBOs) of corporate accounts.
ZH: 强化法规要求机构确定公司账户的最终受益所有人

[v7u_N003023|3023] Screening is conducted prior to onboarding to determine risk:
ZH: 在客户准入前进行筛查以确定风险

[v7u_N003024|3024] Sanctions screening is when customer details are cross-checked against UN, EU, OFAC, and national sanctions lists to detect high-risk entities.
ZH: 制裁筛查是将客户信息与联合国、欧盟、OFAC及国家制裁名单进行交叉核对

[v7u_N003025|3025] Adverse media monitoring is conducted to identify links to financial crime, corruption, and fraudulent activities.
ZH: 负面媒体监控旨在识别与金融犯罪、腐败和欺诈活动的关联

[v7u_N003026|3026] PEP screening is when organizations determine whether the individual or beneficial owner is a PEP, or the relative or close associate of a PEP.
ZH: 政治敏感人物筛查用于确定个人或受益所有人是否为政治敏感人物或其亲属或密切关联人
```

allowed_unit_ids:

```json
[
  "v7u_N003011",
  "v7u_N003012",
  "v7u_N003013",
  "v7u_N003014",
  "v7u_N003015",
  "v7u_N003016",
  "v7u_N003017",
  "v7u_N003018",
  "v7u_N003019",
  "v7u_N003020",
  "v7u_N003021",
  "v7u_N003022",
  "v7u_N003023",
  "v7u_N003024",
  "v7u_N003025",
  "v7u_N003026"
]
```

## S2 Process IR

```json
{
  "section_id": "CH42-S01",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "如何根据委员会评估决定特定客户是否进入完整KYC及尽职调查级别",
      "title": "Pre-KYC委员会评估客户适宜性并决定后续KYC路径",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "特定客户类型，如PEP、高净值人士、高风险司法管辖区客户",
          "evidence_unit_ids": [
            "v7u_N003013"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "委员会 might assess 客户适宜性，决定是否进入完整KYC及所需DD级别",
          "evidence_unit_ids": [
            "v7u_N003013",
            "v7u_N003015"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "standard",
          "label": "委员会评估因素：司法管辖区风险、业务活动、战略契合度",
          "evidence_unit_ids": [
            "v7u_N003014"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "客户进入完整KYC，适用标准尽职调查",
          "evidence_unit_ids": [
            "v7u_N003015"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "客户进入完整KYC，适用强化尽职调查",
          "evidence_unit_ids": [
            "v7u_N003015"
          ],
          "modality": null
        },
        {
          "element_id": "e006",
          "role": "outcome",
          "label": "客户被过滤，不进入完整KYC",
          "evidence_unit_ids": [
            "v7u_N003015",
            "v7u_N003016"
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
          "condition": "客户属于特定高风险类型（PEP、高净值、高风险司法管辖区）",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N003013"
          ],
          "source_quote": "For specific customer profiles, such as PEPs, high-net-worth individuals, and customers from high-risk jurisdictions, a pre-KYC onboarding committee might assess suitability before formal identification."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e003",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N003014"
          ],
          "source_quote": "The committee typically includes compliance experts, risk managers, legal advisors, and business unit leaders, who collectively evaluate jurisdictional risks, business activities, and strategic fit."
        },
        {
          "relation_id": "r003",
          "kind": "branch",
          "decision_element_id": "e002",
          "target_element_id": "e004",
          "condition": "评估结果认为客户适宜且适用标准尽职调查",
          "relation_type": "branch_condition_routes_path",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N003015"
          ],
          "source_quote": "The outcome determines whether customers proceed to full KYC and what level of due diligence—standard or enhanced—is required."
        },
        {
          "relation_id": "r004",
          "kind": "branch",
          "decision_element_id": "e002",
          "target_element_id": "e005",
          "condition": "评估结果认为客户适宜且适用强化尽职调查",
          "relation_type": "branch_condition_routes_path",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N003015"
          ],
          "source_quote": "The outcome determines whether customers proceed to full KYC and what level of due diligence—standard or enhanced—is required."
        },
        {
          "relation_id": "r005",
          "kind": "branch",
          "decision_element_id": "e002",
          "target_element_id": "e006",
          "condition": "评估结果认为客户不适宜",
          "relation_type": "branch_condition_routes_path",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N003015",
            "v7u_N003016"
          ],
          "source_quote": "The outcome determines whether customers proceed to full KYC and what level of due diligence—standard or enhanced—is required. This step ensures efficient resource use, early risk mitigation, and regulatory alignment by filtering out unsuitable clients early in the process."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "如何在客户准入前通过筛查确定风险",
      "title": "客户准入前筛查以确定风险",
      "card_nature": "risk_indicator",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "客户准入前",
          "evidence_unit_ids": [
            "v7u_N003023"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "制裁筛查：将客户信息与联合国、欧盟、OFAC及国家制裁名单交叉核对",
          "evidence_unit_ids": [
            "v7u_N003024"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "负面媒体监控：识别与金融犯罪、腐败和欺诈活动的关联",
          "evidence_unit_ids": [
            "v7u_N003025"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "PEP筛查：确定个人或受益所有人是否为PEP或其密切关联人",
          "evidence_unit_ids": [
            "v7u_N003026"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "检测高风险实体",
          "evidence_unit_ids": [
            "v7u_N003024"
          ],
          "modality": null
        },
        {
          "element_id": "e006",
          "role": "outcome",
          "label": "识别金融犯罪、腐败和欺诈活动关联",
          "evidence_unit_ids": [
            "v7u_N003025"
          ],
          "modality": null
        },
        {
          "element_id": "e007",
          "role": "outcome",
          "label": "确定PEP身份或关联",
          "evidence_unit_ids": [
            "v7u_N003026"
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
          "condition": "在客户准入前开展筛查",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N003023"
          ],
          "source_quote": "Screening is conducted prior to onboarding to determine risk:"
        },
        {
          "relation_id": "r002",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e003",
          "condition": "在客户准入前开展筛查",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N003023"
          ],
          "source_quote": "Screening is conducted prior to onboarding to determine risk:"
        },
        {
          "relation_id": "r003",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e004",
          "condition": "在客户准入前开展筛查",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N003023"
          ],
          "source_quote": "Screening is conducted prior to onboarding to determine risk:"
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e005",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N003024"
          ],
          "source_quote": "Sanctions screening is when customer details are cross-checked against UN, EU, OFAC, and national sanctions lists to detect high-risk entities."
        },
        {
          "relation_id": "r005",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e006",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N003025"
          ],
          "source_quote": "Adverse media monitoring is conducted to identify links to financial crime, corruption, and fraudulent activities."
        },
        {
          "relation_id": "r006",
          "kind": "produce",
          "process_element_id": "e004",
          "outcome_element_id": "e007",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N003026"
          ],
          "source_quote": "PEP screening is when organizations determine whether the individual or beneficial owner is a PEP, or the relative or close associate of a PEP."
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
      "reason": "该候选描述了特定客户类型触发委员会评估适宜性，并决定后续KYC路径，构成完整的评估决策流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选仅描述身份识别与验证步骤的组成要素（收集信息、验证、了解目的、识别UBO），未包含程序性或判断性迁移关系，属于静态定义性内容。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了客户准入前筛查流程，包括制裁、负面媒体和PEP筛查及其风险检测目的，构成清晰的程序性流程。"
    }
  ],
  "skip_reason": null
}
```
