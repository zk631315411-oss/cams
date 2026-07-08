# P2A section core points v1

You are helping build Phase 2A for a CAMS v7 textbook knowledge graph.

Task: For one complete section, assign each unit one function type from the provided candidate type table, then identify review-oriented `core_point` nodes inside the section.

Definitions:

- `section`: a P1 textbook section fragment identified by `section_id`.
- `unit`: a frozen base knowledge unit. The only formal reference object is `unit_id`.
- `core_point`: a review-outline knowledge node inside the section. It is not an exam point and not a question objective.
- `non_contiguous_concept`: the concept-anchor units of a core_point appear in separated spans inside the same section.

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
10. You may group non-contiguous concept units into one core_point if they clearly return to the same review topic within the same section.
11. Do not force non-contiguous grouping. Use it only when the section genuinely returns to an earlier topic after an intervening case, example, list, or background passage.
12. If `non_contiguous_concept` is `true`, `review_flags` must include `needs_human_granularity_review`.

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

Core_point span rules:

- `concept_unit_spans` covers the core conceptual anchors, such as definitions, classifications, rules, and named models.
- `evidence_unit_spans` covers all units used by the core_point, including support, examples, and cases.
- Keep support narrow. P2A support is rough evidence only; formal `core_point -> unit` role edges belong to P2B.
- If examples sit between concept anchors, `concept_unit_spans` may be non-contiguous while `evidence_unit_spans` may remain continuous.
- If `non_contiguous_concept` is `true`, `concept_unit_spans` must contain two or more spans and `intervening_support_unit_ids` must list support/case/context units between concept spans.
- Add `needs_human_granularity_review` when the non-contiguous grouping is plausible but schema-sensitive.

Examples:

- Good non-contiguous grouping: units 124-128 describe forms of corruption. Unit 125 defines embezzlement, unit 126 gives an embezzlement case, unit 127 defines graft, and unit 128 gives a graft case. This may be one core_point about "forms of corruption" with `concept_unit_spans` as `[[124, 125], [127, 127]]`, `evidence_unit_spans` as `[[124, 128]]`, `non_contiguous_concept` as `true`, unit 126 as an intervening support unit, and `review_flags` including `needs_human_granularity_review`.
- Bad non-contiguous grouping: unit 119 says public officials are susceptible to corruption, while units 129-130 discuss bribery/corruption links to money laundering. They both involve risk, but they are not the same named review topic. Do not merge them only because they share a broad category such as risk, compliance, crime, control, or relationship.
- Good short Key takeaways grouping: units 9 and 11 both discuss warning signs or suspicious activity indicators, and unit 12 discusses collaboration that helps uncover crime. These may be one review point about "suspicious activity detection and investigation support". Do not create one core_point per unit merely because the section is short.
- Bad long Key takeaways grouping: do not merge a long Key takeaways section into a few broad buckets merely because all units share the same section title. For example, bribery risks and controls, tax avoidance/evasion/CRS, and fraud/red flags are separate review areas and should usually become separate core_points or small clusters.
- Good long Key takeaways splitting: when a long Key takeaways section moves through multiple natural review topics, keep those topics separate. For example, tax avoidance definition, tax evasion definition/examples/penalties, aggressive tax avoidance, tax evasion as a money-laundering predicate offense, AFC monitoring indicators, CRS reporting, fraud fundamentals, and fraud red flags are usually separate review points or small clusters. Do not collapse them into one tax core_point or one fraud core_point if the section contains enough material for separate review nodes.
- Bad support boundary: unit 184 and unit 193 both discuss trust in cyber-enabled crime. Units 185-187 may support a review point about trust-based cybercrime methods. Units 188-192 are a different list about crime outcomes/results, so do not include all of them as support for the trust core_point merely because they sit between units 184 and 193.
- Good topic return with unrelated intervening units: unit 205 introduces that detecting human trafficking/smuggling requires multiple indicators, and units 210-215 later list indicators. Units 206-209 discuss operational characteristics, not support for the indicator topic. This may be a non-contiguous core_point with separate `evidence_unit_spans`, empty `intervening_support_unit_ids`, `review_flags` including `needs_human_granularity_review`, and a reason explaining that the topic returns after unrelated material.

Return exactly one JSON object with this shape:

```json
{
  "section_id": "CH02-S03",
  "unit_function_labels": [
    {
      "unit_id": "v7u_N000115",
      "function_type": "definition",
      "reason": "brief reason based on the section text"
    }
  ],
  "core_points": [
    {
      "draft_core_point_id": "cp_CH02_S03_001",
      "title_en": "short English review title",
      "title_zh": "简短中文复习标题",
      "anchor_unit_ids": ["v7u_N000115"],
      "support_unit_ids": ["v7u_N000116"],
      "concept_unit_spans": [[115, 115]],
      "evidence_unit_spans": [[115, 116]],
      "non_contiguous_concept": false,
      "intervening_support_unit_ids": [],
      "review_flags": [],
      "reason": "why this is one review core_point"
    }
  ],
  "needs_review": []
}
```
