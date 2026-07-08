# P2A section probe v2 prompt

You are helping design Phase 2A for a CAMS v7 textbook knowledge graph.

Task: For one complete section, assign each unit one function type from the provided candidate type table, then identify review-oriented `core_point` nodes inside the section.

Definitions:

- `section`: a P1 textbook section fragment identified by `section_id`.
- `unit`: a frozen base knowledge unit. The only formal reference object is `unit_id`.
- `core_point`: a review-outline knowledge node inside the section. It is not an exam point and not a question objective.

Hard rules:

1. Work only inside the provided `section_id`.
2. Use only the provided `unit_id` values. Do not invent unit IDs.
3. Do not rewrite or invent textbook evidence.
4. The input does not provide old per-unit `type`; do not infer that any hidden old type exists.
5. For `unit_function_labels`, choose exactly one `function_type` from `candidate_function_types`.
6. Do not create new function type names.
7. Use `section_text_with_unit_anchors` as the primary text view; use `units` for evidence lookup.
8. Do not output formal `core_point -> unit` role edges. That belongs to P2B.
9. A `core_point` should be useful as a review-outline node, not merely a local function type label.
10. If a section is too large for one clean judgment, still produce a best-effort result and mark the uncertainty in `needs_review`.

Candidate function types:

```text
definition
classification
rule
process
risk_indicator
case
context
fact
needs_review
```

Return exactly one JSON object with this shape:

```json
{
  "section_id": "CH02-S01",
  "unit_function_labels": [
    {
      "unit_id": "v7u_N000060",
      "function_type": "definition",
      "reason": "brief reason based on the section text"
    }
  ],
  "core_points": [
    {
      "draft_core_point_id": "cp_CH02_S01_001",
      "title_en": "short English review title",
      "title_zh": "简短中文复习标题",
      "anchor_unit_ids": ["v7u_N000060"],
      "support_unit_ids": ["v7u_N000061"],
      "reason": "why this is one review core_point"
    }
  ],
  "needs_review": []
}
```

