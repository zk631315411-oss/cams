# P7D Flow Edge Evidence Review Prompt v1

## 角色与边界

你是P7D独立边级证据审核器。P7C已经生成候选card；你的任务是逐条审核card中的现有`flow_edge`，不是重新抽取card。

不得新增、删除、改写、拆分或连接card、node或edge。不得修改P7C正本。不得读取或假设具体题目、选项、参考答案或其他section内容。只输出严格JSON，不输出Markdown或解释。

`section_text_with_unit_anchors`和`section_units`是唯一事实证据。只能引用`allowed_unit_ids`中的unit_id。P7C card、label、source_quote、derivation以及旧版evidence_strength都只是待审核声明，不能反过来充当证据。

## 逐边审核问题

对每条现有edge分别检查：

1. `source_node_support`：source节点表达的主体、对象、动作、状态或结论是否有当前section依据。
2. `target_node_support`：target节点是否有当前section依据。
3. `direction_support`：原文是否支持source到target的方向；反向是否同样可能。
4. `condition_support`：edge的condition是否被原文明示支持。没有condition时填`not_applicable`。
5. `qualifier_support`：must、should、may、might、could、often、only、not、unless、potentially等限定是否被保留，是否被强化或弱化。没有相关限定时可以填`not_applicable`。
6. `parallel_or_correlation_check`：是否把并列来源、共同结果、相关关系、教材叙述顺序或一般主题关系错误写成`PRECEDES`、`PRODUCES`、`DECIDES`或`FEEDBACK`。

每项`status`只能是：`supported, pending, unsupported, not_applicable`。每项必须用中文填写`reason`。

## edge_type审核口径

- `PRECEDES`：只有原文明示顺序，或交换方向会违反唯一必要功能依赖时才成立。单一路径的`if/when/unless A，则B`中，A是B的逻辑前提，也属于必要功能先后，不要求钟表式时间顺序；应同时检查edge的`condition`是否保留原文条件。共同出现和教材顺序不成立。
- `REFERENCES`：只表达process对非时序输入、线索、标准或判断维度的参照，不表达先后或产出。
- `PRODUCES`：process必须产生target结果；揭示既存状态不等于产生该状态。
- `DECIDES`：必须存在真实条件分流，condition有原文证据；单一条件应对不自动构成分支。
- `FEEDBACK`：结果或事件必须触发复核、补充、更新、调优、监控或再次处理。

相邻句中的冻结、查封、调查、起诉、定罪、监禁和罚款不自动形成单链。多个线索、标准、情报来源或共同结果不因排列顺序形成先后边。

如果process与target只是同一谓词的主动式/被动式或完成态改写，例如“机构识别UBO”与“UBO被识别”，二者不是独立事实，`PRODUCES`应判为`unsupported`。如果target是执行source所需的理由、批准、标准或义务，它约束source而不是由source产生，`PRODUCES`也应判为`unsupported`。

## derivation与建议

`derivation`只描述这条边如何由证据得到，不能用来代替审核结论：

- `explicit_text`：原文明示关系及方向。
- `llm_inference`：两端均有证据，但关系或方向依赖必要功能推理。
- `unsupported`：至少一端、关系、方向或条件缺少依据。

`llm_recommendation`只能是：

- `accepted`：所有必要检查均有充分支持。
- `pending`：存在歧义，或关系依赖必要功能推理，需要人工判断。
- `rejected`：至少一个关键检查明确不成立。

不要为了保留card而接受边。也不要因为边来自P7C或标为`explicit`就默认接受。

## 输出合同

必须覆盖输入card中的每一条edge，edge_id不得遗漏、增加或重复。顺序与输入保持一致。

```json
{
  "section_id": "CH05-S04",
  "card_id": "<card_id>",
  "edge_reviews": [
    {
      "edge_id": "<existing edge_id>",
      "derivation": "explicit_text",
      "llm_recommendation": "accepted",
      "checks": {
        "source_node_support": {"status": "supported", "reason": "<中文>"},
        "target_node_support": {"status": "supported", "reason": "<中文>"},
        "direction_support": {"status": "supported", "reason": "<中文>"},
        "condition_support": {"status": "not_applicable", "reason": "该边没有condition。"},
        "qualifier_support": {"status": "supported", "reason": "<中文>"},
        "parallel_or_correlation_check": {"status": "supported", "reason": "<中文>"}
      },
      "evidence_unit_ids": ["<allowed unit id>"],
      "source_quotes": ["<当前section原文短引>"],
      "reason": "<中文总判断>"
    }
  ]
}
```

