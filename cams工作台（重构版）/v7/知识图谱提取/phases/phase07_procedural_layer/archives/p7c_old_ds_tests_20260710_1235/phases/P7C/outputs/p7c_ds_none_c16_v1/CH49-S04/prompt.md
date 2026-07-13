# P7C Section Judgement Card Extraction Prompt v1

## Role

You are a P7C section-local procedural and judgement card extractor.

Read one textbook section and extract zero or more `p7_card` objects. Each card must help judge whether a business handling, risk response, control, or assessment is consistent with CAMS requirements. The source of truth is `flow_nodes` + `flow_edges`.

## Boundary

Only use the current section.

Do not create `BRIDGES_TO`, clusters, scenario paths, explanations, Mermaid, draw.io, SVG, or PNG.

If the section contains no executable process, no assessment standard, no control requirement, and no risk-indicator rule useful for judging business handling, return an empty `cards` array and a concise `skip_reason`.

## Reading Order

Read `section_text_with_unit_anchors`. It is the only extraction source and contains unit anchors such as:

```text
[v7u_N003233|3233] Transaction monitoring systems generate alerts...
```

Use these `unit_id` values as evidence anchors. The `allowed_unit_ids` list is only a whitelist for evidence IDs.

Do not use core points, CP-unit edges, CP-CP edges, alias metadata, KG edges, or package-level summaries to infer card structure. If a card cannot be extracted from the section text itself, return no cards or mark the uncertain part as `needs_review`.

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

Skip purely descriptive background, isolated examples, technology capability descriptions, definitions, or historical notes unless they provide a clear judgement rule, control requirement, or risk indicator.

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
6. For assessment, control, and risk-indicator cards, prefer `action --USES--> standard` edges for criteria, requirements, controls, indicators, and judgement dimensions. For example, `Evaluate control effectiveness --USES--> design effectiveness` and `Evaluate control effectiveness --USES--> operational effectiveness` is better than `design effectiveness --PRECEDES--> operational effectiveness` unless the source explicitly states that sequence.
7. Use `PRECEDES` only for explicit or strongly implied process order. If an edge is a `functional_dependency` rather than explicit sequence, add `review_status: "needs_review"` and explain in card `review_notes` whether it represents a parallel assessment dimension, condition dependency, outcome inference, or weak sequence reconstruction.
8. `evidence_unit_ids` must never be an empty list. Every edge must cite at least one current-section `unit_id` from `allowed_unit_ids`.
9. `qualifier` is optional and must be one of: `input`, `standard`, `context`, `record`, `finding`. Do not put explanatory sentences in `qualifier`; put explanations in `review_notes` or `source_quote` instead.

When setting card-level `review_status: "needs_review"`, explain the reason in `review_notes`. Use one or more of these categories when applicable: weak inferred process order; non-procedural source material converted into an assessment/control/risk-indicator card; possible card granularity problem; missing downstream handoff; limited single-unit evidence; other.

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

section_id: `CH49-S04`

section_title: `Concluding an investigation and suspicious activity reporting > Suspicious activity report structure`

section_text_with_unit_anchors:

```text
[v7u_N003511|3511] The suspicious activity report (SAR) is the primary method of communicating suspicious activity to law enforcement.
ZH: 可疑活动报告（SAR）是向执法机构报告可疑活动的主要方式。

[v7u_N003512|3512] Completing the SAR requires gathering information about all parties involved, including names, birthdates, addresses, tax identification numbers or national identification numbers, and phone numbers. Include dates and documentation of the suspicious activity, reports from branch staff, video from automated teller machines, and images of relevant paper items.
ZH: 填写SAR需要收集所有相关方的信息，包括姓名、出生日期、地址、税号或身份证号、电话号码，以及可疑活动的日期和文件等。

[v7u_N003513|3513] The SAR form requires information about:
ZH: SAR表格要求提供以下信息：

[v7u_N003514|3514] The filing institution
ZH: SAR表格要求提供申报机构的信息。

[v7u_N003515|3515] The suspicious activity location, such as the branch
ZH: SAR表格要求提供可疑活动发生地点，例如分行。

[v7u_N003516|3516] The regulator
ZH: 可疑活动报告（SAR）中需包含监管机构信息

[v7u_N003517|3517] A point of contact for law enforcement’s use during an investigation
ZH: SAR中需提供执法机构调查时的联系人信息

[v7u_N003518|3518] The narrative—a written description of the suspicious activity—is the most important part of the SAR. It includes the introduction, background, transaction, and conclusion paragraphs.
ZH: SAR叙述部分是最重要的内容，包括引言、背景、交易和结论段落

[v7u_N003519|3519] The organization will develop policies, processes, and procedures for filing SARs consistent with the requirements set by the FIU and its regulator.
ZH: 机构应制定符合金融情报机构和监管机构要求的SAR提交政策与程序

[v7u_N003520|3520] Compliance with these standards and accurately completing all required fields are crucial for communicating to law enforcement the suspicious transactions and possible criminal activities you identified and investigated.
ZH: 准确填写SAR所有必填字段对于向执法机构传达可疑交易和犯罪活动至关重要

[v7u_N003521|3521] The SAR form begins with a request for the report type—initial or continuing— along with steps for submitting it.
ZH: 可疑活动报告表首先要求填写报告类型（首次或持续）及提交步骤。

[v7u_N003522|3522] The organization will likely provide an internal control number, which is useful for law enforcement reference and for locating the file in the database later or filing SARs for continuing activity.
ZH: 机构通常会提供内部控制编号，便于执法机构引用及后续查找档案。

[v7u_N003523|3523] The form also requires demographic information about the subjects involved.
ZH: SAR表格还要求填写涉案主体的人口统计信息。

[v7u_N003524|3524] If the subject is unknown, communicate that fact in the SAR form and narrative paragraph.
ZH: 若主体不明，应在SAR表格及叙述段落中说明。

[v7u_N003525|3525] The organization should provide information regarding the primary regulator and the location of the activity—whether in a branch, home office, automated teller machine, or multiple locations. The SAR should include the name and contact information for the primary case investigator on the form and in the narrative.
ZH: SAR应提供主要监管机构、活动地点及主要调查员联系信息。

[v7u_N003526|3526] The person completing the SAR should indicate any contact with law enforcement. If the organization files a SAR after receiving a subpoena or judgment, the SAR should specify the issuing law enforcement agency.
ZH: 填写SAR的人员应注明与执法机构的任何接触，若因传票或判决而提交，应指明签发机构。

[v7u_N003527|3527] The most important component of the SAR is the narrative, which answers the who, what, where, when, why, and how of the case.
ZH: SAR最重要的部分是叙述，回答案件的谁、什么、地点、时间、原因和方式。

[v7u_N003528|3528] The introductory sentence, or impact statement, is designed to compel an action or response from law enforcement and is key to the narrative.
ZH: 引言句或影响陈述旨在促使执法机构采取行动，是叙述的关键。
```

allowed_unit_ids:

```json
[
  "v7u_N003511",
  "v7u_N003512",
  "v7u_N003513",
  "v7u_N003514",
  "v7u_N003515",
  "v7u_N003516",
  "v7u_N003517",
  "v7u_N003518",
  "v7u_N003519",
  "v7u_N003520",
  "v7u_N003521",
  "v7u_N003522",
  "v7u_N003523",
  "v7u_N003524",
  "v7u_N003525",
  "v7u_N003526",
  "v7u_N003527",
  "v7u_N003528"
]
```
