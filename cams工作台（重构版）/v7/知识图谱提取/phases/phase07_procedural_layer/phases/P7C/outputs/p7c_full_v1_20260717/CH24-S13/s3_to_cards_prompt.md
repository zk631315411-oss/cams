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

section_id: `CH24-S13`

section_title: `US AML/CFT regulatory landscape > Australia AML regulations`

section_text_with_unit_anchors:

```text
[v7u_N001868|1868] Legislation includes AML/CTF Act 2006 and AML/CTF Amendment Act 2024.
ZH: 澳大利亚反洗钱/反恐怖融资立法包括2006年反洗钱/反恐怖融资法案及2024年修正案

[v7u_N001869|1869] The amendments introduce several provisions, including:
ZH: 修正案引入了若干条款

[v7u_N001870|1870] Extending AML/CFT obligations to DNFBPs.
ZH: 将反洗钱/反恐怖融资义务扩展至指定非金融行业和职业（DNFBPs）

[v7u_N001871|1871] Granting AUSTRAC enhanced enforcement powers.
ZH: 授予AUSTRAC更强的执法权力

[v7u_N001872|1872] Amending tipping off provisions.
ZH: 修改泄密（tipping off）条款

[v7u_N001873|1873] Emphasizing the risk-based approach.
ZH: 强调基于风险的方法（RBA）

[v7u_N001874|1874] Legislation requires entities to comply with the new obligations by 2026.
ZH: 立法要求实体在2026年前遵守新义务

[v7u_N001875|1875] The primary legislation governing AML/CFT in Australia is the Anti-Money Laundering and Counter-Terrorism Financing Act 2006 (AML/CTF Act 2006).
ZH: 澳大利亚反洗钱/反恐怖融资主要立法是2006年反洗钱/反恐怖融资法案

[v7u_N001876|1876] This act requires reporting entities to implement and maintain an AML/CFT compliance program. This program includes risk assessment, internal controls for CDD and regulatory reporting, employee training, and independent reviews.
ZH: 该法案要求报告实体实施并维护反洗钱/反恐怖融资合规计划

[v7u_N001877|1877] Australia recently passed the AML/CTF Amendment Act 2024, which is a significant enhancement of its AML/CFT framework.
ZH: 澳大利亚近期通过了2024年反洗钱/反恐怖融资修正案，显著增强反洗钱/反恐怖融资框架

[v7u_N001878|1878] The purpose of the amendments is to ensure Australia’s laws align with FATF’s international standards and continue to effectively deter, detect, and disrupt money laundering as well as terrorism financing and proliferation financing.
ZH: 修正案旨在使澳大利亚法律符合FATF国际标准

[v7u_N001879|1879] The AML/CTF Amendment Act 2024 introduces several key provisions, including:
ZH: 2024年反洗钱/反恐怖融资修正案引入多项关键条款

[v7u_N001880|1880] Extending AML/CFT obligations to DNFBPs, such as real estate agents, legal professionals, accountants, and dealers in precious metals and stones. This includes the obligations to identify and verify customers, conduct ongoing monitoring, and report suspicious activities to AUSTRAC.
ZH: 反洗钱/反恐怖融资义务扩展至DNFBPs，包括房地产中介、律师、会计师等

[v7u_N001881|1881] Granting AUSTRAC enhanced enforcement powers, including the ability to impose higher penalties for noncompliance, issue remedial directions, and pursue civil and criminal actions against entities that breach AML/CFT obligations.
ZH: AUSTRAC获得增强执法权，可对违反反洗钱/反恐怖融资义务的实体处以更高罚款、发出补救指示并提起民事或刑事诉讼。

[v7u_N001882|1882] Amending tipping off provisions to facilitate greater information sharing between regulatory bodies, law enforcement agencies, and international counterparts.
ZH: 修改举报规定，促进监管机构、执法机构与国际同行之间的信息共享。

[v7u_N001883|1883] Emphasizing the risk-based approach, allowing entities to tailor their AML/CFT measures based on the level of risk identified. This approach ensures that resources are allocated effectively to mitigate higher-risk areas.
ZH: 强调风险为本方法，允许实体根据识别出的风险水平调整反洗钱/反恐怖融资措施，确保资源有效配置以缓解高风险领域。

[v7u_N001884|1884] Reporting entities will be required to comply with many of the new obligations by March 2026.
ZH: 报告实体须在2026年3月前遵守多项新义务。

[v7u_N001885|1885] AUSTRAC is the principal regulatory authority responsible for overseeing the AML/CFT regime in Australia. It acts as both a national FIU and a regulatory agency, collecting and analyzing financial transaction reports, monitoring compliance with AML/CFT obligations, and enforcing regulatory actions against noncompliant entities.
ZH: AUSTRAC是澳大利亚负责监督反洗钱/反恐怖融资制度的主要监管机构，兼具国家FIU和监管机构职能。

[v7u_N001886|1886] The Australian Sanctions Office (ASO) within the Department of Foreign Affairs and Trade (DFAT) administers Australia's sanctions regime, implementing and enforcing UNSC sanctions and Australian autonomous sanctions.
ZH: 澳大利亚制裁办公室（ASO）隶属于外交贸易部，负责管理澳大利亚制裁制度，执行联合国安理会制裁和澳大利亚自主制裁。

[v7u_N001887|1887] DFAT coordinates with AUSTRAC and other regulatory bodies to ensure that entities comply with sanctions obligations.
ZH: 外交贸易部与AUSTRAC及其他监管机构协调，确保实体遵守制裁义务。

[v7u_N001888|1888] Singapore's National AML Strategy was updated in October 2024 and outlines its approach to combat money laundering risks, emphasizing a three-pillar framework of prevention, detection, and enforcement.
ZH: 新加坡于2024年10月更新国家反洗钱战略，强调预防、检测和执法三大支柱框架。

[v7u_N001889|1889] Singapore follows a risk-based approach to AML/CFT compliance. This approach requires financial institutions and DNFBPs to implement CDD, enhanced due diligence for high-risk clients, ongoing transaction monitoring, and suspicious transaction reporting.
ZH: 新加坡要求金融机构和DNFBP实施风险为本的反洗钱/反恐怖融资合规措施，包括客户尽职调查、强化尽职调查、持续交易监控和可疑交易报告。

[v7u_N001890|1890] The key legislation governing AML/CFT in Singapore includes:
ZH: 列举新加坡反洗钱/反恐怖融资关键立法。

[v7u_N001891|1891] The Corruption, Drug Trafficking and Other Serious Crimes (Confiscation of Benefits) Act 1992: Criminalizes money laundering and mandates reporting of suspicious transactions.
ZH: 《腐败、贩毒和其他严重犯罪（没收利益）法》将洗钱定为犯罪并规定可疑交易报告义务。

[v7u_N001892|1892] The Terrorism (Suppression of Financing) Act 2002: Addresses the criminalization and prevention of terrorism financing.
ZH: 《恐怖主义（制止资助）法》将恐怖融资定为犯罪并加以预防。

[v7u_N001893|1893] Singapore's major regulators include:
ZH: 列举新加坡主要监管机构。

[v7u_N001894|1894] Monetary Authority of Singapore: Regulates financial institutions, DNFBPs, and non-profit organizations, and issues AML/CFT guidelines, and supervises compliance.
ZH: 新加坡金融管理局监管金融机构、DNFBP和非营利组织，发布反洗钱/反恐怖融资指引并监督合规。

[v7u_N001895|1895] Commercial Affairs Department of the Singapore Police Force: Investigates financial crimes, including money laundering and fraud.
ZH: 新加坡警察部队商业事务局调查包括洗钱和欺诈在内的金融犯罪。

[v7u_N001896|1896] Accounting and Corporate Regulatory Authority: Oversees corporate entities and enforces AML/CFT obligations on corporate service providers.
ZH: 会计与企业管理局监管企业实体并对企业服务提供商执行反洗钱/反恐怖融资义务。

[v7u_N001897|1897] Casino Regulatory Authority and Gambling Regulatory Authority: Monitor AML/CFT compliance in the gaming sector.
ZH: 赌场监管局和赌博监管局监督博彩业的反洗钱/反恐怖融资合规。

[v7u_N001898|1898] Additionally, DNFBP sectors are regulated for AML/CFT by their licensing authority, registration authority, or self-regulatory body.
ZH: DNFBP行业由其发牌机构、注册机构或自律机构进行反洗钱/反恐怖融资监管。

[v7u_N001899|1899] Precious stones and metal dealers other than pawnbrokers are not considered part of these DNFBP sectors.
ZH: 除当铺外的宝石和贵金属经销商不属于DNFBP行业。

[v7u_N001900|1900] The Suspicious Transaction Reporting Office (STRO) is the FIU of the jurisdiction. STRO is part of the Singapore Police Force and responsible for receiving and analyzing financial intelligence.
ZH: 可疑交易报告办公室（STRO）是新加坡的金融情报机构，隶属于新加坡警察部队，负责接收和分析金融情报。

[v7u_N001901|1901] In addition to the legislation, the following are also useful resources for AFC professionals:
ZH: 除立法外，金融犯罪防控专业人员可参考的其他有用资源

[v7u_N001902|1902] Monetary Authority of Singapore notices and guidelines: Set compliance obligations for obligated entities
ZH: 新加坡金融管理局的通知和指南为义务实体设定合规义务

[v7u_N001903|1903] AML/CFT Industry Partnership guidelines and best practice papers: Enable the financial sector, regulators, law enforcement agencies, and other government entities to collaboratively identify, assess, and mitigate emerging risks. This self-regulatory approach is effective in delivering benefits to customers and strengthening the commercial and investment banking industry.
ZH: 反洗钱/反恐怖融资行业伙伴关系指南和最佳实践文件促进金融业、监管机构、执法机构等协作识别、评估和缓解新兴风险
```

