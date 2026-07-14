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

section_id: `CH06-S09`

section_title: `Money Laundering Risks in Financial Services > Politically exposed person risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "政治敏感人物的定义、范围和关联人",
      "title_en": "PEP definition, scope, and related persons",
      "covered_units": [
        {
          "unit_id": "v7u_N000457",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000469",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000470",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000473",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000474",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000475",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000467",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000468",
          "unit_type": "classification",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000471",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000472",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "政治敏感人物识别挑战与合规要求",
      "title_en": "PEP Identification Challenges and Compliance",
      "covered_units": [
        {
          "unit_id": "v7u_N000458",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000459",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000460",
          "unit_type": "rule",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "FATF对政治敏感人物的分类",
      "title_en": "FATF Classification of PEP Types",
      "covered_units": [
        {
          "unit_id": "v7u_N000462",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000463",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000464",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000461",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "政治敏感人物的腐败风险与示例",
      "title_en": "PEP Vulnerability to Corruption and Examples",
      "covered_units": [
        {
          "unit_id": "v7u_N000465",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000466",
          "unit_type": "case",
          "kg_role": "illustrates"
        }
      ]
    },
    {
      "title_zh": "政治敏感人物风险管理与监控方法",
      "title_en": "PEP Risk Management and Monitoring Approaches",
      "covered_units": [
        {
          "unit_id": "v7u_N000476",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000477",
          "unit_type": "rule",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000481",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000482",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000479",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000478",
          "unit_type": "classification",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000480",
          "unit_type": "rule",
          "kg_role": "explains"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "政治敏感人物的定义、范围和关联人",
      "target_title": "FATF对政治敏感人物的分类",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物的定义、范围和关联人",
      "target_title": "政治敏感人物的腐败风险与示例",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物的定义、范围和关联人",
      "target_title": "政治敏感人物风险管理与监控方法",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物识别挑战与合规要求",
      "target_title": "政治敏感人物风险管理与监控方法",
      "relation_type": "prepares"
    },
    {
      "source_title": "FATF对政治敏感人物的分类",
      "target_title": "政治敏感人物的腐败风险与示例",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物的腐败风险与示例",
      "target_title": "政治敏感人物风险管理与监控方法",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000457|457] A politically exposed person (PEP) is an individual in a prominent political function, their immediate family, close associates, and any businesses held or controlled by that person.
ZH: 政治敏感人物（政治敏感人物）的定义：担任重要公职的个人及其亲属和密切关联人

[v7u_N000458|458] One challenge in identifying PEPs is the varying guidance and recommendations in each jurisdiction.
ZH: 识别政治敏感人物的挑战在于各司法管辖区指引不同

[v7u_N000459|459] Organizations must adhere to their local regulatory requirements in identifying PEPs.
ZH: 机构必须遵守当地监管要求识别政治敏感人物

[v7u_N000460|460] However, organizations may choose to enforce higher standards based on their risk appetite.
ZH: 机构可根据风险偏好执行更高的政治敏感人物标准

[v7u_N000461|461] According to the Financial Action Task Force (FATF), there are three types of PEPs:
ZH: FATF将政治敏感人物分为三类

[v7u_N000462|462] Foreign PEPs are individuals entrusted with prominent public functions by a foreign country.
ZH: 外国政治敏感人物指受外国委托担任重要公共职能的个人

[v7u_N000463|463] Domestic PEPs are individuals entrusted domestically with prominent public functions.
ZH: 国内政治敏感人物指在国内担任重要公共职能的个人

[v7u_N000464|464] International organization PEPs are individuals from an international organization entrusted with a prominent function such as secretary general, executive director, or president.
ZH: 国际组织政治敏感人物指在国际组织中担任秘书长、执行董事或主席等要职的个人

[v7u_N000465|465] Individuals in high positions and their associates are more vulnerable to corruption.
ZH: 高层职位个人及其关联人更易受腐败影响

[v7u_N000466|466] Corruption might be favors where the PEP directs government contracts to an organization in return for kickbacks. In addition, a PEP might influence legislation for bribes or flee the country with government funds.
ZH: 政治敏感人物腐败示例：以政府合同换取回扣、影响立法收受贿赂或携政府资金潜逃

[v7u_N000467|467] Use a broad definition for defining a PEP.
ZH: 应采用宽泛定义来界定政治敏感人物

[v7u_N000468|468] PEPs can generally be defined as:
ZH: 政治敏感人物的一般定义

[v7u_N000469|469] A person in a prominent decision-making or influential role
ZH: 政治敏感人物指担任重要决策或有影响力角色的人

[v7u_N000470|470] A person within royal, military, legislative, judicial, executive, or similar government positions
ZH: 政治敏感人物包括王室、军事、立法、司法、行政或类似政府职位的人

[v7u_N000471|471] PEPs will often use nominees or businesses they are associated with.
ZH: 政治敏感人物常使用名义人或关联企业

[v7u_N000472|472] Therefore, the definition of PEP can also include:
ZH: 政治敏感人物定义还可包括以下人员

[v7u_N000473|473] Immediate family
ZH: 政治敏感人物的直系亲属

[v7u_N000474|474] Close friends or associates
ZH: 政治敏感人物的密友或关联人

[v7u_N000475|475] Businesses owned or held by those individuals
ZH: 政治敏感人物拥有或持有的企业

[v7u_N000476|476] Under a risk-based approach, PEP risk is manageable.
ZH: 基于风险的方法下，政治敏感人物风险是可控的

[v7u_N000477|477] Some organizations follow a “once a PEP, always a PEP” approach because the individual may remain in the same circles of influence, even if they have stepped down.
ZH: 部分机构采用“一旦是政治敏感人物，永远是政治敏感人物”的方法

[v7u_N000478|478] Other organizations will look at:
ZH: 其他机构会考察以下因素

[v7u_N000479|479] The individual’s influence at the time, such as their ability to award contracts or allocate funds
ZH: 考察个人当时的影响力，如授予合同或分配资金的能力

[v7u_N000480|480] How long the individual has been classified as a PEP
ZH: 考察个人被归类为政治敏感人物的时间长短

[v7u_N000481|481] The purpose of the PEP designation is important.
ZH: 政治敏感人物 认定的目的具有重要意义

[v7u_N000482|482] Organizations must take the necessary steps to adapt transaction monitoring and KYC reviews and escalate based on their risk appetite.
ZH: 机构必须根据风险偏好调整交易监控和 了解你的客户 审查
```