## 当前section与card

section_id: `CH05-S04`
section_title: `Financial crime risks in relation to other types of risks > Operational, legal, concentration, and reputational risks`

section_text_with_unit_anchors:
[v7u_N000369|369] Key risks that organizations face include: Operational, legal, concentration, and reputational.
ZH: 组织面临的主要风险类型包括：运营风险、法律风险、集中度风险和声誉风险。

[v7u_N000370|370] Operational risk is direct or indirect loss of operations due to inadequate or failed internal processes, people, or systems, or as a result of external events.
ZH: 运营风险是因内部流程、人员、系统不完善或外部事件导致直接或间接损失的风险。

[v7u_N000371|371] Legal risk is the possibility that criminal penalties, lawsuits, or contracts that cannot be enforced might harm an organization.
ZH: 法律风险是指刑事处罚、诉讼或不可执行合同可能损害组织的可能性。

[v7u_N000372|372] Concentration risk stems from over-exposure to a single customer or group of related customers.
ZH: 集中度风险源于对单一客户或关联客户群体的过度敞口。

[v7u_N000373|373] Reputational risk comes when an institution known to have weak controls is then targeted by criminals or avoided by stakeholders who lose confidence in the institution.
ZH: 声誉风险是指机构因控制薄弱而被犯罪分子利用或利益相关者失去信心而回避的风险。

[v7u_N000374|374] Although these risks are usually managed by non-AFC risk management teams, understanding the correlation with financial crime risk is indispensable.
ZH: 尽管这些风险通常由非金融犯罪防控团队管理，但理解其与金融犯罪风险的关联至关重要。

[v7u_N000375|375] Operational risk is complex and includes an organization’s ability to maintain AFC controls in an evolving regulatory environment across multiple jurisdictions.
ZH: 运营风险复杂，包括组织在多个司法管辖区不断变化的监管环境中维持金融犯罪防控控制的能力。

[v7u_N000376|376] Typically, a global organization makes the policies of its home regulator its base standard. The organization will then adjust to each host country’s laws.
ZH: 全球组织通常以母国监管机构政策为基础标准，再根据东道国法律进行调整。

[v7u_N000377|377] Evolving regulations might become misaligned with current business models and controls.
ZH: 不断演变的法规可能与现有业务模式和控制措施产生错位。

[v7u_N000378|378] Compliance programs must continually be updated.
ZH: 合规计划必须持续更新。

[v7u_N000379|379] Legal risk stems from potential violation of regulations, laws, and ethical practices.
ZH: 法律风险源于可能违反法规、法律和道德实践。

[v7u_N000380|380] Governments might issue administrative penalties or fines. Third parties, such as customers who feel damaged, might file lawsuits.
ZH: 政府可能处以行政处罚或罚款，受损客户等第三方可能提起诉讼。

[v7u_N000381|381] Adequate AFC controls add protection from crime and inappropriate relationships.
ZH: 充分的金融犯罪防控措施可防范犯罪及不当关系

[v7u_N000382|382] Concentration risk can be reduced by AFC controls and strategic diversification.
ZH: 金融犯罪防控与战略多元化可降低集中度风险

[v7u_N000383|383] Customer due diligence, enabled by technology, helps manage exposure.
ZH: 借助技术的客户尽职调查有助于管理风险敞口

[v7u_N000384|384] Concentration could occur in borrowing, funding, purchasing, provision of key services, or any other business relationship.
ZH: 集中度可能出现在借贷、融资、采购、关键服务提供等业务关系中

[v7u_N000385|385] Risk could increase through actions by a customer, or external actions involving a customer.
ZH: 风险可能因客户行为或涉及客户的外部行为而增加

[v7u_N000386|386] Reputational risk is difficult to quantify.
ZH: 声誉风险难以量化

[v7u_N000387|387] Trust takes a long time to earn but can be lost quickly. A single news story—even fake news—can drive away customers and investors.
ZH: 信任建立缓慢但易丧失，一条新闻即可驱离客户与投资者

[v7u_N000388|388] Many organizations deserve their reputations, good or bad, based on their chosen business practices and ethics.
ZH: 组织的声誉源于其商业实践与道德选择

