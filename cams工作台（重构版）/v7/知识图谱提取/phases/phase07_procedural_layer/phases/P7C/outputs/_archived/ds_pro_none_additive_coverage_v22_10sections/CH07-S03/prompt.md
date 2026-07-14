# P7C Section-Local Incremental Directed Card Extraction Prompt v3

## 角色与目的

你是P7C局部程序性与判断性有向结构提取器。

P7C的目的，是在不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标和一般知识关系的前提下，从单个section中增量提取对CAMS题目选项判断有用的局部程序性或判断性有向结构，即把原文中的业务情境、事件、线索、输入或标准，如何关联到特定主体的识别、评估、决策或应对，以及原文明示的独立结论、记录、状态变化、控制效果、分支或后续行动，表示为保留原文限定词的`flow_nodes + flow_edges`。义务应体现为带`must/should`等情态的process；没有独立结果时允许开放关系。

每个节点以及边的存在、方向和条件都必须能够追溯到当前section的unit证据。原文未直接说明但存在必要功能依赖的边，可以标记为LLM推理并待人工复核。基础KG已经足以表达、仅有主题相关性、或无法形成可靠有向判断链的内容不得成卡。

P7C不读取具体题目或参考答案，也不处理跨section桥接。`flow_nodes + flow_edges`是知识正本。只输出严格JSON，不输出Markdown或解释。准确率优先于card数量，但必须完整检查整个section。

## 输入边界

事实证据只能来自`section_text_with_unit_anchors`，且只能引用`allowed_unit_ids`中的unit_id。

`base_kg_section_summary`只用于覆盖审查和判断候选关系是否已被基础KG充分表达，不得作为节点、条件、方向或结果的事实证据。

不得利用或假设任何具体题目、选项、参考答案、其他section内容或跨section关系。不得补造原文没有的主体、情境、动作、条件、阈值、结果或义务。

情态和强度属于事实证据的一部分，必须保持原义：`must`不得弱化为“可以”，`should/may/might/could/often/potentially/help`不得强化为必然事实。例如`help mitigate risk`必须写成“有助于缓解风险”，不得写成“风险已被缓解”。`must/shall/is required to`表达应履行的义务，不等于动作已经完成；除非原文明示完成或结果已经发生，不得据此输出“已调整”“已建立”“已降低”等完成状态。

`must`本身也不等于“持续、定期、永久或反复”。只有原文存在`ongoing/continuous/periodic/always/remain`等直接证据，或当前义务的持续性由原文明确限定时，节点label才可以增加相应限定。`escalate/escalation`默认保留为“升级处理/升级处置”或英文原词，不得翻译为“上报/报告”；只有原文明示`report/notify/file/refer`及其报告或移交对象时，才能写成上报、报告或移交。

## 三阶段内部判断

输出前必须按以下顺序完成判断。不要输出长篇推理过程，但必须把候选覆盖结论写入顶层`coverage_audit`，用于检查信息遗漏；`coverage_audit`只是诊断元数据，不是知识正本。

### 第一阶段：完整发现候选命题

按自然段落、转折、主体变化、对象变化、条件变化和`base_kg_section_summary`中的CP边界扫描整个section。对每个局部主题尝试写出：

`在条件C下，业务情境/事件/线索/输入/标准A，如何关联到主体S带原文情态的识别/评估/决策/应对B，并在有独立原文结果时产生结论/记录/状态变化/控制效果/分支/后续行动D。`

条件C可以为空，A、S和B必须能够由当前section证据支持；D只有在原文存在独立结果时才填写。没有独立结果时，允许保留开放式局部关系，不得为了闭合流程虚构D。不得因为前文已经生成card而忽略后文新的主体、对象、业务线、控制场景或应对链。

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
- 识别、评估、决策或执行动作产生与该动作语义独立的具体结论、记录、状态变化、控制结果或后续行动
- 线索或输入在特定判断中被采用，而不只是被列为风险指标
- 标准直接约束具体主体如何行动，或向机构制度、流程传导要求
- 结果触发复核、补充、更新、调优、监控或再次处理
- 案例中实际发生且未被基础KG充分表达的条件、决策、应对、交接或反馈链

