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

结构复杂度不是门槛。一个unit、一条路径、没有分支或反馈，都不能作为`kg_only`理由。entry是图中的关系起点，不要求是时间事件；业务对象、线索输入、风险阈值、监管要求或政策基准都可以承担有证据的入口角色。

以下通常应提升：

- 金融机构监控系统根据异常活动进行标记并形成识别结论。
- FIU综合SAR和跨境活动并形成红旗发现。
- 风险阈值和直接/间接持股被机构用于UBO判断并形成分类结论。
- 外部监管要求或上位标准触发机构调整控制、政策或职责。
- 明确条件触发拒绝、批准、升级、报告、监控、复核或持续义务。

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

新增card必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, review_status, review_notes`。

`card_nature`只能为：`execution, assessment, risk_indicator, control`。

每张新增card至少包含一个entry、process和exit，并存在entry经过process到exit的有向路径。

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。节点必须由原文明示，`evidence_strength`只能为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, evidence_strength`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard。
- `PRODUCES`只能由process指向exit。
- `DECIDES`只能由`P3_branch_routing`发出，至少两条分支，每条都有原文明示的`condition`。
- `functional_dependency`只允许用于边，且card必须为`needs_review`并在`review_notes`的“LLM推理”中说明。

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

section_id: `CH02-S04`

section_title: `Types of financial crime > Case example: FullTechGlobal corruption scandal`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH02_S04_001",
      "title_zh": "FullTechGlobal 案中的英国反贿赂法域外效力与合规教训",
      "title_en": "UK Bribery Act Extraterritoriality and Compliance Lessons from FullTechGlobal Case",
      "anchor_unit_ids": [
        "v7u_N000135",
        "v7u_N000136",
        "v7u_N000137",
        "v7u_N000141",
        "v7u_N000143",
        "v7u_N000144"
      ],
      "key_unit_ids": [
        "v7u_N000135",
        "v7u_N000136",
        "v7u_N000137",
        "v7u_N000141",
        "v7u_N000143"
      ],
      "support_unit_ids": [
        "v7u_N000131",
        "v7u_N000132",
        "v7u_N000133",
        "v7u_N000134",
        "v7u_N000138",
        "v7u_N000139",
        "v7u_N000140",
        "v7u_N000142"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000135",
          "unit_type": "fact",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000136",
          "unit_type": "rule",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000137",
          "unit_type": "rule",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000141",
          "unit_type": "case",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000143",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000144",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000131",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000132",
          "unit_type": "case",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000133",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000134",
          "unit_type": "rule",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000138",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000139",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000140",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000142",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    }
  ],
  "same_section_core_point_edges": []
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
        "v7u_N000133",
        "v7u_N000134",
        "v7u_N000138",
        "v7u_N000139",
        "v7u_N000140",
        "v7u_N000141",
        "v7u_N000142"
      ],
      "proposition": "Sophie发现客户FullTechGlobal负面新闻（指控其海外销售贿赂腐败，引发英国反贿赂法关切）→启动调查，发现中间人、虚增发票、壳公司等证据→进行审计→发现ABC框架和内控缺陷，并识别贿赂为上游犯罪。",
      "decision": "p7c_card",
      "card_id": "p7card_CH02-S04_001",
      "reason": "案例中实际发生的多步骤调查审计应对链，包含明确的先后顺序和动作-产出关系，基础KG无法表达该程序性有向结构，有助于选项判断类似情境下的调查流程与发现之间的因果。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000135",
        "v7u_N000136",
        "v7u_N000137"
      ],
      "proposition": "英国反贿赂法2010域外效力规则：公司有英国关联则法适用，母公司对子公司腐败负责，英国母公司可能被起诉。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "属于法律规则定义和一般性后果陈述，基础KG可直接保存完整规则，无程序性动作、判断或主体应对的有向结构。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000143",
        "v7u_N000141"
      ],
      "proposition": "审计发现内控缺陷和贿赂后，FullTechGlobal面临严重监管后果（罚款、审查、刑事责任）。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "为因果事实与后果列表，缺少明确的程序性process主体动作，基础KG可记录该后果信息。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH02-S04_001",
      "section_id": "CH02-S04",
      "card_nature": "execution",
      "title": "Sophie对FullTechGlobal腐败案的调查审计链",
      "flow_nodes": [
        {
          "node_id": "E1",
          "node_category": "entry",
          "node_type": "E1_event_signal",
          "label": "发现客户FullTechGlobal负面新闻，指控其海外销售涉及广泛贿赂和腐败，引发英国反贿赂法域外条款关切",
          "evidence_unit_ids": [
            "v7u_N000132",
            "v7u_N000133",
            "v7u_N000134"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "Sophie启动调查，发现中间人使用、虚增咨询费、伪造发票、壳公司和奢华礼品等贿赂腐败证据",
          "evidence_unit_ids": [
            "v7u_N000138",
            "v7u_N000139",
            "v7u_N000140"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "Sophie进行审计，检查ABC框架和内控机制",
          "evidence_unit_ids": [
            "v7u_N000141"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X1",
          "node_category": "exit",
          "node_type": "X2_product",
          "label": "发现ABC框架和内控机制存在缺陷，监督不足",
          "evidence_unit_ids": [
            "v7u_N000141"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X2",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "贿赂被识别为上游犯罪",
          "evidence_unit_ids": [
            "v7u_N000142"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_001",
          "edge_type": "PRECEDES",
          "source": "E1",
          "target": "P1",
          "evidence_unit_ids": [
            "v7u_N000132",
            "v7u_N000138"
          ],
          "evidence_strength": "explicit"
        },
        {
          "edge_id": "edge_002",
          "edge_type": "PRECEDES",
          "source": "P1",
          "target": "P2",
          "evidence_unit_ids": [
            "v7u_N000141"
          ],
          "evidence_strength": "explicit"
        },
        {
          "edge_id": "edge_003",
          "edge_type": "PRODUCES",
          "source": "P2",
          "target": "X1",
          "evidence_unit_ids": [
            "v7u_N000141"
          ],
          "evidence_strength": "explicit"
        },
        {
          "edge_id": "edge_004",
          "edge_type": "PRODUCES",
          "source": "P2",
          "target": "X2",
          "evidence_unit_ids": [
            "v7u_N000141",
            "v7u_N000142"
          ],
          "evidence_strength": "functional_dependency",
          "condition": null,
          "source_quote": "Her audit uncovered deficiencies... Bribery was identified as the predicate crime...",
          "relation_type": "identification_leads_to_conclusion",
          "review_status": "LLM推理：审计发现内控缺陷与识别贿赂为上游犯罪原文未用明确因果词连接，但基于案例上下文，审计是识别贿赂的必要前置步骤，故标记为functional_dependency待复核。"
        }
      ],
      "source_unit_ids": [
        "v7u_N000132",
        "v7u_N000133",
        "v7u_N000134",
        "v7u_N000138",
        "v7u_N000139",
        "v7u_N000140",
        "v7u_N000141",
        "v7u_N000142"
      ],
      "review_status": "needs_review",
      "review_notes": "增量命题：发现客户负面新闻触发调查，调查后审计，审计产生发现内控缺陷和识别贿赂为上游犯罪。KG不足：基础KG无法表达该调查步骤顺序及动作-产出的有向关系。选项判断：可确认或排除关于案例中Sophie行动顺序、调查步骤与发现之间因果关系的选项。LLM推理：边edge_004（审计→识别贿赂为上游犯罪）原文未直接明确，但审计揭示的腐败活动自然包含识别上游犯罪，存在功能依赖，已标记为functional_dependency。"
    }
  ],
  "skip_reason": null
}
```