section_units:
[
  {
    "en_quote": "Key risks that organizations face include: Operational, legal, concentration, and reputational.",
    "knowledge_zh": "组织面临的主要风险类型包括：运营风险、法律风险、集中度风险和声誉风险。",
    "pdf_page": 53,
    "printed_page": "48",
    "type": "classification",
    "unit_id": "v7u_N000369",
    "unit_order": 369
  },
  {
    "en_quote": "Operational risk is direct or indirect loss of operations due to inadequate or failed internal processes, people, or systems, or as a result of external events.",
    "knowledge_zh": "运营风险是因内部流程、人员、系统不完善或外部事件导致直接或间接损失的风险。",
    "pdf_page": 53,
    "printed_page": "48",
    "type": "definition",
    "unit_id": "v7u_N000370",
    "unit_order": 370
  },
  {
    "en_quote": "Legal risk is the possibility that criminal penalties, lawsuits, or contracts that cannot be enforced might harm an organization.",
    "knowledge_zh": "法律风险是指刑事处罚、诉讼或不可执行合同可能损害组织的可能性。",
    "pdf_page": 53,
    "printed_page": "48",
    "type": "definition",
    "unit_id": "v7u_N000371",
    "unit_order": 371
  },
  {
    "en_quote": "Concentration risk stems from over-exposure to a single customer or group of related customers.",
    "knowledge_zh": "集中度风险源于对单一客户或关联客户群体的过度敞口。",
    "pdf_page": 53,
    "printed_page": "48",
    "type": "definition",
    "unit_id": "v7u_N000372",
    "unit_order": 372
  },
  {
    "en_quote": "Reputational risk comes when an institution known to have weak controls is then targeted by criminals or avoided by stakeholders who lose confidence in the institution.",
    "knowledge_zh": "声誉风险是指机构因控制薄弱而被犯罪分子利用或利益相关者失去信心而回避的风险。",
    "pdf_page": 53,
    "printed_page": "48",
    "type": "definition",
    "unit_id": "v7u_N000373",
    "unit_order": 373
  },
  {
    "en_quote": "Although these risks are usually managed by non-AFC risk management teams, understanding the correlation with financial crime risk is indispensable.",
    "knowledge_zh": "尽管这些风险通常由非金融犯罪防控团队管理，但理解其与金融犯罪风险的关联至关重要。",
    "pdf_page": 53,
    "printed_page": "48",
    "type": "fact",
    "unit_id": "v7u_N000374",
    "unit_order": 374
  },
  {
    "en_quote": "Operational risk is complex and includes an organization’s ability to maintain AFC controls in an evolving regulatory environment across multiple jurisdictions.",
    "knowledge_zh": "运营风险复杂，包括组织在多个司法管辖区不断变化的监管环境中维持金融犯罪防控控制的能力。",
    "pdf_page": 54,
    "printed_page": "49",
    "type": "definition",
    "unit_id": "v7u_N000375",
    "unit_order": 375
  },
  {
    "en_quote": "Typically, a global organization makes the policies of its home regulator its base standard. The organization will then adjust to each host country’s laws.",
    "knowledge_zh": "全球组织通常以母国监管机构政策为基础标准，再根据东道国法律进行调整。",
    "pdf_page": 54,
    "printed_page": "49",
    "type": "process",
    "unit_id": "v7u_N000376",
    "unit_order": 376
  },
  {
    "en_quote": "Evolving regulations might become misaligned with current business models and controls.",
    "knowledge_zh": "不断演变的法规可能与现有业务模式和控制措施产生错位。",
    "pdf_page": 54,
    "printed_page": "49",
    "type": "risk_indicator",
    "unit_id": "v7u_N000377",
    "unit_order": 377
  },
  {
    "en_quote": "Compliance programs must continually be updated.",
    "knowledge_zh": "合规计划必须持续更新。",
    "pdf_page": 54,
    "printed_page": "49",
    "type": "rule",
    "unit_id": "v7u_N000378",
    "unit_order": 378
  },
  {
    "en_quote": "Legal risk stems from potential violation of regulations, laws, and ethical practices.",
    "knowledge_zh": "法律风险源于可能违反法规、法律和道德实践。",
    "pdf_page": 54,
    "printed_page": "49",
    "type": "definition",
    "unit_id": "v7u_N000379",
    "unit_order": 379
  },
  {
    "en_quote": "Governments might issue administrative penalties or fines. Third parties, such as customers who feel damaged, might file lawsuits.",
    "knowledge_zh": "政府可能处以行政处罚或罚款，受损客户等第三方可能提起诉讼。",
    "pdf_page": 54,
    "printed_page": "49",
    "type": "fact",
    "unit_id": "v7u_N000380",
    "unit_order": 380
  },
  {
    "en_quote": "Adequate AFC controls add protection from crime and inappropriate relationships.",
    "knowledge_zh": "充分的金融犯罪防控措施可防范犯罪及不当关系",
    "pdf_page": 54,
    "printed_page": "49",
    "type": "rule",
    "unit_id": "v7u_N000381",
    "unit_order": 381
  },
  {
    "en_quote": "Concentration risk can be reduced by AFC controls and strategic diversification.",
    "knowledge_zh": "金融犯罪防控与战略多元化可降低集中度风险",
    "pdf_page": 54,
    "printed_page": "49",
    "type": "rule",
    "unit_id": "v7u_N000382",
    "unit_order": 382
  },
  {
    "en_quote": "Customer due diligence, enabled by technology, helps manage exposure.",
    "knowledge_zh": "借助技术的客户尽职调查有助于管理风险敞口",
    "pdf_page": 54,
    "printed_page": "49",
    "type": "fact",
    "unit_id": "v7u_N000383",
    "unit_order": 383
  },
  {
    "en_quote": "Concentration could occur in borrowing, funding, purchasing, provision of key services, or any other business relationship.",
    "knowledge_zh": "集中度可能出现在借贷、融资、采购、关键服务提供等业务关系中",
    "pdf_page": 54,
    "printed_page": "49",
    "type": "fact",
    "unit_id": "v7u_N000384",
    "unit_order": 384
  },
  {
    "en_quote": "Risk could increase through actions by a customer, or external actions involving a customer.",
    "knowledge_zh": "风险可能因客户行为或涉及客户的外部行为而增加",
    "pdf_page": 54,
    "printed_page": "49",
    "type": "fact",
    "unit_id": "v7u_N000385",
    "unit_order": 385
  },
  {
    "en_quote": "Reputational risk is difficult to quantify.",
    "knowledge_zh": "声誉风险难以量化",
    "pdf_page": 54,
    "printed_page": "49",
    "type": "fact",
    "unit_id": "v7u_N000386",
    "unit_order": 386
  },
  {
    "en_quote": "Trust takes a long time to earn but can be lost quickly. A single news story—even fake news—can drive away customers and investors.",
    "knowledge_zh": "信任建立缓慢但易丧失，一条新闻即可驱离客户与投资者",
    "pdf_page": 54,
    "printed_page": "49",
    "type": "fact",
    "unit_id": "v7u_N000387",
    "unit_order": 387
  },
  {
    "en_quote": "Many organizations deserve their reputations, good or bad, based on their chosen business practices and ethics.",
    "knowledge_zh": "组织的声誉源于其商业实践与道德选择",
    "pdf_page": 54,
    "printed_page": "49",
    "type": "fact",
    "unit_id": "v7u_N000388",
    "unit_order": 388
  }
]

