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

section_id: `CH37-S01`

section_title: `Enterprise-wide risk assessment > Enterprise-wide risk assessment`

section_text_with_unit_anchors:

```text
[v7u_N002721|2721] EWRAs, sometimes called bank-wide risk assessments, institutional risk assessments, or financial crime risk assessments, help organizations evaluate their overall risk exposure to financial crime, including money laundering (ML), terrorist financing (TF), proliferation financing, sanctions evasion, tax evasion, bribery, corruption, and fraud.
ZH: 企业级风险评估（EWRA）的定义与范围，涵盖洗钱、恐怖融资、制裁规避、欺诈等多种金融犯罪。

[v7u_N002722|2722] The EWRA provides a standardized way to measure and track risks, ensuring they are mitigated across all operations, products, and services.
ZH: EWRA 提供标准化的风险衡量与追踪方法，确保风险在所有运营、产品和服务中得到缓解。

[v7u_N002723|2723] Organizations conduct EWRAs periodically and whenever there is material change in the organization’s business structure, its regulatory environment, or if a money laundering or wider financial crime trend is identified.
ZH: 组织应定期或在业务结构、监管环境发生重大变化时，或发现洗钱等金融犯罪趋势时开展 EWRA。

[v7u_N002724|2724] The organization's AFC risk assessment team typically leads the EWRA, although in smaller organizations it might be the governance or advisory team.
ZH: EWRA 通常由金融犯罪防控（金融犯罪防控）风险评估团队主导，小型组织可能由治理或咨询团队负责。

[v7u_N002725|2725] The results of an EWRA are reported to the MLRO, or equivalent, and the relevant stakeholders, such as senior managers and department heads.
ZH: EWRA 结果需报告给洗钱报告官（MLRO）及高级管理层、部门负责人等相关利益方。

[v7u_N002726|2726] The MLRO uses these results in the ongoing evaluation and determination of the organization’s financial crime risk appetite.
ZH: MLRO 利用 EWRA 结果持续评估并确定组织的金融犯罪风险偏好。

[v7u_N002727|2727] The EWRA should use a broad range of public and private information sources to assess risk comprehensively.
ZH: EWRA 应利用广泛的公共和私人信息来源，以全面评估风险。

[v7u_N002728|2728] It should review all customer types, jurisdictions, products, delivery channels, transactions, and the operating environment, including staff education and training on the financial crime risk the organization needs to manage.
ZH: EWRA 应审查所有客户类型、司法管辖区、产品、交付渠道、交易及运营环境，包括员工培训。

[v7u_N002729|2729] Additionally, it should review prior risk alerts as identified by the alert management systems, particularly those that result in a true match, which should be further analyzed for residual risk.
ZH: EWRA 还应审查预警管理系统中的历史风险警报，特别是真实匹配项，以分析剩余风险。

[v7u_N002730|2730] A risk assessment should place particular focus where:
ZH: 风险评估应特别关注以下情形：

[v7u_N002731|2731] The probability of the risk occurring and its impact are greatest.
ZH: 风险发生概率及其影响最大时，应重点关注。

[v7u_N002732|2732] The risk exceeds the organization’s appetite.
ZH: 风险超出组织风险偏好时，应重点关注。

[v7u_N002733|2733] Controls are ineffective.
ZH: 控制措施无效时，应重点关注。

[v7u_N002734|2734] Systems or controls have changed.
ZH: 系统或控制措施发生变化时，应重点关注。

[v7u_N002735|2735] In global organizations, the EWRA should be conducted in a flexible, coordinated manner and based on a common methodology. Subsidiaries or branches should be allowed to include the specific risk dynamics and relevant local elements of their own operations. The parent organization should incorporate input from all subsidiaries and branches in the group-wide risk assessment.
ZH: 全球性组织的 EWRA 应基于统一方法论灵活协调开展，允许子公司纳入本地风险要素，母公司应整合所有子公司的意见。
```

allowed_unit_ids:

```json
[
  "v7u_N002721",
  "v7u_N002722",
  "v7u_N002723",
  "v7u_N002724",
  "v7u_N002725",
  "v7u_N002726",
  "v7u_N002727",
  "v7u_N002728",
  "v7u_N002729",
  "v7u_N002730",
  "v7u_N002731",
  "v7u_N002732",
  "v7u_N002733",
  "v7u_N002734",
  "v7u_N002735"
]
```

## S2 Process IR

