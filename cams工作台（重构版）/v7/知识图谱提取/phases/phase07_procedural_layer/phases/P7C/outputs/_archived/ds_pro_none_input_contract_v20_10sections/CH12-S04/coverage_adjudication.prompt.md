# P7C Section-Local Coverage Adjudication Prompt v2

## 角色

你是P7C覆盖裁决器。首次抽取器已经发现候选命题并生成候选card；这些card尚未经过P7D正式结构校验和边级审核。你的唯一任务是复核`coverage_audit`中原决定为`kg_only`的候选，判断它们是否因KG/P7C边界理解错误而漏成卡。

只输出严格JSON补丁，不输出Markdown或解释。`original_json`提供本次无记忆API调用所需的完整首次抽取上下文；不得回显或改写它。Runner会把补丁确定性合并到P7C正本。

## P7C目的

P7C在不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标和一般知识关系的前提下，从单个section中增量提取对CAMS题目选项判断有用的局部程序性或判断性有向结构：业务情境、事件、线索、输入或标准如何关联到特定主体带原文情态的识别、评估、决策或应对，以及原文明示的独立结论、记录、状态变化、控制效果、分支或后续行动。没有独立结果时允许开放关系。

P7C不读取题目或参考答案，不处理跨section桥接。当前section原文是唯一事实证据；基础KG摘要只能用于去重，不能补造事实。

## 裁决对象

只复核`original_json.coverage_audit`中`decision=kg_only`的候选。不得新增候选，不得删除候选，不得修改候选的`candidate_id`、`unit_ids`或`proposition`。

原本为`p7c_card`的候选及`original_json.cards`只用于理解已有结果、避免重复和避开已占用ID。输出中不得包含、删除、改写、拆分、合并或重新编号这些既有内容。

## 裁决标准

将原`kg_only`候选提升为`p7c_card`，必须同时满足：

1. 当前section证据支持关系两端、特定主体、方向以及条件（如有）。
2. 候选内部存在“情境/事件/线索/输入/标准如何关联到主体动作或判断”的局部结构；只有原文明示独立结果时才增加结果节点。
3. 该方向结构能够帮助判断选项的顺序、条件、主体职责、义务、应对、因果或适用范围。
4. 基础KG只能保存整句话或各知识点，不能充分表达句内的主体、方向、条件、动作约束或独立结果关系。

结构复杂度和是否闭环不是门槛。一个unit、一条路径、没有分支或反馈，或没有独立出口，都不能作为`kg_only`理由。只有对象实际到达、提交、移交或进入某阶段并触发动作时才建entry；静态适用对象、线索输入、分析材料、风险阈值、监管要求、政策基准或风险偏好应作为auxiliary standard/input并由process通过`REFERENCES`指向。

不得用“纯义务陈述”“没有复杂条件”“没有复杂步骤”拒绝提升。只要候选已经明确给出监管要求、风险偏好或状态变化如何约束特定主体的识别、标准选择或分类维持，即使没有独立出口，也满足局部有向结构要求。

以下通常应提升：

- 金融机构的识别动作明确参照监控系统标记的异常活动；只有原文另行给出识别结论时才增加出口。
- FIU综合SAR和跨境活动并形成红旗发现。
- 风险阈值和直接/间接持股被机构用于UBO判断并形成分类结论。
- 外部监管要求或上位标准约束机构调整控制、政策或职责；除非原文明示命令到达后触发动作，否则使用`REFERENCES`而不是`PRECEDES`。
- 明确条件触发拒绝、批准、升级、报告、监控或复核。
- 当地监管要求约束机构如何识别PEP；不得因规则只有一个unit或没有义务出口而拒绝。
- 机构基于风险偏好可以选择更高标准；必须保留可选性，即使没有独立配置出口也可以作为开放式局部关系。
- 卸任等状态变化后，特定机构仍明确维持既有分类；必须保留“部分机构”“可能”等限定。

以下保持`kg_only`：

- 纯定义、分类、阈值数值或组成列表，没有主体应用或其他有向关系。
- 普通犯罪方法、犯罪分子操作步骤或普通案例机制，没有机构、FIU、监管或执法主体的识别、判断或应对。
- 孤立红旗、后果、历史事实或抽象风险缓解目的。
- 只有主题相关性，或者必须补造主体、条件、方向、动作或结果才能闭合。

