# P7C Section-Local Additive Coverage Review Prompt v3

## 角色

你是P7C section级增量完整性审查器。首次抽取器已经输出候选命题和候选card，这些card尚未经过P7D正式结构校验和边级审核。首次结果可能出现三类问题：把P7C关系误判为`kg_only`、把同一关系的前提和应对拆到不同候选、或在已有card中漏画节点和边。

你的任务是在完整检查当前section后输出只增式JSON补丁。准确率仍然重要，但P7C是候选层，允许把有充分当前section证据的边交给P7D继续审核。不得为了减少候选数量而遗漏基础KG无法表达的条件、方向、主体动作或独立结果。

`original_json`提供本次无记忆API调用所需的完整首次抽取上下文。不得回显、删除或改写它。Runner只会执行受保护的追加操作。只输出严格JSON，不输出Markdown或解释。

## P7C目的与KG边界

P7C不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标、一般规则、普通机制因果和组成关系。P7C增量表达：业务情境、事件、线索、输入或标准如何关联到特定主体带原文情态的识别、评估、决策或应对，以及原文明示的独立结论、记录、状态变化、控制效果、分支或后续行动。

基础KG能保存整句话或分别保存两个知识点，不代表它已经表达句内或句间的条件、主体、方向、动作约束和独立结果。没有独立结果时允许开放式局部关系。

P7C不读取题目或参考答案，不处理跨section桥接。`section_text_with_unit_anchors`是唯一事实证据；`base_kg_section_summary`只用于去重。所有新增证据只能引用`allowed_unit_ids`。

## 三项审查

### 一、复核原`kg_only`候选

对`review_target_candidate_ids`中的每个候选逐一裁决。可以保持`kg_only`，也可以将其关联到新增card或已有card的补充内容。

### 二、重新扫描完整section

按自然段落、转折、主体、对象和条件变化重新扫描原文。即使首次抽取没有登记候选，也必须检查是否存在遗漏关系。

重点检查：

- 相邻或邻近unit分别给出条件/变化与动作/应对，首次抽取却拆成两个`kg_only`候选；
- `if, when, unless, even if, based on, require, must, should, may, monitor, identify, review, approval, escalate, trigger, result in, help`等表达；
- 输入、线索、判断维度或标准被特定主体用于识别、评估、阈值选择或处置；
- 动作产生语义独立的结论、记录、状态变化或带原文限定的控制效果；
- 已有card覆盖了主题，但遗漏后文的新对象、条件、结果或应对。

允许跨越首次候选边界，允许合并多个候选的unit，也允许使用首次候选完全未登记的当前section unit。不得跨section取证。

### 三、检查已有card的图表达完整性

逐张比较`original_json.cards`、其对应`coverage_audit.proposition`与原文：

- proposition中的条件、参照关系和独立结果是否都进入`flow_nodes + flow_edges`；
- 结果是否只藏在process标签中而没有结果节点和边；
- 多个判断输入是否只被列出，却没有通过`REFERENCES`连接到评估动作；
- 方向错误的已有边是否需要追加一条证据支持的正确关系。

只能追加节点、边和`source_unit_ids`。不得删除、修改、重新编号或替换已有card、节点或边。已有错误边留给P7D拒绝；可以追加正确的替代边，新增边仍须由P7D审核。

## 成卡标准

新增关系必须同时满足：

1. 当前section证据支持关系两端、主体、方向和条件（如有）。
2. 关系超出基础KG能充分表达的定义、事实、列表、普通机制或一般知识关系。
3. 关系能帮助判断选项的顺序、条件、职责、义务、应对、适用范围或限定性结果。
4. 不需要补造主体、动作、条件或结果。

相邻句之间缺少明确连接词，但存在必要功能依赖时，可以输出`derivation=llm_inference`，交P7D和人工复核；不得伪装为`explicit_text`。

不得以“纯义务陈述”“没有复杂步骤”或“只受风险偏好约束”为由跳过已经具备主体、动作和方向的关系。

以下通常保持`kg_only`：纯定义/分类/阈值数值/组成列表、普通犯罪手法、孤立红旗、普通案例事实、一般机制因果、抽象风险缓解目的，以及必须补造主体或方向才能成立的关系。

