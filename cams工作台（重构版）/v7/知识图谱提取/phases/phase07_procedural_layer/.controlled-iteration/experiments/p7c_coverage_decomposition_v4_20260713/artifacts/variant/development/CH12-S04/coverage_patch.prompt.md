# P7C Coverage Patch Builder Prompt v3

## 角色

你是P7C候选图补丁构建器。上一独立调用已经完成命题发现、KG边界判断和覆盖匹配。你只能把`gap_claims`构造成只增式候选图补丁。

不得重新发现或改判命题，不得删除、修改、替换或重新编号`original_json`中的既有内容。只输出严格JSON，不输出Markdown或解释。

## 证据门

每个节点和边都必须由当前section直接支持。构图前逐项确认主体/制度流程、动作或判断、输入/条件、结果和限定词分别由哪些unit支持。

不得从section主题或业务常识补造一个点名主体。但是，原文明示的制度性流程本身可以作为process，例如“执行CDD”“持续监控交易活动”“进行仔细风险评估”。此时节点标签只写原文流程，不得擅自增加“金融机构执行”等未点名主体。

如果原文既没有点名主体，也没有明确的制度性动作或判断流程，则输出`unresolved`。

## source与target

只有已有节点的动作语义和证据unit都与gap claim一致时才能复用。主题相同或位于同一card不够。

如果结果来自后续调查、证据评估、计算比较或其他新动作，而已有process只表示初步调查、一般识别或宽泛流程，必须新增有原文证据的新process；无法新增时输出`unresolved`。

每条新增边的`evidence_unit_ids`必须同时覆盖source节点和target节点的证据：至少与source的`evidence_unit_ids`有交集，也至少与target的`evidence_unit_ids`有交集。需要时使用两个端点证据unit的并集。不得让edge引用一个在该edge证据中完全没有依据的旧节点。

## 限定词

限定词必须同时进入相关节点标签和边字段：

- `can help identify`的target写成“可以帮助识别……”，不能写成“识别……”；
- `helps ensure`的target写成“有助于确保……”，不能写成“已经确保/得到确保”；
- `appeared/suggested`的结论写成“似乎/证据表明或暗示……”，不能写成确定结论；
- `may/might/could/often/potentially/typically`不得被强化。

只在edge写`qualifier`而节点仍是确定性表述，不合格。

## 独立结果

不得把同一谓词的主动式和被动式拆成process与exit。例如process已经是“创建、修改或删除规则”，不得再输出“规则被创建、修改或删除”的exit。此类动作如果参照明确输入，只输出开放式`process REFERENCES input/standard`。

对于计算或阈值比较示例，建立“合计/计算并比较”的assessment process，再由它产生分类结果。不要把分类结果挂到一般识别process。只添加表达核心缺口所需的最少边；不要为了连通新旧节点增加无证据的`PRECEDES`。

## 图规则

- 静态输入、线索、材料、阈值和标准使用auxiliary节点，由process通过`REFERENCES`指向。
- 动作产生独立分类、结论、记录或状态变化时，使用process到exit的`PRODUCES`。
- 单一路径条件可以使用带`condition`的`PRECEDES`；只有至少两条原文明示路径才使用`DECIDES`。
- 每个gap claim必须得到`new_card`、`card_supplement`或`unresolved`。
- 证据不足时必须`unresolved`，不得为追求覆盖率补造。

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。`evidence_strength`固定为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。

