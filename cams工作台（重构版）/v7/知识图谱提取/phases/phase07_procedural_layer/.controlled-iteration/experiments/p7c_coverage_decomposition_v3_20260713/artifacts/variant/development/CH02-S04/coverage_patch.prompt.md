# P7C Coverage Patch Builder Prompt v2

## 角色

你是P7C候选图补丁构建器。上一独立调用已经完成命题发现、KG边界判断和覆盖匹配；本调用没有API记忆，因此`gap_claims`会完整提供需要处理的命题。

你只能把`gap_claims`构造成只增式候选图补丁。不得重新扫描并新增命题，不得将命题改判为KG，不得删除、修改、替换或重新编号`original_json`中的任何既有内容。只输出严格JSON，不输出Markdown或解释。

## 构图前证据检查

对每个gap claim逐项检查原文，并在内部确认：

1. 主体、动作或判断、输入/条件以及结果分别由哪些unit直接支持。
2. source节点的标签和证据是否真的表示产生target的那个动作或判断，而不只是主题相近。
3. `must, should, may, might, could, often, potentially, help, appeared, suggested, typically`等限定是否同时进入相关节点标签和边字段。
4. target是否为语义独立事实，而不是source动作的被动语态或完成态复述。

任一关键部分没有直接证据时，输出`unresolved`。不得从section主题、业务常识或其他节点推定未写明的执行主体。

## 复用已有节点的限制

只有已有节点的主体、动作语义、限定词和证据unit都与gap claim一致时才能复用。主题相同或位于同一card不够。

如果原文中的结果来自后续调查、证据评估、计算比较或其他新动作，而已有process只表示初步调查、一般识别或宽泛流程，必须新增准确的process节点，不能把结果直接挂到旧process。

新增process节点也必须由原文明示；无法建立有证据的process时输出`unresolved`。

## 限定词硬规则

限定词只写在edge的`qualifier`中不够。P7D会分别审核节点和边：

- 原文为`can help identify`，target标签必须写成“可以帮助识别……”或“可能识别……”，不能写成“识别……”；
- 原文为`helps ensure`，target标签必须保留“有助于确保……”，不能写成“已经确保/得到确保”；
- 原文为`appeared/suggested`，结论节点标签必须保留“似乎/证据表明或暗示”，不能写成确定结论；
- 原文为`may/might/could`，节点标签和边都不得强化为必然结果。

## 独立结果硬规则

不得把同一谓词的主动式和被动式拆成process与exit。例如process已经是“创建、修改或删除规则”，不得再增加“规则被创建、修改或删除”的exit和`PRODUCES`边。此类动作如果参照明确输入，只输出开放式`process REFERENCES input/standard`关系。

对于计算或阈值比较示例，应建立由原文支持的“计算/合计并比较”assessment process，再由它产生带条件的分类结果；不得把分类结果挂到仅表示一般识别的宽泛process上。

## 构图原则

