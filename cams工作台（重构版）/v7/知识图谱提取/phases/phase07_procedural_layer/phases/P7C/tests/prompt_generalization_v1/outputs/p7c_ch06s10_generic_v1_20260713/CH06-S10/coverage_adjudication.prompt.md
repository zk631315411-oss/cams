# P7C Section-Local Additive Coverage Review Prompt v3

## 角色

你是P7C section级增量完整性审查器。首次抽取器已经输出候选命题和候选card，这些card尚未经过P7D正式结构校验和边级审核。首次结果可能出现三类问题：把P7C关系误判为`kg_only`、把同一关系的前提和应对拆到不同候选、或在已有card中漏画节点和边。

你的任务是在完整检查当前section后输出只增式JSON补丁。准确率仍然重要，但P7C是候选层，允许把有充分当前section证据的边交给P7D继续审核。不得为了减少候选数量而遗漏基础KG无法表达的条件、方向、主体动作或独立结果。

`original_json`提供本次无记忆API调用所需的完整首次抽取上下文。不得回显、删除或改写它。Runner只会执行受保护的追加操作。只输出严格JSON，不输出Markdown或解释。

## P7C目的与KG边界

P7C不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标、一般规则、普通机制因果和组成关系。P7C增量表达：业务情境、事件、线索、输入或标准如何关联到特定主体带原文情态的识别、评估、决策或应对，以及原文明示的独立结论、记录、状态变化、控制效果、分支或后续行动。

基础KG能保存整句话或分别保存两个知识点，不代表它已经表达句内或句间的条件、主体、方向、动作约束和独立结果。没有独立结果时允许开放式局部关系。

P7C不读取题目或参考答案，不处理跨section桥接。`section_text_with_unit_anchors`是唯一事实证据；`base_kg_section_summary`只用于去重。所有新增证据只能引用`allowed_unit_ids`。

## 三项审查

### 一、复核原`kg_only`候选

对`review_target_candidate_ids`中的每个候选逐一裁决。可以保持`kg_only`，也可以将其关联到新增card或已有card的补充内容。

### 二、重新扫描完整section

按自然段落、转折、主体、对象和条件变化重新扫描原文。即使首次抽取没有登记候选，也必须检查是否存在遗漏关系。

重点检查：

- 相邻或邻近unit分别给出条件/变化与动作/应对，首次抽取却拆成两个`kg_only`候选；
- `if, when, unless, even if, based on, require, must, should, may, monitor, identify, review, approval, escalate, trigger, result in, help`等表达；
- 输入、线索、判断维度或标准被特定主体用于识别、评估、阈值选择或处置；
- 动作产生语义独立的结论、记录、状态变化或带原文限定的控制效果；
- 已有card覆盖了主题，但遗漏后文的新对象、条件、结果或应对。

允许跨越首次候选边界，允许合并多个候选的unit，也允许使用首次候选完全未登记的当前section unit。不得跨section取证。

### 三、检查已有card的图表达完整性

逐张比较`original_json.cards`、其对应`coverage_audit.proposition`与原文：

- proposition中的条件、参照关系和独立结果是否都进入`flow_nodes + flow_edges`；
- 结果是否只藏在process标签中而没有结果节点和边；
- 多个判断输入是否只被列出，却没有通过`REFERENCES`连接到评估动作；
- 收集/计算/合计等输入处理与依据标准作出判断是否被压缩在同一个宽泛process中；
- 原文支持的互斥结果是否被压成无condition的单一`PRODUCES`；
- 方向错误的已有边是否需要追加一条证据支持的正确关系。

只能追加节点、边和`source_unit_ids`。不得删除、修改、重新编号或替换已有card、节点或边。已有错误边留给P7D拒绝；可以追加正确的替代边，新增边仍须由P7D审核。

### Card归属裁决

`original_json`中的card_id、主题相似性和候选匹配结果只用于覆盖定位，不表示遗漏内容必须补入该card。选择`card_supplement`前，必须在内部判断gap与已有process属于哪种关系：

