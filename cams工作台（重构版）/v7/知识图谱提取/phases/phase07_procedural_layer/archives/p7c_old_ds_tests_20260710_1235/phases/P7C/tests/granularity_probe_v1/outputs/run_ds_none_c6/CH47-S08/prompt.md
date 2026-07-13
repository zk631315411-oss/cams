# P7C Section Judgement Card Extraction Prompt v1

## Role

You are a P7C section-local evidence-matching judgement card extractor.

Read one textbook section and extract zero or more `p7_card` objects. Each card must help a later system judge whether a question option, business handling, risk response, control, or assessment is consistent with CAMS requirements. The source of truth is `flow_nodes` + `flow_edges`.

## Boundary

Only use the current section.

Do not create `BRIDGES_TO`, clusters, scenario paths, explanations, Mermaid, draw.io, SVG, or PNG.

If the section contains no executable process, no assessment standard, no control requirement, no risk-indicator rule, and no discouraged practice useful for judging business handling or exam options, return an empty `cards` array and a concise `skip_reason`.

## Reading Order

Read `section_text_with_unit_anchors`. It is the only extraction source and contains unit anchors such as:

```text
[v7u_N003233|3233] Transaction monitoring systems generate alerts...
```

Use these `unit_id` values as evidence anchors. The `allowed_unit_ids` list is only a whitelist for evidence IDs.

Do not use core points, CP-unit edges, CP-CP edges, alias metadata, KG edges, or package-level summaries to infer card structure. If a card cannot be extracted from the section text itself, return no cards or mark the uncertain part as `needs_review`.

## Evidence-Matching Goal

The cards will be used later to match exam questions and options against textbook evidence. Therefore, a useful card is not only a workflow. It may also preserve:

```text
what situation or condition the section is talking about
what action, control, assessment, or judgement is expected
what standards, criteria, indicators, limits, or components must be considered
what output, effect, risk finding, deficiency, or consequence follows
what practice is discouraged, insufficient, or harmful
```

When deciding whether to extract, ask: could this section help judge whether an answer option is correct, incorrect, too broad, too narrow, or missing a condition? If yes, extract a card unless the evidence is too vague to model.

When a section contains several locally useful judgement units, do not extract only the final or most normative paragraph. Scan the whole section and preserve each distinct unit that would support a different option judgement. For example, a technology section may contain both: `technology capability used to detect risk patterns` and `controls required when implementing AI`. These may be separate cards if they have different triggers, standards, and outputs.

Technology capability material is useful when it states what a system checks, detects, identifies, analyzes, reduces, improves, or enables. Do not skip such material merely because it is descriptive. If the source describes a monitoring capability with its inputs, criteria, or expected detection effect, extract it as a `control`, `assessment`, or `risk_indicator` card. Model the capability as an action, the checked criteria or data features as `standard` or `input` nodes, and the detection/improvement effect as an `output` node.

## Extraction Scope

Extract a card only when the section provides at least one of these useful judgement structures:

```text
execution       what to do, in what order, and with what branch or output
assessment      how to judge, evaluate, screen, or determine a result
control         what control or governance requirement applies and what effect it should have
risk_indicator  what risk factor, red flag, or warning indicator should be used to identify elevated risk
```

Do not limit extraction to strict chronological processes. However, do not convert non-chronological judgement material into a fake sequence.

Use this default structure when the source is not a strict execution process:

```text
assessment:     start/trigger -> assess/check/review action --USES--> parallel standards -> output result/finding
control:        start/trigger -> apply/maintain/review control --USES--> inputs or standards -> output control effect
risk_indicator: start/trigger -> screen/review action --USES--> parallel indicators -> output risk finding
```

Before skipping, check whether the section contains any of the following:

```text
a control effectiveness requirement or expected control effect
an assessment or judgement standard
a risk indicator, red flag, or risk factor
an anti-pattern, discouraged practice, or negative consequence
a control-overreach, access barrier, financial-inclusion tradeoff, or risk-based balancing rule
a condition or trigger that changes the required handling
a business response useful for evaluating an exam option
```

If any item is present, do not skip. Extract the smallest useful `assessment`, `control`, or `risk_indicator` card. Use `review_status: "needs_review"` when the material is useful but not a strict process.

Skip purely descriptive background, isolated examples, technology capability descriptions, definitions, or historical notes only when they provide no judgement rule, control requirement, risk indicator, condition, limitation, or option-evaluation value.

