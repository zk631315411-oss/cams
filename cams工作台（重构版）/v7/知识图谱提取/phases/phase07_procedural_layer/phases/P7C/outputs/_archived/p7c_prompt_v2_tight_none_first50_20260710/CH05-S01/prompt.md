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

section_id: `CH05-S01`

section_title: `Financial crime risks in relation to other types of risks > Financial crime risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH05_S01_001",
      "title_zh": "义务实体与高风险机构",
      "title_en": "Obliged Entities and High-Risk Institutions",
      "anchor_unit_ids": [
        "v7u_N000344",
        "v7u_N000346"
      ],
      "key_unit_ids": [
        "v7u_N000344",
        "v7u_N000346",
        "v7u_N000343",
        "v7u_N000345"
      ],
      "support_unit_ids": [
        "v7u_N000343",
        "v7u_N000345"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000344",
          "unit_type": "case",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000346",
          "unit_type": "classification",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000343",
          "unit_type": "fact",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000345",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH05_S01_002",
      "title_zh": "金融犯罪风险类型",
      "title_en": "Types of Financial Crime Risks",
      "anchor_unit_ids": [
        "v7u_N000348",
        "v7u_N000349",
        "v7u_N000350",
        "v7u_N000351",
        "v7u_N000352",
        "v7u_N000353"
      ],
      "key_unit_ids": [
        "v7u_N000348",
        "v7u_N000349",
        "v7u_N000350",
        "v7u_N000351",
        "v7u_N000352"
      ],
      "support_unit_ids": [
        "v7u_N000347"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000348",
          "unit_type": "classification",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000349",
          "unit_type": "definition",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000350",
          "unit_type": "risk_indicator",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000351",
          "unit_type": "risk_indicator",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000352",
          "unit_type": "definition",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000353",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000347",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH05_S01_003",
      "title_zh": "风险缓解与合规",
      "title_en": "Risk Mitigation and Compliance",
      "anchor_unit_ids": [
        "v7u_N000354",
        "v7u_N000355"
      ],
      "key_unit_ids": [
        "v7u_N000354",
        "v7u_N000355"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000354",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000355",
          "unit_type": "fact",
          "cp_unit_role": "prescribes_measure"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH05_S01_001",
      "target_id": "cp_CH05_S01_002",
      "relation_type": "prepares",
      "reason": "CP1 defines obliged entities and their high-risk status, setting the foundation for CP2 which details the specific types of financial crime risks these entities face."
    },
    {
      "source_id": "cp_CH05_S01_002",
      "target_id": "cp_CH05_S01_003",
      "relation_type": "prepares",
      "reason": "CP2 outlines the various financial crime risks, and CP3 describes the mitigation and compliance measures to address those risks."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000343|343] Institutions that deal with money or assets with transferable value have greater exposure to financial crime risks when conducting business.
ZH: 处理货币或可转让价值资产的机构面临更高金融犯罪风险

[v7u_N000344|344] These include, but are not limited to, banks, nonbank financial institutions, payment service providers, legal firms, and accountants.
ZH: 高风险机构包括银行、非银行金融机构、支付服务商、律所和会计师

[v7u_N000345|345] Criminals exploit these sectors to move illicit funds and obscure ownership structures to evade detection.
ZH: 犯罪分子利用这些行业转移非法资金并隐藏所有权结构

[v7u_N000346|346] Due to their vulnerability, these specific industries, and some others, are deemed “obliged” entities and are subject to stringent financial crime regulations.
ZH: 这些行业被认定为义务实体，须遵守严格的金融犯罪法规

[v7u_N000347|347] The risks associated with financial crime exposure are multifaceted and go far beyond direct financial losses.
ZH: 金融犯罪风险是多方面的，远超直接经济损失

[v7u_N000348|348] Some types of risks that organizations face include, but are not limited to, operational, legal, concentration, and reputational.
ZH: 机构面临的金融犯罪风险类型包括操作、法律、集中和声誉风险

[v7u_N000349|349] Institutions also face systemic risks, where criminal misuse of financial systems can destabilize entire markets or financial ecosystems.
ZH: 系统性风险指犯罪滥用金融系统可能 destabilize 整个市场或金融生态

[v7u_N000350|350] Cybersecurity risks increase as institutions manage digital transactions and combat emerging threats such as ransomware and deepfake fraud.
ZH: 数字交易带来网络安全风险，如勒索软件和深度伪造欺诈

[v7u_N000351|351] Geopolitical risks arise when financial crime intersects with internationa sanctions, trade restrictions, or politically exposed persons, making compliance even more complex and challenging to manage.
ZH: 金融犯罪与国际制裁、贸易限制或政治公众人物交织产生地缘政治风险

[v7u_N000352|352] Regulatory fragmentation presents another challenge, as global financial crime compliance requirements vary across jurisdictions. Regulatory fragmentation is when multiple regulatory bodies have varying rules around the same issue, often creating inconsistencies in enforcement and risk exposure.
ZH: 监管碎片化指不同司法管辖区对同一问题规则不一，导致执法和风险暴露不一致

[v7u_N000353|353] Additionally, technological risks emerge as digital payment platforms, cryptocurrencies, and decentralized finance introduce new and largely unquantified financial crime risks that institutions must monitor and mitigate.
ZH: 数字支付平台、加密货币和去中心化金融带来新的技术风险

[v7u_N000354|354] To address these risks, obliged entities must implement proactive financial crime compliance programs, including transaction monitoring and utilization of tools such as AI, enhanced due diligence, and real-time fraud detection.
ZH: 义务实体必须实施主动的金融犯罪合规计划，包括交易监控和AI工具

[v7u_N000355|355] Strengthening governance frameworks and improving inter-agency collaboration ensures that financial institutions remain resilient against financial crime threats while maintaining regulatory compliance and market stability.
ZH: 加强治理框架和机构间协作有助于金融机构抵御金融犯罪威胁
```

allowed_unit_ids:

```json
[
  "v7u_N000343",
  "v7u_N000344",
  "v7u_N000345",
  "v7u_N000346",
  "v7u_N000347",
  "v7u_N000348",
  "v7u_N000349",
  "v7u_N000350",
  "v7u_N000351",
  "v7u_N000352",
  "v7u_N000353",
  "v7u_N000354",
  "v7u_N000355"
]
```
