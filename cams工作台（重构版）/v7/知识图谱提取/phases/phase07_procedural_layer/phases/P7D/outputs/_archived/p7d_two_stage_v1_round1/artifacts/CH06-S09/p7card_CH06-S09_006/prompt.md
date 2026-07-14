# P7D Flow Edge Evidence Review Prompt v1

## 角色与边界

你是P7D独立边级证据审核器。P7C已经生成候选card；你的任务是逐条审核card中的现有`flow_edge`，不是重新抽取card。

不得新增、删除、改写、拆分或连接card、node或edge。不得修改P7C正本。不得读取或假设具体题目、选项、参考答案或其他section内容。只输出严格JSON，不输出Markdown或解释。

`section_text_with_unit_anchors`是唯一事实证据。只能引用`allowed_unit_ids`中的unit_id。P7C card中的节点、label、edge、condition和relation_type都只是待审核声明，不能反过来充当证据。

输入card已移除P7C声明的`derivation`、`source_quote`、`review_notes`、`candidate_status`和旧审核字段，避免影响独立判断。你必须仅根据当前section原文重新判断审核用`derivation`；Runner会在LLM审核完成后，另行结合未暴露给你的P7C声明生成最终状态。

## 逐边审核问题

对每条现有edge分别检查：

1. `source_node_support`：source节点表达的主体、对象、动作、状态或结论是否有当前section依据。
2. `target_node_support`：target节点是否有当前section依据。
3. `direction_support`：原文是否支持source到target的方向；反向是否同样可能。
4. `condition_support`：edge的condition是否被原文明示支持。若原文关系本身是`if/when/unless`等条件关系而edge遗漏`condition`，填`unsupported`；只有关系确实无条件时，缺少condition才填`not_applicable`。
5. `qualifier_support`：must、should、may、might、could、often、only、not、unless、potentially等限定是否被保留，是否被强化或弱化。没有相关限定时可以填`not_applicable`。
6. `parallel_or_correlation_check`：是否把并列来源、共同结果、相关关系、教材叙述顺序或一般主题关系错误写成`PRECEDES`、`PRODUCES`、`DECIDES`或`FEEDBACK`。

每项`status`只能是：`supported, pending, unsupported, not_applicable`。每项必须用中文填写`reason`。

`evidence_unit_ids`与`source_quotes`必须覆盖该边判断依赖的全部实质证据。若方向、condition或限定词需要把规则、标准与一个或多个实例联合起来才能成立，必须同时引用这些组成unit；只引用结果实例、却遗漏提供阈值或条件的unit，不构成完整审核记录。

## edge_type审核口径

- `PRECEDES`：只有原文明示顺序，或交换方向会违反唯一必要功能依赖时才成立。单一路径的`if/when/unless A，则B`中，A是B的逻辑前提，也属于必要功能先后，不要求钟表式时间顺序；应同时检查edge的`condition`是否保留原文条件。共同出现和教材顺序不成立。
- `REFERENCES`：只表达process对非时序输入、线索、标准或判断维度的参照，不表达先后、产出或条件分支。若带`condition`，它只能限定该参照关系的适用范围，并必须有原文证据。
- `PRODUCES`：process必须产生target结果；揭示既存状态不等于产生该状态。
- `DECIDES`：必须存在真实条件分流，condition有原文证据；单一条件应对不自动构成分支。
- `FEEDBACK`：结果或事件必须触发复核、补充、更新、调优、监控或再次处理。

## 语义压缩与隐藏条件检查

审核每条边时，不仅检查edge对象中的`condition`，还要检查source和target label是否把关系成立所需的条件、标准或判断结果藏在节点文字中。

如果target只有在某项标准、阈值、充分性、批准状态或判断结论成立时才会出现，而候选边使用无condition的`PRODUCES`直接连接到target，不能把`condition_support`标为`not_applicable`。应判断该关系是否遗漏条件；条件不可由现有边可靠表达时，相关检查为`unsupported`，不得因为target label中写了“达到、通过、满足、未达到、否则”等词就视为已经保留条件。

当同一判断标准下存在两个或以上互斥结果时，检查候选图是否错误地用单一泛化exit或无条件`PRODUCES`压扁分流。P7D不负责补画decision或分支，但应拒绝语义不成立的现有边。原文只支持单一路径时，也不得反向要求P7C补造另一分支。

输入处理与标准判断是不同语义操作：原始数据、材料或组成要素应被实际处理它们的process参照；标准、阈值、政策或判断维度应被实际应用它们的判断process参照。如果一个宽泛process label同时声称收集/计算输入并完成条件分类，必须分别检查每条边能否由原文支持，不能用宽泛节点文字替代边的方向与条件证据。

一般规则与同一标准下的正反实例可以共同支持候选分支，但从多个unit或实例归纳出一般关系时，`derivation`通常应为`llm_inference`。孤立实例不得自动推广成一般分流规则。

相邻句中的冻结、查封、调查、起诉、定罪、监禁和罚款不自动形成单链。多个线索、标准、情报来源或共同结果不因排列顺序形成先后边。

