# P7C Granularity Probe v2

Purpose: test a narrower named-level granularity addendum.

v1 proved that prompt-only granularity control can split `CH47-S06`, but it also increased review burden for unrelated complex branching sections. v2 narrows the trigger: split only when the source explicitly presents named levels, stages, phases, layers, or review tiers.

This test does not modify the production P7C prompt.

## Prompt

`prompts/section_card_extraction_v1_granularity_probe_v2.md`

## Regression Sections

```text
CH47-S03,CH47-S04,CH47-S06,CH47-S08,CH47-S13,CH47-S16,CH49-S10,CH49-S14,CH49-S16
```

## Success Criteria

- `CH47-S06` should split into smaller named-level cards.
- `CH47-S03`, `CH47-S04`, `CH47-S08`, `CH47-S16`, `CH49-S10`, `CH49-S14`, and `CH49-S16` should remain close to baseline behavior.
- `CH49-S14` should not worsen merely because it has multiple branches/customer types.
- validation errors should remain 0.

## Failure Criteria

- `CH47-S06` remains a single overmerged macro card.
- non-named-level sections fragment or receive worse P7D required routing.
- validation errors increase.