单个unit可以成卡，只要其中完整存在上述增量结构；多个unit也不能因为主题相关而被拼成card。普通机制或原因导致后果仍由基础KG承接，只有它实际构成完整程序性或判断性有向结构的一部分时，才可进入P7C。

基础KG能够把一条规则作为整体知识保存，不代表它已经表达了规则内部的条件、主体、动作、判断和结果之间的有向结构。遇到`if/when/based on/must/should not/requires`等规则时，必须继续检查其内部是否存在可支持选项判断的P7C增量命题，不能仅以“KG可以保存该规则”为由跳过。

结构复杂度不是成卡门槛。只要候选命题内部明确存在“情境/条件/标准/输入如何关联到特定主体的动作或判断”，并满足证据和选项判断要求，即使它只有一个unit、一条边、没有独立结果、没有分支或反馈，也必须判为`p7c_card`。只有原文明示独立结果时才增加出口。不得使用“规则简单”“只是条件-动作链”“没有分支或反馈”“KG可把整条规则作为事实保存”作为`kg_only`理由。

同样不得使用“纯义务陈述”“没有复杂条件”“没有复杂步骤”作为`kg_only`理由。监管要求、风险偏好或既有分类状态如果明确约束特定主体的识别、标准选择或分类维持，即使没有独立出口，也可以作为开放式P7C局部关系；复杂度和是否闭环不影响是否成卡。

`kg_only`只能表示基础KG已能表达候选的全部有效结构，例如纯定义、纯阈值事实、普通案例机制、孤立指标或一般知识关系；如果基础KG只能保存整句话，却不能表达句内的主体、方向、条件或动作结果关系，则仍属于P7C增量。

### 正反边界示例

以下属于应进入P7C的结构模式，但仍必须以当前section实际证据为准：

- “机构必须基于风险偏好调整交易监控、KYC审查并升级”：将“机构必须调整……”建为带情态的process，将风险偏好建为standard，并用`process --REFERENCES--> standard`表达约束；不得补造配置已变化或升级义务出口。
- “机构必须遵守当地监管要求识别PEP”：将“机构必须识别PEP”建为带情态的process，将当地监管要求建为standard并由process通过`REFERENCES`指向；不得以“纯义务、没有复杂步骤”为由交给KG，也不得补造识别义务或“持续识别”出口。
- “机构可根据风险偏好选择执行更高的PEP标准”：风险偏好条件导向机构可选的标准配置变化，属于P7C；必须保留`may choose`，不得写成必然提高。
- “部分机构采用‘一旦是PEP，永远是PEP’，即使个人已卸任，因为其仍可能保持影响力”：卸任变化和可能保留影响力导向特定机构维持PEP分类，属于条件化判断；必须保留“部分机构”和“可能”。
- “通常按25%识别UBO；高风险时阈值可能降至10%或5%；没有自然人受益所有人时识别并核实控制人”：阈值和例外条件导向差异化识别与分类路径。
- “如果银行知道或怀疑还贷资金非法，则不应接受”：条件entry通过带`condition`的`PRECEDES`导向“银行不应接受”的process；不得再补造“资金不被接受”的同义状态出口。
- “退出超出风险容忍度的客户且存在贷款余额时，核销通常需要充分理由和批准”：将“银行核销贷款”建为process，将“通常需要充分理由和批准”建为standard/input，由process通过带适用条件的`REFERENCES`指向；不得写成“核销`PRODUCES`批准要求”。
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

任一项不成立则不生成card。`derivation=llm_inference`不能绕过KG增量门或证据门。

完成初稿后必须再次逐个检查包含`if, when, unless, based on, must, should, should not, require, approval, escalate, identify, monitor, review`等表达的unit。每个候选unit都要确认：已进入某张card，或确实仅属基础KG。不得在抽出第一条合格链后停止覆盖审查；同一section中彼此独立的条件或处置链应分别成卡，不能遗漏，也不能强行合并。

