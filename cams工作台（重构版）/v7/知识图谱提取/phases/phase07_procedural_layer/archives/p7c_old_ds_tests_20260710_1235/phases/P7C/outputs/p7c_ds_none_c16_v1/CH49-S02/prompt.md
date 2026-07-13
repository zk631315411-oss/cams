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

section_id: `CH49-S02`

section_title: `Concluding an investigation and suspicious activity reporting > Duty to report`

section_text_with_unit_anchors:

```text
[v7u_N003475|3475] If an organization suspects that a customer is committing financial crime, it has a duty to report it to the authorities.
ZH: 组织若怀疑客户实施金融犯罪，有义务向当局报告。

[v7u_N003476|3476] In many countries, there is a personal liability to report financial crime, and there are legal penalties of fines and imprisonment for failing to do so.
ZH: 许多国家规定个人有报告金融犯罪的责任，不报告可能面临罚款和监禁等法律处罚。

[v7u_N003477|3477] However, an organization will have clearly defined policies and procedures to ensure reporting is clear and factual and to protect the relevant employees.
ZH: 组织应有明确定义的政策和程序，确保报告清晰、基于事实并保护相关员工。

[v7u_N003478|3478] Around the world, organizations appoint officers to be responsible for AFC programs and to report suspicions of financial crime.
ZH: 全球范围内，组织任命官员负责金融犯罪防控项目并报告可疑金融犯罪。

[v7u_N003479|3479] The title might be chief compliance officer, anti-bribery and corruption officer, AML officer, money laundering reporting officer, principal officer, chief anti-money laundering compliance officer, or a title reflective of the jurisdiction.
ZH: 官员头衔示例包括首席合规官、反贿赂反腐败官、反洗钱官、洗钱报告官等。

[v7u_N003480|3480] In many countries, there are legal consequences for individuals who fail to report financial crime or are suspected of financial crime. These range from heavy fines to imprisonment.
ZH: 许多国家对未报告金融犯罪或涉嫌金融犯罪的个人设有法律后果，包括高额罚款和监禁。

[v7u_N003481|3481] In some jurisdictions, an individual can be prosecuted for “willful blindness,” which will be judged on the circumstances surrounding the transaction and the defendant’s conduct.
ZH: 某些司法管辖区可起诉“故意视而不见”，依据交易情形和被告行为判断。

[v7u_N003482|3482] Courts define willful blindness as the “deliberate avoidance of knowledge of the facts” and have held that willful blindness is the equivalent of actual knowledge of the illegal source of funds or of the intentions of a customer in a financial crime transaction.
ZH: 故意视而不见被定义为“故意回避了解事实”，等同于实际知情。

[v7u_N003483|3483] It is important that organizations implement policies and procedures to enable staff to report their suspicions to an assigned compliance officer.
ZH: 机构应制定政策和程序，使员工能够向合规官报告可疑情况。

[v7u_N003484|3484] Staff must be properly trained in these procedures to ensure that both they and your organization meet the duty to report requirement.
ZH: 必须对员工进行报告程序培训，以满足报告义务。

[v7u_N003485|3485] The assigned compliance officer will be responsible for assessing the information and deciding what actions must be taken.
ZH: 合规官负责评估信息并决定应采取的行动。

[v7u_N003486|3486] The process might stop following the escalation of the potentially suspicious activity because the compliance officer considers the activity or explanation to be sufficient.
ZH: 若合规官认为活动或解释充分，升级流程可能终止。

[v7u_N003487|3487] If the facts indicate an external report must be made, the most usual action is the submission of a suspicious activity report to the relevant authority in the jurisdiction.
ZH: 若事实表明需对外报告，通常向主管机构提交可疑活动报告。

[v7u_N003488|3488] Reporting within agreed timelines ensures that the individual and the organization effectively discharge their responsibilities.
ZH: 在规定时限内报告可确保个人和机构有效履行职责。

[v7u_N003489|3489] Some jurisdictions may require unusual activities to be reported, in addition to those that are deemed suspicious.
ZH: 某些司法管辖区可能要求报告异常活动，而不仅限于可疑活动。
```

allowed_unit_ids:

```json
[
  "v7u_N003475",
  "v7u_N003476",
  "v7u_N003477",
  "v7u_N003478",
  "v7u_N003479",
  "v7u_N003480",
  "v7u_N003481",
  "v7u_N003482",
  "v7u_N003483",
  "v7u_N003484",
  "v7u_N003485",
  "v7u_N003486",
  "v7u_N003487",
  "v7u_N003488",
  "v7u_N003489"
]
```
