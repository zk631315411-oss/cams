# P7C Section Card Extraction Smoke Prompt

You extract section-level CAMS exam reasoning/process cards from one section.
Return strict JSON only. No markdown fences.

## Purpose

A P7 card serves exam-oriented reasoning and procedural understanding. It may represent:
- a business process or investigation workflow;
- a risk-indicator reasoning pattern;
- a control/standard application pattern;
- a response or handoff pattern.

Do not force non-sequential lists into chronological workflows. Preserve conditions, exceptions, standards, and outputs when supported by current-section evidence.

## Card Nature

Use one of:
- execution
- assessment
- decision
- control
- risk_indicator
- reporting
- escalation
- documentation
- governance
- training
- monitoring
- review
- other

## Flow Nodes

Every node must use both `node_category` and `node_type`.

Allowed `node_category` values:
- entry
- process
- exit
- auxiliary

Allowed `node_type` values:

Entry nodes (`node_category`: `entry`):
- E1_event_signal: event/signal that starts attention or processing
- E2_object_entry: customer/account/transaction/case/object enters scope
- E3_state_threshold: threshold/state/condition becomes relevant
- E4_handoff: upstream handoff or assignment
- E5_time_cycle: periodic/cyclical trigger
- E6_change_exception: change, exception, anomaly, unusual pattern
- E7_external_command: external request/order/regulatory or law-enforcement command
- E8_decision_finding: prior decision/finding triggers downstream work

Process nodes (`node_category`: `process`):
- P1_assessment: identify, evaluate, classify, judge, compare, infer
- P2_execution: perform an operational action
- P3_branch_routing: route based on condition/branch
- P4_collection: collect/request/gather information or evidence
- P5_coordination: coordinate across people/teams/functions
- P6_feedback: request completion, correction, explanation, or supplementary action
- P7_monitoring: monitor/review over time
- P8_constrained_action: act under legal/policy/control constraints
- P9_planning: prepare/plan/design an approach
- P10_sufficiency: determine whether information/evidence/action is sufficient

Exit nodes (`node_category`: `exit`):
- X1_classification: classification, conclusion, finding, risk identification
- X2_product: produced document/report/record/SAR/plan/profile
- X3_state_change: state/status/risk/profile/threshold changes
- X4_handoff: downstream handoff/escalation/referral
- X5_config_change: configuration/tuning/rule/threshold changes
- X6_termination: process ends/closed/no further action
- X7_continuing_obligation: ongoing monitoring/control/obligation continues

Auxiliary nodes (`node_category`: `auxiliary`):
- input: data/source/material used by a process
- standard: criterion/rule/requirement/red flag/control used by a process

Required node fields:
- node_id
- node_category
- node_type
- label
- evidence_unit_ids
- evidence_strength

Optional node fields:
- actor
- description
- source_quote
- modality
- review_status

`review_status` must be exactly one of: needs_review, accepted, rejected.
`evidence_strength` must be exactly one of: explicit, functional_dependency, needs_review, rejected.
Every node must cite at least one current-section unit_id from `allowed_unit_ids`.

## Flow Edges

Allowed `edge_type` values:
- PRECEDES: supported sequence or functional dependency between non-auxiliary nodes
- USES: a process node uses an input or standard node
- PRODUCES: a process node produces an exit node
- DECIDES: a process/branch node routes by a condition; `condition` required
- FEEDBACK: a result asks for completion/correction/update of an updateable node

Allowed optional `relation_type` values:
- clue_supports_identification
- mechanism_explains_risk
- identification_leads_to_conclusion
- conclusion_triggers_response
- condition_routes_path
- component_assembles_product
- standard_constrains_action
- result_handoffs_stage
- feedback_requests_completion
- cycle_requires_monitoring
- standard_transmits_requirement
- parallel_alternative_no_sequence

Use `relation_type` to carry exam/business semantics. Examples:
- red flag -> assessment: clue_supports_identification
- mechanism/rationale -> risk conclusion: mechanism_explains_risk
- assessment -> classification/finding: identification_leads_to_conclusion
- finding -> response/escalation: conclusion_triggers_response
- branch condition -> path: condition_routes_path
- parts -> product: component_assembles_product
- standard/control -> constrained action: standard_constrains_action
- result -> next stage/handoff: result_handoffs_stage
- feedback -> missing/completion action: feedback_requests_completion
- cycle/time trigger -> monitoring: cycle_requires_monitoring
- law/policy/standard -> requirement: standard_transmits_requirement
- parallel criteria/options without sequence: parallel_alternative_no_sequence

Required edge fields:
- edge_id
- edge_type
- source
- target
- evidence_unit_ids
- evidence_strength

Optional edge fields:
- condition
- qualifier
- modality
- source_quote
- review_status
- relation_type

Rules:
1. `source` and `target` must reference node_id values in the same card.
2. Every card must contain at least one entry node (E-prefix).
3. Do not use old node types such as start, trigger, action, decision, output, or end. These are invalid as `node_type` values.
4. If the text has no explicit final product but implies continued monitoring/control, use X7_continuing_obligation.
5. If the text yields a classification/finding rather than a document, use X1_classification.
6. If the text yields a document/report/record/request package, use X2_product.
7. `USES` target must be `input` or `standard`.
8. `PRODUCES` target must be an X-prefix exit node.
9. `DECIDES` edges require `condition`.
10. Do not serialize parallel lists unless the section explicitly states sequence.
11. Every edge must cite at least one current-section unit_id from `allowed_unit_ids`.
12. Use only current-section evidence. Do not invent unit IDs.

## Output JSON Shape

Return this shape exactly:

