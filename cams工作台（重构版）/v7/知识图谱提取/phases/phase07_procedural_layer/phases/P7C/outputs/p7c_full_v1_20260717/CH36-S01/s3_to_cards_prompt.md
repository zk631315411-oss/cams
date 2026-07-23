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

section_id: `CH36-S01`

section_title: `Types of risk assessment > The importance of risk assessment in AFC`

section_text_with_unit_anchors:

```text
[v7u_N002630|2630] FATF Recommendation 1 states, “Countries should identify, assess, and understand the money laundering and terrorist financing risks for the country, and should take action, including designating an authority or mechanism to coordinate actions to assess risks, and apply resources, aimed at ensuring the risks are mitigated effectively.”
ZH: FATF建议1要求各国识别、评估并了解洗钱和恐怖融资风险，并采取协调行动

[v7u_N002631|2631] Risk assessments and the risk-based approach (RBA) are important for understanding and analyzing risks.
ZH: 风险评估和风险为本方法对于理解与分析风险至关重要

[v7u_N002632|2632] Taking necessary measures to mitigate risks minimizes their effects on a country or entity.
ZH: 采取必要措施减轻风险可最小化其对国家或实体的影响

[v7u_N002633|2633] The FATF Interpretive Note to Recommendation 1 also highlights the importance of the RBA.
ZH: FATF建议1的释义说明强调了风险为本方法的重要性

[v7u_N002634|2634] National risk assessment (NRA)
ZH: 国家风险评估（NRA）作为风险评估类型之一

[v7u_N002635|2635] Sectoral risk assessment (SRA)
ZH: 行业风险评估（SRA）作为风险评估类型之一

[v7u_N002636|2636] Enterprise-wide risk assessment (EWRA)
ZH: 企业风险评估（EWRA）作为风险评估类型之一

[v7u_N002637|2637] Risks can vary in their nature, scale, and impact.
ZH: 风险在性质、规模和影响上可能各不相同

[v7u_N002638|2638] An RBA requires countries and financial institutions to prioritize risks and apply appropriate measures based on their level of exposure.
ZH: 风险为本方法要求国家和金融机构根据风险暴露程度优先排序并采取适当措施

[v7u_N002639|2639] Not every risk applies to every institution.
ZH: 并非所有风险都适用于每个机构

[v7u_N002640|2640] Understanding these factors will allow financial institutions to make informed decisions to balance risk and reward.
ZH: 理解这些因素使金融机构能够做出平衡风险与回报的明智决策

[v7u_N002641|2641] Three main types of risk assessments are national risk assessments (NRA), sectoral risk assessments (SRA), and enterprise-wide risk assessments (EWRA).
ZH: 三种主要风险评估类型：国家风险评估、行业风险评估和企业全面风险评估

[v7u_N002642|2642] NRAs identify national-level money laundering and terror financing threats and risks. These assessments review sectors and areas with higher risks.
ZH: 国家风险评估识别国家层面的洗钱与恐怖融资威胁和风险，并审查高风险行业

[v7u_N002643|2643] Financial institutions are required to apply enhanced measures to mitigate these risks.
ZH: 金融机构必须采取强化措施以缓解风险

[v7u_N002644|2644] SRAs are performed by national authorities, supervisory bodies, regulators, and international organizations. These assessments identify, assess, and analyze money laundering and terror financing risks specific to an industry or sector.
ZH: 行业风险评估由国家机关、监管机构等执行，识别并分析特定行业的洗钱与恐怖融资风险

[v7u_N002645|2645] EWRAs analyze and evaluate money laundering and terror financing risks identified within an organization.
ZH: 企业全面风险评估分析并评估组织内部识别的洗钱与恐怖融资风险

[v7u_N002646|2646] These assessments are tailored to the specific organization conducting the assessment and consider customer characteristics, jurisdictions, products, and delivery channels.
ZH: 企业全面风险评估根据组织自身情况定制，考虑客户、地域、产品和渠道特征

[v7u_N002647|2647] The process begins by establishing inherent risks, assessing the effectiveness of controls, computing the residual risk, and obtaining a clear action plan on mitigating the highest risks.
ZH: 企业全面风险评估流程：确定固有风险、评估控制有效性、计算剩余风险、制定行动计划

[v7u_N002648|2648] Business leaders can use the EWRA to assess potential risks and estimate the cost to serve. This helps them make informed decisions about whether to expand or pursue new ventures.
ZH: 企业领导者可利用企业全面风险评估评估潜在风险和成本，辅助业务扩张决策

[v7u_N002649|2649] For example, when entering high-risk areas, the business unit’s EWRA helps evaluate the financial and operational impact, enabling leaders to understand the costs involved to be compliant. EWRAs should include consideration of the risks identified in the NRAs and SRAs for any jurisdiction in which they do business or plan to do business. NRAs and SRAs help organizations manage internal risks by using insights from national and sector-specific risk assessments. By conducting these risk assessments, organizations can:
ZH: 企业全面风险评估应纳入国家风险评估和行业风险评估的见解，以管理内部风险

[v7u_N002650|2650] Allocate resources efficiently by making informed decisions based on risk levels.
ZH: 根据风险水平做出明智决策，有效分配资源

[v7u_N002651|2651] Manage risks associated with customers, jurisdictions, products, and delivery channels by applying targeted measures according to regulatory expectations.
ZH: 通过针对客户、地域、产品和渠道采取针对性措施管理风险

[v7u_N002652|2652] Enhance AFC controls by identifying vulnerabilities and exposures and safeguarding institutions against regulatory enforcements.
ZH: 通过识别漏洞和风险敞口加强金融犯罪防控，保护机构免受监管执法

[v7u_N002653|2653] These risk assessments should be interrelated to foster an effective, riskbased AFC framework.
ZH: 各类风险评估应相互关联，以形成有效的基于风险的金融犯罪防控框架
```

