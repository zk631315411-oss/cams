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

section_id: `CH24-S02`

section_title: `US AML/CFT regulatory landscape > USA PATRIOT Act`

section_text_with_unit_anchors:

```text
[v7u_N001701|1701] In 2001, the US enacted the Uniting and Strengthening America by Providing Appropriate Tools Required to Intercept and Obstruct Terrorism Act (USA PATRIOT Act).
ZH: 2001年美国颁布《爱国者法案》

[v7u_N001702|1702] This Act introduced significant AFC regulatory obligations that have influenced global financial regulations. It strengthened AML/CFT measures, impacting financial institutions worldwide.
ZH: 《爱国者法案》引入重大金融犯罪防控义务，强化反洗钱与反恐怖融资措施

[v7u_N001703|1703] Key global obligations derived from the USA PATRIOT Act include the following topics.
ZH: 《爱国者法案》衍生的关键全球义务列表导引

[v7u_N001704|1704] CDD and KYC: Financial institutions must verify customer identities, monitor transactions, and assess risks associated with business relationships. This requirement has influenced global AML frameworks, such as the FATF Recommendations.
ZH: 金融机构须验证客户身份、监控交易并评估风险，影响全球反洗钱框架

[v7u_N001705|1705] Jurisdictions of primary money laundering concern: Under section 311, the US Department of the Treasury can designate foreign jurisdictions, institutions, or transactions as money laundering risks, prompting actions by financial institutions. Designating a jurisdiction or financial organization forces banks to halt financial dealings with the designee.
ZH: 美国财政部可指定外国司法管辖区或机构为洗钱风险，迫使银行停止交易

[v7u_N001706|1706] EDD for foreign correspondent banking: Section 313 prohibits relationships with shell banks and Section 312 mandates EDD for correspondent accounts held by foreign financial institutions, affecting cross-border banking practices. Section 312 also applies to private banking accounts for non-US persons.
ZH: 第313条禁止与空壳银行往来，第312条要求对外国金融机构代理账户实施强化尽职调查

[v7u_N001707|1707] Forfeiture from US correspondent account: This Act permits the US government to seize funds from a correspondent account in the US that a foreign bank has opened and maintained. The owner of the funds may contest the seizure.
ZH: 允许美国政府扣押外国银行在美国代理账户中的资金，资金所有者可提出异议

[v7u_N001708|1708] Information sharing: Section 314 allows banks to cooperate with each other, law enforcement, and international agencies to combat financial crime. It provides institutions with safe harbor liability protections for sharing information.
ZH: 第314条允许银行与执法机构及国际机构共享信息，并提供安全港保护

[v7u_N001709|1709] Records relating to correspondent accounts for foreign banks: This Act allows the US government to request the production of various types of records, provides subpoena authority for correspondent accounts of foreign banks, and requires foreign banks to designate a registered agent in the US.
ZH: 美国政府可要求外国银行提供代理账户记录，并指定在美国的注册代理人
```

allowed_unit_ids:

```json
[
  "v7u_N001701",
  "v7u_N001702",
  "v7u_N001703",
  "v7u_N001704",
  "v7u_N001705",
  "v7u_N001706",
  "v7u_N001707",
  "v7u_N001708",
  "v7u_N001709"
]
```

## S2 Process IR