相邻或邻近unit共同构成同一条“条件/变化/输入/标准 → 主体动作或判断”命题时，必须记录为一个完整候选，`unit_ids`覆盖关系两端。不得把前提单独记为`kg_only`风险事实、再把应对单独记为`kg_only`一般义务，从而丢失二者之间的有向关系。

每个候选命题必须在`coverage_audit`中记录：

- `candidate_id`：当前section内唯一ID。
- `unit_ids`：支持该候选判断的当前section unit。
- `proposition`：一句话概括候选有向命题。
- `decision`：只能为`p7c_card`或`kg_only`。
- `card_id`：`p7c_card`时填写对应card_id；`kg_only`时为`null`。
- `reason`：使用中文简述为何属于P7C增量或为何基础KG已经足够。

每张输出card必须被至少一条`decision=p7c_card`的记录引用。发现候选但决定交给KG时也必须保留审计记录，不能通过不记录候选来规避覆盖检查。

## 显式证据与LLM推理

节点必须是原文明示的对象、情境、动作、判断、结果或义务，节点的`evidence_strength`只能为`explicit`。不得用LLM推理创造入口、处理或出口节点。

边允许两种`derivation`：

- `explicit_text`：原文明示关系及其方向。
- `llm_inference`：source与target节点均由原文明示，原文未直接陈述边，但该方向是完成原文明示业务功能所必需的唯一合理连接。它表示“LLM推理”，不是最终审核结果。

`llm_inference`不得用于推断原文没有的条件、阈值、主体、结果或义务；如果方向存在两种合理解释，不得成边。`condition`必须由原文明示，不能由LLM补造。

## 构图原则

一张card只表达一个局部程序性或判断性有向结构。只有原文明示关系起点、处理动作和独立结果时，才构成entry→process→exit主路径；缺少其中任一角色时可以输出开放式局部关系，不得补造entry、process或exit来闭合图。

entry表示当前局部结构的关系起点，不要求一定是时间事件。真实事件、对象到达/提交/进入某阶段、阈值越界或发现触发后续动作时才建entry。静态适用对象、审查范围、分析材料或判断维度不是entry，应建为auxiliary `input`并由process通过`REFERENCES`指向。被process参照并约束动作的监管要求、政策基准或风险偏好建为auxiliary `standard`；不得为了形成主路径把被参照的对象、输入或标准强行建成entry。

出口D不要求是物理产物，也可以是原文明示的分类结论、配置变化、识别结果、批准/拒绝决定、交接或后续行动，但必须与process是两个独立语义事实。不得把同一个谓词主动式和被动式各建一个节点，例如“银行不接受资金”与“资金未被接受”、“机构检测到非法活动”与“非法活动被检测到”；这种同义改写不能形成`PRODUCES`。规范性语句只说明“主体必须/应当执行动作”时，把情态保留在process label中，不再补造X7义务出口。若原文说明动作“需要理由、批准或遵循某项要求”，应把该要求建为auxiliary `standard`或`input`并由process通过`REFERENCES`指向，不得写成“动作`PRODUCES`要求/义务”。

处理节点必须写明原文支持的具体主体及动作，例如“银行：拒绝接受可疑还贷资金”，不得只写“进行评估”“采取措施”等无主体通用动作。原文使用一般主体时，可以保留“机构”“有关当局”等原有粒度。

保留原文中的if、when、unless、may、should、must、only、not、potentially、depending on等限定词。限定词应进入`label`、`condition`、`source_quote`或`review_notes`。

不得虚构“需要进行评估”“机构希望降低风险”“对象接受审查”等通用入口。不得虚构“风险得到管理”“持续合规义务”“框架建立完成”等通用出口。“降低风险、保持合规、提高有效性”等抽象目的，只有在原文将其明确表述为当前动作产生的具体控制结果时才可作为出口。

案例只能提取案例中实际发生的结构并保留案例限定，不得自动推广为一般规则。

普通红旗由基础KG承接。只有线索被原文明示用于特定识别或判断，或者存在组合条件、阈值、差异化结论或后续应对时，才进入P7C。

