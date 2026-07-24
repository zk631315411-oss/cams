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

section_id: `CH56-S05`

section_title: `Technology for payment and batch screening > Transaction monitoring and sufficient scenarios coverage`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "基于产品风险评估的场景开发",
      "title_en": "Scenario Development from Product Risk Assessment",
      "covered_units": [
        {
          "unit_id": "v7u_N004412",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N004413",
          "unit_type": "process",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004414",
          "unit_type": "rule",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "定制化和动态更新的场景",
      "title_en": "Customized and Updated Scenarios",
      "covered_units": [
        {
          "unit_id": "v7u_N004415",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004416",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        }
      ]
    },
    {
      "title_zh": "额外的场景开发输入",
      "title_en": "Additional Scenario Inputs",
      "covered_units": [
        {
          "unit_id": "v7u_N004417",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004418",
          "unit_type": "rule",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "场景覆盖不足的风险",
      "title_en": "Risk of Insufficient Scenario Coverage",
      "covered_units": [
        {
          "unit_id": "v7u_N004419",
          "unit_type": "risk_indicator",
          "kg_role": "states_consequence"
        }
      ]
    },
    {
      "title_zh": "有效监控场景的要求",
      "title_en": "Requirements for Effective Monitoring Scenarios",
      "covered_units": [
        {
          "unit_id": "v7u_N004420",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004421",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004422",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004423",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        }
      ]
    },
    {
      "title_zh": "针对不断演变的威胁的供应商交易监控系统",
      "title_en": "Vendor TM Systems for Evolving Threats",
      "covered_units": [
        {
          "unit_id": "v7u_N004424",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004425",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004426",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "文档记录与面向未来的保障",
      "title_en": "Documentation and Future-Proofing",
      "covered_units": [
        {
          "unit_id": "v7u_N004427",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004428",
          "unit_type": "process",
          "kg_role": "prescribes_measure"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "基于产品风险评估的场景开发",
      "target_title": "定制化和动态更新的场景",
      "relation_type": "prepares"
    },
    {
      "source_title": "基于产品风险评估的场景开发",
      "target_title": "额外的场景开发输入",
      "relation_type": "prepares"
    },
    {
      "source_title": "基于产品风险评估的场景开发",
      "target_title": "有效监控场景的要求",
      "relation_type": "prepares"
    },
    {
      "source_title": "定制化和动态更新的场景",
      "target_title": "有效监控场景的要求",
      "relation_type": "prepares"
    },
    {
      "source_title": "额外的场景开发输入",
      "target_title": "有效监控场景的要求",
      "relation_type": "prepares"
    },
    {
      "source_title": "场景覆盖不足的风险",
      "target_title": "有效监控场景的要求",
      "relation_type": "prepares"
    },
    {
      "source_title": "有效监控场景的要求",
      "target_title": "针对不断演变的威胁的供应商交易监控系统",
      "relation_type": "prepares"
    },
    {
      "source_title": "针对不断演变的威胁的供应商交易监控系统",
      "target_title": "文档记录与面向未来的保障",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N004412|4412] To detect financial crimes, financial institutions must ensure their TM systems cover a wide range of scenarios that reflect their current and potential future risk exposures. Scenarios help TM systems recognize various types of illicit activity.
ZH: 金融机构必须确保交易监控系统覆盖广泛场景以检测金融犯罪

[v7u_N004413|4413] This requires conducting a comprehensive product risk assessment to identify vulnerabilities and tailor monitoring rules according to the risk exposure.
ZH: 进行全面的产品风险评估以识别漏洞并定制监控规则

[v7u_N004414|4414] Institutions need technical skills to convert the results of a product risk assessment into scenarios that provide appropriate coverage for the identified risks.
ZH: 机构需要技术能力将风险评估结果转化为适当的监控场景

[v7u_N004415|4415] A one-size-fits-all approach is inadequate because different institutions face varying levels of risk depending on their customers, jurisdictions, products, and delivery channels.
ZH: 一刀切方法不适用，因客户、地域、产品和渠道风险各异

[v7u_N004416|4416] Additionally, these factors change over time. It is necessary to regularly review and update scenarios proactively.
ZH: 必须定期主动审查和更新场景以应对风险因素变化

[v7u_N004417|4417] In addition to product risk assessment, other key risk indicators, such as customer demographics, transactional behavior, and regulatory requirements, should guide scenario development.
ZH: 场景开发应参考客户人口统计、交易行为和监管要求等关键风险指标

[v7u_N004418|4418] Institutions should also analyze law enforcement and government risk reports, such as those from the US Treasury and FinCEN, national money laundering risk assessments, and peer discussions to help develop actionable monitoring scenarios.
ZH: 应分析执法和政府风险报告以制定可操作的监控场景

[v7u_N004419|4419] Without sufficient scenario coverage, financial institutions risk missing critical red flags. This could lead to compliance failures and expose institutions to illicit activities such as money laundering, terrorist financing, and fraud.
ZH: 场景覆盖不足可能导致遗漏红旗信号信号，增加洗钱、恐怖融资和欺诈风险

[v7u_N004420|4420] To ensure TM systems are robust and responsive, institutions must develop risk-based scenarios that adapt to evolving financial crime tactics.
ZH: 机构必须开发基于风险的场景以适应不断变化的金融犯罪手法

[v7u_N004421|4421] High-risk customers, such as PEPs, shell companies, and entities operating in high-risk jurisdictions, require enhanced monitoring with specialized alerts.
ZH: 高风险客户如政治敏感人物和壳公司需要强化监控和专门警报。

[v7u_N004422|4422] Monitoring scenarios should also address suspicious transaction behaviors, including large cash deposits, frequent structuring (or "smurfing"), rapid fund movement between accounts, and cross-border transactions to high-risk regions.
ZH: 监控场景应覆盖可疑交易行为，包括大额现金存款、拆分交易、快速资金转移和跨境交易。

[v7u_N004423|4423] An effective system should detect both obvious violations and subtle behavioral shifts that could indicate emerging risks. It must also integrate historical transaction analysis and peer group comparisons to quickly flag deviations from expected behavior for further investigation.
ZH: 有效系统需检测明显违规和细微行为变化，并整合历史分析与同行比较。

[v7u_N004424|4424] A risk assessment can capture an institution’s risks at a specific time. However, AML risks are constantly evolving.
ZH: 风险评估捕捉特定时点的风险，但反洗钱风险持续演变。

[v7u_N004425|4425] A well-chosen vendor TM system should provide technology-driven monitoring, industry-wide research, and evolving threat intelligence.
ZH: 供应商交易监控系统应提供技术驱动监控、行业研究和威胁情报。

[v7u_N004426|4426] Vendors have access to data across multiple financial institutions. This allows them to identify emerging money laundering trends and recommend monitoring scenarios that a single institution might miss.
ZH: 供应商利用跨机构数据识别洗钱趋势并推荐监控场景。

[v7u_N004427|4427] Financial institutions must document their monitoring decisions and the rationale behind them for future justification, regulatory exams, and system validation.
ZH: 金融机构必须记录监控决策及其理由，以备监管检查和系统验证。

[v7u_N004428|4428] By combining vendor insights with internal risk assessments, financial institutions can future-proof their TM system. This approach ensures comprehensive scenario coverage, regulatory compliance, and proactive detection of financial crimes, strengthening the institution’s risk management framework.
ZH: 结合供应商洞察与内部风险评估，使交易监控系统面向未来。
```

allowed_unit_ids:

```json
[
  "v7u_N004412",
  "v7u_N004413",
  "v7u_N004414",
  "v7u_N004415",
  "v7u_N004416",
  "v7u_N004417",
  "v7u_N004418",
  "v7u_N004419",
  "v7u_N004420",
  "v7u_N004421",
  "v7u_N004422",
  "v7u_N004423",
  "v7u_N004424",
  "v7u_N004425",
  "v7u_N004426",
  "v7u_N004427",
  "v7u_N004428"
]
```

original_json:

```json
{
  "section_id": "CH56-S05",
  "section_title": "Technology for payment and batch screening > Transaction monitoring and sufficient scenarios coverage",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N004413",
        "v7u_N004414"
      ],
      "proposition": "金融机构进行全面产品风险评估以识别漏洞，并基于评估结果转化/定制监控场景。",
      "decision": "p7c_card",
      "card_id": "p7card_CH56-S05_001",
      "reason": "基础KG可能只保存为要求进行风险评估和定制规则，无法表达评估结果被转化使用的有向流程。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N004416"
      ],
      "proposition": "定期时间周期触发金融机构审查和更新监控场景。",
      "decision": "p7c_card",
      "card_id": "p7card_CH56-S05_002",
      "reason": "时间周期触发审查更新的有向结构，超出基础KG的静态措施保存。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N004417",
        "v7u_N004418",
        "v7u_N004422"
      ],
      "proposition": "金融机构开发监控场景时，应参考关键风险指标、执法报告及可疑交易行为类型等多种输入。",
      "decision": "p7c_card",
      "card_id": "p7card_CH56-S05_003",
      "reason": "多种风险信息作为输入指导场景开发，构成明确的process-REFERENCES-input结构。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N004420"
      ],
      "proposition": "金融机构开发基于风险的监控场景，以应对不断变化的金融犯罪手法。",
      "decision": "p7c_card",
      "card_id": "p7card_CH56-S05_004",
      "reason": "开发动作明确受“不断变化的犯罪手法”约束，形成有向约束关系。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N004421"
      ],
      "proposition": "当客户被识别为高风险（PEP、壳公司等）时，金融机构必须实施强化监控和专门警报。",
      "decision": "p7c_card",
      "card_id": "p7card_CH56-S05_005",
      "reason": "客户分类触发强化监控，典型的条件-动作有向链。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N004423"
      ],
      "proposition": "监控系统检测行为偏差并标记，标记触发进一步调查。",
      "decision": "p7c_card",
      "card_id": "p7card_CH56-S05_006",
      "reason": "检测分析产生偏差标记，标记触发进一步调查，完整过程链。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N004426"
      ],
      "proposition": "供应商利用跨机构数据识别洗钱趋势，并推荐监控场景。",
      "decision": "p7c_card",
      "card_id": "p7card_CH56-S05_007",
      "reason": "供应商识别趋势并推荐场景的明确动作-结果链。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N004427"
      ],
      "proposition": "金融机构记录监控决策及其理由，以应对未来监管检查与系统验证要求。",
      "decision": "p7c_card",
      "card_id": "p7card_CH56-S05_008",
      "reason": "记录动作受未来监管要求指引，构成有向约束关系。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N004419"
      ],
      "proposition": "场景覆盖不足会带来遗漏红旗、合规失败及暴露于洗钱等风险。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅陈述风险后果，无程序性或判断性有向结构。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N004415"
      ],
      "proposition": "一刀切方法不适用，因风险因客户、地域等因素而异。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "解释性陈述，无触发动作的主体或应对。"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N004424"
      ],
      "proposition": "风险评估捕捉特定时点的风险，但反洗钱风险持续演变。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "事实陈述，无有向动作链。"
    },
    {
      "candidate_id": "cand_012",
      "unit_ids": [
        "v7u_N004425"
      ],
      "proposition": "供应商TM系统应提供技术驱动监控、行业研究和威胁情报。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "对供应商系统的一般要求，无局部主体动作有向结构。"
    },
    {
      "candidate_id": "cand_013",
      "unit_ids": [
        "v7u_N004428"
      ],
      "proposition": "结合供应商洞察与内部风险评估使TM系统面向未来，确保全面覆盖与合规。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "综合效果描述，无具体节点和边。"
    },
    {
      "candidate_id": "cand_014",
      "unit_ids": [
        "v7u_N004412"
      ],
      "proposition": "金融机构必须确保TM系统覆盖广泛场景以检测金融犯罪。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "高层要求，未形成具体有向结构。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH56-S05_001",
      "section_id": "CH56-S05",
      "card_nature": "assessment",
      "title": "基于产品风险评估开发监控场景",
      "flow_nodes": [
        {
          "node_id": "node_card1_01",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "金融机构进行全面产品风险评估以识别漏洞",
          "evidence_unit_ids": [
            "v7u_N004413"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_card1_02",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "识别的风险漏洞/风险暴露",
          "evidence_unit_ids": [
            "v7u_N004413"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_card1_03",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "金融机构基于风险评估结果开发/定制监控场景",
          "evidence_unit_ids": [
            "v7u_N004414"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_card1_01",
          "edge_type": "PRODUCES",
          "source": "node_card1_01",
          "target": "node_card1_02",
          "evidence_unit_ids": [
            "v7u_N004413"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "edge_card1_02",
          "edge_type": "REFERENCES",
          "source": "node_card1_03",
          "target": "node_card1_02",
          "evidence_unit_ids": [
            "v7u_N004414"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004413",
        "v7u_N004414"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：金融机构进行全面产品风险评估 --PRODUCES--> 识别风险漏洞，然后金融机构基于识别结果 --REFERENCES--> 风险漏洞以转化/定制监控场景；KG不足：基础KG可将“基于产品风险评估开发场景”作为整体过程保存，但无法表达评估结果作为输入被转化使用的内部有向关系；选项判断：可确认产品风险评估是场景开发的前置步骤，其输出被用于场景定制，从而排除未使用评估结果或跳过评估直接开发的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH56-S05_002",
      "section_id": "CH56-S05",
      "card_nature": "control",
      "title": "定期审查和更新监控场景",
      "flow_nodes": [
        {
          "node_id": "node_card2_01",
          "node_category": "entry",
          "node_type": "E5_time_cycle",
          "label": "定期时间周期",
          "evidence_unit_ids": [
            "v7u_N004416"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_card2_02",
          "node_category": "process",
          "node_type": "P7_monitoring",
          "label": "金融机构定期主动审查并更新监控场景",
          "evidence_unit_ids": [
            "v7u_N004416"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_card2_01",
          "edge_type": "PRECEDES",
          "source": "node_card2_01",
          "target": "node_card2_02",
          "evidence_unit_ids": [
            "v7u_N004416"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004416"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：定期时间周期 --PRECEDES--> 金融机构审查和更新监控场景；KG不足：基础KG仅保存“需定期审查更新”的措施要求，但未表达时间触发有向链；选项判断：可确认审查更新由时间周期驱动，排除仅在特定事件触发时才更新的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH56-S05_003",
      "section_id": "CH56-S05",
      "card_nature": "execution",
      "title": "多种风险信息来源指导监控场景开发",
      "flow_nodes": [
        {
          "node_id": "node_card3_01",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "金融机构开发监控场景",
          "evidence_unit_ids": [
            "v7u_N004417",
            "v7u_N004418",
            "v7u_N004422"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_card3_02",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "关键风险指标（客户人口统计、交易行为、监管要求）",
          "evidence_unit_ids": [
            "v7u_N004417"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_card3_03",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "执法和政府风险报告",
          "evidence_unit_ids": [
            "v7u_N004418"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_card3_04",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "可疑交易行为类型（大额现金存款、拆分交易、快速资金转移、高风险地区跨境交易等）",
          "evidence_unit_ids": [
            "v7u_N004422"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_card3_01",
          "edge_type": "REFERENCES",
          "source": "node_card3_01",
          "target": "node_card3_02",
          "evidence_unit_ids": [
            "v7u_N004417"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "edge_card3_02",
          "edge_type": "REFERENCES",
          "source": "node_card3_01",
          "target": "node_card3_03",
          "evidence_unit_ids": [
            "v7u_N004418"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "edge_card3_03",
          "edge_type": "REFERENCES",
          "source": "node_card3_01",
          "target": "node_card3_04",
          "evidence_unit_ids": [
            "v7u_N004422"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004417",
        "v7u_N004418",
        "v7u_N004422"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：金融机构开发监控场景 --REFERENCES--> 关键风险指标、执法报告、可疑交易行为类型等输入；KG不足：基础KG可能将这些作为解释性知识，未表达为明确的过程-输入引用关系；选项判断：可确认场景开发应考虑多种输入，排除仅依赖单一来源的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH56-S05_004",
      "section_id": "CH56-S05",
      "card_nature": "execution",
      "title": "基于风险开发场景以应对不断变化的犯罪手法",
      "flow_nodes": [
        {
          "node_id": "node_card4_01",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "金融机构开发基于风险的监控场景",
          "evidence_unit_ids": [
            "v7u_N004420"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_card4_02",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "不断变化的金融犯罪手法",
          "evidence_unit_ids": [
            "v7u_N004420"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_card4_01",
          "edge_type": "REFERENCES",
          "source": "node_card4_01",
          "target": "node_card4_02",
          "evidence_unit_ids": [
            "v7u_N004420"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_transmits_requirement"
        }
      ],
      "source_unit_ids": [
        "v7u_N004420"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：金融机构开发基于风险的监控场景 --REFERENCES--> 不断变化的金融犯罪手法（作为标准约束）；KG不足：基础KG可能只保存开发基于风险场景的要求，未表达场景需适应犯罪手法变化的动态约束关系；选项判断：可确认场景必须适应变化，排除静态场景的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH56-S05_005",
      "section_id": "CH56-S05",
      "card_nature": "control",
      "title": "对高风险客户实施强化监控和专门警报",
      "flow_nodes": [
        {
          "node_id": "node_card5_01",
          "node_category": "entry",
          "node_type": "E1_event_signal",
          "label": "客户被识别为高风险（如PEP、壳公司、高风险地区实体）",
          "evidence_unit_ids": [
            "v7u_N004421"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_card5_02",
          "node_category": "process",
          "node_type": "P8_constrained_action",
          "label": "金融机构对该客户实施强化监控并设置专门警报",
          "evidence_unit_ids": [
            "v7u_N004421"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_card5_01",
          "edge_type": "PRECEDES",
          "source": "node_card5_01",
          "target": "node_card5_02",
          "evidence_unit_ids": [
            "v7u_N004421"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004421"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：客户被识别为高风险 --PRECEDES--> 金融机构实施强化监控和专门警报；KG不足：基础KG可将“高风险客户需强化监控”作为规则保存，但未表达分类触发监控动作的条件-动作有向链；选项判断：可确认强化监控仅适用于高风险客户，排除对所有客户普遍强化或低风险客户亦强化的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH56-S05_006",
      "section_id": "CH56-S05",
      "card_nature": "assessment",
      "title": "检测异常行为并标记偏差以触发调查",
      "flow_nodes": [
        {
          "node_id": "node_card6_01",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "金融机构（通过监控系统）检测明显违规和细微行为变化，并整合历史交易分析与同行比较",
          "evidence_unit_ids": [
            "v7u_N004423"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_card6_02",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "标记偏离预期的行为（偏差标记）",
          "evidence_unit_ids": [
            "v7u_N004423"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_card6_03",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "金融机构对标记的偏差进行进一步调查",
          "evidence_unit_ids": [
            "v7u_N004423"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_card6_01",
          "edge_type": "PRODUCES",
          "source": "node_card6_01",
          "target": "node_card6_02",
          "evidence_unit_ids": [
            "v7u_N004423"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "edge_card6_02",
          "edge_type": "PRECEDES",
          "source": "node_card6_02",
          "target": "node_card6_03",
          "evidence_unit_ids": [
            "v7u_N004423"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004423"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：监控系统检测违规和行为变化并整合分析 --PRODUCES--> 偏差标记，偏差标记 --PRECEDES--> 进一步调查；KG不足：基础KG可将“系统应检测并标记供调查”作为功能描述，但未表达标记作为分析结果并触发调查的先后有向链；选项判断：可确认检测分析在先，标记偏差是其直接结果，而后触发调查，排除调查与检测并行或无需标记直接调查的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH56-S05_007",
      "section_id": "CH56-S05",
      "card_nature": "execution",
      "title": "供应商基于跨机构数据识别洗钱趋势并推荐监控场景",
      "flow_nodes": [
        {
          "node_id": "node_card7_01",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "供应商（系统）利用跨机构数据识别新兴洗钱趋势并推荐监控场景",
          "evidence_unit_ids": [
            "v7u_N004426"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_card7_02",
          "node_category": "exit",
          "node_type": "X2_product",
          "label": "推荐的监控场景",
          "evidence_unit_ids": [
            "v7u_N004426"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_card7_01",
          "edge_type": "PRODUCES",
          "source": "node_card7_01",
          "target": "node_card7_02",
          "evidence_unit_ids": [
            "v7u_N004426"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004426"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：供应商利用跨机构数据识别洗钱趋势并推荐监控场景 --PRODUCES--> 推荐的监控场景；KG不足：基础KG可将供应商功能作为事实保存，但未表达识别推荐作为动作产生推荐结果的有向链；选项判断：可确认场景推荐是供应商的直接产出，排除供应商仅提供数据无推荐或场景完全由内部开发的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH56-S05_008",
      "section_id": "CH56-S05",
      "card_nature": "control",
      "title": "记录监控决策及其理由以备监管检查与系统验证",
      "flow_nodes": [
        {
          "node_id": "node_card8_01",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "金融机构记录监控决策及其理由",
          "evidence_unit_ids": [
            "v7u_N004427"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_card8_02",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "未来监管检查与系统验证要求",
          "evidence_unit_ids": [
            "v7u_N004427"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_card8_01",
          "edge_type": "REFERENCES",
          "source": "node_card8_01",
          "target": "node_card8_02",
          "evidence_unit_ids": [
            "v7u_N004427"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_transmits_requirement"
        }
      ],
      "source_unit_ids": [
        "v7u_N004427"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：金融机构记录监控决策及其理由 --REFERENCES--> 未来监管检查与系统验证要求（作为标准）；KG不足：基础KG仅保存记录要求，未表达记录动作是受监管检查需求指引的有向关系；选项判断：可确认记录的目的是为监管检查及验证，排除仅用于内部参考或可延迟记录的选项；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_009",
  "cand_010",
  "cand_011",
  "cand_012",
  "cand_013",
  "cand_014"
]
```