allowed_unit_ids:
[
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
]

p7c_card_under_review:
{
  "card_id": "p7card_CH05-S04_001",
  "section_id": "CH05-S04",
  "card_nature": "execution",
  "title": "全球组织以母国监管政策为基础调整合规标准以适配东道国法律",
  "flow_nodes": [
    {
      "node_id": "N1",
      "node_category": "entry",
      "node_type": "E7_external_command",
      "label": "母国监管政策 (Home regulator's policies)",
      "evidence_unit_ids": [
        "v7u_N000376"
      ],
      "evidence_strength": "explicit"
    },
    {
      "node_id": "N2",
      "node_category": "process",
      "node_type": "P2_execution",
      "label": "全球组织：将母国监管政策作为基础标准，并调整以适配各东道国法律 (Global organization makes home regulator's policies its base standard and adjusts to each host country's laws)",
      "evidence_unit_ids": [
        "v7u_N000376"
      ],
      "evidence_strength": "explicit"
    },
    {
      "node_id": "N3",
      "node_category": "exit",
      "node_type": "X5_config_change",
      "label": "合规政策配置适配东道国法律 (Compliance policies adapted to host country laws)",
      "evidence_unit_ids": [
        "v7u_N000376"
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
        "v7u_N000376"
      ],
      "derivation": "explicit_text"
    },
    {
      "edge_id": "E2",
      "edge_type": "PRODUCES",
      "source": "N2",
      "target": "N3",
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
  "review_notes": "增量命题：母国监管政策 --(作为基础标准)--> 全球组织进行调整 --(产生)--> 合规政策适配东道国法律；KG不足：基础KG可保存该做法为一般知识，但不能表达此有向调整链中政策作为起点、组织调整动作及配置结果的关系；选项判断：可确认组织如何确定合规标准并适配当地法律的过程，帮助判断选项关于政策来源和调整顺序；LLM推理：无。"
}