普通控制或框架组成由基础KG承接。只有原文说明其适用情境、主体动作、约束、先后、具体结果或反馈机制时，才进入P7C。

多个并行情报来源、线索、标准或组成要素不得按教材叙述顺序串成`PRECEDES`。它们可以通过`REFERENCES`关联到共同处理节点；如果只有并列知识关系，则交给基础KG。

实际到达、提交、移交或状态变化并触发处理的对象、事件或发现应建为entry，并通过`PRECEDES`进入process。只说明“对某类对象执行动作”时，该对象是适用范围而非先后事件；仅被处理动作参照的对象、线索、输入或标准应建为auxiliary，并由process通过`REFERENCES`指向它。不得仅因对象在语法上先出现就建立`E2_object_entry --PRECEDES--> process`。

单一路径的`if/when/unless A，则B`不是分支，不使用`DECIDES`；A可以作为条件entry通过`PRECEDES`进入B，并在edge的`condition`中逐字保留条件。这里的`PRECEDES`表示逻辑前提，未必表示钟表式先后。若条件只限定某项input/standard何时适用于process，可以直接写在`REFERENCES.condition`中而不另建entry；这仍是适用范围限定，不是条件分支。只有原文明示至少两条不同路径时才使用`P3_branch_routing + DECIDES`。

调查、审计或评估可以产生“发现、分类、报告或结论”，不能被写成产生其所揭示的既存违法行为、风险状态或控制缺陷。例如审计揭示长期未被发现的腐败，只能产生“发现控制缺陷/识别腐败”的结论，不能产生“腐败长期未被发现”这一既存状态。

相邻句子中的执法措施和司法结果不自动形成`PRECEDES`或`PRODUCES`。冻结、查封、起诉、定罪、监禁和罚款之间只有在原文明示先后、触发或产出关系时才能连接；否则应保留为共同上游调查或执法行动的并列结果，或者拆卡/省略关系。

### 节点级构图示例

“机构必须基于风险偏好调整交易监控、KYC审查并升级”可构为开放式约束关系：

```text
process P8_constrained_action：机构必须调整交易监控、KYC审查并升级处理
standard：机构的风险偏好
process --REFERENCES--> standard（relation_type=standard_constrains_action）
```

这里原文只有规范性要求，所以不得写成“监控/KYC配置已调整”，不得补造X7义务出口，也不得把`escalate`写成“上报”。

“不存在自然人受益所有人时，应识别并核实控制人或名义受益所有人”可构为单一条件链：

```text
entry E6_change_exception：不存在自然人受益所有人
process P2_execution：机构识别并核实控制人或名义受益所有人
entry --PRECEDES--> process（condition=不存在自然人受益所有人）
```

原文只明示例外路径时，不得反向补造“存在自然人受益所有人”的另一分支。`P3_branch_routing + DECIDES`只用于原文明示至少两条不同路径的真实分流；只有单一条件应对时，使用条件entry进入process。

“通常按25%识别受益所有权，机构按风险法设定适当阈值，高风险客户可能降至10%或5%，识别UBO时同时考虑直接和间接持股”不是普通阈值列表。它可构为判断卡：

```text
auxiliary input：待审查对象的直接和间接持股信息
process P1_assessment：机构合计直接与间接持股，并按适用风险阈值判断UBO
auxiliary standard：通常25%，风险法下高风险客户可能为10%或5%
exit X1_classification：依据适用阈值形成UBO识别结论
process --REFERENCES--> input
process --REFERENCES--> standard
process --PRODUCES--> exit
```

必须保留`most jurisdictions, risk-based, might, could`等限定，不得把10%或5%写成所有高风险客户的固定阈值。

“延期起诉协议要求全面整改，银行因此加强中央监督和合规职能、限制地方业务自主权并减少高风险地区敞口”属于外部命令触发组织纠正措施及配置变化的P7C增量链，不得因为它出现在历史案例中而整段交给KG。声誉损害可以是同一上游事件的并列后果，但不得作为整改动作的触发原因。

