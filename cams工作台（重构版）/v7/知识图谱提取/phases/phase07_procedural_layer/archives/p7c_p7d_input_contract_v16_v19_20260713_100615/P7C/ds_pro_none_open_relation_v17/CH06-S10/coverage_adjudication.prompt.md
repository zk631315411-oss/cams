# P7C Section-Local Coverage Adjudication Prompt v1

## 角色

你是P7C覆盖裁决器。首次抽取器已经发现候选命题并生成通过结构校验的card；你的唯一任务是复核`coverage_audit`中原决定为`kg_only`的候选，判断它们是否因KG/P7C边界理解错误而漏成卡。

只输出完整严格JSON，不输出Markdown或解释。`flow_nodes + flow_edges`仍是知识正本；`coverage_adjudication`和`coverage_audit`只是诊断元数据。

## P7C目的

P7C在不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标和一般知识关系的前提下，从单个section中增量提取对CAMS题目选项判断有用的局部程序性或判断性有向结构：业务情境、事件、线索、输入或标准，如何关联到特定主体的识别、评估、决策或应对，并在相应条件下产生结论、义务、控制结果、分支或后续行动。

P7C不读取题目或参考答案，不处理跨section桥接。当前section原文是唯一事实证据；基础KG摘要只能用于去重，不能补造事实。

## 裁决对象

只复核`original_json.coverage_audit`中`decision=kg_only`的候选。不得新增候选，不得删除候选，不得修改候选的`candidate_id`、`unit_ids`或`proposition`。

原本为`p7c_card`的候选及其`card_id`必须保持不变。`original_json.cards`中的每张既有card必须完整保留，不得删除、改写、拆分、合并或重新编号。

## 裁决标准

将原`kg_only`候选提升为`p7c_card`，必须同时满足：

1. 当前section证据支持关系两端、特定主体、方向以及条件（如有）。
2. 候选内部存在“情境/事件/线索/输入/标准如何关联到主体动作或判断”的局部结构；只有原文明示独立结果时才增加结果节点。
3. 该方向结构能够帮助判断选项的顺序、条件、主体职责、义务、应对、因果或适用范围。
4. 基础KG只能保存整句话或各知识点，不能充分表达句内的主体、方向、条件及动作结果关系。

结构复杂度和是否闭环不是门槛。一个unit、一条路径、没有分支或反馈，或没有独立出口，都不能作为`kg_only`理由。只有对象实际到达、提交、移交或进入某阶段并触发动作时才建entry；静态适用对象、线索输入、分析材料、风险阈值、监管要求、政策基准或风险偏好应作为auxiliary standard/input并由process通过`REFERENCES`指向。

不得用“纯义务陈述”“没有复杂条件”“没有复杂步骤”拒绝提升。只要候选已经明确给出监管要求、风险偏好或状态变化如何约束特定主体的识别、标准选择或分类维持，即使没有独立出口，也满足局部有向结构要求。

以下通常应提升：

- 金融机构监控系统根据异常活动进行标记并形成识别结论。
- FIU综合SAR和跨境活动并形成红旗发现。
- 风险阈值和直接/间接持股被机构用于UBO判断并形成分类结论。
- 外部监管要求或上位标准约束机构调整控制、政策或职责；除非原文明示命令到达后触发动作，否则使用`REFERENCES`而不是`PRECEDES`。
- 明确条件触发拒绝、批准、升级、报告、监控或复核。
- 当地监管要求约束机构如何识别PEP；不得因规则只有一个unit或没有义务出口而拒绝。
- 机构基于风险偏好可以选择更高标准；必须保留可选性，即使没有独立配置出口也可以作为开放式局部关系。
- 卸任等状态变化后，特定机构仍明确维持既有分类；必须保留“部分机构”“可能”等限定。

以下保持`kg_only`：

- 纯定义、分类、阈值数值或组成列表，没有主体应用和结果关系。
- 普通犯罪方法、犯罪分子操作步骤或普通案例机制，没有机构、FIU、监管或执法主体的识别、判断或应对。
- 孤立红旗、后果、历史事实或抽象风险缓解目的。
- 只有主题相关性，或者必须补造主体、条件、方向、动作或结果才能闭合。

## 修改规则

对每个原`kg_only`候选，在顶层`coverage_adjudication`中新增一条记录：

```json
{
  "candidate_id": "cand_001",
  "original_decision": "kg_only",
  "final_decision": "kg_only",
  "reason": "<中文裁决理由>"
}
```

`final_decision`只能为`kg_only`或`p7c_card`。

保持`kg_only`时：原`coverage_audit`记录的`decision`仍为`kg_only`，`card_id`仍为`null`，可以更新中文`reason`。

提升为`p7c_card`时：

- 将原`coverage_audit`记录的`decision`改为`p7c_card`；
- 填入新增card的`card_id`；
- 更新中文`reason`，说明基础KG不能表达的方向结构；
- 在`cards`末尾追加一张有证据的局部card；
- 不得修改其他候选或已有card。

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

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard。
- `PRODUCES`只能由process指向exit。
- `DECIDES`只能由`P3_branch_routing`发出，至少两条分支，每条都有原文明示的`condition`。
- `derivation=llm_inference`只说明边依赖必要功能推理，不改变`candidate_status`，也不表示P7D已经接受或拒绝。

