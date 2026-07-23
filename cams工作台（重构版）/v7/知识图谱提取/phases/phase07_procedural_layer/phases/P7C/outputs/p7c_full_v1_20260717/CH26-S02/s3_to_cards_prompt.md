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

section_id: `CH26-S02`

section_title: `Other laws and regulations that impact organizations > Digital Operational Resilience Act`

section_text_with_unit_anchors:

```text
[v7u_N002028|2028] Digitalization has deepened interconnections and dependencies within the financial sector and with third-party service providers. In this context, information and communications technology (ICT) risk has increased as illicit actors frequently exploit ICT infrastructures to attack financial institutions.
ZH: 数字化加深了金融业与第三方的互联和依赖，增加了ICT风险。

[v7u_N002029|2029] Considering the relevance of digital resilience, the EU passed the Digital Operational Resilience Act (DORA). The goal of this regulation is to strengthen the cybersecurity of EU’s financial services sector.
ZH: 欧盟通过《数字运营韧性法案》（DORA）以加强金融服务业网络安全。

[v7u_N002030|2030] It applies to all financial institutions as of January 2025.
ZH: DORA自2025年1月起适用于所有金融机构。

[v7u_N002031|2031] DORA sets requirements in the following areas:
ZH: DORA在以下领域设定要求（列表引导）。

[v7u_N002032|2032] ICT risk management: Financial institutions should implement a robust control system coordinated by an independent ICT risk control function. This body is responsible for setting the data operational resilience strategy, which includes determining the appropriate risk tolerance level. A management body then approves this tolerance level. These bodies should make the necessary arrangements to ensure continuity of critical AFC functions and include a secondary processing site.
ZH: ICT风险管理：金融机构应建立由独立ICT风险控制职能协调的稳健控制体系。

[v7u_N002033|2033] Incident reporting: Financial institutions should promptly report significant ICT incidents to the designated competent authorities.
ZH: 事件报告：金融机构应及时向指定主管当局报告重大ICT事件。

[v7u_N002034|2034] Resilience testing: Financial institutions should conduct yearly vulnerability assessments, while the designated competent authorities are responsible for conducting threat-led penetration tests every three years.
ZH: 金融机构每年进行漏洞评估，主管当局每三年进行威胁主导的渗透测试。

[v7u_N002035|2035] The financial institution utilizing a third-party service is primarily responsible for remediating vulnerabilities it identifies during end-to-end testing.
ZH: 使用第三方服务的金融机构主要负责修复端到端测试中发现的漏洞。

[v7u_N002036|2036] Third-party risk management: Financial institutions should conduct ex-ante due diligence - meaning a preventative review before taking action - and ongoing monitoring of vendors.
ZH: 金融机构应对供应商进行事前尽职调查和持续监控。

[v7u_N002037|2037] They should prohibit dealing with vendors that have insufficient security standards.
ZH: 应禁止与安全标准不足的供应商交易。

[v7u_N002038|2038] To mitigate concentration risk, financial institutions should establish an exit strategy from vendor services related to critical AFC functions, such as sanction screening and transaction monitoring.
ZH: 为缓解集中风险，金融机构应为关键金融犯罪防控功能的供应商服务制定退出策略。

[v7u_N002039|2039] Additionally, critical ICT third-party service providers are subject to EU-level supervision and obliged to establish a subsidiary in the EU.
ZH: 关键ICT第三方服务提供商受欧盟层面监管，并须在欧盟设立子公司。

[v7u_N002040|2040] Information sharing: Financial institutions can regularly share information regarding threats and vulnerability intelligence to prevent the materialization of incidents. Information sharing enables other financial institutions to effectively contain impacts of financial crimes and recover faster.
ZH: 信息共享：金融机构可定期共享威胁和漏洞情报，以预防事件发生。

[v7u_N002041|2041] By meeting DORA’s enhanced cybersecurity and risk management requirements, financial institutions reduce the risk that criminals and terrorists will exploit digital vulnerabilities to launder money through their accounts.
ZH: 遵守DORA的网络安全和风险管理要求可降低洗钱风险
```

allowed_unit_ids:

