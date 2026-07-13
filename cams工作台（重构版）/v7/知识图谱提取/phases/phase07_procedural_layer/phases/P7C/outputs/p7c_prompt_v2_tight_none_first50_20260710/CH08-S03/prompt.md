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

section_id: `CH08-S03`

section_title: `Private banking and wealth management risks > Trust risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH08_S03_001",
      "title_zh": "信托的定义和基本特征",
      "title_en": "Definition and basic characteristics of trusts",
      "anchor_unit_ids": [
        "v7u_N000602"
      ],
      "key_unit_ids": [
        "v7u_N000602",
        "v7u_N000603",
        "v7u_N000604",
        "v7u_N000605"
      ],
      "support_unit_ids": [
        "v7u_N000603",
        "v7u_N000604",
        "v7u_N000605"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000602",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000603",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000604",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000605",
          "unit_type": "rule",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH08_S03_002",
      "title_zh": "信托的合法用途",
      "title_en": "Legitimate uses of trusts",
      "anchor_unit_ids": [
        "v7u_N000606"
      ],
      "key_unit_ids": [
        "v7u_N000606",
        "v7u_N000607",
        "v7u_N000608"
      ],
      "support_unit_ids": [
        "v7u_N000607",
        "v7u_N000608"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000606",
          "unit_type": "fact",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000607",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000608",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        }
      ]
    },
    {
      "core_point_id": "cp_CH08_S03_003",
      "title_zh": "信托当事人：委托人、受托人、受益人",
      "title_en": "Parties to a trust: settlor, trustee, beneficiary",
      "anchor_unit_ids": [
        "v7u_N000609"
      ],
      "key_unit_ids": [
        "v7u_N000609",
        "v7u_N000610",
        "v7u_N000611"
      ],
      "support_unit_ids": [
        "v7u_N000610",
        "v7u_N000611"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000609",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000610",
          "unit_type": "definition",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000611",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH08_S03_004",
      "title_zh": "研究信托：关键人物和文件",
      "title_en": "Researching a trust: key parties and documentation",
      "anchor_unit_ids": [
        "v7u_N000613"
      ],
      "key_unit_ids": [
        "v7u_N000613",
        "v7u_N000612"
      ],
      "support_unit_ids": [
        "v7u_N000612"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000613",
          "unit_type": "fact",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000612",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH08_S03_005",
      "title_zh": "信托被滥用于隐瞒的风险",
      "title_en": "Risks and misuse of trusts for concealment",
      "anchor_unit_ids": [
        "v7u_N000614",
        "v7u_N000615",
        "v7u_N000616",
        "v7u_N000617",
        "v7u_N000618"
      ],
      "key_unit_ids": [
        "v7u_N000614",
        "v7u_N000615",
        "v7u_N000616",
        "v7u_N000617",
        "v7u_N000618"
      ],
      "support_unit_ids": [
        "v7u_N000619",
        "v7u_N000620",
        "v7u_N000621"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000614",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000615",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000616",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000617",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000618",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000619",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000620",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000621",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH08_S03_001",
      "target_id": "cp_CH08_S03_003",
      "relation_type": "contains",
      "reason": "CP1 defines trusts and their basic characteristics, while CP3 details the specific parties (settlor, trustee, beneficiary) which are key components of a trust."
    },
    {
      "source_id": "cp_CH08_S03_001",
      "target_id": "cp_CH08_S03_002",
      "relation_type": "prepares",
      "reason": "CP1 provides the foundational definition of trusts, which is necessary background for understanding their legitimate uses in CP2."
    },
    {
      "source_id": "cp_CH08_S03_001",
      "target_id": "cp_CH08_S03_005",
      "relation_type": "prepares",
      "reason": "CP1 establishes the basic trust structure, which is then contrasted with its misuse for concealment in CP5."
    },
    {
      "source_id": "cp_CH08_S03_003",
      "target_id": "cp_CH08_S03_004",
      "relation_type": "prepares",
      "reason": "CP3 identifies the key parties to a trust, which are the essential elements to research as outlined in CP4."
    },
    {
      "source_id": "cp_CH08_S03_002",
      "target_id": "cp_CH08_S03_005",
      "relation_type": "contrasts",
      "reason": "CP2 describes legitimate uses of trusts, while CP5 discusses their misuse for concealment, creating a clear contrast."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000602|602] Trusts are legal arrangements that separate the legal title and control of an asset.
ZH: 信托是分离资产法定所有权与控制权的法律安排

[v7u_N000603|603] In most jurisdictions a trust is a legal person.
ZH: 在大多数司法管辖区，信托被视为法人

[v7u_N000604|604] The assets in a trust are legally owned by trustees who are natural persons.
ZH: 信托资产由作为自然人的受托人合法所有

[v7u_N000605|605] A trust cannot conduct transactions or hold property, but must do so through those trustees.
ZH: 信托不能直接进行交易或持有财产，必须通过受托人进行

[v7u_N000606|606] Trusts have many legitimate uses, including succession and estate planning, and wealth and confidentiality protection. Trusts can also speed up probate.
ZH: 信托的合法用途包括继承与遗产规划、财富与保密保护以及加速遗嘱认证

[v7u_N000607|607] Offshore trusts are sometimes used for legal tax avoidance in tax havens.
ZH: 离岸信托有时用于在避税天堂进行合法避税

[v7u_N000608|608] Charitable trusts and foundations often have sizable assets used to promote good causes.
ZH: 慈善信托和基金会通常拥有大量资产用于促进公益事业

[v7u_N000609|609] The entity that establishes the trust is called the settlor, donor, grantor, trustor, or trust maker.
ZH: 设立信托的实体称为委托人、捐赠人、授予人、信托人或信托设立人

[v7u_N000610|610] The settlor’s role is to legally transfer control of an asset to the trustees, who manage the trust for one or more beneficiaries.
ZH: 委托人的角色是将资产控制权合法转移给受托人，由受托人为受益人管理信托

[v7u_N000611|611] In certain trusts, the settlor may also be the trustee, the beneficiary, or even both.
ZH: 在某些信托中，委托人也可以同时是受托人或受益人，甚至两者兼是

[v7u_N000612|612] Trusts are often created with guidance from a corporate service provider.
ZH: 信托通常在公司服务提供商的指导下设立

[v7u_N000613|613] In researching a trust, you need to know the settlor, the trustees, the beneficiaries, and any individual who has control over the trust. Typically, the settlor transfers a legal title clearly documented either by a trust instrument or a trust deed.
ZH: 研究信托时需要了解委托人、受托人、受益人及任何控制信托的个人，通常有信托文书或信托契据

[v7u_N000614|614] However, in many jurisdictions, there is no registration requirement for a trust. They are viewed as private arrangements and their existence is not a matter of public record.
ZH: 许多司法管辖区不要求信托注册，信托被视为私人安排，不公开记录

[v7u_N000615|615] FATF has expressed a particular concern about the ease with which corporate vehicles can be created and dissolved in some jurisdictions.
ZH: FATF特别关注某些司法管辖区公司载体易于创建和解散的问题

[v7u_N000616|616] Those seeking to disguise their connection with financial crime appreciate the separation of legal and beneficial ownership which gives an aura of legitimacy.
ZH: 犯罪分子利用信托中法定所有权与受益所有人的分离来掩盖与金融犯罪的关联

[v7u_N000617|617] But trusts can have the same or connected persons as both settlor and trustee, meaning the trustee will simply follow the directions of the settlor. Even when the trustees are advised by a seemingly independent investment management company, those, too, might be influenced by the settlor.
ZH: 当委托人与受托人身份关联时，受托人可能仅遵循委托人指示，即使有独立投资管理公司也可能受委托人影响

[v7u_N000618|618] Trusts are often the last layer of secrecy in a complex legal structure designed to disguise a criminal’s connection to illicit funds. In order to aid this concealment, arrangements often span multiple jurisdictions, with trust assets and investment management companies each located in a different country.
ZH: 信托常作为复杂法律结构中的最后保密层，通过跨多个司法管辖区来掩盖犯罪资金关联

[v7u_N000619|619] An example would be a high-ranking member of government who is paid a bribe to award a large road construction contract to a construction company.
ZH: 示例：政府高官收受贿赂，将大型道路建设合同授予某建筑公司

[v7u_N000620|620] He cannot receive this directly without raising suspicion.
ZH: 该官员不能直接收受贿赂而不引起怀疑

[v7u_N000621|621] So, the construction company pays an advisory fee to a company set up in another jurisdiction. Ownership of the advisory company has been settled into a trust, the beneficiaries of which are the government official and his family.
ZH: 通过咨询费与信托结构隐匿政府官员受益所有权
```

allowed_unit_ids:

```json
[
  "v7u_N000602",
  "v7u_N000603",
  "v7u_N000604",
  "v7u_N000605",
  "v7u_N000606",
  "v7u_N000607",
  "v7u_N000608",
  "v7u_N000609",
  "v7u_N000610",
  "v7u_N000611",
  "v7u_N000612",
  "v7u_N000613",
  "v7u_N000614",
  "v7u_N000615",
  "v7u_N000616",
  "v7u_N000617",
  "v7u_N000618",
  "v7u_N000619",
  "v7u_N000620",
  "v7u_N000621"
]
```
