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
  "section_id": "CH08-S05",
  "section_title": "Private banking and wealth management risks > Special purpose vehicle risks",
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
  },
  "gap_claims": [
    {
      "claim_id": "claim_006",
      "unit_ids": [
        "v7u_N000660"
      ],
      "proposition": "金融机构对SPV和PIV进行强化尽职调查（包括识别最终受益所有人并了解真实目的）有助于减轻潜在的金融犯罪风险。",
      "kg_boundary": "p7_incremental",
      "coverage_status": "missing",
      "matched_card_ids": [],
      "missing_part": "现有卡片p7card_CH08-S05_001仅覆盖了EDD的过程和标准约束，但缺失了EDD实施对风险减轻的正向效果节点或边，未能体现“有助于减轻风险”这一非确定性因果关系。",
      "condition": null,
      "qualifier": "help mitigate, potential",
      "reason": "该命题为一个有向效果关系，表达了合规动作对风险控制的非决定性正面影响，可用于评估控制措施的有效性，属于P7C增量命题，但未被现有卡片覆盖。"
    }
  ]
}
```
