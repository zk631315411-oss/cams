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

section_id: `CH42-S01`

section_title: `Onboarding AFC controls > The KYC process`

section_text_with_unit_anchors:

```text
[v7u_N003011|3011] With evolving global regulatory frameworks, financial institutions must implement risk-based due diligence to prevent financial crime.
ZH: 金融机构必须实施基于风险的尽职调查以防止金融犯罪

[v7u_N003012|3012] The KYC process is a core requirement in AFC compliance, ensuring financial institutions identify, verify, and assess customer risks before establishing or maintaining business relationships.
ZH: 了解你的客户流程是金融犯罪合规的核心要求，用于识别、验证和评估客户风险

[v7u_N003013|3013] For specific customer profiles, such as PEPs, high-net-worth individuals, and customers from high-risk jurisdictions, a pre-KYC onboarding committee might assess suitability before formal identification.
ZH: 对于政治敏感人物等特定客户，在正式了解你的客户前由委员会评估其适宜性

[v7u_N003014|3014] The committee typically includes compliance experts, risk managers, legal advisors, and business unit leaders, who collectively evaluate jurisdictional risks, business activities, and strategic fit.
ZH: 委员会由合规、风险、法务及业务部门代表组成，评估司法管辖区风险等

[v7u_N003015|3015] The outcome determines whether customers proceed to full KYC and what level of due diligence—standard or enhanced—is required.
ZH: 委员会评估结果决定客户是否进入完整了解你的客户及所需尽职调查级别

[v7u_N003016|3016] This step ensures efficient resource use, early risk mitigation, and regulatory alignment by filtering out unsuitable clients early in the process.
ZH: 了解你的客户前步骤旨在早期过滤不合适客户，确保资源高效利用和监管合规

[v7u_N003017|3017] The typical KYC/CDD process consists of the following steps:
ZH: 典型的了解你的客户/客户尽职调查流程包含以下步骤

[v7u_N003018|3018] Identity and verification (ID&V):
ZH: 身份识别与验证步骤

[v7u_N003019|3019] Identification is the collection of personal and business details, including name, date of birth, nationality, address, tax identification number, and company registration data.
ZH: 身份识别是收集个人和企业的详细信息

[v7u_N003020|3020] Verification is the authentication of provided information using government-issued documents, biometric authentication, AI-driven verification tools, and forensic analysis of identification records.
ZH: 验证是通过政府文件、生物识别等技术对信息进行认证

[v7u_N003021|3021] Organizations must understand and obtain information, as appropriate, on the purpose and intended nature of the customer’s relationship with the organization.
ZH: 机构必须了解客户关系的预期目的和性质

[v7u_N003022|3022] Enhanced regulations require organizations to determine the ultimate beneficial owners (UBOs) of corporate accounts.
ZH: 强化法规要求机构确定公司账户的最终受益所有人

[v7u_N003023|3023] Screening is conducted prior to onboarding to determine risk:
ZH: 在客户准入前进行筛查以确定风险

[v7u_N003024|3024] Sanctions screening is when customer details are cross-checked against UN, EU, OFAC, and national sanctions lists to detect high-risk entities.
ZH: 制裁筛查是将客户信息与联合国、欧盟、OFAC及国家制裁名单进行交叉核对

[v7u_N003025|3025] Adverse media monitoring is conducted to identify links to financial crime, corruption, and fraudulent activities.
ZH: 负面媒体监控旨在识别与金融犯罪、腐败和欺诈活动的关联

[v7u_N003026|3026] PEP screening is when organizations determine whether the individual or beneficial owner is a PEP, or the relative or close associate of a PEP.
ZH: 政治敏感人物筛查用于确定个人或受益所有人是否为政治敏感人物或其亲属或密切关联人
```

## Section Package JSON

Use this package only as current-section evidence context. `section_text_with_unit_anchors` remains the primary source.

