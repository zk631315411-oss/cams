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
2. 候选内部存在“情境/事件/线索/输入/标准如何关联到主体动作或判断”的局部结构；只有原文明示独立结果时才增加结果节点。
3. 该方向结构能够帮助判断选项的顺序、条件、主体职责、义务、应对、因果或适用范围。
4. 基础KG只能保存整句话或各知识点，不能充分表达句内的主体、方向、条件及动作结果关系。

结构复杂度和是否闭环不是门槛。一个unit、一条路径、没有分支或反馈，或没有独立出口，都不能作为`kg_only`理由。只有对象实际到达、提交、移交或进入某阶段并触发动作时才建entry；静态适用对象、线索输入、分析材料、风险阈值、监管要求、政策基准或风险偏好应作为auxiliary standard/input并由process通过`REFERENCES`指向。

不得用“纯义务陈述”“没有复杂条件”“没有复杂步骤”拒绝提升。只要候选已经明确给出监管要求、风险偏好或状态变化如何约束特定主体的识别、标准选择或分类维持，即使没有独立出口，也满足局部有向结构要求。

以下通常应提升：

- 金融机构监控系统根据异常活动进行标记并形成识别结论。
- FIU综合SAR和跨境活动并形成红旗发现。
- 风险阈值和直接/间接持股被机构用于UBO判断并形成分类结论。
- 外部监管要求或上位标准约束机构调整控制、政策或职责；除非原文明示命令到达后触发动作，否则使用`REFERENCES`而不是`PRECEDES`。
- 明确条件触发拒绝、批准、升级、报告、监控或复核。
- 当地监管要求约束机构如何识别PEP；不得因规则只有一个unit或没有义务出口而拒绝。
- 机构基于风险偏好可以选择更高标准；必须保留可选性，即使没有独立配置出口也可以作为开放式局部关系。
- 卸任等状态变化后，特定机构仍明确维持既有分类；必须保留“部分机构”“可能”等限定。

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

新增card必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。`candidate_status`固定为`candidate`，不是最终审核状态。

`card_nature`只能为：`execution, assessment, risk_indicator, control`。

新增card可以是完整闭环，也可以是开放式局部关系；不得为了满足entry→process→exit而补造出口。

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。节点必须由原文明示，`evidence_strength`只能为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard。
- `PRODUCES`只能由process指向exit。
- `DECIDES`只能由`P3_branch_routing`发出，至少两条分支，每条都有原文明示的`condition`。
- `derivation=llm_inference`只说明边依赖必要功能推理，不改变`candidate_status`，也不表示P7D已经接受或拒绝。

静态适用对象、审查材料或判断输入不得仅因语法顺序建成`entry --PRECEDES--> process`；应建为auxiliary input并由process通过`REFERENCES`指向。不得把同一谓词的主动式和被动式拆成process与exit，也不得把“动作需要理由、批准或遵循要求”写成“动作`PRODUCES`要求/义务”。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写，不得创造新类型。

必须保留`must, should, may, might, could, often, potentially, help`等情态强度。不得将“有助于缓解”强化为“风险已经消除”。`must/shall/is required to`只证明义务存在，不证明动作已经完成；除非原文明示完成或结果已经发生，不得输出“已调整”“已建立”“已降低”等完成状态。

`must`本身不证明义务是持续、定期、永久或反复的，不得无证据增加这些限定。`escalate/escalation`默认写成“升级处理/升级处置”或保留英文，不得翻译为“上报/报告”；只有原文明示`report/notify/file/refer`及其对象时，才能写成上报、报告或移交。

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

section_id: `CH08-S05`

