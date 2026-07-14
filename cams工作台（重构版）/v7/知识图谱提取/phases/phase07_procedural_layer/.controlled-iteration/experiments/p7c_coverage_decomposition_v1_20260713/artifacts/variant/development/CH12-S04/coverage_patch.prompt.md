# P7C Coverage Patch Builder Prompt v1

## 角色

你是P7C候选图补丁构建器。上一独立调用已经完成命题发现、KG边界判断和覆盖匹配；本调用没有API记忆，因此`gap_claims`会完整提供需要处理的命题。

你只能把`gap_claims`构造成只增式候选图补丁。不得重新扫描并新增命题，不得将命题改判为KG，不得删除、修改、替换或重新编号`original_json`中的任何既有内容。只输出严格JSON，不输出Markdown或解释。

## 构图原则

- 每个`gap_claims`必须得到`new_card`、`card_supplement`或`unresolved`处理结果。
- 优先补充语义上相同的已有card；不同主体、不同业务对象或不同局部链才新建card。
- `partially_covered`中的错误旧边不得删除。应追加保留原文条件和限定词的正确替代边，旧边留给P7D拒绝。
- 结果必须是语义独立事实。同一谓词的主动式和被动式不得拆成process与exit。
- 静态输入、线索、材料、阈值和标准使用auxiliary节点，由process通过`REFERENCES`指向。
- 动作产生独立分类、结论、记录、状态变化或控制效果时，使用process到exit的`PRODUCES`。
- 单一路径条件可以使用带`condition`的`PRECEDES`；只有至少两条原文明示路径才使用`DECIDES`。
- 保留`must, should, may, might, could, often, potentially, help, appeared, suggested, typically`等原文强度。标签和边的`qualifier`不得把可能性、暂定判断或帮助关系强化为确定结果。
- 证据不足以可靠构图时输出`unresolved`，不得补造节点或边。

## 节点和边

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
- `PRODUCES`只能由process指向exit。
- `DECIDES`只能由`P3_branch_routing`发出，并保留原文分支条件。
- 默认省略`relation_type`；证据充分时才填写，不得自造类型。

## 输出合同

顶层必须且只能包含：`section_id, claim_resolutions, new_cards, card_supplements`。

`claim_resolutions`必须逐项覆盖`gap_claims`：

```json
{
  "claim_id": "claim_001",
  "resolution": "card_supplement",
  "card_id": "p7card_CH00-S00_001",
  "reason": "<中文构图说明>"
}
```

`resolution`只能为`new_card, card_supplement, unresolved`。`unresolved`时`card_id=null`并说明无法构图的证据缺口。

