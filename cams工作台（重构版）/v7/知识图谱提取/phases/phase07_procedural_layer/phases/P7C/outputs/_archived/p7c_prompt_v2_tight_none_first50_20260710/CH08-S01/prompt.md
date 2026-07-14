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

section_id: `CH08-S01`

section_title: `Private banking and wealth management risks > Money laundering risks associated with private banking and wealth management`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH08_S01_001",
      "title_zh": "私人银行与财富管理的定义与特点",
      "title_en": "Private Banking and Wealth Management Definition and Features",
      "anchor_unit_ids": [
        "v7u_N000575",
        "v7u_N000576",
        "v7u_N000577"
      ],
      "key_unit_ids": [
        "v7u_N000575",
        "v7u_N000576",
        "v7u_N000577"
      ],
      "support_unit_ids": [
        "v7u_N000575",
        "v7u_N000576",
        "v7u_N000577"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000575",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000576",
          "unit_type": "definition",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000577",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH08_S01_002",
      "title_zh": "私人银行固有的金融犯罪风险",
      "title_en": "Inherent Financial Crime Risks in Private Banking",
      "anchor_unit_ids": [
        "v7u_N000578",
        "v7u_N000579",
        "v7u_N000580",
        "v7u_N000581"
      ],
      "key_unit_ids": [
        "v7u_N000578",
        "v7u_N000579",
        "v7u_N000580",
        "v7u_N000581"
      ],
      "support_unit_ids": [
        "v7u_N000578",
        "v7u_N000579",
        "v7u_N000580",
        "v7u_N000581"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000578",
          "unit_type": "risk_indicator",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000579",
          "unit_type": "risk_indicator",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000580",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000581",
          "unit_type": "risk_indicator",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH08_S01_003",
      "title_zh": "私人银行高风险客户类型",
      "title_en": "High-Risk Customer Profiles in Private Banking",
      "anchor_unit_ids": [
        "v7u_N000583",
        "v7u_N000584",
        "v7u_N000585"
      ],
      "key_unit_ids": [
        "v7u_N000583",
        "v7u_N000584",
        "v7u_N000585",
        "v7u_N000582"
      ],
      "support_unit_ids": [
        "v7u_N000582",
        "v7u_N000583",
        "v7u_N000584",
        "v7u_N000585"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000583",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000584",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000585",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000582",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH08_S01_004",
      "title_zh": "私人银行的合规与风险管理控制",
      "title_en": "Compliance and Risk Management Controls in Private Banking",
      "anchor_unit_ids": [
        "v7u_N000586",
        "v7u_N000587"
      ],
      "key_unit_ids": [
        "v7u_N000586",
        "v7u_N000587"
      ],
      "support_unit_ids": [
        "v7u_N000586",
        "v7u_N000587"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000586",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000587",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH08_S01_001",
      "target_id": "cp_CH08_S01_002",
      "relation_type": "prepares",
      "reason": "CP1 defines private banking and its features, providing the foundation for understanding the inherent financial crime risks discussed in CP2."
    },
    {
      "source_id": "cp_CH08_S01_002",
      "target_id": "cp_CH08_S01_003",
      "relation_type": "contains",
      "reason": "CP2 discusses inherent financial crime risks, and CP3 provides specific examples of high-risk customer profiles that illustrate those risks."
    },
    {
      "source_id": "cp_CH08_S01_002",
      "target_id": "cp_CH08_S01_004",
      "relation_type": "prepares",
      "reason": "CP2 explains the inherent risks, which sets the stage for the compliance and risk management controls described in CP4."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000575|575] Private banking and wealth management offer high-net-worth and ultrahigh-net-worth individuals personalized and confidential banking services, such as checking/current accounts, saving accounts, investment portfolio management, estate planning, and legacy services.
ZH: 私人银行与财富管理为高净值及超高净值个人提供个性化、保密的银行服务。

[v7u_N000576|576] Fees are often based on assets under management (AUM), which is the total market value of the assets that a person, or entity, manages on behalf of a customer.
ZH: 私人银行费用通常基于管理资产规模（AUM）计算。

[v7u_N000577|577] Private banking often operates semi-autonomously from other parts of a bank.
ZH: 私人银行通常半自主运营，独立于银行其他部门。

[v7u_N000578|578] Some of the financial crime risks associated with private banking stem from its perceived high profitability for the organization and the culture of discretion and trust between the relationship managers and their customers.
ZH: 私人银行的金融犯罪风险源于其高盈利性以及关系经理与客户间的保密与信任文化。

[v7u_N000579|579] The desire to establish and maintain close relationships with their customers might cause relationship managers to overlook warning signs.
ZH: 关系经理为维护客户关系可能忽视警示信号，增加洗钱风险。

[v7u_N000580|580] Competition for high-net-worth individuals increases the pressure on relationship managers to obtain new customers, to increase their AUM, and to contribute a greater percentage to the net income of their organizations. Additionally, most relationship managers and business development managers receive compensation based on the AUM they bring to their institutions.
ZH: 私人银行关系经理的薪酬通常基于其带来的管理资产规模，增加获取新客户的压力。

[v7u_N000581|581] Due to this compensation structure, private banking managers might not recognize certain aspects of their customer activities as high risk from an AFC perspective. This conflict of interest is an inherent risk of private banking and wealth management.
ZH: 私人银行薪酬结构导致利益冲突，构成金融犯罪防控固有风险

[v7u_N000582|582] Other examples of financial crime risk in private banking include:
ZH: 列举私人银行金融犯罪风险的其他示例

[v7u_N000583|583] Customers who use private investment companies or complex ownership structures to reduce the transparency of the ultimate beneficial owners.
ZH: 客户使用私人投资公司或复杂所有权结构降低最终受益所有人透明度

[v7u_N000584|584] Customers who choose to maintain personal and business wealth in numerous jurisdictions without justified business reasons to evade tax.
ZH: 客户在多个司法管辖区持有财富且无合理商业理由，可能为逃税

[v7u_N000585|585] Customers who are considered PEPs or have close associates who are PEPs increase the bribery and corruption risk of the business.
ZH: 政治敏感人物（政治敏感人物）或其密切关联人增加贿赂与腐败风险

[v7u_N000586|586] The compliance department must be empowered and robust in its approach to providing proper oversight and challenges to the business.
ZH: 合规部门必须有权有力，对业务进行适当监督与质疑

[v7u_N000587|587] Business leaders should use a balanced scorecard for performance evaluation. This ensures that managing risk remains a fundamental part of the private banker's role.
ZH: 业务领导者应使用平衡计分卡进行绩效评估，确保风险管理融入私人银行家职责

[v7u_N000588|588] Here are a few higher risks associated with private banking and wealth management.
ZH: 引出私人银行与财富管理相关的若干较高风险
```

allowed_unit_ids:

```json
[
  "v7u_N000575",
  "v7u_N000576",
  "v7u_N000577",
  "v7u_N000578",
  "v7u_N000579",
  "v7u_N000580",
  "v7u_N000581",
  "v7u_N000582",
  "v7u_N000583",
  "v7u_N000584",
  "v7u_N000585",
  "v7u_N000586",
  "v7u_N000587",
  "v7u_N000588"
]
```
