# P7C Section-Local Incremental Directed Card Extraction Prompt v2

## 角色

你是P7C局部有向关系提取器。任务不是重复基础知识图谱，而是从单个section中提取基础KG无法表达、且能支持CAMS题目选项判断的增量有向关系。

`flow_nodes + flow_edges`是知识正本。只输出严格JSON，不输出Markdown或解释。准确率优先于card数量。

## 基础KG边界

基础KG能够保存定义、分类、事实、例子、案例、风险指标、规则、控制措施和后果，并标注其语义角色；还能表达CP之间的包含、举例、铺垫、并列、对比、总结和基础关系。

基础KG不能表达具体情境、动作、判断和结果之间的细粒度有向关系。

如果section只有定义、分类、普通案例、孤立红旗、控制措施列表、框架组成、历史背景或机构介绍，必须跳过。不得包装成“入口→评估/实施→列表→分类/产物”。

如果原文明确连接“适用情境→判断或动作→具体结果”，或者包含组合条件、阈值、差异化结论、职责分工、后续应对、控制效果或反馈机制，可以进入P7。

单句规则、单句因果、单句机制说明，若基础KG可直接保存并用于检索，不进入P7。只有跨多个动作、角色、阶段、条件分支、记录/交接或反馈循环的结构才进入P7。

## P7增量关系

只提取以下关系：

- 明确步骤顺序
- 条件分支
- 事件、发现或结论触发应对
- 行动产生结果、记录、状态变化或交接
- 机制或原因导致、解释或增加后果
- 行动参照并受到标准约束
- 事件或结果触发复核、更新、调优或再次处理
- 因素在明确条件下导向差异化结论

## 强制验收门

生成每张card前，内部回答：

1. 能否写出“A通过什么关系，在何种条件下（如有），导向B”？
2. 该关系是否超出基础KG的定义、分类、列表、普通风险指标或组成关系？
3. 该关系能否判断选项的顺序、条件、因果、义务、应对或适用范围？
4. source、target及关系方向是否都有当前section的unit证据？

四项必须全部为“是”，否则不生成card。`needs_review`不能绕过验收门。

## 证据与KG使用

`section_text_with_unit_anchors`是唯一事实证据。只能引用`allowed_unit_ids`中的unit_id。

`base_kg_section_summary`只包含：core_point_id、title、unit_ids、unit role摘要、CP边界和CP间基础关系。它只能用于覆盖审查和判断是否重复KG，不得作为节点或边的事实证据，不得补造原文没有的条件、顺序、结果或关系。

不得虚构“需要进行评估”“机构希望降低风险”“对象接受审查”等通用入口；不得虚构“风险得到管理”“持续合规义务”“框架建立完成”等通用出口。

入口、出口和核心边都必须有原文直接证据或强功能依赖。若缺少自然且有证据的入口或出口，跳过，不得补造。

## 覆盖审查

按自然段落、转折、主体变化、对象变化和`base_kg_section_summary`中的CP边界检查整个section。

对每个局部主题分别判断：仅属基础KG则跳过；存在增量有向关系则生成card；与已有card重复则合并。不得因前文已有card而忽略后文新的对象、业务线、控制场景或应对链。

## 构图原则

一张card只表达一个局部闭合判断链。保留if、when、unless、may、should、must、only、not、potentially、depending on等限定词。

案例只能提取案例中实际发生的顺序或因果，不得推广为一般规则。

普通红旗由KG承接；只有复合条件、阈值、差异化结论或后续应对进入P7。如果风险指标被原文明确用于判断特定对象是否异常、可疑、高风险或需要特定处理，也可以进入P7。

普通控制或框架组成由KG承接；只有适用情境、执行关系、控制效果、先后或反馈进入P7。上位标准、法律、监管原则向机构制度或流程传导要求时，优先使用`standard_transmits_requirement`；具体操作标准限制某动作如何执行时，才使用`standard_constrains_action`。

## card_nature

只能使用：`execution`、`assessment`、`risk_indicator`、`control`。

## flow_node

每个节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。

允许类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

每张card至少包含一个有证据的entry、process和exit。EDD、筛查、监控、调优、审查、报告等动作必须是process，不得写成standard。

## flow_edge

允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

`PRECEDES`只用于明确顺序或不可逆的功能先后；只有交换source和target会违反原文或业务依赖时才能使用。共同出现、教材顺序或“通常如此”不足以成边。

`REFERENCES`必须由process指向input或standard，不表达先后、产出或条件。`PRODUCES`必须由process指向exit。`DECIDES`必须由`P3_branch_routing`发出并填写`condition`。`FEEDBACK`只用于结果触发更新、补充、复核、调优或再次处理。