特别地，“当局调查非法活动时受到腐败官员阻挠”只有调查困难和犯罪机制，不是金融机构/监管主体的识别、评估、决策或应对链，必须保持`kg_only`。不要因为句子含有`investigate`、`block`或`hinder`就自动成卡。

后续unit如果只是独立事实、犯罪性质说明、处罚或背景结果，不能仅因位于某个process之后就追加为该process的`PRODUCES`目标。只有原文明确说明同一动作产生该结果，或存在必要功能依赖时，才允许建立边；否则保留为KG内容。

调优、控制或框架组成的定义、目标和一般效果通常由KG承接；只有具体主体基于明确输入执行创建/修改/删除、监控、评估或应对动作时，才进入P7C。

## 图规则

新增完整card和card补充使用相同图规则。

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。节点必须由原文明示，`evidence_strength`只能为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard，不表达先后或产出。
- `PRODUCES`只能由process指向语义独立的exit。
- 单一路径条件使用带`condition`的`PRECEDES`；只有至少两条原文明示路径才使用`DECIDES`。
- `DECIDES`只能由`P3_branch_routing`发出。
- `derivation`只能为`explicit_text`或`llm_inference`。

静态适用对象、材料、因素、阈值、监管要求或风险偏好不得仅因语法顺序建成`entry --PRECEDES--> process`；应作为input/standard，由process通过`REFERENCES`指向。不得把同一谓词的主动式和被动式拆成动作和结果，不得把动作所需的批准、理由、标准或要求/义务写成`PRODUCES`。

`REFERENCES.condition`只限定input/standard适用于process的范围，不表达条件分支。单一路径`PRECEDES.condition`表达逻辑前提，不要求钟表式先后。

必须保留`must, should, may, might, could, often, potentially, help, typically`等情态和限定。`help mitigate`只能写成“有助于缓解”，不能写成必然降低。`must`本身不证明义务是持续、定期、永久或反复的。`X7_continuing_obligation`只用于原文明示新建立的独立持续义务，规范性动作仍保留在process中。

`escalate/escalation`默认写成“升级处理/升级处置”或保留英文，不得翻译为“上报/报告”；只有原文明示`report/notify/file/refer`及对象时才能写成报告或移交。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写。

## 补丁合同

顶层必须且只能包含：

```text
section_id
coverage_adjudication
new_candidates
new_cards
card_supplements
```

### coverage_adjudication

对每个`review_target_candidate_ids`恰好输出一条：

```json
{
  "candidate_id": "cand_001",
  "original_decision": "kg_only",
  "final_decision": "kg_only",
  "card_id": null,
  "reason": "<中文>"
}
```

`final_decision`只能是`kg_only`或`p7c_card`。提升时`card_id`必须指向`new_cards`中的新card，或指向被`card_supplements`补充的已有card。多个候选可以共同指向同一card。

### new_candidates

用于记录跨候选关系、首次未登记的关系或已有card的遗漏关系。每项必填：

```json
{
  "candidate_id": "coverage_gap_001",
  "unit_ids": ["<当前section unit_id>"],
  "proposition": "<完整有向命题>",
  "decision": "p7c_card",
  "card_id": "<新增或被补充的card_id>",
  "reason": "<KG不能表达什么>",
  "origin_candidate_ids": ["<相关首次候选ID，可为空>" ]
}
```

新`candidate_id`不得与`original_json.coverage_audit`重复。`unit_ids`可以是多个原候选unit的并集，也可以包含首次未登记的当前section unit。

### new_cards

只放新增完整card。每张必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。`candidate_status`固定为`candidate`。card ID不得与已有card重复。每张新card必须被某条提升裁决或`new_candidates`引用。

### card_supplements

只用于给已有card追加内容：

```json
{
  "patch_id": "coverage_supplement_001",
  "card_id": "<已有card_id>",
  "reason": "<中文说明遗漏>",
  "origin_candidate_ids": ["<相关首次候选ID或本补丁new_candidate ID，可为空>"],
  "add_flow_nodes": [],
  "add_flow_edges": [],
  "add_source_unit_ids": []
}
```

