# P7C full_book_v1 batch_02 summary

## Scope

- Batch: batch_02
- Sections: CH47-S08 through CH47-S14
- Output root: `phases/P7C/full_book_v1/batch_02`
- Extraction standard: P7C Section Flow Card Extraction Prompt v1, procedural schema v2

## Results

| Section | Title | Cards | Notes |
|---|---|---:|---|
| CH47-S08 | Transaction monitoring > Steps applied to an investigation | 1 | Pre-escalation investigation review modeled as an execution card. |
| CH47-S09 | Transaction monitoring > Information gathering | 1 | Internal/external sources, RFI, holistic review, and documentation modeled as one assessment card. |
| CH47-S10 | Transaction monitoring > How much research is reasonably enough? | 2 | One assessment card for reasonableness; one control card for AML program controls. |
| CH47-S11 | Transaction monitoring > Communication channels and tipping off | 1 | Customer outreach and anti-tipping-off communication controls modeled as one control card. |
| CH47-S12 | Transaction monitoring > Communicating with customers | 1 | Customer meeting process, uncooperative behavior indicator, and documentation modeled as one execution card. |
| CH47-S13 | Transaction monitoring > Investigating someone inside the organization | 2 | Internal investigation planning and witness interviews separated into two cards. |
| CH47-S14 | Transaction monitoring > Analysis of information | 1 | Relationship mapping, fund-flow analysis, and AFC consultation modeled as one assessment card. |

Total cards: 9

## Manual Attention

- CH47-S09: RFI is treated as part of the same information-gathering card; reviewers may choose to split it if later stages need a standalone RFI process card.
- CH47-S10: The control card combines program-level reasonable design requirements with detect/monitor/report systems; downstream reviewers may prefer a narrower control card.
- CH47-S11: The no-outreach branch is inferred from the source's "if both conditions are met" wording and is marked `needs_review`.
- CH47-S12: Meeting conduct is reconstructed from techniques and final documentation requirements, so several edges are functional dependencies rather than explicit sequence.
- CH47-S13: Internal investigation planning and witness interview ordering is reconstructed from requirement statements; both cards are marked `needs_review`.
- CH47-S14: Relationship mapping and cash/fund flow analysis are parallel techniques inside one card, not strict chronological steps.

## Validation

- All `cards.raw.json` files parse as strict JSON.
- Top-level keys are `section_id`, `section_title`, `cards`, and `skip_reason`.
- `card_nature`, node types, edge types, and evidence strengths use allowed enumerations.
- Every card has at least one `start` or `trigger` node.
- Every `DECIDES` edge has a `condition`.
- Every edge endpoint resolves to a node in the same card.
- Every evidence `unit_id` belongs to the corresponding current section package.
- No bridge, cluster, scenario path, Mermaid, draw.io, or candidate explanation outputs were generated.
