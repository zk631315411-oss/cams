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

section_id: `CH51-S08`

section_title: `Understanding AFC technology > Transitioning from traditional systems to AIbased tools`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "AI过渡的初期规划与风险评估",
      "title_en": "Initial planning and risk assessment for AI transition",
      "covered_units": [
        {
          "unit_id": "v7u_N003854",
          "unit_type": "process",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003855",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003856",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003858",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003857",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003853",
          "unit_type": "rule",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "试点、方案选择与期望设定",
      "title_en": "Piloting, solution selection, and expectation setting",
      "covered_units": [
        {
          "unit_id": "v7u_N003859",
          "unit_type": "process",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N003861",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003864",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003860",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003863",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003862",
          "unit_type": "fact",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "AI系统的实施与测试",
      "title_en": "Implementation and testing of AI systems",
      "covered_units": [
        {
          "unit_id": "v7u_N003865",
          "unit_type": "rule",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N003866",
          "unit_type": "process",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N003867",
          "unit_type": "rule",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N003868",
          "unit_type": "rule",
          "kg_role": "describes_process"
        }
      ]
    },
    {
      "title_zh": "AI局限性、监管沟通与运营准备",
      "title_en": "AI limitations, regulatory engagement, and operational readiness",
      "covered_units": [
        {
          "unit_id": "v7u_N003870",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003871",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003869",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "AI过渡的战略总结",
      "title_en": "Strategic conclusion for AI transition",
      "covered_units": [
        {
          "unit_id": "v7u_N003872",
          "unit_type": "rule",
          "kg_role": "states_rule"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "AI过渡的初期规划与风险评估",
      "target_title": "试点、方案选择与期望设定",
      "relation_type": "prepares"
    },
    {
      "source_title": "试点、方案选择与期望设定",
      "target_title": "AI系统的实施与测试",
      "relation_type": "prepares"
    },
    {
      "source_title": "AI系统的实施与测试",
      "target_title": "AI局限性、监管沟通与运营准备",
      "relation_type": "prepares"
    },
    {
      "source_title": "AI局限性、监管沟通与运营准备",
      "target_title": "AI过渡的战略总结",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N003853|3853] Transitioning from a traditional rules-based AFC system to AI-driven tools, such as technology for remote onboarding, requires careful planning to maintain effectiveness and compliance. Organizations should ensure that innovation enhances risk management rather than introducing new vulnerabilities.
ZH: 从传统规则系统过渡到AI驱动的金融犯罪防控工具需谨慎规划以维持有效性和合规性

[v7u_N003854|3854] A key first step is conducting a comprehensive risk assessment to identify gaps in the existing system, define objectives for AI integration, in phases as needed, and assess regulatory expectations.
ZH: AI整合的关键第一步是进行全面的风险评估，识别现有系统差距并明确目标

[v7u_N003855|3855] AI can enhance AFC detection capabilities, but institutions need to ensure model transparency, auditability, and explainability to meet compliance standards.
ZH: 机构需确保AI模型的透明度、可审计性和可解释性以满足合规标准

[v7u_N003856|3856] Organizations should continuously monitor and update risk assessments to adapt to evolving threats.
ZH: 机构应持续监控并更新风险评估以适应不断演变的威胁

[v7u_N003857|3857] Plus, a thorough risk assessment also helps prioritize time and financial investment.
ZH: 全面的风险评估有助于优先安排时间和资金投入

[v7u_N003858|3858] It is also important to define short- and long-term goals for AI integration.
ZH: 为AI整合定义短期和长期目标至关重要

[v7u_N003859|3859] One way organizations can begin to pilot and experiment with AI is to use it to complement existing systems in a post-detection role before a full transition.
ZH: 机构可先让AI在现有系统后检测环节中发挥补充作用，进行试点实验

[v7u_N003860|3860] This will help focus on improvements that offer the greatest value in risk or cost management.
ZH: 聚焦于在风险或成本管理方面提供最大价值的改进

[v7u_N003861|3861] Choosing the right solutions is essential, as no single system fits all needs.
ZH: 选择适合的金融犯罪防控解决方案至关重要，没有万能系统。

[v7u_N003862|3862] Business sponsors often expect efficiency gains to fund further investments that enhance risk coverage.
ZH: 业务赞助方期望效率提升为风险覆盖投资提供资金。

[v7u_N003863|3863] However, depending on the maturity of the existing operation—such as its leanness and efficiency—AI may primarily focus on increasing AFC effectiveness.
ZH: AI的侧重点取决于现有运营的成熟度。

[v7u_N003864|3864] The organization should establish expectations in the early stages of the project so that stakeholders are aligned on strategic objectives.
ZH: 组织应在项目早期建立期望，确保利益相关方战略一致。

[v7u_N003865|3865] To prevent disruptions during development and implementation and minimize operational risk, organizations may run AI systems in parallel with existing rules-based systems before fully transitioning.
ZH: 在完全过渡前，可并行运行AI与基于规则的系统以降低运营风险。

[v7u_N003866|3866] The process of testing, validating, and tuning AI models ensures accuracy and prevents unintended gaps in coverage.
ZH: 测试、验证和调优AI模型可确保准确性并防止覆盖缺口。

[v7u_N003867|3867] Engaging regulators and compliance, legal, IT, and operations teams early ensures the new system integrates effectively across business units.
ZH: 尽早让监管、合规、法务、IT和运营团队参与，确保系统有效整合。

[v7u_N003868|3868] Running pilot programs to test AI systems before full implementation may minimize risk, even if it takes longer to transition.
ZH: 在全面实施前运行AI试点项目可降低风险。

[v7u_N003869|3869] AI is still in its early days and, in its current state, is unlikely to completely eliminate the human in the loop. AI systems typically complement and support, rather than replace, human oversight.
ZH: AI目前仍处于早期阶段，不太可能完全消除人工监督，而是起补充作用。

[v7u_N003870|3870] Engaging regulators early and often helps set expectations and allows consideration of any concerns regarding explainability requirements.
ZH: 尽早并经常与监管机构沟通，以设定期望并考虑可解释性要求。

[v7u_N003871|3871] Addressing operational impacts, such as training staff on new workflows and system output, is likely to prevent inefficiencies in the future.
ZH: 解决运营影响，如培训员工掌握新工作流程和系统输出，可防止未来低效。

[v7u_N003872|3872] By carefully planning the transition, balancing AI’s benefits with regulatory expectations, and avoiding common pitfalls, organizations can modernize AFC controls and onboarding while maintaining compliance and effectiveness.
ZH: 通过精心规划过渡，平衡AI效益与监管期望，可现代化金融犯罪防控控制并保持合规。
```

allowed_unit_ids:

```json
[
  "v7u_N003853",
  "v7u_N003854",
  "v7u_N003855",
  "v7u_N003856",
  "v7u_N003857",
  "v7u_N003858",
  "v7u_N003859",
  "v7u_N003860",
  "v7u_N003861",
  "v7u_N003862",
  "v7u_N003863",
  "v7u_N003864",
  "v7u_N003865",
  "v7u_N003866",
  "v7u_N003867",
  "v7u_N003868",
  "v7u_N003869",
  "v7u_N003870",
  "v7u_N003871",
  "v7u_N003872"
]
```

original_json:

```json
{
  "section_id": "CH51-S08",
  "section_title": "Understanding AFC technology > Transitioning from traditional systems to AIbased tools",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N003853"
      ],
      "proposition": "过渡需谨慎规划并确保风险管理增强",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性原则陈述，基础KG已能表达规划与风险管理的关系，无具体有向判断结构。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N003854"
      ],
      "proposition": "第一步进行风险评估以识别差距和定义目标",
      "decision": "kg_only",
      "card_id": null,
      "reason": "风险评估作为措施已由基础KG覆盖，其内部步骤（识别差距）属于该过程的一部分，无独立分类结果，缺乏P7C增量结构。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N003855"
      ],
      "proposition": "机构需确保AI模型透明度、可审计性和可解释性以满足合规标准",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S08_001",
      "reason": "有向约束关系：标准→动作。基础KG仅记录规则，未表达合规标准对动作的约束方向。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N003856"
      ],
      "proposition": "机构应持续监控并更新风险评估以适应不断演变的威胁",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S08_002",
      "reason": "威胁演变触发持续监控的因果链，KG未表达此动态触发关系。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N003857"
      ],
      "proposition": "风险评估有助于优先安排时间和资金投入",
      "decision": "kg_only",
      "card_id": null,
      "reason": "只是解释风险评估的附带益处，无独立程序或判断结构。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N003858"
      ],
      "proposition": "为AI整合定义短期和长期目标很重要",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般重要性陈述，缺乏具体主体、条件或产出关系。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N003859"
      ],
      "proposition": "组织可在全面过渡前试点使用AI作为补充",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S08_003",
      "reason": "时间条件约束试点动作，基础KG未强调条件化步骤。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N003860"
      ],
      "proposition": "试点有助于聚焦最大价值的改进",
      "decision": "kg_only",
      "card_id": null,
      "reason": "解释试点好处，无独立有向结构。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N003861"
      ],
      "proposition": "选择适合方案至关重要，无万能系统",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性提醒，无程序性关联。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N003862"
      ],
      "proposition": "业务赞助方期望效率提升以资助风险覆盖投资",
      "decision": "kg_only",
      "card_id": null,
      "reason": "描述利益相关方期望，无具体行动关系。"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N003863"
      ],
      "proposition": "根据运营成熟度，AI可能主要专注于提高AFC有效性",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S08_004",
      "reason": "成熟度条件导向AI侧重点的判断，KG只记录事实，未表达条件判断结构。"
    },
    {
      "candidate_id": "cand_012",
      "unit_ids": [
        "v7u_N003864"
      ],
      "proposition": "组织应在项目早期建立期望以使利益相关方一致",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S08_005",
      "reason": "动作产生利益相关方对齐的产出，KG未表达此有向关系。"
    },
    {
      "candidate_id": "cand_013",
      "unit_ids": [
        "v7u_N003865"
      ],
      "proposition": "为预防中断，组织可在完全过渡前并行运行系统",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S08_006",
      "reason": "风险条件触发并行运行措施，KG未表达因果链。"
    },
    {
      "candidate_id": "cand_014",
      "unit_ids": [
        "v7u_N003866"
      ],
      "proposition": "测试、验证和调优AI模型确保准确性并防止覆盖缺口",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S08_007",
      "reason": "动作直接产生准确性和覆盖完整性，KG未表达测试的产出关系。"
    },
    {
      "candidate_id": "cand_015",
      "unit_ids": [
        "v7u_N003867"
      ],
      "proposition": "尽早让监管等团队参与确保新系统有效整合",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S08_008",
      "reason": "早期参与动作产生有效整合结果，KG未表达此产出。"
    },
    {
      "candidate_id": "cand_016",
      "unit_ids": [
        "v7u_N003868"
      ],
      "proposition": "全面实施前运行试点可降低风险",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S08_009",
      "reason": "试点动作降低风险的产出，KG未表达。"
    },
    {
      "candidate_id": "cand_017",
      "unit_ids": [
        "v7u_N003869"
      ],
      "proposition": "AI仍处于早期阶段，不太可能完全取代人工，起补充作用",
      "decision": "kg_only",
      "card_id": null,
      "reason": "事实陈述AI局限性，无判断或程序结构。"
    },
    {
      "candidate_id": "cand_018",
      "unit_ids": [
        "v7u_N003870"
      ],
      "proposition": "尽早并经常与监管沟通有助于设定期望并考虑可解释性要求",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S08_010",
      "reason": "沟通动作产生设定期望等具体结果，KG未表达此产出链。"
    },
    {
      "candidate_id": "cand_019",
      "unit_ids": [
        "v7u_N003871"
      ],
      "proposition": "解决运营影响（如培训）可能防止未来低效",
      "decision": "p7c_card",
      "card_id": "p7card_CH51-S08_011",
      "reason": "解决运营影响（培训）产出防止低效，KG未表达。"
    },
    {
      "candidate_id": "cand_020",
      "unit_ids": [
        "v7u_N003872"
      ],
      "proposition": "通过规划、平衡效益与监管期望、避免陷阱，可现代化AFC控制并保持合规",
      "decision": "kg_only",
      "card_id": null,
      "reason": "总结性陈述，涵盖多个抽象动作和目标，无独立有向结构，更适合KG。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH51-S08_001",
      "section_id": "CH51-S08",
      "card_nature": "control",
      "title": "机构需确保AI模型特性以满足合规标准",
      "flow_nodes": [
        {
          "node_id": "N1",
          "node_category": "process",
          "node_type": "P8_constrained_action",
          "label": "机构需确保AI模型透明度、可审计性和可解释性",
          "evidence_unit_ids": [
            "v7u_N003855"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N2",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "合规标准",
          "evidence_unit_ids": [
            "v7u_N003855"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "REFERENCES",
          "source": "N1",
          "target": "N2",
          "evidence_unit_ids": [
            "v7u_N003855"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N003855"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构确保AI模型透明度、可审计性和可解释性 --REFERENCES(standard_constrains_action)--> 合规标准；KG不足：基础KG仅记录规则“需确保模型特性”，无法表达合规标准对动作的约束方向；选项判断：可确认机构确保模型特性是为了满足合规标准，而不仅仅是自愿行为；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH51-S08_002",
      "section_id": "CH51-S08",
      "card_nature": "execution",
      "title": "威胁演变驱动机构持续监控和更新风险评估",
      "flow_nodes": [
        {
          "node_id": "N3",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "威胁环境不断演变",
          "evidence_unit_ids": [
            "v7u_N003856"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N4",
          "node_category": "process",
          "node_type": "P7_monitoring",
          "label": "机构应持续监控并更新风险评估",
          "evidence_unit_ids": [
            "v7u_N003856"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E2",
          "edge_type": "PRECEDES",
          "source": "N3",
          "target": "N4",
          "condition": "适应不断演变的威胁",
          "evidence_unit_ids": [
            "v7u_N003856"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N003856"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：威胁环境不断演变 --PRECEDES(condition=适应威胁演变)--> 机构应持续监控并更新风险评估；KG不足：基础KG只规定措施“持续监控”，未表达外部威胁演变触发持续性监控的因果逻辑；选项判断：可确认持续监控的动力来自威胁演变，监控是可更新的动态过程；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH51-S08_003",
      "section_id": "CH51-S08",
      "card_nature": "execution",
      "title": "全面过渡前试点使用AI作为补充",
      "flow_nodes": [
        {
          "node_id": "N5",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "尚未完全过渡到AI的阶段",
          "evidence_unit_ids": [
            "v7u_N003859"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N6",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "组织可试点使用AI在post-detection角色中作为补充",
          "evidence_unit_ids": [
            "v7u_N003859"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E3",
          "edge_type": "PRECEDES",
          "source": "N5",
          "target": "N6",
          "condition": "在完全过渡前",
          "evidence_unit_ids": [
            "v7u_N003859"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N003859"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：全面过渡前的阶段 --PRECEDES(condition=完全过渡前)--> 组织可试点使用AI在post-detection角色中作为补充；KG不足：基础KG描述了试点过程，但未强调“在完全过渡前”这一时间条件约束动作；选项判断：可确认试点是在完全过渡前进行的，且作为现有系统的补充；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH51-S08_004",
      "section_id": "CH51-S08",
      "card_nature": "assessment",
      "title": "运营成熟度影响AI侧重点",
      "flow_nodes": [
        {
          "node_id": "N7",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "现有运营成熟度（如精简高效）",
          "evidence_unit_ids": [
            "v7u_N003863"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N8",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "AI可能主要专注于提高AFC有效性",
          "evidence_unit_ids": [
            "v7u_N003863"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E4",
          "edge_type": "PRECEDES",
          "source": "N7",
          "target": "N8",
          "condition": "当运营成熟精简高效时",
          "evidence_unit_ids": [
            "v7u_N003863"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N003863"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：现有运营成熟度（如精简高效） --PRECEDES(condition=运营成熟精简高效)--> AI可能主要专注于提高AFC有效性；KG不足：基础KG记录为解释性事实，未表达成熟度条件导致AI侧重点不同的判断结构；选项判断：可确认AI的侧重点取决于现状成熟度，高效时侧重有效性；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH51-S08_005",
      "section_id": "CH51-S08",
      "card_nature": "execution",
      "title": "早期建立期望以使利益相关方一致",
      "flow_nodes": [
        {
          "node_id": "N9",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "组织应在项目早期建立期望",
          "evidence_unit_ids": [
            "v7u_N003864"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N10",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "利益相关方在战略目标上一致",
          "evidence_unit_ids": [
            "v7u_N003864"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E5",
          "edge_type": "PRODUCES",
          "source": "N9",
          "target": "N10",
          "evidence_unit_ids": [
            "v7u_N003864"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N003864"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：组织在项目早期建立期望 --PRODUCES--> 利益相关方在战略目标上一致；KG不足：基础KG陈述规则“应建立期望”，未表达该动作的产出是利益相关方对齐；选项判断：可确认建立期望的目的是实现战略对齐；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH51-S08_006",
      "section_id": "CH51-S08",
      "card_nature": "execution",
      "title": "为预防中断在过渡期并行运行新旧系统",
      "flow_nodes": [
        {
          "node_id": "N11",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "过渡期间存在运营中断风险",
          "evidence_unit_ids": [
            "v7u_N003865"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N12",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "组织可并行运行AI与传统系统",
          "evidence_unit_ids": [
            "v7u_N003865"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E6",
          "edge_type": "PRECEDES",
          "source": "N11",
          "target": "N12",
          "condition": "为预防中断和最小化运营风险",
          "evidence_unit_ids": [
            "v7u_N003865"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N003865"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：过渡期间存在运营中断风险 --PRECEDES--> 组织并行运行AI与传统系统；KG不足：基础KG描述并行运行过程，未表达风险条件触发措施的因果链；选项判断：可确认并行运行的直接目的是预防中断和最小化风险；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH51-S08_007",
      "section_id": "CH51-S08",
      "card_nature": "assessment",
      "title": "测试、验证和调优AI模型确保准确性和覆盖完整性",
      "flow_nodes": [
        {
          "node_id": "N13",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "机构测试、验证和调优AI模型",
          "evidence_unit_ids": [
            "v7u_N003866"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N14",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "模型准确且无意外覆盖缺口",
          "evidence_unit_ids": [
            "v7u_N003866"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E7",
          "edge_type": "PRODUCES",
          "source": "N13",
          "target": "N14",
          "evidence_unit_ids": [
            "v7u_N003866"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N003866"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构测试、验证和调优AI模型 --PRODUCES--> 模型准确且覆盖无意外缺口；KG不足：基础KG描述测试过程，未强调产出模型准确性和覆盖完整性；选项判断：可确认测试调优直接确保准确性和防止缺口；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH51-S08_008",
      "section_id": "CH51-S08",
      "card_nature": "execution",
      "title": "让多团队尽早参与确保新系统有效整合",
      "flow_nodes": [
        {
          "node_id": "N15",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构尽早让监管、合规、法务、IT和运营团队参与",
          "evidence_unit_ids": [
            "v7u_N003867"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N16",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "新系统有效整合",
          "evidence_unit_ids": [
            "v7u_N003867"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E8",
          "edge_type": "PRODUCES",
          "source": "N15",
          "target": "N16",
          "evidence_unit_ids": [
            "v7u_N003867"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N003867"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构尽早让多团队参与 --PRODUCES--> 新系统有效整合；KG不足：基础KG描述参与过程，未表达整合是参与的直接结果；选项判断：可确认早期参与是为了实现系统有效整合；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH51-S08_009",
      "section_id": "CH51-S08",
      "card_nature": "execution",
      "title": "全面实施前运行试点降低风险",
      "flow_nodes": [
        {
          "node_id": "N17",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构在全面实施前运行AI试点项目",
          "evidence_unit_ids": [
            "v7u_N003868"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N18",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "风险降低",
          "evidence_unit_ids": [
            "v7u_N003868"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E9",
          "edge_type": "PRODUCES",
          "source": "N17",
          "target": "N18",
          "evidence_unit_ids": [
            "v7u_N003868"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N003868"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构在全面实施前运行AI试点项目 --PRODUCES--> 风险降低；KG不足：基础KG描述试点过程，未强调试点本身降低风险的结果；选项判断：可确认试点的主要目的是降低风险；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH51-S08_010",
      "section_id": "CH51-S08",
      "card_nature": "execution",
      "title": "与监管频繁沟通以设定期望并考虑可解释性要求",
      "flow_nodes": [
        {
          "node_id": "N19",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构尽早并经常与监管机构沟通",
          "evidence_unit_ids": [
            "v7u_N003870"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N20",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "设定期望并考虑可解释性要求",
          "evidence_unit_ids": [
            "v7u_N003870"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E10",
          "edge_type": "PRODUCES",
          "source": "N19",
          "target": "N20",
          "evidence_unit_ids": [
            "v7u_N003870"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N003870"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构尽早并经常与监管沟通 --PRODUCES--> 设定期望并考虑可解释性要求；KG不足：基础KG规定沟通措施，未表达沟通产生的具体结果（设定期望等）；选项判断：可确认频繁沟通有助于设定期望和处理监管要求；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH51-S08_011",
      "section_id": "CH51-S08",
      "card_nature": "execution",
      "title": "解决运营影响（如培训）防止未来低效",
      "flow_nodes": [
        {
          "node_id": "N21",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构解决运营影响（包括培训员工掌握新工作流程和系统输出）",
          "evidence_unit_ids": [
            "v7u_N003871"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N22",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "未来低效被防止",
          "evidence_unit_ids": [
            "v7u_N003871"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E11",
          "edge_type": "PRODUCES",
          "source": "N21",
          "target": "N22",
          "evidence_unit_ids": [
            "v7u_N003871"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N003871"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构解决运营影响（包括培训员工） --PRODUCES--> 未来低效被防止；KG不足：基础KG规定措施“解决运营影响”，未表达防止低效这一直接结果；选项判断：可确认培训等运营解决措施旨在预防未来低效；LLM推理：无。"
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
  "cand_005",
  "cand_006",
  "cand_008",
  "cand_009",
  "cand_010",
  "cand_017",
  "cand_020"
]
```

