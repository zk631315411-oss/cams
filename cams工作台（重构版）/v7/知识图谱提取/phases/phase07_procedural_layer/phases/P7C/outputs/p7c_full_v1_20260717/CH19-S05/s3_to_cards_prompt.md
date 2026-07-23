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

section_id: `CH19-S05`

section_title: `Financial Action Task Force > FATF 11 Immediate Outcomes`

section_text_with_unit_anchors:

```text
[v7u_N001382|1382] Mutual evaluation reports of member jurisdictions focus on two areas: technical compliance with the FATF Recommendations and the effectiveness of the jurisdiction's overall program.
ZH: FATF互评估报告关注技术合规性和反洗钱体系有效性两大领域。

[v7u_N001383|1383] FATF measures and rates effectiveness using 11 Immediate Outcomes (IOs), with each IO receiving an effectiveness rating of low, moderate, substantial, or high.
ZH: FATF使用11项直接目标（IO）评估有效性，评级分为低、中、显著、高。

[v7u_N001384|1384] For jurisdictions that FATF rates as having low or moderate effectiveness in IOs, FATF provides key recommended actions and tracks the jurisdiction's progress in meeting the recommendations.
ZH: FATF对有效性评级为低或中的司法管辖区提出关键建议并跟踪改进进展。

[v7u_N001385|1385] FATF’s IOs are not meant to be a checklist, but rather a starting point to assist assessors in determining the effectiveness of a jurisdiction's AML/CFT framework. FATF expects assessors to use their judgment and experience in determining their ratings.
ZH: FATF的直接目标并非检查清单，而是评估人员判断反洗钱/反恐怖融资框架有效性的起点。

[v7u_N001386|1386] The table below lists the area of focus and specific outcomes associated with each of the 11 IOs:
ZH: 表格列出了11项直接目标的重点领域和具体成果。

[v7u_N001387|1387] FATF mutual evaluations are peer reviews between FATF member jurisdictions that result in thorough reports that analyze AML procedures and their effectiveness.
ZH: FATF互评估是成员国之间的同行评审，生成分析反洗钱程序及其有效性的详细报告。

[v7u_N001388|1388] A typical report provides an in-depth description and analysis of a jurisdiction’s legal and regulatory framework for preventing criminal abuse of its financial system.
ZH: 典型互评估报告深入描述和分析司法管辖区防止金融系统被犯罪滥用的法律和监管框架。

[v7u_N001389|1389] The report also includes recommendations for jurisdictions to strengthen their capabilities.
ZH: 互评估报告还包括加强司法管辖区能力的建议。

[v7u_N001390|1390] Mutual evaluations are strict, meaning each jurisdiction is only deemed compliant when it can prove the same to other FATF members.
ZH: 互评估要求严格，司法管辖区必须向其他FATF成员证明其合规才能被视为合规。

[v7u_N001391|1391] FATF mutual evaluations have two basic components. The main component is effectiveness and is the focus of an on-site visit to the assessed jurisdiction. During the visit, the assessment team collects evidence demonstrating that the jurisdiction’s measures are operational and deliver the right results.
ZH: FATF互评估有两个基本组成部分，主要部分是有效性，通过现场访问收集证据。

[v7u_N001392|1392] The second component is technical compliance.
ZH: 互评估的第二部分是技术合规性。

[v7u_N001393|1393] The assessed member must provide information on its laws and regulations to combat money laundering and the proliferation of weapons of mass destruction.
ZH: 被评估成员必须提供其打击洗钱和大规模杀伤性武器扩散的法律法规信息。

[v7u_N001394|1394] The goal of technical compliance has been the main focus of FATF.
ZH: 技术合规性曾是FATF的主要关注点。

[v7u_N001395|1395] However, numerous money laundering scandals demonstrated that technical compliance was insufficient, and the main focus was shifted to AML effectiveness.
ZH: 多起洗钱丑闻表明技术合规性不足，FATF重点转向反洗钱有效性。

[v7u_N001396|1396] Expectations about FATF mutual evaluations differ from jurisdiction to jurisdiction, based on AML and other financial crime risks.
ZH: 对FATF互评估的期望因司法管辖区而异，取决于反洗钱及其他金融犯罪风险。

[v7u_N001397|1397] The organization has developed an elaborate assessment methodology to ensure consistent, fair assessments.
ZH: FATF制定了详细的评估方法以确保评估一致、公平。

[v7u_N001398|1398] A complete mutual evaluation takes an average of 18 months.
ZH: 一次完整的互评估平均需要18个月。

[v7u_N001399|1399] The mutual evaluation process has seven stages.
ZH: 互评估流程包含七个阶段。

[v7u_N001400|1400] Getting started:
ZH: 互评估流程的第一个阶段是“开始”。

[v7u_N001401|1401] Assessor training: Training for the experts who will perform assessment
ZH: 评估员培训：为执行评估的专家提供培训

[v7u_N001402|1402] Jurisdiction training: Training for representatives of the evaluated jurisdictions
ZH: 司法管辖区培训：为被评估司法管辖区的代表提供培训

[v7u_N001403|1403] Selection of assessors: Selection of the experts that form the assessment team
ZH: 评估员遴选：选择组成评估团队的专家

[v7u_N001404|1404] Technical review: Assessment team analyzes the jurisdiction’s laws and regulations
ZH: 技术审查：评估团队分析司法管辖区的法律法规

[v7u_N001405|1405] Scoping note: Assessment team identifies areas of focus for the on-site visit
ZH: 范围界定说明：评估团队确定现场访问的重点领域

[v7u_N001406|1406] On-site visit: Assessment team travels to the jurisdiction and reviews the effectiveness of AML regulations
ZH: 现场访问：评估团队前往司法管辖区审查反洗钱法规的有效性

[v7u_N001407|1407] Draft MER: Finalize mutual evaluation report
ZH: 起草互评估报告：完成互评估报告

[v7u_N001408|1408] FATF plenary adoption:
ZH: FATF全体会议通过：互评估报告提交全体会议审议

[v7u_N001409|1409] Plenary discussion: FATF plenary discusses the findings in the report and votes on the ratings
ZH: 全体会议讨论：FATF全体会议讨论报告中的发现并对评级进行投票

[v7u_N001410|1410] Final quality review: All jurisdictions review the report before publishing
ZH: 最终质量审查：所有司法管辖区在报告发布前进行审查

[v7u_N001411|1411] Publication and follow-up: Jurisdiction addresses issues and begins strengthening its AML measures
ZH: 发布与后续行动：司法管辖区解决问题并开始加强反洗钱措施
```

