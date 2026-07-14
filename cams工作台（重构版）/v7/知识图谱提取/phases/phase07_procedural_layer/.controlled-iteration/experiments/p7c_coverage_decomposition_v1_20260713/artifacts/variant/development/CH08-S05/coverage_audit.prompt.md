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
  "section_id": "CH08-S05",
  "section_title": "Private banking and wealth management risks > Special purpose vehicle risks",
  "base_kg_section_summary": {
    "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
    "covered_topics": [
      {
        "title_zh": "SPV定义与合法用途",
        "title_en": "SPV Definition and Legitimate Uses",
        "covered_units": [
          {
            "unit_id": "v7u_N000642",
            "unit_type": "definition",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N000643",
            "unit_type": "fact",
            "kg_role": "illustrates"
          },
          {
            "unit_id": "v7u_N000644",
            "unit_type": "fact",
            "kg_role": "illustrates"
          },
          {
            "unit_id": "v7u_N000645",
            "unit_type": "fact",
            "kg_role": "illustrates"
          }
        ]
      },
      {
        "title_zh": "SPV金融犯罪风险与红旗信号",
        "title_en": "SPV Financial Crime Risks and Red Flags",
        "covered_units": [
          {
            "unit_id": "v7u_N000646",
            "unit_type": "fact",
            "kg_role": "states_consequence"
          },
          {
            "unit_id": "v7u_N000647",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000650",
            "unit_type": "fact",
            "kg_role": "indicates_risk"
          },
          {
            "unit_id": "v7u_N000651",
            "unit_type": "fact",
            "kg_role": "indicates_risk"
          },
          {
            "unit_id": "v7u_N000652",
            "unit_type": "fact",
            "kg_role": "indicates_risk"
          },
          {
            "unit_id": "v7u_N000653",
            "unit_type": "fact",
            "kg_role": "indicates_risk"
          },
          {
            "unit_id": "v7u_N000648",
            "unit_type": "fact",
            "kg_role": "describes_process"
          },
          {
            "unit_id": "v7u_N000649",
            "unit_type": "classification",
            "kg_role": "provides_context"
          }
        ]
      },
      {
        "title_zh": "集合投资工具（PIV）定义与风险",
        "title_en": "Pooled Investment Vehicle (PIV) Definition and Risks",
        "covered_units": [
          {
            "unit_id": "v7u_N000654",
            "unit_type": "definition",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N000655",
            "unit_type": "risk_indicator",
            "kg_role": "indicates_risk"
          }
        ]
      },
      {
        "title_zh": "利用SPV和PIV的贸易洗钱",
        "title_en": "Trade-Based Money Laundering Using SPVs and PIVs",
        "covered_units": [
          {
            "unit_id": "v7u_N000656",
            "unit_type": "process",
            "kg_role": "describes_process"
          },
          {
            "unit_id": "v7u_N000657",
            "unit_type": "fact",
            "kg_role": "explains"
          }
        ]
      },
      {
        "title_zh": "强化尽职调查与客户尽职调查要求",
        "title_en": "Enhanced Due Diligence (EDD) and CDD Requirements",
        "covered_units": [
          {
            "unit_id": "v7u_N000658",
            "unit_type": "rule",
            "kg_role": "prescribes_measure"
          },
          {
            "unit_id": "v7u_N000659",
            "unit_type": "rule",
            "kg_role": "prescribes_measure"
          },
          {
            "unit_id": "v7u_N000660",
            "unit_type": "fact",
            "kg_role": "states_consequence"
          }
        ]
      }
    ],
    "covered_relations": [
      {
        "source_title": "SPV定义与合法用途",
        "target_title": "SPV金融犯罪风险与红旗信号",
        "relation_type": "contrasts"
      },
      {
        "source_title": "SPV金融犯罪风险与红旗信号",
        "target_title": "利用SPV和PIV的贸易洗钱",
        "relation_type": "prepares"
      },
      {
        "source_title": "集合投资工具（PIV）定义与风险",
        "target_title": "利用SPV和PIV的贸易洗钱",
        "relation_type": "prepares"
      },
      {
        "source_title": "SPV金融犯罪风险与红旗信号",
        "target_title": "强化尽职调查与客户尽职调查要求",
        "relation_type": "prepares"
      },
      {
        "source_title": "集合投资工具（PIV）定义与风险",
        "target_title": "强化尽职调查与客户尽职调查要求",
        "relation_type": "prepares"
      }
    ]
  },
  "section_text_with_unit_anchors": "[v7u_N000642|642] Special purpose vehicles (SPVs) are legal entities created for specific and limited purposes.\nZH: 特殊目的载体（SPV）是为特定有限目的设立的法律实体\n\n[v7u_N000643|643] SPVs can be used in mergers and acquisitions, joint ventures, real estate projects, infrastructure development, and energy projects.\nZH: SPV可用于并购、合资、房地产、基础设施和能源项目\n\n[v7u_N000644|644] SPVs can also be used to manage and protect intellectual property assets including trademarks and copyrights.\nZH: SPV可用于管理和保护知识产权资产\n\n[v7u_N000645|645] SPVs are often used in complex financial transactions and investments such as securities and asset-backed financing.\nZH: SPV常用于复杂金融交易和资产支持融资\n\n[v7u_N000646|646] There are financial crime risks associated with SPVs.\nZH: SPV存在金融犯罪风险\n\n[v7u_N000647|647] SPVs can have complex and opaque structures to disguise the true beneficial ownership.\nZH: SPV可能通过复杂不透明的结构掩盖真实受益所有人\n\n[v7u_N000648|648] SPVs might be used to obscure the source of illicit funds. Criminals layer illicit proceeds through a series of transactions via the SPVs, transferring funds to or from financial institutions. This creates a complex web of\nZH: 犯罪分子通过SPV进行一系列交易来分层非法收益，掩盖资金来源\n\n[v7u_N000649|649] There are several red flags that indicate attempts to disguise illicit funds or conduct fraudulent activities using SPVs. These include:\nZH: 列举利用SPV掩饰非法资金或欺诈活动的红旗信号信号\n\n[v7u_N000650|650] Complex ownership structures involving multiple layers of companies\nZH: 涉及多层公司的复杂所有权结构是红旗信号\n\n[v7u_N000651|651] Lack of transparency\nZH: 缺乏透明度是红旗信号\n\n[v7u_N000652|652] Unclear purpose of the SPV\nZH: SPV目的不明确是红旗信号\n\n[v7u_N000653|653] Criminals might select jurisdictions that have lenient regulatory oversight or tax-friendly environments. This enables them to hide their financial activities and minimize tax liabilities.\nZH: 犯罪分子选择监管宽松或税收优惠的司法管辖区以隐藏活动和避税\n\n[v7u_N000654|654] Pooled investment vehicles (PIVs) are small investments pooled together from a large group of investors.\nZH: 集合投资工具（PIV）是从大量投资者汇集的小额投资\n\n[v7u_N000655|655] PIVs can be used in Ponzi schemes and insider trading.\nZH: PIV可能被用于庞氏骗局和内幕交易\n\n[v7u_N000656|656] Additionally, criminals might engage in trade-based money laundering using SPVs and PIVs. Criminals manipulate trade transactions between SPVs and PIVs by deflating or inflating prices.\nZH: 犯罪分子利用SPV和PIV进行贸易洗钱，操纵交易价格\n\n[v7u_N000657|657] This process enables the movement of illicit funds while disguising it as legitimate trade activity.\nZH: 该过程将非法资金伪装成合法贸易活动进行转移\n\n[v7u_N000658|658] Financial institutions must be vigilant in conducting enhanced due diligence (EDD) on SPVs and PIVs. It is important to ensure these investments comply with CDD regulations such as the Financial Crime Enforcement Network's CDD rule.\nZH: 金融机构必须对SPV和PIV进行强化尽职调查，遵守客户尽职调查规则\n\n[v7u_N000659|659] Financial institutions must identify ultimate beneficial owners and understand the true purpose of these entities.\nZH: 金融机构必须识别最终受益所有人并了解实体真实目的\n\n[v7u_N000660|660] This will help mitigate any potential financial crime risks associated with SPVs.\nZH: 这有助于减轻与SPV相关的金融犯罪风险",
  "allowed_unit_ids": [
    "v7u_N000642",
    "v7u_N000643",
    "v7u_N000644",
    "v7u_N000645",
    "v7u_N000646",
    "v7u_N000647",
    "v7u_N000648",
    "v7u_N000649",
    "v7u_N000650",
    "v7u_N000651",
    "v7u_N000652",
    "v7u_N000653",
    "v7u_N000654",
    "v7u_N000655",
    "v7u_N000656",
    "v7u_N000657",
    "v7u_N000658",
    "v7u_N000659",
    "v7u_N000660"
  ],
  "original_json": {
    "section_id": "CH08-S05",
    "section_title": "Private banking and wealth management risks > Special purpose vehicle risks",
    "coverage_audit": [
      {
        "candidate_id": "cand_001",
        "unit_ids": [
          "v7u_N000658",
          "v7u_N000659",
          "v7u_N000660"
        ],
        "proposition": "金融机构必须对SPV和PIV进行强化尽职调查，包括识别最终受益所有人并了解真实目的，并确保遵守CDD规则，这有助于减轻金融犯罪风险。",
        "decision": "p7c_card",
        "card_id": "p7card_CH08-S05_001",
        "reason": "存在process-standard的约束关系和动作分解，基础KG难以表达EDD必须参照CDD规则的具体有向约束以及EDD内部子动作。"
      },
      {
        "candidate_id": "cand_002",
        "unit_ids": [
          "v7u_N000642",
          "v7u_N000643",
          "v7u_N000644",
          "v7u_N000645"
        ],
        "proposition": "SPV的定义与合法用途。",
        "decision": "kg_only",
        "card_id": null,
        "reason": "纯定义和事实，无程序性或判断性有向结构。"
      },
      {
        "candidate_id": "cand_003",
        "unit_ids": [
          "v7u_N000646",
          "v7u_N000647",
          "v7u_N000648",
          "v7u_N000649",
          "v7u_N000650",
          "v7u_N000651",
          "v7u_N000652",
          "v7u_N000653"
        ],
        "proposition": "SPV的金融犯罪风险、犯罪分子利用SPV的手法以及相关红旗信号。",
        "decision": "kg_only",
        "card_id": null,
        "reason": "普通风险机制、犯罪手法描述和孤立风险指标，可由基础KG表达。"
      },
      {
        "candidate_id": "cand_004",
        "unit_ids": [
          "v7u_N000654",
          "v7u_N000655"
        ],
        "proposition": "PIV的定义与庞氏骗局、内幕交易风险。",
        "decision": "kg_only",
        "card_id": null,
        "reason": "定义和风险说明，无局部有向结构。"
      },
      {
        "candidate_id": "cand_005",
        "unit_ids": [
          "v7u_N000656",
          "v7u_N000657"
        ],
        "proposition": "犯罪分子利用SPV和PIV进行贸易洗钱的手法。",
        "decision": "kg_only",
        "card_id": null,
        "reason": "犯罪过程描述，基础KG可承接。"
      }
    ],
    "cards": [
      {
        "card_id": "p7card_CH08-S05_001",
        "section_id": "CH08-S05",
        "card_nature": "execution",
        "title": "强化尽职调查（EDD）对SPV和PIV的要求",
        "flow_nodes": [
          {
            "node_id": "p7node_CH08-S05_001_input_01",
            "node_category": "auxiliary",
            "node_type": "input",
            "label": "SPVs and PIVs (特殊目的载体和集合投资工具)",
            "evidence_unit_ids": [
              "v7u_N000658"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "p7node_CH08-S05_001_process_01",
            "node_category": "process",
            "node_type": "P2_execution",
            "label": "金融机构必须对SPV和PIV进行强化尽职调查，包括识别最终受益所有人并了解真实目的",
            "evidence_unit_ids": [
              "v7u_N000658",
              "v7u_N000659"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "p7node_CH08-S05_001_standard_01",
            "node_category": "auxiliary",
            "node_type": "standard",
            "label": "CDD regulations such as the Financial Crime Enforcement Network's CDD rule (客户尽职调查规则)",
            "evidence_unit_ids": [
              "v7u_N000658"
            ],
            "evidence_strength": "explicit"
          }
        ],
        "flow_edges": [
          {
            "edge_id": "p7edge_CH08-S05_001_proc_ref_std",
            "edge_type": "REFERENCES",
            "source": "p7node_CH08-S05_001_process_01",
            "target": "p7node_CH08-S05_001_standard_01",
            "evidence_unit_ids": [
              "v7u_N000658"
            ],
            "derivation": "explicit_text",
            "relation_type": "standard_constrains_action",
            "condition": null,
            "source_quote": "It is important to ensure these investments comply with CDD regulations such as the Financial Crime Enforcement Network's CDD rule."
          },
          {
            "edge_id": "p7edge_CH08-S05_001_proc_ref_input",
            "edge_type": "REFERENCES",
            "source": "p7node_CH08-S05_001_process_01",
            "target": "p7node_CH08-S05_001_input_01",
            "evidence_unit_ids": [
              "v7u_N000658"
            ],
            "derivation": "explicit_text",
            "relation_type": null,
            "condition": null,
            "source_quote": "Financial institutions must be vigilant in conducting enhanced due diligence (EDD) on SPVs and PIVs."
          }
        ],
        "source_unit_ids": [
          "v7u_N000658",
          "v7u_N000659"
        ],
        "candidate_status": "candidate",
        "review_notes": "增量命题：金融机构必须执行EDD --REFERENCES--> CDD规则（标准约束动作），且EDD包含识别UBO和了解真实目的。KG不足：基础KG可能保存了EDD义务的一般事实，但未能表达EDD过程必须参照CDD规则的具体有向约束以及EDD内部子动作（识别UBO、了解目的）在程序上的从属关系。选项判断：可以帮助判断金融机构在EDD过程中是否必须识别UBO并遵守CDD规则，以及EDD适用的对象（SPV/PIV）。LLM推理：无。"
      }
    ],
    "skip_reason": null
  }
}
```
