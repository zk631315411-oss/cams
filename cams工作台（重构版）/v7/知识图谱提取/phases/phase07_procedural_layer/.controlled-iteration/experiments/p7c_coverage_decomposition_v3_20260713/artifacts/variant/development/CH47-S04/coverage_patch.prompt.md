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
  "section_id": "CH47-S04",
  "section_title": "Transaction monitoring > Transaction monitoring system tuning",
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
  },
  "gap_claims": [
    {
      "claim_id": "claim_008",
      "unit_ids": [
        "v7u_N003279"
      ],
      "proposition": "基于以往可疑活动和实际事件经验创建、修改或移除检测规则和场景",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "缺少card表达场景设置动作参照可疑活动经验和实际事件作为输入依据。需要创建边连接经验（输入）和动作节点。",
      "condition": null,
      "qualifier": null,
      "reason": "场景设置动作（创建/修改/移除检测规则）明确参照可疑活动经验和实际事件作为输入依据，构成有向参照关系，可判断选项中场景设置的依据；基础KG不能表达此细粒度输入关系，属于P7C开放关系。"
    }
  ]
}
```
