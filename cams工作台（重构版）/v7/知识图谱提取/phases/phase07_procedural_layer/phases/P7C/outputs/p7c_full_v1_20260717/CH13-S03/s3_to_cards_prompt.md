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

section_id: `CH13-S03`

section_title: `Money laundering risks associated with cryptoassets and other FinTechs > Central bank digital currency`

section_text_with_unit_anchors:

```text
[v7u_N001016|1016] A central bank digital currency (CBDC) is a digital version of a country’s fiat currency issued and regulated by its central bank. It also functions as legal tender.
ZH: 央行数字货币（CBDC）是由央行发行和监管的数字法定货币，具有法定货币地位

[v7u_N001017|1017] CBDCs combine the advantages of digital payments, such as speed and convenience, with the stability of traditional currencies.
ZH: CBDC兼具数字支付的速度便利和传统货币的稳定性

[v7u_N001018|1018] While often discussed alongside cryptocurrencies such as Bitcoin and Ethereum, CBDCs are different because cryptocurrencies operate independently of government oversight.
ZH: CBDC与加密货币不同，加密货币独立于政府监管

[v7u_N001019|1019] Central banks issue CBDCs for several reasons:
ZH: 列出央行发行CBDC的原因

[v7u_N001020|1020] Payment efficiency: CBDCs can facilitate faster and more efficient payment systems both domestically and internationally compared to conventional systems.
ZH: CBDC可促进国内外更快速高效的支付系统

[v7u_N001021|1021] Cost reduction: The issuance of a CBDC can reduce the costs associated with physical cash production and handling. It also reduces the operational expenses related to clearing and settlement systems used in traditional banking.
ZH: 发行CBDC可降低现金生产和处理成本，并减少传统清算结算系统的运营费用。

[v7u_N001022|1022] Monetary policy implementation: Central banks can influence monetary policy more directly through CBDCs by adjusting the supply and demand for digital currency. This enables the central banks to more readily respond to economic changes or manage economic instability.
ZH: 央行可通过CBDC更直接地实施货币政策，快速应对经济变化或不稳定。

[v7u_N001023|1023] Financial inclusion: A well-designed CBDC could grant access to banking services for individuals excluded from the traditional financial system, particularly in countries with underdeveloped banking infrastructure. The access makes it easier for unbanked populations to obtain basic financial services.
ZH: 设计良好的CBDC可为无银行账户人群提供金融服务，促进金融包容性。

[v7u_N001024|1024] Illicit activity deterrence: Unlike cash, CBDCs can be monitored in real time, providing authorities with greater transparency over transactions. This monitoring can help combat money laundering, tax evasion, and terrorist financing.
ZH: CBDC可实时监控交易，提高透明度，有助于打击洗钱、逃税和恐怖融资。

[v7u_N001025|1025] Several countries are actively researching, piloting, or already implementing CBDCs, each with distinct goals and strategies. Some examples include:
ZH: 多个国家正在研究、试点或实施CBDC，各有不同目标和策略。

[v7u_N001026|1026] The Bahamas: The Sand Dollar is the first fully implemented CBDC in the world, launched in October 2020 and available across the island for use alongside traditional cash. The initiative aims to improve financial inclusion and enhance security against money laundering and illicit activities.
ZH: 巴哈马的Sand Dollar是全球首个全面实施的CBDC，旨在提升金融包容性和反洗钱安全性。

[v7u_N001027|1027] Nigeria: The eNaira was launched in October 2021. It facilitates digital payments, transfers, and transactions, aiming to increase financial inclusion and streamline cash management across the country.
ZH: 尼日利亚的eNaira于2021年10月推出，旨在促进数字支付和金融包容性。

[v7u_N001028|1028] Jamaica: Jamaica Digital Exchange (Jam-Dex) was launched in May 2022. It enables secure P2P transactions and payments for goods and services. It aims to reduce the costs associated with cash handling and storage.
ZH: 牙买加的Jam-Dex于2022年5月推出，支持安全的点对点交易和支付。
```

allowed_unit_ids:

```json
[
  "v7u_N001016",
  "v7u_N001017",
  "v7u_N001018",
  "v7u_N001019",
  "v7u_N001020",
  "v7u_N001021",
  "v7u_N001022",
  "v7u_N001023",
  "v7u_N001024",
  "v7u_N001025",
  "v7u_N001026",
  "v7u_N001027",
  "v7u_N001028"
]
```

## S2 Process IR

```json
{
  "section_id": "CH13-S03",
  "episodes": [],
  "candidate_audit": [
    {
      "candidate_id": "s1c_001",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选描述 CBDC 可被实时监控并提供透明度，有助于打击洗钱等非法活动，但原文仅为能力陈述和效果说明，未包含任何原文明示的业务判断、调查、审查或决策过程，缺乏程序性迁移。不符合流程的正面定义。"
    },
    {
      "candidate_id": "s1c_gap_ch13_s03_monetary_policy",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选描述央行通过 CBDC 调整供需来影响货币政策实施，以快速应对经济变化，但原文仅为货币政策工具的能力介绍，未呈现具体的触发条件、业务判断标准或决策路径，属于知识性说明，不构成流程 episode。"
    }
  ],
  "skip_reason": "本节内容为 CBDC 的定义、特点和发行原因的说明性介绍。候选关系（监控助力反洗钱、调整供需影响货币政策）均属于静态特性或能力描述，没有原文明示的程序性判断或业务处理链，因此无符合条件的 episode 生成。"
}
```
