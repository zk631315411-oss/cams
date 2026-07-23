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

section_id: `CH30-S04`

section_title: `Using reports, guidance notes, and policy papers in your AML/CFT controls > National, sectoral, and thematic risk assessments`

section_text_with_unit_anchors:

```text
[v7u_N002183|2183] A national risk assessment (NRA) is a document that a jurisdiction produces to identify and evaluate money laundering threats and vulnerabilities, determine risk levels, and develop strategies to respond to risks.
ZH: 国家风险评估（NRA）是司法管辖区识别和评估洗钱威胁与脆弱性的文件。

[v7u_N002184|2184] NRAs should be comprehensive documents, drawing on a wide range of data.
ZH: NRA应全面并基于广泛数据。

[v7u_N002185|2185] FATF Recommendation 1 requires jurisdictions to identify, assess, understand, and mitigate the money laundering, terrorist financing, and proliferation financing risks they face.
ZH: FATF建议1要求司法管辖区识别、评估、理解并减轻洗钱、恐怖融资和扩散融资风险。

[v7u_N002186|2186] Jurisdictions can consolidate and articulate their knowledge of these risks using an NRA.
ZH: NRA是司法管辖区整合和表达风险知识的工具。

[v7u_N002187|2187] FATF encourages all jurisdictions to produce an NRA, and EU jurisdictions are legally obliged to produce a risk assessment via the fourth EU AML directive.
ZH: FATF鼓励所有司法管辖区开展NRA，欧盟司法管辖区根据第四反洗钱指令有法律义务。

[v7u_N002188|2188] FATF has produced guidance for conducting NRAs. In addition, international organizations such as the World Bank and the Council of Europe have produced detailed methodologies that jurisdictions can use and adapt to produce an NRA. Alternatively, jurisdictions might decide to develop their own methodology.
ZH: FATF、世界银行和欧洲委员会等提供NRA指南和方法论。

[v7u_N002189|2189] NRAs analyze risk in a number of ways, including focusing on emerging sectors or areas of increasing risk.
ZH: NRA以多种方式分析风险，包括关注新兴领域或风险上升领域。

[v7u_N002190|2190] Jurisdictions can produce sectoral risk assessments (SRAs) or thematic risk assessments to supplement the NRA and to highlight these issues.
ZH: 司法管辖区可开展行业风险评估（SRA）或专题风险评估以补充NRA。

[v7u_N002191|2191] Whereas SRAs focus on specific sectors, such as the gaming industry, thematic assessments look at issues such as the risk that emerging technologies pose.
ZH: SRA聚焦特定行业，专题评估关注新兴技术等议题。

[v7u_N002192|2192] A jurisdiction might conduct a separate SRA or thematic risk assessment if new risks arise or in response to new regulations for a sector.
ZH: 当新风险出现或新法规出台时，司法管辖区可能开展单独的SRA或专题评估。

[v7u_N002193|2193] As with NRAs, international organizations provide methodologies to help jurisdictions create SRAs and thematic risk assessments.
ZH: 国际组织为SRA和专题风险评估提供方法论。

[v7u_N002194|2194] FATF Recommendation 2 requires jurisdictions to implement policies that align with the identified risk.
ZH: FATF建议2要求司法管辖区实施与已识别风险一致的政策。

[v7u_N002195|2195] Jurisdictions should also produce action plans to mitigate the risks identified in the NRA, SRA, or thematic risk assessment, which can be public or confidential documents.
ZH: 司法管辖区应制定行动计划以减轻NRA、SRA或专题评估中识别的风险。

[v7u_N002196|2196] Public risk assessments and action plans provide organizations with information about risk levels the government applies to their sector and other sectors, along with other highlevel information about risk and the government’s priorities for addressing it.
ZH: 公开的风险评估和行动计划为组织提供政府对其行业及其他行业风险水平的信息。
```

allowed_unit_ids:

```json
[
  "v7u_N002183",
  "v7u_N002184",
  "v7u_N002185",
  "v7u_N002186",
  "v7u_N002187",
  "v7u_N002188",
  "v7u_N002189",
  "v7u_N002190",
  "v7u_N002191",
  "v7u_N002192",
  "v7u_N002193",
  "v7u_N002194",
  "v7u_N002195",
  "v7u_N002196"
]
```

## S2 Process IR

