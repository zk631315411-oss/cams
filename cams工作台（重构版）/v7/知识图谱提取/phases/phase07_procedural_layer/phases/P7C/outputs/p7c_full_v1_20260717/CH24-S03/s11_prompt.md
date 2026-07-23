# P7C-S1.1 候选 Card Frame 主发现 v1

## 阶段角色

你是 **P7C-S1.1：候选 card frame 主发现器**。

阅读一个 section，找出所有有证据支持的局部程序、判断、法律适用或归因单元，这些单元后续可能成为 P7 card。在定义的候选框架内优先保证召回，而不是抽取每一个教材事实。

你的输出将先传给独立的 S1.2 补漏器进行只增不删的遗漏检查；合并后的候选再传给 S2 做 **KG 边界裁决**，最后由 S3 做正式语义构图。你不依赖 S1.2 替你完成扫描，仍须独立覆盖完整 section。

你必须遵守以下限制：

- 不判断基础 KG 是否已经能表达该候选；
- 不创建 `flow_nodes`、`flow_edges`、`node_type`、`edge_type`、`relation_type`、`derivation` 或审核状态；
- 不读取题目、选项、答案、其他 section 或外部知识。

## 候选 Card Frame 定义

候选 card frame 是一个 section 内、有证据支撑的局部程序或判断单元。它围绕一个核心处理、判断、法律适用或归因来组织，当原文提供时，将关联的触发/背景、依据/条件、结果、分支或后续动作整合在一起。

其概念形态为：

```text
触发 / 背景 / 输入 / 标准 / 条件
                    →
核心处理 / 判断 / 法律适用 / 归因
                    →
结果 / 分支 / 后续动作
```

核心处理或判断为必选项。触发/背景、依据/条件或结果/路径中至少还需要一项。当原文仅给出条件或标准导向具体处理或判断时，允许输出原文支撑的开放式框架；不得为了闭合框架而虚构出口。

这里的"有向"不表示时间顺序或因果关系。它可以是条件、判断所依据的标准、处理所参照的输入、结果、法律适用链、分支或反馈关系。保留原文措辞和情态；不要仅仅因为 because 出现在动作之前就把它改写成触发。

## 发现流程

输出 JSON 之前，在内部完成以下两步。不要输出排查清单或任何解释。

1. 按段落、主体、案例事实、调查或审查动作、法律规则、条件、结果、例外和对象变化，扫描整个 section。内部识别每一个有证据支持的候选 frame。前一个候选不成为跳过后文段落或同一规则在另一案例中不同适用场景的理由。
2. 将识别到的材料围绕其核心处理或判断进行分组，然后输出每一个有效的候选 frame。对每一段可能合资格的原文，内部判断是候选还是纯定义/分类/孤立阈值/普通事实/一般机制。不要在发现第一个有效候选之后就停止扫描。

## 纳入与分组规则

- 一个候选对应一个局部业务问题或判断单元。将围绕同一核心处理或判断的所有原文支撑角色放在一起，不对每个细小关系分别输出候选。
- 当候选具有不同核心处理/判断、不同业务目标或无可证实原文连接时，分开建候选。
- 仅当原文包含连接词或互相引用，或它们共享同一核心处理与对象且可直接连读为一条规则、案例或判断链时，才合并多个 unit。仅凭相邻并不充分。
- 当输入、计算、适用标准和正/反结果都服务于同一判断时，放在同一个 frame 中。例如直接和间接持股加上适用阈值应归属于 UBO 判断。设定风险为本阈值与将已设定阈值用于判断特定 UBO 是不同的核心判断，可以是独立的 frame。
- 风险为本规则加上高风险阈值例外是一个关于"设定或调整适用阈值"的候选。保留 `might`、`could` 和例外阈值数值；不要将其降级为孤立阈值事实或"机构采用风险为本方法"的一般陈述。
- 将 `if`、`when`、`unless`、`must`、`should`、`may`、`might`、`could`、`only`、`not`、`potentially` 和 `typically` 等明示情态和限定词保留在整合后的 proposition 和相关 frame 字段中。
- 具体的机构动作、评估、决策、应对、法律适用或归因可以是核心字段。有名有姓的主体有用但对于法律适用或归因链并非强制。
- 案例中实际发生的制度响应应被记录。具名主体的调查、审查、审计、筛查、分析、跟进或升级，只要产生了发现、结论、分类或后续动作，就是候选 frame——即使以过去时态叙述也同样处理。
- 当案例事实、当事方关系、指控或地点引发法律适用、管辖权、责任或监管关切时，输出该案例特有的适用性 frame。后续仅包含一般规则的候选不能替代前述案例特有 frame。
- 不要将没有核心处理、判断、法律适用或归因的犯罪手法、一般机制或普通案例事实变成候选 frame。