allowed_unit_ids:

```json
[
  "v7u_N001382",
  "v7u_N001383",
  "v7u_N001384",
  "v7u_N001385",
  "v7u_N001386",
  "v7u_N001387",
  "v7u_N001388",
  "v7u_N001389",
  "v7u_N001390",
  "v7u_N001391",
  "v7u_N001392",
  "v7u_N001393",
  "v7u_N001394",
  "v7u_N001395",
  "v7u_N001396",
  "v7u_N001397",
  "v7u_N001398",
  "v7u_N001399",
  "v7u_N001400",
  "v7u_N001401",
  "v7u_N001402",
  "v7u_N001403",
  "v7u_N001404",
  "v7u_N001405",
  "v7u_N001406",
  "v7u_N001407",
  "v7u_N001408",
  "v7u_N001409",
  "v7u_N001410",
  "v7u_N001411"
]
```

## S2 Process IR

```json
{
  "section_id": "CH19-S05",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_gap_ch19_s05_fatf_rates_effectiveness",
        "s1c_002"
      ],
      "focal_question": "如何根据直接目标确定有效性评级？",
      "title": "使用直接目标评定有效性评级",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "FATF expects assessors to use their judgment and experience in determining ratings",
          "evidence_unit_ids": [
            "v7u_N001385"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "FATF’s IOs are a starting point to assist assessors in determining effectiveness",
          "evidence_unit_ids": [
            "v7u_N001385"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "measures and rates effectiveness using 11 Immediate Outcomes",
          "evidence_unit_ids": [
            "v7u_N001383",
            "v7u_N001385"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "each IO receiving an effectiveness rating of low, moderate, substantial, or high",
          "evidence_unit_ids": [
            "v7u_N001383"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e001",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001385"
          ],
          "source_quote": "FATF expects assessors to use their judgment and experience in determining their ratings."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001385"
          ],
          "source_quote": "FATF’s IOs are not meant to be a checklist, but rather a starting point to assist assessors in determining the effectiveness of a jurisdiction's AML/CFT framework."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001383"
          ],
          "source_quote": "FATF measures and rates effectiveness using 11 Immediate Outcomes (IOs), with each IO receiving an effectiveness rating of low, moderate, substantial, or high."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "当有效性评级为低或中时，FATF应如何应对？",
      "title": "低/中有效性评级后的建议与跟踪",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "jurisdictions that FATF rates as having low or moderate effectiveness in IOs",
          "evidence_unit_ids": [
            "v7u_N001384"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "FATF provides key recommended actions",
          "evidence_unit_ids": [
            "v7u_N001384"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "tracks the jurisdiction's progress in meeting the recommendations",
          "evidence_unit_ids": [
            "v7u_N001384"
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
          "condition": "jurisdiction is rated as having low or moderate effectiveness in IOs",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001384"
          ],
          "source_quote": "For jurisdictions that FATF rates as having low or moderate effectiveness in IOs, FATF provides key recommended actions and tracks the jurisdiction's progress in meeting the recommendations."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001384"
          ],
          "source_quote": "FATF provides key recommended actions and tracks the jurisdiction's progress in meeting the recommendations."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "司法管辖区在何种条件下被视为合规？",
      "title": "司法管辖区合规判定的条件",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "jurisdiction can prove compliance to other FATF members",
          "evidence_unit_ids": [
            "v7u_N001390"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "jurisdiction is only deemed compliant",
          "evidence_unit_ids": [
            "v7u_N001390"
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
          "condition": "jurisdiction can prove compliance to other FATF members",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001390"
          ],
          "source_quote": "Mutual evaluations are strict, meaning each jurisdiction is only deemed compliant when it can prove the same to other FATF members."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "评估团队在技术审查阶段做什么？",
      "title": "技术审查：分析法律法规",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "assessment team analyzes the jurisdiction’s laws and regulations",
          "evidence_unit_ids": [
            "v7u_N001404"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "input",
          "label": "jurisdiction’s laws and regulations",
          "evidence_unit_ids": [
            "v7u_N001404"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e001",
          "auxiliary_element_id": "e002",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001404"
          ],
          "source_quote": "Technical review: Assessment team analyzes the jurisdiction’s laws and regulations"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "评估团队如何确定现场访问的重点？",
      "title": "范围界定：识别现场访问重点领域",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "assessment team identifies areas of focus for the on-site visit",
          "evidence_unit_ids": [
            "v7u_N001405"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "areas of focus for the on-site visit",
          "evidence_unit_ids": [
            "v7u_N001405"
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
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001405"
          ],
          "source_quote": "Scoping note: Assessment team identifies areas of focus for the on-site visit"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_004",
        "s1c_007"
      ],
      "focal_question": "评估团队在现场访问期间如何评估有效性？",
      "title": "现场访问：审查有效性并收集证据",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "On-site visit",
          "evidence_unit_ids": [
            "v7u_N001406"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "assessment team travels to the jurisdiction",
          "evidence_unit_ids": [
            "v7u_N001406"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "assessment team reviews the effectiveness of AML regulations",
          "evidence_unit_ids": [
            "v7u_N001406"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "assessment team collects evidence demonstrating that the jurisdiction’s measures are operational and deliver the right results",
          "evidence_unit_ids": [
            "v7u_N001391"
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
            "v7u_N001406"
          ],
          "source_quote": "On-site visit: Assessment team travels to the jurisdiction and reviews the effectiveness of AML regulations"
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001406"
          ],
          "source_quote": "travels to the jurisdiction and reviews the effectiveness of AML regulations"
        },
        {
          "relation_id": "r003",
          "kind": "sequence",
          "before_element_id": "e003",
          "after_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001391"
          ],
          "source_quote": "During the visit, the assessment team collects evidence demonstrating that the jurisdiction’s measures are operational and deliver the right results."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_008"
      ],
      "focal_question": "评估报告如何定稿？",
      "title": "起草MER：完成互评估报告",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "finalize mutual evaluation report",
          "evidence_unit_ids": [
            "v7u_N001407"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "mutual evaluation report",
          "evidence_unit_ids": [
            "v7u_N001407"
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
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001407"
          ],
          "source_quote": "Draft MER: Finalize mutual evaluation report"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_008",
      "source_candidate_ids": [
        "s1c_009"
      ],
      "focal_question": "FATF全体会议如何决定评级？",
      "title": "全体会议讨论与投票评定评级",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "FATF plenary discussion",
          "evidence_unit_ids": [
            "v7u_N001409"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "input",
          "label": "findings in the report",
          "evidence_unit_ids": [
            "v7u_N001409"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "FATF plenary discusses the findings",
          "evidence_unit_ids": [
            "v7u_N001409"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "votes on the ratings",
          "evidence_unit_ids": [
            "v7u_N001409"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "ratings",
          "evidence_unit_ids": [
            "v7u_N001409"
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
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001409"
          ],
          "source_quote": "Plenary discussion: FATF plenary discusses the findings in the report and votes on the ratings"
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001409"
          ],
          "source_quote": "discusses the findings in the report"
        },
        {
          "relation_id": "r003",
          "kind": "sequence",
          "before_element_id": "e003",
          "after_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001409"
          ],
          "source_quote": "discusses the findings in the report and votes on the ratings"
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e004",
          "outcome_element_id": "e005",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001409"
          ],
          "source_quote": "votes on the ratings"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_009",
      "source_candidate_ids": [
        "s1c_010"
      ],
      "focal_question": "报告发布前的审查是如何进行的？",
      "title": "最终质量审查：所有司法管辖区在发布前审查报告",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "before publishing",
          "evidence_unit_ids": [
            "v7u_N001410"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "all jurisdictions review the report",
          "evidence_unit_ids": [
            "v7u_N001410"
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
          "condition": "before publishing",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001410"
          ],
          "source_quote": "Final quality review: All jurisdictions review the report before publishing"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_010",
      "source_candidate_ids": [
        "s1c_011"
      ],
      "focal_question": "报告发布后司法管辖区应采取什么行动？",
      "title": "发布与后续：司法管辖区处理问题并加强措施",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "publication and follow-up",
          "evidence_unit_ids": [
            "v7u_N001411"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "jurisdiction addresses issues",
          "evidence_unit_ids": [
            "v7u_N001411"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "begins strengthening its AML measures",
          "evidence_unit_ids": [
            "v7u_N001411"
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
            "v7u_N001411"
          ],
          "source_quote": "Publication and follow-up: Jurisdiction addresses issues and begins strengthening its AML measures"
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001411"
          ],
          "source_quote": "addresses issues and begins strengthening its AML measures"
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
      "reason": "描述了当IOs有效性评级为低或中时，FATF提供建议和跟踪进展的动作，独立构成触发-响应流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "描述了评估者以直接目标为起点、运用判断确定有效性评级的过程，为评级episode提供核心动作和标准。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "描述了司法管辖区只有向其他成员证明合规才被视为合规的条件判断，构成独立的判定流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "描述了现场访问期间评估团队收集证据的动作，为现场访问episode提供关键证据收集步骤。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "描述了技术审查阶段评估团队分析法律法规的动作，独立构成一个审查步骤。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "描述了范围界定阶段评估团队识别现场访问重点领域的动作，独立产出重点领域。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "描述了现场访问阶段评估团队前往并审查有效性的动作，为现场访问episode提供核心审查动作。"
    },
    {
      "candidate_id": "s1c_008",
      "disposition": "mapped",
      "episode_ids": [
        "ep_007"
      ],
      "reason": "描述了起草MER阶段最终确定互评估报告的动作，独立产出报告。"
    },
    {
      "candidate_id": "s1c_009",
      "disposition": "mapped",
      "episode_ids": [
        "ep_008"
      ],
      "reason": "描述了全体会议讨论发现并投票评级的动作，输出评级结果。"
    },
    {
      "candidate_id": "s1c_010",
      "disposition": "mapped",
      "episode_ids": [
        "ep_009"
      ],
      "reason": "描述了最终质量审查阶段所有司法管辖区在发布前审查报告的动作。"
    },
    {
      "candidate_id": "s1c_011",
      "disposition": "mapped",
      "episode_ids": [
        "ep_010"
      ],
      "reason": "描述了发布与后续阶段司法管辖区处理问题和加强措施的动作。"
    },
    {
      "candidate_id": "s1c_gap_ch19_s05_fatf_rates_effectiveness",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "描述了FATF使用11项直接目标衡量和评级有效性的程序，为评级episode提供核心动作和评级结果。"
    }
  ],
  "skip_reason": null
}
```
