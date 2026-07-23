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

section_id: `CH02-S01`

section_title: `Types of financial crime > Predicate crimes and money laundering`

section_text_with_unit_anchors:

```text
[v7u_N000060|60] Predicate crimes are specified unlawful activities whose proceeds can give rise to prosecution for money laundering.
ZH: 上游犯罪是指其收益可导致洗钱起诉的特定非法活动

[v7u_N000061|61] Individuals or organizations who engage in predicate crimes often want to "clean," or launder the proceeds from these crimes so they can use them legitimately without drawing attention from law enforcement.
ZH: 实施上游犯罪的个人或组织清洗犯罪收益以合法使用

[v7u_N000062|62] FATF has identified 21 categories of predicate offenses that financial institutions must acknowledge and monitor under AML compliance programs.
ZH: FATF 确定了金融机构必须关注的 21 类上游犯罪

[v7u_N000063|63] However, different jurisdictions might classify these offenses differently.
ZH: 不同司法管辖区对上游犯罪的分类存在差异

[v7u_N000064|64] For example, while some countries have strong laws against human trafficking, others do not recognize certain forms of exploitation as criminal offenses.
ZH: 举例：各国对人口贩卖的法律认定不同导致分类差异

[v7u_N000065|65] This variation can complicate AML efforts, with compliance professionals operating in cross-border contexts needing to align risk controls with the laws and regulations of more than one jurisdiction.
ZH: 跨境反洗钱合规需协调多个司法管辖区的法律差异

[v7u_N000066|66] The list of 21 FATF-designated predicate crimes includes:
ZH: FATF 指定的 21 类上游犯罪清单引述

[v7u_N000067|67] 1. Participation in an organized criminal group and racketeering: Engaging in systemic financial crimes
ZH: 参与有组织犯罪集团和敲诈勒索属于上游犯罪

[v7u_N000068|68] 2. Terrorism, including terrorist financing: Providing financial support to these operations
ZH: 恐怖主义及恐怖融资属于上游犯罪

[v7u_N000069|69] 3. Trafficking in human beings and migrant smuggling: Generating illicit profits through human exploitation
ZH: 人口贩卖和偷运移民属于上游犯罪

[v7u_N000070|70] 4. Sexual exploitation, including that of children: Crimes linked to forced prostitution and human trafficking
ZH: 性剥削（包括儿童性剥削）属于上游犯罪

[v7u_N000071|71] 5. Illicit trafficking in narcotic drugs and psychotropic substances: Production, transportation, and sale of illegal substances
ZH: 非法贩运麻醉药品和精神药物属于上游犯罪

[v7u_N000072|72] 6. Illicit arms trafficking: Illegal trade and smuggling of firearms and explosives
ZH: 非法武器贩运属于上游犯罪

[v7u_N000073|73] 7. Illicit trafficking of stolen and other goods: Black market trade of stolen and counterfeit items
ZH: 非法贩运被盗物品及其他货物属于上游犯罪

[v7u_N000074|74] 8. Corruption and bribery: Abuse of power in public or private sectors for financial gain
ZH: 腐败和贿赂属于上游犯罪

[v7u_N000075|75] 9. Fraud: Financial deception, scams, and identity theft schemes
ZH: 欺诈属于上游犯罪

[v7u_N000076|76] 10. Counterfeiting currency: Illegal manufacturing of banknotes
ZH: 伪造货币属于上游犯罪

[v7u_N000077|77] 11. Counterfeiting and piracy of products: Violations of intellectual property, including counterfeit goods
ZH: 假冒和盗版产品属于上游犯罪

[v7u_N000078|78] 12. Environmental crime: Logging, poaching, and waste disposal
ZH: 环境犯罪属于上游犯罪

[v7u_N000079|79] 13. Murder and grievous bodily injury: Violent crimes motivated by financial gain
ZH: 谋杀和严重身体伤害属于上游犯罪

[v7u_N000080|80] 14. Kidnapping, illegal restraint, and hostage-taking: Crimes involving ransom demands
ZH: 绑架、非法拘禁和劫持人质属于上游犯罪

[v7u_N000081|81] 15. Robbery or theft: Large-scale property crimes driven by financial motives
ZH: 抢劫或盗窃：出于财务动机的大规模财产犯罪

[v7u_N000082|82] 16. Smuggling (including in relation to customs and excise duties and taxes): Illegal movement of goods to evade duties
ZH: 走私（包括关税和消费税相关）：为逃避关税而非法移动货物

[v7u_N000083|83] 17. Tax crimes (related to direct and indirect taxes): Tax fraud and false reporting schemes
ZH: 税收犯罪（直接税和间接税）：税务欺诈和虚假申报计划

[v7u_N000084|84] 18. Extortion: Coercing for financial gain through threats or intimidation
ZH: 敲诈勒索：通过威胁或恐吓强迫获取经济利益

[v7u_N000085|85] 19. Forgery: Falsifying documents, financial records, or identities
ZH: 伪造：伪造文件、财务记录或身份信息

[v7u_N000086|86] 20.Piracy: Maritime or cyber-based hijacking for financial gain
ZH: 海盗行为：为获取经济利益而进行的海上或网络劫持

[v7u_N000087|87] 21. Insider trading and market manipulation: Illegal use of nonpublic information to achieve profits
ZH: 内幕交易和市场操纵：利用非公开信息非法获利

[v7u_N000088|88] Economic sanctions, whether asset freezes or sector-specific restrictions, impose high financial, reputational, and operational costs on individuals and entities targeted by them.
ZH: 制裁对目标个人和实体施加高额财务、声誉和运营成本

[v7u_N000089|89] For this reason, sanctions targets often attempt to evade or circumvent sanctions in order to secretly engage in a prohibited activity, such as continuing to use an asset or receive economic benefits.
ZH: 制裁目标常试图规避制裁以秘密从事被禁止的活动

[v7u_N000090|90] For example, a designated individual might evade personal sanctions and continue using his luxury yacht by obscuring its ownership.
ZH: 示例：被制裁个人通过隐藏豪华游艇所有权规避个人制裁

[v7u_N000091|91] Sanctions evasion can be internal, with the help of personnel at an organization, or external, when evaders try to bypass internal controls without assistance from the inside.
ZH: 制裁规避可分为内部规避（借助内部人员）和外部规避

[v7u_N000092|92] Methods of sanctions evasion include payments, trade, and ownership.
ZH: 制裁规避方法包括支付、贸易和所有权相关手段

[v7u_N000093|93] Payment-related evasion occurs when, for example, Bank A attempts to have Bank B process prohibited transactions, with or without help from Bank B insiders.
ZH: 支付相关规避：银行A试图让银行B处理被禁止交易

[v7u_N000094|94] Identifying information is removed, or stripped, from payment instructions to avoid detection.
ZH: 从支付指令中移除识别信息以逃避检测

[v7u_N000095|95] Nested and payable accounts are particularly vulnerable to this evasion typology.
ZH: 嵌套账户和应付账户特别容易受到支付信息剥离的规避手法影响

[v7u_N000096|96] Trade-related evasion involves illegally importing or exporting goods without proper licensing or despite trade bans.
ZH: 贸易相关规避：未经适当许可或违反贸易禁令非法进出口货物

[v7u_N000097|97] Common techniques include the use of shell companies, switching cargo on the open sea (also known as transshipment), and using neutral or opaque jurisdictions for transit.
ZH: 贸易规避常见手法：使用壳公司、公海换货（转运）、利用中立或保密司法管辖区

[v7u_N000098|98] Ownership-related evasion involves obscuring the ownership of an asset by a designated person. This can be achieved by using complex corporate structures, proxies, and bearer shares and by diluting ownership.
ZH: 所有权相关规避：通过复杂公司结构、代理人、不记名股票和稀释所有权隐藏资产所有权

[v7u_N000099|99] Regulated entities must have strong AML and sanctions compliance programs with robust policies, procedures, and internal controls for detecting and preventing sanctions evasion. The penalties for noncompliance and failing to prevent sanctions evasion could include:
ZH: 受监管实体必须建立强大的反洗钱和制裁合规计划，违规处罚包括：

[v7u_N000100|100] Civil monetary penalties against organizations
ZH: 对组织的民事罚款

[v7u_N000101|101] Civil and criminal prosecution of individuals
ZH: 个人可能面临洗钱相关民事和刑事起诉

[v7u_N000102|102] Designations as a sanctions target
ZH: 个人可能被列为制裁目标

[v7u_N000103|103] Businessman Alexei Komarov amassed his fortune through Volkof Industries, a high-tech distribution company with clients worldwide. Though some of his customers were from a wide range of industries (from consumer electronics and automotive to healthcare and industrial manufacturing), most sales went to a foreign government engaged in nuclear weapons development. After UN sanctions targeted this proliferation activity, Volkof Industries faced restrictions, losing its access to global markets.
ZH: Alexei Komarov通过Volkof Industries从事扩散融资的案例

[v7u_N000104|104] Facing financial collapse, Komarov was determined to find a way to continue trading.
ZH: Komarov面临财务崩溃，决心继续交易

[v7u_N000105|105] To evade the sanctions, he created a shell company, RedStar Solutions.
ZH: Komarov创建壳公司RedStar Solutions以规避制裁

[v7u_N000106|106] He incorporated it in a jurisdiction with limited regulatory expectations toward AML and sanctions compliance and masked it as a technical support and maintenance service provider.
ZH: 在监管宽松的司法管辖区注册壳公司并伪装成技术服务商

[v7u_N000107|107] Through RedStar, he resumed exports to the foreign government developing its nuclear weapons program, using transshipment points in permissive jurisdictions and falsified invoices that labeled export-controlled items, such as semiconductors, as “industrial machinery and spare parts.”
ZH: 通过转运点和伪造发票恢复出口受控物品

[v7u_N000108|108] RedStar also employed local distributors in those jurisdictions to further distance Komarov and Volkof Industries from the transactions and paid them to ensure the shipments were received without question.
ZH: 利用当地分销商进一步掩盖交易关联

[v7u_N000109|109] To launder the proceeds back to Volkof Industries, Komarov routed payments through offshore accounts and shell companies. He was thus able to credit Volkof Industries’ accounts using laundered funds from the illegal activities of RedStar.
ZH: 通过离岸账户和壳公司清洗非法收益的示例

[v7u_N000110|110] Komarov’s goal was not just to hide the profits of RedStar, but to keep Volkof Industries trading, as its name still carried weight in industry circles. Despite UN sanctions against Volkof Industries, this strategy helped the company meet loan obligations, retain employees, and strengthen business ties to the foreign government, its main client.
ZH: Komarov的双重目标：隐藏利润并维持Volkof Industries运营

[v7u_N000111|111] The scheme unraveled when a bank’s compliance officer flagged irregular payment flows linked to RedStar. Further investigation exposed the illicit network, revealing Komarov and Volkof Industries’ role in sanctions evasion, proliferation financing, laundering criminal proceeds, and foreign bribery and corruption offences.
ZH: 合规官发现异常支付，揭露制裁规避、扩散融资、洗钱等犯罪
```
