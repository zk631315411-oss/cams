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

section_id: `CH47-S06`

section_title: `Transaction monitoring > Procedures for alerts review`

section_text_with_unit_anchors:

```text
[v7u_N003295|3295] In larger organizations, the process for reviewing transaction monitoring alerts typically involves multiple levels of review and information gathering.
ZH: 大型机构采用多级警报审查流程，涉及多级审查和信息收集

[v7u_N003296|3296] Smaller organizations might use a one-touch system, where a single analyst handles the alert from generation through the submission of a SAR.
ZH: 小型机构可能采用单点接触系统，由一名分析师处理从警报生成到提交可疑活动报告的全过程

[v7u_N003297|3297] When multiple levels of reviews are used, Level 1 review—or the initial review stage—occurs when a TM system generates an alert.
ZH: 一级审查是交易监控系统生成警报后的初始审查阶段

[v7u_N003298|3298] An analyst examines the alert’s validity by evaluating various data points, including the alert's nature, transaction type, customer profile, account history, and previous alert history.
ZH: 分析师通过评估警报性质、交易类型、客户资料、账户历史等数据点检查警报有效性

[v7u_N003299|3299] This analysis helps determine if the activity aligns with expected customer behavioral patterns.
ZH: 分析旨在确定活动是否符合预期的客户行为模式

[v7u_N003300|3300] If the activity appears abnormal or exceeds accepted thresholds, the alert escalates to Level 2 review for further investigation.
ZH: 若活动异常或超出阈值，警报升级至二级审查进行进一步调查

[v7u_N003301|3301] If not, the analyst can dismiss it as a false positive, and document sufficient rationale for arriving at that conclusion.
ZH: 分析师可将警报判定为误报并记录充分理由

[v7u_N003302|3302] During the Level 2 review, or investigation stage, analysts perform a detailed analysis of the alert and data from the initial review to establish whether the unusual behavior could indicate a financial crime. This stage typically includes:
ZH: 二级审查（调查阶段）对警报和数据进行详细分析以判断是否指向金融犯罪

[v7u_N003303|3303] Analyzing transaction patterns and frequency.
ZH: 分析交易模式和频率

[v7u_N003304|3304] Assessing the source and destination of funds.
ZH: 评估资金来源和去向

[v7u_N003305|3305] Reviewing KYC information and the customer risk profile.
ZH: 审查了解你的客户信息和客户风险画像

[v7u_N003306|3306] Gathering additional records, such as communication logs between the customer and institution, and any prior investigations related to the customer or account.
ZH: 收集额外记录，如客户与机构沟通记录及既往调查信息

[v7u_N003307|3307] Conducting open-source research to include social media, news articles, public records and notices, alerts, or guidance issued by law enforcement and regulatory agencies, to inform their opinion on the escalated activity.
ZH: 开展开源研究，包括社交媒体、新闻、公共记录及监管机构发布的警报和指引

[v7u_N003308|3308] Analysts then determine whether the activity is suspicious, providing a robust rationale based on the data collected.
ZH: 分析师基于收集的数据判定活动是否可疑并提供充分理由

[v7u_N003309|3309] Highly suspicious cases or those that involve numerous transactions or sensitive situations should be escalated to Level 3 review, or the complex analysis stage.
ZH: 高度可疑案件应升级至三级审查（复杂分析阶段）

[v7u_N003310|3310] Senior analysts or compliance officers conduct this comprehensive assessment, which might include cross-department collaboration, complex risk assessments, and intricate analysis of transaction networks.
ZH: 高级分析师或合规官开展全面评估，包括跨部门协作、复杂风险评估和交易网络分析

[v7u_N003311|3311] Throughout this process, analysts meticulously document each step and, if required, file SARs with regulatory authorities, ensuring they include all pertinent information and rationale.
ZH: 分析师在审查过程中详细记录每一步，必要时向监管机构提交可疑活动报告

[v7u_N003312|3312] Following the filing, ongoing monitoring is critical to mitigate further issues and identify additional criminal activities.
ZH: 提交可疑活动报告后需持续监控以防范进一步风险并识别其他犯罪活动

[v7u_N003313|3313] Analysts often recommend enhanced customer monitoring or account restrictions as preventive measures.
ZH: 分析师常建议加强客户监控或限制账户作为预防措施
```

allowed_unit_ids:

```json
[
  "v7u_N003295",
  "v7u_N003296",
  "v7u_N003297",
  "v7u_N003298",
  "v7u_N003299",
  "v7u_N003300",
  "v7u_N003301",
  "v7u_N003302",
  "v7u_N003303",
  "v7u_N003304",
  "v7u_N003305",
  "v7u_N003306",
  "v7u_N003307",
  "v7u_N003308",
  "v7u_N003309",
  "v7u_N003310",
  "v7u_N003311",
  "v7u_N003312",
  "v7u_N003313"
]
```
