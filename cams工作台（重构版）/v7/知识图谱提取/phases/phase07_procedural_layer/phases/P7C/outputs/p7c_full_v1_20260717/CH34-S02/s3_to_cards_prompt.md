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

section_id: `CH34-S02`

section_title: `Three lines of defense > First line of defense AFC function`

section_text_with_unit_anchors:

```text
[v7u_N002421|2421] The first line of defense (LOD) is critical in a financial institution’s risk management framework. It includes front-line functions that are responsible for directly managing customers and risks in their day-to-day operations. Each organization structures itself differently based on its legacy, size, and complexity. The first line is composed of the following functions, which might be named or organized differently:
ZH: 第一道防线在金融机构风险管理框架中的关键作用及其组成

[v7u_N002422|2422] Business development engages with clients and creates sales opportunities. This function should be aware of the risks associated with onboarding new clients, support the due diligence process, and escalate any identified red flags.
ZH: 业务拓展职能需了解客户准入风险、支持尽职调查并上报红旗信号信号

[v7u_N002423|2423] Business support provides resources and operational support to enable smooth client interactions and transactions. This function ensures that staff have access to the necessary systems to perform their jobs effectively. Business support functions might sometimes perform initial due diligence.
ZH: 业务支持职能提供运营支持，确保员工使用必要系统，有时执行初步尽职调查

[v7u_N002424|2424] Product development creates and launches new financial products, assesses potential financial crime risks, and ensures compliance with regulatory requirements.
ZH: 产品开发职能评估金融犯罪风险并确保合规

[v7u_N002425|2425] Product support ensures existing products remain compliant with regulations and meet client needs without introducing unnecessary risk.
ZH: 产品支持职能确保现有产品合规且不引入不必要风险

[v7u_N002426|2426] Operations functions execute and process transactions, implementing operational procedures to detect and report suspicious activities internally.
ZH: 运营职能执行交易并实施操作程序以内部检测和报告可疑活动

[v7u_N002427|2427] First-line risks and controls identify, assess, and manage risks arising from frontline operations, setting up internal controls and procedures to ensure compliance according to the organization's policies.
ZH: 第一道防线风险与控制职能识别、评估和管理一线运营风险，设置内部控制

[v7u_N002428|2428] In the first line, risks and control functions aligned with business units typically monitor transactions, review suspicious alerts, and perform regular control assurance reviews.
ZH: 第一道防线风险与控制职能通常监控交易、审查可疑警报并执行控制保证审查

[v7u_N002429|2429] These positions are typically established in consultation with the second LOD.
ZH: 第一道防线岗位通常与第二道防线协商设立

[v7u_N002430|2430] Risk management structures may vary by institution size and type.
ZH: 风险管理结构因机构规模和类型而异

[v7u_N002431|2431] For example, transaction monitoring may fall under the first or second LOD.
ZH: 交易监控可能属于第一道或第二道防线

[v7u_N002432|2432] Teams often escalate complex cases and alerts that cannot be ruled out to the second line’s financial intelligence unit (FIU) for further investigation.
ZH: 复杂案件和警报升级至第二道防线金融情报单位（FIU）进一步调查

[v7u_N002433|2433] Industries such as gaming, gambling, and law firms might place these controls in the second LOD.
ZH: 博彩、赌博和律师事务所等行业可能将控制置于第二道防线

[v7u_N002434|2434] Larger financial institutions tend to maintain more defined separation between lines.
ZH: 大型金融机构倾向于保持更明确的防线分离

[v7u_N002435|2435] Within the first line, the front office is responsible for client-facing operations and revenue-generating business development. Because office personnel are the first point of contact for clients, they are critical in managing client relationship risks.
ZH: 第一道防线前台负责客户关系和创收业务，管理客户关系风险

[v7u_N002436|2436] The middle office supports the front office by managing risk and compliance frameworks within the first LOD. It acts as a liaison among various internal stakeholders, ensuring that front office activity risks are communicated and managed effectively.
ZH: 中台支持前台，管理第一道防线内的风险与合规框架，协调内部利益相关者

[v7u_N002437|2437] In this framework, the front office manages client relationship risks, while the middle office handles internal operational and processing risks. Both offices implement controls designed and overseen by the second line, assessing risk and escalating suspicious activities or control breaches.
ZH: 前台管理客户关系风险，中台处理运营和流程风险，均实施第二道防线设计的控制

[v7u_N002438|2438] This structure ensures risk ownership begins at the point of origination, with proper oversight and clear escalation channels.
ZH: 该结构确保风险所有权始于源头，并具备适当监督和清晰升级渠道
```

allowed_unit_ids:

```json
[
  "v7u_N002421",
  "v7u_N002422",
  "v7u_N002423",
  "v7u_N002424",
  "v7u_N002425",
  "v7u_N002426",
  "v7u_N002427",
  "v7u_N002428",
  "v7u_N002429",
  "v7u_N002430",
  "v7u_N002431",
  "v7u_N002432",
  "v7u_N002433",
  "v7u_N002434",
  "v7u_N002435",
  "v7u_N002436",
  "v7u_N002437",
  "v7u_N002438"
]
```

## S2 Process IR

