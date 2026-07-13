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

必须保留`must, should, may, might, could, often, potentially, help`等情态强度。不得将“有助于缓解”强化为“风险已经消除”。

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

section_id: `CH05-S04`

section_title: `Financial crime risks in relation to other types of risks > Operational, legal, concentration, and reputational risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH05_S04_001",
      "title_zh": "主要风险类型：运营、法律、集中度、声誉",
      "title_en": "Key risk types: operational, legal, concentration, reputational",
      "anchor_unit_ids": [
        "v7u_N000369"
      ],
      "key_unit_ids": [
        "v7u_N000369"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000369",
          "unit_type": "classification",
          "cp_unit_role": "classifies"
        }
      ]
    },
    {
      "core_point_id": "cp_CH05_S04_002",
      "title_zh": "运营风险：定义与监管挑战",
      "title_en": "Operational risk: definition and regulatory challenges",
      "anchor_unit_ids": [
        "v7u_N000370",
        "v7u_N000375"
      ],
      "key_unit_ids": [
        "v7u_N000370",
        "v7u_N000375",
        "v7u_N000376",
        "v7u_N000377",
        "v7u_N000378"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000370",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000375",
          "unit_type": "definition",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000376",
          "unit_type": "process",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000377",
          "unit_type": "risk_indicator",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000378",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        }
      ]
    },
    {
      "core_point_id": "cp_CH05_S04_003",
      "title_zh": "法律风险：来源、后果及AFC保护",
      "title_en": "Legal risk: sources, consequences, and AFC protection",
      "anchor_unit_ids": [
        "v7u_N000371",
        "v7u_N000379"
      ],
      "key_unit_ids": [
        "v7u_N000371",
        "v7u_N000379",
        "v7u_N000381",
        "v7u_N000380"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000371",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000379",
          "unit_type": "definition",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000381",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000380",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        }
      ]
    },
    {
      "core_point_id": "cp_CH05_S04_004",
      "title_zh": "集中度风险：过度敞口、缓解与管理",
      "title_en": "Concentration risk: over-exposure, mitigation, and management",
      "anchor_unit_ids": [
        "v7u_N000372",
        "v7u_N000382"
      ],
      "key_unit_ids": [
        "v7u_N000372",
        "v7u_N000382",
        "v7u_N000384",
        "v7u_N000385",
        "v7u_N000383"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000372",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000382",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000384",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000385",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000383",
          "unit_type": "fact",
          "cp_unit_role": "prescribes_measure"
        }
      ]
    },
    {
      "core_point_id": "cp_CH05_S04_005",
      "title_zh": "声誉风险：特征与信任因素",
      "title_en": "Reputational risk: characteristics and trust factor",
      "anchor_unit_ids": [
        "v7u_N000373",
        "v7u_N000386"
      ],
      "key_unit_ids": [
        "v7u_N000373",
        "v7u_N000386",
        "v7u_N000387",
        "v7u_N000388"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000373",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000386",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000387",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000388",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH05_S04_001",
      "target_id": "cp_CH05_S04_002",
      "relation_type": "contains",
      "reason": "CP1 lists the four key risk types, and CP2 explains operational risk as one of those types."
    },
    {
      "source_id": "cp_CH05_S04_001",
      "target_id": "cp_CH05_S04_003",
      "relation_type": "contains",
      "reason": "CP1 lists the four key risk types, and CP3 explains legal risk as one of those types."
    },
    {
      "source_id": "cp_CH05_S04_001",
      "target_id": "cp_CH05_S04_004",
      "relation_type": "contains",
      "reason": "CP1 lists the four key risk types, and CP4 explains concentration risk as one of those types."
    },
    {
      "source_id": "cp_CH05_S04_001",
      "target_id": "cp_CH05_S04_005",
      "relation_type": "contains",
      "reason": "CP1 lists the four key risk types, and CP5 explains reputational risk as one of those types."
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
        "v7u_N000376"
      ],
      "proposition": "全球组织以母国监管政策为基础标准，并根据东道国法律调整，形成适配的合规配置",
      "decision": "p7c_card",
      "card_id": "p7card_CH05-S04_001",
      "reason": "存在从外部命令到调整动作再到配置变化的局部程序性有向结构，超出基础KG的表达能力。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000369"
      ],
      "proposition": "组织面临运营、法律、集中度、声誉等主要风险类型",
      "decision": "kg_only",
      "card_id": null,
      "reason": "该陈述为风险类型分类事实，无程序性有向结构，可由基础KG充分表达。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000370"
      ],
      "proposition": "运营风险定义：因内部流程、人员、系统或外部事件导致损失的风险",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义陈述，无有向结构，基础KG可充分表达。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000371"
      ],
      "proposition": "法律风险定义：刑事处罚、诉讼或不可执行合同可能损害组织",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义陈述。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000372"
      ],
      "proposition": "集中度风险定义：源于对单一客户或关联客户群体的过度敞口",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义陈述。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000373"
      ],
      "proposition": "声誉风险定义：因控制薄弱被犯罪分子利用或利益相关者失去信心",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯定义陈述。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000374"
      ],
      "proposition": "这些风险通常由非AFC团队管理，但理解其与金融犯罪风险的关联很重要",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般说明性陈述，无具体程序性结构。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N000375"
      ],
      "proposition": "运营风险包括在多司法管辖区维持AFC控制的能力",
      "decision": "kg_only",
      "card_id": null,
      "reason": "细化定义，无有向结构。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N000377"
      ],
      "proposition": "不断演变的法规可能与现有业务模式和控制错位",
      "decision": "kg_only",
      "card_id": null,
      "reason": "风险指标/一般因果，无明确应对链。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N000378"
      ],
      "proposition": "合规计划必须持续更新",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立义务陈述，原文未明示触发条件或完整应对结构。"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N000379"
      ],
      "proposition": "法律风险源于可能违反法规、法律和道德实践",
      "decision": "kg_only",
      "card_id": null,
      "reason": "定义性陈述。"
    },
    {
      "candidate_id": "cand_012",
      "unit_ids": [
        "v7u_N000380"
      ],
      "proposition": "政府可能处以处罚或罚款，第三方可能提起诉讼",
      "decision": "kg_only",
      "card_id": null,
      "reason": "可能性后果陈述，无有向处置链。"
    },
    {
      "candidate_id": "cand_013",
      "unit_ids": [
        "v7u_N000381"
      ],
      "proposition": "充分的AFC控制可增加对犯罪和不当关系的保护",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般规则陈述，无具体执行结构。"
    },
    {
      "candidate_id": "cand_014",
      "unit_ids": [
        "v7u_N000382"
      ],
      "proposition": "AFC与战略多元化可降低集中度风险",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般规则陈述。"
    },
    {
      "candidate_id": "cand_015",
      "unit_ids": [
        "v7u_N000383"
      ],
      "proposition": "借助技术的客户尽职调查有助于管理风险敞口",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般规则陈述。"
    },
    {
      "candidate_id": "cand_016",
      "unit_ids": [
        "v7u_N000384"
      ],
      "proposition": "集中度可能出现在借贷、融资、采购等业务关系中",
      "decision": "kg_only",
      "card_id": null,
      "reason": "风险存在领域的事实陈述。"
    },
    {
      "candidate_id": "cand_017",
      "unit_ids": [
        "v7u_N000385"
      ],
      "proposition": "风险可能因客户行为或涉及客户的外部行为而增加",
      "decision": "kg_only",
      "card_id": null,
      "reason": "风险增加因素说明。"
    },
    {
      "candidate_id": "cand_018",
      "unit_ids": [
        "v7u_N000386"
      ],
      "proposition": "声誉风险难以量化",
      "decision": "kg_only",
      "card_id": null,
      "reason": "风险特征事实。"
    },
    {
      "candidate_id": "cand_019",
      "unit_ids": [
        "v7u_N000387"
      ],
      "proposition": "信任建立缓慢但易丧失，一条新闻即可驱离客户与投资者",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般机制描述，无程序性结构。"
    },
    {
      "candidate_id": "cand_020",
      "unit_ids": [
        "v7u_N000388"
      ],
      "proposition": "组织的声誉源于其商业实践与道德选择",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般事实陈述。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH05-S04_001",
      "section_id": "CH05-S04",
      "card_nature": "execution",
      "title": "全球组织以母国监管政策为基础标准并适配东道国法律",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "entry",
          "node_type": "E7_external_command",
          "label": "母国监管政策",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "全球组织根据各东道国法律调整",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n3",
          "node_category": "exit",
          "node_type": "X5_config_change",
          "label": "合规政策配置适配东道国法律",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n4",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "各东道国法律",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "PRECEDES",
          "source": "n1",
          "target": "n2",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "evidence_strength": "explicit"
        },
        {
          "edge_id": "e2",
          "edge_type": "REFERENCES",
          "source": "n2",
          "target": "n4",
          "relation_type": "standard_constrains_action",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "evidence_strength": "explicit"
        },
        {
          "edge_id": "e3",
          "edge_type": "PRODUCES",
          "source": "n2",
          "target": "n3",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "source_unit_ids": [
        "v7u_N000376"
      ],
      "review_status": "accepted",
      "review_notes": "增量命题：母国监管政策 --PRECEDES--> 全球组织根据东道国法律调整 --PRODUCES--> 合规配置适配东道国法律；KG不足：基础KG可记录政策基准事实，但无法表达内部顺序、调整动作及配置变化的有向结构；选项判断：可确认或排除关于合规调整步骤、基准来源及东道国法律作用的选项；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```