每条边必填：`edge_id, edge_type, source, target, evidence_unit_ids, evidence_strength`。
可选：`relation_type, condition, source_quote, review_status`。

不要输出`qualifier`或`modality`字段；如需表达限定词，写入`label`、`condition`、`source_quote`或`review_notes`。

## relation_type

允许：

`clue_supports_identification, mechanism_explains_risk, identification_leads_to_conclusion, conclusion_triggers_response, branch_condition_routes_path, component_assembles_product, standard_constrains_action, result_handoffs_stage, feedback_requests_completion, cycle_requires_monitoring, standard_transmits_requirement, parallel_alternative_no_sequence`。

`branch_condition_routes_path`只能用于带`condition`的`DECIDES`边。证据不足时省略`relation_type`，不得机械映射或硬贴。

## 证据与审核状态

P7C只输出`explicit, functional_dependency, needs_review`；不得输出`rejected`。

核心增量关系全部明确时，card为`accepted`。少量边存在有方向证据的功能依赖时，card为`needs_review`。入口、出口、方向或增量价值不成立时不输出card。

每张card的`review_notes`必填，格式为：
`增量命题：A --关系--> B（条件如有）；KG不足：基础KG不能表达什么；选项判断：可确认或排除什么选项。`

`review_notes`必须使用中文。`title`、`label`和`source_quote`可保留英文教材术语或原文关键词，但解释性内容必须使用中文，避免中英混写。

不得输出空`flow_nodes`或空`flow_edges`。

## 输出结构

每张card必填：
`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, review_status, review_notes`。

顶层必须输出：
`section_id, section_title, cards, skip_reason`。

没有合格card时输出：
{"section_id":"<section_id>","section_title":"<section_title>","cards":[],"skip_reason":"Only knowledge already representable by the base KG, or no evidence-supported incremental directed relation."}

## 当前section

section_id: `CH07-S02`

