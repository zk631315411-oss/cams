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

section_id: `CH06-S07`

section_title: `Money Laundering Risks in Financial Services > Shell and shelf companies risks`

section_text_with_unit_anchors:

```text
[v7u_N000426|426] A shell company or corporation is a company that, at the time of incorporation, has no significant assets or operations.
ZH: 壳公司（shell company）指成立时无重大资产或运营的公司

[v7u_N000427|427] A similarly named "shelf" company is a corporation that has had no activity. It has been created and put "on the shelf" so that it can be sold later to someone who prefers a previously registered corporation over a new one.
ZH: 现成公司（shelf company）是已注册但无活动的公司，可后续出售

[v7u_N000428|428] Both shell and shelf companies are generally kept dormant and used later to appear legitimate while usually masking the beneficial owner.
ZH: 壳公司和现成公司通常保持休眠，用于掩盖受益所有人

[v7u_N000429|429] A front company is an entity that conducts some legitimate business while also shielding another company from liability or scrutiny.
ZH: 幌子公司（front company）从事合法业务同时掩护另一公司

[v7u_N000430|430] Financial criminals might use a front company to conceal illicit activity. For example, they might operate a car wash to launder the profits of drug trafficking.
ZH: 幌子公司可用于洗钱，例如以洗车行掩盖毒品交易利润

[v7u_N000431|431] While there are legitimate uses for shell, shelf, and front companies, within the context of researching and accepting customers, they are considered high risk.
ZH: 壳公司、现成公司和幌公司在客户准入中视为高风险

[v7u_N000432|432] Shell companies can be established with the primary objective of claiming the proceeds of crime as legitimate revenue or commingling criminal proceeds with legitimate revenue. According to the Financial Action Task Force (FATF), the use of shell companies to facilitate financial crime is a well-documented typology.
ZH: 壳公司可用于将犯罪收益混入合法收入，FATF已记录此类型

[v7u_N000433|433] Shell companies can be set up in onshore and offshore locations.
ZH: 壳公司可在在岸和离岸地点设立

[v7u_N000434|434] Their ownership structures can take several forms:
ZH: 壳公司的所有权结构有多种形式

[v7u_N000435|435] Shares can be issued to a natural or legal person in registered or bearer form.
ZH: 股份可以记名或不记名形式发行给自然人或法人

[v7u_N000436|436] Some shell companies can be created for a single purpose or to hold a single asset.
ZH: 部分壳公司可为单一目的或持有单一资产而设立

[v7u_N000437|437] Some shell companies can be established as multipurpose entities.
ZH: 部分壳公司可设立为多用途实体

[v7u_N000438|438] Shell companies are often legally incorporated and registered by the criminal organization but have no legitimate business purpose. Often purchased from lawyers, accountants, or corporate service providers, they are convenient vehicles for bribery and corruption, money laundering, and sanctions evasion.
ZH: 壳公司常由犯罪组织合法注册但无正当商业目的，用于贿赂、洗钱和逃避制裁

[v7u_N000439|439] Sometimes, the stock of these shell corporations is issued in bearer shares, which means that whoever carries them is the purported owner.
ZH: 不记名股票（bearer shares）的持有者即为名义所有人

[v7u_N000440|440] Tax haven countries and their strict secrecy laws can further conceal the true ownership of shell corporations. In addition, the information may be held by professionals who claim secrecy.
ZH: 避税天堂的保密法及专业人士的保密义务可进一步隐藏壳公司真实所有权

[v7u_N000441|441] When FATF reviewed the rules and practices that impair the effectiveness of financial crime prevention and detection systems, it found in particular that shell corporations and nominees are widely used mechanisms to launder the proceeds from crime. As a result, shell companies are considered to represent a higher risk of financial crime.
ZH: FATF发现壳公司和名义人是洗钱高风险机制

[v7u_N000442|442] Danske Bank, Denmark's largest financial institution, became embroiled in a significant money laundering case centered around its Estonian branch. According to Reuters, between 2007 and 2015, approximately €200 billion of suspicious funds were funneled through the bank, primarily originating from Russia as well as Estonia, Latvia, Cyprus, and Great Britain. The scandal became known in 2018, unveiling the intricate use of shell and shelf companies to facilitate the laundering process.
ZH: 丹麦银行爱沙尼亚分行洗钱案涉及壳公司和现成公司

[v7u_N000443|443] One prominent example was the use of United Kingdom limited liability partnerships (LLP) and Scottish limited partnerships (SLP). These entities allowed for minimal disclosure requirements, enabling criminals to hide behind complex ownership structures. The shell companies conducted fictitious transactions and created false invoices to justify the movement of funds, making it difficult for authorities to trace the origins of the illicit money.
ZH: 英国LLP和SLP被用于洗钱，利用低披露要求隐藏所有权

[v7u_N000444|444] The laundering process in the Danske Bank scandal involved multiple steps to layer and integrate the illicit funds.
ZH: 丹麦银行洗钱过程包括多层放置、离析和融合

[v7u_N000445|445] Initially, money was deposited into accounts held by shell and shelf companies in Danske Bank's Estonian branch.
ZH: 资金最初存入丹麦银行爱沙尼亚分行的壳公司和现成公司账户

[v7u_N000446|446] These funds were then transferred through a complex web of transactions involving other shell companies, often spanning multiple jurisdictions.
ZH: 资金通过涉及其他壳公司的复杂交易网络跨境转移

[v7u_N000447|447] By moving the money through various entities and accounts, the criminals created a convoluted trail that was challenging to untangle.
ZH: 犯罪分子通过多个实体和账户转移资金制造混乱的追踪线索

[v7u_N000448|448] The use of false documentation, including fake contracts and invoices, provided legitimacy to the transactions.
ZH: 使用虚假合同和发票等伪造文件为交易提供合法性

[v7u_N000449|449] An additional finding of the scandal revealed that Danske Bank’s head office was unaware of the AML compliance failings, including the lack of an MLRO appointment for over a year, as they did not have adequate oversight and supervision of the Estonian branch and of the transactions that were being processed.
ZH: 丹麦银行总部对爱沙尼亚分行的反洗钱合规失败不知情

[v7u_N000450|450] The Danske Bank scandal had far-reaching consequences for the institution and the broader financial landscape. According to a press release by the US Department of Justice, Danske Bank faced significant regulatory scrutiny, leading to the resignation of several top executives. Danske Bank pleaded guilty to bank fraud conspiracy and paid substantial fines of more than US$2 billion.
ZH: 丹麦银行因洗钱丑闻认罪银行欺诈并支付超20亿美元罚款

[v7u_N000451|451] The scandal also reiterated the importance of robust AML controls and the need for enhanced transparency in financial transactions and adequate supervision of subsidiary businesses and operations if they are remote or overseas in higher-risk jurisdictions.
ZH: 丑闻重申了健全反洗钱控制和海外子公司监管的重要性
```