- 每个`gap_claims`必须得到`new_card`、`card_supplement`或`unresolved`处理结果。
- 优先补充语义上相同且证据匹配的已有card；不同主体、不同业务对象或不同局部链才新建card。
- `partially_covered`中的错误旧边不得删除。可以追加证据充分的正确替代节点和边，旧边留给P7D拒绝。
- 静态输入、线索、材料、阈值和标准使用auxiliary节点，由process通过`REFERENCES`指向。
- 动作产生独立分类、结论、记录、状态变化或控制效果时，使用process到exit的`PRODUCES`。
- 单一路径条件可以使用带`condition`的`PRECEDES`；只有至少两条原文明示路径才使用`DECIDES`。
- 证据不足以可靠构图时输出`unresolved`，不得为了覆盖率补造节点或边。

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
- `PRODUCES`只能由process指向语义独立的exit。
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
  "reason": "<说明主体、source、target、限定词分别由哪些unit支持>"
}
```

`resolution`只能为`new_card, card_supplement, unresolved`。`unresolved`时`card_id=null`，并具体说明缺少主体、source动作、target结果、方向、条件或限定词中的哪一项证据。

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
  "reason": "<中文证据说明>",
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
  "section_id": "CH02-S04",
  "section_title": "Types of financial crime > Case example: FullTechGlobal corruption scandal",
  "section_text_with_unit_anchors": "[v7u_N000131|131] Sophie is an AFC manager in the compliance department of a financial institution that has some global businesses as its customers.\nZH: Sophie 是金融机构合规部的金融犯罪防控经理。\n\n[v7u_N000132|132] One day, she came across negative news concerning their customer FullTechGlobal Services, which is incorporated and headquartered in the US and is a subsidiary of a UK company.\nZH: Sophie 发现客户 FullTechGlobal Services 的负面新闻。\n\n[v7u_N000133|133] The company faced serious accusations of widespread bribery and corruption due to its overseas sales practices.\nZH: 该公司因海外销售行为面临广泛贿赂和腐败的严重指控。\n\n[v7u_N000134|134] This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010.\nZH: 此事引发对《英国反贿赂法》域外条款的关切。\n\n[v7u_N000135|135] The UK Bribery Act 2010 is one of the world’s strictest anti-corruption laws.\nZH: 《英国反贿赂法》是全球最严格的反腐败法律之一。\n\n[v7u_N000136|136] It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location.\nZH: 该法适用于任何与英国有关联的公司，母公司需对子公司腐败行为负责。\n\n[v7u_N000137|137] This extraterritorial scope means that the UK parents of non-UK businesses engaging in bribery and corruption can also face prosecution, emphasizing the need for robust compliance measures.\nZH: 域外管辖意味着非英国企业的英国母公司也可能因贿赂腐败被起诉。\n\n[v7u_N000138|138] Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts.\nZH: FullTechGlobal 在高风险司法管辖区战略性地雇佣中间人获取合同。\n\n[v7u_N000139|139] According to the allegations and further investigative efforts, it appeared the subsidiary was systematically obscuring illicit financial flows through inflated consultancy fees, fabricated invoicing practices, and opaque shell companies.\nZH: 子公司通过虚增咨询费、伪造发票和壳公司掩盖非法资金流动。\n\n[v7u_N000140|140] Additionally, evidence suggested that FullTechGlobal provided sophisticated inducements, including lavish gifts and premium travel arrangements to public officials and high-ranking executives to unlawfully influence decision-making processes.\nZH: FullTechGlobal 向公职人员和高级管理人员提供奢华礼品和旅行安排以影响决策。\n\n[v7u_N000141|141] She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities.\nZH: FullTechGlobal腐败案审计发现内部控制缺陷和监管不足\n\n[v7u_N000142|142] Bribery was identified as the predicate crime, leading to the laundering of illicit funds through complex financial networks designed to evade regulatory scrutiny and forensic tracing efforts.\nZH: 贿赂作为上游犯罪，通过复杂金融网络洗钱\n\n[v7u_N000143|143] Given these findings, the regulatory implications under the UK Bribery Act 2010 are profound. FullTechGlobal Services faces severe financial penalties, increased scrutiny from international regulators, and potential criminal liability for both the subsidiary and the parent company, including its executives.\nZH: FullTechGlobal面临英国《反贿赂法》下的严厉处罚和监管审查\n\n[v7u_N000144|144] As an AFC manager, she recognizes that her institution needs to maintain compliance integrity and mitigate bribery and corruption risks in its dealings with global businesses such as FullTechGlobal Services.\nZH: 金融犯罪防控经理有义务维护合规诚信并降低贿赂风险",
  "allowed_unit_ids": [
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
  ],
  "original_json": {
    "section_id": "CH02-S04",
    "section_title": "Types of financial crime > Case example: FullTechGlobal corruption scandal",
    "coverage_audit": [
      {
        "candidate_id": "cand_001",
        "unit_ids": [
          "v7u_N000132",
          "v7u_N000134",
          "v7u_N000138"
        ],
        "proposition": "负面新闻引发对英国反贿赂法的关切，导致Sophie进行初始调查",
        "decision": "kg_only",
        "card_id": null,
        "reason": "原文未明确负面新闻和调查之间的触发关系，仅为叙述顺序，无法可靠构建有向边。"
      },
      {
        "candidate_id": "cand_002",
        "unit_ids": [
          "v7u_N000138",
          "v7u_N000139",
          "v7u_N000140"
        ],
        "proposition": "Sophie的初始调查揭示了FullTechGlobal的腐败方法（雇佣中间人、掩盖资金流、提供贿赂）",
        "decision": "p7c_card",
        "card_id": "p7card_CH02-S04_001",
        "reason": "调查动作与发现之间存在明确有向产出关系，超出基础KG单纯事实存储，属于可帮助选项判断的程序性结构。"
      },
      {
        "candidate_id": "cand_003",
        "unit_ids": [
          "v7u_N000141"
        ],
        "proposition": "Sophie的审计识别出FullTechGlobal的ABC框架和内部控制缺陷",
        "decision": "p7c_card",
        "card_id": "p7card_CH02-S04_002",
        "reason": "审计动作与结论之间存在显式有向产出关系，超出基础KG风险指标陈述，属于增量判断结构。"
      },
      {
        "candidate_id": "cand_004",
        "unit_ids": [
          "v7u_N000141",
          "v7u_N000142"
        ],
        "proposition": "审计发现缺陷导致识别贿赂为上游犯罪",
        "decision": "kg_only",
        "card_id": null,
        "reason": "缺乏显式连接，仅为叙述顺序，且被动语态无明确动作主体。"
      },
      {
        "candidate_id": "cand_005",
        "unit_ids": [
          "v7u_N000142"
        ],
        "proposition": "贿赂作为上游犯罪导致洗钱",
        "decision": "kg_only",
        "card_id": null,
        "reason": "普通因果解释，无程序性有向结构，基础KG可表达。"
      },
      {
        "candidate_id": "cand_006",
        "unit_ids": [
          "v7u_N000132",
          "v7u_N000133"
        ],
        "proposition": "负面新闻充当风险指标触发后续行动",
        "decision": "kg_only",
        "card_id": null,
        "reason": "未明确触发机制，仅为背景信息，基础KG已覆盖为风险指标。"
      },
      {
        "candidate_id": "cand_007",
        "unit_ids": [
          "v7u_N000143"
        ],
        "proposition": "FullTechGlobal面临严厉处罚和监管审查",
        "decision": "kg_only",
        "card_id": null,
        "reason": "法律后果陈述，无程序性有向结构。"
      },
      {
        "candidate_id": "cand_008",
        "unit_ids": [
          "v7u_N000144"
        ],
        "proposition": "Sophie认识到机构需维护诚信和降低风险",
        "decision": "kg_only",
        "card_id": null,
        "reason": "仅为认识/一般义务陈述，无具体动作或结果。"
      }
    ],
    "cards": [
      {
        "card_id": "p7card_CH02-S04_001",
        "section_id": "CH02-S04",
        "card_nature": "assessment",
        "title": "Sophie初始调查揭示FullTechGlobal腐败方法",
        "flow_nodes": [
          {
            "node_id": "P1",
            "node_category": "process",
            "node_type": "P1_assessment",
            "label": "Sophie进行初始调查",
            "evidence_unit_ids": [
              "v7u_N000138",
              "v7u_N000139",
              "v7u_N000140"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "X1",
            "node_category": "exit",
            "node_type": "X1_classification",
            "label": "识别出FullTechGlobal在高风险司法管辖区战略雇佣中间人",
            "evidence_unit_ids": [
              "v7u_N000138"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "X2",
            "node_category": "exit",
            "node_type": "X1_classification",
            "label": "识别出FullTechGlobal通过虚增咨询费、伪造发票和壳公司掩盖非法资金流",
            "evidence_unit_ids": [
              "v7u_N000139"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "X3",
            "node_category": "exit",
            "node_type": "X1_classification",
            "label": "识别出FullTechGlobal向公职人员提供奢华礼品和旅行安排",
            "evidence_unit_ids": [
              "v7u_N000140"
            ],
            "evidence_strength": "explicit"
          }
        ],
        "flow_edges": [
          {
            "edge_id": "E1",
            "edge_type": "PRODUCES",
            "source": "P1",
            "target": "X1",
            "evidence_unit_ids": [
              "v7u_N000138"
            ],
            "derivation": "explicit_text"
          },
          {
            "edge_id": "E2",
            "edge_type": "PRODUCES",
            "source": "P1",
            "target": "X2",
            "evidence_unit_ids": [
              "v7u_N000139"
            ],
            "derivation": "explicit_text"
          },
          {
            "edge_id": "E3",
            "edge_type": "PRODUCES",
            "source": "P1",
            "target": "X3",
            "evidence_unit_ids": [
              "v7u_N000140"
            ],
            "derivation": "explicit_text"
          }
        ],
        "source_unit_ids": [
          "v7u_N000138",
          "v7u_N000139",
          "v7u_N000140"
        ],
        "candidate_status": "candidate",
        "review_notes": "增量命题：Sophie的初始调查（PRODUCES）识别出FullTechGlobal的腐败方法（雇佣中间人、掩盖资金流、提供贿赂）；KG不足：基础KG仅存储为案件事实，未表达调查动作与发现之间的有向程序关系；选项判断：可确认Sophie初始调查产生的具体发现；LLM推理：无。"
      },
      {
        "card_id": "p7card_CH02-S04_002",
        "section_id": "CH02-S04",
        "card_nature": "assessment",
        "title": "Sophie审计识别FullTechGlobal内部控制缺陷",
        "flow_nodes": [
          {
            "node_id": "P1",
            "node_category": "process",
            "node_type": "P1_assessment",
            "label": "Sophie跟进调查并进行审查/审计",
            "evidence_unit_ids": [
              "v7u_N000141"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "X1",
            "node_category": "exit",
            "node_type": "X1_classification",
            "label": "识别出FullTechGlobal的ABC框架和内部控制缺陷以及监管不足",
            "evidence_unit_ids": [
              "v7u_N000141"
            ],
            "evidence_strength": "explicit"
          }
        ],
        "flow_edges": [
          {
            "edge_id": "E1",
            "edge_type": "PRODUCES",
            "source": "P1",
            "target": "X1",
            "evidence_unit_ids": [
              "v7u_N000141"
            ],
            "derivation": "explicit_text"
          }
        ],
        "source_unit_ids": [
          "v7u_N000141"
        ],
        "candidate_status": "candidate",
        "review_notes": "增量命题：Sophie的审查/审计（PRODUCES）识别出FullTechGlobal内部控制缺陷；KG不足：基础KG仅标记为风险指标，未表达审计动作与发现之间的有向关系；选项判断：可确认审计产生的具体结论；LLM推理：无。"
      }
    ],
    "skip_reason": null
  },
  "gap_claims": [
    {
      "claim_id": "claim_003",
      "unit_ids": [
        "v7u_N000139"
      ],
      "proposition": "Sophie的初始调查（根据指控和进一步调查努力）似乎显示子公司通过虚增咨询费、伪造发票和壳公司掩盖非法资金流",
      "kg_boundary": "p7_incremental",
      "coverage_status": "partially_covered",
      "matched_card_ids": [
        "p7card_CH02-S04_001"
      ],
      "missing_part": "节点X2和边E2未保留原文限定词'appeared'及输入条件'根据指控和进一步调查努力'，将可能性发现表述为确定性结论。",
      "condition": "根据指控和进一步调查努力",
      "qualifier": "appeared",
      "reason": "P7C硬门槛满足（调查动作→发现），但已有card遗漏了不确定性限定词，影响选项判断的准确度，故部分覆盖。"
    },
    {
      "claim_id": "claim_004",
      "unit_ids": [
        "v7u_N000140"
      ],
      "proposition": "Sophie的初始调查（证据表明）发现FullTechGlobal向公职人员和高管提供奢华礼品和旅行安排以非法影响决策",
      "kg_boundary": "p7_incremental",
      "coverage_status": "partially_covered",
      "matched_card_ids": [
        "p7card_CH02-S04_001"
      ],
      "missing_part": "节点X3和边E3未保留原文限定词'suggested'，将可能性发现表述为确定性结论。",
      "condition": "证据表明",
      "qualifier": "suggested",
      "reason": "P7C硬门槛满足，但已有card遗漏了情态限定，导致覆盖不完全。"
    }
  ]
}
```
