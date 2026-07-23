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

section_id: `CH32-S05`

section_title: `Cooperation involving the private sector > Private sector information sharing`

section_text_with_unit_anchors:

```text
[v7u_N002343|2343] Private sector information sharing provides organizations with information they would not otherwise have, creating opportunities to identify and mitigate risk.
ZH: 私营部门信息共享可提供机构原本无法获取的信息，有助于识别和缓释风险

[v7u_N002344|2344] For example, if Bank A suspects money laundering from a customer, it might offboard them.
ZH: 例如，若A银行怀疑某客户洗钱，可能终止其账户

[v7u_N002345|2345] However, that customer can then easily open an account with Bank B and continue laundering money. Information sharing prevents this and other typologies, leading to better prevention and detection of money laundering and terrorist financing.
ZH: 信息共享可防止客户转向其他机构继续洗钱，提升洗钱和恐怖融资的预防与检测能力

[v7u_N002346|2346] There are various methods of sharing information in the private sector, often developed via public-private partnerships.
ZH: 私营部门有多种信息共享方式，通常通过公私伙伴关系发展而来

[v7u_N002347|2347] USA PATRIOT Act Section 314b is one of the oldest examples.
ZH: 美国《爱国者法案》第314b条是最早的私营部门信息共享示例之一

[v7u_N002348|2348] 314b allows financial institutions to share customer or transactional information with each other to assist with AML/CFT compliance.
ZH: 第314b条允许金融机构相互共享客户或交易信息以协助反洗钱/反恐怖融资合规

[v7u_N002349|2349] It provides participating organizations with a safe harbor from legal liability.
ZH: 第314b条为参与机构提供安全港，免除法律责任

[v7u_N002350|2350] US organizations widely use 314b to identify money laundering and terrorist financing and help decide whether to maintain an account.
ZH: 美国机构广泛使用第314b条识别洗钱和恐怖融资，并协助决定是否保留账户

[v7u_N002351|2351] In the UK, the Economic Crime and Corporate Transparency Act 2023 provides the legal means for two regulated organizations to share information with each other. Like Section 314b in the US, the act exempts such disclosures from civil liability and confidentiality obligations.
ZH: 英国《2023年经济犯罪与公司透明度法案》允许两家受监管机构共享信息，并豁免民事责任和保密义务

[v7u_N002352|2352] Other examples of private-to-private sector sharing exist globally. For example, in Singapore, COSMIC is a digitally secure platform that allows financial institutions to share information. When a customer exhibits “red flags” indicating potential financial crime concerns, financial institutions can share information if certain thresholds are met.
ZH: 新加坡COSMIC平台允许金融机构在客户出现红旗信号信号时共享信息

[v7u_N002353|2353] In the EU, Article 75 of Regulation (EU) 2024/1624 allows organizations to take part in cross-border information sharing partnerships, if their national supervisor approves it. Organizations may share information about customer identity, business relationships, transactions, and customer risk factors.
ZH: 欧盟(EU)2024/1624号法规第75条允许经国家监管机构批准的跨境信息共享伙伴关系

[v7u_N002354|2354] Organizations looking to join private-to-private sector information sharing arrangements should carefully consider their obligations under local data protection legislation and customer confidentiality requirements within their organization.
ZH: 加入私营部门信息共享安排前须考虑当地数据保护法和客户保密义务

[v7u_N002355|2355] National supervisor approval under Article 75 requires the partnership to carry out a data protection impact assessment before processing personal information.
ZH: 第75条要求伙伴关系在处理个人信息前进行数据保护影响评估

[v7u_N002356|2356] If proceeding, organizations should assign appropriate resources and develop policies and procedures to govern the activity.
ZH: 机构应分配适当资源并制定政策和程序来管理信息共享活动

[v7u_N002357|2357] The potential benefits are significant. Appropriate private-to-private information sharing can considerably enhance an AML/CFT program.
ZH: 适当的私营部门信息共享可显著增强反洗钱/反恐怖融资计划
```

allowed_unit_ids:

```json
[
  "v7u_N002343",
  "v7u_N002344",
  "v7u_N002345",
  "v7u_N002346",
  "v7u_N002347",
  "v7u_N002348",
  "v7u_N002349",
  "v7u_N002350",
  "v7u_N002351",
  "v7u_N002352",
  "v7u_N002353",
  "v7u_N002354",
  "v7u_N002355",
  "v7u_N002356",
  "v7u_N002357"
]
```

## S2 Process IR

