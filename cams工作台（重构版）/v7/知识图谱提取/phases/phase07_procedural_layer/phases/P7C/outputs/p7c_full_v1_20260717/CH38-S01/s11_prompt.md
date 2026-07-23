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

section_id: `CH38-S01`

section_title: `The importance of continuous risk assessment > Continuously assessing financial crime risk`

section_text_with_unit_anchors:

```text
[v7u_N002823|2823] Financial crime risks are dynamic and constantly evolving.
ZH: 金融犯罪风险是动态且不断演变的

[v7u_N002824|2824] Criminals will always attempt to move illicit funds through the financial sector undetected. They will use new technologies and trends, regardless of the controls that organizations establish. Criminals continuously search for loopholes to exploit and test the resilience of AFC frameworks.
ZH: 犯罪分子持续利用新技术寻找漏洞以不被察觉地转移非法资金

[v7u_N002825|2825] Organizations must reevaluate risks whenever there is a material change to their business. This could include higher-risk product offerings, entering a new market, or changes in jurisdictions where the organization operates.
ZH: 组织在业务发生重大变化时必须重新评估风险

[v7u_N002826|2826] Continuously assessing financial crime risk helps organizations adapt to evolving ML/TF techniques and threats, monitor transactions to detect patterns and significant changes, respond to emerging geographical risks, and meet regulations and international standards.
ZH: 持续评估金融犯罪风险有助于组织适应不断变化的洗钱/恐怖融资手法和威胁

[v7u_N002827|2827] FATF and regulatory bodies promote a proactive approach to risk management and reassessing risks as required. This approach, and regular risk assessments, enable organizations to divert their resources to high-risk areas to mitigate them effectively.
ZH: FATF和监管机构提倡主动风险管理，将资源转向高风险领域以有效缓解风险

[v7u_N002828|2828] In addition to conducting overarching enterprise-wide risk assessments regularly, organizations manage risk continually through CRAs.
ZH: 组织通过客户风险评估（CRA）持续管理风险

[v7u_N002829|2829] Organizations should conduct a CRA for every customer they onboard before establishing a business relationship with that customer. They should also review the CRA regularly and whenever there are changes in a customer’s behavior and risk profile. These changes might include:
ZH: 组织应在建立业务关系前对每位客户进行CRA，并定期或在客户行为变化时审查

[v7u_N002830|2830] Transaction pattern deviations.
ZH: 交易模式偏离是触发CRA审查的变化之一

[v7u_N002831|2831] Requests for new products or services.
ZH: 客户请求新产品或服务是触发CRA审查的变化之一

[v7u_N002832|2832] Reluctance to provide information or documentation.
ZH: 客户不愿提供信息或文件是触发CRA审查的变化之一

[v7u_N002833|2833] Increased exposure to high-risk jurisdictions.
ZH: 客户对高风险司法管辖区的敞口增加是触发CRA审查的变化之一

[v7u_N002834|2834] Changes in the customer’s sector.
ZH: 客户所在行业发生变化是触发CRA审查的变化之一

[v7u_N002835|2835] Changes in how the organization operates, such as changing product lines or shifting to online business operations.
ZH: 组织运营方式变化（如产品线变更或转向线上业务）是触发CRA审查的变化之一

[v7u_N002836|2836] CRAs enable organizations to detect changes in customer behavior and reassess risks.
ZH: CRA使组织能够检测客户行为变化并重新评估风险

[v7u_N002837|2837] For example, if an organization detects that a customer plans to extend its sales to high-risk jurisdictions, it might need to introduce enhanced measures such as increased third-party screening, request additional documentation, or increase transaction scrutiny.
ZH: 例如：客户扩展销售至高风险司法管辖区时，需采取增强措施如加强第三方筛查、要求额外文件或增加交易审查

[v7u_N002838|2838] Product and channel risk assessments enable organizations to detect deviations from the intended use of their products, helping to identify new threats or risks.
ZH: 产品和渠道风险评估有助于检测产品预期用途的偏离，识别新威胁或风险

[v7u_N002839|2839] Some risks might not be clear at product launch, but might be identified through ongoing monitoring.
ZH: 某些风险在产品推出时可能不明显，但可通过持续监控识别

[v7u_N002840|2840] For example, during COVID-19, organizations shifted to digital channels. This required aligning existing faceto-face channel controls to address emerging fraud risks, such as digital identity fraud, cross-border wire transfers, and new ways of verifying the authenticity of documentation.
ZH: 例如：疫情期间组织转向数字渠道，需调整现有面对面渠道控制以应对数字身份欺诈等新兴欺诈风险

[v7u_N002841|2841] These risk assessments help organizations continuously assess financial crime risks and enable them to take a holistic, proactive approach to manage and reassess risks as needed.
ZH: 风险持续评估帮助组织主动管理金融犯罪风险
```
