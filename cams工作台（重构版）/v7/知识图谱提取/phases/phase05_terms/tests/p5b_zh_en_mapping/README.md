# P5B zh/en mapping test

Purpose: test the Chinese ↔ English term mapping step for P5.

P5B does not depend on P5A. P5A handles abbreviation ↔ full form. P5B handles bilingual mapping from `unit.terms`.

Input:

```text
phases/phase00_quality_gate/outputs/eligible_units.jsonl
```

Optional first-five filter:

```text
phases/phase01_chapter_index/outputs/first_five_chapters_units.jsonl
```

Rule under test:

```text
1. Read each unit.terms item as an observed (en, zh) pair.
2. Normalize English by lowercase and whitespace; keep Chinese text as the display value after trimming whitespace.
3. Count pair frequency, English total frequency, and Chinese total frequency.
4. Mark clean mappings when one English maps to one Chinese and one Chinese maps back to one English.
5. Mark review items when one English has multiple Chinese translations or one Chinese has multiple English terms.
6. Keep low-frequency mappings, but flag them for review instead of deleting them.
```

Outputs:

```text
outputs/p5b_zh_en_mapping_first5.json
outputs/p5b_zh_en_mapping_all.json
previews/p5b_zh_en_mapping_first5.md
previews/p5b_zh_en_mapping_all.md
```

