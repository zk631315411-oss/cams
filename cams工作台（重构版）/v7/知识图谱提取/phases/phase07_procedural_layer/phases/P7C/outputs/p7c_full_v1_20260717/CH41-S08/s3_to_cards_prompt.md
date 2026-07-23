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

section_id: `CH41-S08`

section_title: `Governance and oversight > • United Kingdom:`

section_text_with_unit_anchors:

```text
[v7u_N002978|2978] REP-CRIM report: Describes criminal activities detected within the financial institution.
ZH: REP-CRIM报告描述金融机构内检测到的犯罪活动。

[v7u_N002979|2979] Annual MLRO’s report: Summarizes the organization’s AFC compliance activities, highlighting trends, risks, and mitigation measures.
ZH: 年度MLRO报告总结组织的金融犯罪防控合规活动，突出趋势、风险和缓解措施。

[v7u_N002980|2980] Regulatory reporting requirements include, but are not limited to:
ZH: 监管报告要求的列表引导。

[v7u_N002981|2981] Accuracy and completeness: Reports must contain detailed, verifiable data to prevent errors, regulatory scrutiny, and reporting breaches.
ZH: 可疑活动报告必须包含详细、可验证的数据，以防止错误、监管审查和报告违规。

[v7u_N002982|2982] Timeliness: Filing deadlines differ globally, and institutions must ensure swift and precise submission.
ZH: 全球提交截止日期不同，机构必须确保及时、准确地提交报告。

[v7u_N002983|2983] Confidentiality and anti-tipping off: Disclosure of SAR details is strictly prohibited to prevent interference with law enforcement investigations.
ZH: 严格禁止泄露可疑活动报告细节，以防止干扰执法调查。

[v7u_N002984|2984] By aligning regulatory reporting processes with jurisdictional requirements, institutions strengthen financial integrity, regulatory cooperation, and financial crime prevention efforts.
ZH: 使监管报告流程符合司法管辖区要求，可增强金融诚信、监管合作和金融犯罪预防。

[v7u_N002985|2985] Responding to regulator requests is a crucial element of an organization’s AFC compliance program, underscoring the need for transparency, collaboration, and accountability. Effective engagement with regulators helps to avoid penalties, while demonstrating a culture of compliance that fosters long-term trust and credibility. It is also a key part of the cooperative effort between regulators and industry to combat money laundering, terrorism financing, and other financial crimes.
ZH: 回应监管机构请求是金融犯罪防控合规计划的关键要素，有助于避免处罚并建立信任。

[v7u_N002986|2986] Regulators may conduct routine examinations or targeted investigations, assessing whether institutions adhere to local and global AFC mandates.
ZH: 监管机构可能进行常规检查或专项调查，评估机构是否遵守当地和全球金融犯罪防控规定。

[v7u_N002987|2987] In some cases, a monitorship may be imposed following serious compliance breaches, requiring the institution to correct shortcomings under strict regulatory supervision.
ZH: 严重合规违规后可能实施监管监督，要求机构在严格监管下纠正缺陷。

[v7u_N002988|2988] By cooperating fully and addressing identified gaps promptly, organizations reduce reputational and operational risks.
ZH: 机构应充分合作并及时解决已发现的差距，以降低声誉和运营风险。

[v7u_N002989|2989] Jurisdictions often grant regulators special provisions to obtain relevant records and information. For example, in the UK, Section 166 of the Financial Services and Markets Act 2000 allows regulators to demand data on customer files, transactions, or risk management processes.
ZH: 英国《2000年金融服务与市场法》第166条允许监管机构要求提供客户档案、交易或风险管理流程数据。

[v7u_N002990|2990] Organizations must maintain accurate records and structured governance to quickly comply with such requests and demonstrate robust AFC controls.
ZH: 机构必须维护准确记录和结构化治理，以快速响应监管请求并展示有效的金融犯罪防控控制。

[v7u_N002991|2991] Best practices for engaging with regulators include the following:
ZH: 与监管机构互动的最佳实践包括以下内容。

[v7u_N002992|2992] Preparedness and data integrity: Keep customer due diligence files, transaction logs, and audit trails up to date, facilitating timely and accurate submissions.
ZH: 保持客户尽职调查文件、交易日志和审计线索最新，以便及时准确提交。

[v7u_N002993|2993] Designated liaison: Centralize regulator interactions under a head of compliance or similar role, ensuring efficient and consistent communication.
ZH: 指定合规负责人等角色集中处理监管互动，确保沟通高效一致。

[v7u_N002994|2994] Timely and transparent responses: Provide complete information before deadlines, proactively disclosing potential delays or challenges to build regulatory trust.
ZH: 在截止日期前提供完整信息，主动披露潜在延迟或挑战，以建立监管信任。

[v7u_N002995|2995] Remediation and monitoring: Develop corrective action plans, report progress, and strengthen AFC frameworks to prevent repeat findings.
ZH: 制定纠正行动计划、报告进展并加强金融犯罪防控框架，防止问题再次发生。

[v7u_N002996|2996] By responding promptly to regulator requests, organizations reinforce AFC commitments, mitigate compliance risks, and maintain strong supervisory relationships that bolster financial integrity.
ZH: 及时回应监管请求可强化金融犯罪防控承诺，降低合规风险并维护良好的监管关系。
```

