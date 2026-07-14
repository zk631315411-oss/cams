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

section_id: `CH05-S04`

section_title: `Financial crime risks in relation to other types of risks > Operational, legal, concentration, and reputational risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH05_S04_001",
      "title_zh": "主要风险类型：运营、法律、集中度、声誉",
      "title_en": "Key risk types: operational, legal, concentration, reputational",
      "anchor_unit_ids": [
        "v7u_N000369"
      ],
      "key_unit_ids": [
        "v7u_N000369"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000369",
          "unit_type": "classification",
          "cp_unit_role": "classifies"
        }
      ]
    },
    {
      "core_point_id": "cp_CH05_S04_002",
      "title_zh": "运营风险：定义与监管挑战",
      "title_en": "Operational risk: definition and regulatory challenges",
      "anchor_unit_ids": [
        "v7u_N000370",
        "v7u_N000375"
      ],
      "key_unit_ids": [
        "v7u_N000370",
        "v7u_N000375",
        "v7u_N000376",
        "v7u_N000377",
        "v7u_N000378"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000370",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000375",
          "unit_type": "definition",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000376",
          "unit_type": "process",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000377",
          "unit_type": "risk_indicator",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000378",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        }
      ]
    },
    {
      "core_point_id": "cp_CH05_S04_003",
      "title_zh": "法律风险：来源、后果及AFC保护",
      "title_en": "Legal risk: sources, consequences, and AFC protection",
      "anchor_unit_ids": [
        "v7u_N000371",
        "v7u_N000379"
      ],
      "key_unit_ids": [
        "v7u_N000371",
        "v7u_N000379",
        "v7u_N000381",
        "v7u_N000380"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000371",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000379",
          "unit_type": "definition",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000381",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000380",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        }
      ]
    },
    {
      "core_point_id": "cp_CH05_S04_004",
      "title_zh": "集中度风险：过度敞口、缓解与管理",
      "title_en": "Concentration risk: over-exposure, mitigation, and management",
      "anchor_unit_ids": [
        "v7u_N000372",
        "v7u_N000382"
      ],
      "key_unit_ids": [
        "v7u_N000372",
        "v7u_N000382",
        "v7u_N000384",
        "v7u_N000385",
        "v7u_N000383"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000372",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000382",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000384",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000385",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000383",
          "unit_type": "fact",
          "cp_unit_role": "prescribes_measure"
        }
      ]
    },
    {
      "core_point_id": "cp_CH05_S04_005",
      "title_zh": "声誉风险：特征与信任因素",
      "title_en": "Reputational risk: characteristics and trust factor",
      "anchor_unit_ids": [
        "v7u_N000373",
        "v7u_N000386"
      ],
      "key_unit_ids": [
        "v7u_N000373",
        "v7u_N000386",
        "v7u_N000387",
        "v7u_N000388"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000373",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000386",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000387",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000388",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH05_S04_001",
      "target_id": "cp_CH05_S04_002",
      "relation_type": "contains",
      "reason": "CP1 lists the four key risk types, and CP2 explains operational risk as one of those types."
    },
    {
      "source_id": "cp_CH05_S04_001",
      "target_id": "cp_CH05_S04_003",
      "relation_type": "contains",
      "reason": "CP1 lists the four key risk types, and CP3 explains legal risk as one of those types."
    },
    {
      "source_id": "cp_CH05_S04_001",
      "target_id": "cp_CH05_S04_004",
      "relation_type": "contains",
      "reason": "CP1 lists the four key risk types, and CP4 explains concentration risk as one of those types."
    },
    {
      "source_id": "cp_CH05_S04_001",
      "target_id": "cp_CH05_S04_005",
      "relation_type": "contains",
      "reason": "CP1 lists the four key risk types, and CP5 explains reputational risk as one of those types."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000369|369] Key risks that organizations face include: Operational, legal, concentration, and reputational.
ZH: 组织面临的主要风险类型包括：运营风险、法律风险、集中度风险和声誉风险。

[v7u_N000370|370] Operational risk is direct or indirect loss of operations due to inadequate or failed internal processes, people, or systems, or as a result of external events.
ZH: 运营风险是因内部流程、人员、系统不完善或外部事件导致直接或间接损失的风险。

[v7u_N000371|371] Legal risk is the possibility that criminal penalties, lawsuits, or contracts that cannot be enforced might harm an organization.
ZH: 法律风险是指刑事处罚、诉讼或不可执行合同可能损害组织的可能性。

[v7u_N000372|372] Concentration risk stems from over-exposure to a single customer or group of related customers.
ZH: 集中度风险源于对单一客户或关联客户群体的过度敞口。

[v7u_N000373|373] Reputational risk comes when an institution known to have weak controls is then targeted by criminals or avoided by stakeholders who lose confidence in the institution.
ZH: 声誉风险是指机构因控制薄弱而被犯罪分子利用或利益相关者失去信心而回避的风险。

[v7u_N000374|374] Although these risks are usually managed by non-AFC risk management teams, understanding the correlation with financial crime risk is indispensable.
ZH: 尽管这些风险通常由非金融犯罪防控团队管理，但理解其与金融犯罪风险的关联至关重要。

[v7u_N000375|375] Operational risk is complex and includes an organization’s ability to maintain AFC controls in an evolving regulatory environment across multiple jurisdictions.
ZH: 运营风险复杂，包括组织在多个司法管辖区不断变化的监管环境中维持金融犯罪防控控制的能力。

[v7u_N000376|376] Typically, a global organization makes the policies of its home regulator its base standard. The organization will then adjust to each host country’s laws.
ZH: 全球组织通常以母国监管机构政策为基础标准，再根据东道国法律进行调整。

[v7u_N000377|377] Evolving regulations might become misaligned with current business models and controls.
ZH: 不断演变的法规可能与现有业务模式和控制措施产生错位。

[v7u_N000378|378] Compliance programs must continually be updated.
ZH: 合规计划必须持续更新。

[v7u_N000379|379] Legal risk stems from potential violation of regulations, laws, and ethical practices.
ZH: 法律风险源于可能违反法规、法律和道德实践。

[v7u_N000380|380] Governments might issue administrative penalties or fines. Third parties, such as customers who feel damaged, might file lawsuits.
ZH: 政府可能处以行政处罚或罚款，受损客户等第三方可能提起诉讼。

[v7u_N000381|381] Adequate AFC controls add protection from crime and inappropriate relationships.
ZH: 充分的金融犯罪防控措施可防范犯罪及不当关系

[v7u_N000382|382] Concentration risk can be reduced by AFC controls and strategic diversification.
ZH: 金融犯罪防控与战略多元化可降低集中度风险

[v7u_N000383|383] Customer due diligence, enabled by technology, helps manage exposure.
ZH: 借助技术的客户尽职调查有助于管理风险敞口

[v7u_N000384|384] Concentration could occur in borrowing, funding, purchasing, provision of key services, or any other business relationship.
ZH: 集中度可能出现在借贷、融资、采购、关键服务提供等业务关系中

[v7u_N000385|385] Risk could increase through actions by a customer, or external actions involving a customer.
ZH: 风险可能因客户行为或涉及客户的外部行为而增加

[v7u_N000386|386] Reputational risk is difficult to quantify.
ZH: 声誉风险难以量化

[v7u_N000387|387] Trust takes a long time to earn but can be lost quickly. A single news story—even fake news—can drive away customers and investors.
ZH: 信任建立缓慢但易丧失，一条新闻即可驱离客户与投资者

[v7u_N000388|388] Many organizations deserve their reputations, good or bad, based on their chosen business practices and ethics.
ZH: 组织的声誉源于其商业实践与道德选择
```

allowed_unit_ids:

```json
[
  "v7u_N000369",
  "v7u_N000370",
  "v7u_N000371",
  "v7u_N000372",
  "v7u_N000373",
  "v7u_N000374",
  "v7u_N000375",
  "v7u_N000376",
  "v7u_N000377",
  "v7u_N000378",
  "v7u_N000379",
  "v7u_N000380",
  "v7u_N000381",
  "v7u_N000382",
  "v7u_N000383",
  "v7u_N000384",
  "v7u_N000385",
  "v7u_N000386",
  "v7u_N000387",
  "v7u_N000388"
]
```
