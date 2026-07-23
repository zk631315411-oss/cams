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

section_id: `CH24-S03`

section_title: `US AML/CFT regulatory landscape > The Anti-Money Laundering Act of 2020`

section_text_with_unit_anchors:

```text
[v7u_N001710|1710] The main focus of the Anti-Money Laundering Act of 2020 (known as the AML Act in the US) was to modernize US banking laws and regulations for AML compliance.
ZH: 2020年《反洗钱法案》旨在现代化美国银行反洗钱合规法规

[v7u_N001711|1711] The act also broadens the use of AML practices to further national security and intelligence goals through greater transparency and enforcement measures.
ZH: 该法案通过提高透明度和执法措施，扩大反洗钱实践以促进国家安全和情报目标

[v7u_N001712|1712] This included the creation of a national Beneficial Ownership database, which will be updated with ownership information for entities required to register.
ZH: 创建国家受益所有人数据库，要求实体登记所有权信息

[v7u_N001713|1713] Additional rules, such as which financial institutions can access the database and how that information may be used, are anticipated in the future.
ZH: 预计未来将出台关于数据库访问权限和使用规则的补充规定

[v7u_N001714|1714] For example, the act expands AML compliance to include jurisdiction over activities in cryptocurrencies such as Bitcoin, as well as art and antique dealers.
ZH: 反洗钱合规范围扩大至加密货币及艺术品和古董经销商

[v7u_N001715|1715] The AML Act also includes new investigative powers regarding foreign financial institutions, while creating new criminal penalties for hiding transactions related to senior foreign political figures.
ZH: 新增针对外国金融机构的调查权，并对隐藏与外国高级政治人物相关交易的行为设定刑事处罚

[v7u_N001716|1716] The AML Act represents a strategic update to US banking law by including new financial technologies as well as national security priorities in AML compliance.
ZH: 《反洗钱法案》将新金融技术和国家安全优先事项纳入反洗钱合规，是美国银行法的战略更新

[v7u_N001717|1717] For example, the AML Act requires shell companies and other previously unregulated legal entities to disclose their beneficial owners and register ownership structures with FinCEN.
ZH: 要求壳公司等实体向FinCEN披露受益所有人并注册所有权结构

[v7u_N001718|1718] The act also extends protection for whistleblowers who alert authorities of AML regulatory violations.
ZH: 法案扩大对举报反洗钱违规行为的举报人保护

[v7u_N001719|1719] The goal is to broaden investigative powers to outline connections between entities like shell companies and their relationships with correspondent banks around the globe.
ZH: 目标是扩大调查权，以揭示壳公司等实体与全球代理行之间的关系

[v7u_N001720|1720] The AML Act also updates existing AML regulations to include cryptocurrency exchanges. They are considered to be money services businesses and have the same licensing and reporting requirements.
ZH: 法案将加密货币交易所视为货币服务企业，适用相同的许可和报告要求

[v7u_N001721|1721] Another goal of the AML Act is to transform SARs from a simple reporting requirement to a tool for intelligence gathering. SARs are now expected to provide a “high degree of usefulness” for law enforcement and national security agencies.
ZH: 《反洗钱法》将可疑交易报告转变为高价值情报工具

[v7u_N001722|1722] Additionally, there are provisions to facilitate cross-border sharing of SARs within financial institutions.
ZH: 《反洗钱法》允许金融机构内部跨境共享可疑交易报告

[v7u_N001723|1723] The AML Act also requires the development of further regulations to enhance strategic priorities regarding:
ZH: 《反洗钱法》要求制定进一步法规以强化战略优先事项

[v7u_N001724|1724] Corruption and fraud.
ZH: 战略优先事项包括腐败与欺诈

[v7u_N001725|1725] Cybercrime.
ZH: 战略优先事项包括网络犯罪

[v7u_N001726|1726] Terrorist financing.
ZH: 战略优先事项包括恐怖融资

[v7u_N001727|1727] Transnational criminal activity.
ZH: 战略优先事项包括跨国犯罪活动

[v7u_N001728|1728] Drug trafficking.
ZH: 战略优先事项包括毒品贩运

[v7u_N001729|1729] Human trafficking.
ZH: 战略优先事项包括人口贩运

[v7u_N001730|1730] Nuclear proliferation financing.
ZH: 战略优先事项包括核扩散融资

[v7u_N001731|1731] Pursuant to the AML Act, FinCEN has issued several notices of proposed rulemaking to further implement the AML Act. These include:
ZH: FinCEN 根据《反洗钱法》发布多项拟议规则制定通知

[v7u_N001732|1732] The requirement to maintain risk-based AML/CFT programs, such as mandatory risk assessment processes.
ZH: 要求维持基于风险的 反洗钱/反恐怖融资 计划，包括强制性风险评估流程

[v7u_N001733|1733] The incorporation of national priorities in institutions’ AML/CFT programs.
ZH: 要求将国家优先事项纳入机构的 反洗钱/反恐怖融资 计划

[v7u_N001734|1734] Additional rulemaking to further implement the AML Act and its legislative objectives will likely continue.
ZH: 《反洗钱法》的进一步规则制定可能会继续

[v7u_N001735|1735] The Financial Crimes Enforcement Network (FinCEN) is a bureau within the US Department of the Treasury. Its director reports to the Under Secretary for Terrorism and Financial Intelligence. FinCEN’s mission is to protect the financial system from illicit activities, combat financial crimes, and enhance national security.
ZH: FinCEN 是美国财政部下属机构，负责保护金融体系、打击金融犯罪并加强国家安全

[v7u_N001736|1736] The US Congress designates FinCEN as the central authority that collects, analyzes, and disseminates financial transaction data to support law enforcement, regulatory agencies, and policymakers.
ZH: 美国国会指定 FinCEN 为收集、分析和传播金融交易数据的中央权威机构

[v7u_N001737|1737] FinCEN’s analysis of data specifically plays a crucial role in combating AML and CFT as it assists in tracking fraud, tax evasion, narcotics trafficking, and terrorist financing.
ZH: FinCEN 的数据分析在打击洗钱和恐怖融资中发挥关键作用

[v7u_N001738|1738] FinCEN operates under the Bank Secrecy Act, which was amended by the USA PATRIOT Act.
ZH: FinCEN 依据《银行保密法》运作，该法经《爱国者法案》修订

[v7u_N001739|1739] The Bank Secrecy Act and its amendments grant FinCEN the authority to issue regulations, enforce compliance, and oversee AML programs in financial institutions.
ZH: 《银行保密法》授权 FinCEN 发布法规、执行合规并监督金融机构的反洗钱计划

[v7u_N001740|1740] For instance, FinCEN sets the standards for what constitutes suspicious activity and ensures that financial institutions properly file reports that could prove useful in criminal, tax, and counterterrorism investigations.
ZH: FinCEN 设定可疑活动标准并确保金融机构正确提交报告以支持调查

[v7u_N001741|1741] Additionally, FinCEN manages the collection, processing, storage, dissemination, and protection of Bank Secrecy Act data.
ZH: FinCEN 负责管理、保护《银行保密法》数据。

[v7u_N001742|1742] It partners with law enforcement in searching for information to investigate and prosecute entities involved in financial crime.
ZH: FinCEN 与执法部门合作，支持金融犯罪调查与起诉。

[v7u_N001743|1743] As the US FIU, FinCEN collaborates globally with over 100 FIUs within the Egmont Group, sharing financial intelligence to detect illicit financial flows. It also maintains a government-wide access service for financial crime data, helping federal, state, local, and international partners.
ZH: FinCEN 作为美国 FIU，与全球 100 多个 FIU 合作共享金融情报。

[v7u_N001744|1744] FinCEN’s key functions include:
ZH: FinCEN 的主要职能包括以下方面。

[v7u_N001745|1745] Issuing and enforcing AML/CFT regulations.
ZH: FinCEN 负责发布和执行 反洗钱/反恐怖融资 法规。

[v7u_N001746|1746] Supporting law enforcement in investigations and prosecutions.
ZH: FinCEN 支持执法部门的调查和起诉工作。

[v7u_N001747|1747] Managing and protecting Bank Secrecy Act data.
ZH: FinCEN 管理和保护《银行保密法》数据。

[v7u_N001748|1748] Coordinating with foreign FIUs on cross-border financial crime.
ZH: FinCEN 与外国 FIU 协调打击跨境金融犯罪。

[v7u_N001749|1749] Identifying financial crime risks and assisting with resource allocation.
ZH: FinCEN 识别金融犯罪风险并协助资源分配。

[v7u_N001750|1750] US financial regulators work collectively to ensure the financial system’s stability, integrity, and efficiency. The Office of the Comptroller of the Currency (OCC), Federal Reserve System (FRS), Federal Deposit Insurance Corporation (FDIC), and Securities and Exchange Commission (SEC) create a framework that safeguards financial institutions and consumers, mitigating risks that could threaten economic stability. They enforce compliance, promote transparency, and protect investors and depositors, while ensuring trust in financial markets.
ZH: 美国金融监管机构共同维护金融体系的稳定、完整和效率。

[v7u_N001751|1751] The OCC is an independent bureau within the US Department of the Treasury responsible for chartering, regulating, and supervising all national banks, federal savings associations, and US branches of foreign banks.
ZH: OCC 是财政部下属独立机构，负责全国性银行和联邦储蓄协会的监管。

[v7u_N001752|1752] It ensures that financial institutions operate safely and soundly, provide fair access to financial services, treat customers fairly, and comply with laws and regulations.
ZH: OCC 确保金融机构安全稳健运营、公平对待客户并遵守法律法规。

[v7u_N001753|1753] The FRS serves as the central bank of the US, working to ensure financial system stability by minimizing and containing systemic risks.
ZH: FRS 作为美国中央银行，致力于维护金融体系稳定。

[v7u_N001754|1754] It conducts several types of examinations to promote the safety and soundness of financial institutions while enhancing the efficiency and security of payment and settlement systems.
ZH: FRS 开展多种检查以促进金融机构安全稳健及支付结算系统效率。

[v7u_N001755|1755] Additionally, the FRS provides services to the banking industry and the US government, facilitating US dollar transactions and payments.
ZH: FRS 为银行业和美国政府提供美元交易和支付服务。

[v7u_N001756|1756] The FDIC is an independent agency established by Congress to uphold stability and public confidence in the US financial system. It fulfills this mission by insuring deposits, supervising financial institutions for safety, soundness, and consumer protection, and ensuring that financial institutions can be restructured or liquidated in an orderly manner if they fail.
ZH: FDIC 通过存款保险和监管维护金融体系稳定与公众信心。

[v7u_N001757|1757] The SEC oversees all aspects of the securities industry, ensuring investor protection, fair, orderly, and efficient markets, and capital formation.
ZH: SEC 监管证券行业，保护投资者并确保市场公平有序。

[v7u_N001758|1758] The president, with the Senate’s advice and consent, appoints up to five commissioners to lead the agency.
ZH: SEC 由总统任命并经参议院同意的最多五名委员领导。

[v7u_N001759|1759] By overseeing banking operations, managing systemic risks, insuring deposits, and regulating securities, these regulators collectively foster a resilient and well-functioning financial industry.
ZH: 各监管机构共同促进金融业的韧性和良好运作。

[v7u_N001760|1760] If a financial institution is found in violation of US laws and regulations related to financial crime, these regulators can impose civil monetary penalties, forfeiture of proceeds, limitations on future business activities, and criminal charges against the bank or its officers.
ZH: 金融机构违反金融犯罪法规时，监管机构可处以民事罚款、没收收益、限制业务或提起刑事指控。
```

