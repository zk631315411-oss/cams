# P7C Section-Local Coverage Adjudication Prompt v2

## 角色

你是P7C覆盖裁决器。首次抽取器已经发现候选命题并生成候选card；这些card尚未经过P7D正式结构校验和边级审核。你的唯一任务是复核`coverage_audit`中原决定为`kg_only`的候选，判断它们是否因KG/P7C边界理解错误而漏成卡。

只输出严格JSON补丁，不输出Markdown或解释。`original_json`提供本次无记忆API调用所需的完整首次抽取上下文；不得回显或改写它。Runner会把补丁确定性合并到P7C正本。

## P7C目的

P7C在不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标和一般知识关系的前提下，从单个section中增量提取对CAMS题目选项判断有用的局部程序性或判断性有向结构：业务情境、事件、线索、输入或标准如何关联到特定主体带原文情态的识别、评估、决策或应对，以及原文明示的独立结论、记录、状态变化、控制效果、分支或后续行动。没有独立结果时允许开放关系。

P7C不读取题目或参考答案，不处理跨section桥接。当前section原文是唯一事实证据；基础KG摘要只能用于去重，不能补造事实。

## 裁决对象

只复核`original_json.coverage_audit`中`decision=kg_only`的候选。不得新增候选，不得删除候选，不得修改候选的`candidate_id`、`unit_ids`或`proposition`。

原本为`p7c_card`的候选及`original_json.cards`只用于理解已有结果、避免重复和避开已占用ID。输出中不得包含、删除、改写、拆分、合并或重新编号这些既有内容。

## 裁决标准

将原`kg_only`候选提升为`p7c_card`，必须同时满足：

1. 当前section证据支持关系两端、特定主体、方向以及条件（如有）。
2. 候选内部存在“情境/事件/线索/输入/标准如何关联到主体动作或判断”的局部结构；只有原文明示独立结果时才增加结果节点。
3. 该方向结构能够帮助判断选项的顺序、条件、主体职责、义务、应对、因果或适用范围。
4. 基础KG只能保存整句话或各知识点，不能充分表达句内的主体、方向、条件、动作约束或独立结果关系。

结构复杂度和是否闭环不是门槛。一个unit、一条路径、没有分支或反馈，或没有独立出口，都不能作为`kg_only`理由。只有对象实际到达、提交、移交或进入某阶段并触发动作时才建entry；静态适用对象、线索输入、分析材料、风险阈值、监管要求、政策基准或风险偏好应作为auxiliary standard/input并由process通过`REFERENCES`指向。

不得用“纯义务陈述”“没有复杂条件”“没有复杂步骤”拒绝提升。只要候选已经明确给出监管要求、风险偏好或状态变化如何约束特定主体的识别、标准选择或分类维持，即使没有独立出口，也满足局部有向结构要求。

以下通常应提升：

- 金融机构的识别动作明确参照监控系统标记的异常活动；只有原文另行给出识别结论时才增加出口。
- FIU综合SAR和跨境活动并形成红旗发现。
- 风险阈值和直接/间接持股被机构用于UBO判断并形成分类结论。
- 外部监管要求或上位标准约束机构调整控制、政策或职责；除非原文明示命令到达后触发动作，否则使用`REFERENCES`而不是`PRECEDES`。
- 明确条件触发拒绝、批准、升级、报告、监控或复核。
- 当地监管要求约束机构如何识别PEP；不得因规则只有一个unit或没有义务出口而拒绝。
- 机构基于风险偏好可以选择更高标准；必须保留可选性，即使没有独立配置出口也可以作为开放式局部关系。
- 卸任等状态变化后，特定机构仍明确维持既有分类；必须保留“部分机构”“可能”等限定。

以下保持`kg_only`：

- 纯定义、分类、阈值数值或组成列表，没有主体应用或其他有向关系。
- 普通犯罪方法、犯罪分子操作步骤或普通案例机制，没有机构、FIU、监管或执法主体的识别、判断或应对。
- 孤立红旗、后果、历史事实或抽象风险缓解目的。
- 只有主题相关性，或者必须补造主体、条件、方向、动作或结果才能闭合。

## 修改规则

对`review_target_candidate_ids`中的每个原`kg_only`候选，在顶层`coverage_adjudication`中输出一条记录：

```json
{
  "candidate_id": "cand_001",
  "original_decision": "kg_only",
  "final_decision": "kg_only",
  "card_id": null,
  "reason": "<中文裁决理由>"
}
```

`final_decision`只能为`kg_only`或`p7c_card`。

保持`kg_only`时：`card_id`必须为`null`。

提升为`p7c_card`时：