allowed_unit_ids:

```json
[
  "v7u_N002978",
  "v7u_N002979",
  "v7u_N002980",
  "v7u_N002981",
  "v7u_N002982",
  "v7u_N002983",
  "v7u_N002984",
  "v7u_N002985",
  "v7u_N002986",
  "v7u_N002987",
  "v7u_N002988",
  "v7u_N002989",
  "v7u_N002990",
  "v7u_N002991",
  "v7u_N002992",
  "v7u_N002993",
  "v7u_N002994",
  "v7u_N002995",
  "v7u_N002996"
]
```

## S2 Process IR

```json
{
  "section_id": "CH41-S08",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "监管机构如何通过检查评估机构是否遵守AFC规定？",
      "title": "监管检查与合规评估",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "监管机构进行常规检查或专项调查",
          "evidence_unit_ids": [
            "v7u_N002986"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "评估机构是否遵守当地和全球金融犯罪防控规定",
          "evidence_unit_ids": [
            "v7u_N002986"
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
            "v7u_N002986"
          ],
          "source_quote": "Regulators may conduct routine examinations or targeted investigations, assessing whether institutions adhere to local and global AFC mandates."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "严重合规违规后，监管监视如何要求机构纠正缺陷？",
      "title": "严重违规后的监管监视与纠正要求",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "发生严重合规违规",
          "evidence_unit_ids": [
            "v7u_N002987"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "可能实施监管监督(monitorship)",
          "evidence_unit_ids": [
            "v7u_N002987"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "机构在严格监管下纠正缺陷",
          "evidence_unit_ids": [
            "v7u_N002987"
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
            "v7u_N002987"
          ],
          "source_quote": "In some cases, a monitorship may be imposed following serious compliance breaches, requiring the institution to correct shortcomings under strict regulatory supervision."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002987"
          ],
          "source_quote": "In some cases, a monitorship may be imposed following serious compliance breaches, requiring the institution to correct shortcomings under strict regulatory supervision."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "机构如何通过合作与解决差距降低风险？",
      "title": "通过合作与补救降低声誉和运营风险",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "机构充分合作并及时解决已发现的差距",
          "evidence_unit_ids": [
            "v7u_N002988"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "降低声誉和运营风险",
          "evidence_unit_ids": [
            "v7u_N002988"
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
            "v7u_N002988"
          ],
          "source_quote": "By cooperating fully and addressing identified gaps promptly, organizations reduce reputational and operational risks."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "机构为何必须维护准确记录与结构化治理？",
      "title": "维护记录与治理以快速响应监管请求",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "维护准确记录和结构化治理",
          "evidence_unit_ids": [
            "v7u_N002990"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "快速遵从监管请求并展示有效的金融犯罪防控控制",
          "evidence_unit_ids": [
            "v7u_N002990"
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
            "v7u_N002990"
          ],
          "source_quote": "Organizations must maintain accurate records and structured governance to quickly comply with such requests and demonstrate robust AFC controls."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_gap_ch41_s08_align_processes"
      ],
      "focal_question": "对齐报告流程与管辖要求能带来什么效果？",
      "title": "对齐报告流程以增强金融诚信与预防犯罪",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "使监管报告流程符合司法管辖区要求",
          "evidence_unit_ids": [
            "v7u_N002984"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "增强金融诚信、监管合作和金融犯罪预防",
          "evidence_unit_ids": [
            "v7u_N002984"
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
            "v7u_N002984"
          ],
          "source_quote": "By aligning regulatory reporting processes with jurisdictional requirements, institutions strengthen financial integrity, regulatory cooperation, and financial crime prevention efforts."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_gap_ch41_s08_data_integrity"
      ],
      "focal_question": "保持数据完整性有何目的？",
      "title": "保持数据最新以便于监管提交",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "保持客户尽职调查文件、交易日志和审计线索最新",
          "evidence_unit_ids": [
            "v7u_N002992"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "便于及时、准确地提交",
          "evidence_unit_ids": [
            "v7u_N002992"
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
            "v7u_N002992"
          ],
          "source_quote": "Keep customer due diligence files, transaction logs, and audit trails up to date, facilitating timely and accurate submissions."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_gap_ch41_s08_designated_liaison"
      ],
      "focal_question": "指定联络人如何确保高效沟通？",
      "title": "集中监管互动以确保沟通高效一致",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "将监管互动集中到合规负责人或类似角色",
          "evidence_unit_ids": [
            "v7u_N002993"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "确保沟通高效、一致",
          "evidence_unit_ids": [
            "v7u_N002993"
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
            "v7u_N002993"
          ],
          "source_quote": "Centralize regulator interactions under a head of compliance or similar role, ensuring efficient and consistent communication."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_008",
      "source_candidate_ids": [
        "s1c_gap_ch41_s08_timely_responses"
      ],
      "focal_question": "如何通过及时透明回应建立监管信任？",
      "title": "及时透明回应以建立监管信任",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "在截止日期前提供完整信息，并主动披露潜在延迟或挑战",
          "evidence_unit_ids": [
            "v7u_N002994"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "建立监管信任",
          "evidence_unit_ids": [
            "v7u_N002994"
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
            "v7u_N002994"
          ],
          "source_quote": "Provide complete information before deadlines, proactively disclosing potential delays or challenges to build regulatory trust."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_009",
      "source_candidate_ids": [
        "s1c_gap_ch41_s08_remediation"
      ],
      "focal_question": "补救和监控措施如何防止问题再发生？",
      "title": "制定补救计划以预防重复发现",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "制定纠正行动计划，报告进展并加强金融犯罪防控框架",
          "evidence_unit_ids": [
            "v7u_N002995"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "防止问题再次发生",
          "evidence_unit_ids": [
            "v7u_N002995"
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
            "v7u_N002995"
          ],
          "source_quote": "Develop corrective action plans, report progress, and strengthen AFC frameworks to prevent repeat findings."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_010",
      "source_candidate_ids": [
        "s1c_gap_ch41_s08_prompt_response_benefits"
      ],
      "focal_question": "及时回应监管请求能带来哪些好处？",
      "title": "及时回应以强化承诺、降低风险和维护关系",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "及时回应监管请求",
          "evidence_unit_ids": [
            "v7u_N002996"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "强化金融犯罪防控承诺，降低合规风险，维护良好的监管关系并增强金融诚信",
          "evidence_unit_ids": [
            "v7u_N002996"
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
            "v7u_N002996"
          ],
          "source_quote": "By responding promptly to regulator requests, organizations reinforce AFC commitments, mitigate compliance risks, and maintain strong supervisory relationships that bolster financial integrity."
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
      "reason": "该候选描述了监管机构进行检查并评估机构合规性的过程，构成独立的判断流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了严重违规触发监管监视及纠正要求，构成程序性流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述了机构通过合作和解决差距来降低风险的动作与结果关系，构成流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选仅为法律授权条款，无动态业务过程或判断迁移，属于静态法律知识。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选明确了维护记录和治理的义务及其目的，构成从动作到结果的规定流程。"
    },
    {
      "candidate_id": "s1c_gap_ch41_s08_report_accuracy",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选为报告数据的静态准确性要求，缺乏具体处理动作或判断迁移。"
    },
    {
      "candidate_id": "s1c_gap_ch41_s08_report_timeliness",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选为提交报告的静态及时性要求，无程序性过程。"
    },
    {
      "candidate_id": "s1c_gap_ch41_s08_report_confidentiality",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选为禁止性保密规定，不属于业务判断或处理流程。"
    },
    {
      "candidate_id": "s1c_gap_ch41_s08_align_processes",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选描述了通过对齐报告流程以增强各项能力的动作-结果关系，构成流程。"
    },
    {
      "candidate_id": "s1c_gap_ch41_s08_data_integrity",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "该候选描述了保持数据最新以便于提交的动作与目的，构成流程。"
    },
    {
      "candidate_id": "s1c_gap_ch41_s08_designated_liaison",
      "disposition": "mapped",
      "episode_ids": [
        "ep_007"
      ],
      "reason": "该候选描述了集中监管互动以确保高效沟通的动作与目的，构成流程。"
    },
    {
      "candidate_id": "s1c_gap_ch41_s08_timely_responses",
      "disposition": "mapped",
      "episode_ids": [
        "ep_008"
      ],
      "reason": "该候选描述了及时提供完整信息以建立信任的动作与目的，构成流程。"
    },
    {
      "candidate_id": "s1c_gap_ch41_s08_remediation",
      "disposition": "mapped",
      "episode_ids": [
        "ep_009"
      ],
      "reason": "该候选描述了制定补救计划等以防止重复发生的动作与目的，构成流程。"
    },
    {
      "candidate_id": "s1c_gap_ch41_s08_prompt_response_benefits",
      "disposition": "mapped",
      "episode_ids": [
        "ep_010"
      ],
      "reason": "该候选描述了及时回应监管请求以带来多方面好处的动作与结果关系，构成流程。"
    }
  ],
  "skip_reason": null
}
```