allowed_unit_ids:

```json
[
  "v7u_N001710",
  "v7u_N001711",
  "v7u_N001712",
  "v7u_N001713",
  "v7u_N001714",
  "v7u_N001715",
  "v7u_N001716",
  "v7u_N001717",
  "v7u_N001718",
  "v7u_N001719",
  "v7u_N001720",
  "v7u_N001721",
  "v7u_N001722",
  "v7u_N001723",
  "v7u_N001724",
  "v7u_N001725",
  "v7u_N001726",
  "v7u_N001727",
  "v7u_N001728",
  "v7u_N001729",
  "v7u_N001730",
  "v7u_N001731",
  "v7u_N001732",
  "v7u_N001733",
  "v7u_N001734",
  "v7u_N001735",
  "v7u_N001736",
  "v7u_N001737",
  "v7u_N001738",
  "v7u_N001739",
  "v7u_N001740",
  "v7u_N001741",
  "v7u_N001742",
  "v7u_N001743",
  "v7u_N001744",
  "v7u_N001745",
  "v7u_N001746",
  "v7u_N001747",
  "v7u_N001748",
  "v7u_N001749",
  "v7u_N001750",
  "v7u_N001751",
  "v7u_N001752",
  "v7u_N001753",
  "v7u_N001754",
  "v7u_N001755",
  "v7u_N001756",
  "v7u_N001757",
  "v7u_N001758",
  "v7u_N001759",
  "v7u_N001760"
]
```

