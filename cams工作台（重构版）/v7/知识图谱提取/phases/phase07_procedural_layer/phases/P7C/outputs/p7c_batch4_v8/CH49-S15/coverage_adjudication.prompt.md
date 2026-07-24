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

section_id: `CH49-S15`

section_title: `Concluding an investigation and suspicious activity reporting > De-risking`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "去风险化与去银行化定义及受影响行业",
      "title_en": "De-risking and debanking definitions and affected sectors",
      "covered_units": [
        {
          "unit_id": "v7u_N003678",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N003681",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N003679",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003680",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N003682",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N003683",
          "unit_type": "fact",
          "kg_role": "illustrates"
        }
      ]
    },
    {
      "title_zh": "去风险化的原因与示例",
      "title_en": "Causes and examples of de-risking",
      "covered_units": [
        {
          "unit_id": "v7u_N003684",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003687",
          "unit_type": "case",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003688",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003686",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N003689",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N003685",
          "unit_type": "fact",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "去风险化的缓解措施",
      "title_en": "Mitigation measures for de-risking",
      "covered_units": [
        {
          "unit_id": "v7u_N003690",
          "unit_type": "classification",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003691",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003692",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003693",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003694",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003695",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003696",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003697",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003698",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "去风险化与去银行化定义及受影响行业",
      "target_title": "去风险化的原因与示例",
      "relation_type": "prepares"
    },
    {
      "source_title": "去风险化的原因与示例",
      "target_title": "去风险化的缓解措施",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N003678|3678] FATF defines de-risking as the act of a financial institution terminating or restricting customer relationships, sometimes for entire client categories, because they no longer align with the organization’s risk appetite.
ZH: FATF 将去风险化定义为金融机构因客户不再符合风险偏好而终止或限制客户关系的行为。

[v7u_N003679|3679] Instead of managing risk through a risk-based approach, some organizations choose to avoid it, leading them to offboard entire segments of high-risk clients or not offer a service at all.
ZH: 部分机构选择规避风险而非基于风险方法管理风险，导致放弃高风险客户群体或完全不提供服务。

[v7u_N003680|3680] This results in financial exclusion, or de-banking.
ZH: 去风险化导致金融排斥或去银行化。

[v7u_N003681|3681] Debanking is the broader loss of financial services due to risk appetite, commercial factors, profitability, complex regulatory constraints related to AFC compliance, sanctions, or financial regulations.
ZH: 去风险化是指因风险偏好、商业因素或合规约束导致客户失去金融服务。

[v7u_N003682|3682] Consequently, certain client categories lose access to banking services, even though they might not have been directly involved with illicit activity.
ZH: 某些客户类别即使未直接涉及非法活动，也可能失去银行服务。

[v7u_N003683|3683] De-risking has reduced correspondent banking relationships in some regions and restricted banking access for sectors such as MSBs, cryptocurrency exchanges, money or value transfer services (MVTS), and non-profit organizations (NPO).
ZH: 去风险化减少了代理行关系，并限制了货币服务企业、加密货币交易所等行业的银行服务。

[v7u_N003684|3684] Organizations might avoid customers who pose compliance risks that could jeopardize regulatory obligations.
ZH: 机构可能避免与带来合规风险的客户往来。

[v7u_N003685|3685] This is common in higher-risk sectors, where cross-border remittances increase exposure to illicit activity.
ZH: 去风险化常见于跨境汇款等高风险的行业。

[v7u_N003686|3686] For example, in 2013, HSBC asked over 40 foreign embassies, including the Vatican, Papua New Guinea, and Benin, to close their accounts. This decision caused significant disruption, as diplomatic missions rely on bank accounts for essential business transactions.
ZH: 汇丰银行曾要求超过40家外国使馆关闭账户，造成重大影响。

[v7u_N003687|3687] Some organizations might also sever ties with customers over reputational concerns, such as de-banking arms manufacturers, despite legal compliance.
ZH: 机构可能因声誉担忧而与客户断绝关系，即使客户合法合规。

[v7u_N003688|3688] Regulatory inconsistencies further complicate de-risking.
ZH: 监管不一致使去风险化问题更加复杂。

[v7u_N003689|3689] For example, in the US, federally insured banks face challenges when state laws, such as those legalizing cannabis businesses, conflict with federal laws. To mitigate legal risks, many banks avoid serving such businesses altogether.
ZH: 美国银行因州法与联邦法冲突而避免服务大麻企业。

[v7u_N003690|3690] Making broad decisions based on risk aversion, rather than conducting individual risk assessments, conflicts with FATF’s Recommendations. FATF emphasizes proportional, risk-based management over broad exclusions. To mitigate de-risking, organizations could:
ZH: 基于风险规避的广泛决策与FATF建议相悖，FATF强调基于风险的个别管理。

[v7u_N003691|3691] Form a de-risking committee with members from business, legal, and compliance departments to assess risk. Some financial institutions refer to this as a Reputational Risk forum or a Client Selection committee.
ZH: 成立由业务、法律和合规部门组成的去风险化委员会来评估风险。

[v7u_N003692|3692] Adopt a risk-based approach by conducting case-by-case individual risk assessments and reviews rather than categorizing entire sectors as high risk.
ZH: 采用基于风险的方法，逐案进行个别风险评估，而非将整个行业归类为高风险。

[v7u_N003693|3693] Develop a sector-specific Wolfsberg-type questionnaire to standardize information collection.
ZH: 制定行业特定的沃尔夫斯堡式问卷以标准化信息收集。

[v7u_N003694|3694] Implement advanced transaction monitoring to improve transparency and efficiency while reducing reliance on broad restrictions.
ZH: 实施高级交易监控以提高透明度并减少对广泛限制的依赖。

[v7u_N003695|3695] Engage in multi-stakeholder discussions with regulators and industry bodies to align expectations and reduce compliance burdens.
ZH: 与监管机构和行业组织进行多方利益相关者讨论，以协调期望并降低合规负担。

[v7u_N003696|3696] Develop nuanced risk tiers that account for multiple factors beyond jurisdiction or nationality.
ZH: 开发考虑多种因素的细致风险分层，超越司法管辖区或国籍。

[v7u_N003697|3697] Provide financial access through tiered accounts with risk-appropriate transaction limits, supporting inclusion while managing exposure.
ZH: 通过分层账户提供金融服务，设置与风险相适应的交易限额。

[v7u_N003698|3698] Conduct due diligence or EDD appropriate to the specific risks of the sector or business type.
ZH: 根据行业或业务类型的特定风险进行尽职调查或强化尽职调查。
```

allowed_unit_ids:

```json
[
  "v7u_N003678",
  "v7u_N003679",
  "v7u_N003680",
  "v7u_N003681",
  "v7u_N003682",
  "v7u_N003683",
  "v7u_N003684",
  "v7u_N003685",
  "v7u_N003686",
  "v7u_N003687",
  "v7u_N003688",
  "v7u_N003689",
  "v7u_N003690",
  "v7u_N003691",
  "v7u_N003692",
  "v7u_N003693",
  "v7u_N003694",
  "v7u_N003695",
  "v7u_N003696",
  "v7u_N003697",
  "v7u_N003698"
]
```

original_json:

```json
{
  "section_id": "CH49-S15",
  "section_title": "Concluding an investigation and suspicious activity reporting > De-risking",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N003678",
        "v7u_N003679",
        "v7u_N003680",
        "v7u_N003681",
        "v7u_N003682",
        "v7u_N003683"
      ],
      "proposition": "去风险化是金融机构因风险偏好终止或限制客户关系的行为，可能导致金融排斥和某些行业失去银行服务。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "这些unit提供了去风险化和去银行化的定义、后果和受影响行业的说明，属于基础KG可以充分表达的定义、事实和一般概念关系，没有超出KG的程序性或判断性有向结构。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N003684",
        "v7u_N003685",
        "v7u_N003686",
        "v7u_N003687",
        "v7u_N003688",
        "v7u_N003689"
      ],
      "proposition": "机构可能因合规风险、声誉担忧或监管不一致而避免服务某些客户，如汇丰要求使馆关户或美国银行因法律冲突避免大麻企业。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "这些unit解释了去风险化的原因并提供了具体案例，属于基础KG可以充分表达的事实、普通案例和因果关系，不构成需要P7C提取的局部程序性或判断性有向结构。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N003690",
        "v7u_N003691",
        "v7u_N003692",
        "v7u_N003693",
        "v7u_N003694",
        "v7u_N003695",
        "v7u_N003696",
        "v7u_N003697",
        "v7u_N003698"
      ],
      "proposition": "FATF强调基于风险的个别管理，为缓解去风险化，机构可以采取多种措施，如成立委员会、个案评估、制定问卷、实施监控等。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "FATF的建议和缓解措施列表属于基础KG可以充分表达的一般规则和并列措施，没有明确的条件触发、前后依赖、判断分支或独立结果等有向过程结构，因此交由基础KG保存。"
    }
  ],
  "cards": [],
  "skip_reason": "当前section主要包含去风险化的定义、后果、原因案例以及并列的缓解措施，基础KG已能充分表达这些定义、事实、案例和措施列表，未发现需要P7C提取的局部程序性或判断性有向结构。"
}
```

review_target_candidate_ids:

```json
[
  "cand_001",
  "cand_002",
  "cand_003"
]
```

