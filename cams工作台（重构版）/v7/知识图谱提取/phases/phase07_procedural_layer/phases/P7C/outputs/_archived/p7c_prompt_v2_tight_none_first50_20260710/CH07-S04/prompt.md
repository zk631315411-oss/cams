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

section_id: `CH07-S04`

section_title: `Money laundering risks associated with retail and commercial banking > Card risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH07_S04_001",
      "title_zh": "卡相关产品类别",
      "title_en": "Categories of card-related products",
      "anchor_unit_ids": [
        "v7u_N000557"
      ],
      "key_unit_ids": [
        "v7u_N000557"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000557",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        }
      ]
    },
    {
      "core_point_id": "cp_CH07_S04_002",
      "title_zh": "预付卡洗钱风险",
      "title_en": "Prepaid card money laundering risks",
      "anchor_unit_ids": [
        "v7u_N000558"
      ],
      "key_unit_ids": [
        "v7u_N000558",
        "v7u_N000559",
        "v7u_N000560"
      ],
      "support_unit_ids": [
        "v7u_N000559",
        "v7u_N000560"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000558",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000559",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000560",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        }
      ]
    },
    {
      "core_point_id": "cp_CH07_S04_003",
      "title_zh": "礼品卡洗钱风险",
      "title_en": "Gift card money laundering risks",
      "anchor_unit_ids": [
        "v7u_N000561"
      ],
      "key_unit_ids": [
        "v7u_N000561",
        "v7u_N000562"
      ],
      "support_unit_ids": [
        "v7u_N000562"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000561",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000562",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        }
      ]
    },
    {
      "core_point_id": "cp_CH07_S04_004",
      "title_zh": "借记卡洗钱风险缓解",
      "title_en": "Debit card money laundering risk mitigation",
      "anchor_unit_ids": [
        "v7u_N000563"
      ],
      "key_unit_ids": [
        "v7u_N000563",
        "v7u_N000564"
      ],
      "support_unit_ids": [
        "v7u_N000564"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000563",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000564",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH07_S04_005",
      "title_zh": "信用卡洗钱风险特征",
      "title_en": "Credit card money laundering risk characteristics",
      "anchor_unit_ids": [
        "v7u_N000565"
      ],
      "key_unit_ids": [
        "v7u_N000565",
        "v7u_N000566",
        "v7u_N000567"
      ],
      "support_unit_ids": [
        "v7u_N000566",
        "v7u_N000567"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000565",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000566",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000567",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH07_S04_001",
      "target_id": "cp_CH07_S04_002",
      "relation_type": "contains",
      "reason": "CP1 lists categories of card-related products, and CP2 details one of those categories: prepaid cards."
    },
    {
      "source_id": "cp_CH07_S04_001",
      "target_id": "cp_CH07_S04_003",
      "relation_type": "contains",
      "reason": "CP1 lists categories of card-related products, and CP3 details one of those categories: gift cards."
    },
    {
      "source_id": "cp_CH07_S04_001",
      "target_id": "cp_CH07_S04_004",
      "relation_type": "contains",
      "reason": "CP1 lists categories of card-related products, and CP4 details one of those categories: debit cards."
    },
    {
      "source_id": "cp_CH07_S04_001",
      "target_id": "cp_CH07_S04_005",
      "relation_type": "contains",
      "reason": "CP1 lists categories of card-related products, and CP5 details one of those categories: credit cards."
    },
    {
      "source_id": "cp_CH07_S04_002",
      "target_id": "cp_CH07_S04_003",
      "relation_type": "contrasts",
      "reason": "CP2 describes high money laundering risk for prepaid cards, while CP3 describes lower risk for gift cards, explicitly contrasting the risk levels."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000557|557] Retail and commercial banks provide a wide range of card-related products, including but not limited to debit cards, gift cards, prepaid cards, and credit cards.
ZH: 零售和商业银行提供借记卡、礼品卡、预付卡和信用卡等多种卡产品

[v7u_N000558|558] Prepaid cards allow users to load funds onto the card and use it for purchases and withdrawals via common payment processing networks. Unlike debit or credit cards, prepaid cards are not linked to a bank account.
ZH: 预付卡可加载资金用于消费和取现，但不关联银行账户

[v7u_N000559|559] The characteristic of being a bearer instrument and transferable presents a high risk for money laundering.
ZH: 预付卡作为可转让的持票人工具，洗钱风险高

[v7u_N000560|560] Because prepaid cards can be purchased and reloaded anonymously, with minimal KYC being conducted, they are susceptible to exploitation by individuals seeking to move illicit funds without detection.
ZH: 预付卡可匿名购买和充值且了解你的客户要求低，易被用于转移非法资金

[v7u_N000561|561] Gift cards are a popular choice for gifting, providing the recipient with the flexibility to use the card at specific retailers or a group of merchants. They are typically prepaid and can have limited or no ability to be reloaded.
ZH: 礼品卡的定义与特点：预付、灵活使用，通常不可充值。

[v7u_N000562|562] The limited use and lower transaction values of gift cards generally pose a lower risk of misuse when compared to prepaid cards.
ZH: 礼品卡因使用受限、交易金额低，洗钱风险通常低于预付卡。

[v7u_N000563|563] Debit cards are directly linked to a user’s current or checking account, or a savings account, allowing them to access their funds for purchases and withdrawals. Transactions made using a debit card are immediately deducted from the account balance.
ZH: 借记卡直接关联银行账户，交易即时扣减余额。

[v7u_N000564|564] The risk of money laundering with debit cards is somewhat mitigated by the direct association with a bank account and the regulatory oversight and AFC controls that are involved.
ZH: 借记卡因关联银行账户及监管与金融犯罪防控控制，洗钱风险有所缓解。

[v7u_N000565|565] Credit cards allow users to borrow funds up to a predetermined limit for purchases, withdrawals, and balance transfers. Users are required to repay the borrowed amount, usually with interest, according to the terms of the card issuer.
ZH: 信用卡允许用户透支消费、取现及转账，需按条款还款并支付利息。

[v7u_N000566|566] Credit card accounts are not typically used in the initial placement stage of money laundering and are more likely to be used in the layering and integration stages.
ZH: 信用卡账户通常不用于洗钱的处置阶段，更多用于离析阶段和融合阶段。

[v7u_N000567|567] While credit cards are less prone to money laundering risks when compared to prepaid cards, they still require vigilance due to their ability to be overpaid, paid down quickly, or use with purchasing of high-value or luxury goods.
ZH: 信用卡洗钱风险虽低于预付卡，但仍需警惕超额还款、快速还款及购买高价值商品等行为。
```

allowed_unit_ids:

```json
[
  "v7u_N000557",
  "v7u_N000558",
  "v7u_N000559",
  "v7u_N000560",
  "v7u_N000561",
  "v7u_N000562",
  "v7u_N000563",
  "v7u_N000564",
  "v7u_N000565",
  "v7u_N000566",
  "v7u_N000567"
]
```