```text
downstream_extension：新动作或结果确实位于已有动作之后，且存在原文支持的主流程边
refinement：新结构是在展开已有宽泛process内部的输入处理、标准应用或条件判断
independent_relation：只与已有card主题相同，没有有证据的主流程连接
duplicate：与已有节点或边语义重复
```

只有`downstream_extension`，或者只需为已有原子process补充其直接使用的input/standard/边时，才允许`card_supplement`。`refinement`不得作为新的并列process追加到旧card；在只增式合同不能重写旧process时，应根据证据选择`new_card`或不新增，不得为了复用旧card而制造重复处理节点。

两个process共同`REFERENCES`同一个input或standard，只表示它们参照同一辅助信息，不构成两个process之间的主流程连接。选择supplement前必须在内部合并新旧节点并检查：新增process或exit是否能通过非`REFERENCES`的有证据方向进入已有主路径；不能时不得supplement，也不得补造`PRECEDES`。

构图时遵守语义原子性：原始输入连接到实际处理它的process，标准连接到实际应用它的判断process。若结果取决于标准、阈值、充分性或判断结论，不能把条件藏在exit label中再使用无condition的`PRODUCES`。证据支持两个或以上互斥结果时使用`P3_branch_routing + DECIDES`；一般规则与同一标准下的正反实例可以共同支持候选分支，但跨unit归纳边必须标记`llm_inference`。

## 成卡标准

新增关系必须同时满足：

1. 当前section证据支持关系两端、主体、方向和条件（如有）。
2. 关系超出基础KG能充分表达的定义、事实、列表、普通机制或一般知识关系。
3. 关系能帮助判断选项的顺序、条件、职责、义务、应对、适用范围或限定性结果。
4. 不需要补造主体、动作、条件或结果。

相邻句之间缺少明确连接词，但存在必要功能依赖时，可以输出`derivation=llm_inference`，交P7D和人工复核；不得伪装为`explicit_text`。

不得以“纯义务陈述”“没有复杂步骤”或“只受风险偏好约束”为由跳过已经具备主体、动作和方向的关系。

以下通常保持`kg_only`：纯定义/分类/阈值数值/组成列表、普通犯罪手法、孤立红旗、普通案例事实、一般机制因果、抽象风险缓解目的，以及必须补造主体或方向才能成立的关系。

仅描述某项调查、活动或机制受到阻碍，不自动构成P7C关系。只有原文进一步给出特定主体据此实施的识别、评估、决策、应对或交接，才检查是否成卡；不得仅因出现行动动词就自动成卡。

后续unit如果只是独立事实、犯罪性质说明、处罚或背景结果，不能仅因位于某个process之后就追加为该process的`PRODUCES`目标。只有原文明确说明同一动作产生该结果，或存在必要功能依赖时，才允许建立边；否则保留为KG内容。

调优、控制或框架组成的定义、目标和一般效果通常由KG承接；只有具体主体基于明确输入执行创建/修改/删除、监控、评估或应对动作时，才进入P7C。

## 通用回归不变量

- 相邻或邻近unit分别表达变化/前提与主体应对时，必须先判断两端是否共同形成一条有向命题；若形成，证据应覆盖两端。缺少明示连接词但存在唯一必要功能依赖时标记`llm_inference`，不得把两端各自交给KG而遗漏关系。
- 状态变化、原因或判断依据通常是process参照的input，不得仅按语法顺序写成它`PRECEDES`主体采用某种方法。必须保留“部分、通常、即使、可能”等限定。
- 多个判断因素应连接到实际使用它们的评估process；没有独立出口不影响开放式关系成卡。
- 某项标准只在特定风险、对象或情境下适用时，适用条件必须进入`condition`或有证据的条件节点与边，不能只埋在standard或exit的label中。
- 原文同时给出标准约束和带情态的识别/控制效果时，应分别保留两种关系，并完整保留`help/may/can`等强度。
- 动作所需的参与方、材料、理由、批准或其他判断输入，应由实际消费它的process通过`REFERENCES`连接，不得写成该动作产生的结果。
- 不得把同一谓词的主动式/被动式改写拆成process与exit。不得把多个制度主体的行动仅按教材排列顺序串成总链；只有原文明示的局部触发、必要功能先后或结果关系才可追加。

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
- 单一路径条件使用带`condition`的`PRECEDES`；只有证据支持至少两个互斥结果时才使用`DECIDES`。互斥结果可以由明示规则直接给出，也可以由同一标准下的正反实例共同支持；仅有孤立案例时不得推广。
- `DECIDES`只能由`P3_branch_routing`发出。
- `derivation`只能为`explicit_text`或`llm_inference`。

