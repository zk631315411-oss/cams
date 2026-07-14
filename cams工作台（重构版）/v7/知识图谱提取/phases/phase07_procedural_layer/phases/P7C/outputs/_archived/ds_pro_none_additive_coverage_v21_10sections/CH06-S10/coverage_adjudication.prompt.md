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
  "origin_candidate_ids": ["<相关首次候选ID，可为空>"],
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
        "v7u_N000488",
        "v7u_N000493"
      ],
      "proposition": "审查所有权结构时，机构必须识别客户UBO，并需参照直接和间接持股信息",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_001",
      "reason": "条件触发的识别义务与所需输入形成局部有向关系，基础KG无法表达审查情境与识别动作的关联及输入参照。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000490",
        "v7u_N000491"
      ],
      "proposition": "机构基于风险为本方法设定受益所有权阈值，高风险客户阈值可能低至10%或5%",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_002",
      "reason": "机构设定阈值的动作与高风险可能降低的标准之间存在有向约束，基础KG只能保存静态规则，无法表达动作-标准关系。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000496"
      ],
      "proposition": "无自然人最终受益所有人时，机构应识别并核实控制人或名义受益所有人",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_003",
      "reason": "例外条件触发替代识别义务，形成单一条件-动作有向链，基础KG仅能保存整条规则，无法表达条件导向关系。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000483"
      ],
      "proposition": "控制权和所有权在反洗钱工作中至关重要，它们可能被隐藏，让犯罪分子掩饰犯罪活动",
      "decision": "kg_only",
      "card_id": null,
      "reason": "背景介绍，无具体步骤、判断或应对措施，属一般性说明。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000484"
      ],
      "proposition": "受益所有人定义",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义，无程序性结构。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000485"
      ],
      "proposition": "最终受益所有人定义",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000486"
      ],
      "proposition": "BO与UBO的区别说明",
      "decision": "kg_only",
      "card_id": null,
      "reason": "概念区别解释，无动作或判断链路。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N000487"
      ],
      "proposition": "区别对监管要求重要性",
      "decision": "kg_only",
      "card_id": null,
      "reason": "强调重要性，未形成具体的有向关系。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N000489"
      ],
      "proposition": "多数司法管辖区要求25%阈值识别受益所有人",
      "decision": "kg_only",
      "card_id": null,
      "reason": "静态规则陈述，无机构主体动作或条件-动作结构。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N000492"
      ],
      "proposition": "高风险代理行可能设定5%阈值示例",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯示例，不构成独立程序性结构。"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N000494"
      ],
      "proposition": "个人D成为UBO的计算示例",
      "decision": "kg_only",
      "card_id": null,
      "reason": "计算案例，基础KG可保存。"
    },
    {
      "candidate_id": "cand_012",
      "unit_ids": [
        "v7u_N000495"
      ],
      "proposition": "个人C不是UBO的计算示例",
      "decision": "kg_only",
      "card_id": null,
      "reason": "计算案例。"
    },
    {
      "candidate_id": "cand_013",
      "unit_ids": [
        "v7u_N000497"
      ],
      "proposition": "上市公司名义BO可为总裁或CEO示例",
      "decision": "kg_only",
      "card_id": null,
      "reason": "示例说明，无独立程序性结构。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH06-S10_001",
      "section_id": "CH06-S10",
      "card_nature": "execution",
      "title": "审查所有权结构时的UBO识别义务及所需信息",
      "flow_nodes": [
        {
          "node_id": "N1",
          "node_category": "process",
          "node_type": "P8_constrained_action",
          "label": "机构在审查所有权结构时必须识别客户最终受益所有人(UBO)",
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N2",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "直接和间接持股信息",
          "evidence_unit_ids": [
            "v7u_N000493"
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
            "v7u_N000493"
          ],
          "derivation": "explicit_text",
          "relation_type": "clue_supports_identification"
        }
      ],
      "source_unit_ids": [
        "v7u_N000488",
        "v7u_N000493"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：审查所有权结构时，机构必须识别UBO，且需参照直接和间接持股信息。KG不足：基础KG不能表达审查情境与识别义务的关联，也不能表达识别动作需参照持股信息作为输入。选项判断：可确认识别UBO的触发条件及所需信息。LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S10_002",
      "section_id": "CH06-S10",
      "card_nature": "execution",
      "title": "机构基于风险为本方法设定受益所有权阈值",
      "flow_nodes": [
        {
          "node_id": "N1",
          "node_category": "process",
          "node_type": "P8_constrained_action",
          "label": "机构基于风险为本方法设定受益所有权阈值",
          "evidence_unit_ids": [
            "v7u_N000490"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N2",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "高风险客户阈值可能低至10%或5%",
          "evidence_unit_ids": [
            "v7u_N000491"
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
            "v7u_N000491"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N000490",
        "v7u_N000491"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构采用风险为本方法设定阈值，并参照高风险客户可能的更低阈值。KG不足：基础KG不能表达设定动作与风险标准之间的有向约束。选项判断：可确认机构设定阈值的义务及考虑高风险调整。LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S10_003",
      "section_id": "CH06-S10",
      "card_nature": "execution",
      "title": "无自然人最终受益所有人时的替代识别",
      "flow_nodes": [
        {
          "node_id": "N1",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "不存在自然人最终受益所有人",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "N2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构应识别并核实控制人或名义受益所有人",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "PRECEDES",
          "source": "N1",
          "target": "N2",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "derivation": "explicit_text",
          "condition": "当公司不存在自然人受益所有人时"
        }
      ],
      "source_unit_ids": [
        "v7u_N000496"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：不存在自然人UBO时，机构应识别控制人或名义BO。KG不足：基础KG不能表达该条件触发的有向关系。选项判断：可确认例外情况的识别要求。LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_004",
  "cand_005",
  "cand_006",
  "cand_007",
  "cand_008",
  "cand_009",
  "cand_010",
  "cand_011",
  "cand_012",
  "cand_013"
]
```
