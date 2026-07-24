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

section_id: `CH56-S01`

section_title: `Technology for payment and batch screening > Types of ongoing screening`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "实时与批量筛查：类型与目的",
      "title_en": "Real-time and Batch Screening: Types and Purposes",
      "covered_units": [
        {
          "unit_id": "v7u_N004307",
          "unit_type": "classification",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N004308",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N004313",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N004312",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004314",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004306",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N004309",
          "unit_type": "risk_indicator",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N004310",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N004311",
          "unit_type": "rule",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N004315",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004316",
          "unit_type": "classification",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "筛查技术：规模与支付网络集成",
      "title_en": "Screening Technology: Scale and Payment Network Integration",
      "covered_units": [
        {
          "unit_id": "v7u_N004318",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004319",
          "unit_type": "fact",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004331",
          "unit_type": "fact",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004324",
          "unit_type": "fact",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004327",
          "unit_type": "fact",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004317",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N004320",
          "unit_type": "fact",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N004321",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004322",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004323",
          "unit_type": "fact",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N004325",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004326",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N004328",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N004329",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N004330",
          "unit_type": "fact",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004332",
          "unit_type": "fact",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004333",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        }
      ]
    },
    {
      "title_zh": "高级筛查方法与校准",
      "title_en": "Advanced Screening Methods and Calibration",
      "covered_units": [
        {
          "unit_id": "v7u_N004337",
          "unit_type": "definition",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004338",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004339",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004340",
          "unit_type": "process",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004334",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N004335",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N004336",
          "unit_type": "fact",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "数字资产筛查：挑战与实践",
      "title_en": "Digital Asset Screening: Challenges and Practices",
      "covered_units": [
        {
          "unit_id": "v7u_N004342",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004344",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004345",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004346",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004354",
          "unit_type": "definition",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004356",
          "unit_type": "process",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004341",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N004343",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N004347",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004348",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N004349",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004350",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004351",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N004352",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N004353",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004355",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004357",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004358",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004359",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004360",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "实时与批量筛查：类型与目的",
      "target_title": "筛查技术：规模与支付网络集成",
      "relation_type": "prepares"
    },
    {
      "source_title": "筛查技术：规模与支付网络集成",
      "target_title": "高级筛查方法与校准",
      "relation_type": "prepares"
    },
    {
      "source_title": "高级筛查方法与校准",
      "target_title": "数字资产筛查：挑战与实践",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N004306|4306] Ongoing screening in payment systems is critical for preventing and detecting financial crimes, including money laundering, terrorist financing, and sanctions evasion.
ZH: 支付系统中的持续筛查对于预防和检测洗钱、恐怖融资和制裁规避至关重要

[v7u_N004307|4307] There are typically two types of screening: Real-time screening and batch screening. Each serves its own purpose.
ZH: 持续筛查分为实时筛查和批量筛查两种类型，各有其用途

[v7u_N004308|4308] Real-time screening involves screening payments as they happen, which helps prevent payments involving sanctioned individuals or entities.
ZH: 实时筛查在支付发生时进行，有助于防止涉及受制裁个人或实体的交易

[v7u_N004309|4309] Failing to prevent such transactions can put any business at risk for severe regulatory penalties, reputational damage, and legal consequences.
ZH: 未能阻止受制裁交易会使企业面临严重的监管处罚、声誉损害和法律后果

[v7u_N004310|4310] Noncompliance with sanctions regulations can result in heavy fines imposed by regulatory bodies such as the OFAC in the US or OFSI in the UK.
ZH: 违反制裁法规可能导致美国OFAC或英国OFSI等监管机构处以巨额罚款

[v7u_N004311|4311] When an organization onboards a customer, as part of its KYC checks it should screen the customer in real time against sanctions or terror lists.
ZH: 机构在客户准入时作为了解你的客户检查的一部分，应实时筛查客户是否涉及制裁或恐怖名单

[v7u_N004312|4312] If the customer is identified as a PEP, the organization may need to conduct additional due diligence.
ZH: 若客户被识别为政治敏感人物，机构可能需要进行额外的尽职调查

[v7u_N004313|4313] Batch screening is a process of screening the organization’s entire customer base against sanctions and terror lists.
ZH: 批量筛查是对机构整个客户群进行制裁和恐怖名单筛查的过程

[v7u_N004314|4314] Organizations also screen customers against specific watch lists and PEP lists.
ZH: 机构还会针对特定观察名单和政治敏感人物名单进行筛查

[v7u_N004315|4315] Batch screening of existing customers is necessary because a customer may have been added to a sanctions or watch list since being onboarded. The only way an organization can know about the customer’s change in status is by batch screening.
ZH: 对现有客户进行批量筛查是必要的，因为客户可能在准入后被列入制裁或观察名单

[v7u_N004316|4316] Organizations use both real-time and batch screening because they serve different purposes. Real-time screening is necessary for payments that organizations must detect and block immediately. Batch screening identifies existing customers who have been added to sanctions or watch lists.
ZH: 实时筛查用于立即拦截支付，批量筛查用于识别已列入制裁或观察名单的现有客户

[v7u_N004317|4317] Maintaining effective screening technology helps organizations prevent and detect financial crimes such as money laundering, terrorist financing, and sanctions evasion.
ZH: 维持有效的筛查技术有助于机构预防和检测洗钱、恐怖融资和制裁规避等金融犯罪

[v7u_N004318|4318] The choice of technology depends on the scale of transaction volume, business type, and risk profile.
ZH: 筛查技术的选择取决于交易量规模、业务类型和风险状况

[v7u_N004319|4319] Technologies range from simple tools to large-scale systems maintained by dedicated IT teams that perform real-time screening and batch screening. These systems rely on current databases, automated updates, and advanced analytics to minimize false positives and ensure regulatory compliance.
ZH: 筛查技术从简单工具到大型系统不等，依赖最新数据库、自动更新和高级分析以减少误报

[v7u_N004320|4320] Small businesses with limited clientele might only need a simple solution connected to a website of the local jurisdiction, such as the US Department of the Treasury, which screens customers against the OFAC and UN sanctions lists.
ZH: 客户群有限的小型企业可能只需连接当地司法管辖区网站的简单解决方案

[v7u_N004321|4321] However, basic solutions work only for organizations with low transaction volumes and low-risk exposure.
ZH: 基础解决方案仅适用于低交易量和低风险敞口的机构。

[v7u_N004322|4322] As customer and transaction volumes increase, organizations require more sophisticated systems to maintain efficiency and accuracy.
ZH: 随着客户和交易量增长，机构需要更复杂的系统来保持效率和准确性。

[v7u_N004323|4323] In contrast, large financial institutions, such as banks issuing credit cards, require advanced technology to manage high volumes of daily transactions and large numbers of customers. These organizations use large databases integrated with vendor software platforms capable of both real-time and batch screening.
ZH: 大型金融机构使用先进技术管理高交易量，并集成实时与批量筛查平台。

[v7u_N004324|4324] Additionally, organizations use fuzzy logic to identify inexact matches, which often result from inadvertent or deliberate variations in spelling or numbers.
ZH: 机构使用模糊逻辑识别拼写或数字的近似匹配。

[v7u_N004325|4325] Organizations need to regularly tune their fuzzy logic algorithms to balance detection accuracy with minimizing false positives.
ZH: 机构需要定期调整模糊逻辑算法以平衡检测准确性与减少误报。

[v7u_N004326|4326] This will also ensure that the screening system is not delaying legitimate transactions.
ZH: 调整算法可确保筛查系统不延迟合法交易。

[v7u_N004327|4327] AI enhances these systems by prioritizing screening results, detecting anomalies, and reducing false positives.
ZH: 人工智能通过优先排序筛查结果、检测异常和减少误报来增强系统。

[v7u_N004328|4328] Using these ongoing screening technologies, large financial institutions can maintain compliance with regulatory requirements while efficiently managing the risks of high transaction volumes.
ZH: 持续筛查技术帮助大型金融机构在管理高交易量风险的同时保持合规。

[v7u_N004329|4329] Payment screening helps prevent and detect financial crimes while ensuring compliance with regulatory requirements.
ZH: 支付筛查有助于预防和检测金融犯罪并确保合规。

[v7u_N004330|4330] Financial institutions and payment processors use advanced screening tools to monitor transactions against sanctions lists, PEP databases, and other risk indicators.
ZH: 金融机构使用高级筛查工具监控制裁名单、政治敏感人物数据库及其他风险指标。

[v7u_N004331|4331] These systems integrate seamlessly with global payment networks such as SWIFT, CHAPS, RTGS, CHIPS, and Fedwire.
ZH: 这些系统与SWIFT、CHAPS、RTGS、CHIPS和Fedwire等全球支付网络无缝集成。

[v7u_N004332|4332] They use structured message formats such as XML to facilitate real-time payment screening.
ZH: 系统使用XML等结构化消息格式实现实时支付筛查。

[v7u_N004333|4333] By leveraging these technologies, financial institutions can identify and block potentially illicit transactions before processing them, reducing the risk of money laundering, terrorist financing, and sanctions violations.
ZH: 利用这些技术，金融机构可在处理前识别并阻止潜在非法交易，降低洗钱、恐怖融资和制裁违规风险。

[v7u_N004334|4334] The level of technological sophistication in payment screening depends on the institution’s application and risk profile.
ZH: 支付筛查的技术复杂程度取决于机构的应用和风险状况。

[v7u_N004335|4335] Simple, traditional tools with namematching techniques might suffice for small businesses with known clientele.
ZH: 对于客户已知的小型企业，简单的名称匹配工具可能足够。

[v7u_N004336|4336] However, for larger financial institutions handling millions of transactions, basic name matching is insufficient.
ZH: 对于处理数百万笔交易的大型金融机构，基本名称匹配不够用。

[v7u_N004337|4337] These organizations require more advanced methodologies, such as fuzzy logic algorithms. These algorithms enable approximate name matching, allowing for variations in spelling and transliteration errors.
ZH: 模糊逻辑算法允许近似名称匹配，处理拼写和音译差异。

[v7u_N004338|4338] Advanced AI tools can scan entire documents and transaction details to detect hidden risks. These tools help ensure that criminals do not exploit complex financial products and transactions for the purpose of evading sanctions or engaging in other illicit activities.
ZH: 高级AI工具可扫描整个文档和交易细节以检测隐藏风险，防止规避制裁等行为。

[v7u_N004339|4339] Although sophisticated technologies enhance detection capabilities, they also introduce challenges in calibration. A conservative approach with strict thresholds might result in high false positives, leading to inefficiencies and unnecessary transaction delays. Conversely, overly lenient thresholds might allow serious financial crimes to proceed undetected.
ZH: 复杂技术带来校准挑战：严格阈值导致高误报，宽松阈值可能漏掉严重犯罪。

[v7u_N004340|4340] Machine learning allows the system to learn from previous results to refine the parameters, helping to strike the right balance. This helps maintain regulatory compliance while minimizing disruptions to legitimate transactions. Financial institutions can use real-time updates to adjust and tune screening filters to continuously refine their screening models.
ZH: 机器学习从历史结果中学习以优化参数，实时更新帮助持续调整筛查模型。

[v7u_N004341|4341] The transfer of value in digital assets and currencies follows a structure similar to traditional financial transactions. It involves an originator, intermediaries, and a recipient.
ZH: 数字资产价值转移的结构与传统金融交易类似，涉及发起人、中介和接收方。

[v7u_N004342|4342] However, a key difference is the reliability and transparency of transaction information.
ZH: 数字资产交易与传统金融的关键区别在于交易信息的可靠性和透明度。

[v7u_N004343|4343] Traditional banking adheres to standardized KYC and AML protocols.
ZH: 传统银行业遵循标准化的了解你的客户和反洗钱协议。

[v7u_N004344|4344] Digital asset transactions may lack universally accepted compliance measures.
ZH: 数字资产交易可能缺乏普遍接受的合规措施。

[v7u_N004345|4345] Regulatory frameworks for digital asset transactions vary across jurisdictions.
ZH: 数字资产交易的监管框架因司法管辖区而异。

[v7u_N004346|4346] This causes inconsistencies in how jurisdictions verify and monitor transaction details. This variability creates enforcement gaps, making it difficult to apply the same level of scrutiny as in fiat currency transactions.
ZH: 监管差异导致验证和监控交易细节的不一致，造成执法漏洞。

[v7u_N004347|4347] Furthermore, the decentralized and borderless nature of digital assets complicates financial institutions’ ability to enforce compliance.
ZH: 数字资产的去中心化和无国界特性使金融机构难以执行合规。

[v7u_N004348|4348] Criminals exploit this regulatory arbitrage by operating in jurisdictions with lax oversight.
ZH: 犯罪分子利用监管套利，在监管宽松的司法管辖区运营。

[v7u_N004349|4349] A major challenge is the fundamental debate over the legitimacy of digital assets and currencies.
ZH: 数字资产合法性的根本性争论是主要挑战。

[v7u_N004350|4350] Many financial institutions remain skeptical, arguing that fiat currencies are backed by sovereign governments, which provides stability and assurance. Digital assets lack this backing.
ZH: 许多金融机构因数字资产缺乏主权政府支持而持怀疑态度。

[v7u_N004351|4351] This skepticism has led many traditional organizations to avoid digital asset transactions.
ZH: 这种怀疑导致许多传统机构避免数字资产交易。

[v7u_N004352|4352] Increasingly, financial institutions are expanding into offering cryptocurrencies, other blockchain-based assets, and associated services.
ZH: 金融机构正逐步扩展至加密货币及其他区块链资产和相关服务。

[v7u_N004353|4353] These organizations employ experts with deep knowledge of blockchain technology, transaction monitoring, and risk mitigation strategies specific to digital assets. Their expertise bridges the gap between evolving regulations and the technical complexities of blockchain transactions. This ensures rigorous digital asset screening that is comparable to traditional finance.
ZH: 这些机构雇佣区块链专家，确保数字资产筛查的严谨性，与传统金融相当。

[v7u_N004354|4354] Screening in digital asset transactions focuses on identifying high-risk third parties, particularly VASPs that operate outside regulatory frameworks.
ZH: 数字资产交易筛查侧重于识别高风险第三方，特别是监管框架外的VASP。

[v7u_N004355|4355] Many financial institutions maintain internal lists of unregistered or noncompliant entities. They refuse to engage with these entities to mitigate regulatory and reputational risks.
ZH: 许多金融机构维护未注册或不合规实体内部名单，并拒绝与其交易以降低风险。

[v7u_N004356|4356] The screening process involves analyzing blockchain addresses and transaction histories—or on-chain data—and using risk intelligence databases—or off-chain data—to detect illicit activities such as fraud, money laundering, and sanctions evasion.
ZH: 筛查过程结合链上数据和链下风险情报数据库，检测欺诈、洗钱和制裁规避。

[v7u_N004357|4357] However, the pseudonymous nature of many digital asset transactions may make ownership and identity verification challenging.
ZH: 数字资产交易的假名性质使所有权和身份验证具有挑战性。

[v7u_N004358|4358] This complexity requires advanced analytics and blockchain forensics to improve transparency and compliance efforts.
ZH: 这种复杂性需要高级分析和区块链取证来提高透明度和合规性。

[v7u_N004359|4359] As the regulatory environment for digital assets evolves, financial institutions must continuously update their screening capabilities.
ZH: 随着数字资产监管环境演变，金融机构必须持续更新筛查能力。

[v7u_N004360|4360] Adopting new technologies and regulatory best practices will help ensure compliance while maintaining operational efficiency.
ZH: 采用新技术和监管最佳实践有助于在保持运营效率的同时确保合规。
```

allowed_unit_ids:

```json
[
  "v7u_N004306",
  "v7u_N004307",
  "v7u_N004308",
  "v7u_N004309",
  "v7u_N004310",
  "v7u_N004311",
  "v7u_N004312",
  "v7u_N004313",
  "v7u_N004314",
  "v7u_N004315",
  "v7u_N004316",
  "v7u_N004317",
  "v7u_N004318",
  "v7u_N004319",
  "v7u_N004320",
  "v7u_N004321",
  "v7u_N004322",
  "v7u_N004323",
  "v7u_N004324",
  "v7u_N004325",
  "v7u_N004326",
  "v7u_N004327",
  "v7u_N004328",
  "v7u_N004329",
  "v7u_N004330",
  "v7u_N004331",
  "v7u_N004332",
  "v7u_N004333",
  "v7u_N004334",
  "v7u_N004335",
  "v7u_N004336",
  "v7u_N004337",
  "v7u_N004338",
  "v7u_N004339",
  "v7u_N004340",
  "v7u_N004341",
  "v7u_N004342",
  "v7u_N004343",
  "v7u_N004344",
  "v7u_N004345",
  "v7u_N004346",
  "v7u_N004347",
  "v7u_N004348",
  "v7u_N004349",
  "v7u_N004350",
  "v7u_N004351",
  "v7u_N004352",
  "v7u_N004353",
  "v7u_N004354",
  "v7u_N004355",
  "v7u_N004356",
  "v7u_N004357",
  "v7u_N004358",
  "v7u_N004359",
  "v7u_N004360"
]
```

original_json:

```json
{
  "section_id": "CH56-S01",
  "section_title": "Technology for payment and batch screening > Types of ongoing screening",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N004311"
      ],
      "proposition": "在客户准入时，机构应对客户进行实时制裁/恐怖名单筛查",
      "decision": "p7c_card",
      "card_id": "p7card_CH56-S01_001",
      "reason": "原文明示特定时机（准入）触发策略性动作（实时筛查），基础KG可保存规则但无法表达内部的时机-动作有向关系。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N004312"
      ],
      "proposition": "如果被识别为PEP，机构可能需要进行额外尽职调查",
      "decision": "p7c_card",
      "card_id": "p7card_CH56-S01_002",
      "reason": "原文明示分类结论如何触发后续动作，构成判断-应对有向链，超出基础KG表达能力。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N004316"
      ],
      "proposition": "对于需要立即阻止的支付，机构需使用实时筛查",
      "decision": "kg_only",
      "card_id": null,
      "reason": "原文仅描述实时筛查的功能和必要性，未形成特定主体在具体情境下的条件-动作有向结构，基础KG可充分表达为功能事实。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N004359"
      ],
      "proposition": "数字资产监管环境演变促使金融机构必须持续更新筛查能力",
      "decision": "p7c_card",
      "card_id": "p7card_CH56-S01_003",
      "reason": "原文明示外部环境变化如何触发机构特定更新义务，形成触发-应对有向链，超出KG表达能力。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH56-S01_001",
      "section_id": "CH56-S01",
      "card_nature": "execution",
      "title": "在客户准入时执行实时筛查",
      "flow_nodes": [
        {
          "node_id": "E1_onboarding",
          "node_category": "entry",
          "node_type": "E2_object_entry",
          "label": "客户准入事件",
          "evidence_unit_ids": [
            "v7u_N004311"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P1_realtime_screening",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构对客户进行实时制裁/恐怖名单筛查",
          "evidence_unit_ids": [
            "v7u_N004311"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_001",
          "edge_type": "PRECEDES",
          "source": "E1_onboarding",
          "target": "P1_realtime_screening",
          "evidence_unit_ids": [
            "v7u_N004311"
          ],
          "derivation": "explicit_text",
          "condition": "当机构办理客户准入手续时",
          "source_quote": "When an organization onboards a customer, as part of its KYC checks it should screen the customer in real time against sanctions or terror lists."
        }
      ],
      "source_unit_ids": [
        "v7u_N004311"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：客户准入事件 --PRECEDES（条件：准入时）--> 实时筛查动作；KG不足：基础KG可表达'实时筛查用于客户准入'的一般事实，但无法表达准入事件触发筛查动作的时间条件和方向关系；选项判断：可确认客户准入时是否必须执行实时筛查；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH56-S01_002",
      "section_id": "CH56-S01",
      "card_nature": "execution",
      "title": "客户被识别为PEP后可能进行额外尽职调查",
      "flow_nodes": [
        {
          "node_id": "E1_pep_identified",
          "node_category": "entry",
          "node_type": "E8_decision_finding",
          "label": "客户被识别为政治敏感人物（PEP）",
          "evidence_unit_ids": [
            "v7u_N004312"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P1_edd",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构：进行额外尽职调查（EDD）",
          "evidence_unit_ids": [
            "v7u_N004312"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_001",
          "edge_type": "PRECEDES",
          "source": "E1_pep_identified",
          "target": "P1_edd",
          "evidence_unit_ids": [
            "v7u_N004312"
          ],
          "derivation": "explicit_text",
          "condition": "如果客户被识别为PEP",
          "source_quote": "If the customer is identified as a PEP, the organization may need to conduct additional due diligence."
        }
      ],
      "source_unit_ids": [
        "v7u_N004312"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：PEP识别结论 --PRECEDES（条件：若识别为PEP）--> 额外尽调义务；KG不足：基础KG可保存'PEP需加强尽调'的一般规则，但无法表达分类结论如何触发后续动作的有向判断链；选项判断：可确认识别为PEP后是否需要进行额外尽调；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH56-S01_003",
      "section_id": "CH56-S01",
      "card_nature": "execution",
      "title": "监管环境演变推动金融机构更新筛查能力",
      "flow_nodes": [
        {
          "node_id": "E1_regulatory_evolve",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "数字资产监管环境演变",
          "evidence_unit_ids": [
            "v7u_N004359"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P1_update_capabilities",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "金融机构：持续更新筛查能力",
          "evidence_unit_ids": [
            "v7u_N004359"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_001",
          "edge_type": "PRECEDES",
          "source": "E1_regulatory_evolve",
          "target": "P1_update_capabilities",
          "evidence_unit_ids": [
            "v7u_N004359"
          ],
          "derivation": "explicit_text",
          "condition": "随着监管环境演变",
          "source_quote": "As the regulatory environment for digital assets evolves, financial institutions must continuously update their screening capabilities."
        }
      ],
      "source_unit_ids": [
        "v7u_N004359"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：监管环境演变 --PRECEDES（条件：监管环境演变）--> 机构必须更新筛查能力；KG不足：基础KG可表达监管演变需更新技术的一般关系，但无法表达环境变化触发机构特定更新义务的方向和强制性；选项判断：可确认在监管演变时金融机构是否有更新筛查能力的义务；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_003"
]
```

