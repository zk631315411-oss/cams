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

section_id: `CH47-S08`

section_title: `Transaction monitoring > Steps applied to an investigation`

section_text_with_unit_anchors:

```text
[v7u_N003330|3330] Before escalating an investigation to confirm and report suspicion, an analyst is expected to understand the nature of the suspicion and determine whether there is a possible explanation for the transaction.
ZH: 分析师在升级调查前必须理解可疑性质并判断是否有合理解释

[v7u_N003331|3331] Any patterns of previous transactions from the same account or customer should also be reviewed.
ZH: 应审查同一账户或客户的过往交易模式

[v7u_N003332|3332] Information gathered during onboarding, along with historical transaction data, can provide helpful context.
ZH: 开户时收集的信息和历史交易数据可提供有用背景

[v7u_N003333|3333] Finally, all research should be clearly documented, indicating what information—if any—is missing.
ZH: 所有研究应清晰记录，并注明缺失的信息
```

allowed_unit_ids:

```json
[
  "v7u_N003330",
  "v7u_N003331",
  "v7u_N003332",
  "v7u_N003333"
]
```
