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
  "section_id": "CH05-S04",
  "section_title": "Financial crime risks in relation to other types of risks > Operational, legal, concentration, and reputational risks",
  "section_text_with_unit_anchors": "[v7u_N000369|369] Key risks that organizations face include: Operational, legal, concentration, and reputational.\nZH: 组织面临的主要风险类型包括：运营风险、法律风险、集中度风险和声誉风险。\n\n[v7u_N000370|370] Operational risk is direct or indirect loss of operations due to inadequate or failed internal processes, people, or systems, or as a result of external events.\nZH: 运营风险是因内部流程、人员、系统不完善或外部事件导致直接或间接损失的风险。\n\n[v7u_N000371|371] Legal risk is the possibility that criminal penalties, lawsuits, or contracts that cannot be enforced might harm an organization.\nZH: 法律风险是指刑事处罚、诉讼或不可执行合同可能损害组织的可能性。\n\n[v7u_N000372|372] Concentration risk stems from over-exposure to a single customer or group of related customers.\nZH: 集中度风险源于对单一客户或关联客户群体的过度敞口。\n\n[v7u_N000373|373] Reputational risk comes when an institution known to have weak controls is then targeted by criminals or avoided by stakeholders who lose confidence in the institution.\nZH: 声誉风险是指机构因控制薄弱而被犯罪分子利用或利益相关者失去信心而回避的风险。\n\n[v7u_N000374|374] Although these risks are usually managed by non-AFC risk management teams, understanding the correlation with financial crime risk is indispensable.\nZH: 尽管这些风险通常由非金融犯罪防控团队管理，但理解其与金融犯罪风险的关联至关重要。\n\n[v7u_N000375|375] Operational risk is complex and includes an organization’s ability to maintain AFC controls in an evolving regulatory environment across multiple jurisdictions.\nZH: 运营风险复杂，包括组织在多个司法管辖区不断变化的监管环境中维持金融犯罪防控控制的能力。\n\n[v7u_N000376|376] Typically, a global organization makes the policies of its home regulator its base standard. The organization will then adjust to each host country’s laws.\nZH: 全球组织通常以母国监管机构政策为基础标准，再根据东道国法律进行调整。\n\n[v7u_N000377|377] Evolving regulations might become misaligned with current business models and controls.\nZH: 不断演变的法规可能与现有业务模式和控制措施产生错位。\n\n[v7u_N000378|378] Compliance programs must continually be updated.\nZH: 合规计划必须持续更新。\n\n[v7u_N000379|379] Legal risk stems from potential violation of regulations, laws, and ethical practices.\nZH: 法律风险源于可能违反法规、法律和道德实践。\n\n[v7u_N000380|380] Governments might issue administrative penalties or fines. Third parties, such as customers who feel damaged, might file lawsuits.\nZH: 政府可能处以行政处罚或罚款，受损客户等第三方可能提起诉讼。\n\n[v7u_N000381|381] Adequate AFC controls add protection from crime and inappropriate relationships.\nZH: 充分的金融犯罪防控措施可防范犯罪及不当关系\n\n[v7u_N000382|382] Concentration risk can be reduced by AFC controls and strategic diversification.\nZH: 金融犯罪防控与战略多元化可降低集中度风险\n\n[v7u_N000383|383] Customer due diligence, enabled by technology, helps manage exposure.\nZH: 借助技术的客户尽职调查有助于管理风险敞口\n\n[v7u_N000384|384] Concentration could occur in borrowing, funding, purchasing, provision of key services, or any other business relationship.\nZH: 集中度可能出现在借贷、融资、采购、关键服务提供等业务关系中\n\n[v7u_N000385|385] Risk could increase through actions by a customer, or external actions involving a customer.\nZH: 风险可能因客户行为或涉及客户的外部行为而增加\n\n[v7u_N000386|386] Reputational risk is difficult to quantify.\nZH: 声誉风险难以量化\n\n[v7u_N000387|387] Trust takes a long time to earn but can be lost quickly. A single news story—even fake news—can drive away customers and investors.\nZH: 信任建立缓慢但易丧失，一条新闻即可驱离客户与投资者\n\n[v7u_N000388|388] Many organizations deserve their reputations, good or bad, based on their chosen business practices and ethics.\nZH: 组织的声誉源于其商业实践与道德选择",
  "allowed_unit_ids": [
    "v7u_N000369",
    "v7u_N000370",
    "v7u_N000371",
    "v7u_N000372",
    "v7u_N000373",
    "v7u_N000374",
    "v7u_N000375",
    "v7u_N000376",
    "v7u_N000377",
    "v7u_N000378",
    "v7u_N000379",
    "v7u_N000380",
    "v7u_N000381",
    "v7u_N000382",
    "v7u_N000383",
    "v7u_N000384",
    "v7u_N000385",
    "v7u_N000386",
    "v7u_N000387",
    "v7u_N000388"
  ],
  "original_json": {
    "section_id": "CH05-S04",
    "section_title": "Financial crime risks in relation to other types of risks > Operational, legal, concentration, and reputational risks",
    "coverage_audit": [
      {
        "candidate_id": "cand_001",
        "unit_ids": [
          "v7u_N000376"
        ],
        "proposition": "全球组织通常以母国监管机构政策为基础标准，然后根据各东道国法律进行调整",
        "decision": "p7c_card",
        "card_id": "p7card_CH05-S04_001",
        "reason": "原文明示顺序性程序结构：先设定基础标准，再根据各地法律调整，包含有向动作序列，超出基础KG的简单事实保存范围。"
      },
      {
        "candidate_id": "cand_002",
        "unit_ids": [
          "v7u_N000369"
        ],
        "proposition": "组织面临的主要风险类型包括运营、法律、集中度、声誉风险",
        "decision": "kg_only",
        "card_id": null,
        "reason": "纯分类列表，无有向条件-动作结构，基础KG可充分表达。"
      },
      {
        "candidate_id": "cand_003",
        "unit_ids": [
          "v7u_N000370"
        ],
        "proposition": "运营风险是因内部流程、人员、系统不完善或外部事件导致直接或间接损失的风险",
        "decision": "kg_only",
        "card_id": null,
        "reason": "定义性陈述，无程序性或判断性有向关系。"
      },
      {
        "candidate_id": "cand_004",
        "unit_ids": [
          "v7u_N000371"
        ],
        "proposition": "法律风险是指刑事处罚、诉讼或不可执行合同可能损害组织的可能性",
        "decision": "kg_only",
        "card_id": null,
        "reason": "定义性陈述，无具体动作链。"
      },
      {
        "candidate_id": "cand_005",
        "unit_ids": [
          "v7u_N000372"
        ],
        "proposition": "集中度风险源于对单一客户或关联客户群体的过度敞口",
        "decision": "kg_only",
        "card_id": null,
        "reason": "定义性陈述。"
      },
      {
        "candidate_id": "cand_006",
        "unit_ids": [
          "v7u_N000373"
        ],
        "proposition": "声誉风险是因控制薄弱被犯罪分子利用或利益相关者丧失信心而回避的风险",
        "decision": "kg_only",
        "card_id": null,
        "reason": "定义性陈述。"
      },
      {
        "candidate_id": "cand_007",
        "unit_ids": [
          "v7u_N000374"
        ],
        "proposition": "虽然这些风险通常由非AFC团队管理，但理解其与金融犯罪风险的关联必不可少",
        "decision": "kg_only",
        "card_id": null,
        "reason": "仅陈述管理归属和重要性，无具体条件-动作有向链。"
      },
      {
        "candidate_id": "cand_008",
        "unit_ids": [
          "v7u_N000375"
        ],
        "proposition": "运营风险复杂，包括在多个司法管辖区不断变化的监管环境中维持AFC控制的能力",
        "decision": "kg_only",
        "card_id": null,
        "reason": "对运营风险复杂性的补充说明，未形成指向特定判断或应对的有向结构。"
      },
      {
        "candidate_id": "cand_009",
        "unit_ids": [
          "v7u_N000377",
          "v7u_N000378"
        ],
        "proposition": "当法规演变可能与现有业务模式和控制错位时，合规计划必须持续更新",
        "decision": "kg_only",
        "card_id": null,
        "reason": "两句之间无明确因果或条件连接词，原文未明示法规错位直接触发更新义务，仅为独立的风险陈述与一般性义务陈述，基础KG可分别保存。"
      },
      {
        "candidate_id": "cand_010",
        "unit_ids": [
          "v7u_N000379"
        ],
        "proposition": "法律风险源于可能违反法规、法律和道德实践",
        "decision": "kg_only",
        "card_id": null,
        "reason": "风险来源说明，无程序性结构。"
      },
      {
        "candidate_id": "cand_011",
        "unit_ids": [
          "v7u_N000380"
        ],
        "proposition": "政府可能处以行政罚款，受损第三方可能提起诉讼",
        "decision": "kg_only",
        "card_id": null,
        "reason": "列举法律风险的可能后果，属一般事实，基础KG可保存。"
      },
      {
        "candidate_id": "cand_012",
        "unit_ids": [
          "v7u_N000381"
        ],
        "proposition": "充分的AFC控制可防范犯罪及不当关系",
        "decision": "kg_only",
        "card_id": null,
        "reason": "控制效益的一般性声明，无特定条件-动作链。"
      },
      {
        "candidate_id": "cand_013",
        "unit_ids": [
          "v7u_N000382",
          "v7u_N000383"
        ],
        "proposition": "通过AFC控制和战略多元化及借助技术的客户尽职调查，可降低集中度风险并管理敞口",
        "decision": "kg_only",
        "card_id": null,
        "reason": "一般性缓解措施说明，未形成有向判断或行动步骤。"
      },
      {
        "candidate_id": "cand_014",
        "unit_ids": [
          "v7u_N000384",
          "v7u_N000385"
        ],
        "proposition": "集中度可能出现在借贷、融资等多种业务关系中，风险可能因客户或外部行动而增加",
        "decision": "kg_only",
        "card_id": null,
        "reason": "列举风险发生场景和增加因素，属知识性事实，无程序性结构。"
      },
      {
        "candidate_id": "cand_015",
        "unit_ids": [
          "v7u_N000386",
          "v7u_N000387",
          "v7u_N000388"
        ],
        "proposition": "声誉风险难以量化，信任易失，组织声誉源于商业实践与道德选择",
        "decision": "kg_only",
        "card_id": null,
        "reason": "声誉风险特征的一般说明，无具体动作或判断链。"
      }
    ],
    "cards": [
      {
        "card_id": "p7card_CH05-S04_001",
        "section_id": "CH05-S04",
        "card_nature": "execution",
        "title": "全球组织以母国标准为基础并适应东道国法律",
        "flow_nodes": [
          {
            "node_id": "P1",
            "node_category": "process",
            "node_type": "P8_constrained_action",
            "label": "全球组织通常以母国监管机构政策为基础标准",
            "evidence_unit_ids": [
              "v7u_N000376"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "P2",
            "node_category": "process",
            "node_type": "P8_constrained_action",
            "label": "全球组织然后根据各东道国法律进行调整",
            "evidence_unit_ids": [
              "v7u_N000376"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "S1",
            "node_category": "auxiliary",
            "node_type": "standard",
            "label": "母国监管机构政策",
            "evidence_unit_ids": [
              "v7u_N000376"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "S2",
            "node_category": "auxiliary",
            "node_type": "standard",
            "label": "各东道国法律",
            "evidence_unit_ids": [
              "v7u_N000376"
            ],
            "evidence_strength": "explicit"
          }
        ],
        "flow_edges": [
          {
            "edge_id": "e1",
            "edge_type": "REFERENCES",
            "source": "P1",
            "target": "S1",
            "evidence_unit_ids": [
              "v7u_N000376"
            ],
            "derivation": "explicit_text",
            "relation_type": "standard_constrains_action"
          },
          {
            "edge_id": "e2",
            "edge_type": "REFERENCES",
            "source": "P2",
            "target": "S2",
            "evidence_unit_ids": [
              "v7u_N000376"
            ],
            "derivation": "explicit_text",
            "relation_type": "standard_constrains_action"
          },
          {
            "edge_id": "e3",
            "edge_type": "PRECEDES",
            "source": "P1",
            "target": "P2",
            "evidence_unit_ids": [
              "v7u_N000376"
            ],
            "derivation": "explicit_text"
          }
        ],
        "source_unit_ids": [
          "v7u_N000376"
        ],
        "candidate_status": "candidate",
        "review_notes": "增量命题：全球组织先以母国政策为基础标准，再根据东道国法律进行调整（顺序性）；KG不足：基础KG只能将该实践保存为一条事实，无法表达“先……然后……”的有向动作序列；选项判断：可据以判断或排除涉及全球化组织政策制定顺序的选项；LLM推理：无。"
      }
    ],
    "skip_reason": null
  },
  "gap_claims": [
    {
      "claim_id": "claim_006",
      "unit_ids": [
        "v7u_N000374"
      ],
      "proposition": "尽管运营、法律、集中度和声誉风险通常由非金融犯罪防控团队管理，但理解这些风险与金融犯罪风险的关联是必不可少的",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "缺少表达组织必须理解风险关联这一义务动作的节点，以及连接该动作与相关风险主题的REFERENCES边，也未保留让步条件与必不可少的限定。",
      "condition": "尽管这些风险通常由非金融犯罪防控团队管理",
      "qualifier": "必不可少的",
      "reason": "原文明示即使管理归属不同，理解关联仍是强制要求，属于有向义务命题，对CAMS选项判断至关重要，首次抽取误判为kg_only。"
    },
    {
      "claim_id": "claim_010",
      "unit_ids": [
        "v7u_N000378"
      ],
      "proposition": "合规计划必须持续更新",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "缺少一个表示组织必须持续更新合规计划的义务节点，以及可能的触发条件（如法规错位）的边，未体现“必须”的强制限定。",
      "condition": null,
      "qualifier": "必须",
      "reason": "原文明确要求合规计划持续更新，为有向动作义务，对判断组织合规义务是否履行有重要意义，首次抽取错误地将其与v7u_N000377合并并判为kg_only。"
    },
    {
      "claim_id": "claim_013",
      "unit_ids": [
        "v7u_N000381"
      ],
      "proposition": "充分的金融犯罪防控措施可以防范犯罪及不当关系",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "缺少表达充分AFC控制产生防范效果的有向边，以及体现“可以”这一情态的结果节点。",
      "condition": "充分的金融犯罪防控措施",
      "qualifier": "可以",
      "reason": "原文表达了控制措施对风险结果的有向影响，属于P7C控制效益命题，有助于评估控制有效性，首次抽取误判为kg_only。"
    },
    {
      "claim_id": "claim_014",
      "unit_ids": [
        "v7u_N000382"
      ],
      "proposition": "金融犯罪防控和战略多元化可以降低集中度风险",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "缺少从AFC控制与战略多元化指向降低集中度风险的有向边，以及表示“可以”的限定。",
      "condition": null,
      "qualifier": "可以",
      "reason": "明确的缓解措施效果命题，对CAMS选项中评估多元化策略的作用有判断价值，首次抽取将其与v7u_N000383合并并判为kg_only。"
    },
    {
      "claim_id": "claim_015",
      "unit_ids": [
        "v7u_N000383"
      ],
      "proposition": "借助技术的客户尽职调查有助于管理风险敞口",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "缺少从技术赋能的CDD指向管理风险敞口的有向边，未体现“有助于”这一情态限定。",
      "condition": "借助技术",
      "qualifier": "有助于",
      "reason": "原文显示CDD对敞口管理的积极作用，属于P7C范畴的局部有向命题，首次抽取未单独识别。"
    }
  ]
}
```