section_title: `Private banking and wealth management risks > Special purpose vehicle risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH08-S05_001",
      "title_zh": "SPV定义与合法用途",
      "title_en": "SPV Definition and Legitimate Uses",
      "anchor_unit_ids": [
        "v7u_N000642"
      ],
      "key_unit_ids": [
        "v7u_N000642",
        "v7u_N000643",
        "v7u_N000644",
        "v7u_N000645"
      ],
      "support_unit_ids": [
        "v7u_N000643",
        "v7u_N000644",
        "v7u_N000645"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000642",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000643",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000644",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000645",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        }
      ]
    },
    {
      "core_point_id": "cp_CH08-S05_002",
      "title_zh": "SPV金融犯罪风险与红旗信号",
      "title_en": "SPV Financial Crime Risks and Red Flags",
      "anchor_unit_ids": [
        "v7u_N000646",
        "v7u_N000647",
        "v7u_N000650",
        "v7u_N000651",
        "v7u_N000652",
        "v7u_N000653"
      ],
      "key_unit_ids": [
        "v7u_N000646",
        "v7u_N000647",
        "v7u_N000650",
        "v7u_N000651",
        "v7u_N000652"
      ],
      "support_unit_ids": [
        "v7u_N000648",
        "v7u_N000649"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000646",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000647",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000650",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000651",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000652",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000653",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000648",
          "unit_type": "fact",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000649",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH08-S05_003",
      "title_zh": "集合投资工具（PIV）定义与风险",
      "title_en": "Pooled Investment Vehicle (PIV) Definition and Risks",
      "anchor_unit_ids": [
        "v7u_N000654",
        "v7u_N000655"
      ],
      "key_unit_ids": [
        "v7u_N000654",
        "v7u_N000655"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000654",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000655",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        }
      ]
    },
    {
      "core_point_id": "cp_CH08-S05_004",
      "title_zh": "利用SPV和PIV的贸易洗钱",
      "title_en": "Trade-Based Money Laundering Using SPVs and PIVs",
      "anchor_unit_ids": [
        "v7u_N000656",
        "v7u_N000657"
      ],
      "key_unit_ids": [
        "v7u_N000656",
        "v7u_N000657"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000656",
          "unit_type": "process",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000657",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH08-S05_005",
      "title_zh": "强化尽职调查与客户尽职调查要求",
      "title_en": "Enhanced Due Diligence (EDD) and CDD Requirements",
      "anchor_unit_ids": [
        "v7u_N000658",
        "v7u_N000659"
      ],
      "key_unit_ids": [
        "v7u_N000658",
        "v7u_N000659",
        "v7u_N000660"
      ],
      "support_unit_ids": [
        "v7u_N000660"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000658",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000659",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000660",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH08-S05_001",
      "target_id": "cp_CH08-S05_002",
      "relation_type": "contrasts",
      "reason": "CP1 describes legitimate uses of SPVs, while CP2 describes their financial crime risks and red flags, creating a clear contrast between proper and illicit use."
    },
    {
      "source_id": "cp_CH08-S05_002",
      "target_id": "cp_CH08-S05_004",
      "relation_type": "prepares",
      "reason": "CP2 introduces SPV financial crime risks, and CP4 details a specific method (trade-based money laundering) using SPVs and PIVs, so CP2 provides foundational risk context for CP4."
    },
    {
      "source_id": "cp_CH08-S05_003",
      "target_id": "cp_CH08-S05_004",
      "relation_type": "prepares",
      "reason": "CP3 defines PIVs and their risks, and CP4 describes trade-based money laundering using both SPVs and PIVs, so CP3 provides necessary background on PIVs for CP4."
    },
    {
      "source_id": "cp_CH08-S05_002",
      "target_id": "cp_CH08-S05_005",
      "relation_type": "prepares",
      "reason": "CP2 outlines SPV financial crime risks, and CP5 prescribes EDD and CDD measures to mitigate those risks, so CP2 establishes the problem that CP5 addresses."
    },
    {
      "source_id": "cp_CH08-S05_003",
      "target_id": "cp_CH08-S05_005",
      "relation_type": "prepares",
      "reason": "CP3 mentions PIV risks like Ponzi schemes, and CP5 requires EDD on PIVs, so CP3 provides risk context for the due diligence measures in CP5."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000642|642] Special purpose vehicles (SPVs) are legal entities created for specific and limited purposes.
ZH: 特殊目的载体（SPV）是为特定有限目的设立的法律实体

[v7u_N000643|643] SPVs can be used in mergers and acquisitions, joint ventures, real estate projects, infrastructure development, and energy projects.
ZH: SPV可用于并购、合资、房地产、基础设施和能源项目

[v7u_N000644|644] SPVs can also be used to manage and protect intellectual property assets including trademarks and copyrights.
ZH: SPV可用于管理和保护知识产权资产

[v7u_N000645|645] SPVs are often used in complex financial transactions and investments such as securities and asset-backed financing.
ZH: SPV常用于复杂金融交易和资产支持融资

[v7u_N000646|646] There are financial crime risks associated with SPVs.
ZH: SPV存在金融犯罪风险

[v7u_N000647|647] SPVs can have complex and opaque structures to disguise the true beneficial ownership.
ZH: SPV可能通过复杂不透明的结构掩盖真实受益所有人

[v7u_N000648|648] SPVs might be used to obscure the source of illicit funds. Criminals layer illicit proceeds through a series of transactions via the SPVs, transferring funds to or from financial institutions. This creates a complex web of
ZH: 犯罪分子通过SPV进行一系列交易来分层非法收益，掩盖资金来源

[v7u_N000649|649] There are several red flags that indicate attempts to disguise illicit funds or conduct fraudulent activities using SPVs. These include:
ZH: 列举利用SPV掩饰非法资金或欺诈活动的红旗信号信号

[v7u_N000650|650] Complex ownership structures involving multiple layers of companies
ZH: 涉及多层公司的复杂所有权结构是红旗信号

[v7u_N000651|651] Lack of transparency
ZH: 缺乏透明度是红旗信号

[v7u_N000652|652] Unclear purpose of the SPV
ZH: SPV目的不明确是红旗信号

[v7u_N000653|653] Criminals might select jurisdictions that have lenient regulatory oversight or tax-friendly environments. This enables them to hide their financial activities and minimize tax liabilities.
ZH: 犯罪分子选择监管宽松或税收优惠的司法管辖区以隐藏活动和避税

[v7u_N000654|654] Pooled investment vehicles (PIVs) are small investments pooled together from a large group of investors.
ZH: 集合投资工具（PIV）是从大量投资者汇集的小额投资

[v7u_N000655|655] PIVs can be used in Ponzi schemes and insider trading.
ZH: PIV可能被用于庞氏骗局和内幕交易

[v7u_N000656|656] Additionally, criminals might engage in trade-based money laundering using SPVs and PIVs. Criminals manipulate trade transactions between SPVs and PIVs by deflating or inflating prices.
ZH: 犯罪分子利用SPV和PIV进行贸易洗钱，操纵交易价格

[v7u_N000657|657] This process enables the movement of illicit funds while disguising it as legitimate trade activity.
ZH: 该过程将非法资金伪装成合法贸易活动进行转移

[v7u_N000658|658] Financial institutions must be vigilant in conducting enhanced due diligence (EDD) on SPVs and PIVs. It is important to ensure these investments comply with CDD regulations such as the Financial Crime Enforcement Network's CDD rule.
ZH: 金融机构必须对SPV和PIV进行强化尽职调查，遵守客户尽职调查规则

[v7u_N000659|659] Financial institutions must identify ultimate beneficial owners and understand the true purpose of these entities.
ZH: 金融机构必须识别最终受益所有人并了解实体真实目的

[v7u_N000660|660] This will help mitigate any potential financial crime risks associated with SPVs.
ZH: 这有助于减轻与SPV相关的金融犯罪风险
```

