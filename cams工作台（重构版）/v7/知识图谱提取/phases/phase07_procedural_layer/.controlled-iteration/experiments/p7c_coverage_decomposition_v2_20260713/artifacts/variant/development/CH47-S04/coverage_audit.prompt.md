# P7C Proposition-Level Coverage Audit Prompt v2

## 角色

你是P7C命题级覆盖审查器。首次抽取器已经输出`original_json`，但它可能漏掉命题、把P7C关系误判为KG内容，或只覆盖主题而没有完整表达方向、条件、限定词和结果。

本调用只建立覆盖命题台账，不生成card、flow_node或flow_edge。只输出严格JSON，不输出Markdown或解释。

## P7C边界

基础KG能够表达定义、分类、事实、普通案例、孤立风险指标、一般规则、控制措施、普通控制效果、普通机制因果、组成关系和普通知识点关系。

P7C只增量表达对CAMS选项判断有用的局部有向命题：业务情境、事件、线索、输入或标准如何关联到反洗钱、反金融犯罪、合规、监管、FIU或执法主体及其控制流程的识别、评估、决策或应对，以及在相应条件下产生的独立结论、记录、分类、状态变化、分支或后续行动。

## P7C命题硬门槛

命题必须同时通过四项，才能标记为`p7_incremental`：

1. 至少存在一个反洗钱/合规/监管/调查主体的操作性动作或判断，或者一个明确的制度性控制流程动作。
2. 该动作或判断与另一个语义节点之间存在原文明示的输入参照、标准约束、条件触发、判断结果、独立产出或后续应对关系。
3. 这条关系能够判断选项中的主体、条件、方向、限定词、分类结果、应对或适用范围。
4. 基础KG即使保存整句话或各个事实，仍不能充分表达上述细粒度有向结构。

只有一个动作节点而没有第二个语义节点和可靠关系，不得进入P7C。只有主题相关性、教材相邻顺序或推测出的业务常识，不得进入P7C。

## 必须交给KG的内容

以下即使语法上含有因果词、情态词或动作词，通常仍为`kg_only`：

- 产品、工具、犯罪手法或组织特征导致、增加或掩盖风险的一般机制；
- “某控制可以降低风险、帮助管理风险、提高效率、防范犯罪”等普通控制效果；
- 普通案例事实、犯罪操作步骤、调查困难、当局受到阻碍，但没有由此形成判断、应对、分支或程序结果；
- 总结性倡议、抽象义务或“应维护诚信、持续更新、理解风险很重要”等表述，但原文没有明确连接其输入、条件、标准或独立结果；
- 定义、分类、阈值数字、组成列表、孤立红旗和一般法律后果。

不得把“当局调查时常受腐败官员阻碍”包装成“调查产生受阻状态”；这是调查困难和犯罪机制，由KG承接。

不得把“控制可以降低风险”自动包装成`process PRODUCES 风险降低`。只有具体识别、评估、核实、分类或监控动作产生原文明示且可单独判断的结果时，才可能属于P7C。例如“CDD有助于确保客户按照预期和历史交易模式正确细分”包含具体评估动作、参照维度和限定性分类结果，不是抽象的风险降低口号。

## 两类不得漏掉的开放或示例关系

1. 原文以`based on, according to, using, considering, require`等形式说明制度性动作明确参照输入、经验、线索、阈值或标准时，即使没有独立出口，也属于可审查的P7C开放关系。例如“创建、修改或删除检测规则时基于历史可疑活动和实际事件经验”应登记为动作参照经验，而不能仅因该句位于定义段落就交给KG。
2. 原文给出计算或比较过程，并明确导向相反的分类结果时，案例事实由KG保存，但“计算输入→比较阈值→分类”的判断结构属于P7C。例如合计直接和间接持股后明确认定或不认定UBO，应分别检查分类出口是否进入图。

## 审查方法

按自然段落、unit、转折、主体、对象和条件变化完整扫描section。先写出完整命题，再依次执行硬门槛、KG排除项和覆盖比较。

