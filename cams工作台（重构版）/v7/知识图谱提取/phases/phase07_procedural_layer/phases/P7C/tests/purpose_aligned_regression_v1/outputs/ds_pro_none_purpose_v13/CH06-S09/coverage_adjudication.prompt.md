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

section_id: `CH06-S09`

section_title: `Money Laundering Risks in Financial Services > Politically exposed person risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH06_S09_001",
      "title_zh": "政治敏感人物的定义、范围和关联人",
      "title_en": "PEP definition, scope, and related persons",
      "anchor_unit_ids": [
        "v7u_N000457",
        "v7u_N000469",
        "v7u_N000470",
        "v7u_N000473",
        "v7u_N000474",
        "v7u_N000475"
      ],
      "key_unit_ids": [
        "v7u_N000457",
        "v7u_N000469",
        "v7u_N000470",
        "v7u_N000473",
        "v7u_N000474"
      ],
      "support_unit_ids": [
        "v7u_N000467",
        "v7u_N000468",
        "v7u_N000471",
        "v7u_N000472"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000457",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000469",
          "unit_type": "fact",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000470",
          "unit_type": "fact",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000473",
          "unit_type": "fact",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000474",
          "unit_type": "fact",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000475",
          "unit_type": "fact",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000467",
          "unit_type": "rule",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000468",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000471",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000472",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH06_S09_002",
      "title_zh": "政治敏感人物识别挑战与合规要求",
      "title_en": "PEP Identification Challenges and Compliance",
      "anchor_unit_ids": [
        "v7u_N000458",
        "v7u_N000459",
        "v7u_N000460"
      ],
      "key_unit_ids": [
        "v7u_N000458",
        "v7u_N000459",
        "v7u_N000460"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000458",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000459",
          "unit_type": "rule",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000460",
          "unit_type": "rule",
          "cp_unit_role": "explains"
        }
      ]
    },
    {
      "core_point_id": "cp_CH06_S09_003",
      "title_zh": "FATF对政治敏感人物的分类",
      "title_en": "FATF Classification of PEP Types",
      "anchor_unit_ids": [
        "v7u_N000462",
        "v7u_N000463",
        "v7u_N000464"
      ],
      "key_unit_ids": [
        "v7u_N000462",
        "v7u_N000463",
        "v7u_N000464",
        "v7u_N000461"
      ],
      "support_unit_ids": [
        "v7u_N000461"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000462",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000463",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000464",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000461",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH06_S09_004",
      "title_zh": "政治敏感人物的腐败风险与示例",
      "title_en": "PEP Vulnerability to Corruption and Examples",
      "anchor_unit_ids": [
        "v7u_N000465"
      ],
      "key_unit_ids": [
        "v7u_N000465",
        "v7u_N000466"
      ],
      "support_unit_ids": [
        "v7u_N000466"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000465",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000466",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        }
      ]
    },
    {
      "core_point_id": "cp_CH06_S09_005",
      "title_zh": "政治敏感人物风险管理与监控方法",
      "title_en": "PEP Risk Management and Monitoring Approaches",
      "anchor_unit_ids": [
        "v7u_N000476",
        "v7u_N000477",
        "v7u_N000481",
        "v7u_N000482"
      ],
      "key_unit_ids": [
        "v7u_N000476",
        "v7u_N000477",
        "v7u_N000481",
        "v7u_N000482",
        "v7u_N000479"
      ],
      "support_unit_ids": [
        "v7u_N000478",
        "v7u_N000479",
        "v7u_N000480"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000476",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000477",
          "unit_type": "rule",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000481",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000482",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000479",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000478",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000480",
          "unit_type": "rule",
          "cp_unit_role": "explains"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH06_S09_001",
      "target_id": "cp_CH06_S09_003",
      "relation_type": "prepares",
      "reason": "CP1 defines PEP and its scope, providing the foundational definition needed to understand the FATF classification in CP3."
    },
    {
      "source_id": "cp_CH06_S09_001",
      "target_id": "cp_CH06_S09_004",
      "relation_type": "prepares",
      "reason": "CP1 defines PEP, which is necessary to understand the vulnerability to corruption discussed in CP4."
    },
    {
      "source_id": "cp_CH06_S09_001",
      "target_id": "cp_CH06_S09_005",
      "relation_type": "prepares",
      "reason": "CP1 defines PEP, which is the prerequisite for the risk management and monitoring approaches in CP5."
    },
    {
      "source_id": "cp_CH06_S09_002",
      "target_id": "cp_CH06_S09_005",
      "relation_type": "prepares",
      "reason": "CP2 discusses identification challenges and compliance requirements, which set the stage for the risk management approaches in CP5."
    },
    {
      "source_id": "cp_CH06_S09_003",
      "target_id": "cp_CH06_S09_004",
      "relation_type": "prepares",
      "reason": "CP3 classifies PEP types, which helps understand the specific vulnerabilities to corruption discussed in CP4."
    },
    {
      "source_id": "cp_CH06_S09_004",
      "target_id": "cp_CH06_S09_005",
      "relation_type": "prepares",
      "reason": "CP4 explains PEP vulnerability to corruption, which is the risk that CP5's management and monitoring approaches aim to address."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000457|457] A politically exposed person (PEP) is an individual in a prominent political function, their immediate family, close associates, and any businesses held or controlled by that person.
ZH: 政治敏感人物（政治敏感人物）的定义：担任重要公职的个人及其亲属和密切关联人

[v7u_N000458|458] One challenge in identifying PEPs is the varying guidance and recommendations in each jurisdiction.
ZH: 识别政治敏感人物的挑战在于各司法管辖区指引不同

[v7u_N000459|459] Organizations must adhere to their local regulatory requirements in identifying PEPs.
ZH: 机构必须遵守当地监管要求识别政治敏感人物

[v7u_N000460|460] However, organizations may choose to enforce higher standards based on their risk appetite.
ZH: 机构可根据风险偏好执行更高的政治敏感人物标准

[v7u_N000461|461] According to the Financial Action Task Force (FATF), there are three types of PEPs:
ZH: FATF将政治敏感人物分为三类

[v7u_N000462|462] Foreign PEPs are individuals entrusted with prominent public functions by a foreign country.
ZH: 外国政治敏感人物指受外国委托担任重要公共职能的个人

[v7u_N000463|463] Domestic PEPs are individuals entrusted domestically with prominent public functions.
ZH: 国内政治敏感人物指在国内担任重要公共职能的个人

[v7u_N000464|464] International organization PEPs are individuals from an international organization entrusted with a prominent function such as secretary general, executive director, or president.
ZH: 国际组织政治敏感人物指在国际组织中担任秘书长、执行董事或主席等要职的个人

[v7u_N000465|465] Individuals in high positions and their associates are more vulnerable to corruption.
ZH: 高层职位个人及其关联人更易受腐败影响

[v7u_N000466|466] Corruption might be favors where the PEP directs government contracts to an organization in return for kickbacks. In addition, a PEP might influence legislation for bribes or flee the country with government funds.
ZH: 政治敏感人物腐败示例：以政府合同换取回扣、影响立法收受贿赂或携政府资金潜逃

[v7u_N000467|467] Use a broad definition for defining a PEP.
ZH: 应采用宽泛定义来界定政治敏感人物

[v7u_N000468|468] PEPs can generally be defined as:
ZH: 政治敏感人物的一般定义

[v7u_N000469|469] A person in a prominent decision-making or influential role
ZH: 政治敏感人物指担任重要决策或有影响力角色的人

[v7u_N000470|470] A person within royal, military, legislative, judicial, executive, or similar government positions
ZH: 政治敏感人物包括王室、军事、立法、司法、行政或类似政府职位的人

[v7u_N000471|471] PEPs will often use nominees or businesses they are associated with.
ZH: 政治敏感人物常使用名义人或关联企业

[v7u_N000472|472] Therefore, the definition of PEP can also include:
ZH: 政治敏感人物定义还可包括以下人员

[v7u_N000473|473] Immediate family
ZH: 政治敏感人物的直系亲属

[v7u_N000474|474] Close friends or associates
ZH: 政治敏感人物的密友或关联人

[v7u_N000475|475] Businesses owned or held by those individuals
ZH: 政治敏感人物拥有或持有的企业

[v7u_N000476|476] Under a risk-based approach, PEP risk is manageable.
ZH: 基于风险的方法下，政治敏感人物风险是可控的

[v7u_N000477|477] Some organizations follow a “once a PEP, always a PEP” approach because the individual may remain in the same circles of influence, even if they have stepped down.
ZH: 部分机构采用“一旦是政治敏感人物，永远是政治敏感人物”的方法

[v7u_N000478|478] Other organizations will look at:
ZH: 其他机构会考察以下因素

[v7u_N000479|479] The individual’s influence at the time, such as their ability to award contracts or allocate funds
ZH: 考察个人当时的影响力，如授予合同或分配资金的能力

[v7u_N000480|480] How long the individual has been classified as a PEP
ZH: 考察个人被归类为政治敏感人物的时间长短

[v7u_N000481|481] The purpose of the PEP designation is important.
ZH: 政治敏感人物 认定的目的具有重要意义

[v7u_N000482|482] Organizations must take the necessary steps to adapt transaction monitoring and KYC reviews and escalate based on their risk appetite.
ZH: 机构必须根据风险偏好调整交易监控和 了解你的客户 审查
```