```json
{
  "section_id": "CH32-S05",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001",
        "s1c_gap_ch32_s05_314b_usage"
      ],
      "focal_question": "How to utilize US PATRIOT Act Section 314b to share information and assist AML/CFT compliance?",
      "title": "Utilizing Section 314b for AML/CFT Compliance",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "USA PATRIOT Act Section 314b (allows sharing and provides safe harbor)",
          "evidence_unit_ids": [
            "v7u_N002348",
            "v7u_N002349"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "share customer or transactional information with other financial institutions",
          "evidence_unit_ids": [
            "v7u_N002348",
            "v7u_N002350"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "identify money laundering and terrorist financing",
          "evidence_unit_ids": [
            "v7u_N002350"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "help decide whether to maintain an account",
          "evidence_unit_ids": [
            "v7u_N002350"
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
            "v7u_N002348"
          ],
          "source_quote": "314b allows financial institutions to share customer or transactional information with each other to assist with AML/CFT compliance."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002350"
          ],
          "source_quote": "US organizations widely use 314b to identify money laundering and terrorist financing"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": "helps_achieve",
          "evidence_unit_ids": [
            "v7u_N002350"
          ],
          "source_quote": "help decide whether to maintain an account"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "How does the UK Economic Crime and Corporate Transparency Act 2023 enable information sharing?",
      "title": "Information Sharing under UK ECCTA 2023",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "UK Economic Crime and Corporate Transparency Act 2023 (provides legal means for sharing and exempts from civil liability and confidentiality)",
          "evidence_unit_ids": [
            "v7u_N002351"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "share information with other regulated organizations",
          "evidence_unit_ids": [
            "v7u_N002351"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "exempt from civil liability and confidentiality obligations",
          "evidence_unit_ids": [
            "v7u_N002351"
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
            "v7u_N002351"
          ],
          "source_quote": "the Economic Crime and Corporate Transparency Act 2023 provides the legal means for two regulated organizations to share information with each other."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002351"
          ],
          "source_quote": "the act exempts such disclosures from civil liability and confidentiality obligations."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "Under what conditions can financial institutions share information via COSMIC in Singapore?",
      "title": "Information Sharing via COSMIC Platform",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Customer exhibits red flags indicating potential financial crime concerns and certain thresholds are met",
          "evidence_unit_ids": [
            "v7u_N002352"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "share information via COSMIC platform",
          "evidence_unit_ids": [
            "v7u_N002352"
          ],
          "modality": "permitted"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": "when a customer exhibits red flags indicating potential financial crime concerns and if certain thresholds are met",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002352"
          ],
          "source_quote": "When a customer exhibits “red flags” indicating potential financial crime concerns, financial institutions can share information if certain thresholds are met."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "What are the requirements and steps for cross-border information sharing under EU Article 75?",
      "title": "Cross-border Information Sharing under EU Article 75",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "Article 75 of Regulation (EU) 2024/1624",
          "evidence_unit_ids": [
            "v7u_N002353",
            "v7u_N002355"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "carry out a data protection impact assessment",
          "evidence_unit_ids": [
            "v7u_N002355"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "national supervisor approval",
          "evidence_unit_ids": [
            "v7u_N002353",
            "v7u_N002355"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "take part in cross-border information sharing partnerships",
          "evidence_unit_ids": [
            "v7u_N002353"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e005",
          "role": "action",
          "label": "share information about customer identity, business relationships, transactions, and customer risk factors",
          "evidence_unit_ids": [
            "v7u_N002353"
          ],
          "modality": "permitted"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e001",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002355"
          ],
          "source_quote": "National supervisor approval under Article 75 requires the partnership to carry out a data protection impact assessment before processing personal information."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002355"
          ],
          "source_quote": "National supervisor approval... requires... a data protection impact assessment before processing"
        },
        {
          "relation_id": "r003",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e003",
          "process_element_id": "e004",
          "condition": "if national supervisor approves",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002353"
          ],
          "source_quote": "Article 75 of Regulation (EU) 2024/1624 allows organizations to take part in cross-border information sharing partnerships, if their national supervisor approves it."
        },
        {
          "relation_id": "r004",
          "kind": "reference",
          "process_element_id": "e004",
          "auxiliary_element_id": "e001",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002353"
          ],
          "source_quote": "Article 75... allows organizations to take part in cross-border information sharing partnerships..."
        },
        {
          "relation_id": "r005",
          "kind": "sequence",
          "before_element_id": "e004",
          "after_element_id": "e005",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002353"
          ],
          "source_quote": "Organizations may share information about customer identity, business relationships, transactions, and customer risk factors."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_005",
        "s1c_006"
      ],
      "focal_question": "What preparatory steps should organizations take when joining private sector information sharing arrangements?",
      "title": "Preparation for Joining Information Sharing Arrangements",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Organization looks to join private-to-private sector information sharing arrangements",
          "evidence_unit_ids": [
            "v7u_N002354"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "should carefully consider obligations under local data protection legislation and customer confidentiality requirements",
          "evidence_unit_ids": [
            "v7u_N002354"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "if proceeding, assign appropriate resources and develop policies and procedures to govern the activity",
          "evidence_unit_ids": [
            "v7u_N002356"
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
            "v7u_N002354"
          ],
          "source_quote": "Organizations looking to join private-to-private sector information sharing arrangements should carefully consider their obligations under local data protection legislation and customer confidentiality requirements within their organization."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002356"
          ],
          "source_quote": "If proceeding, organizations should assign appropriate resources and develop policies and procedures to govern the activity."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_007"
      ],
      "focal_question": "How does a bank decide to offboard a customer suspected of money laundering?",
      "title": "Offboarding Customer upon Money Laundering Suspicion",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Bank A suspects money laundering from a customer",
          "evidence_unit_ids": [
            "v7u_N002344"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "offboard the customer",
          "evidence_unit_ids": [
            "v7u_N002344"
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
          "condition": "if Bank A suspects money laundering from a customer",
          "relation_type": null,
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N002344"
          ],
          "source_quote": "if Bank A suspects money laundering from a customer, it might offboard them."
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
      "reason": "Provides legal basis and safe harbor for sharing, forming the standard for the episode's action."
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "Defines the legal means for sharing and liability exemption, constituting the core process."
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "Describes condition-based sharing via COSMIC platform, with clear trigger and action."
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "Covers Article 75 requirements including DPIA and approval, forming a multi-step process."
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "Specifies the consideration step as a preparatory action when joining sharing arrangements."
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "Specifies resource assignment and policy development step, following consideration if proceeding."
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "Illustrates a conditional offboarding decision based on money laundering suspicion, forming a standalone process."
    },
    {
      "candidate_id": "s1c_gap_ch32_s05_314b_usage",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "Provides the actual usage of 314b to identify ML/TF and assist account decisions, completing the process."
    }
  ],
  "skip_reason": null
}
```