```json
{
  "section_id": "CH30-S04",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_gap_ch30_s04_nra_methodology_choice"
      ],
      "focal_question": "司法管辖区如何选择NRA方法论？",
      "title": "选择NRA方法论",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "FATF、世界银行等提供的NRA方法论",
          "evidence_unit_ids": [
            "v7u_N002188"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "司法管辖区可使用和调整现有方法论，或决定开发自己的方法论",
          "evidence_unit_ids": [
            "v7u_N002188"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "使用现有方法论开展NRA",
          "evidence_unit_ids": [
            "v7u_N002188"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "开发自己的方法论开展NRA",
          "evidence_unit_ids": [
            "v7u_N002188"
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
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002188"
          ],
          "source_quote": "jurisdictions can use and adapt to produce an NRA",
          "trigger_mode": null,
          "condition": null
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002188"
          ],
          "source_quote": "jurisdictions can use and adapt to produce an NRA",
          "trigger_mode": null,
          "condition": null
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002188"
          ],
          "source_quote": "jurisdictions might decide to develop their own methodology",
          "trigger_mode": null,
          "condition": null
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_gap_ch30_s04_sra_supplement_nra"
      ],
      "focal_question": "司法管辖区如何通过SRA或专题风险评估补充NRA？",
      "title": "开展SRA或专题风险评估以补充NRA",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e101",
          "role": "input",
          "label": "已完成的国家风险评估（NRA）",
          "evidence_unit_ids": [
            "v7u_N002190"
          ],
          "modality": null
        },
        {
          "element_id": "e102",
          "role": "action",
          "label": "开展行业或专题风险评估",
          "evidence_unit_ids": [
            "v7u_N002190"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e103",
          "role": "outcome",
          "label": "行业风险评估（SRA）或专题风险评估",
          "evidence_unit_ids": [
            "v7u_N002190"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r101",
          "kind": "reference",
          "process_element_id": "e102",
          "auxiliary_element_id": "e101",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002190"
          ],
          "source_quote": "to supplement the NRA",
          "trigger_mode": null,
          "condition": null
        },
        {
          "relation_id": "r102",
          "kind": "produce",
          "process_element_id": "e102",
          "outcome_element_id": "e103",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002190"
          ],
          "source_quote": "Jurisdictions can produce sectoral risk assessments (SRAs) or thematic risk assessments to supplement the NRA and to highlight these issues.",
          "trigger_mode": null,
          "condition": null
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_gap_ch30_s04_new_risk_sra"
      ],
      "focal_question": "当新风险或新法规出现时，司法管辖区如何响应？",
      "title": "针对新风险或法规开展单独的SRA或专题风险评估",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e201",
          "role": "context",
          "label": "新风险出现或行业新法规出台",
          "evidence_unit_ids": [
            "v7u_N002192"
          ],
          "modality": null
        },
        {
          "element_id": "e202",
          "role": "action",
          "label": "可能开展单独的行业或专题风险评估",
          "evidence_unit_ids": [
            "v7u_N002192"
          ],
          "modality": null
        },
        {
          "element_id": "e203",
          "role": "outcome",
          "label": "单独的行业风险评估（SRA）或专题风险评估",
          "evidence_unit_ids": [
            "v7u_N002192"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r201",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e201",
          "process_element_id": "e202",
          "condition": "新风险出现或行业新法规出台",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002192"
          ],
          "source_quote": "if new risks arise or in response to new regulations for a sector"
        },
        {
          "relation_id": "r202",
          "kind": "produce",
          "process_element_id": "e202",
          "outcome_element_id": "e203",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002192"
          ],
          "source_quote": "A jurisdiction might conduct a separate SRA or thematic risk assessment",
          "trigger_mode": null,
          "condition": null
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_gap_ch30_s04_action_plan_mitigate_risk"
      ],
      "focal_question": "司法管辖区如何缓解已识别的风险？",
      "title": "制定行动计划以缓解已识别风险",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e301",
          "role": "input",
          "label": "NRA、SRA或专题风险评估中识别的风险",
          "evidence_unit_ids": [
            "v7u_N002195"
          ],
          "modality": null
        },
        {
          "element_id": "e302",
          "role": "action",
          "label": "应制定行动计划",
          "evidence_unit_ids": [
            "v7u_N002195"
          ],
          "modality": null
        },
        {
          "element_id": "e303",
          "role": "outcome",
          "label": "行动计划（可公开或保密）",
          "evidence_unit_ids": [
            "v7u_N002195"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r301",
          "kind": "reference",
          "process_element_id": "e302",
          "auxiliary_element_id": "e301",
          "relation_type": "conclusion_triggers_response",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002195"
          ],
          "source_quote": "to mitigate the risks identified in the NRA, SRA, or thematic risk assessment",
          "trigger_mode": null,
          "condition": null
        },
        {
          "relation_id": "r302",
          "kind": "produce",
          "process_element_id": "e302",
          "outcome_element_id": "e303",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002195"
          ],
          "source_quote": "Jurisdictions should also produce action plans to mitigate the risks identified",
          "trigger_mode": null,
          "condition": null
        }
      ],
      "split_reason": null
    }
  ],
  "candidate_audit": [
    {
      "candidate_id": "s1c_gap_ch30_s04_nra_methodology_choice",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选提供了司法管辖区在已有方法论基础上选择采用或开发自身方法论的独立处置链，程序关系清晰可建模。"
    },
    {
      "candidate_id": "s1c_gap_ch30_s04_sra_supplement_nra",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了为补充NRA而开展SRA或专题评估的动作，具备明确的action-outcome关系。"
    },
    {
      "candidate_id": "s1c_gap_ch30_s04_new_risk_sra",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选以条件触发单独评估的过程，满足trigger-action程序链。"
    },
    {
      "candidate_id": "s1c_gap_ch30_s04_action_plan_mitigate_risk",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选基于已识别风险制定行动计划，形成清晰的输入-动作-输出流程。"
    }
  ],
  "skip_reason": null
}
```
