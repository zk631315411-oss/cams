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
2. 候选内部存在“情境/事件/线索/输入/标准 → 主体动作或判断 → 结果/义务/控制效果”的局部结构。
3. 该方向结构能够帮助判断选项的顺序、条件、主体职责、义务、应对、因果或适用范围。
4. 基础KG只能保存整句话或各知识点，不能充分表达句内的主体、方向、条件及动作结果关系。

结构复杂度和是否闭环不是门槛。一个unit、一条路径、没有分支或反馈，或没有独立出口，都不能作为`kg_only`理由。entry是图中的关系起点，不要求是时间事件；业务对象、线索输入、风险阈值可以承担入口角色；被动作参照的监管要求、政策基准或风险偏好应作为auxiliary standard/input并由process通过`REFERENCES`指向。

不得用“纯义务陈述”“没有复杂条件”“没有复杂步骤”拒绝提升。只要候选已经明确给出监管要求、风险偏好或状态变化如何约束特定主体的识别、标准选择或分类维持，并形成义务、配置或分类出口，就满足局部有向结构要求。

以下通常应提升：

- 金融机构监控系统根据异常活动进行标记并形成识别结论。
- FIU综合SAR和跨境活动并形成红旗发现。
- 风险阈值和直接/间接持股被机构用于UBO判断并形成分类结论。
- 外部监管要求或上位标准触发机构调整控制、政策或职责。
- 明确条件触发拒绝、批准、升级、报告、监控、复核或持续义务。
- 当地监管要求约束机构如何识别PEP并形成识别义务；不得因规则只有一个unit而拒绝。
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
        "v7u_N000488"
      ],
      "proposition": "审查所有权结构时，机构有义务识别客户的最终受益所有人（UBO）。",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_001",
      "reason": "基础KG可保存该规则，但未表达条件（审查所有权结构）到动作（识别UBO）的有向义务关系，属于增量程序性结构。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000489",
        "v7u_N000490",
        "v7u_N000491",
        "v7u_N000492",
        "v7u_N000493",
        "v7u_N000494",
        "v7u_N000495"
      ],
      "proposition": "待审查对象的直接与间接持股信息，经机构合计并与风险为本的阈值比较后，得出UBO识别结论。",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_002",
      "reason": "涉及风险为本阈值调整、直接与间接持股合计的条件化判断流程，形成完整的有向评估链，基础KG未能充分表达此内部判断结构。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000496",
        "v7u_N000497"
      ],
      "proposition": "当公司不存在自然人受益所有人时，机构应当识别并核实控制人或名义受益所有人。",
      "decision": "p7c_card",
      "card_id": "p7card_CH06-S10_003",
      "reason": "明确例外条件导向特定的识别核实动作并产生主体确认结果，构成增量判断性链，基础KG无法表达此条件-动作-结果的方向性。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000483",
        "v7u_N000484",
        "v7u_N000485",
        "v7u_N000486",
        "v7u_N000487"
      ],
      "proposition": "控制权与所有权在反洗钱中至关重要，BO与UBO的定义和区别对监管要求具有重要意义。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅包含定义、概念区别及一般重要性陈述，基础KG已能充分表达此类基本概念和静态关系，无增量程序性或判断性有向结构。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH06-S10_001",
      "section_id": "CH06-S10",
      "card_nature": "execution",
      "title": "审查所有权结构时识别UBO的监管义务",
      "flow_nodes": [
        {
          "node_id": "n1_e6_obligation_trigger",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "审查所有权结构的情形",
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n1_p2_identify_ubo",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构识别客户UBO",
          "evidence_unit_ids": [
            "v7u_N000488"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1_precedes_1",
          "edge_type": "PRECEDES",
          "source": "n1_e6_obligation_trigger",
          "target": "n1_p2_identify_ubo",
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
      "review_notes": "增量命题：审查所有权结构的情形 —触发→ 机构识别客户UBO的义务；KG不足：基础KG可保存此规则但未表达其内部条件-义务的指向关系；选项判断：可用于判断在何种情况下机构有识别UBO的义务；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S10_002",
      "section_id": "CH06-S10",
      "card_nature": "assessment",
      "title": "基于风险为本阈值的UBO持股合计判断",
      "flow_nodes": [
        {
          "node_id": "n2_e2_ownership_info",
          "node_category": "entry",
          "node_type": "E2_object_entry",
          "label": "待审查对象的直接和间接持股信息",
          "evidence_unit_ids": [
            "v7u_N000493",
            "v7u_N000494",
            "v7u_N000495"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2_p1_assess_ubo",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "机构合计直接与间接持股，并按适用风险阈值判断UBO",
          "evidence_unit_ids": [
            "v7u_N000489",
            "v7u_N000490",
            "v7u_N000491",
            "v7u_N000493",
            "v7u_N000494",
            "v7u_N000495"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2_std_threshold",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "适用的风险为本阈值：一般25%，高风险客户可能10%或5%（如高风险代理行可设5%）",
          "evidence_unit_ids": [
            "v7u_N000489",
            "v7u_N000490",
            "v7u_N000491",
            "v7u_N000492"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2_x1_ubo_conclusion",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "UBO识别结论（根据合计持股是否达到适用阈值判定为是/否UBO）",
          "evidence_unit_ids": [
            "v7u_N000494",
            "v7u_N000495"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e2_precedes_1",
          "edge_type": "PRECEDES",
          "source": "n2_e2_ownership_info",
          "target": "n2_p1_assess_ubo",
          "evidence_unit_ids": [
            "v7u_N000493"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e2_ref_1",
          "edge_type": "REFERENCES",
          "source": "n2_p1_assess_ubo",
          "target": "n2_std_threshold",
          "evidence_unit_ids": [
            "v7u_N000489",
            "v7u_N000490",
            "v7u_N000491"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        },
        {
          "edge_id": "e2_produces_1",
          "edge_type": "PRODUCES",
          "source": "n2_p1_assess_ubo",
          "target": "n2_x1_ubo_conclusion",
          "evidence_unit_ids": [
            "v7u_N000494",
            "v7u_N000495"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N000489",
        "v7u_N000490",
        "v7u_N000491",
        "v7u_N000492",
        "v7u_N000493",
        "v7u_N000494",
        "v7u_N000495"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：待审查对象的持股信息 —> 机构合计直接与间接持股并与风险调整后的阈值比较 —> 得出UBO识别结论；KG不足：基础KG可记录阈值规则和间接持股要求，但不能表达条件-判断-结论的有向流程；选项判断：可用于判断在给定持股结构和风险背景下机构如何决定某人是否为UBO；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH06-S10_003",
      "section_id": "CH06-S10",
      "card_nature": "execution",
      "title": "无自然人受益所有人时识别控制人或名义受益所有人",
      "flow_nodes": [
        {
          "node_id": "n3_e6_no_natural_bo",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "公司不存在自然人受益所有人",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n3_p2_identify_controller",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "机构识别并核实控制人或名义受益所有人",
          "evidence_unit_ids": [
            "v7u_N000496",
            "v7u_N000497"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n3_x1_controller_identified",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "控制人或名义受益所有人被识别并核实（从而了解公司的决策控制人）",
          "evidence_unit_ids": [
            "v7u_N000496",
            "v7u_N000497"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e3_precedes_1",
          "edge_type": "PRECEDES",
          "source": "n3_e6_no_natural_bo",
          "target": "n3_p2_identify_controller",
          "evidence_unit_ids": [
            "v7u_N000496"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e3_produces_1",
          "edge_type": "PRODUCES",
          "source": "n3_p2_identify_controller",
          "target": "n3_x1_controller_identified",
          "evidence_unit_ids": [
            "v7u_N000496",
            "v7u_N000497"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N000496",
        "v7u_N000497"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：公司不存在自然人受益所有人 —> 机构识别并核实控制人或名义受益所有人 —> 控制人/名义受益所有人被确认；KG不足：基础KG可记录该规则，但不能表达条件导向识别动作及结果的有向链；选项判断：可用于判断在无自然人UBO时机构应采取何行动；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```
