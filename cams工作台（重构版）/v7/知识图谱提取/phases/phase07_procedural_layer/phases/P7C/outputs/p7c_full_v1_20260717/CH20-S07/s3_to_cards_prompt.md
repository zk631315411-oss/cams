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

section_id: `CH20-S07`

section_title: `AFC guidance from leading international organizations > Wolfsberg Group AFC guidance`

section_text_with_unit_anchors:

```text
[v7u_N001563|1563] The Wolfsberg Group is an association of global banks that develop policies and guidance for managing financial crime risk.
ZH: 沃尔夫斯堡集团是由全球银行组成的协会，制定金融犯罪风险管理政策与指引

[v7u_N001564|1564] The group first came together in 2000 at the Château Wolfsberg in Switzerland, as part of a collaborative effort with representatives of Transparency International.
ZH: 沃尔夫斯堡集团于2000年在瑞士沃尔夫斯堡城堡成立，与透明国际合作

[v7u_N001565|1565] The group is made up of senior financial crime compliance personnel from member banks, representing the US, the UK, Switzerland, Germany, France, the Netherlands, Italy, Spain, and Japan.
ZH: 沃尔夫斯堡集团成员来自美国、英国、瑞士等九国的资深金融犯罪合规人员

[v7u_N001566|1566] The Wolfsberg Group issues guidelines to assist members in managing their risks, helping them make sound decisions about clients to protect their operations from criminal abuse.
ZH: 沃尔夫斯堡集团发布指引协助成员管理风险，保护业务免受犯罪滥用

[v7u_N001567|1567] Note that the group has no enforcement powers; therefore, its publications are designed to be adapted to its members’ needs and serve as guidance notes for financial institutions depending on their organizational risk, regulatory standards, and business profile.
ZH: 沃尔夫斯堡集团无执法权，其出版物为金融机构提供可调整的指引

[v7u_N001568|1568] The Wolfsberg Group routinely revises these principles to outline best practices for financial institutions to detect and mitigate risks associated with high-net-worth clients, PEPs, and offshore entities.
ZH: 沃尔夫斯堡集团定期修订原则，为高净值客户、政治敏感人物和离岸实体风险提供最佳实践

[v7u_N001569|1569] Key provisions include:
ZH: 沃尔夫斯堡集团指引的关键条款列表

[v7u_N001570|1570] KYC: Banks should verify client identities and assess their risk profiles.
ZH: 了解你的客户要求银行核实客户身份并评估风险状况

[v7u_N001571|1571] Due diligence: Banks should apply enhanced scrutiny for high-risk customers, particularly PEPs.
ZH: 对高风险客户特别是政治敏感人物应加强尽职调查

[v7u_N001572|1572] Source of wealth and funds: Banks should investigate and document how clients acquired their wealth.
ZH: 银行应调查并记录客户财富来源与资金来源

[v7u_N001573|1573] Ongoing monitoring: Banks should conduct continuous reviews of transactions to detect suspicious activities.
ZH: 银行应持续监控交易以发现可疑活动

[v7u_N001574|1574] It emphasizes that financial institutions should allocate resources based on the level of risk posed by a customer, transaction, or jurisdiction.
ZH: 金融机构应根据客户、交易或司法管辖区的风险水平分配资源

[v7u_N001575|1575] In 2014, the Wolfsberg Group published . Since its publication, the Wolfsberg Group has updated the principles that establish best practices for financial institutions engaging in cross-border banking relationships. The best practices include:
ZH: 沃尔夫斯堡集团2014年发布并更新跨境银行关系最佳实践原则

[v7u_N001576|1576] Considering 11 specific risk indicators when conducting due diligence. This includes assessing the risk of correspondent relationships, considering factors like jurisdiction, ownership structure, and regulatory compliance.
ZH: 尽职调查中考虑11项具体风险指标，包括司法管辖区、所有权结构和监管合规

[v7u_N001577|1577] Applying stricter scrutiny to high-risk relationships, such as those involving shell banks or offshore financial centers.
ZH: 对涉及空壳银行或离岸金融中心的高风险关系实施更严格审查
```

allowed_unit_ids:

```json
[
  "v7u_N001563",
  "v7u_N001564",
  "v7u_N001565",
  "v7u_N001566",
  "v7u_N001567",
  "v7u_N001568",
  "v7u_N001569",
  "v7u_N001570",
  "v7u_N001571",
  "v7u_N001572",
  "v7u_N001573",
  "v7u_N001574",
  "v7u_N001575",
  "v7u_N001576",
  "v7u_N001577"
]
```

