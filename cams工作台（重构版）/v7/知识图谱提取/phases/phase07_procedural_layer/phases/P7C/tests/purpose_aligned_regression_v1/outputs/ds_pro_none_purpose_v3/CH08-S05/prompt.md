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

情态和强度属于事实证据的一部分，必须保持原义：`must`不得弱化为“可以”，`should/may/might/could/often/potentially/help`不得强化为必然事实。例如`help mitigate risk`必须写成“有助于缓解风险”，不得写成“风险已被缓解”。

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

基础KG能够把一条规则作为整体知识保存，不代表它已经表达了规则内部的条件、主体、动作、判断和结果之间的有向结构。遇到`if/when/based on/must/should not/requires`等规则时，必须继续检查其内部是否存在可支持选项判断的P7C增量命题，不能仅以“KG可以保存该规则”为由跳过。

### 正反边界示例

以下属于应进入P7C的结构模式，但仍必须以当前section实际证据为准：

- “机构必须基于风险偏好调整交易监控、KYC审查并升级”：风险偏好约束特定主体的具体控制动作，并产生监控/KYC配置变化或升级义务。
- “通常按25%识别UBO；高风险时阈值可能降至10%或5%；没有自然人受益所有人时识别并核实控制人”：阈值和例外条件导向差异化识别与分类路径。
- “如果银行知道或怀疑还贷资金非法，则不应接受”：明确条件导向特定主体的禁止性应对及资金不被接受的状态。
- “退出超出风险容忍度的客户且存在贷款余额时，核销通常需要充分理由和批准”：退出情境和贷款余额共同约束核销决策及批准要求；它与“可疑还贷不得接受”是独立处置链，应分别检查。
- “金融机构对SPV/PIV实施EDD，识别UBO并了解真实目的，这有助于缓解潜在金融犯罪风险”：具体主体、控制动作、识别结果和带限定强度的控制效果形成局部链。

以下通常只由基础KG承接，不得单独成卡：

- “调查环境犯罪可能受到被贿赂官员阻碍”：只有普通机制或困难说明，没有完整的主体处置或判断结构。
- “犯罪分子使用BMPE转换资金并掩饰来源”：只有普通案例机制，没有条件、职责、判断、应对或交接结构。
- “犯罪组织通过空壳公司虚增合同进行placement，再与共谋账户进行layering”：仍是基础KG可保存的普通犯罪方法和案例机制，不因出现先后动词就自动成为P7C card。除非当前section进一步明示该机制如何触发机构或当局的识别、判断或应对。
- “某项措施维护合规诚信、降低风险”：只有抽象目的，不得补造成持续义务或受控状态。

### 第三阶段：证据化构图

每张card生成前，必须确认：

1. 可以写出“A通过什么关系，在何种条件下（如有），导向B”。
2. 该关系超出基础KG能够充分表达的定义、分类、事实、列表、孤立指标、普通案例或一般知识关系。
3. 该关系能够帮助确认或排除关于顺序、条件、因果、主体职责、义务、应对或适用范围的选项。
4. 每个节点及每条边的存在、方向和条件都能追溯到当前section的unit证据。

任一项不成立则不生成card。`needs_review`不能绕过KG增量门或证据门。

完成初稿后必须再次逐个检查包含`if, when, unless, based on, must, should, should not, require, approval, escalate, identify, monitor, review`等表达的unit。每个候选unit都要确认：已进入某张card，或确实仅属基础KG。不得在抽出第一条合格链后停止覆盖审查；同一section中彼此独立的条件或处置链应分别成卡，不能遗漏，也不能强行合并。

## 显式证据与LLM推理

节点必须是原文明示的对象、情境、动作、判断、结果或义务，节点的`evidence_strength`只能为`explicit`。不得用LLM推理创造入口、处理或出口节点。

边允许两种`evidence_strength`：

- `explicit`：原文明示关系及其方向。
- `functional_dependency`：source与target节点均由原文明示，原文未直接陈述边，但该方向是完成原文明示业务功能所必需的唯一合理连接。它表示“LLM推理、待人工复核”。

