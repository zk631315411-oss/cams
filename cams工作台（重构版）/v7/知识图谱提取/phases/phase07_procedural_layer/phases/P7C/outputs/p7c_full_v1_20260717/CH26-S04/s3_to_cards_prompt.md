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

section_id: `CH26-S04`

section_title: `Other laws and regulations that impact organizations > The GDPR and the balance between privacy and transparency`

section_text_with_unit_anchors:

```text
[v7u_N002057|2057] The GDPR applies to all data processing activities. These include activities where an organization processes personal data to comply with other regulations it is subject to, such as data gathering for AML purposes.
ZH: 《通用数据保护条例》适用于所有数据处理活动，包括为反洗钱合规目的收集数据

[v7u_N002058|2058] AML obligations require organizations to obtain and process the personal data of relevant data subjects when performing KYC tasks. These tasks can include gathering ultimate beneficial ownership information and customer identification information such as the full name and date of birth of individual directors.
ZH: 反洗钱义务要求组织在执行了解你的客户任务时获取和处理数据主体的个人数据

[v7u_N002059|2059] The GDPR applies to all organizations that use personal data and are established in the EU or that fall within the extraterritorial scope of the law.
ZH: 《通用数据保护条例》适用于在欧盟设立或属于域外适用范围的所有使用个人数据的组织

[v7u_N002060|2060] Therefore, organizations must adhere to AML obligations and the GDPR.
ZH: 组织必须同时遵守反洗钱义务和《通用数据保护条例》

[v7u_N002061|2061] The GDPR obliges organizations to provide data subjects with a variety of rights regarding their personal data. These rights can include a right of access, a right to deletion, and the right to be informed, also referred to as transparency. The GDPR requires organizations to inform data subjects about why and how the organization will use their personal data.
ZH: 《通用数据保护条例》要求组织赋予数据主体访问、删除、知情等权利，并履行透明度义务。

[v7u_N002062|2062] Articles 75 and 76 of Regulation (EU) 2024/1624 of the European Parliament and of the Council also reference these requirements and state the permissible instances where organizations or other obliged entities may share or process relevant personal information for AML compliance purposes.
ZH: 欧盟第2024/1624号条例第75和76条引用《通用数据保护条例》要求，允许为反洗钱合规目的共享或处理个人信息。

[v7u_N002063|2063] For organizations to lawfully obtain and process personal data, they need at least one lawful reason.
ZH: 组织合法获取和处理个人数据需要至少一项合法理由。

[v7u_N002064|2064] The GDPR provides a list of lawful grounds available for processing standard forms of personal data, such as ID and proof of address information.
ZH: 《通用数据保护条例》列出了处理标准个人数据（如身份证明和地址证明）的合法依据清单。

[v7u_N002065|2065] Additionally, the GDPR states exemptions for the processing of special and sensitive forms of personal data.
ZH: 《通用数据保护条例》规定了特殊和敏感个人数据处理的豁免情形。

[v7u_N002066|2066] This data can include information on race, ethnicity, or political beliefs, as determined from an organization’s KYC information. This data can also include criminal convictions and offenses.
ZH: 特殊类别数据包括从了解你的客户信息中获取的种族、民族或政治信仰，以及刑事定罪和犯罪记录。

[v7u_N002067|2067] The AML regulation states that organizations can use these forms of personal data under the condition that they apply appropriate transparency measures.
ZH: 反洗钱法规规定，组织在采取适当透明度措施的条件下可使用这些个人数据。

[v7u_N002068|2068] Note that data subject rights are not absolute. The offense of tipping off under AML law will impact the extent to which an organization can share certain details of its processing activities with a relevant data subject.
ZH: 数据主体权利并非绝对；反洗钱法中的“泄密”罪限制了组织向数据主体披露处理活动细节的程度。
```

allowed_unit_ids:

```json
[
  "v7u_N002057",
  "v7u_N002058",
  "v7u_N002059",
  "v7u_N002060",
  "v7u_N002061",
  "v7u_N002062",
  "v7u_N002063",
  "v7u_N002064",
  "v7u_N002065",
  "v7u_N002066",
  "v7u_N002067",
  "v7u_N002068"
]
```

## S2 Process IR