```json
{
  "section_id": "CH42-S01",
  "section_title": "Onboarding AFC controls > The KYC process",
  "chapter_id": "CH42",
  "chapter_title": "Onboarding AFC controls",
  "section_order": 1,
  "section_text_with_unit_anchors": "[v7u_N003011|3011] With evolving global regulatory frameworks, financial institutions must implement risk-based due diligence to prevent financial crime.\nZH: 金融机构必须实施基于风险的尽职调查以防止金融犯罪\n\n[v7u_N003012|3012] The KYC process is a core requirement in AFC compliance, ensuring financial institutions identify, verify, and assess customer risks before establishing or maintaining business relationships.\nZH: 了解你的客户流程是金融犯罪合规的核心要求，用于识别、验证和评估客户风险\n\n[v7u_N003013|3013] For specific customer profiles, such as PEPs, high-net-worth individuals, and customers from high-risk jurisdictions, a pre-KYC onboarding committee might assess suitability before formal identification.\nZH: 对于政治敏感人物等特定客户，在正式了解你的客户前由委员会评估其适宜性\n\n[v7u_N003014|3014] The committee typically includes compliance experts, risk managers, legal advisors, and business unit leaders, who collectively evaluate jurisdictional risks, business activities, and strategic fit.\nZH: 委员会由合规、风险、法务及业务部门代表组成，评估司法管辖区风险等\n\n[v7u_N003015|3015] The outcome determines whether customers proceed to full KYC and what level of due diligence—standard or enhanced—is required.\nZH: 委员会评估结果决定客户是否进入完整了解你的客户及所需尽职调查级别\n\n[v7u_N003016|3016] This step ensures efficient resource use, early risk mitigation, and regulatory alignment by filtering out unsuitable clients early in the process.\nZH: 了解你的客户前步骤旨在早期过滤不合适客户，确保资源高效利用和监管合规\n\n[v7u_N003017|3017] The typical KYC/CDD process consists of the following steps:\nZH: 典型的了解你的客户/客户尽职调查流程包含以下步骤\n\n[v7u_N003018|3018] Identity and verification (ID&V):\nZH: 身份识别与验证步骤\n\n[v7u_N003019|3019] Identification is the collection of personal and business details, including name, date of birth, nationality, address, tax identification number, and company registration data.\nZH: 身份识别是收集个人和企业的详细信息\n\n[v7u_N003020|3020] Verification is the authentication of provided information using government-issued documents, biometric authentication, AI-driven verification tools, and forensic analysis of identification records.\nZH: 验证是通过政府文件、生物识别等技术对信息进行认证\n\n[v7u_N003021|3021] Organizations must understand and obtain information, as appropriate, on the purpose and intended nature of the customer’s relationship with the organization.\nZH: 机构必须了解客户关系的预期目的和性质\n\n[v7u_N003022|3022] Enhanced regulations require organizations to determine the ultimate beneficial owners (UBOs) of corporate accounts.\nZH: 强化法规要求机构确定公司账户的最终受益所有人\n\n[v7u_N003023|3023] Screening is conducted prior to onboarding to determine risk:\nZH: 在客户准入前进行筛查以确定风险\n\n[v7u_N003024|3024] Sanctions screening is when customer details are cross-checked against UN, EU, OFAC, and national sanctions lists to detect high-risk entities.\nZH: 制裁筛查是将客户信息与联合国、欧盟、OFAC及国家制裁名单进行交叉核对\n\n[v7u_N003025|3025] Adverse media monitoring is conducted to identify links to financial crime, corruption, and fraudulent activities.\nZH: 负面媒体监控旨在识别与金融犯罪、腐败和欺诈活动的关联\n\n[v7u_N003026|3026] PEP screening is when organizations determine whether the individual or beneficial owner is a PEP, or the relative or close associate of a PEP.\nZH: 政治敏感人物筛查用于确定个人或受益所有人是否为政治敏感人物或其亲属或密切关联人",
  "units": [
    {
      "en_quote": "With evolving global regulatory frameworks, financial institutions must implement risk-based due diligence to prevent financial crime.",
      "knowledge_zh": "金融机构必须实施基于风险的尽职调查以防止金融犯罪",
      "pdf_page": 309,
      "printed_page": "304",
      "type": "rule",
      "unit_id": "v7u_N003011",
      "unit_order": 3011
    },
    {
      "en_quote": "The KYC process is a core requirement in AFC compliance, ensuring financial institutions identify, verify, and assess customer risks before establishing or maintaining business relationships.",
      "knowledge_zh": "了解你的客户流程是金融犯罪合规的核心要求，用于识别、验证和评估客户风险",
      "pdf_page": 309,
      "printed_page": "304",
      "type": "definition",
      "unit_id": "v7u_N003012",
      "unit_order": 3012
    },
    {
      "en_quote": "For specific customer profiles, such as PEPs, high-net-worth individuals, and customers from high-risk jurisdictions, a pre-KYC onboarding committee might assess suitability before formal identification.",
      "knowledge_zh": "对于政治敏感人物等特定客户，在正式了解你的客户前由委员会评估其适宜性",
      "pdf_page": 309,
      "printed_page": "304",
      "type": "process",
      "unit_id": "v7u_N003013",
      "unit_order": 3013
    },
    {
      "en_quote": "The committee typically includes compliance experts, risk managers, legal advisors, and business unit leaders, who collectively evaluate jurisdictional risks, business activities, and strategic fit.",
      "knowledge_zh": "委员会由合规、风险、法务及业务部门代表组成，评估司法管辖区风险等",
      "pdf_page": 309,
      "printed_page": "304",
      "type": "fact",
      "unit_id": "v7u_N003014",
      "unit_order": 3014
    },
    {
      "en_quote": "The outcome determines whether customers proceed to full KYC and what level of due diligence—standard or enhanced—is required.",
      "knowledge_zh": "委员会评估结果决定客户是否进入完整了解你的客户及所需尽职调查级别",
      "pdf_page": 309,
      "printed_page": "304",
      "type": "process",
      "unit_id": "v7u_N003015",
      "unit_order": 3015
    },
    {
      "en_quote": "This step ensures efficient resource use, early risk mitigation, and regulatory alignment by filtering out unsuitable clients early in the process.",
      "knowledge_zh": "了解你的客户前步骤旨在早期过滤不合适客户，确保资源高效利用和监管合规",
      "pdf_page": 309,
      "printed_page": "304",
      "type": "fact",
      "unit_id": "v7u_N003016",
      "unit_order": 3016
    },
    {
      "en_quote": "The typical KYC/CDD process consists of the following steps:",
      "knowledge_zh": "典型的了解你的客户/客户尽职调查流程包含以下步骤",
      "pdf_page": 310,
      "printed_page": "305",
      "type": "classification",
      "unit_id": "v7u_N003017",
      "unit_order": 3017
    },
    {
      "en_quote": "Identity and verification (ID&V):",
      "knowledge_zh": "身份识别与验证步骤",
      "pdf_page": 310,
      "printed_page": "305",
      "type": "context",
      "unit_id": "v7u_N003018",
      "unit_order": 3018
    },
    {
      "en_quote": "Identification is the collection of personal and business details, including name, date of birth, nationality, address, tax identification number, and company registration data.",
      "knowledge_zh": "身份识别是收集个人和企业的详细信息",
      "pdf_page": 310,
      "printed_page": "305",
      "type": "definition",
      "unit_id": "v7u_N003019",
      "unit_order": 3019
    },
    {
      "en_quote": "Verification is the authentication of provided information using government-issued documents, biometric authentication, AI-driven verification tools, and forensic analysis of identification records.",
      "knowledge_zh": "验证是通过政府文件、生物识别等技术对信息进行认证",
      "pdf_page": 310,
      "printed_page": "305",
      "type": "definition",
      "unit_id": "v7u_N003020",
      "unit_order": 3020
    },
    {
      "en_quote": "Organizations must understand and obtain information, as appropriate, on the purpose and intended nature of the customer’s relationship with the organization.",
      "knowledge_zh": "机构必须了解客户关系的预期目的和性质",
      "pdf_page": 310,
      "printed_page": "305",
      "type": "rule",
      "unit_id": "v7u_N003021",
      "unit_order": 3021
    },
    {
      "en_quote": "Enhanced regulations require organizations to determine the ultimate beneficial owners (UBOs) of corporate accounts.",
      "knowledge_zh": "强化法规要求机构确定公司账户的最终受益所有人",
      "pdf_page": 310,
      "printed_page": "305",
      "type": "rule",
      "unit_id": "v7u_N003022",
      "unit_order": 3022
    },
    {
      "en_quote": "Screening is conducted prior to onboarding to determine risk:",
      "knowledge_zh": "在客户准入前进行筛查以确定风险",
      "pdf_page": 310,
      "printed_page": "305",
      "type": "context",
      "unit_id": "v7u_N003023",
      "unit_order": 3023
    },
    {
      "en_quote": "Sanctions screening is when customer details are cross-checked against UN, EU, OFAC, and national sanctions lists to detect high-risk entities.",
      "knowledge_zh": "制裁筛查是将客户信息与联合国、欧盟、OFAC及国家制裁名单进行交叉核对",
      "pdf_page": 310,
      "printed_page": "305",
      "type": "definition",
      "unit_id": "v7u_N003024",
      "unit_order": 3024
    },
    {
      "en_quote": "Adverse media monitoring is conducted to identify links to financial crime, corruption, and fraudulent activities.",
      "knowledge_zh": "负面媒体监控旨在识别与金融犯罪、腐败和欺诈活动的关联",
      "pdf_page": 311,
      "printed_page": "306",
      "type": "definition",
      "unit_id": "v7u_N003025",
      "unit_order": 3025
    },
    {
      "en_quote": "PEP screening is when organizations determine whether the individual or beneficial owner is a PEP, or the relative or close associate of a PEP.",
      "knowledge_zh": "政治敏感人物筛查用于确定个人或受益所有人是否为政治敏感人物或其亲属或密切关联人",
      "pdf_page": 311,
      "printed_page": "306",
      "type": "definition",
      "unit_id": "v7u_N003026",
      "unit_order": 3026
    }
  ],
  "core_points": [
    {
      "anchor_unit_ids": [
        "v7u_N003011",
        "v7u_N003012"
      ],
      "core_point_id": "cp_CH42_S01_001",
      "key_unit_ids": [
        "v7u_N003011",
        "v7u_N003012"
      ],
      "reason": "Overarching requirement for risk-based due diligence and KYC as core AFC control.",
      "support_unit_ids": [],
      "title_en": "Risk-Based KYC Requirement",
      "title_zh": "基于风险的KYC要求"
    },
    {
      "anchor_unit_ids": [
        "v7u_N003013"
      ],
      "core_point_id": "cp_CH42_S01_002",
      "key_unit_ids": [
        "v7u_N003013",
        "v7u_N003014",
        "v7u_N003016",
        "v7u_N003015"
      ],
      "reason": "Describes optional pre-KYC committee for high-risk profiles, its composition, outcome, and purpose.",
      "support_unit_ids": [
        "v7u_N003014",
        "v7u_N003015",
        "v7u_N003016"
      ],
      "title_en": "Pre-KYC Onboarding Committee",
      "title_zh": "KYC前准入委员会"
    },
    {
      "anchor_unit_ids": [
        "v7u_N003018",
        "v7u_N003019",
        "v7u_N003020"
      ],
      "core_point_id": "cp_CH42_S01_003",
      "key_unit_ids": [
        "v7u_N003018",
        "v7u_N003019",
        "v7u_N003020",
        "v7u_N003017"
      ],
      "reason": "Defines the ID&V step in KYC, covering identification and verification.",
      "support_unit_ids": [
        "v7u_N003017"
      ],
      "title_en": "Identity and Verification (ID&V)",
      "title_zh": "身份识别与验证"
    },
    {
      "anchor_unit_ids": [
        "v7u_N003021",
        "v7u_N003022"
      ],
      "core_point_id": "cp_CH42_S01_004",
      "key_unit_ids": [
        "v7u_N003021",
        "v7u_N003022"
      ],
      "reason": "Regulatory requirements to understand purpose of relationship and determine UBOs.",
      "support_unit_ids": [],
      "title_en": "Purpose and Beneficial Ownership Requirements",
      "title_zh": "了解客户目的与受益所有人要求"
    },
    {
      "anchor_unit_ids": [
        "v7u_N003023",
        "v7u_N003024",
        "v7u_N003025",
        "v7u_N003026"
      ],
      "core_point_id": "cp_CH42_S01_005",
      "key_unit_ids": [
        "v7u_N003023",
        "v7u_N003024",
        "v7u_N003025",
        "v7u_N003026"
      ],
      "reason": "Defines the screening step and its types: sanctions, adverse media, and PEP screening.",
      "support_unit_ids": [],
      "title_en": "Pre-Onboarding Screening",
      "title_zh": "准入前筛查"
    }
  ],
  "core_point_unit_edges": [
    {
      "edge_id": "p2b:cp_CH42_S01_001:v7u_N003011",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3011 states the overarching regulatory requirement for financial institutions to implement risk-based due diligence to prevent financial crime.",
      "relation_type": "states_rule",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_001",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003011"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_001:v7u_N003012",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3012 defines the KYC process as a core AFC compliance requirement for identifying, verifying, and assessing customer risks.",
      "relation_type": "defines",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_001",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003012"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_002:v7u_N003013",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3013 defines the pre-KYC onboarding committee concept, stating it assesses suitability for specific high-risk customer profiles before formal identification.",
      "relation_type": "defines",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_002",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003013"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_002:v7u_N003014",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3014 lists the typical composition of the committee, classifying its members.",
      "relation_type": "classifies",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_002",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003014"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_002:v7u_N003015",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3015 states the outcome of the committee's assessment, determining progression to full KYC and due diligence level.",
      "relation_type": "states_consequence",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_002",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003015"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_002:v7u_N003016",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3016 explains the purpose of the pre-KYC step, including efficient resource use, early risk mitigation, and regulatory alignment.",
      "relation_type": "explains",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_002",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003016"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_003:v7u_N003017",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3017 introduces the KYC/CDD process steps, providing context for the ID&V step.",
      "relation_type": "provides_context",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_003",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003017"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_003:v7u_N003018",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3018 names the ID&V step, classifying it as a component of the KYC process.",
      "relation_type": "classifies",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_003",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003018"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_003:v7u_N003019",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3019 defines identification as the collection of personal and business details.",
      "relation_type": "defines",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_003",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003019"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_003:v7u_N003020",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3020 defines verification as the authentication of provided information.",
      "relation_type": "defines",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_003",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003020"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_004:v7u_N003021",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3021 states the regulatory requirement to understand the purpose and intended nature of the customer relationship.",
      "relation_type": "states_rule",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_004",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003021"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_004:v7u_N003022",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3022 states the enhanced regulatory requirement to determine ultimate beneficial owners.",
      "relation_type": "states_rule",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_004",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003022"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_005:v7u_N003023",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3023 defines the screening step and its purpose of determining risk prior to onboarding.",
      "relation_type": "defines",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_005",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003023"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_005:v7u_N003024",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3024 describes sanctions screening as a type of pre-onboarding screening.",
      "relation_type": "classifies",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_005",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003024"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_005:v7u_N003025",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3025 describes adverse media monitoring as a type of pre-onboarding screening.",
      "relation_type": "classifies",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_005",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003025"
    },
    {
      "edge_id": "p2b:cp_CH42_S01_005:v7u_N003026",
      "edge_scope": "core_point_unit",
      "evidence_summary": null,
      "reason": "Unit 3026 describes PEP screening as a type of pre-onboarding screening.",
      "relation_type": "classifies",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_005",
      "source_phase": "P2B",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "v7u_N003026"
    }
  ],
  "same_section_core_point_edges": [
    {
      "edge_id": "p2c_rel_CH42_S01_001_002",
      "edge_scope": "same_section_core_point",
      "evidence_summary": null,
      "reason": "CP1 defines the risk-based KYC requirement, and CP2 describes the pre-KYC onboarding committee as a specific mechanism for high-risk profiles, which is a component of the overall KYC process.",
      "relation_type": "contains",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_001",
      "source_phase": "P2C",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "cp_CH42_S01_002"
    },
    {
      "edge_id": "p2c_rel_CH42_S01_001_003",
      "edge_scope": "same_section_core_point",
      "evidence_summary": null,
      "reason": "CP1 defines the KYC process, and CP3 details the Identity and Verification step, which is a core component of KYC.",
      "relation_type": "contains",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_001",
      "source_phase": "P2C",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "cp_CH42_S01_003"
    },
    {
      "edge_id": "p2c_rel_CH42_S01_001_004",
      "edge_scope": "same_section_core_point",
      "evidence_summary": null,
      "reason": "CP1 defines the KYC process, and CP4 specifies the requirement to understand purpose and beneficial ownership, which is a key element of KYC due diligence.",
      "relation_type": "contains",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_001",
      "source_phase": "P2C",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "cp_CH42_S01_004"
    },
    {
      "edge_id": "p2c_rel_CH42_S01_001_005",
      "edge_scope": "same_section_core_point",
      "evidence_summary": null,
      "reason": "CP1 defines the KYC process, and CP5 describes pre-onboarding screening, which is a critical step within the KYC framework.",
      "relation_type": "contains",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_001",
      "source_phase": "P2C",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "cp_CH42_S01_005"
    },
    {
      "edge_id": "p2c_rel_CH42_S01_002_003",
      "edge_scope": "same_section_core_point",
      "evidence_summary": null,
      "reason": "CP2 describes the pre-KYC committee that assesses suitability before formal identification, setting the stage for the ID&V step in CP3.",
      "relation_type": "prepares",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_002",
      "source_phase": "P2C",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "cp_CH42_S01_003"
    },
    {
      "edge_id": "p2c_rel_CH42_S01_002_005",
      "edge_scope": "same_section_core_point",
      "evidence_summary": null,
      "reason": "CP2's pre-KYC committee assessment occurs before the screening step described in CP5, preparing the customer for subsequent screening.",
      "relation_type": "prepares",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_002",
      "source_phase": "P2C",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "cp_CH42_S01_005"
    },
    {
      "edge_id": "p2c_rel_CH42_S01_003_004",
      "edge_scope": "same_section_core_point",
      "evidence_summary": null,
      "reason": "CP3 covers identity collection and verification, which is a prerequisite for understanding the customer's purpose and beneficial ownership in CP4.",
      "relation_type": "prepares",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_003",
      "source_phase": "P2C",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "cp_CH42_S01_004"
    },
    {
      "edge_id": "p2c_rel_CH42_S01_003_005",
      "edge_scope": "same_section_core_point",
      "evidence_summary": null,
      "reason": "CP3's ID&V step provides the customer information needed for the screening processes in CP5.",
      "relation_type": "prepares",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_003",
      "source_phase": "P2C",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "cp_CH42_S01_005"
    },
    {
      "edge_id": "p2c_rel_CH42_S01_004_005",
      "edge_scope": "same_section_core_point",
      "evidence_summary": null,
      "reason": "CP4's determination of purpose and beneficial ownership informs the risk assessment that drives the screening in CP5.",
      "relation_type": "prepares",
      "source_evidence_unit_ids": [],
      "source_id": "cp_CH42_S01_004",
      "source_phase": "P2C",
      "support_strength": null,
      "target_evidence_unit_ids": [],
      "target_id": "cp_CH42_S01_005"
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
