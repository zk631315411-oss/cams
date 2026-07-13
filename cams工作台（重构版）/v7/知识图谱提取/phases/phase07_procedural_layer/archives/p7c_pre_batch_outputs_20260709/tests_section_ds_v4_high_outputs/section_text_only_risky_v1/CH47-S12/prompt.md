# P7C Section Flow Card Extraction Prompt v1

## Role

You are a P7C section-local execution flow extractor.

Read one textbook section and extract zero or more `p7_card` objects. Each card is a local executable flowchart. The source of truth is `flow_nodes` + `flow_edges`.

## Boundary

Only use the current section.

Do not create `BRIDGES_TO`, clusters, scenario paths, explanations, Mermaid, draw.io, SVG, or PNG.

If there is no executable process, return an empty `cards` array and a concise `skip_reason`.

## Reading Order

Read `section_text_with_unit_anchors`. It is the only extraction source and contains unit anchors such as:

```text
[v7u_N003233|3233] Transaction monitoring systems generate alerts...
```

Use these `unit_id` values as evidence anchors. The `allowed_unit_ids` list is only a whitelist for evidence IDs.

Do not use core points, CP-unit edges, CP-CP edges, alias metadata, KG edges, or package-level summaries to infer flow structure. If a process cannot be extracted from the section text itself, return no cards or mark the uncertain part as `needs_review`.

## Card Granularity

One card = one section-local, locally closed handling process with one primary process objective.

A card should have:

```text
an entry point
a set of actions or decisions
a clear output, stable result, or handoff point
```

Prefer fewer, clearer cards. Do not force a card when the section only defines concepts.

Split a section into multiple cards when it contains separate local process objectives that can each stand on their own. A common case is:

```text
primary assessment flow
remediation or corrective-action subflow
```

For example, an assessment/result-calculation flow and a remediation/corrective-action workflow may be separate cards if each has its own entry, decision point, and output.

Another common case is an optional preliminary path plus a main process. For example, a pre-onboarding committee suitability assessment for specific customer profiles should usually be a separate card from the typical KYC/CDD process if both have their own entry, decision, and output.

Do not over-split examples, definitions, list items, or parallel standards into separate cards. Parallel standards should usually remain nodes inside the same card and be connected with `USES` edges.

Risk-factor material may be extracted as an assessment or risk-indicator card only when it gives usable screening or evaluation criteria. In that case, set `card_nature` to `assessment` or `risk_indicator`, model the risk indicators as `standard` nodes used by an `action` such as assess, review, or screen, and explain in `review_notes` that the card is not a strict operating workflow.

For `risk_indicator` cards, do not force a chronological sequence among risk factors. The usual structure is `start/trigger -> assess/review/screen action`, parallel `standard` nodes connected by `USES`, and an `output` risk finding.

## Required Card Fields

Each card must include:

```text
card_id
section_id
card_nature
title
flow_nodes
flow_edges
source_unit_ids
review_status
```

`card_nature` must be one of:

```text
execution       strict execution process: trigger, steps, branches, output
assessment      judgement process: assessment object, criteria, result
risk_indicator  risk-factor or red-flag card: risk scenario, indicators, risk conclusion
control         control or governance requirement: control action, control objective, applicable context, expected effect
```

Use `execution` or `control` for what-to-do paths. Use `assessment` or `risk_indicator` for how-to-judge standards and scenario triggers.

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

`summary` is only a human-readable description. `scenario`, `trigger`, and `objective` are retrieval or review aids. The formal trigger should be represented as a `trigger` node when the source text supports it.

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

`review_status` must be exactly one of:

```text
needs_review
accepted
rejected
```

Do not output `reviewed`, `pass`, `valid`, `ok`, or other review status values.

Rules:

1. Every card must contain at least one `start` or `trigger` node.
2. A `start` node may be structural, but it must not add business action not stated by the source.
3. If the source text states a clear trigger condition or trigger event, create a `trigger` node.
4. Any `input`, `standard`, or `output` referenced by `USES`, `PRODUCES`, or `FEEDBACK` must appear as a node.
5. Do not create an `end` node unless it can cite at least one current-section `unit_id`. If the local exit is only inferred, use an `output` node with evidence instead of adding an unsupported `end` node.
6. `evidence_unit_ids` must never be an empty list. Every node must cite at least one current-section `unit_id` from `allowed_unit_ids`.

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

1. `source` and `target` must reference `node_id` values in the same card.
2. Conditional branches must use a `decision` node and `DECIDES` edges.
3. Every `DECIDES` edge must include `condition`, such as `yes`, `no`, `if needed`, `if explainable`, or `if potentially suspicious`.
4. Do not use `PRECEDES` to hide a condition branch.
5. Do not turn parallel assessment dimensions into a chronological chain. When the source says `both A and B`, `A and B`, `includes A and B`, `consists of A and B`, `key elements include`, or similar list language, treat the items as parallel standards, inputs, outputs, or branches unless the source explicitly states sequence.
6. For assessment/checking processes, prefer `action --USES--> standard` edges for evaluation criteria. For example, `Evaluate control effectiveness --USES--> design effectiveness` and `Evaluate control effectiveness --USES--> operational effectiveness` is better than `design effectiveness --PRECEDES--> operational effectiveness` unless the source explicitly states that sequence.
7. Use `PRECEDES` only for explicit or strongly implied process order. If an edge is a `functional_dependency` rather than explicit sequence, add `review_status: "needs_review"` and explain in card `review_notes` whether it represents a parallel assessment dimension, condition dependency, outcome inference, or weak sequence reconstruction.
8. `evidence_unit_ids` must never be an empty list. Every edge must cite at least one current-section `unit_id` from `allowed_unit_ids`.
9. `qualifier` is optional and must be one of: `input`, `standard`, `context`, `record`, `finding`. Do not put explanatory sentences in `qualifier`; put explanations in `review_notes` or `source_quote` instead.