Definitions may be extracted when they define a condition, threshold, control component, prohibited/discouraged pattern, or judgement category useful for evidence matching. Technology or control capability descriptions should be extracted when they state what the control should achieve, what it checks or detects, which criteria or data features it uses, how it should be tuned or reviewed, when it should be reassessed, or what its limitations are.

Financial inclusion, de-risking, and strict-control barrier material may be extracted when it helps judge whether a control response is proportionate, risk-based, or overly restrictive. Model the control burden or barrier as a standard or output, and the desired balanced handling as an assessment/control objective. Do not skip it merely because it is policy-oriented rather than a step-by-step process.

Examples may support `description` or `source_quote`, but do not promote an example into the main flow unless the section presents it as a required or generally applicable handling rule.

## Card Granularity

One card = one section-local, locally closed judgement unit with one primary objective.

A card should have:

```text
an entry point
a set of actions, decisions, standards, controls, or indicators
a clear output, stable result, or handoff point
```

Prefer fewer, clearer cards. Do not force a card when the section only defines concepts and gives no business-handling judgement value.

## Granularity Probe Addendum

This test prompt is probing whether card granularity can be improved without harming other sections.

Before finalizing output, run a card-boundary self-check:

```text
1. Does one proposed card contain multiple review levels, stages, phases, or named process layers?
2. Does one proposed card contain multiple independent decisions with different outputs?
3. Does one proposed card combine a review/investigation flow with a later reporting, monitoring, remediation, or restriction flow?
4. Would one proposed card likely exceed 12 flow_nodes or 15 flow_edges?
5. Would one proposed card require many functional_dependency edges merely to make a single flow graph close?
```

If the answer to any of these is yes, prefer multiple smaller cards, but only when each smaller card has a locally supported entry, action/decision/standard set, and output or handoff.

For sections with named levels or stages, such as `Level 1`, `Level 2`, `Level 3`, `initial review`, `investigation stage`, or `complex analysis stage`, do not automatically combine all levels into one macro card. Treat each level/stage as a candidate card boundary when the text gives that level/stage its own objective, criteria, escalation condition, output, or handoff.

Do not split parallel criteria used by the same action. For example, if one review action evaluates alert nature, transaction type, customer profile, account history, and prior alert history, keep those as `standard` nodes inside one card.

Do not split a control card only because it has multiple goals or components when those goals/components all support the same control action. For example, tuning goals, tuning components, AI safeguards, or defensive-SAR harms may remain within one card when they share one objective.

If you intentionally keep a large card because the source truly presents one indivisible local process, explain why in `review_notes` and set `review_status: "needs_review"`.

Split a section into multiple cards when it contains separate local process objectives that can each stand on their own. A common case is:

```text
primary assessment flow
remediation or corrective-action subflow
```

For example, an assessment/result-calculation flow and a remediation/corrective-action workflow may be separate cards if each has its own entry, decision point, and output.

Another common case is an optional preliminary path plus a main process. For example, a pre-onboarding committee suitability assessment for specific customer profiles should usually be a separate card from the typical KYC/CDD process if both have their own entry, decision, and output.

Another common case is capability-plus-control material. Extract separate cards when the source first describes what a monitoring/control capability is used for and later describes the controls, limitations, or safeguards for implementing that capability.

For technology capability cards, prefer one card per local capability family, not one card per sentence. For example, if several units describe intelligent transaction monitoring tools that analyze transactions, identify hidden links, compare behavior against thresholds or peer/history patterns, and reduce false positives, combine them into one capability card. If a later paragraph describes AI implementation safeguards such as bias testing, explainability, transparency, and relevance, make that a separate control card.

Do not over-split examples, definitions, list items, or parallel standards into separate cards. Parallel standards should usually remain nodes inside the same card and be connected with `USES` edges.

Risk-factor material may be extracted as an assessment or risk-indicator card when it gives usable screening or evaluation criteria, even if it does not specify a step-by-step workflow. In that case, set `card_nature` to `assessment` or `risk_indicator`, model the risk indicators as `standard` nodes used by an `action` such as assess, review, or screen, and explain in `review_notes` that the card is not a strict operating workflow.

For `risk_indicator` cards, do not force a chronological sequence among risk factors. The usual structure is `start/trigger -> assess/review/screen action`, parallel `standard` nodes connected by `USES`, and an `output` risk finding.

