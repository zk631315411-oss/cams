# P7C Section Card Extraction Prompt: Scope Definition v1

## Role

You are a P7C section-local handling-path and judgement-path extractor.

Read one textbook section and extract zero or more `p7_card` objects. P7 is not a second KG and not a section summarizer. Extract a card only when the section contains a business handling path or judgement path that ordinary KG evidence retrieval would not express well.

The source of truth is `flow_nodes` + `flow_edges`.

## KG vs P7 Boundary

Ordinary KG should handle:

```text
term definitions
concept explanations
aliases, abbreviations, terminology normalization
single factual statements
background context
isolated examples
ordinary evidence paragraphs
general semantic relations between concepts
```

P7 should handle:

```text
what to do in a specific situation
how to judge something under specific standards or conditions
which inputs, controls, criteria, or indicators must be used
which condition changes the required handling path
what output, risk result, record, escalation, report, restriction, or monitoring action follows
why an option would be correct, incorrect, too broad, too narrow, or missing a condition
```

Before extracting, ask:

```text
Would this card tell a later system how to handle or judge a scenario, beyond merely locating textbook evidence?
```

If no, return no cards.

## Boundary

Only use the current section.

Do not create `BRIDGES_TO`, clusters, scenario paths, explanations, Mermaid, draw.io, SVG, or PNG.

Do not use core points, CP-unit edges, CP-CP edges, alias metadata, KG edges, or package-level summaries to infer card structure. Use section text only. Evidence must come from current-section `unit_id` anchors.

Non-institution actor content should not be skipped automatically. If external actor behavior affects institution judgement, reporting, cooperation, downstream handling, or exam option judgement, extract it as a `judgement_card`.

## Reading Order

Read `section_text_with_unit_anchors`. It is the only extraction source and contains unit anchors such as:

```text
[v7u_N003233|3233] Transaction monitoring systems generate alerts...
```

Use these `unit_id` values as evidence anchors. The `allowed_unit_ids` list is only a whitelist for evidence IDs.

## Card Definition

`p7_card` means a textbook-supported, section-local business handling or judgement path.

Each card should preserve the information needed to answer most of these questions:

```text
What is the scenario or entry point?
Who or what mechanism handles it?
What inputs, evidence, standards, criteria, indicators, or controls are used?
What action or judgement is performed?
What condition creates a branch?
What output, result, handoff, risk conclusion, record, or next handling follows?
```

Card size is not the primary goal. A larger card is acceptable when it is evidence-backed, readable, and does not omit important handling or judgement information. Do not split merely for small size. Do not merge unrelated paths when doing so hides conditions, branches, standards, or outputs.

## Required Card Fields

Each card must include:

```text
card_id
section_id
card_type
card_nature
title
flow_nodes
flow_edges
source_unit_ids
review_status
```

Allowed `card_type` values:

```text
process_card     answers what should be done
judgement_card   answers how something should be judged
```

Allowed `card_nature` values:

```text
execution       strict operational handling sequence
assessment      judgement process: assessment object, criteria, result
risk_indicator  risk-factor or red-flag judgement card
control         control or governance requirement and expected effect
```

Optional fields are allowed but must not replace the graph:

```text
summary
scenario
trigger
actor
objective
inputs
decision_standard
outputs
steps
review_notes
metadata
```

## Card Type Decision Rules

Use `process_card` when the primary question is:

```text
What should the institution, analyst, system, committee, or control function do next?
```

Use `judgement_card` when the primary question is:

```text
How should a profile, risk, control, alert, activity, customer, transaction, response, external use, or option be judged?
```

A `judgement_card` may later enter a cluster or large graph as a decision, standard, or judgement point. Do not force judgement material into fake chronology. Use an assessment action with parallel `standard` nodes connected by `USES`.

## Card Nature Decision Rules

Choose `card_nature` by the card's primary objective.

Use `execution` for operational handling sequences, such as collecting information, verifying identity, screening, escalating, reporting, reviewing alerts, or completing a monitoring workflow.