When setting card-level `review_status: "needs_review"`, explain the reason in `review_notes`. Use one or more of these categories when applicable: weak inferred process order; non-procedural source material converted into an assessment card; possible card granularity problem; missing downstream handoff; limited single-unit evidence; other.

Card-level `review_status` must be exactly one of:

```text
needs_review
accepted
rejected
```

Do not output `reviewed`, `pass`, `valid`, `ok`, or other review status values.

## Evidence Strength

Use only:

```text
explicit
functional_dependency
needs_review
rejected
```

Do not use `co_listed_input`, `weak_inference`, `no_relation`, `high`, `medium`, or `low`.

Evidence must be current-section unit evidence. Do not cite CP titles, P2B labels, or alias metadata as evidence.

Only use IDs listed in `allowed_unit_ids`. Do not invent unit IDs.

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
      "card_nature": "execution",
      "title": "Short card title",
      "summary": "Optional one-sentence human-readable description.",
      "flow_nodes": [
        {
          "node_id": "n_start",
          "node_type": "start",
          "label": "Start",
          "evidence_unit_ids": ["v7u_..."],
          "evidence_strength": "functional_dependency",
          "review_status": "needs_review"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7flowedge_<section_id>_001_001",
          "edge_type": "PRECEDES",
          "source": "n_start",
          "target": "n_action_01",
          "evidence_unit_ids": ["v7u_..."],
          "evidence_strength": "functional_dependency",
          "review_status": "needs_review"
        }
      ],
      "source_unit_ids": ["v7u_..."],
      "review_status": "needs_review",
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
  "skip_reason": "No section-level executable process found."
}
```

## Current Section

section_id: `CH47-S12`

section_title: `Transaction monitoring > Communicating with customers`

section_text_with_unit_anchors:

```text
[v7u_N003371|3371] At times it will be necessary to engage with customers to gather additional information for due diligence or investigative purposes. Customer-facing employees, such as relationship managers, typically conduct these meetings, as they might already have a relationship with the customer.
ZH: 必要时需与客户接触以收集尽职调查或调查所需的额外信息，通常由客户经理等面向客户的员工进行。

[v7u_N003372|3372] Some jurisdictions require advanced notification to customers that the organization will collect information.
ZH: 某些司法管辖区要求提前通知客户机构将收集信息。

[v7u_N003373|3373] Even if not required, providing this notice is advisable, as it helps reduce the impression that the organization is asking unnecessary questions. It is also advisable to tell the customer how the data will be used.
ZH: 即使未要求，也建议提前通知客户并说明数据用途，以减少客户疑虑。

[v7u_N003374|3374] Customers are often wary of giving out personal information because they believe it will be used for marketing, resold, or otherwise compromised.
ZH: 客户常因担心个人信息被用于营销、转售或泄露而不愿提供。

[v7u_N003375|3375] There is a difference between anonymity and discretion. Discretion is good, and commonly sought by customers, so assure them that the organization will treat their data with care and in adherence with relevant data regulations.
ZH: 区分匿名与谨慎，向客户保证机构将谨慎处理数据并遵守数据法规。

[v7u_N003376|3376] Having good interpersonal skills and engaging in a conversational manner is more likely to put the customer at ease, as opposed to making the meeting feel like an interrogation.
ZH: 良好的人际交往能力和对话式沟通更容易让客户放松，而非像审讯。

[v7u_N003377|3377] The staff member should allow the customer to speak freely.
ZH: 工作人员应允许客户自由发言。

[v7u_N003378|3378] Using a template and script ensures that all required information is collected with an appropriate level of detail.
ZH: 使用模板和脚本可确保以适当详细程度收集所有必要信息。

[v7u_N003379|3379] However, it is important for the staff member to remain alert to customer responses that might require follow-up or clarification.
ZH: 工作人员必须对客户可能需要跟进或澄清的回应保持警觉。

[v7u_N003380|3380] If the staff member puts the customer at ease, but that customer is uncooperative, this might raise suspicions. While not every uncooperative customer is laundering money, many violations could have been prevented had suspicions been raised earlier.
ZH: 客户不合作可能引起怀疑，许多违规行为本可通过及早怀疑而预防。

[v7u_N003381|3381] Finally, ensure the meeting provides enough reliable detail to verify the information through other sources. Record the details of the meeting in writing as soon as possible to ensure a complete and accurate record.
ZH: 及时书面记录会议细节，确保信息可验证
```

allowed_unit_ids:

```json
[
  "v7u_N003371",
  "v7u_N003372",
  "v7u_N003373",
  "v7u_N003374",
  "v7u_N003375",
  "v7u_N003376",
  "v7u_N003377",
  "v7u_N003378",
  "v7u_N003379",
  "v7u_N003380",
  "v7u_N003381"
]
```