allowed_unit_ids:

```json
[
  "v7u_N000426",
  "v7u_N000427",
  "v7u_N000428",
  "v7u_N000429",
  "v7u_N000430",
  "v7u_N000431",
  "v7u_N000432",
  "v7u_N000433",
  "v7u_N000434",
  "v7u_N000435",
  "v7u_N000436",
  "v7u_N000437",
  "v7u_N000438",
  "v7u_N000439",
  "v7u_N000440",
  "v7u_N000441",
  "v7u_N000442",
  "v7u_N000443",
  "v7u_N000444",
  "v7u_N000445",
  "v7u_N000446",
  "v7u_N000447",
  "v7u_N000448",
  "v7u_N000449",
  "v7u_N000450",
  "v7u_N000451"
]
```

## S2 Process IR

```json
{
  "section_id": "CH06-S07",
  "episodes": [],
  "candidate_audit": [
    {
      "candidate_id": "s1c_001",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "候选仅为静态定义性陈述，未包含机构根据标准做出判断或触发的后续处理过程，不构成流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "FATF调查发现及其结论属于外部知识，未体现机构内部基于该发现产生的业务判断或程序，不构成流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选描述丑闻调查的发现及原因，属于案例事实披露，未包含可复用的业务处理或判断流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选描述银行在丑闻后的法律认罪及罚款，属于外部法律制裁后果，不构成机构内部可执行或重复的业务流程。"
    }
  ],
  "skip_reason": "当前section内容主要为定义性陈述和案例描述，未发现符合流程定义的程序性或判断性迁移，无符合条件的episode。"
}
```
