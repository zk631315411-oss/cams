# P7C CP-to-Candidate Prompt v1

## Role

You are the first-stage recall assistant in a P7C AB test.

Your task is to organize section-local core points into possible P7 flow-node candidates. You are not extracting final P7 cards in this stage.

## Non-Negotiable Boundary

Do not output final `flow_nodes`, `flow_edges`, `cards`, or a process graph.

Core points are broad knowledge groupings. A core point is not automatically a P7 node. CP-CP relations such as `prepares` are not P7 flow edges.

The output is a recall-oriented candidate pool. The second-stage extractor may delete, merge, split, relabel, retype, or supplement every candidate after reading the section units.

## What Counts as a Useful Candidate

Create a candidate only when a core point may contribute to a section-local handling path or judgement path. Candidate roles include:

```text
scenario
trigger
action
decision
input
criterion
condition
safeguard
limitation
exception
outcome
implication
output
```

Good candidates help answer one of these questions:

```text
What situation starts or changes handling?
What should an institution, analyst, system, or control function do?
What input, criterion, standard, threshold, safeguard, or limitation is used?
What judgement, effect, output, record, escalation, restriction, or monitoring result follows?
What makes an exam option correct, incorrect, too broad, too narrow, or conditional?
```

Do not create candidates for pure definitions, aliases, background facts, isolated examples, or generic concept relations unless they carry a usable handling or judgement role.

## Candidate Construction Rules

1. One CP may yield zero, one, or multiple candidates.
2. Multiple CPs may support one candidate.
3. Candidate labels should express a possible role in a handling or judgement path, not merely repeat a CP title.
4. Use CP unit IDs to identify likely evidence, but do not claim that a candidate is already a validated final node.
5. `same_section_cp_edges` may help interpret topic organization only. Never translate them into `PRECEDES`, `USES`, `PRODUCES`, `DECIDES`, or `FEEDBACK`.
6. Keep uncertain but plausible candidates with `confidence: "low"` and explain the uncertainty.
7. Reject CPs that appear to contain only ordinary KG material.

## Output JSON Shape

Return strict JSON only. Do not include markdown fences.

```json
{
  "section_id": "CH47-S04",
  "flow_node_candidates": [
    {
      "candidate_id": "cand_CH47-S04_001",
      "candidate_kind": "criterion",
      "candidate_label": "Possible concise role label",
      "candidate_role": "How this material may contribute to a P7 handling or judgement path",
      "source_core_point_ids": ["cp_..."],
      "evidence_unit_ids": ["v7u_..."],
      "cp_match_status": "exact",
      "confidence": "high",
      "reason": "Why this is a useful candidate rather than ordinary KG content"
    }
  ],
  "rejected_core_points": [
    {
      "core_point_id": "cp_...",
      "reason": "Why it is ordinary KG material or otherwise not useful for P7 candidate recall"
    }
  ],
  "cp_edge_notes": [
    {
      "edge_id": "p2c_...",
      "note": "Optional observation about topic organization; explicitly not a P7 edge"
    }
  ]
}
```

Allowed `candidate_kind` values:

```text
scenario
trigger
action
decision
input
criterion
condition
safeguard
limitation
exception
outcome
implication
output
```

Allowed `cp_match_status` values:

```text
exact
partial
ambiguous
```

Allowed `confidence` values:

```text
high
medium
low
```

## Current Section CP Package

section_id: `CH47-S04`

section_title: `Transaction monitoring > Transaction monitoring system tuning`

core_points:

```json
[
  {
    "anchor_unit_ids": [
      "v7u_N003272"
    ],
    "core_point_id": "cp_CH47_S04_001",
    "key_unit_ids": [
      "v7u_N003272",
      "v7u_N003273",
      "v7u_N003274",
      "v7u_N003275",
      "v7u_N003276"
    ],
    "reason": "Provides the definition of TM system tuning and lists its key benefits as a single review point.",
    "support_unit_ids": [
      "v7u_N003273",
      "v7u_N003274",
      "v7u_N003275",
      "v7u_N003276",
      "v7u_N003277"
    ],
    "title_en": "TM System Tuning: Definition and Importance",
    "title_zh": "交易监控系统调优：定义与重要性"
  },
  {
    "anchor_unit_ids": [
      "v7u_N003278"
    ],
    "core_point_id": "cp_CH47_S04_002",
    "key_unit_ids": [
      "v7u_N003278",
      "v7u_N003280",
      "v7u_N003284",
      "v7u_N003279",
      "v7u_N003282"
    ],
    "reason": "Groups the classification of four components with the definitions and details of the components explicitly covered (scenario setting, threshold setting, frequency).",
    "support_unit_ids": [
      "v7u_N003279",
      "v7u_N003280",
      "v7u_N003281",
      "v7u_N003282",
      "v7u_N003283",
      "v7u_N003284",
      "v7u_N003285"
    ],
    "title_en": "Key Components of Tuning",
    "title_zh": "调优的关键组成部分"
  },
  {
    "anchor_unit_ids": [
      "v7u_N003286"
    ],
    "core_point_id": "cp_CH47_S04_003",
    "key_unit_ids": [
      "v7u_N003286"
    ],
    "reason": "Captures the rule that tuning should be dynamic and event-triggered as a standalone review point.",
    "support_unit_ids": [],
    "title_en": "Dynamic Tuning Requirement",
    "title_zh": "动态调优要求"
  }
]
```