新增card必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes, coverage_claim_ids`。

- `card_nature`只能为`execution, assessment, risk_indicator, control`。
- `candidate_status`固定为`candidate`。
- `coverage_claim_ids`列出该card承接的gap claim。

补充已有card使用：

```json
{
  "patch_id": "coverage_patch_001",
  "card_id": "<已有card_id>",
  "coverage_claim_ids": ["claim_001"],
  "reason": "<中文>",
  "add_flow_nodes": [],
  "add_flow_edges": [],
  "add_source_unit_ids": []
}
```

补充至少新增一个节点或一条边。新增ID不得与已有ID重复。新增边可以连接已有节点和新增节点。所有证据必须来自`allowed_unit_ids`，并包含在最终card的`source_unit_ids`中。

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
      "claim_id": "claim_006",
      "unit_ids": [
        "v7u_N000921"
      ],
      "proposition": "当客户为高风险（如政治暴露人物PEPs）时，需要进行仔细的风险评估。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达条件（高风险客户）触发动作（进行仔细风险评估）的有向关系，明确执行主体为证券经纪机构，并保留义务限定“需要”。",
      "condition": "高风险客户（如PEPs）",
      "qualifier": "需要",
      "reason": "条件-动作有向命题，对判断何时加强风险评估有用，超出基础KG的风险指标记录，现有卡片未覆盖。"
    },
    {
      "claim_id": "claim_007",
      "unit_ids": [
        "v7u_N000921"
      ],
      "proposition": "政治暴露人物（PEPs）可能易于腐败。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达PEPs与腐败易感性之间的可能风险关系，保留限定词“可能”。",
      "condition": null,
      "qualifier": "可能",
      "reason": "具体风险属性有向关系，有助于理解PEPs为何高风险，超出基础KG的简单分类。"
    },
    {
      "claim_id": "claim_008",
      "unit_ids": [
        "v7u_N000921"
      ],
      "proposition": "中介机构可能代表客户进行非法交易。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达中介与非法交易便利之间的可能风险关系，保留限定词“可能”。",
      "condition": null,
      "qualifier": "可能",
      "reason": "具体风险属性有向关系，有助于理解中介风险，超出基础KG。"
    },
    {
      "claim_id": "claim_010",
      "unit_ids": [
        "v7u_N000923"
      ],
      "proposition": "持续监控交易活动可帮助识别可能表明洗钱的异常模式或行为。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达措施（持续监控）与目的（识别异常模式）之间的帮助关系，限定词“可帮助”。",
      "condition": null,
      "qualifier": "可帮助",
      "reason": "措施-目的帮助关系，对理解监控作用有用，超出基础KG的一般性措施记录。"
    },
    {
      "claim_id": "claim_011",
      "unit_ids": [
        "v7u_N000923"
      ],
      "proposition": "基于预定义标准标记可疑交易的强大交易监控系统可帮助识别大额或异常交易、快速交易模式、高频交易和涉及高风险司法管辖区的交易。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达监控系统与识别具体可疑交易类型之间的帮助关系，限定词“可帮助”，并枚举识别内容。",
      "condition": "基于预定义标准标记可疑交易",
      "qualifier": "可帮助",
      "reason": "措施-目的帮助关系并列举具体识别对象，对选项判断有用，超出基础KG。"
    },
    {
      "claim_id": "claim_012",
      "unit_ids": [
        "v7u_N000924"
      ],
      "proposition": "执行客户尽职调查（CDD）有助于确保资金来源合法，并确保客户根据其预期和历史交易模式正确细分。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达CDD与确保资金来源合法及客户细分两个结果之间的帮助关系，限定词“有助于”。",
      "condition": null,
      "qualifier": "有助于",
      "reason": "措施-目的帮助关系，超出基础KG。"
    },
    {
      "claim_id": "claim_014",
      "unit_ids": [
        "v7u_N000928"
      ],
      "proposition": "交易所交易基金（ETF）可掩盖基础投资者的身份。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达ETF与掩盖身份之间的可能风险关系，限定词“可”。",
      "condition": null,
      "qualifier": "可",
      "reason": "产品风险属性有向关系，超出基础KG的分类描述。"
    },
    {
      "claim_id": "claim_015",
      "unit_ids": [
        "v7u_N000929"
      ],
      "proposition": "衍生品（如期权和期货）的复杂性和杠杆可能被用于洗钱。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达衍生品特性与其被用于洗钱之间的可能关系，限定词“可能”。",
      "condition": null,
      "qualifier": "可能",
      "reason": "产品风险属性有向关系，超出基础KG。"
    },
    {
      "claim_id": "claim_016",
      "unit_ids": [
        "v7u_N000930"
      ],
      "proposition": "对冲基金的不透明结构和最低投资要求可能吸引非法行为者。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达对冲基金特性与吸引非法行为者之间的可能关系，限定词“可能”。",
      "condition": null,
      "qualifier": "可能",
      "reason": "产品风险属性有向关系，超出基础KG。"
    },
    {
      "claim_id": "claim_017",
      "unit_ids": [
        "v7u_N000931"
      ],
      "proposition": "私募股权交易缺乏透明度可带来洗钱挑战。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达私募股权缺乏透明度与洗钱挑战之间的可能因果关系，限定词“可”。",
      "condition": null,
      "qualifier": "可",
      "reason": "风险后果有向关系，超出基础KG。"
    },
    {
      "claim_id": "claim_018",
      "unit_ids": [
        "v7u_N000932"
      ],
      "proposition": "大宗商品交易建议可能被操纵和用于非法活动。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达大宗商品交易建议与操纵及非法活动之间的可能关系，限定词“可能”。",
      "condition": null,
      "qualifier": "可能",
      "reason": "风险属性有向关系，超出基础KG。"
    },
    {
      "claim_id": "claim_019",
      "unit_ids": [
        "v7u_N000933"
      ],
      "proposition": "房地产投资涉及多方利益相关者（包括卖方、买方、租户、物业经理和代理商），应全面审查以降低洗钱风险。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达条件（涉及多方）触发推荐措施（应全面审查）的有向关系，限定词“应”。",
      "condition": "涉及多方利益相关者",
      "qualifier": "应",
      "reason": "条件-措施有向命题，对判断控制要求有用，超出基础KG。"
    },
    {
      "claim_id": "claim_020",
      "unit_ids": [
        "v7u_N000934"
      ],
      "proposition": "众筹平台因监管不足和投资者匿名性可能被滥用于洗钱。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达众筹平台特性与洗钱滥用之间的可能风险关系，限定词“可能”。",
      "condition": null,
      "qualifier": "可能",
      "reason": "风险属性有向关系，超出基础KG。"
    },
    {
      "claim_id": "claim_021",
      "unit_ids": [
        "v7u_N000935"
      ],
      "proposition": "资产管理产品与服务的复杂性和多样性使检测洗钱越来越困难。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达产品复杂性导致检测困难的因果关系。",
      "condition": null,
      "qualifier": null,
      "reason": "因果关系有向命题，对理解挑战有用，超出基础KG的解释性事实。"
    },
    {
      "claim_id": "claim_023",
      "unit_ids": [
        "v7u_N000937"
      ],
      "proposition": "通过采取基于风险的方法（强调强大的CDD控制和持续监控），资产管理公司可以满足监管要求并展示对行业诚信的真正承诺。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达采取基于风险的方法与满足要求及展示承诺之间的手段-结果关系，限定词“可以”。",
      "condition": "采取基于风险的方法",
      "qualifier": "可以",
      "reason": "手段-结果有向命题，对判断方法有效性有用，超出基础KG。"
    },
    {
      "claim_id": "claim_024",
      "unit_ids": [
        "v7u_N000937"
      ],
      "proposition": "加密货币等新兴资产类别可能更容易被洗钱者利用。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "需创建卡表达新兴资产类别与更易被利用之间的比较风险关系，限定词“可能更容易”。",
      "condition": null,
      "qualifier": "可能更容易",
      "reason": "风险可能性比较关系，对评估新风险有用，超出基础KG。"
    }
  ]
}
```
