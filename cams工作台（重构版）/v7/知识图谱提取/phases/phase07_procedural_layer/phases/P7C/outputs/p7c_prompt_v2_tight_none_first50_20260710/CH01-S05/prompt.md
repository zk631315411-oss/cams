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

section_id: `CH01-S05`

section_title: `Money Laundering and Financial Crime > Money laundering`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH01_S05_001",
      "title_zh": "洗钱定义与上游犯罪",
      "title_en": "Money Laundering Definition and Predicate Crimes",
      "anchor_unit_ids": [
        "v7u_N000016",
        "v7u_N000017"
      ],
      "key_unit_ids": [
        "v7u_N000016",
        "v7u_N000017",
        "v7u_N000019",
        "v7u_N000018"
      ],
      "support_unit_ids": [
        "v7u_N000018",
        "v7u_N000019"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000016",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000017",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000019",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000018",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        }
      ]
    },
    {
      "core_point_id": "cp_CH01_S05_002",
      "title_zh": "洗钱的三个阶段：处置、离析、融合",
      "title_en": "Three Stages of Money Laundering",
      "anchor_unit_ids": [
        "v7u_N000020",
        "v7u_N000021",
        "v7u_N000022",
        "v7u_N000023"
      ],
      "key_unit_ids": [
        "v7u_N000020",
        "v7u_N000021",
        "v7u_N000022",
        "v7u_N000023",
        "v7u_N000024"
      ],
      "support_unit_ids": [
        "v7u_N000024",
        "v7u_N000025"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000020",
          "unit_type": "classification",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000021",
          "unit_type": "process",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000022",
          "unit_type": "process",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000023",
          "unit_type": "process",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000024",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000025",
          "unit_type": "definition",
          "cp_unit_role": "explains"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH01_S05_001",
      "target_id": "cp_CH01_S05_002",
      "relation_type": "prepares",
      "reason": "CP1 defines money laundering and predicate crimes, providing foundational concepts that prepare for understanding the three stages in CP2."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000016|16] The definition of money laundering varies in each country where it is recognized as a crime. However, it is generally understood to be the process of concealing or disguising the existence, source, movement, destination, or illegal application of criminally derived property or funds to make them appear legitimate.
ZH: 洗钱的定义：掩饰犯罪所得来源使其看似合法的过程

[v7u_N000017|17] Criminal activities that lead to money laundering are also referred to as predicate crimes.
ZH: 导致洗钱的犯罪活动称为上游犯罪

[v7u_N000018|18] Examples include arms sales, narcotics trafficking, contraband smuggling, embezzlement, insider trading, bribery, and fraud schemes.
ZH: 上游犯罪示例：军火销售、毒品贩运、走私、贪污、内幕交易、贿赂和欺诈

[v7u_N000019|19] Different jurisdictions decide which crimes qualify as predicate offenses for the purposes of AML prosecutions.
ZH: 不同司法管辖区自行决定哪些犯罪构成反洗钱起诉的上游犯罪

[v7u_N000020|20] There are three basic stages of money laundering. These are placement, layering, and integration.
ZH: 洗钱三阶段：处置阶段、离析阶段和融合阶段

[v7u_N000021|21] The first stage of money laundering involves placement of funds into a financial system. This process begins with the collection or generation of proceeds derived from criminal activity. This so-called “dirty money” is placed into the financial system, such as through a bank account.
ZH: 洗钱的第一阶段：将犯罪所得资金存入金融系统

[v7u_N000022|22] The proceeds are then layered. Layering involves activities to conceal the origin of the dirty money, such as transferring the proceeds from the bank account to a holding company. Other examples are paying the proceeds to a company in order to pay a false invoice and making a private loan to another company.
ZH: 洗钱的第二阶段：通过复杂交易掩盖资金非法来源

[v7u_N000023|23] Finally, the proceeds are integrated, or used, by the criminal to purchase goods and services in the legitimate economy.
ZH: 洗钱的第三阶段：将清洗后的资金融入合法经济

[v7u_N000024|24] The three stages of money laundering are not always followed in this exact way. Sometimes two of the steps occur almost simultaneously.
ZH: 洗钱三阶段并非固定顺序，有时两步几乎同时发生

[v7u_N000025|25] The important point is that the objective of money laundering is to “clean” or conceal the proceeds of criminal activity in order to use them in the legitimate economy.
ZH: 洗钱的最终目的是将犯罪所得清洗后用于合法经济
```

allowed_unit_ids:

```json
[
  "v7u_N000016",
  "v7u_N000017",
  "v7u_N000018",
  "v7u_N000019",
  "v7u_N000020",
  "v7u_N000021",
  "v7u_N000022",
  "v7u_N000023",
  "v7u_N000024",
  "v7u_N000025"
]
```
