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

section_id: `CH04-S02`

section_title: `Consequences of financial crime > Institutional accountability to prevent financial crime`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH04_S02_001",
      "title_zh": "受监管实体与义务实体的定义和义务",
      "title_en": "Regulated and Obliged Entities: Definitions and Obligations",
      "anchor_unit_ids": [
        "v7u_N000324",
        "v7u_N000326"
      ],
      "key_unit_ids": [
        "v7u_N000324",
        "v7u_N000326",
        "v7u_N000322",
        "v7u_N000325",
        "v7u_N000323"
      ],
      "support_unit_ids": [
        "v7u_N000321",
        "v7u_N000322",
        "v7u_N000323",
        "v7u_N000325",
        "v7u_N000327",
        "v7u_N000328",
        "v7u_N000329"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000324",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000326",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000322",
          "unit_type": "fact",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000325",
          "unit_type": "rule",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000323",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000321",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000327",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000328",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000329",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH04_S02_002",
      "title_zh": "不遵守金融犯罪义务的后果",
      "title_en": "Consequences of Non-Compliance with Financial Crime Obligations",
      "anchor_unit_ids": [
        "v7u_N000331"
      ],
      "key_unit_ids": [
        "v7u_N000331",
        "v7u_N000332",
        "v7u_N000330"
      ],
      "support_unit_ids": [
        "v7u_N000330",
        "v7u_N000332"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000331",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000332",
          "unit_type": "risk_indicator",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000330",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH04_S02_003",
      "title_zh": "机构的合规投资",
      "title_en": "Institutional Investment in Compliance",
      "anchor_unit_ids": [
        "v7u_N000333"
      ],
      "key_unit_ids": [
        "v7u_N000333"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000333",
          "unit_type": "rule",
          "cp_unit_role": "states_rule"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH04_S02_001",
      "target_id": "cp_CH04_S02_002",
      "relation_type": "prepares",
      "reason": "CP1 defines the entities and their obligations, which sets the foundation for understanding the consequences of non-compliance in CP2."
    },
    {
      "source_id": "cp_CH04_S02_001",
      "target_id": "cp_CH04_S02_003",
      "relation_type": "prepares",
      "reason": "CP1 establishes the regulatory framework and obligations, which logically leads to the requirement for institutional investment in compliance in CP3."
    },
    {
      "source_id": "cp_CH04_S02_002",
      "target_id": "cp_CH04_S02_003",
      "relation_type": "prepares",
      "reason": "CP2 outlines the severe consequences of non-compliance, which motivates the need for compliance investment described in CP3."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000321|321] Financial crime undermines economic stability and has wider negative societal consequences if ignored.
ZH: 金融犯罪破坏经济稳定并带来负面社会后果。

[v7u_N000322|322] Imposing strict obligations through legislation and regulation on institutions with the objective of preventing illicit funds entering and flowing through the financial system is one of the ways to fight financial crime.
ZH: 通过立法和监管对机构施加义务是打击金融犯罪的方式之一。

[v7u_N000323|323] Depending upon the entity type, how regulation is applied can differ greatly due to the distinct differences between regulated entities and obliged entities.
ZH: 受监管实体与义务实体因类型不同，监管适用方式差异很大。

[v7u_N000324|324] A regulated entity is a business that falls under the direct supervision of financial regulators, such as banks, money services businesses, and other financial institutions.
ZH: 受监管实体是直接受金融监管机构监督的企业，如银行、货币服务企业等。

[v7u_N000325|325] These entities must comply with detailed AML/CFT requirements which include, but are not limited to, implementing comprehensive AML programs, conducting customer due diligence, real-time transaction monitoring, and promptly reporting suspicious activity.
ZH: 受监管实体必须遵守详细的反洗钱/反恐怖融资要求，包括实施反洗钱计划、客户尽职调查、实时交易监控和可疑活动报告。

[v7u_N000326|326] An obliged entity is a broader category that includes both regulated entities and nonfinancial organizations subject to other financial crime laws, such as ABC and sanctions regulations.
ZH: 义务实体是更广泛的类别，包括受监管实体和受其他金融犯罪法律约束的非金融组织。

[v7u_N000327|327] For example, sectors like energy, mining, logistics, pharmaceuticals, and real estate might not be directly regulated by financial authorities, yet they must perform risk assessments and have adequate and effective controls to deter financial crime.
ZH: 非金融行业如能源、采矿、物流、制药和房地产等也须进行风险评估并采取控制措施。

[v7u_N000328|328] These organizations are expected to take reasonable steps to prevent illicit activities and to implement remediation measures following enforcement actions, such as fines or leadership changes.
ZH: 义务实体应采取合理措施预防非法活动，并在执法行动后实施补救措施。

[v7u_N000329|329] An entity can be both regulated and obliged, meaning all relevant financial crime laws and regulations will apply to the institution.
ZH: 一个实体可以同时是受监管实体和义务实体，适用所有相关金融犯罪法律。

[v7u_N000330|330] Regulatory developments, such as the AML Act in the US, the Economic Crime and Corporate Transparency Act 2023 in the UK, the EU AML Package, and updated guidelines from FATF, have heightened industry-wide standards.
ZH: 美国反洗钱法案、英国经济犯罪法案、欧盟反洗钱一揽子计划及FATF指南等监管发展提高了行业标准。

[v7u_N000331|331] Failure to comply with these obligations can result in severe consequences, including heavy fines, operational restrictions, and substantial reputational damage.
ZH: 不遵守义务可能导致巨额罚款、运营限制和声誉损害等严重后果。

[v7u_N000332|332] In extreme cases, repeat offenders risk disqualification from critical markets, loss of operating licenses, or entering into a deferred prosecution agreement whereby the offending entity agrees to fulfill certain requirements, such as an overhaul of the AML/CTF compliance program in exchange for the postponement of prosecution.
ZH: 屡犯者可能面临市场禁入、吊销执照或达成暂缓起诉协议。

[v7u_N000333|333] All institutions, irrespective of whether regulated or obliged, must invest in appropriate and effective compliance strategies, staff training, and advanced monitoring technologies to safeguard against financial crime in an increasingly complex environment. These measures not only protect the institution from regulatory scrutiny, but also safeguard consumers and investors, which builds confidence and supports long-term business sustainability.
ZH: 所有机构必须投资合规策略、员工培训和先进监控技术以防范金融犯罪。
```

allowed_unit_ids:

```json
[
  "v7u_N000321",
  "v7u_N000322",
  "v7u_N000323",
  "v7u_N000324",
  "v7u_N000325",
  "v7u_N000326",
  "v7u_N000327",
  "v7u_N000328",
  "v7u_N000329",
  "v7u_N000330",
  "v7u_N000331",
  "v7u_N000332",
  "v7u_N000333"
]
```
