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

section_id: `CH19-S06`

section_title: `Financial Action Task Force > FATF high-risk and noncooperative jurisdictions`

section_text_with_unit_anchors:

```text
[v7u_N001412|1412] FATF identifies high-risk and noncooperative jurisdictions through a comprehensive review process. FATF’s International Cooperation Review Group oversees this process and assesses a jurisdiction's AML/CFT measures to identify threats, vulnerabilities, and risks.
ZH: FATF通过全面审查流程识别高风险和不合作司法管辖区

[v7u_N001413|1413] FATF reviews jurisdictions for many reasons it deems indicative of noncooperation. Specifically, FATF will review a jurisdiction when it:
ZH: FATF因多种原因审查司法管辖区，具体情形包括

[v7u_N001414|1414] Does not participate in an FSRB.
ZH: 不参与区域性反洗钱组织

[v7u_N001415|1415] Delays or does not allow an FSRB to publish mutual evaluation results.
ZH: 延迟或不允许区域性反洗钱组织发布互评估结果

[v7u_N001416|1416] Is nominated by a FATF member or an FSRB that identifies money laundering, terrorist financing, or proliferation financing risks or threats.
ZH: 被FATF成员或区域性反洗钱组织提名存在洗钱、恐怖融资或扩散融资风险

[v7u_N001417|1417] Achieves poor results in its mutual evaluation, such as:
ZH: 互评估结果不佳，例如

[v7u_N001418|1418] Having 20 or more noncompliant or partially compliant ratings for technical compliance.
ZH: 技术合规性方面有20项或更多不合规或部分合规评级

[v7u_N001419|1419] Receiving ratings of noncompliant or partially compliant on three or more of Recommendations 3, 5, 6, 10, 11, and 20.
ZH: 建议3、5、6、10、11和20中有三项或更多被评为不合规或部分合规

[v7u_N001420|1420] Having a low or moderate level of effectiveness for 9 or more of the 11 IOs, with a minimum of two lows.
ZH: 11项立即成果中有9项或更多有效性评级为低或中等，且至少两项为低

[v7u_N001421|1421] Having a low level of effectiveness for 6 or more of the 11 IOs.
ZH: FATF 11项有效性指标中6项以上评级低的司法管辖区

[v7u_N001422|1422] FATF provides 25 criteria that help identify relevant detrimental rules and practices that are inconsistent with the 40 Recommendations. The criteria are categorized into four broad areas:
ZH: FATF 25条标准分为四大类，用于识别与40项建议不一致的规则和做法

[v7u_N001423|1423] Loopholes in financial regulations
ZH: 金融监管漏洞是FATF识别的有害规则之一

[v7u_N001424|1424] Obstacles raised by other regulatory requirements
ZH: 其他监管要求造成的障碍是FATF识别的有害规则之一

[v7u_N001425|1425] Obstacles to international cooperation
ZH: 国际合作障碍是FATF识别的有害规则之一

[v7u_N001426|1426] Inadequate resources for preventing and detecting money laundering activities
ZH: 预防和检测洗钱活动的资源不足是FATF识别的有害规则之一

[v7u_N001427|1427] Based on these criteria, FATF officially identifies noncooperative jurisdictions and territories in two public documents it publishes three times a year.
ZH: FATF根据25条标准每年三次发布不合作司法管辖区名单

[v7u_N001428|1428] The list is called the "grey list." It identifies jurisdictions with strategic deficiencies in their AML/CFT systems that are actively working with FATF to address these issues.
ZH: FATF灰名单指在反洗钱/反恐怖融资体系存在战略缺陷但正积极整改的司法管辖区

[v7u_N001429|1429] The list is called the "black list." It identifies jurisdictions with significant AML/CFT deficiencies, prompting all FATF members to apply enhanced due diligence (EDD) and potentially take countermeasures against them.
ZH: FATF黑名单指反洗钱/反恐怖融资缺陷严重，需采取强化尽职调查和反制措施的司法管辖区
```

allowed_unit_ids:

```json
[
  "v7u_N001412",
  "v7u_N001413",
  "v7u_N001414",
  "v7u_N001415",
  "v7u_N001416",
  "v7u_N001417",
  "v7u_N001418",
  "v7u_N001419",
  "v7u_N001420",
  "v7u_N001421",
  "v7u_N001422",
  "v7u_N001423",
  "v7u_N001424",
  "v7u_N001425",
  "v7u_N001426",
  "v7u_N001427",
  "v7u_N001428",
  "v7u_N001429"
]
```

## S2 Process IR

