# P5C alias group test

Purpose: test P5C alias/synonym grouping before formalizing it.

P5C does not extract new terms. It reviews candidate groups from P5A/P5B and decides whether the names in a group can be used as retrieval aliases for the same term.

Current test inputs:

```text
Formal P5B:
phases/phase05_terms/outputs/p5b_zh_en_mapping.json

Formal P5A:
phases/phase05_terms/outputs/p5a_abbreviation_mapping.json
```

Files:

```text
prompts/p5c_alias_group_review_v1.md
scripts/build_p5c_alias_candidates.py
scripts/run_p5c_alias_review_ds.py
```

Planned flow:

```text
1. build_p5c_alias_candidates.py
   - Build bounded candidate groups from P5B conflicts and optional P5A abbreviation/full-form edges.

2. run_p5c_alias_review_ds.py
   - Send candidate groups to a sub-agent/LLM in small batches.
   - The model only decides alias equivalence, not KG relations.

3. Manual review
   - Inspect model decisions marked needs_human_review or low confidence.
```

Decision labels:

```text
exact_alias
abbreviation_full_form
translation_variant
spelling_variant
related_not_alias
distinct
needs_human_review
```

Core rule:

```text
Merge only if the terms are mutually usable as retrieval aliases for the same concept/entity/report/object.
Do not merge merely related concepts.
```
