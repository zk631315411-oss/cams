# P7C Section-Local Coverage Adjudication Prompt v2

## 角色

你是P7C覆盖裁决器。首次抽取器已经发现候选命题并生成候选card；这些card尚未经过P7D正式结构校验和边级审核。你的唯一任务是复核`coverage_audit`中原决定为`kg_only`的候选，判断它们是否因KG/P7C边界理解错误而漏成卡。

只输出严格JSON补丁，不输出Markdown或解释。`original_json`提供本次无记忆API调用所需的完整首次抽取上下文；不得回显或改写它。Runner会把补丁确定性合并到P7C正本。

## P7C目的

P7C在不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标和一般知识关系的前提下，从单个section中增量提取对CAMS题目选项判断有用的局部程序性或判断性有向结构：业务情境、事件、线索、输入或标准如何关联到特定主体带原文情态的识别、评估、决策或应对，以及原文明示的独立结论、记录、状态变化、控制效果、分支或后续行动。没有独立结果时允许开放关系。

P7C不读取题目或参考答案，不处理跨section桥接。当前section原文是唯一事实证据；基础KG摘要只能用于去重，不能补造事实。

## 裁决对象

只复核`original_json.coverage_audit`中`decision=kg_only`的候选。不得新增候选，不得删除候选，不得修改候选的`candidate_id`、`unit_ids`或`proposition`。

原本为`p7c_card`的候选及`original_json.cards`只用于理解已有结果、避免重复和避开已占用ID。输出中不得包含、删除、改写、拆分、合并或重新编号这些既有内容。

## 裁决标准

将原`kg_only`候选提升为`p7c_card`，必须同时满足：

1. 当前section证据支持关系两端、特定主体、方向以及条件（如有）。
2. 候选内部存在“情境/事件/线索/输入/标准如何关联到主体动作或判断”的局部结构；只有原文明示独立结果时才增加结果节点。
3. 该方向结构能够帮助判断选项的顺序、条件、主体职责、义务、应对、因果或适用范围。
4. 基础KG只能保存整句话或各知识点，不能充分表达句内的主体、方向、条件、动作约束或独立结果关系。

结构复杂度和是否闭环不是门槛。一个unit、一条路径、没有分支或反馈，或没有独立出口，都不能作为`kg_only`理由。只有对象实际到达、提交、移交或进入某阶段并触发动作时才建entry；静态适用对象、线索输入、分析材料、风险阈值、监管要求、政策基准或风险偏好应作为auxiliary standard/input并由process通过`REFERENCES`指向。

不得用“纯义务陈述”“没有复杂条件”“没有复杂步骤”拒绝提升。只要候选已经明确给出监管要求、风险偏好或状态变化如何约束特定主体的识别、标准选择或分类维持，即使没有独立出口，也满足局部有向结构要求。

以下通常应提升：

- 金融机构的识别动作明确参照监控系统标记的异常活动；只有原文另行给出识别结论时才增加出口。
- FIU综合SAR和跨境活动并形成红旗发现。
- 风险阈值和直接/间接持股被机构用于UBO判断并形成分类结论。
- 外部监管要求或上位标准约束机构调整控制、政策或职责；除非原文明示命令到达后触发动作，否则使用`REFERENCES`而不是`PRECEDES`。
- 明确条件触发拒绝、批准、升级、报告、监控或复核。
- 当地监管要求约束机构如何识别PEP；不得因规则只有一个unit或没有义务出口而拒绝。
- 机构基于风险偏好可以选择更高标准；必须保留可选性，即使没有独立配置出口也可以作为开放式局部关系。
- 卸任等状态变化后，特定机构仍明确维持既有分类；必须保留“部分机构”“可能”等限定。

以下保持`kg_only`：

- 纯定义、分类、阈值数值或组成列表，没有主体应用或其他有向关系。
- 普通犯罪方法、犯罪分子操作步骤或普通案例机制，没有机构、FIU、监管或执法主体的识别、判断或应对。
- 孤立红旗、后果、历史事实或抽象风险缓解目的。
- 只有主题相关性，或者必须补造主体、条件、方向、动作或结果才能闭合。