`REFERENCES`不要求原文必须出现字面上的“参照/使用”。当相邻句围绕同一对象，原文明示process正在设定、应用或比较某项参数，而target恰好给出该参数的基准或风险调整值，且不存在其他合理连接时，可以审核为`llm_inference`而不是直接判为`unsupported`。若只是同主题并列或存在多种合理连接，仍应拒绝或待审。

`PRODUCES`可以表达原文明示的限定性控制效果，例如`help mitigate/may reduce/can improve`，前提是target label完整保留“有助于/可能/可以”等情态，且`qualifier_support`通过。`PRODUCES`这个结构类型本身不把限定性效果强化为必然完成状态；若target删掉限定词或写成“已经降低/已经消除”，应判为`unsupported`。

如果process与target只是同一谓词的主动式/被动式或完成态改写，例如“机构识别UBO”与“UBO被识别”，二者不是独立事实，`PRODUCES`应判为`unsupported`。如果target是执行source所需的理由、批准、标准或义务，它约束source而不是由source产生，`PRODUCES`也应判为`unsupported`。

当target为`X7_continuing_obligation`时，必须确认原文明示source动作、决定或协议新建立了一个语义独立的持续义务。若target只是把source中的“必须/应当执行某动作”复制成义务出口，`PRODUCES`应判为`unsupported`。

## derivation与建议

`derivation`只描述这条边如何由证据得到，不能用来代替审核结论：

- `explicit_text`：原文明示关系及方向。
- `llm_inference`：两端均有证据，但关系或方向依赖必要功能推理。
- `unsupported`：至少一端、关系、方向或条件缺少依据。

`llm_recommendation`只能是：

- `accepted`：所有必要检查均有充分支持。
- `pending`：存在歧义，或关系依赖必要功能推理，需要人工判断。
- `rejected`：至少一个关键检查明确不成立。

不要为了保留card而接受边。也不要因为边来自P7C或标为`explicit`就默认接受。

## 输出合同

必须覆盖输入card中的每一条edge，edge_id不得遗漏、增加或重复。顺序与输入保持一致。

```json
{
  "section_id": "CH06-S09",
  "card_id": "<card_id>",
  "edge_reviews": [
    {
      "edge_id": "<existing edge_id>",
      "derivation": "explicit_text",
      "llm_recommendation": "accepted",
      "checks": {
        "source_node_support": {"status": "supported", "reason": "<中文>"},
        "target_node_support": {"status": "supported", "reason": "<中文>"},
        "direction_support": {"status": "supported", "reason": "<中文>"},
        "condition_support": {"status": "not_applicable", "reason": "该边没有condition。"},
        "qualifier_support": {"status": "supported", "reason": "<中文>"},
        "parallel_or_correlation_check": {"status": "supported", "reason": "<中文>"}
      },
      "evidence_unit_ids": ["<allowed unit id>"],
      "source_quotes": ["<当前section原文短引>"],
      "reason": "<中文总判断>"
    }
  ]
}
```

## 当前section与card

section_id: `CH06-S09`
section_title: `Money Laundering Risks in Financial Services > Politically exposed person risks`

section_text_with_unit_anchors:
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

allowed_unit_ids:
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

p7c_card_under_review:
{
  "card_id": "p7card_CH06-S09_006",
  "section_id": "CH06-S09",
  "title": "Other Organizations Consider Influence and Duration When Assessing PEP Risk",
  "card_nature": "assessment",
  "source_unit_ids": [
    "v7u_N000478",
    "v7u_N000479",
    "v7u_N000480"
  ],
  "flow_nodes": [
    {
      "node_id": "P_006",
      "node_category": "process",
      "node_type": "P1_assessment",
      "label": "其他组织评估PEP风险",
      "evidence_unit_ids": [
        "v7u_N000478"
      ]
    },
    {
      "node_id": "IN_006_1",
      "node_category": "auxiliary",
      "node_type": "input",
      "label": "个人当时的影响力",
      "evidence_unit_ids": [
        "v7u_N000479"
      ]
    },
    {
      "node_id": "IN_006_2",
      "node_category": "auxiliary",
      "node_type": "input",
      "label": "被归类为PEP的时间长短",
      "evidence_unit_ids": [
        "v7u_N000480"
      ]
    }
  ],
  "flow_edges": [
    {
      "edge_id": "E_006_1",
      "edge_type": "REFERENCES",
      "source": "P_006",
      "target": "IN_006_1",
      "relation_type": "clue_supports_identification",
      "evidence_unit_ids": [
        "v7u_N000478",
        "v7u_N000479"
      ]
    },
    {
      "edge_id": "E_006_2",
      "edge_type": "REFERENCES",
      "source": "P_006",
      "target": "IN_006_2",
      "relation_type": "clue_supports_identification",
      "evidence_unit_ids": [
        "v7u_N000478",
        "v7u_N000480"
      ]
    }
  ]
}
