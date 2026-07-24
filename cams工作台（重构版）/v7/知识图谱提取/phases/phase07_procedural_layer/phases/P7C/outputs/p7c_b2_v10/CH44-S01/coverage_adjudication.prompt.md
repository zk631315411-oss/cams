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

section_id: `CH44-S01`

section_title: `Ongoing AFC controls > Ongoing due diligence`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "持续尽职调查与定期KYC审查",
      "title_en": "Ongoing Due Diligence and Periodic KYC Reviews",
      "covered_units": [
        {
          "unit_id": "v7u_N003132",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N003134",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N003135",
          "unit_type": "classification",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N003133",
          "unit_type": "classification",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003136",
          "unit_type": "risk_indicator",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N003137",
          "unit_type": "fact",
          "kg_role": "illustrates"
        }
      ]
    },
    {
      "title_zh": "支付筛查",
      "title_en": "Payment Screening",
      "covered_units": [
        {
          "unit_id": "v7u_N003138",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N003139",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003140",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003141",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N003142",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N003143",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003144",
          "unit_type": "definition",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003145",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003146",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003147",
          "unit_type": "definition",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003148",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003149",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003150",
          "unit_type": "definition",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N003151",
          "unit_type": "process",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N003152",
          "unit_type": "definition",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003153",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003154",
          "unit_type": "process",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003155",
          "unit_type": "process",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003156",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003157",
          "unit_type": "case",
          "kg_role": "illustrates"
        }
      ]
    },
    {
      "title_zh": "批量筛查",
      "title_en": "Batch Screening",
      "covered_units": [
        {
          "unit_id": "v7u_N003158",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N003161",
          "unit_type": "fact",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003170",
          "unit_type": "fact",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003164",
          "unit_type": "fact",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N003165",
          "unit_type": "fact",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N003159",
          "unit_type": "classification",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N003160",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N003162",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003163",
          "unit_type": "classification",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N003166",
          "unit_type": "fact",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N003167",
          "unit_type": "risk_indicator",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N003168",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003169",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "持续尽职调查与定期KYC审查",
      "target_title": "支付筛查",
      "relation_type": "contains"
    },
    {
      "source_title": "持续尽职调查与定期KYC审查",
      "target_title": "批量筛查",
      "relation_type": "contains"
    },
    {
      "source_title": "支付筛查",
      "target_title": "批量筛查",
      "relation_type": "parallels"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N003132|3132] Ongoing due diligence is a process that ensures financial institutions regularly update customer risk assessments, monitor customer transactions, and identify suspicious behavior to maintain compliance with AFC regulations.
ZH: 持续尽职调查的定义：确保金融机构定期更新客户风险评估、监控交易并识别可疑行为

[v7u_N003133|3133] Unlike the customer due diligence undertaken at onboarding, ongoing due diligence is an evolving process that responds to risk changes, financial crime threats, and regulatory developments.
ZH: 持续尽职调查与开户时客户尽职调查的区别：前者是应对风险变化的动态过程

[v7u_N003134|3134] Ongoing due diligence consists of several critical monitoring mechanisms, including periodic KYC reviews, trigger event reviews, real-time payment screening, batch screening, perpetual KYC, and advanced compliance technologies.
ZH: 持续尽职调查的关键监控机制包括定期了解你的客户审查、触发事件审查、实时支付筛查等

[v7u_N003135|3135] Periodic KYC reviews take place at regular intervals, based on the customer’s risk level. Financial institutions must review and update customer information, ownership structures, business activities, and risk classifications. For example:
ZH: 定期了解你的客户审查：根据客户风险等级定期更新客户信息、所有权结构、业务活动和风险分类

[v7u_N003136|3136] High-risk customers are typically reviewed annually.
ZH: 高风险客户通常每年审查一次

[v7u_N003137|3137] Medium-risk customers are typically reviewed every two to three years.
ZH: 中风险客户通常每两到三年审查一次

[v7u_N003138|3138] Payment or transaction screening is the process of verifying transactions, both incoming and outgoing, to prevent financial crime. It is a primary financial crime control for organizations that facilitate the transfer of funds for their customers, or on behalf of another entity.
ZH: 支付筛查的定义：验证进出交易以防止金融犯罪，是资金转移机构的主要金融犯罪控制措施

[v7u_N003139|3139] Organizations are required to perform payment screening to prevent sanctions breaches and the financing of terrorism.
ZH: 机构必须进行支付筛查以防止违反制裁和恐怖融资

[v7u_N003140|3140] Each entity handling the transaction in a payment chain is required to conduct payment screening.
ZH: 支付链中处理交易的每个实体都必须进行支付筛查

[v7u_N003141|3141] The originating bank is the organization sending the funds.
ZH: 汇出行是发送资金的机构。

[v7u_N003142|3142] The beneficiary bank is the organization receiving the funds on behalf of its customers.
ZH: 收款行是代表客户接收资金的机构。

[v7u_N003143|3143] Both organizations screen the payment against any relevant lists.
ZH: 汇出行和收款行均需对付款进行名单筛查。

[v7u_N003144|3144] Payment screening identifies the risk of individuals, entities, or jurisdictions for payments an organization sends or receives.
ZH: 付款筛查用于识别付款中涉及的个人、实体或司法管辖区的风险。

[v7u_N003145|3145] Payments carry varying levels of risk that depend on several factors, such as jurisdiction and purpose of payment.
ZH: 付款的风险水平取决于司法管辖区和付款目的等因素。

[v7u_N003146|3146] A compliance officer must determine which transactions to accept based on the organization’s risk appetite.
ZH: 合规官必须根据机构的风险偏好决定接受哪些交易。

[v7u_N003147|3147] Payments are typically structured messages of data containing complete information about the payment.
ZH: 付款是包含完整支付信息的结构化数据消息。

[v7u_N003148|3148] Such information might include financial institutions involved, sending and receiving parties, amounts, dates, currencies, address, and free text information.
ZH: 付款信息可能包括参与的金融机构、发送方和接收方、金额、日期、货币、地址和自由文本。

[v7u_N003149|3149] Each payment has multiple messages. One message carries the transfer of funds information. The other transaction messages are used to request and send instructions through the payment network.
ZH: 每笔付款包含多条消息，分别用于资金转移和指令传输。

[v7u_N003150|3150] Payment screening is usually an automated, real-time process. This means the system screens payments as they are initiated and before they are completed.
ZH: 付款筛查通常是自动化的实时流程，在付款发起时和完成前进行筛查。

[v7u_N003151|3151] If the system identifies any preset match, the transaction will be held, investigated, and, if necessary, blocked.
ZH: 若系统识别到预设匹配，交易将被暂挂、调查并在必要时阻止。

[v7u_N003152|3152] Payment screening systems, such as the one shown, match transactions against list data.
ZH: 付款筛查系统将交易与名单数据进行匹配。

[v7u_N003153|3153] The matching configuration is based on message types and fields within a message.
ZH: 匹配配置基于消息类型和消息内的字段。

[v7u_N003154|3154] The system compares entity names on the list to the entity names on the transaction.
ZH: 系统将名单上的实体名称与交易中的实体名称进行比较。

[v7u_N003155|3155] Similarly, the system matches bank identifier codes (BIC) on the sanctioned list against the sending and receiving BIC in the payment message.
ZH: 系统将制裁名单上的银行识别码与付款消息中的发送和接收BIC进行匹配。

[v7u_N003156|3156] The message type might identify the nature of the payment. This could change the configuration.
ZH: 消息类型可能识别付款性质，从而改变筛查配置。

[v7u_N003157|3157] For example, if it is a trade finance transaction, you would screen against dual-use goods lists as well as additional high-risk vessel data.
ZH: 例如，贸易融资交易需额外筛查两用物品清单和高风险船舶数据。

[v7u_N003158|3158] Batch screening is a critical process and component in AFC compliance, allowing financial institutions to systematically review customer databases against updated sanctions lists, PEP lists, and adverse media sources. Unlike real-time transaction monitoring, batch screening is conducted at scheduled intervals to detect newly sanctioned individuals, evolving high-risk customers, and emerging financial crime threats.
ZH: 批量筛查是金融犯罪合规的关键流程，定期对客户数据库进行制裁、政治敏感人物和负面新闻筛查。

[v7u_N003159|3159] Batch screening is essential for:
ZH: 批量筛查对于以下方面至关重要：

[v7u_N003160|3160] Identifying emerging risks: Customers previously classified as low risk might become high risk due to sanctions, criminal investigations, or political exposure.
ZH: 识别新兴风险：之前低风险的客户可能因制裁、刑事调查或政治暴露而变为高风险。

[v7u_N003161|3161] Regulatory compliance: Financial institutions must comply with AFC obligations outlined by FinCEN, OFAC, the EU AML Directives, or other relevant regulatory bodies.
ZH: 金融机构必须遵守FinCEN、OFAC、欧盟反洗钱指令等监管机构规定的金融犯罪防控义务。

[v7u_N003162|3162] Preventing financial crime: Batch screening helps identify links to money laundering, terrorist financing, and fraud, ensuring institutions do not inadvertently facilitate illicit transactions.
ZH: 批量筛查有助于识别与洗钱、恐怖融资和欺诈的关联，防止机构无意中促成非法交易。

[v7u_N003163|3163] Batch screening follows a structured, automated process using compliance software:
ZH: 批量筛查遵循使用合规软件的结构化自动化流程。

[v7u_N003164|3164] Data extraction: Retrieving customer identities, identification numbers, and associated business relationships from internal databases.
ZH: 数据提取：从内部数据库检索客户身份、识别号及相关业务关系。

[v7u_N003165|3165] List matching: Comparing customer details against international sanctions databases, such as lists from the UN, EU, OFAC, and others; watchlists; and adverse media sources.
ZH: 名单匹配：将客户详情与联合国、欧盟、OFAC等国际制裁数据库、观察名单及负面媒体来源进行比对。

[v7u_N003166|3166] False positive resolution: Screening algorithms flag potential matches, requiring manual verification by compliance teams. AI-driven technology systems might risk-rate matches, offering a prioritized list.
ZH: 误报处理：筛查算法标记潜在匹配项，需合规团队人工核实；AI系统可对匹配项进行风险评级并排序。

[v7u_N003167|3167] Escalation and reporting: High-risk entities are subjected to enhanced due diligence, and where necessary, suspicious activity reports are filed with FIUs if money laundering or other financial crime concerns arise. Sanctions violations will be reported to the relevant regulatory bodies. Those customers would typically be offboarded in accordance with the
ZH: 升级与报告：高风险实体接受强化尽职调查，必要时向金融情报机构提交可疑活动报告；制裁违规上报监管机构，客户通常被终止关系。

[v7u_N003168|3168] AI-driven screening solutions: When appropriately tested and implemented, an AI-driven system can provide improved accuracy, reducing false positives and enhancing detection of hidden risks.
ZH: AI驱动的筛查方案：经适当测试和部署后，可提高准确性，减少误报并增强对隐藏风险的检测。

[v7u_N003169|3169] Perpetual batch screening: Replaces periodic updates with continuous real-time monitoring for faster risk detection.
ZH: 持续批量筛查：以持续实时监控取代定期更新，实现更快的风险检测。

[v7u_N003170|3170] Jurisdictional mandates: Many regulators now require ongoing screening to ensure compliance with AFC frameworks.
ZH: 许多监管机构要求进行持续筛查以确保符合金融犯罪防控框架。
```

allowed_unit_ids:

```json
[
  "v7u_N003132",
  "v7u_N003133",
  "v7u_N003134",
  "v7u_N003135",
  "v7u_N003136",
  "v7u_N003137",
  "v7u_N003138",
  "v7u_N003139",
  "v7u_N003140",
  "v7u_N003141",
  "v7u_N003142",
  "v7u_N003143",
  "v7u_N003144",
  "v7u_N003145",
  "v7u_N003146",
  "v7u_N003147",
  "v7u_N003148",
  "v7u_N003149",
  "v7u_N003150",
  "v7u_N003151",
  "v7u_N003152",
  "v7u_N003153",
  "v7u_N003154",
  "v7u_N003155",
  "v7u_N003156",
  "v7u_N003157",
  "v7u_N003158",
  "v7u_N003159",
  "v7u_N003160",
  "v7u_N003161",
  "v7u_N003162",
  "v7u_N003163",
  "v7u_N003164",
  "v7u_N003165",
  "v7u_N003166",
  "v7u_N003167",
  "v7u_N003168",
  "v7u_N003169",
  "v7u_N003170"
]
```

original_json:

```json
{
  "section_id": "CH44-S01",
  "section_title": "Ongoing AFC controls > Ongoing due diligence",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N003135",
        "v7u_N003136",
        "v7u_N003137"
      ],
      "proposition": "机构根据客户风险等级进行定期KYC审查，高风险客户通常每年审查，中风险客户通常每两到三年审查。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S01_001",
      "reason": "风险等级约束审查义务和频率，构成判断性有向结构，超出基础KG单独事实的保存能力。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N003146"
      ],
      "proposition": "合规官必须根据机构的风险偏好决定接受哪些交易。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S01_002",
      "reason": "风险偏好作为标准直接约束决策动作，形成有向约束关系，基础KG无法表达这一过程性。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N003151"
      ],
      "proposition": "如果系统识别到预设匹配，则交易被暂挂、调查并在必要时阻止。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S01_003",
      "reason": "明确的条件触发动作链，基础KG可保存动作事实但无法表达条件触发的有向过程。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N003156"
      ],
      "proposition": "消息类型可能识别支付性质，从而改变筛查配置。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "这是一般知识关系，基础KG能够表达“消息类型影响配置”的事实，无明确主体动作和判断过程。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N003157"
      ],
      "proposition": "如果是贸易融资交易，需要额外筛查两用物品清单和高风险船舶数据。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S01_004",
      "reason": "特定交易类型导向额外筛查要求，构成条件-动作有向结构，基础KG无法表达这种条件分支。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N003164",
        "v7u_N003165",
        "v7u_N003166"
      ],
      "proposition": "批量筛查的自动化流程顺序为：数据提取、名单匹配、误报处理（人工核实及AI评级）。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S01_005",
      "reason": "三个步骤形成有向流程链，基础KG可分别保存步骤但无法表达它们之间的顺序和功能依赖。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N003167"
      ],
      "proposition": "当客户被识别为高风险实体时，机构实施强化尽职调查。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S01_006",
      "reason": "风险分类触发具体应对，构成分类-动作的有向关系，基础KG无法表达这种触发链。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N003167"
      ],
      "proposition": "若存在洗钱或其他金融犯罪疑虑，机构向金融情报机构提交可疑活动报告。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S01_007",
      "reason": "明确的触发条件导向报告动作，构成判断性有向结构，基础KG可保存报告义务但无法表达条件触发。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N003167"
      ],
      "proposition": "制裁违规发生时，机构向监管机构报告并通常终止客户关系。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S01_008",
      "reason": "违规事件触发报告和终止行动，构成事件-应对有向结构，超出基础KG孤立事实的表达。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N003168"
      ],
      "proposition": "AI驱动的筛查方案可提高准确性、减少误报并增强对隐藏风险的检测。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "描述技术效果，无主体动作或判断过程，属于一般知识。"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N003169"
      ],
      "proposition": "持续批量筛查以持续实时监控取代定期更新，实现更快风险检测。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "说明技术趋势和事实，无程序性有向结构。"
    },
    {
      "candidate_id": "cand_012",
      "unit_ids": [
        "v7u_N003170"
      ],
      "proposition": "许多监管机构要求进行持续筛查以确保合规。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性监管要求陈述，基础KG可保存为规则事实。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH44-S01_001",
      "section_id": "CH44-S01",
      "card_nature": "execution",
      "title": "机构根据客户风险等级定期审查KYC信息",
      "flow_nodes": [
        {
          "node_id": "N1",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "客户风险等级 (高风险/中风险)",
          "evidence_unit_ids": [
            "v7u_N003135"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "金融机构必须定期审查和更新客户信息、所有权结构、业务活动和风险分类",
          "evidence_unit_ids": [
            "v7u_N003135"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "REFERENCES",
          "source": "N2",
          "target": "N1",
          "evidence_unit_ids": [
            "v7u_N003135",
            "v7u_N003136",
            "v7u_N003137"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N003135",
        "v7u_N003136",
        "v7u_N003137"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构必须定期审查KYC信息，且基于客户风险等级；风险等级约束审查频率（高风险通常每年，中风险通常每两到三年）。基础KG不足：基础KG可保存风险频率事实，但无法表达风险等级约束审查义务及频率差异的有向结构。选项判断：可确认或排除机构审查频率与风险等级的关联。LLM推理：无。"
    },
    {
      "card_id": "p7card_CH44-S01_002",
      "section_id": "CH44-S01",
      "card_nature": "execution",
      "title": "合规官根据机构风险偏好决定接受交易",
      "flow_nodes": [
        {
          "node_id": "N1",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "机构的风险偏好",
          "evidence_unit_ids": [
            "v7u_N003146"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N2",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "合规官必须决定接受哪些交易",
          "evidence_unit_ids": [
            "v7u_N003146"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "REFERENCES",
          "source": "N2",
          "target": "N1",
          "evidence_unit_ids": [
            "v7u_N003146"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N003146"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：合规官必须基于机构风险偏好决定接受哪些交易。基础KG不足：基础KG可保存“合规官决定接受交易”，但无法表达风险偏好约束决策的过程。选项判断：可确认决策依据是风险偏好。LLM推理：无。"
    },
    {
      "card_id": "p7card_CH44-S01_003",
      "section_id": "CH44-S01",
      "card_nature": "execution",
      "title": "支付筛查系统预设匹配时交易被暂挂、调查和阻止",
      "flow_nodes": [
        {
          "node_id": "N1",
          "node_category": "entry",
          "node_type": "E8_decision_finding",
          "label": "系统识别到预设匹配",
          "evidence_unit_ids": [
            "v7u_N003151"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "交易被暂挂、调查，并在必要时阻止",
          "evidence_unit_ids": [
            "v7u_N003151"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "PRECEDES",
          "source": "N1",
          "target": "N2",
          "evidence_unit_ids": [
            "v7u_N003151"
          ],
          "derivation": "explicit_text",
          "condition": "如果系统识别到预设匹配"
        }
      ],
      "source_unit_ids": [
        "v7u_N003151"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：如果系统识别到预设匹配，则交易被暂挂、调查并在必要时阻止。基础KG不足：基础KG可保存“交易暂挂”等动作，但无法表达条件触发的有向链。选项判断：可确认触发暂挂的条件是预设匹配。LLM推理：无。"
    },
    {
      "card_id": "p7card_CH44-S01_004",
      "section_id": "CH44-S01",
      "card_nature": "execution",
      "title": "贸易融资交易需额外筛查两用物品清单和高风险船舶数据",
      "flow_nodes": [
        {
          "node_id": "N1",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "交易为贸易融资交易",
          "evidence_unit_ids": [
            "v7u_N003157"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "对两用物品清单和高风险船舶数据进行额外筛查",
          "evidence_unit_ids": [
            "v7u_N003157"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "PRECEDES",
          "source": "N1",
          "target": "N2",
          "evidence_unit_ids": [
            "v7u_N003157"
          ],
          "derivation": "explicit_text",
          "condition": "如果是贸易融资交易"
        }
      ],
      "source_unit_ids": [
        "v7u_N003157"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：若是贸易融资交易，需额外筛查两用物品清单和高风险船舶数据。基础KG不足：基础KG可保存清单内容，但无法表达条件-动作的有向结构。选项判断：可确认特定交易类型的额外筛查要求。LLM推理：无。"
    },
    {
      "card_id": "p7card_CH44-S01_005",
      "section_id": "CH44-S01",
      "card_nature": "execution",
      "title": "批量筛查的自动化流程：数据提取后进行名单匹配，然后进行误报处理",
      "flow_nodes": [
        {
          "node_id": "N1",
          "node_category": "process",
          "node_type": "P4_collection",
          "label": "系统从内部数据库提取客户身份、识别号和相关业务关系",
          "evidence_unit_ids": [
            "v7u_N003164"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N2",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "系统将客户详情与国际制裁数据库、观察名单及负面媒体来源进行匹配",
          "evidence_unit_ids": [
            "v7u_N003165"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N3",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "合规团队对算法标记的潜在匹配进行人工核实，AI系统可对其进行风险评级并提供优先列表",
          "evidence_unit_ids": [
            "v7u_N003166"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "PRECEDES",
          "source": "N1",
          "target": "N2",
          "evidence_unit_ids": [
            "v7u_N003164",
            "v7u_N003165"
          ],
          "derivation": "llm_inference"
        },
        {
          "edge_id": "E2",
          "edge_type": "PRECEDES",
          "source": "N2",
          "target": "N3",
          "evidence_unit_ids": [
            "v7u_N003165",
            "v7u_N003166"
          ],
          "derivation": "llm_inference"
        }
      ],
      "source_unit_ids": [
        "v7u_N003164",
        "v7u_N003165",
        "v7u_N003166"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：批量筛查遵循数据提取 -> 名单匹配 -> 误报处理的顺序流程。基础KG不足：基础KG可分别保存各步骤，但无法表达步骤间的顺序依赖和功能先后。选项判断：可确认或排除筛查步骤的顺序。LLM推理：边E1和E2为llm_inference，因原文顺序描述未用明确时序词，但功能上数据提取是匹配的前提，匹配是误报处理的前提，别无合理替代。"
    },
    {
      "card_id": "p7card_CH44-S01_006",
      "section_id": "CH44-S01",
      "card_nature": "execution",
      "title": "当识别为高风险实体时，实施强化尽职调查",
      "flow_nodes": [
        {
          "node_id": "N1",
          "node_category": "entry",
          "node_type": "E8_decision_finding",
          "label": "客户被归类为高风险实体",
          "evidence_unit_ids": [
            "v7u_N003167"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构实施强化尽职调查",
          "evidence_unit_ids": [
            "v7u_N003167"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "PRECEDES",
          "source": "N1",
          "target": "N2",
          "evidence_unit_ids": [
            "v7u_N003167"
          ],
          "derivation": "llm_inference"
        }
      ],
      "source_unit_ids": [
        "v7u_N003167"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：客户被识别为高风险实体后，机构需实施强化尽职调查。基础KG不足：基础KG可保存“强化尽职调查”这个概念，但无法表达风险分类触发具体应对的有向关系。选项判断：可确认高风险实体的应对措施。LLM推理：边从entry到process为llm_inference，因原文被动语态未用if-then，但逻辑上高风险实体状态引发EDD，别无解释。"
    },
    {
      "card_id": "p7card_CH44-S01_007",
      "section_id": "CH44-S01",
      "card_nature": "execution",
      "title": "当存在洗钱或其他金融犯罪疑虑时，向FIU提交可疑活动报告",
      "flow_nodes": [
        {
          "node_id": "N1",
          "node_category": "entry",
          "node_type": "E8_decision_finding",
          "label": "发现洗钱或其他金融犯罪疑虑",
          "evidence_unit_ids": [
            "v7u_N003167"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构向金融情报机构提交可疑活动报告",
          "evidence_unit_ids": [
            "v7u_N003167"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "PRECEDES",
          "source": "N1",
          "target": "N2",
          "evidence_unit_ids": [
            "v7u_N003167"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N003167"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：若存在洗钱或金融犯罪疑虑，机构向FIU提交SAR。基础KG不足：基础KG可保存提交SAR的义务，但无法表达条件触发关系。选项判断：可确认提交SAR的条件是存在金融犯罪疑虑。LLM推理：无。"
    },
    {
      "card_id": "p7card_CH44-S01_008",
      "section_id": "CH44-S01",
      "card_nature": "execution",
      "title": "制裁违规时向监管机构报告并通常终止客户关系",
      "flow_nodes": [
        {
          "node_id": "N1",
          "node_category": "entry",
          "node_type": "E8_decision_finding",
          "label": "发现制裁违规",
          "evidence_unit_ids": [
            "v7u_N003167"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构向相关监管机构报告并通常终止客户关系",
          "evidence_unit_ids": [
            "v7u_N003167"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "PRECEDES",
          "source": "N1",
          "target": "N2",
          "evidence_unit_ids": [
            "v7u_N003167"
          ],
          "derivation": "llm_inference"
        }
      ],
      "source_unit_ids": [
        "v7u_N003167"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：制裁违规发生时，机构向监管报告并通常终止客户关系。基础KG不足：基础KG可分别保存报告和终止义务，但无法表达违规识别触发应对的有向关系。选项判断：可确认制裁违规的后续行动。LLM推理：边为llm_inference，原文没有明示if-then，但从语境推断违规触发报告和终止。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_004",
  "cand_010",
  "cand_011",
  "cand_012"
]
```