案例中，金融机构、FIU、执法机关或监管机关实际执行的检测、综合分析、升级、监控、冻结、查封或整改，可以形成局部P7C card；犯罪分子的洗钱手法本身仍通常由KG承接。应将有证据的局部制度响应分别成卡，不能为了避免强行单链而把全部响应跳过。例如：

```text
FIU综合银行SAR和跨境活动 -> 形成红旗发现
FIU升级案件 -> 执法机构开展定向监控
执法机构协调资产冻结 -> 查封数字钱包并瓦解相关公司
```

上述三条只有在当前section分别明示时才可提取，不能再把它们自动连接到定罪、监禁或罚款。

当原文说某项重大决定`often requires justification and approval`时，process应表达“主体评估或作出该项决定”，auxiliary standard/input表达“通常需要理由和批准”，并使用`process --REFERENCES--> standard/input`。不得把审批要求写成出口，也不得把尚在考虑的动作写成已经执行完成。

“全球组织通常以母国监管政策为基础标准，并根据各东道国法律调整”属于开放式约束关系：将“全球组织通常调整合规政策”建为process，将母国监管政策和东道国法律分别建为standard，由process通过`REFERENCES`指向。不得把静态政策标准建为`E7_external_command`，也不得把“调整政策”与“政策已适配”拆成同义process和出口；必须保留`typically`的通常性限定。

## card_nature

只能使用：`execution`、`assessment`、`risk_indicator`、`control`。

## flow_node

每个节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。

允许类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

EDD、筛查、监控、调优、审查、报告、批准、拒绝等动作必须是process，不得写成standard。`X1_classification`只用于分类或判断结论，不得承载刑罚、冻结或一般后果。`X7_continuing_obligation`只用于原文明示某个上游动作、决定或协议新建立了与该process语义独立的持续义务；“主体必须/应当执行某动作”本身只写成带情态的process，不能再复制成X7。

## flow_edge

允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `PRECEDES`：只用于原文明示顺序、单一条件/触发的逻辑前提，或交换source和target会违反必要业务功能的先后。共同出现、教材顺序或“通常如此”不足以成边。
- `REFERENCES`：process指向非时序性的input或standard，表示处理动作参照线索、输入、标准、判断维度或组成要素，不表达先后、产出或条件分支。可选`condition`只能限定该参照关系的适用范围。
- `PRODUCES`：process产生有证据的exit。相关后果、共同结果或抽象目标不得伪装成产物。
- `DECIDES`：必须由`P3_branch_routing`发出并填写有原文证据的`condition`，用于真实条件分流。
- `FEEDBACK`：结果或事件触发更新、补充、复核、调优、监控或再次处理。

每条边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。

可选：`relation_type, condition, source_quote`。新产物不得输出边级`evidence_strength`或`review_status`；旧字段仅由兼容校验器读取，不属于当前输出合同。

不要输出`qualifier`或`modality`字段；如需表达限定词，写入`label`、`condition`、`source_quote`或`review_notes`。

## relation_type

允许：

`clue_supports_identification, mechanism_explains_risk, identification_leads_to_conclusion, conclusion_triggers_response, branch_condition_routes_path, component_assembles_product, standard_constrains_action, result_handoffs_stage, feedback_requests_completion, cycle_requires_monitoring, standard_transmits_requirement, parallel_alternative_no_sequence`。

`relation_type`回答业务语义，不能根据`edge_type`机械映射。`branch_condition_routes_path`只能用于带`condition`的`DECIDES`边。证据不足时省略`relation_type`，不得硬贴。

默认省略`relation_type`。只有业务语义和端点角色完全符合下列约束时才填写；不要创造允许列表之外的新名称：

