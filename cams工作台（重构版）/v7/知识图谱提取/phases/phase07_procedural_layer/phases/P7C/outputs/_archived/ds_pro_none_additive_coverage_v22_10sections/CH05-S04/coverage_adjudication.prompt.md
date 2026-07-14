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

只放新增完整card。每张必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。`candidate_status`固定为`candidate`。card ID不得与已有card重复。每张新card必须被某条提升裁决或`new_candidates`引用。

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

section_id: `CH05-S04`

section_title: `Financial crime risks in relation to other types of risks > Operational, legal, concentration, and reputational risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "主要风险类型：运营、法律、集中度、声誉",
      "title_en": "Key risk types: operational, legal, concentration, reputational",
      "covered_units": [
        {
          "unit_id": "v7u_N000369",
          "unit_type": "classification",
          "kg_role": "classifies"
        }
      ]
    },
    {
      "title_zh": "运营风险：定义与监管挑战",
      "title_en": "Operational risk: definition and regulatory challenges",
      "covered_units": [
        {
          "unit_id": "v7u_N000370",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000375",
          "unit_type": "definition",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000376",
          "unit_type": "process",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000377",
          "unit_type": "risk_indicator",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000378",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        }
      ]
    },
    {
      "title_zh": "法律风险：来源、后果及AFC保护",
      "title_en": "Legal risk: sources, consequences, and AFC protection",
      "covered_units": [
        {
          "unit_id": "v7u_N000371",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000379",
          "unit_type": "definition",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000381",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000380",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        }
      ]
    },
    {
      "title_zh": "集中度风险：过度敞口、缓解与管理",
      "title_en": "Concentration risk: over-exposure, mitigation, and management",
      "covered_units": [
        {
          "unit_id": "v7u_N000372",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000382",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000384",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000385",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000383",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        }
      ]
    },
    {
      "title_zh": "声誉风险：特征与信任因素",
      "title_en": "Reputational risk: characteristics and trust factor",
      "covered_units": [
        {
          "unit_id": "v7u_N000373",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000386",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000387",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000388",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "主要风险类型：运营、法律、集中度、声誉",
      "target_title": "运营风险：定义与监管挑战",
      "relation_type": "contains"
    },
    {
      "source_title": "主要风险类型：运营、法律、集中度、声誉",
      "target_title": "法律风险：来源、后果及AFC保护",
      "relation_type": "contains"
    },
    {
      "source_title": "主要风险类型：运营、法律、集中度、声誉",
      "target_title": "集中度风险：过度敞口、缓解与管理",
      "relation_type": "contains"
    },
    {
      "source_title": "主要风险类型：运营、法律、集中度、声誉",
      "target_title": "声誉风险：特征与信任因素",
      "relation_type": "contains"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000369|369] Key risks that organizations face include: Operational, legal, concentration, and reputational.
ZH: 组织面临的主要风险类型包括：运营风险、法律风险、集中度风险和声誉风险。

[v7u_N000370|370] Operational risk is direct or indirect loss of operations due to inadequate or failed internal processes, people, or systems, or as a result of external events.
ZH: 运营风险是因内部流程、人员、系统不完善或外部事件导致直接或间接损失的风险。

[v7u_N000371|371] Legal risk is the possibility that criminal penalties, lawsuits, or contracts that cannot be enforced might harm an organization.
ZH: 法律风险是指刑事处罚、诉讼或不可执行合同可能损害组织的可能性。

[v7u_N000372|372] Concentration risk stems from over-exposure to a single customer or group of related customers.
ZH: 集中度风险源于对单一客户或关联客户群体的过度敞口。

[v7u_N000373|373] Reputational risk comes when an institution known to have weak controls is then targeted by criminals or avoided by stakeholders who lose confidence in the institution.
ZH: 声誉风险是指机构因控制薄弱而被犯罪分子利用或利益相关者失去信心而回避的风险。

[v7u_N000374|374] Although these risks are usually managed by non-AFC risk management teams, understanding the correlation with financial crime risk is indispensable.
ZH: 尽管这些风险通常由非金融犯罪防控团队管理，但理解其与金融犯罪风险的关联至关重要。

[v7u_N000375|375] Operational risk is complex and includes an organization’s ability to maintain AFC controls in an evolving regulatory environment across multiple jurisdictions.
ZH: 运营风险复杂，包括组织在多个司法管辖区不断变化的监管环境中维持金融犯罪防控控制的能力。

[v7u_N000376|376] Typically, a global organization makes the policies of its home regulator its base standard. The organization will then adjust to each host country’s laws.
ZH: 全球组织通常以母国监管机构政策为基础标准，再根据东道国法律进行调整。

[v7u_N000377|377] Evolving regulations might become misaligned with current business models and controls.
ZH: 不断演变的法规可能与现有业务模式和控制措施产生错位。

[v7u_N000378|378] Compliance programs must continually be updated.
ZH: 合规计划必须持续更新。

[v7u_N000379|379] Legal risk stems from potential violation of regulations, laws, and ethical practices.
ZH: 法律风险源于可能违反法规、法律和道德实践。

[v7u_N000380|380] Governments might issue administrative penalties or fines. Third parties, such as customers who feel damaged, might file lawsuits.
ZH: 政府可能处以行政处罚或罚款，受损客户等第三方可能提起诉讼。

[v7u_N000381|381] Adequate AFC controls add protection from crime and inappropriate relationships.
ZH: 充分的金融犯罪防控措施可防范犯罪及不当关系

[v7u_N000382|382] Concentration risk can be reduced by AFC controls and strategic diversification.
ZH: 金融犯罪防控与战略多元化可降低集中度风险

[v7u_N000383|383] Customer due diligence, enabled by technology, helps manage exposure.
ZH: 借助技术的客户尽职调查有助于管理风险敞口

[v7u_N000384|384] Concentration could occur in borrowing, funding, purchasing, provision of key services, or any other business relationship.
ZH: 集中度可能出现在借贷、融资、采购、关键服务提供等业务关系中

[v7u_N000385|385] Risk could increase through actions by a customer, or external actions involving a customer.
ZH: 风险可能因客户行为或涉及客户的外部行为而增加

[v7u_N000386|386] Reputational risk is difficult to quantify.
ZH: 声誉风险难以量化

[v7u_N000387|387] Trust takes a long time to earn but can be lost quickly. A single news story—even fake news—can drive away customers and investors.
ZH: 信任建立缓慢但易丧失，一条新闻即可驱离客户与投资者

[v7u_N000388|388] Many organizations deserve their reputations, good or bad, based on their chosen business practices and ethics.
ZH: 组织的声誉源于其商业实践与道德选择
```

