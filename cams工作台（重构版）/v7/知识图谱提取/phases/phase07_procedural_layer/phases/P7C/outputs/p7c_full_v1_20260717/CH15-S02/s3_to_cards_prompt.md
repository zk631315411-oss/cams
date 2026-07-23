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

section_id: `CH15-S02`

section_title: `Money laundering risks associated with DNFBPs > Gaming sector risks`

section_text_with_unit_anchors:

```text
[v7u_N001071|1071] The gaming sector includes physical and virtual casinos, internet gaming, and betting or gambling.
ZH: 博彩业包括实体赌场、虚拟赌场、互联网游戏及投注或赌博

[v7u_N001072|1072] Gaming operators offer various products and services based on their local regulations.
ZH: 博彩运营商根据当地法规提供不同的产品和服务

[v7u_N001073|1073] This means that the financial crime risk associated with each gaming segment is unique.
ZH: 每个博彩细分领域具有独特的金融犯罪风险

[v7u_N001074|1074] For example, both casinos and online operators are vulnerable to many forms of money laundering, such as customers converting illicit funds into chips, engaging in minimal play, and using falsified documents to open multiple accounts.
ZH: 赌场和在线运营商均易遭受多种洗钱方式，如筹码转换和伪造文件开户

[v7u_N001075|1075] The gaming sector has unique characteristics that carry inherently high financial crime risks.
ZH: 博彩业具有固有高金融犯罪风险的独特特征

[v7u_N001076|1076] These include risks associated with a fragmented regulatory environment, the cross-border nature of activities, and the offering of quasi-financial services.
ZH: 博彩业风险因素包括监管环境碎片化、跨境活动和准金融服务

[v7u_N001077|1077] Another inherent risk arises from the variety, frequency, and volume of transactions.
ZH: 交易种类、频率和数量带来的固有风险

[v7u_N001078|1078] This situation is further complicated by the rapid growth of online gaming, which involves non-face-to-face customer interactions and onboarding, along with emerging technologies that often introduce vulnerabilities alongside opportunity.
ZH: 在线游戏增长带来非面对面交互和新兴技术漏洞

[v7u_N001079|1079] Since online gaming operators onboard customers remotely, they might face exposure to high-risk jurisdictions.
ZH: 远程开户使在线博彩运营商面临高风险司法管辖区敞口

[v7u_N001080|1080] The quick onboarding process appeals to criminals, and the risk of identity fraud escalates when necessary controls are lacking.
ZH: 快速开户流程吸引犯罪分子，缺乏控制时身份欺诈风险上升

[v7u_N001081|1081] Additionally, online gaming operators might inadvertently permit customers outside the jurisdiction to participate in gaming if IP spoofing occurs or geolocation safeguards fail, usually facilitated by users accessing the website or mobile application through a VPN.
ZH: 在线博彩运营商可能因IP欺骗或地理定位失败而允许辖区外客户参与

[v7u_N001082|1082] Physical casinos encounter certain financial crime risks as well.
ZH: 实体赌场面临金融犯罪风险

[v7u_N001083|1083] While they are not classified as financial institutions, they do provide quasi-financial services.
ZH: 赌场虽非金融机构但提供准金融服务

[v7u_N001084|1084] For example, they accept funds on account, perform money and foreign currency exchanges, facilitate money transfers, provide stored-value services, cash checks, and offer safe deposit boxes.
ZH: 赌场提供的准金融服务包括资金托管、货币兑换、转账、储值、支票兑现和保险箱

[v7u_N001085|1085] These services potentially expose them to many of the same risks faced by financial institutions.
ZH: 赌场因提供准金融服务而面临与金融机构类似的风险

[v7u_N001086|1086] Junkets, a form of tourism, including sponsored or incentive-based trips, are also inherently high-risk due to the cross-border movement of funds and people, particularly involving high-net-worth individuals.
ZH: 赌团因跨境资金和人员流动及涉及高净值人士而具有高风险

[v7u_N001087|1087] Junket operators refer clients to casinos and seldom collect KYC details from the customers and share them with casinos. This practice introduces risks regarding transparency of customer identification and source of funds.
ZH: 赌团运营商不收集了解你的客户信息导致客户身份和资金来源透明度风险

[v7u_N001088|1088] Both physical and online gaming are susceptible to certain financial crime risks.
ZH: 实体和在线博彩均易受金融犯罪风险影响

[v7u_N001089|1089] They encounter criminal threats such as organized crime, loan sharking, prostitution, drug dealing, and human trafficking, all of which are predicate offenses.
ZH: 博彩业面临有组织犯罪、高利贷、卖淫、毒品和人口贩卖等上游犯罪威胁

[v7u_N001090|1090] They are also at risk of transaction structuring to evade reporting thresholds, including the use of third parties and multiple transactions to arrange deposits.
ZH: 博彩业存在通过第三方和多笔交易规避报告门槛的结构化交易风险

[v7u_N001091|1091] In peer-to-peer or collusion gaming, such as poker, participants might intentionally lose to another player to transfer value and potentially criminal proceeds.
ZH: 在P2P或串通博彩中参与者可能故意输牌以转移价值
```

allowed_unit_ids:

```json
[
  "v7u_N001071",
  "v7u_N001072",
  "v7u_N001073",
  "v7u_N001074",
  "v7u_N001075",
  "v7u_N001076",
  "v7u_N001077",
  "v7u_N001078",
  "v7u_N001079",
  "v7u_N001080",
  "v7u_N001081",
  "v7u_N001082",
  "v7u_N001083",
  "v7u_N001084",
  "v7u_N001085",
  "v7u_N001086",
  "v7u_N001087",
  "v7u_N001088",
  "v7u_N001089",
  "v7u_N001090",
  "v7u_N001091"
]
```

## S2 Process IR

```json
{
  "section_id": "CH15-S02",
  "episodes": [],
  "candidate_audit": [
    {
      "candidate_id": "s1c_gap_ch15_s02_online_gaming_jurisdiction_risk",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述基于IP欺骗或地理定位失败导致的无意允许辖区外客户参与的风险场景，原文无业务过程、判断或行动，不满足程序性迁移定义。"
    },
    {
      "candidate_id": "s1c_gap_ch15_s02_junket_high_risk",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "静态风险分类，仅说明赌团因跨境资金与高净值人士而具有高风险，无触发、约束或产生业务判断或程序。"
    },
    {
      "candidate_id": "s1c_gap_ch15_s02_junket_kyc_risk",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述赌团运营商不收集KYC导致透明度风险，属于实践与风险知识描述，无原文明示的流程或判断。"
    }
  ],
  "skip_reason": "本节所有合并候选均为博彩业固有风险与脆弱性的描述，缺乏原文明示的程序性或判断性迁移（如业务处理、决策或控制过程），无合格episode可建模。"
}
```
