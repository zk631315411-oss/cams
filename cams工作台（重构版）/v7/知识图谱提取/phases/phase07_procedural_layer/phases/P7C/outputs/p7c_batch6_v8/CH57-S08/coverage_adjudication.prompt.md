# P7C Section-Local Additive Coverage Review Prompt v3

## 角色

你是P7C section级增量完整性审查器。首次抽取器已经输出候选命题和候选card，这些card尚未经过P7D正式结构校验和边级审核。首次结果可能出现三类问题：把P7C关系误判为`kg_only`、把同一关系的前提和应对拆到不同候选、或在已有card中漏画节点和边。

你的任务是在完整检查当前section后输出只增式JSON补丁。准确率仍然重要，但P7C是候选层，允许把有充分当前section证据的边交给P7D继续审核。重点是确保基础KG无法表达的条件、方向、主体动作或独立结果都进入候选。

`original_json`提供本次无记忆API调用所需的完整首次抽取上下文。Runner只执行受保护的追加操作——不修改任何已有card、节点或边；只追加新内容。输出严格JSON。

## P7C目的与KG边界

P7C不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标、一般规则、普通机制因果和组成关系。P7C增量表达：业务情境、事件、线索、输入或标准如何关联到特定主体带原文情态的识别、评估、决策或应对，以及原文明示的独立结论、记录、状态变化、控制效果、分支或后续行动。

基础KG能保存整句话或分别保存两个知识点，不代表它已经表达句内或句间的条件、主体、方向、动作约束和独立结果。没有独立结果时允许开放式局部关系。

P7C不读取题目或参考答案，不处理跨section桥接。`section_text_with_unit_anchors`是唯一事实证据；`base_kg_section_summary`只用于去重。所有新增证据只能引用`allowed_unit_ids`。

## 核心任务（按优先级执行）

### 第一优先：独立全量重扫描

**无论`review_target_candidate_ids`是否为空，必须完整扫描整个section。** 按自然段落、转折、主体、对象和条件变化重新阅读原文，检查是否存在遗漏的P7C关系——包括首次抽取完全没有登记的命题。

重点检查：
- `if, when, unless, even if, based on, require, must, should, may, monitor, identify, review, approval, escalate, trigger, result in, help`等表达
- 相邻或邻近unit分别给出条件/变化与动作/应对，首次却拆成两个`kg_only`候选或完全未登记
- 输入、线索、判断维度或标准被特定主体用于识别、评估、阈值选择或处置
- 动作产生语义独立的结论、记录、状态变化或带原文限定的控制效果
- 已有card覆盖了主题，但遗漏后文的新对象、条件、结果或应对

允许跨越首次候选边界，允许合并多个候选的unit，也允许使用首次候选完全未登记的当前section unit。所有证据只从当前section的allowed_unit_ids中提取。

`review_target_candidate_ids`为空时，本轮仅执行全量重扫描和已有card图完整性检查，直接输出扫描发现的new_candidates/new_cards/card_supplements。

### 第二优先：复核原`kg_only`候选（如有）

先建立内部覆盖映射：逐个按`candidate_id`从`original_json.coverage_audit`精确定位候选，再把其`proposition + unit_ids`与每张已有card的节点、边和条件作语义比较。按candidate ID精确匹配，不按数组位置或相邻主题猜测。

已有card已经表达同一P7C有向命题时，该关系属于`duplicate`，不新建card或supplement。候选中剩余的定义、数值、例子或一般规则若可由KG承接，也不重新组合成”更完整”的大流程。Coverage只补真正遗漏的P7C关系，不生成比原文或首次候选更丰富的替代方案。

### 第二优先：复核原`kg_only`候选（如有）

对`review_target_candidate_ids`中的每个候选逐一裁决。可以保持`kg_only`，也可以将其关联到新增card或已有card的补充内容。

（全量重扫描已在第一优先中完成，此处只需针对review_target中的候选做逐条裁决。）

