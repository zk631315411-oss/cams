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

section_id: `CH36-S01`

section_title: `Types of risk assessment > The importance of risk assessment in AFC`

section_text_with_unit_anchors:

```text
[v7u_N002630|2630] FATF Recommendation 1 states, “Countries should identify, assess, and understand the money laundering and terrorist financing risks for the country, and should take action, including designating an authority or mechanism to coordinate actions to assess risks, and apply resources, aimed at ensuring the risks are mitigated effectively.”
ZH: FATF建议1要求各国识别、评估并了解洗钱和恐怖融资风险，并采取协调行动

[v7u_N002631|2631] Risk assessments and the risk-based approach (RBA) are important for understanding and analyzing risks.
ZH: 风险评估和风险为本方法对于理解与分析风险至关重要

[v7u_N002632|2632] Taking necessary measures to mitigate risks minimizes their effects on a country or entity.
ZH: 采取必要措施减轻风险可最小化其对国家或实体的影响

[v7u_N002633|2633] The FATF Interpretive Note to Recommendation 1 also highlights the importance of the RBA.
ZH: FATF建议1的释义说明强调了风险为本方法的重要性

[v7u_N002634|2634] National risk assessment (NRA)
ZH: 国家风险评估（NRA）作为风险评估类型之一

[v7u_N002635|2635] Sectoral risk assessment (SRA)
ZH: 行业风险评估（SRA）作为风险评估类型之一

[v7u_N002636|2636] Enterprise-wide risk assessment (EWRA)
ZH: 企业风险评估（EWRA）作为风险评估类型之一

[v7u_N002637|2637] Risks can vary in their nature, scale, and impact.
ZH: 风险在性质、规模和影响上可能各不相同

[v7u_N002638|2638] An RBA requires countries and financial institutions to prioritize risks and apply appropriate measures based on their level of exposure.
ZH: 风险为本方法要求国家和金融机构根据风险暴露程度优先排序并采取适当措施

[v7u_N002639|2639] Not every risk applies to every institution.
ZH: 并非所有风险都适用于每个机构

[v7u_N002640|2640] Understanding these factors will allow financial institutions to make informed decisions to balance risk and reward.
ZH: 理解这些因素使金融机构能够做出平衡风险与回报的明智决策

[v7u_N002641|2641] Three main types of risk assessments are national risk assessments (NRA), sectoral risk assessments (SRA), and enterprise-wide risk assessments (EWRA).
ZH: 三种主要风险评估类型：国家风险评估、行业风险评估和企业全面风险评估

[v7u_N002642|2642] NRAs identify national-level money laundering and terror financing threats and risks. These assessments review sectors and areas with higher risks.
ZH: 国家风险评估识别国家层面的洗钱与恐怖融资威胁和风险，并审查高风险行业

[v7u_N002643|2643] Financial institutions are required to apply enhanced measures to mitigate these risks.
ZH: 金融机构必须采取强化措施以缓解风险

[v7u_N002644|2644] SRAs are performed by national authorities, supervisory bodies, regulators, and international organizations. These assessments identify, assess, and analyze money laundering and terror financing risks specific to an industry or sector.
ZH: 行业风险评估由国家机关、监管机构等执行，识别并分析特定行业的洗钱与恐怖融资风险

[v7u_N002645|2645] EWRAs analyze and evaluate money laundering and terror financing risks identified within an organization.
ZH: 企业全面风险评估分析并评估组织内部识别的洗钱与恐怖融资风险

[v7u_N002646|2646] These assessments are tailored to the specific organization conducting the assessment and consider customer characteristics, jurisdictions, products, and delivery channels.
ZH: 企业全面风险评估根据组织自身情况定制，考虑客户、地域、产品和渠道特征

[v7u_N002647|2647] The process begins by establishing inherent risks, assessing the effectiveness of controls, computing the residual risk, and obtaining a clear action plan on mitigating the highest risks.
ZH: 企业全面风险评估流程：确定固有风险、评估控制有效性、计算剩余风险、制定行动计划

[v7u_N002648|2648] Business leaders can use the EWRA to assess potential risks and estimate the cost to serve. This helps them make informed decisions about whether to expand or pursue new ventures.
ZH: 企业领导者可利用企业全面风险评估评估潜在风险和成本，辅助业务扩张决策

[v7u_N002649|2649] For example, when entering high-risk areas, the business unit’s EWRA helps evaluate the financial and operational impact, enabling leaders to understand the costs involved to be compliant. EWRAs should include consideration of the risks identified in the NRAs and SRAs for any jurisdiction in which they do business or plan to do business. NRAs and SRAs help organizations manage internal risks by using insights from national and sector-specific risk assessments. By conducting these risk assessments, organizations can:
ZH: 企业全面风险评估应纳入国家风险评估和行业风险评估的见解，以管理内部风险

[v7u_N002650|2650] Allocate resources efficiently by making informed decisions based on risk levels.
ZH: 根据风险水平做出明智决策，有效分配资源

[v7u_N002651|2651] Manage risks associated with customers, jurisdictions, products, and delivery channels by applying targeted measures according to regulatory expectations.
ZH: 通过针对客户、地域、产品和渠道采取针对性措施管理风险

[v7u_N002652|2652] Enhance AFC controls by identifying vulnerabilities and exposures and safeguarding institutions against regulatory enforcements.
ZH: 通过识别漏洞和风险敞口加强金融犯罪防控，保护机构免受监管执法

[v7u_N002653|2653] These risk assessments should be interrelated to foster an effective, riskbased AFC framework.
ZH: 各类风险评估应相互关联，以形成有效的基于风险的金融犯罪防控框架
```