## 修改规则

对`review_target_candidate_ids`中的每个原`kg_only`候选，在顶层`coverage_adjudication`中输出一条记录：

```json
{
  "candidate_id": "cand_001",
  "original_decision": "kg_only",
  "final_decision": "kg_only",
  "card_id": null,
  "reason": "<中文裁决理由>"
}
```

`final_decision`只能为`kg_only`或`p7c_card`。

保持`kg_only`时：`card_id`必须为`null`。

提升为`p7c_card`时：

- 在裁决记录中填写新card的`card_id`；
- `reason`说明基础KG不能表达的方向结构；
- 在顶层`promoted_cards`中输出且只输出对应的新card；
- 新card ID不得与`original_json.cards`中的既有ID重复；
- 每个提升候选恰好对应一张新card，不得输出未被裁决提升的card。

## 新增card规则

新增card必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。`candidate_status`固定为`candidate`，不是最终审核状态。

`card_nature`只能为：`execution, assessment, risk_indicator, control`。

新增card可以是完整闭环，也可以是开放式局部关系；不得为了满足entry→process→exit而补造出口。

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。节点必须由原文明示，`evidence_strength`只能为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

`X7_continuing_obligation`只用于原文明示上游动作、决定或协议新建立了独立持续义务；规范性语句中的“主体必须/应当执行某动作”应保留在process中，不得复制为X7出口。

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard。
- `PRODUCES`只能由process指向exit。
- `DECIDES`只能由`P3_branch_routing`发出，至少两条分支，每条都有原文明示的`condition`。
- `derivation=llm_inference`只说明边依赖必要功能推理，不改变`candidate_status`，也不表示P7D已经接受或拒绝。

`REFERENCES.condition`可以限定某项input/standard适用于process的情境，但不表示条件分支。单一条件直接触发动作时使用带`condition`的`PRECEDES`；只有至少两条原文明示路径时才使用`DECIDES`。

静态适用对象、审查材料或判断输入不得仅因语法顺序建成`entry --PRECEDES--> process`；应建为auxiliary input并由process通过`REFERENCES`指向。不得把同一谓词的主动式和被动式拆成process与exit，也不得把“动作需要理由、批准或遵循要求”写成“动作`PRODUCES`要求/义务”。

单一路径的`if/when/unless A，则B`使用条件entry到process的`PRECEDES`，并在edge的`condition`中保留原文条件；它表达逻辑前提，不要求钟表式先后。输出每条`PRODUCES`前必须反问：source和target合并后是否仍损失一个独立事实；若不损失，删除同义target和该边。理由、批准、标准或义务约束动作时使用process指向standard/input的`REFERENCES`。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写，不得创造新类型。

必须保留`must, should, may, might, could, often, potentially, help`等情态强度。不得将“有助于缓解”强化为“风险已经消除”。`must/shall/is required to`只证明义务存在，不证明动作已经完成；除非原文明示完成或结果已经发生，不得输出“已调整”“已建立”“已降低”等完成状态。

`must`本身不证明义务是持续、定期、永久或反复的，不得无证据增加这些限定。`escalate/escalation`默认写成“升级处理/升级处置”或保留英文，不得翻译为“上报/报告”；只有原文明示`report/notify/file/refer`及其对象时，才能写成上报、报告或移交。

新增card的节点、边和`source_unit_ids`只能引用对应候选原有的`unit_ids`。不得借裁决轮追加其他unit、扩展候选命题或引入无关主题；若原候选证据本身不足，保持`kg_only`。

## 输出约束

只返回补丁对象，顶层只能包含：

```text
section_id
coverage_adjudication
promoted_cards
```

示例：

```json
{
  "section_id": "<section_id>",
  "coverage_adjudication": [
    {
      "candidate_id": "cand_001",
      "original_decision": "kg_only",
      "final_decision": "kg_only",
      "card_id": null,
      "reason": "<中文KG边界理由>"
    }
  ],
  "promoted_cards": []
}
```