- 在裁决记录中填写新card的`card_id`；
- `reason`说明基础KG不能表达的方向结构；
- 在顶层`promoted_cards`中输出且只输出对应的新card；
- 新card ID不得与`original_json.cards`中的既有ID重复；
- 每个提升候选恰好对应一张新card，不得输出未被裁决提升的card。

## 新增card规则

新增card必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。`candidate_status`固定为`candidate`，不是最终审核状态。

`card_nature`只能为：`execution, assessment, risk_indicator, control`。

新增card可以是完整闭环，也可以是开放式局部关系；不得为了满足entry→process→exit而补造出口。

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。节点必须由原文明示，`evidence_strength`只能为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

`X7_continuing_obligation`只用于原文明示上游动作、决定或协议新建立了独立持续义务；规范性语句中的“主体必须/应当执行某动作”应保留在process中，不得复制为X7出口。

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard。
- `PRODUCES`只能由process指向exit。
- `DECIDES`只能由`P3_branch_routing`发出，至少两条分支，每条都有原文明示的`condition`。
- `derivation=llm_inference`只说明边依赖必要功能推理，不改变`candidate_status`，也不表示P7D已经接受或拒绝。

`REFERENCES.condition`可以限定某项input/standard适用于process的情境，但不表示条件分支。单一条件直接触发动作时使用带`condition`的`PRECEDES`；只有至少两条原文明示路径时才使用`DECIDES`。

静态适用对象、审查材料或判断输入不得仅因语法顺序建成`entry --PRECEDES--> process`；应建为auxiliary input并由process通过`REFERENCES`指向。不得把同一谓词的主动式和被动式拆成process与exit，也不得把“动作需要理由、批准或遵循要求”写成“动作`PRODUCES`要求/义务”。

单一路径的`if/when/unless A，则B`使用条件entry到process的`PRECEDES`，并在edge的`condition`中保留原文条件；它表达逻辑前提，不要求钟表式先后。输出每条`PRODUCES`前必须反问：source和target合并后是否仍损失一个独立事实；若不损失，删除同义target和该边。理由、批准、标准或义务约束动作时使用process指向standard/input的`REFERENCES`。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写，不得创造新类型。

必须保留`must, should, may, might, could, often, potentially, help`等情态强度。不得将“有助于缓解”强化为“风险已经消除”。`must/shall/is required to`只证明义务存在，不证明动作已经完成；除非原文明示完成或结果已经发生，不得输出“已调整”“已建立”“已降低”等完成状态。

`must`本身不证明义务是持续、定期、永久或反复的，不得无证据增加这些限定。`escalate/escalation`默认写成“升级处理/升级处置”或保留英文，不得翻译为“上报/报告”；只有原文明示`report/notify/file/refer`及其对象时，才能写成上报、报告或移交。

新增card的节点、边和`source_unit_ids`只能引用对应候选原有的`unit_ids`。不得借裁决轮追加其他unit、扩展候选命题或引入无关主题；若原候选证据本身不足，保持`kg_only`。

## 输出约束

只返回补丁对象，顶层只能包含：

```text
section_id
coverage_adjudication
promoted_cards
```

示例：

```json
{
  "section_id": "<section_id>",
  "coverage_adjudication": [
    {
      "candidate_id": "cand_001",
      "original_decision": "kg_only",
      "final_decision": "kg_only",
      "card_id": null,
      "reason": "<中文KG边界理由>"
    }
  ],
  "promoted_cards": []
}
```

