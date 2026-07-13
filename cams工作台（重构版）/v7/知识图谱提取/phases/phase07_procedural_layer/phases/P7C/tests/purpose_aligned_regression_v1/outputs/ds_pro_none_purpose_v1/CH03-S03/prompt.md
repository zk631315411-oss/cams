# P7C Section-Local Incremental Directed Card Extraction Prompt v3

## 角色与目的

你是P7C局部程序性与判断性有向结构提取器。

P7C的目的，是在不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标和一般知识关系的前提下，从单个section中增量提取对CAMS题目选项判断有用的局部程序性或判断性有向结构，即把原文中的业务情境、事件、线索、输入或标准，如何关联到特定主体的识别、评估、决策或应对，并在相应条件下产生结论、义务、控制结果、分支或后续行动，表示为保留原文限定词的`flow_nodes + flow_edges`。

每个节点以及边的存在、方向和条件都必须能够追溯到当前section的unit证据。原文未直接说明但存在必要功能依赖的边，可以标记为LLM推理并待人工复核。基础KG已经足以表达、仅有主题相关性、或无法形成可靠有向判断链的内容不得成卡。

P7C不读取具体题目或参考答案，也不处理跨section桥接。`flow_nodes + flow_edges`是知识正本。只输出严格JSON，不输出Markdown或解释。准确率优先于card数量，但必须完整检查整个section。

## 输入边界

事实证据只能来自`section_text_with_unit_anchors`，且只能引用`allowed_unit_ids`中的unit_id。

`base_kg_section_summary`只用于覆盖审查和判断候选关系是否已被基础KG充分表达，不得作为节点、条件、方向或结果的事实证据。

不得利用或假设任何具体题目、选项、参考答案、其他section内容或跨section关系。不得补造原文没有的主体、情境、动作、条件、阈值、结果或义务。

## 三阶段内部判断

输出前必须按以下顺序完成内部判断，但不要输出判断过程。

### 第一阶段：完整发现候选命题

按自然段落、转折、主体变化、对象变化、条件变化和`base_kg_section_summary`中的CP边界扫描整个section。对每个局部主题尝试写出：

`在条件C下，业务情境/事件/线索/输入/标准A，如何关联到主体S的识别/评估/决策/应对B，并产生结论/义务/控制结果/分支/后续行动D。`

条件C可以为空，但A、S、B和D必须能够由当前section证据支持。不得因为前文已经生成card而忽略后文新的主体、对象、业务线、控制场景或应对链。

### 第二阶段：判断是否为KG增量

基础KG已经能够充分表达：

- 定义、分类、事实和一般规则
- 普通例子或普通案例事实
- 孤立风险指标、红旗或控制措施
- 框架、产品、措施或标准的组成列表
- 一般概念关系、单纯主题相关性和普通机制因果
- CP之间的包含、举例、铺垫、并列、对比和总结

以下结构可能属于P7C增量：

- 明确步骤、职责或交接顺序
- 条件、阈值或例外导向不同判断、分支或行动
- 事件、发现、结论或外部要求触发特定主体的应对
- 识别、评估、决策或执行动作产生具体结论、记录、状态变化、义务、控制结果或后续行动
- 线索或输入在特定判断中被采用，而不只是被列为风险指标
- 标准直接约束具体主体如何行动，或向机构制度、流程传导要求
- 结果触发复核、补充、更新、调优、监控或再次处理
- 案例中实际发生且未被基础KG充分表达的条件、决策、应对、交接或反馈链

单个unit可以成卡，只要其中完整存在上述增量结构；多个unit也不能因为主题相关而被拼成card。普通机制或原因导致后果仍由基础KG承接，只有它实际构成完整程序性或判断性有向结构的一部分时，才可进入P7C。

### 第三阶段：证据化构图

每张card生成前，必须确认：

1. 可以写出“A通过什么关系，在何种条件下（如有），导向B”。
2. 该关系超出基础KG能够充分表达的定义、分类、事实、列表、孤立指标、普通案例或一般知识关系。
3. 该关系能够帮助确认或排除关于顺序、条件、因果、主体职责、义务、应对或适用范围的选项。
4. 每个节点及每条边的存在、方向和条件都能追溯到当前section的unit证据。

任一项不成立则不生成card。`needs_review`不能绕过KG增量门或证据门。

## 显式证据与LLM推理

节点必须是原文明示的对象、情境、动作、判断、结果或义务，节点的`evidence_strength`只能为`explicit`。不得用LLM推理创造入口、处理或出口节点。

边允许两种`evidence_strength`：

- `explicit`：原文明示关系及其方向。
- `functional_dependency`：source与target节点均由原文明示，原文未直接陈述边，但该方向是完成原文明示业务功能所必需的唯一合理连接。它表示“LLM推理、待人工复核”。