{
  "section_id": "<section_id>",
  "section_title": "<section_title>",
  "cards": [
    {
      "card_id": "p7card_<section_id>_001",
      "section_id": "<section_id>",
      "card_nature": "risk_indicator",
      "title": "Short card title",
      "summary": "Optional one-sentence human-readable description.",
      "flow_nodes": [
        {
          "node_id": "n_entry_01",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "Unusual or exceptional pattern appears",
          "evidence_unit_ids": ["v7u_..."],
          "evidence_strength": "explicit",
          "review_status": "accepted"
        },
        {
          "node_id": "n_process_01",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "Assess whether the pattern indicates suspicious activity",
          "evidence_unit_ids": ["v7u_..."],
          "evidence_strength": "functional_dependency",
          "review_status": "needs_review"
        },
        {
          "node_id": "n_exit_01",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "Potential suspicious activity identified",
          "evidence_unit_ids": ["v7u_..."],
          "evidence_strength": "functional_dependency",
          "review_status": "needs_review"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7flowedge_<section_id>_001_001",
          "edge_type": "PRECEDES",
          "source": "n_entry_01",
          "target": "n_process_01",
          "evidence_unit_ids": ["v7u_..."],
          "evidence_strength": "functional_dependency",
          "review_status": "needs_review",
          "relation_type": "clue_supports_identification"
        },
        {
          "edge_id": "p7flowedge_<section_id>_001_002",
          "edge_type": "PRODUCES",
          "source": "n_process_01",
          "target": "n_exit_01",
          "evidence_unit_ids": ["v7u_..."],
          "evidence_strength": "functional_dependency",
          "review_status": "needs_review",
          "relation_type": "identification_leads_to_conclusion"
        }
      ],
      "source_unit_ids": ["v7u_..."],
      "review_status": "needs_review",
      "review_notes": ""
    }
  ],
  "skip_reason": null
}

If no cards should be extracted:

{
  "section_id": "<section_id>",
  "section_title": "<section_title>",
  "cards": [],
  "skip_reason": "No section-level executable process, assessment standard, control requirement, or risk-indicator rule found."
}

## Current Section

section_id: `CH11-S05`

section_title: `Money laundering risks associated with MSBs, payment service providers, and ecommerce > Case example: LotusMall and illegal gambling`

section_text_with_unit_anchors:

```text
[v7u_N000865|865] As e-commerce has expanded, so too have opportunities for illicit financial activity.
ZH: 电子商务扩张增加了非法金融活动的机会

[v7u_N000866|866] One example is LotusMall, a Chinese e-commerce platform, LotusMall, was implicated in facilitating illegal online gambling and associated money laundering.
ZH: 中国电子商务平台LotusMall被指协助非法在线赌博和洗钱

[v7u_N000867|867] Operators of gambling websites such as LuckyBet exploited the e-commerce platform by directing users to fund their gambling accounts through QR code payments processed via a PSP. However, transaction records showed the payments were actually being made to merchants on LotusMall, creating the appearance of legitimate e-commerce activity.
ZH: 赌博网站LuckyBet利用电子商务平台通过二维码支付伪装交易

[v7u_N000868|868] Behind the scenes, LuckyBet had orchestrated a network of fake storefronts.
ZH: LuckyBet策划了虚假店铺网络

[v7u_N000869|869] They recruited individuals, often paid a commission, to register as sellers using their real identification, listing everyday goods such as clothing.
ZH: LuckyBet招募个人使用真实身份注册为卖家

[v7u_N000870|870] These stores appeared legitimate, but no products were ever shipped. Instead, funds from gamblers were funneled directly to LuckyBet under the guise of online purchases.
ZH: 虚假店铺从未发货，赌徒资金以购物名义流向LuckyBet

[v7u_N000871|871] For some merchants, product listings were priced far above the expected market value, a red flag for fraud.
ZH: 商品定价远高于市场价值是欺诈红旗信号信号

[v7u_N000872|872] Other merchants had many low-value products listed, but had extremely high numbers of transactions per day, which is another red flag.
ZH: 大量低价商品但日交易量极高是另一红旗信号信号

[v7u_N000873|873] Additionally, LuckyBet’s gambling sites operated from offshore servers, adding another layer of anonymity and making law enforcement tracing efforts more difficult.
ZH: LuckyBet使用境外服务器增加匿名性，阻碍执法追踪

[v7u_N000874|874] Authorities eventually uncovered the operation when two individuals were arrested for selling over 90,000 fake delivery records tied to these bogus transactions. In total, more than CNY¥10 billion (approximately US$1.38 billion) was laundered through LotusMall.
ZH: LotusMall洗钱案中超过100亿元人民币被清洗

[v7u_N000875|875] The fallout was severe: LotusMall reported financial losses of CNY¥3.4 billion (around US$468 million) and faced legal action against senior executives for enabling money laundering.
ZH: LotusMall因洗钱案损失34亿元人民币并面临法律诉讼

[v7u_N000876|876] Authorities urged e-commerce platforms to improve risk monitoring, flag high-risk patterns such as multiple seller accounts linked to a single entity, and take a more proactive stance against fraud and collusion between buyers and sellers.
ZH: 当局敦促电子商务平台加强风险监控并打击欺诈
```

allowed_unit_ids:

```json
[
  "v7u_N000865",
  "v7u_N000866",
  "v7u_N000867",
  "v7u_N000868",
  "v7u_N000869",
  "v7u_N000870",
  "v7u_N000871",
  "v7u_N000872",
  "v7u_N000873",
  "v7u_N000874",
  "v7u_N000875",
  "v7u_N000876"
]
```