静态适用对象、审查材料或判断输入不得仅因语法顺序建成`entry --PRECEDES--> process`；应建为auxiliary input并由process通过`REFERENCES`指向。不得把同一谓词的主动式和被动式拆成process与exit，也不得把“动作需要理由、批准或遵循要求”写成“动作`PRODUCES`要求/义务”。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写，不得创造新类型。

必须保留`must, should, may, might, could, often, potentially, help`等情态强度。不得将“有助于缓解”强化为“风险已经消除”。`must/shall/is required to`只证明义务存在，不证明动作已经完成；除非原文明示完成或结果已经发生，不得输出“已调整”“已建立”“已降低”等完成状态。

`must`本身不证明义务是持续、定期、永久或反复的，不得无证据增加这些限定。`escalate/escalation`默认写成“升级处理/升级处置”或保留英文，不得翻译为“上报/报告”；只有原文明示`report/notify/file/refer`及其对象时，才能写成上报、报告或移交。

新增card只能引用对应候选`unit_ids`及同一局部命题必要的当前section unit。不得借裁决轮扩展到无关主题。

## 输出约束

返回完整顶层对象：

```text
section_id
section_title
coverage_adjudication
coverage_audit
cards
skip_reason
```

如果最终存在card，`skip_reason`必须为`null`。如果仍无card，保留合适的中文`skip_reason`。

## 当前section

section_id: `CH06-S10`

