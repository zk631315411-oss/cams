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

section_id: `CH20-S04`

section_title: `AFC guidance from leading international organizations > Organisation for Economic Co-operation and Development AFC guidance`

section_text_with_unit_anchors:

```text
[v7u_N001503|1503] The Organisation for Economic Co-operation and Development (OECD) is an intergovernmental organization founded in 1961. It works closely with policymakers, stakeholders, and citizens to establish evidence-based international standards for a variety of policy issues.
ZH: OECD是1961年成立的政府间组织，与政策制定者、利益相关者和公民合作制定基于证据的国际标准。

[v7u_N001504|1504] The OECD consists of three sections:
ZH: OECD由三个部分组成。

[v7u_N001505|1505] The Council is its decision-making body. It is composed of one representative from each member country plus the EU and is chaired by the Secretary-General.
ZH: OECD理事会是决策机构，由各成员国代表和欧盟代表组成，由秘书长主持。

[v7u_N001506|1506] The Substantive Committees propose solutions, develop standards, assess data, and review policy actions. There are more than 300 such committees.
ZH: OECD专业委员会提出解决方案、制定标准、评估数据并审查政策行动，共有300多个委员会。

[v7u_N001507|1507] The Secretariat is made up of more than 3,500 employees who carry out the work of the OECD. They include economists, lawyers, scientists, political analysts, digital experts, statisticians, and other specialists.
ZH: OECD秘书处由3500多名员工组成，包括经济学家、律师、科学家等专家。

[v7u_N001508|1508] In November 1997, the OECD adopted the Convention on Combating Bribery of Foreign Public Officials in International Business Transactions.
ZH: 1997年11月，OECD通过了《打击在国际商业交易中贿赂外国公职人员公约》。

[v7u_N001509|1509] The Convention requires signatory countries to establish legislation that criminalizes the bribery of foreign public officials in international business transactions.
ZH: 该公约要求签署国立法将贿赂外国公职人员定为刑事犯罪。

[v7u_N001510|1510] It also establishes an open-ended, peer-driven monitoring mechanism to ensure the thorough implementation of international obligations.
ZH: 公约建立了开放、同行驱动的监督机制以确保国际义务的全面实施。

[v7u_N001511|1511] It is the first and only international anti-corruption instrument focused on the “supply side” of the bribery transaction: the person or entity offering, promising, or giving a bribe.
ZH: 该公约是首个也是唯一一个聚焦贿赂交易“供应方”的国际反腐败文书。

[v7u_N001512|1512] The OECD Working Group on Bribery in International Business Transactions evaluates and makes recommendations on a jurisdiction’s implementation and enforcement of the Convention and related instruments. The Working Group issues reports that detail a jurisdiction’s achievements and challenges, including enforcement of foreign bribery offenses. The reports also document the jurisdiction’s progress since its last evaluation.
ZH: OECD贿赂工作组评估并建议各司法管辖区实施和执行公约的情况，发布详细报告。

[v7u_N001513|1513] Many organizations utilize the OECD's guidance and resources as a reference to identify risks from various areas. The OECD discusses a range of topics, including:
ZH: 许多组织利用OECD的指导和资源识别风险，OECD讨论一系列主题。

[v7u_N001514|1514] Digital currencies, such as cryptocurrencies.
ZH: 数字货币（如加密货币）是OECD讨论的主题之一。

[v7u_N001515|1515] Beneficial ownership.
ZH: 受益所有人是OECD讨论的主题之一。

[v7u_N001516|1516] Transnational organized crime.
ZH: 跨国有组织犯罪是OECD讨论的主题之一。

[v7u_N001517|1517] Tax crime.
ZH: 税务犯罪是OECD讨论的主题之一。

[v7u_N001518|1518] Risks of corruption, conflict financing, and money laundering linked to gold flows.
ZH: 与黄金流动相关的腐败、冲突融资和洗钱风险是OECD讨论的主题之一。

[v7u_N001519|1519] Main areas of weakness and potential areas for action to combat money laundering, tax evasion, and foreign bribery.
ZH: 打击洗钱、逃税和外国贿赂的主要薄弱环节和潜在行动领域是OECD讨论的主题之一。

[v7u_N001520|1520] Identifying, freezing, and returning stolen assets.
ZH: 识别、冻结和返还被盗资产是OECD讨论的主题之一。
```

allowed_unit_ids:

```json
[
  "v7u_N001503",
  "v7u_N001504",
  "v7u_N001505",
  "v7u_N001506",
  "v7u_N001507",
  "v7u_N001508",
  "v7u_N001509",
  "v7u_N001510",
  "v7u_N001511",
  "v7u_N001512",
  "v7u_N001513",
  "v7u_N001514",
  "v7u_N001515",
  "v7u_N001516",
  "v7u_N001517",
  "v7u_N001518",
  "v7u_N001519",
  "v7u_N001520"
]
```

## S2 Process IR

```json
{
  "section_id": "CH20-S04",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "OECD贿赂工作组如何评估并提出建议后发布报告？",
      "title": "OECD贿赂工作组评估和建议流程",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "一个司法管辖区的实施和执行公约及相关文书的情况",
          "evidence_unit_ids": [
            "v7u_N001512"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "OECD贿赂工作组评估并提出建议",
          "evidence_unit_ids": [
            "v7u_N001512"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "发布详细报告，记录成就、挑战、执法情况及进展",
          "evidence_unit_ids": [
            "v7u_N001512"
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
          "evidence_unit_ids": [
            "v7u_N001512"
          ],
          "relation_type": null,
          "qualifier": null,
          "source_quote": "evaluates and makes recommendations on a jurisdiction’s implementation and enforcement of the Convention and related instruments."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "evidence_unit_ids": [
            "v7u_N001512"
          ],
          "relation_type": null,
          "qualifier": null,
          "source_quote": "issues reports that detail a jurisdiction’s achievements and challenges, including enforcement of foreign bribery offenses. The reports also document the jurisdiction’s progress since its last evaluation."
        }
      ],
      "split_reason": null
    }
  ],
  "candidate_audit": [
    {
      "candidate_id": "s1c_001",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述的是OECD公约作为法律文书的要求（签署国须立法将贿赂外国公职人员定罪并建立监督机制），属于静态法律义务陈述，不涉及原文明示的业务识别、调查、审查、分析、决策或控制过程，因此不构成流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选独立支持OECD贿赂工作组的评估、建议与报告发布流程，包含明确的业务动作与产出，满足流程定义。"
    }
  ],
  "skip_reason": null
}
```
