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
  "section_id": "CH03-S02",
  "section_title": "Examples of predicate crimes > Environmental crime",
  "section_text_with_unit_anchors": "[v7u_N000216|216] While all financial crime is troubling, environmental crimes are unique in terms of their lasting effects.\nZH: 环境犯罪具有独特的持久影响\n\n[v7u_N000217|217] The Financial Crimes Enforcement Network (FinCEN) acknowledged this fact in its advisory on environmental crimes, defining them as “...illegal activity that harms human health, and harm nature and natural resources by damaging environmental quality. This can include driving biodiversity loss, and causing the overexploitation of natural resources, and thereby increasing carbon dioxide levels in the atmosphere.\nZH: FinCEN将环境犯罪定义为损害人类健康、自然和资源的非法活动\n\n[v7u_N000218|218] Wildlife trafficking can be considered a subcategory of environmental crime due to its impact on nature. However, for enforcement purposes, it is a standalone crime.\nZH: 野生动物贩运既是环境犯罪子类也是独立犯罪\n\n[v7u_N000219|219] Environmental crimes are complex. It is difficult to pursue criminal charges for the following reasons:\nZH: 环境犯罪复杂，刑事指控困难的原因\n\n[v7u_N000220|220] They often involve transnational criminal organizations (TCOs).\nZH: 环境犯罪常涉及跨国犯罪组织\n\n[v7u_N000221|221] They can be very difficult to detect prior to and during the activity.\nZH: 环境犯罪作为上游犯罪，在活动前和活动中难以被发现。\n\n[v7u_N000222|222] They can involve several global criminal and noncriminal regulations.\nZH: 环境犯罪涉及多项全球刑事和非刑事法规。\n\n[v7u_N000223|223] TCOs and other criminal organizations are constantly looking for ways to supplement their income, and environmental crimes offer the opportunity to both earn and launder funds simultaneously.\nZH: 环境犯罪为犯罪组织提供同时赚取和清洗资金的机会。\n\n[v7u_N000224|224] For example, a TCO might be a part owner of a waste management and transportation front company.\nZH: 犯罪组织可能部分拥有废物管理和运输幌子公司。\n\n[v7u_N000225|225] Their ownership would allow the TCO to inflate contracts to place illicit funds. It could then execute those contracts with complicit accountholders to layer the funds.\nZH: 犯罪组织通过虚增合同和共谋账户持有人进行离析阶段。\n\n[v7u_N000226|226] If there is any actual hazardous waste disposal carried out, it is done in a way that minimizes overhead and increases profit, such as dumping chemical production byproducts in public drinking and bathing reservoirs.\nZH: 危险废物处置中通过最小化间接费用增加利润，如将化学副产品倾倒入公共水源。\n\n[v7u_N000227|227] Similarly, TCOs might initiate or extort legitimate-appearing fishing, logging, and mining operations, either illegally harvesting natural resources or expanding the scope of a previously legitimate operation.\nZH: 犯罪组织发起或勒索看似合法的渔业、伐木和采矿业务。\n\n[v7u_N000228|228] When authorities investigate the illicit activity, they often become hindered by corrupt government officials who have been bribed to block or hide the inquiry.\nZH: 腐败官员收受贿赂阻碍对非法活动的调查。",
  "allowed_unit_ids": [
    "v7u_N000216",
    "v7u_N000217",
    "v7u_N000218",
    "v7u_N000219",
    "v7u_N000220",
    "v7u_N000221",
    "v7u_N000222",
    "v7u_N000223",
    "v7u_N000224",
    "v7u_N000225",
    "v7u_N000226",
    "v7u_N000227",
    "v7u_N000228"
  ],
  "original_json": {
    "section_id": "CH03-S02",
    "section_title": "Examples of predicate crimes > Environmental crime",
    "coverage_audit": [
      {
        "candidate_id": "cand_001",
        "unit_ids": [
          "v7u_N000216"
        ],
        "proposition": "环境犯罪具有独特的持久影响",
        "decision": "kg_only",
        "card_id": null,
        "reason": "属于孤立事实陈述，未形成条件化主体动作或判断链，基础KG可保存。"
      },
      {
        "candidate_id": "cand_002",
        "unit_ids": [
          "v7u_N000217",
          "v7u_N000218"
        ],
        "proposition": "FinCEN定义环境犯罪，野生动物贩运为子类但独立",
        "decision": "kg_only",
        "card_id": null,
        "reason": "属于定义和分类知识，基础KG可直接表达。"
      },
      {
        "candidate_id": "cand_003",
        "unit_ids": [
          "v7u_N000219",
          "v7u_N000220",
          "v7u_N000221",
          "v7u_N000222"
        ],
        "proposition": "环境犯罪复杂，刑事指控困难的原因包括涉及跨国组织、难以发现、法规复杂",
        "decision": "kg_only",
        "card_id": null,
        "reason": "属于一般性解释和原因列表，无特定主体应对或判断结构，基础KG可承接。"
      },
      {
        "candidate_id": "cand_004",
        "unit_ids": [
          "v7u_N000223",
          "v7u_N000224",
          "v7u_N000225"
        ],
        "proposition": "犯罪组织通过虚增合同和共谋账户利用环境犯罪洗钱",
        "decision": "kg_only",
        "card_id": null,
        "reason": "属于普通犯罪案例机制（placement/layering），无机构识别、评估或应对响应，基础KG可作案例表达。"
      },
      {
        "candidate_id": "cand_005",
        "unit_ids": [
          "v7u_N000226",
          "v7u_N000227"
        ],
        "proposition": "如果进行危险废物处置，以最小化费用方式倾倒；犯罪组织发起或勒索看似合法的资源开采业务",
        "decision": "kg_only",
        "card_id": null,
        "reason": "属于犯罪手法具体描述，无制度性应对或条件化判断，基础KG可保存为案例机制。"
      },
      {
        "candidate_id": "cand_006",
        "unit_ids": [
          "v7u_N000228"
        ],
        "proposition": "当局调查非法活动时，常受到受贿官员阻碍",
        "decision": "kg_only",
        "card_id": null,
        "reason": "属于孤立风险指标或一般困难陈述，无后续机构应对流程或判断分析，基础KG已识别为风险说明。"
      }
    ],
    "cards": [],
    "skip_reason": "当前章节内容主要是定义、分类、犯罪背景、起诉困难、犯罪手法案例和一般风险说明，所有命题已由基础KG充分表达，不存在超出定义、事实、案例或孤立风险指标的增量程序性或判断性有向结构。"
  },
  "gap_claims": [
    {
      "claim_id": "claim_006",
      "unit_ids": [
        "v7u_N000228"
      ],
      "proposition": "当当局调查非法环境活动时，常常会受到受贿官员的阻碍",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "缺少表达该有向命题的完整卡片，需创建包含主体（调查当局）、动作（调查）、条件（受贿官员阻碍）和限定词（often）的节点与边。",
      "condition": "调查环境犯罪时",
      "qualifier": "often",
      "reason": "当局调查动作与腐败阻碍结果构成开放但有向的关系，对反洗钱评估调查障碍具有增量程序性价值，原卡片集合为空，故判定为缺失。"
    }
  ]
}
```
