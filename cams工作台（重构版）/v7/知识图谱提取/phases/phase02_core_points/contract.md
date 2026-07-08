# P2A Contract

## Input Object

```json
{
  "request_id": "p2a::CH02-S03",
  "chapter_id": "CH02",
  "section_id": "CH02-S03",
  "section_order": 3,
  "section_title": "Types of financial crime > Bribery and corruption",
  "candidate_function_types": [
    {"function_type": "definition", "description_zh": "定义、概念边界、术语解释"}
  ],
  "section_text_with_unit_anchors": "[v7u_N000115|115] Bribery is...",
  "units": [
    {
      "chapter_id": "CH02",
      "section_id": "CH02-S03",
      "section_title": "Types of financial crime > Bribery and corruption",
      "unit_order": 115,
      "unit_id": "v7u_N000115",
      "knowledge_zh": "贿赂的定义...",
      "en_quote": "Bribery is...",
      "printed_page": "25",
      "pdf_page": 30
    }
  ]
}
```

禁止输入字段：

```text
type
unit_type
old_type
```

## Output Object

```json
{
  "section_id": "CH02-S03",
  "unit_function_labels": [
    {
      "unit_id": "v7u_N000115",
      "function_type": "definition",
      "reason": "Defines bribery."
    }
  ],
  "core_points": [
    {
      "draft_core_point_id": "cp_CH02_S03_001",
      "title_en": "Bribery definition and forms",
      "title_zh": "贿赂的定义与形式",
      "anchor_unit_ids": ["v7u_N000115"],
      "support_unit_ids": ["v7u_N000116"],
      "concept_unit_spans": [[115, 115]],
      "evidence_unit_spans": [[115, 116]],
      "non_contiguous_concept": false,
      "intervening_support_unit_ids": [],
      "review_flags": [],
      "reason": "Why this is one review core_point."
    }
  ],
  "needs_review": []
}
```

## Validation Rules

1. Every `unit_function_labels[].unit_id` must be in input `units`.
2. Every `function_type` must be in `candidate_function_types`.
3. Every unit ID referenced by a core_point must be in input `units`.
4. `concept_unit_spans` and `evidence_unit_spans` must use unit_order values from the same section.
5. If `non_contiguous_concept=true`, `concept_unit_spans` must have two or more spans and `review_flags` must include `non_contiguous_concept_units` or equivalent.
6. P2A must not output formal `core_point -> unit` role edges.

