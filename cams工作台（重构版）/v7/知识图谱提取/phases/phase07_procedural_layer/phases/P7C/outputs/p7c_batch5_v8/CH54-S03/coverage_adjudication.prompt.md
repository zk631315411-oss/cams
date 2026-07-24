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

section_id: `CH54-S03`

section_title: `Technology for KYC > Perpetual KYC`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "持续了解你的客户 (pKYC) 概述",
      "title_en": "Perpetual KYC (pKYC) Overview",
      "covered_units": [
        {
          "unit_id": "v7u_N004067",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N004068",
          "unit_type": "classification",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004069",
          "unit_type": "definition",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004072",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004074",
          "unit_type": "process",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004063",
          "unit_type": "definition",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N004064",
          "unit_type": "process",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N004065",
          "unit_type": "risk_indicator",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004066",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004070",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N004071",
          "unit_type": "fact",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N004073",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N004075",
          "unit_type": "definition",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004076",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N004077",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004078",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004079",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004080",
          "unit_type": "context",
          "kg_role": "provides_context"
        }
      ]
    }
  ],
  "covered_relations": []
}
```

section_text_with_unit_anchors:

```text
[v7u_N004063|4063] Traditional KYC within organizations involves performing KYC checks during customer onboarding and classifying customers according to risk categories (such as high, medium, or low) or risk scores.
ZH: 传统了解你的客户在客户准入时执行检查并按风险类别或评分分类

[v7u_N004064|4064] Subsequently, organizations typically update customer KYC information periodically, following a regular cycle based on the customer’s risk rating, or during event-driven reviews.
ZH: 机构按风险评级定期或事件驱动更新客户了解你的客户信息

[v7u_N004065|4065] However, typical periodic review cycles, such as once every three to five years, are too infrequent, allowing customer data to become outdated.
ZH: 定期审查周期过长导致客户数据过时的风险

[v7u_N004066|4066] To avoid this problem, organizations are increasingly shifting from periodic KYC practices to perpetual KYC to improve the overall efficiency of KYC processes.
ZH: 机构从定期了解你的客户转向持续了解你的客户以提高效率

[v7u_N004067|4067] Perpetual KYC maintains accurate customer data through nearreal-time updates based on changes in customers’ behaviors and circumstances.
ZH: 持续了解你的客户通过近实时更新保持客户数据准确

[v7u_N004068|4068] Unlike traditional KYC, perpetual KYC is a continuous process.
ZH: 持续了解你的客户是一个连续过程，区别于传统了解你的客户

[v7u_N004069|4069] Perpetual KYC monitors various up-to-date data points on an ongoing basis to identify any triggers that might warrant a KYC review of a customer.
ZH: 持续了解你的客户持续监控数据点以识别触发了解你的客户审查的触发器

[v7u_N004070|4070] These triggers include anomalies in transaction patterns, adverse media reports, changes to company structures, expansion to new markets, and growth into diverse sectors.
ZH: 持续了解你的客户的触发器包括交易异常、负面媒体、公司结构变化等

[v7u_N004071|4071] Perpetual KYC also picks up static data changes, such as changes to a customer’s address or headquarters location.
ZH: 持续了解你的客户也监控静态数据变化如地址变更

[v7u_N004072|4072] It is a data-led practice and uses multiple data sources, both internal and external, that are continuously updated.
ZH: 持续了解你的客户是数据驱动实践，使用持续更新的内外部数据源

[v7u_N004073|4073] External data might include voter registers, PEP databases, and other publicly available information.
ZH: 外部数据源包括选民登记册、政治敏感人物数据库和公开信息

[v7u_N004074|4074] This approach leads organizations to adopt a data-led methodology, allowing customer file reviews to focus on the highest-risk customers on an “as-often-as-needed” basis.
ZH: 数据驱动方法使客户档案审查聚焦于高风险客户

[v7u_N004075|4075] Perpetual KYC does not eliminate the need to carry out customer file reviews. It is a practice that ensures data is up to date, making any necessary reviews efficient and effective.
ZH: 持续了解你的客户确保数据最新，使必要审查高效有效

[v7u_N004076|4076] The implementation of perpetual KYC practices offers multiple benefits for organizations.
ZH: 实施持续了解你的客户为机构带来多重益处

