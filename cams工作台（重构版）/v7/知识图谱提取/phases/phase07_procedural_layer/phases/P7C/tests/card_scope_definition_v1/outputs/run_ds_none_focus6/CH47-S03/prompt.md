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

section_id: `CH47-S03`

section_title: `Transaction monitoring > Technology solutions for transaction monitoring`

section_text_with_unit_anchors:

```text
[v7u_N003256|3256] Organizations are actively seeking and implementing solutions that generate more useful alerts that reduce wasteful efforts caused by false positives. They continuously improve their ability to manage financial crime risk by assigning resources to mitigate genuine threats to the business.
ZH: 机构积极寻求和实施能生成更有用警报的解决方案，以减少误报并持续改进风险管理。

[v7u_N003257|3257] For example, intelligent contextual analysis operates on a binary rule to check if a transaction exceeds a threshold and meets additional criteria. These criteria might include changes from a customer’s past behavior compared to their history and their peers, or if the customer is transacting in a higher-risk industry sector.
ZH: 智能上下文分析基于二元规则检查交易是否超过阈值并满足额外条件，如行为变化或行业风险。

[v7u_N003258|3258] Network analysis detects patterns among beneficiaries and others in a customer's network, helping uncover connections that might otherwise go unnoticed.
ZH: 网络分析检测客户网络中受益人及其他方之间的模式，揭示可能被忽略的关联。

[v7u_N003259|3259] These tools can automatically analyze transactions and identify hidden links between customers without manual intervention.
ZH: 这些工具可自动分析交易并发现客户间的隐藏关联，无需人工干预。

[v7u_N003260|3260] This saves a significant amount of time by eliminating the need to manually track and trace related transactions.
ZH: 自动化节省了大量手动追踪和追溯相关交易的时间。

[v7u_N003261|3261] These automated systems can check vast amounts of data instantly.
ZH: 自动化系统可即时检查海量数据。

[v7u_N003262|3262] They can identify connections between corporate accounts based on common data features, such as email domains, phone numbers, and addresses.
ZH: 系统通过共同数据特征识别企业账户间的关联。

[v7u_N003263|3263] Manual checks of this data would be time consuming and labor intensive.
ZH: 人工检查此类数据耗时且劳动密集。

[v7u_N003264|3264] Technology developments in AI have improved this process, equipping compliance staff with better tools in the fight against financial crime.
ZH: 人工智能技术发展为合规人员提供了更好的金融犯罪打击工具。

[v7u_N003265|3265] AI-powered transaction monitoring is revolutionizing how organizations prevent and detect fraud. By leveraging advanced algorithms and machine learning techniques, these systems analyze vast amounts of transaction data in real time. This helps organizations identify suspicious patterns and behaviors that might indicate fraud or money laundering.
ZH: AI驱动的交易监控通过实时分析大量数据革新欺诈和洗钱检测。

[v7u_N003266|3266] As transaction monitoring technologies evolve, AFC professionals should stay informed about advances in AI, machine learning, and data analytics. These professionals benefit from collaborating with IT, attending industry conferences, and participating in training programs.
ZH: 金融犯罪防控专业人员应了解AI、机器学习等进展，并与IT部门合作。

[v7u_N003267|3267] Actively monitoring technology developments will help them adopt effective solutions, enhance detection, and adapt to emerging fraud and money laundering risks.
ZH: 积极监控技术发展有助于采用有效方案、增强检测并适应新兴风险。

[v7u_N003268|3268] Implementing AI solutions comes with its own risks.
ZH: 实施AI解决方案本身存在风险。

[v7u_N003269|3269] These solutions must be tested with diverse data sets to help eliminate bias.
ZH: AI解决方案必须用多样化数据集测试以消除偏见。

[v7u_N003270|3270] They should also be explainable, transparent, and relevant to the organization’s specific context.
ZH: AI应具备可解释性、透明性并与组织具体情境相关。

[v7u_N003271|3271] With proper care and diligence, AI can support effective financial crime risk management.
ZH: 在适当谨慎下，AI可支持有效的金融犯罪风险管理。
```

allowed_unit_ids:

```json
[
  "v7u_N003256",
  "v7u_N003257",
  "v7u_N003258",
  "v7u_N003259",
  "v7u_N003260",
  "v7u_N003261",
  "v7u_N003262",
  "v7u_N003263",
  "v7u_N003264",
  "v7u_N003265",
  "v7u_N003266",
  "v7u_N003267",
  "v7u_N003268",
  "v7u_N003269",
  "v7u_N003270",
  "v7u_N003271"
]
```
