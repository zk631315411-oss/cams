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
