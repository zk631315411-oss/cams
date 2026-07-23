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

section_id: `CH19-S04`

section_title: `Financial Action Task Force > FATF Recommendations 24-40`

section_text_with_unit_anchors:

```text
[v7u_N001367|1367] FATF Recommendations 24 to 40 outline key measures to strengthen transparency, institutional oversight, and global cooperation in AML/CFT efforts.
ZH: FATF建议24-40概述加强透明度、机构监督和全球合作的关键措施

[v7u_N001368|1368] Recommendations 24 and 25 advise jurisdictions to assess the risk of misuse of legal persons and legal arrangements.
ZH: FATF建议24和25要求各辖区评估法人和法律安排被滥用的风险

[v7u_N001369|1369] Jurisdictions should also ensure competent authorities can access accurate, up-to-date beneficial ownership information on legal persons and trusts, requiring trustees to obtain and maintain such data for transparency and compliance.
ZH: 各辖区应确保主管机关能获取准确、最新的受益所有人信息

[v7u_N001370|1370] Jurisdictions should not permit legal persons to issue new bearer shares or bearer share warrants and should take measures to prevent the misuse of these types of stocks and documents.
ZH: 各辖区不应允许法人发行新的不记名股票或不记名认股权证

[v7u_N001371|1371] Recommendations 26 to 35 advise jurisdictions to ensure financial institutions are properly regulated and supervised to implement FATF Recommendations effectively.
ZH: FATF建议26-35要求各辖区确保金融机构受到适当监管以有效实施FATF建议

[v7u_N001372|1372] Supervisors should have sufficient authority, resources, and independence to monitor compliance, conduct inspections, and impose sanctions.
ZH: 监管机构应具备充分的权力、资源和独立性以监督合规并实施制裁

[v7u_N001373|1373] Jurisdictions should subject DNFBPs to licensing, registration, and supervision by competent authorities or self-regulatory bodies.
ZH: 各辖区应对指定非金融行业和职业实施许可、注册和监管

[v7u_N001374|1374] Jurisdictions should establish an FIU to analyze suspicious transaction reports and support law enforcement investigations.
ZH: 各辖区应设立金融情报机构以分析可疑交易报告并支持执法调查

[v7u_N001375|1375] Authorities should have powers to track, freeze, and seize criminal assets, enforce cross-border currency controls, and collect AML/CFT statistics.
ZH: 主管机关应有权追踪、冻结和扣押犯罪资产并实施跨境货币管制

[v7u_N001376|1376] Jurisdictions should have clear guidelines, feedback, and proportionate sanctions in place to ensure compliance and enforcement.
ZH: 各辖区应制定明确的指引、反馈和相称的制裁以确保合规与执行

[v7u_N001377|1377] Recommendations 36 to 40 advise jurisdictions to swiftly adopt and fully implement the Vienna, Palermo, and Terrorist Financing Conventions, along with other relevant international agreements.
ZH: 各辖区应迅速采纳并全面实施维也纳公约、巴勒莫公约和反恐融资公约

[v7u_N001378|1378] Jurisdictions should provide broad mutual legal assistance for money laundering and terrorist financing cases, ensuring efficient processes for handling such requests.
ZH: 各辖区应为洗钱和恐怖融资案件提供广泛的司法协助

[v7u_N001379|1379] Jurisdictions should take rapid action to identify, freeze, seize, and confiscate criminal assets at the request of foreign authorities.
ZH: 各辖区应应外国当局请求迅速采取行动识别、冻结、扣押和没收犯罪资产

[v7u_N001380|1380] Additionally, they should ensure extradition for money laundering and terrorist financing, including prosecuting nationals if extradition is not possible.
ZH: 各辖区应确保对洗钱和恐怖融资进行引渡，包括在无法引渡时起诉本国国民

[v7u_N001381|1381] Authorities should facilitate international cooperation through information exchange and joint investigations to combat financial crimes effectively on a global scale.
ZH: FATF建议要求当局通过信息交换和联合调查促进国际合作以打击金融犯罪。
```

allowed_unit_ids:

```json
[
  "v7u_N001367",
  "v7u_N001368",
  "v7u_N001369",
  "v7u_N001370",
  "v7u_N001371",
  "v7u_N001372",
  "v7u_N001373",
  "v7u_N001374",
  "v7u_N001375",
  "v7u_N001376",
  "v7u_N001377",
  "v7u_N001378",
  "v7u_N001379",
  "v7u_N001380",
  "v7u_N001381"
]
```

## S2 Process IR

```json
{
  "section_id": "CH19-S04",
  "episodes": [],
  "candidate_audit": [
    {
      "candidate_id": "s1c_001",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选仅转述 FATF 建议的要求，描述各辖区应评估风险，但未提供任何具体的评估过程、判断步骤或程序性迁移，属于规范性陈述。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选描述辖区应确保主管机关可获取受益所有人信息，属于总体义务要求，未体现原文明示的业务处理或判断流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选要求辖区禁止发行不记名股票并采取措施防止滥用，属于规范性禁令，未包含任何具体的业务判断或程序性迁移。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选概述 FATF 建议要求确保金融机构受监管，属于框架性要求，未描述具体的监管过程或判断。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选说明监管机构应具备的职权，属于静态能力要求，未形成原文明示的触发-执行-结果流程。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选要求对 DNFBP 实施许可、注册和监管，属于义务声明，未包含业务过程中的判断或行动序列。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选提出应设立 FIU 以分析可疑交易报告，属于组织建制要求，未具体描述分析判断的流程步骤。"
    },
    {
      "candidate_id": "s1c_008",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选列出主管机关应具有的权力，属于权限清单，不构成程序性或判断性关系图。"
    },
    {
      "candidate_id": "s1c_009",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选要求制定指引和制裁以确保合规，是制度建设要求，未提供具体的合并、反馈或判断流程细节。"
    },
    {
      "candidate_id": "s1c_010",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选建议采纳和实施国际公约，属于宏观政策义务，没有程序性或判断性元素。"
    },
    {
      "candidate_id": "s1c_011",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选要求提供广泛司法协助，是国际合作义务，未描述具体的处理流程或决策机制。"
    },
    {
      "candidate_id": "s1c_012",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选要求应外国请求采取行动，虽有触发条件（外国请求），但原文仅陈述应然行动，未展开为可建模的程序性步骤。"
    },
    {
      "candidate_id": "s1c_013",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选包含条件分支（无法引渡时起诉），但整体仍为辖区总体义务的陈述，未描述具体的判断过程或行动执行流程。"
    },
    {
      "candidate_id": "s1c_014",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选要求通过信息交换等促进国际合作，属于职责描述，没有原文明示的业务判断或程序迁移。"
    }
  ],
  "skip_reason": "本节为 FATF 建议 24-40 的概述，内容均为对各辖区应达到的能力或采取的措施的规范性要求，缺少原文明示的具体业务流程、判断步骤或程序性迁移，不满足流程 episode 的正向定义，因此无 episode 输出。"
}
```
