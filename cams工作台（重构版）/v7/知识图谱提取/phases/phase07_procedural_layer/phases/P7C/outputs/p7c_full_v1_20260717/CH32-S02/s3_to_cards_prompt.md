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

section_id: `CH32-S02`

section_title: `Cooperation involving the private sector > Case study: AUSTRAC Fintel Alliance investigation`

section_text_with_unit_anchors:

```text
[v7u_N002313|2313] AUSTRAC, the Australian FIU and AML regulator, established the Fintel Alliance as a public-private partnership in 2017. Its goals are to increase the financial sector’s resilience to criminal exploitation and support law enforcement investigations.
ZH: 澳大利亚AUSTRAC于2017年建立Fintel Alliance公私合作伙伴关系，旨在增强金融部门抵御犯罪利用的能力并支持执法调查。

[v7u_N002314|2314] The Fintel Alliance includes major banks, remittance service providers, and gambling operators, as well as law enforcement and security agencies from Australia and overseas. Working together, the Fintel Alliance develops shared intelligence and delivers innovative solutions to detect, disrupt, and prevent serious crime and national security matters.
ZH: Fintel Alliance包括主要银行、汇款服务商、赌博运营商以及国内外执法和安全机构，共同开发共享情报并提供创新解决方案。

[v7u_N002315|2315] In 2024, the Fintel Alliance supported one of the most complex law enforcement investigations in Australian history.
ZH: 2024年，Fintel Alliance支持了澳大利亚历史上最复杂的执法调查之一。

[v7u_N002316|2316] The Australian Federal Police (AFP) led the investigation into seven members of an alleged money laundering syndicate.
ZH: 澳大利亚联邦警察领导了对一个涉嫌洗钱团伙七名成员的调查。

[v7u_N002317|2317] The syndicate operated a prominent, multi-billion-dollar registered remittance business in Australia.
ZH: 该团伙在澳大利亚经营一家知名的、价值数十亿美元的注册汇款业务。

[v7u_N002318|2318] The AFP alleged that in addition to providing remittance services for law-abiding customers, the business offered a system for organized criminals to covertly transfer crime proceeds across borders.
ZH: 警方指控该业务为有组织犯罪分子提供秘密跨境转移犯罪收益的系统。

[v7u_N002319|2319] The AFP accused the syndicate members of coaching criminal customers in creating fake business paperwork to launder at least AU$229 million in the previous three years.
ZH: 警方指控团伙成员指导犯罪客户伪造商业文件，在过去三年中洗钱至少2.29亿澳元。

[v7u_N002320|2320] The Fintel Alliance and private industry partners provided collaborative financial analysis to support this case.
ZH: Fintel Alliance和私营行业合作伙伴为此案提供了协作性金融分析支持。

[v7u_N002321|2321] They tracked transactions across international borders and digital environments to identify suspicious transactions linked to crime.
ZH: AUSTRAC Fintel Alliance追踪跨境和数字环境中的可疑交易

[v7u_N002322|2322] Their analysis enabled the AFP to fully identify and comprehensively dismantle the transnational syndicate’s financial structures.
ZH: 分析使AFP能够全面识别并瓦解跨国犯罪集团的金融结构

[v7u_N002323|2323] The AFP filed charges and obtained restraint orders over a significant value of assets in connection with the alleged offenses. AUSTRAC took regulatory action against one digital currency exchange and six remittance businesses associated with the charged individuals.
ZH: AFP提起指控并获取资产限制令，AUSTRAC对相关交易所和汇款机构采取监管行动

[v7u_N002324|2324] The outcome of this case highlights the combined strength of AUSTRAC’s financial intelligence expertise, regulatory authority, and strategic partnership with law enforcement.
ZH: 该案例展示了AUSTRAC金融情报、监管权力与执法战略合作的综合力量
```

allowed_unit_ids:

```json
[
  "v7u_N002313",
  "v7u_N002314",
  "v7u_N002315",
  "v7u_N002316",
  "v7u_N002317",
  "v7u_N002318",
  "v7u_N002319",
  "v7u_N002320",
  "v7u_N002321",
  "v7u_N002322",
  "v7u_N002323",
  "v7u_N002324"
]
```

## S2 Process IR

```json
{
  "section_id": "CH32-S02",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001",
        "s1c_002",
        "s1c_gap_ch32_s02_afp_investigation_findings"
      ],
      "focal_question": "Fintel Alliance 如何支持 AFP 调查洗钱团伙并促成后续执法行动",
      "title": "Fintel Alliance 支持 AFP 调查洗钱团伙及后续执法监管行动",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "AFP 在 Fintel Alliance 的支持下，通过协作金融分析和交易追踪，调查洗钱团伙，识别可疑交易",
          "evidence_unit_ids": [
            "v7u_N002316",
            "v7u_N002320",
            "v7u_N002321"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "调查发现洗钱手法：业务提供秘密跨境转移系统，指导犯罪客户伪造文件，洗钱至少 2.29 亿澳元",
          "evidence_unit_ids": [
            "v7u_N002318",
            "v7u_N002319"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "分析使 AFP 能全面识别并瓦解跨国犯罪集团的金融结构",
          "evidence_unit_ids": [
            "v7u_N002322"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "AFP 提起指控并获取资产限制令，AUSTRAC 对相关的数字货币交易所和汇款机构采取监管行动",
          "evidence_unit_ids": [
            "v7u_N002323"
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
            "v7u_N002318",
            "v7u_N002319"
          ],
          "source_quote": "The AFP alleged that in addition to providing remittance services for law-abiding customers, the business offered a system for organized criminals to covertly transfer crime proceeds across borders. / The AFP accused the syndicate members of coaching criminal customers in creating fake business paperwork to launder at least AU$229 million in the previous three years."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002322"
          ],
          "source_quote": "Their analysis enabled the AFP to fully identify and comprehensively dismantle the transnational syndicate’s financial structures."
        },
        {
          "relation_id": "r003",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e002",
          "process_element_id": "e004",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002323"
          ],
          "source_quote": "The AFP filed charges and obtained restraint orders over a significant value of assets in connection with the alleged offenses. AUSTRAC took regulatory action against one digital currency exchange and six remittance businesses associated with the charged individuals."
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
      "reason": "提供 Fintel Alliance 的金融分析支持及其产生的识别金融结构结果，构成调查流程的核心动作与产出。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "提供调查发现所触发的后续执法与监管行动，作为流程的最终执行阶段。"
    },
    {
      "candidate_id": "s1c_gap_ch32_s02_afp_investigation_findings",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "提供 AFP 调查领导与具体洗钱手法发现，完善调查过程的起点与中间结果。"
    }
  ],
  "skip_reason": null
}
```