```json
{
  "section_id": "CH24-S02",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_gap_ch24_s02_cdd_kyc"
      ],
      "focal_question": "金融机构如何执行客户尽职调查和了解你的客户要求？",
      "title": "执行客户身份验证、交易监控和风险评估",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "业务关系",
          "evidence_unit_ids": [
            "v7u_N001704"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "验证客户身份、监控交易和评估风险",
          "evidence_unit_ids": [
            "v7u_N001704"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": "存在业务关系",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001704"
          ],
          "source_quote": "Financial institutions must verify customer identities, monitor transactions, and assess risks associated with business relationships."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "当美国财政部指定外国实体为洗钱风险时，金融机构必须如何反应？",
      "title": "根据第311条指定洗钱风险并迫使银行停止交易",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "美国财政部将外国司法管辖区、机构或交易指定为洗钱风险",
          "evidence_unit_ids": [
            "v7u_N001705"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "金融机构停止与该指定方的金融交易",
          "evidence_unit_ids": [
            "v7u_N001705"
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
          "process_element_id": "e002",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001705"
          ],
          "source_quote": "Designating a jurisdiction or financial organization forces banks to halt financial dealings with the designee."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_002",
        "s1c_gap_ch24_s02_private_banking_edd"
      ],
      "focal_question": "第312条要求对哪些情况实施强化尽职调查？",
      "title": "要求对特定代理账户和私人银行账户实施强化尽职调查",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "外国金融机构持有的代理账户",
          "evidence_unit_ids": [
            "v7u_N001706"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "context",
          "label": "非美国人的私人银行账户",
          "evidence_unit_ids": [
            "v7u_N001706"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "实施强化尽职调查（EDD）",
          "evidence_unit_ids": [
            "v7u_N001706"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e003",
          "condition": "如果存在外国金融机构代理账户",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001706"
          ],
          "source_quote": "Section 312 mandates EDD for correspondent accounts held by foreign financial institutions"
        },
        {
          "relation_id": "r002",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e002",
          "process_element_id": "e003",
          "condition": "如果存在非美国人的私人银行账户",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001706"
          ],
          "source_quote": "Section 312 also applies to private banking accounts for non-US persons."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_gap_ch24_s02_shell_bank_prohibition"
      ],
      "focal_question": "根据第313条，金融机构是否被允许与空壳银行建立或维持关系？",
      "title": "禁止与空壳银行建立或维持关系",
      "card_nature": "control",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "与空壳银行的关系",
          "evidence_unit_ids": [
            "v7u_N001706"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "禁止与空壳银行建立或维持关系",
          "evidence_unit_ids": [
            "v7u_N001706"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": "如果对方是空壳银行",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001706"
          ],
          "source_quote": "Section 313 prohibits relationships with shell banks"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "根据该法，美国政府扣押外国银行代理账户资金后，资金所有者有何权利？",
      "title": "扣押美国代理账户资金及资金所有者的异议权",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "外国银行在美国代理账户中持有资金",
          "evidence_unit_ids": [
            "v7u_N001707"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "美国政府扣押代理账户资金",
          "evidence_unit_ids": [
            "v7u_N001707"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "资金所有者对扣押提出异议",
          "evidence_unit_ids": [
            "v7u_N001707"
          ],
          "modality": "permitted"
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
            "v7u_N001707"
          ],
          "source_quote": "This Act permits the US government to seize funds from a correspondent account in the US that a foreign bank has opened and maintained."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "trigger_mode": null,
          "before_element_id": "e002",
          "after_element_id": "e003",
          "condition": null,
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001707"
          ],
          "source_quote": "The owner of the funds may contest the seizure."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "第314条如何允许信息共享，并提供什么保护？",
      "title": "允许信息共享并提供安全港责任保护",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "银行之间及与执法机构、国际机构共享信息以打击金融犯罪",
          "evidence_unit_ids": [
            "v7u_N001708"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "提供安全港责任保护",
          "evidence_unit_ids": [
            "v7u_N001708"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "trigger_mode": null,
          "process_element_id": "e001",
          "outcome_element_id": "e002",
          "condition": null,
          "relation_type": "component_assembles_product",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001708"
          ],
          "source_quote": "Section 314 allows banks to cooperate with each other, law enforcement, and international agencies to combat financial crime. It provides institutions with safe harbor liability protections for sharing information."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "根据该法，美国政府对外国银行的代理账户有哪些权力和要求？",
      "title": "要求外国银行提供记录、接受传票并指定注册代理人",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "外国银行在美国拥有代理账户",
          "evidence_unit_ids": [
            "v7u_N001709"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "要求外国银行提供各种记录",
          "evidence_unit_ids": [
            "v7u_N001709"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "对外国银行代理账户发出传票",
          "evidence_unit_ids": [
            "v7u_N001709"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "要求外国银行指定在美国的注册代理人",
          "evidence_unit_ids": [
            "v7u_N001709"
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
          "process_element_id": "e002",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001709"
          ],
          "source_quote": "This Act allows the US government to request the production of various types of records"
        },
        {
          "relation_id": "r002",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e001",
          "process_element_id": "e003",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001709"
          ],
          "source_quote": "provides subpoena authority for correspondent accounts of foreign banks"
        },
        {
          "relation_id": "r003",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e001",
          "process_element_id": "e004",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001709"
          ],
          "source_quote": "requires foreign banks to designate a registered agent in the US."
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
        "ep_002"
      ],
      "reason": "该候选描述了财政部指定洗钱风险并迫使银行停止交易的流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选提供了第312条对外国金融机构代理账户的EDD要求，作为该流程的一个触发条件。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选描述了扣押资金及异议的程序。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "该候选描述了信息共享及安全港保护。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_007"
      ],
      "reason": "该候选描述了要求记录、传票和指定代理人的多重权力。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s02_cdd_kyc",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选提供了CDD/KYC的基本义务流程。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s02_shell_bank_prohibition",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选描述了禁止与空壳银行关系的流程。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s02_private_banking_edd",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选提供了第312条对私人银行账户的EDD要求，作为同一流程的另一触发条件。"
    }
  ],
  "skip_reason": null
}
```
