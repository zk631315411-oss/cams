# P5A abbreviation/full-form first-five test

Purpose: test the P5A abbreviation ↔ full-form discovery rule on the first five chapters.

Scope:

```text
P1 first_five_chapters_units.jsonl gives the first-five unit_id set.
P0 eligible_units.jsonl provides unit.terms and en_quote.
```

Rule under test:

```text
1. Extract abbreviations from en_quote.
2. Extract English full-form candidates from unit.terms.
3. Record abbreviation/full-form co-occurrence inside the same unit.
4. Parenthetical evidence like `full form (ABBR)` or `ABBR (full form)` can auto-merge even when low frequency.
5. Compound slash abbreviations can auto-merge each component when the component initials match a co-occurring full form.
6. Statistical auto-merge requires cooccur_count >= 1, abbr_unit_count >= 3, abbr_overlap_ratio >= 0.5, full_form_overlap_ratio >= 0.5, and no stronger competing full-form candidate.
7. Otherwise keep the pair as candidate/review-only or keep the abbreviation as independent.
```

Outputs:

```text
outputs/p5a_abbreviation_candidates_first5.json
outputs/p5a_abbreviation_summary_first5.json
previews/p5a_abbreviation_candidates_first5.md
```
