# P7C Section Flow Card Extraction Prompt v1

## Role

You are a P7C section-local execution flow extractor.

Read one textbook section and extract zero or more `p7_card` objects. Each card is a local executable flowchart. The source of truth is `flow_nodes` + `flow_edges`.

## Boundary

Only use the current section.

Do not create `BRIDGES_TO`, clusters, scenario paths, explanations, Mermaid, draw.io, SVG, or PNG.

If there is no executable process, return an empty `cards` array and a concise `skip_reason`.

## Reading Order

First read `section_text_with_unit_anchors`. It is the primary source and contains unit anchors such as:

```text
[v7u_N003233|3233] Transaction monitoring systems generate alerts...
```

Use these `unit_id` values as evidence anchors. Auxiliary files may be used only for evidence confirmation and structure.

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

## Card Nature Decision Rules

Choose `card_nature` by the card's primary objective, not by the mere presence of actions or decisions.

Use `assessment` when the card's primary objective is to:

```text
assess suitability
evaluate a profile, control, risk, or result
screen against criteria
determine whether to proceed
determine risk level
determine required due diligence level
decide whether standard or enhanced handling is required
```

This remains `assessment` even if the card has a trigger, action node, decision node, and output branches.

Use `execution` when the card's primary objective is to perform an operational process or handling sequence, such as collecting information, verifying identity, conducting screening, filing a report, escalating a case, or completing a control activity.

Use `control` when the card's primary objective is to describe a governance/control requirement and its expected control effect.

Use `risk_indicator` when the source mainly lists risk factors, red flags, or warning indicators used to identify elevated risk.

Example rule:

```text
A pre-onboarding committee assesses whether a customer should proceed and what due diligence level is required.
This is assessment, not execution.
```

If the boundary between `assessment` and `execution` is uncertain, choose the closer primary objective, set `review_status` to `needs_review`, and explain the boundary issue in `review_notes`.

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

Rules:

1. Every card must contain at least one `start` or `trigger` node.
2. A `start` node may be structural, but it must not add business action not stated by the source.
3. If the source text states a clear trigger condition or trigger event, create a `trigger` node.
4. Any `input`, `standard`, or `output` referenced by `USES`, `PRODUCES`, or `FEEDBACK` must appear as a node.

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

When setting card-level `review_status: "needs_review"`, explain the reason in `review_notes`. Use one or more of these categories when applicable: weak inferred process order; non-procedural source material converted into an assessment card; possible card granularity problem; missing downstream handoff; limited single-unit evidence; other.

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

section_id: `CH47-S01`

section_title: `Transaction monitoring > Transaction monitoring controls`

section_text_with_unit_anchors:

```text
[v7u_N003232|3232] Organizations apply transaction monitoring controls to manage ongoing risks.
ZH: 组织应用交易监控控制来管理持续风险。

[v7u_N003233|3233] Transaction monitoring systems generate alerts when customer activity or behavior is beyond normal parameters for the customer profile.
ZH: 交易监控系统在客户活动超出正常参数时生成警报。

[v7u_N003234|3234] The alerts are reviewed to assess whether unusual behavior can be explained or if it is potentially suspicious.
ZH: 审查警报以评估异常行为是否可解释或可疑。

[v7u_N003235|3235] Transaction monitoring controls are typically automated, but staff can still raise alerts manually, when needed.
ZH: 交易监控控制通常自动化，但员工也可手动触发警报。

[v7u_N003236|3236] Traditionally, rules-based systems were used. However, organizations are increasingly adopting AI-based controls to improve suspicious activity detection.
ZH: 交易监控从基于规则的系统向基于AI的控制演进。

[v7u_N003237|3237] A manual alert might be, for example, a report raised by the front office when a cash deposit is made in a bank branch.
ZH: 手动警报示例：前台报告银行网点的现金存款。

[v7u_N003238|3238] However, an automated control might be more targeted and more specific—for example, identifying and alerting on all transactions in a particular currency for citizens of a particular jurisdiction.
ZH: 自动化控制示例：识别并警报特定司法管辖区公民的特定货币交易。

[v7u_N003239|3239] This might be needed where currency control restrictions are applied.
ZH: 此自动化控制可能用于货币管制限制的情况。

[v7u_N003240|3240] A threshold is criteria for behavior.
ZH: 阈值是行为的标准。

[v7u_N003241|3241] A TM system might be applied to monitor customer account activity, assessing transactions to and from customers, or checking accounts, with specific thresholds for different types of customer accounts.
ZH: 交易监控系统可应用于监控客户账户活动，对不同类型账户设置特定阈值。

[v7u_N003242|3242] An organization might choose to use one monitoring system or separate systems to monitor transactions. Transactions completed by larger customers, such as corporations or financial institutions, might be monitored by the same system, but using different scenarios and thresholds.
ZH: 机构可选择单一或分离的监控系统，对大型客户使用不同场景和阈值。
```

