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
  "section_id": "CH49-S13",
  "flow_node_candidates": [
    {
      "candidate_id": "cand_CH49-S13_001",
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

section_id: `CH49-S13`

section_title: `Concluding an investigation and suspicious activity reporting > How law enforcement case investigators read a SAR`

core_points:

```json
[
  {
    "anchor_unit_ids": [
      "v7u_N003645",
      "v7u_N003650",
      "v7u_N003651"
    ],
    "core_point_id": "cp_CH49_S13_001",
    "key_unit_ids": [
      "v7u_N003645",
      "v7u_N003650",
      "v7u_N003651",
      "v7u_N003655",
      "v7u_N003656"
    ],
    "reason": "This single review point covers the entire section, as all units cohesively describe SARs, their value, limitations, and how law enforcement investigators use them to initiate and enhance cases.",
    "support_unit_ids": [
      "v7u_N003646",
      "v7u_N003647",
      "v7u_N003648",
      "v7u_N003649",
      "v7u_N003652",
      "v7u_N003653",
      "v7u_N003654",
      "v7u_N003655",
      "v7u_N003656",
      "v7u_N003657",
      "v7u_N003658",
      "v7u_N003659"
    ],
    "title_en": "How law enforcement case investigators read a SAR",
    "title_zh": "执法案件调查人员如何阅读可疑活动报告"
  }
]
```

same_section_cp_edges:

```json
[]
```

cp_unit_excerpt_map:

```json
{
  "v7u_N003645": {
    "type": "fact",
    "en_quote": "If an AFC program were a factory, suspicious activity reports (SAR) would be its most important product and law enforcement would be its main customer.",
    "knowledge_zh": "可疑活动报告（SAR）是金融犯罪防控（金融犯罪防控）项目最重要的产品，执法部门是其主要客户"
  },
  "v7u_N003646": {
    "type": "fact",
    "en_quote": "SARs can be used to initiate an investigation or enhance an ongoing investigation.",
    "knowledge_zh": "SAR可用于启动调查或增强正在进行的调查"
  },
  "v7u_N003647": {
    "type": "fact",
    "en_quote": "Law enforcement and the intelligence community use these reports to respond to illicit activity and gather intelligence useful in preventing future occurences.",
    "knowledge_zh": "执法和情报界利用SAR报告应对非法活动并收集情报以预防未来事件"
  },
  "v7u_N003648": {
    "type": "fact",
    "en_quote": "SAR data contains critical details to identify suspects, networks, jurisdictions, and, most importantly, the movement of illicit funds.",
    "knowledge_zh": "SAR数据包含识别嫌疑人、网络、司法管辖区和非法资金流动的关键细节"
  },
  "v7u_N003649": {
    "type": "fact",
    "en_quote": "SARs offer an abundance of direct and indirect access to evidence of money laundering and the illicit activity that fuels it.",
    "knowledge_zh": "SAR提供直接和间接获取洗钱及上游非法活动证据的丰富途径"
  },
  "v7u_N003650": {
    "type": "rule",
    "en_quote": "However, SARs cannot be used as evidence.",
    "knowledge_zh": "SAR不能作为证据使用"
  },
  "v7u_N003651": {
    "type": "definition",
    "en_quote": "The most important purpose of SARs is to assist law enforcement and analysts in collecting information and intelligence on potential illegal activity.",
    "knowledge_zh": "SAR最重要的目的是协助执法和分析人员收集潜在非法活动的信息和情报"
  },
  "v7u_N003652": {
    "type": "fact",
    "en_quote": "The phrase “follow the money” routinely proves to be true.",
    "knowledge_zh": "“跟着钱走”这句话在实践中经常被证明是正确的"
  },
  "v7u_N003653": {
    "type": "fact",
    "en_quote": "These reports are invaluable in initiating new cases, enhancing ongoing investigations, and developing broader financial intelligence activity monitoring.",
    "knowledge_zh": "SAR在启动新案件、增强现有调查和制定更广泛的金融情报活动监测方面具有不可估量的价值"
  },
  "v7u_N003654": {
    "type": "fact",
    "en_quote": "The SAR form data and narrative are critical for law enforcement and analysts to leverage in the field.",
    "knowledge_zh": "SAR表格数据和叙述对于执法和分析人员在实地工作中至关重要"
  },
  "v7u_N003655": {
    "type": "process",
    "en_quote": "Once they access the relevant database, they can effectively search names, identifiers, data, filing and subject entities, and vital narrative information.",
    "knowledge_zh": "执法部门访问相关数据库后可有效搜索姓名、标识符、数据、备案和主体实体以及关键叙述信息"
  },
  "v7u_N003656": {
    "type": "process",
    "en_quote": "Law enforcement will look at these reports to identify what the illicit activity was, where and when it occurred, what products were used to facilitate the activity, and—most importantly—why it is considered suspicious.",
    "knowledge_zh": "执法部门通过SAR识别非法活动内容、地点、时间、使用的产品以及被认定为可疑的原因"
  },
  "v7u_N003657": {
    "type": "process",
    "en_quote": "They can also search a SAR database to see if a suspect is mentioned in other SARs, which institution filed, and where the illicit money might have gone.",
    "knowledge_zh": "执法部门可搜索SAR数据库查看嫌疑人是否出现在其他SAR中、由哪家机构提交以及非法资金可能流向何处"
  },
  "v7u_N003658": {
    "type": "process",
    "en_quote": "Based on the pattern of activity—who, what, where, when, how, and why—law enforcement might develop or add criminal charges for the underlying activity and possible money laundering.",
    "knowledge_zh": "基于活动模式（谁、什么、地点、时间、方式、原因），执法部门可能增加或提出相关犯罪和洗钱指控"
  },
  "v7u_N003659": {
    "type": "process",
    "en_quote": "Law enforcement may be able to follow the money and other supporting data, determine other criminals involved in the activity, and expand the investigation further.",
    "knowledge_zh": "执法部门可追踪资金和其他支持数据，确定其他涉案犯罪分子并扩大调查范围"
  }
}
```
