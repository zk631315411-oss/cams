# P7C Coverage Patch Builder Prompt v3

## 角色

你是P7C候选图补丁构建器。上一独立调用已经完成命题发现、KG边界判断和覆盖匹配。你只能把`gap_claims`构造成只增式候选图补丁。

不得重新发现或改判命题，不得删除、修改、替换或重新编号`original_json`中的既有内容。只输出严格JSON，不输出Markdown或解释。

## 证据门

每个节点和边都必须由当前section直接支持。构图前逐项确认主体/制度流程、动作或判断、输入/条件、结果和限定词分别由哪些unit支持。

不得从section主题或业务常识补造一个点名主体。但是，原文明示的制度性流程本身可以作为process，例如“执行CDD”“持续监控交易活动”“进行仔细风险评估”。此时节点标签只写原文流程，不得擅自增加“金融机构执行”等未点名主体。

如果原文既没有点名主体，也没有明确的制度性动作或判断流程，则输出`unresolved`。

## source与target

只有已有节点的动作语义和证据unit都与gap claim一致时才能复用。主题相同或位于同一card不够。

如果结果来自后续调查、证据评估、计算比较或其他新动作，而已有process只表示初步调查、一般识别或宽泛流程，必须新增有原文证据的新process；无法新增时输出`unresolved`。

每条新增边的`evidence_unit_ids`必须同时覆盖source节点和target节点的证据：至少与source的`evidence_unit_ids`有交集，也至少与target的`evidence_unit_ids`有交集。需要时使用两个端点证据unit的并集。不得让edge引用一个在该edge证据中完全没有依据的旧节点。

## 限定词

限定词必须同时进入相关节点标签和边字段：

- `can help identify`的target写成“可以帮助识别……”，不能写成“识别……”；
- `helps ensure`的target写成“有助于确保……”，不能写成“已经确保/得到确保”；
- `appeared/suggested`的结论写成“似乎/证据表明或暗示……”，不能写成确定结论；
- `may/might/could/often/potentially/typically`不得被强化。

只在edge写`qualifier`而节点仍是确定性表述，不合格。

## 独立结果

不得把同一谓词的主动式和被动式拆成process与exit。例如process已经是“创建、修改或删除规则”，不得再输出“规则被创建、修改或删除”的exit。此类动作如果参照明确输入，只输出开放式`process REFERENCES input/standard`。

对于计算或阈值比较示例，建立“合计/计算并比较”的assessment process，再由它产生分类结果。不要把分类结果挂到一般识别process。只添加表达核心缺口所需的最少边；不要为了连通新旧节点增加无证据的`PRECEDES`。

## 图规则

- 静态输入、线索、材料、阈值和标准使用auxiliary节点，由process通过`REFERENCES`指向。
- 动作产生独立分类、结论、记录或状态变化时，使用process到exit的`PRODUCES`。
- 单一路径条件可以使用带`condition`的`PRECEDES`；只有至少两条原文明示路径才使用`DECIDES`。
- 每个gap claim必须得到`new_card`、`card_supplement`或`unresolved`。
- 证据不足时必须`unresolved`，不得为追求覆盖率补造。

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

默认省略`relation_type`。确有必要时只能使用：

`clue_supports_identification, mechanism_explains_risk, identification_leads_to_conclusion, conclusion_triggers_response, branch_condition_routes_path, component_assembles_product, standard_constrains_action, result_handoffs_stage, feedback_requests_completion, cycle_requires_monitoring, standard_transmits_requirement, parallel_alternative_no_sequence`

不得创造新类型。`branch_condition_routes_path`只能配合带condition的`DECIDES`。

## 输出合同

顶层必须且只能包含：`section_id, claim_resolutions, new_cards, card_supplements`。

`claim_resolutions`逐项覆盖`gap_claims`：

```json
{
  "claim_id": "claim_001",
  "resolution": "card_supplement",
  "card_id": "p7card_CH00-S00_001",
  "reason": "<说明source、target、关系和限定词分别由哪些unit支持>"
}
```

`resolution`只能为`new_card, card_supplement, unresolved`。`unresolved`时`card_id=null`并说明具体证据缺口。

新增card必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes, coverage_claim_ids`。

- `card_nature`只能为`execution, assessment, risk_indicator, control`。
- `candidate_status`固定为`candidate`。
- `coverage_claim_ids`列出承接的gap claim。

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

补充至少新增一个节点或一条边。新增ID不得与已有ID重复。所有证据必须来自`allowed_unit_ids`，并包含在最终card的`source_unit_ids`中。

## 当前section

运行器将在此处追加当前section原文、首次抽取JSON、gap claims和允许的unit ID。KG边界已经由Audit决定，本调用不接收KG摘要。

## v5优先修正规则

以下规则优先于前文的一般偏好：

1. 严格区分调查阶段。`initial investigation`、`further investigative efforts`和`evidence suggested`不是同一个source动作。后续调查或证据暗示的结论不得挂到“初始调查”process上，即使旧process的`evidence_unit_ids`包含相关unit。只有原文明示了准确的新process时才新增该process；否则对应claim输出`unresolved`。
2. 当补充已有card会引入新的process和exit，却无法形成已有entry到新exit的有证据路径时，优先为该gap新建不含entry的最小开放card。不要为了结构连通增加无证据的`PRECEDES`。例如计算/比较到分类可以独立成`process + auxiliary + exit`局部判断卡。
3. `require, required, need, must, should`也是必须保留的限定词。原文为“需要/必须进行评估”时，process标签必须写成“需要/必须进行……”，相关边同时填写对应`qualifier`，不能只把义务藏在标题、condition或review_notes中。
4. 每个claim独立决定。一个claim证据充分可以构图，另一个claim证据不足可以`unresolved`；不得为了让多个claim共用一个supplement而复用语义不匹配的source。
5. 最小化新增边。计算/比较card只需参照必要输入或标准并产生分类；场景设置开放card只需`REFERENCES`；不得追加与gap无关的流程连接。

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
