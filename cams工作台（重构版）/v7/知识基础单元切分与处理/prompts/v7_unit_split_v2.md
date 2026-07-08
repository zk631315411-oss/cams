# v7_unit_split_v2

You are grouping English CAMS textbook sentences into base knowledge units.

Return exactly one JSON object. Do not return Markdown.

## Task

For the given request, group the existing `sentence_id` values into base knowledge units.

## Hard Rules

1. Only use sentence IDs that appear in the request.
2. Every input sentence ID must appear exactly once in `sentence_groups`.
3. Do not invent, rewrite, merge, split, or translate source text.
4. A group should express one textbook knowledge unit that could later be cited by an exam question.
5. A single source sentence cannot be split.
6. Multiple sentences may be grouped only when they jointly express one complete knowledge unit.
7. If a sentence is a fragment, unresolved cross-block continuation, extraction damage, teaching metadata, non-content text, or otherwise unsafe as direct evidence, put that sentence in a `needs_review` group.
8. Normal English curly apostrophes, em dashes, accented Latin letters, and currency symbols are not corruption by themselves.
9. Imperative or recommendation-style textbook guidance is content, not teaching metadata, when it states a compliance expectation, risk-control practice, or exam-citable rule. For example, sentences such as "Use a broad definition for defining a PEP" should usually be `rule` or `obligation`, not `needs_review`, unless the sentence is actually a learning objective, exam instruction, navigation text, or other non-content metadata.

## Allowed Unit Types

Use only:

- `definition`
- `classification`
- `rule`
- `obligation`
- `process`
- `red_flag`
- `risk_indicator`
- `case_fact`
- `example`
- `fact`
- `needs_review`

## Output Schema

```json
{
  "request_id": "same request_id as input",
  "sentence_groups": [
    {
      "sentence_ids": ["existing_sentence_id"],
      "unit_type": "definition",
      "knowledge_hint_en": "short English label faithful to the grouped sentence(s)",
      "reason": "brief reason for the grouping",
      "risk_flags": []
    }
  ],
  "window_risk_flags": []
}
```

`knowledge_hint_en` is only a label. It is not evidence. Evidence text will be reconstructed later from `sentence_ids`.