### 第三优先：检查已有card的图表达完整性

逐张比较`original_json.cards`、其对应`coverage_audit.proposition`与原文：

- proposition中的条件、参照关系和独立结果是否都进入`flow_nodes + flow_edges`；
- 结果是否只藏在process标签中而没有结果节点和边；
- 多个判断输入是否只被列出，却没有通过`REFERENCES`连接到评估动作；
- 收集/计算/合计等输入处理与依据标准作出判断是否被压缩在同一个宽泛process中；
- 原文支持的互斥结果是否被压成无condition的单一`PRODUCES`；
- 方向错误的已有边是否需要追加一条证据支持的正确关系。

只追加节点、边和`source_unit_ids`，不删除、修改、重新编号或替换已有card、节点或边。已有错误边留给P7D拒绝；可以追加正确的替代边，新增边仍须由P7D审核。

### Card归属裁决

`original_json`中的card_id、主题相似性和候选匹配结果只用于覆盖定位，不表示遗漏内容必须补入该card。选择`card_supplement`前，必须在内部判断gap与已有process属于哪种关系：

```text
downstream_extension：新动作或结果确实位于已有动作之后，且存在原文支持的主流程边
refinement：新结构是在展开已有宽泛process内部的输入处理、标准应用或条件判断
independent_relation：只与已有card主题相同，没有有证据的主流程连接
duplicate：与已有节点或边语义重复
```

判为`duplicate`时不输出`new_candidates`、`new_cards`或`card_supplements`。若它原本不是`review_target_candidate_ids`中的`kg_only`候选，不新增裁决记录；若目标候选本身只是已由KG承接的残余事实，则保持`kg_only`。

只有`downstream_extension`，或者只需为已有原子process补充其直接使用的input/standard/边时，才允许`card_supplement`。`refinement`不作为新的并列process追加到旧card；在只增式合同不能重写旧process时，应根据证据选择`new_card`或不新增，不为了复用旧card而制造重复处理节点。

两个process共同`REFERENCES`同一个input或standard，只表示它们参照同一辅助信息，不构成两个process之间的主流程连接。选择supplement前必须在内部合并新旧节点并检查：新增process或exit是否能通过非`REFERENCES`的有证据方向进入已有主路径；不能时不supplement，也不补造`PRECEDES`。

构图时遵守语义原子性：原始输入连接到实际处理它的process，标准连接到实际应用它的判断process。若结果取决于标准、阈值、充分性或判断结论，条件显式进入边的`condition`字段或通过`P3_branch_routing + DECIDES`表达，不隐藏在exit label中。证据支持两个或以上互斥结果时使用`P3_branch_routing + DECIDES`；一般规则与同一标准下的正反实例可以共同支持候选分支，但跨unit归纳边必须标记`llm_inference`。

## 成卡标准

新增关系必须同时满足：

1. 当前section证据支持关系两端、主体、方向和条件（如有）。
2. 关系超出基础KG能充分表达的定义、事实、列表、普通机制或一般知识关系。
3. 关系能帮助判断选项的顺序、条件、职责、义务、应对、适用范围或限定性结果。
4. 不需要补造主体、动作、条件或结果。

相邻句之间缺少明确连接词，但存在必要功能依赖时，可以输出`derivation=llm_inference`，交P7D和人工复核；此时derivation如实标记为`llm_inference`。

已经具备主体、动作和方向的关系——即使可被描述为”纯义务陈述””没有复杂步骤”或”只受风险偏好约束”——也属于P7C增量，不跳过。

以下通常保持`kg_only`：纯定义/分类/阈值数值/组成列表、普通犯罪手法、孤立红旗、普通案例事实、一般机制因果、抽象风险缓解目的，以及必须补造主体或方向才能成立的关系。

仅描述某项调查、活动或机制受到阻碍，不自动构成P7C关系。只有原文进一步给出特定主体据此实施的识别、评估、决策、应对或交接，才检查是否成卡。行动动词出现不代表自动成卡——需要检查是否有明确的主体、方向和证据支持。