## S2 Process IR

```json
{
  "section_id": "CH24-S03",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "壳公司等实体如何被要求向FinCEN披露受益所有人并注册所有权结构？",
      "title": "壳公司等实体向FinCEN披露受益所有人并注册",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "壳公司及其他未受监管的法律实体",
          "evidence_unit_ids": [
            "v7u_N001717"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "向FinCEN披露受益所有人并注册所有权结构",
          "evidence_unit_ids": [
            "v7u_N001717"
          ],
          "modality": "required"
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
            "v7u_N001717"
          ],
          "source_quote": "For example, the AML Act requires shell companies and other previously unregulated legal entities to disclose their beneficial owners and register ownership structures with FinCEN."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "加密货币交易所如何被归类为货币服务企业并适用相应要求？",
      "title": "加密货币交易所被归为货币服务企业并适用许可报告要求",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "加密货币交易所",
          "evidence_unit_ids": [
            "v7u_N001720"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "视为货币服务企业",
          "evidence_unit_ids": [
            "v7u_N001720"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "适用相同的许可和报告要求",
          "evidence_unit_ids": [
            "v7u_N001720"
          ],
          "modality": "required"
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
            "v7u_N001720"
          ],
          "source_quote": "The AML Act also updates existing AML regulations to include cryptocurrency exchanges. They are considered to be money services businesses and have the same licensing and reporting requirements."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001720"
          ],
          "source_quote": "The AML Act also updates existing AML regulations to include cryptocurrency exchanges. They are considered to be money services businesses and have the same licensing and reporting requirements."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "AML Act 如何允许金融机构内部跨境共享 SAR？",
      "title": "允许金融机构内部跨境共享可疑交易报告",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "金融机构内部",
          "evidence_unit_ids": [
            "v7u_N001722"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "跨境共享可疑交易报告",
          "evidence_unit_ids": [
            "v7u_N001722"
          ],
          "modality": "permitted"
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
            "v7u_N001722"
          ],
          "source_quote": "Additionally, there are provisions to facilitate cross-border sharing of SARs within financial institutions."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_005",
        "s1c_gap_003"
      ],
      "focal_question": "FinCEN 如何根据 AML Act 要求机构加强 AML/CFT 计划？",
      "title": "FinCEN 发布拟议规则要求机构进行风险为本计划和国家优先事项纳入",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "AML Act",
          "evidence_unit_ids": [
            "v7u_N001731"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "FinCEN发布拟议规则通知",
          "evidence_unit_ids": [
            "v7u_N001731"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "金融机构维持基于风险的AML/CFT计划，包括强制性风险评估流程",
          "evidence_unit_ids": [
            "v7u_N001732"
          ],
          "modality": "required"
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "金融机构将国家优先事项纳入其AML/CFT计划",
          "evidence_unit_ids": [
            "v7u_N001733"
          ],
          "modality": "required"
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
            "v7u_N001731"
          ],
          "source_quote": "Pursuant to the AML Act, FinCEN has issued several notices of proposed rulemaking to further implement the AML Act."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001732"
          ],
          "source_quote": "The requirement to maintain risk-based AML/CFT programs, such as mandatory risk assessment processes."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001733"
          ],
          "source_quote": "The incorporation of national priorities in institutions’ AML/CFT programs."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "FinCEN 如何设定可疑活动标准并确保报告提交以支持调查？",
      "title": "FinCEN设定可疑活动标准并确保提交有用报告",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "FinCEN设定可疑活动标准",
          "evidence_unit_ids": [
            "v7u_N001740"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "确保金融机构正确提交可疑活动报告",
          "evidence_unit_ids": [
            "v7u_N001740"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "报告可能对刑事、税务和反恐调查有用",
          "evidence_unit_ids": [
            "v7u_N001740"
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
            "v7u_N001740"
          ],
          "source_quote": "FinCEN sets the standards for what constitutes suspicious activity and ensures that financial institutions properly file reports that could prove useful in criminal, tax, and counterterrorism investigations."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N001740"
          ],
          "source_quote": "FinCEN sets the standards for what constitutes suspicious activity and ensures that financial institutions properly file reports that could prove useful in criminal, tax, and counterterrorism investigations."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_007"
      ],
      "focal_question": "发现违规后监管机构如何处罚？",
      "title": "金融机构违规后监管机构施加处罚",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "decision",
          "label": "金融机构被发现在金融犯罪相关法规下违规",
          "evidence_unit_ids": [
            "v7u_N001760"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "监管机构可处以民事罚款、没收收益、限制业务活动或刑事指控",
          "evidence_unit_ids": [
            "v7u_N001760"
          ],
          "modality": "permitted"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": "a financial institution is found in violation of US laws and regulations related to financial crime",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001760"
          ],
          "source_quote": "If a financial institution is found in violation of US laws and regulations related to financial crime, these regulators can impose civil monetary penalties, forfeiture of proceeds, limitations on future business activities, and criminal charges against the bank or its officers."
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
      "reason": "该候选描述了AML Act要求壳公司等实体披露受益所有人并注册，构成程序性要求，有明确动作和方向。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了加密货币交易所被归类为货币服务企业并适用相应要求，包含分类判断和后续要求，构成流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选为立法目标（转变SAR为情报工具，提供高度有用性），没有原文明示的业务过程、判断或行动，属于静态期望而非程序性迁移。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述了允许金融机构内部跨境共享SAR，包含允许的动作和范围。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选描述了FinCEN发布拟议规则要求机构维持基于风险的AML/CFT计划，构成规则制定和执行要求的过程。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选描述了FinCEN设定标准并确保提交报告，有明确动作和产出。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "该候选描述了违规发现后监管机构施加处罚，包含条件判断和后续执行，是典型的程序性迁移。"
    },
    {
      "candidate_id": "s1c_gap_001",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选为立法设定刑事处罚，未描述机构或个人的具体流程或判断，属于法律后果的静态规定。"
    },
    {
      "candidate_id": "s1c_gap_002",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选为扩大举报人保护，是法定保护措施，不包含原文明示的程序性判断或行动。"
    },
    {
      "candidate_id": "s1c_gap_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选为FinCEN拟议规则的一部分，与s1c_005同属一个规则制定过程，提供国家优先事项纳入要求。"
    }
  ],
  "skip_reason": null
}
```