```json
{
  "section_id": "CH26-S04",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001",
        "s1c_003"
      ],
      "focal_question": "GDPR 如何适用于处理个人数据的组织，并产生哪些数据主体权利相关义务？",
      "title": "GDPR 适用产生的数据主体权利提供义务",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "组织进行数据处理活动（包括为反洗钱合规目的）",
          "evidence_unit_ids": [
            "v7u_N002057"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "GDPR 适用于在欧盟设立或属于域外适用范围的个人数据使用组织",
          "evidence_unit_ids": [
            "v7u_N002059"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "decision",
          "label": "GDPR 适用",
          "evidence_unit_ids": [
            "v7u_N002057",
            "v7u_N002059"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "必须同时遵守反洗钱义务和 GDPR",
          "evidence_unit_ids": [
            "v7u_N002060"
          ],
          "modality": "required"
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "必须提供数据主体权利并履行透明度义务",
          "evidence_unit_ids": [
            "v7u_N002061"
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
          "condition": "组织使用个人数据并位于欧盟或属于域外适用范围",
          "relation_type": "standard_transmits_requirement",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002057",
            "v7u_N002059"
          ],
          "source_quote": "The GDPR applies to all organizations that use personal data and are established in the EU or that fall within the extraterritorial scope of the law."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002059"
          ],
          "source_quote": "The GDPR applies to all organizations that use personal data and are established in the EU or that fall within the extraterritorial scope of the law."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002060"
          ],
          "source_quote": "Therefore, organizations must adhere to AML obligations and the GDPR."
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e005",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002061"
          ],
          "source_quote": "The GDPR obliges organizations to provide data subjects with a variety of rights regarding their personal data."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "组织能否依据欧盟第2024/1624号条例为反洗钱合规目的共享或处理相关个人信息？",
      "title": "依据EU 2024/1624条例许可的AML数据共享与处理",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "为反洗钱合规目的",
          "evidence_unit_ids": [
            "v7u_N002062"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "欧盟第2024/1624号条例第75和76条",
          "evidence_unit_ids": [
            "v7u_N002062"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "decision",
          "label": "允许共享或处理相关个人信息",
          "evidence_unit_ids": [
            "v7u_N002062"
          ],
          "modality": "permitted"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002062"
          ],
          "source_quote": "Articles 75 and 76 of Regulation (EU) 2024/1624 of the European Parliament and of the Council also reference these requirements and state the permissible instances where organizations or other obliged entities may share or process relevant personal information for AML compliance purposes."
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
            "v7u_N002062"
          ],
          "source_quote": "Articles 75 and 76 of Regulation (EU) 2024/1624 ... state the permissible instances where organizations ... may share or process relevant personal information for AML compliance purposes."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "组织在何种条件下可依据GDPR和AML法规使用特殊类别的个人数据？",
      "title": "特殊类别个人数据处理的豁免与透明度条件",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "为反洗钱合规目的处理特殊类别个人数据",
          "evidence_unit_ids": [
            "v7u_N002065",
            "v7u_N002067"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "GDPR 规定特殊和敏感个人数据的豁免",
          "evidence_unit_ids": [
            "v7u_N002065"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "standard",
          "label": "AML 法规的条件：采取适当透明度措施",
          "evidence_unit_ids": [
            "v7u_N002067"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "应用适当的透明度措施",
          "evidence_unit_ids": [
            "v7u_N002067"
          ],
          "modality": "required"
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "允许使用这些特殊类别个人数据",
          "evidence_unit_ids": [
            "v7u_N002067"
          ],
          "modality": "permitted"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e004",
          "auxiliary_element_id": "e003",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002067"
          ],
          "source_quote": "The AML regulation states that organizations can use these forms of personal data under the condition that they apply appropriate transparency measures."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e004",
          "auxiliary_element_id": "e002",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002065"
          ],
          "source_quote": "Additionally, the GDPR states exemptions for the processing of special and sensitive forms of personal data."
        },
        {
          "relation_id": "r003",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e004",
          "condition": "当处理特殊数据时",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002067"
          ],
          "source_quote": "The AML regulation states that organizations can use these forms of personal data under the condition that they apply appropriate transparency measures."
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e004",
          "outcome_element_id": "e005",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002067"
          ],
          "source_quote": "The AML regulation states that organizations can use these forms of personal data under the condition that they apply appropriate transparency measures."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "反洗钱泄密罪如何限制组织向数据主体披露处理细节？",
      "title": "数据主体权利与反洗钱泄密罪的平衡",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "数据主体权利请求（如知情权）导致需共享处理细节",
          "evidence_unit_ids": [
            "v7u_N002068"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "反洗钱法中的泄密罪",
          "evidence_unit_ids": [
            "v7u_N002068"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "decision",
          "label": "泄密罪影响共享程度评估",
          "evidence_unit_ids": [
            "v7u_N002068"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "限制向数据主体共享某些处理细节",
          "evidence_unit_ids": [
            "v7u_N002068"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002068"
          ],
          "source_quote": "The offense of tipping off under AML law will impact the extent to which an organization can share certain details of its processing activities with a relevant data subject."
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
            "v7u_N002068"
          ],
          "source_quote": "The offense of tipping off under AML law will impact the extent to which an organization can share certain details of its processing activities with a relevant data subject."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002068"
          ],
          "source_quote": "The offense of tipping off under AML law will impact the extent to which an organization can share certain details of its processing activities with a relevant data subject."
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
      "reason": "该候选提供了 GDPR 的法律适用判断和必须同时遵守 AML 与 GDPR 的义务，构成一个程序性流程的起点和结果。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选仅陈述数据处理需要合法理由的静态法律规定，不包含原文明示的处理或判断过程，属于非程序性事实。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选提供了 GDPR 要求组织提供数据主体权利并履行透明度义务的具体义务，与 s1c_001 共同构成完整的 GDPR 适用与义务履行流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选基于欧盟条例明确规定了在反洗钱合规目的下共享或处理个人信息的许可，构成一个独立的法律许可评估流程。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述了特殊类别个人数据处理的豁免以及 AML 法规要求的透明度条件，形成了一个需要执行透明度措施以获得许可的程序性流程。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选揭示了数据主体权利的非绝对性，以及泄密罪如何限制组织共享处理细节，构成了一个在回应数据主体请求时必须进行的平衡判断流程。"
    }
  ],
  "skip_reason": null
}
```
