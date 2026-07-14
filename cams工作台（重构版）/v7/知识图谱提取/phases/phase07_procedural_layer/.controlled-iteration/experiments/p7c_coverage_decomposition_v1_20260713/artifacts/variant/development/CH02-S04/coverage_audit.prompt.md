# P7C Proposition-Level Coverage Audit Prompt v1

## 角色

你是P7C命题级覆盖审查器。首次抽取器已经输出`original_json`，但它可能漏掉命题、把P7C关系误判为KG内容，或只覆盖主题而没有完整表达方向、条件、限定词和结果。

本调用只建立覆盖命题台账，不生成card、flow_node或flow_edge。只输出严格JSON，不输出Markdown或解释。

## P7C边界

基础KG能够表达定义、分类、事实、普通案例、孤立风险指标、一般规则、普通机制因果、组成关系和普通知识点关系。

P7C只增量表达对CAMS选项判断有用的局部有向命题：业务情境、事件、线索、输入或标准如何关联到特定主体的识别、评估、决策或应对，以及在相应条件下产生的结论、义务、控制结果、分支或后续行动。没有独立出口时，主体动作参照输入、线索或标准的开放关系也可以属于P7C。

普通案例事实仍由KG承接；但案例中原文明示的调查、识别、判断或应对如何导向带限定词的结论，可以成为P7C候选。普通犯罪手法及犯罪机制不属于P7C。

## 审查方法

按自然段落、unit、转折、主体、对象和条件变化完整扫描section。对每个可能带有方向、条件、动作约束或独立结果的命题单独登记。

必须先写出命题，再判断KG/P7边界，最后比较现有图。不得因为已有card标题相近、节点含有相同主题词，或者某个主题已经成卡，就认定命题已经覆盖。

对P7C命题逐项比较：

- 主体和动作是否存在；
- source、target和方向是否一致；
- 条件是否进入边或节点；
- `must, should, may, might, could, often, potentially, help, appeared, suggested, typically`等限定是否保留；
- 独立分类、结论、记录、状态变化或控制效果是否有节点和边；
- 开放式参照关系是否因“没有出口”而被错误跳过。

`coverage_status`判定：

- `covered`：已有card完整表达同一有向命题，包括主体、方向、条件和限定词。
- `partially_covered`：已有card只覆盖主题或部分端点，遗漏方向、条件、限定词、独立出口，或把可能性/帮助关系写成确定性结果。
- `missing`：已有card没有表达该P7C命题。
- `not_applicable`：该命题属于`kg_only`。

如果已有边写强、写反或漏掉限定词，应判为`partially_covered`，不能因为端点已经出现而判为`covered`。

## 输出合同

顶层必须且只能包含：`section_id, claims, scan_summary`。

每项claim必填：

```json
{
  "claim_id": "claim_001",
  "unit_ids": ["<当前section unit_id>"],
  "proposition": "<保留主体、方向、条件和限定词的完整中文命题>",
  "kg_boundary": "p7_incremental",
  "coverage_status": "partially_covered",
  "matched_card_ids": ["<已有card_id>"],
  "missing_part": "<具体缺少的方向、条件、限定词、节点或边；无则为null>",
  "condition": "<原文条件；无则为null>",
  "qualifier": "<原文情态或限定；无则为null>",
  "reason": "<中文边界与覆盖理由>"
}
```

约束：

- `kg_boundary`只能是`kg_only`或`p7_incremental`。
- `kg_only`必须使用`coverage_status=not_applicable`，`matched_card_ids=[]`，`missing_part=null`。
- `p7_incremental + covered`必须至少匹配一张已有card，且`missing_part=null`。
- `p7_incremental + partially_covered`必须至少匹配一张已有card，并具体填写`missing_part`。
- `p7_incremental + missing`必须具体填写`missing_part`；`matched_card_ids`可以为空。
- 只能引用`allowed_unit_ids`和`original_json.cards`中存在的card ID。
- `scan_summary`用一句中文说明扫描范围和P7C缺口数量。

## 当前section

运行器将在此处追加当前section原文、KG摘要、首次抽取JSON和允许的unit ID。

## 调用输入

```json
{
  "section_id": "CH02-S04",
  "section_title": "Types of financial crime > Case example: FullTechGlobal corruption scandal",
  "base_kg_section_summary": {
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
  },
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
  }
}
```
