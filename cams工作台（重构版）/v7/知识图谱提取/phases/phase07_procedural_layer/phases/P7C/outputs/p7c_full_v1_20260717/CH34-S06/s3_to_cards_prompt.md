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

section_id: `CH34-S06`

section_title: `Three lines of defense > Financial crime functions' structure`

section_text_with_unit_anchors:

```text
[v7u_N002460|2460] The second line of defense in AFC consists of various functions, each specializing in distinct compliance and risk management areas. Each function has specific structures, roles, and responsibilities.
ZH: 第二道防线金融犯罪防控职能由多个专门领域组成，各有特定结构、角色与职责。

[v7u_N002461|2461] How an organization structures its second-line AFC function depends on its size, complexity, geographic reach, and legacy.
ZH: 第二道防线金融犯罪防控职能的结构取决于组织的规模、复杂性、地理覆盖和历史因素。

[v7u_N002462|2462] The following is a list of typical AFC functions found within the second line of defense.
ZH: 列出第二道防线中典型的金融犯罪防控职能。

[v7u_N002463|2463] In some organizations, the data analytics function sits within the transaction monitoring function. This function identifies financial crime risk patterns and trends. They develop analytical models to detect anomalies and flag fraudulent or suspicious transactions.
ZH: 数据分析职能识别金融犯罪风险模式与趋势，开发分析模型检测异常和可疑交易。

[v7u_N002464|2464] The model risk management function is responsible for overseeing the validation and governance of AFC models, including transaction monitoring systems. Such systems evaluate the effectiveness of these models to ensure accuracy and compliance with regulatory standards.
ZH: 模型风险管理职能负责金融犯罪防控模型的验证与治理，包括交易监控系统，确保准确性和合规性。

[v7u_N002465|2465] The investigation function conducts in-depth investigations of suspicious activities identified by transaction monitoring or reported by employees. This function gathers evidence, analyzes information, and prepares SARs plus internal and external reports.
ZH: 调查职能对可疑活动进行深入调查，收集证据，分析信息，并准备可疑活动报告（SAR）。

[v7u_N002466|2466] The policies management function develops, maintains, and updates AFC policies and procedures to ensure compliance with evolving regulations. This function collaborates with other departments to implement policies, manage document control, and change management.
ZH: 政策管理职能制定、维护和更新金融犯罪防控政策与程序，确保合规并管理文档变更。

[v7u_N002467|2467] The regulatory reporting and liaison function files the required regulatory reports, such as SARs and currency transaction reports (CTR). This function liaises with regulatory authorities to ensure accurate, timely submissions and acts as a point of contact for regulatory audits and inquiries.
ZH: 监管报告与联络职能提交SAR和货币交易报告（CTR），并与监管机构沟通确保准确及时提交。

[v7u_N002468|2468] The compliance testing function conducts periodic QA of AFC controls and reviews testing to assess their effectiveness. This function identifies compliance gaps and recommends corrective actions.
ZH: 合规测试职能对金融犯罪防控控制进行定期质量保证（QA）审查，识别合规差距并建议纠正措施。

[v7u_N002469|2469] The MLRO/BSA officer oversees the AML program, reports suspicious activities to authorities, and ensures AML regulations compliance. This role coordinates with various functions to maintain organizational compliance.
ZH: 洗钱报告官（MLRO）/《银行保密法》（《银行保密法》）官员监督反洗钱（反洗钱）计划，报告可疑活动并确保合规。

[v7u_N002470|2470] Global organizations have a subsidiary management function that ensures subsidiaries comply with parent company policies and jurisdiction-specific regulations. This function provides support, guidance, and audits to assess AFC programs in subsidiaries.
ZH: 全球性组织的子公司管理职能确保子公司遵守母公司政策和当地法规，提供支持、指导和审计。

[v7u_N002471|2471] Each of these functions plays a critical role in ensuring that the second line of defense AFC structure proactively identifies, assesses, and mitigates financial crime risks. By collaborating, they maintain a strong compliance framework that meets regulatory requirements and protects the integrity of the financial system.
ZH: 第二道防线金融犯罪防控职能通过协作主动识别、评估和缓释金融犯罪风险，维护合规框架。
```