allowed_unit_ids:

```json
[
  "v7u_N000457",
  "v7u_N000458",
  "v7u_N000459",
  "v7u_N000460",
  "v7u_N000461",
  "v7u_N000462",
  "v7u_N000463",
  "v7u_N000464",
  "v7u_N000465",
  "v7u_N000466",
  "v7u_N000467",
  "v7u_N000468",
  "v7u_N000469",
  "v7u_N000470",
  "v7u_N000471",
  "v7u_N000472",
  "v7u_N000473",
  "v7u_N000474",
  "v7u_N000475",
  "v7u_N000476",
  "v7u_N000477",
  "v7u_N000478",
  "v7u_N000479",
  "v7u_N000480",
  "v7u_N000481",
  "v7u_N000482"
]
```

original_json:

```json
{
  "section_id": "CH06-S09",
  "section_title": "Money Laundering Risks in Financial Services > Politically exposed person risks",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N000459"
      ],
      "proposition": "机构必须遵守当地监管要求识别PEP，从而承担持续识别义务",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S09_001",
      "reason": "监管要求触发特定主体行动并产生义务的有向链，超出基础KG的规则文本保存"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000460"
      ],
      "proposition": "机构可以根据风险偏好执行更高的PEP标准，从而标准提高",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S09_002",
      "reason": "风险偏好作为条件导向可选的标准提升，形成条件-动作-配置变化的有向结构"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000467"
      ],
      "proposition": "应使用宽泛定义界定PEP",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅为规则建议，缺乏明确主体动作与具体出口，基础KG可将其作为事实保存"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000477"
      ],
      "proposition": "部分机构采用永久PEP方法，将卸任但仍可能保持影响力的人持续归类为PEP",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S09_003",
      "reason": "卸任状态触发特定机构的分类决策和持久归类，形成有向判断链，超出基础KG对该方法的静态描述"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000478",
        "v7u_N000479",
        "v7u_N000480"
      ],
      "proposition": "其他机构基于个人当前影响力和PEP时长等因素评估PEP状态",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅列出评估因素，未明确产生何种决定或出口，属于孤立评估维度，基础KG可保存"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000482"
      ],
      "proposition": "机构必须根据风险偏好调整交易监控和KYC审查并上报，从而配置变化并承担上报义务",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S09_004",
      "reason": "风险偏好约束强制调整动作，产生具体配置变化与义务的有向链"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH06-S09_001",
      "section_id": "CH06-S09",
      "card_nature": "execution",
      "title": "机构必须遵守当地监管要求识别PEP",
      "flow_nodes": [
        {
          "node_id": "p7card_CH06-S09_001_n01",
          "node_category": "entry",
          "node_type": "E7_external_command",
          "label": "当地监管要求识别PEP",
          "evidence_unit_ids": [
            "v7u_N000459"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH06-S09_001_n02",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构遵守要求识别PEP",
          "evidence_unit_ids": [
            "v7u_N000459"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH06-S09_001_n03",
          "node_category": "exit",
          "node_type": "X7_continuing_obligation",
          "label": "机构承担持续识别PEP的义务",
          "evidence_unit_ids": [
            "v7u_N000459"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7card_CH06-S09_001_e01",
          "edge_type": "PRECEDES",
          "source": "p7card_CH06-S09_001_n01",
          "target": "p7card_CH06-S09_001_n02",
          "evidence_unit_ids": [
            "v7u_N000459"
          ],
          "evidence_strength": "explicit"
        },
        {
          "edge_id": "p7card_CH06-S09_001_e02",
          "edge_type": "PRODUCES",
          "source": "p7card_CH06-S09_001_n02",
          "target": "p7card_CH06-S09_001_n03",
          "evidence_unit_ids": [
            "v7u_N000459"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "source_unit_ids": [
        "v7u_N000459"
      ],
      "review_status": "accepted",
      "review_notes": "增量命题：当地监管要求→机构识别PEP→持续识别义务；KG不足：基础KG仅保存规则文本，未表达主体、动作与结果的有向关系；选项判断：可确认机构识别PEP的义务来源；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S09_002",
      "section_id": "CH06-S09",
      "card_nature": "execution",
      "title": "机构可根据风险偏好执行更高PEP标准",
      "flow_nodes": [
        {
          "node_id": "p7card_CH06-S09_002_n01",
          "node_category": "entry",
          "node_type": "E3_state_threshold",
          "label": "机构的风险偏好",
          "evidence_unit_ids": [
            "v7u_N000460"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH06-S09_002_n02",
          "node_category": "process",
          "node_type": "P8_constrained_action",
          "label": "机构可能选择执行更高PEP标准",
          "evidence_unit_ids": [
            "v7u_N000460"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH06-S09_002_n03",
          "node_category": "exit",
          "node_type": "X5_config_change",
          "label": "PEP标准提高",
          "evidence_unit_ids": [
            "v7u_N000460"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7card_CH06-S09_002_e01",
          "edge_type": "PRECEDES",
          "source": "p7card_CH06-S09_002_n01",
          "target": "p7card_CH06-S09_002_n02",
          "evidence_unit_ids": [
            "v7u_N000460"
          ],
          "evidence_strength": "explicit",
          "condition": "based on risk appetite"
        },
        {
          "edge_id": "p7card_CH06-S09_002_e02",
          "edge_type": "PRODUCES",
          "source": "p7card_CH06-S09_002_n02",
          "target": "p7card_CH06-S09_002_n03",
          "evidence_unit_ids": [
            "v7u_N000460"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "source_unit_ids": [
        "v7u_N000460"
      ],
      "review_status": "accepted",
      "review_notes": "增量命题：风险偏好→可选执行更高标准→标准提高；KG不足：基础KG保存事实，但未表达条件-动作-配置变化的有向链；选项判断：可确认基于风险偏好提高标准的可选性；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S09_003",
      "section_id": "CH06-S09",
      "card_nature": "assessment",
      "title": "部分机构采用永久PEP方法处理卸任个人",
      "flow_nodes": [
        {
          "node_id": "p7card_CH06-S09_003_n01",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "个人从公职卸任，但仍可能保持影响力",
          "evidence_unit_ids": [
            "v7u_N000477"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH06-S09_003_n02",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "机构遵循“一旦是PEP，永远是PEP”方法，将个人持续视为PEP",
          "evidence_unit_ids": [
            "v7u_N000477"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH06-S09_003_n03",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "个人被永久归类为PEP",
          "evidence_unit_ids": [
            "v7u_N000477"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7card_CH06-S09_003_e01",
          "edge_type": "PRECEDES",
          "source": "p7card_CH06-S09_003_n01",
          "target": "p7card_CH06-S09_003_n02",
          "evidence_unit_ids": [
            "v7u_N000477"
          ],
          "evidence_strength": "explicit"
        },
        {
          "edge_id": "p7card_CH06-S09_003_e02",
          "edge_type": "PRODUCES",
          "source": "p7card_CH06-S09_003_n02",
          "target": "p7card_CH06-S09_003_n03",
          "evidence_unit_ids": [
            "v7u_N000477"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "source_unit_ids": [
        "v7u_N000477"
      ],
      "review_status": "accepted",
      "review_notes": "增量命题：卸任但可能保持影响力→机构采用永久PEP方法→个人永久归类为PEP；KG不足：基础KG保存该方法为实践，但未表达决策链；选项判断：可确认某些机构对卸任PEP的处理方式；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S09_004",
      "section_id": "CH06-S09",
      "card_nature": "execution",
      "title": "机构必须基于风险偏好调整交易监控和KYC审查并上报",
      "flow_nodes": [
        {
          "node_id": "p7card_CH06-S09_004_n01",
          "node_category": "entry",
          "node_type": "E3_state_threshold",
          "label": "机构的风险偏好",
          "evidence_unit_ids": [
            "v7u_N000482"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH06-S09_004_n02",
          "node_category": "process",
          "node_type": "P8_constrained_action",
          "label": "机构必须采取必要步骤调整交易监控和KYC审查并上报",
          "evidence_unit_ids": [
            "v7u_N000482"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH06-S09_004_n03",
          "node_category": "exit",
          "node_type": "X5_config_change",
          "label": "交易监控和KYC审查已根据风险偏好调整",
          "evidence_unit_ids": [
            "v7u_N000482"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH06-S09_004_n04",
          "node_category": "exit",
          "node_type": "X7_continuing_obligation",
          "label": "机构承担根据风险偏好上报的义务",
          "evidence_unit_ids": [
            "v7u_N000482"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7card_CH06-S09_004_e01",
          "edge_type": "PRECEDES",
          "source": "p7card_CH06-S09_004_n01",
          "target": "p7card_CH06-S09_004_n02",
          "evidence_unit_ids": [
            "v7u_N000482"
          ],
          "evidence_strength": "explicit",
          "condition": "based on risk appetite"
        },
        {
          "edge_id": "p7card_CH06-S09_004_e02",
          "edge_type": "PRODUCES",
          "source": "p7card_CH06-S09_004_n02",
          "target": "p7card_CH06-S09_004_n03",
          "evidence_unit_ids": [
            "v7u_N000482"
          ],
          "evidence_strength": "explicit"
        },
        {
          "edge_id": "p7card_CH06-S09_004_e03",
          "edge_type": "PRODUCES",
          "source": "p7card_CH06-S09_004_n02",
          "target": "p7card_CH06-S09_004_n04",
          "evidence_unit_ids": [
            "v7u_N000482"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "source_unit_ids": [
        "v7u_N000482"
      ],
      "review_status": "accepted",
      "review_notes": "增量命题：风险偏好→机构调整监控、KYC并上报→配置变化与上报义务；KG不足：基础KG只保存该规则，未表达内部有向链；选项判断：可确认风险偏好如何驱动具体的监控和KYC调整；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```