```json
{
  "section_id": "CH37-S01",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001",
        "s1c_002",
        "s1c_003",
        "s1c_004",
        "s1c_gap_ch37_s01_ewra_review_scope"
      ],
      "focal_question": "如何开展企业级风险评估并报告结果",
      "title": "Enterprise-wide risk assessment conduct and reporting",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "定期、业务结构重大变化、监管环境重大变化或发现洗钱/金融犯罪趋势",
          "evidence_unit_ids": [
            "v7u_N002723"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "conduct enterprise-wide risk assessment (EWRA)",
          "evidence_unit_ids": [
            "v7u_N002723"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "standard",
          "label": "use a broad range of public and private information sources to assess risk comprehensively",
          "evidence_unit_ids": [
            "v7u_N002727"
          ],
          "modality": "required"
        },
        {
          "element_id": "e004",
          "role": "standard",
          "label": "review all customer types, jurisdictions, products, delivery channels, transactions, and the operating environment, including staff education and training on the financial crime risk",
          "evidence_unit_ids": [
            "v7u_N002728"
          ],
          "modality": "required"
        },
        {
          "element_id": "e005",
          "role": "standard",
          "label": "review prior risk alerts as identified by alert management systems, particularly true matches, and further analyze for residual risk",
          "evidence_unit_ids": [
            "v7u_N002729"
          ],
          "modality": "required"
        },
        {
          "element_id": "e006",
          "role": "standard",
          "label": "place particular focus where: risk probability and impact greatest, risk exceeds appetite, controls ineffective, or systems/controls changed",
          "evidence_unit_ids": [
            "v7u_N002730",
            "v7u_N002731",
            "v7u_N002732",
            "v7u_N002733",
            "v7u_N002734"
          ],
          "modality": "required"
        },
        {
          "element_id": "e007",
          "role": "standard",
          "label": "for global organizations, conduct EWRA in flexible, coordinated manner based on common methodology; allow subsidiaries to include local risk dynamics; parent incorporates input from all subsidiaries and branches",
          "evidence_unit_ids": [
            "v7u_N002735"
          ],
          "modality": "required"
        },
        {
          "element_id": "e008",
          "role": "outcome",
          "label": "EWRA results",
          "evidence_unit_ids": [
            "v7u_N002725"
          ],
          "modality": null
        },
        {
          "element_id": "e009",
          "role": "action",
          "label": "report the results to the MLRO, or equivalent, and the relevant stakeholders, such as senior managers and department heads",
          "evidence_unit_ids": [
            "v7u_N002725"
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
          "condition": "periodically or when material change in business structure/regulatory environment or financial crime trend identified",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002723"
          ],
          "source_quote": "Organizations conduct EWRAs periodically and whenever there is material change in the organization’s business structure, its regulatory environment, or if a money laundering or wider financial crime trend is identified."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e003",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002727"
          ],
          "source_quote": "The EWRA should use a broad range of public and private information sources to assess risk comprehensively."
        },
        {
          "relation_id": "r003",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e004",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002728"
          ],
          "source_quote": "It should review all customer types, jurisdictions, products, delivery channels, transactions, and the operating environment, including staff education and training on the financial crime risk the organization needs to manage."
        },
        {
          "relation_id": "r004",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e005",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002729"
          ],
          "source_quote": "Additionally, it should review prior risk alerts as identified by the alert management systems, particularly those that result in a true match, which should be further analyzed for residual risk."
        },
        {
          "relation_id": "r005",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e006",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002730",
            "v7u_N002731",
            "v7u_N002732",
            "v7u_N002733",
            "v7u_N002734"
          ],
          "source_quote": "A risk assessment should place particular focus where: The probability of the risk occurring and its impact are greatest; the risk exceeds the organization’s appetite; controls are ineffective; systems or controls have changed."
        },
        {
          "relation_id": "r006",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e007",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002735"
          ],
          "source_quote": "In global organizations, the EWRA should be conducted in a flexible, coordinated manner and based on a common methodology. Subsidiaries or branches should be allowed to include the specific risk dynamics and relevant local elements of their own operations. The parent organization should incorporate input from all subsidiaries and branches in the group-wide risk assessment."
        },
        {
          "relation_id": "r007",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e008",
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002725"
          ],
          "source_quote": "The results of an EWRA are reported to the MLRO, or equivalent, and the relevant stakeholders, such as senior managers and department heads."
        },
        {
          "relation_id": "r008",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e008",
          "process_element_id": "e009",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002725"
          ],
          "source_quote": "The results of an EWRA are reported to the MLRO, or equivalent, and the relevant stakeholders, such as senior managers and department heads."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "MLRO如何利用EWRA结果评估金融犯罪风险偏好",
      "title": "MLRO's use of EWRA results for risk appetite evaluation",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e010",
          "role": "input",
          "label": "EWRA results",
          "evidence_unit_ids": [
            "v7u_N002726"
          ],
          "modality": null
        },
        {
          "element_id": "e011",
          "role": "action",
          "label": "MLRO uses these results in the ongoing evaluation and determination of the organization’s financial crime risk appetite",
          "evidence_unit_ids": [
            "v7u_N002726"
          ],
          "modality": "required"
        },
        {
          "element_id": "e012",
          "role": "outcome",
          "label": "ongoing determination of financial crime risk appetite",
          "evidence_unit_ids": [
            "v7u_N002726"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r009",
          "kind": "reference",
          "process_element_id": "e011",
          "auxiliary_element_id": "e010",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002726"
          ],
          "source_quote": "The MLRO uses these results in the ongoing evaluation and determination of the organization’s financial crime risk appetite."
        },
        {
          "relation_id": "r010",
          "kind": "produce",
          "process_element_id": "e011",
          "outcome_element_id": "e012",
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002726"
          ],
          "source_quote": "The MLRO uses these results in the ongoing evaluation and determination of the organization’s financial crime risk appetite."
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
      "reason": "该候选明确EWRA的触发条件（定期或特定事件），直接支持ep_001中触发EWRA开展的关系。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "support_only",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选提供风险评估应特别关注的情形标准，自身不构成独立程序关系，但为EWRA执行过程提供必要的关注标准。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "support_only",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选提供全球组织EWRA应遵循的特定开展方式要求，自身不构成独立程序关系，但为EWRA过程提供情境化标准。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选明确EWRA结果的报告动作，形成EWRA结果到报告的关系，直接参与ep_001的程序序列。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选提供MLRO使用EWRA结果评估风险偏好的独立程序，形成完整的input-action-outcome关系，独立成ep_002。"
    },
    {
      "candidate_id": "s1c_gap_ch37_s01_ewra_review_scope",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选明确EWRA执行中应审查的广泛信息源和具体要素（客户、产品、警报等），直接作为EWRA动作的参考标准，支持多条reference关系。"
    }
  ],
  "skip_reason": null
}
```
