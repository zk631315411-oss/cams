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

section_id: `CH28-S01`

section_title: `Case example: Using typology reports to enhance AML controls`

section_text_with_unit_anchors:

```text
[v7u_N002134|2134] Law enforcement authorities in Isabella's jurisdiction have noted an increase in money laundering via cryptoassets and the banking sector. Authorities believe that criminals are recruiting individuals as money mules.
ZH: 案例：执法机构发现通过加密资产和银行业洗钱增加，并利用钱骡

[v7u_N002135|2135] Law enforcement sets up a working group to address this trend. The group includes the FIU, regulator, and representatives of the bank and virtual assets sectors. The group's aim is to produce better intelligence to detect those involved in this activity and improve controls in the private sector.
ZH: 执法机构成立工作组，包括金融情报机构、监管机构及银行和虚拟资产行业代表

[v7u_N002136|2136] Isabella's organization is invited to join the group. She obtains agreement from senior management.
ZH: Isabella所在组织经高级管理层同意后加入工作组

[v7u_N002137|2137] Law enforcement issues a typology report via the group, explaining how the suspected money laundering happens. The report indicates that students open accounts with VASPs and move the proceeds of crime to and from these accounts via their local bank accounts.
ZH: 执法机构发布类型学报告，揭示学生利用虚拟资产服务提供商账户和银行账户转移犯罪收益

[v7u_N002138|2138] The group requests that participant organizations consider this information, review their data to confirm the typology, and identify customer activity that aligns.
ZH: 工作组要求参与组织审查数据以确认类型学并识别匹配的客户活动

[v7u_N002139|2139] Isabella reviews her organization's client population and confirms a large number of student accounts.
ZH: Isabella审查客户群体，确认存在大量学生账户

[v7u_N002140|2140] There are more accounts than she can review manually, so she works with the internal data team to identify ways to segment this population further.
ZH: Isabella与数据团队合作，进一步细分学生账户群体

[v7u_N002141|2141] She is able to identify accounts that are behaving unusually using this strategy.
ZH: 案例：Isabella通过细分策略识别异常账户行为

[v7u_N002142|2142] She also identifies accounts that mention the name of a VASP or a particular cryptoasset in payment references or via customer communication.
ZH: 案例：Isabella识别在支付备注或客户沟通中提及VASP或加密资产的账户

[v7u_N002143|2143] Isabella reports this trend to senior management, then prepares and files SARs, ensuring that the FIU knows these reports are being submitted because of the public-private partnership. She also reports her findings to the working group and confirms that their typology appears to be sound.
ZH: 案例：Isabella向高级管理层报告趋势，准备并提交可疑活动报告，并向工作组反馈

[v7u_N002144|2144] Isabella also presents the findings to a senior internal committee along with recommendations for better protecting the organization from this activity in the future. Her recommendations include changes to the KYC and client risk profile parameters as well as adjustments to transaction monitoring processes.
ZH: 案例：Isabella向高级内部委员会提交发现和建议，包括了解你的客户和客户风险参数调整
```

allowed_unit_ids:

```json
[
  "v7u_N002134",
  "v7u_N002135",
  "v7u_N002136",
  "v7u_N002137",
  "v7u_N002138",
  "v7u_N002139",
  "v7u_N002140",
  "v7u_N002141",
  "v7u_N002142",
  "v7u_N002143",
  "v7u_N002144"
]
```

## S2 Process IR

