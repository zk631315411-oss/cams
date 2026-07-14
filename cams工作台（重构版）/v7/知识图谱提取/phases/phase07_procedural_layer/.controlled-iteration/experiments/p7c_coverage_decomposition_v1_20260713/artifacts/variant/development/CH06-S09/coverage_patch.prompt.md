# P7C Coverage Patch Builder Prompt v1

## 角色

你是P7C候选图补丁构建器。上一独立调用已经完成命题发现、KG边界判断和覆盖匹配；本调用没有API记忆，因此`gap_claims`会完整提供需要处理的命题。

你只能把`gap_claims`构造成只增式候选图补丁。不得重新扫描并新增命题，不得将命题改判为KG，不得删除、修改、替换或重新编号`original_json`中的任何既有内容。只输出严格JSON，不输出Markdown或解释。

## 构图原则

- 每个`gap_claims`必须得到`new_card`、`card_supplement`或`unresolved`处理结果。
- 优先补充语义上相同的已有card；不同主体、不同业务对象或不同局部链才新建card。
- `partially_covered`中的错误旧边不得删除。应追加保留原文条件和限定词的正确替代边，旧边留给P7D拒绝。
- 结果必须是语义独立事实。同一谓词的主动式和被动式不得拆成process与exit。
- 静态输入、线索、材料、阈值和标准使用auxiliary节点，由process通过`REFERENCES`指向。
- 动作产生独立分类、结论、记录、状态变化或控制效果时，使用process到exit的`PRODUCES`。
- 单一路径条件可以使用带`condition`的`PRECEDES`；只有至少两条原文明示路径才使用`DECIDES`。
- 保留`must, should, may, might, could, often, potentially, help, appeared, suggested, typically`等原文强度。标签和边的`qualifier`不得把可能性、暂定判断或帮助关系强化为确定结果。
- 证据不足以可靠构图时输出`unresolved`，不得补造节点或边。

## 节点和边

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。`evidence_strength`固定为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。

- `edge_type`只能为`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。
- `derivation`只能为`explicit_text`或`llm_inference`。
- `REFERENCES`只能由process指向auxiliary input或standard。
- `PRODUCES`只能由process指向exit。
- `DECIDES`只能由`P3_branch_routing`发出，并保留原文分支条件。
- 默认省略`relation_type`；证据充分时才填写，不得自造类型。

## 输出合同

顶层必须且只能包含：`section_id, claim_resolutions, new_cards, card_supplements`。

`claim_resolutions`必须逐项覆盖`gap_claims`：

```json
{
  "claim_id": "claim_001",
  "resolution": "card_supplement",
  "card_id": "p7card_CH00-S00_001",
  "reason": "<中文构图说明>"
}
```

`resolution`只能为`new_card, card_supplement, unresolved`。`unresolved`时`card_id=null`并说明无法构图的证据缺口。

新增card必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes, coverage_claim_ids`。

- `card_nature`只能为`execution, assessment, risk_indicator, control`。
- `candidate_status`固定为`candidate`。
- `coverage_claim_ids`列出该card承接的gap claim。

补充已有card使用：

```json
{
  "patch_id": "coverage_patch_001",
  "card_id": "<已有card_id>",
  "coverage_claim_ids": ["claim_001"],
  "reason": "<中文>",
  "add_flow_nodes": [],
  "add_flow_edges": [],
  "add_source_unit_ids": []
}
```

补充至少新增一个节点或一条边。新增ID不得与已有ID重复。新增边可以连接已有节点和新增节点。所有证据必须来自`allowed_unit_ids`，并包含在最终card的`source_unit_ids`中。

## 当前section

运行器将在此处追加当前section原文、首次抽取JSON、gap claims和允许的unit ID。KG边界已经由Audit决定，本调用不接收KG摘要。

## 调用输入

