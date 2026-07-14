# P7D Human Decisions - p7c_v5_focus_sections

Date: 2026-07-10

## Decisions

| section | card | P7D result | human decision | execution route |
|---|---|---|---|---|
| CH47-S06 | p7card_CH47-S06_001 | fail / required | repair_overmerged_card | api_repair_split_proposal |
| CH49-S16 | p7card_CH49-S16_001 | fail / required | downgrade_to_evidence | evidence_only |

## CH47-S06 Handling

The existing card is semantically useful but overmerged. It should not enter the formal execution graph as-is.

The repair step must not receive manually preselected split-card titles. Instead, an external API repair pass should read the section text, the overmerged card, P7D findings, and the P7A card contract, then derive replacement card boundaries from the section itself. The API must first output proposed boundaries with evidence spans, then output replacement `p7_card` objects.

After the replacement cards pass P7D, the original card should be treated as superseded rather than deleted.

## CH49-S16 Handling

The card is useful evidence for financial inclusion and control side-effect judgement, but it is not an executable process. It should be routed to evidence-only / judgement-only use and excluded from formal execution graph generation.
