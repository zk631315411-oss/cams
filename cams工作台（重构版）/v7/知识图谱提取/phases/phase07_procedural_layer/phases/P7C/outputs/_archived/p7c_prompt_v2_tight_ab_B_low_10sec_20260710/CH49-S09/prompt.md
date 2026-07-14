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

section_id: `CH49-S09`

section_title: `Concluding an investigation and suspicious activity reporting > Follow-up action when no SAR is filed`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH49_S09_001",
      "title_zh": "不提交SAR时的决策流程与记录",
      "title_en": "Decision Process and Documentation When Not Filing a SAR",
      "anchor_unit_ids": [
        "v7u_N003588",
        "v7u_N003589",
        "v7u_N003590"
      ],
      "key_unit_ids": [
        "v7u_N003588",
        "v7u_N003589",
        "v7u_N003590",
        "v7u_N003587"
      ],
      "support_unit_ids": [
        "v7u_N003587"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N003588",
          "unit_type": "rule",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003589",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003590",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003587",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH49_S09_002",
      "title_zh": "持续风险重新评估与记录保存义务",
      "title_en": "Ongoing Risk Reassessment and Recordkeeping Obligations",
      "anchor_unit_ids": [
        "v7u_N003591",
        "v7u_N003593",
        "v7u_N003596",
        "v7u_N003600"
      ],
      "key_unit_ids": [
        "v7u_N003591",
        "v7u_N003593",
        "v7u_N003596",
        "v7u_N003600",
        "v7u_N003597"
      ],
      "support_unit_ids": [
        "v7u_N003592",
        "v7u_N003594",
        "v7u_N003595",
        "v7u_N003597",
        "v7u_N003598",
        "v7u_N003599",
        "v7u_N003601"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N003591",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003593",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003596",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003600",
          "unit_type": "rule",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003597",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N003592",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003594",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003595",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003598",
          "unit_type": "rule",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N003599",
          "unit_type": "rule",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N003601",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH49_S09_001",
      "target_id": "cp_CH49_S09_002",
      "relation_type": "prepares",
      "reason": "CP1 establishes the decision process and documentation when not filing a SAR, which sets the foundation for CP2's ongoing risk reassessment and recordkeeping obligations that follow such a decision."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N003587|3587] Reporting suspicious activity is critical for an effective AFC program.
ZH: 报告可疑活动对有效的金融犯罪防控（金融犯罪防控）计划至关重要

[v7u_N003588|3588] In cases where a SAR is not filed, organizations must still adhere to internal procedures to ensure compliance and mitigate risks.
ZH: 未提交SAR时，机构仍须遵守内部程序以确保合规并降低风险

[v7u_N003589|3589] When deciding not to file a SAR, the financial institution must have a clear process for evaluating unusual activity, including an escalation procedure.
ZH: 决定不提交SAR时，金融机构必须有明确的异常活动评估流程，包括升级程序

[v7u_N003590|3590] Document the rationale for not filing a SAR in detail. This includes describing the activity that prompted the review, the steps taken to analyze it, the reasoning behind the decision not to file, and any supporting documents, such as transaction records or memos. This documentation will allow regulators to understand the decision.
ZH: 详细记录不提交SAR的理由，包括活动描述、分析步骤、决策依据及支持文件

[v7u_N003591|3591] A trigger-event KYC review should be conducted to reassess the customer's risk profile based on recent changes, such as updated customer information, unusual transaction patterns, negative news, or changes in ownership.
ZH: 触发事件后应进行了解你的客户审查，根据客户信息变化、异常交易等重新评估风险状况

[v7u_N003592|3592] Thoroughly document the review and actions taken.
ZH: 必须全面记录审查过程和所采取的行动

[v7u_N003593|3593] The customer’s CRA should be reperformed and further risk mitigants considered if there is a change in the customer’s risk profile.
ZH: 客户风险状况变化时，应重新执行客户风险评估（CRA）并考虑进一步风险缓释措施

[v7u_N003594|3594] This process should also be documented.
ZH: 该过程也应记录在案

[v7u_N003595|3595] Additionally, update the client file with all investigation-related documentation.
ZH: 此外，将所有调查相关文件更新至客户档案

[v7u_N003596|3596] Ongoing monitoring should track customer activity for further unusual or suspicious behavior.
ZH: 持续监控应跟踪客户活动，以发现进一步异常或可疑行为

[v7u_N003597|3597] Even if a SAR is not filed, future events might require a review of the client's transaction history and investigation records. This could occur if there is future suspicious activity by the same customer, during regulatory reviews assessing the institution's AFC compliance program, or as part of government or law enforcement inquiries requesting information.
ZH: 即使未提交SAR，未来事件（如同客户再次可疑活动、监管审查或执法查询）可能要求审查客户交易历史和调查记录

[v7u_N003598|3598] Proper record keeping ensures that the organization can readily provide necessary information to regulators and law enforcement.
ZH: 妥善记录保存确保机构能随时向监管和执法部门提供必要信息

[v7u_N003599|3599] By keeping thorough and organized records, organizations demonstrate their commitment to compliance and mitigating potential penalties. All records should be easily accessible and retrievable.
ZH: 保持完整有序的记录，展示合规承诺并减轻潜在处罚，所有记录应易于访问和检索

[v7u_N003600|3600] Not filing a SAR does not absolve the organization of its AFC compliance obligations.
ZH: 不提交SAR并不免除机构的金融犯罪防控（金融犯罪防控）合规义务

[v7u_N003601|3601] Organizations must continue to follow internal procedures to maintain a strong compliance program.
ZH: 组织有义务继续遵循内部程序以维持强有力的合规计划。
```

allowed_unit_ids:

```json
[
  "v7u_N003587",
  "v7u_N003588",
  "v7u_N003589",
  "v7u_N003590",
  "v7u_N003591",
  "v7u_N003592",
  "v7u_N003593",
  "v7u_N003594",
  "v7u_N003595",
  "v7u_N003596",
  "v7u_N003597",
  "v7u_N003598",
  "v7u_N003599",
  "v7u_N003600",
  "v7u_N003601"
]
```
