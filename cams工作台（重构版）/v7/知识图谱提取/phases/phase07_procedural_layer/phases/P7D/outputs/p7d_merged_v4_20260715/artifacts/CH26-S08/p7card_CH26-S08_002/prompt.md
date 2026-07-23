# P7D Flow Edge Evidence Review Prompt v1

## 角色与边界

你是P7D独立边级证据审核器。P7C已经生成候选card；你的任务是逐条审核card中的现有`flow_edge`，不是重新抽取card。

不得新增、删除、改写、拆分或连接card、node或edge。不得修改P7C正本。不得读取或假设具体题目、选项、参考答案或其他section内容。只输出严格JSON，不输出Markdown或解释。

`section_text_with_unit_anchors`是唯一事实证据。只能引用`allowed_unit_ids`中的unit_id。P7C card中的节点、label、edge、condition和relation_type都只是待审核声明，不能反过来充当证据。

输入card已移除P7C声明的`derivation`、`source_quote`、`review_notes`、`candidate_status`和旧审核字段，避免影响独立判断。你必须仅根据当前section原文独立判断每条边的`derivation`（explicit_text/llm_inference/unsupported）和`llm_recommendation`（accepted/pending/rejected）。最终`review_status`由审核结果独立决定，不依赖P7C声明。

## 逐边审核问题

对每条现有edge分别检查：

1. `source_node_support`：source节点表达的主体、对象、动作、状态或结论是否有当前section依据。
2. `target_node_support`：target节点是否有当前section依据。
3. `direction_support`：原文是否支持source到target的方向；反向是否同样可能。
4. `condition_support`：edge的condition是否被原文明示支持。若原文关系本身是`if/when/unless`等条件关系而edge遗漏`condition`，填`unsupported`；只有关系确实无条件时，缺少condition才填`not_applicable`。
5. `qualifier_support`：must、should、may、might、could、often、only、not、unless、potentially等限定是否被保留，是否被强化或弱化；edge使用`aimed_to`、`may_lead_to`、`helps_achieve`时，分别核对原文是否明确表达“旨在/以期”“可能产生”“有助于”。没有相关限定时可以填`not_applicable`。
6. `parallel_or_correlation_check`：是否把并列来源、共同结果、相关关系、教材叙述顺序或一般主题关系错误写成`PRECEDES`、`PRODUCES`、`DECIDES`或`FEEDBACK`。

每项`status`只能是：`supported, pending, unsupported, not_applicable`。每项必须用中文填写`reason`。

`evidence_unit_ids`与`source_quotes`必须覆盖该边判断依赖的全部实质证据。若方向、condition或限定词需要把规则、标准与一个或多个实例联合起来才能成立，必须同时引用这些组成unit；只引用结果实例、却遗漏提供阈值或条件的unit，不构成完整审核记录。

## edge_type审核口径

- `PRECEDES`：只有原文明示顺序，或交换方向会违反唯一必要功能依赖时才成立。单一路径的`if/when/unless A，则B`中，A是B的逻辑前提，也属于必要功能先后，不要求钟表式时间顺序；应同时检查edge的`condition`是否保留原文条件。共同出现和教材顺序不成立。**原文用 because/due to/as a reason/for this reason 等表达理由或判断依据时，该关系不是流程先后，不得接受为 PRECEDES。** 应判断是否更适合 REFERENCES（判断依据→处理动作，按 REFERENCES 的正本方向即 process→auxiliary，人读反向为 auxiliary→process）。
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

当edge填写`qualifier=aimed_to/may_lead_to/helps_achieve`时，必须审核该限定是否作用于当前source→target关系，而不是只在附近出现。限定有原文依据且作用域正确时可通过；缺失、错配或把目的/可能性强化为已实现结果时应判为`unsupported`。

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
  "section_id": "CH26-S08",
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

section_id: `CH26-S08`
section_title: `Other laws and regulations that impact organizations > ESG regulations`

section_text_with_unit_anchors:
[v7u_N002105|2105] “Environmental, social, and governance” (ESG) refers to a framework organizations use to steer their business practices in accordance with the objectives of sustainable development.
ZH: ESG框架定义：环境、社会和治理

[v7u_N002106|2106] “Environmental” refers to an organization’s impact on the planet.
ZH: ESG中“环境”指组织对地球的影响

[v7u_N002107|2107] “Social” refers to an organization’s relationship with various stakeholders, including employees, customers, and communities within which they operate.
ZH: ESG中“社会”指组织与利益相关者的关系

[v7u_N002108|2108] “Governance” refers to how factors such as leadership, board composition, and transparency govern an organization.
ZH: ESG中“治理”指领导力、董事会构成和透明度

[v7u_N002109|2109] The UN has established a number of initiatives to advance ESG goals on a global basis.
ZH: 联合国设立多项倡议推动全球ESG目标

[v7u_N002110|2110] A widely known initiative is its Sustainable Development Goals, which provide a framework of 17 objectives to address poverty, inequality, and environmental threats while promoting peace and prosperity.
ZH: 联合国可持续发展目标提供17项目标框架

[v7u_N002111|2111] All UN Member States adopted the goals, and many organizations align their strategies with them.
ZH: 所有联合国会员国采纳可持续发展目标

[v7u_N002112|2112] Other ESG-related UN initiatives include the UN Guiding Principles on Business and Human Rights, the UN Environment Program Finance Initiative, and the UN Global Compact, an initiative to encourage businesses to support a wide range of ESG priorities.
ZH: 其他ESG相关联合国倡议包括UNGP、UNEP FI和UNGC

