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

section_id: `CH02-S01`

section_title: `Types of financial crime > Predicate crimes and money laundering`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH02_S01_001",
      "title_zh": "上游犯罪及FATF分类",
      "title_en": "Predicate Crimes and FATF Categories",
      "anchor_unit_ids": [
        "v7u_N000060",
        "v7u_N000062",
        "v7u_N000066",
        "v7u_N000067",
        "v7u_N000068",
        "v7u_N000069",
        "v7u_N000070",
        "v7u_N000071",
        "v7u_N000072",
        "v7u_N000073",
        "v7u_N000074",
        "v7u_N000075",
        "v7u_N000076",
        "v7u_N000077",
        "v7u_N000078",
        "v7u_N000079",
        "v7u_N000080",
        "v7u_N000081",
        "v7u_N000082",
        "v7u_N000083",
        "v7u_N000084",
        "v7u_N000085",
        "v7u_N000086",
        "v7u_N000087"
      ],
      "key_unit_ids": [
        "v7u_N000060",
        "v7u_N000062",
        "v7u_N000066",
        "v7u_N000067",
        "v7u_N000068"
      ],
      "support_unit_ids": [
        "v7u_N000061",
        "v7u_N000063",
        "v7u_N000064",
        "v7u_N000065"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000060",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000062",
          "unit_type": "fact",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000066",
          "unit_type": "classification",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000067",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000068",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000069",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000070",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000071",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000072",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000073",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000074",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000075",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000076",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000077",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000078",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000079",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000080",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000081",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000082",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000083",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000084",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000085",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000086",
          "unit_type": "definition",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000087",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000061",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000063",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000064",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000065",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S01_002",
      "title_zh": "制裁规避手段与处罚",
      "title_en": "Sanctions Evasion Methods and Penalties",
      "anchor_unit_ids": [
        "v7u_N000089",
        "v7u_N000091",
        "v7u_N000092",
        "v7u_N000093",
        "v7u_N000096",
        "v7u_N000098",
        "v7u_N000099",
        "v7u_N000100",
        "v7u_N000101",
        "v7u_N000102"
      ],
      "key_unit_ids": [
        "v7u_N000089",
        "v7u_N000091",
        "v7u_N000092",
        "v7u_N000093",
        "v7u_N000096"
      ],
      "support_unit_ids": [
        "v7u_N000088",
        "v7u_N000090",
        "v7u_N000094",
        "v7u_N000095",
        "v7u_N000097"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000089",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000091",
          "unit_type": "classification",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000092",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000093",
          "unit_type": "definition",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000096",
          "unit_type": "definition",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000098",
          "unit_type": "definition",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000099",
          "unit_type": "classification",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000100",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000101",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000102",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000088",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000090",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000094",
          "unit_type": "process",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000095",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000097",
          "unit_type": "classification",
          "cp_unit_role": "describes_process"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S01_003",
      "title_zh": "案例研究：Alexei Komarov的制裁规避计划",
      "title_en": "Case Study: Alexei Komarov's Sanctions Evasion Scheme",
      "anchor_unit_ids": [
        "v7u_N000103",
        "v7u_N000104",
        "v7u_N000105",
        "v7u_N000106",
        "v7u_N000107",
        "v7u_N000108",
        "v7u_N000109",
        "v7u_N000110",
        "v7u_N000111"
      ],
      "key_unit_ids": [
        "v7u_N000103",
        "v7u_N000104",
        "v7u_N000105",
        "v7u_N000106",
        "v7u_N000107"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000103",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000104",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000105",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000106",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000107",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000108",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000109",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000110",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000111",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH02_S01_003",
      "target_id": "cp_CH02_S01_002",
      "relation_type": "illustrates",
      "reason": "CP3 is a detailed case study that concretely illustrates the sanctions evasion methods and penalties described in CP2."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000060|60] Predicate crimes are specified unlawful activities whose proceeds can give rise to prosecution for money laundering.
ZH: 上游犯罪是指其收益可导致洗钱起诉的特定非法活动

[v7u_N000061|61] Individuals or organizations who engage in predicate crimes often want to "clean," or launder the proceeds from these crimes so they can use them legitimately without drawing attention from law enforcement.
ZH: 实施上游犯罪的个人或组织清洗犯罪收益以合法使用

[v7u_N000062|62] FATF has identified 21 categories of predicate offenses that financial institutions must acknowledge and monitor under AML compliance programs.
ZH: FATF 确定了金融机构必须关注的 21 类上游犯罪

[v7u_N000063|63] However, different jurisdictions might classify these offenses differently.
ZH: 不同司法管辖区对上游犯罪的分类存在差异

[v7u_N000064|64] For example, while some countries have strong laws against human trafficking, others do not recognize certain forms of exploitation as criminal offenses.
ZH: 举例：各国对人口贩卖的法律认定不同导致分类差异

[v7u_N000065|65] This variation can complicate AML efforts, with compliance professionals operating in cross-border contexts needing to align risk controls with the laws and regulations of more than one jurisdiction.
ZH: 跨境反洗钱合规需协调多个司法管辖区的法律差异

[v7u_N000066|66] The list of 21 FATF-designated predicate crimes includes:
ZH: FATF 指定的 21 类上游犯罪清单引述

[v7u_N000067|67] 1. Participation in an organized criminal group and racketeering: Engaging in systemic financial crimes
ZH: 参与有组织犯罪集团和敲诈勒索属于上游犯罪

[v7u_N000068|68] 2. Terrorism, including terrorist financing: Providing financial support to these operations
ZH: 恐怖主义及恐怖融资属于上游犯罪

[v7u_N000069|69] 3. Trafficking in human beings and migrant smuggling: Generating illicit profits through human exploitation
ZH: 人口贩卖和偷运移民属于上游犯罪

[v7u_N000070|70] 4. Sexual exploitation, including that of children: Crimes linked to forced prostitution and human trafficking
ZH: 性剥削（包括儿童性剥削）属于上游犯罪

[v7u_N000071|71] 5. Illicit trafficking in narcotic drugs and psychotropic substances: Production, transportation, and sale of illegal substances
ZH: 非法贩运麻醉药品和精神药物属于上游犯罪

[v7u_N000072|72] 6. Illicit arms trafficking: Illegal trade and smuggling of firearms and explosives
ZH: 非法武器贩运属于上游犯罪

[v7u_N000073|73] 7. Illicit trafficking of stolen and other goods: Black market trade of stolen and counterfeit items
ZH: 非法贩运被盗物品及其他货物属于上游犯罪

[v7u_N000074|74] 8. Corruption and bribery: Abuse of power in public or private sectors for financial gain
ZH: 腐败和贿赂属于上游犯罪

[v7u_N000075|75] 9. Fraud: Financial deception, scams, and identity theft schemes
ZH: 欺诈属于上游犯罪

[v7u_N000076|76] 10. Counterfeiting currency: Illegal manufacturing of banknotes
ZH: 伪造货币属于上游犯罪

[v7u_N000077|77] 11. Counterfeiting and piracy of products: Violations of intellectual property, including counterfeit goods
ZH: 假冒和盗版产品属于上游犯罪

[v7u_N000078|78] 12. Environmental crime: Logging, poaching, and waste disposal
ZH: 环境犯罪属于上游犯罪

[v7u_N000079|79] 13. Murder and grievous bodily injury: Violent crimes motivated by financial gain
ZH: 谋杀和严重身体伤害属于上游犯罪

[v7u_N000080|80] 14. Kidnapping, illegal restraint, and hostage-taking: Crimes involving ransom demands
ZH: 绑架、非法拘禁和劫持人质属于上游犯罪

[v7u_N000081|81] 15. Robbery or theft: Large-scale property crimes driven by financial motives
ZH: 抢劫或盗窃：出于财务动机的大规模财产犯罪

[v7u_N000082|82] 16. Smuggling (including in relation to customs and excise duties and taxes): Illegal movement of goods to evade duties
ZH: 走私（包括关税和消费税相关）：为逃避关税而非法移动货物

[v7u_N000083|83] 17. Tax crimes (related to direct and indirect taxes): Tax fraud and false reporting schemes
ZH: 税收犯罪（直接税和间接税）：税务欺诈和虚假申报计划

[v7u_N000084|84] 18. Extortion: Coercing for financial gain through threats or intimidation
ZH: 敲诈勒索：通过威胁或恐吓强迫获取经济利益

[v7u_N000085|85] 19. Forgery: Falsifying documents, financial records, or identities
ZH: 伪造：伪造文件、财务记录或身份信息

[v7u_N000086|86] 20.Piracy: Maritime or cyber-based hijacking for financial gain
ZH: 海盗行为：为获取经济利益而进行的海上或网络劫持

[v7u_N000087|87] 21. Insider trading and market manipulation: Illegal use of nonpublic information to achieve profits
ZH: 内幕交易和市场操纵：利用非公开信息非法获利

[v7u_N000088|88] Economic sanctions, whether asset freezes or sector-specific restrictions, impose high financial, reputational, and operational costs on individuals and entities targeted by them.
ZH: 制裁对目标个人和实体施加高额财务、声誉和运营成本

[v7u_N000089|89] For this reason, sanctions targets often attempt to evade or circumvent sanctions in order to secretly engage in a prohibited activity, such as continuing to use an asset or receive economic benefits.
ZH: 制裁目标常试图规避制裁以秘密从事被禁止的活动

[v7u_N000090|90] For example, a designated individual might evade personal sanctions and continue using his luxury yacht by obscuring its ownership.
ZH: 示例：被制裁个人通过隐藏豪华游艇所有权规避个人制裁

[v7u_N000091|91] Sanctions evasion can be internal, with the help of personnel at an organization, or external, when evaders try to bypass internal controls without assistance from the inside.
ZH: 制裁规避可分为内部规避（借助内部人员）和外部规避

[v7u_N000092|92] Methods of sanctions evasion include payments, trade, and ownership.
ZH: 制裁规避方法包括支付、贸易和所有权相关手段

[v7u_N000093|93] Payment-related evasion occurs when, for example, Bank A attempts to have Bank B process prohibited transactions, with or without help from Bank B insiders.
ZH: 支付相关规避：银行A试图让银行B处理被禁止交易

[v7u_N000094|94] Identifying information is removed, or stripped, from payment instructions to avoid detection.
ZH: 从支付指令中移除识别信息以逃避检测

[v7u_N000095|95] Nested and payable accounts are particularly vulnerable to this evasion typology.
ZH: 嵌套账户和应付账户特别容易受到支付信息剥离的规避手法影响

[v7u_N000096|96] Trade-related evasion involves illegally importing or exporting goods without proper licensing or despite trade bans.
ZH: 贸易相关规避：未经适当许可或违反贸易禁令非法进出口货物

[v7u_N000097|97] Common techniques include the use of shell companies, switching cargo on the open sea (also known as transshipment), and using neutral or opaque jurisdictions for transit.
ZH: 贸易规避常见手法：使用壳公司、公海换货（转运）、利用中立或保密司法管辖区

[v7u_N000098|98] Ownership-related evasion involves obscuring the ownership of an asset by a designated person. This can be achieved by using complex corporate structures, proxies, and bearer shares and by diluting ownership.
ZH: 所有权相关规避：通过复杂公司结构、代理人、不记名股票和稀释所有权隐藏资产所有权

[v7u_N000099|99] Regulated entities must have strong AML and sanctions compliance programs with robust policies, procedures, and internal controls for detecting and preventing sanctions evasion. The penalties for noncompliance and failing to prevent sanctions evasion could include:
ZH: 受监管实体必须建立强大的反洗钱和制裁合规计划，违规处罚包括：

[v7u_N000100|100] Civil monetary penalties against organizations
ZH: 对组织的民事罚款

[v7u_N000101|101] Civil and criminal prosecution of individuals
ZH: 个人可能面临洗钱相关民事和刑事起诉

[v7u_N000102|102] Designations as a sanctions target
ZH: 个人可能被列为制裁目标

[v7u_N000103|103] Businessman Alexei Komarov amassed his fortune through Volkof Industries, a high-tech distribution company with clients worldwide. Though some of his customers were from a wide range of industries (from consumer electronics and automotive to healthcare and industrial manufacturing), most sales went to a foreign government engaged in nuclear weapons development. After UN sanctions targeted this proliferation activity, Volkof Industries faced restrictions, losing its access to global markets.
ZH: Alexei Komarov通过Volkof Industries从事扩散融资的案例

[v7u_N000104|104] Facing financial collapse, Komarov was determined to find a way to continue trading.
ZH: Komarov面临财务崩溃，决心继续交易

[v7u_N000105|105] To evade the sanctions, he created a shell company, RedStar Solutions.
ZH: Komarov创建壳公司RedStar Solutions以规避制裁

[v7u_N000106|106] He incorporated it in a jurisdiction with limited regulatory expectations toward AML and sanctions compliance and masked it as a technical support and maintenance service provider.
ZH: 在监管宽松的司法管辖区注册壳公司并伪装成技术服务商

[v7u_N000107|107] Through RedStar, he resumed exports to the foreign government developing its nuclear weapons program, using transshipment points in permissive jurisdictions and falsified invoices that labeled export-controlled items, such as semiconductors, as “industrial machinery and spare parts.”
ZH: 通过转运点和伪造发票恢复出口受控物品

[v7u_N000108|108] RedStar also employed local distributors in those jurisdictions to further distance Komarov and Volkof Industries from the transactions and paid them to ensure the shipments were received without question.
ZH: 利用当地分销商进一步掩盖交易关联

[v7u_N000109|109] To launder the proceeds back to Volkof Industries, Komarov routed payments through offshore accounts and shell companies. He was thus able to credit Volkof Industries’ accounts using laundered funds from the illegal activities of RedStar.
ZH: 通过离岸账户和壳公司清洗非法收益的示例

[v7u_N000110|110] Komarov’s goal was not just to hide the profits of RedStar, but to keep Volkof Industries trading, as its name still carried weight in industry circles. Despite UN sanctions against Volkof Industries, this strategy helped the company meet loan obligations, retain employees, and strengthen business ties to the foreign government, its main client.
ZH: Komarov的双重目标：隐藏利润并维持Volkof Industries运营

[v7u_N000111|111] The scheme unraveled when a bank’s compliance officer flagged irregular payment flows linked to RedStar. Further investigation exposed the illicit network, revealing Komarov and Volkof Industries’ role in sanctions evasion, proliferation financing, laundering criminal proceeds, and foreign bribery and corruption offences.
ZH: 合规官发现异常支付，揭露制裁规避、扩散融资、洗钱等犯罪
```

allowed_unit_ids:

```json
[
  "v7u_N000060",
  "v7u_N000061",
  "v7u_N000062",
  "v7u_N000063",
  "v7u_N000064",
  "v7u_N000065",
  "v7u_N000066",
  "v7u_N000067",
  "v7u_N000068",
  "v7u_N000069",
  "v7u_N000070",
  "v7u_N000071",
  "v7u_N000072",
  "v7u_N000073",
  "v7u_N000074",
  "v7u_N000075",
  "v7u_N000076",
  "v7u_N000077",
  "v7u_N000078",
  "v7u_N000079",
  "v7u_N000080",
  "v7u_N000081",
  "v7u_N000082",
  "v7u_N000083",
  "v7u_N000084",
  "v7u_N000085",
  "v7u_N000086",
  "v7u_N000087",
  "v7u_N000088",
  "v7u_N000089",
  "v7u_N000090",
  "v7u_N000091",
  "v7u_N000092",
  "v7u_N000093",
  "v7u_N000094",
  "v7u_N000095",
  "v7u_N000096",
  "v7u_N000097",
  "v7u_N000098",
  "v7u_N000099",
  "v7u_N000100",
  "v7u_N000101",
  "v7u_N000102",
  "v7u_N000103",
  "v7u_N000104",
  "v7u_N000105",
  "v7u_N000106",
  "v7u_N000107",
  "v7u_N000108",
  "v7u_N000109",
  "v7u_N000110",
  "v7u_N000111"
]
```
