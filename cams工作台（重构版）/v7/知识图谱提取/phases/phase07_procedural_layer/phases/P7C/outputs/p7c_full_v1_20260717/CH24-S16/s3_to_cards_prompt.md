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

section_id: `CH24-S16`

section_title: `US AML/CFT regulatory landscape > Japan AML regulations`

section_text_with_unit_anchors:

```text
[v7u_N001927|1927] Japan’s AML/CFT framework aligns with FATF’s Recommendations and evolving financial crime risks.
ZH: 日本的反洗钱/反恐怖融资框架与FATF建议及不断变化的金融犯罪风险保持一致。

[v7u_N001928|1928] The framework includes the Act on Prevention of Transfer of Criminal Proceeds, the Act on Punishment of Organized Crimes and Control of Crime Proceeds, and the Foreign Exchange and Foreign Trade Act.
ZH: 日本反洗钱/反恐怖融资框架包括《犯罪收益转移防止法》等法律。

[v7u_N001929|1929] According to Japan’s AML/CFT legislation, financial institutions and DNFBPs must adhere to CDD requirements, report suspicious transactions, and implement internal risk-based AML programs.
ZH: 金融机构和DNFBP必须遵守客户尽职调查要求、报告可疑交易并实施基于风险的反洗钱计划。

[v7u_N001930|1930] Additionally, the legislation requires enhanced due diligence for high-risk customers, including PEPs.
ZH: 法律要求对高风险客户（包括政治敏感人物）进行强化尽职调查。

[v7u_N001931|1931] Compliance failures can result in administrative penalties or criminal sanctions.
ZH: 合规失败可能导致行政处罚或刑事制裁。

[v7u_N001932|1932] In addition to these requirements, financial institutions must conduct ongoing monitoring of customer transactions to detect unusual patterns and regularly update risk assessments to reflect emerging threats.
ZH: 金融机构必须持续监控客户交易并定期更新风险评估。

[v7u_N001933|1933] Obliged entities are also encouraged to invest in technological solutions such as artificial intelligence and machine learning to improve transaction monitoring and fraud detection.
ZH: 鼓励义务实体投资人工智能和机器学习等技术解决方案以改进交易监控和欺诈检测。

[v7u_N001934|1934] Recent updates to these legislations include strengthening digital asset regulations, increasing oversight of money transfer service providers, and enhancing transparency in beneficial ownership reporting.
ZH: 日本近期立法更新包括加强数字资产监管、增加对汇款服务提供商的监管以及提高受益所有人透明度。

[v7u_N001935|1935] Japan is also focusing on international cooperation, working closely with FATF and other global regulators to improve its AML/CFT measures.
ZH: 日本注重国际合作，与FATF及其他全球监管机构密切合作以改进其反洗钱/反恐怖融资措施。

[v7u_N001936|1936] Additionally, the Japanese government established an Inter-Ministerial Council for AML/CFT/CPF Policy to coordinate and advance the government’s AML/CFT and weapons proliferation efforts. In April 2024, the Council formulated a National AML/CFT/CPF Action Plan and monitors progress on the Action Plan as part of its work.
ZH: 日本政府设立了反洗钱/反恐怖融资/防扩散融资部际委员会，并于2024年4月制定了国家行动计划。
```

allowed_unit_ids:

```json
[
  "v7u_N001927",
  "v7u_N001928",
  "v7u_N001929",
  "v7u_N001930",
  "v7u_N001931",
  "v7u_N001932",
  "v7u_N001933",
  "v7u_N001934",
  "v7u_N001935",
  "v7u_N001936"
]
```

## S2 Process IR