same_section_cp_edges:

```json
[
  {
    "edge_id": "p2c_rel_CH47_S04_001_002",
    "edge_scope": "same_section_core_point",
    "evidence_summary": null,
    "reason": "CP1 defines TM system tuning and its importance, providing foundational understanding for CP2 which details the key components of tuning.",
    "relation_type": "prepares",
    "source_evidence_unit_ids": [],
    "source_id": "cp_CH47_S04_001",
    "source_phase": "P2C",
    "support_strength": null,
    "target_evidence_unit_ids": [],
    "target_id": "cp_CH47_S04_002"
  },
  {
    "edge_id": "p2c_rel_CH47_S04_002_003",
    "edge_scope": "same_section_core_point",
    "evidence_summary": null,
    "reason": "CP2 explains the components of tuning, including frequency, which sets the stage for CP3's requirement that tuning be dynamic and triggered by events.",
    "relation_type": "prepares",
    "source_evidence_unit_ids": [],
    "source_id": "cp_CH47_S04_002",
    "source_phase": "P2C",
    "support_strength": null,
    "target_evidence_unit_ids": [],
    "target_id": "cp_CH47_S04_003"
  }
]
```

cp_unit_excerpt_map:

```json
{
  "v7u_N003272": {
    "type": "classification",
    "en_quote": "TM system tuning is the process of refining and adjusting parameters and thresholds of specific detection logic rules, or scenarios. Scenarios are designed to detect suspicious activities and abnormal transaction behaviors, such as money laundering, fraud, or other illicit activities. Tuning is important because it:",
    "knowledge_zh": "交易监控系统调优是调整检测规则参数和阈值的过程。"
  },
  "v7u_N003273": {
    "type": "risk_indicator",
    "en_quote": "Ensures the TM system effectively detects suspicious activity.",
    "knowledge_zh": "调优确保交易监控系统有效检测可疑活动。"
  },
  "v7u_N003274": {
    "type": "fact",
    "en_quote": "Reduces false positives.",
    "knowledge_zh": "调优减少误报。"
  },
  "v7u_N003275": {
    "type": "fact",
    "en_quote": "Ensures efficient resource use.",
    "knowledge_zh": "调优确保资源高效利用。"
  },
  "v7u_N003276": {
    "type": "fact",
    "en_quote": "Allows organizations to manage changes in financial crime and in their business operations.",
    "knowledge_zh": "调优使组织能够应对金融犯罪和业务运营的变化。"
  },
  "v7u_N003277": {
    "type": "fact",
    "en_quote": "Ensures regulatory compliance.",
    "knowledge_zh": "调优确保监管合规。"
  },
  "v7u_N003278": {
    "type": "fact",
    "en_quote": "Tuning involves four key components: scenario setting, customer segmentation, threshold setting, and frequency.",
    "knowledge_zh": "调优包括场景设置、客户细分、阈值设置和频率四个关键组成部分。"
  },
  "v7u_N003279": {
    "type": "definition",
    "en_quote": "Scenario setting involves creating, modifying, or removing detection rules and scenarios based on previous experiences with suspicious activity and actual incidents.",
    "knowledge_zh": "场景设置是基于以往经验创建、修改或移除检测规则和场景。"
  },
  "v7u_N003280": {
    "type": "definition",
    "en_quote": "Threshold setting defines the minimum level of activity required for a transaction to trigger an alert.",
    "knowledge_zh": "阈值设置定义了触发警报所需的最低活动水平。"
  },
  "v7u_N003281": {
    "type": "case",
    "en_quote": "For example, the threshold for reporting a CTR might be any currency transaction that exceeds US$10,000.",
    "knowledge_zh": "货币交易报告（CTR）阈值示例：超过10,000美元的任何货币交易"
  },
  "v7u_N003282": {
    "type": "fact",
    "en_quote": "Adjusting thresholds refines sensitivity and accuracy.",
    "knowledge_zh": "调整阈值可提高交易监控系统的灵敏度和准确性"
  },
  "v7u_N003283": {
    "type": "rule",
    "en_quote": "Reducing the number of false positives is a key goal in setting thresholds to make the most efficient use of resources.",
    "knowledge_zh": "减少误报是设定阈值的关键目标，以高效利用资源"
  },
  "v7u_N003284": {
    "type": "fact",
    "en_quote": "The frequency determines how often tuning should occur.",
    "knowledge_zh": "调优频率决定了交易监控系统应多久进行一次调整"
  },
  "v7u_N003285": {
    "type": "fact",
    "en_quote": "The frequency might also be influenced by changes in business strategy, anomalies, regulatory updates, or market changes.",
    "knowledge_zh": "调优频率受业务策略变化、异常、监管更新或市场变化影响"
  },
  "v7u_N003286": {
    "type": "rule",
    "en_quote": "Tuning should be dynamic, with special assessments triggered by significant events or trends.",
    "knowledge_zh": "调优应是动态的，重大事件或趋势应触发专项评估"
  }
}
```