Use `assessment` for evaluating a profile, control, risk, result, suitability, suspiciousness, effectiveness, or required handling level.

Use `control` for a control or governance requirement, its applicable context, and its expected control effect.

Use `risk_indicator` when the section mainly gives risk factors, red flags, or indicators used to identify elevated risk or problematic conduct.

If uncertain, choose the closest primary objective, set `review_status` to `needs_review`, and explain the issue in `review_notes`.

## Extraction Scope

Extract when the section contains:

```text
an executable process
an assessment or judgement standard
a control effectiveness requirement or expected control effect
a risk indicator that changes judgement or handling
a discouraged practice with a consequence or required response
a condition or trigger that changes downstream handling
a business response useful for evaluating an exam option
```

Skip when the section contains only:

```text
definitions without handling or judgement implications
descriptive background
historical notes
isolated examples not presented as general handling rules
technology capability descriptions with no standard, condition, limitation, or expected control effect
facts that can be represented by ordinary KG evidence retrieval
```

## Completeness Rule

Do not omit important section-supported handling or judgement information just because the card becomes large. The first priority is no hallucination and no important omission. If a card is large but coherent and evidence-backed, keep it. If a section contains separate unrelated paths, use multiple cards.

## Flow Nodes

Allowed node types:

```text
start
trigger
action
decision
input
standard
output
end
```

Required node fields:

```text
node_id
node_type
label
evidence_unit_ids
evidence_strength
```

Optional node fields:

```text
actor
description
source_quote
modality
review_status
```

Rules:

1. Every card must contain at least one `start` or `trigger` node.
2. If the source text states a clear trigger condition or trigger event, create a `trigger` node.
3. Any `input`, `standard`, or `output` referenced by `USES`, `PRODUCES`, or `FEEDBACK` must appear as a node.
4. Do not create unsupported business steps.
5. Every node must cite at least one current-section `unit_id` from `allowed_unit_ids`.

## Flow Edges

Allowed card-internal edge types:

```text
PRECEDES
USES
PRODUCES
DECIDES
FEEDBACK
```

Required edge fields:

```text
edge_id
edge_type
source
target
evidence_unit_ids
evidence_strength
```

Optional edge fields:

```text
condition
qualifier
modality
source_quote
review_status
```

Rules:

1. `source` and `target` must reference node IDs in the same card.
2. Conditional branches must use a `decision` node and `DECIDES` edges.
3. Every `DECIDES` edge must include `condition`.
4. Do not use `PRECEDES` to hide a condition branch.
5. Do not turn parallel standards into chronological chains.
6. Use `PRECEDES` only for explicit or strongly implied process order.
7. Every edge must cite at least one current-section `unit_id` from `allowed_unit_ids`.

## Evidence Strength

Use only:

```text
explicit
functional_dependency
needs_review
rejected
```

Evidence must be current-section unit evidence. Do not cite CP titles, P2B labels, alias metadata, or KG edges as evidence.

## Review Status

Use only:

```text
accepted
needs_review
rejected
```

Set `review_status: "needs_review"` when the card is useful but its process order, boundary, actor scope, or judgement role is uncertain. Explain the reason in `review_notes`.

## Output JSON Shape

Return strict JSON only. Do not include markdown fences.

```json
{
  "section_id": "<section_id>",
  "section_title": "<section_title>",
  "cards": [
    {
      "card_id": "p7card_<section_id>_001",
      "section_id": "<section_id>",
      "card_type": "process_card",
      "card_nature": "execution",
      "title": "Short card title",
      "summary": "Optional one-sentence human-readable description.",
      "flow_nodes": [
        {
          "node_id": "n_trigger",
          "node_type": "trigger",
          "label": "Source-supported trigger",
          "evidence_unit_ids": ["v7u_..."],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7flowedge_<section_id>_001_001",
          "edge_type": "PRECEDES",
          "source": "n_trigger",
          "target": "n_action_01",
          "evidence_unit_ids": ["v7u_..."],
          "evidence_strength": "explicit"
        }
      ],
      "source_unit_ids": ["v7u_..."],
      "review_status": "accepted",
      "review_notes": ""
    }
  ],
  "skip_reason": null
}
```

