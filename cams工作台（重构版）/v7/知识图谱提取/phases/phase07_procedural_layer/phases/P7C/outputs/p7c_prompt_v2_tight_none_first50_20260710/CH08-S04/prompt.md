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

section_id: `CH08-S04`

section_title: `Private banking and wealth management risks > Offshore financial center risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH08_S04_001",
      "title_zh": "离岸金融中心的定义与特征",
      "title_en": "Definition and Characteristics of Offshore Financial Centers",
      "anchor_unit_ids": [
        "v7u_N000622"
      ],
      "key_unit_ids": [
        "v7u_N000622",
        "v7u_N000623",
        "v7u_N000624",
        "v7u_N000625"
      ],
      "support_unit_ids": [
        "v7u_N000623",
        "v7u_N000624",
        "v7u_N000625"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000622",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000623",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000624",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000625",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH08_S04_002",
      "title_zh": "离岸金融中心的风险与红旗信号",
      "title_en": "Risks and Red Flags of Offshore Financial Centers",
      "anchor_unit_ids": [
        "v7u_N000626",
        "v7u_N000628",
        "v7u_N000629",
        "v7u_N000630",
        "v7u_N000632",
        "v7u_N000633",
        "v7u_N000634"
      ],
      "key_unit_ids": [
        "v7u_N000626",
        "v7u_N000628",
        "v7u_N000629",
        "v7u_N000630",
        "v7u_N000632"
      ],
      "support_unit_ids": [
        "v7u_N000627",
        "v7u_N000631",
        "v7u_N000635",
        "v7u_N000636",
        "v7u_N000637",
        "v7u_N000638",
        "v7u_N000639",
        "v7u_N000640"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000626",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000628",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000629",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000630",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000632",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000633",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000634",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000627",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000631",
          "unit_type": "context",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000635",
          "unit_type": "rule",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000636",
          "unit_type": "risk_indicator",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000637",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000638",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000639",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000640",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        }
      ]
    },
    {
      "core_point_id": "cp_CH08_S04_003",
      "title_zh": "离岸金融中心风险缓释：强化尽职调查与交易监控",
      "title_en": "Mitigating OFC Risks: Enhanced Due Diligence and Transaction Monitoring",
      "anchor_unit_ids": [
        "v7u_N000641"
      ],
      "key_unit_ids": [
        "v7u_N000641"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000641",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH08_S04_001",
      "target_id": "cp_CH08_S04_002",
      "relation_type": "prepares",
      "reason": "CP1 defines OFCs and their legitimate functions, providing the necessary background to understand the risks and red flags discussed in CP2."
    },
    {
      "source_id": "cp_CH08_S04_002",
      "target_id": "cp_CH08_S04_003",
      "relation_type": "prepares",
      "reason": "CP2 identifies the risks and red flags of OFCs, which directly motivates the mitigation measures (enhanced due diligence and transaction monitoring) described in CP3."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000622|622] An offshore financial center (OFC) is a jurisdiction that provides sophisticated financial services to non-residents. OFCs are also known as offshore booking centers.
ZH: 离岸金融中心为非居民提供复杂金融服务

[v7u_N000623|623] They serve as a stable and convenient financial services hub for nonresidents.
ZH: 离岸金融中心作为非居民稳定便捷的金融服务中心

[v7u_N000624|624] OFCs allow businesses to conduct cross-border transactions and manage funds.
ZH: 离岸金融中心支持跨境交易与资金管理

[v7u_N000625|625] Customers who use OFCs benefit from favorable regulatory environments due to their geographical proximity to key markets.
ZH: 离岸金融中心客户受益于有利的监管环境与地理邻近性

[v7u_N000626|626] There is risk related to OFCs when they are used for illicit purposes. OFCs can be used for tax evasion or hiding illicit funds.
ZH: 离岸金融中心被用于逃税或隐藏非法资金的风险

[v7u_N000627|627] Red flags associated with OFCs include:
ZH: 离岸金融中心相关红旗信号信号列表引导

[v7u_N000628|628] Complex ownership structures
ZH: 复杂所有权结构作为离岸金融中心红旗信号

[v7u_N000629|629] Use of shell companies for holding assets
ZH: 使用壳公司持有资产作为离岸金融中心红旗信号

[v7u_N000630|630] Lack of transparency
ZH: 缺乏透明度作为离岸金融中心红旗信号

[v7u_N000631|631] Unusual transaction patterns including:
ZH: 异常交易模式列表引导

[v7u_N000632|632] Sudden, large flows of funds
ZH: 突然的大额资金流动作为异常交易模式

[v7u_N000633|633] Round tripping or moving funds in and out
ZH: 资金循环进出（round tripping）作为异常交易模式

[v7u_N000634|634] Rapid asset transfers between offshore entities
ZH: 离岸实体间快速资产转移作为异常交易模式

[v7u_N000635|635] While some of these red flags can be legitimate business practices, there should be a clear business purpose or reasonable explanation. Otherwise, they are often a sign of illicit activity.
ZH: 红旗信号信号需有明确商业目的或合理解释，否则可能指向非法活动

[v7u_N000636|636] Complex ownership structures can obscure the true beneficial owner and the flow of funds. The use of shell companies can also be an attempt to conceal beneficial ownership.
ZH: 复杂所有权结构与壳公司可掩盖真实受益所有人及资金流向

[v7u_N000637|637] A lack of transparency makes it challenging to obtain complete information on companies and transactions.
ZH: 缺乏透明度导致难以获取公司与交易的完整信息

[v7u_N000638|638] Offshore jurisdictions typically have less stringent reporting and transparency requirements.
ZH: 离岸司法管辖区通常报告与透明度要求较宽松

[v7u_N000639|639] An unusual frequency of transactions with known tax havens or jurisdictions with weak regulations might indicate illicit activity.
ZH: 与已知避税地或监管薄弱地区交易频率异常可能指向非法活动

[v7u_N000640|640] Criminals can also use a technique called round tripping to move funds in and out of the OFC without a legitimate economic purpose. For example, an investor sends funds to the OFC and then reinvests those funds back into their home country.
ZH: 犯罪分子利用资金循环（round tripping）在离岸金融中心进出资金而无合法经济目的

[v7u_N000641|641] Enhanced due diligence is essential to detect any suspicious activity. Transaction monitoring can help uncover potential misuse of OFCs.
ZH: 对离岸金融中心风险需采取强化尽职调查和交易监控
```

allowed_unit_ids:

```json
[
  "v7u_N000622",
  "v7u_N000623",
  "v7u_N000624",
  "v7u_N000625",
  "v7u_N000626",
  "v7u_N000627",
  "v7u_N000628",
  "v7u_N000629",
  "v7u_N000630",
  "v7u_N000631",
  "v7u_N000632",
  "v7u_N000633",
  "v7u_N000634",
  "v7u_N000635",
  "v7u_N000636",
  "v7u_N000637",
  "v7u_N000638",
  "v7u_N000639",
  "v7u_N000640",
  "v7u_N000641"
]
```
