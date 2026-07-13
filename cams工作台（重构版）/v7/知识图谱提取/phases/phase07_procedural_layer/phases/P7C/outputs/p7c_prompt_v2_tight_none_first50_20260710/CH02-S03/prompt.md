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

section_id: `CH02-S03`

section_title: `Types of financial crime > Bribery and corruption`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH02_S03_001",
      "title_zh": "贿赂：定义、形式、礼品风险与ABC政策",
      "title_en": "Bribery: definition, forms, gift risk, and ABC policy",
      "anchor_unit_ids": [
        "v7u_N000115",
        "v7u_N000116",
        "v7u_N000120",
        "v7u_N000122"
      ],
      "key_unit_ids": [
        "v7u_N000115",
        "v7u_N000116",
        "v7u_N000120",
        "v7u_N000122",
        "v7u_N000123"
      ],
      "support_unit_ids": [
        "v7u_N000121",
        "v7u_N000123"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000115",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000116",
          "unit_type": "classification",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000120",
          "unit_type": "definition",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000122",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000123",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000121",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S03_002",
      "title_zh": "腐败：定义、类型与形式",
      "title_en": "Corruption: definition, types, and forms",
      "anchor_unit_ids": [
        "v7u_N000117",
        "v7u_N000118",
        "v7u_N000125",
        "v7u_N000127"
      ],
      "key_unit_ids": [
        "v7u_N000117",
        "v7u_N000118",
        "v7u_N000125",
        "v7u_N000127",
        "v7u_N000119"
      ],
      "support_unit_ids": [
        "v7u_N000119",
        "v7u_N000124",
        "v7u_N000126",
        "v7u_N000128"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000117",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000118",
          "unit_type": "classification",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000125",
          "unit_type": "definition",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000127",
          "unit_type": "definition",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000119",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000124",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000126",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000128",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S03_005",
      "title_zh": "贿赂和腐败与洗钱的联系",
      "title_en": "Bribery and corruption link to money laundering",
      "anchor_unit_ids": [
        "v7u_N000129",
        "v7u_N000130"
      ],
      "key_unit_ids": [
        "v7u_N000129",
        "v7u_N000130"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000129",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000130",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH02_S03_002",
      "target_id": "cp_CH02_S03_001",
      "relation_type": "contains",
      "reason": "CP2 defines corruption and lists bribery as one of its types, so CP2 contains CP1 as a subtype."
    },
    {
      "source_id": "cp_CH02_S03_001",
      "target_id": "cp_CH02_S03_005",
      "relation_type": "prepares",
      "reason": "CP1 defines bribery, which is a prerequisite for understanding its link to money laundering in CP5."
    },
    {
      "source_id": "cp_CH02_S03_002",
      "target_id": "cp_CH02_S03_005",
      "relation_type": "prepares",
      "reason": "CP2 defines corruption, which is a prerequisite for understanding its link to money laundering in CP5."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000115|115] Bribery is giving or receiving money or some other asset in exchange for the improper use of one’s delegated power.
ZH: 贿赂的定义：给予或收受金钱或资产以换取权力滥用

[v7u_N000116|116] A bribe can be in cash but can also take other forms. These forms include gifts, entertainment, business events, hiring, padded invoices, political donations, and kickbacks.
ZH: 贿赂的形式包括现金、礼物、招待、雇佣、虚开发票等

[v7u_N000117|117] Corruption is the misuse of delegated power for one’s personal benefit.
ZH: 腐败的定义：滥用委托权力谋取私利

[v7u_N000118|118] Corruption is a broad term that refers to many types of unethical behavior. These types include bribery, embezzlement, extortion, graft, and influence peddling.
ZH: 腐败包括贿赂、贪污、勒索、收取回扣、影响力交易等

[v7u_N000119|119] People in positions of public power and authority, such as government officials, are particularly susceptible to corruption.
ZH: 政府官员等掌握公共权力者尤其容易腐败

[v7u_N000120|120] The giving of gifts, hospitality, or entertainment can be viewed as bribery, especially if it is lavish.
ZH: 赠送礼物、款待或娱乐若过于奢华可能被视为贿赂

[v7u_N000121|121] However, some cultures not only allow gift giving as a part of doing business but expect it. Failing to provide a gift or refusing a gift might offend a business partner from such a culture.
ZH: 部分文化中，送礼是商业惯例，拒绝可能冒犯商业伙伴。

[v7u_N000122|122] Organizations must clearly define acceptable gifts in their ABC policies.
ZH: 组织必须在反贿赂反腐败政策中明确界定可接受的礼品。

[v7u_N000123|123] An example of bribery is providing expensive tickets to a sporting event to senior members of an organization with which your company is bidding on a project.
ZH: 贿赂示例：向竞标项目的高级成员提供昂贵体育赛事门票。

[v7u_N000124|124] Corruption can occur in various forms.
ZH: 腐败有多种表现形式。

[v7u_N000125|125] In one form, embezzlement, a person entrusted with a position of authority or fiduciary responsibility steals money directly from the government or company.
ZH: 贪污：受托人利用职权直接窃取政府或公司资金。

[v7u_N000126|126] For example, a CFO at a stateowned investment firm misuses his position for self-enrichment by transferring money out of the firm's account into his own personal account.
ZH: 案例：国有投资公司首席财务官将公司资金转入个人账户。

[v7u_N000127|127] In another form, graft, a person obtains a dishonest financial advantage in a less direct way.
ZH: 贪腐：以间接方式获取不正当财务利益。

[v7u_N000128|128] For example, a government official in charge of appropriations hires a road construction company that she owns and overpays the company, to her own profit.
ZH: 贪腐示例：负责拨款的政府官员高价雇佣自己拥有的道路建设公司。

[v7u_N000129|129] Bribery and corruption are often linked to other financial crimes, such as money laundering.
ZH: 贿赂和腐败常与其他金融犯罪（如洗钱）相关联。

[v7u_N000130|130] Organizations face the risk that their customers will launder financial bribes, either given or received, through their accounts.
ZH: 组织面临客户通过其账户清洗贿赂资金的风险。
```

allowed_unit_ids:

```json
[
  "v7u_N000115",
  "v7u_N000116",
  "v7u_N000117",
  "v7u_N000118",
  "v7u_N000119",
  "v7u_N000120",
  "v7u_N000121",
  "v7u_N000122",
  "v7u_N000123",
  "v7u_N000124",
  "v7u_N000125",
  "v7u_N000126",
  "v7u_N000127",
  "v7u_N000128",
  "v7u_N000129",
  "v7u_N000130"
]
```