## S2 Process IR

```json
{
  "section_id": "CH20-S07",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "银行如何在KYC中核实客户身份并评估风险？",
      "title": "KYC中核实客户身份并评估风险状况",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "KYC",
          "evidence_unit_ids": [
            "v7u_N001570"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Banks should verify client identities and assess their risk profiles.",
          "evidence_unit_ids": [
            "v7u_N001570"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001570"
          ],
          "source_quote": "KYC: Banks should verify client identities and assess their risk profiles."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "在尽职调查中如何对高风险客户实施加强审查？",
      "title": "对高风险客户加强尽职调查",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Due diligence",
          "evidence_unit_ids": [
            "v7u_N001571"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "high-risk customers, particularly PEPs",
          "evidence_unit_ids": [
            "v7u_N001571"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "Banks should apply enhanced scrutiny",
          "evidence_unit_ids": [
            "v7u_N001571"
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
          "process_element_id": "e003",
          "condition": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001571"
          ],
          "source_quote": "Due diligence: Banks should apply enhanced scrutiny for high-risk customers, particularly PEPs."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001571"
          ],
          "source_quote": "for high-risk customers, particularly PEPs"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "银行如何调查和记录客户财富来源？",
      "title": "调查和记录客户财富来源",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Source of wealth and funds",
          "evidence_unit_ids": [
            "v7u_N001572"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Banks should investigate and document how clients acquired their wealth.",
          "evidence_unit_ids": [
            "v7u_N001572"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001572"
          ],
          "source_quote": "Source of wealth and funds: Banks should investigate and document how clients acquired their wealth."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "银行如何通过持续监控交易发现可疑活动？",
      "title": "持续监控交易以发现可疑活动",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Ongoing monitoring",
          "evidence_unit_ids": [
            "v7u_N001573"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Banks should conduct continuous reviews of transactions.",
          "evidence_unit_ids": [
            "v7u_N001573"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "detect suspicious activities",
          "evidence_unit_ids": [
            "v7u_N001573"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001573"
          ],
          "source_quote": "Ongoing monitoring: Banks should conduct continuous reviews of transactions to detect suspicious activities."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001573"
          ],
          "source_quote": "to detect suspicious activities"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "金融机构如何根据风险水平分配资源？",
      "title": "根据风险水平分配资源",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "level of risk posed by a customer, transaction, or jurisdiction",
          "evidence_unit_ids": [
            "v7u_N001574"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "financial institutions should allocate resources",
          "evidence_unit_ids": [
            "v7u_N001574"
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
            "v7u_N001574"
          ],
          "source_quote": "financial institutions should allocate resources based on the level of risk posed by a customer, transaction, or jurisdiction."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "在跨境银行关系尽职调查中应考虑哪些风险指标？",
      "title": "在尽职调查中考虑11项风险指标",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "conducting due diligence",
          "evidence_unit_ids": [
            "v7u_N001576"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Considering 11 specific risk indicators, including assessing the risk of correspondent relationships, considering jurisdiction, ownership structure, and regulatory compliance.",
          "evidence_unit_ids": [
            "v7u_N001576"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001576"
          ],
          "source_quote": "Considering 11 specific risk indicators when conducting due diligence."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_007"
      ],
      "focal_question": "如何对高风险跨境关系实施更严格审查？",
      "title": "对高风险关系适用更严格审查",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "high-risk relationships, such as those involving shell banks or offshore financial centers",
          "evidence_unit_ids": [
            "v7u_N001577"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Applying stricter scrutiny",
          "evidence_unit_ids": [
            "v7u_N001577"
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
            "v7u_N001577"
          ],
          "source_quote": "Applying stricter scrutiny to high-risk relationships, such as those involving shell banks or offshore financial centers."
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
      "reason": "该候选描述了银行在KYC中应执行的身份核实和风险评估动作，构成独立流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "描述了尽职调查中针对高风险客户的加强审查动作，构成带条件的流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "描述了调查和记录客户财富来源的动作。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "描述了持续监控交易以发现可疑活动的动作与目的。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "描述了根据风险水平分配资源的动作，构成标准约束流程。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "描述了在尽职调查中考虑风险指标的程序动作。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "mapped",
      "episode_ids": [
        "ep_007"
      ],
      "reason": "描述了对高风险关系适用更严格审查的动作。"
    }
  ],
  "skip_reason": null
}
```
