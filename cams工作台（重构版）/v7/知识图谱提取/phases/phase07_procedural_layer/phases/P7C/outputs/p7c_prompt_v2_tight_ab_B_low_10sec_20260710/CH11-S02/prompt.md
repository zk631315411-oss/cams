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

不得输出空`flow_nodes`或空`flow_edges`。

## 输出结构

每张card必填：
`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, review_status, review_notes`。

顶层必须输出：
`section_id, section_title, cards, skip_reason`。

没有合格card时输出：
{"section_id":"<section_id>","section_title":"<section_title>","cards":[],"skip_reason":"Only knowledge already representable by the base KG, or no evidence-supported incremental directed relation."}

## 当前section

section_id: `CH11-S02`

section_title: `Money laundering risks associated with MSBs, payment service providers, and ecommerce > Money services business`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH11_S02_001",
      "title_zh": "货币服务企业定义、服务与许可",
      "title_en": "MSB Definition, Services, and Licensing",
      "anchor_unit_ids": [
        "v7u_N000813",
        "v7u_N000814",
        "v7u_N000815",
        "v7u_N000824"
      ],
      "key_unit_ids": [
        "v7u_N000813",
        "v7u_N000814",
        "v7u_N000815",
        "v7u_N000824",
        "v7u_N000817"
      ],
      "support_unit_ids": [
        "v7u_N000816",
        "v7u_N000817",
        "v7u_N000818",
        "v7u_N000819",
        "v7u_N000820",
        "v7u_N000821",
        "v7u_N000822",
        "v7u_N000823",
        "v7u_N000825",
        "v7u_N000826",
        "v7u_N000827"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000813",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000814",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000815",
          "unit_type": "rule",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000824",
          "unit_type": "rule",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000817",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000816",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000818",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000819",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000820",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000821",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000822",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000823",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000825",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000826",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000827",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH11_S02_002",
      "title_zh": "哈瓦拉作为非正式货币服务企业",
      "title_en": "Hawala as an Informal MSB",
      "anchor_unit_ids": [
        "v7u_N000828",
        "v7u_N000829"
      ],
      "key_unit_ids": [
        "v7u_N000828",
        "v7u_N000829"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000828",
          "unit_type": "definition",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000829",
          "unit_type": "classification",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH11_S02_003",
      "title_zh": "货币服务企业洗钱风险与缓释措施",
      "title_en": "MSB Money Laundering Risks and Mitigations",
      "anchor_unit_ids": [
        "v7u_N000830",
        "v7u_N000831",
        "v7u_N000832",
        "v7u_N000833",
        "v7u_N000834",
        "v7u_N000835",
        "v7u_N000836",
        "v7u_N000837",
        "v7u_N000838",
        "v7u_N000839",
        "v7u_N000840"
      ],
      "key_unit_ids": [
        "v7u_N000830",
        "v7u_N000831",
        "v7u_N000832",
        "v7u_N000833",
        "v7u_N000834"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000830",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000831",
          "unit_type": "risk_indicator",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000832",
          "unit_type": "classification",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000833",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000834",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000835",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000836",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000837",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000838",
          "unit_type": "fact",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000839",
          "unit_type": "definition",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000840",
          "unit_type": "rule",
          "cp_unit_role": "explains"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH11_S02_001",
      "target_id": "cp_CH11_S02_002",
      "relation_type": "contains",
      "reason": "CP1 defines MSBs and their services, and CP2 describes hawala as a specific type of MSB (informal value transfer system)."
    },
    {
      "source_id": "cp_CH11_S02_001",
      "target_id": "cp_CH11_S02_003",
      "relation_type": "prepares",
      "reason": "CP1 establishes the definition and regulatory framework for MSBs, which is foundational for understanding the money laundering risks and mitigations discussed in CP3."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000813|813] A money service business (MSB) is a type of nonbank financial institution that provides financial services involving the transfer of money or value.
ZH: 货币服务企业是提供货币或价值转移服务的非银行金融机构

[v7u_N000814|814] An entity is an MSB if it holds funds on behalf of another person or entity.
ZH: 若实体代他人持有资金，则被视为货币服务企业

[v7u_N000815|815] In many jurisdictions, MSBs are required to comply with local regulatory AML and CFT requirements. These requirements can include registering with local regulators and establishing an AML compliance program.
ZH: 许多司法辖区要求货币服务企业遵守反洗钱和反恐怖融资规定，包括注册和建立合规计划

[v7u_N000816|816] MSB services vary according to their licensing requirement. Examples of MSB services include:
ZH: 货币服务企业的服务因牌照要求而异，以下为示例列表

[v7u_N000817|817] Currency exchange
ZH: 货币服务企业的服务包括货币兑换

[v7u_N000818|818] Money transfers
ZH: 货币服务企业的服务包括汇款

[v7u_N000819|819] Money orders
ZH: 货币服务企业的服务包括汇票

[v7u_N000820|820] Stored-value products, such as prepaid cards or gift cards
ZH: 货币服务企业的服务包括储值产品，如预付卡或礼品卡

[v7u_N000821|821] Bill payment services
ZH: 货币服务企业提供的账单支付服务

[v7u_N000822|822] These services can be delivered through online platforms, mobile apps, or physical branches.
ZH: 货币服务企业服务可通过在线平台、移动应用或实体网点提供

[v7u_N000823|823] MSBs originally required licensing mainly for currency exchange, but the scope has expanded to include cross-border money transfers and additional services.
ZH: 货币服务企业许可范围从货币兑换扩展到跨境汇款及其他服务

[v7u_N000824|824] If a business participates in activities categorized as MSB services, it must obtain a license to operate legally.
ZH: 从事货币服务企业服务的企业必须获得许可才能合法运营

[v7u_N000825|825] Historically, MSBs were mainly used to serve individual customers’ crossborder transactions more quickly and cheaply.
ZH: 历史上货币服务企业主要用于为个人客户提供更快更便宜的跨境交易

[v7u_N000826|826] Today, MSBs also serve small and medium-sized businesses that are not served by larger financial institutions.
ZH: 如今货币服务企业也为大型金融机构服务不足的中小企业提供服务

[v7u_N000827|827] The changes in the usage of MSB licenses also bring stringent jurisdictional registration requirements and regulations.
ZH: 货币服务企业许可使用变化带来严格的司法注册要求和法规

[v7u_N000828|828] According to FinCEN, hawala is an informal value transfer system (IVTS), which is classified under the money transmitter category of MSBs.
ZH: FinCEN将哈瓦拉归类为非正式价值转移系统和货币服务企业中的货币转移商

[v7u_N000829|829] However, hawala differs from other, more traditional, MSBs in several ways. The primary distinction is that MSBs are regulated by the banking system, while hawala operates as an informal and largely unregulated method of money transfer.
ZH: 哈瓦拉与传统货币服务企业的主要区别在于监管：货币服务企业受银行体系监管，哈瓦拉为非正规且基本不受监管

[v7u_N000830|830] MSBs face complex jurisdictional licensing requirements, including varying fees and compliance obligations. Each jurisdiction may impose different AML regulations, which can create operational burdens and increase regulatory scrutiny. This complexity can lead to difficulties in maintaining compliance across multiple borders.
ZH: 货币服务企业面临复杂的司法许可要求，包括不同费用和反洗钱合规义务

[v7u_N000831|831] Noncompliance, intentional or accidental, might lead to severe penalties, including regulatory fines, consent orders, and even loss of business licenses.
ZH: 货币服务企业不合规可能导致监管罚款、同意令甚至吊销营业执照

[v7u_N000832|832] MSBs often serve customers or engage in business activities less likely to be supported by traditional financial institutions. These customers include individuals lacking access to mainstream banking services. However, customers without access to traditional banking services can pose challenges when assessing money laundering and terrorist financing risks. Some of these risks include:
ZH: 货币服务企业服务无银行账户客户带来的洗钱和恐怖融资风险

[v7u_N000833|833] Lack of financial history: Unbanked customers often lack financial records, making it difficult for MSBs to assess the legitimacy of their transactions.
ZH: 无银行账户客户缺乏财务记录，货币服务企业难以评估交易合法性

[v7u_N000834|834] Cash transactions: Unbanked individuals rely on cash, which can create vulnerabilities for MSBs, such as difficulty in tracking a high volume of transactions and ascertaining the source of these funds.
ZH: 无银行账户者依赖现金交易，给货币服务企业带来追踪和资金来源确认困难

[v7u_N000835|835] These risks typically fall outside the risk appetite of traditional financial institutions, particularly due to the substantial volume of cross-border remittances.
ZH: 这些风险通常超出传统金融机构的风险偏好，尤其是大量跨境汇款

[v7u_N000836|836] MSBs need to implement additional strategic money laundering and operational controls, such as enhanced due diligence. They should also limit the exposure to high-risk customers.
ZH: 货币服务企业需实施额外洗钱和运营控制，如强化尽职调查，并限制高风险客户敞口

[v7u_N000837|837] Cross-border transactions complicate compliance efforts. Different jurisdictions enforce varying laws regarding fund movement, currency controls, sanctions, and regulatory and tax reporting. Some countries implement strict restrictions on remittances, while others are more lenient.
ZH: 跨境交易因不同司法管辖区的资金流动、货币管制、制裁和税务报告法律而复杂化

[v7u_N000838|838] Establishing long-term and trusted relationships with correspondent banks can mitigate money laundering and compliance risks.
ZH: 与代理行建立长期信任关系可降低洗钱和合规风险

[v7u_N000839|839] A correspondent bank serves as an intermediary in international transactions, aiding the MSB in accessing banking services that might not be directly available to it because of its higher-risk customer base.
ZH: 代理行作为国际交易中介，帮助货币服务企业获得因高风险客户群而无法直接获得的银行服务

[v7u_N000840|840] Correspondent banks are required to assess the soundness of the MSB’s compliance program and ensure that the MSB’s activities align with the correspondent bank’s risk appetite.
ZH: 代理行需评估货币服务企业合规计划的健全性，并确保其活动符合代理行的风险偏好
```

allowed_unit_ids:

```json
[
  "v7u_N000813",
  "v7u_N000814",
  "v7u_N000815",
  "v7u_N000816",
  "v7u_N000817",
  "v7u_N000818",
  "v7u_N000819",
  "v7u_N000820",
  "v7u_N000821",
  "v7u_N000822",
  "v7u_N000823",
  "v7u_N000824",
  "v7u_N000825",
  "v7u_N000826",
  "v7u_N000827",
  "v7u_N000828",
  "v7u_N000829",
  "v7u_N000830",
  "v7u_N000831",
  "v7u_N000832",
  "v7u_N000833",
  "v7u_N000834",
  "v7u_N000835",
  "v7u_N000836",
  "v7u_N000837",
  "v7u_N000838",
  "v7u_N000839",
  "v7u_N000840"
]
```
