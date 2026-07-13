# P7C Granularity Probe v1

Purpose: test whether a prompt-only granularity addendum can make DS avoid overmerged macro cards while preserving good existing card behavior.

This test does not modify the production P7C prompt.

## Prompt

`prompts/section_card_extraction_v1_granularity_probe.md`

The prompt is copied from the production `section_card_extraction_v1.md` and adds a card-boundary self-check:

- split when one card combines multiple named levels/stages with separate objectives or outputs;
- split when one card combines review/investigation with later reporting, monitoring, remediation, or restriction flows;
- keep parallel criteria inside one card;
- keep multi-component control cards intact when they share one objective.

## Regression Sections

```text
CH47-S03,CH47-S04,CH47-S06,CH47-S08,CH47-S13,CH47-S16,CH49-S10,CH49-S14,CH49-S16
```

## Success Criteria

- `CH47-S06` should no longer be one 25-node / 26-edge macro card.
- `CH47-S03` should remain a small set of capability/control cards, not be over-split.
- `CH47-S04` should remain one TM tuning control card.
- `CH47-S08`, `CH47-S16`, `CH49-S10`, and `CH49-S14` should not degrade semantically.
- validation errors should remain 0.

## Failure Criteria

- prompt causes control cards to fragment into one card per standard/component;
- prompt causes simple sequential workflows to fragment into one card per step;
- `CH47-S06` remains a single overmerged macro card;
- validation errors increase.

