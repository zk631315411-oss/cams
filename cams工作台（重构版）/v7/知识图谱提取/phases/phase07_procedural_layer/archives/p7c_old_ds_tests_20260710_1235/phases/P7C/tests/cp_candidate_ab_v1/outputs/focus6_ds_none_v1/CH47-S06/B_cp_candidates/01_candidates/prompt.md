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
  "section_id": "CH47-S06",
  "flow_node_candidates": [
    {
      "candidate_id": "cand_CH47-S06_001",
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

section_id: `CH47-S06`

section_title: `Transaction monitoring > Procedures for alerts review`

core_points:

```json
[
  {
    "anchor_unit_ids": [
      "v7u_N003295",
      "v7u_N003296",
      "v7u_N003297"
    ],
    "core_point_id": "cp_CH47_S06_001",
    "key_unit_ids": [
      "v7u_N003295",
      "v7u_N003296",
      "v7u_N003297",
      "v7u_N003298",
      "v7u_N003300"
    ],
    "reason": "Covers the two main approaches (multi-level for large orgs, one-touch for small) and the definition and steps of Level 1 initial review; these form a coherent starting point for understanding the alert review procedure.",
    "support_unit_ids": [
      "v7u_N003298",
      "v7u_N003299",
      "v7u_N003300",
      "v7u_N003301"
    ],
    "title_en": "Alert Review Approaches and Level 1 Initial Review",
    "title_zh": "警报审查方法和一级初步审查"
  },
  {
    "anchor_unit_ids": [
      "v7u_N003302"
    ],
    "core_point_id": "cp_CH47_S06_002",
    "key_unit_ids": [
      "v7u_N003302",
      "v7u_N003303",
      "v7u_N003304",
      "v7u_N003305",
      "v7u_N003306"
    ],
    "reason": "Focuses solely on the Level 2 investigation stage, including its definition and the list of analytical activities performed; this is a distinct review topic within the section.",
    "support_unit_ids": [
      "v7u_N003303",
      "v7u_N003304",
      "v7u_N003305",
      "v7u_N003306",
      "v7u_N003307",
      "v7u_N003308"
    ],
    "title_en": "Level 2 Investigation Stage",
    "title_zh": "二级调查阶段"
  },
  {
    "anchor_unit_ids": [
      "v7u_N003309",
      "v7u_N003310"
    ],
    "core_point_id": "cp_CH47_S06_003",
    "key_unit_ids": [
      "v7u_N003309",
      "v7u_N003310",
      "v7u_N003311",
      "v7u_N003312",
      "v7u_N003313"
    ],
    "reason": "Covers the escalation to Level 3 complex analysis and the subsequent documentation, ongoing monitoring, and preventive recommendations; these are logically grouped as the final stages of the alert review process.",
    "support_unit_ids": [
      "v7u_N003311",
      "v7u_N003312",
      "v7u_N003313"
    ],
    "title_en": "Level 3 Complex Analysis and Post-Review Actions",
    "title_zh": "三级复杂分析和审查后行动"
  }
]
```

same_section_cp_edges:

```json
[
  {
    "edge_id": "p2c_rel_CH47_S06_001_002",
    "edge_scope": "same_section_core_point",
    "evidence_summary": null,
    "reason": "Level 1 initial review (CP1) is the prerequisite stage that triggers escalation to Level 2 investigation (CP2).",
    "relation_type": "prepares",
    "source_evidence_unit_ids": [],
    "source_id": "cp_CH47_S06_001",
    "source_phase": "P2C",
    "support_strength": null,
    "target_evidence_unit_ids": [],
    "target_id": "cp_CH47_S06_002"
  },
  {
    "edge_id": "p2c_rel_CH47_S06_002_003",
    "edge_scope": "same_section_core_point",
    "evidence_summary": null,
    "reason": "Level 2 investigation (CP2) escalates highly suspicious cases to Level 3 complex analysis (CP3).",
    "relation_type": "prepares",
    "source_evidence_unit_ids": [],
    "source_id": "cp_CH47_S06_002",
    "source_phase": "P2C",
    "support_strength": null,
    "target_evidence_unit_ids": [],
    "target_id": "cp_CH47_S06_003"
  }
]
```

cp_unit_excerpt_map:

```json
{
  "v7u_N003295": {
    "type": "fact",
    "en_quote": "In larger organizations, the process for reviewing transaction monitoring alerts typically involves multiple levels of review and information gathering.",
    "knowledge_zh": "大型机构采用多级警报审查流程，涉及多级审查和信息收集"
  },
  "v7u_N003296": {
    "type": "fact",
    "en_quote": "Smaller organizations might use a one-touch system, where a single analyst handles the alert from generation through the submission of a SAR.",
    "knowledge_zh": "小型机构可能采用单点接触系统，由一名分析师处理从警报生成到提交可疑活动报告的全过程"
  },
  "v7u_N003297": {
    "type": "definition",
    "en_quote": "When multiple levels of reviews are used, Level 1 review—or the initial review stage—occurs when a TM system generates an alert.",
    "knowledge_zh": "一级审查是交易监控系统生成警报后的初始审查阶段"
  },
  "v7u_N003298": {
    "type": "process",
    "en_quote": "An analyst examines the alert’s validity by evaluating various data points, including the alert's nature, transaction type, customer profile, account history, and previous alert history.",
    "knowledge_zh": "分析师通过评估警报性质、交易类型、客户资料、账户历史等数据点检查警报有效性"
  },
  "v7u_N003299": {
    "type": "process",
    "en_quote": "This analysis helps determine if the activity aligns with expected customer behavioral patterns.",
    "knowledge_zh": "分析旨在确定活动是否符合预期的客户行为模式"
  },
  "v7u_N003300": {
    "type": "process",
    "en_quote": "If the activity appears abnormal or exceeds accepted thresholds, the alert escalates to Level 2 review for further investigation.",
    "knowledge_zh": "若活动异常或超出阈值，警报升级至二级审查进行进一步调查"
  },
  "v7u_N003301": {
    "type": "process",
    "en_quote": "If not, the analyst can dismiss it as a false positive, and document sufficient rationale for arriving at that conclusion.",
    "knowledge_zh": "分析师可将警报判定为误报并记录充分理由"
  },
  "v7u_N003302": {
    "type": "classification",
    "en_quote": "During the Level 2 review, or investigation stage, analysts perform a detailed analysis of the alert and data from the initial review to establish whether the unusual behavior could indicate a financial crime. This stage typically includes:",
    "knowledge_zh": "二级审查（调查阶段）对警报和数据进行详细分析以判断是否指向金融犯罪"
  },
  "v7u_N003303": {
    "type": "fact",
    "en_quote": "Analyzing transaction patterns and frequency.",
    "knowledge_zh": "分析交易模式和频率"
  },
  "v7u_N003304": {
    "type": "fact",
    "en_quote": "Assessing the source and destination of funds.",
    "knowledge_zh": "评估资金来源和去向"
  },
  "v7u_N003305": {
    "type": "fact",
    "en_quote": "Reviewing KYC information and the customer risk profile.",
    "knowledge_zh": "审查了解你的客户信息和客户风险画像"
  },
  "v7u_N003306": {
    "type": "fact",
    "en_quote": "Gathering additional records, such as communication logs between the customer and institution, and any prior investigations related to the customer or account.",
    "knowledge_zh": "收集额外记录，如客户与机构沟通记录及既往调查信息"
  },
  "v7u_N003307": {
    "type": "fact",
    "en_quote": "Conducting open-source research to include social media, news articles, public records and notices, alerts, or guidance issued by law enforcement and regulatory agencies, to inform their opinion on the escalated activity.",
    "knowledge_zh": "开展开源研究，包括社交媒体、新闻、公共记录及监管机构发布的警报和指引"
  },
  "v7u_N003308": {
    "type": "process",
    "en_quote": "Analysts then determine whether the activity is suspicious, providing a robust rationale based on the data collected.",
    "knowledge_zh": "分析师基于收集的数据判定活动是否可疑并提供充分理由"
  },
  "v7u_N003309": {
    "type": "rule",
    "en_quote": "Highly suspicious cases or those that involve numerous transactions or sensitive situations should be escalated to Level 3 review, or the complex analysis stage.",
    "knowledge_zh": "高度可疑案件应升级至三级审查（复杂分析阶段）"
  },
  "v7u_N003310": {
    "type": "risk_indicator",
    "en_quote": "Senior analysts or compliance officers conduct this comprehensive assessment, which might include cross-department collaboration, complex risk assessments, and intricate analysis of transaction networks.",
    "knowledge_zh": "高级分析师或合规官开展全面评估，包括跨部门协作、复杂风险评估和交易网络分析"
  },
  "v7u_N003311": {
    "type": "process",
    "en_quote": "Throughout this process, analysts meticulously document each step and, if required, file SARs with regulatory authorities, ensuring they include all pertinent information and rationale.",
    "knowledge_zh": "分析师在审查过程中详细记录每一步，必要时向监管机构提交可疑活动报告"
  },
  "v7u_N003312": {
    "type": "rule",
    "en_quote": "Following the filing, ongoing monitoring is critical to mitigate further issues and identify additional criminal activities.",
    "knowledge_zh": "提交可疑活动报告后需持续监控以防范进一步风险并识别其他犯罪活动"
  },
  "v7u_N003313": {
    "type": "process",
    "en_quote": "Analysts often recommend enhanced customer monitoring or account restrictions as preventive measures.",
    "knowledge_zh": "分析师常建议加强客户监控或限制账户作为预防措施"
  }
}
```