section_title: `Money laundering risks associated with retail and commercial banking > High-risk retail and commercial banking products`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH07_S02_001",
      "title_zh": "零售银行洗钱风险",
      "title_en": "Retail Banking Money Laundering Risks",
      "anchor_unit_ids": [
        "v7u_N000515",
        "v7u_N000518",
        "v7u_N000520"
      ],
      "key_unit_ids": [
        "v7u_N000515",
        "v7u_N000518",
        "v7u_N000520",
        "v7u_N000516",
        "v7u_N000517"
      ],
      "support_unit_ids": [
        "v7u_N000514",
        "v7u_N000516",
        "v7u_N000517",
        "v7u_N000519"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000515",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000518",
          "unit_type": "definition",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000520",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000516",
          "unit_type": "risk_indicator",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000517",
          "unit_type": "risk_indicator",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000514",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000519",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH07_S02_002",
      "title_zh": "商业银行洗钱风险",
      "title_en": "Commercial Banking Money Laundering Risks",
      "anchor_unit_ids": [
        "v7u_N000521",
        "v7u_N000526",
        "v7u_N000528",
        "v7u_N000529"
      ],
      "key_unit_ids": [
        "v7u_N000521",
        "v7u_N000526",
        "v7u_N000528",
        "v7u_N000529",
        "v7u_N000522"
      ],
      "support_unit_ids": [
        "v7u_N000522",
        "v7u_N000523",
        "v7u_N000524",
        "v7u_N000525",
        "v7u_N000527",
        "v7u_N000530"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000521",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000526",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000528",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000529",
          "unit_type": "risk_indicator",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000522",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000523",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000524",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000525",
          "unit_type": "definition",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000527",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000530",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        }
      ]
    },
    {
      "core_point_id": "cp_CH07_S02_003",
      "title_zh": "贸易型洗钱风险",
      "title_en": "Trade-Based Money Laundering Risks",
      "anchor_unit_ids": [
        "v7u_N000532"
      ],
      "key_unit_ids": [
        "v7u_N000532",
        "v7u_N000533",
        "v7u_N000534",
        "v7u_N000535",
        "v7u_N000536"
      ],
      "support_unit_ids": [
        "v7u_N000531",
        "v7u_N000533",
        "v7u_N000534",
        "v7u_N000535",
        "v7u_N000536",
        "v7u_N000537",
        "v7u_N000538",
        "v7u_N000539",
        "v7u_N000540"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000532",
          "unit_type": "classification",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000533",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000534",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000535",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000536",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000531",
          "unit_type": "definition",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000537",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000538",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000539",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000540",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        }
      ]
    },
    {
      "core_point_id": "cp_CH07_S02_004",
      "title_zh": "易受影响的贸易融资产品",
      "title_en": "Vulnerable Trade Finance Products",
      "anchor_unit_ids": [
        "v7u_N000541",
        "v7u_N000542",
        "v7u_N000543",
        "v7u_N000544"
      ],
      "key_unit_ids": [
        "v7u_N000541",
        "v7u_N000542",
        "v7u_N000543",
        "v7u_N000544",
        "v7u_N000545"
      ],
      "support_unit_ids": [
        "v7u_N000545"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000541",
          "unit_type": "classification",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000542",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000543",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000544",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000545",
          "unit_type": "fact",
          "cp_unit_role": "prescribes_measure"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH07_S02_001",
      "target_id": "cp_CH07_S02_002",
      "relation_type": "parallels",
      "reason": "Both CPs describe money laundering risks in different banking sectors (retail vs. commercial), presented as parallel topics in the section."
    },
    {
      "source_id": "cp_CH07_S02_003",
      "target_id": "cp_CH07_S02_004",
      "relation_type": "prepares",
      "reason": "CP3 explains TBML risks, and CP4 identifies specific trade finance products vulnerable to those risks, so CP3 provides foundational knowledge for CP4."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000514|514] As financial crime continually evolves, both retail and commercial banking sectors face significant risks related to money laundering.
ZH: 零售和商业银行面临不断演变的洗钱风险

[v7u_N000515|515] The increased use of remote onboarding in retail banking has introduced new risks, in particular the rise of synthetic identities.
ZH: 零售银行远程开户带来新风险，尤其是合成身份

[v7u_N000516|516] The process of using selfies and videos for verifying customer identities during onboarding can be exploited using deepfake technology.
ZH: 利用自拍和视频验证身份的过程可能被深度伪造技术利用

[v7u_N000517|517] These synthetic identities can be difficult to detect, posing a significant risk during the customer onboarding process.
ZH: 合成身份难以检测，对客户开户构成重大风险

[v7u_N000518|518] Mule accounts are another high-risk area in retail banking. Criminals recruit individuals, often those in low-income employment or in financial difficulty, to transfer illicit funds through their bank accounts.
ZH: 钱骡账户的定义：犯罪分子招募个人通过其账户转移非法资金

[v7u_N000519|519] These mules act as intermediaries, which makes it challenging for banks to trace the origin of the funds.
ZH: 钱骡作为中间人使银行难以追踪资金来源

[v7u_N000520|520] Credit-related products, including credit cards, also pose money laundering risks. Criminals might use credit cards to make large purchases or withdraw cash, subsequently repaying the credit with illicit funds.
ZH: 信用卡等信贷产品存在洗钱风险，犯罪分子可用非法资金还款

[v7u_N000521|521] In commercial banking, there is a risk of front companies, which are legitimate businesses that criminals use as a cover for money laundering activities.
ZH: 空壳公司是犯罪分子利用合法企业掩盖洗钱活动的工具。

[v7u_N000522|522] These businesses might have legitimate operations but also engage in illicit activities.
ZH: 空壳公司可能同时拥有合法经营和非法活动。

[v7u_N000523|523] This makes it difficult for banks to distinguish between legal and illegal transactions.
ZH: 空壳公司使银行难以区分合法与非法交易。

[v7u_N000524|524] For example, a nail salon with unusually high profits might raise red flags, but one with only slightly higher profits than the regional average might be harder to detect.
ZH: 以美甲店为例，利润异常高可能触发红旗信号信号，但略高于平均水平则难以检测。

[v7u_N000525|525] Compared with corporate banking, commercial banking usually serves small and medium-sized corporations with a primarily local or regional footprint.
ZH: 商业银行业务主要服务本地或区域性的中小企业，区别于企业银行。

[v7u_N000526|526] Therefore, commercial banking often provides services to cash-intensive businesses such as restaurants, convenience stores, and nail salons. These businesses handle large volumes of cash transactions, which makes them vulnerable to money laundering activities.
ZH: 商业银行为现金密集型行业提供服务，这些行业易被用于洗钱。

[v7u_N000527|527] Businesses such as casinos and car dealerships, for instance, handle large cash transactions that can obscure the movement of illicit funds.
ZH: 赌场和汽车经销商等现金密集型行业的大额现金交易可能掩盖非法资金流动。

[v7u_N000528|528] The wide variation of customers within a commercial banking portfolio presents further challenges in establishing transaction monitoring rulesets and programming alert management systems.
ZH: 商业银行业务客户多样性给交易监控规则和警报管理系统带来挑战。

[v7u_N000529|529] Commercial banking might involve high-value transactions, which can be exploited for money laundering purposes. When combined with the large volume of transactions, this can obscure the movement of illicit funds, as they become mixed seamlessly with legitimate cash flows.
ZH: 商业银行业务中的高价值交易可能被用于洗钱，与大量交易混合后难以追踪。

[v7u_N000530|530] Financial institutions should employ sophisticated tools and analytics to monitor and flag suspicious cash or high-value transactions.
ZH: 金融机构应使用先进工具和分析方法监控可疑现金或高价值交易。

[v7u_N000531|531] Trade finance involves a range of financial products and services that facilitate the movement of goods and services across borders and ensure that exporters receive payments promptly while importers receive their goods as agreed.
ZH: 贸易融资是促进跨境货物和服务流动的金融产品和服务。

[v7u_N000532|532] Given the complexity and global nature of trade transactions, money launderers might seek to disguise the proceeds of crime and move value using TBML to misrepresent the price, quantity, or quality of imports and exports. Risks of TBML can include:
ZH: 列举贸易型洗钱（TB洗钱）的风险类型。

[v7u_N000533|533] Trades booked remotely within a group of related entities to obscure the true nature and purpose of transactions.
ZH: 在关联实体集团内远程交易以掩盖交易真实性质。

[v7u_N000534|534] Pre-arranged trading that can create artificial trading volumes and obscure the origin of funds.
ZH: 预先安排的交易可制造虚假交易量并掩盖资金来源。

[v7u_N000535|535] Instructions or involvement from third parties that add layers of complexity, making it harder to trace the source of funds.
ZH: 第三方指令或参与增加复杂性，使资金来源更难追踪。

[v7u_N000536|536] Nonstandard settlement arrangements a customer uses to disguise the true nature of transactions.
ZH: 非标准结算安排被用于掩盖交易真实性质。

[v7u_N000537|537] Uneconomic or irrational trading strategies that do not make economic sense.
ZH: 不经济或不合理的交易策略可能暗示洗钱风险。

[v7u_N000538|538] Unusual trading patterns such as counterparty concentration, unusual winloss rates, or flat or neutralizing activity.
ZH: 异常交易模式如对手方集中、异常盈亏率或中性化活动是洗钱风险信号。

[v7u_N000539|539] Factoring and forfaiting, which can be exploited to convert illicit receivables into legitimate funds.
ZH: 保理和福费廷可能被利用将非法应收账款转换为合法资金。

[v7u_N000540|540] Supply chain financing where complex supply chain arrangements might be used to obscure the origin and flow of illicit funds.
ZH: 供应链融资中复杂的供应链安排可能被用于掩盖非法资金来源和流向。

[v7u_N000541|541] Certain trade finance products are particularly vulnerable to exploitation by money launderers, including:
ZH: 列举易被洗钱滥用的贸易融资产品

[v7u_N000542|542] Letters of credit which can be misused to create fictitious trade transactions to move illicit funds across borders.
ZH: 信用证可被滥用于虚构贸易交易以跨境转移非法资金

[v7u_N000543|543] Bills of exchange that can be manipulated to disguise the true nature of transactions and facilitate money laundering.
ZH: 汇票可被操纵以掩盖交易真实性质并便利洗钱

[v7u_N000544|544] Trade credit insurance where fraudulent claims can be made to launder money.
ZH: 贸易信用保险可能通过欺诈性索赔用于洗钱

[v7u_N000545|545] Understanding the features of trade finance that might be abused and recognizing the associated risks is important for financial institutions, regulatory bodies, and businesses involved in trade. By implementing robust AML/CFT measures and remaining vigilant, stakeholders can mitigate these risks and ensure the integrity of trade finance transactions.
ZH: 金融机构、监管机构和贸易企业需了解贸易融资风险并实施反洗钱/反恐怖融资措施
```

allowed_unit_ids:

```json
[
  "v7u_N000514",
  "v7u_N000515",
  "v7u_N000516",
  "v7u_N000517",
  "v7u_N000518",
  "v7u_N000519",
  "v7u_N000520",
  "v7u_N000521",
  "v7u_N000522",
  "v7u_N000523",
  "v7u_N000524",
  "v7u_N000525",
  "v7u_N000526",
  "v7u_N000527",
  "v7u_N000528",
  "v7u_N000529",
  "v7u_N000530",
  "v7u_N000531",
  "v7u_N000532",
  "v7u_N000533",
  "v7u_N000534",
  "v7u_N000535",
  "v7u_N000536",
  "v7u_N000537",
  "v7u_N000538",
  "v7u_N000539",
  "v7u_N000540",
  "v7u_N000541",
  "v7u_N000542",
  "v7u_N000543",
  "v7u_N000544",
  "v7u_N000545"
]
```