```json
{
  "section_id": "CH06-S09",
  "section_title": "Money Laundering Risks in Financial Services > Politically exposed person risks",
  "section_text_with_unit_anchors": "[v7u_N000457|457] A politically exposed person (PEP) is an individual in a prominent political function, their immediate family, close associates, and any businesses held or controlled by that person.\nZH: 政治敏感人物（政治敏感人物）的定义：担任重要公职的个人及其亲属和密切关联人\n\n[v7u_N000458|458] One challenge in identifying PEPs is the varying guidance and recommendations in each jurisdiction.\nZH: 识别政治敏感人物的挑战在于各司法管辖区指引不同\n\n[v7u_N000459|459] Organizations must adhere to their local regulatory requirements in identifying PEPs.\nZH: 机构必须遵守当地监管要求识别政治敏感人物\n\n[v7u_N000460|460] However, organizations may choose to enforce higher standards based on their risk appetite.\nZH: 机构可根据风险偏好执行更高的政治敏感人物标准\n\n[v7u_N000461|461] According to the Financial Action Task Force (FATF), there are three types of PEPs:\nZH: FATF将政治敏感人物分为三类\n\n[v7u_N000462|462] Foreign PEPs are individuals entrusted with prominent public functions by a foreign country.\nZH: 外国政治敏感人物指受外国委托担任重要公共职能的个人\n\n[v7u_N000463|463] Domestic PEPs are individuals entrusted domestically with prominent public functions.\nZH: 国内政治敏感人物指在国内担任重要公共职能的个人\n\n[v7u_N000464|464] International organization PEPs are individuals from an international organization entrusted with a prominent function such as secretary general, executive director, or president.\nZH: 国际组织政治敏感人物指在国际组织中担任秘书长、执行董事或主席等要职的个人\n\n[v7u_N000465|465] Individuals in high positions and their associates are more vulnerable to corruption.\nZH: 高层职位个人及其关联人更易受腐败影响\n\n[v7u_N000466|466] Corruption might be favors where the PEP directs government contracts to an organization in return for kickbacks. In addition, a PEP might influence legislation for bribes or flee the country with government funds.\nZH: 政治敏感人物腐败示例：以政府合同换取回扣、影响立法收受贿赂或携政府资金潜逃\n\n[v7u_N000467|467] Use a broad definition for defining a PEP.\nZH: 应采用宽泛定义来界定政治敏感人物\n\n[v7u_N000468|468] PEPs can generally be defined as:\nZH: 政治敏感人物的一般定义\n\n[v7u_N000469|469] A person in a prominent decision-making or influential role\nZH: 政治敏感人物指担任重要决策或有影响力角色的人\n\n[v7u_N000470|470] A person within royal, military, legislative, judicial, executive, or similar government positions\nZH: 政治敏感人物包括王室、军事、立法、司法、行政或类似政府职位的人\n\n[v7u_N000471|471] PEPs will often use nominees or businesses they are associated with.\nZH: 政治敏感人物常使用名义人或关联企业\n\n[v7u_N000472|472] Therefore, the definition of PEP can also include:\nZH: 政治敏感人物定义还可包括以下人员\n\n[v7u_N000473|473] Immediate family\nZH: 政治敏感人物的直系亲属\n\n[v7u_N000474|474] Close friends or associates\nZH: 政治敏感人物的密友或关联人\n\n[v7u_N000475|475] Businesses owned or held by those individuals\nZH: 政治敏感人物拥有或持有的企业\n\n[v7u_N000476|476] Under a risk-based approach, PEP risk is manageable.\nZH: 基于风险的方法下，政治敏感人物风险是可控的\n\n[v7u_N000477|477] Some organizations follow a “once a PEP, always a PEP” approach because the individual may remain in the same circles of influence, even if they have stepped down.\nZH: 部分机构采用“一旦是政治敏感人物，永远是政治敏感人物”的方法\n\n[v7u_N000478|478] Other organizations will look at:\nZH: 其他机构会考察以下因素\n\n[v7u_N000479|479] The individual’s influence at the time, such as their ability to award contracts or allocate funds\nZH: 考察个人当时的影响力，如授予合同或分配资金的能力\n\n[v7u_N000480|480] How long the individual has been classified as a PEP\nZH: 考察个人被归类为政治敏感人物的时间长短\n\n[v7u_N000481|481] The purpose of the PEP designation is important.\nZH: 政治敏感人物 认定的目的具有重要意义\n\n[v7u_N000482|482] Organizations must take the necessary steps to adapt transaction monitoring and KYC reviews and escalate based on their risk appetite.\nZH: 机构必须根据风险偏好调整交易监控和 了解你的客户 审查",
  "allowed_unit_ids": [
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
  ],
  "original_json": {
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
  },
  "gap_claims": [
    {
      "claim_id": "claim_005",
      "unit_ids": [
        "v7u_N000478",
        "v7u_N000479",
        "v7u_N000480"
      ],
      "proposition": "其他机构根据个人卸任后的影响力和分类时长来决定是否继续将其认定为PEP",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "未表达其他机构依据影响力和时长进行决策的有向命题，缺少对应节点和边。",
      "condition": "个人卸任后",
      "qualifier": null,
      "reason": "原文通过其他机构的考察维度隐含了评估决策的有向关系，属于P7C增量命题，但现有cards未覆盖。"
    }
  ]
}
```
