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
  "section_id": "CH06-S09",
  "section_title": "Money Laundering Risks in Financial Services > Politically exposed person risks",
  "base_kg_section_summary": {
    "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
    "covered_topics": [
      {
        "title_zh": "政治敏感人物的定义、范围和关联人",
        "title_en": "PEP definition, scope, and related persons",
        "covered_units": [
          {
            "unit_id": "v7u_N000457",
            "unit_type": "definition",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N000469",
            "unit_type": "fact",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N000470",
            "unit_type": "fact",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N000473",
            "unit_type": "fact",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N000474",
            "unit_type": "fact",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N000475",
            "unit_type": "fact",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N000467",
            "unit_type": "rule",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000468",
            "unit_type": "classification",
            "kg_role": "provides_context"
          },
          {
            "unit_id": "v7u_N000471",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000472",
            "unit_type": "classification",
            "kg_role": "provides_context"
          }
        ]
      },
      {
        "title_zh": "政治敏感人物识别挑战与合规要求",
        "title_en": "PEP Identification Challenges and Compliance",
        "covered_units": [
          {
            "unit_id": "v7u_N000458",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000459",
            "unit_type": "rule",
            "kg_role": "states_rule"
          },
          {
            "unit_id": "v7u_N000460",
            "unit_type": "rule",
            "kg_role": "explains"
          }
        ]
      },
      {
        "title_zh": "FATF对政治敏感人物的分类",
        "title_en": "FATF Classification of PEP Types",
        "covered_units": [
          {
            "unit_id": "v7u_N000462",
            "unit_type": "fact",
            "kg_role": "classifies"
          },
          {
            "unit_id": "v7u_N000463",
            "unit_type": "fact",
            "kg_role": "classifies"
          },
          {
            "unit_id": "v7u_N000464",
            "unit_type": "fact",
            "kg_role": "classifies"
          },
          {
            "unit_id": "v7u_N000461",
            "unit_type": "classification",
            "kg_role": "provides_context"
          }
        ]
      },
      {
        "title_zh": "政治敏感人物的腐败风险与示例",
        "title_en": "PEP Vulnerability to Corruption and Examples",
        "covered_units": [
          {
            "unit_id": "v7u_N000465",
            "unit_type": "fact",
            "kg_role": "indicates_risk"
          },
          {
            "unit_id": "v7u_N000466",
            "unit_type": "case",
            "kg_role": "illustrates"
          }
        ]
      },
      {
        "title_zh": "政治敏感人物风险管理与监控方法",
        "title_en": "PEP Risk Management and Monitoring Approaches",
        "covered_units": [
          {
            "unit_id": "v7u_N000476",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000477",
            "unit_type": "rule",
            "kg_role": "illustrates"
          },
          {
            "unit_id": "v7u_N000481",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000482",
            "unit_type": "rule",
            "kg_role": "prescribes_measure"
          },
          {
            "unit_id": "v7u_N000479",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000478",
            "unit_type": "classification",
            "kg_role": "provides_context"
          },
          {
            "unit_id": "v7u_N000480",
            "unit_type": "rule",
            "kg_role": "explains"
          }
        ]
      }
    ],
    "covered_relations": [
      {
        "source_title": "政治敏感人物的定义、范围和关联人",
        "target_title": "FATF对政治敏感人物的分类",
        "relation_type": "prepares"
      },
      {
        "source_title": "政治敏感人物的定义、范围和关联人",
        "target_title": "政治敏感人物的腐败风险与示例",
        "relation_type": "prepares"
      },
      {
        "source_title": "政治敏感人物的定义、范围和关联人",
        "target_title": "政治敏感人物风险管理与监控方法",
        "relation_type": "prepares"
      },
      {
        "source_title": "政治敏感人物识别挑战与合规要求",
        "target_title": "政治敏感人物风险管理与监控方法",
        "relation_type": "prepares"
      },
      {
        "source_title": "FATF对政治敏感人物的分类",
        "target_title": "政治敏感人物的腐败风险与示例",
        "relation_type": "prepares"
      },
      {
        "source_title": "政治敏感人物的腐败风险与示例",
        "target_title": "政治敏感人物风险管理与监控方法",
        "relation_type": "prepares"
      }
    ]
  },
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
  }
}
```