即使所有候选都保持`kg_only`，也必须逐一输出裁决记录，此时`promoted_cards`为空数组。不得输出`coverage_audit`、既有`cards`、`skip_reason`或其他首次抽取字段。

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
      "proposition": "审查所有权结构时，监管义务要求识别UBO",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_002",
      "reason": "监管外部命令触发识别过程，构成有向触发结构，基础KG仅保存为规则但未表达触发方向。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000489",
        "v7u_N000490"
      ],
      "proposition": "机构采用风险为本方法设定受益所有权阈值，参照多数司法管辖区的25%要求",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_001",
      "reason": "机构设定阈值动作受外部标准约束，形成约束关系，基础KG未表达此方向。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000491"
      ],
      "proposition": "高风险客户的可能较低阈值（低至10%或5%）约束机构阈值设定",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_001",
      "reason": "同样属于阈值设定过程的约束条件，与cand_002合并。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000492"
      ],
      "proposition": "示例：高风险代理行设定5%阈值",
      "decision": "kg_only",
      "card_id": null,
      "reason": "示例，其规则已由前面标准覆盖。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000493"
      ],
      "proposition": "识别UBO时需考虑直接和间接持股",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_002",
      "reason": "识别动作需要参照特定输入信息，构成有向参照，与识别过程合并。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000494",
        "v7u_N000495"
      ],
      "proposition": "示例：通过合计直接和间接持股计算UBO",
      "decision": "kg_only",
      "card_id": null,
      "reason": "示例，其判断逻辑已体现在一般识别过程中。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000496"
      ],
      "proposition": "无自然人受益所有人时，应识别并核实控制人或名义受益所有人",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_003",
      "reason": "例外条件导向替代识别动作，构成有向分支结构。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N000497"
      ],
      "proposition": "示例：上市公司可将总裁或CEO作为名义受益所有人",
      "decision": "kg_only",
      "card_id": null,
      "reason": "示例，已由Card C的替代识别规则覆盖。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N000483",
        "v7u_N000484",
        "v7u_N000485",
        "v7u_N000486",
        "v7u_N000487"
      ],
      "proposition": "控制权与所有权的定义、区别及其在AML中的重要性",
      "decision": "kg_only",
      "card_id": null,
      "reason": "定义性知识，不构成程序性有向结构，基础KG已充分表达。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH06-S10_001",
      "section_id": "CH06-S10",
      "card_nature": "execution",
      "title": "机构设定受益所有权阈值的风险为本方方法",
      "flow_nodes": [
        {
          "node_id": "n1_p7card_CH06-S10_001",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构采用风险为本的方法设定受益所有权阈值",
          "evidence_unit_ids": [
            "v7u_N000490"
          ],
          "evidence_strength": "explicit",
          "source_quote": "Your organization will set the appropriate threshold using a riskbased approach."
        },
        {
          "node_id": "n2_p7card_CH06-S10_001",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "多数司法管辖区的25%受益所有权阈值要求",
          "evidence_unit_ids": [
            "v7u_N000489"
          ],
          "evidence_strength": "explicit",
          "source_quote": "For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more."
        },
        {
          "node_id": "n3_p7card_CH06-S10_001",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "高风险客户的可能较低阈值（可能低至10%或5%）",
          "evidence_unit_ids": [
            "v7u_N000491"
          ],
          "evidence_strength": "explicit",
          "source_quote": "For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5% for customers who pose a significantly higher risk."
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1_p7card_CH06-S10_001",
          "edge_type": "REFERENCES",
          "source": "n1_p7card_CH06-S10_001",
          "target": "n2_p7card_CH06-S10_001",
          "evidence_unit_ids": [
            "v7u_N000489",
            "v7u_N000490"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        },
        {
          "edge_id": "e2_p7card_CH06-S10_001",
          "edge_type": "REFERENCES",
          "source": "n1_p7card_CH06-S10_001",
          "target": "n3_p7card_CH06-S10_001",
          "evidence_unit_ids": [
            "v7u_N000490",
            "v7u_N000491"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N000489",
        "v7u_N000490",
        "v7u_N000491"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构设定受益所有权阈值（process） 受到 多数司法管辖区的25%要求（standard）和高风险下调可能性（standard）的约束；KG不足：基础KG将规则保存为事实，但未表达设定动作与标准之间的约束方向；选项判断：可确认机构设定阈值时需考虑法定基准和风险调整，排除固定阈值或忽略风险的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S10_002",
      "section_id": "CH06-S10",
      "card_nature": "assessment",
      "title": "最终受益所有人（UBO）的识别判断过程",
      "flow_nodes": [
        {
          "node_id": "n1_p7card_CH06-S10_002",
          "node_category": "entry",
          "node_type": "E7_external_command",
          "label": "监管义务要求识别最终受益所有人（审查所有权结构时）",
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "evidence_strength": "explicit",
          "source_quote": "When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer."
        },
        {
          "node_id": "n2_p7card_CH06-S10_002",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "机构计算直接和间接持股总比例，并与适用阈值比较，以确定最终受益所有人",
          "evidence_unit_ids": [
            "v7u_N000493",
            "v7u_N000494",
            "v7u_N000495"
          ],
          "evidence_strength": "explicit",
          "source_quote": "In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership. (v7u_N000493); Individual D owns 10% of Company A directly... also own 72% indirectly... then considered a UBO with 82% shareholding. (v7u_N000494)"
        },
        {
          "node_id": "n3_p7card_CH06-S10_002",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "直接和间接持股信息",
          "evidence_unit_ids": [
            "v7u_N000493"
          ],
          "evidence_strength": "explicit",
          "source_quote": "identify indirect ownership stakes in addition to direct ownership"
        },
        {
          "node_id": "n4_p7card_CH06-S10_002",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "适用受益所有权阈值（多数司法管辖区通常为25%，基于风险方法设定，高风险客户可能低至10%或5%）",
          "evidence_unit_ids": [
            "v7u_N000489",
            "v7u_N000490",
            "v7u_N000491"
          ],
          "evidence_strength": "explicit",
          "source_quote": "most jurisdictions require beneficial ownership to be identified at a threshold of 25% (v7u_N000489); Your organization will set the appropriate threshold using a riskbased approach (v7u_N000490); For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5% (v7u_N000491)"
        },
        {
          "node_id": "n5_p7card_CH06-S10_002",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "UBO识别结论（达到或未达到阈值）",
          "evidence_unit_ids": [
            "v7u_N000494",
            "v7u_N000495"
          ],
          "evidence_strength": "explicit",
          "source_quote": "Individual D is then considered a UBO with 82% shareholding of Company A. (v7u_N000494); Individual C... is not a UBO. (v7u_N000495)"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1_p7card_CH06-S10_002",
          "edge_type": "PRECEDES",
          "source": "n1_p7card_CH06-S10_002",
          "target": "n2_p7card_CH06-S10_002",
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "derivation": "explicit_text",
          "condition": "当审查所有权结构时"
        },
        {
          "edge_id": "e2_p7card_CH06-S10_002",
          "edge_type": "REFERENCES",
          "source": "n2_p7card_CH06-S10_002",
          "target": "n3_p7card_CH06-S10_002",
          "evidence_unit_ids": [
            "v7u_N000493"
          ],
          "derivation": "explicit_text",
          "relation_type": "clue_supports_identification"
        },
        {
          "edge_id": "e3_p7card_CH06-S10_002",
          "edge_type": "REFERENCES",
          "source": "n2_p7card_CH06-S10_002",
          "target": "n4_p7card_CH06-S10_002",
          "evidence_unit_ids": [
            "v7u_N000489",
            "v7u_N000490",
            "v7u_N000491"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        },
        {
          "edge_id": "e4_p7card_CH06-S10_002",
          "edge_type": "PRODUCES",
          "source": "n2_p7card_CH06-S10_002",
          "target": "n5_p7card_CH06-S10_002",
          "evidence_unit_ids": [
            "v7u_N000494",
            "v7u_N000495"
          ],
          "derivation": "explicit_text",
          "relation_type": "identification_leads_to_conclusion"
        }
      ],
      "source_unit_ids": [
        "v7u_N000488",
        "v7u_N000489",
        "v7u_N000490",
        "v7u_N000491",
        "v7u_N000493",
        "v7u_N000494",
        "v7u_N000495"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：监管义务（entry） 触发 机构计算持股并与阈值比较（process），该过程参照直接和间接持股信息（input）和适用阈值标准（standard），并 产生 UBO识别结论（exit）；KG不足：基础KG未表达从触发到判断、输入到结论的有向链；选项判断：可确认UBO识别需要综合直接/间接持股并与风险调整阈值比较，排除仅直接持股或固定阈值的选项；LLM推理：process的“计算直接和间接持股总比例并与适用阈值比较”结合了单元493的直接/间接持股要求和示例494/495的计算步骤，为完成识别功能所必需的唯一合理推导，无其他合理解释。"
    },
    {
      "card_id": "p7card_CH06-S10_003",
      "section_id": "CH06-S10",
      "card_nature": "execution",
      "title": "无自然人受益所有人时的替代识别",
      "flow_nodes": [
        {
          "node_id": "n1_p7card_CH06-S10_003",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "不存在自然人受益所有人",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "evidence_strength": "explicit",
          "source_quote": "In companies where there is no natural beneficial owner"
        },
        {
          "node_id": "n2_p7card_CH06-S10_003",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构应识别并核实控制人或名义受益所有人",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "evidence_strength": "explicit",
          "source_quote": "a controller or a notional beneficial owner should be identified and verified"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1_p7card_CH06-S10_003",
          "edge_type": "PRECEDES",
          "source": "n1_p7card_CH06-S10_003",
          "target": "n2_p7card_CH06-S10_003",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "derivation": "explicit_text",
          "condition": "在不存在自然人受益所有人的公司中"
        }
      ],
      "source_unit_ids": [
        "v7u_N000496"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：在不存在自然人受益所有人的例外条件下（entry），机构应识别并核实控制人或名义受益所有人（process）；KG不足：基础KG将此作为规则保留，但未表达条件-动作的有向结构；选项判断：可确认当无自然人UBO时必须采取替代识别措施，排除始终按持股识别的选项；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_004",
  "cand_006",
  "cand_008",
  "cand_009"
]
```
