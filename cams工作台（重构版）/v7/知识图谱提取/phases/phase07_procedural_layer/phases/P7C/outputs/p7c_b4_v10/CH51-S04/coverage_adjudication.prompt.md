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

section_id: `CH51-S04`

section_title: `Understanding AFC technology > Adopting a risk-based approach when choosing AFC technology`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "风险为本方法的定义与资源优先分配",
      "title_en": "Risk-based approach definition and resource prioritization",
      "covered_units": [
        {
          "unit_id": "v7u_N003790",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N003791",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003793",
          "unit_type": "process",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003792",
          "unit_type": "fact",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "进行针对性风险评估以选择金融犯罪防控技术",
      "title_en": "Conducting targeted risk assessments for AFC technology selection",
      "covered_units": [
        {
          "unit_id": "v7u_N003794",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003795",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003796",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003797",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        }
      ]
    },
    {
      "title_zh": "基于风险确定技术适用性",
      "title_en": "Risk-based determination of technology fit",
      "covered_units": [
        {
          "unit_id": "v7u_N003798",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003799",
          "unit_type": "fact",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N003800",
          "unit_type": "fact",
          "kg_role": "illustrates"
        }
      ]
    },
    {
      "title_zh": "考虑系统增强而非全面替换",
      "title_en": "Considering system augmentation before full replacement",
      "covered_units": [
        {
          "unit_id": "v7u_N003801",
          "unit_type": "case",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003802",
          "unit_type": "case",
          "kg_role": "illustrates"
        }
      ]
    },
    {
      "title_zh": "金融犯罪防控技术与业务战略对齐",
      "title_en": "Aligning AFC technology with business strategy",
      "covered_units": [
        {
          "unit_id": "v7u_N003803",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003804",
          "unit_type": "case",
          "kg_role": "illustrates"
        }
      ]
    },
    {
      "title_zh": "利用跨职能需求与实体解析",
      "title_en": "Leveraging cross-functional requirements and entity resolution",
      "covered_units": [
        {
          "unit_id": "v7u_N003805",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003806",
          "unit_type": "definition",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N003807",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "技术选择中风险考量不足的风险",
      "title_en": "Risk of inadequate risk consideration in technology selection",
      "covered_units": [
        {
          "unit_id": "v7u_N003808",
          "unit_type": "risk_indicator",
          "kg_role": "states_consequence"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "风险为本方法的定义与资源优先分配",
      "target_title": "进行针对性风险评估以选择金融犯罪防控技术",
      "relation_type": "prepares"
    },
    {
      "source_title": "进行针对性风险评估以选择金融犯罪防控技术",
      "target_title": "基于风险确定技术适用性",
      "relation_type": "prepares"
    },
    {
      "source_title": "基于风险确定技术适用性",
      "target_title": "考虑系统增强而非全面替换",
      "relation_type": "prepares"
    },
    {
      "source_title": "考虑系统增强而非全面替换",
      "target_title": "金融犯罪防控技术与业务战略对齐",
      "relation_type": "parallels"
    },
    {
      "source_title": "金融犯罪防控技术与业务战略对齐",
      "target_title": "利用跨职能需求与实体解析",
      "relation_type": "parallels"
    },
    {
      "source_title": "风险为本方法的定义与资源优先分配",
      "target_title": "技术选择中风险考量不足的风险",
      "relation_type": "contrasts"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N003790|3790] A risk-based approach refers to the process of identifying the highest risks and prioritizing resources to address them.
ZH: 风险为本方法是指识别最高风险并优先分配资源以应对风险的过程。

[v7u_N003791|3791] Investing in AFC tools and technologies also follows the same principle.
ZH: 金融犯罪防控工具和技术的投资同样遵循风险为本原则。

[v7u_N003792|3792] In practice, constraints such as budgets, timelines, and other competing priorities may mean resources are limited.
ZH: 实践中预算、时间等约束可能导致资源有限。

[v7u_N003793|3793] Applying a risk-based approach in this instance would lead to the organization choosing to overhaul the weakest or most inefficient controls.
ZH: 应用风险为本方法时，机构会选择改造最薄弱或效率最低的控制。

[v7u_N003794|3794] Selecting AFC technology requires first conducting targeted risk assessments for each AFC control, such as CDD, screening, and monitoring.
ZH: 选择金融犯罪防控技术前需先对每项控制（如客户尽职调查、筛查、监控）进行针对性风险评估。

[v7u_N003795|3795] These assessments help identify gaps in current systems, prioritize high-risk areas, and inform decisions about whether to augment existing technology or fully replace it.
ZH: 风险评估有助于识别系统差距、优先处理高风险领域并决定是增强还是替换现有技术。

[v7u_N003796|3796] Inputs into these risk assessments include data source analysis, transaction types, customer profiles, jurisdictions, and other attributes needed to present and understand a clear risk profile.
ZH: 风险评估输入包括数据源分析、交易类型、客户画像、司法管辖区等。

[v7u_N003797|3797] If the organization has limited experience in selecting AFC technology, engaging strategic advisory firms may further enhance decision-making. Experts in financial crime compliance and technology may provide independent evaluations, recommend best-fit solutions, and ensure alignment with evolving regulatory requirements. Their advice may also help the organization navigate complex implementation challenges, potentially saving time and money.
ZH: 聘请战略咨询公司可提升金融犯罪防控技术选型决策，提供独立评估和最佳方案建议。

[v7u_N003798|3798] A risk-based approach influences which technology is most fit for purpose.
ZH: 风险为本方法影响哪种技术最适合特定用途。

[v7u_N003799|3799] For instance, not all monitoring and screening functions benefit equally from new technologies.
ZH: 并非所有监控和筛查功能都能从新技术中同等受益。

[v7u_N003800|3800] While AI-driven transaction monitoring and machine learning-based name screening may enhance efficiency and effectiveness, investigative and analytical tasks may consume the most resources and be good candidates for automation.
ZH: 人工智能驱动的交易监控和机器学习名称筛查可提升效率，调查分析任务适合自动化。

[v7u_N003801|3801] Before committing to a full system replacement, organizations may consider augmentation.
ZH: 在全面替换系统前，组织可考虑增强现有系统。

[v7u_N003802|3802] For example, they might consider enhancing existing systems with new capabilities, thereby reducing immediate cost and disruption while still improving effectiveness.
ZH: 增强现有系统可降低成本与中断，同时提升有效性。

[v7u_N003803|3803] Selecting AFC technology should also align with business strategy.
ZH: 选择金融犯罪防控技术应与业务战略保持一致。

[v7u_N003804|3804] For instance, an organizational strategy to move data processing to the cloud influences AFC system options.
ZH: 将数据处理迁移至云端的战略会影响金融犯罪防控系统选择。

[v7u_N003805|3805] A well-considered AFC technology strategy leverages similar requirements across AFC dimensions.
ZH: 金融犯罪防控技术战略应利用各维度间的相似需求。

[v7u_N003806|3806] For example, consider entity resolution, which refers to the process of confirming whether multiple records are referring to the same data item, such as an address, a device, or a phone number.
ZH: 实体解析是确认多条记录是否指向同一数据项的过程。

[v7u_N003807|3807] Entity resolution is a significant part of CDD, screening, and transaction monitoring systems, so sharing this capability across multiple solutions makes sense when possible.
ZH: 实体解析是客户尽职调查、筛查和交易监控系统的重要组成部分。

[v7u_N003808|3808] Failure to adequately consider risks when selecting new technology may signal to business sponsors, auditors, and regulators that the AFC function does not fully understand its role and the risks the organization faces.
ZH: 选择新技术时未充分考虑风险，可能向监管者等信号表明金融犯罪防控职能未理解其角色。
```

allowed_unit_ids:

```json
[
  "v7u_N003790",
  "v7u_N003791",
  "v7u_N003792",
  "v7u_N003793",
  "v7u_N003794",
  "v7u_N003795",
  "v7u_N003796",
  "v7u_N003797",
  "v7u_N003798",
  "v7u_N003799",
  "v7u_N003800",
  "v7u_N003801",
  "v7u_N003802",
  "v7u_N003803",
  "v7u_N003804",
  "v7u_N003805",
  "v7u_N003806",
  "v7u_N003807",
  "v7u_N003808"
]
```

original_json:

```json
{
  "section_id": "CH51-S04",
  "section_title": "Understanding AFC technology > Adopting a risk-based approach when choosing AFC technology",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N003790",
        "v7u_N003791",
        "v7u_N003792",
        "v7u_N003793"
      ],
      "proposition": "在资源约束条件下，风险为本方法约束组织选择改造最薄弱或效率最低的控制",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S04_001",
      "reason": "明确的条件-标准-动作有向结构：在资源有限时，风险为本方法作为标准直接约束组织改造最弱控制。基础KG只能将其作为整体事实保存，无法表达方法如何约束决策的过程关系。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N003794",
        "v7u_N003795",
        "v7u_N003796"
      ],
      "proposition": "选择AFC技术前必须先进行针对性风险评估，并参考多种风险输入数据",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S04_002",
      "reason": "明确的步骤顺序和输入参照：评估过程必须前置且引用具体风险输入。基础KG可能存储静态规则，但无法表达过程先后及输入依赖关系。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N003797"
      ],
      "proposition": "如果组织在选择AFC技术方面经验有限，聘请战略咨询公司可增强决策",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S04_003",
      "reason": "条件触发应对：经验有限状态下触发聘请咨询公司的建议。基础KG可保存为孤立建议，但无法表达条件-动作的触发关系。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N003801"
      ],
      "proposition": "在承诺全面替换系统之前，组织应考虑增强现有系统",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S04_004",
      "reason": "明确的步骤顺序建议：增强评估应先于全面替换决策。基础KG可存储为最佳实践，但无法表达步骤间的顺序约束。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N003803"
      ],
      "proposition": "选择AFC技术应与业务战略保持一致",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S04_005",
      "reason": "标准约束动作：业务战略作为标准直接影响技术选择过程。基础KG可存储该原则，但无法表达标准对过程的有向约束关系。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N003805",
        "v7u_N003806",
        "v7u_N003807"
      ],
      "proposition": "由于实体解析是多个系统的重要组成部分，在可能时应跨解决方案共享此能力",
      "decision": "kg_only",
      "card_id": null,
      "reason": "属于通用最佳实践建议，无明确条件分支或严格程序步骤，基础KG可表达此因果关系和建议。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N003808"
      ],
      "proposition": "选择新技术时未充分考虑风险可能向监管者等发出信号表明AFC职能未理解其角色",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立风险指标/后果，基础KG可承接。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N003799",
        "v7u_N003800"
      ],
      "proposition": "AI驱动交易监控和ML名称筛查可提升效率，但并非所有监控和筛查功能同等受益，调查分析任务适合自动化",
      "decision": "kg_only",
      "card_id": null,
      "reason": "普通案例机制和举例，基础KG可保存这些事实。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N003798"
      ],
      "proposition": "风险为本方法影响哪种技术最适合特定用途",
      "decision": "kg_only",
      "card_id": null,
      "reason": "抽象的一般性陈述，无具体主体动作或条件，基础KG可表达。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N003802"
      ],
      "proposition": "增强现有系统可降低立即成本与中断，同时提升有效性",
      "decision": "kg_only",
      "card_id": null,
      "reason": "对增强措施好处的举例说明，无有向判断结构，基础KG可承接。"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N003804"
      ],
      "proposition": "组织将数据处理迁移至云端的战略影响AFC系统选择方案",
      "decision": "kg_only",
      "card_id": null,
      "reason": "业务战略影响技术选择的实例，已由card p7card_CH51-S04_005的原则覆盖，实例本身无需单独成卡。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH51-S04_001",
      "section_id": "CH51-S04",
      "card_nature": "control",
      "title": "资源约束下应用风险为本方法导致改造最弱控制",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "风险为本方法：识别最高风险并优先分配资源",
          "evidence_unit_ids": [
            "v7u_N003790",
            "v7u_N003791"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "组织：改造最薄弱或效率最低的控制",
          "evidence_unit_ids": [
            "v7u_N003793"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "REFERENCES",
          "source": "n2",
          "target": "n1",
          "evidence_unit_ids": [
            "v7u_N003790",
            "v7u_N003791",
            "v7u_N003793"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action",
          "condition": "When faced with constraints such as budgets, timelines, and other competing priorities that may mean resources are limited.",
          "source_quote": "Applying a risk-based approach in this instance would lead to the organization choosing to overhaul the weakest or most inefficient controls."
        }
      ],
      "source_unit_ids": [
        "v7u_N003790",
        "v7u_N003791",
        "v7u_N003792",
        "v7u_N003793"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：在资源约束条件下，风险为本方法约束组织选择改造最弱控制；KG不足：基础KG可将整句保存为事实，但无法表达方法作为标准如何在一定条件下导向具体改造决策的有向约束关系；选项判断：可用于确认在资源有限时，风险为本方法会优先引导组织改造最弱控制，而非其他措施；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH51-S04_002",
      "section_id": "CH51-S04",
      "card_nature": "assessment",
      "title": "选择AFC技术前须进行针对性风险评估",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "机构：对每项AFC控制进行针对性风险评估",
          "evidence_unit_ids": [
            "v7u_N003794",
            "v7u_N003795"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构：选择AFC技术",
          "evidence_unit_ids": [
            "v7u_N003794"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n3",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "数据源分析、交易类型、客户画像、司法管辖区等风险信息",
          "evidence_unit_ids": [
            "v7u_N003796"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "PRECEDES",
          "source": "n1",
          "target": "n2",
          "evidence_unit_ids": [
            "v7u_N003794"
          ],
          "derivation": "explicit_text",
          "condition": "必须先进行风险评估",
          "source_quote": "Selecting AFC technology requires first conducting targeted risk assessments for each AFC control, such as CDD, screening, and monitoring."
        },
        {
          "edge_id": "e2",
          "edge_type": "REFERENCES",
          "source": "n1",
          "target": "n3",
          "evidence_unit_ids": [
            "v7u_N003796"
          ],
          "derivation": "explicit_text",
          "condition": "",
          "source_quote": "Inputs into these risk assessments include data source analysis, transaction types, customer profiles, jurisdictions, and other attributes needed to present and understand a clear risk profile."
        }
      ],
      "source_unit_ids": [
        "v7u_N003794",
        "v7u_N003795",
        "v7u_N003796"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：选择AFC技术之前必须先进行针对性风险评估，并且评估需要参考多种风险输入数据；KG不足：基础KG可能将‘选择技术需评估’存储为静态规则，但无法表达评估作为前置过程的顺序关系和输入参照关系；选项判断：可用于确认正确步骤顺序（先评估后选择）以及评估需考虑哪些输入；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH51-S04_003",
      "section_id": "CH51-S04",
      "card_nature": "execution",
      "title": "经验有限时可聘请战略咨询公司增强技术选型决策",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "组织在选择AFC技术方面经验有限",
          "evidence_unit_ids": [
            "v7u_N003797"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "组织：聘请战略咨询公司以增强决策",
          "evidence_unit_ids": [
            "v7u_N003797"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "PRECEDES",
          "source": "n1",
          "target": "n2",
          "evidence_unit_ids": [
            "v7u_N003797"
          ],
          "derivation": "explicit_text",
          "condition": "If the organization has limited experience in selecting AFC technology",
          "source_quote": "If the organization has limited experience in selecting AFC technology, engaging strategic advisory firms may further enhance decision-making."
        }
      ],
      "source_unit_ids": [
        "v7u_N003797"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：当组织经验有限时，建议聘请咨询公司以增强决策；KG不足：基础KG可存储该建议，但无法表达条件-动作的触发关系；选项判断：可确认在何种条件下组织应考虑借助外部顾问；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH51-S04_004",
      "section_id": "CH51-S04",
      "card_nature": "assessment",
      "title": "在全面替换系统前应考虑增强现有系统",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "组织：考虑增强现有系统",
          "evidence_unit_ids": [
            "v7u_N003801"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "组织：决定全面替换系统",
          "evidence_unit_ids": [
            "v7u_N003801"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "PRECEDES",
          "source": "n1",
          "target": "n2",
          "evidence_unit_ids": [
            "v7u_N003801"
          ],
          "derivation": "explicit_text",
          "condition": "Before committing to a full system replacement",
          "source_quote": "Before committing to a full system replacement, organizations may consider augmentation."
        }
      ],
      "source_unit_ids": [
        "v7u_N003801"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：在决定全面替换系统之前，应先考虑增强现有系统；KG不足：基础KG可存储该建议，但无法表达步骤间的顺序约束；选项判断：可用于确定正确的决策流程（先评估增强，再考虑替换）；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH51-S04_005",
      "section_id": "CH51-S04",
      "card_nature": "execution",
      "title": "选择AFC技术应与业务战略保持一致",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "业务战略",
          "evidence_unit_ids": [
            "v7u_N003803"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "process",
          "node_type": "P8_constrained_action",
          "label": "机构：选择AFC技术",
          "evidence_unit_ids": [
            "v7u_N003803"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "REFERENCES",
          "source": "n2",
          "target": "n1",
          "evidence_unit_ids": [
            "v7u_N003803"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action",
          "source_quote": "Selecting AFC technology should also align with business strategy."
        }
      ],
      "source_unit_ids": [
        "v7u_N003803"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：选择AFC技术的过程应受到业务战略的约束；KG不足：基础KG可存储该原则，但无法表达战略作为标准对选择过程的有向约束；选项判断：可用于判断技术选择决策应考虑业务战略一致性；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_006",
  "cand_007",
  "cand_008",
  "cand_009",
  "cand_010",
  "cand_011"
]
```