至少新增一个节点或一条边。新增ID不得与该card已有ID重复。新增边可以连接已有节点和新增节点。所有新增节点、边的证据unit必须已经存在于card的`source_unit_ids`，或同时列入`add_source_unit_ids`。每个被补充的card必须由一条提升裁决或`new_candidates`引用。

没有某类修改时输出空数组。即使`review_target_candidate_ids`为空，仍必须扫描完整section、审核已有card，并输出五个顶层字段。

## 输出骨架

```json
{
  "section_id": "<section_id>",
  "coverage_adjudication": [],
  "new_candidates": [],
  "new_cards": [],
  "card_supplements": []
}
```

## 当前section

section_id: `CH12-S04`

section_title: `Money laundering risks associated with insurance, securities, brokerage, and custodian services > Securities and brokerage risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "证券和经纪洗钱风险与控制措施",
      "title_en": "Securities and Brokerage Money Laundering Risks and Controls",
      "covered_units": [
        {
          "unit_id": "v7u_N000916",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000917",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000923",
          "unit_type": "process",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000918",
          "unit_type": "risk_indicator",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000919",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000912",
          "unit_type": "classification",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000913",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000914",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000915",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000920",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000921",
          "unit_type": "risk_indicator",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000922",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000924",
          "unit_type": "process",
          "kg_role": "prescribes_measure"
        }
      ]
    },
    {
      "title_zh": "资产管理：产品、风险与控制措施",
      "title_en": "Asset Management: Products, Risks, and Controls",
      "covered_units": [
        {
          "unit_id": "v7u_N000926",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000928",
          "unit_type": "definition",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000935",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000937",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000925",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000927",
          "unit_type": "classification",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000929",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000930",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000931",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000932",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000933",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000934",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000936",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "证券和经纪洗钱风险与控制措施",
      "target_title": "资产管理：产品、风险与控制措施",
      "relation_type": "parallels"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000912|912] According to FATF, securities providers can range from those that largely interact with retail investors, such as retail stockbrokers, wealth managers, and financial advisors, to those who serve institutional markets such as clearing members, prime brokers, and global custodians.
ZH: FATF指出证券服务商范围从零售投资者到机构市场。

[v7u_N000913|913] Providers offer various services including capital market research, portfolio management, and investment funds distribution.
ZH: 服务商提供资本市场研究、投资组合管理和投资基金分销等服务。

[v7u_N000914|914] The securities and brokerage sector serves direct customers and intermediaries that transact on behalf of their underlying customers.
ZH: 证券和经纪业服务于直接客户和代表其客户交易的中介。

[v7u_N000915|915] Transactions can encompass a wide range of financial instruments, including transferable securities, moneymarket instruments, investment funds, options, futures, swaps, forward rate agreements, and other derivative contracts.
ZH: 交易涵盖多种金融工具，包括可转让证券、货币市场工具、投资基金、期权、期货等。

[v7u_N000916|916] This sector is particularly vulnerable during the layering and integration stages of money laundering.
ZH: 证券业在洗钱的离析阶段和融合阶段尤其脆弱。

[v7u_N000917|917] FATF notes that the sector is unique in that it can be used not only to launder illicit funds but also to generate illicit funds within the industry itself through fraudulent activities.
ZH: FATF指出证券业既可洗钱也可通过欺诈产生非法资金。

[v7u_N000918|918] Characteristics such as high levels of interaction between securities providers and intermediaries such as investors and brokers, substantial transaction volumes, rapid execution speeds, and a degree of anonymity, all create opportunities for criminals to launder proceeds.
ZH: 高互动性、大交易量、快速执行和匿名性为洗钱创造机会。

[v7u_N000919|919] Complex financial products present a risk as they can obscure the source of funds and complicate transaction monitoring.
ZH: 复杂金融产品可能掩盖资金来源并复杂化交易监控。

[v7u_N000920|920] Offshore accounts provide anonymity, which can facilitate money laundering and enable criminals to exploit lax regulatory jurisdictions.
ZH: 离岸账户提供匿名性，便利洗钱并利用监管宽松的司法管辖区。

[v7u_N000921|921] High-risk customers, such as PEPs, and intermediaries require careful risk assessment. PEPs might be susceptible to corruption, while intermediaries might facilitate illicit transactions on behalf of customers.
ZH: 高风险客户如政治敏感人物和中介机构需要仔细的风险评估

[v7u_N000922|922] Additionally, the rise of electronic trading platforms emphasizes speed and high transaction volumes, making it challenging to monitor and apply mitigation controls.
ZH: 电子交易平台的高速度和高交易量增加了监控难度

[v7u_N000923|923] Continuous monitoring of trading activities can help identify unusual patterns or behaviors that might indicate money laundering. Robust transaction monitoring systems that flag suspicious transactions based on predefined criteria can help identify large or unusual trades, rapid trading patterns, highfrequency transactions and transactions involving high-risk jurisdictions.
ZH: 持续监控交易活动以识别异常模式，防范洗钱

[v7u_N000924|924] Conducting CDD helps ensure that the source of funds is legitimate, and that customers are correctly segmented according to their expected and historical trading patterns.
ZH: 客户尽职调查用于验证资金来源和客户细分

[v7u_N000925|925] Asset managers or asset management companies conduct investments and handle assets on behalf of their customers.
ZH: 资产管理公司代表客户进行投资和资产管理

[v7u_N000926|926] Asset managers are required to understand the money laundering risks of their business as they handle large volumes of capital across multiple jurisdictions, in diverse and evolving asset classes, often with anonymity in transactions, using complex financial products and third parties.
ZH: 资产管理公司有义务了解其业务中的洗钱风险

[v7u_N000927|927] Asset managers provide a variety of financial products and services, including:
ZH: 资产管理公司提供的金融产品和服务列表

[v7u_N000928|928] Exchange-traded funds (ETF): These are investment funds traded on stock exchanges, similar to individual stocks. They offer diversification and liquidity but can also obscure the identities of underlying investors.
ZH: 交易所交易基金（ETF）的定义及其洗钱风险

[v7u_N000929|929] Derivatives: These financial instruments, such as options and futures, derive their value from underlying assets. Their complexity and potential for leverage can be exploited for money laundering.
ZH: 衍生品（如期权和期货）的复杂性和杠杆可能被用于洗钱

[v7u_N000930|930] Hedge funds: These pooled investment funds employ various strategies to generate returns. Their often opaque structures and high minimum investment requirements can attract illicit actors.
ZH: 对冲基金的不透明结构和最低投资要求可能吸引非法行为者

[v7u_N000931|931] Private equity: This involves investing directly in private companies or buying out public companies. The lack of transparency in these transactions can pose money laundering challenges.
ZH: 私募股权交易缺乏透明度，带来洗钱挑战

[v7u_N000932|932] Commodity trading advice: Asset managers might provide guidance on trading physical commodities, which can be subject to manipulation and illicit activities.
ZH: 大宗商品交易建议可能被操纵和用于非法活动

[v7u_N000933|933] Real estate investments: Investing in real estate involves various stakeholders, including sellers, buyers, renters, property managers, and agents, all of whom should be thoroughly vetted to mitigate money laundering risks.
ZH: 房地产投资涉及多方利益相关者，需全面审查以降低洗钱风险

[v7u_N000934|934] Crowdfunding: As a relatively new form of asset management, crowdfunding platforms allow individuals to invest in projects or startups. These platforms can be misused for money laundering due to insufficient regulatory oversight and the anonymity they can provide to investors.
ZH: 众筹平台因监管不足和匿名性可能被滥用于洗钱

[v7u_N000935|935] The complexity and variability of these products and services make it increasingly difficult to detect money laundering.
ZH: 产品和服务的复杂性和多样性增加了洗钱检测难度

[v7u_N000936|936] Additionally, asset managers face a complex and evolving CDD process that requires knowledge of all parties involved in the transactions. Those parties include investment fund managers, portfolio managers, and alternative investment fund managers, such as those overseeing hedge funds and private equity.
ZH: 资产管理公司面临复杂的客户尽职调查，需了解所有交易方

[v7u_N000937|937] By adopting a risk-based approach that emphasizes strong CDD controls and continuous monitoring, they can meet regulatory requirements and demonstrate a genuine commitment to the sector’s integrity. This commitment also addresses emerging risks associated with new asset classes, such as cryptocurrencies and novel financial instruments, which might be more susceptible to exploitation by money launderers.
ZH: 基于风险的方法通过强化客户尽职调查和监控应对新兴资产类别的洗钱风险
```