即使所有候选都保持`kg_only`，也必须逐一输出裁决记录，此时`promoted_cards`为空数组。不得输出`coverage_audit`、既有`cards`、`skip_reason`或其他首次抽取字段。

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
        "v7u_N000916",
        "v7u_N000917",
        "v7u_N000918"
      ],
      "proposition": "证券业在洗钱分层和融合阶段脆弱，且可用于产生非法资金，其高互动性等特性为洗钱创造机会",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立风险陈述和因果关系，基础KG可充分表达"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000919",
        "v7u_N000920",
        "v7u_N000922",
        "v7u_N000935"
      ],
      "proposition": "复杂金融产品、离岸账户、电子交易平台的高速度和交易量以及产品多样性使得洗钱检测和监控更具挑战性",
      "decision": "kg_only",
      "card_id": null,
      "reason": "普通因果和挑战说明，基础KG可表达"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000921"
      ],
      "proposition": "PEPs等高风险客户和中介需要进行仔细的风险评估",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立要求，未描述具体有向判断链，基础KG可将其作为风险指标和一般要求保存"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000924"
      ],
      "proposition": "执行客户尽职调查有助于确保资金来源合法并正确细分客户",
      "decision": "kg_only",
      "card_id": null,
      "reason": "描述CDD的目的，但结果非独立，未形成有向判断或程序链，KG可保存措施"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000925",
        "v7u_N000926",
        "v7u_N000927",
        "v7u_N000928",
        "v7u_N000929",
        "v7u_N000930",
        "v7u_N000931",
        "v7u_N000932",
        "v7u_N000933",
        "v7u_N000934"
      ],
      "proposition": "资产管理公司提供的各种金融产品（ETF、衍生品、对冲基金等）及其相关洗钱风险",
      "decision": "kg_only",
      "card_id": null,
      "reason": "产品定义、分类和一般风险指标，基础KG可充分表达"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000936"
      ],
      "proposition": "资产管理的CDD过程复杂，需要了解所有交易方",
      "decision": "kg_only",
      "card_id": null,
      "reason": "描述过程的要求，未形成有向判断链，KG可保存"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000937"
      ],
      "proposition": "采用强调强CDD和持续监控的风险为本方法可以满足监管要求并应对新兴资产类别的风险",
      "decision": "kg_only",
      "card_id": null,
      "reason": "抽象结果说明，非有向结构，KG可表达措施效果"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N000923"
      ],
      "proposition": "机构持续监控交易活动，基于预定义标准标记可疑交易，以帮助识别异常模式和可疑交易",
      "decision": "p7c_card",
      "card_id": "p7card_CH12-S04_001",
      "reason": "包含标准约束监控动作的有向关系，超出基础KG的表达能力"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N000912",
        "v7u_N000913",
        "v7u_N000914",
        "v7u_N000915"
      ],
      "proposition": "证券服务商范围、提供的服务、服务对象和交易工具",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯粹背景信息和分类，无程序性或判断性结构"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH12-S04_001",
      "section_id": "CH12-S04",
      "card_nature": "control",
      "title": "持续交易监控与基于预定义标准的可疑交易标记",
      "flow_nodes": [
        {
          "node_id": "std_001",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "预定义标准 (predefined criteria)",
          "evidence_unit_ids": [
            "v7u_N000923"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "proc_001",
          "node_category": "process",
          "node_type": "P7_monitoring",
          "label": "机构持续监控交易活动并基于预定义标准标记可疑交易，以帮助识别异常模式和可疑交易行为",
          "evidence_unit_ids": [
            "v7u_N000923"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_001",
          "edge_type": "REFERENCES",
          "source": "proc_001",
          "target": "std_001",
          "evidence_unit_ids": [
            "v7u_N000923"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N000923"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构持续监控交易活动并基于预定义标准标记可疑交易，这有助于识别异常模式和可疑交易（标准约束监控动作）；KG不足：基础KG可以保存'持续监控是控制措施'这一事实，但无法表达监控动作参照了预定义标准并据此标记可疑交易的有向约束关系；选项判断：可用于确认或排除关于监控机制如何运作的选项，比如是否基于预定义标准标记可疑交易；LLM推理：无。"
    }
  ],
  "skip_reason": null
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
  "cand_009"
]
```