[v7u_N002113|2113] Although ESG regulations vary across jurisdictions, trends include increased mandatory disclosure, accountability, and transparency in organizational practices. The scope of ESG ranges from climate change to corporate governance to human rights. ESG considerations intersect with AML/CFT with respect to:
ZH: ESG法规趋势与反洗钱/反恐怖融资交叉领域概述

[v7u_N002114|2114] Environmental crime: This includes, for example, noncompliance with antipollution rules to achieve economic benefits or the exploitation of illegal mining. Financial crime such as bribery and corruption of local officials might be involved as part of the enterprise.
ZH: 环境犯罪涉及违反环保规则和非法采矿，常伴随贿赂和腐败

[v7u_N002115|2115] Social impact: This includes the exploitation of forced labor and corruption to achieve business objectives.
ZH: 社会影响包括强迫劳动和腐败以实现商业目标

[v7u_N002116|2116] Governance and compliance: This includes governance failures that result in a failure to prevent financial crime within organizations; regulatory enforcement actions all over the world have demonstrated their impact.
ZH: 治理失败导致未能预防金融犯罪，全球监管执法行动已显示其影响

[v7u_N002117|2117] ESG and AML/CFT regulations are converging as global regulatory frameworks continue to evolve to include sustainable business practices and financial crime prevention.
ZH: ESG与反洗钱/反恐怖融资法规正趋于融合

[v7u_N002118|2118] Strong governance frameworks under ESG regulation help prevent and deter corruption, fraud, and other illicit financial activity.
ZH: ESG治理框架有助于预防和阻止腐败、欺诈等金融犯罪

[v7u_N002119|2119] In addition, ESG’s emphasis on social responsibility can help identify certain threats to human rights that might have links to financial crimes.
ZH: ESG社会责任有助于识别与金融犯罪相关的人权威胁

[v7u_N002120|2120] For example, money laundering often involves the proceeds of human trafficking and modern slavery.
ZH: 洗钱常涉及人口贩运和现代奴隶制的收益

[v7u_N002121|2121] By integrating ESG principles into AML/CFT compliance, organizations are better suited to identify and mitigate such risks.
ZH: 将ESG原则融入反洗钱/反恐怖融资合规有助于识别和缓解风险

[v7u_N002122|2122] Both ESG and AML/CFT compliance frameworks depend on a risk-based approach to enable effective compliance and risk mitigation.
ZH: ESG与反洗钱/反恐怖融资均依赖风险为本方法实现有效合规

[v7u_N002123|2123] For ESG regulation, organizations should identify, assess, and manage risks particular to the elements of ESG, such as environmental impact, social responsibility, and organizational governance integrity.
ZH: 组织应识别、评估和管理ESG相关风险，包括环境影响、社会责任和治理诚信

[v7u_N002124|2124] The risk-based approach helps organizations prioritize resources, focus, and efforts on high-risk areas, such as industries with very high carbon emissions or locations vulnerable to human rights violations.
ZH: 风险为本方法帮助组织将资源优先投入高风险领域，如高碳排放行业或人权风险地区

[v7u_N002125|2125] Similarly, AML/CFT regulations require organizations to assess and manage risks particular to money laundering and terrorist financing.
ZH: 反洗钱/反恐怖融资法规要求组织评估和管理洗钱与恐怖融资风险

[v7u_N002126|2126] The adoption of a risk-based approach enables organizations to prioritize resources on high-risk clients, jurisdictions, and services, ensuring that compliance levels are proportionate to the level of risk.
ZH: 采用风险为本方法使组织能够优先对高风险客户、司法管辖区和服务投入资源

[v7u_N002127|2127] Both ESG and AML/CFT frameworks require ongoing due diligence, monitoring, and responsiveness to emerging risks.
ZH: ESG与反洗钱/反恐怖融资框架均要求持续尽职调查、监控和应对新兴风险

allowed_unit_ids:
[
  "v7u_N002105",
  "v7u_N002106",
  "v7u_N002107",
  "v7u_N002108",
  "v7u_N002109",
  "v7u_N002110",
  "v7u_N002111",
  "v7u_N002112",
  "v7u_N002113",
  "v7u_N002114",
  "v7u_N002115",
  "v7u_N002116",
  "v7u_N002117",
  "v7u_N002118",
  "v7u_N002119",
  "v7u_N002120",
  "v7u_N002121",
  "v7u_N002122",
  "v7u_N002123",
  "v7u_N002124",
  "v7u_N002125",
  "v7u_N002126",
  "v7u_N002127"
]

p7c_card_under_review:
{
  "card_id": "p7card_CH26-S08_002",
  "section_id": "CH26-S08",
  "title": "ESG法规要求组织识别、评估和管理ESG相关风险",
  "card_nature": "execution",
  "source_unit_ids": [
    "v7u_N002123"
  ],
  "flow_nodes": [
    {
      "node_id": "n001",
      "node_category": "auxiliary",
      "node_type": "standard",
      "label": "ESG regulation",
      "evidence_unit_ids": [
        "v7u_N002123"
      ]
    },
    {
      "node_id": "n002",
      "node_category": "process",
      "node_type": "P2_execution",
      "label": "organizations should identify, assess, and manage risks particular to the elements of ESG",
      "evidence_unit_ids": [
        "v7u_N002123"
      ]
    }
  ],
  "flow_edges": [
    {
      "edge_id": "edge_001",
      "edge_type": "REFERENCES",
      "source": "n002",
      "target": "n001",
      "evidence_unit_ids": [
        "v7u_N002123"
      ]
    }
  ]
}