```json
[
  "v7u_N002028",
  "v7u_N002029",
  "v7u_N002030",
  "v7u_N002031",
  "v7u_N002032",
  "v7u_N002033",
  "v7u_N002034",
  "v7u_N002035",
  "v7u_N002036",
  "v7u_N002037",
  "v7u_N002038",
  "v7u_N002039",
  "v7u_N002040",
  "v7u_N002041"
]
```

## S2 Process IR

```json
{
  "section_id": "CH26-S02",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "金融机构如何建立ICT风险管理体系并确定风险容忍度？",
      "title": "ICT风险管理体系建立与风险容忍度批准",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "实施由独立ICT风险控制职能协调的稳健控制体系",
          "evidence_unit_ids": [
            "v7u_N002032"
          ],
          "modality": "optional"
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "设定数据运营韧性战略，包括确定风险容忍度",
          "evidence_unit_ids": [
            "v7u_N002032"
          ],
          "modality": "optional"
        },
        {
          "element_id": "e003",
          "role": "decision",
          "label": "管理层批准风险容忍度",
          "evidence_unit_ids": [
            "v7u_N002032"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "做出安排以确保关键AFC功能连续性并包括二级处理站点",
          "evidence_unit_ids": [
            "v7u_N002032"
          ],
          "modality": "optional"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "sequence",
          "before_element_id": "e001",
          "after_element_id": "e002",
          "evidence_unit_ids": [
            "v7u_N002032"
          ],
          "source_quote": "Financial institutions should implement a robust control system coordinated by an independent ICT risk control function. This body is responsible for setting the data operational resilience strategy...",
          "condition": null,
          "trigger_mode": null,
          "relation_type": null,
          "qualifier": null
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "evidence_unit_ids": [
            "v7u_N002032"
          ],
          "source_quote": "...which includes determining the appropriate risk tolerance level. A management body then approves this tolerance level.",
          "condition": null,
          "trigger_mode": null,
          "relation_type": null,
          "qualifier": null
        },
        {
          "relation_id": "r003",
          "kind": "sequence",
          "before_element_id": "e003",
          "after_element_id": "e004",
          "evidence_unit_ids": [
            "v7u_N002032"
          ],
          "source_quote": "These bodies should make the necessary arrangements to ensure continuity of critical AFC functions and include a secondary processing site.",
          "condition": null,
          "trigger_mode": null,
          "relation_type": null,
          "qualifier": null
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "发生重大ICT事件后金融机构应如何响应？",
      "title": "重大ICT事件报告",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "发生重大ICT事件",
          "evidence_unit_ids": [
            "v7u_N002033"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "及时向指定主管当局报告重大ICT事件",
          "evidence_unit_ids": [
            "v7u_N002033"
          ],
          "modality": "optional"
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
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002033"
          ],
          "source_quote": "Financial institutions should promptly report significant ICT incidents to the designated competent authorities."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "金融机构如何进行漏洞评估并修复发现的漏洞？",
      "title": "年度漏洞评估与漏洞修复",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "应每年进行漏洞评估",
          "evidence_unit_ids": [
            "v7u_N002034"
          ],
          "modality": "optional"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "识别出漏洞",
          "evidence_unit_ids": [
            "v7u_N002035"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "修复漏洞",
          "evidence_unit_ids": [
            "v7u_N002035"
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
          "evidence_unit_ids": [
            "v7u_N002034",
            "v7u_N002035"
          ],
          "source_quote": "Financial institutions should conduct yearly vulnerability assessments ... The financial institution ... is primarily responsible for remediating vulnerabilities it identifies during end-to-end testing.",
          "condition": null,
          "trigger_mode": null,
          "relation_type": null,
          "qualifier": null
        },
        {
          "relation_id": "r002",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e002",
          "process_element_id": "e003",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002035"
          ],
          "source_quote": "remediating vulnerabilities it identifies"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "金融机构如何基于尽职调查和监控管理供应商安全风险？",
      "title": "供应商安全尽职调查与禁止交易",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "应进行事前尽职调查和持续监控",
          "evidence_unit_ids": [
            "v7u_N002036"
          ],
          "modality": "optional"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "供应商安全标准评估结果",
          "evidence_unit_ids": [
            "v7u_N002036",
            "v7u_N002037"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "decision",
          "label": "判断供应商安全标准是否不足",
          "evidence_unit_ids": [
            "v7u_N002037"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "应禁止与安全标准不足的供应商交易",
          "evidence_unit_ids": [
            "v7u_N002037"
          ],
          "modality": "optional"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e002",
          "evidence_unit_ids": [
            "v7u_N002036"
          ],
          "source_quote": "Financial institutions should conduct ex-ante due diligence ... and ongoing monitoring of vendors.",
          "condition": null,
          "trigger_mode": null,
          "relation_type": null,
          "qualifier": null
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "evidence_unit_ids": [
            "v7u_N002036",
            "v7u_N002037"
          ],
          "source_quote": "prohibit dealing with vendors that have insufficient security standards",
          "condition": null,
          "trigger_mode": null,
          "relation_type": null,
          "qualifier": null
        },
        {
          "relation_id": "r003",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e003",
          "process_element_id": "e004",
          "condition": "安全标准不足",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002037"
          ],
          "source_quote": "They should prohibit dealing with vendors that have insufficient security standards."
        }
      ],
      "split_reason": "该候选包含的尽职调查与退出策略分别服务于不同的风险管理目标，且相互独立，故拆分为两个episode。"
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "金融机构如何缓解第三方集中风险？",
      "title": "建立退出策略缓解集中风险",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "应为关键AFC功能建立退出策略",
          "evidence_unit_ids": [
            "v7u_N002038"
          ],
          "modality": "optional"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "缓解集中风险",
          "evidence_unit_ids": [
            "v7u_N002038"
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
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002038"
          ],
          "source_quote": "To mitigate concentration risk, financial institutions should establish an exit strategy...",
          "condition": null,
          "trigger_mode": null,
          "relation_type": null
        }
      ],
      "split_reason": "该候选包含的尽职调查与退出策略分别服务于不同的风险管理目标，且相互独立，故拆分为两个episode。"
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_007"
      ],
      "focal_question": "金融机构如何通过信息共享提升数字运营韧性？",
      "title": "威胁和漏洞情报信息共享",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "可定期共享威胁和漏洞情报",
          "evidence_unit_ids": [
            "v7u_N002040"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "预防安全事件发生",
          "evidence_unit_ids": [
            "v7u_N002040"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "帮助其他金融机构有效控制影响并更快恢复",
          "evidence_unit_ids": [
            "v7u_N002040"
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
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002040"
          ],
          "source_quote": "Financial institutions can regularly share information regarding threats and vulnerability intelligence to prevent the materialization of incidents.",
          "condition": null,
          "trigger_mode": null,
          "relation_type": null
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "qualifier": "helps_achieve",
          "evidence_unit_ids": [
            "v7u_N002040"
          ],
          "source_quote": "Information sharing enables other financial institutions to effectively contain impacts of financial crimes and recover faster.",
          "condition": null,
          "trigger_mode": null,
          "relation_type": null
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
      "reason": "描述DORA自2025年1月起适用于所有金融机构，是静态法律适用事实，不构成业务处理或判断流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "描述了金融机构实施ICT风险管理、设定战略、确定并批准风险容忍度及确保连续性的程序性动作和判断，构成ICT风险管理流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "描述了重大ICT事件触发报告义务的程序，构成事件报告流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "候选人中关于金融机构年度漏洞评估和漏洞修复的内容构成韧性测试与修复流程；主管当局渗透测试部分属职责规定，不构成金融机构流程，未建模。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004",
        "ep_005"
      ],
      "reason": "候选人包含两个独立流程：供应商尽职调查与禁止交易管理供应商安全风险；建立退出策略缓解集中风险。两者目标不同，故拆分为两个episode。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述关键ICT第三方服务提供商的监管义务，非金融机构的业务流程。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "描述了金融机构实施信息共享以预防事件和帮助其他机构的程序性动作和目的，构成信息共享流程。"
    },
    {
      "candidate_id": "s1c_008",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述满足DORA要求降低洗钱风险的因果知识，不包含业务处理或判断流程。"
    }
  ],
  "skip_reason": null
}
```