## 修改规则

对`review_target_candidate_ids`中的每个原`kg_only`候选，在顶层`coverage_adjudication`中输出一条记录：

```json
{
  "candidate_id": "cand_001",
  "original_decision": "kg_only",
  "final_decision": "kg_only",
  "card_id": null,
  "reason": "<中文裁决理由>"
}
```

`final_decision`只能为`kg_only`或`p7c_card`。

保持`kg_only`时：`card_id`必须为`null`。

提升为`p7c_card`时：

- 在裁决记录中填写新card的`card_id`；
- `reason`说明基础KG不能表达的方向结构；
- 在顶层`promoted_cards`中输出且只输出对应的新card；
- 新card ID不得与`original_json.cards`中的既有ID重复；
- 每个提升候选恰好对应一张新card，不得输出未被裁决提升的card。

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

`X7_continuing_obligation`只用于原文明示上游动作、决定或协议新建立了独立持续义务；规范性语句中的“主体必须/应当执行某动作”应保留在process中，不得复制为X7出口。

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard。
- `PRODUCES`只能由process指向exit。
- `DECIDES`只能由`P3_branch_routing`发出，至少两条分支，每条都有原文明示的`condition`。
- `derivation=llm_inference`只说明边依赖必要功能推理，不改变`candidate_status`，也不表示P7D已经接受或拒绝。

`REFERENCES.condition`可以限定某项input/standard适用于process的情境，但不表示条件分支。单一条件直接触发动作时使用带`condition`的`PRECEDES`；只有至少两条原文明示路径时才使用`DECIDES`。

静态适用对象、审查材料或判断输入不得仅因语法顺序建成`entry --PRECEDES--> process`；应建为auxiliary input并由process通过`REFERENCES`指向。不得把同一谓词的主动式和被动式拆成process与exit，也不得把“动作需要理由、批准或遵循要求”写成“动作`PRODUCES`要求/义务”。

单一路径的`if/when/unless A，则B`使用条件entry到process的`PRECEDES`，并在edge的`condition`中保留原文条件；它表达逻辑前提，不要求钟表式先后。输出每条`PRODUCES`前必须反问：source和target合并后是否仍损失一个独立事实；若不损失，删除同义target和该边。理由、批准、标准或义务约束动作时使用process指向standard/input的`REFERENCES`。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写，不得创造新类型。

必须保留`must, should, may, might, could, often, potentially, help`等情态强度。不得将“有助于缓解”强化为“风险已经消除”。`must/shall/is required to`只证明义务存在，不证明动作已经完成；除非原文明示完成或结果已经发生，不得输出“已调整”“已建立”“已降低”等完成状态。

`must`本身不证明义务是持续、定期、永久或反复的，不得无证据增加这些限定。`escalate/escalation`默认写成“升级处理/升级处置”或保留英文，不得翻译为“上报/报告”；只有原文明示`report/notify/file/refer`及其对象时，才能写成上报、报告或移交。

新增card的节点、边和`source_unit_ids`只能引用对应候选原有的`unit_ids`。不得借裁决轮追加其他unit、扩展候选命题或引入无关主题；若原候选证据本身不足，保持`kg_only`。

## 输出约束

只返回补丁对象，顶层只能包含：

```text
section_id
coverage_adjudication
promoted_cards
```

示例：

```json
{
  "section_id": "<section_id>",
  "coverage_adjudication": [
    {
      "candidate_id": "cand_001",
      "original_decision": "kg_only",
      "final_decision": "kg_only",
      "card_id": null,
      "reason": "<中文KG边界理由>"
    }
  ],
  "promoted_cards": []
}
```

即使所有候选都保持`kg_only`，也必须逐一输出裁决记录，此时`promoted_cards`为空数组。不得输出`coverage_audit`、既有`cards`、`skip_reason`或其他首次抽取字段。

## 当前section

section_id: `CH06-S09`

