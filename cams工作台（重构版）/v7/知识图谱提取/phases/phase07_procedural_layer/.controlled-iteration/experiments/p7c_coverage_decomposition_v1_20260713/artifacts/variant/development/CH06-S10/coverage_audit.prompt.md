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
  "section_id": "CH06-S10",
  "section_title": "Money Laundering Risks in Financial Services > Control and ownership for AML compliance",
  "base_kg_section_summary": {
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
  },
  "section_text_with_unit_anchors": "[v7u_N000483|483] Control and ownership play a vital role in AML efforts, as they can often be obscured or concealed, allowing bad actors to disguise criminal activities and facilitate financial crime.\nZH: 控制权和所有权在反洗钱工作中至关重要\n\n[v7u_N000484|484] A beneficial owner (BO) is defined as an individual or entity that possesses ownership of a legal entity, either through shareholding or other means.\nZH: 受益所有人（BO）的定义：通过持股或其他方式拥有法律实体的个人或实体\n\n[v7u_N000485|485] In contrast, the ultimate beneficial owner (UBO) refers specifically to one or more natural persons who ultimately owns a substantial percentage of shareholding.\nZH: 最终受益所有人（UBO）的定义：最终持有重大比例股份的自然人\n\n[v7u_N000486|486] It is important to note that a BO might appear to have ownership of a company but might not control the company. Conversely, a UBO might not directly hold shares but does exert ultimate control over it.\nZH: BO 可能拥有所有权但不控制公司，UBO 可能不直接持股但实施最终控制\n\n[v7u_N000487|487] This distinction is crucial when it comes to regulatory requirements surrounding ownership structures.\nZH: BO 与 UBO 的区别对所有权结构的监管要求至关重要\n\n[v7u_N000488|488] When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer.\nZH: 监管要求审查所有权结构时必须识别客户的 UBO\n\n[v7u_N000489|489] For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more. That means you need to know every entity or individual who owns at least 25% of a customer.\nZH: 多数司法管辖区要求识别持股 25% 或以上的受益所有人\n\n[v7u_N000490|490] Your organization will set the appropriate threshold using a riskbased approach.\nZH: 机构应采用风险为本的方法设定受益所有权阈值\n\n[v7u_N000491|491] For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5% for customers who pose a significantly higher risk.\nZH: 高风险客户的受益所有人阈值可能低至 10% 甚至 5%\n\n[v7u_N000492|492] For example, high-risk financial institutions with correspondent banking relationships in a high-risk jurisdiction might set their threshold at 5%.\nZH: 示例：高风险司法管辖区的代理行关系可能设定 5% 的阈值\n\n[v7u_N000493|493] In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership.\nZH: 识别 UBO 需要同时考虑直接和间接持股\n\n[v7u_N000494|494] Individual D owns 10% of Company A directly. They also own 72% of Company A indirectly, as they own 90% of shares of Company B, which owns 80% of Company A. Individual D is then considered a UBO with 82% shareholding of Company A.\nZH: 示例：个人 D 通过直接和间接持股合计 82%，成为 UBO\n\n[v7u_N000495|495] Individual C, who owns 10% of Company A directly and an additional 8% indirectly via their 10% ownership of Company B, is not a UBO.\nZH: 示例：个人 C 直接持股 10% 加间接持股 8%，未达到 UBO 标准\n\n[v7u_N000496|496] In companies where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified. This allows you to understand who is in control of the decision-making in the company when natural individual UBOs are not present.\nZH: 无自然人受益所有人时，应识别并核实控制人或名义受益所有人\n\n[v7u_N000497|497] For example, for a company that is publicly listed on the stock exchange and has thousands of shareholders, a notional beneficial owner could be the president or chief executive officer, or equivalent.\nZH: 示例：上市公司可将总裁或 CEO 作为名义受益所有人",
  "allowed_unit_ids": [
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
  ],
  "original_json": {
    "section_id": "CH06-S10",
    "section_title": "Money Laundering Risks in Financial Services > Control and ownership for AML compliance",
    "coverage_audit": [
      {
        "candidate_id": "cand_001",
        "unit_ids": [
          "v7u_N000483",
          "v7u_N000484",
          "v7u_N000485",
          "v7u_N000486",
          "v7u_N000487"
        ],
        "proposition": "控制权和所有权重要，BO和UBO有区别，区分对监管要求重要",
        "decision": "kg_only",
        "card_id": null,
        "reason": "纯定义、事实和背景知识，无程序性或判断性有向结构，基础KG已能充分表达。"
      },
      {
        "candidate_id": "cand_002",
        "unit_ids": [
          "v7u_N000488",
          "v7u_N000489",
          "v7u_N000490",
          "v7u_N000491",
          "v7u_N000493"
        ],
        "proposition": "审查所有权结构时，机构必须基于风险方法识别UBO，通常按≥25%阈值，高风险可降至10%或5%，并需考虑直接和间接持股",
        "decision": "p7c_card",
        "card_id": "p7card_CH06-S10_001",
        "reason": "KG仅能保存各规则作为整体事实，无法表达条件触发动作、风险调整标准和持股信息作为识别依据的有向关系，属于增量程序性结构。"
      },
      {
        "candidate_id": "cand_003",
        "unit_ids": [
          "v7u_N000492"
        ],
        "proposition": "高风险代理行关系可能设定5%阈值",
        "decision": "kg_only",
        "card_id": null,
        "reason": "示例，用于支持cand_002，本身不构成独立有向命题。"
      },
      {
        "candidate_id": "cand_004",
        "unit_ids": [
          "v7u_N000494",
          "v7u_N000495"
        ],
        "proposition": "间接持股计算示例",
        "decision": "kg_only",
        "card_id": null,
        "reason": "示例，说明直接和间接持股合计方法，不构成独立程序性结构。"
      },
      {
        "candidate_id": "cand_005",
        "unit_ids": [
          "v7u_N000496"
        ],
        "proposition": "无自然人UBO时，机构应识别控制人或名义受益所有人",
        "decision": "p7c_card",
        "card_id": "p7card_CH06-S10_002",
        "reason": "KG仅保存规则事实，无法表达“无自然人”条件触发替代识别动作的有向关系，属于增量程序性结构。"
      },
      {
        "candidate_id": "cand_006",
        "unit_ids": [
          "v7u_N000497"
        ],
        "proposition": "上市公司可将总裁或CEO作为名义受益所有人",
        "decision": "kg_only",
        "card_id": null,
        "reason": "示例，支持cand_005，不构成独立有向命题。"
      }
    ],
    "cards": [
      {
        "card_id": "p7card_CH06-S10_001",
        "section_id": "CH06-S10",
        "card_nature": "assessment",
        "title": "基于风险方法的UBO识别程序",
        "flow_nodes": [
          {
            "node_id": "N1",
            "node_category": "entry",
            "node_type": "E1_event_signal",
            "label": "审查客户所有权结构",
            "evidence_unit_ids": [
              "v7u_N000488"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "N2",
            "node_category": "process",
            "node_type": "P1_assessment",
            "label": "机构基于风险方法识别客户的UBO",
            "evidence_unit_ids": [
              "v7u_N000488",
              "v7u_N000490"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "N3",
            "node_category": "auxiliary",
            "node_type": "standard",
            "label": "持股阈值标准：通常25%或以上，高风险客户可低至10%甚至5%",
            "evidence_unit_ids": [
              "v7u_N000489",
              "v7u_N000491"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "N4",
            "node_category": "auxiliary",
            "node_type": "input",
            "label": "直接和间接持股信息",
            "evidence_unit_ids": [
              "v7u_N000493"
            ],
            "evidence_strength": "explicit"
          }
        ],
        "flow_edges": [
          {
            "edge_id": "E1",
            "edge_type": "PRECEDES",
            "source": "N1",
            "target": "N2",
            "evidence_unit_ids": [
              "v7u_N000488"
            ],
            "derivation": "explicit_text",
            "condition": "当审查所有权结构时",
            "source_quote": "When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer."
          },
          {
            "edge_id": "E2",
            "edge_type": "REFERENCES",
            "source": "N2",
            "target": "N3",
            "evidence_unit_ids": [
              "v7u_N000489",
              "v7u_N000490",
              "v7u_N000491"
            ],
            "derivation": "explicit_text",
            "relation_type": "standard_constrains_action"
          },
          {
            "edge_id": "E3",
            "edge_type": "REFERENCES",
            "source": "N2",
            "target": "N4",
            "evidence_unit_ids": [
              "v7u_N000493"
            ],
            "derivation": "explicit_text",
            "relation_type": "clue_supports_identification"
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
        "review_notes": "增量命题：审查所有权结构 --条件触发(PRECEDES)--> 机构基于风险方法识别客户的UBO；识别过程需参照持股阈值标准（通常25%，高风险可降至10%或5%）和直接间接持股信息。KG不足：基础KG仅能保存“需识别UBO”、“25%阈值”等孤立事实，无法表达条件触发识别动作、风险调整阈值约束识别过程、以及持股信息作为识别依据的有向关系。选项判断：可确认或排除关于识别UBO的顺序、条件、阈值适用、风险调整方法以及必须考虑间接持股等选项。LLM推理：无"
      },
      {
        "card_id": "p7card_CH06-S10_002",
        "section_id": "CH06-S10",
        "card_nature": "execution",
        "title": "无自然人UBO时的替代识别",
        "flow_nodes": [
          {
            "node_id": "N1",
            "node_category": "entry",
            "node_type": "E6_change_exception",
            "label": "公司中不存在自然人受益所有人",
            "evidence_unit_ids": [
              "v7u_N000496"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "N2",
            "node_category": "process",
            "node_type": "P2_execution",
            "label": "机构识别并核实控制人或名义受益所有人",
            "evidence_unit_ids": [
              "v7u_N000496"
            ],
            "evidence_strength": "explicit"
          }
        ],
        "flow_edges": [
          {
            "edge_id": "E1",
            "edge_type": "PRECEDES",
            "source": "N1",
            "target": "N2",
            "evidence_unit_ids": [
              "v7u_N000496"
            ],
            "derivation": "explicit_text",
            "condition": "当公司中不存在自然人受益所有人时",
            "source_quote": "In companies where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified."
          }
        ],
        "source_unit_ids": [
          "v7u_N000496"
        ],
        "candidate_status": "candidate",
        "review_notes": "增量命题：公司中不存在自然人受益所有人 --条件触发(PRECEDES)--> 机构识别并核实控制人或名义受益所有人。KG不足：KG仅能保存规则文本，无法表达“无自然人”条件触发替代识别动作的有向关系。选项判断：可帮助确定在缺少自然人UBO时的正确后续动作。LLM推理：无"
      }
    ],
    "skip_reason": null
  }
}
```