- `edge_type`只能为`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。
- `derivation`只能为`explicit_text`或`llm_inference`。
- `REFERENCES`只能由process指向auxiliary input或standard。
- `PRODUCES`只能由process指向语义独立的exit。
- `DECIDES`只能由`P3_branch_routing`发出，并保留原文分支条件。

默认省略`relation_type`。确有必要时只能使用：

`clue_supports_identification, mechanism_explains_risk, identification_leads_to_conclusion, conclusion_triggers_response, branch_condition_routes_path, component_assembles_product, standard_constrains_action, result_handoffs_stage, feedback_requests_completion, cycle_requires_monitoring, standard_transmits_requirement, parallel_alternative_no_sequence`

不得创造新类型。`branch_condition_routes_path`只能配合带condition的`DECIDES`。

## 输出合同

顶层必须且只能包含：`section_id, claim_resolutions, new_cards, card_supplements`。

`claim_resolutions`逐项覆盖`gap_claims`：

```json
{
  "claim_id": "claim_001",
  "resolution": "card_supplement",
  "card_id": "p7card_CH00-S00_001",
  "reason": "<说明source、target、关系和限定词分别由哪些unit支持>"
}
```

`resolution`只能为`new_card, card_supplement, unresolved`。`unresolved`时`card_id=null`并说明具体证据缺口。

新增card必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes, coverage_claim_ids`。

- `card_nature`只能为`execution, assessment, risk_indicator, control`。
- `candidate_status`固定为`candidate`。
- `coverage_claim_ids`列出承接的gap claim。

补充已有card使用：

```json
{
  "patch_id": "coverage_patch_001",
  "card_id": "<已有card_id>",
  "coverage_claim_ids": ["claim_001"],
  "reason": "<中文证据说明>",
  "add_flow_nodes": [],
  "add_flow_edges": [],
  "add_source_unit_ids": []
}
```

补充至少新增一个节点或一条边。新增ID不得与已有ID重复。所有证据必须来自`allowed_unit_ids`，并包含在最终card的`source_unit_ids`中。

## 当前section

运行器将在此处追加当前section原文、首次抽取JSON、gap claims和允许的unit ID。KG边界已经由Audit决定，本调用不接收KG摘要。

## 调用输入