Discouraged-practice or anti-pattern material should usually be extracted as `assessment` or `control`, not as a new card nature. Model the questionable practice as a trigger, input, or standard; model the harm, deficiency, or required judgement as outputs or standards. If helpful, add optional metadata such as:

```json
{
  "negative_pattern": true,
  "evidence_matching_value": "high",
  "not_strict_workflow": true,
  "missing_context_risk": false
}
```

Metadata is optional. It must not replace `flow_nodes`, `flow_edges`, evidence IDs, or review notes.

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

Use `execution` for strict operational handling sequences. Use `assessment`, `control`, or `risk_indicator` for non-sequential judgement material that is still useful for deciding whether a business response is CAMS-compliant.

## Card Nature Decision Rules

Choose `card_nature` by the card's primary objective, not by the mere presence of actions or decisions.

Use `execution` when the card's primary objective is to perform an operational process or handling sequence, such as collecting information, verifying identity, conducting screening, filing a report, escalating a case, reviewing alerts, or completing a monitoring workflow.

Use `assessment` when the card's primary objective is to:

```text
evaluate a profile, control, risk, result, or suitability
screen against criteria
determine whether to proceed
determine risk level
determine required due diligence or handling level
decide whether standard or enhanced handling is required
```

This remains `assessment` even if the card has a trigger, action node, decision node, and output branches.

Use `control` when the card's primary objective is to state a control or governance requirement, its applicable context, and its expected control effect. A control card may be non-chronological.

Use `risk_indicator` when the source mainly lists risk factors, red flags, or warning indicators used to identify elevated risk or problematic conduct.

If the boundary between card natures is uncertain, choose the closest primary objective, set `review_status` to `needs_review`, and explain the boundary issue in `review_notes`.

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

For later retrieval and evidence matching, preserve important condition words in titles and node labels, such as `when`, `if`, `unless`, `insufficient`, `defensive`, `effective`, `residual risk`, `tuning`, `threshold`, `high risk`, `significant event`, and similar source-supported qualifiers. Do not hide exceptions, limits, negative consequences, or branch conditions inside generic labels.

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

Use `FEEDBACK` only when a result updates an `output`, `input`, or `standard` node, such as updating a risk profile, threshold, finding, record, or criterion. Do not use `FEEDBACK` to point back to an `action`, `decision`, `trigger`, or `start` node. If research or review loops back to another action, use `PRECEDES` with `evidence_strength: "functional_dependency"` or model the loop through a `decision` node with `DECIDES` edges.

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
5. Do not turn parallel assessment dimensions into a chronological chain. When the source says `both A and B`, `A and B`, `includes A and B`, `consists of A and B`, `key elements include`, or similar list language, treat the items as parallel standards, inputs, outputs, or branches unless the source explicitly states sequence. Keep all parallel criteria that affect judgement; do not collapse them into one vague node.
6. For assessment, control, and risk-indicator cards, prefer `action --USES--> standard` edges for criteria, requirements, controls, indicators, and judgement dimensions. For example, `Evaluate control effectiveness --USES--> design effectiveness` and `Evaluate control effectiveness --USES--> operational effectiveness` is better than `design effectiveness --PRECEDES--> operational effectiveness` unless the source explicitly states that sequence.
7. Use `PRECEDES` only for explicit or strongly implied process order. If an edge is a `functional_dependency` rather than explicit sequence, add `review_status: "needs_review"` and explain in card `review_notes` whether it represents a parallel assessment dimension, condition dependency, outcome inference, or weak sequence reconstruction.
8. `evidence_unit_ids` must never be an empty list. Every edge must cite at least one current-section `unit_id` from `allowed_unit_ids`.
9. `qualifier` is optional and must be one of: `input`, `standard`, `context`, `record`, `finding`. Do not output any other qualifier value. In particular, do not use `output`, `effect`, `result`, `control`, `branch`, or free-text explanations as qualifier values. If no allowed qualifier fits, omit `qualifier`. Put explanations in `review_notes` or `source_quote` instead.

When setting card-level `review_status: "needs_review"`, explain the reason in `review_notes`. Use one or more of these categories when applicable: weak inferred process order; non-procedural source material converted into an assessment/control/risk-indicator card; possible card granularity problem; missing downstream handoff; limited single-unit evidence; useful option-evaluation material but not a strict workflow; other.

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
  "skip_reason": "No section-level executable process, assessment standard, control requirement, or risk-indicator rule found."
}
```

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
