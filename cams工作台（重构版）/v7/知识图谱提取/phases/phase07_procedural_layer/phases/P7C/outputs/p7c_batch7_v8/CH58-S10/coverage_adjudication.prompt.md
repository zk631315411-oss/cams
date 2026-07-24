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

section_id: `CH58-S10`

section_title: `Data as an input for solutions > External data`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "外部数据简介",
      "title_en": "Introduction to External Data",
      "covered_units": [
        {
          "unit_id": "v7u_N004742",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N004743",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004745",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004744",
          "unit_type": "fact",
          "kg_role": "illustrates"
        }
      ]
    },
    {
      "title_zh": "外部数据的用途",
      "title_en": "Uses of External Data",
      "covered_units": [
        {
          "unit_id": "v7u_N004746",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N004747",
          "unit_type": "fact",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N004749",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N004748",
          "unit_type": "fact",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "数据质量与验证要求",
      "title_en": "Data Quality and Validation Requirements",
      "covered_units": [
        {
          "unit_id": "v7u_N004752",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004754",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004755",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004757",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004751",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004750",
          "unit_type": "rule",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N004753",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004756",
          "unit_type": "rule",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "外部数据的法律与合规要求",
      "title_en": "Legal and Regulatory Compliance for External Data",
      "covered_units": [
        {
          "unit_id": "v7u_N004758",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N004760",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004759",
          "unit_type": "case",
          "kg_role": "illustrates"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "外部数据简介",
      "target_title": "外部数据的用途",
      "relation_type": "prepares"
    },
    {
      "source_title": "外部数据简介",
      "target_title": "数据质量与验证要求",
      "relation_type": "prepares"
    },
    {
      "source_title": "外部数据简介",
      "target_title": "外部数据的法律与合规要求",
      "relation_type": "prepares"
    },
    {
      "source_title": "数据质量与验证要求",
      "target_title": "外部数据的法律与合规要求",
      "relation_type": "parallels"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N004742|4742] External data refers to information from sources outside the organization.
ZH: 外部数据指来自组织外部的信息。

[v7u_N004743|4743] It is important that organizations source, collate, clean, and prepare external data before using it. It is essential that organizations source, collate, clean, and prepare external data before incorporating it into their compliance systems.
ZH: 组织在使用外部数据前必须进行来源、整理、清洗和准备工作。

[v7u_N004744|4744] Third parties can also provide external data, such as lists for screening purposes, intelligence from government agencies, or identification details from registries.
ZH: 第三方可提供外部数据，如筛查名单、政府情报或注册信息。

[v7u_N004745|4745] External data enriches and enhances internal data.
ZH: 外部数据可丰富和增强内部数据。

[v7u_N004746|4746] For example, organizations import business registration details to improve KYC and due diligence processes. Similarly, data from court records and other government agencies can be valuable.
ZH: 组织导入商业注册信息以改进了解你的客户和尽职调查流程。

[v7u_N004747|4747] Organizations also use external data to perform a specific function, such as list screening.
ZH: 组织使用外部数据执行特定功能，如名单筛查。

[v7u_N004748|4748] For larger financial institutions, data sources are usually third-party providers who collate data from multiple sources and provide a single preconfigured dataset.
ZH: 大型金融机构通常从第三方提供商获取整合后的外部数据集。

[v7u_N004749|4749] Another example of a specific function for external data is adverse media screening, which sources can supply automatically or manually.
ZH: 外部数据可用于负面媒体报道筛查，数据源可自动或手动提供。

[v7u_N004750|4750] Organizations should take care when using external data.
ZH: 组织在使用外部数据时应谨慎。

[v7u_N004751|4751] They are accountable for system accuracy.
ZH: 组织对系统准确性负责。

[v7u_N004752|4752] Organizations should validate and test externally provided data for accuracy, reliability, compatibility, and consistency.
ZH: 组织应验证和测试外部数据的准确性、可靠性、兼容性和一致性。

[v7u_N004753|4753] This is particularly relevant when using open-source or publicly available records.
ZH: 使用开源或公开记录时尤其需要验证和测试。

[v7u_N004754|4754] Organizations should consider the source of external data and whether additional checks are needed to validate its quality or assess potential malicious data or misinformation, such as incorrect adverse media reports.
ZH: 组织应考虑外部数据来源，并评估是否需要额外检查以验证质量或识别恶意数据。

[v7u_N004755|4755] AI products provide useful information, but AI responses should be verified like any external data.
ZH: AI产品提供有用信息，但AI响应应像外部数据一样被验证。

[v7u_N004756|4756] It is more appropriate to use AI to locate primary sources, which can then be verified for accuracy.
ZH: 更合适的方式是使用AI定位主要来源，然后验证其准确性。

[v7u_N004757|4757] Organizations should require additional system testing when incorporating external data into compliance systems to check for poor quality and negative performance impacts.
ZH: 将外部数据纳入合规系统时，组织应要求额外的系统测试以检查质量问题和负面性能影响。

[v7u_N004758|4758] Additionally, an organization should consider whether it has a legal right to use the data. Consider whether storage and retention restrictions apply.
ZH: 组织应考虑使用数据的法律权利以及存储和保留限制。

[v7u_N004759|4759] For example, many jurisdictions have laws and regulations governing what data may be used for and how organizations must store or delete it.
ZH: 许多司法管辖区有法律法规规定数据的使用方式及存储或删除要求。

[v7u_N004760|4760] Organizations are using privacy-enhancing technologies and other tools to broaden the availability of data for financial crime purposes while adhering to local data regulations.
ZH: 组织正在使用隐私增强技术等工具，在遵守当地数据法规的同时扩大金融犯罪数据的可用性。
```

allowed_unit_ids:

```json
[
  "v7u_N004742",
  "v7u_N004743",
  "v7u_N004744",
  "v7u_N004745",
  "v7u_N004746",
  "v7u_N004747",
  "v7u_N004748",
  "v7u_N004749",
  "v7u_N004750",
  "v7u_N004751",
  "v7u_N004752",
  "v7u_N004753",
  "v7u_N004754",
  "v7u_N004755",
  "v7u_N004756",
  "v7u_N004757",
  "v7u_N004758",
  "v7u_N004759",
  "v7u_N004760"
]
```

original_json:

```json
{
  "section_id": "CH58-S10",
  "section_title": "Data as an input for solutions > External data",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N004743"
      ],
      "proposition": "组织在使用外部数据前必须执行source, collate, clean, prepare动作",
      "decision": "kg_only",
      "card_id": null,
      "reason": "该义务缺少具体的使用情境，属于一般性准备要求，基础KG可表达"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N004744"
      ],
      "proposition": "第三方可提供外部数据，如筛查名单、政府情报等",
      "decision": "kg_only",
      "card_id": null,
      "reason": "事实陈述，无程序性有向结构"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N004745"
      ],
      "proposition": "外部数据可丰富和增强内部数据",
      "decision": "kg_only",
      "card_id": null,
      "reason": "效益说明，无程序步骤或判断"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N004746"
      ],
      "proposition": "组织导入商业注册信息改进KYC和尽职调查流程",
      "decision": "p7c_card",
      "card_id": "p7card_CH58-S10_001",
      "reason": "导入动作与流程改进之间存在有向因果关系，基础KG无法表达该方向链"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N004747"
      ],
      "proposition": "组织使用外部数据执行名单筛查等特定功能",
      "decision": "kg_only",
      "card_id": null,
      "reason": "用途说明，无有向程序链"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N004748"
      ],
      "proposition": "大型金融机构从第三方获取整合后的外部数据集",
      "decision": "kg_only",
      "card_id": null,
      "reason": "事实描述，无有向步骤"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N004749"
      ],
      "proposition": "外部数据可用于负面媒体报道筛查，数据源可自动或手动提供",
      "decision": "kg_only",
      "card_id": null,
      "reason": "用途和来源说明，无程序性有向关系"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N004750"
      ],
      "proposition": "组织在使用外部数据时应谨慎",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性告诫，无具体动作或条件"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N004751"
      ],
      "proposition": "组织对系统准确性负责",
      "decision": "kg_only",
      "card_id": null,
      "reason": "责任陈述，无程序步骤"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N004752",
        "v7u_N004753"
      ],
      "proposition": "使用开源或公开记录时，组织应验证和测试外部数据的准确性、可靠性、兼容性和一致性",
      "decision": "p7c_card",
      "card_id": "p7card_CH58-S10_002",
      "reason": "条件触发的验证动作形成有向结构，基础KG无法表达特定条件下的义务传导"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N004754"
      ],
      "proposition": "组织应考虑外部数据来源并评估是否需要额外检查以验证质量或识别恶意数据",
      "decision": "p7c_card",
      "card_id": "p7card_CH58-S10_003",
      "reason": "评估过程明确参照了输入来源，形成判断性有向关系，基础KG无法表达该参照依赖"
    },
    {
      "candidate_id": "cand_012",
      "unit_ids": [
        "v7u_N004755"
      ],
      "proposition": "组织应验证AI产品响应（像验证外部数据一样）",
      "decision": "p7c_card",
      "card_id": "p7card_CH58-S10_004",
      "reason": "验证动作与输入对象的参照关系构成有向结构，基础KG仅能表达义务本身"
    },
    {
      "candidate_id": "cand_013",
      "unit_ids": [
        "v7u_N004756"
      ],
      "proposition": "使用AI定位主要来源后，应验证其准确性",
      "decision": "p7c_card",
      "card_id": "p7card_CH58-S10_005",
      "reason": "两个动作的先后顺序和依赖关系构成程序性链，基础KG无法表达步骤间的方向"
    },
    {
      "candidate_id": "cand_014",
      "unit_ids": [
        "v7u_N004757"
      ],
      "proposition": "将外部数据纳入合规系统时，组织应要求额外系统测试以检查低质量和负面性能影响",
      "decision": "p7c_card",
      "card_id": "p7card_CH58-S10_006",
      "reason": "纳入动作触发测试要求的有向因果链，基础KG无法表达该条件-动作关系"
    },
    {
      "candidate_id": "cand_015",
      "unit_ids": [
        "v7u_N004758"
      ],
      "proposition": "组织应考虑数据使用的法律权利和存储保留限制",
      "decision": "kg_only",
      "card_id": null,
      "reason": "考虑性义务缺少后续决策或动作链，基础KG可表达"
    },
    {
      "candidate_id": "cand_016",
      "unit_ids": [
        "v7u_N004759"
      ],
      "proposition": "许多司法管辖区有法律法规规定数据使用和存储要求",
      "decision": "kg_only",
      "card_id": null,
      "reason": "事实说明，无程序性有向结构"
    },
    {
      "candidate_id": "cand_017",
      "unit_ids": [
        "v7u_N004760"
      ],
      "proposition": "组织使用隐私增强技术等工具，在遵守当地数据法规的同时扩大金融犯罪数据可用性",
      "decision": "p7c_card",
      "card_id": "p7card_CH58-S10_007",
      "reason": "动作同时参照约束标准并产生独立结果，形成多重有向关系，基础KG无法表达内部结构化依赖"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH58-S10_001",
      "section_id": "CH58-S10",
      "card_nature": "execution",
      "title": "导入商业注册信息改进KYC案例",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "组织：导入商业注册信息",
          "evidence_unit_ids": [
            "v7u_N004746"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "KYC和尽职调查流程得到改进",
          "evidence_unit_ids": [
            "v7u_N004746"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "PRODUCES",
          "source": "n1",
          "target": "n2",
          "evidence_unit_ids": [
            "v7u_N004746"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004746"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：组织导入商业注册信息 → 改进KYC和尽职调查流程；KG不足：基础KG只能表达导入改进这一事实，无法表达导入动作和流程改进之间的有向因果关系；选项判断：可确认或排除关于外部数据如何改进KYC流程的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH58-S10_002",
      "section_id": "CH58-S10",
      "card_nature": "control",
      "title": "使用开源或公开记录时验证测试外部数据",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "使用开源或公开记录",
          "evidence_unit_ids": [
            "v7u_N004753"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "组织应验证和测试外部数据的准确性、可靠性、兼容性和一致性",
          "evidence_unit_ids": [
            "v7u_N004752",
            "v7u_N004753"
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
          "condition": "当使用开源或公开记录时",
          "evidence_unit_ids": [
            "v7u_N004752",
            "v7u_N004753"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004752",
        "v7u_N004753"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：使用开源或公开记录 → 组织应验证和测试外部数据；KG不足：基础KG将验证测试作为一般规则保存，无法表达在使用开源记录时这一特定条件触发的有向关系；选项判断：可确认或排除关于何时需要验证外部数据的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH58-S10_003",
      "section_id": "CH58-S10",
      "card_nature": "assessment",
      "title": "考虑外部数据来源并评估额外检查必要性",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "组织应考虑外部数据来源并评估是否需要额外检查以验证质量或识别恶意数据",
          "evidence_unit_ids": [
            "v7u_N004754"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "外部数据来源",
          "evidence_unit_ids": [
            "v7u_N004754"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "REFERENCES",
          "source": "n1",
          "target": "n2",
          "relation_type": "clue_supports_identification",
          "evidence_unit_ids": [
            "v7u_N004754"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004754"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：组织在评估时参照外部数据来源，考虑是否需要额外检查；KG不足：基础KG可保存'考虑来源'这一要求，但无法表达'来源'作为输入被'评估'动作参照的有向关系；选项判断：可确认或排除关于验证外部数据时应考虑来源的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH58-S10_004",
      "section_id": "CH58-S10",
      "card_nature": "control",
      "title": "验证AI产品响应",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "组织应验证AI产品响应（像验证外部数据一样）",
          "evidence_unit_ids": [
            "v7u_N004755"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "AI产品响应",
          "evidence_unit_ids": [
            "v7u_N004755"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "REFERENCES",
          "source": "n1",
          "target": "n2",
          "evidence_unit_ids": [
            "v7u_N004755"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004755"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：组织应将AI响应作为输入进行验证；KG不足：基础KG可保存'AI响应应被验证'的事实，但无法表达'AI响应'作为被验证的输入对象与验证动作之间的有向参照关系；选项判断：可确认或排除关于AI数据验证要求的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH58-S10_005",
      "section_id": "CH58-S10",
      "card_nature": "execution",
      "title": "使用AI定位主要来源后验证准确性",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "使用AI定位主要来源",
          "evidence_unit_ids": [
            "v7u_N004756"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "验证准确性",
          "evidence_unit_ids": [
            "v7u_N004756"
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
          "condition": "在定位主要来源后",
          "evidence_unit_ids": [
            "v7u_N004756"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004756"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：使用AI定位主要来源 → 验证其准确性；KG不足：基础KG可保存'使用AI定位来源然后验证'作为一般做法，但无法表达两个动作之间的先后顺序和依赖关系；选项判断：可确认或排除关于AI在外部数据验证中使用方法的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH58-S10_006",
      "section_id": "CH58-S10",
      "card_nature": "control",
      "title": "将外部数据纳入合规系统时的额外系统测试",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "将外部数据纳入合规系统",
          "evidence_unit_ids": [
            "v7u_N004757"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "组织应要求额外的系统测试以检查低质量和负面性能影响",
          "evidence_unit_ids": [
            "v7u_N004757"
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
          "condition": "当将外部数据纳入合规系统时",
          "evidence_unit_ids": [
            "v7u_N004757"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004757"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：将外部数据纳入合规系统 → 组织应要求额外系统测试；KG不足：基础KG可保存'纳入时需测试'的规则，但无法表达纳入动作触发测试要求的有向因果；选项判断：可确认或排除关于何时需要额外系统测试的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH58-S10_007",
      "section_id": "CH58-S10",
      "card_nature": "execution",
      "title": "使用隐私增强技术扩大数据可用性并遵守法规",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "组织使用隐私增强技术等工具扩大金融犯罪数据可用性",
          "evidence_unit_ids": [
            "v7u_N004760"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "当地数据法规",
          "evidence_unit_ids": [
            "v7u_N004760"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n3",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "金融犯罪数据可用性扩大",
          "evidence_unit_ids": [
            "v7u_N004760"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "REFERENCES",
          "source": "n1",
          "target": "n2",
          "relation_type": "standard_constrains_action",
          "evidence_unit_ids": [
            "v7u_N004760"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e2",
          "edge_type": "PRODUCES",
          "source": "n1",
          "target": "n3",
          "evidence_unit_ids": [
            "v7u_N004760"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004760"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：组织使用PET → 扩大数据可用性，同时参照当地数据法规作为约束；KG不足：基础KG可保存'组织使用PET遵守法规扩大可用性'的事实，但无法表达法规作为约束标准被动作参照，以及扩大可用性是动作产出的独立结果；选项判断：可确认或排除关于PET用途和合规要求的选项；LLM推理：无。"
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
  "cand_005",
  "cand_006",
  "cand_007",
  "cand_008",
  "cand_009",
  "cand_015",
  "cand_016"
]
```