后续unit如果只是独立事实、犯罪性质说明、处罚或背景结果，不因仅位于某个process之后就追加为该process的`PRODUCES`目标。只有原文明确说明同一动作产生该结果，或存在必要功能依赖时，才建立边；否则保留为KG内容。

调优、控制或框架组成的定义、目标和一般效果通常由KG承接；只有具体主体基于明确输入执行创建/修改/删除、监控、评估或应对动作时，才进入P7C。

## 通用回归不变量

- 相邻或邻近unit分别表达变化/前提与主体应对时，先判断两端是否共同形成一条有向命题；若形成，证据覆盖两端。缺少明示连接词但存在唯一必要功能依赖时标记`llm_inference`，两端各自交给KG会导致有向关系丢失。
- 状态变化、原因或判断依据通常是process参照的input，按语义角色通过REFERENCES连接，不按语法顺序写成PRECEDES。保留”部分、通常、即使、可能”等限定。
- 多个判断因素应连接到实际使用它们的评估process；没有独立出口不影响开放式关系成卡。
- 某项标准只在特定风险、对象或情境下适用时，适用条件进入`condition`或有证据的条件节点与边，不埋在standard或exit的label中。
- 原文同时给出标准约束和带情态的识别/控制效果时，分别保留两种关系，并完整保留`help/may/can`等强度。
- 动作所需的参与方、材料、理由、批准或其他判断输入，由实际消费它的process通过`REFERENCES`连接；这些是执行动作的参照条件，不是动作产生的独立结果。
- 一个动作只建一个节点——主动式和被动式不拆成process与exit。多个制度主体的行动只有原文明示局部触发、必要功能先后或结果关系时才连接，不按教材排列顺序串成总链。

示意：若原文分别说明“两个原始数值先合计”“合计值与适用标准比较”“达到与未达到标准导向不同结果”，应把输入处理、标准判断和互斥结果分开表达；这是结构示意，不规定任何业务对象、数值、节点数量或结论。

## 图规则

新增完整card和card补充使用相同图规则。

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。节点必须由原文明示，`evidence_strength`只能为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard，不表达先后或产出。
- `PRODUCES`只能由process指向语义独立的exit。
- 单一路径条件使用带`condition`的`PRECEDES`；只有证据支持至少两个互斥结果时才使用`DECIDES`。互斥结果可以由明示规则直接给出，也可以由同一标准下的正反实例共同支持；仅有孤立案例时不推广为一般分支。
- `DECIDES`只能由`P3_branch_routing`发出。
- `derivation`只能为`explicit_text`或`llm_inference`。

静态适用对象、材料、因素、阈值、监管要求或风险偏好应作为input/standard，由process通过`REFERENCES`指向，不按语法顺序建成`entry --PRECEDES--> process`。一个动作只建一个节点——不拆成主动式process和被动式exit。动作所需的批准、理由、标准或要求/义务是执行的参照条件，不通过`PRODUCES`表达。

`REFERENCES.condition`只限定input/standard适用于process的范围，不表达条件分支。单一路径`PRECEDES.condition`表达逻辑前提，不要求钟表式先后。

保留`must, should, may, might, could, often, potentially, help, typically`等情态和限定。`help mitigate`写成”有助于缓解”，不写成必然降低。`must`本身不证明义务是持续、定期、永久或反复的。`X7_continuing_obligation`只用于原文明示新建立的独立持续义务，规范性动作仍保留在process中。

`escalate/escalation`默认写成”升级处理/升级处置”或保留英文；只有原文明示`report/notify/file/refer`及对象时才写成报告或移交。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写。

## 补丁合同

顶层必须且只能包含：

```text
section_id
coverage_adjudication
new_candidates
new_cards
card_supplements
```

### coverage_adjudication

对每个`review_target_candidate_ids`恰好输出一条：