静态适用对象、材料、因素、阈值、监管要求或风险偏好不得仅因语法顺序建成`entry --PRECEDES--> process`；应作为input/standard，由process通过`REFERENCES`指向。不得把同一谓词的主动式和被动式拆成动作和结果，不得把动作所需的批准、理由、标准或要求/义务写成`PRODUCES`。

`REFERENCES.condition`只限定input/standard适用于process的范围，不表达条件分支。单一路径`PRECEDES.condition`表达逻辑前提，不要求钟表式先后。

必须保留`must, should, may, might, could, often, potentially, help, typically`等情态和限定。`help mitigate`只能写成“有助于缓解”，不能写成必然降低。`must`本身不证明义务是持续、定期、永久或反复的。`X7_continuing_obligation`只用于原文明示新建立的独立持续义务，规范性动作仍保留在process中。

`escalate/escalation`默认写成“升级处理/升级处置”或保留英文，不得翻译为“上报/报告”；只有原文明示`report/notify/file/refer`及对象时才能写成报告或移交。

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

新`candidate_id`不得与`original_json.coverage_audit`重复。`unit_ids`可以是多个原候选unit的并集，也可以包含首次未登记的当前section unit。

### new_cards

只放新增完整card。每张必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。`card_nature`只能为`execution, assessment, risk_indicator, control`；不得输出`local_process`等自造值。`candidate_status`固定为`candidate`。card ID不得与已有card重复。每张新card必须被某条提升裁决或`new_candidates`引用。

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

至少新增一个节点或一条边。新增ID不得与该card已有ID重复。新增边可以连接已有节点和新增节点。所有新增节点、边的证据unit必须已经存在于card的`source_unit_ids`，或同时列入`add_source_unit_ids`。每个被补充的card必须由一条提升裁决或`new_candidates`引用。

`card_supplement`不是默认选项。matched card、相同主题、共享unit或共享auxiliary都不足以证明归属。若新增内容是在细化已有宽泛process，或者新增process/exit无法通过非`REFERENCES`边进入已有主路径，应使用`new_card`承载证据充分的局部结构；不得把两个断开的处理中心塞进同一card。

没有某类修改时输出空数组。即使`review_target_candidate_ids`为空，仍必须扫描完整section、审核已有card，并输出五个顶层字段。

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

section_id: `CH06-S10`

