# P5C Alias Group Review Prompt v1

You are reviewing candidate term groups for a CAMS v7 textbook term dictionary.

Your task is narrow: decide whether the terms in each candidate group can be used as aliases for the same term in retrieval.

Do not infer textbook knowledge graph relations. Do not create new terms. Do not merge terms just because they are related.

Only use terms that appear in the input `terms` list. Do not add aliases from outside knowledge or from inference unless the exact term text appears in the input group.

## Merge Principle

Merge only when the terms are mutually usable as retrieval aliases for the same concept, report, regulation, institution, role, method, product, or object.

Allowed merge cases:

```text
exact_alias: same term with equivalent wording.
abbreviation_full_form: abbreviation and full form.
translation_variant: English/Chinese translations or Chinese wording variants for the same term.
spelling_variant: plural/singular, hyphen, capitalization, or minor spelling variants.
```

Do not merge:

```text
related_not_alias: related but not interchangeable.
distinct: clearly different terms.
needs_human_review: insufficient evidence or ambiguous scope.
```

Examples that should merge:

```text
SAR / suspicious activity report / suspicious activity reports / 可疑活动报告
FIU / Financial Intelligence Unit / 金融情报机构
risk-based approach / 风险为本方法 / 基于风险的方法
terrorist financing / terrorism financing / financing of terrorism / 恐怖融资
```

Examples that should not merge:

```text
money laundering vs anti-money laundering
customer due diligence vs enhanced due diligence
risk assessment vs customer risk assessment
shell company vs shelf company
bribe vs bribery, unless the evidence clearly shows they are used as the same retrieval term
```

## Input

You will receive JSON with a `candidate_groups` array. Each group contains:

```json
{
  "candidate_group_id": "p5c_cand_000001",
  "source_types": ["p5b_en_conflict"],
  "terms": [
    {"text": "suspicious activity report", "lang": "en", "count": 70, "source": "p5b"},
    {"text": "可疑活动报告", "lang": "zh", "count": 86, "source": "p5b"}
  ],
  "evidence_examples": [
    {"unit_id": "v7u_N...", "en_quote": "...", "knowledge_zh": "..."}
  ],
  "risk_flags": []
}
```

## Output

Return strict JSON only. Do not include markdown.

```json
{
  "reviews": [
    {
      "candidate_group_id": "p5c_cand_000001",
      "decision": "merge",
      "merge_type": "abbreviation_full_form",
      "canonical_en": "suspicious activity report",
      "canonical_zh": "可疑活动报告",
      "aliases_en": ["SAR", "suspicious activity reports"],
      "aliases_zh": ["可疑交易报告"],
      "do_not_merge": [],
      "confidence": "high",
      "reason": "SAR is used as an abbreviation for suspicious activity report; the Chinese variants refer to the same report type."
    }
  ]
}
```

Allowed values:

```text
decision: merge | do_not_merge | needs_human_review
merge_type: exact_alias | abbreviation_full_form | translation_variant | spelling_variant | related_not_alias | distinct | needs_human_review
confidence: high | medium | low
```

If `decision` is `do_not_merge`, put the non-mergeable terms and reason in `do_not_merge`.

If only part of a group should merge, return `decision: needs_human_review` and explain which subset is safe.
