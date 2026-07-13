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

section_id: `CH49-S13`

section_title: `Concluding an investigation and suspicious activity reporting > How law enforcement case investigators read a SAR`

section_text_with_unit_anchors:

```text
[v7u_N003645|3645] If an AFC program were a factory, suspicious activity reports (SAR) would be its most important product and law enforcement would be its main customer.
ZH: 可疑活动报告（SAR）是金融犯罪防控（金融犯罪防控）项目最重要的产品，执法部门是其主要客户

[v7u_N003646|3646] SARs can be used to initiate an investigation or enhance an ongoing investigation.
ZH: SAR可用于启动调查或增强正在进行的调查

[v7u_N003647|3647] Law enforcement and the intelligence community use these reports to respond to illicit activity and gather intelligence useful in preventing future occurences.
ZH: 执法和情报界利用SAR报告应对非法活动并收集情报以预防未来事件

[v7u_N003648|3648] SAR data contains critical details to identify suspects, networks, jurisdictions, and, most importantly, the movement of illicit funds.
ZH: SAR数据包含识别嫌疑人、网络、司法管辖区和非法资金流动的关键细节

[v7u_N003649|3649] SARs offer an abundance of direct and indirect access to evidence of money laundering and the illicit activity that fuels it.
ZH: SAR提供直接和间接获取洗钱及上游非法活动证据的丰富途径

[v7u_N003650|3650] However, SARs cannot be used as evidence.
ZH: SAR不能作为证据使用

[v7u_N003651|3651] The most important purpose of SARs is to assist law enforcement and analysts in collecting information and intelligence on potential illegal activity.
ZH: SAR最重要的目的是协助执法和分析人员收集潜在非法活动的信息和情报

[v7u_N003652|3652] The phrase “follow the money” routinely proves to be true.
ZH: “跟着钱走”这句话在实践中经常被证明是正确的

[v7u_N003653|3653] These reports are invaluable in initiating new cases, enhancing ongoing investigations, and developing broader financial intelligence activity monitoring.
ZH: SAR在启动新案件、增强现有调查和制定更广泛的金融情报活动监测方面具有不可估量的价值

[v7u_N003654|3654] The SAR form data and narrative are critical for law enforcement and analysts to leverage in the field.
ZH: SAR表格数据和叙述对于执法和分析人员在实地工作中至关重要

[v7u_N003655|3655] Once they access the relevant database, they can effectively search names, identifiers, data, filing and subject entities, and vital narrative information.
ZH: 执法部门访问相关数据库后可有效搜索姓名、标识符、数据、备案和主体实体以及关键叙述信息

[v7u_N003656|3656] Law enforcement will look at these reports to identify what the illicit activity was, where and when it occurred, what products were used to facilitate the activity, and—most importantly—why it is considered suspicious.
ZH: 执法部门通过SAR识别非法活动内容、地点、时间、使用的产品以及被认定为可疑的原因

[v7u_N003657|3657] They can also search a SAR database to see if a suspect is mentioned in other SARs, which institution filed, and where the illicit money might have gone.
ZH: 执法部门可搜索SAR数据库查看嫌疑人是否出现在其他SAR中、由哪家机构提交以及非法资金可能流向何处

[v7u_N003658|3658] Based on the pattern of activity—who, what, where, when, how, and why—law enforcement might develop or add criminal charges for the underlying activity and possible money laundering.
ZH: 基于活动模式（谁、什么、地点、时间、方式、原因），执法部门可能增加或提出相关犯罪和洗钱指控

[v7u_N003659|3659] Law enforcement may be able to follow the money and other supporting data, determine other criminals involved in the activity, and expand the investigation further.
ZH: 执法部门可追踪资金和其他支持数据，确定其他涉案犯罪分子并扩大调查范围
```

allowed_unit_ids:

```json
[
  "v7u_N003645",
  "v7u_N003646",
  "v7u_N003647",
  "v7u_N003648",
  "v7u_N003649",
  "v7u_N003650",
  "v7u_N003651",
  "v7u_N003652",
  "v7u_N003653",
  "v7u_N003654",
  "v7u_N003655",
  "v7u_N003656",
  "v7u_N003657",
  "v7u_N003658",
  "v7u_N003659"
]
```
