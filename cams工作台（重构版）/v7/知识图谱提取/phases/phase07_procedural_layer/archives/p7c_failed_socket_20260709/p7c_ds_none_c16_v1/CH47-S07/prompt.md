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

section_id: `CH47-S07`

section_title: `Transaction monitoring > Other sources of investigation`

section_text_with_unit_anchors:

```text
[v7u_N003314|3314] AML investigations might originate from a wide range of sources beyond transaction monitoring systems. These sources include internal and external referrals, requests for information from counterparties or correspondent banks, negative news, regulatory findings and recommendations, and law enforcement requests.
ZH: 反洗钱调查来源包括内部和外部转介、信息请求、负面新闻、监管发现及执法请求

[v7u_N003315|3315] Internal referrals, can come from various departments—such as fraud, correspondent banks, branches, digital, and telephony teams—which are wellpositioned to identify suspicious activities. Internal hotlines and whistleblower complaints also serve as sources for AML investigations.
ZH: 内部转介可来自欺诈、代理行、分行、数字及电话团队等部门，内部热线和举报也是来源

[v7u_N003316|3316] External referrals come from sources outside the organization—such as concerned citizens and business partners—through their customer-facing employees or other channels.
ZH: 外部转介来自组织外部，如关注此事的公民和商业伙伴

[v7u_N003317|3317] Requests for information (RFI) from counterparties or correspondent banks are formal requests for clarification, data, or additional details that can arise from multiple contexts, such as customer due diligence and transaction monitoring.
ZH: 信息请求（RFI）是交易对手或代理行提出的正式澄清、数据或额外细节请求

[v7u_N003318|3318] For example, in the US, Sections 314a and 314b of the USA PATRIOT Act allow financial institutions and government agencies to share potential money laundering information. They allow access to a broader information network, enhancing the ability to detect suspicious activities and initiate reviews. Receiving such a request can trigger an additional internal investigation.
ZH: 美国《爱国者法案》第314a和314b条允许金融机构与政府机构共享潜在洗钱信息

[v7u_N003319|3319] Ongoing negative news screening programs and systems can identify information that prompts reviews and generates investigative leads.
ZH: 持续的负面新闻筛查程序可识别信息，触发审查并生成调查线索

[v7u_N003320|3320] Regulatory findings and recommendations can help identify additional risks and initiate reviews.
ZH: 监管发现和建议有助于识别额外风险并启动审查

[v7u_N003321|3321] Law enforcement agencies (LEA) may use legal instruments that require financial institutions to provide documents or information for investigations. These instruments include:
ZH: 执法机构可使用的法律工具列表引导

[v7u_N003322|3322] Court orders: A judge may direct the institution to release account information or transaction records related to an ongoing investigation.
ZH: 法院命令可要求金融机构提供账户信息或交易记录

[v7u_N003323|3323] Subpoenas: Legal requests compel the organization to produce specific communications or records relevant to a case.
ZH: 传票强制要求机构提供特定通信或记录

[v7u_N003324|3324] Search warrants: These court-issued permissions allow law enforcement agencies to search premises and documents. Information gathered from search warrants could also be sources of potentially suspicious activity.
ZH: 搜查令允许执法机构搜查场所和文件，可能发现可疑活动

[v7u_N003325|3325] Other: Direct inquiries from law enforcement can prompt a financial institution to investigate activities possibly linked to criminal activities.
ZH: 执法机构的直接询问可促使金融机构调查可能涉及犯罪的活动

[v7u_N003326|3326] Given the high likelihood of materiality and sensitivity, these investigation sources must be handled with extra care.
ZH: 调查来源具有高度重要性和敏感性，必须谨慎处理

[v7u_N003327|3327] It is particularly important to avoid tipping off a potential subject of an investigation.
ZH: 必须避免向调查对象通风报信

[v7u_N003328|3328] In some cases, tipping off is a felony that can result in criminal charges against the employee.
ZH: 通风报信在某些情况下属于重罪，员工可能面临刑事指控

[v7u_N003329|3329] For this reason, organizations should have robust procedures for the management of investigations that minimize the risk of information leaks.
ZH: 机构应制定稳健的调查管理程序以最大限度降低信息泄露风险
```

allowed_unit_ids:

```json
[
  "v7u_N003314",
  "v7u_N003315",
  "v7u_N003316",
  "v7u_N003317",
  "v7u_N003318",
  "v7u_N003319",
  "v7u_N003320",
  "v7u_N003321",
  "v7u_N003322",
  "v7u_N003323",
  "v7u_N003324",
  "v7u_N003325",
  "v7u_N003326",
  "v7u_N003327",
  "v7u_N003328",
  "v7u_N003329"
]
```