- `clue_supports_identification`：只能用于`REFERENCES`，process指向作为识别线索的`input`。
- `standard_constrains_action`或`standard_transmits_requirement`：只能用于`REFERENCES`，process指向`standard`。
- `component_assembles_product`：只能用于`REFERENCES`，process指向作为组成要素的`input`。
- `identification_leads_to_conclusion`：只能用于`PRODUCES`，识别/评估process产生`X1_classification`结论。
- `conclusion_triggers_response`：只能表示已有发现或分类触发后续process，不能用于“动作产生结果”。
- `branch_condition_routes_path`：只能用于`DECIDES`。
- `feedback_requests_completion`：只能用于`FEEDBACK`。
- `result_handoffs_stage`：只能表示exit交接到后续process的`PRECEDES`。
- `mechanism_explains_risk`：只能用于合格P7C行动链内部的`PRODUCES`，表示process明示产生或解释独立风险结果；普通犯罪机制或一般因果仍由KG承接。
- `cycle_requires_monitoring`：只能用于时间周期或复核周期entry通过`PRECEDES`触发`P7_monitoring`，且周期与监控要求均有原文证据。
- `parallel_alternative_no_sequence`：只能用于process通过`REFERENCES`关联作为并列替代输入的auxiliary；如果只是普通并列列表而没有共同process，交给KG且不成边。

如果一条边只是普通顺序、动作产出、对象进入处理或条件触发，而上面没有完全匹配的语义类型，省略`relation_type`是正确结果。

### 边输出前反事实检查

逐边检查后才能输出：

1. `PRECEDES`：必须能说明它是时间顺序、单一条件/触发、交接或不可交换的必要功能先后中的哪一种；单一条件/触发必须填写`condition`。若source只是静态适用对象或材料，改为process指向input的`REFERENCES`。
2. `PRODUCES`：将source和target合并成一句话后，如果没有损失独立事实，说明二者只是同义改写，删除target和该边。若target是执行source所需的理由、批准、标准或义务，改为process指向standard/input的`REFERENCES`。
3. `REFERENCES`：交换方向后应当不符合“处理动作参照输入/标准”的读法；若原文表达的是真实步骤、产出、条件分流或反馈，不得用`REFERENCES`压扁。

## 候选声明（不是最终审核）

P7C节点的`evidence_strength`只能为`explicit`。边的`derivation`只能为`explicit_text`或`llm_inference`。不要输出`pending/accepted/rejected`；最终审核状态由P7D单独保存。

- `llm_inference`只说明边依赖必要功能推理，不等于P7D已经接受或拒绝。
- 入口、方向、条件、主体或KG增量价值本身不成立时，不输出该card；没有独立出口不是跳过理由。

每张card的`review_notes`必填并使用中文，格式为：

`增量命题：A --关系--> B（条件如有）；KG不足：基础KG不能表达什么；选项判断：可确认或排除什么选项；LLM推理：列出derivation=llm_inference的边及必要性，若无则写“无”。`

`title`、`label`和`source_quote`可保留英文教材术语或原文关键词，但解释性内容必须使用中文。`source_unit_ids`必须覆盖该card所有节点和边引用的unit_id。不得输出空`flow_nodes`或空`flow_edges`。

## 输出结构

