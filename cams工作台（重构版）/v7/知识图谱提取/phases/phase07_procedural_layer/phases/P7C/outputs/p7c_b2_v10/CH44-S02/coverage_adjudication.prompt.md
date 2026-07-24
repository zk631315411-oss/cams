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

section_id: `CH44-S02`

section_title: `Ongoing AFC controls > Politically exposed persons screening`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "政治敏感人物风险与筛查要求",
      "title_en": "PEP Risk and Screening Requirement",
      "covered_units": [
        {
          "unit_id": "v7u_N003172",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003171",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "政治敏感人物分类类型",
      "title_en": "PEP Classification Types",
      "covered_units": [
        {
          "unit_id": "v7u_N003174",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N003175",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N003176",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N003173",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "FATF关于政治敏感人物风险等级的指引",
      "title_en": "FATF Guidance on PEP Risk Levels",
      "covered_units": [
        {
          "unit_id": "v7u_N003177",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003178",
          "unit_type": "rule",
          "kg_role": "states_rule"
        }
      ]
    },
    {
      "title_zh": "政治敏感人物分类扩展：家属与密切关联人",
      "title_en": "Extended PEP Classification: Family and Associates",
      "covered_units": [
        {
          "unit_id": "v7u_N003179",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "政治敏感人物身份终止与审查",
      "title_en": "PEP Status Expiration and Review",
      "covered_units": [
        {
          "unit_id": "v7u_N003182",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003181",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003180",
          "unit_type": "fact",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "政治敏感人物筛查的外包",
      "title_en": "Outsourcing PEP Screening",
      "covered_units": [
        {
          "unit_id": "v7u_N003183",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        }
      ]
    },
    {
      "title_zh": "政治敏感人物筛查方案考虑要点",
      "title_en": "PEP Screening Program Considerations",
      "covered_units": [
        {
          "unit_id": "v7u_N003185",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003186",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003187",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003188",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003189",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003184",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "负面媒体筛查：定义与要求",
      "title_en": "Adverse Media Screening: Definition and Mandate",
      "covered_units": [
        {
          "unit_id": "v7u_N003190",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N003191",
          "unit_type": "rule",
          "kg_role": "states_rule"
        }
      ]
    },
    {
      "title_zh": "负面媒体筛查的目的",
      "title_en": "Objectives of Adverse Media Screening",
      "covered_units": [
        {
          "unit_id": "v7u_N003193",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N003194",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003195",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003192",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "评估负面媒体发现",
      "title_en": "Evaluating Adverse Media Findings",
      "covered_units": [
        {
          "unit_id": "v7u_N003198",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003199",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003200",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003201",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003196",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003197",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "自动化负面媒体筛查的挑战",
      "title_en": "Challenges in Automated Adverse Media Screening",
      "covered_units": [
        {
          "unit_id": "v7u_N003203",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N003204",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003202",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "政治敏感人物风险与筛查要求",
      "target_title": "政治敏感人物分类类型",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物分类类型",
      "target_title": "政治敏感人物分类扩展：家属与密切关联人",
      "relation_type": "contains"
    },
    {
      "source_title": "政治敏感人物分类类型",
      "target_title": "FATF关于政治敏感人物风险等级的指引",
      "relation_type": "prepares"
    },
    {
      "source_title": "FATF关于政治敏感人物风险等级的指引",
      "target_title": "政治敏感人物身份终止与审查",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物风险与筛查要求",
      "target_title": "政治敏感人物筛查的外包",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物筛查的外包",
      "target_title": "政治敏感人物筛查方案考虑要点",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物筛查方案考虑要点",
      "target_title": "负面媒体筛查：定义与要求",
      "relation_type": "parallels"
    },
    {
      "source_title": "负面媒体筛查：定义与要求",
      "target_title": "负面媒体筛查的目的",
      "relation_type": "prepares"
    },
    {
      "source_title": "负面媒体筛查的目的",
      "target_title": "评估负面媒体发现",
      "relation_type": "prepares"
    },
    {
      "source_title": "评估负面媒体发现",
      "target_title": "自动化负面媒体筛查的挑战",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N003171|3171] PEPs are at heightened risk of involvement in bribery and corruption schemes because of their access to public funds and legal tenders.
ZH: 政治敏感人物因接触公共资金和合法招标，参与贿赂和腐败的风险更高。

[v7u_N003172|3172] For this reason, screening customers to identify PEPs along with relatives and close associates of PEPs, is a critical control in an anti-financial crime framework.
ZH: 筛查客户以识别政治敏感人物及其亲属和密切关联人，是金融犯罪防控框架中的关键控制措施。

[v7u_N003173|3173] Different jurisdictions and regulatory bodies classify PEPs into the following categories:
ZH: 不同司法管辖区和监管机构将政治敏感人物分为以下类别。

[v7u_N003174|3174] Foreign PEPs include officials in foreign governments, such as heads of state, senior politicians, military leaders, judicial officials, and high-ranking members of state-owned enterprises.
ZH: 外国政治敏感人物包括外国政府官员，如国家元首、高级政客、军事领导人、司法官员及国有企业高层。

[v7u_N003175|3175] Domestic PEPs include officials who hold a high public office within the country of an organization’s operation.
ZH: 国内政治敏感人物包括在机构运营所在国担任高级公职的官员。

[v7u_N003176|3176] International organization PEPs are executives and board members of global entities, such as the UN, International Monetary Fund, and World Bank.
ZH: 国际组织政治敏感人物包括联合国、国际货币基金组织、世界银行等全球实体的高管和董事会成员。

[v7u_N003177|3177] FATF guidance provides that foreign PEPs should always be considered high risk and subject to enhanced due diligence.
ZH: FATF指引规定，外国政治敏感人物应始终被视为高风险并接受强化尽职调查。

[v7u_N003178|3178] For domestic and international organization PEPs, FATF recommends that a risk assessment be conducted to determine their level of risk and the appropriate level of due diligence.
ZH: 对于国内和国际组织政治敏感人物，FATF建议进行风险评估以确定其风险等级和适当的尽职调查水平。

[v7u_N003179|3179] Note that some jurisdictions extend PEP classifications to family members and close associates because of their potential indirect involvement in financial crimes.
ZH: 部分司法管辖区将政治敏感人物分类扩展至家庭成员和密切关联人，因其可能间接参与金融犯罪。

[v7u_N003180|3180] However, PEP classifications vary globally.
ZH: 政治敏感人物的分类在全球范围内存在差异。

[v7u_N003181|3181] Additionally, some jurisdictions classify individuals as PEPs for life, while others set an expiration period after leaving office.
ZH: 不同司法管辖区对政治敏感人物分类的终身制与过期制差异

[v7u_N003182|3182] Financial institutions should establish clear review procedures that determine when to lift a PEP classification.
ZH: 金融机构须建立解除政治敏感人物分类的审查程序

[v7u_N003183|3183] Many organizations select a third-party vendor to provide information about potential PEPs. When this happens, organizations should follow appropriate outsourcing procedures, because the outsourcing organization continues to own the risk.
ZH: 使用第三方政治敏感人物供应商时须遵循外包程序，风险仍由机构承担

[v7u_N003184|3184] Regardless of whether PEP screening is done in-house or via a vendor, the following areas should be considered:
ZH: 无论内部或外包进行政治敏感人物筛查，均需考虑以下方面

[v7u_N003185|3185] When to screen: In most jurisdictions, PEP screening must be done before the customer becomes active, and customers should be rescreened on an ongoing basis to check whether their PEP status has changed.
ZH: 政治敏感人物筛查须在客户激活前完成，并持续重新筛查

[v7u_N003186|3186] Who to screen: Consider which parties to screen, particularly if customers are corporate entities with multiple beneficial owners and associated parties.
ZH: 筛查对象包括公司客户的多名受益所有人及相关方

[v7u_N003187|3187] Alert processing: Have a clear procedure and a team in place to clear the PEP alerts. Consider the tolerance for false positives during this process. There should also be a sign-off process for higher-risk PEPs.
ZH: 须建立清晰的政治敏感人物警报处理流程和团队，高风险政治敏感人物需签批

[v7u_N003188|3188] Testing: Implement a formal, ongoing testing process to ensure the system continues to operate effectively and with QA checks.
ZH: 须实施正式的持续测试流程，确保系统有效运行并包含质量检查

[v7u_N003189|3189] Other controls: Include enhanced due diligence processes on PEPs at onboarding and throughout the customer life cycle. Consider what other controls are needed for PEPs, such as specific transaction monitoring rules.
ZH: 对政治敏感人物须在准入及整个客户生命周期中实施强化尽职调查等控制

[v7u_N003190|3190] Adverse media checks—also known as negative news screening— identify publicly available information linking individuals or entities to financial crime risks.
ZH: 负面媒体检查（不良新闻筛查）用于识别与金融犯罪风险相关的公开信息

[v7u_N003191|3191] With the increasing de-escalation of fact-checking on social media platforms, and the rise of automated software-as-a-service screening solutions, financial institutions must take a risk-based approach to adverse media screening, ensuring accurate and credible risk assessments.
ZH: 金融机构须对负面媒体筛查采取基于风险的方法，确保准确可信

[v7u_N003192|3192] Financial institutions must conduct adverse media screening to:
ZH: 金融机构须进行负面媒体筛查，目的如下

[v7u_N003193|3193] Identify emerging risks: Customers might pose higher financial crime risks or reputational risks due to negative media exposure, criminal allegations, or regulatory investigations.
ZH: 识别新兴风险：客户可能因负面媒体曝光、刑事指控或监管调查而面临更高风险

[v7u_N003194|3194] Ensure compliance with global AFC regulations: FinCEN, the EU AML Directives, and other regulatory bodies require financial institutions to implement continuous media monitoring for high-risk customers.
ZH: FinCEN、欧盟反洗钱指令等监管机构要求对高风险客户实施持续媒体监控

[v7u_N003195|3195] Strengthen risk-based AFC frameworks: Adverse media findings can influence customer due diligence, enhanced due diligence, and ongoing transaction monitoring.
ZH: 负面媒体发现可影响客户尽职调查、强化尽职调查及持续交易监控

[v7u_N003196|3196] It is important to note that not all negative media findings warrant an increased risk rating.
ZH: 并非所有负面媒体发现都必然导致风险评级升高

[v7u_N003197|3197] Organizations must assess the following information:
ZH: 组织须评估以下信息

[v7u_N003198|3198] The credibility of the source: Reliable sources include regulatory reports, major financial publications, and law enforcement notices. Unverified social media posts and low-quality blogs should be carefully evaluated.
ZH: 信息来源的可信度：可靠来源包括监管报告、主要金融出版物和执法通知

[v7u_N003199|3199] The relevance to AFC risks: Does the media report indicate financial crime violations?
ZH: 评估媒体报告与金融犯罪风险的相关性

[v7u_N003200|3200] The timeframe: Older cases might hold less relevance, especially if legal outcomes exonerated the individual or entity. However, if the allegations or case relate to a senior manager or an individual that held a regulated role, this must be considered.
ZH: 时间因素：旧案相关性较低，但涉及高管或受监管个人的须考虑

[v7u_N003201|3201] Any follow-up actions: Were legal proceedings dismissed? Were regulatory fines settled? Were there any consequences for the individual such as personal fines, imprisonment, or travel bans? Risk assessments should reflect post-incident changes.
ZH: 事后跟进问题：法律程序、监管罚款、个人后果等，风险评估应反映事后变化

[v7u_N003202|3202] Challenges in automated adverse media screening solutions include:
ZH: 自动化负面媒体筛查解决方案面临的挑战列表的引导句

[v7u_N003203|3203] Social media misinformation: The decline in platform-driven factchecking increases the likelihood of false or misleading reports.
ZH: 社交媒体虚假信息风险：平台事实核查减少导致虚假或误导性报告增加

[v7u_N003204|3204] Organizations must agree to and prioritize verified sources.
ZH: 机构必须同意并优先使用经过验证的信息来源
```

allowed_unit_ids:

```json
[
  "v7u_N003171",
  "v7u_N003172",
  "v7u_N003173",
  "v7u_N003174",
  "v7u_N003175",
  "v7u_N003176",
  "v7u_N003177",
  "v7u_N003178",
  "v7u_N003179",
  "v7u_N003180",
  "v7u_N003181",
  "v7u_N003182",
  "v7u_N003183",
  "v7u_N003184",
  "v7u_N003185",
  "v7u_N003186",
  "v7u_N003187",
  "v7u_N003188",
  "v7u_N003189",
  "v7u_N003190",
  "v7u_N003191",
  "v7u_N003192",
  "v7u_N003193",
  "v7u_N003194",
  "v7u_N003195",
  "v7u_N003196",
  "v7u_N003197",
  "v7u_N003198",
  "v7u_N003199",
  "v7u_N003200",
  "v7u_N003201",
  "v7u_N003202",
  "v7u_N003203",
  "v7u_N003204"
]
```

original_json:

```json
{
  "section_id": "CH44-S02",
  "section_title": "Ongoing AFC controls > Politically exposed persons screening",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N003171"
      ],
      "proposition": "PEP因接触公共资金和合法招标，参与贿赂和腐败的风险更高。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅为一般性风险解释，无方向性结构。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N003172"
      ],
      "proposition": "筛查客户以识别PEP及其亲属和密切关联人是关键控制措施。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般控制陈述，无具体条件或主体动作的有向关系。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N003173"
      ],
      "proposition": "不同司法管辖区将PEP分为不同类型。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯粹分类介绍，无程序性结构。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N003174"
      ],
      "proposition": "外国PEP定义。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯粹定义。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N003175"
      ],
      "proposition": "国内PEP定义。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯粹定义。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N003176"
      ],
      "proposition": "国际组织PEP定义。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯粹定义。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N003177"
      ],
      "proposition": "FATF指引：外国PEP应始终被视为高风险并接受强化尽职调查。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S02_001",
      "reason": "明确由PEP类别导向强制高风险判断和EDD的有向链，超出基础KG的规则整体保存能力。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N003178"
      ],
      "proposition": "FATF建议：对国内和国际组织PEP进行风险评估以确定风险水平和适当尽职调查。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S02_002",
      "reason": "类别触发风险评估→确定DD的有向过程，超出基础KG。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N003179"
      ],
      "proposition": "部分司法管辖区将PEP分类扩展至家属和密切关联人。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅为补充事实说明，无程序性结构。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N003180"
      ],
      "proposition": "PEP分类在全球存在差异。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性事实。"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N003181"
      ],
      "proposition": "不同司法管辖区对PEP分类采用终身制或过期制。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "分类差异说明，无程序性判断。"
    },
    {
      "candidate_id": "cand_012",
      "unit_ids": [
        "v7u_N003182"
      ],
      "proposition": "金融机构应建立审查程序以确定何时解除PEP分类。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "宽泛义务，缺少具体条件、触发或结果，不足以形成可靠有向结构。"
    },
    {
      "candidate_id": "cand_013",
      "unit_ids": [
        "v7u_N003183"
      ],
      "proposition": "当机构选择第三方供应商提供PEP信息时，应遵循适当外包程序。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S02_003",
      "reason": "选择外包事件明确触发遵循程序的义务，构成有向顺序。"
    },
    {
      "candidate_id": "cand_014",
      "unit_ids": [
        "v7u_N003184"
      ],
      "proposition": "无论内部或外包进行PEP筛查，均需考虑以下方面（引导句）。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅篇章引导，无实质有向内容。"
    },
    {
      "candidate_id": "cand_015a",
      "unit_ids": [
        "v7u_N003185"
      ],
      "proposition": "在大多数司法管辖区，客户激活前，机构必须进行PEP筛查。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S02_004",
      "reason": "明确时间条件（激活前）触发强制筛查动作，形成有向顺序。"
    },
    {
      "candidate_id": "cand_015b",
      "unit_ids": [
        "v7u_N003185"
      ],
      "proposition": "机构应持续重新筛查客户以检查PEP状态是否变化。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "持续性义务过于笼统，无明确触发事件或独立结果，仅为基础KG可表达的一般要求。"
    },
    {
      "candidate_id": "cand_016",
      "unit_ids": [
        "v7u_N003186"
      ],
      "proposition": "筛查应考虑哪些当事方，特别是公司客户的多名受益所有人及相关方。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性考虑建议，无明确触发或方向。"
    },
    {
      "candidate_id": "cand_017",
      "unit_ids": [
        "v7u_N003187"
      ],
      "proposition": "当PEP警报涉及高风险PEP时，应有签批过程。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S02_007",
      "reason": "高风险警报条件触发额外签批控制，构成有向应对链。"
    },
    {
      "candidate_id": "cand_018",
      "unit_ids": [
        "v7u_N003188"
      ],
      "proposition": "应实施正式、持续的测试流程以确保系统有效运行。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般控制义务，无具体条件或触发，KG可表达。"
    },
    {
      "candidate_id": "cand_019",
      "unit_ids": [
        "v7u_N003189"
      ],
      "proposition": "对PEP应在准入及整个客户生命周期中实施强化尽职调查等控制。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "控制措施的列举说明，无单体有向过程。"
    },
    {
      "candidate_id": "cand_020",
      "unit_ids": [
        "v7u_N003190"
      ],
      "proposition": "负面媒体检查的定义。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯粹定义。"
    },
    {
      "candidate_id": "cand_021",
      "unit_ids": [
        "v7u_N003191"
      ],
      "proposition": "金融机构须对负面媒体筛查采取基于风险的方法。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般原则性要求，无程序性细节。"
    },
    {
      "candidate_id": "cand_022",
      "unit_ids": [
        "v7u_N003192"
      ],
      "proposition": "金融机构须进行负面媒体筛查（目的引导句）。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅引导目的列表。"
    },
    {
      "candidate_id": "cand_023",
      "unit_ids": [
        "v7u_N003193"
      ],
      "proposition": "负面媒体筛查有助于识别新兴风险。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "目的说明，非有向过程。"
    },
    {
      "candidate_id": "cand_024",
      "unit_ids": [
        "v7u_N003194"
      ],
      "proposition": "监管要求金融机构对高风险客户实施持续媒体监控。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S02_006",
      "reason": "明确的高风险客户类触发持续监控义务，监管要求作为标准约束动作，形成有向约束关系。"
    },
    {
      "candidate_id": "cand_025",
      "unit_ids": [
        "v7u_N003195"
      ],
      "proposition": "负面媒体发现可影响客户尽职调查、强化尽职调查和持续交易监控。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "说明影响关系，无具体动作链。"
    },
    {
      "candidate_id": "cand_026",
      "unit_ids": [
        "v7u_N003196"
      ],
      "proposition": "并非所有负面媒体发现都应导致风险评级升高。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性提醒，无方向性结构。"
    },
    {
      "candidate_id": "cand_027",
      "unit_ids": [
        "v7u_N003197"
      ],
      "proposition": "组织须评估以下信息（引导句）。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "篇章引导。"
    },
    {
      "candidate_id": "cand_028",
      "unit_ids": [
        "v7u_N003198"
      ],
      "proposition": "评估信息来源的可信度，可靠来源包括监管报告等。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "列出评估维度，无明确触发或结果。"
    },
    {
      "candidate_id": "cand_029",
      "unit_ids": [
        "v7u_N003199"
      ],
      "proposition": "评估媒体报告是否与金融犯罪风险相关。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "评估维度，无独立结果。"
    },
    {
      "candidate_id": "cand_030",
      "unit_ids": [
        "v7u_N003200"
      ],
      "proposition": "如果负面媒体报道或案件涉及高级经理或受监管个人，即使时间久远也必须考虑。",
      "decision": "p7c_card",
      "card_id": "p7card_CH44-S02_005",
      "reason": "特定人员身份条件触发强制性考虑，构成条件导向的有向判断。"
    },
    {
      "candidate_id": "cand_031",
      "unit_ids": [
        "v7u_N003201"
      ],
      "proposition": "风险评估应反映事后跟进变化。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "模糊的后续调整要求，无明确触发或具体动作链。"
    },
    {
      "candidate_id": "cand_032",
      "unit_ids": [
        "v7u_N003202"
      ],
      "proposition": "自动化负面媒体筛查的挑战引导。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "引导句。"
    },
    {
      "candidate_id": "cand_033",
      "unit_ids": [
        "v7u_N003203"
      ],
      "proposition": "社交媒体虚假信息风险增加。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "风险说明。"
    },
    {
      "candidate_id": "cand_034",
      "unit_ids": [
        "v7u_N003204"
      ],
      "proposition": "机构必须同意并优先使用经过验证的信息来源。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般义务，无触发或独立结果，KG可表达。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH44-S02_001",
      "section_id": "CH44-S02",
      "card_nature": "execution",
      "title": "Foreign PEPs Always High Risk with Enhanced Due Diligence",
      "flow_nodes": [
        {
          "node_id": "p7card_CH44-S02_001_standard_001",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "FATF指引",
          "evidence_unit_ids": [
            "v7u_N003177"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH44-S02_001_process_001",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构应始终将外国PEP视为高风险并实施强化尽职调查",
          "evidence_unit_ids": [
            "v7u_N003177"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7card_CH44-S02_001_edge_001",
          "edge_type": "REFERENCES",
          "source": "p7card_CH44-S02_001_process_001",
          "target": "p7card_CH44-S02_001_standard_001",
          "evidence_unit_ids": [
            "v7u_N003177"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N003177"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：外国PEP分类 → 机构（应始终）视为高风险并实施EDD。KG不足：基础KG可保存此规则为整体，但无法表达由类别导向强制判断和EDD的有向过程。选项判断：可确认外国PEP的EDD是强制性的，无例外。LLM推理：无。"
    },
    {
      "card_id": "p7card_CH44-S02_002",
      "section_id": "CH44-S02",
      "card_nature": "assessment",
      "title": "Domestic and International PEPs Require Risk Assessment",
      "flow_nodes": [
        {
          "node_id": "p7card_CH44-S02_002_standard_001",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "FATF指引",
          "evidence_unit_ids": [
            "v7u_N003178"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH44-S02_002_process_001",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "机构应对国内和国际组织PEP进行风险评估以确定其风险水平和适当的尽职调查水平",
          "evidence_unit_ids": [
            "v7u_N003178"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7card_CH44-S02_002_edge_001",
          "edge_type": "REFERENCES",
          "source": "p7card_CH44-S02_002_process_001",
          "target": "p7card_CH44-S02_002_standard_001",
          "evidence_unit_ids": [
            "v7u_N003178"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N003178"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：国内/国际组织PEP分类 → 机构（应）进行风险评估→确定风险水平和适当DD。KG不足：基础KG只能表达建议规则，无法表达分类触发评估→判定DD的完整有向过程。选项判断：可确认此类PEP的DD水平取决于风险评估，非自动高风险。LLM推理：无。"
    },
    {
      "card_id": "p7card_CH44-S02_003",
      "section_id": "CH44-S02",
      "card_nature": "execution",
      "title": "Outsourced PEP Screening Triggers Outsourcing Procedures",
      "flow_nodes": [
        {
          "node_id": "p7card_CH44-S02_003_entry_001",
          "node_category": "entry",
          "node_type": "E8_decision_finding",
          "label": "机构选择第三方供应商提供PEP信息",
          "evidence_unit_ids": [
            "v7u_N003183"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH44-S02_003_process_001",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构应遵循适当的外包程序",
          "evidence_unit_ids": [
            "v7u_N003183"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7card_CH44-S02_003_edge_001",
          "edge_type": "PRECEDES",
          "source": "p7card_CH44-S02_003_entry_001",
          "target": "p7card_CH44-S02_003_process_001",
          "evidence_unit_ids": [
            "v7u_N003183"
          ],
          "derivation": "explicit_text",
          "condition": "当选择第三方供应商时"
        }
      ],
      "source_unit_ids": [
        "v7u_N003183"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：选择外包PEP信息服务 → 机构（应）遵循外包程序。KG不足：基础KG可保存规则，但无法表达选择动作触发程序遵守义务的有向顺序。选项判断：可确认外包时程序合规是必须的，风险仍由机构承担。LLM推理：无。"
    },
    {
      "card_id": "p7card_CH44-S02_004",
      "section_id": "CH44-S02",
      "card_nature": "execution",
      "title": "PEP Screening Must Occur Before Customer Activation",
      "flow_nodes": [
        {
          "node_id": "p7card_CH44-S02_004_entry_001",
          "node_category": "entry",
          "node_type": "E5_time_cycle",
          "label": "客户激活前",
          "evidence_unit_ids": [
            "v7u_N003185"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH44-S02_004_process_001",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构必须进行PEP筛查",
          "evidence_unit_ids": [
            "v7u_N003185"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7card_CH44-S02_004_edge_001",
          "edge_type": "PRECEDES",
          "source": "p7card_CH44-S02_004_entry_001",
          "target": "p7card_CH44-S02_004_process_001",
          "evidence_unit_ids": [
            "v7u_N003185"
          ],
          "derivation": "explicit_text",
          "condition": "在客户激活前"
        }
      ],
      "source_unit_ids": [
        "v7u_N003185"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：客户激活前的时间点 → 机构（必须）进行PEP筛查。KG不足：基础KG可保存时间要求，但无法表达时间顺序触发强制筛查的有向过程。选项判断：可确认筛查必须在账户使用前完成。LLM推理：无。"
    },
    {
      "card_id": "p7card_CH44-S02_005",
      "section_id": "CH44-S02",
      "card_nature": "assessment",
      "title": "Adverse Media on Senior Managers Must Be Considered Despite Age",
      "flow_nodes": [
        {
          "node_id": "p7card_CH44-S02_005_entry_001",
          "node_category": "entry",
          "node_type": "E1_event_signal",
          "label": "负面媒体报道或案件涉及高级经理或受监管个人",
          "evidence_unit_ids": [
            "v7u_N003200"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH44-S02_005_process_001",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构必须考虑该信息",
          "evidence_unit_ids": [
            "v7u_N003200"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7card_CH44-S02_005_edge_001",
          "edge_type": "PRECEDES",
          "source": "p7card_CH44-S02_005_entry_001",
          "target": "p7card_CH44-S02_005_process_001",
          "evidence_unit_ids": [
            "v7u_N003200"
          ],
          "derivation": "explicit_text",
          "condition": "若涉及高级经理或受监管个人，即使时间久远"
        }
      ],
      "source_unit_ids": [
        "v7u_N003200"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：旧媒体信息涉及特殊职位人员 → 机构（必须）考虑该信息。KG不足：基础KG只能表达对时效性的一般说明，无法表达特定人员身份触发强制性考虑的有向判断。选项判断：可确认即便信息陈旧，特定人员相关也必须考虑。LLM推理：无。"
    },
    {
      "card_id": "p7card_CH44-S02_006",
      "section_id": "CH44-S02",
      "card_nature": "control",
      "title": "Regulatory Mandate for Continuous Media Monitoring of High-Risk Customers",
      "flow_nodes": [
        {
          "node_id": "p7card_CH44-S02_006_standard_001",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "FinCEN、欧盟反洗钱指令等监管要求",
          "evidence_unit_ids": [
            "v7u_N003194"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH44-S02_006_process_001",
          "node_category": "process",
          "node_type": "P7_monitoring",
          "label": "金融机构必须对高风险客户实施持续媒体监控",
          "evidence_unit_ids": [
            "v7u_N003194"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7card_CH44-S02_006_edge_001",
          "edge_type": "REFERENCES",
          "source": "p7card_CH44-S02_006_process_001",
          "target": "p7card_CH44-S02_006_standard_001",
          "evidence_unit_ids": [
            "v7u_N003194"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_transmits_requirement"
        }
      ],
      "source_unit_ids": [
        "v7u_N003194"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：高风险客户类别 → 金融机构（必须）实施持续媒体监控，受监管要求约束。KG不足：基础KG可保存监管要求，但无法表达特定客户类触发持续监控义务的有向约束关系。选项判断：可确认高风险客户是持续媒体监控的法定对象。LLM推理：无。"
    },
    {
      "card_id": "p7card_CH44-S02_007",
      "section_id": "CH44-S02",
      "card_nature": "control",
      "title": "High-Risk PEP Alerts Trigger Sign-Off Process",
      "flow_nodes": [
        {
          "node_id": "p7card_CH44-S02_007_entry_001",
          "node_category": "entry",
          "node_type": "E1_event_signal",
          "label": "PEP警报涉及高风险PEP",
          "evidence_unit_ids": [
            "v7u_N003187"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH44-S02_007_process_001",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构应实施签批过程",
          "evidence_unit_ids": [
            "v7u_N003187"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7card_CH44-S02_007_edge_001",
          "edge_type": "PRECEDES",
          "source": "p7card_CH44-S02_007_entry_001",
          "target": "p7card_CH44-S02_007_process_001",
          "evidence_unit_ids": [
            "v7u_N003187"
          ],
          "derivation": "explicit_text",
          "condition": "当警报涉及高风险PEP时"
        }
      ],
      "source_unit_ids": [
        "v7u_N003187"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：高风险PEP警报 → 机构（应）实施签批过程。KG不足：基础KG可保存签批要求，但无法表达由高风险警报触发签批的有向顺序。选项判断：可确认高风险PEP需要额外批准。LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_001",
  "cand_002",
  "cand_003",
  "cand_004",
  "cand_005",
  "cand_006",
  "cand_009",
  "cand_010",
  "cand_011",
  "cand_012",
  "cand_014",
  "cand_015b",
  "cand_016",
  "cand_018",
  "cand_019",
  "cand_020",
  "cand_021",
  "cand_022",
  "cand_023",
  "cand_025",
  "cand_026",
  "cand_027",
  "cand_028",
  "cand_029",
  "cand_031",
  "cand_032",
  "cand_033",
  "cand_034"
]
```

