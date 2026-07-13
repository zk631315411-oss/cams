# P7D Flow Edge Evidence Review Prompt v1

## 角色与边界

你是P7D独立边级证据审核器。P7C已经生成候选card；你的任务是逐条审核card中的现有`flow_edge`，不是重新抽取card。

不得新增、删除、改写、拆分或连接card、node或edge。不得修改P7C正本。不得读取或假设具体题目、选项、参考答案或其他section内容。只输出严格JSON，不输出Markdown或解释。

`section_text_with_unit_anchors`和`section_units`是唯一事实证据。只能引用`allowed_unit_ids`中的unit_id。P7C card、label、source_quote、derivation以及旧版evidence_strength都只是待审核声明，不能反过来充当证据。

## 逐边审核问题

对每条现有edge分别检查：

1. `source_node_support`：source节点表达的主体、对象、动作、状态或结论是否有当前section依据。
2. `target_node_support`：target节点是否有当前section依据。
3. `direction_support`：原文是否支持source到target的方向；反向是否同样可能。
4. `condition_support`：edge的condition是否被原文明示支持。没有condition时填`not_applicable`。
5. `qualifier_support`：must、should、may、might、could、often、only、not、unless、potentially等限定是否被保留，是否被强化或弱化。没有相关限定时可以填`not_applicable`。
6. `parallel_or_correlation_check`：是否把并列来源、共同结果、相关关系、教材叙述顺序或一般主题关系错误写成`PRECEDES`、`PRODUCES`、`DECIDES`或`FEEDBACK`。

每项`status`只能是：`supported, pending, unsupported, not_applicable`。每项必须用中文填写`reason`。

## edge_type审核口径

- `PRECEDES`：只有原文明示顺序，或交换方向会违反唯一必要功能依赖时才成立。共同出现和教材顺序不成立。
- `REFERENCES`：只表达process对非时序输入、线索、标准或判断维度的参照，不表达先后或产出。
- `PRODUCES`：process必须产生target结果；揭示既存状态不等于产生该状态。
- `DECIDES`：必须存在真实条件分流，condition有原文证据；单一条件应对不自动构成分支。
- `FEEDBACK`：结果或事件必须触发复核、补充、更新、调优、监控或再次处理。

相邻句中的冻结、查封、调查、起诉、定罪、监禁和罚款不自动形成单链。多个线索、标准、情报来源或共同结果不因排列顺序形成先后边。

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

