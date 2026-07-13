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

section_id: `CH02-S06`

section_title: `Types of financial crime > Cyber-enabled crime`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH02_S06_001",
      "title_zh": "网络犯罪的定义与范围",
      "title_en": "Definition and scope of cyber-enabled crime",
      "anchor_unit_ids": [
        "v7u_N000181",
        "v7u_N000182"
      ],
      "key_unit_ids": [
        "v7u_N000181",
        "v7u_N000182",
        "v7u_N000180"
      ],
      "support_unit_ids": [
        "v7u_N000180"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000181",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000182",
          "unit_type": "classification",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000180",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S06_004",
      "title_zh": "与洗钱和恐怖融资的关联",
      "title_en": "Connection to money laundering and terrorist financing",
      "anchor_unit_ids": [
        "v7u_N000183",
        "v7u_N000197",
        "v7u_N000198"
      ],
      "key_unit_ids": [
        "v7u_N000183",
        "v7u_N000197",
        "v7u_N000198"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000183",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000197",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000198",
          "unit_type": "fact",
          "cp_unit_role": "describes_process"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S06_002A",
      "title_zh": "基于信任的网络犯罪手段",
      "title_en": "Trust-based cyber-enabled crime methods",
      "anchor_unit_ids": [
        "v7u_N000185",
        "v7u_N000186",
        "v7u_N000187",
        "v7u_N000193",
        "v7u_N000194"
      ],
      "key_unit_ids": [
        "v7u_N000185",
        "v7u_N000186",
        "v7u_N000187",
        "v7u_N000193",
        "v7u_N000194"
      ],
      "support_unit_ids": [
        "v7u_N000184"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000185",
          "unit_type": "fact",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000186",
          "unit_type": "fact",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000187",
          "unit_type": "fact",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000193",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000194",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000184",
          "unit_type": "classification",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S06_002B",
      "title_zh": "网络犯罪造成的结果和类型",
      "title_en": "Cyber-enabled crime outcomes and result types",
      "anchor_unit_ids": [
        "v7u_N000189",
        "v7u_N000190",
        "v7u_N000191",
        "v7u_N000192"
      ],
      "key_unit_ids": [
        "v7u_N000189",
        "v7u_N000190",
        "v7u_N000191",
        "v7u_N000192",
        "v7u_N000188"
      ],
      "support_unit_ids": [
        "v7u_N000188"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000189",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000190",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000191",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000192",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000188",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S06_003",
      "title_zh": "网络犯罪的示例",
      "title_en": "Examples of cyber-enabled crime",
      "anchor_unit_ids": [
        "v7u_N000195"
      ],
      "key_unit_ids": [
        "v7u_N000195",
        "v7u_N000196"
      ],
      "support_unit_ids": [
        "v7u_N000196"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000195",
          "unit_type": "definition",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000196",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH02_S06_001",
      "target_id": "cp_CH02_S06_002A",
      "relation_type": "contains",
      "reason": "CP1 defines cyber-enabled crime, and CP2A details trust-based methods used to commit it, making CP2A a sub-topic of CP1."
    },
    {
      "source_id": "cp_CH02_S06_001",
      "target_id": "cp_CH02_S06_002B",
      "relation_type": "contains",
      "reason": "CP1 defines cyber-enabled crime, and CP2B describes the outcomes and result types of such crime, making CP2B a sub-topic of CP1."
    },
    {
      "source_id": "cp_CH02_S06_001",
      "target_id": "cp_CH02_S06_004",
      "relation_type": "prepares",
      "reason": "CP1 provides the foundational definition of cyber-enabled crime, which is necessary to understand its connection to money laundering and terrorist financing in CP4."
    },
    {
      "source_id": "cp_CH02_S06_002A",
      "target_id": "cp_CH02_S06_002B",
      "relation_type": "parallels",
      "reason": "CP2A and CP2B are parallel sub-topics under CP1, covering methods and outcomes respectively, presented in textbook order."
    },
    {
      "source_id": "cp_CH02_S06_003",
      "target_id": "cp_CH02_S06_001",
      "relation_type": "illustrates",
      "reason": "CP3 provides concrete examples of cyber-enabled crime, illustrating the definition and scope in CP1."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000180|180] Cyber-enabled crime has been recognized as a multi-billion-dollar industry.
ZH: 网络犯罪已被公认为价值数十亿美元的产业。

[v7u_N000181|181] The Financial Crimes Enforcement Network (FinCEN) defines cyber-enabled crime as “Illegal activities carried out or facilitated by electronic systems and devices, such as networks and computers.”
ZH: FinCEN对网络犯罪的官方定义

[v7u_N000182|182] These illegal activities include, but are not limited to, fraud, identity theft, and other crimes.
ZH: 网络犯罪包括欺诈、身份盗窃等非法活动

[v7u_N000183|183] Cyber-enabled criminals use technology to gain access to funds, yet they must still launder their ill-gotten gains.
ZH: 网络犯罪分子仍需清洗非法所得

[v7u_N000184|184] The foundation of all cyber-enabled crime is trust. Trust is necessary to gain the confidence of the target. Some of the methods used by well-educated, technologically savvy cybercriminals include:
ZH: 网络犯罪的基础是信任，列举常用手段

[v7u_N000185|185] Social engineering
ZH: 社会工程学是网络犯罪手段之一

[v7u_N000186|186] Impersonation methods such as phishing and spoofing
ZH: 网络犯罪使用钓鱼和欺骗等冒充手段

[v7u_N000187|187] Installation of malicious software such as malware and ransomware
ZH: 网络犯罪安装恶意软件如木马和勒索软件

[v7u_N000188|188] Some of the effective methods that result in cyber-enabled crime include:
ZH: 列举网络犯罪的有效方法

[v7u_N000189|189] Disruption or destruction of networks
ZH: 网络犯罪包括破坏或摧毁网络

[v7u_N000190|190] Fraudulently obtaining funds
ZH: 网络犯罪包括欺诈获取资金

[v7u_N000191|191] Extortion for a ransom payment
ZH: 网络犯罪包括勒索赎金

[v7u_N000192|192] Committing identity theft for other nefarious purposes
ZH: 网络犯罪包括实施身份盗窃用于其他非法目的

[v7u_N000193|193] Cybercriminals can use deceptive practices, together or separately, depending upon the intended outcome of the criminal scheme. These techniques can be successful only when the cybercriminal has earned the target’s trust. Whether it is to obtain sensitive information from a target or to convince the target to click on a fraudulent link, cybercriminals must create a combination of urgency and source reliability.
ZH: 网络犯罪分子利用信任，结合紧迫性和来源可靠性实施欺骗

[v7u_N000194|194] When the intention of the criminal scheme is to spy, corrupt, or extort, the installed malicious computer programs can infect the target’s operating system.
ZH: 恶意程序在间谍、破坏或勒索意图下感染目标操作系统

[v7u_N000195|195] Examples of cyber-enabled crime are as broad as the imagination. Hacking, attempted hacking, account takeovers, compromised accounts, payment card fraud, fraudulent wire transfers, and others meet this definition.
ZH: 网络犯罪示例包括黑客攻击、账户接管、支付卡欺诈等

[v7u_N000196|196] Given how we conduct much of our lives through electronic systems or devices, it would be difficult to find a crime that was not cyber-enabled in some way.
ZH: 现代生活中难以找到完全非网络化的犯罪

[v7u_N000197|197] There is a direct relationship between cyber-enabled crime, money laundering, and terrorist financing. In fact, terrorists and money-launderers use many of the same techniques to conceal funds and payments.
ZH: 网络犯罪、洗钱与恐怖融资之间存在直接关联

[v7u_N000198|198] Cyber-enabled crime occurs rapidly, through the internet. Proceeds of this crime, or payments, also can occur rapidly, through a multitude of accounts involving many different institutions.
ZH: 网络犯罪通过互联网快速发生，资金流转迅速且涉及多个机构
```

allowed_unit_ids:

```json
[
  "v7u_N000180",
  "v7u_N000181",
  "v7u_N000182",
  "v7u_N000183",
  "v7u_N000184",
  "v7u_N000185",
  "v7u_N000186",
  "v7u_N000187",
  "v7u_N000188",
  "v7u_N000189",
  "v7u_N000190",
  "v7u_N000191",
  "v7u_N000192",
  "v7u_N000193",
  "v7u_N000194",
  "v7u_N000195",
  "v7u_N000196",
  "v7u_N000197",
  "v7u_N000198"
]
```
