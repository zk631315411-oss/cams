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

section_id: `CH30-S02`

section_title: `Using reports, guidance notes, and policy papers in your AML/CFT controls > Case example: Terrorist financing red flags`

section_text_with_unit_anchors:

```text
[v7u_N002165|2165] A regulator issues a report describing new information on how a major terrorist group finances itself. The report contains a list of red flags to look for.
ZH: 监管机构发布关于恐怖融资新信息的报告，并列出需关注的红旗信号信号。

[v7u_N002166|2166] The money laundering reporting officer (MLRO) considers how the bank can incorporate the list of red flags into its AML/CFT controls.
ZH: 反洗钱报告官（洗钱RO）考虑将红旗信号信号纳入机构的 反洗钱/反恐怖融资 控制措施。

[v7u_N002167|2167] The bank’s home regulator issued the document, and while the bank is not legally required to implement the guidance, the regulator expects that the bank will consider it.
ZH: 尽管无法律强制要求，监管机构期望银行考虑其发布的指导文件。

[v7u_N002168|2168] The MLRO conducts a review of the bank’s existing controls and processes to determine which areas are impacted. She then analyzes whether appropriate controls are in place and whether any gaps need to be addressed.
ZH: MLRO 审查现有控制措施和流程，分析差距并确定受影响领域。

[v7u_N002169|2169] One red flag identifies the use of import/export companies with a connection to certain jurisdictions.
ZH: 红旗信号信号：与特定司法管辖区有关联的进出口公司。

[v7u_N002170|2170] The bank has numerous import/export companies as clients. It has EDD procedures in place to provide extra scrutiny of such companies.
ZH: 银行拥有众多进出口公司客户，并已建立强化尽职调查（EDD）程序。

[v7u_N002171|2171] The MLRO reviews the bank’s procedures to assess alignment with the red flag.
ZH: MLRO 审查银行现有程序，评估其与红旗信号信号的一致性。

[v7u_N002172|2172] She finds that the bank asks all its import/export companies for extra information at onboarding and subjects them to an annual review.
ZH: 银行要求所有进出口公司在开户时提供额外信息并接受年度审查。

[v7u_N002173|2173] The bank requires that clients importing or exporting to certain higher risk jurisdictions provide additional documentation to support this activity.
ZH: 银行要求向高风险司法管辖区进出口的客户提供额外文件。

[v7u_N002174|2174] However, the new red flag refers to an additional jurisdiction that is not on the bank’s list.
ZH: 新红旗信号信号涉及一个银行现有清单中未包含的额外司法管辖区。

[v7u_N002175|2175] The MLRO consults with risk management and other stakeholders regarding any changes to the risk profile or operations that may arise from the new red flag.
ZH: MLRO 与风险管理及其他利益相关方协商新红旗信号信号可能带来的风险变化。

[v7u_N002176|2176] She then informs relevant business areas that the procedures need updating to include this additional jurisdiction.
ZH: MLRO 通知相关业务部门更新程序以纳入新增司法管辖区。

[v7u_N002177|2177] The MLRO also assesses the number of cases likely to be generated and ensures affected teams are aware and adequately resourced before making the change.
ZH: MLRO 评估可能产生的案件数量，确保受影响团队知情并配备足够资源。

[v7u_N002178|2178] She determines that no additional training is required at this time but informs the training team that future training should reflect the new information.
ZH: MLRO 确定当前无需额外培训，但通知培训团队未来培训应反映新信息。

[v7u_N002179|2179] In addition, the MLRO commissions a retrospective review of existing clients who trade with the jurisdiction to determine previously unidentified risk and whether additional action is required. When all actions are completed, she ensures that the change is reflected in appropriate documentation within the financial institution.
ZH: MLRO 委托对与该司法管辖区有交易的现有客户进行回溯审查，并更新文档。
```

allowed_unit_ids:

```json
[
  "v7u_N002165",
  "v7u_N002166",
  "v7u_N002167",
  "v7u_N002168",
  "v7u_N002169",
  "v7u_N002170",
  "v7u_N002171",
  "v7u_N002172",
  "v7u_N002173",
  "v7u_N002174",
  "v7u_N002175",
  "v7u_N002176",
  "v7u_N002177",
  "v7u_N002178",
  "v7u_N002179"
]
```

## S2 Process IR

```json
{
  "section_id": "CH30-S02",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "如何将监管机构发布的新恐怖融资红旗纳入银行反洗钱/反恐怖融资控制？",
      "title": "MLRO根据监管红旗报告更新银行AML/CFT控制",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "监管机构发布关于恐怖融资新信息的报告，包含需关注的红旗列表",
          "evidence_unit_ids": [
            "v7u_N002165"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "监管机构期望银行考虑其指导文件（无法律强制要求）",
          "evidence_unit_ids": [
            "v7u_N002167"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "MLRO考虑如何将红旗列表纳入银行的反洗钱/反恐怖融资控制",
          "evidence_unit_ids": [
            "v7u_N002166"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "MLRO审查现有控制和流程，确定受影响领域，分析控制是否适当以及需解决的差距",
          "evidence_unit_ids": [
            "v7u_N002168"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "input",
          "label": "一项红旗：与特定司法管辖区有关联的进出口公司",
          "evidence_unit_ids": [
            "v7u_N002169"
          ],
          "modality": null
        },
        {
          "element_id": "e006",
          "role": "input",
          "label": "银行现有EDD程序：要求所有进出口公司在开户时提供额外信息并进行年度审查，并要求向某些高风险司法管辖区进出口的客户提供额外文件",
          "evidence_unit_ids": [
            "v7u_N002170",
            "v7u_N002172",
            "v7u_N002173"
          ],
          "modality": null
        },
        {
          "element_id": "e007",
          "role": "decision",
          "label": "发现新红旗涉及银行清单上未包含的额外司法管辖区",
          "evidence_unit_ids": [
            "v7u_N002174"
          ],
          "modality": null
        },
        {
          "element_id": "e008",
          "role": "action",
          "label": "MLRO与风险管理和其他利益相关方就新红旗可能导致的风险概况或运营变化进行协商",
          "evidence_unit_ids": [
            "v7u_N002175"
          ],
          "modality": null
        },
        {
          "element_id": "e009",
          "role": "action",
          "label": "MLRO通知相关业务部门需要更新程序以纳入此额外司法管辖区",
          "evidence_unit_ids": [
            "v7u_N002176"
          ],
          "modality": null
        },
        {
          "element_id": "e010",
          "role": "action",
          "label": "MLRO评估可能产生的案件数量，并确保受影响团队在变更前知情且资源充足",
          "evidence_unit_ids": [
            "v7u_N002177"
          ],
          "modality": null
        },
        {
          "element_id": "e011",
          "role": "decision",
          "label": "确定当前无需额外培训",
          "evidence_unit_ids": [
            "v7u_N002178"
          ],
          "modality": null
        },
        {
          "element_id": "e012",
          "role": "action",
          "label": "通知培训团队未来培训应反映新信息",
          "evidence_unit_ids": [
            "v7u_N002178"
          ],
          "modality": null
        },
        {
          "element_id": "e013",
          "role": "action",
          "label": "MLRO委托对与该司法管辖区有交易的现有客户进行回溯审查，以确定之前未识别的风险和是否需额外行动",
          "evidence_unit_ids": [
            "v7u_N002179"
          ],
          "modality": null
        },
        {
          "element_id": "e014",
          "role": "outcome",
          "label": "在所有行动完成后，确保变更反映在金融机构的适当文档中",
          "evidence_unit_ids": [
            "v7u_N002179"
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
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002165",
            "v7u_N002166"
          ],
          "source_quote": "A regulator issues a report describing new information on how a major terrorist group finances itself. The report contains a list of red flags to look for. The money laundering reporting officer (MLRO) considers how the bank can incorporate the list of red flags into its AML/CFT controls."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002166",
            "v7u_N002167"
          ],
          "source_quote": "The bank’s home regulator issued the document, and while the bank is not legally required to implement the guidance, the regulator expects that the bank will consider it."
        },
        {
          "relation_id": "r003",
          "kind": "sequence",
          "before_element_id": "e003",
          "after_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002166",
            "v7u_N002168"
          ],
          "source_quote": "The money laundering reporting officer (MLRO) considers how the bank can incorporate the list... The MLRO conducts a review of the bank’s existing controls and processes to determine which areas are impacted."
        },
        {
          "relation_id": "r004",
          "kind": "reference",
          "process_element_id": "e004",
          "auxiliary_element_id": "e005",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002168",
            "v7u_N002169"
          ],
          "source_quote": "One red flag identifies the use of import/export companies with a connection to certain jurisdictions."
        },
        {
          "relation_id": "r005",
          "kind": "reference",
          "process_element_id": "e004",
          "auxiliary_element_id": "e006",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002168",
            "v7u_N002170",
            "v7u_N002172",
            "v7u_N002173"
          ],
          "source_quote": "The bank has numerous import/export companies as clients. It has EDD procedures in place to provide extra scrutiny of such companies. The MLRO reviews the bank’s procedures to assess alignment with the red flag. She finds that the bank asks all its import/export companies for extra information at onboarding and subjects them to an annual review. The bank requires that clients importing or exporting to certain higher risk jurisdictions provide additional documentation."
        },
        {
          "relation_id": "r006",
          "kind": "produce",
          "process_element_id": "e004",
          "outcome_element_id": "e007",
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002168",
            "v7u_N002174"
          ],
          "source_quote": "However, the new red flag refers to an additional jurisdiction that is not on the bank’s list."
        },
        {
          "relation_id": "r007",
          "kind": "sequence",
          "before_element_id": "e007",
          "after_element_id": "e008",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002174",
            "v7u_N002175"
          ],
          "source_quote": "The MLRO consults with risk management and other stakeholders regarding any changes to the risk profile or operations that may arise from the new red flag."
        },
        {
          "relation_id": "r008",
          "kind": "sequence",
          "before_element_id": "e008",
          "after_element_id": "e009",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002175",
            "v7u_N002176"
          ],
          "source_quote": "She then informs relevant business areas that the procedures need updating to include this additional jurisdiction."
        },
        {
          "relation_id": "r009",
          "kind": "sequence",
          "before_element_id": "e009",
          "after_element_id": "e010",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002176",
            "v7u_N002177"
          ],
          "source_quote": "The MLRO also assesses the number of cases likely to be generated and ensures affected teams are aware and adequately resourced before making the change."
        },
        {
          "relation_id": "r010",
          "kind": "sequence",
          "before_element_id": "e010",
          "after_element_id": "e011",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002177",
            "v7u_N002178"
          ],
          "source_quote": "She determines that no additional training is required at this time but informs the training team that future training should reflect the new information."
        },
        {
          "relation_id": "r011",
          "kind": "sequence",
          "before_element_id": "e011",
          "after_element_id": "e012",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002178"
          ],
          "source_quote": "but informs the training team that future training should reflect the new information."
        },
        {
          "relation_id": "r012",
          "kind": "sequence",
          "before_element_id": "e009",
          "after_element_id": "e013",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002176",
            "v7u_N002179"
          ],
          "source_quote": "In addition, the MLRO commissions a retrospective review of existing clients who trade with the jurisdiction to determine previously unidentified risk and whether additional action is required."
        },
        {
          "relation_id": "r013",
          "kind": "produce",
          "process_element_id": "e013",
          "outcome_element_id": "e014",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002179"
          ],
          "source_quote": "When all actions are completed, she ensures that the change is reflected in appropriate documentation within the financial institution."
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
      "reason": "该候选完整描述了监管报告触发、MLRO审查、差距识别及后续更新控制的程序流程，包含多个程序性和判断性关系，因此映射为一个episode。"
    }
  ],
  "skip_reason": null
}
```