allowed_unit_ids:

```json
[
  "v7u_N002460",
  "v7u_N002461",
  "v7u_N002462",
  "v7u_N002463",
  "v7u_N002464",
  "v7u_N002465",
  "v7u_N002466",
  "v7u_N002467",
  "v7u_N002468",
  "v7u_N002469",
  "v7u_N002470",
  "v7u_N002471"
]
```

## S2 Process IR

```json
{
  "section_id": "CH34-S06",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "调查职能如何对可疑活动进行调查并生成可疑活动报告？",
      "title": "调查职能对可疑活动的调查与报告流程",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Suspicious activities identified by transaction monitoring or reported by employees",
          "evidence_unit_ids": [
            "v7u_N002465"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "The investigation function conducts in-depth investigations, gathers evidence, and analyzes information",
          "evidence_unit_ids": [
            "v7u_N002465"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "Prepares SARs plus internal and external reports",
          "evidence_unit_ids": [
            "v7u_N002465"
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
            "v7u_N002465"
          ],
          "source_quote": "The investigation function conducts in-depth investigations of suspicious activities identified by transaction monitoring or reported by employees."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002465"
          ],
          "source_quote": "This function gathers evidence, analyzes information, and prepares SARs plus internal and external reports."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_gap_ch34_s06_data_analytics"
      ],
      "focal_question": "数据分析职能如何识别风险模式并标记可疑交易？",
      "title": "数据分析职能识别风险模式与标记可疑交易的流程",
      "card_nature": "risk_indicator",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "Identifies financial crime risk patterns and trends",
          "evidence_unit_ids": [
            "v7u_N002463"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Develops analytical models to detect anomalies and flag fraudulent or suspicious transactions",
          "evidence_unit_ids": [
            "v7u_N002463"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "Detected anomalies and flagged fraudulent or suspicious transactions",
          "evidence_unit_ids": [
            "v7u_N002463"
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
            "v7u_N002463"
          ],
          "source_quote": "This function identifies financial crime risk patterns and trends. They develop analytical models to detect anomalies and flag fraudulent or suspicious transactions."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002463"
          ],
          "source_quote": "develop analytical models to detect anomalies and flag fraudulent or suspicious transactions"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_gap_ch34_s06_model_risk_mgmt"
      ],
      "focal_question": "模型风险管理职能如何监督和评估AFC模型以确保准确性和合规性？",
      "title": "模型风险管理职能的监督与评估流程",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "The model risk management function oversees the validation and governance of AFC models, including transaction monitoring systems, and evaluates their effectiveness",
          "evidence_unit_ids": [
            "v7u_N002464"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "Ensure accuracy and compliance with regulatory standards",
          "evidence_unit_ids": [
            "v7u_N002464"
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
            "v7u_N002464"
          ],
          "source_quote": "Such systems evaluate the effectiveness of these models to ensure accuracy and compliance with regulatory standards."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_gap_ch34_s06_policies_mgmt"
      ],
      "focal_question": "政策管理职能如何通过制定和更新政策与程序来确保合规？",
      "title": "政策管理职能的政策制定与实施流程",
      "card_nature": "control",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "Develops, maintains, and updates AFC policies and procedures, and collaborates with other departments to implement policies, manage document control, and change management",
          "evidence_unit_ids": [
            "v7u_N002466"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "Ensure compliance with evolving regulations",
          "evidence_unit_ids": [
            "v7u_N002466"
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
            "v7u_N002466"
          ],
          "source_quote": "develops, maintains, and updates AFC policies and procedures to ensure compliance with evolving regulations. This function collaborates with other departments to implement policies, manage document control, and change management."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_gap_ch34_s06_reg_reporting"
      ],
      "focal_question": "监管报告与联络职能如何提交监管报告并确保准确及时？",
      "title": "监管报告与联络职能的报告提交与联络流程",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "The regulatory reporting and liaison function files the required regulatory reports, such as SARs and CTR, and liaises with regulatory authorities",
          "evidence_unit_ids": [
            "v7u_N002467"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "Ensure accurate, timely submissions and act as a point of contact for regulatory audits and inquiries",
          "evidence_unit_ids": [
            "v7u_N002467"
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
            "v7u_N002467"
          ],
          "source_quote": "This function liaises with regulatory authorities to ensure accurate, timely submissions and acts as a point of contact for regulatory audits and inquiries."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_gap_ch34_s06_compliance_testing"
      ],
      "focal_question": "合规测试职能如何进行QA审查并建议纠正措施？",
      "title": "合规测试职能的QA审查与纠正建议流程",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "Conducts periodic QA of AFC controls and reviews testing to assess their effectiveness, and identifies compliance gaps",
          "evidence_unit_ids": [
            "v7u_N002468"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "Recommends corrective actions",
          "evidence_unit_ids": [
            "v7u_N002468"
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
            "v7u_N002468"
          ],
          "source_quote": "This function identifies compliance gaps and recommends corrective actions."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_gap_ch34_s06_mlro_bsa"
      ],
      "focal_question": "MLRO/BSA官员如何监督反洗钱计划并维持组织合规？",
      "title": "MLRO/BSA官员的监督与合规管理流程",
      "card_nature": "control",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "The MLRO/BSA officer oversees the AML program, reports suspicious activities to authorities, ensures AML regulations compliance, and coordinates with various functions",
          "evidence_unit_ids": [
            "v7u_N002469"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "Maintain organizational compliance",
          "evidence_unit_ids": [
            "v7u_N002469"
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
            "v7u_N002469"
          ],
          "source_quote": "This role coordinates with various functions to maintain organizational compliance."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_008",
      "source_candidate_ids": [
        "s1c_gap_ch34_s06_subsidiary_mgmt"
      ],
      "focal_question": "子公司管理职能如何确保子公司合规并评估其AFC计划？",
      "title": "子公司管理职能的合规确保与审计评估流程",
      "card_nature": "control",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "Ensures subsidiaries comply with parent company policies and jurisdiction-specific regulations, and provides support, guidance, and audits",
          "evidence_unit_ids": [
            "v7u_N002470"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "Assess AFC programs in subsidiaries",
          "evidence_unit_ids": [
            "v7u_N002470"
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
            "v7u_N002470"
          ],
          "source_quote": "This function provides support, guidance, and audits to assess AFC programs in subsidiaries."
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
      "reason": "该候选描述调查职能对可疑活动的完整处理流程（调查、证据收集、分析、报告），构成独立的程序性episode。"
    },
    {
      "candidate_id": "s1c_gap_ch34_s06_data_analytics",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述数据分析职能识别风险模式、开发模型并标记可疑交易的流程，构成独立的程序性episode。"
    },
    {
      "candidate_id": "s1c_gap_ch34_s06_model_risk_mgmt",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述模型风险管理职能监督验证、评估有效性以确保准确性与合规性的流程，构成独立的程序性episode。"
    },
    {
      "candidate_id": "s1c_gap_ch34_s06_policies_mgmt",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选描述政策管理职能制定、更新、实施政策以确保合规的流程，构成独立的程序性episode。"
    },
    {
      "candidate_id": "s1c_gap_ch34_s06_reg_reporting",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选描述监管报告与联络职能提交报告、联络以确保准确及时提交的流程，构成独立的程序性episode。"
    },
    {
      "candidate_id": "s1c_gap_ch34_s06_compliance_testing",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "该候选描述合规测试职能进行QA审查、识别差距并建议纠正措施的流程，构成独立的程序性episode。"
    },
    {
      "candidate_id": "s1c_gap_ch34_s06_mlro_bsa",
      "disposition": "mapped",
      "episode_ids": [
        "ep_007"
      ],
      "reason": "该候选描述MLRO/BSA官员监督反洗钱计划、报告可疑活动并协调维持合规的流程，构成独立的程序性episode。"
    },
    {
      "candidate_id": "s1c_gap_ch34_s06_subsidiary_mgmt",
      "disposition": "mapped",
      "episode_ids": [
        "ep_008"
      ],
      "reason": "该候选描述子公司管理职能确保合规、提供审计以评估AFC计划的流程，构成独立的程序性episode。"
    }
  ],
  "skip_reason": null
}
```
