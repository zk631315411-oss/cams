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

section_id: `CH02-S05`

section_title: `Types of financial crime > Key takeaways`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH02_S05_001",
      "title_zh": "贿赂风险与反贿赂控制措施",
      "title_en": "Bribery risks and anti-bribery controls",
      "anchor_unit_ids": [
        "v7u_N000145",
        "v7u_N000149"
      ],
      "key_unit_ids": [
        "v7u_N000145",
        "v7u_N000149",
        "v7u_N000146",
        "v7u_N000150",
        "v7u_N000151"
      ],
      "support_unit_ids": [
        "v7u_N000146",
        "v7u_N000147",
        "v7u_N000148",
        "v7u_N000150",
        "v7u_N000151"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000145",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000149",
          "unit_type": "fact",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000146",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000150",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000151",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000147",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000148",
          "unit_type": "context",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S05_002",
      "title_zh": "避税与逃税",
      "title_en": "Tax avoidance and tax evasion",
      "anchor_unit_ids": [
        "v7u_N000152",
        "v7u_N000154"
      ],
      "key_unit_ids": [
        "v7u_N000152",
        "v7u_N000154",
        "v7u_N000156",
        "v7u_N000155",
        "v7u_N000153"
      ],
      "support_unit_ids": [
        "v7u_N000153",
        "v7u_N000155",
        "v7u_N000156"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000152",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000154",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000156",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000155",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000153",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S05_003",
      "title_zh": "激进避税",
      "title_en": "Aggressive tax avoidance",
      "anchor_unit_ids": [
        "v7u_N000157"
      ],
      "key_unit_ids": [
        "v7u_N000157",
        "v7u_N000158"
      ],
      "support_unit_ids": [
        "v7u_N000158"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000157",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000158",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S05_004",
      "title_zh": "金融犯罪防控专业人员验证避税参数的角色",
      "title_en": "AFC professionals’ role in verifying tax avoidance parameters",
      "anchor_unit_ids": [
        "v7u_N000159"
      ],
      "key_unit_ids": [
        "v7u_N000159"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000159",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S05_005",
      "title_zh": "逃税作为洗钱的上游犯罪",
      "title_en": "Tax evasion as a money laundering predicate offense",
      "anchor_unit_ids": [
        "v7u_N000160"
      ],
      "key_unit_ids": [
        "v7u_N000160",
        "v7u_N000161"
      ],
      "support_unit_ids": [
        "v7u_N000161"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000160",
          "unit_type": "fact",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000161",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S05_006",
      "title_zh": "监控客户活动以发现逃税指标",
      "title_en": "Client activity monitoring for tax evasion indicators",
      "anchor_unit_ids": [
        "v7u_N000162",
        "v7u_N000163"
      ],
      "key_unit_ids": [
        "v7u_N000162",
        "v7u_N000163"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000162",
          "unit_type": "rule",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000163",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S05_007",
      "title_zh": "共同申报准则（CRS）",
      "title_en": "Common Reporting Standard (CRS)",
      "anchor_unit_ids": [
        "v7u_N000164"
      ],
      "key_unit_ids": [
        "v7u_N000164"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000164",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S05_008",
      "title_zh": "欺诈定义与一般特征",
      "title_en": "Fraud definition and general characteristics",
      "anchor_unit_ids": [
        "v7u_N000165"
      ],
      "key_unit_ids": [
        "v7u_N000165",
        "v7u_N000166",
        "v7u_N000167"
      ],
      "support_unit_ids": [
        "v7u_N000166",
        "v7u_N000167"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000165",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000166",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000167",
          "unit_type": "context",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S05_009",
      "title_zh": "欺诈三角：压力、机会、合理化",
      "title_en": "Fraud Triangle: pressure, opportunity, rationalization",
      "anchor_unit_ids": [
        "v7u_N000168"
      ],
      "key_unit_ids": [
        "v7u_N000168",
        "v7u_N000169",
        "v7u_N000170",
        "v7u_N000171"
      ],
      "support_unit_ids": [
        "v7u_N000169",
        "v7u_N000170",
        "v7u_N000171"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000168",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000169",
          "unit_type": "definition",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000170",
          "unit_type": "definition",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000171",
          "unit_type": "definition",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH02_S05_010",
      "title_zh": "常见欺诈红旗信号",
      "title_en": "Common fraud red flags",
      "anchor_unit_ids": [
        "v7u_N000173"
      ],
      "key_unit_ids": [
        "v7u_N000173",
        "v7u_N000174",
        "v7u_N000175",
        "v7u_N000176",
        "v7u_N000177"
      ],
      "support_unit_ids": [
        "v7u_N000172",
        "v7u_N000174",
        "v7u_N000175",
        "v7u_N000176",
        "v7u_N000177",
        "v7u_N000178",
        "v7u_N000179"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000173",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000174",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000175",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000176",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000177",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000172",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000178",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000179",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH02_S05_002",
      "target_id": "cp_CH02_S05_003",
      "relation_type": "contains",
      "reason": "CP2 covers tax avoidance and tax evasion broadly, and CP3 details aggressive tax avoidance as a specific subtype of tax avoidance."
    },
    {
      "source_id": "cp_CH02_S05_002",
      "target_id": "cp_CH02_S05_005",
      "relation_type": "prepares",
      "reason": "CP2 defines tax evasion, and CP5 explains its role as a predicate offense for money laundering, building on that definition."
    },
    {
      "source_id": "cp_CH02_S05_005",
      "target_id": "cp_CH02_S05_006",
      "relation_type": "prepares",
      "reason": "CP5 establishes tax evasion as a predicate offense, and CP6 describes monitoring for its indicators, a logical next step."
    },
    {
      "source_id": "cp_CH02_S05_008",
      "target_id": "cp_CH02_S05_009",
      "relation_type": "contains",
      "reason": "CP8 defines fraud and its general characteristics, and CP9 explains the Fraud Triangle, a key model for understanding fraud motivations."
    },
    {
      "source_id": "cp_CH02_S05_008",
      "target_id": "cp_CH02_S05_010",
      "relation_type": "contains",
      "reason": "CP8 introduces fraud, and CP10 lists common red flags, which are indicators of fraud."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000145|145] Multinationals using intermediaries in high-risk areas face increased bribery risks.
ZH: 在高风险地区使用中介的跨国公司面临更高的贿赂风险

[v7u_N000146|146] Corporate bribery often involves third parties, shell companies, and false invoicing.
ZH: 企业贿赂常涉及第三方、壳公司和虚假发票

[v7u_N000147|147] Illicit funds are frequently laundered to conceal their origin.
ZH: 非法资金常被洗钱以掩盖其来源

[v7u_N000148|148] Financial institutions should:
ZH: 金融机构应采取以下措施

[v7u_N000149|149] Conduct audits to identify control deficiencies.
ZH: 进行审计以识别控制缺陷

[v7u_N000150|150] Enhance transaction monitoring for suspicious activities, especially regarding “consultancy fees” to individuals or intermediaries located in high-risk jurisdictions.
ZH: 加强对高风险地区咨询费的可疑交易监控

[v7u_N000151|151] Include anti-bribery clauses for customers engaging in intermediary models.
ZH: 对采用中介模式的客户加入反贿赂条款

[v7u_N000152|152] Tax avoidance, or tax planning, is not illegal. It is the activity of legitimately reducing the amount of tax owed to government by legal or natural persons.
ZH: 避税是合法减少税负的行为

[v7u_N000153|153] Some jurisdictions encourage tax avoidance by allowing pre-tax savings.
ZH: 一些司法管辖区通过允许税前储蓄来鼓励避税

[v7u_N000154|154] Tax evasion is the use of illegal practices to avoid paying a tax liability.
ZH: 逃税是使用非法手段逃避纳税义务

[v7u_N000155|155] This could include not declaring taxable income or hiding taxable assets from the authorities.
ZH: 逃税示例：不申报应税收入或隐藏应税资产

[v7u_N000156|156] Tax evasion is illegal and those caught are generally subject to criminal charges and substantial penalties.
ZH: 逃税违法，将面临刑事指控和重大处罚

[v7u_N000157|157] While tax avoidance is legal and causes financial services firms no concerns, aggressive tax avoidance is defined as the aggressive legal interpretation of the law without adequately considering its intent or spirit.
ZH: 激进避税是激进地解释法律而不考虑其意图或精神

[v7u_N000158|158] An example of aggressive tax avoidance is a multinational company requiring its subsidiaries to pay a royalty fee for the use of its intellectual property. This reduces the profitability of the overseas unit and therefore reduces the tax they pay in that jurisdiction.
ZH: 激进避税示例：跨国公司要求子公司支付知识产权使用费以减少利润和税款

[v7u_N000159|159] AFC professionals should be satisfied that a customer’s activities across an account fall within avoidance parameters.
ZH: 金融犯罪防控专业人员应确保客户活动在避税参数范围内

[v7u_N000160|160] Tax evasion is illegal and is considered a predicate offense for money laundering.
ZH: 逃税是洗钱的上游犯罪

[v7u_N000161|161] A predicate offense is a component part of a more serious crime.
ZH: 上游犯罪是更严重犯罪的组成部分。

[v7u_N000162|162] Information gathered at onboarding and during transaction monitoring should inform the activity the organization should expect across the customer’s account.
ZH: 开户和交易监控数据应告知机构对客户账户的预期活动。

[v7u_N000163|163] Unusual activity such as excessive personal expense claims across a small business account might be a warning signal that a customer is evading tax.
ZH: 小企业账户中过度的个人费用报销可能是逃税的警告信号。

[v7u_N000164|164] The Common Reporting Standard (CRS), developed in response to the G-20 countries' request and approved by the OECD (Organization for Economic Cooperation and Development) Council, calls on jurisdictions to obtain information from their financial institutions and automatically exchange that information with other jurisdictions on an annual basis. It sets out the financial account information to be exchanged, the financial institutions required to report, the different types of accounts and taxpayers covered, as well as common due diligence procedures to be followed by financial institutions. Its purpose is to combat tax evasion.
ZH: 共同申报准则（CRS）要求司法管辖区每年自动交换金融账户信息以打击逃税。

[v7u_N000165|165] Fraud is an intentional act of criminal deception in order to obtain an unjust or illegal advantage. Typically, fraud results in financial or personal gain. Notice that fraud is intentional and uses deception to achieve the goal.
ZH: 欺诈是为获取不正当利益而故意进行的欺骗行为。

[v7u_N000166|166] Fraud can be committed by one or more individuals—from low-level employees, to management, to government officials. It can be found in every country and every type of business.
ZH: 欺诈可由个人或多人实施，存在于各国和各行业。

[v7u_N000167|167] Knowing the common features of fraud, as well as typical motivations and red flags, will help you combat this crime.
ZH: 了解欺诈的常见特征、动机和红旗信号信号有助于打击此类犯罪。

[v7u_N000168|168] People commit fraud for three major reasons: pressure, opportunity, and rationalization. This three-sided model is referred to as the “Fraud Triangle.”
ZH: 欺诈三角模型指出欺诈的三个主要原因：压力、机会和合理化。

[v7u_N000169|169] Pressure is sometimes called "incentive." It can be a financial problem that drives a person to commit fraud, such as gambling or other debt. This can create the pressure to commit fraud.
ZH: 压力（或诱因）是驱动个人实施欺诈的财务问题，如赌博债务。

[v7u_N000170|170] Opportunity is often provided by a lack of effective internal controls within an institution. For example, confidential documents are left unattended in the office.
ZH: 机会通常由机构内部缺乏有效的内部控制提供。

[v7u_N000171|171] Rationalization is when the fraudster convinces herself that what she is doing does not really matter or that the fraud is justified.
ZH: 合理化是欺诈者说服自己行为无关紧要或正当的过程。

[v7u_N000172|172] There are many different types of fraud, or schemes, each of which has its own unique red flags. Common red flags of fraud include:
ZH: 欺诈有多种类型，每种都有独特的红旗信号信号，常见红旗信号包括：

[v7u_N000173|173] Something sounds too good to be true
ZH: 听起来好得令人难以置信。

[v7u_N000174|174] A promise of high returns for low investment
ZH: 承诺低投资高回报。

[v7u_N000175|175] Demand for upfront payments
ZH: 要求预先付款。

[v7u_N000176|176] Deliberate creation of an artificial shortage of opportunities
ZH: 故意制造人为的机会稀缺。

[v7u_N000177|177] Element of secrecy
ZH: 保密元素。

[v7u_N000178|178] Sense of urgency
ZH: 紧迫感。

[v7u_N000179|179] Pressure to act...right now!
ZH: 立即行动的压力。
```

allowed_unit_ids:

```json
[
  "v7u_N000145",
  "v7u_N000146",
  "v7u_N000147",
  "v7u_N000148",
  "v7u_N000149",
  "v7u_N000150",
  "v7u_N000151",
  "v7u_N000152",
  "v7u_N000153",
  "v7u_N000154",
  "v7u_N000155",
  "v7u_N000156",
  "v7u_N000157",
  "v7u_N000158",
  "v7u_N000159",
  "v7u_N000160",
  "v7u_N000161",
  "v7u_N000162",
  "v7u_N000163",
  "v7u_N000164",
  "v7u_N000165",
  "v7u_N000166",
  "v7u_N000167",
  "v7u_N000168",
  "v7u_N000169",
  "v7u_N000170",
  "v7u_N000171",
  "v7u_N000172",
  "v7u_N000173",
  "v7u_N000174",
  "v7u_N000175",
  "v7u_N000176",
  "v7u_N000177",
  "v7u_N000178",
  "v7u_N000179"
]
```
