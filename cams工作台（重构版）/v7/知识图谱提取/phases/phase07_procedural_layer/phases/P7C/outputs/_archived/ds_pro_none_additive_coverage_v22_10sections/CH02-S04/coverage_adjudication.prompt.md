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

section_id: `CH02-S04`

section_title: `Types of financial crime > Case example: FullTechGlobal corruption scandal`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "FullTechGlobal 案中的英国反贿赂法域外效力与合规教训",
      "title_en": "UK Bribery Act Extraterritoriality and Compliance Lessons from FullTechGlobal Case",
      "covered_units": [
        {
          "unit_id": "v7u_N000135",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000136",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000137",
          "unit_type": "rule",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000141",
          "unit_type": "case",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000143",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000144",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000131",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000132",
          "unit_type": "case",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000133",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000134",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000138",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000139",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000140",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000142",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    }
  ],
  "covered_relations": []
}
```

section_text_with_unit_anchors:

```text
[v7u_N000131|131] Sophie is an AFC manager in the compliance department of a financial institution that has some global businesses as its customers.
ZH: Sophie 是金融机构合规部的金融犯罪防控经理。

[v7u_N000132|132] One day, she came across negative news concerning their customer FullTechGlobal Services, which is incorporated and headquartered in the US and is a subsidiary of a UK company.
ZH: Sophie 发现客户 FullTechGlobal Services 的负面新闻。

[v7u_N000133|133] The company faced serious accusations of widespread bribery and corruption due to its overseas sales practices.
ZH: 该公司因海外销售行为面临广泛贿赂和腐败的严重指控。

[v7u_N000134|134] This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010.
ZH: 此事引发对《英国反贿赂法》域外条款的关切。

[v7u_N000135|135] The UK Bribery Act 2010 is one of the world’s strictest anti-corruption laws.
ZH: 《英国反贿赂法》是全球最严格的反腐败法律之一。

[v7u_N000136|136] It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location.
ZH: 该法适用于任何与英国有关联的公司，母公司需对子公司腐败行为负责。

[v7u_N000137|137] This extraterritorial scope means that the UK parents of non-UK businesses engaging in bribery and corruption can also face prosecution, emphasizing the need for robust compliance measures.
ZH: 域外管辖意味着非英国企业的英国母公司也可能因贿赂腐败被起诉。

[v7u_N000138|138] Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts.
ZH: FullTechGlobal 在高风险司法管辖区战略性地雇佣中间人获取合同。

[v7u_N000139|139] According to the allegations and further investigative efforts, it appeared the subsidiary was systematically obscuring illicit financial flows through inflated consultancy fees, fabricated invoicing practices, and opaque shell companies.
ZH: 子公司通过虚增咨询费、伪造发票和壳公司掩盖非法资金流动。

[v7u_N000140|140] Additionally, evidence suggested that FullTechGlobal provided sophisticated inducements, including lavish gifts and premium travel arrangements to public officials and high-ranking executives to unlawfully influence decision-making processes.
ZH: FullTechGlobal 向公职人员和高级管理人员提供奢华礼品和旅行安排以影响决策。

[v7u_N000141|141] She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities.
ZH: FullTechGlobal腐败案审计发现内部控制缺陷和监管不足

[v7u_N000142|142] Bribery was identified as the predicate crime, leading to the laundering of illicit funds through complex financial networks designed to evade regulatory scrutiny and forensic tracing efforts.
ZH: 贿赂作为上游犯罪，通过复杂金融网络洗钱

[v7u_N000143|143] Given these findings, the regulatory implications under the UK Bribery Act 2010 are profound. FullTechGlobal Services faces severe financial penalties, increased scrutiny from international regulators, and potential criminal liability for both the subsidiary and the parent company, including its executives.
ZH: FullTechGlobal面临英国《反贿赂法》下的严厉处罚和监管审查