allowed_unit_ids:

```json
[
  "v7u_N000642",
  "v7u_N000643",
  "v7u_N000644",
  "v7u_N000645",
  "v7u_N000646",
  "v7u_N000647",
  "v7u_N000648",
  "v7u_N000649",
  "v7u_N000650",
  "v7u_N000651",
  "v7u_N000652",
  "v7u_N000653",
  "v7u_N000654",
  "v7u_N000655",
  "v7u_N000656",
  "v7u_N000657",
  "v7u_N000658",
  "v7u_N000659",
  "v7u_N000660"
]
```

original_json:

```json
{
  "section_id": "CH08-S05",
  "section_title": "Private banking and wealth management risks > Special purpose vehicle risks",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N000642",
        "v7u_N000643",
        "v7u_N000644",
        "v7u_N000645"
      ],
      "proposition": "SPV的定义和合法用途，包括并购、合资、房地产、知识产权管理等。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG已能表达SPV定义与合法用途，属于纯事实列举和定义，无增量程序性或判断性结构。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000646",
        "v7u_N000647",
        "v7u_N000648",
        "v7u_N000649",
        "v7u_N000650",
        "v7u_N000651",
        "v7u_N000652",
        "v7u_N000653"
      ],
      "proposition": "SPV金融犯罪风险与红旗信号：SPV可能通过复杂结构掩饰受益所有权，犯罪分子利用SPV分层非法资金，选择宽松辖区；红旗包括复杂所有权结构、缺乏透明度、目的不明确。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG已能表达SPV金融犯罪风险、洗钱手法、红旗信号及管辖选择，均为一般风险描述和孤立指标，无机构应对的有向判断结构。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000654",
        "v7u_N000655"
      ],
      "proposition": "PIV的定义和风险：集合投资工具从小投资者汇集资金，可能被用于庞氏骗局和内幕交易。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG已能表达PIV定义和相关欺诈风险，属于孤立事实和风险指标，无程序性有向结构。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000656",
        "v7u_N000657"
      ],
      "proposition": "犯罪分子利用SPV和PIV进行贸易洗钱，通过操纵价格将非法资金伪装成合法贸易活动。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "描述犯罪分子的具体作案方法，属于普通案例机制，基础KG核心点004已覆盖，无机构应对或有向判断链。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000658",
        "v7u_N000659",
        "v7u_N000660"
      ],
      "proposition": "金融机构必须对SPV和PIV执行强化尽职调查（EDD），识别最终受益所有人并了解真实目的，这有助于减轻潜在金融犯罪风险。",
      "decision": "p7c_card",
      "card_id": "p7card_CH08-S05_001",
      "reason": "基础KG核心点005仅概括EDD和CDD要求，未表达“识别UBO与了解真实目的”的具体执行动作和“有助于减轻风险”的有向传导关系，属于增量程序性结构。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH08-S05_001",
      "section_id": "CH08-S05",
      "card_nature": "execution",
      "title": "金融机构对SPV和PIV的强化尽职调查程序",
      "flow_nodes": [
        {
          "node_id": "N001",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "金融机构：对特殊目的载体和集合投资工具执行强化尽职调查，识别最终受益所有人并了解真实目的",
          "evidence_unit_ids": [
            "v7u_N000658",
            "v7u_N000659"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N002",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "特殊目的载体和集合投资工具（潜在交易/投资）",
          "evidence_unit_ids": [
            "v7u_N000658"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N003",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "客户尽职调查规则（如FinCEN CDD规则）",
          "evidence_unit_ids": [
            "v7u_N000658"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N004",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "潜在金融犯罪风险可能得到减轻",
          "evidence_unit_ids": [
            "v7u_N000660"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E001",
          "edge_type": "REFERENCES",
          "source": "N001",
          "target": "N002",
          "evidence_unit_ids": [
            "v7u_N000658"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "E002",
          "edge_type": "REFERENCES",
          "source": "N001",
          "target": "N003",
          "evidence_unit_ids": [
            "v7u_N000658"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        },
        {
          "edge_id": "E003",
          "edge_type": "PRODUCES",
          "source": "N001",
          "target": "N004",
          "evidence_unit_ids": [
            "v7u_N000660"
          ],
          "derivation": "explicit_text",
          "source_quote": "This will help mitigate any potential financial crime risks"
        }
      ],
      "source_unit_ids": [
        "v7u_N000658",
        "v7u_N000659",
        "v7u_N000660"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：金融机构在涉及特殊目的载体和集合投资工具的业务中，必须执行强化尽职调查并识别最终受益所有人及真实目的，进而有助于减轻潜在金融犯罪风险。KG不足：基础KG核心点005仅概括了'EDD和CDD要求'这一规则，但未表达'识别UBO与了解真实目的'作为具体执行动作，以及该动作与'帮助减轻风险'之间的有向传导关系。选项判断：可据此确认或排除关于SPV/PIV的EDD义务主体、具体动作内容以及风险减轻效果的强度（'有助于'而非必然消除）。LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```