```json
{
  "section_id": "CH19-S06",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "FATF如何基于不合作迹象审查并识别高风险和不合作司法管辖区？",
      "title": "基于不合作迹象启动审查并识别高风险及不合作司法管辖区",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "FATF conducts a comprehensive review (ICRG assesses AML/CFT measures to identify threats, vulnerabilities, and risks)",
          "evidence_unit_ids": [
            "v7u_N001412"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "context",
          "label": "Jurisdiction does not participate in an FSRB",
          "evidence_unit_ids": [
            "v7u_N001414"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "context",
          "label": "Jurisdiction delays or does not allow an FSRB to publish mutual evaluation results",
          "evidence_unit_ids": [
            "v7u_N001415"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "context",
          "label": "Jurisdiction is nominated by a FATF member or an FSRB that identifies money laundering, terrorist financing, or proliferation financing risks or threats",
          "evidence_unit_ids": [
            "v7u_N001416"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "context",
          "label": "Jurisdiction achieves poor mutual evaluation results: 20 or more noncompliant or partially compliant ratings for technical compliance",
          "evidence_unit_ids": [
            "v7u_N001417",
            "v7u_N001418"
          ],
          "modality": null
        },
        {
          "element_id": "e006",
          "role": "context",
          "label": "Jurisdiction achieves poor mutual evaluation results: ratings of noncompliant or partially compliant on three or more of Recommendations 3, 5, 6, 10, 11, and 20",
          "evidence_unit_ids": [
            "v7u_N001417",
            "v7u_N001419"
          ],
          "modality": null
        },
        {
          "element_id": "e007",
          "role": "context",
          "label": "Jurisdiction achieves poor mutual evaluation results: low or moderate level of effectiveness for 9 or more of the 11 IOs, with a minimum of two lows",
          "evidence_unit_ids": [
            "v7u_N001417",
            "v7u_N001420"
          ],
          "modality": null
        },
        {
          "element_id": "e008",
          "role": "context",
          "label": "Jurisdiction achieves poor mutual evaluation results: low level of effectiveness for 6 or more of the 11 IOs",
          "evidence_unit_ids": [
            "v7u_N001417",
            "v7u_N001421"
          ],
          "modality": null
        },
        {
          "element_id": "e009",
          "role": "outcome",
          "label": "FATF identifies high-risk and noncooperative jurisdictions",
          "evidence_unit_ids": [
            "v7u_N001412"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e002",
          "process_element_id": "e001",
          "condition": "Jurisdiction does not participate in an FSRB",
          "relation_type": "clue_supports_identification",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001413",
            "v7u_N001414"
          ],
          "source_quote": "FATF reviews jurisdictions for many reasons it deems indicative of noncooperation. Specifically, FATF will review a jurisdiction when it: Does not participate in an FSRB."
        },
        {
          "relation_id": "r002",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e003",
          "process_element_id": "e001",
          "condition": "Jurisdiction delays or does not allow an FSRB to publish mutual evaluation results",
          "relation_type": "clue_supports_identification",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001413",
            "v7u_N001415"
          ],
          "source_quote": "FATF reviews jurisdictions for many reasons it deems indicative of noncooperation. Specifically, FATF will review a jurisdiction when it: Delays or does not allow an FSRB to publish mutual evaluation results."
        },
        {
          "relation_id": "r003",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e004",
          "process_element_id": "e001",
          "condition": "Jurisdiction is nominated by a FATF member or an FSRB that identifies money laundering, terrorist financing, or proliferation financing risks or threats",
          "relation_type": "clue_supports_identification",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001413",
            "v7u_N001416"
          ],
          "source_quote": "FATF reviews jurisdictions for many reasons it deems indicative of noncooperation. Specifically, FATF will review a jurisdiction when it: Is nominated by a FATF member or an FSRB that identifies money laundering, terrorist financing, or proliferation financing risks or threats."
        },
        {
          "relation_id": "r004",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e005",
          "process_element_id": "e001",
          "condition": "Jurisdiction has 20 or more noncompliant or partially compliant ratings for technical compliance",
          "relation_type": "clue_supports_identification",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001413",
            "v7u_N001417",
            "v7u_N001418"
          ],
          "source_quote": "FATF reviews jurisdictions for many reasons it deems indicative of noncooperation. Specifically, FATF will review a jurisdiction when it: Achieves poor results in its mutual evaluation, such as: Having 20 or more noncompliant or partially compliant ratings for technical compliance."
        },
        {
          "relation_id": "r005",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e006",
          "process_element_id": "e001",
          "condition": "Jurisdiction receives ratings of noncompliant or partially compliant on three or more of Recommendations 3, 5, 6, 10, 11, and 20",
          "relation_type": "clue_supports_identification",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001413",
            "v7u_N001417",
            "v7u_N001419"
          ],
          "source_quote": "FATF reviews jurisdictions for many reasons it deems indicative of noncooperation. Specifically, FATF will review a jurisdiction when it: Achieves poor results in its mutual evaluation, such as: Receiving ratings of noncompliant or partially compliant on three or more of Recommendations 3, 5, 6, 10, 11, and 20."
        },
        {
          "relation_id": "r006",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e007",
          "process_element_id": "e001",
          "condition": "Jurisdiction has a low or moderate level of effectiveness for 9 or more of the 11 IOs, with a minimum of two lows",
          "relation_type": "clue_supports_identification",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001413",
            "v7u_N001417",
            "v7u_N001420"
          ],
          "source_quote": "FATF reviews jurisdictions for many reasons it deems indicative of noncooperation. Specifically, FATF will review a jurisdiction when it: Achieves poor results in its mutual evaluation, such as: Having a low or moderate level of effectiveness for 9 or more of the 11 IOs, with a minimum of two lows."
        },
        {
          "relation_id": "r007",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e008",
          "process_element_id": "e001",
          "condition": "Jurisdiction has a low level of effectiveness for 6 or more of the 11 IOs",
          "relation_type": "clue_supports_identification",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001413",
            "v7u_N001417",
            "v7u_N001421"
          ],
          "source_quote": "FATF reviews jurisdictions for many reasons it deems indicative of noncooperation. Specifically, FATF will review a jurisdiction when it: Achieves poor results in its mutual evaluation, such as: Having a low level of effectiveness for 6 or more of the 11 IOs."
        },
        {
          "relation_id": "r008",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e009",
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001412"
          ],
          "source_quote": "FATF identifies high-risk and noncooperative jurisdictions through a comprehensive review process. FATF’s International Cooperation Review Group oversees this process and assesses a jurisdiction's AML/CFT measures to identify threats, vulnerabilities, and risks."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002",
        "s1c_003"
      ],
      "focal_question": "FATF如何基于25条标准将非合作司法管辖区分入灰名单与黑名单并触发成员行动？",
      "title": "基于25条标准发布灰名单与黑名单并触发EDD及反制措施",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "25 criteria for identifying detrimental rules and practices inconsistent with the 40 Recommendations (categorized into four areas: loopholes in financial regulations, obstacles raised by other regulatory requirements, obstacles to international cooperation, inadequate resources for preventing and detecting money laundering activities)",
          "evidence_unit_ids": [
            "v7u_N001422",
            "v7u_N001423",
            "v7u_N001424",
            "v7u_N001425",
            "v7u_N001426"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "FATF classifies noncooperative jurisdictions into grey or black list based on the criteria",
          "evidence_unit_ids": [
            "v7u_N001427"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "Grey list: identifies jurisdictions with strategic deficiencies in AML/CFT systems that are actively working with FATF to address these issues",
          "evidence_unit_ids": [
            "v7u_N001428"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "Black list: identifies jurisdictions with significant AML/CFT deficiencies",
          "evidence_unit_ids": [
            "v7u_N001429"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "action",
          "label": "FATF members apply enhanced due diligence (EDD) and potentially take countermeasures against black-listed jurisdictions",
          "evidence_unit_ids": [
            "v7u_N001429"
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
            "v7u_N001422",
            "v7u_N001427"
          ],
          "source_quote": "Based on these criteria, FATF officially identifies noncooperative jurisdictions and territories in two public documents it publishes three times a year."
        },
        {
          "relation_id": "r002",
          "kind": "branch",
          "decision_element_id": "e002",
          "target_element_id": "e003",
          "condition": "jurisdiction has strategic deficiencies but is actively working with FATF",
          "relation_type": "branch_condition_routes_path",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001427",
            "v7u_N001428"
          ],
          "source_quote": "The list is called the \"grey list.\" It identifies jurisdictions with strategic deficiencies in their AML/CFT systems that are actively working with FATF to address these issues."
        },
        {
          "relation_id": "r003",
          "kind": "branch",
          "decision_element_id": "e002",
          "target_element_id": "e004",
          "condition": "jurisdiction has significant AML/CFT deficiencies",
          "relation_type": "branch_condition_routes_path",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001427",
            "v7u_N001429"
          ],
          "source_quote": "The list is called the \"black list.\" It identifies jurisdictions with significant AML/CFT deficiencies, prompting all FATF members to apply enhanced due diligence (EDD) and potentially take countermeasures against them."
        },
        {
          "relation_id": "r004",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e004",
          "process_element_id": "e005",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001429"
          ],
          "source_quote": "prompting all FATF members to apply enhanced due diligence (EDD) and potentially take countermeasures against them."
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
      "reason": "该候选描述了FATF基于多种不合作迹象启动审查并识别高风险和不合作司法管辖区的程序性流程，提供了触发条件、审查动作和识别结果。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "support_only",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选提供25条标准及其分类，自身不构成流程，但为ep_002的分类决策提供必要的标准依据。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了基于标准发布灰名单和黑名单并触发成员采取EDD和反制措施的流程，提供了决策分支、结果和后续行动。"
    }
  ],
  "skip_reason": null
}
```