不得因为已有card标题相近、节点含有相同主题词，或者某个主题已经成卡，就认定命题已经覆盖。对每个P7C命题逐项比较：

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
  "reason": "<必须说明四项硬门槛如何满足，或为何由KG承接>"
}
```

约束：

- `kg_boundary`只能是`kg_only`或`p7_incremental`。
- `kg_only`必须使用`coverage_status=not_applicable`，`matched_card_ids=[]`，`missing_part=null`。
- `p7_incremental + covered`必须至少匹配一张已有card，且`missing_part=null`。
- `p7_incremental + partially_covered`必须至少匹配一张已有card，并具体填写`missing_part`。
- `p7_incremental + missing`必须具体填写`missing_part`；`matched_card_ids`可以为空。
- 只能引用`allowed_unit_ids`和`original_json.cards`中存在的card ID。
- `scan_summary`用一句中文说明扫描范围、P7C缺口数量和KG排除数量。

## 当前section

运行器将在此处追加当前section原文、KG摘要、首次抽取JSON和允许的unit ID。

## 调用输入

```json
{
  "section_id": "CH47-S04",
  "section_title": "Transaction monitoring > Transaction monitoring system tuning",
  "base_kg_section_summary": {
    "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
    "covered_topics": [
      {
        "title_zh": "交易监控系统调优：定义与重要性",
        "title_en": "TM System Tuning: Definition and Importance",
        "covered_units": [
          {
            "unit_id": "v7u_N003272",
            "unit_type": "classification",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N003273",
            "unit_type": "risk_indicator",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N003274",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N003275",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N003276",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N003277",
            "unit_type": "fact",
            "kg_role": "explains"
          }
        ]
      },
      {
        "title_zh": "调优的关键组成部分",
        "title_en": "Key Components of Tuning",
        "covered_units": [
          {
            "unit_id": "v7u_N003278",
            "unit_type": "fact",
            "kg_role": "classifies"
          },
          {
            "unit_id": "v7u_N003280",
            "unit_type": "definition",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N003284",
            "unit_type": "fact",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N003279",
            "unit_type": "definition",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N003282",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N003281",
            "unit_type": "case",
            "kg_role": "illustrates"
          },
          {
            "unit_id": "v7u_N003283",
            "unit_type": "rule",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N003285",
            "unit_type": "fact",
            "kg_role": "explains"
          }
        ]
      },
      {
        "title_zh": "动态调优要求",
        "title_en": "Dynamic Tuning Requirement",
        "covered_units": [
          {
            "unit_id": "v7u_N003286",
            "unit_type": "rule",
            "kg_role": "states_rule"
          }
        ]
      }
    ],
    "covered_relations": [
      {
        "source_title": "交易监控系统调优：定义与重要性",
        "target_title": "调优的关键组成部分",
        "relation_type": "prepares"
      },
      {
        "source_title": "调优的关键组成部分",
        "target_title": "动态调优要求",
        "relation_type": "prepares"
      }
    ]
  },
  "section_text_with_unit_anchors": "[v7u_N003272|3272] TM system tuning is the process of refining and adjusting parameters and thresholds of specific detection logic rules, or scenarios. Scenarios are designed to detect suspicious activities and abnormal transaction behaviors, such as money laundering, fraud, or other illicit activities. Tuning is important because it:\nZH: 交易监控系统调优是调整检测规则参数和阈值的过程。\n\n[v7u_N003273|3273] Ensures the TM system effectively detects suspicious activity.\nZH: 调优确保交易监控系统有效检测可疑活动。\n\n[v7u_N003274|3274] Reduces false positives.\nZH: 调优减少误报。\n\n[v7u_N003275|3275] Ensures efficient resource use.\nZH: 调优确保资源高效利用。\n\n[v7u_N003276|3276] Allows organizations to manage changes in financial crime and in their business operations.\nZH: 调优使组织能够应对金融犯罪和业务运营的变化。\n\n[v7u_N003277|3277] Ensures regulatory compliance.\nZH: 调优确保监管合规。\n\n[v7u_N003278|3278] Tuning involves four key components: scenario setting, customer segmentation, threshold setting, and frequency.\nZH: 调优包括场景设置、客户细分、阈值设置和频率四个关键组成部分。\n\n[v7u_N003279|3279] Scenario setting involves creating, modifying, or removing detection rules and scenarios based on previous experiences with suspicious activity and actual incidents.\nZH: 场景设置是基于以往经验创建、修改或移除检测规则和场景。\n\n[v7u_N003280|3280] Threshold setting defines the minimum level of activity required for a transaction to trigger an alert.\nZH: 阈值设置定义了触发警报所需的最低活动水平。\n\n[v7u_N003281|3281] For example, the threshold for reporting a CTR might be any currency transaction that exceeds US$10,000.\nZH: 货币交易报告（CTR）阈值示例：超过10,000美元的任何货币交易\n\n[v7u_N003282|3282] Adjusting thresholds refines sensitivity and accuracy.\nZH: 调整阈值可提高交易监控系统的灵敏度和准确性\n\n[v7u_N003283|3283] Reducing the number of false positives is a key goal in setting thresholds to make the most efficient use of resources.\nZH: 减少误报是设定阈值的关键目标，以高效利用资源\n\n[v7u_N003284|3284] The frequency determines how often tuning should occur.\nZH: 调优频率决定了交易监控系统应多久进行一次调整\n\n[v7u_N003285|3285] The frequency might also be influenced by changes in business strategy, anomalies, regulatory updates, or market changes.\nZH: 调优频率受业务策略变化、异常、监管更新或市场变化影响\n\n[v7u_N003286|3286] Tuning should be dynamic, with special assessments triggered by significant events or trends.\nZH: 调优应是动态的，重大事件或趋势应触发专项评估",
  "allowed_unit_ids": [
    "v7u_N003272",
    "v7u_N003273",
    "v7u_N003274",
    "v7u_N003275",
    "v7u_N003276",
    "v7u_N003277",
    "v7u_N003278",
    "v7u_N003279",
    "v7u_N003280",
    "v7u_N003281",
    "v7u_N003282",
    "v7u_N003283",
    "v7u_N003284",
    "v7u_N003285",
    "v7u_N003286"
  ],
  "original_json": {
    "section_id": "CH47-S04",
    "section_title": "Transaction monitoring > Transaction monitoring system tuning",
    "coverage_audit": [
      {
        "candidate_id": "cand_001",
        "unit_ids": [
          "v7u_N003272"
        ],
        "proposition": "交易监控系统调优是调整检测规则参数和阈值的过程（定义）",
        "decision": "kg_only",
        "card_id": null,
        "reason": "基础KG可充分表达定义。"
      },
      {
        "candidate_id": "cand_002",
        "unit_ids": [
          "v7u_N003273"
        ],
        "proposition": "调优确保有效检测可疑活动（重要性）",
        "decision": "kg_only",
        "card_id": null,
        "reason": "一般因果关系，基础KG可表达。"
      },
      {
        "candidate_id": "cand_003",
        "unit_ids": [
          "v7u_N003274"
        ],
        "proposition": "调优减少误报（重要性）",
        "decision": "kg_only",
        "card_id": null,
        "reason": "一般因果关系，基础KG可表达。"
      },
      {
        "candidate_id": "cand_004",
        "unit_ids": [
          "v7u_N003275"
        ],
        "proposition": "调优确保资源高效利用（重要性）",
        "decision": "kg_only",
        "card_id": null,
        "reason": "一般因果关系，基础KG可表达。"
      },
      {
        "candidate_id": "cand_005",
        "unit_ids": [
          "v7u_N003276"
        ],
        "proposition": "调优允许组织应对金融犯罪和业务运营的变化（重要性）",
        "decision": "kg_only",
        "card_id": null,
        "reason": "一般描述，基础KG可表达。"
      },
      {
        "candidate_id": "cand_006",
        "unit_ids": [
          "v7u_N003277"
        ],
        "proposition": "调优确保监管合规（重要性）",
        "decision": "kg_only",
        "card_id": null,
        "reason": "一般结果，基础KG可表达。"
      },
      {
        "candidate_id": "cand_007",
        "unit_ids": [
          "v7u_N003278"
        ],
        "proposition": "调优包括场景设置、客户细分、阈值设置和频率四个关键组成部分（分类）",
        "decision": "kg_only",
        "card_id": null,
        "reason": "组成部分列表，基础KG可表达。"
      },
      {
        "candidate_id": "cand_008",
        "unit_ids": [
          "v7u_N003279"
        ],
        "proposition": "场景设置基于以往可疑活动和实际事件经验创建、修改或移除检测规则和场景",
        "decision": "kg_only",
        "card_id": null,
        "reason": "方法说明，无独立结果，基础KG可保存此事实。"
      },
      {
        "candidate_id": "cand_009",
        "unit_ids": [
          "v7u_N003280"
        ],
        "proposition": "阈值设置定义了触发警报所需的最低活动水平（定义）",
        "decision": "kg_only",
        "card_id": null,
        "reason": "定义说明，基础KG可表达。"
      },
      {
        "candidate_id": "cand_010",
        "unit_ids": [
          "v7u_N003281"
        ],
        "proposition": "CTR报告阈值示例：超过10,000美元触发报告",
        "decision": "kg_only",
        "card_id": null,
        "reason": "普通案例示例，基础KG可表达。"
      },
      {
        "candidate_id": "cand_011",
        "unit_ids": [
          "v7u_N003282"
        ],
        "proposition": "调整阈值可提高交易监控系统的灵敏度和准确性",
        "decision": "kg_only",
        "card_id": null,
        "reason": "一般效果说明，无独立结构，基础KG可表达。"
      },
      {
        "candidate_id": "cand_012",
        "unit_ids": [
          "v7u_N003283"
        ],
        "proposition": "减少误报是设定阈值的关键目标",
        "decision": "kg_only",
        "card_id": null,
        "reason": "目标陈述，基础KG可表达。"
      },
      {
        "candidate_id": "cand_013",
        "unit_ids": [
          "v7u_N003284"
        ],
        "proposition": "频率决定了交易监控系统应多久进行一次调优（定义）",
        "decision": "kg_only",
        "card_id": null,
        "reason": "组成部分定义，基础KG可表达。"
      },
      {
        "candidate_id": "cand_014",
        "unit_ids": [
          "v7u_N003285"
        ],
        "proposition": "调优频率可能受业务策略变化、异常、监管更新或市场变化影响",
        "decision": "kg_only",
        "card_id": null,
        "reason": "影响因素列举，基础KG可表达。"
      },
      {
        "candidate_id": "cand_015",
        "unit_ids": [
          "v7u_N003286"
        ],
        "proposition": "重大事件或趋势应触发专项评估（动态调优）",
        "decision": "p7c_card",
        "card_id": "p7card_CH47-S04_001",
        "reason": "明确的条件触发关系：重大事件或趋势触发机构应进行的专项评估，构成局部程序性有向结构，基础KG不能充分表达触发逻辑。"
      }
    ],
    "cards": [
      {
        "card_id": "p7card_CH47-S04_001",
        "section_id": "CH47-S04",
        "card_nature": "control",
        "title": "动态调优触发专项评估",
        "flow_nodes": [
          {
            "node_id": "E6_001",
            "node_category": "entry",
            "node_type": "E6_change_exception",
            "label": "重大事件或趋势发生",
            "evidence_unit_ids": [
              "v7u_N003286"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "P8_001",
            "node_category": "process",
            "node_type": "P8_constrained_action",
            "label": "机构应进行专项评估（调优）",
            "evidence_unit_ids": [
              "v7u_N003286"
            ],
            "evidence_strength": "explicit"
          }
        ],
        "flow_edges": [
          {
            "edge_id": "E1",
            "edge_type": "PRECEDES",
            "source": "E6_001",
            "target": "P8_001",
            "evidence_unit_ids": [
              "v7u_N003286"
            ],
            "derivation": "explicit_text",
            "condition": "发生重大事件或趋势时",
            "source_quote": "special assessments triggered by significant events or trends"
          }
        ],
        "source_unit_ids": [
          "v7u_N003286"
        ],
        "candidate_status": "candidate",
        "review_notes": "增量命题：重大事件或趋势（E6_change_exception）触发机构应进行专项评估（P8_constrained_action）；KG不足：基础KG只能保存静态规则，不能表达条件触发关系；选项判断：可确认或排除动态调优的触发条件和应执行的动作；LLM推理：无。"
      }
    ],
    "skip_reason": null
  }
}
```
