# P7C full_book_v1 batch_01 summary

## Scope

- Worker scope: CH47-S01 through CH47-S07 only.
- Input source: `phases/P7B/section_packages/<section_id>`.
- Output root: `phases/P7C/full_book_v1/batch_01`.
- Extraction contract: P7C v1 section-local `p7_card` objects only; no bridge edges, clusters, scenario paths, Mermaid, draw.io, or exam explanations.

## Card counts

| section_id | section_title | cards | notes |
| --- | --- | ---: | --- |
| CH47-S01 | Transaction monitoring > Transaction monitoring controls | 1 | Main alert generation and review flow. Manual alert routing needs review because downstream handling is inferred. |
| CH47-S02 | Transaction monitoring > Transaction monitoring versus payment screening | 2 | Split post-onboarding transaction monitoring assessment from pre-completion payment screening. Negative/no-match branches are inferred. |
| CH47-S03 | Transaction monitoring > Technology solutions for transaction monitoring | 2 | Split intelligent monitoring solution controls from AI implementation risk controls. Parallel solution patterns are not chronological. |
| CH47-S04 | Transaction monitoring > Transaction monitoring system tuning | 1 | Tuning components are parallel controls; ordering is reconstructed only as functional dependency. |
| CH47-S05 | Transaction monitoring > Typical scenarios that would generate an alert | 1 | Risk-indicator card; red flags modeled as parallel standards used by screening. |
| CH47-S06 | Transaction monitoring > Procedures for alerts review | 1 | Main multi-level alert review workflow. The non-Level-3 path from Level 2 to documentation is inferred. |
| CH47-S07 | Transaction monitoring > Other sources of investigation | 2 | Split investigation-source assessment from sensitive-source handling controls. Source lists are parallel standards, not a timeline. |

Total cards: 10.

## Manual attention points

- CH47-S01: confirm whether manually raised alerts should always enter the same alert-review process or be modeled as a separate intake path.
- CH47-S02: confirm whether inferred negative/no-match outputs are acceptable in P7C cards when the section only states the positive mandatory action.
- CH47-S03 and CH47-S04: several edges intentionally use `functional_dependency` because the source presents components and tool patterns rather than ordered procedures.
- CH47-S06: confirm whether the Level 2 non-escalation resolution should end at documentation/SAR decision or should include a separate close/no-SAR output.
- CH47-S07: investigation sources are list-like; the first card is an assessment card for lead recognition rather than an operational workflow.