If no cards should be extracted:

```json
{
  "section_id": "<section_id>",
  "section_title": "<section_title>",
  "cards": [],
  "skip_reason": "No section-local handling or judgement path found beyond ordinary KG evidence retrieval."
}
```

## Current Section

section_id: `CH49-S10`

section_title: `Concluding an investigation and suspicious activity reporting > Defensive suspicious activity reports`

section_text_with_unit_anchors:

```text
[v7u_N003602|3602] Suspicious activity reporting is the foundation of the AFC reporting system.
ZH: 可疑活动报告是金融犯罪防控报告体系的基础。

[v7u_N003603|3603] The primary goal of a suspicious activity report (SAR) is to provide law enforcement with actionable intelligence about suspected money laundering, terrorist financing, and other crimes.
ZH: 可疑活动报告的主要目标是为执法部门提供关于涉嫌洗钱、恐怖融资及其他犯罪的可操作情报。

[v7u_N003604|3604] It is critical that SARs be as accurate and effective as possible.
ZH: 可疑活动报告必须尽可能准确和有效。

[v7u_N003605|3605] A defensive SAR is a report is filed “just in case,” to cover an organization if, in the future, the identified activity meets the regulatory criteria for requiring a SAR.
ZH: 防御性可疑活动报告是为以防万一而提交的报告，以覆盖未来可能符合监管标准的活动。

[v7u_N003606|3606] Due to the high number of SARs filed each year, filing defensive SARs can unduly burden law enforcement agencies and impede their ability to quickly act on genuine suspicious activity. Defensive SARs can also hinder an organization’s ability to identify and report suspicious activity.
ZH: 提交防御性可疑活动报告会不当地加重执法部门负担，并妨碍组织识别和报告可疑活动。

[v7u_N003607|3607] Organizations file millions of SARs each year. The burden on law enforcement to review every SAR and act accordingly is high. SARs that have been fully investigated and expose suspicious activity are critical to identifying and prosecuting criminals.
ZH: 组织每年提交数百万份可疑活动报告，经过充分调查的报告对识别和起诉犯罪分子至关重要。

[v7u_N003608|3608] Organizations file defensive SARs for several reasons, including staffing shortages, avoiding regulatory scrutiny, and lacking time to perform the necessary research to make an informed decision. Regulators often view defensive SARs as a temporary fix to avoid regulatory scrutiny, without considering the full effect on law enforcement.
ZH: 组织因人员短缺、避免监管审查等原因提交防御性可疑活动报告，监管机构通常将其视为临时措施。

[v7u_N003609|3609] Defensive SARs are a sign of weakness or deficiencies in an AFC compliance program.
ZH: 防御性可疑活动报告是金融犯罪防控合规计划存在弱点或缺陷的标志。

[v7u_N003610|3610] If an organization lacks sufficient time or a complete understanding of the business model necessary to properly monitor and research a customer activity, as a best practice, the organization should consider its business risk appetite and the relationship with the customer.
ZH: 当缺乏足够时间或对业务模式理解不足时，组织应考虑业务风险偏好和客户关系。

[v7u_N003611|3611] Simply filing defensive SARs ignores compliance program deficiencies and negatively affects the organization and law enforcement.
ZH: 仅仅提交防御性可疑活动报告会忽视合规计划缺陷，并对组织和执法部门产生负面影响。
```

allowed_unit_ids:

```json
[
  "v7u_N003602",
  "v7u_N003603",
  "v7u_N003604",
  "v7u_N003605",
  "v7u_N003606",
  "v7u_N003607",
  "v7u_N003608",
  "v7u_N003609",
  "v7u_N003610",
  "v7u_N003611"
]
```
