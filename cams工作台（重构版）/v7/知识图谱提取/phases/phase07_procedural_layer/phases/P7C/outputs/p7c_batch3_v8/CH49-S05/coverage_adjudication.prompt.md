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

section_id: `CH49-S05`

section_title: `Concluding an investigation and suspicious activity reporting > Case example: SAR for a family trust`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "可疑活动监测与指标",
      "title_en": "Suspicious Activity Detection and Indicators",
      "covered_units": [
        {
          "unit_id": "v7u_N003529",
          "unit_type": "case",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N003530",
          "unit_type": "risk_indicator",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N003531",
          "unit_type": "risk_indicator",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N003532",
          "unit_type": "fact",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "SAR 所需信息",
      "title_en": "Information Required in a SAR",
      "covered_units": [
        {
          "unit_id": "v7u_N003533",
          "unit_type": "classification",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N003534",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N003535",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N003536",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N003537",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N003538",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N003539",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N003540",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N003541",
          "unit_type": "case",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N003542",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N003543",
          "unit_type": "case",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N003544",
          "unit_type": "risk_indicator",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "SAR 提交行动与要求",
      "title_en": "SAR Submission Actions and Requirements",
      "covered_units": [
        {
          "unit_id": "v7u_N003545",
          "unit_type": "fact",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N003547",
          "unit_type": "process",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N003549",
          "unit_type": "rule",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N003550",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N003552",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003553",
          "unit_type": "rule",
          "kg_role": "states_rule"
        }
      ]
    },
    {
      "title_zh": "洗钱分析与怀疑依据",
      "title_en": "Money Laundering Analysis and Suspicion Basis",
      "covered_units": [
        {
          "unit_id": "v7u_N003546",
          "unit_type": "case",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "SAR 叙述撰写最佳实践",
      "title_en": "SAR Narrative Writing Best Practices",
      "covered_units": [
        {
          "unit_id": "v7u_N003548",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003551",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003554",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "可疑活动监测与指标",
      "target_title": "洗钱分析与怀疑依据",
      "relation_type": "prepares"
    },
    {
      "source_title": "SAR 所需信息",
      "target_title": "洗钱分析与怀疑依据",
      "relation_type": "prepares"
    },
    {
      "source_title": "洗钱分析与怀疑依据",
      "target_title": "SAR 叙述撰写最佳实践",
      "relation_type": "prepares"
    },
    {
      "source_title": "洗钱分析与怀疑依据",
      "target_title": "SAR 提交行动与要求",
      "relation_type": "prepares"
    },
    {
      "source_title": "SAR 叙述撰写最佳实践",
      "target_title": "SAR 提交行动与要求",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N003529|3529] The downtown branch of North Bank detects unusual activity in the Citizen Family Trust account, including large withdrawals totaling millions of US dollars over a three-week period. The purpose of these transactions is unclear and inconsistent with the customer’s typical activity.
ZH: 北银行市中心分行发现Citizen家族信托账户出现异常活动，三周内大额取款数百万美元。

[v7u_N003530|3530] The large, rapid withdrawals combined with a high-risk source of funds, or windfall, suggest possible money laundering.
ZH: 大额快速取款结合高风险资金来源（意外之财）暗示可能洗钱。

[v7u_N003531|3531] The declared source of wealth and account behavior show inconsistencies.
ZH: 申报的财富来源与账户行为存在不一致。

[v7u_N003532|3532] There have been no previous SAR filings at this institution for this customer.
ZH: 该客户此前在该机构无SAR申报记录。

[v7u_N003533|3533] The MLRO gathers information to include in the initial SAR:
ZH: MLRO收集信息以纳入初始SAR。

[v7u_N003534|3534] Customers’ names and birthdates: Lola Citizen 03/25/1965; Malik Citizen 01/15/1964
ZH: 客户姓名和出生日期：Lola Citizen 1965年3月25日；Malik Citizen 1964年1月15日。

[v7u_N003535|3535] Addresses, phone numbers
ZH: 地址和电话号码。

[v7u_N003536|3536] Tax identification numbers
ZH: 税务识别号。

[v7u_N003537|3537] The account opening date: March 3, 2000
ZH: 账户开立日期：2000年3月3日。

[v7u_N003538|3538] Declared wealth and funds: Windfall, lottery, gambling
ZH: 申报的财富和资金：意外之财、彩票、赌博。

[v7u_N003539|3539] Names of the controlling persons: Lola Citizen 50%; Malik Citizen 50%
ZH: 控制人姓名：Lola Citizen 50%；Malik Citizen 50%。

[v7u_N003540|3540] Business relationship: Building wealth
ZH: 业务关系：积累财富。

[v7u_N003541|3541] The MLRO notes that both account holders are on the boards of directors of local companies.
ZH: MLRO 注意到两个账户持有人均为当地公司董事会成员。

[v7u_N003542|3542] The next section of the SAR requests information about the dates and amounts of the unusual transactions.
ZH: SAR 要求提供异常交易的日期和金额信息。

[v7u_N003543|3543] The MLRO indicated two dates in the past three weeks, with withdrawals totaling US$4.3 million and US$6.6 million, respectively.
ZH: MLRO 报告过去三周内两笔大额取款，金额分别为 430 万和 660 万美元。

[v7u_N003544|3544] These withdrawals were significantly larger than the typical transactions expected from a family trust, which is usually unregulated.
ZH: 来自未受监管家族信托的异常大额取款构成可疑指标。

[v7u_N003545|3545] The MLRO also includes her name and contact information as the primary case investigator on the form.
ZH: MLRO 在表格中填写其姓名和联系方式作为主要案件调查员。

[v7u_N003546|3546] The MLRO’s analysis suggests the activity might involve structuring or illicit fund placement, with the high-risk source of funds raising additional concerns. Furthermore, there is no clear rationale for the withdrawals, especially with the customers nearing retirement age. The large transactions contradict the stated goal of “building wealth,” leading the MLRO to suspect potential money laundering.
ZH: 洗钱RO 分析认为该活动可能涉及拆分交易或非法资金处置阶段，且缺乏合理理由，怀疑洗钱。

[v7u_N003547|3547] To support the SAR filing, the MLRO attaches relevant documentation, including transaction records, customer identification information, and internal review notes. These attachments are clearly labeled to provide necessary evidence for the SAR.
ZH: MLRO 附上交易记录、客户身份信息和内部审查记录等文件以支持 SAR 提交。

[v7u_N003548|3548] The narrative is written in plain English, avoiding jargon, and directly addressing the key questions of who, what, where, when, why, and how.
ZH: SAR 叙述应使用简明英语，避免行话，直接回答谁、什么、何时、何地、为何、如何等问题。

[v7u_N003549|3549] The MLRO clearly states the internal control number for law enforcement reference and confirms that there has been no prior contact with law enforcement about this account.
ZH: MLRO 需在 SAR 中注明内部控制编号，并确认此前未就该账户联系执法部门。

[v7u_N003550|3550] The impact statement might compel law enforcement to take action regarding the suspicious activity in the Citizen Family Trust account.
ZH: 影响陈述可能促使执法部门对可疑活动采取行动。

[v7u_N003551|3551] Before presenting the SAR to the SAR review committee, the MLRO ensures the narrative is written with clear headings and bullet points to make it easy to understand.
ZH: MLRO 确保 SAR 叙述使用清晰标题和要点，便于理解。

[v7u_N003552|3552] The MLRO adheres to legal considerations by maintaining strict confidentiality and ensuring that account holders are not tipped off.
ZH: MLRO 遵守保密要求，不得向账户持有人通风报信。

[v7u_N003553|3553] The SAR is submitted to FinCEN’s online portal within the standard 30-day deadline.
ZH: SAR 应在 30 天标准期限内通过 FinCEN 在线门户提交。

[v7u_N003554|3554] A clear, well-structured SAR supports compliance and strengthens the financial institution's ability to prevent and detect financial crime. Law enforcement relies on clear intelligence to investigate illicit activities.
ZH: 清晰、结构良好的 SAR 有助于合规并加强金融机构预防和发现金融犯罪的能力。
```

allowed_unit_ids:

```json
[
  "v7u_N003529",
  "v7u_N003530",
  "v7u_N003531",
  "v7u_N003532",
  "v7u_N003533",
  "v7u_N003534",
  "v7u_N003535",
  "v7u_N003536",
  "v7u_N003537",
  "v7u_N003538",
  "v7u_N003539",
  "v7u_N003540",
  "v7u_N003541",
  "v7u_N003542",
  "v7u_N003543",
  "v7u_N003544",
  "v7u_N003545",
  "v7u_N003546",
  "v7u_N003547",
  "v7u_N003548",
  "v7u_N003549",
  "v7u_N003550",
  "v7u_N003551",
  "v7u_N003552",
  "v7u_N003553",
  "v7u_N003554"
]
```

original_json:

```json
{
  "section_id": "CH49-S05",
  "section_title": "Concluding an investigation and suspicious activity reporting > Case example: SAR for a family trust",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N003529",
        "v7u_N003530",
        "v7u_N003531",
        "v7u_N003538",
        "v7u_N003540",
        "v7u_N003546"
      ],
      "proposition": "基于异常大额取款、高风险资金来源、账户行为不一致以及声明目标，MLRO进行分析并怀疑可能洗钱",
      "decision": "p7c_card",
      "card_id": "p7card_CH49-S05_001",
      "reason": "基础KG虽可保存分析结论，但无法表达'MLRO依据具体线索进行分析并产出分类结论'的局部有向判断链，属于P7C增量"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N003533"
      ],
      "proposition": "MLRO收集客户信息以纳入初始SAR",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG已将SAR所需信息分类为事实并描述该过程，无增量有向结构"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N003547"
      ],
      "proposition": "MLRO附上相关文件以支持SAR提交",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG已将该动作作为SAR提交过程事实保存，无增量有向结构"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N003551"
      ],
      "proposition": "在提交SAR给审查委员会前，MLRO确保叙述使用清晰标题和要点",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅有局部时间关系但无独立出口，且基础KG可作为最佳实践规则保存，无判断或程序性增量"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N003552"
      ],
      "proposition": "MLRO遵守保密要求，不向账户持有人通风报信",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG已将其作为规定措施（prescribes_measure）表达，无需重复有向结构"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N003553"
      ],
      "proposition": "SAR应在30天内通过FinCEN门户提交",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG已将该规则作为事实保存，无超出条件或判断的增量有向结构"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N003550"
      ],
      "proposition": "影响陈述可能促使执法部门采取行动",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅为可能性说明，无具体主体、动作或独立结果的完整有向结构"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH49-S05_001",
      "section_id": "CH49-S05",
      "card_nature": "assessment",
      "title": "MLRO分析线索并怀疑洗钱",
      "flow_nodes": [
        {
          "node_id": "input1",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "异常大额取款活动（三周内数百万美元，目的不明且与典型活动不一致）",
          "evidence_unit_ids": [
            "v7u_N003529"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "input2",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "大额快速取款",
          "evidence_unit_ids": [
            "v7u_N003530"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "input3",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "高风险资金来源（意外之财、彩票、赌博）",
          "evidence_unit_ids": [
            "v7u_N003530",
            "v7u_N003538"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "input4",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "申报财富与账户行为不一致",
          "evidence_unit_ids": [
            "v7u_N003531"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "input5",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "账户声明目标为积累财富",
          "evidence_unit_ids": [
            "v7u_N003540"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "process1",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "MLRO分析可疑活动",
          "evidence_unit_ids": [
            "v7u_N003546"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "exit1",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "怀疑可能涉及洗钱",
          "evidence_unit_ids": [
            "v7u_N003546"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "REFERENCES",
          "source": "process1",
          "target": "input1",
          "evidence_unit_ids": [
            "v7u_N003546"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e2",
          "edge_type": "REFERENCES",
          "source": "process1",
          "target": "input2",
          "evidence_unit_ids": [
            "v7u_N003546"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e3",
          "edge_type": "REFERENCES",
          "source": "process1",
          "target": "input3",
          "evidence_unit_ids": [
            "v7u_N003546"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e4",
          "edge_type": "REFERENCES",
          "source": "process1",
          "target": "input4",
          "evidence_unit_ids": [
            "v7u_N003546"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e5",
          "edge_type": "REFERENCES",
          "source": "process1",
          "target": "input5",
          "evidence_unit_ids": [
            "v7u_N003546"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e6",
          "edge_type": "PRODUCES",
          "source": "process1",
          "target": "exit1",
          "evidence_unit_ids": [
            "v7u_N003546"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N003529",
        "v7u_N003530",
        "v7u_N003531",
        "v7u_N003538",
        "v7u_N003540",
        "v7u_N003546"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：MLRO依据异常取款、高风险来源、不一致行为和声明目标等线索进行分析 → 产出怀疑洗钱的分类结论。KG不足：基础KG只能将分析结论作为案例事实保存，无法表达线索输入到分析动作再到结论产出的有向判断链。选项判断：可确认或排除关于MLRO分析依据和结论的选项。LLM推理：无。"
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
  "cand_004",
  "cand_005",
  "cand_006",
  "cand_007"
]
```