[v7u_N004077|4077] One major benefit is effective financial crime risk management. By allowing updates and potential reviews, organizations can focus their resources on higher-risk areas.
ZH: 持续了解你的客户通过聚焦高风险领域实现有效的金融犯罪风险管理

[v7u_N004078|4078] Investing in perpetual KYC practices not only reduces costs but also results in operational efficiencies by minimizing unnecessary reviews triggered by non-risk-increasing factors.
ZH: 持续了解你的客户降低成本和运营效率，减少不必要的审查

[v7u_N004079|4079] Effective use of customer contact channels ensures that customer data remains up to date during each customer interaction, eliminating the need for complete refreshes each time. This, in turn, results in improved customer experience.
ZH: 有效利用客户联系渠道保持数据更新，改善客户体验

[v7u_N004080|4080] Effective risk management
ZH: 持续了解你的客户下的有效风险管理
```

allowed_unit_ids:

```json
[
  "v7u_N004063",
  "v7u_N004064",
  "v7u_N004065",
  "v7u_N004066",
  "v7u_N004067",
  "v7u_N004068",
  "v7u_N004069",
  "v7u_N004070",
  "v7u_N004071",
  "v7u_N004072",
  "v7u_N004073",
  "v7u_N004074",
  "v7u_N004075",
  "v7u_N004076",
  "v7u_N004077",
  "v7u_N004078",
  "v7u_N004079",
  "v7u_N004080"
]
```

original_json:

```json
{
  "section_id": "CH54-S03",
  "section_title": "Technology for KYC > Perpetual KYC",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N004069",
        "v7u_N004070"
      ],
      "proposition": "机构持续监控数据点，识别出触发器，可能触发KYC审查。",
      "decision": "p7c_card",
      "card_id": "p7card_CH54-S03_001",
      "reason": "基础KG只记载pKYC监控数据点识别触发器的事实，未表达监控动作产生独立识别结果并可能触发审查的有向关系，属于增量程序性结构。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N004074",
        "v7u_N004077"
      ],
      "proposition": "机构采用数据驱动方法（pKYC实践），导致审查聚焦于最高风险客户。",
      "decision": "p7c_card",
      "card_id": "p7card_CH54-S03_002",
      "reason": "基础KG可记载pKYC能聚焦高风险，但未表达采用方法导致审查聚焦的有向过程，属于增量程序性结构。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N004078"
      ],
      "proposition": "机构投资pKYC，通过减少不必要审查，降低成本并提高运营效率。",
      "decision": "p7c_card",
      "card_id": "p7card_CH54-S03_003",
      "reason": "基础KG可记载pKYC降低成本提高效率，但未表达通过减少不必要审查的因果链，属于增量程序性结构。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N004079"
      ],
      "proposition": "机构有效利用客户联系渠道，保持数据最新，从而改善客户体验。",
      "decision": "p7c_card",
      "card_id": "p7card_CH54-S03_004",
      "reason": "基础KG可记载pKYC改善体验，但未表达通过保持数据最新的具体步骤链，属于增量程序性结构。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N004075"
      ],
      "proposition": "机构实施pKYC，确保数据最新，使必要审查高效有效。",
      "decision": "p7c_card",
      "card_id": "p7card_CH54-S03_005",
      "reason": "基础KG可记载pKYC使审查高效，但未表达通过数据最新的具体因果链，属于增量程序性结构。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N004067"
      ],
      "proposition": "机构基于行为和情况变化进行近实时更新，保持客户数据准确。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG已充分表达pKYC基于变化进行更新的事实，无超出定义的程序性或判断性有向结构。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N004066"
      ],
      "proposition": "机构从定期KYC转向持续KYC以提高效率。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅趋势陈述，无增量程序结构，基础KG可表达。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N004063",
        "v7u_N004064"
      ],
      "proposition": "机构在onboarding时执行KYC检查并分类，并按风险定期更新。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "传统流程，基础KG已覆盖。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N004065"
      ],
      "proposition": "定期审查周期过长导致数据过时。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "风险陈述，基础KG可表达。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N004068"
      ],
      "proposition": "pKYC是连续过程，区别于传统KYC。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "分类对比，基础KG已覆盖。"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N004071"
      ],
      "proposition": "pKYC也捕捉静态数据变化。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "静态特征事实，无增量有向结构。"
    },
    {
      "candidate_id": "cand_012",
      "unit_ids": [
        "v7u_N004072"
      ],
      "proposition": "pKYC是数据驱动实践，使用多种数据源。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "事实描述，基础KG可表达。"
    },
    {
      "candidate_id": "cand_013",
      "unit_ids": [
        "v7u_N004073"
      ],
      "proposition": "外部数据源包括选民登记册等。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "列表举例，基础KG已覆盖。"
    },
    {
      "candidate_id": "cand_014",
      "unit_ids": [
        "v7u_N004076"
      ],
      "proposition": "实施pKYC带来多重益处。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "引言性陈述，无有向结构。"
    },
    {
      "candidate_id": "cand_015",
      "unit_ids": [
        "v7u_N004080"
      ],
      "proposition": "有效风险管理。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "片段，无有向结构。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH54-S03_001",
      "section_id": "CH54-S03",
      "card_nature": "assessment",
      "title": "持续监控识别触发KYC审查的触发器",
      "flow_nodes": [
        {
          "node_id": "P001",
          "node_category": "process",
          "node_type": "P7_monitoring",
          "label": "机构持续监控各种最新数据点以识别触发器 (Perpetual KYC monitors various up-to-date data points to identify triggers)",
          "evidence_unit_ids": [
            "v7u_N004069"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X001",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "触发器被识别：交易异常、负面媒体、公司结构变化等 (Triggers identified: anomalies in transaction patterns, adverse media, changes to company structures, etc.)",
          "evidence_unit_ids": [
            "v7u_N004069",
            "v7u_N004070"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E001",
          "edge_type": "PRODUCES",
          "source": "P001",
          "target": "X001",
          "evidence_unit_ids": [
            "v7u_N004069"
          ],
          "derivation": "explicit_text",
          "source_quote": "monitors various up-to-date data points on an ongoing basis to identify any triggers"
        }
      ],
      "source_unit_ids": [
        "v7u_N004069",
        "v7u_N004070"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构持续监控数据点 → 识别出触发器；KG不足：基础KG只记载pKYC监控数据点识别触发器的事实，未表达监控动作产生独立识别结果的有向关系；选项判断：可帮助确认或排除关于pKYC监控过程的顺序和产物选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH54-S03_002",
      "section_id": "CH54-S03",
      "card_nature": "execution",
      "title": "pKYC数据驱动方法使审查聚焦高风险客户",
      "flow_nodes": [
        {
          "node_id": "P001",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构采用数据驱动方法 (pKYC实践) (Organizations adopt a data-led methodology)",
          "evidence_unit_ids": [
            "v7u_N004074",
            "v7u_N004077"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X001",
          "node_category": "exit",
          "node_type": "X5_config_change",
          "label": "客户档案审查按需聚焦于最高风险客户 (Customer file reviews focus on highest-risk customers on an as-often-as-needed basis)",
          "evidence_unit_ids": [
            "v7u_N004074",
            "v7u_N004077"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E001",
          "edge_type": "PRODUCES",
          "source": "P001",
          "target": "X001",
          "evidence_unit_ids": [
            "v7u_N004074",
            "v7u_N004077"
          ],
          "derivation": "explicit_text",
          "source_quote": "leads organizations to adopt a data-led methodology, allowing customer file reviews to focus on the highest-risk customers"
        }
      ],
      "source_unit_ids": [
        "v7u_N004074",
        "v7u_N004077"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构采用数据驱动方法 (pKYC) → 审查聚焦高风险客户；KG不足：基础KG可记载pKYC能聚焦高风险，但未表达采用方法导致审查聚焦的有向过程；选项判断：可确认或排除关于pKYC如何导致资源配置变化的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH54-S03_003",
      "section_id": "CH54-S03",
      "card_nature": "execution",
      "title": "投资pKYC减少不必要审查并降低成本提高效率",
      "flow_nodes": [
        {
          "node_id": "P001",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构投资pKYC实践 (Organizations invest in perpetual KYC practices)",
          "evidence_unit_ids": [
            "v7u_N004078"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X001",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "不必要审查减少 (Unnecessary reviews triggered by non-risk-increasing factors are minimized)",
          "evidence_unit_ids": [
            "v7u_N004078"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X002",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "成本降低和运营效率提高 (Costs reduced and operational efficiencies increased)",
          "evidence_unit_ids": [
            "v7u_N004078"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E001",
          "edge_type": "PRODUCES",
          "source": "P001",
          "target": "X001",
          "evidence_unit_ids": [
            "v7u_N004078"
          ],
          "derivation": "explicit_text",
          "source_quote": "minimizing unnecessary reviews"
        },
        {
          "edge_id": "E002",
          "edge_type": "PRECEDES",
          "source": "X001",
          "target": "X002",
          "evidence_unit_ids": [
            "v7u_N004078"
          ],
          "derivation": "explicit_text",
          "source_quote": "not only reduces costs but also results in operational efficiencies by minimizing unnecessary reviews"
        }
      ],
      "source_unit_ids": [
        "v7u_N004078"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构投资pKYC → 不必要审查减少 → 降低成本和提高效率；KG不足：基础KG可记载pKYC降低成本提高效率，但未表达通过减少不必要审查的因果链；选项判断：可确认或排除关于pKYC经济效益实现机制的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH54-S03_004",
      "section_id": "CH54-S03",
      "card_nature": "execution",
      "title": "有效利用客户联系渠道保持数据最新并改善客户体验",
      "flow_nodes": [
        {
          "node_id": "P001",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构有效利用客户联系渠道 (Organizations effectively use customer contact channels)",
          "evidence_unit_ids": [
            "v7u_N004079"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X001",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "客户数据在每次交互时保持最新 (Customer data remains up to date during each customer interaction)",
          "evidence_unit_ids": [
            "v7u_N004079"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X002",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "改善客户体验 (Improved customer experience)",
          "evidence_unit_ids": [
            "v7u_N004079"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E001",
          "edge_type": "PRODUCES",
          "source": "P001",
          "target": "X001",
          "evidence_unit_ids": [
            "v7u_N004079"
          ],
          "derivation": "explicit_text",
          "source_quote": "ensures that customer data remains up to date"
        },
        {
          "edge_id": "E002",
          "edge_type": "PRECEDES",
          "source": "X001",
          "target": "X002",
          "evidence_unit_ids": [
            "v7u_N004079"
          ],
          "derivation": "explicit_text",
          "source_quote": "eliminating the need for complete refreshes each time. This, in turn, results in improved customer experience."
        }
      ],
      "source_unit_ids": [
        "v7u_N004079"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构有效利用联系渠道 → 数据保持最新 → 改善客户体验；KG不足：基础KG可记载pKYC改善体验，但未表达通过保持数据最新的具体步骤链；选项判断：可确认或排除关于客户体验改进机制的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH54-S03_005",
      "section_id": "CH54-S03",
      "card_nature": "execution",
      "title": "pKYC确保数据最新使必要审查高效有效",
      "flow_nodes": [
        {
          "node_id": "P001",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构实施pKYC实践以确保数据最新 (Organizations implement perpetual KYC to ensure data is up to date)",
          "evidence_unit_ids": [
            "v7u_N004075"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X001",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "客户数据保持最新 (Customer data is up to date)",
          "evidence_unit_ids": [
            "v7u_N004075"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X002",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "必要审查高效有效 (Necessary reviews are efficient and effective)",
          "evidence_unit_ids": [
            "v7u_N004075"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E001",
          "edge_type": "PRODUCES",
          "source": "P001",
          "target": "X001",
          "evidence_unit_ids": [
            "v7u_N004075"
          ],
          "derivation": "explicit_text",
          "source_quote": "ensures data is up to date"
        },
        {
          "edge_id": "E002",
          "edge_type": "PRECEDES",
          "source": "X001",
          "target": "X002",
          "evidence_unit_ids": [
            "v7u_N004075"
          ],
          "derivation": "explicit_text",
          "source_quote": "making any necessary reviews efficient and effective"
        }
      ],
      "source_unit_ids": [
        "v7u_N004075"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构实施pKYC → 数据保持最新 → 使审查高效有效；KG不足：基础KG可记载pKYC使审查高效，但未表达通过数据最新的具体因果链；选项判断：可确认或排除关于pKYC如何提高审查效率的选项；LLM推理：无。"
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
  "cand_011",
  "cand_012",
  "cand_013",
  "cand_014",
  "cand_015"
]
```