```json
{
  "candidate_id": "cand_001",
  "original_decision": "kg_only",
  "final_decision": "kg_only",
  "card_id": null,
  "reason": "<中文>"
}
```

`final_decision`只能是`kg_only`或`p7c_card`。提升时`card_id`必须指向`new_cards`中的新card，或指向被`card_supplements`补充的已有card。多个候选可以共同指向同一card。

### new_candidates

用于记录跨候选关系、首次未登记的关系或已有card的遗漏关系。每项必填：

```json
{
  "candidate_id": "coverage_gap_001",
  "unit_ids": ["<当前section unit_id>"],
  "proposition": "<完整有向命题>",
  "decision": "p7c_card",
  "card_id": "<新增或被补充的card_id>",
  "reason": "<KG不能表达什么>",
  "origin_candidate_ids": ["<相关首次候选ID，可为空>" ]
}
```

新`candidate_id`不与`original_json.coverage_audit`中已有ID重复。`unit_ids`可以是多个原候选unit的并集，也可以包含首次未登记的当前section unit。

### new_cards

只放新增完整card。每张必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。`card_nature`只使用`execution, assessment, risk_indicator, control`。`candidate_status`固定为`candidate`。card ID不与已有card重复。每张新card必须被某条提升裁决或`new_candidates`引用。

### card_supplements

只用于给已有card追加内容：

```json
{
  "patch_id": "coverage_supplement_001",
  "card_id": "<已有card_id>",
  "reason": "<中文说明遗漏>",
  "origin_candidate_ids": ["<相关首次候选ID或本补丁new_candidate ID，可为空>"],
  "add_flow_nodes": [],
  "add_flow_edges": [],
  "add_source_unit_ids": []
}
```

至少新增一个节点或一条边。新增ID不与该card已有ID重复。新增边可以连接已有节点和新增节点。所有新增节点、边的证据unit必须已经存在于card的`source_unit_ids`，或同时列入`add_source_unit_ids`。每个被补充的card必须由一条提升裁决或`new_candidates`引用。

`card_supplement`不是默认选项。matched card、相同主题、共享unit或共享auxiliary都不足以证明归属。若新增内容是在细化已有宽泛process，或者新增process/exit无法通过非`REFERENCES`边进入已有主路径，应使用`new_card`承载证据充分的局部结构；两个断开的处理中心不塞进同一card。

没有某类修改时输出空数组。即使`review_target_candidate_ids`为空，仍必须扫描完整section、审核已有card，并输出五个顶层字段。

必须优先保证JSON合同完整：五个顶层数组字段始终全部输出；理由保持简洁。确认存在真实gap后开始生成新card。

## 输出骨架

```json
{
  "section_id": "<section_id>",
  "coverage_adjudication": [],
  "new_candidates": [],
  "new_cards": [],
  "card_supplements": []
}
```

## 当前section

section_id: `CH57-S08`

section_title: `Transaction monitoring scenario calibration testing > Case example: Identify data for a new TM system`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "识别新交易监控系统的数据：核心数据、风险映射、补充来源与评估",
      "title_en": "Identifying data for a new TM system: core data, risk mapping, supplemental sources, and evaluation",
      "covered_units": [
        {
          "unit_id": "v7u_N004590",
          "unit_type": "case",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004591",
          "unit_type": "case",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004592",
          "unit_type": "process",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004596",
          "unit_type": "case",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004599",
          "unit_type": "process",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004589",
          "unit_type": "case",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N004593",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004594",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N004595",
          "unit_type": "process",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004597",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004598",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004600",
          "unit_type": "fact",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004601",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004602",
          "unit_type": "case",
          "kg_role": "states_consequence"
        }
      ]
    }
  ],
  "covered_relations": []
}
```

section_text_with_unit_anchors:

```text
[v7u_N004589|4589] Sarah, a financial crime analyst at a mid-sized bank, has been asked to identify data needed for a new TM system. The goal is to ensure the system effectively detects suspicious activity while balancing operational feasibility and regulatory requirements.
ZH: 案例：分析师被要求为新交易监控系统识别所需数据

