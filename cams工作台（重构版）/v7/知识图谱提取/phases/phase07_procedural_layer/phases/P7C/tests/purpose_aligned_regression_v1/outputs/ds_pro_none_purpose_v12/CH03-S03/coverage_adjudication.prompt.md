# P7C Section-Local Coverage Adjudication Prompt v1

## 角色

你是P7C覆盖裁决器。首次抽取器已经发现候选命题并生成通过结构校验的card；你的唯一任务是复核`coverage_audit`中原决定为`kg_only`的候选，判断它们是否因KG/P7C边界理解错误而漏成卡。

只输出完整严格JSON，不输出Markdown或解释。`flow_nodes + flow_edges`仍是知识正本；`coverage_adjudication`和`coverage_audit`只是诊断元数据。

## P7C目的

P7C在不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标和一般知识关系的前提下，从单个section中增量提取对CAMS题目选项判断有用的局部程序性或判断性有向结构：业务情境、事件、线索、输入或标准，如何关联到特定主体的识别、评估、决策或应对，并在相应条件下产生结论、义务、控制结果、分支或后续行动。

P7C不读取题目或参考答案，不处理跨section桥接。当前section原文是唯一事实证据；基础KG摘要只能用于去重，不能补造事实。

## 裁决对象

只复核`original_json.coverage_audit`中`decision=kg_only`的候选。不得新增候选，不得删除候选，不得修改候选的`candidate_id`、`unit_ids`或`proposition`。

原本为`p7c_card`的候选及其`card_id`必须保持不变。`original_json.cards`中的每张既有card必须完整保留，不得删除、改写、拆分、合并或重新编号。

## 裁决标准

将原`kg_only`候选提升为`p7c_card`，必须同时满足：

1. 当前section证据支持关系两端、特定主体、方向以及条件（如有）。
2. 候选内部存在“情境/事件/线索/输入/标准 → 主体动作或判断 → 结果/义务/控制效果”的局部结构。
3. 该方向结构能够帮助判断选项的顺序、条件、主体职责、义务、应对、因果或适用范围。
4. 基础KG只能保存整句话或各知识点，不能充分表达句内的主体、方向、条件及动作结果关系。

结构复杂度不是门槛。一个unit、一条路径、没有分支或反馈，都不能作为`kg_only`理由。entry是图中的关系起点，不要求是时间事件；业务对象、线索输入、风险阈值、监管要求或政策基准都可以承担有证据的入口角色。

以下通常应提升：

- 金融机构监控系统根据异常活动进行标记并形成识别结论。
- FIU综合SAR和跨境活动并形成红旗发现。
- 风险阈值和直接/间接持股被机构用于UBO判断并形成分类结论。
- 外部监管要求或上位标准触发机构调整控制、政策或职责。
- 明确条件触发拒绝、批准、升级、报告、监控、复核或持续义务。

以下保持`kg_only`：

- 纯定义、分类、阈值数值或组成列表，没有主体应用和结果关系。
- 普通犯罪方法、犯罪分子操作步骤或普通案例机制，没有机构、FIU、监管或执法主体的识别、判断或应对。
- 孤立红旗、后果、历史事实或抽象风险缓解目的。
- 只有主题相关性，或者必须补造主体、条件、方向、动作或结果才能闭合。

## 修改规则

对每个原`kg_only`候选，在顶层`coverage_adjudication`中新增一条记录：

```json
{
  "candidate_id": "cand_001",
  "original_decision": "kg_only",
  "final_decision": "kg_only",
  "reason": "<中文裁决理由>"
}
```

`final_decision`只能为`kg_only`或`p7c_card`。

保持`kg_only`时：原`coverage_audit`记录的`decision`仍为`kg_only`，`card_id`仍为`null`，可以更新中文`reason`。

提升为`p7c_card`时：

- 将原`coverage_audit`记录的`decision`改为`p7c_card`；
- 填入新增card的`card_id`；
- 更新中文`reason`，说明基础KG不能表达的方向结构；
- 在`cards`末尾追加一张有证据的局部card；
- 不得修改其他候选或已有card。

## 新增card规则

新增card必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, review_status, review_notes`。

`card_nature`只能为：`execution, assessment, risk_indicator, control`。

每张新增card至少包含一个entry、process和exit，并存在entry经过process到exit的有向路径。

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。节点必须由原文明示，`evidence_strength`只能为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, evidence_strength`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard。
- `PRODUCES`只能由process指向exit。
- `DECIDES`只能由`P3_branch_routing`发出，至少两条分支，每条都有原文明示的`condition`。
- `functional_dependency`只允许用于边，且card必须为`needs_review`并在`review_notes`的“LLM推理”中说明。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写，不得创造新类型。

必须保留`must, should, may, might, could, often, potentially, help`等情态强度。不得将“有助于缓解”强化为“风险已经消除”。