[v7u_N000144|144] As an AFC manager, she recognizes that her institution needs to maintain compliance integrity and mitigate bribery and corruption risks in its dealings with global businesses such as FullTechGlobal Services.
ZH: 金融犯罪防控经理有义务维护合规诚信并降低贿赂风险
```

allowed_unit_ids:

```json
[
  "v7u_N000131",
  "v7u_N000132",
  "v7u_N000133",
  "v7u_N000134",
  "v7u_N000135",
  "v7u_N000136",
  "v7u_N000137",
  "v7u_N000138",
  "v7u_N000139",
  "v7u_N000140",
  "v7u_N000141",
  "v7u_N000142",
  "v7u_N000143",
  "v7u_N000144"
]
```

original_json:

```json
{
  "section_id": "CH02-S04",
  "section_title": "Types of financial crime > Case example: FullTechGlobal corruption scandal",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N000132",
        "v7u_N000138",
        "v7u_N000139",
        "v7u_N000140"
      ],
      "proposition": "Sophie发现FullTechGlobal负面新闻后，进行了初步调查，发现了贿赂手段（使用中间人、虚增费用、提供奢华礼品和旅行）",
      "decision": "p7c_card",
      "card_id": "p7card_CH02-S04_001",
      "reason": "这是一条具体的触发-应对-发现链，超出基础KG的风险指标保存，构成局部程序性结构，有助于判断调查响应和发现。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000141",
        "v7u_N000142"
      ],
      "proposition": "Sophie进行跟进审查，发现ABC框架失败、内部控制缺陷和监督不足，并识别出贿赂为上游犯罪导致洗钱",
      "decision": "p7c_card",
      "card_id": "p7card_CH02-S04_002",
      "reason": "审查过程产生具体分类结论，形成process-to-exit的有向链，KG不能表达审查动作与具体发现间的直接产生关系，可帮助判断审计结论。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000143",
        "v7u_N000144"
      ],
      "proposition": "鉴于审查发现，Sophie认识到其机构需要维护合规诚信并降低贿赂风险",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅表达认知责任，没有具体行动或独立程序性结果，基础KG可保存这种一般防范意识。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000134"
      ],
      "proposition": "FullTechGlobal的负面新闻引发对英国反贿赂法域外条款的关切",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅表达关切，无后续具体动作或判断，基础KG可将其作为风险关联保存。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000136",
        "v7u_N000137"
      ],
      "proposition": "英国反贿赂法2010的域外管辖规则：对关联公司适用，母公司承担子公司责任，可能被起诉",
      "decision": "kg_only",
      "card_id": null,
      "reason": "法律规则本身可由基础KG完整表达，无增量程序性结构。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000135"
      ],
      "proposition": "英国反贿赂法2010是世界上最严格的反腐败法律之一",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义性描述，基础KG可覆盖。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000133"
      ],
      "proposition": "FullTechGlobal面临的贿赂和腐败指控",
      "decision": "kg_only",
      "card_id": null,
      "reason": "属于负面新闻的具体内容，已经在P7C card中作为发现引用，本身不形成独立有向链。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N000131"
      ],
      "proposition": "Sophie是金融机构的AFC经理",
      "decision": "kg_only",
      "card_id": null,
      "reason": "角色背景介绍，无程序性结构。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH02-S04_001",
      "section_id": "CH02-S04",
      "card_nature": "execution",
      "title": "Sophie的初步调查基于负面新闻发现贿赂手段",
      "flow_nodes": [
        {
          "node_id": "E1",
          "node_category": "entry",
          "node_type": "E2_object_entry",
          "label": "FullTechGlobal负面新闻报告",
          "evidence_unit_ids": [
            "v7u_N000132"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "Sophie发起初步调查",
          "evidence_unit_ids": [
            "v7u_N000138"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X1",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "发现贿赂手段：使用中间人、虚增咨询费、伪造发票、提供奢华礼品和旅行",
          "evidence_unit_ids": [
            "v7u_N000138",
            "v7u_N000139",
            "v7u_N000140"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1->P1",
          "edge_type": "PRECEDES",
          "source": "E1",
          "target": "P1",
          "evidence_unit_ids": [
            "v7u_N000132",
            "v7u_N000138"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "P1->X1",
          "edge_type": "PRODUCES",
          "source": "P1",
          "target": "X1",
          "evidence_unit_ids": [
            "v7u_N000138",
            "v7u_N000139",
            "v7u_N000140"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N000132",
        "v7u_N000138",
        "v7u_N000139",
        "v7u_N000140"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：负面新闻 → 初步调查 → 发现贿赂手段；KG不足：基础KG可保存负面新闻作为风险指标，但不能表达该具体应对动作和调查后的发现链；选项判断：可帮助确认或排除关于调查响应步骤和初步结果的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH02-S04_002",
      "section_id": "CH02-S04",
      "card_nature": "assessment",
      "title": "Sophie的跟进审查发现内部控制缺陷和识别上游犯罪",
      "flow_nodes": [
        {
          "node_id": "P1",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "Sophie进行跟进审查和审计",
          "evidence_unit_ids": [
            "v7u_N000141"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X1",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "发现FullTechGlobal的ABC框架失败、内部控制和监督不足",
          "evidence_unit_ids": [
            "v7u_N000141"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X2",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "识别贿赂为上游犯罪，导致通过复杂金融网络洗钱",
          "evidence_unit_ids": [
            "v7u_N000142"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "P1->X1",
          "edge_type": "PRODUCES",
          "source": "P1",
          "target": "X1",
          "evidence_unit_ids": [
            "v7u_N000141"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "P1->X2",
          "edge_type": "PRODUCES",
          "source": "P1",
          "target": "X2",
          "evidence_unit_ids": [
            "v7u_N000142"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N000141",
        "v7u_N000142"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：审查 → 发现控制缺陷；审查 → 识别上游犯罪和洗钱；KG不足：基础KG可保存'内部控制缺陷'和'上游犯罪'作为事实，但无法表达审查动作与具体发现间的产生关系；选项判断：可帮助确认审计结论的具体内容；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_003",
  "cand_004",
  "cand_005",
  "cand_006",
  "cand_007",
  "cand_008"
]
```