```json
{
  "section_id": "CH24-S16",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "如何对高风险客户实施强化尽职调查？",
      "title": "依据法律要求对高风险客户（包括PEPs）进行强化尽职调查",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "高风险客户（包括PEPs）",
          "evidence_unit_ids": [
            "v7u_N001930"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "进行强化尽职调查",
          "evidence_unit_ids": [
            "v7u_N001930"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "standard",
          "label": "日本AML/CFT法律要求",
          "evidence_unit_ids": [
            "v7u_N001930"
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
          "condition": "客户为高风险客户",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001930"
          ],
          "source_quote": "the legislation requires enhanced due diligence for high-risk customers, including PEPs."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e003",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001930"
          ],
          "source_quote": "the legislation requires enhanced due diligence for high-risk customers, including PEPs."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_gap_ch24_s16_obligations"
      ],
      "focal_question": "金融机构和DNFBPs必须履行哪些基本AML/CFT义务？",
      "title": "日本法律要求的金融机构和DNFBPs基本AML义务",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e201",
          "role": "standard",
          "label": "日本AML/CFT法律",
          "evidence_unit_ids": [
            "v7u_N001929"
          ],
          "modality": null
        },
        {
          "element_id": "e202",
          "role": "action",
          "label": "遵守客户尽职调查要求",
          "evidence_unit_ids": [
            "v7u_N001929"
          ],
          "modality": "required"
        },
        {
          "element_id": "e203",
          "role": "action",
          "label": "报告可疑交易",
          "evidence_unit_ids": [
            "v7u_N001929"
          ],
          "modality": "required"
        },
        {
          "element_id": "e204",
          "role": "action",
          "label": "实施基于风险的内部反洗钱计划",
          "evidence_unit_ids": [
            "v7u_N001929"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r201",
          "kind": "reference",
          "process_element_id": "e202",
          "auxiliary_element_id": "e201",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001929"
          ],
          "source_quote": "According to Japan’s AML/CFT legislation, financial institutions and DNFBPs must adhere to CDD requirements"
        },
        {
          "relation_id": "r202",
          "kind": "reference",
          "process_element_id": "e203",
          "auxiliary_element_id": "e201",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001929"
          ],
          "source_quote": "report suspicious transactions"
        },
        {
          "relation_id": "r203",
          "kind": "reference",
          "process_element_id": "e204",
          "auxiliary_element_id": "e201",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001929"
          ],
          "source_quote": "implement internal risk-based AML programs"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_gap_ch24_s16_ongoing_monitoring"
      ],
      "focal_question": "金融机构如何通过持续交易监控检测异常？",
      "title": "持续监控客户交易以检测异常模式",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e301",
          "role": "action",
          "label": "持续监控客户交易",
          "evidence_unit_ids": [
            "v7u_N001932"
          ],
          "modality": "required"
        },
        {
          "element_id": "e302",
          "role": "outcome",
          "label": "检测异常模式",
          "evidence_unit_ids": [
            "v7u_N001932"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r301",
          "kind": "produce",
          "process_element_id": "e301",
          "outcome_element_id": "e302",
          "relation_type": "component_assembles_product",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001932"
          ],
          "source_quote": "financial institutions must conduct ongoing monitoring of customer transactions to detect unusual patterns"
        }
      ],
      "split_reason": "同一候选包含持续监控与风险更新的并列独立流程，拆分为两个episode。"
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_gap_ch24_s16_ongoing_monitoring"
      ],
      "focal_question": "金融机构如何通过风险更新反映新兴威胁？",
      "title": "定期更新风险评估以反映新兴威胁",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e401",
          "role": "action",
          "label": "定期更新风险评估",
          "evidence_unit_ids": [
            "v7u_N001932"
          ],
          "modality": "required"
        },
        {
          "element_id": "e402",
          "role": "outcome",
          "label": "反映新兴威胁",
          "evidence_unit_ids": [
            "v7u_N001932"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r401",
          "kind": "produce",
          "process_element_id": "e401",
          "outcome_element_id": "e402",
          "relation_type": "component_assembles_product",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001932"
          ],
          "source_quote": "regularly update risk assessments to reflect emerging threats"
        }
      ],
      "split_reason": "同一候选包含持续监控与风险更新的并列独立流程，拆分为两个episode。"
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_gap_ch24_s16_tech_investment"
      ],
      "focal_question": "义务实体如何通过技术投资改进交易监控和欺诈检测？",
      "title": "鼓励投资技术解决方案以改进监控与检测",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e501",
          "role": "action",
          "label": "投资人工智能和机器学习等技术解决方案",
          "evidence_unit_ids": [
            "v7u_N001933"
          ],
          "modality": null
        },
        {
          "element_id": "e502",
          "role": "outcome",
          "label": "改进交易监控和欺诈检测",
          "evidence_unit_ids": [
            "v7u_N001933"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r501",
          "kind": "produce",
          "process_element_id": "e501",
          "outcome_element_id": "e502",
          "relation_type": "component_assembles_product",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001933"
          ],
          "source_quote": "Obliged entities are also encouraged to invest in technological solutions such as artificial intelligence and machine learning to improve transaction monitoring and fraud detection."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_gap_ch24_s16_inter_ministerial_council"
      ],
      "focal_question": "日本政府如何通过部际委员会制定和监控AML行动计划？",
      "title": "政府设立部际委员会制定并监控国家AML行动计划",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e601",
          "role": "action",
          "label": "日本政府设立部际委员会",
          "evidence_unit_ids": [
            "v7u_N001936"
          ],
          "modality": null
        },
        {
          "element_id": "e602",
          "role": "action",
          "label": "制定国家AML/CFT/CPF行动计划",
          "evidence_unit_ids": [
            "v7u_N001936"
          ],
          "modality": null
        },
        {
          "element_id": "e603",
          "role": "action",
          "label": "监控行动计划进展",
          "evidence_unit_ids": [
            "v7u_N001936"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r601",
          "kind": "sequence",
          "before_element_id": "e601",
          "after_element_id": "e602",
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001936"
          ],
          "source_quote": "the Japanese government established an Inter-Ministerial Council ... In April 2024, the Council formulated a National AML/CFT/CPF Action Plan"
        },
        {
          "relation_id": "r602",
          "kind": "sequence",
          "before_element_id": "e602",
          "after_element_id": "e603",
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001936"
          ],
          "source_quote": "the Council formulated a National AML/CFT/CPF Action Plan and monitors progress on the Action Plan as part of its work."
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
      "reason": "该候选描述了法律要求对高风险客户进行EDD，构成一条程序性关系，已建模。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "合规失败可能导致处罚，属于法律后果描述，并非机构业务处理流程，不包含业务判断或行动，故排除。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s16_obligations",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选承接了法律强制要求金融机构和DNFBPs履行CDD、报告和实施计划等义务，构成程序性内容，已建模。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s16_ongoing_monitoring",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003",
        "ep_004"
      ],
      "reason": "该候选包含持续监控和风险更新两个独立义务，各自支持程序性关系，拆分为两个episode。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s16_tech_investment",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选承接了鼓励投资技术解决方案以改进监控的程序性建议，已建模。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s16_inter_ministerial_council",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "该候选描述了政府设立委员会、制定计划并监控进展的管理过程，构成程序性流程，已建模。"
    }
  ],
  "skip_reason": null
}
```