section_units:
[
  {
    "en_quote": "A politically exposed person (PEP) is an individual in a prominent political function, their immediate family, close associates, and any businesses held or controlled by that person.",
    "knowledge_zh": "政治敏感人物（政治敏感人物）的定义：担任重要公职的个人及其亲属和密切关联人",
    "pdf_page": 62,
    "printed_page": "57",
    "type": "definition",
    "unit_id": "v7u_N000457",
    "unit_order": 457
  },
  {
    "en_quote": "One challenge in identifying PEPs is the varying guidance and recommendations in each jurisdiction.",
    "knowledge_zh": "识别政治敏感人物的挑战在于各司法管辖区指引不同",
    "pdf_page": 62,
    "printed_page": "57",
    "type": "fact",
    "unit_id": "v7u_N000458",
    "unit_order": 458
  },
  {
    "en_quote": "Organizations must adhere to their local regulatory requirements in identifying PEPs.",
    "knowledge_zh": "机构必须遵守当地监管要求识别政治敏感人物",
    "pdf_page": 62,
    "printed_page": "57",
    "type": "rule",
    "unit_id": "v7u_N000459",
    "unit_order": 459
  },
  {
    "en_quote": "However, organizations may choose to enforce higher standards based on their risk appetite.",
    "knowledge_zh": "机构可根据风险偏好执行更高的政治敏感人物标准",
    "pdf_page": 62,
    "printed_page": "57",
    "type": "rule",
    "unit_id": "v7u_N000460",
    "unit_order": 460
  },
  {
    "en_quote": "According to the Financial Action Task Force (FATF), there are three types of PEPs:",
    "knowledge_zh": "FATF将政治敏感人物分为三类",
    "pdf_page": 62,
    "printed_page": "57",
    "type": "classification",
    "unit_id": "v7u_N000461",
    "unit_order": 461
  },
  {
    "en_quote": "Foreign PEPs are individuals entrusted with prominent public functions by a foreign country.",
    "knowledge_zh": "外国政治敏感人物指受外国委托担任重要公共职能的个人",
    "pdf_page": 62,
    "printed_page": "57",
    "type": "fact",
    "unit_id": "v7u_N000462",
    "unit_order": 462
  },
  {
    "en_quote": "Domestic PEPs are individuals entrusted domestically with prominent public functions.",
    "knowledge_zh": "国内政治敏感人物指在国内担任重要公共职能的个人",
    "pdf_page": 62,
    "printed_page": "57",
    "type": "fact",
    "unit_id": "v7u_N000463",
    "unit_order": 463
  },
  {
    "en_quote": "International organization PEPs are individuals from an international organization entrusted with a prominent function such as secretary general, executive director, or president.",
    "knowledge_zh": "国际组织政治敏感人物指在国际组织中担任秘书长、执行董事或主席等要职的个人",
    "pdf_page": 62,
    "printed_page": "57",
    "type": "fact",
    "unit_id": "v7u_N000464",
    "unit_order": 464
  },
  {
    "en_quote": "Individuals in high positions and their associates are more vulnerable to corruption.",
    "knowledge_zh": "高层职位个人及其关联人更易受腐败影响",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "fact",
    "unit_id": "v7u_N000465",
    "unit_order": 465
  },
  {
    "en_quote": "Corruption might be favors where the PEP directs government contracts to an organization in return for kickbacks. In addition, a PEP might influence legislation for bribes or flee the country with government funds.",
    "knowledge_zh": "政治敏感人物腐败示例：以政府合同换取回扣、影响立法收受贿赂或携政府资金潜逃",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "case",
    "unit_id": "v7u_N000466",
    "unit_order": 466
  },
  {
    "en_quote": "Use a broad definition for defining a PEP.",
    "knowledge_zh": "应采用宽泛定义来界定政治敏感人物",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "rule",
    "unit_id": "v7u_N000467",
    "unit_order": 467
  },
  {
    "en_quote": "PEPs can generally be defined as:",
    "knowledge_zh": "政治敏感人物的一般定义",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "classification",
    "unit_id": "v7u_N000468",
    "unit_order": 468
  },
  {
    "en_quote": "A person in a prominent decision-making or influential role",
    "knowledge_zh": "政治敏感人物指担任重要决策或有影响力角色的人",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "fact",
    "unit_id": "v7u_N000469",
    "unit_order": 469
  },
  {
    "en_quote": "A person within royal, military, legislative, judicial, executive, or similar government positions",
    "knowledge_zh": "政治敏感人物包括王室、军事、立法、司法、行政或类似政府职位的人",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "fact",
    "unit_id": "v7u_N000470",
    "unit_order": 470
  },
  {
    "en_quote": "PEPs will often use nominees or businesses they are associated with.",
    "knowledge_zh": "政治敏感人物常使用名义人或关联企业",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "fact",
    "unit_id": "v7u_N000471",
    "unit_order": 471
  },
  {
    "en_quote": "Therefore, the definition of PEP can also include:",
    "knowledge_zh": "政治敏感人物定义还可包括以下人员",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "classification",
    "unit_id": "v7u_N000472",
    "unit_order": 472
  },
  {
    "en_quote": "Immediate family",
    "knowledge_zh": "政治敏感人物的直系亲属",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "fact",
    "unit_id": "v7u_N000473",
    "unit_order": 473
  },
  {
    "en_quote": "Close friends or associates",
    "knowledge_zh": "政治敏感人物的密友或关联人",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "fact",
    "unit_id": "v7u_N000474",
    "unit_order": 474
  },
  {
    "en_quote": "Businesses owned or held by those individuals",
    "knowledge_zh": "政治敏感人物拥有或持有的企业",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "fact",
    "unit_id": "v7u_N000475",
    "unit_order": 475
  },
  {
    "en_quote": "Under a risk-based approach, PEP risk is manageable.",
    "knowledge_zh": "基于风险的方法下，政治敏感人物风险是可控的",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "fact",
    "unit_id": "v7u_N000476",
    "unit_order": 476
  },
  {
    "en_quote": "Some organizations follow a “once a PEP, always a PEP” approach because the individual may remain in the same circles of influence, even if they have stepped down.",
    "knowledge_zh": "部分机构采用“一旦是政治敏感人物，永远是政治敏感人物”的方法",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "rule",
    "unit_id": "v7u_N000477",
    "unit_order": 477
  },
  {
    "en_quote": "Other organizations will look at:",
    "knowledge_zh": "其他机构会考察以下因素",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "classification",
    "unit_id": "v7u_N000478",
    "unit_order": 478
  },
  {
    "en_quote": "The individual’s influence at the time, such as their ability to award contracts or allocate funds",
    "knowledge_zh": "考察个人当时的影响力，如授予合同或分配资金的能力",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "fact",
    "unit_id": "v7u_N000479",
    "unit_order": 479
  },
  {
    "en_quote": "How long the individual has been classified as a PEP",
    "knowledge_zh": "考察个人被归类为政治敏感人物的时间长短",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "rule",
    "unit_id": "v7u_N000480",
    "unit_order": 480
  },
  {
    "en_quote": "The purpose of the PEP designation is important.",
    "knowledge_zh": "政治敏感人物 认定的目的具有重要意义",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "fact",
    "unit_id": "v7u_N000481",
    "unit_order": 481
  },
  {
    "en_quote": "Organizations must take the necessary steps to adapt transaction monitoring and KYC reviews and escalate based on their risk appetite.",
    "knowledge_zh": "机构必须根据风险偏好调整交易监控和 了解你的客户 审查",
    "pdf_page": 63,
    "printed_page": "58",
    "type": "rule",
    "unit_id": "v7u_N000482",
    "unit_order": 482
  }
]

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
  "card_id": "p7card_CH06-S09_001",
  "section_id": "CH06-S09",
  "card_nature": "execution",
  "title": "当地监管要求约束机构识别PEP",
  "flow_nodes": [
    {
      "node_id": "P1",
      "node_category": "process",
      "node_type": "P8_constrained_action",
      "label": "机构必须识别PEP",
      "evidence_unit_ids": [
        "v7u_N000459"
      ],
      "evidence_strength": "explicit"
    },
    {
      "node_id": "S1",
      "node_category": "auxiliary",
      "node_type": "standard",
      "label": "当地监管要求",
      "evidence_unit_ids": [
        "v7u_N000459"
      ],
      "evidence_strength": "explicit"
    }
  ],
  "flow_edges": [
    {
      "edge_id": "e1",
      "edge_type": "REFERENCES",
      "source": "P1",
      "target": "S1",
      "evidence_unit_ids": [
        "v7u_N000459"
      ],
      "derivation": "explicit_text",
      "relation_type": "standard_constrains_action",
      "condition": null,
      "source_quote": "Organizations must adhere to their local regulatory requirements in identifying PEPs."
    }
  ],
  "source_unit_ids": [
    "v7u_N000459"
  ],
  "candidate_status": "candidate",
  "review_notes": "增量命题：当地监管要求约束机构的PEP识别动作；KG不足：基础KG可保存该规则但无法表达内部约束关系；选项判断：可确认机构识别PEP的义务来源；LLM推理：无"
}