新增card只能引用对应候选`unit_ids`及同一局部命题必要的当前section unit。不得借裁决轮扩展到无关主题。

## 输出约束

返回完整顶层对象：

```text
section_id
section_title
coverage_adjudication
coverage_audit
cards
skip_reason
```

如果最终存在card，`skip_reason`必须为`null`。如果仍无card，保留合适的中文`skip_reason`。

## 当前section

section_id: `CH03-S03`

section_title: `Examples of predicate crimes > Drug trafficking`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH03_S03_001",
      "title_zh": "毒品贩卖定义与结构",
      "title_en": "Drug Trafficking Definition and Structure",
      "anchor_unit_ids": [
        "v7u_N000229",
        "v7u_N000230"
      ],
      "key_unit_ids": [
        "v7u_N000229",
        "v7u_N000230",
        "v7u_N000232",
        "v7u_N000231"
      ],
      "support_unit_ids": [
        "v7u_N000231",
        "v7u_N000232"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000229",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000230",
          "unit_type": "case",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000232",
          "unit_type": "fact",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000231",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH03_S03_002",
      "title_zh": "毒品贩卖中的洗钱阶段与方法",
      "title_en": "Money Laundering Stages and Methods in Drug Trafficking",
      "anchor_unit_ids": [
        "v7u_N000233",
        "v7u_N000234",
        "v7u_N000237",
        "v7u_N000241",
        "v7u_N000243"
      ],
      "key_unit_ids": [
        "v7u_N000233",
        "v7u_N000234",
        "v7u_N000237",
        "v7u_N000241",
        "v7u_N000243"
      ],
      "support_unit_ids": [
        "v7u_N000235",
        "v7u_N000236",
        "v7u_N000238",
        "v7u_N000239",
        "v7u_N000240",
        "v7u_N000242"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000233",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000234",
          "unit_type": "fact",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000237",
          "unit_type": "case",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000241",
          "unit_type": "process",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000243",
          "unit_type": "case",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000235",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000236",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000238",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000239",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000240",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000242",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH03_S03_001",
      "target_id": "cp_CH03_S03_002",
      "relation_type": "prepares",
      "reason": "CP1 defines drug trafficking and its structure, providing the foundational predicate crime context for CP2's detailed explanation of money laundering stages and methods within that crime."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000229|229] Drug trafficking involves the illegal production, distribution, and sale of controlled substances.
ZH: 毒品贩运涉及受控物质的非法生产、分销和销售。

[v7u_N000230|230] Commonly trafficked drugs include heroin, cocaine, cannabis, and synthetic drugs such as fentanyl and methamphetamine.
ZH: 常见贩毒品种包括海洛因、可卡因、大麻及芬太尼等合成毒品。

[v7u_N000231|231] The legal status of some of these drugs complicates enforcement and regulation efforts. For example, both fentanyl and cannabis have legal medicinal uses, and recreational cannabis use is permitted in certain jurisdictions, but illegal in others.
ZH: 部分毒品的法律地位复杂化执法工作，如大麻和芬太尼的合法医疗用途。

[v7u_N000232|232] Drug trafficking operates as a highly structured network, analogous to a multinational corporation, and can involve an extensive global supply chain.
ZH: 毒品贩运运作类似跨国公司，涉及广泛的全球供应链。

[v7u_N000233|233] Money laundering can occur during the sourcing, manufacturing, or distribution stages.
ZH: 洗钱可发生在毒品贩运的采购、制造或分销阶段。

[v7u_N000234|234] Criminal organizations utilize various methods to launder money at the sourcing stage when the raw material is obtained and refined.
ZH: 犯罪组织在采购阶段利用多种方法清洗资金。

[v7u_N000235|235] Payments for chemical precursors and logistics are often made on the basis of fraudulent trade invoices and routed through offshore shell companies, cryptocurrency mixing services, and hawala networks.
ZH: 化学前体和物流付款常通过虚假贸易发票、离岸壳公司、加密货币混合服务和哈瓦拉网络进行。

[v7u_N000236|236] This allows traffickers to obscure the origins of their funds from the beginning of the supply chain.
ZH: 贩毒者从供应链起点即掩盖资金来源。

[v7u_N000237|237] At the manufacturing stage, proceeds are funneled through agribusiness, real estate acquisitions, shell logistics firms, and TBML.
ZH: 制造阶段通过农业、房地产、壳物流公司和贸易洗钱转移收益。

[v7u_N000238|238] These methods help traffickers integrate illicit funds into the economy.
ZH: 这些方法帮助贩毒者将非法资金融入经济。

[v7u_N000239|239] According to FinCEN, criminal organizations also utilize the international trade system to launder proceeds from drug trafficking.
ZH: FinCEN指出犯罪组织利用国际贸易体系清洗毒品贩运收益。

[v7u_N000240|240] Colombian drug traffickers, for instance, have historically used the Colombian Black Market Peso Exchange (BMPE) to convert US dollars into Colombian pesos. This system allows traffickers to settle drug debts or purchase future shipments while obscuring the origins of their funds.
ZH: 哥伦比亚黑市比索兑换是贸易洗钱的典型案例。

[v7u_N000241|241] Once drugs are sold and distributed, traffickers launder the consolidated cash through shell companies to appear legitimate, integrating illicit funds into the financial system.
ZH: 贩毒者通过壳公司清洗毒品现金，将非法资金融入金融体系

[v7u_N000242|242] This process highlights the legal implications of drug trafficking as a predicate offense for money laundering, as the proceeds are considered "dirty money" that need to be concealed to avoid detection by law enforcement.
ZH: 毒品贩运作为洗钱的上游犯罪，其收益被视为需要隐藏的脏钱

[v7u_N000243|243] Integration methods include real estate acquisitions in global cities, luxury asset purchases such as art, gold, yachts, and rare diamonds, and crypto-laundering through exchanges and non-fungible token platforms.
ZH: 毒品资金的融合阶段方式包括全球城市房地产收购、奢侈品购买及加密货币洗钱
```

allowed_unit_ids:

```json
[
  "v7u_N000229",
  "v7u_N000230",
  "v7u_N000231",
  "v7u_N000232",
  "v7u_N000233",
  "v7u_N000234",
  "v7u_N000235",
  "v7u_N000236",
  "v7u_N000237",
  "v7u_N000238",
  "v7u_N000239",
  "v7u_N000240",
  "v7u_N000241",
  "v7u_N000242",
  "v7u_N000243"
]
```

original_json:

```json
{
  "section_id": "CH03-S03",
  "section_title": "Examples of predicate crimes > Drug trafficking",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N000229",
        "v7u_N000230"
      ],
      "proposition": "毒品贩运的定义和常见毒品列表",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义和事实列举，基础KG可充分表达，无程序性或判断性有向结构。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000231"
      ],
      "proposition": "部分毒品的法律地位（如合法医疗用途）导致执法和监管工作复杂化",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅说明复杂性状态，无特定主体行动、决策链或明确结果，属于一般事实说明，基础KG可表达。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000232"
      ],
      "proposition": "毒品贩运作为高度结构化的网络，运作类似跨国公司，涉及全球供应链",
      "decision": "kg_only",
      "card_id": null,
      "reason": "描述犯罪组织一般特征，非针对机构识别/评估/应对的结构，基础KG可保存。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000233"
      ],
      "proposition": "洗钱可发生在毒品贩运的采购、制造或分销阶段",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般事实陈述，无特定条件、主体动作或结果，基础KG可表达。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000234",
        "v7u_N000235",
        "v7u_N000236"
      ],
      "proposition": "在采购阶段，犯罪组织利用虚假贸易发票、壳公司、加密货币混合服务和哈瓦拉网络等方法掩盖资金来源",
      "decision": "kg_only",
      "card_id": null,
      "reason": "描述犯罪手法和普通案例机制，未涉及机构识别、判断或应对程序，基础KG可保存。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000237",
        "v7u_N000238"
      ],
      "proposition": "在制造阶段，收益通过农业、房地产、壳物流公司和贸易洗钱转移，以融入非法资金进入经济",
      "decision": "kg_only",
      "card_id": null,
      "reason": "犯罪方法列举与目的说明，无机构层面的有向处置结构，属于基础KG范畴。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000239",
        "v7u_N000240"
      ],
      "proposition": "FinCEN指出犯罪组织利用国际贸易体系洗钱，如哥伦比亚BMPE案例，用于结算债务或购买货物并掩盖来源",
      "decision": "kg_only",
      "card_id": null,
      "reason": "引用和案例方法描述，未涉及当局或机构的识别、行动或结果链，基础KG可承接。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N000241"
      ],
      "proposition": "分销后，贩毒者通过壳公司清洗现金以融入金融体系",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般洗钱阶段描述，无具体条件、主体判断或应对，基础KG可表达。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N000242"
      ],
      "proposition": "毒品贩运作为洗钱上游犯罪，其收益为需隐藏的“脏钱”，凸显法律含义",
      "decision": "kg_only",
      "card_id": null,
      "reason": "法律含义说明，无程序性或判断性结构，基础KG可保存。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N000243"
      ],
      "proposition": "毒品资金融合阶段的方法包括全球城市房地产收购、奢侈品购买及加密洗钱",
      "decision": "kg_only",
      "card_id": null,
      "reason": "犯罪方法列举，无机构应对或决策链，基础KG可承接。"
    }
  ],
  "cards": [],
  "skip_reason": "当前section仅包含毒品贩运与洗钱的定义、一般事实、犯罪方法及案例描述，均为基础KG可充分表达的内容，未发现证据支持的增量程序性或判断性有向结构（如条件触发特定主体的识别、评估、决策或应对并产生明确结论/义务/控制结果）。"
}
```