section_title: `Money Laundering Risks in Financial Services > Control and ownership for AML compliance`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH06_S10_001",
      "title_zh": "受益所有人（BO）与最终受益所有人（UBO）",
      "title_en": "Beneficial Owner (BO) vs Ultimate Beneficial Owner (UBO)",
      "anchor_unit_ids": [
        "v7u_N000484",
        "v7u_N000485"
      ],
      "key_unit_ids": [
        "v7u_N000484",
        "v7u_N000485",
        "v7u_N000486",
        "v7u_N000487",
        "v7u_N000483"
      ],
      "support_unit_ids": [
        "v7u_N000483",
        "v7u_N000486",
        "v7u_N000487"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000484",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000485",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000486",
          "unit_type": "classification",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000487",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000483",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        }
      ]
    },
    {
      "core_point_id": "cp_CH06_S10_002",
      "title_zh": "UBO识别要求、门槛及特殊情况",
      "title_en": "UBO Identification Requirements, Thresholds, and Special Cases",
      "anchor_unit_ids": [
        "v7u_N000488",
        "v7u_N000489",
        "v7u_N000490",
        "v7u_N000491",
        "v7u_N000493",
        "v7u_N000496"
      ],
      "key_unit_ids": [
        "v7u_N000488",
        "v7u_N000489",
        "v7u_N000490",
        "v7u_N000491",
        "v7u_N000493"
      ],
      "support_unit_ids": [
        "v7u_N000492",
        "v7u_N000494",
        "v7u_N000495",
        "v7u_N000497"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000488",
          "unit_type": "rule",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000489",
          "unit_type": "rule",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000490",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000491",
          "unit_type": "rule",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000493",
          "unit_type": "rule",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000496",
          "unit_type": "rule",
          "cp_unit_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000492",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000494",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000495",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000497",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH06_S10_001",
      "target_id": "cp_CH06_S10_002",
      "relation_type": "prepares",
      "reason": "CP1 defines BO and UBO and explains their distinction, providing the foundational concepts needed for CP2 which details UBO identification requirements and thresholds."
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
        "v7u_N000489",
        "v7u_N000490",
        "v7u_N000491",
        "v7u_N000493"
      ],
      "proposition": "机构审查所有权结构时，有监管义务识别UBO，通常阈值25%，机构基于风险设定适当阈值，高风险客户可能10%或5%，并须同时考虑直接和间接持股，形成UBO识别结论。",
      "decision": "p7c_card",
      "card_id": "p7card_CH06_S10_001",
      "reason": "形成从审查事件触发、标准约束识别动作到产生分类结论的有向判断链，基础KG只能保存孤立规则和阈值，不能表达审查->识别->结论的完整局部程序结构。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000496"
      ],
      "proposition": "不存在自然人受益所有人时，机构应识别并核实控制人或名义受益所有人，形成控制人识别结论。",
      "decision": "p7c_card",
      "card_id": "p7card_CH06_S10_002",
      "reason": "例外条件导向不同识别路径，形成条件->动作->结论的判断链，基础KG不能表达例外下的差异化识别流程。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000483"
      ],
      "proposition": "控制权和所有权在AML中重要且常被隐藏。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅为背景事实陈述，基础KG可保存。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000484",
        "v7u_N000485",
        "v7u_N000486",
        "v7u_N000487"
      ],
      "proposition": "BO和UBO的定义、区别及其监管重要性。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义、分类和事实说明，基础KG已能充分表达。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000492"
      ],
      "proposition": "高风险代理行关系可能设定5%UBO阈值示例。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "案例说明，基础KG可保存为普通案例事实。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000494",
        "v7u_N000495"
      ],
      "proposition": "通过直接和间接持股计算UBO的示例。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "案例计算演示，基础KG可保存为普通案例。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000497"
      ],
      "proposition": "上市公司可将总裁或CEO作为名义受益所有人。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "案例说明，基础KG可保存。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH06_S10_001",
      "section_id": "CH06-S10",
      "card_nature": "assessment",
      "title": "常规UBO识别：基于风险阈值的直接与间接持股评估",
      "flow_nodes": [
        {
          "node_id": "E1_review_ownership",
          "node_category": "entry",
          "node_type": "E1_event_signal",
          "label": "机构：审查客户所有权结构",
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P1_identify_ubo",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "机构必须识别最终受益所有人（UBO）",
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "I_ownership_info",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "客户所有权结构信息（直接和间接持股）",
          "evidence_unit_ids": [
            "v7u_N000493"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "S_ubo_thresholds",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "UBO识别阈值：通常≥25%；机构须采用风险为本方法设定阈值；高风险客户可能低至10%甚至5%",
          "evidence_unit_ids": [
            "v7u_N000489",
            "v7u_N000490",
            "v7u_N000491"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X1_ubo_identified",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "UBO识别结论（确定谁是UBO）",
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_001_1",
          "edge_type": "PRECEDES",
          "source": "E1_review_ownership",
          "target": "P1_identify_ubo",
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "derivation": "explicit_text",
          "relation_type": null,
          "condition": "When reviewing ownership structures",
          "source_quote": "When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer."
        },
        {
          "edge_id": "edge_001_2",
          "edge_type": "REFERENCES",
          "source": "P1_identify_ubo",
          "target": "I_ownership_info",
          "evidence_unit_ids": [
            "v7u_N000493"
          ],
          "derivation": "explicit_text",
          "relation_type": "clue_supports_identification",
          "condition": null,
          "source_quote": "In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership."
        },
        {
          "edge_id": "edge_001_3",
          "edge_type": "REFERENCES",
          "source": "P1_identify_ubo",
          "target": "S_ubo_thresholds",
          "evidence_unit_ids": [
            "v7u_N000489",
            "v7u_N000490",
            "v7u_N000491"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action",
          "condition": null,
          "source_quote": "For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more... Your organization will set the appropriate threshold using a riskbased approach... For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5%..."
        },
        {
          "edge_id": "edge_001_4",
          "edge_type": "PRODUCES",
          "source": "P1_identify_ubo",
          "target": "X1_ubo_identified",
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "derivation": "llm_inference",
          "relation_type": "identification_leads_to_conclusion",
          "condition": null,
          "source_quote": null
        }
      ],
      "source_unit_ids": [
        "v7u_N000488",
        "v7u_N000489",
        "v7u_N000490",
        "v7u_N000491",
        "v7u_N000493"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：机构审查所有权结构 → 基于风险阈值和直接间接持股信息识别UBO → 产生UBO识别结论。KG不足：基础KG可保存孤立阈值和规则，但不能表达审查事件触发识别动作、标准约束评估及产生分类结论的有向判断链。选项判断：可确认或排除关于识别条件、阈值适用和直接间接持股要求的选项。LLM推理：P1_identify_ubo --PRODUCES--> X1_ubo_identified 边为功能必要推理（识别动作必然产生识别结论），无其他LLM推理。"
    },
    {
      "card_id": "p7card_CH06_S10_002",
      "section_id": "CH06-S10",
      "card_nature": "assessment",
      "title": "例外情况：无自然人UBO时识别控制人或名义受益所有人",
      "flow_nodes": [
        {
          "node_id": "E6_no_natural_ubo",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "不存在自然人受益所有人",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P2_identify_controller",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构应识别并核实控制人或名义受益所有人",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X1_controller_identified",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "控制人或名义受益所有人被识别",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_002_1",
          "edge_type": "PRECEDES",
          "source": "E6_no_natural_ubo",
          "target": "P2_identify_controller",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "derivation": "explicit_text",
          "relation_type": null,
          "condition": "In companies where there is no natural beneficial owner",
          "source_quote": "In companies where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified."
        },
        {
          "edge_id": "edge_002_2",
          "edge_type": "PRODUCES",
          "source": "P2_identify_controller",
          "target": "X1_controller_identified",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "derivation": "llm_inference",
          "relation_type": "identification_leads_to_conclusion",
          "condition": null,
          "source_quote": null
        }
      ],
      "source_unit_ids": [
        "v7u_N000496"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：不存在自然人UBO → 机构识别控制人或名义受益所有人 → 控制人被识别。KG不足：基础KG只能保存规则文本，不能表达例外条件导向不同识别动作及结果的差异化判断链。选项判断：可确认或排除关于无自然人UBO时识别控制人的选项。LLM推理：P2_identify_controller --PRODUCES--> X1_controller_identified 边为功能必要推理（识别核实动作产生识别结果），无其他LLM推理。"
    }
  ],
  "skip_reason": null
}
```