```json
{
  "section_id": "CH28-S01",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_gap_ch28_s01_wg_formed",
        "s1c_gap_ch28_s01_typo_report",
        "s1c_gap_ch28_s01_wg_request"
      ],
      "focal_question": "执法机构如何通过工作组生成类型学报告并要求参与组织进行审查？",
      "title": "成立工作组、发布类型学报告并要求参与者审查数据",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "执法机构成立工作组，包括FIU、监管机构及银行和虚拟资产行业代表，旨在产生情报并改进控制",
          "evidence_unit_ids": [
            "v7u_N002135"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "执法机构通过工作组发布类型学报告，揭示学生利用VASP和银行账户转移犯罪收益的洗钱方式",
          "evidence_unit_ids": [
            "v7u_N002137"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "工作组要求参与组织考虑类型学信息、审查数据以确认类型学并识别匹配的客户活动",
          "evidence_unit_ids": [
            "v7u_N002138"
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
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002135",
            "v7u_N002137"
          ],
          "source_quote": "Law enforcement sets up a working group to address this trend. ... Law enforcement issues a typology report via the group"
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002137",
            "v7u_N002138"
          ],
          "source_quote": "Law enforcement issues a typology report via the group... The group requests that participant organizations consider this information, review their data"
        }
      ],
      "split_reason": "s1c_gap_ch28_s01_wg_request 在该episode中作为工作组流程的终点动作，同时作为ep_003审查流程的启动上下文，因此被两个episode复用。"
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_gap_ch28_s01_mgmt_approval"
      ],
      "focal_question": "如何获得组织内部批准以加入工作组？",
      "title": "受邀后获取高级管理层同意加入工作组",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "Isabella的组织受邀加入工作组",
          "evidence_unit_ids": [
            "v7u_N002136"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Isabella获得高级管理层同意",
          "evidence_unit_ids": [
            "v7u_N002136"
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
            "v7u_N002136"
          ],
          "source_quote": "Isabella's organization is invited to join the group. She obtains agreement from senior management."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_gap_ch28_s01_wg_request",
        "s1c_001",
        "s1c_002",
        "s1c_003"
      ],
      "focal_question": "如何基于工作组要求审查客户群体并识别匹配类型学的异常账户？",
      "title": "审查客户群体，细分并识别异常行为及涉VASP/加密资产的账户",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "工作组要求参与组织审查数据以确认类型学并识别匹配活动",
          "evidence_unit_ids": [
            "v7u_N002138"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Isabella审查客户群体",
          "evidence_unit_ids": [
            "v7u_N002139"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "确认存在大量学生账户",
          "evidence_unit_ids": [
            "v7u_N002139"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "与数据团队合作进一步细分客户群体并识别异常行为账户及提及VASP或加密资产的账户",
          "evidence_unit_ids": [
            "v7u_N002140",
            "v7u_N002141",
            "v7u_N002142"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "识别出的异常账户（包括行为异常或提及VASP/加密资产的账户）",
          "evidence_unit_ids": [
            "v7u_N002141",
            "v7u_N002142"
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
            "v7u_N002138",
            "v7u_N002139"
          ],
          "source_quote": "The group requests that participant organizations consider this information, review their data ... Isabella reviews her organization's client population"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002139"
          ],
          "source_quote": "Isabella reviews her organization's client population and confirms a large number of student accounts."
        },
        {
          "relation_id": "r003",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e003",
          "process_element_id": "e004",
          "condition": "学生账户数量超过手动审查能力",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002140",
            "v7u_N002139"
          ],
          "source_quote": "There are more accounts than she can review manually, so she works with the internal data team to identify ways to segment this population further."
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e004",
          "outcome_element_id": "e005",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002141",
            "v7u_N002142"
          ],
          "source_quote": "She is able to identify accounts that are behaving unusually using this strategy. She also identifies accounts that mention the name of a VASP or a particular cryptoasset"
        }
      ],
      "split_reason": "s1c_gap_ch28_s01_wg_request 在该episode中作为审查流程的触发上下文，原本已在ep_001中作为动作使用，此处复用为context。"
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_004",
        "s1c_005"
      ],
      "focal_question": "如何基于识别出的异常账户趋势采取报告和改进措施？",
      "title": "报告趋势、提交SAR、反馈工作组并向内部委员会提出建议",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "识别出的异常账户趋势和发现",
          "evidence_unit_ids": [
            "v7u_N002143",
            "v7u_N002144"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "Isabella向高级管理层报告趋势，准备并提交可疑活动报告，确保FIU知晓，向工作组反馈发现并确认类型学有效",
          "evidence_unit_ids": [
            "v7u_N002143"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "Isabella向高级内部委员会提交发现和建议，包括调整KYC、客户风险参数和交易监控流程",
          "evidence_unit_ids": [
            "v7u_N002144"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "提出的建议（调整KYC、客户风险参数和交易监控流程）",
          "evidence_unit_ids": [
            "v7u_N002144"
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
            "v7u_N002143"
          ],
          "source_quote": "Isabella reports this trend to senior management, then prepares and files SARs... She also reports her findings to the working group"
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002143",
            "v7u_N002144"
          ],
          "source_quote": "She also presents the findings to a senior internal committee"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002144"
          ],
          "source_quote": "Isabella also presents the findings to a senior internal committee along with recommendations... Her recommendations include changes to the KYC and client risk profile parameters as well as adjustments to transaction monitoring processes."
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
        "ep_003"
      ],
      "reason": "该候选描述Isabella审查客户群体并确认大量学生账户，是识别异常账户的前置步骤，直接支持审查识别流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述因账户过多无法手动审查而合作细分，是识别流程中的必要解决方法。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述使用细分策略识别异常账户，是审查流程的核心产出。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选描述基于识别结果进行报告、提交SAR和反馈工作组，是后续处理行动的一部分。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选描述向内部委员会提交发现和建议，是报告和建议流程的组成部分。"
    },
    {
      "candidate_id": "s1c_gap_ch28_s01_wg_formed",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选描述执法机构成立工作组，是公私合作生成类型学情报的起点。"
    },
    {
      "candidate_id": "s1c_gap_ch28_s01_mgmt_approval",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述获取高层批准加入工作组，是组织内部决策程序。"
    },
    {
      "candidate_id": "s1c_gap_ch28_s01_typo_report",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选描述执法机构发布类型学报告，是工作组流程中的关键情报产出。"
    },
    {
      "candidate_id": "s1c_gap_ch28_s01_wg_request",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001",
        "ep_003"
      ],
      "reason": "该候选在工作组流程中作为要求审查的动作，在Isabella审查流程中作为触发上下文，因此被两个episode复用，相应split_reason已在episode中说明。"
    }
  ],
  "skip_reason": null
}
```