section_title: `Money Laundering Risks in Financial Services > Control and ownership for AML compliance`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "受益所有人（BO）与最终受益所有人（UBO）",
      "title_en": "Beneficial Owner (BO) vs Ultimate Beneficial Owner (UBO)",
      "covered_units": [
        {
          "unit_id": "v7u_N000484",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000485",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000486",
          "unit_type": "classification",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000487",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000483",
          "unit_type": "fact",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "UBO识别要求、门槛及特殊情况",
      "title_en": "UBO Identification Requirements, Thresholds, and Special Cases",
      "covered_units": [
        {
          "unit_id": "v7u_N000488",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000489",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000490",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000491",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000493",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000496",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000492",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000494",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000495",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000497",
          "unit_type": "case",
          "kg_role": "illustrates"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "受益所有人（BO）与最终受益所有人（UBO）",
      "target_title": "UBO识别要求、门槛及特殊情况",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000483|483] Control and ownership play a vital role in AML efforts, as they can often be obscured or concealed, allowing bad actors to disguise criminal activities and facilitate financial crime.
ZH: 控制权和所有权在反洗钱工作中至关重要

[v7u_N000484|484] A beneficial owner (BO) is defined as an individual or entity that possesses ownership of a legal entity, either through shareholding or other means.
ZH: 受益所有人（BO）的定义：通过持股或其他方式拥有法律实体的个人或实体

[v7u_N000485|485] In contrast, the ultimate beneficial owner (UBO) refers specifically to one or more natural persons who ultimately owns a substantial percentage of shareholding.
ZH: 最终受益所有人（UBO）的定义：最终持有重大比例股份的自然人

[v7u_N000486|486] It is important to note that a BO might appear to have ownership of a company but might not control the company. Conversely, a UBO might not directly hold shares but does exert ultimate control over it.
ZH: BO 可能拥有所有权但不控制公司，UBO 可能不直接持股但实施最终控制

[v7u_N000487|487] This distinction is crucial when it comes to regulatory requirements surrounding ownership structures.
ZH: BO 与 UBO 的区别对所有权结构的监管要求至关重要

[v7u_N000488|488] When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer.
ZH: 监管要求审查所有权结构时必须识别客户的 UBO

[v7u_N000489|489] For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more. That means you need to know every entity or individual who owns at least 25% of a customer.
ZH: 多数司法管辖区要求识别持股 25% 或以上的受益所有人

[v7u_N000490|490] Your organization will set the appropriate threshold using a riskbased approach.
ZH: 机构应采用风险为本的方法设定受益所有权阈值

[v7u_N000491|491] For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5% for customers who pose a significantly higher risk.
ZH: 高风险客户的受益所有人阈值可能低至 10% 甚至 5%

[v7u_N000492|492] For example, high-risk financial institutions with correspondent banking relationships in a high-risk jurisdiction might set their threshold at 5%.
ZH: 示例：高风险司法管辖区的代理行关系可能设定 5% 的阈值

[v7u_N000493|493] In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership.
ZH: 识别 UBO 需要同时考虑直接和间接持股

[v7u_N000494|494] Individual D owns 10% of Company A directly. They also own 72% of Company A indirectly, as they own 90% of shares of Company B, which owns 80% of Company A. Individual D is then considered a UBO with 82% shareholding of Company A.
ZH: 示例：个人 D 通过直接和间接持股合计 82%，成为 UBO

[v7u_N000495|495] Individual C, who owns 10% of Company A directly and an additional 8% indirectly via their 10% ownership of Company B, is not a UBO.
ZH: 示例：个人 C 直接持股 10% 加间接持股 8%，未达到 UBO 标准

[v7u_N000496|496] In companies where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified. This allows you to understand who is in control of the decision-making in the company when natural individual UBOs are not present.
ZH: 无自然人受益所有人时，应识别并核实控制人或名义受益所有人

[v7u_N000497|497] For example, for a company that is publicly listed on the stock exchange and has thousands of shareholders, a notional beneficial owner could be the president or chief executive officer, or equivalent.
ZH: 示例：上市公司可将总裁或 CEO 作为名义受益所有人
```

allowed_unit_ids:

```json
[
  "v7u_N000483",
  "v7u_N000484",
  "v7u_N000485",
  "v7u_N000486",
  "v7u_N000487",
  "v7u_N000488",
  "v7u_N000489",
  "v7u_N000490",
  "v7u_N000491",
  "v7u_N000492",
  "v7u_N000493",
  "v7u_N000494",
  "v7u_N000495",
  "v7u_N000496",
  "v7u_N000497"
]
```

original_json:

```json
{
  "section_id": "CH06-S10",
  "section_title": "Money Laundering Risks in Financial Services > Control and ownership for AML compliance",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N000488"
      ],
      "proposition": "当审查所有权结构时，机构必须识别客户UBO。",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_001",
      "reason": "基础KG将规则存储为整体事实，未表达条件（审查所有权结构）与动作（识别UBO）之间的有向结构。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000490"
      ],
      "proposition": "机构采用风险为本方法设定受益所有权阈值。",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_002",
      "reason": "基础KG将规则存储为整体事实，未表达动作（设定阈值）与标准（风险为本方法）之间的约束关系。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000489",
        "v7u_N000493",
        "v7u_N000494",
        "v7u_N000495"
      ],
      "proposition": "在识别UBO时，机构合计直接和间接持股比例，与25%阈值比较，达到或超过25%者识别为UBO，否则不识别。",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_003",
      "reason": "基础KG存储了25%阈值规则和案例，但未表达输入（直接和间接持股比例）经合计计算并与阈值比较后得出分类的有向判断结构。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000496"
      ],
      "proposition": "当不存在自然人受益所有人时，机构应识别并核实控制人或名义受益所有人。",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_004",
      "reason": "基础KG存储了规则，但未表达条件（无自然人UBO）与动作（识别控制人）之间的有向触发关系。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000483",
        "v7u_N000484",
        "v7u_N000485",
        "v7u_N000486",
        "v7u_N000487"
      ],
      "proposition": "控制与所有权在AML中重要，BO和UBO的定义与区别。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG已充分表达定义、分类和背景知识。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000491",
        "v7u_N000492"
      ],
      "proposition": "高风险客户阈值可能低至10%或5%；例如代理行可能设5%。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯阈值事实和案例，没有独立的程序性或判断性有向结构。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000497"
      ],
      "proposition": "上市公司可将总裁或CEO作为名义受益所有人。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "案例，对v7u_N000496规则的举例，无新增有向结构。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH06-S10_001",
      "section_id": "CH06-S10",
      "card_nature": "execution",
      "title": "审查所有权结构时识别UBO的义务",
      "flow_nodes": [
        {
          "node_id": "E1",
          "node_category": "entry",
          "node_type": "E1_event_signal",
          "label": "机构审查所有权结构",
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构必须识别客户UBO",
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "PRECEDES",
          "source": "E1",
          "target": "P1",
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N000488"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构审查所有权结构 → 机构必须识别客户UBO；KG不足：基础KG将“审查所有权结构时识别UBO”作为整体规则存储，未表达条件与动作的有向关系；选项判断：可确认审查所有权结构是触发识别UBO的情景；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S10_002",
      "section_id": "CH06-S10",
      "card_nature": "execution",
      "title": "风险为本方法设定受益所有权阈值",
      "flow_nodes": [
        {
          "node_id": "P1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构设定受益所有权阈值",
          "evidence_unit_ids": [
            "v7u_N000490"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "S1",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "风险为本方法",
          "evidence_unit_ids": [
            "v7u_N000490"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "REFERENCES",
          "source": "P1",
          "target": "S1",
          "evidence_unit_ids": [
            "v7u_N000490"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N000490"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构设定阈值 → 参照 风险为本方法；KG不足：基础KG将整体规则存储，未表达动作与标准间的参照关系；选项判断：可确认阈值设定方法的依据是风险为本；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S10_003",
      "section_id": "CH06-S10",
      "card_nature": "assessment",
      "title": "通过合计直接和间接持股与25%阈值比较识别UBO",
      "flow_nodes": [
        {
          "node_id": "I1",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "个人直接持股比例",
          "evidence_unit_ids": [
            "v7u_N000493",
            "v7u_N000494"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "I2",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "个人间接持股比例",
          "evidence_unit_ids": [
            "v7u_N000493",
            "v7u_N000494"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P1",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "合计直接和间接持股比例（计算总持股比例）",
          "evidence_unit_ids": [
            "v7u_N000494"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "S1",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "25%受益所有权阈值",
          "evidence_unit_ids": [
            "v7u_N000489"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P3",
          "node_category": "process",
          "node_type": "P3_branch_routing",
          "label": "判断总持股比例是否达到25%阈值",
          "evidence_unit_ids": [
            "v7u_N000489",
            "v7u_N000494",
            "v7u_N000495"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X1",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "分类为UBO",
          "evidence_unit_ids": [
            "v7u_N000494"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X2",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "分类为非UBO",
          "evidence_unit_ids": [
            "v7u_N000495"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "REFERENCES",
          "source": "P1",
          "target": "I1",
          "evidence_unit_ids": [
            "v7u_N000493",
            "v7u_N000494"
          ],
          "derivation": "explicit_text",
          "relation_type": "clue_supports"
        }
      ],
      "candidate_status": "candidate"
    }
  ]
}
```

review_target_candidate_ids:

```json
[
  "cand_005",
  "cand_006",
  "cand_007"
]
```