```json
{
  "section_id": "CH12-S04",
  "section_title": "Money laundering risks associated with insurance, securities, brokerage, and custodian services > Securities and brokerage risks",
  "section_text_with_unit_anchors": "[v7u_N000912|912] According to FATF, securities providers can range from those that largely interact with retail investors, such as retail stockbrokers, wealth managers, and financial advisors, to those who serve institutional markets such as clearing members, prime brokers, and global custodians.\nZH: FATF指出证券服务商范围从零售投资者到机构市场。\n\n[v7u_N000913|913] Providers offer various services including capital market research, portfolio management, and investment funds distribution.\nZH: 服务商提供资本市场研究、投资组合管理和投资基金分销等服务。\n\n[v7u_N000914|914] The securities and brokerage sector serves direct customers and intermediaries that transact on behalf of their underlying customers.\nZH: 证券和经纪业服务于直接客户和代表其客户交易的中介。\n\n[v7u_N000915|915] Transactions can encompass a wide range of financial instruments, including transferable securities, moneymarket instruments, investment funds, options, futures, swaps, forward rate agreements, and other derivative contracts.\nZH: 交易涵盖多种金融工具，包括可转让证券、货币市场工具、投资基金、期权、期货等。\n\n[v7u_N000916|916] This sector is particularly vulnerable during the layering and integration stages of money laundering.\nZH: 证券业在洗钱的离析阶段和融合阶段尤其脆弱。\n\n[v7u_N000917|917] FATF notes that the sector is unique in that it can be used not only to launder illicit funds but also to generate illicit funds within the industry itself through fraudulent activities.\nZH: FATF指出证券业既可洗钱也可通过欺诈产生非法资金。\n\n[v7u_N000918|918] Characteristics such as high levels of interaction between securities providers and intermediaries such as investors and brokers, substantial transaction volumes, rapid execution speeds, and a degree of anonymity, all create opportunities for criminals to launder proceeds.\nZH: 高互动性、大交易量、快速执行和匿名性为洗钱创造机会。\n\n[v7u_N000919|919] Complex financial products present a risk as they can obscure the source of funds and complicate transaction monitoring.\nZH: 复杂金融产品可能掩盖资金来源并复杂化交易监控。\n\n[v7u_N000920|920] Offshore accounts provide anonymity, which can facilitate money laundering and enable criminals to exploit lax regulatory jurisdictions.\nZH: 离岸账户提供匿名性，便利洗钱并利用监管宽松的司法管辖区。\n\n[v7u_N000921|921] High-risk customers, such as PEPs, and intermediaries require careful risk assessment. PEPs might be susceptible to corruption, while intermediaries might facilitate illicit transactions on behalf of customers.\nZH: 高风险客户如政治敏感人物和中介机构需要仔细的风险评估\n\n[v7u_N000922|922] Additionally, the rise of electronic trading platforms emphasizes speed and high transaction volumes, making it challenging to monitor and apply mitigation controls.\nZH: 电子交易平台的高速度和高交易量增加了监控难度\n\n[v7u_N000923|923] Continuous monitoring of trading activities can help identify unusual patterns or behaviors that might indicate money laundering. Robust transaction monitoring systems that flag suspicious transactions based on predefined criteria can help identify large or unusual trades, rapid trading patterns, highfrequency transactions and transactions involving high-risk jurisdictions.\nZH: 持续监控交易活动以识别异常模式，防范洗钱\n\n[v7u_N000924|924] Conducting CDD helps ensure that the source of funds is legitimate, and that customers are correctly segmented according to their expected and historical trading patterns.\nZH: 客户尽职调查用于验证资金来源和客户细分\n\n[v7u_N000925|925] Asset managers or asset management companies conduct investments and handle assets on behalf of their customers.\nZH: 资产管理公司代表客户进行投资和资产管理\n\n[v7u_N000926|926] Asset managers are required to understand the money laundering risks of their business as they handle large volumes of capital across multiple jurisdictions, in diverse and evolving asset classes, often with anonymity in transactions, using complex financial products and third parties.\nZH: 资产管理公司有义务了解其业务中的洗钱风险\n\n[v7u_N000927|927] Asset managers provide a variety of financial products and services, including:\nZH: 资产管理公司提供的金融产品和服务列表\n\n[v7u_N000928|928] Exchange-traded funds (ETF): These are investment funds traded on stock exchanges, similar to individual stocks. They offer diversification and liquidity but can also obscure the identities of underlying investors.\nZH: 交易所交易基金（ETF）的定义及其洗钱风险\n\n[v7u_N000929|929] Derivatives: These financial instruments, such as options and futures, derive their value from underlying assets. Their complexity and potential for leverage can be exploited for money laundering.\nZH: 衍生品（如期权和期货）的复杂性和杠杆可能被用于洗钱\n\n[v7u_N000930|930] Hedge funds: These pooled investment funds employ various strategies to generate returns. Their often opaque structures and high minimum investment requirements can attract illicit actors.\nZH: 对冲基金的不透明结构和最低投资要求可能吸引非法行为者\n\n[v7u_N000931|931] Private equity: This involves investing directly in private companies or buying out public companies. The lack of transparency in these transactions can pose money laundering challenges.\nZH: 私募股权交易缺乏透明度，带来洗钱挑战\n\n[v7u_N000932|932] Commodity trading advice: Asset managers might provide guidance on trading physical commodities, which can be subject to manipulation and illicit activities.\nZH: 大宗商品交易建议可能被操纵和用于非法活动\n\n[v7u_N000933|933] Real estate investments: Investing in real estate involves various stakeholders, including sellers, buyers, renters, property managers, and agents, all of whom should be thoroughly vetted to mitigate money laundering risks.\nZH: 房地产投资涉及多方利益相关者，需全面审查以降低洗钱风险\n\n[v7u_N000934|934] Crowdfunding: As a relatively new form of asset management, crowdfunding platforms allow individuals to invest in projects or startups. These platforms can be misused for money laundering due to insufficient regulatory oversight and the anonymity they can provide to investors.\nZH: 众筹平台因监管不足和匿名性可能被滥用于洗钱\n\n[v7u_N000935|935] The complexity and variability of these products and services make it increasingly difficult to detect money laundering.\nZH: 产品和服务的复杂性和多样性增加了洗钱检测难度\n\n[v7u_N000936|936] Additionally, asset managers face a complex and evolving CDD process that requires knowledge of all parties involved in the transactions. Those parties include investment fund managers, portfolio managers, and alternative investment fund managers, such as those overseeing hedge funds and private equity.\nZH: 资产管理公司面临复杂的客户尽职调查，需了解所有交易方\n\n[v7u_N000937|937] By adopting a risk-based approach that emphasizes strong CDD controls and continuous monitoring, they can meet regulatory requirements and demonstrate a genuine commitment to the sector’s integrity. This commitment also addresses emerging risks associated with new asset classes, such as cryptocurrencies and novel financial instruments, which might be more susceptible to exploitation by money launderers.\nZH: 基于风险的方法通过强化客户尽职调查和监控应对新兴资产类别的洗钱风险",
  "allowed_unit_ids": [
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
  ],
  "original_json": {
    "section_id": "CH12-S04",
    "section_title": "Money laundering risks associated with insurance, securities, brokerage, and custodian services > Securities and brokerage risks",
    "coverage_audit": [
      {
        "candidate_id": "cand_001",
        "unit_ids": [
          "v7u_N000921"
        ],
        "proposition": "当客户为高风险（如PEPs）时，需要进行仔细的风险评估。",
        "decision": "kg_only",
        "card_id": null,
        "reason": "缺乏明确执行主体，且基础KG已作为风险指标覆盖。"
      },
      {
        "candidate_id": "cand_002",
        "unit_ids": [
          "v7u_N000923"
        ],
        "proposition": "通过持续监控交易活动，可以识别异常模式或洗钱行为。",
        "decision": "kg_only",
        "card_id": null,
        "reason": "通用控制建议，基础KG已作为‘规定措施’覆盖。"
      },
      {
        "candidate_id": "cand_003",
        "unit_ids": [
          "v7u_N000924"
        ],
        "proposition": "通过执行客户尽职调查（CDD），有助于确保资金来源合法并正确细分客户。",
        "decision": "kg_only",
        "card_id": null,
        "reason": "通用控制建议，基础KG已作为‘规定措施’覆盖。"
      },
      {
        "candidate_id": "cand_004",
        "unit_ids": [
          "v7u_N000926"
        ],
        "proposition": "资产管理公司必须了解其业务中的洗钱风险。",
        "decision": "kg_only",
        "card_id": null,
        "reason": "纯义务陈述，基础KG已作为规则覆盖；无额外有向结构约束具体识别或分类。"
      },
      {
        "candidate_id": "cand_005",
        "unit_ids": [
          "v7u_N000936"
        ],
        "proposition": "资产管理公司的CDD流程要求了解所有交易方。",
        "decision": "p7c_card",
        "card_id": "p7card_CH12-S04_001",
        "reason": "代表流程对具体要求的参照关系，超出基础KG对CDD的一般性解释，有助于判断CDD范围。"
      },
      {
        "candidate_id": "cand_006",
        "unit_ids": [
          "v7u_N000937"
        ],
        "proposition": "通过采取基于风险的方法（强调CDD和持续监控），资产管理公司可以满足监管要求并应对新兴风险。",
        "decision": "kg_only",
        "card_id": null,
        "reason": "宽泛的因果论述，结果抽象（满足监管要求），基础KG可保存为通用规则。"
      }
    ],
    "cards": [
      {
        "card_id": "p7card_CH12-S04_001",
        "section_id": "CH12-S04",
        "card_nature": "execution",
        "title": "资产管理公司CDD流程要求了解所有交易方",
        "flow_nodes": [
          {
            "node_id": "n1",
            "node_category": "process",
            "node_type": "P2_execution",
            "label": "资产管理公司：执行客户尽职调查（CDD）流程",
            "evidence_unit_ids": [
              "v7u_N000936"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "n2",
            "node_category": "auxiliary",
            "node_type": "standard",
            "label": "必须了解所有交易方",
            "evidence_unit_ids": [
              "v7u_N000936"
            ],
            "evidence_strength": "explicit"
          }
        ],
        "flow_edges": [
          {
            "edge_id": "e1",
            "edge_type": "REFERENCES",
            "source": "n1",
            "target": "n2",
            "evidence_unit_ids": [
              "v7u_N000936"
            ],
            "derivation": "explicit_text",
            "relation_type": "standard_constrains_action",
            "source_quote": "requires knowledge of all parties involved in the transactions"
          }
        ],
        "source_unit_ids": [
          "v7u_N000936"
        ],
        "candidate_status": "candidate",
        "review_notes": "增量命题：资产管理公司的CDD流程必须参照“了解所有交易方”这一要求（standard_constrains_action）。KG不足：基础KG仅解释CDD复杂且需了解所有方，未表达流程对要求的参照关系。选项判断：可确认资产管理公司CDD范围必须涵盖所有交易方。LLM推理：无。"
      }
    ],
    "skip_reason": null
  },
  "gap_claims": [
    {
      "claim_id": "claim_010",
      "unit_ids": [
        "v7u_N000921"
      ],
      "proposition": "当客户为高风险（如PEPs）或中介时，金融机构需要进行仔细的风险评估。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "整个有向命题缺失：无卡片表达高风险客户身份条件触发金融机构风险评估动作的流程关系。",
      "condition": "客户为高风险（如PEPs）或中介",
      "qualifier": "require",
      "reason": "硬门槛满足：1) 金融机构的风险评估是操作性控制动作；2) 高风险客户身份作为条件触发该动作，形成原文明示的条件-动作关系；3) 可用于判断在何种条件下机构需启动评估；4) 基础KG仅将高风险客户列为风险指标，未表达评估被触发的流程关系。因此为P7C增量命题，但现有卡片未覆盖。"
    },
    {
      "claim_id": "claim_012",
      "unit_ids": [
        "v7u_N000923"
      ],
      "proposition": "持续监控交易活动可以帮助识别可能表明洗钱的异常模式或行为。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "整个命题缺失：无卡片表达持续监控动作与异常模式识别结果之间的帮助关系。",
      "condition": null,
      "qualifier": "can help identify",
      "reason": "硬门槛满足：1) 持续监控是操作性动作；2) 该动作与识别异常模式之间存在原文明示的'can help'结果关系；3) 可用于判断监控措施可能的识别输出方向；4) 基础KG仅将监控列为规定措施，未表达帮助识别关系。因此为P7C增量，缺失。"
    },
    {
      "claim_id": "claim_013",
      "unit_ids": [
        "v7u_N000923"
      ],
      "proposition": "基于预定义标准，稳健的交易监控系统通过标记可疑交易，可以帮助识别大额或异常交易、快速交易模式、高频交易及涉及高风险司法管辖区的交易。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "整个命题缺失：无卡片表达监控系统基于标准的标记动作及帮助识别具体交易类型的双重关系（参照+帮助产出）。",
      "condition": null,
      "qualifier": "based on predefined criteria; can help identify",
      "reason": "硬门槛满足：1) 监控系统标记可疑交易是操作性动作；2) 标记动作明确参照预定义标准，且'can help identify'指向具体识别产出；3) 可用于判断系统标记的标准约束及识别目标；4) 基础KG未表达标准参照与帮助识别关系。因此为P7C增量，缺失。"
    },
    {
      "claim_id": "claim_014",
      "unit_ids": [
        "v7u_N000924"
      ],
      "proposition": "执行客户尽职调查（CDD）有助于确保资金来源合法，并按照客户预期和历史交易模式正确细分客户。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "整个命题缺失：无卡片表达CDD动作与确保资金合法、基于交易模式细分客户之间的有向帮助关系。",
      "condition": null,
      "qualifier": "helps ensure; according to their expected and historical trading patterns",
      "reason": "硬门槛满足：1) CDD动作是操作性流程；2) CDD通过'helps ensure'关系指向资金合法性保证和基于预期/历史模式的客户细分结果，后者是带有参照维度的分类出口；3) 可用于判断CDD的效果范围和细分依据；4) 基础KG仅作为规定措施，未表达CDD的有向效果和细分参照。因此为P7C增量，缺失。"
    }
  ]
}
```