```json
{
  "section_id": "CH34-S02",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "如何将无法排除的复杂案件和警报升级至第二道防线FIU？",
      "title": "复杂案件和警报升级流程",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "复杂案件和无法排除的警报",
          "evidence_unit_ids": [
            "v7u_N002432"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "升级至第二道防线的金融情报单位(FIU)",
          "evidence_unit_ids": [
            "v7u_N002432"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "FIU 进行进一步调查",
          "evidence_unit_ids": [
            "v7u_N002432"
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
          "condition": "案件或警报无法被排除",
          "source_quote": "Teams often escalate complex cases and alerts that cannot be ruled out to the second line’s financial intelligence unit (FIU) for further investigation.",
          "evidence_unit_ids": [
            "v7u_N002432"
          ],
          "qualifier": null
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "source_quote": "Teams often escalate complex cases and alerts that cannot be ruled out to the second line’s financial intelligence unit (FIU) for further investigation.",
          "evidence_unit_ids": [
            "v7u_N002432"
          ],
          "qualifier": null
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_gap_ch34_s02_bd_escalate"
      ],
      "focal_question": "业务发展如何在客户准入中识别并上报红旗信号？",
      "title": "业务发展职能上报红旗信号流程",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "业务发展与客户接触并创造销售机会",
          "evidence_unit_ids": [
            "v7u_N002422"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "需了解客户准入风险并支持尽职调查过程",
          "evidence_unit_ids": [
            "v7u_N002422"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "上报任何识别的红旗信号",
          "evidence_unit_ids": [
            "v7u_N002422"
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
          "source_quote": "Business development engages with clients and creates sales opportunities. This function should be aware of the risks associated with onboarding new clients, support the due diligence process, and escalate any identified red flags.",
          "evidence_unit_ids": [
            "v7u_N002422"
          ],
          "qualifier": null
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "source_quote": "Business development engages with clients and creates sales opportunities. This function should be aware of the risks associated with onboarding new clients, support the due diligence process, and escalate any identified red flags.",
          "evidence_unit_ids": [
            "v7u_N002422"
          ],
          "qualifier": null
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_gap_ch34_s02_pd_risk_assess"
      ],
      "focal_question": "产品开发如何在推出新产品时评估金融犯罪风险并确保合规？",
      "title": "新产品开发中的金融犯罪风险评估与合规流程",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "创建并推出新产品",
          "evidence_unit_ids": [
            "v7u_N002424"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "评估潜在金融犯罪风险并确保符合监管要求",
          "evidence_unit_ids": [
            "v7u_N002424"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "新产品符合监管要求",
          "evidence_unit_ids": [
            "v7u_N002424"
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
          "source_quote": "Product development creates and launches new financial products, assesses potential financial crime risks, and ensures compliance with regulatory requirements.",
          "evidence_unit_ids": [
            "v7u_N002424"
          ],
          "qualifier": null
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "source_quote": "Product development creates and launches new financial products, assesses potential financial crime risks, and ensures compliance with regulatory requirements.",
          "evidence_unit_ids": [
            "v7u_N002424"
          ],
          "qualifier": null
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_gap_ch34_s02_ops_detect_report"
      ],
      "focal_question": "运营职能如何在交易处理中检测并报告可疑活动？",
      "title": "交易处理中检测并报告可疑活动流程",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "执行和处理交易",
          "evidence_unit_ids": [
            "v7u_N002426"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "实施操作程序",
          "evidence_unit_ids": [
            "v7u_N002426"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "内部检测并报告可疑活动",
          "evidence_unit_ids": [
            "v7u_N002426"
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
          "source_quote": "Operations functions execute and process transactions, implementing operational procedures to detect and report suspicious activities internally.",
          "evidence_unit_ids": [
            "v7u_N002426"
          ],
          "qualifier": null
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "source_quote": "Operations functions execute and process transactions, implementing operational procedures to detect and report suspicious activities internally.",
          "evidence_unit_ids": [
            "v7u_N002426"
          ],
          "qualifier": "aimed_to"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_gap_ch34_s02_fomo_escalate"
      ],
      "focal_question": "前台和中台在实施第二道防线设计的控制时，如何评估风险并升级可疑活动或控制违反？",
      "title": "前台中台实施控制中的风险升级流程",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "前台和中台实施第二道防线设计的控制",
          "evidence_unit_ids": [
            "v7u_N002437"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "评估风险并升级可疑活动或控制违反",
          "evidence_unit_ids": [
            "v7u_N002437"
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
          "source_quote": "Both offices implement controls designed and overseen by the second line, assessing risk and escalating suspicious activities or control breaches.",
          "evidence_unit_ids": [
            "v7u_N002437"
          ],
          "qualifier": null
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
      "reason": "该候选明确描述了将无法排除的复杂案件和警报升级至第二道防线FIU的程序性迁移，构成合格流程。"
    },
    {
      "candidate_id": "s1c_gap_ch34_s02_bd_escalate",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选包含业务发展职能在客户接触中识别并上报红旗信号的程序性义务，构成合格流程。"
    },
    {
      "candidate_id": "s1c_gap_ch34_s02_pd_risk_assess",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选包含产品开发在推出新产品时评估金融犯罪风险并确保合规的程序性动作，构成合格流程。"
    },
    {
      "candidate_id": "s1c_gap_ch34_s02_ops_detect_report",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选包含运营职能在交易处理中实施操作程序以检测和报告可疑活动的有向关系，构成合格流程。"
    },
    {
      "candidate_id": "s1c_gap_ch34_s02_fomo_escalate",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选包含前台和中台在实施控制时评估风险并升级可疑活动或控制违反的程序性迁移，构成合格流程。"
    },
    {
      "candidate_id": "s1c_gap_ch34_s02_l1rc_review_alert",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选仅描述第一线风险控制人员的常规职责（监控、审查、执行审查），缺乏明确的流程输出或有向关系，属于静态职责描述，不构成程序性或判断性迁移。"
    }
  ],
  "skip_reason": null
}
```
