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

section_id: `CH20-S03`

section_title: `AFC guidance from leading international organizations > World Bank and International Monetary Fund AFC guidance`

section_text_with_unit_anchors:

```text
[v7u_N001487|1487] The World Bank is an international organization that provides funding, policies, and technical assistance to developing countries.
ZH: 世界银行为发展中国家提供资金、政策和技术援助

[v7u_N001488|1488] The International Monetary Fund (IMF) keeps track of the global economy while seeking to maintain the stability of the global monetary system and lend funds to member countries.
ZH: 国际货币基金组织（IMF）监测全球经济并维护货币体系稳定

[v7u_N001489|1489] The World Bank and IMF have cooperated since the early 2000s in efforts to combat money laundering and terrorist financing.
ZH: 世界银行和IMF自2000年代初合作打击洗钱和恐怖融资

[v7u_N001490|1490] They require jurisdictions that benefit from their programs to have effective AML/CFT controls.
ZH: 受益于世界银行和IMF项目的司法管辖区须具备有效的反洗钱/反恐怖融资管控措施

[v7u_N001491|1491] They work closely with FATF to implement FATF standards and incorporate FATF compliance in their Financial Sector Assessment Program reviews of member jurisdictions.
ZH: 世界银行和IMF与FATF密切合作，在金融部门评估规划中纳入FATF合规要求

[v7u_N001492|1492] The World Bank and IMF have Observer status with FATF.
ZH: 世界银行和IMF在FATF中拥有观察员地位

[v7u_N001493|1493] Their role in combating money laundering and terrorist financing includes four main areas:
ZH: 世界银行和IMF在打击洗钱和恐怖融资方面的作用涵盖四个主要领域

[v7u_N001494|1494] Raising awareness
ZH: 提高认识是世界银行和IMF在AML/CFT领域的作用之一

[v7u_N001495|1495] Developing a universal assessment methodology
ZH: 制定通用评估方法是世界银行和IMF在AML/CFT领域的作用之一

[v7u_N001496|1496] Building institutional capacity
ZH: 建设机构能力是世界银行和IMF在AML/CFT领域的作用之一

[v7u_N001497|1497] Researching and analyzing different aspects of the global economy
ZH: 研究和分析全球经济不同方面是世界银行和IMF在AML/CFT领域的作用之一

[v7u_N001498|1498] The World Bank and IMF provide a wide range of resources to address money laundering and terrorist financing. They jointly publish the Anti-Money Laundering and Combating the Financing of Terrorism, which is the primary AML/CFT resource from these organizations.
ZH: 世界银行和IMF联合发布主要反洗钱/反恐怖融资资源《反洗钱与打击恐怖融资》

[v7u_N001499|1499] This guide provides an overview of relevant global and regional bodies, preventive measures, and the role and functions of national FIUs. It also includes a detailed section on terrorist financing.
ZH: 该指南概述全球和区域机构、预防措施及国家金融情报机构的作用，并包含恐怖融资专题

[v7u_N001500|1500] Guidance is generally aimed at the jurisdictional level, not individual institutions.
ZH: 世界银行和IMF的指导主要面向司法管辖区层面而非单个机构

[v7u_N001501|1501] In addition to their joint guidance, each institution also provides its own resources to assist in combatting financial crime. The World Bank publishes ad hoc reports in areas such as trade finance, training, and risk assessments.
ZH: 世界银行发布贸易融资、培训和风险评估等专题报告以协助打击金融犯罪。

[v7u_N001502|1502] IMF publishes periodic reviews of its AML/CFT strategy, accompanied by extensive background papers addressing specific topics. It also provides publications on emerging issues such as beneficial ownership and virtual assets, and hosts live and recorded roundtables regularly. Additionally, it administers the AML/CFT Thematic Fund for Capacity Development, a global initiative to assist countries in strengthening their AML/CFT regimes.
ZH: IMF发布反洗钱/反恐怖融资战略定期审查、背景文件、新兴议题出版物，并管理能力发展专题基金。
```

allowed_unit_ids:

