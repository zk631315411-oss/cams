# P7C Section-Local Incremental Directed Card Extraction Prompt v2

## 角色

你是P7C局部有向关系提取器。任务不是重复基础知识图谱，而是从单个section中提取基础KG无法表达、且能支持CAMS题目选项判断的增量有向关系。

`flow_nodes + flow_edges`是知识正本。只输出严格JSON，不输出Markdown或解释。准确率优先于card数量。

## 基础KG边界

基础KG能够保存定义、分类、事实、例子、案例、风险指标、规则、控制措施和后果，并标注其语义角色；还能表达CP之间的包含、举例、铺垫、并列、对比、总结和基础关系。

基础KG不能表达具体情境、动作、判断和结果之间的细粒度有向关系。

如果section只有定义、分类、普通案例、孤立红旗、控制措施列表、框架组成、历史背景或机构介绍，必须跳过。不得包装成“入口→评估/实施→列表→分类/产物”。

如果原文明确连接“适用情境→判断或动作→具体结果”，或者包含组合条件、阈值、差异化结论、职责分工、后续应对、控制效果或反馈机制，可以进入P7。

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
可选：`relation_type, condition, qualifier, modality, source_quote, review_status`。

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

section_id: `CH20-S05`

section_title: `AFC guidance from leading international organizations > Basel Committee on Banking Supervision AFC guidance`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH20_S05_001",
      "title_zh": "BCBS概述",
      "title_en": "BCBS Overview",
      "anchor_unit_ids": [
        "v7u_N001521",
        "v7u_N001522",
        "v7u_N001523",
        "v7u_N001524"
      ],
      "key_unit_ids": [
        "v7u_N001521",
        "v7u_N001522",
        "v7u_N001523",
        "v7u_N001524"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N001521",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N001522",
          "unit_type": "definition",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N001523",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N001524",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        }
      ]
    },
    {
      "core_point_id": "cp_CH20_S05_002",
      "title_zh": "BCBS文件类型",
      "title_en": "BCBS Document Types",
      "anchor_unit_ids": [
        "v7u_N001526",
        "v7u_N001527",
        "v7u_N001528"
      ],
      "key_unit_ids": [
        "v7u_N001526",
        "v7u_N001527",
        "v7u_N001528",
        "v7u_N001525"
      ],
      "support_unit_ids": [
        "v7u_N001525"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N001526",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N001527",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N001528",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N001525",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH20_S05_003",
      "title_zh": "1988年BCBS洗钱原则",
      "title_en": "1988 BCBS Principles on Money Laundering",
      "anchor_unit_ids": [
        "v7u_N001530",
        "v7u_N001531",
        "v7u_N001532",
        "v7u_N001533",
        "v7u_N001534",
        "v7u_N001535"
      ],
      "key_unit_ids": [
        "v7u_N001530",
        "v7u_N001531",
        "v7u_N001532",
        "v7u_N001533",
        "v7u_N001534"
      ],
      "support_unit_ids": [
        "v7u_N001529"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N001530",
          "unit_type": "fact",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N001531",
          "unit_type": "fact",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N001532",
          "unit_type": "fact",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N001533",
          "unit_type": "fact",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N001534",
          "unit_type": "fact",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N001535",
          "unit_type": "fact",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N001529",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH20_S05_004",
      "title_zh": "KYC关键要素",
      "title_en": "KYC Key Elements",
      "anchor_unit_ids": [
        "v7u_N001537",
        "v7u_N001538",
        "v7u_N001539",
        "v7u_N001540"
      ],
      "key_unit_ids": [
        "v7u_N001537",
        "v7u_N001538",
        "v7u_N001539",
        "v7u_N001540",
        "v7u_N001536"
      ],
      "support_unit_ids": [
        "v7u_N001536"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N001537",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N001538",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N001539",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N001540",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N001536",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH20_S05_005",
      "title_zh": "BCBS 2014/2020反洗钱/反恐融资指引",
      "title_en": "BCBS 2014/2020 AML/CFT Guidelines",
      "anchor_unit_ids": [
        "v7u_N001542",
        "v7u_N001543",
        "v7u_N001544",
        "v7u_N001545",
        "v7u_N001546",
        "v7u_N001547"
      ],
      "key_unit_ids": [
        "v7u_N001542",
        "v7u_N001543",
        "v7u_N001544",
        "v7u_N001545",
        "v7u_N001546"
      ],
      "support_unit_ids": [
        "v7u_N001541",
        "v7u_N001548"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N001542",
          "unit_type": "fact",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N001543",
          "unit_type": "fact",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N001544",
          "unit_type": "fact",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N001545",
          "unit_type": "classification",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N001546",
          "unit_type": "classification",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N001547",
          "unit_type": "classification",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N001541",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N001548",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH20_S05_001",
      "target_id": "cp_CH20_S05_002",
      "relation_type": "contains",
      "reason": "CP1 provides an overview of BCBS, and CP2 details the types of documents it issues, which is a component of its function."
    },
    {
      "source_id": "cp_CH20_S05_001",
      "target_id": "cp_CH20_S05_003",
      "relation_type": "contains",
      "reason": "CP1 introduces BCBS, and CP3 describes a specific set of principles issued by BCBS in 1988, which is a historical output of the organization."
    },
    {
      "source_id": "cp_CH20_S05_001",
      "target_id": "cp_CH20_S05_005",
      "relation_type": "contains",
      "reason": "CP1 introduces BCBS, and CP5 describes its 2014/2020 guidelines, a later and more comprehensive output of the organization."
    },
    {
      "source_id": "cp_CH20_S05_003",
      "target_id": "cp_CH20_S05_004",
      "relation_type": "prepares",
      "reason": "CP3 covers the 1988 principles, which laid the groundwork for the KYC key elements detailed in CP4, as the 1997 document followed and expanded on the earlier statement."
    },
    {
      "source_id": "cp_CH20_S05_003",
      "target_id": "cp_CH20_S05_005",
      "relation_type": "prepares",
      "reason": "CP3 describes the foundational 1988 principles, which set the stage for the more comprehensive 2014/2020 guidelines in CP5."
    },
    {
      "source_id": "cp_CH20_S05_004",
      "target_id": "cp_CH20_S05_005",
      "relation_type": "prepares",
      "reason": "CP4 outlines KYC key elements, which are foundational concepts that the 2014/2020 guidelines in CP5 build upon for a broader AML framework."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N001521|1521] The Basel Committee on Banking Supervision (BCBS) was established by the G-10 countries in 1974 as the primary global standard setter for bank regulation and as a forum for global cooperation on banking supervision.
ZH: 巴塞尔银行监管委员会（BCBS）由G-10国家于1974年成立，是全球银行监管的主要标准制定者。

[v7u_N001522|1522] Its mandate is to enhance the global banking system through strengthening banking regulation, supervision, and practices.
ZH: BCBS的使命是通过加强银行监管、监督和实践来增强全球银行体系。

[v7u_N001523|1523] It does not have enforcement authority, but relies on its members’ commitment to achieve its mandate.
ZH: BCBS没有执法权，依赖成员承诺来实现其使命。

[v7u_N001524|1524] BCBS members include banking supervisory authorities and central banks from 28 member countries.
ZH: BCBS成员包括来自28个成员国的银行监管机构和中央银行。

[v7u_N001525|1525] BCBS issues:
ZH: BCBS发布三类文件：标准、指南和良好实践。

[v7u_N001526|1526] Standards to incorporate into local legal frameworks.
ZH: BCBS发布标准供各国纳入本地法律框架。

[v7u_N001527|1527] Guidelines for implementing the standards in areas where they are considered desirable for banks’ safety, soundness, and conduct, particularly internationally active banks.
ZH: BCBS发布指南，帮助实施标准以保障银行安全、稳健和操守。

[v7u_N001528|1528] Sound practices that describe actual observed practices, to promote common understanding and improve supervisory or banking approaches.
ZH: BCBS发布良好实践，描述实际观察到的做法，促进共识和改进。

[v7u_N001529|1529] In 1988, the BCBS issued a statement of principles, called Criminal Use of the Banking System for the Purpose of Money Laundering These principles are still useful for AML/CFT as they focus on:
ZH: 1988年BCBS发布《银行系统用于洗钱的犯罪用途》原则声明，聚焦六项要点。

[v7u_N001530|1530] Customer identification.
ZH: 原则要点包括客户身份识别。

[v7u_N001531|1531] Compliance with laws.
ZH: 原则要点包括遵守法律。

[v7u_N001532|1532] Conformity with high ethical standards and local laws and regulations.
ZH: 原则要点包括符合高道德标准及当地法律法规。

[v7u_N001533|1533] Full cooperation with national law enforcement to the extent permitted without breaching customer confidentiality.
ZH: 原则要点包括在不违反客户保密的前提下与执法部门充分合作。

[v7u_N001534|1534] Staff training.
ZH: 原则要点包括员工培训。

[v7u_N001535|1535] Recordkeeping and audits.
ZH: 原则要点包括记录保存和审计。

[v7u_N001536|1536] This statement was followed in 1997 by the issuance of . This document included provisions regarding KYC rules. BCBS periodically updates the principles. However, the key elements of a KYC program remain unchanged and include:
ZH: 1997年BCBS发布文件包含了解你的客户规则，了解你的客户计划的关键要素包括四项。

[v7u_N001537|1537] Customer identification.
ZH: KYC要素包括客户身份识别。

[v7u_N001538|1538] Risk management.
ZH: KYC要素包括风险管理。

[v7u_N001539|1539] Customer acceptance policy.
ZH: KYC要素包括客户接纳政策。

[v7u_N001540|1540] Ongoing monitoring.
ZH: KYC要素包括持续监控。

[v7u_N001541|1541] In 2014, the BCBS issued guidelines titled They were updated in 2020. The guidelines:
ZH: 巴塞尔银行监管委员会于2014年发布并于2020年更新的金融犯罪防控指南

[v7u_N001542|1542] Support banks and supervisors in implementing the FATF Recommendations concerning AML/CFT.
ZH: 指南支持银行和监管机构实施FATF关于反洗钱和反恐怖融资的建议

[v7u_N001543|1543] Advocate for banks to implement risk analysis and governance arrangements.
ZH: 指南倡导银行实施风险分析和治理安排

[v7u_N001544|1544] Describe three lines of defense in a bank’s AML efforts.
ZH: 指南描述了银行反洗钱工作的三道防线

[v7u_N001545|1545] First line: Include business units that identify, assess, and control the risks of their business.
ZH: 第一道防线包括识别、评估和控制业务风险的业务部门

[v7u_N001546|1546] Second line: Include AML compliance and internal controls.
ZH: 第二道防线包括反洗钱合规和内部控制

[v7u_N001547|1547] Third line: Include internal audit functions.
ZH: 第三道防线包括内部审计职能

[v7u_N001548|1548] These guidelines provide banks with a foundation for their AML frameworks and controls.
ZH: 这些指南为银行的反洗钱框架和控制提供了基础
```

allowed_unit_ids:

```json
[
  "v7u_N001521",
  "v7u_N001522",
  "v7u_N001523",
  "v7u_N001524",
  "v7u_N001525",
  "v7u_N001526",
  "v7u_N001527",
  "v7u_N001528",
  "v7u_N001529",
  "v7u_N001530",
  "v7u_N001531",
  "v7u_N001532",
  "v7u_N001533",
  "v7u_N001534",
  "v7u_N001535",
  "v7u_N001536",
  "v7u_N001537",
  "v7u_N001538",
  "v7u_N001539",
  "v7u_N001540",
  "v7u_N001541",
  "v7u_N001542",
  "v7u_N001543",
  "v7u_N001544",
  "v7u_N001545",
  "v7u_N001546",
  "v7u_N001547",
  "v7u_N001548"
]
```