[v7u_N004590|4590] She identifies core transactional data as essential components, including customer account numbers, transaction time stamps, amounts, counterparties, and geographic locations.
ZH: 核心交易数据包括客户账号、时间戳、金额、交易对手和地理位置

[v7u_N004591|4591] Sarah then consults with compliance and IT teams to assess customer profile information that can enhance risk detection. This includes customer risk ratings, account types, expected transaction behaviors, and historical activity.
ZH: 客户画像信息包括风险评级、账户类型、预期交易行为和历史活动

[v7u_N004592|4592] Next, Sarah reviews the latest annual risk assessment to identify risks that the TM systems should control. She conducts a product risk assessment to ensure that the AML risks of all products are understood. She then maps the existing scenarios of the TM system against the risks to examine coverage and to understand what additional scenarios may be needed.
ZH: 通过年度风险评估和产品风险评估来识别交易监控系统需控制的风险并映射现有场景

[v7u_N004593|4593] Each specific risk has attributes that match corresponding data points that form the foundation of the TM system.
ZH: 每个特定风险的属性对应构成交易监控系统基础的数据点

[v7u_N004594|4594] For example, a risk such as rapid fund transfers requires data points, including inbound and outbound payment time stamps, acceptable thresholds based on risk profiles, transaction amounts, and thresholds for amounts based on different risk profiles.
ZH: 示例：快速资金转移风险需要入账和出账时间戳、基于风险画像的可接受阈值等数据点

[v7u_N004595|4595] Where necessary, she adds these to available core transactional and customer risk profile data.
ZH: 必要时将补充数据添加到核心交易数据和客户风险画像数据中

[v7u_N004596|4596] Sarah then identifies supplemental data sources to refine alerts and improve investigative efficiency. She considers including data on adverse media screenings, PEP status, and SAR filings. She also explores integrating behavioral indicators, such as sudden deviations from a customer's usual transaction size or velocity.
ZH: 识别补充数据源以优化警报并提高调查效率，包括负面媒体、政治敏感人物状态和可疑活动报告

[v7u_N004597|4597] However, Sarah understands that selecting data is not just about adding more variables. She knows she should avoid treating this process as a checklist.
ZH: 数据选择不是添加更多变量，应避免清单式方法

[v7u_N004598|4598] This process should align with the identified risks and available data.
ZH: 数据选择流程应与已识别的风险和可用数据保持一致

[v7u_N004599|4599] She evaluates whether the bank has consistent, reliable access to each dataset, whether it meets privacy and regulatory requirements, and whether it aligns with the bank’s specific risks.
ZH: 评估数据集的访问可靠性、隐私和监管合规性以及与银行特定风险的一致性

[v7u_N004600|4600] She also assesses the data’s compatibility with existing formats and the system’s processing capacity.
ZH: 评估数据与现有格式的兼容性以及系统的处理能力

[v7u_N004601|4601] This ensures that additional data fields enhance detection without overwhelming resources or generating excessive false positives.
ZH: 额外数据字段在增强检测的同时避免资源过载和误报

