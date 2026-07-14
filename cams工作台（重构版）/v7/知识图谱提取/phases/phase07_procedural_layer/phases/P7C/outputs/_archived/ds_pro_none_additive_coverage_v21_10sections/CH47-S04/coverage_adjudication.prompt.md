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

section_id: `CH47-S04`

section_title: `Transaction monitoring > Transaction monitoring system tuning`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "交易监控系统调优：定义与重要性",
      "title_en": "TM System Tuning: Definition and Importance",
      "covered_units": [
        {
          "unit_id": "v7u_N003272",
          "unit_type": "classification",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N003273",
          "unit_type": "risk_indicator",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003274",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003275",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003276",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003277",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "调优的关键组成部分",
      "title_en": "Key Components of Tuning",
      "covered_units": [
        {
          "unit_id": "v7u_N003278",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N003280",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N003284",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N003279",
          "unit_type": "definition",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003282",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003281",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N003283",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003285",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "动态调优要求",
      "title_en": "Dynamic Tuning Requirement",
      "covered_units": [
        {
          "unit_id": "v7u_N003286",
          "unit_type": "rule",
          "kg_role": "states_rule"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "交易监控系统调优：定义与重要性",
      "target_title": "调优的关键组成部分",
      "relation_type": "prepares"
    },
    {
      "source_title": "调优的关键组成部分",
      "target_title": "动态调优要求",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N003272|3272] TM system tuning is the process of refining and adjusting parameters and thresholds of specific detection logic rules, or scenarios. Scenarios are designed to detect suspicious activities and abnormal transaction behaviors, such as money laundering, fraud, or other illicit activities. Tuning is important because it:
ZH: 交易监控系统调优是调整检测规则参数和阈值的过程。

[v7u_N003273|3273] Ensures the TM system effectively detects suspicious activity.
ZH: 调优确保交易监控系统有效检测可疑活动。

[v7u_N003274|3274] Reduces false positives.
ZH: 调优减少误报。

[v7u_N003275|3275] Ensures efficient resource use.
ZH: 调优确保资源高效利用。

[v7u_N003276|3276] Allows organizations to manage changes in financial crime and in their business operations.
ZH: 调优使组织能够应对金融犯罪和业务运营的变化。

[v7u_N003277|3277] Ensures regulatory compliance.
ZH: 调优确保监管合规。

[v7u_N003278|3278] Tuning involves four key components: scenario setting, customer segmentation, threshold setting, and frequency.
ZH: 调优包括场景设置、客户细分、阈值设置和频率四个关键组成部分。

[v7u_N003279|3279] Scenario setting involves creating, modifying, or removing detection rules and scenarios based on previous experiences with suspicious activity and actual incidents.
ZH: 场景设置是基于以往经验创建、修改或移除检测规则和场景。

[v7u_N003280|3280] Threshold setting defines the minimum level of activity required for a transaction to trigger an alert.
ZH: 阈值设置定义了触发警报所需的最低活动水平。

[v7u_N003281|3281] For example, the threshold for reporting a CTR might be any currency transaction that exceeds US$10,000.
ZH: 货币交易报告（CTR）阈值示例：超过10,000美元的任何货币交易

[v7u_N003282|3282] Adjusting thresholds refines sensitivity and accuracy.
ZH: 调整阈值可提高交易监控系统的灵敏度和准确性

[v7u_N003283|3283] Reducing the number of false positives is a key goal in setting thresholds to make the most efficient use of resources.
ZH: 减少误报是设定阈值的关键目标，以高效利用资源

[v7u_N003284|3284] The frequency determines how often tuning should occur.
ZH: 调优频率决定了交易监控系统应多久进行一次调整

[v7u_N003285|3285] The frequency might also be influenced by changes in business strategy, anomalies, regulatory updates, or market changes.
ZH: 调优频率受业务策略变化、异常、监管更新或市场变化影响

[v7u_N003286|3286] Tuning should be dynamic, with special assessments triggered by significant events or trends.
ZH: 调优应是动态的，重大事件或趋势应触发专项评估
```

allowed_unit_ids:

```json
[
  "v7u_N003272",
  "v7u_N003273",
  "v7u_N003274",
  "v7u_N003275",
  "v7u_N003276",
  "v7u_N003277",
  "v7u_N003278",
  "v7u_N003279",
  "v7u_N003280",
  "v7u_N003281",
  "v7u_N003282",
  "v7u_N003283",
  "v7u_N003284",
  "v7u_N003285",
  "v7u_N003286"
]
```

original_json:

```json
{
  "section_id": "CH47-S04",
  "section_title": "Transaction monitoring > Transaction monitoring system tuning",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N003272"
      ],
      "proposition": "交易监控系统调优是调整检测规则参数和阈值的过程（定义）",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义，基础KG已能充分表达。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N003273"
      ],
      "proposition": "调优确保有效检测可疑活动（效果）",
      "decision": "kg_only",
      "card_id": null,
      "reason": "解释调优的效果/目的，无增量程序性或判断性有向结构，基础KG可保存。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N003274"
      ],
      "proposition": "调优减少误报（效果）",
      "decision": "kg_only",
      "card_id": null,
      "reason": "效果陈述，无增量结构，基础KG充足。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N003275"
      ],
      "proposition": "调优确保高效资源利用（效果）",
      "decision": "kg_only",
      "card_id": null,
      "reason": "效果陈述，基础KG可表达。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N003276"
      ],
      "proposition": "调优使组织管理金融犯罪和业务变化（功能）",
      "decision": "kg_only",
      "card_id": null,
      "reason": "功能说明，无特定的条件-动作链，基础KG覆盖。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N003277"
      ],
      "proposition": "调优确保监管合规（效果）",
      "decision": "kg_only",
      "card_id": null,
      "reason": "效果陈述，基础KG可表达。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N003278"
      ],
      "proposition": "调优包含四个关键组成部分（列表）",
      "decision": "kg_only",
      "card_id": null,
      "reason": "组成列表，基础KG能充分表达分类关系。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N003279"
      ],
      "proposition": "场景设置是基于经验创建、修改或移除检测规则（定义/解释）",
      "decision": "kg_only",
      "card_id": null,
      "reason": "定义性解释，不包含条件化触发或特定有向判断，基础KG可保存。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N003280"
      ],
      "proposition": "阈值设置定义触发警报的最低活动水平（定义）",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义，基础KG覆盖。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N003281"
      ],
      "proposition": "CTR报告阈值示例：超过10000美元的货币交易（示例）",
      "decision": "kg_only",
      "card_id": null,
      "reason": "普通示例/事实，基础KG可表达。"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N003282"
      ],
      "proposition": "调整阈值可提高灵敏度和准确性（效果）",
      "decision": "kg_only",
      "card_id": null,
      "reason": "效果说明，基础KG充足。"
    },
    {
      "candidate_id": "cand_012",
      "unit_ids": [
        "v7u_N003283"
      ],
      "proposition": "减少误报是设定阈值的关键目标（目标）",
      "decision": "kg_only",
      "card_id": null,
      "reason": "目标陈述，无增量有向结构，基础KG可保存。"
    },
    {
      "candidate_id": "cand_013",
      "unit_ids": [
        "v7u_N003284"
      ],
      "proposition": "频率决定调优应多久进行一次（定义）",
      "decision": "kg_only",
      "card_id": null,
      "reason": "定义，基础KG覆盖。"
    },
    {
      "candidate_id": "cand_014",
      "unit_ids": [
        "v7u_N003285"
      ],
      "proposition": "频率可能受业务策略变化、异常、监管更新或市场变化影响（影响因素）",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般因果关系，无明确触发特定主体的应对动作，基础KG可表达。"
    },
    {
      "candidate_id": "cand_015",
      "unit_ids": [
        "v7u_N003286"
      ],
      "proposition": "当发生重大事件或趋势时，应触发专项评估（条件触发动作）",
      "decision": "p7c_card",
      "card_id": "p7card_CH47-S04_001",
      "reason": "规则内部包含‘重大事件/趋势 → 实施专项评估’的局部有向判断链，超出基础KG仅将其作为整体规则保存的表达能力，可帮助判断选项中的触发条件和评估动作。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH47-S04_001",
      "section_id": "CH47-S04",
      "card_nature": "assessment",
      "title": "重大事件触发专项调优评估",
      "flow_nodes": [
        {
          "node_id": "E1_CH47S04_001",
          "node_category": "entry",
          "node_type": "E1_event_signal",
          "label": "发生重大事件或趋势",
          "evidence_unit_ids": [
            "v7u_N003286"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P1_CH47S04_001",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "机构：实施专项调优评估",
          "evidence_unit_ids": [
            "v7u_N003286"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1_PRECEDES_P1",
          "edge_type": "PRECEDES",
          "source": "E1_CH47S04_001",
          "target": "P1_CH47S04_001",
          "evidence_unit_ids": [
            "v7u_N003286"
          ],
          "derivation": "explicit_text",
          "condition": "triggered by significant events or trends",
          "source_quote": "with special assessments triggered by significant events or trends"
        }
      ],
      "source_unit_ids": [
        "v7u_N003286"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：当发生重大事件或趋势时 → 机构实施专项调优评估；KG不足：基础KG仅将‘调优应是动态的，由重大事件触发专项评估’保存为规则文本，不能表达事件触发评估的局部有向关系；选项判断：可确认或排除‘专项评估在何种条件下被触发’、‘调优的动态性体现在触发评估’等选项；LLM推理：无。"
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
  "cand_008",
  "cand_009",
  "cand_010",
  "cand_011",
  "cand_012",
  "cand_013",
  "cand_014"
]
```