allowed_unit_ids:

```json
[
  "v7u_N000369",
  "v7u_N000370",
  "v7u_N000371",
  "v7u_N000372",
  "v7u_N000373",
  "v7u_N000374",
  "v7u_N000375",
  "v7u_N000376",
  "v7u_N000377",
  "v7u_N000378",
  "v7u_N000379",
  "v7u_N000380",
  "v7u_N000381",
  "v7u_N000382",
  "v7u_N000383",
  "v7u_N000384",
  "v7u_N000385",
  "v7u_N000386",
  "v7u_N000387",
  "v7u_N000388"
]
```

original_json:

```json
{
  "section_id": "CH05-S04",
  "section_title": "Financial crime risks in relation to other types of risks > Operational, legal, concentration, and reputational risks",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N000369"
      ],
      "proposition": "组织面临的主要风险类型包括运营、法律、集中度和声誉风险。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯分类列表，基础KG已涵盖。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000370"
      ],
      "proposition": "运营风险是因内部流程、人员、系统不完善或外部事件导致直接或间接损失的风险。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义，基础KG已涵盖。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000371"
      ],
      "proposition": "法律风险是刑事处罚、诉讼或不可执行合同可能损害组织的可能性。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义，基础KG已涵盖。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000372"
      ],
      "proposition": "集中度风险源于对单一客户或关联客户群体的过度敞口。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义，基础KG已涵盖。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000373"
      ],
      "proposition": "声誉风险是机构因控制薄弱被犯罪分子利用或利益相关者丧失信心而回避的风险。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义，基础KG已涵盖。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000374"
      ],
      "proposition": "理解这些风险与金融犯罪风险的关联至关重要，尽管通常由非AFC团队管理。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性关联陈述，无具体程序性结构。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000375"
      ],
      "proposition": "运营风险包括机构在不断变化的监管环境中维持AFC控制的能力。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "定义性扩展说明，无具体有向关系。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N000376"
      ],
      "proposition": "全球组织通常以母国监管政策为基础标准，并根据各东道国法律调整政策。",
      "decision": "p7c_card",
      "card_id": "p7card_CH05-S04_001",
      "reason": "包含明确的顺序和参照关系，构成增量程序性链。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N000377"
      ],
      "proposition": "不断演变的法规可能与现有业务模式和控制产生错位。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立风险指标，无对应主体动作或判断。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N000378"
      ],
      "proposition": "合规计划必须持续更新。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立义务陈述，无具体条件或程序性上下文。"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N000379"
      ],
      "proposition": "法律风险源于可能违反法规、法律和道德实践。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "来源说明，基础KG已作为定义部分。"
    },
    {
      "candidate_id": "cand_012",
      "unit_ids": [
        "v7u_N000380"
      ],
      "proposition": "政府可能处以行政处罚或罚款，受损客户可能提起诉讼。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立后果事实，无应对或有向结构。"
    },
    {
      "candidate_id": "cand_013",
      "unit_ids": [
        "v7u_N000381"
      ],
      "proposition": "充分的AFC控制可防范犯罪和不当关系。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "控制与效果的一般知识关系，基础KG可表达。"
    },
    {
      "candidate_id": "cand_014",
      "unit_ids": [
        "v7u_N000382"
      ],
      "proposition": "金融犯罪防控与战略多元化可降低集中度风险。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "控制与效果的一般知识关系，基础KG可表达。"
    },
    {
      "candidate_id": "cand_015",
      "unit_ids": [
        "v7u_N000383"
      ],
      "proposition": "借助技术的客户尽职调查有助于管理风险敞口。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性控制描述，无特定条件或决策链。"
    },
    {
      "candidate_id": "cand_016",
      "unit_ids": [
        "v7u_N000384"
      ],
      "proposition": "集中度可能出现在借贷、融资、采购等多种业务关系中。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立领域列举，基础KG可保存。"
    },
    {
      "candidate_id": "cand_017",
      "unit_ids": [
        "v7u_N000385"
      ],
      "proposition": "风险可能因客户行为或涉及客户的外部行为而增加。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立风险要素，无对应判断或应对。"
    },
    {
      "candidate_id": "cand_018",
      "unit_ids": [
        "v7u_N000386"
      ],
      "proposition": "声誉风险难以量化。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立特征事实。"
    },
    {
      "candidate_id": "cand_019",
      "unit_ids": [
        "v7u_N000387"
      ],
      "proposition": "信任建立缓慢但易丧失，新闻可驱离客户与投资者。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立特征事实，无程序性链接。"
    },
    {
      "candidate_id": "cand_020",
      "unit_ids": [
        "v7u_N000388"
      ],
      "proposition": "组织声誉源于其商业实践与道德选择。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立归因说明。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH05-S04_001",
      "section_id": "CH05-S04",
      "card_nature": "execution",
      "title": "全球组织基于母国和东道国监管要求调整合规政策",
      "flow_nodes": [
        {
          "node_id": "n001",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "母国监管政策（作为基础标准）",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n002",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "东道国法律",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n003",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "全球组织：通常将母国监管政策作为基础标准",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n004",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "全球组织：然后根据各东道国法律调整政策",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e001",
          "edge_type": "REFERENCES",
          "source": "n003",
          "target": "n001",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e002",
          "edge_type": "REFERENCES",
          "source": "n004",
          "target": "n002",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e003",
          "edge_type": "PRECEDES",
          "source": "n003",
          "target": "n004",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "derivation": "explicit_text",
          "source_quote": "Typically, a global organization makes the policies of its home regulator its base standard. The organization will then adjust to each host country’s laws."
        }
      ],
      "source_unit_ids": [
        "v7u_N000376"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：全球组织通常先以母国监管政策为基础标准，再根据东道国法律调整政策；KG不足：基础KG如仅保存事实不能表达该顺序和参照约束；选项判断：可用于确认或排除关于合规政策建立步骤的选项；LLM推理：无。"
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
  "cand_007",
  "cand_009",
  "cand_010",
  "cand_011",
  "cand_012",
  "cand_013",
  "cand_014",
  "cand_015",
  "cand_016",
  "cand_017",
  "cand_018",
  "cand_019",
  "cand_020"
]
```