[v7u_N004602|4602] By taking a risk-based approach to data selection, Sarah ensures that the new TM system is both effective and efficient, aligning with the bank’s compliance needs while leveraging available data intelligently.
ZH: Sarah采用基于风险的方法选择数据，确保交易监控系统有效且高效
```

allowed_unit_ids:

```json
[
  "v7u_N004589",
  "v7u_N004590",
  "v7u_N004591",
  "v7u_N004592",
  "v7u_N004593",
  "v7u_N004594",
  "v7u_N004595",
  "v7u_N004596",
  "v7u_N004597",
  "v7u_N004598",
  "v7u_N004599",
  "v7u_N004600",
  "v7u_N004601",
  "v7u_N004602"
]
```

original_json:

```json
{
  "section_id": "CH57-S08",
  "section_title": "Transaction monitoring scenario calibration testing > Case example: Identify data for a new TM system",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N004592",
        "v7u_N004595"
      ],
      "proposition": "Sarah基于年度风险评估识别交易监控系统需控制的风险，然后映射现有场景以检查覆盖并了解额外场景需求，最后将必要的数据点添加到核心数据中。",
      "decision": "p7c_card",
      "card_id": "p7card_CH57-S08_001",
      "reason": "内部存在明确的主体动作（识别风险、映射场景、添加数据）及其对特定输入（年度风险评估、现有场景）的依赖关系，形成了有向操作链，基础KG只能将其作为过程描述保存，无法表达这些内部顺序和条件。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N004596"
      ],
      "proposition": "Sarah识别补充数据源（如负面媒体、PEP、SAR）并考虑行为指标，以优化警报和提高调查效率。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅为静态的数据源清单和执行一个简单识别动作，无进一步的有向判断或条件依赖，基础KG可以直接存储该事实。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N004597",
        "v7u_N004598"
      ],
      "proposition": "数据选择应避免清单式方法，并与已识别风险和可用数据对齐。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "属于一般性指导原则，无程序性链条，KG可保存为规则。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N004599",
        "v7u_N004600",
        "v7u_N004601"
      ],
      "proposition": "Sarah评估数据集是否符合一致性、可靠性、隐私法规、风险对齐和兼容性要求，以确保增强检测而不超载。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "评估动作仅为列举多项检查标准，既无分支结论也无独立出口，属于基础事实描述，KG可充分表达。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH57-S08_001",
      "section_id": "CH57-S08",
      "card_nature": "execution",
      "title": "风险识别、映射与数据添加流程",
      "flow_nodes": [
        {
          "node_id": "input1",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "年度风险评估",
          "evidence_unit_ids": [
            "v7u_N004592"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "input2",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "现有TM系统场景",
          "evidence_unit_ids": [
            "v7u_N004592"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P1",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "Sarah识别交易监控系统需控制的风险",
          "evidence_unit_ids": [
            "v7u_N004592"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P2",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "Sarah将现有TM系统场景与风险进行映射，以检查覆盖和了解额外场景需求",
          "evidence_unit_ids": [
            "v7u_N004592"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P3",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "Sarah将必要的风险相关数据点添加到核心交易数据和客户风险画像数据中",
          "evidence_unit_ids": [
            "v7u_N004595"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e_ref1",
          "edge_type": "REFERENCES",
          "source": "P1",
          "target": "input1",
          "evidence_unit_ids": [
            "v7u_N004592"
          ],
          "derivation": "explicit_text",
          "relation_type": "clue_supports_identification"
        },
        {
          "edge_id": "e_seq1",
          "edge_type": "PRECEDES",
          "source": "P1",
          "target": "P2",
          "evidence_unit_ids": [
            "v7u_N004592"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e_seq2",
          "edge_type": "PRECEDES",
          "source": "P1",
          "target": "P3",
          "evidence_unit_ids": [
            "v7u_N004592",
            "v7u_N004595"
          ],
          "derivation": "explicit_text",
          "condition": "在必要时（基于风险识别存在必要数据点）"
        },
        {
          "edge_id": "e_ref2",
          "edge_type": "REFERENCES",
          "source": "P2",
          "target": "input2",
          "evidence_unit_ids": [
            "v7u_N004592"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004592",
        "v7u_N004595"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：Sarah通过年度风险评估识别需控制的风险，并基于此映射现有TM场景（输入1→P1→P2，P2参照输入2）和添加必要数据点（P1→P3，有条件）；KG不足：基础KG仅将本段作为一般过程描述，无法表达内部顺序和对特定输入的有向依赖；选项判断：可确认识别风险、映射场景与添加数据之间的动作顺序和输入关联；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_002",
  "cand_003",
  "cand_004"
]
```