section_title: `Money Laundering Risks in Financial Services > Politically exposed person risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "政治敏感人物的定义、范围和关联人",
      "title_en": "PEP definition, scope, and related persons",
      "covered_units": [
        {
          "unit_id": "v7u_N000457",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000469",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000470",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000473",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000474",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000475",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000467",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000468",
          "unit_type": "classification",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000471",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000472",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "政治敏感人物识别挑战与合规要求",
      "title_en": "PEP Identification Challenges and Compliance",
      "covered_units": [
        {
          "unit_id": "v7u_N000458",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000459",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000460",
          "unit_type": "rule",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "FATF对政治敏感人物的分类",
      "title_en": "FATF Classification of PEP Types",
      "covered_units": [
        {
          "unit_id": "v7u_N000462",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000463",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000464",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000461",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "政治敏感人物的腐败风险与示例",
      "title_en": "PEP Vulnerability to Corruption and Examples",
      "covered_units": [
        {
          "unit_id": "v7u_N000465",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000466",
          "unit_type": "case",
          "kg_role": "illustrates"
        }
      ]
    },
    {
      "title_zh": "政治敏感人物风险管理与监控方法",
      "title_en": "PEP Risk Management and Monitoring Approaches",
      "covered_units": [
        {
          "unit_id": "v7u_N000476",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000477",
          "unit_type": "rule",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000481",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000482",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000479",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000478",
          "unit_type": "classification",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000480",
          "unit_type": "rule",
          "kg_role": "explains"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "政治敏感人物的定义、范围和关联人",
      "target_title": "FATF对政治敏感人物的分类",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物的定义、范围和关联人",
      "target_title": "政治敏感人物的腐败风险与示例",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物的定义、范围和关联人",
      "target_title": "政治敏感人物风险管理与监控方法",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物识别挑战与合规要求",
      "target_title": "政治敏感人物风险管理与监控方法",
      "relation_type": "prepares"
    },
    {
      "source_title": "FATF对政治敏感人物的分类",
      "target_title": "政治敏感人物的腐败风险与示例",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物的腐败风险与示例",
      "target_title": "政治敏感人物风险管理与监控方法",
      "relation_type": "prepares"
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
      "proposition": "机构必须遵守当地监管要求识别PEP",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S09_001",
      "reason": "该局部有向结构体现process引用standard的约束关系，超出基础KG的一般规则表达"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000460"
      ],
      "proposition": "机构可根据风险偏好选择执行更高的PEP标准",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S09_002",
      "reason": "风险偏好作为standard约束可选择动作，有向关系超出基础KG的简单规则存储"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000477"
      ],
      "proposition": "部分机构采用‘一旦是PEP，永远是PEP’方法，即使个人卸任也可能维持PEP分类",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S09_003",
      "reason": "条件触发的判断链：卸任变化导向维持分类，为基础KG未表达的局部判断结构"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000482"
      ],
      "proposition": "机构必须基于风险偏好调整交易监控和KYC审查并升级处理",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S09_004",
      "reason": "process引用standard的约束关系，包含escalate动作，超出基础KG的规则表达"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000478",
        "v7u_N000479",
        "v7u_N000480"
      ],
      "proposition": "其他机构考察个人当时影响力和已被归类为PEP的时间长短，以此决定是否维持PEP分类",
      "decision": "kg_only",
      "card_id": null,
      "reason": "原文仅列出考察因素，未明确决策动作和结果，属于解释性内容，由基础KG承接"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000466"
      ],
      "proposition": "PEP可能利用政府合同换取回扣或影响立法受贿等腐败行为",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立案例说明，无机构应对或判断结构，为基础KG可承接的普通案例机制"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000465"
      ],
      "proposition": "高层职位个人及其关联人更易受腐败影响",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立风险指标，无具体主体动作或判断链，由基础KG承接"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N000467"
      ],
      "proposition": "应采用宽泛定义来界定PEP",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性建议，无有向结构，由基础KG作为规则保存"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH06-S09_001",
      "section_id": "CH06-S09",
      "card_nature": "execution",
      "title": "识别PEP必须遵守当地监管要求",
      "flow_nodes": [
        {
          "node_id": "P001",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构必须识别PEP (must adhere to local regulatory requirements)",
          "evidence_unit_ids": [
            "v7u_N000459"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "S001",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "当地监管要求 (local regulatory requirements)",
          "evidence_unit_ids": [
            "v7u_N000459"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E001",
          "edge_type": "REFERENCES",
          "source": "P001",
          "target": "S001",
          "evidence_unit_ids": [
            "v7u_N000459"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N000459"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构必须识别PEP --REFERENCES--> 当地监管要求；KG不足：基础KG可存储规则但无法表达process与standard之间的约束有向关系；选项判断：可确认机构识别PEP时必须遵守当地监管要求，区分必须遵守与可选择的更高标准；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S09_002",
      "section_id": "CH06-S09",
      "card_nature": "execution",
      "title": "可根据风险偏好选择更高PEP标准",
      "flow_nodes": [
        {
          "node_id": "P002",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构可选择执行更高的PEP标准 (may choose to enforce higher standards based on risk appetite)",
          "evidence_unit_ids": [
            "v7u_N000460"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "S002",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "机构的风险偏好 (risk appetite)",
          "evidence_unit_ids": [
            "v7u_N000460"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E002",
          "edge_type": "REFERENCES",
          "source": "P002",
          "target": "S002",
          "evidence_unit_ids": [
            "v7u_N000460"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N000460"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构可选择执行更高PEP标准 --REFERENCES--> 风险偏好；KG不足：基础KG作为一般规则存储，无方向性约束；选项判断：可确认这一选择基于风险偏好，非强制；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S09_003",
      "section_id": "CH06-S09",
      "card_nature": "assessment",
      "title": "部分机构采用‘一旦是PEP，永远是PEP’方法维持分类",
      "flow_nodes": [
        {
          "node_id": "E003",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "个人卸任 (individual has stepped down from prominent public function)",
          "evidence_unit_ids": [
            "v7u_N000477"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P003",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "部分机构采用‘一旦是PEP，永远是PEP’方法继续将个人视为PEP (Some organizations follow 'once a PEP, always a PEP' approach, continuing to treat the individual as a PEP)",
          "evidence_unit_ids": [
            "v7u_N000477"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E003_1",
          "edge_type": "PRECEDES",
          "source": "E003",
          "target": "P003",
          "evidence_unit_ids": [
            "v7u_N000477"
          ],
          "derivation": "explicit_text",
          "condition": "即使个人已卸任，因其仍可能保持相同影响力圈"
        }
      ],
      "source_unit_ids": [
        "v7u_N000477"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：个人卸任 --[条件]--> 部分机构维持PEP分类；KG不足：基础KG可表达该规则但无法表达条件触发的判断链；选项判断：可确认部分机构对卸任PPE仍视为PPE，其他机构可能不同；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S09_004",
      "section_id": "CH06-S09",
      "card_nature": "control",
      "title": "必须基于风险偏好调整监控和KYC审查并升级",
      "flow_nodes": [
        {
          "node_id": "P004",
          "node_category": "process",
          "node_type": "P8_constrained_action",
          "label": "机构必须调整交易监控和KYC审查并升级 (must adapt transaction monitoring and KYC reviews and escalate based on risk appetite)",
          "evidence_unit_ids": [
            "v7u_N000482"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "S004",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "机构的风险偏好 (risk appetite)",
          "evidence_unit_ids": [
            "v7u_N000482"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E004",
          "edge_type": "REFERENCES",
          "source": "P004",
          "target": "S004",
          "evidence_unit_ids": [
            "v7u_N000482"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N000482"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构必须调整监控/KYC并升级 --REFERENCES--> 风险偏好；KG不足：基础KG作为一般合规要求存储，无约束关系方向；选项判断：可确认调整动作基于风险偏好，包含escalate；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_005",
  "cand_006",
  "cand_007",
  "cand_008"
]
```
