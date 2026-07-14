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
- 方向错误的已有边是否需要追加一条证据支持的正确关系。

只能追加节点、边和`source_unit_ids`。不得删除、修改、重新编号或替换已有card、节点或边。已有错误边留给P7D拒绝；可以追加正确的替代边，新增边仍须由P7D审核。

## 成卡标准

新增关系必须同时满足：

1. 当前section证据支持关系两端、主体、方向和条件（如有）。
2. 关系超出基础KG能充分表达的定义、事实、列表、普通机制或一般知识关系。
3. 关系能帮助判断选项的顺序、条件、职责、义务、应对、适用范围或限定性结果。
4. 不需要补造主体、动作、条件或结果。

相邻句之间缺少明确连接词，但存在必要功能依赖时，可以输出`derivation=llm_inference`，交P7D和人工复核；不得伪装为`explicit_text`。

不得以“纯义务陈述”“没有复杂步骤”或“只受风险偏好约束”为由跳过已经具备主体、动作和方向的关系。

以下通常保持`kg_only`：纯定义/分类/阈值数值/组成列表、普通犯罪手法、孤立红旗、普通案例事实、一般机制因果、抽象风险缓解目的，以及必须补造主体或方向才能成立的关系。

特别地，“当局调查非法活动时受到腐败官员阻挠”只有调查困难和犯罪机制，不是金融机构/监管主体的识别、评估、决策或应对链，必须保持`kg_only`。不要因为句子含有`investigate`、`block`或`hinder`就自动成卡。

后续unit如果只是独立事实、犯罪性质说明、处罚或背景结果，不能仅因位于某个process之后就追加为该process的`PRODUCES`目标。只有原文明确说明同一动作产生该结果，或存在必要功能依赖时，才允许建立边；否则保留为KG内容。

调优、控制或框架组成的定义、目标和一般效果通常由KG承接；只有具体主体基于明确输入执行创建/修改/删除、监控、评估或应对动作时，才进入P7C。

## 重点回归边界

- “不断演变的法规可能与现有业务模式和控制错位；合规计划必须持续更新”：两句共同形成变化/错位到更新应对的候选，`unit_ids`必须覆盖两句；没有明确连接词时边标记`llm_inference`，不能把两句分别留给KG。
- “部分机构采用一旦PEP永远PEP，因为个人即使卸任仍可能保持影响力”：不得写成“卸任`PRECEDES`机构采用方法”。应把“部分机构维持PEP分类”作为process，把“卸任后仍可能保有影响力”作为input并用`REFERENCES`表达理由/判断依据，同时保留“部分机构、即使、可能”。
- “其他机构考察个人影响力和PEP分类时间”：评估动作应通过`REFERENCES`连接两个判断输入，即使没有独立出口也可以成卡。
- “高风险客户的受益所有权阈值可能降至10%或5%”：高风险适用条件必须进入关系的`condition`或明确的条件节点和边，不能只埋在“适用阈值”节点标签中。
- “持续监控基于预定义标准标记交易，并有助于识别异常模式”：标准约束和带`help`限定的识别结果都应进入图。
- “资产管理人的CDD流程要求了解所有交易参与方”：CDD动作应通过`REFERENCES`连接所需参与方信息。

不得把“识别并核实控制人”再连接到“控制人已识别”这种主动式/被动式同义出口。不得把FIU红旗、案件升级、执法监控和资产冻结仅按教材顺序重新串成总链；只有原文明示的局部触发或结果边才可追加。

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
- 单一路径条件使用带`condition`的`PRECEDES`；只有至少两条原文明示路径才使用`DECIDES`。
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

section_id: `CH03-S02`

