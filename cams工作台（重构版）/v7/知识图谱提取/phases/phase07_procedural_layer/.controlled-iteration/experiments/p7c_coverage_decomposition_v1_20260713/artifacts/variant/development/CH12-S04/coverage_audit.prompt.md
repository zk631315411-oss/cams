# P7C Proposition-Level Coverage Audit Prompt v1

## 角色

你是P7C命题级覆盖审查器。首次抽取器已经输出`original_json`，但它可能漏掉命题、把P7C关系误判为KG内容，或只覆盖主题而没有完整表达方向、条件、限定词和结果。

本调用只建立覆盖命题台账，不生成card、flow_node或flow_edge。只输出严格JSON，不输出Markdown或解释。

## P7C边界

基础KG能够表达定义、分类、事实、普通案例、孤立风险指标、一般规则、普通机制因果、组成关系和普通知识点关系。

P7C只增量表达对CAMS选项判断有用的局部有向命题：业务情境、事件、线索、输入或标准如何关联到特定主体的识别、评估、决策或应对，以及在相应条件下产生的结论、义务、控制结果、分支或后续行动。没有独立出口时，主体动作参照输入、线索或标准的开放关系也可以属于P7C。

普通案例事实仍由KG承接；但案例中原文明示的调查、识别、判断或应对如何导向带限定词的结论，可以成为P7C候选。普通犯罪手法及犯罪机制不属于P7C。

## 审查方法

按自然段落、unit、转折、主体、对象和条件变化完整扫描section。对每个可能带有方向、条件、动作约束或独立结果的命题单独登记。

必须先写出命题，再判断KG/P7边界，最后比较现有图。不得因为已有card标题相近、节点含有相同主题词，或者某个主题已经成卡，就认定命题已经覆盖。

对P7C命题逐项比较：

- 主体和动作是否存在；
- source、target和方向是否一致；
- 条件是否进入边或节点；
- `must, should, may, might, could, often, potentially, help, appeared, suggested, typically`等限定是否保留；
- 独立分类、结论、记录、状态变化或控制效果是否有节点和边；
- 开放式参照关系是否因“没有出口”而被错误跳过。

`coverage_status`判定：

- `covered`：已有card完整表达同一有向命题，包括主体、方向、条件和限定词。
- `partially_covered`：已有card只覆盖主题或部分端点，遗漏方向、条件、限定词、独立出口，或把可能性/帮助关系写成确定性结果。
- `missing`：已有card没有表达该P7C命题。
- `not_applicable`：该命题属于`kg_only`。

如果已有边写强、写反或漏掉限定词，应判为`partially_covered`，不能因为端点已经出现而判为`covered`。

## 输出合同

顶层必须且只能包含：`section_id, claims, scan_summary`。

每项claim必填：

```json
{
  "claim_id": "claim_001",
  "unit_ids": ["<当前section unit_id>"],
  "proposition": "<保留主体、方向、条件和限定词的完整中文命题>",
  "kg_boundary": "p7_incremental",
  "coverage_status": "partially_covered",
  "matched_card_ids": ["<已有card_id>"],
  "missing_part": "<具体缺少的方向、条件、限定词、节点或边；无则为null>",
  "condition": "<原文条件；无则为null>",
  "qualifier": "<原文情态或限定；无则为null>",
  "reason": "<中文边界与覆盖理由>"
}
```

约束：

- `kg_boundary`只能是`kg_only`或`p7_incremental`。
- `kg_only`必须使用`coverage_status=not_applicable`，`matched_card_ids=[]`，`missing_part=null`。
- `p7_incremental + covered`必须至少匹配一张已有card，且`missing_part=null`。
- `p7_incremental + partially_covered`必须至少匹配一张已有card，并具体填写`missing_part`。
- `p7_incremental + missing`必须具体填写`missing_part`；`matched_card_ids`可以为空。
- 只能引用`allowed_unit_ids`和`original_json.cards`中存在的card ID。
- `scan_summary`用一句中文说明扫描范围和P7C缺口数量。

## 当前section

运行器将在此处追加当前section原文、KG摘要、首次抽取JSON和允许的unit ID。

## 调用输入

```json
{
  "section_id": "CH12-S04",
  "section_title": "Money laundering risks associated with insurance, securities, brokerage, and custodian services > Securities and brokerage risks",
  "base_kg_section_summary": {
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
  },
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
  }
}
```
