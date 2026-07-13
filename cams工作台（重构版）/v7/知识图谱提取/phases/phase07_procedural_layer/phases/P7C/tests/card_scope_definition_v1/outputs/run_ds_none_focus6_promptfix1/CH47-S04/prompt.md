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
what a control, tool, threshold, monitoring rule, or filing/reporting output is supposed to achieve
what limitation, safeguard, proportionality concern, or downstream use changes the judgement
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

Non-institution actor content should not be skipped automatically. If external actor behavior affects institution judgement, reporting, cooperation, downstream handling, or exam option judgement, extract it as a `judgement_card` from the institution/exam perspective. Do not model an external actor's operational workflow as `process_card` unless the section's main purpose is to teach that external process itself.

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

Use `judgement_card` even when there is no strict sequence if the section gives usable criteria, expected effects, limitations, safeguards, proportionality concerns, or downstream value for judging a business response or exam option.

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
a control or technology capability with criteria, limitations, safeguards, or expected effects
a threshold, parameter, tuning frequency, or event-triggered reassessment rule
a proportionality, control-overreach, access-barrier, or financial-inclusion judgement
external actor use that changes how an institution-side action or report should be valued
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

Do not skip merely because the material is non-chronological. If it provides criteria, effects, limits, safeguards, or proportionality rules for judgement, extract it as `judgement_card` and avoid fake process order.

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

section_id: `CH47-S04`

section_title: `Transaction monitoring > Transaction monitoring system tuning`

section_text_with_unit_anchors:

```text
[v7u_N003272|3272] TM system tuning is the process of refining and adjusting parameters and thresholds of specific detection logic rules, or scenarios. Scenarios are designed to detect suspicious activities and abnormal transaction behaviors, such as money laundering, fraud, or other illicit activities. Tuning is important because it:
ZH: 交易监控系统调优是调整检测规则参数和阈值的过程。

[v7u_N003273|3273] Ensures the TM system effectively detects suspicious activity.
ZH: 调优确保交易监控系统有效检测可疑活动。

[v7u_N003274|3274] Reduces false positives.
ZH: 调优减少误报。

[v7u_N003275|3275] Ensures efficient resource use.
ZH: 调优确保资源高效利用。

[v7u_N003276|3276] Allows organizations to manage changes in financial crime and in their business operations.
ZH: 调优使组织能够应对金融犯罪和业务运营的变化。

[v7u_N003277|3277] Ensures regulatory compliance.
ZH: 调优确保监管合规。

[v7u_N003278|3278] Tuning involves four key components: scenario setting, customer segmentation, threshold setting, and frequency.
ZH: 调优包括场景设置、客户细分、阈值设置和频率四个关键组成部分。

[v7u_N003279|3279] Scenario setting involves creating, modifying, or removing detection rules and scenarios based on previous experiences with suspicious activity and actual incidents.
ZH: 场景设置是基于以往经验创建、修改或移除检测规则和场景。

[v7u_N003280|3280] Threshold setting defines the minimum level of activity required for a transaction to trigger an alert.
ZH: 阈值设置定义了触发警报所需的最低活动水平。

[v7u_N003281|3281] For example, the threshold for reporting a CTR might be any currency transaction that exceeds US$10,000.
ZH: 货币交易报告（CTR）阈值示例：超过10,000美元的任何货币交易

[v7u_N003282|3282] Adjusting thresholds refines sensitivity and accuracy.
ZH: 调整阈值可提高交易监控系统的灵敏度和准确性

[v7u_N003283|3283] Reducing the number of false positives is a key goal in setting thresholds to make the most efficient use of resources.
ZH: 减少误报是设定阈值的关键目标，以高效利用资源

[v7u_N003284|3284] The frequency determines how often tuning should occur.
ZH: 调优频率决定了交易监控系统应多久进行一次调整

[v7u_N003285|3285] The frequency might also be influenced by changes in business strategy, anomalies, regulatory updates, or market changes.
ZH: 调优频率受业务策略变化、异常、监管更新或市场变化影响

[v7u_N003286|3286] Tuning should be dynamic, with special assessments triggered by significant events or trends.
ZH: 调优应是动态的，重大事件或趋势应触发专项评估
```

allowed_unit_ids:

```json
[
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
]
```