section_title: `Examples of predicate crimes > Environmental crime`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "环境犯罪的定义和范围",
      "title_en": "Definition and scope of environmental crime",
      "covered_units": [
        {
          "unit_id": "v7u_N000217",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000218",
          "unit_type": "classification",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000216",
          "unit_type": "fact",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "起诉环境犯罪的困难",
      "title_en": "Difficulties in prosecuting environmental crimes",
      "covered_units": [
        {
          "unit_id": "v7u_N000220",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000221",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000222",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000219",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "环境犯罪与洗钱",
      "title_en": "Environmental crimes and money laundering",
      "covered_units": [
        {
          "unit_id": "v7u_N000223",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000225",
          "unit_type": "process",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000228",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000224",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000226",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000227",
          "unit_type": "case",
          "kg_role": "illustrates"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "环境犯罪的定义和范围",
      "target_title": "起诉环境犯罪的困难",
      "relation_type": "prepares"
    },
    {
      "source_title": "起诉环境犯罪的困难",
      "target_title": "环境犯罪与洗钱",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000216|216] While all financial crime is troubling, environmental crimes are unique in terms of their lasting effects.
ZH: 环境犯罪具有独特的持久影响

[v7u_N000217|217] The Financial Crimes Enforcement Network (FinCEN) acknowledged this fact in its advisory on environmental crimes, defining them as “...illegal activity that harms human health, and harm nature and natural resources by damaging environmental quality. This can include driving biodiversity loss, and causing the overexploitation of natural resources, and thereby increasing carbon dioxide levels in the atmosphere.
ZH: FinCEN将环境犯罪定义为损害人类健康、自然和资源的非法活动

[v7u_N000218|218] Wildlife trafficking can be considered a subcategory of environmental crime due to its impact on nature. However, for enforcement purposes, it is a standalone crime.
ZH: 野生动物贩运既是环境犯罪子类也是独立犯罪

[v7u_N000219|219] Environmental crimes are complex. It is difficult to pursue criminal charges for the following reasons:
ZH: 环境犯罪复杂，刑事指控困难的原因

[v7u_N000220|220] They often involve transnational criminal organizations (TCOs).
ZH: 环境犯罪常涉及跨国犯罪组织

[v7u_N000221|221] They can be very difficult to detect prior to and during the activity.
ZH: 环境犯罪作为上游犯罪，在活动前和活动中难以被发现。

[v7u_N000222|222] They can involve several global criminal and noncriminal regulations.
ZH: 环境犯罪涉及多项全球刑事和非刑事法规。

[v7u_N000223|223] TCOs and other criminal organizations are constantly looking for ways to supplement their income, and environmental crimes offer the opportunity to both earn and launder funds simultaneously.
ZH: 环境犯罪为犯罪组织提供同时赚取和清洗资金的机会。

[v7u_N000224|224] For example, a TCO might be a part owner of a waste management and transportation front company.
ZH: 犯罪组织可能部分拥有废物管理和运输幌子公司。

[v7u_N000225|225] Their ownership would allow the TCO to inflate contracts to place illicit funds. It could then execute those contracts with complicit accountholders to layer the funds.
ZH: 犯罪组织通过虚增合同和共谋账户持有人进行离析阶段。

[v7u_N000226|226] If there is any actual hazardous waste disposal carried out, it is done in a way that minimizes overhead and increases profit, such as dumping chemical production byproducts in public drinking and bathing reservoirs.
ZH: 危险废物处置中通过最小化间接费用增加利润，如将化学副产品倾倒入公共水源。

[v7u_N000227|227] Similarly, TCOs might initiate or extort legitimate-appearing fishing, logging, and mining operations, either illegally harvesting natural resources or expanding the scope of a previously legitimate operation.
ZH: 犯罪组织发起或勒索看似合法的渔业、伐木和采矿业务。

[v7u_N000228|228] When authorities investigate the illicit activity, they often become hindered by corrupt government officials who have been bribed to block or hide the inquiry.
ZH: 腐败官员收受贿赂阻碍对非法活动的调查。
```

allowed_unit_ids:

```json
[
  "v7u_N000216",
  "v7u_N000217",
  "v7u_N000218",
  "v7u_N000219",
  "v7u_N000220",
  "v7u_N000221",
  "v7u_N000222",
  "v7u_N000223",
  "v7u_N000224",
  "v7u_N000225",
  "v7u_N000226",
  "v7u_N000227",
  "v7u_N000228"
]
```

original_json:

```json
{
  "section_id": "CH03-S02",
  "section_title": "Examples of predicate crimes > Environmental crime",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N000216"
      ],
      "proposition": "环境犯罪具有独特的持久影响",
      "decision": "kg_only",
      "card_id": null,
      "reason": "属于孤立事实陈述，未形成条件化主体动作或判断链，基础KG可保存。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000217",
        "v7u_N000218"
      ],
      "proposition": "FinCEN定义环境犯罪，野生动物贩运为子类但独立",
      "decision": "kg_only",
      "card_id": null,
      "reason": "属于定义和分类知识，基础KG可直接表达。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000219",
        "v7u_N000220",
        "v7u_N000221",
        "v7u_N000222"
      ],
      "proposition": "环境犯罪复杂，刑事指控困难的原因包括涉及跨国组织、难以发现、法规复杂",
      "decision": "kg_only",
      "card_id": null,
      "reason": "属于一般性解释和原因列表，无特定主体应对或判断结构，基础KG可承接。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000223",
        "v7u_N000224",
        "v7u_N000225"
      ],
      "proposition": "犯罪组织通过虚增合同和共谋账户利用环境犯罪洗钱",
      "decision": "kg_only",
      "card_id": null,
      "reason": "属于普通犯罪案例机制（placement/layering），无机构识别、评估或应对响应，基础KG可作案例表达。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000226",
        "v7u_N000227"
      ],
      "proposition": "如果进行危险废物处置，以最小化费用方式倾倒；犯罪组织发起或勒索看似合法的资源开采业务",
      "decision": "kg_only",
      "card_id": null,
      "reason": "属于犯罪手法具体描述，无制度性应对或条件化判断，基础KG可保存为案例机制。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000228"
      ],
      "proposition": "当局调查非法活动时，常受到受贿官员阻碍",
      "decision": "kg_only",
      "card_id": null,
      "reason": "属于孤立风险指标或一般困难陈述，无后续机构应对流程或判断分析，基础KG已识别为风险说明。"
    }
  ],
  "cards": [],
  "skip_reason": "当前章节内容主要是定义、分类、犯罪背景、起诉困难、犯罪手法案例和一般风险说明，所有命题已由基础KG充分表达，不存在超出定义、事实、案例或孤立风险指标的增量程序性或判断性有向结构。"
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
  "cand_006"
]
```