allowed_unit_ids:

```json
[
  "v7u_N000457",
  "v7u_N000458",
  "v7u_N000459",
  "v7u_N000460",
  "v7u_N000461",
  "v7u_N000462",
  "v7u_N000463",
  "v7u_N000464",
  "v7u_N000465",
  "v7u_N000466",
  "v7u_N000467",
  "v7u_N000468",
  "v7u_N000469",
  "v7u_N000470",
  "v7u_N000471",
  "v7u_N000472",
  "v7u_N000473",
  "v7u_N000474",
  "v7u_N000475",
  "v7u_N000476",
  "v7u_N000477",
  "v7u_N000478",
  "v7u_N000479",
  "v7u_N000480",
  "v7u_N000481",
  "v7u_N000482"
]
```

original_json:

```json
{
  "section_id": "CH06-S09",
  "section_title": "Money Laundering Risks in Financial Services > Politically exposed person risks",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N000459"
      ],
      "proposition": "当地监管要求约束机构识别PEP的义务",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S09_001",
      "reason": "基础KG可将该规则保存为整体事实，但不能表达当地监管要求如何约束识别动作的内部有向关系，属于P7C增量。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000460"
      ],
      "proposition": "机构可基于风险偏好选择执行更高PEP标准",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S09_002",
      "reason": "风险偏好作为条件导向机构选择更高标准，形成有向指引关系，基础KG无法表达该方向性。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000477"
      ],
      "proposition": "即使个人卸任且可能保持影响力，部分机构仍维持PEP分类",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S09_003",
      "reason": "卸任变化与潜在影响力作为条件，导向部分机构的分类维持决策，构成条件化判断链，基础KG不能表达该有向结构。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000482"
      ],
      "proposition": "机构必须基于风险偏好调整监控、KYC审查并升级",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S09_004",
      "reason": "风险偏好约束具体操作义务的内部有向关系，超过基础KG的保存能力。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000478",
        "v7u_N000479",
        "v7u_N000480"
      ],
      "proposition": "其他机构考察个人影响力和分类时长以决定PEP状态",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅有考察维度列表，未形成明确的条件-判断-结论有向链，基础KG可保存为一般事实。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000476"
      ],
      "proposition": "基于风险的方法下PEP风险可控",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性陈述，无有向结构，归属基础KG。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000458"
      ],
      "proposition": "识别PEP的挑战在于各司法管辖区指引不同",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性挑战描述，无明确主体动作或判断方向。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N000467"
      ],
      "proposition": "应使用宽泛定义界定PEP",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性建议，无特定主体、条件或程序性方向，基础KG可保存。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N000481"
      ],
      "proposition": "PEP认定的目的很重要",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性陈述，无有向关系。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N000457",
        "v7u_N000461",
        "v7u_N000462",
        "v7u_N000463",
        "v7u_N000464",
        "v7u_N000465",
        "v7u_N000466",
        "v7u_N000468",
        "v7u_N000469",
        "v7u_N000470",
        "v7u_N000471",
        "v7u_N000472",
        "v7u_N000473",
        "v7u_N000474",
        "v7u_N000475"
      ],
      "proposition": "PEP定义、分类、风险指标及示例",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义、分类、孤立风险指标和案例机制，基础KG已充分表达，无增量有向结构。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH06-S09_001",
      "section_id": "CH06-S09",
      "card_nature": "assessment",
      "title": "当地监管要求约束PEP识别义务",
      "flow_nodes": [
        {
          "node_id": "P1",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "机构必须依据当地监管要求识别PEP",
          "evidence_unit_ids": [
            "v7u_N000459"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "ST1",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "当地监管要求",
          "evidence_unit_ids": [
            "v7u_N000459"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "REFERENCES",
          "source": "P1",
          "target": "ST1",
          "evidence_unit_ids": [
            "v7u_N000459"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N000459"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：当地监管要求 --constrains--> 机构识别PEP的义务；KG不足：基础KG不能表达标准约束具体识别动作的内部有向关系；选项判断：可确认或排除关于识别PEP是否必须遵循当地监管要求的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S09_002",
      "section_id": "CH06-S09",
      "card_nature": "assessment",
      "title": "风险偏好指导选择更高PEP标准",
      "flow_nodes": [
        {
          "node_id": "P1",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "机构可选择执行更高的PEP标准",
          "evidence_unit_ids": [
            "v7u_N000460"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "ST1",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "机构的风险偏好",
          "evidence_unit_ids": [
            "v7u_N000460"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "REFERENCES",
          "source": "P1",
          "target": "ST1",
          "evidence_unit_ids": [
            "v7u_N000460"
          ],
          "derivation": "explicit_text",
          "condition": "基于其风险偏好",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N000460"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：风险偏好 --guides--> 机构可选择执行更高的PEP标准；KG不足：基础KG不能表达风险偏好作为条件导向标准选择的方向性；选项判断：可确认或排除关于选择更高标准是否需要依据风险偏好的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S09_003",
      "section_id": "CH06-S09",
      "card_nature": "assessment",
      "title": "部分机构在个人卸任后仍维持PEP分类",
      "flow_nodes": [
        {
          "node_id": "E6",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "个人已卸任，但可能保持影响力",
          "evidence_unit_ids": [
            "v7u_N000477"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P1",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "部分机构维持PEP分类",
          "evidence_unit_ids": [
            "v7u_N000477"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "PRECEDES",
          "source": "E6",
          "target": "P1",
          "evidence_unit_ids": [
            "v7u_N000477"
          ],
          "derivation": "explicit_text",
          "condition": "即使已卸任，仍可能保持影响力"
        }
      ],
      "source_unit_ids": [
        "v7u_N000477"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：个人卸任（仍可能保持影响力）--conditions--> 部分机构维持PEP分类；KG不足：基础KG不能表达卸任条件与分类维持之间的有向判断链；选项判断：可确认部分机构即使个人卸任仍维持PEP，排除自动去分类的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S09_004",
      "section_id": "CH06-S09",
      "card_nature": "execution",
      "title": "机构必须基于风险偏好调整监控和审查",
      "flow_nodes": [
        {
          "node_id": "P1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构必须调整交易监控、KYC审查并升级处理",
          "evidence_unit_ids": [
            "v7u_N000482"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "ST1",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "机构的风险偏好",
          "evidence_unit_ids": [
            "v7u_N000482"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "REFERENCES",
          "source": "P1",
          "target": "ST1",
          "evidence_unit_ids": [
            "v7u_N000482"
          ],
          "derivation": "explicit_text",
          "condition": "基于其风险偏好",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N000482"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：风险偏好 --constrains--> 机构必须调整监控、KYC审查并升级；KG不足：基础KG不能表达该义务的内部有向约束关系；选项判断：可确认调整监控必须基于风险偏好的义务，排除无需基于风险偏好的说法；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_005",
  "cand_006",
  "cand_007",
  "cand_008",
  "cand_009",
  "cand_010"
]
```
