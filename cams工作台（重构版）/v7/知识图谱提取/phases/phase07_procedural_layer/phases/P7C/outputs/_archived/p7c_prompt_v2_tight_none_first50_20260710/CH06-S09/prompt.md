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

section_id: `CH06-S09`

section_title: `Money Laundering Risks in Financial Services > Politically exposed person risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH06_S09_001",
      "title_zh": "政治敏感人物的定义、范围和关联人",
      "title_en": "PEP definition, scope, and related persons",
      "anchor_unit_ids": [
        "v7u_N000457",
        "v7u_N000469",
        "v7u_N000470",
        "v7u_N000473",
        "v7u_N000474",
        "v7u_N000475"
      ],
      "key_unit_ids": [
        "v7u_N000457",
        "v7u_N000469",
        "v7u_N000470",
        "v7u_N000473",
        "v7u_N000474"
      ],
      "support_unit_ids": [
        "v7u_N000467",
        "v7u_N000468",
        "v7u_N000471",
        "v7u_N000472"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000457",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000469",
          "unit_type": "fact",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000470",
          "unit_type": "fact",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000473",
          "unit_type": "fact",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000474",
          "unit_type": "fact",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000475",
          "unit_type": "fact",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000467",
          "unit_type": "rule",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000468",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000471",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000472",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH06_S09_002",
      "title_zh": "政治敏感人物识别挑战与合规要求",
      "title_en": "PEP Identification Challenges and Compliance",
      "anchor_unit_ids": [
        "v7u_N000458",
        "v7u_N000459",
        "v7u_N000460"
      ],
      "key_unit_ids": [
        "v7u_N000458",
        "v7u_N000459",
        "v7u_N000460"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000458",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000459",
          "unit_type": "rule",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000460",
          "unit_type": "rule",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH06_S09_003",
      "title_zh": "FATF对政治敏感人物的分类",
      "title_en": "FATF Classification of PEP Types",
      "anchor_unit_ids": [
        "v7u_N000462",
        "v7u_N000463",
        "v7u_N000464"
      ],
      "key_unit_ids": [
        "v7u_N000462",
        "v7u_N000463",
        "v7u_N000464",
        "v7u_N000461"
      ],
      "support_unit_ids": [
        "v7u_N000461"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000462",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000463",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000464",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000461",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH06_S09_004",
      "title_zh": "政治敏感人物的腐败风险与示例",
      "title_en": "PEP Vulnerability to Corruption and Examples",
      "anchor_unit_ids": [
        "v7u_N000465"
      ],
      "key_unit_ids": [
        "v7u_N000465",
        "v7u_N000466"
      ],
      "support_unit_ids": [
        "v7u_N000466"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000465",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000466",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        }
      ]
    },
    {
      "core_point_id": "cp_CH06_S09_005",
      "title_zh": "政治敏感人物风险管理与监控方法",
      "title_en": "PEP Risk Management and Monitoring Approaches",
      "anchor_unit_ids": [
        "v7u_N000476",
        "v7u_N000477",
        "v7u_N000481",
        "v7u_N000482"
      ],
      "key_unit_ids": [
        "v7u_N000476",
        "v7u_N000477",
        "v7u_N000481",
        "v7u_N000482",
        "v7u_N000479"
      ],
      "support_unit_ids": [
        "v7u_N000478",
        "v7u_N000479",
        "v7u_N000480"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000476",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000477",
          "unit_type": "rule",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000481",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000482",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000479",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000478",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000480",
          "unit_type": "rule",
          "cp_unit_role": "explains"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH06_S09_001",
      "target_id": "cp_CH06_S09_003",
      "relation_type": "prepares",
      "reason": "CP1 defines PEP and its scope, providing the foundational definition needed to understand the FATF classification in CP3."
    },
    {
      "source_id": "cp_CH06_S09_001",
      "target_id": "cp_CH06_S09_004",
      "relation_type": "prepares",
      "reason": "CP1 defines PEP, which is necessary to understand the vulnerability to corruption discussed in CP4."
    },
    {
      "source_id": "cp_CH06_S09_001",
      "target_id": "cp_CH06_S09_005",
      "relation_type": "prepares",
      "reason": "CP1 defines PEP, which is the prerequisite for the risk management and monitoring approaches in CP5."
    },
    {
      "source_id": "cp_CH06_S09_002",
      "target_id": "cp_CH06_S09_005",
      "relation_type": "prepares",
      "reason": "CP2 discusses identification challenges and compliance requirements, which set the stage for the risk management approaches in CP5."
    },
    {
      "source_id": "cp_CH06_S09_003",
      "target_id": "cp_CH06_S09_004",
      "relation_type": "prepares",
      "reason": "CP3 classifies PEP types, which helps understand the specific vulnerabilities to corruption discussed in CP4."
    },
    {
      "source_id": "cp_CH06_S09_004",
      "target_id": "cp_CH06_S09_005",
      "relation_type": "prepares",
      "reason": "CP4 explains PEP vulnerability to corruption, which is the risk that CP5's management and monitoring approaches aim to address."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000457|457] A politically exposed person (PEP) is an individual in a prominent political function, their immediate family, close associates, and any businesses held or controlled by that person.
ZH: 政治敏感人物（政治敏感人物）的定义：担任重要公职的个人及其亲属和密切关联人

[v7u_N000458|458] One challenge in identifying PEPs is the varying guidance and recommendations in each jurisdiction.
ZH: 识别政治敏感人物的挑战在于各司法管辖区指引不同

[v7u_N000459|459] Organizations must adhere to their local regulatory requirements in identifying PEPs.
ZH: 机构必须遵守当地监管要求识别政治敏感人物

[v7u_N000460|460] However, organizations may choose to enforce higher standards based on their risk appetite.
ZH: 机构可根据风险偏好执行更高的政治敏感人物标准

[v7u_N000461|461] According to the Financial Action Task Force (FATF), there are three types of PEPs:
ZH: FATF将政治敏感人物分为三类

[v7u_N000462|462] Foreign PEPs are individuals entrusted with prominent public functions by a foreign country.
ZH: 外国政治敏感人物指受外国委托担任重要公共职能的个人

[v7u_N000463|463] Domestic PEPs are individuals entrusted domestically with prominent public functions.
ZH: 国内政治敏感人物指在国内担任重要公共职能的个人

[v7u_N000464|464] International organization PEPs are individuals from an international organization entrusted with a prominent function such as secretary general, executive director, or president.
ZH: 国际组织政治敏感人物指在国际组织中担任秘书长、执行董事或主席等要职的个人

[v7u_N000465|465] Individuals in high positions and their associates are more vulnerable to corruption.
ZH: 高层职位个人及其关联人更易受腐败影响

[v7u_N000466|466] Corruption might be favors where the PEP directs government contracts to an organization in return for kickbacks. In addition, a PEP might influence legislation for bribes or flee the country with government funds.
ZH: 政治敏感人物腐败示例：以政府合同换取回扣、影响立法收受贿赂或携政府资金潜逃

[v7u_N000467|467] Use a broad definition for defining a PEP.
ZH: 应采用宽泛定义来界定政治敏感人物

[v7u_N000468|468] PEPs can generally be defined as:
ZH: 政治敏感人物的一般定义

[v7u_N000469|469] A person in a prominent decision-making or influential role
ZH: 政治敏感人物指担任重要决策或有影响力角色的人

[v7u_N000470|470] A person within royal, military, legislative, judicial, executive, or similar government positions
ZH: 政治敏感人物包括王室、军事、立法、司法、行政或类似政府职位的人

[v7u_N000471|471] PEPs will often use nominees or businesses they are associated with.
ZH: 政治敏感人物常使用名义人或关联企业

[v7u_N000472|472] Therefore, the definition of PEP can also include:
ZH: 政治敏感人物定义还可包括以下人员

[v7u_N000473|473] Immediate family
ZH: 政治敏感人物的直系亲属

[v7u_N000474|474] Close friends or associates
ZH: 政治敏感人物的密友或关联人

[v7u_N000475|475] Businesses owned or held by those individuals
ZH: 政治敏感人物拥有或持有的企业

[v7u_N000476|476] Under a risk-based approach, PEP risk is manageable.
ZH: 基于风险的方法下，政治敏感人物风险是可控的

[v7u_N000477|477] Some organizations follow a “once a PEP, always a PEP” approach because the individual may remain in the same circles of influence, even if they have stepped down.
ZH: 部分机构采用“一旦是政治敏感人物，永远是政治敏感人物”的方法

[v7u_N000478|478] Other organizations will look at:
ZH: 其他机构会考察以下因素

[v7u_N000479|479] The individual’s influence at the time, such as their ability to award contracts or allocate funds
ZH: 考察个人当时的影响力，如授予合同或分配资金的能力

[v7u_N000480|480] How long the individual has been classified as a PEP
ZH: 考察个人被归类为政治敏感人物的时间长短

[v7u_N000481|481] The purpose of the PEP designation is important.
ZH: 政治敏感人物 认定的目的具有重要意义

[v7u_N000482|482] Organizations must take the necessary steps to adapt transaction monitoring and KYC reviews and escalate based on their risk appetite.
ZH: 机构必须根据风险偏好调整交易监控和 了解你的客户 审查
```

allowed_unit_ids:

```json
[
  "v7u_N000457",
  "v7u_N000458",
  "v7u_N000459",
  "v7u_N000460",
  "v7u_N000461",
  "v7u_N000462",
  "v7u_N000463",
  "v7u_N000464",
  "v7u_N000465",
  "v7u_N000466",
  "v7u_N000467",
  "v7u_N000468",
  "v7u_N000469",
  "v7u_N000470",
  "v7u_N000471",
  "v7u_N000472",
  "v7u_N000473",
  "v7u_N000474",
  "v7u_N000475",
  "v7u_N000476",
  "v7u_N000477",
  "v7u_N000478",
  "v7u_N000479",
  "v7u_N000480",
  "v7u_N000481",
  "v7u_N000482"
]
```