allowed_unit_ids:

```json
[
  "v7u_N001868",
  "v7u_N001869",
  "v7u_N001870",
  "v7u_N001871",
  "v7u_N001872",
  "v7u_N001873",
  "v7u_N001874",
  "v7u_N001875",
  "v7u_N001876",
  "v7u_N001877",
  "v7u_N001878",
  "v7u_N001879",
  "v7u_N001880",
  "v7u_N001881",
  "v7u_N001882",
  "v7u_N001883",
  "v7u_N001884",
  "v7u_N001885",
  "v7u_N001886",
  "v7u_N001887",
  "v7u_N001888",
  "v7u_N001889",
  "v7u_N001890",
  "v7u_N001891",
  "v7u_N001892",
  "v7u_N001893",
  "v7u_N001894",
  "v7u_N001895",
  "v7u_N001896",
  "v7u_N001897",
  "v7u_N001898",
  "v7u_N001899",
  "v7u_N001900",
  "v7u_N001901",
  "v7u_N001902",
  "v7u_N001903"
]
```

## S2 Process IR

```json
{
  "section_id": "CH24-S13",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "报告实体如何依据法律要求建立合规计划？",
      "title": "AML/CTF法案要求报告实体实施合规计划",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "AML/CTF 2006 法案要求",
          "evidence_unit_ids": [
            "v7u_N001875",
            "v7u_N001876"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "报告实体实施并维护 AML/CFT 合规计划",
          "evidence_unit_ids": [
            "v7u_N001876"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "合规计划包括风险评估、内部管控、员工培训和独立审查",
          "evidence_unit_ids": [
            "v7u_N001876"
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
            "v7u_N001876"
          ],
          "source_quote": "This act requires reporting entities to implement and maintain an AML/CFT compliance program."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001876"
          ],
          "source_quote": "This program includes risk assessment, internal controls for CDD and regulatory reporting, employee training, and independent reviews."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "实体如何基于风险水平定制 AML/CFT 措施？",
      "title": "基于风险的方法定制 AML/CFT 措施",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "风险为本方法",
          "evidence_unit_ids": [
            "v7u_N001883"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "根据识别的风险水平定制反洗钱/反恐怖融资措施",
          "evidence_unit_ids": [
            "v7u_N001883"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "资源有效配置以缓解高风险领域",
          "evidence_unit_ids": [
            "v7u_N001883"
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
            "v7u_N001883"
          ],
          "source_quote": "Emphasizing the risk-based approach, allowing entities to tailor their AML/CFT measures based on the level of risk identified."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001883"
          ],
          "source_quote": "This approach ensures that resources are allocated effectively to mitigate higher-risk areas."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "新加坡金融机构如何实施风险为本合规措施？",
      "title": "新加坡风险为本方法要求实施 CDD 等措施",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "新加坡采用的风险为本方法",
          "evidence_unit_ids": [
            "v7u_N001889"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "金融机构和 DNFBPs 实施客户尽职调查、强化尽职调查、持续交易监控和可疑交易报告",
          "evidence_unit_ids": [
            "v7u_N001889"
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
            "v7u_N001889"
          ],
          "source_quote": "Singapore follows a risk-based approach to AML/CFT compliance. This approach requires financial institutions and DNFBPs to implement CDD, enhanced due diligence for high-risk clients, ongoing transaction monitoring, and suspicious transaction reporting."
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
      "reason": "法案要求报告实体实施合规计划，构成明确的义务触发和业务动作。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "修正案扩展义务至 DNFBPs 为法律内容的静态描述，未包含实体的业务行动或判断。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "授予 AUSTRAC 增强执法权为法律权力陈述，不构成实体执行的程序性过程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "强调风险为本且允许实体定制措施，有实体基于风险水平调整措施的业务动作。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "要求金融机构实施具体合规措施，具备明确的义务和业务动作。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "法律将洗钱定为犯罪并规定报告义务，属于静态的法律定性，无程序性迁移。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "法律将恐怖融资定为犯罪并预防，属于静态的法律定性，无程序性迁移。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s13_tippingoff",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "修改泄密条款以促进信息共享，为立法意图与效果描述，未涉及实体执行过程。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s13_compliancedeadline",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "要求实体在2026年前遵守新义务，为静态时间规定，无实体处理过程。"
    }
  ],
  "skip_reason": null
}
```
