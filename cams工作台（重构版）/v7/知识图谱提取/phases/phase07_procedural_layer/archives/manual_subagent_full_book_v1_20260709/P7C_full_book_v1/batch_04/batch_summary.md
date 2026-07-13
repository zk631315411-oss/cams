# P7C full_book_v1 batch_04 summary

## Scope

- Root: `phases/P7C/full_book_v1/batch_04`
- Sections processed: CH49-S05, CH49-S06, CH49-S07, CH49-S08, CH49-S09, CH49-S10
- Output shape: one `cards.raw.json` per section, strict JSON with `section_id`, `section_title`, `cards`, and `skip_reason`.

## Card Counts

| section_id | section_title | cards | notes |
|---|---|---:|---|
| CH49-S05 | Concluding an investigation and suspicious activity reporting > Case example: SAR for a family trust | 1 | Case narrative converted into a SAR preparation and submission execution flow. |
| CH49-S06 | Concluding an investigation and suspicious activity reporting > Key takeaways | 1 | Key-takeaway list converted into parallel SAR submission control standards. |
| CH49-S07 | Concluding an investigation and suspicious activity reporting > Maintaining an account after unusual activity | 2 | Split into post-SAR account disposition assessment and open-account management controls. |
| CH49-S08 | Concluding an investigation and suspicious activity reporting > Reasons and consequences for not filing a SAR | 1 | Risk-based SAR filing decision and documentation assessment. |
| CH49-S09 | Concluding an investigation and suspicious activity reporting > Follow-up action when no SAR is filed | 1 | Follow-up controls after non-filing decision. |
| CH49-S10 | Concluding an investigation and suspicious activity reporting > Defensive suspicious activity reports | 1 | Defensive SAR material modeled as a risk-indicator card. |

Total cards: 7

## Validation

- All `cards.raw.json` files parse as JSON.
- Each card has the P7C required fields.
- `card_nature` values are limited to `execution`, `assessment`, `risk_indicator`, and `control`.
- Each card has at least one `start` or `trigger` node.
- Flow edge endpoints resolve to node IDs inside the same card.
- All `DECIDES` edges include `condition`.
- All node, edge, and card `source_unit_ids` refer only to unit IDs present in the current section text.
- No bridge, cluster, scenario path, Mermaid, draw.io, or exam-answer material was generated.

## Needs Human Attention

- CH49-S05: several process-order edges are reconstructed from the case narrative order rather than explicit procedural wording.
- CH49-S06: the section is a key-takeaway list, so the card is a control-standard representation rather than a strict workflow.
- CH49-S07: the close/change branch in the account disposition card is inferred from the maintain-or-close framing; the source states the continue/maintain obligations more directly.
- CH49-S09: KYC review, CRA reperformance, file updates, ongoing monitoring, and recordkeeping may be parallel obligations; the card uses a practical follow-up sequence with `needs_review` notes.
- CH49-S10: defensive SAR content is mostly explanatory/risk-indicator material; screening-to-mitigation order is inferred and marked for review.