allowed_unit_ids:

```json
[
  "v7u_N002630",
  "v7u_N002631",
  "v7u_N002632",
  "v7u_N002633",
  "v7u_N002634",
  "v7u_N002635",
  "v7u_N002636",
  "v7u_N002637",
  "v7u_N002638",
  "v7u_N002639",
  "v7u_N002640",
  "v7u_N002641",
  "v7u_N002642",
  "v7u_N002643",
  "v7u_N002644",
  "v7u_N002645",
  "v7u_N002646",
  "v7u_N002647",
  "v7u_N002648",
  "v7u_N002649",
  "v7u_N002650",
  "v7u_N002651",
  "v7u_N002652",
  "v7u_N002653"
]
```

## S2 Process IR

```json
{
  "section_id": "CH36-S01",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "国家应如何根据 FATF 建议 1 应对洗钱与恐怖融资风险？",
      "title": "FATF 建议 1 要求国家识别、评估和理解风险并采取行动缓解风险",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "FATF Recommendation 1",
          "evidence_unit_ids": [
            "v7u_N002630"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Countries identify, assess, and understand the money laundering and terrorist financing risks for the country",
          "evidence_unit_ids": [
            "v7u_N002630"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "designate an authority or mechanism to coordinate actions to assess risks",
          "evidence_unit_ids": [
            "v7u_N002630"
          ],
          "modality": "required"
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "apply resources",
          "evidence_unit_ids": [
            "v7u_N002630"
          ],
          "modality": "required"
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "旨在确保风险有效缓解 (aimed at ensuring the risks are mitigated effectively)",
          "evidence_unit_ids": [
            "v7u_N002630"
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
            "v7u_N002630"
          ],
          "source_quote": "FATF Recommendation 1 states, “Countries should identify, assess, and understand the money laundering and terrorist financing risks for the country, and should take action, including designating an authority or mechanism to coordinate actions to assess risks, and apply resources, aimed at ensuring the risks are mitigated effectively.”"
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002630"
          ],
          "source_quote": "and should take action, including designating an authority or mechanism to coordinate actions to assess risks"
        },
        {
          "relation_id": "r003",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e004",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002630"
          ],
          "source_quote": "and apply resources"
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e005",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002630"
          ],
          "source_quote": "aimed at ensuring the risks are mitigated effectively"
        },
        {
          "relation_id": "r005",
          "kind": "produce",
          "process_element_id": "e004",
          "outcome_element_id": "e005",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002630"
          ],
          "source_quote": "aimed at ensuring the risks are mitigated effectively"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "风险为本方法如何要求国家和金融机构根据风险暴露程度优先排序并采取措施？",
      "title": "RBA 要求基于风险暴露程度优先排序风险并应用适当措施",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "the level of exposure",
          "evidence_unit_ids": [
            "v7u_N002638"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "prioritize risks",
          "evidence_unit_ids": [
            "v7u_N002638"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "apply appropriate measures",
          "evidence_unit_ids": [
            "v7u_N002638"
          ],
          "modality": "required"
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
            "v7u_N002638"
          ],
          "source_quote": "prioritize risks … based on their level of exposure"
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002638"
          ],
          "source_quote": "prioritize risks and apply appropriate measures"
        },
        {
          "relation_id": "r003",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e001",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002638"
          ],
          "source_quote": "apply appropriate measures based on their level of exposure"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "国家风险评估识别高风险领域后，金融机构如何应对？",
      "title": "国家风险评估识别高风险领域触发金融机构采取强化措施缓解风险",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "NRAs identify national-level money laundering and terror financing threats and risks and review sectors and areas with higher risks",
          "evidence_unit_ids": [
            "v7u_N002642"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Financial institutions apply enhanced measures",
          "evidence_unit_ids": [
            "v7u_N002643"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "mitigate these risks",
          "evidence_unit_ids": [
            "v7u_N002643"
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
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002642",
            "v7u_N002643"
          ],
          "source_quote": "NRAs identify national-level money laundering and terror financing threats and risks. These assessments review sectors and areas with higher risks. Financial institutions are required to apply enhanced measures to mitigate these risks."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002643"
          ],
          "source_quote": "to mitigate these risks"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "如何执行企业全面风险评估以产出缓解最高风险的行动计划？",
      "title": "企业全面风险评估的执行过程：从固有风险到行动计划",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "risks identified in NRAs and SRAs",
          "evidence_unit_ids": [
            "v7u_N002649"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "input",
          "label": "customer characteristics, jurisdictions, products, delivery channels and specific organization tailoring",
          "evidence_unit_ids": [
            "v7u_N002646"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "establish inherent risks",
          "evidence_unit_ids": [
            "v7u_N002647"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "assess the effectiveness of controls",
          "evidence_unit_ids": [
            "v7u_N002647"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "action",
          "label": "compute the residual risk",
          "evidence_unit_ids": [
            "v7u_N002647"
          ],
          "modality": null
        },
        {
          "element_id": "e006",
          "role": "outcome",
          "label": "obtain a clear action plan on mitigating the highest risks",
          "evidence_unit_ids": [
            "v7u_N002647"
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
            "v7u_N002649"
          ],
          "source_quote": "EWRAs should include consideration of the risks identified in the NRAs and SRAs"
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e002",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002646"
          ],
          "source_quote": "These assessments are tailored to the specific organization conducting the assessment and consider customer characteristics, jurisdictions, products, and delivery channels."
        },
        {
          "relation_id": "r003",
          "kind": "sequence",
          "before_element_id": "e003",
          "after_element_id": "e004",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002647"
          ],
          "source_quote": "The process begins by establishing inherent risks, assessing the effectiveness of controls"
        },
        {
          "relation_id": "r004",
          "kind": "sequence",
          "before_element_id": "e004",
          "after_element_id": "e005",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002647"
          ],
          "source_quote": "computing the residual risk"
        },
        {
          "relation_id": "r005",
          "kind": "produce",
          "process_element_id": "e005",
          "outcome_element_id": "e006",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002647"
          ],
          "source_quote": "and obtaining a clear action plan on mitigating the highest risks"
        }
      ],
      "split_reason": "候选涵盖 EWRA 执行过程（固有风险识别、控制评估、剩余风险计算、行动计划）和领导者使用 EWRA 进行商业决策两个独立中心；EWRA 执行产出可重复使用的行动计划，领导者决策以不同主体和目的使用 EWRA 结果，因此拆分。"
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "企业领导者如何使用 EWRA 评估潜在风险与成本以支持业务扩张决策？",
      "title": "企业领导者利用 EWRA 评估风险与成本以辅助业务扩张决策",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "Business leaders use the EWRA to assess potential risks and estimate the cost to serve",
          "evidence_unit_ids": [
            "v7u_N002648"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "make informed decisions about whether to expand or pursue new ventures",
          "evidence_unit_ids": [
            "v7u_N002648"
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
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002648"
          ],
          "source_quote": "Business leaders can use the EWRA to assess potential risks and estimate the cost to serve. This helps them make informed decisions about whether to expand or pursue new ventures."
        }
      ],
      "split_reason": "候选涵盖 EWRA 执行过程（固有风险识别、控制评估、剩余风险计算、行动计划）和领导者使用 EWRA 进行商业决策两个独立中心；EWRA 执行产出可重复使用的行动计划，领导者决策以不同主体和目的使用 EWRA 结果，因此拆分。"
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_gap_ch36_s01_sra"
      ],
      "focal_question": "行业风险评估如何执行以识别特定行业的洗钱与恐怖融资风险？",
      "title": "行业风险评估的执行与特定行业风险识别",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "national authorities, supervisory bodies, regulators, and international organizations perform SRAs",
          "evidence_unit_ids": [
            "v7u_N002644"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "identify, assess, and analyze money laundering and terror financing risks specific to an industry or sector",
          "evidence_unit_ids": [
            "v7u_N002644"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "sequence",
          "before_element_id": "e001",
          "after_element_id": "e002",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002644"
          ],
          "source_quote": "SRAs are performed … These assessments identify, assess, and analyze money laundering and terror financing risks specific to an industry or sector."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_gap_ch36_s01_assessment_benefits"
      ],
      "focal_question": "进行风险评估能为组织带来哪些能力，且各类风险评估应如何关联？",
      "title": "综合风险评估带来的资源分配、风险管理和控制增强能力，以及风险评估的关联要求",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "organizations conduct these risk assessments (NRA, SRA, EWRA)",
          "evidence_unit_ids": [
            "v7u_N002649"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "allocate resources efficiently by making informed decisions based on risk levels",
          "evidence_unit_ids": [
            "v7u_N002650"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "manage risks associated with customers, jurisdictions, products, and delivery channels by applying targeted measures according to regulatory expectations",
          "evidence_unit_ids": [
            "v7u_N002651"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "enhance AFC controls by identifying vulnerabilities and exposures and safeguarding institutions against regulatory enforcements",
          "evidence_unit_ids": [
            "v7u_N002652"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "standard",
          "label": "These risk assessments should be interrelated to foster an effective, risk-based AFC framework",
          "evidence_unit_ids": [
            "v7u_N002653"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e002",
          "relation_type": null,
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N002650"
          ],
          "source_quote": "By conducting these risk assessments, organizations can: Allocate resources efficiently by making informed decisions based on risk levels."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N002651"
          ],
          "source_quote": "Manage risks associated with customers, jurisdictions, products, and delivery channels by applying targeted measures according to regulatory expectations."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N002652"
          ],
          "source_quote": "Enhance AFC controls by identifying vulnerabilities and exposures and safeguarding institutions against regulatory enforcements."
        },
        {
          "relation_id": "r004",
          "kind": "reference",
          "process_element_id": "e001",
          "auxiliary_element_id": "e005",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002653"
          ],
          "source_quote": "These risk assessments should be interrelated to foster an effective, riskbased AFC framework."
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
      "reason": "该候选明确描述了 FATF 建议 1 要求国家识别、评估和理解风险，并采取指定机构、应用资源等行动以缓解风险，构成一个完整的程序性要求流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了风险为本方法要求国家和金融机构基于风险暴露程度优先排序风险并采取适当措施，包含输入、动作与顺序关系，构成程序性流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述了国家风险评估识别高风险领域，触发金融机构采取强化措施缓解风险，包含清晰的触发-响应及目的关系，构成程序性流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004",
        "ep_005"
      ],
      "reason": "该候选包含两个独立中心：EWRA 执行过程（从固有风险到行动计划的步骤序列，考虑 NRA/SRA 输入）和领导者使用 EWRA 进行商业决策（评估成本与风险以支持扩张决策）。两者分别形成独立可复用的流程，因此拆分为两个 episode。"
    },
    {
      "candidate_id": "s1c_gap_ch36_s01_sra",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "该候选描述了行业风险评估由特定机构执行，并识别、评估和分析行业特定风险，包含动作间的顺序关系，构成程序性流程。"
    },
    {
      "candidate_id": "s1c_gap_ch36_s01_assessment_benefits",
      "disposition": "mapped",
      "episode_ids": [
        "ep_007"
      ],
      "reason": "该候选描述了组织通过进行三种风险评估可以获得高效分配资源、管理风险、增强控制等能力，并要求评估相互关联，形成从动作到可能结果的 produce 关系与标准约束，构成程序性流程。"
    }
  ],
  "skip_reason": null
}
```