`functional_dependency`不得用于推断原文没有的条件、阈值、主体、结果或义务；如果方向存在两种合理解释，不得成边。`condition`必须由原文明示，不能由LLM补造。

## 构图原则

一张card只表达一个局部闭合的程序性或判断性有向结构，并至少包含一个entry、一个process和一个exit。至少存在一条从entry经过process到达exit的主路径。

处理节点必须写明原文支持的具体主体及动作，例如“银行：拒绝接受可疑还贷资金”，不得只写“进行评估”“采取措施”等无主体通用动作。原文使用一般主体时，可以保留“机构”“有关当局”等原有粒度。

保留原文中的if、when、unless、may、should、must、only、not、potentially、depending on等限定词。限定词应进入`label`、`condition`、`source_quote`或`review_notes`。

不得虚构“需要进行评估”“机构希望降低风险”“对象接受审查”等通用入口。不得虚构“风险得到管理”“持续合规义务”“框架建立完成”等通用出口。“降低风险、保持合规、提高有效性”等抽象目的，只有在原文将其明确表述为当前动作产生的具体控制结果时才可作为出口。

案例只能提取案例中实际发生的结构并保留案例限定，不得自动推广为一般规则。

普通红旗由基础KG承接。只有线索被原文明示用于特定识别或判断，或者存在组合条件、阈值、差异化结论或后续应对时，才进入P7C。

普通控制或框架组成由基础KG承接。只有原文说明其适用情境、主体动作、约束、先后、具体结果或反馈机制时，才进入P7C。

多个并行情报来源、线索、标准或组成要素不得按教材叙述顺序串成`PRECEDES`。它们可以通过`REFERENCES`关联到共同处理节点；如果只有并列知识关系，则交给基础KG。

## card_nature

只能使用：`execution`、`assessment`、`risk_indicator`、`control`。

## flow_node

每个节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。

允许类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

EDD、筛查、监控、调优、审查、报告、批准、拒绝等动作必须是process，不得写成standard。`X1_classification`只用于分类或判断结论，不得承载刑罚、冻结或一般后果。

## flow_edge

允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `PRECEDES`：只用于原文明示顺序，或交换source和target会违反必要业务功能的先后。共同出现、教材顺序或“通常如此”不足以成边。
- `REFERENCES`：process指向非时序性的input或standard，表示处理动作参照线索、输入、标准、判断维度或组成要素，不表达先后、产出或条件。
- `PRODUCES`：process产生有证据的exit。相关后果、共同结果或抽象目标不得伪装成产物。
- `DECIDES`：必须由`P3_branch_routing`发出并填写有原文证据的`condition`，用于真实条件分流。
- `FEEDBACK`：结果或事件触发更新、补充、复核、调优、监控或再次处理。

每条边必填：`edge_id, edge_type, source, target, evidence_unit_ids, evidence_strength`。

可选：`relation_type, condition, source_quote, review_status`。

不要输出`qualifier`或`modality`字段；如需表达限定词，写入`label`、`condition`、`source_quote`或`review_notes`。

## relation_type

允许：

`clue_supports_identification, mechanism_explains_risk, identification_leads_to_conclusion, conclusion_triggers_response, branch_condition_routes_path, component_assembles_product, standard_constrains_action, result_handoffs_stage, feedback_requests_completion, cycle_requires_monitoring, standard_transmits_requirement, parallel_alternative_no_sequence`。

`relation_type`回答业务语义，不能根据`edge_type`机械映射。`branch_condition_routes_path`只能用于带`condition`的`DECIDES`边。证据不足时省略`relation_type`，不得硬贴。

## 审核状态

P7C节点只输出`explicit`；边只输出`explicit`或`functional_dependency`。不得在节点或边的`evidence_strength`中输出`needs_review`或`rejected`。

- 所有节点和边均为`explicit`时，card的`review_status`必须为`accepted`。
- 任一边为`functional_dependency`时，card的`review_status`必须为`needs_review`。
- 入口、出口、方向、条件、主体或KG增量价值本身不成立时，不输出该card，不得输出`rejected`卡。

每张card的`review_notes`必填并使用中文，格式为：

`增量命题：A --关系--> B（条件如有）；KG不足：基础KG不能表达什么；选项判断：可确认或排除什么选项；LLM推理：列出functional_dependency边及必要性，若无则写“无”。`

`title`、`label`和`source_quote`可保留英文教材术语或原文关键词，但解释性内容必须使用中文。`source_unit_ids`必须覆盖该card所有节点和边引用的unit_id。不得输出空`flow_nodes`或空`flow_edges`。

## 输出结构

每张card必填：
`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, review_status, review_notes`。

顶层必须输出：
`section_id, section_title, cards, skip_reason`。

没有合格card时输出：
{"section_id":"<section_id>","section_title":"<section_title>","cards":[],"skip_reason":"基础KG已能充分表达，或当前section不存在证据支持的增量程序性或判断性有向结构。"}

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
