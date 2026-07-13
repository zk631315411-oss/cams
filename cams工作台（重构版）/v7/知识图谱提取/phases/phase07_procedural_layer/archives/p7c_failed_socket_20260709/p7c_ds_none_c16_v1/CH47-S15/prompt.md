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

section_id: `CH47-S15`

section_title: `Transaction monitoring > Suspicious activity escalation process`

section_text_with_unit_anchors:

```text
[v7u_N003410|3410] If investigators have completed the research and identified risk indicators that cannot be mitigated, they might need to escalate this customer for additional investigation. Depending on the jurisdiction and organizational policies, the end result might be filing a SAR to the FIU. Based on the organization's processes, one or more additional people might review the research before choosing whether to file a report with authorities.
ZH: 无法缓解风险指标时，需升级客户调查，可能提交可疑活动报告。

[v7u_N003411|3411] The internal process used to escalate findings is important—and can have legal and regulatory consequences. It is important to know the policy and process well.
ZH: 内部升级流程具有法律和监管后果，必须熟悉政策和流程。

[v7u_N003412|3412] Throughout their research, investigators have been relying on the work and support of others. Some might have done previous research, perhaps when preparing a customer profile or researching previous transaction alerts. Some might have provided the information they personally know about the customer.
ZH: 调查人员依赖他人先前的工作和支持，如客户资料或交易警报研究。

[v7u_N003413|3413] Investigators filtered, organized, and prioritized.
ZH: 调查人员对信息进行筛选、组织和优先级排序。

[v7u_N003414|3414] They relied on all of those sources and adequately documented the case.
ZH: 调查人员必须依赖所有来源并充分记录案件。

[v7u_N003415|3415] Now others will collaborate in the decision regarding next steps.
ZH: 其他人将协作决定下一步行动。

[v7u_N003416|3416] Because each jurisdiction and organization is unique, the roles of people involved and the processes they use will differ.
ZH: 各司法管辖区和组织的角色与流程各不相同。

[v7u_N003417|3417] Failing to follow the process carefully can lead to legal and regulatory consequences.
ZH: 未仔细遵循流程可能导致法律和监管后果。

[v7u_N003418|3418] So, ask, learn, and move thoughtfully.
ZH: 应主动询问、学习并谨慎行动。

[v7u_N003419|3419] One potential next step is to file an internal escalation report.
ZH: 下一步可能是提交内部升级报告。

[v7u_N003420|3420] This has many names. Some call it an unusual activity report (UAR). Some call it an internal SAR.
ZH: 内部升级报告有多种名称，如异常活动报告或内部可疑活动报告。

[v7u_N003421|3421] But language is important, especially in jurisdictions where any unusual activity must be reported to authorities.
ZH: 在可疑活动上报中，使用精确语言至关重要

[v7u_N003422|3422] So, learn the correct report name for the organization and use only that name.
ZH: 必须使用机构规定的正确报告名称

[v7u_N003423|3423] Don’t be casual in referring to something as "unusual" or "suspicious", especially when documenting.
ZH: 在文档记录中避免随意使用“异常”或“可疑”等措辞

[v7u_N003424|3424] Some jurisdictions have timing requirements for when a financial institution should file a SAR based on when it was determined to be suspicious.
ZH: 部分司法管辖区对可疑交易报告（SAR）提交有时间要求

[v7u_N003425|3425] Based on the investigative results, the MLRO might file a SAR with the country’s FIU, so law enforcement can gain access to the information.
ZH: 洗钱报告官（MLRO）根据调查结果向金融情报机构（FIU）提交可疑交易报告（SAR）

[v7u_N003426|3426] To demonstrate that an organization has undertaken appropriate research to prevent financial crime, it is important to create an audit trail. This means documenting all steps the team has taken to demonstrate compliance efforts to auditors and the supervisory authorities. Include how any inaccuracies or false matches were resolved.
ZH: 创建审计线索，记录合规步骤及不准确或误匹配的解决过程

[v7u_N003427|3427] Some of this will be straightforward, as one source may be older and therefore less reliable than another source.
ZH: 信息来源的可靠性比较：较旧来源通常可靠性较低

[v7u_N003428|3428] Save documentation as PDFs, printed out, or collected in some other manner according to the organization’s record retention policy.
ZH: 按照机构记录保留政策，以PDF、打印件等形式保存文档

[v7u_N003429|3429] Thorough documentation provides a record to support your organization’s risk-based approach. So, even if you fail to capture every relevant piece of information, the process itself is defensible.
ZH: 详尽的文档记录支持基于风险的方法，即使信息不全，过程本身也可辩护

[v7u_N003430|3430] Once documented, your research should be properly and securely stored to respect privacy laws and data security.
ZH: 研究文档必须妥善安全存储，以遵守隐私法和数据安全要求

[v7u_N003431|3431] Internal auditors, regulators, and law enforcement might review the documented findings, and law enforcement might use them in court.
ZH: 内部审计、监管机构和执法部门可能审查文档记录，执法部门可能在法庭上使用

[v7u_N003432|3432] It is important to document the research at the time it is performed. A search today might turn up very different results than a search performed in several months, when a decision is being questioned. Even those searches that do not produce target or relevant matches should be documented with appropriate date and time stamps.
ZH: 研究应在执行时立即记录，并标注日期和时间戳

[v7u_N003433|3433] Document the search strings, logic, and keywords. Sometimes the method and logic behind generating search results can be as important as the results themselves. Documentation will help demonstrate that the team has followed a risk-based approach.
ZH: 记录搜索字符串、逻辑和关键词，以证明遵循了基于风险的方法

[v7u_N003434|3434] Be aware of data privacy laws and data security protocols.
ZH: 注意数据隐私法律和数据安全协议

[v7u_N003435|3435] Tools, databases, and methods for research that may be acceptable for one organization may not be acceptable in another organization or jurisdiction.
ZH: 可接受的研究工具、数据库和方法因机构和司法管辖区而异

[v7u_N003436|3436] A process should be in place to document the research as information is collected, so nothing is lost or forgotten.
ZH: 应建立流程，在收集信息时同步记录研究，以防遗漏

[v7u_N003437|3437] Developing research notes and a standard template increases the likelihood that all required information will be captured.
ZH: 制定研究笔记和标准模板有助于确保捕获所有必要信息
```

allowed_unit_ids:

```json
[
  "v7u_N003410",
  "v7u_N003411",
  "v7u_N003412",
  "v7u_N003413",
  "v7u_N003414",
  "v7u_N003415",
  "v7u_N003416",
  "v7u_N003417",
  "v7u_N003418",
  "v7u_N003419",
  "v7u_N003420",
  "v7u_N003421",
  "v7u_N003422",
  "v7u_N003423",
  "v7u_N003424",
  "v7u_N003425",
  "v7u_N003426",
  "v7u_N003427",
  "v7u_N003428",
  "v7u_N003429",
  "v7u_N003430",
  "v7u_N003431",
  "v7u_N003432",
  "v7u_N003433",
  "v7u_N003434",
  "v7u_N003435",
  "v7u_N003436",
  "v7u_N003437"
]
```