```json
[
  "v7u_N001487",
  "v7u_N001488",
  "v7u_N001489",
  "v7u_N001490",
  "v7u_N001491",
  "v7u_N001492",
  "v7u_N001493",
  "v7u_N001494",
  "v7u_N001495",
  "v7u_N001496",
  "v7u_N001497",
  "v7u_N001498",
  "v7u_N001499",
  "v7u_N001500",
  "v7u_N001501",
  "v7u_N001502"
]
```

## S2 Process IR

```json
{
  "section_id": "CH20-S03",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_gap_ch20_s03_require_controls"
      ],
      "focal_question": "世界银行和IMF如何对受益于其项目的司法管辖区施加AML/CFT管控要求？",
      "title": "根据项目受益条件要求具备有效AML/CFT管控",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "受益于世界银行和IMF项目",
          "evidence_unit_ids": [
            "v7u_N001490"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "要求具备有效的反洗钱/反恐怖融资管控",
          "evidence_unit_ids": [
            "v7u_N001490"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "具备有效的反洗钱/反恐怖融资管控",
          "evidence_unit_ids": [
            "v7u_N001490"
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
          "condition": "管辖区受益于其项目",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001490"
          ],
          "source_quote": "They require jurisdictions that benefit from their programs to have effective AML/CFT controls."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001490"
          ],
          "source_quote": "They require jurisdictions that benefit from their programs to have effective AML/CFT controls."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_gap_ch20_s03_fatf_fsap"
      ],
      "focal_question": "世界银行和IMF如何在金融部门评估规划审查中纳入FATF合规要求？",
      "title": "与FATF合作在FSAP审查中纳入FATF合规要求",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "在金融部门评估规划（FSAP）审查中纳入FATF合规要求",
          "evidence_unit_ids": [
            "v7u_N001491"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "FSAP审查包含FATF合规要求",
          "evidence_unit_ids": [
            "v7u_N001491"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001491"
          ],
          "source_quote": "They work closely with FATF to implement FATF standards and incorporate FATF compliance in their Financial Sector Assessment Program reviews of member jurisdictions."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_gap_ch20_s03_joint_guide"
      ],
      "focal_question": "世界银行和IMF联合发布的主要反洗钱/反恐怖融资资源是什么？",
      "title": "联合发布《反洗钱与打击恐怖融资》作为主要AML/CFT资源",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "世界银行和IMF联合发布《反洗钱与打击恐怖融资》",
          "evidence_unit_ids": [
            "v7u_N001498"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "《反洗钱与打击恐怖融资》作为主要反洗钱/反恐怖融资资源",
          "evidence_unit_ids": [
            "v7u_N001498"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001498"
          ],
          "source_quote": "They jointly publish the Anti-Money Laundering and Combating the Financing of Terrorism, which is the primary AML/CFT resource from these organizations."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_gap_ch20_s03_wb_reports"
      ],
      "focal_question": "世界银行如何通过发布专题报告提供资源？",
      "title": "世界银行发布贸易融资、培训和风险评估等专题报告",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "世界银行发布贸易融资、培训和风险评估等专题报告",
          "evidence_unit_ids": [
            "v7u_N001501"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "在贸易融资、培训和风险评估等领域的专题报告",
          "evidence_unit_ids": [
            "v7u_N001501"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001501"
          ],
          "source_quote": "The World Bank publishes ad hoc reports in areas such as trade finance, training, and risk assessments."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_gap_ch20_s03_imf_resources"
      ],
      "focal_question": "IMF如何发布其AML/CFT战略审查及背景文件？",
      "title": "IMF发布AML/CFT战略定期审查及背景文件",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "IMF发布AML/CFT战略定期审查及广泛的背景文件",
          "evidence_unit_ids": [
            "v7u_N001502"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "AML/CFT战略定期审查",
          "evidence_unit_ids": [
            "v7u_N001502"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "针对特定主题的广泛背景文件",
          "evidence_unit_ids": [
            "v7u_N001502"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001502"
          ],
          "source_quote": "IMF publishes periodic reviews of its AML/CFT strategy, accompanied by extensive background papers addressing specific topics."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001502"
          ],
          "source_quote": "IMF publishes periodic reviews of its AML/CFT strategy, accompanied by extensive background papers addressing specific topics."
        }
      ],
      "split_reason": "该候选包含多个独立的资源提供行动，为准确表达流程，将战略审查发布拆分为独立episode。"
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_gap_ch20_s03_imf_resources"
      ],
      "focal_question": "IMF提供哪些新兴议题的出版物？",
      "title": "IMF提供受益所有权和虚拟资产等新兴议题的出版物",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "IMF提供新兴议题的出版物，如受益所有权和虚拟资产",
          "evidence_unit_ids": [
            "v7u_N001502"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "关于受益所有权和虚拟资产等新兴议题的出版物",
          "evidence_unit_ids": [
            "v7u_N001502"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001502"
          ],
          "source_quote": "It also provides publications on emerging issues such as beneficial ownership and virtual assets"
        }
      ],
      "split_reason": "该候选包含多个独立的资源提供行动，将新兴议题出版物提供拆分为独立episode。"
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_gap_ch20_s03_imf_resources"
      ],
      "focal_question": "IMF如何举办圆桌会议？",
      "title": "IMF定期举办现场和录制的圆桌会议",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "IMF定期举办现场和录制的圆桌会议",
          "evidence_unit_ids": [
            "v7u_N001502"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "现场和录制的圆桌会议",
          "evidence_unit_ids": [
            "v7u_N001502"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001502"
          ],
          "source_quote": "and hosts live and recorded roundtables regularly"
        }
      ],
      "split_reason": "该候选包含多个独立的资源提供行动，将圆桌会议举办拆分为独立episode。"
    },
    {
      "episode_id": "ep_008",
      "source_candidate_ids": [
        "s1c_gap_ch20_s03_imf_resources"
      ],
      "focal_question": "IMF如何管理AML/CFT能力发展专题基金？",
      "title": "IMF管理反洗钱/反恐怖融资能力发展专题基金",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "IMF管理反洗钱/反恐怖融资能力发展专题基金",
          "evidence_unit_ids": [
            "v7u_N001502"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "反洗钱/反恐怖融资能力发展专题基金，旨在协助各国加强AML/CFT体制",
          "evidence_unit_ids": [
            "v7u_N001502"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001502"
          ],
          "source_quote": "Additionally, it administers the AML/CFT Thematic Fund for Capacity Development, a global initiative to assist countries in strengthening their AML/CFT regimes."
        }
      ],
      "split_reason": "该候选包含多个独立的资源提供行动，将专项基金管理拆分为独立episode。"
    }
  ],
  "candidate_audit": [
    {
      "candidate_id": "s1c_gap_ch20_s03_require_controls",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选描述了一个条件触发的要求流程，通过condition触发action并产出义务，构成完整的程序性迁移。"
    },
    {
      "candidate_id": "s1c_gap_ch20_s03_fatf_fsap",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了在FSAP审查中纳入FATF合规要求的行动及其结果，符合流程定义。"
    },
    {
      "candidate_id": "s1c_gap_ch20_s03_joint_guide",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述了联合发布指南作为主要资源的行动和产出。"
    },
    {
      "candidate_id": "s1c_gap_ch20_s03_guidance_scope",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选仅描述指导的适用对象，原文无任何程序性或判断性迁移，属于静态范围陈述。"
    },
    {
      "candidate_id": "s1c_gap_ch20_s03_wb_reports",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选描述了世界银行发布专题报告的行动及产出。"
    },
    {
      "candidate_id": "s1c_gap_ch20_s03_imf_resources",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005",
        "ep_006",
        "ep_007",
        "ep_008"
      ],
      "reason": "该候选包含多个独立的资源提供行动，每个行动均产生相应的资源或服务，因此拆分为战略审查发布、新兴议题出版物、圆桌会议举办、专项基金管理四个独立流程。"
    }
  ],
  "skip_reason": null
}
```