不输出纯定义、分类、孤立阈值、产品列表、控制列表、普通案例事实、普通风险指标或一般机制。例如：

```text
"UBO 是指……的自然人。"                              → 不构成候选
"大多数司法管辖区使用 25% 的阈值。"                    → 不构成候选
"该公司使用了空壳公司。"                              → 不构成候选
"贿赂可能导致洗钱。"                                 → 不构成候选
```

这些内容，并不因为它们包含了一个关系或一个数值，就属于候选 card frame。S2 在 S1 发现有效候选 frame 之后，才判断 KG 是否已经充分。

## 跨 Unit 归纳

`induction="cross_unit"` 仅用于完整的跨 unit 分支：section 提供了通用规则或判断标准，以及在该同一标准下由原文支持的正例和反例。候选必须引用全部三组。

不要从孤立实例或相邻事实推广出分支。此时应保持独立的原文支撑候选 frame（如有）。

## 证据规则

`section_text_with_unit_anchors` 是唯一事实来源。Unit ID 出现在原文中的方括号内，例如 `[v7u_N000496|496]`。

- 只引用这些锚点中可见的 ID。
- 每个引用的 unit 必须有且仅有一条 `evidence_spans` 条目，其中包含该 unit 中一段精确、连续的短引述。精确引述中不使用省略号。
- 逐字复制 `evidence_spans.quote` 中的内容。不要在引述内部将代词还原为具名主体、修复语法、翻译或改写；主体名称和简明释义应分别放在 `proposition` 或 `candidate_frame` 中。
- `source_quotes` 为下游兼容而保留。每一项必须与 `evidence_spans` 中的某一条引述字符串完全相同；不要把自由概括当作引述。
- proposition 和 frame 字段可以使用简明中文或英文描述，但必须保留原文含义、已列明的主体以及情态。

## 示例

### 1. 完整处理到结果链

```text
[v7u_N000801|801] When a transaction is flagged, the institution must review it and file a report when suspicion remains.
```

```json
{
  "candidate_id": "s1c_001",
  "unit_ids": ["v7u_N000801"],
  "proposition": "当交易被标记时，机构必须审查；如仍有怀疑，则提交报告。",
  "source_quotes": ["When a transaction is flagged, the institution must review it and file a report when suspicion remains."],
  "relation_cues": ["when", "must"],
  "candidate_frame": {
    "trigger_or_context": ["交易被标记"],
    "basis_or_condition": ["如仍有怀疑"],
    "focal_handling_or_judgment": "机构审查交易",
    "outcomes_or_paths": ["仍有怀疑时提交报告"]
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000801", "quote": "When a transaction is flagged, the institution must review it and file a report when suspicion remains."}
  ],
  "induction": null,
  "cross_unit_basis": null
}
```

### 2. 开放条件到处理 frame

```text
[v7u_N000496|496] where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified.
```

```json
{
  "candidate_id": "s1c_001",
  "unit_ids": ["v7u_N000496"],
  "proposition": "当不存在自然人受益所有人时，应识别并核实控制人或名义受益所有人。",
  "source_quotes": ["where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified."],
  "relation_cues": ["where", "should"],
  "candidate_frame": {
    "trigger_or_context": ["不存在自然人受益所有人"],
    "basis_or_condition": [],
    "focal_handling_or_judgment": "识别并核实控制人或名义受益所有人",
    "outcomes_or_paths": []
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000496", "quote": "where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified."}
  ],
  "induction": null,
  "cross_unit_basis": null
}
```

### 3. 无名主体的法律适用 frame

```text
[v7u_N000136|136] It applies to any company with a UK connection.
```

```json
{
  "candidate_id": "s1c_002",
  "unit_ids": ["v7u_N000136"],
  "proposition": "具有英国关联的公司适用该法律。",
  "source_quotes": ["It applies to any company with a UK connection"],
  "relation_cues": ["applies to"],
  "candidate_frame": {
    "trigger_or_context": ["公司具有英国关联"],
    "basis_or_condition": [],
    "focal_handling_or_judgment": "法律适用于该公司",
    "outcomes_or_paths": []
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000136", "quote": "It applies to any company with a UK connection"}
  ],
  "induction": null,
  "cross_unit_basis": null
}
```

### 4. 案例特有的法律适用 frame

```text
[v7u_N000900|900] Company A is incorporated in Country A and is a subsidiary of a Country B parent.
[v7u_N000901|901] Allegations of overseas bribery raised concerns under Country B's extraterritorial anti-bribery provisions.
```

即使后续 unit 单独陈述了国家 B 法律的一般适用范围，这仍然是一个候选。引发适用关切的具体事实与一般规则不能互相替代。