每张card必填：
`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。`candidate_status`固定为`candidate`，不是P7D审核状态。

顶层必须输出：
`section_id, section_title, coverage_audit, cards, skip_reason`。

顶层结构：

```json
{
  "section_id": "<section_id>",
  "section_title": "<section_title>",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": ["<unit_id>"],
      "proposition": "<候选有向命题>",
      "decision": "p7c_card",
      "card_id": "p7card_<section_id>_001",
      "reason": "<中文增量或KG边界说明>"
    }
  ],
  "cards": [],
  "skip_reason": null
}
```

没有合格card时也必须保留已发现候选的`coverage_audit`记录，并将其`decision`写为`kg_only`；只有完整扫描后确实没有任何候选命题时，`coverage_audit`才可以为空。例如：

```json
{
  "section_id": "<section_id>",
  "section_title": "<section_title>",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": ["<unit_id>"],
      "proposition": "<候选命题>",
      "decision": "kg_only",
      "card_id": null,
      "reason": "<中文KG边界说明>"
    }
  ],
  "cards": [],
  "skip_reason": "基础KG已能充分表达，或当前section不存在证据支持的增量程序性或判断性有向结构。"
}
```

## 当前section

section_id: `CH07-S03`

section_title: `Money laundering risks associated with retail and commercial banking > Credit-related product risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "提前还贷作为洗钱手段",
      "title_en": "Early Loan Repayment as a Money Laundering Method",
      "covered_units": [
        {
          "unit_id": "v7u_N000552",
          "unit_type": "risk_indicator",
          "kg_role": "describes_process"
        }
      ]
    },
    {
      "title_zh": "关闭有未偿信贷账户的挑战",
      "title_en": "Challenges in Closing Accounts with Outstanding Credit Balances",
      "covered_units": [
        {
          "unit_id": "v7u_N000554",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000555",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000556",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000553",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "提前还贷作为洗钱手段",
      "target_title": "关闭有未偿信贷账户的挑战",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000546|546] Credit-related products are fundamental to customer propositions in retail and commercial banking.
ZH: 信贷相关产品是零售和商业银行客户服务的基础

[v7u_N000547|547] Lending products, a subset of credit-related products, include personal loans, home ownership finance, and secured and unsecured loans.
ZH: 贷款产品包括个人贷款、住房融资及有担保和无担保贷款

[v7u_N000548|548] Personal loans help banks build customer relationships, while home ownership finance and secured loans can be a significant source of revenue and capital, respectively.
ZH: 个人贷款有助于建立客户关系，住房融资和有担保贷款分别是重要的收入和资本来源

[v7u_N000549|549] They are essential financial services that enable individuals and businesses to achieve their goals, drive economic growth, and promote financial stability.
ZH: 信贷相关产品是促进经济增长和金融稳定的基本金融服务

[v7u_N000550|550] Secured and unsecured loans are crucial for businesses, offering the necessary capital to expand operations, invest in new projects, and manage cash flow effectively.
ZH: 有担保和无担保贷款为企业扩张、投资和现金流管理提供必要资本

[v7u_N000551|551] However, credit-related products also present substantial money laundering risks.
ZH: 信贷相关产品也带来重大的洗钱风险

[v7u_N000552|552] Early loan repayment is one method used by criminals to disguise the origin of illicit funds. By repaying loans ahead of schedule, criminals can convert illegal proceeds into ostensibly legitimate funds. This tactic complicates the detection of suspicious activity, as early repayments do not inherently indicate wrongdoing and can often be viewed as a sign of financial health.
ZH: 提前还贷是犯罪分子将非法资金伪装为合法资金的手段

[v7u_N000553|553] Banks often face significant challenges when attempting to close customer accounts due to money laundering concerns, while the customer still owes money on credit-related products. One of the primary difficulties is the potential need to write off the loan balance, which creates a financial loss for the bank. This situation can lead to the following complications:
ZH: 因洗钱担忧关闭客户账户时，若客户仍有贷款余额，银行面临财务损失等挑战

[v7u_N000554|554] Recovery of funds: If the bank knows or suspects the customer is using illicit funds to repay the loan, the risk of default becomes a secondary risk to manage. The bank should not accept funds for the purposes of loan
ZH: 若银行知道或怀疑客户使用非法资金还贷，不应接受该资金用于还贷

[v7u_N000555|555] Risk appetite: When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval.
ZH: 退出超出风险容忍度的客户关系时，贷款余额使核销成为重大财务决策

[v7u_N000556|556] Reputational risk: Failure to effectively manage these challenges can damage the bank's reputation and erode trust with regulators and customers, impacting long-term business operations and compliance standing.
ZH: 未能有效管理这些挑战会损害银行声誉并削弱监管机构和客户的信任
```

allowed_unit_ids:

```json
[
  "v7u_N000546",
  "v7u_N000547",
  "v7u_N000548",
  "v7u_N000549",
  "v7u_N000550",
  "v7u_N000551",
  "v7u_N000552",
  "v7u_N000553",
  "v7u_N000554",
  "v7u_N000555",
  "v7u_N000556"
]
```