allowed_unit_ids:

```json
[
  "v7u_N000912",
  "v7u_N000913",
  "v7u_N000914",
  "v7u_N000915",
  "v7u_N000916",
  "v7u_N000917",
  "v7u_N000918",
  "v7u_N000919",
  "v7u_N000920",
  "v7u_N000921",
  "v7u_N000922",
  "v7u_N000923",
  "v7u_N000924",
  "v7u_N000925",
  "v7u_N000926",
  "v7u_N000927",
  "v7u_N000928",
  "v7u_N000929",
  "v7u_N000930",
  "v7u_N000931",
  "v7u_N000932",
  "v7u_N000933",
  "v7u_N000934",
  "v7u_N000935",
  "v7u_N000936",
  "v7u_N000937"
]
```

original_json:

```json
{
  "section_id": "CH12-S04",
  "section_title": "Money laundering risks associated with insurance, securities, brokerage, and custodian services > Securities and brokerage risks",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N000918"
      ],
      "proposition": "证券业的高水平互动、大交易量、快速执行和匿名性为犯罪分子创造洗钱机会。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅描述行业特性如何形成风险，属于一般风险原因说明，基础KG已能覆盖这类风险指标事实。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000919"
      ],
      "proposition": "复杂金融产品掩盖资金来源并复杂化交易监控，带来洗钱风险。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "阐述复杂产品造成的风险，没有涉及主体应对或程序性结构，基础KG可保存为风险事实。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000920"
      ],
      "proposition": "离岸账户提供匿名性，便利洗钱并利用监管宽松辖区。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "说明离岸账户的洗钱风险，属于孤立风险指标，基础KG充分表达。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000921"
      ],
      "proposition": "高风险客户如PEPs和中介需要仔细风险评估。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性控制建议，缺乏条件、具体步骤或分支，基础KG可将其作为一般控制要求保存。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000922"
      ],
      "proposition": "电子交易平台的高速和高交易量增加了监控和应用缓解控制的难度。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "描述困难，没有形成动作-结果链，基础KG可表达此类事实。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000923"
      ],
      "proposition": "持续监控交易活动有助于识别可能指示洗钱的异常模式。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般控制措施及其潜在效果，没有独立结论或条件分支，基础KG可保存为控制措施的一般益处。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000924"
      ],
      "proposition": "进行客户尽职调查有助于确保资金来源合法且客户根据交易模式正确细分。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "类似cand_006，CDD措施的一般效果，基础KG足以表达该知识。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N000926"
      ],
      "proposition": "资产管理公司有义务了解其业务中的洗钱风险。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立的义务陈述，未形成与输入、条件或结果的局部有向连接，无法构成有向结构。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N000936"
      ],
      "proposition": "资产管理公司面临复杂的CDD流程，需要了解交易中涉及的所有方。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "描述性事实，无具体动作链或判断分支，基础KG可保存。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N000937"
      ],
      "proposition": "资产管理公司采用基于风险的方法（强调强CDD和持续监控）可以满足监管要求、展示承诺并应对新兴洗钱风险。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "条件-结果关系，但结果属于抽象目的且非独立产物，整体为一般因果规则，基础KG可表达。"
    }
  ],
  "cards": [],
  "skip_reason": "当前section内容主要为一般风险说明、控制措施介绍及孤立义务，均能被基础KG充分表达；没有形成明确的、可追溯原始unit证据的局部程序性或判断性有向结构。"
}
```

review_target_candidate_ids:

```json
[
  "cand_001",
  "cand_002",
  "cand_003",
  "cand_004",
  "cand_005",
  "cand_006",
  "cand_007",
  "cand_008",
  "cand_009",
  "cand_010"
]
```