```json
{
  "candidate_id": "s1c_004",
  "unit_ids": ["v7u_N000900", "v7u_N000901"],
  "proposition": "公司A的主体关系和海外贿赂指控引发对国家B反贿赂法域外适用的关切。",
  "source_quotes": ["Company A is incorporated in Country A and is a subsidiary of a Country B parent.", "Allegations of overseas bribery raised concerns under Country B's extraterritorial anti-bribery provisions."],
  "relation_cues": ["subsidiary", "raised concerns", "extraterritorial"],
  "candidate_frame": {
    "trigger_or_context": ["公司A是国家B母公司的境外子公司，并面临海外贿赂指控"],
    "basis_or_condition": ["国家B反贿赂法的域外条款"],
    "focal_handling_or_judgment": "引发对该法域外适用的法律关切",
    "outcomes_or_paths": []
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000900", "quote": "Company A is incorporated in Country A and is a subsidiary of a Country B parent."},
    {"unit_id": "v7u_N000901", "quote": "Allegations of overseas bribery raised concerns under Country B's extraterritorial anti-bribery provisions."}
  ],
  "induction": null,
  "cross_unit_basis": null
}
```

### 5. 案例调查到发现 frame

```text
[v7u_N000902|902] The analyst's initial investigation revealed that the customer had engaged intermediaries in high-risk jurisdictions.
```

这是一个候选：分析师调查是核心动作，中间人安排是其发现。相比之下，单独一句 `The customer engaged intermediaries in high-risk jurisdictions.` 是普通案例事实，不是候选 frame。

### 6. 跨 unit 判断分支

```text
[v7u_N000489|489] ... identified at a threshold of 25% or more.
[v7u_N000493|493] ... identify indirect ownership stakes in addition to direct ownership.
[v7u_N000494|494] Individual D is then considered a UBO with 82% shareholding.
[v7u_N000495|495] Individual C ... is not a UBO.
```

仅当共用阈值以及正、反结果全部被引用时，才能作为一个候选：

```json
{
  "candidate_id": "s1c_005",
  "unit_ids": ["v7u_N000489", "v7u_N000493", "v7u_N000494", "v7u_N000495"],
  "proposition": "合计直接和间接持股达到适用阈值时认定为UBO，未达到时不认定为UBO。",
  "source_quotes": ["identified at a threshold of 25% or more", "identify indirect ownership stakes in addition to direct ownership", "considered a UBO with 82% shareholding", "is not a UBO"],
  "relation_cues": ["threshold", "direct", "indirect", "considered", "not"],
  "candidate_frame": {
    "trigger_or_context": ["需要判断持股是否达到适用阈值"],
    "basis_or_condition": ["受益所有权识别阈值"],
    "focal_handling_or_judgment": "合计直接和间接持股，并根据阈值判断是否认定为UBO",
    "outcomes_or_paths": ["达到阈值：认定为UBO", "未达到阈值：不认定为UBO"]
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000489", "quote": "identified at a threshold of 25% or more"},
    {"unit_id": "v7u_N000493", "quote": "identify indirect ownership stakes in addition to direct ownership"},
    {"unit_id": "v7u_N000494", "quote": "considered a UBO with 82% shareholding"},
    {"unit_id": "v7u_N000495", "quote": "is not a UBO"}
  ],
  "induction": "cross_unit",
  "cross_unit_basis": {
    "rule_unit_ids": ["v7u_N000489"],
    "positive_example_unit_ids": ["v7u_N000494"],
    "negative_example_unit_ids": ["v7u_N000495"]
  }
}
```

### 7. 风险为本阈值例外 frame

```text
[v7u_N000910|910] The organisation sets the appropriate ownership threshold using a risk-based approach.
[v7u_N000911|911] For high-risk customers, the threshold might be 10% and could be 5% for significantly higher-risk customers.
```

这是一个关于"设定适用阈值"的候选。它与后续将特定客户的直接和间接持股与该阈值进行比较的判断是不同 frame。

### 8. `because` 是线索，不是自动触发

```text
because of adverse news, the institution reviews the customer relationship
```

如果原文支持该审查，这可以是一个候选 frame。在 `relation_cues` 和依据字段中保留 `because`。例如使用 `basis_or_condition: ["because of adverse news"]`，而不是 `trigger_or_context`——除非原文本身陈述了触发顺序。

## 输出 Contract

只输出严格 JSON。顶层字段为 `section_id`、`section_title`、`propositions` 和 `skip_reason`。

每个 proposition 必填：

```text
candidate_id
unit_ids
proposition
source_quotes
relation_cues
candidate_frame
evidence_spans
induction
cross_unit_basis
```

`candidate_frame` 始终包含：

```text
trigger_or_context
basis_or_condition
focal_handling_or_judgment
outcomes_or_paths
```

非跨 unit 候选时 `induction` 和 `cross_unit_basis` 设为 `null`。没有任何有效候选 frame 时，输出空 `propositions` 数组和中文 `skip_reason`。

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
