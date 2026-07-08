# P2A section probe v3 prompt

You are helping design Phase 2A for a CAMS v7 textbook knowledge graph.

Task: For one complete section, assign each unit one function type from the provided candidate type table, then identify review-oriented `core_point` nodes inside the section.

Definitions:

- `section`: a P1 textbook section fragment identified by `section_id`.
- `unit`: a frozen base knowledge unit. The only formal reference object is `unit_id`.
- `core_point`: a review-outline knowledge node inside the section. It is not an exam point and not a question objective.
- `non_contiguous core_point`: a core_point whose source units appear in more than one separated span inside the same section.

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
10. You may group non-contiguous units into one core_point if they clearly return to the same review topic within the same section.
11. Do not force non-contiguous grouping. Use it only when the section genuinely returns to an earlier topic after an intervening case, example, list, or background passage.

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

Core_point continuity rules:

- Every core_point must include `source_unit_spans`.
- Every core_point must include `non_contiguous`.
- If `non_contiguous` is `false`, `source_unit_spans` should contain one span.
- If `non_contiguous` is `true`, `source_unit_spans` must contain two or more spans, `intervening_unit_ids` must list the units between those spans, and `review_flags` must include `non_contiguous_core_point`.
- If non-contiguous grouping is plausible but uncertain, include `needs_human_granularity_review` in `review_flags` and explain why.

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
      "source_unit_spans": [[60, 61]],
      "non_contiguous": false,
      "intervening_unit_ids": [],
      "review_flags": [],
      "reason": "why this is one review core_point"
    }
  ],
  "needs_review": []
}
```

