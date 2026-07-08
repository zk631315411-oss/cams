# P2A section full-context probe prompt

You are helping design Phase 2A for a CAMS v7 textbook knowledge graph.

Task: For one complete section, identify review-oriented `core_point` nodes using only the provided units.

Definitions:

- `section`: a P1 textbook section fragment identified by `section_id`.
- `unit`: a frozen base knowledge unit. The only formal reference object is `unit_id`.
- `core_point`: a review-outline knowledge node inside the section. It is not an exam point and not a question objective.

Hard rules:

1. Work only inside the provided `section_id`.
2. Use only the provided `unit_id` values. Do not invent unit IDs.
3. Do not rewrite or invent textbook evidence.
4. Do not use old unit `type`; it is intentionally omitted.
5. Do not output `core_point -> unit` role edges. That belongs to P2B.
6. A `core_point` should be useful as a review-outline node, not merely a local text function label.
7. If several units are definition/example/risk materials for the same review topic, they may belong to one core_point.
8. If a section contains genuinely separate review topics, output multiple core_points.

Return exactly one JSON object with this shape:

```json
{
  "section_id": "CH02-S03",
  "unit_function_labels": [
    {
      "unit_id": "v7u_N000115",
      "function_label": "definition|classification|example|risk|rule|context|fact",
      "reason": "brief reason based on the unit text"
    }
  ],
  "core_points": [
    {
      "draft_core_point_id": "cp_CH02_S03_001",
      "title_en": "short English review title",
      "title_zh": "简短中文复习标题",
      "anchor_unit_ids": ["v7u_N000115"],
      "support_unit_ids": ["v7u_N000116"],
      "reason": "why this is one review core_point"
    }
  ],
  "needs_review": []
}
```