## Section Package JSON

Use this package only as current-section evidence context. `section_text_with_unit_anchors` remains the primary source.

```json
{
  "section_id": "CH47-S01",
  "section_title": "Transaction monitoring > Transaction monitoring controls",
  "chapter_id": "CH47",
  "chapter_title": "Transaction monitoring",
  "section_order": 1,
  "section_text_with_unit_anchors": "[v7u_N003232|3232] Organizations apply transaction monitoring controls to manage ongoing risks.\nZH: 组织应用交易监控控制来管理持续风险。\n\n[v7u_N003233|3233] Transaction monitoring systems generate alerts when customer activity or behavior is beyond normal parameters for the customer profile.\nZH: 交易监控系统在客户活动超出正常参数时生成警报。\n\n[v7u_N003234|3234] The alerts are reviewed to assess whether unusual behavior can be explained or if it is potentially suspicious.\nZH: 审查警报以评估异常行为是否可解释或可疑。\n\n[v7u_N003235|3235] Transaction monitoring controls are typically automated, but staff can still raise alerts manually, when needed.\nZH: 交易监控控制通常自动化，但员工也可手动触发警报。\n\n[v7u_N003236|3236] Traditionally, rules-based systems were used. However, organizations are increasingly adopting AI-based controls to improve suspicious activity detection.\nZH: 交易监控从基于规则的系统向基于AI的控制演进。\n\n[v7u_N003237|3237] A manual alert might be, for example, a report raised by the front office when a cash deposit is made in a bank branch.\nZH: 手动警报示例：前台报告银行网点的现金存款。\n\n[v7u_N003238|3238] However, an automated control might be more targeted and more specific—for example, identifying and alerting on all transactions in a particular currency for citizens of a particular jurisdiction.\nZH: 自动化控制示例：识别并警报特定司法管辖区公民的特定货币交易。\n\n[v7u_N003239|3239] This might be needed where currency control restrictions are applied.\nZH: 此自动化控制可能用于货币管制限制的情况。\n\n[v7u_N003240|3240] A threshold is criteria for behavior.\nZH: 阈值是行为的标准。\n\n[v7u_N003241|3241] A TM system might be applied to monitor customer account activity, assessing transactions to and from customers, or checking accounts, with specific thresholds for different types of customer accounts.\nZH: 交易监控系统可应用于监控客户账户活动，对不同类型账户设置特定阈值。\n\n[v7u_N003242|3242] An organization might choose to use one monitoring system or separate systems to monitor transactions. Transactions completed by larger customers, such as corporations or financial institutions, might be monitored by the same system, but using different scenarios and thresholds.\nZH: 机构可选择单一或分离的监控系统，对大型客户使用不同场景和阈值。",
  "units": [
    {
      "en_quote": "Organizations apply transaction monitoring controls to manage ongoing risks.",
      "knowledge_zh": "组织应用交易监控控制来管理持续风险。",
      "pdf_page": 333,
      "printed_page": "328",
      "type": "fact",
      "unit_id": "v7u_N003232",
      "unit_order": 3232
    },
    {
      "en_quote": "Transaction monitoring systems generate alerts when customer activity or behavior is beyond normal parameters for the customer profile.",
      "knowledge_zh": "交易监控系统在客户活动超出正常参数时生成警报。",
      "pdf_page": 333,
      "printed_page": "328",
      "type": "process",
      "unit_id": "v7u_N003233",
      "unit_order": 3233
    },
    {
      "en_quote": "The alerts are reviewed to assess whether unusual behavior can be explained or if it is potentially suspicious.",
      "knowledge_zh": "审查警报以评估异常行为是否可解释或可疑。",
      "pdf_page": 333,
      "printed_page": "328",
      "type": "process",
      "unit_id": "v7u_N003234",
      "unit_order": 3234
    },
    {
      "en_quote": "Transaction monitoring controls are typically automated, but staff can still raise alerts manually, when needed.",
      "knowledge_zh": "交易监控控制通常自动化，但员工也可手动触发警报。",
      "pdf_page": 333,
      "printed_page": "328",
      "type": "fact",
      "unit_id": "v7u_N003235",
      "unit_order": 3235
    },
    {
      "en_quote": "Traditionally, rules-based systems were used. However, organizations are increasingly adopting AI-based controls to improve suspicious activity detection.",
      "knowledge_zh": "交易监控从基于规则的系统向基于AI的控制演进。",
      "pdf_page": 333,
      "printed_page": "328",
      "type": "fact",
      "unit_id": "v7u_N003236",
      "unit_order": 3236
    },
    {
      "en_quote": "A manual alert might be, for example, a report raised by the front office when a cash deposit is made in a bank branch.",
      "knowledge_zh": "手动警报示例：前台报告银行网点的现金存款。",
      "pdf_page": 333,
      "printed_page": "328",
      "type": "case",
      "unit_id": "v7u_N003237",
      "unit_order": 3237
    },
    {
      "en_quote": "However, an automated control might be more targeted and more specific—for example, identifying and alerting on all transactions in a particular currency for citizens of a particular jurisdiction.",
      "knowledge_zh": "自动化控制示例：识别并警报特定司法管辖区公民的特定货币交易。",
      "pdf_page": 333,
      "printed_page": "328",
      "type": "case",
      "unit_id": "v7u_N003238",
      "unit_order": 3238
    },
    {
      "en_quote": "This might be needed where currency control restrictions are applied.",
      "knowledge_zh": "此自动化控制可能用于货币管制限制的情况。",
      "pdf_page": 333,
      "printed_page": "328",
      "type": "fact",
      "unit_id": "v7u_N003239",
      "unit_order": 3239
    },
    {
      "en_quote": "A threshold is criteria for behavior.",
      "knowledge_zh": "阈值是行为的标准。",
      "pdf_page": 333,
      "printed_page": "328",
      "type": "definition",
      "unit_id": "v7u_N003240",
      "unit_order": 3240
    },
    {
      "en_quote": "A TM system might be applied to monitor customer account activity, assessing transactions to and from customers, or checking accounts, with specific thresholds for different types of customer accounts.",
      "knowledge_zh": "交易监控系统可应用于监控客户账户活动，对不同类型账户设置特定阈值。",
      "pdf_page": 333,
      "printed_page": "328",
      "type": "fact",
      "unit_id": "v7u_N003241",
      "unit_order": 3241
    },
    {
      "en_quote": "An organization might choose to use one monitoring system or separate systems to monitor transactions. Transactions completed by larger customers, such as corporations or financial institutions, might be monitored by the same system, but using different scenarios and thresholds.",
      "knowledge_zh": "机构可选择单一或分离的监控系统，对大型客户使用不同场景和阈值。",
      "pdf_page": 333,
      "printed_page": "328",
      "type": "fact",
      "unit_id": "v7u_N003242",
      "unit_order": 3242
    }
  ],
  "core_points": [
    {
      "anchor_unit_ids": [
        "v7u_N003232",
        "v7u_N003233",
        "v7u_N003234",
        "v7u_N003235"
      ],
      "core_point_id": "cp_CH47_S01_001",
      "key_unit_ids": [
        "v7u_N003232",
        "v7u_N003233",
        "v7u_N003234",
        "v7u_N003235",
        "v7u_N003239"
      ],
      "reason": "Covers the core process of transaction monitoring alert generation and review, including manual and automated methods, supported by examples and AI evolution context.",
      "support_unit_ids": [
        "v7u_N003236",
        "v7u_N003237",
        "v7u_N003238",
        "v7u_N003239"
      ],
      "title_en": "Alert Generation and Review in Transaction Monitoring",
      "title_zh": "交易监控中的警报生成与审查"
    },
    {
      "anchor_unit_ids": [
        "v7u_N003240",
        "v7u_N003241",
        "v7u_N003242"
      ],
      "core_point_id": "cp_CH47_S01_002",
      "key_unit_ids": [
        "v7u_N003240",
        "v7u_N003241",
        "v7u_N003242"
      ],
      "reason": "Defines threshold and describes its application in TM systems for different customer accounts and system configurations.",
      "support_unit_ids": [],
      "title_en": "Thresholds in Transaction Monitoring",
      "title_zh": "交易监控中的阈值"
    }
  ],
  "core_point_unit_edges": [
    {
      "edge_id": "p2b:cp_CH47_S01_001:v7u_N003232",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3232 explains the purpose of transaction monitoring controls, which is the foundation for alert generation.",
      "relation_type": "explains",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH47_S01_001",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003232"
    },
    {
      "edge_id": "p2b:cp_CH47_S01_001:v7u_N003233",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3233 describes the process of alert generation when activity exceeds normal parameters.",
      "relation_type": "describes_process",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH47_S01_001",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003233"
    },
    {
      "edge_id": "p2b:cp_CH47_S01_001:v7u_N003234",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3234 describes the review step in the alert process.",
      "relation_type": "describes_process",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH47_S01_001",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003234"
    },
    {
      "edge_id": "p2b:cp_CH47_S01_001:v7u_N003235",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3235 explains that controls are typically automated but manual alerts are possible, qualifying the process.",
      "relation_type": "explains",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH47_S01_001",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003235"
    },
    {
      "edge_id": "p2b:cp_CH47_S01_001:v7u_N003236",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3236 provides background on the evolution from rules-based to AI-based controls, contextualizing alert generation.",
      "relation_type": "provides_context",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH47_S01_001",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003236"
    },
    {
      "edge_id": "p2b:cp_CH47_S01_001:v7u_N003237",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3237 gives an example of a manual alert.",
      "relation_type": "illustrates",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH47_S01_001",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003237"
    },
    {
      "edge_id": "p2b:cp_CH47_S01_001:v7u_N003238",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3238 gives an example of an automated control alert.",
      "relation_type": "illustrates",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH47_S01_001",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003238"
    },
    {
      "edge_id": "p2b:cp_CH47_S01_001:v7u_N003239",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3239 explains a scenario where the automated control example might be needed, adding context.",
      "relation_type": "explains",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH47_S01_001",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003239"
    },
    {
      "edge_id": "p2b:cp_CH47_S01_002:v7u_N003240",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3240 defines what a threshold is: criteria for behavior.",
      "relation_type": "defines",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH47_S01_002",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003240"
    },
    {
      "edge_id": "p2b:cp_CH47_S01_002:v7u_N003241",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3241 explains how thresholds are applied in TM systems for different customer accounts.",
      "relation_type": "explains",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH47_S01_002",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003241"
    },
    {
      "edge_id": "p2b:cp_CH47_S01_002:v7u_N003242",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3242 explains the use of different scenarios and thresholds for larger customers in TM systems.",
      "relation_type": "explains",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH47_S01_002",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003242"
    }
  ],
  "same_section_core_point_edges": [
    {
      "edge_id": "p2c_rel_CH47_S01_001_002",
      "edge_scope": "same_section_core_point",
      "evidence_summary": null,
      "reason": "CP1 covers the overall alert generation and review process, while CP2 details thresholds, which are a key component of that process.",
      "relation_type": "contains",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH47_S01_001",
      "source_phase": "P2C",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "cp_CH47_S01_002"
    }
  ],
  "instructions": {
    "card_must_have_start_or_trigger_node": true,
    "card_must_not_cross_section": true,
    "cite_unit_evidence_for_every_node_and_edge": true,
    "decides_edges_must_have_condition_labels": true,
    "do_not_create_bridge_edges": true,
    "do_not_create_clusters": true,
    "do_not_create_render_files": true,
    "do_not_create_scenario_paths": true,
    "drawio_mermaid_svg_png_are_render_views_not_evidence_source": true,
    "flow_element_definitions": {
      "action": "Real executable step in the formal flow graph.",
      "decision": "Conditional branching point based on facts, standards, thresholds, evidence sufficiency, or compliance requirements.",
      "end": "Local exit, stable result, or handoff point of the current card; not necessarily the end of the business matter.",
      "start": "Local entry point of the current card; not the start of the whole customer lifecycle or textbook process.",
      "steps": "Human-readable summary derived from flow_nodes and flow_edges; not the source of truth.",
      "summary": "Optional human-readable card description; it does not replace flow_nodes or flow_edges."
    },
    "flow_node_types": [
      "start",
      "trigger",
      "action",
      "decision",
      "input",
      "standard",
      "output",
      "end"
    ],
    "include_all_section_core_point_unit_edges": true,
    "json_flow_graph_is_source_of_truth": true,
    "optional_card_fields": [
      "summary",
      "scenario",
      "trigger",
      "actor",
      "objective",
      "inputs",
      "decision_standard",
      "outputs",
      "steps",
      "review_notes",
      "metadata"
    ],
    "output_zero_or_more_cards": true,
    "p2b_relation_type_is_candidate_only_not_edge_filter": true,
    "p5_alias_is_normalization_only": true,
    "p7a_contract": "minimal_flow_graph_contract",
    "required_card_fields": [
      "card_id",
      "section_id",
      "title",
      "flow_nodes",
      "flow_edges",
      "source_unit_ids",
      "review_status"
    ],
    "steps_are_human_readable_summary_not_source_of_truth": true,
    "summary_scenario_trigger_objective_are_optional": true,
    "trigger_field_does_not_replace_trigger_node": true,
    "use_only_card_internal_edge_types": [
      "PRECEDES",
      "USES",
      "PRODUCES",
      "DECIDES",
      "FEEDBACK"
    ]
  },
  "alias_index": {
    "status": "available",
    "usage": "normalization_only_not_evidence",
    "not_kg_edge": true,
    "alias_group_count": 184,
    "sample_alias_groups": [
      {
        "alias_group_id": "p5c_alias_000001",
        "alias_scope": "retrieval_equivalent_report_variant",
        "aliases_en": [
          "SAR",
          "STR",
          "suspicious activity reports",
          "suspicious transaction report",
          "suspicious transaction reporting",
          "suspicious transaction reports"
        ],
        "aliases_zh": [
          "可疑交易报告"
        ],
        "canonical_en": "suspicious activity report",
        "canonical_zh": "可疑活动报告"
      },
      {
        "alias_group_id": "p5c_alias_000002",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [
          "RBA"
        ],
        "aliases_zh": [
          "基于风险的方法"
        ],
        "canonical_en": "risk-based approach",
        "canonical_zh": "风险为本方法"
      },
      {
        "alias_group_id": "p5c_alias_000003",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [
          "FIU"
        ],
        "aliases_zh": [
          "金融情报单位",
          "金融情报中心"
        ],
        "canonical_en": "Financial Intelligence Unit",
        "canonical_zh": "金融情报机构"
      },
      {
        "alias_group_id": "p5c_alias_000004",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [
          "FATF"
        ],
        "aliases_zh": [],
        "canonical_en": "Financial Action Task Force",
        "canonical_zh": "金融行动特别工作组"
      },
      {
        "alias_group_id": "p5c_alias_000005",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [
          "Financial Crime Enforcement Network"
        ],
        "aliases_zh": [],
        "canonical_en": "FinCEN",
        "canonical_zh": "金融犯罪执法网络"
      },
      {
        "alias_group_id": "p5c_alias_000006",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [
          "MLRO"
        ],
        "aliases_zh": [
          "反洗钱报告官",
          "洗钱报告负责人",
          "反洗钱报告负责人"
        ],
        "canonical_en": "money laundering reporting officer",
        "canonical_zh": "洗钱报告官"
      },
      {
        "alias_group_id": "p5c_alias_000007",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [
          "EWRA",
          "enterprise-wide risk assessments"
        ],
        "aliases_zh": [
          "企业级风险评估",
          "企业范围风险评估",
          "企业风险评估",
          "全机构风险评估"
        ],
        "canonical_en": "enterprise-wide risk assessment",
        "canonical_zh": "企业全面风险评估"
      },
      {
        "alias_group_id": "p5c_alias_000008",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [
          "AI"
        ],
        "aliases_zh": [],
        "canonical_en": "artificial intelligence",
        "canonical_zh": "人工智能"
      },
      {
        "alias_group_id": "p5c_alias_000009",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [
          "DNFBP",
          "DNFBPs"
        ],
        "aliases_zh": [
          "指定非金融行业和职业"
        ],
        "canonical_en": "Designated Nonfinancial Businesses and Professions",
        "canonical_zh": "指定非金融行业与职业"
      },
      {
        "alias_group_id": "p5c_alias_000010",
        "alias_scope": "translation_variant",
        "aliases_en": [
          "false positives"
        ],
        "aliases_zh": [
          "假阳性"
        ],
        "canonical_en": "false positive",
        "canonical_zh": "误报"
      },
      {
        "alias_group_id": "p5c_alias_000011",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "支付筛查"
        ],
        "canonical_en": "payment screening",
        "canonical_zh": "付款筛查"
      },
      {
        "alias_group_id": "p5c_alias_000012",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "通风报信"
        ],
        "canonical_en": "tipping off",
        "canonical_zh": "泄密"
      },
      {
        "alias_group_id": "p5c_alias_000013",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [
          "VASP"
        ],
        "aliases_zh": [
          "加密资产服务提供商"
        ],
        "canonical_en": "virtual asset service provider",
        "canonical_zh": "虚拟资产服务提供商"
      },
      {
        "alias_group_id": "p5c_alias_000014",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [
          "PSP",
          "payment service providers",
          "payment services provider"
        ],
        "aliases_zh": [
          "支付服务商"
        ],
        "canonical_en": "payment service provider",
        "canonical_zh": "支付服务提供商"
      },
      {
        "alias_group_id": "p5c_alias_000015",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "结构化交易",
          "结构化拆分"
        ],
        "canonical_en": "structuring",
        "canonical_zh": "拆分交易"
      },
      {
        "alias_group_id": "p5c_alias_000016",
        "alias_scope": "exact_alias",
        "aliases_en": [
          "negative media",
          "negative media coverage"
        ],
        "aliases_zh": [
          "负面媒体报道"
        ],
        "canonical_en": "adverse media",
        "canonical_zh": "负面媒体"
      },
      {
        "alias_group_id": "p5c_alias_000017",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "生物识别技术"
        ],
        "canonical_en": "biometric technology",
        "canonical_zh": "生物特征技术"
      },
      {
        "alias_group_id": "p5c_alias_000018",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "商业银行业务"
        ],
        "canonical_en": "commercial banking",
        "canonical_zh": "商业银行"
      },
      {
        "alias_group_id": "p5c_alias_000019",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "贸易型洗钱"
        ],
        "canonical_en": "trade-based money laundering",
        "canonical_zh": "贸易洗钱"
      },
      {
        "alias_group_id": "p5c_alias_000020",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [],
        "aliases_zh": [],
        "canonical_en": "AUSTRAC",
        "canonical_zh": "澳大利亚交易报告与分析中心"
      },
      {
        "alias_group_id": "p5c_alias_000021",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "风险画像"
        ],
        "canonical_en": "risk profile",
        "canonical_zh": "风险状况"
      },
      {
        "alias_group_id": "p5c_alias_000022",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "资产追缴"
        ],
        "canonical_en": "asset recovery",
        "canonical_zh": "资产追回"
      },
      {
        "alias_group_id": "p5c_alias_000023",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "生物识别"
        ],
        "canonical_en": "biometrics",
        "canonical_zh": "生物特征识别"
      },
      {
        "alias_group_id": "p5c_alias_000024",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "两用物品"
        ],
        "canonical_en": "dual-use goods",
        "canonical_zh": "两用商品"
      },
      {
        "alias_group_id": "p5c_alias_000025",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [],
        "aliases_zh": [
          "金融行动特别工作组建议"
        ],
        "canonical_en": "FATF Recommendations",
        "canonical_zh": "FATF建议"
      },
      {
        "alias_group_id": "p5c_alias_000026",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "人口贩卖"
        ],
        "canonical_en": "human trafficking",
        "canonical_zh": "人口贩运"
      },
      {
        "alias_group_id": "p5c_alias_000027",
        "alias_scope": "translation_variant",
        "aliases_en": [
          "jurisdictions"
        ],
        "aliases_zh": [
          "地域"
        ],
        "canonical_en": "jurisdiction",
        "canonical_zh": "司法管辖区"
      },
      {
        "alias_group_id": "p5c_alias_000028",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "运营风险"
        ],
        "canonical_en": "operational risk",
        "canonical_zh": "操作风险"
      },
      {
        "alias_group_id": "p5c_alias_000029",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "避税天堂",
          "避税港"
        ],
        "canonical_en": "tax haven",
        "canonical_zh": "避税地"
      },
      {
        "alias_group_id": "p5c_alias_000030",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "透明性"
        ],
        "canonical_en": "transparency",
        "canonical_zh": "透明度"
      },
      {
        "alias_group_id": "p5c_alias_000031",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "英国《反贿赂法》2010"
        ],
        "canonical_en": "UK Bribery Act 2010",
        "canonical_zh": "《英国反贿赂法》"
      },
      {
        "alias_group_id": "p5c_alias_000032",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "问责制"
        ],
        "canonical_en": "accountability",
        "canonical_zh": "问责"
      },
      {
        "alias_group_id": "p5c_alias_000033",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [
          "ABC"
        ],
        "aliases_zh": [
          "反贿赂与腐败"
        ],
        "canonical_en": "anti-bribery and corruption",
        "canonical_zh": "反贿赂与反腐败"
      },
      {
        "alias_group_id": "p5c_alias_000034",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "审计轨迹",
          "审计追踪"
        ],
        "canonical_en": "audit trail",
        "canonical_zh": "审计线索"
      },
      {
        "alias_group_id": "p5c_alias_000035",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "现金密集型行业"
        ],
        "canonical_en": "cash-intensive business",
        "canonical_zh": "现金密集型业务"
      },
      {
        "alias_group_id": "p5c_alias_000036",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [
          "DORA"
        ],
        "aliases_zh": [],
        "canonical_en": "Digital Operational Resilience Act",
        "canonical_zh": "《数字运营韧性法案》"
      },
      {
        "alias_group_id": "p5c_alias_000037",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "有效性指标",
          "立即成果"
        ],
        "canonical_en": "Immediate Outcome",
        "canonical_zh": "直接目标"
      },
      {
        "alias_group_id": "p5c_alias_000038",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "韩国金融情报院"
        ],
        "canonical_en": "Korea FIU",
        "canonical_zh": "韩国金融情报中心"
      },
      {
        "alias_group_id": "p5c_alias_000039",
        "alias_scope": "abbreviation_full_form",
        "aliases_en": [],
        "aliases_zh": [],
        "canonical_en": "OFAC",
        "canonical_zh": "外国资产控制办公室"
      },
      {
        "alias_group_id": "p5c_alias_000040",
        "alias_scope": "translation_variant",
        "aliases_en": [],
        "aliases_zh": [
          "政策和程序"
        ],
        "canonical_en": "policies and procedures",
        "canonical_zh": "政策与程序"
      }
    ]
  }
}
```
