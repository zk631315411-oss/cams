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

section_id: `CH26-S07`

section_title: `Other laws and regulations that impact organizations > AI regulations around the world`

section_text_with_unit_anchors:

```text
[v7u_N002091|2091] In 2025, the US issued Executive Order 14179, , which directs government agencies to encourage innovation rather than regulation, rescinding a previous blueprint that set forth five principles for AI governance.
ZH: 美国2025年行政令14179鼓励AI创新而非监管，撤销先前AI治理蓝图

[v7u_N002092|2092] The EU AI Act and other complementary laws, such as the EU Digital Services Act, form part of the EU’s digital strategy to regulate the digital landscape and ensure the safe and ethical use of technology.
ZH: 欧盟AI法案与数字服务法等构成数字战略，确保技术安全与道德使用

[v7u_N002093|2093] The first of its kind, the EU AI Act specifically targets the development and deployment of AI models and systems within the EU.
ZH: 欧盟AI法案专门针对AI模型和系统在欧盟内的开发与部署

[v7u_N002094|2094] It seeks to achieve this by categorizing AI models and systems into varying levels of risk and imposing corresponding regulatory requirements.
ZH: 欧盟AI法案按风险等级对AI模型和系统分类并施加相应监管要求

[v7u_N002095|2095] Emphasizing human oversight, transparency, nondiscrimination, and accountability, this Act applies to AI systems and tools in service in the EU regardless of where the deployer or provider is located.
ZH: 欧盟AI法案强调人类监督、透明度、非歧视和问责，适用于在欧盟使用的AI系统

[v7u_N002096|2096] The UK has opted for a principles-based approach for AI, although the UK has proposed bills that would codify AI principles if passed and signed into law.
ZH: 英国对AI采取基于原则的方法，已提出法案拟将AI原则成文化

[v7u_N002097|2097] In 2023, the UK government issued a white paper outlining general principles but left flexibility on how they would apply the principles in specific sectors.
ZH: 英国政府2023年发布AI白皮书，概述一般原则但保留部门灵活性

[v7u_N002098|2098] Regarding other jurisdictions, AI approaches vary.
ZH: 各司法管辖区对AI的监管方法各不相同

[v7u_N002099|2099] China has AI regulations that align with its national development plan, including the deep synthesis provisions that focus on the use of AI to create “deep fake” content.
ZH: 中国AI法规与国家发展计划一致，包括针对深度合成（deep fake）的规定

[v7u_N002100|2100] Hong Kong relies on sector-specific guidelines with a particular focus on ethical and privacy concerns. Its principles are laid out in its 2024 Ethical Artificial Intelligence Framework. This guideline is issued by the Hong Kong Monetary Authority and applies only to banks, not all financial institutions.
ZH: 香港依赖行业特定指南，侧重伦理与隐私，2024年《伦理人工智能框架》仅适用于银行

[v7u_N002101|2101] Japan relies on existing sector-specific laws together with AI governance guidelines.
ZH: 日本依赖行业特定法律和AI治理指南

[v7u_N002102|2102] As outlined in its AI Strategy 2022, Japan’s AI initiatives emphasize safe and human-centric innovation, focusing on industrial transformation, ethical AI governance, and international collaboration.
ZH: 日本AI战略2022强调安全、以人为本的创新

[v7u_N002103|2103] In 2025, the government’s AI Policy Study Group issued an interim report that emphasized the role of business rather than government in the governance of AI.
ZH: 日本2025年AI政策研究组中期报告强调企业主导AI治理

[v7u_N002104|2104] Singapore’s AI initiatives focus on developing a trusted, inclusive, and progressive AI ecosystem, guided by its National AI Strategy 2.0 to drive innovation, safeguard ethics, and boost economic transformation.
ZH: 新加坡AI倡议聚焦可信、包容、进步的AI生态系统
```

allowed_unit_ids:

```json
[
  "v7u_N002091",
  "v7u_N002092",
  "v7u_N002093",
  "v7u_N002094",
  "v7u_N002095",
  "v7u_N002096",
  "v7u_N002097",
  "v7u_N002098",
  "v7u_N002099",
  "v7u_N002100",
  "v7u_N002101",
  "v7u_N002102",
  "v7u_N002103",
  "v7u_N002104"
]
```

## S2 Process IR

```json
{
  "section_id": "CH26-S07",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "欧盟AI法案如何实现安全与道德使用？",
      "title": "通过风险分级与监管要求实现安全与道德使用",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "categorizing AI models and systems into varying levels of risk and imposing corresponding regulatory requirements",
          "evidence_unit_ids": [
            "v7u_N002094"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "achieve safe and ethical use of technology",
          "evidence_unit_ids": [
            "v7u_N002094"
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
            "v7u_N002094"
          ],
          "source_quote": "It seeks to achieve this by categorizing AI models and systems into varying levels of risk and imposing corresponding regulatory requirements."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_gap_ch26_s07_us_exec_order"
      ],
      "focal_question": "美国2025年行政令14179如何改变AI治理方向？",
      "title": "美国签发行政令鼓励创新并撤销先前AI治理蓝图",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "the US issued Executive Order 14179",
          "evidence_unit_ids": [
            "v7u_N002091"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "government agencies are directed to encourage innovation rather than regulation",
          "evidence_unit_ids": [
            "v7u_N002091"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "previous AI governance blueprint is rescinded",
          "evidence_unit_ids": [
            "v7u_N002091"
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
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002091"
          ],
          "source_quote": "directs government agencies to encourage innovation rather than regulation"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002091"
          ],
          "source_quote": "rescinding a previous blueprint that set forth five principles for AI governance"
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
      "reason": "该候选描述了欧盟AI法案通过风险分级和施加监管要求来实现安全与道德使用的具体程序，构成独立流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选仅静态陈述欧盟AI法案的适用范围，未描述任何业务处理、判断或行动过程，属于非程序性知识。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选仅静态陈述香港伦理AI框架的适用范围（仅限银行），未描述业务判断或动态过程，属于非程序性事实。"
    },
    {
      "candidate_id": "s1c_gap_ch26_s07_us_exec_order",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了美国发布行政令指示政府机构鼓励创新并撤销先前AI治理蓝图的行政行动，包含明确的动作和结果。"
    },
    {
      "candidate_id": "s1c_gap_ch26_s07_uk_bill_codify",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选描述英国提出法案及附条件的结果，但未体现机构业务判断或流程，仅为立法动态介绍，不构成程序性内容。"
    }
  ],
  "skip_reason": null
}
```