`functional_dependency`不得用于推断原文没有的条件、阈值、主体、结果或义务；如果方向存在两种合理解释，不得成边。`condition`必须由原文明示，不能由LLM补造。

## 构图原则

一张card只表达一个局部闭合的程序性或判断性有向结构，并至少包含一个entry、一个process和一个exit。至少存在一条从entry经过process到达exit的主路径。

出口D不要求是物理产物，也可以是原文明示的分类结论、禁止或允许状态、配置变化、识别结果、批准/拒绝状态、交接、义务或后续行动。同一unit中的一个动词短语可以同时提供处理动作及其直接结果，例如“银行不接受资金”可表示为银行的拒绝动作和资金未被接受的状态；这不是补造节点，但不得把动作的抽象目的当作结果。

处理节点必须写明原文支持的具体主体及动作，例如“银行：拒绝接受可疑还贷资金”，不得只写“进行评估”“采取措施”等无主体通用动作。原文使用一般主体时，可以保留“机构”“有关当局”等原有粒度。

保留原文中的if、when、unless、may、should、must、only、not、potentially、depending on等限定词。限定词应进入`label`、`condition`、`source_quote`或`review_notes`。

不得虚构“需要进行评估”“机构希望降低风险”“对象接受审查”等通用入口。不得虚构“风险得到管理”“持续合规义务”“框架建立完成”等通用出口。“降低风险、保持合规、提高有效性”等抽象目的，只有在原文将其明确表述为当前动作产生的具体控制结果时才可作为出口。

案例只能提取案例中实际发生的结构并保留案例限定，不得自动推广为一般规则。

普通红旗由基础KG承接。只有线索被原文明示用于特定识别或判断，或者存在组合条件、阈值、差异化结论或后续应对时，才进入P7C。

普通控制或框架组成由基础KG承接。只有原文说明其适用情境、主体动作、约束、先后、具体结果或反馈机制时，才进入P7C。

多个并行情报来源、线索、标准或组成要素不得按教材叙述顺序串成`PRECEDES`。它们可以通过`REFERENCES`关联到共同处理节点；如果只有并列知识关系，则交给基础KG。

实际触发处理的对象、事件或发现应建为entry，并通过`PRECEDES`进入process。仅被处理动作参照的线索、输入或标准应建为auxiliary，并由process通过`REFERENCES`指向它。不得创建“entry节点作为REFERENCES目标”或“entry节点通过REFERENCES进入process”的结构。

调查、审计或评估可以产生“发现、分类、报告或结论”，不能被写成产生其所揭示的既存违法行为、风险状态或控制缺陷。例如审计揭示长期未被发现的腐败，只能产生“发现控制缺陷/识别腐败”的结论，不能产生“腐败长期未被发现”这一既存状态。

相邻句子中的执法措施和司法结果不自动形成`PRECEDES`或`PRODUCES`。冻结、查封、起诉、定罪、监禁和罚款之间只有在原文明示先后、触发或产出关系时才能连接；否则应保留为共同上游调查或执法行动的并列结果，或者拆卡/省略关系。

### 节点级构图示例

“机构必须基于风险偏好调整交易监控、KYC审查并升级”可构为：

```text
entry E3_state_threshold：机构的风险偏好要求
process P8_constrained_action：机构基于风险偏好调整交易监控、KYC审查并升级
exit X5_config_change或X7_continuing_obligation：监控/KYC配置按风险偏好调整，或形成按风险升级的义务
entry --PRECEDES--> process --PRODUCES--> exit
```

不得因风险偏好也可作为standard而省略主路径；如另建standard辅助节点，则由process通过`REFERENCES`指向standard。

“不存在自然人受益所有人时，应识别并核实控制人或名义受益所有人”可构为单一条件链：

```text
entry E6_change_exception：不存在自然人受益所有人
process P2_execution：机构识别并核实控制人或名义受益所有人
exit X1_classification：控制人或名义受益所有人被识别
```

原文只明示例外路径时，不得反向补造“存在自然人受益所有人”的另一分支。`P3_branch_routing + DECIDES`只用于原文明示至少两条不同路径的真实分流；只有单一条件应对时，使用条件entry进入process。

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
