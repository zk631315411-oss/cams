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

## 调用输入

```json
{
  "section_id": "CH06-S10",
  "section_title": "Money Laundering Risks in Financial Services > Control and ownership for AML compliance",
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
  },
  "gap_claims": [
    {
      "claim_id": "claim_004",
      "unit_ids": [
        "v7u_N000494",
        "v7u_N000495"
      ],
      "proposition": "在识别UBO时，直接和间接持股比例被合计后与法定阈值比较，持股比例达到阈值者被认定为UBO，未达到者不被认定。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "partially_covered",
      "matched_card_ids": [
        "p7card_CH06-S10_001"
      ],
      "missing_part": "缺少将持股合计与阈值比较并产生认定/不认定UBO结果的过程，即缺少分类结果节点和比较边。",
      "condition": null,
      "qualifier": null,
      "reason": "原文通过示例展示了合计持股并比较阈值后明确认定或不认定UBO的判断结构，构成计算-比较-分类的有向命题，KG仅能保存案例事实，无法表达此判断过程。已有卡片001覆盖了输入和标准，但缺失结果出口，故部分覆盖。"
    }
  ]
}
```
