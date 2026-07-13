# P7C Full Book v1 Semantic Approval Report

## Scope

This report reviews semantic quality for the currently produced `P7C/full_book_v1` cards.

Current coverage:

```text
Produced section files: 27 / 32
Produced cards: 36
Missing batch_03 sections: CH47-S16, CH49-S01, CH49-S02, CH49-S03, CH49-S04
```

P7D structural status:

```text
pass: 2
pass_with_review_findings: 34
fail: 0
validator_error: 0
review_result_none: 2
review_result_pass: 28
review_result_fail: 6
```

## Approval Scale

```text
approve                 May proceed downstream.
approve_with_review     May proceed, but downstream must respect review_notes and functional_dependency markers.
revise_before_downstream Do not use in P7E/P7F until rewritten or simplified.
hold_or_rerun            Hold; rerun section-level P7C after prompt or extraction guidance is clarified.
```

## Overall Judgment

The existing outputs are structurally usable but semantically uneven.

The strongest cards are sections with explicit operational sequence, decision points, or reporting duties. The weakest cards are list-like or principle-like sections where the extractor converted parallel controls into pseudo-sequential flow.

The main semantic risk is not cross-section contamination. The main risk is over-proceduralization: list items, control principles, examples, or quality standards are sometimes represented as process steps connected with `PRECEDES`.

## Approved For Downstream

These cards can enter P7E/P7F experiments as procedural cards.

| section_id | card_id | judgment | reason |
|---|---|---|---|
| CH47-S01 | p7card_CH47-S01_001 | approve_with_review | Alert generation and review is a real local process. Manual alert handling is inferred but marked. |
| CH47-S02 | p7card_CH47-S02_001 | approve_with_review | Transaction monitoring after onboarding is a valid assessment flow. Negative no-SAR branch is inferred and should remain review-visible. |
| CH47-S02 | p7card_CH47-S02_002 | approve_with_review | Payment screening before completion is a valid process. No-match branch is inferred but acceptable as a review-visible complement. |
| CH47-S05 | p7card_CH47-S05_001 | approve | Scenario screening is clean and structurally simple. |
| CH47-S06 | p7card_CH47-S06_001 | approve_with_review | Alert review through Level 1/2/3 and SAR decision is a strong procedural card. The non-Level-3 path is inferred but marked. |
| CH47-S08 | p7card_CH47-S08_001 | approve_with_review | Pre-escalation investigation review is a plausible local workflow. |
| CH47-S09 | p7card_CH47-S09_001 | approve_with_review | Information gathering and next-step determination is useful, but assessment-card shape should be checked if downstream needs strict action-standard-output form. |
| CH47-S10 | p7card_CH47-S10_001 | approve | Reasonableness assessment has clear standards and output. |
| CH47-S11 | p7card_CH47-S11_001 | approve_with_review | Customer outreach can be used as a workflow, but negative/no-outreach branch should remain review-visible. |
| CH47-S13 | p7card_CH47-S13_001 | approve_with_review | Internal employee investigation planning is useful. HR/IT/evidence sequencing is partly inferred. |
| CH47-S15 | p7card_CH47-S15_001 | approve_with_review | Escalation for SAR decision is a real flow. No-report branch is inferred. |
| CH47-S15 | p7card_CH47-S15_002 | approve_with_review | Controlled terminology is a valid control card, not a strict workflow. |
| CH47-S15 | p7card_CH47-S15_003 | approve_with_review | Audit trail creation is a valid control workflow, though documentation actions are partially parallel. |
| CH49-S07 | p7card_CH49-S07_001 | approve_with_review | Maintain/close account decision after SAR filing is useful as a decision card. |
| CH49-S07 | p7card_CH49-S07_002 | approve_with_review | Managing an account that remains open is a useful control card. |
| CH49-S08 | p7card_CH49-S08_001 | approve_with_review | Risk-based SAR filing decision is downstream-useful with review notes. |
| CH49-S11 | p7card_CH49-S11_001 | approve_with_review | Formal law-enforcement request response is operationally useful. |
| CH49-S11 | p7card_CH49-S11_002 | approve_with_review | Communication documentation is a valid control card. |
| CH49-S12 | p7card_CH49-S12_001 | approve_with_review | Law-enforcement request assessment and coordination is useful. |
| CH49-S14 | p7card_CH49-S14_001 | approve_with_review | Potential new-customer refusal/exit is a plausible decision flow. |
| CH49-S14 | p7card_CH49-S14_002 | approve_with_review | Established-customer exit flow is useful with review-visible legal/policy dependencies. |

## Revise Before Downstream

These cards should not enter P7E/P7F as-is.

| section_id | card_id | judgment | issue | recommended action |
|---|---|---|---|---|
| CH47-S03 | p7card_CH47-S03_001 | revise_before_downstream | Parallel technology options are connected from a common start with `PRECEDES`; this can be misread as a process. | Recast as a control card with one action such as `select/apply monitoring technology` using parallel standards/options, or keep as non-procedural control evidence. |
| CH47-S03 | p7card_CH47-S03_002 | revise_before_downstream | AI implementation controls are useful, but `test -> effective FCRM` is too compressed. | Keep as a small control card, but represent explainability/transparency/context as standards, not implied results. |
| CH47-S04 | p7card_CH47-S04_001 | hold_or_rerun | Tuning components are parallel controls, but the card uses many `PRECEDES` edges and triggered a required review. | Rerun section-level P7C with instruction: tuning components are parallel; use one tuning action with standards/options, plus a separate special-assessment trigger if needed. |
| CH47-S10 | p7card_CH47-S10_002 | revise_before_downstream | AML program design standards and monitoring/reporting systems are over-merged. | Split or simplify into a control-standard card; avoid chronology unless the section states it. |
| CH47-S12 | p7card_CH47-S12_001 | revise_before_downstream | Meeting guidance is useful, but too many inferred `PRECEDES` edges produce a faux sequence. | Rewrite as execution-lite: prepare/engage/collect/document, with customer wariness and communication techniques as standards. |
| CH47-S13 | p7card_CH47-S13_002 | revise_before_downstream | Witness interview card is conceptually useful but too many edges are functional dependencies. | Simplify to `prepare interview plan -> conduct interview -> produce witness statement`, with legal/policy/HR/third-party items as standards or conditional controls. |
| CH47-S14 | p7card_CH47-S14_001 | hold_or_rerun | The card over-merges analysis methods, relationship mapping, cash-flow analysis, visualization, new-network consultation, and final decision. | Split into method cards or recast as an assessment card with parallel methods. Do not imply strict sequence among methods. |
| CH49-S05 | p7card_CH49-S05_001 | revise_before_downstream | Case example converted to process may be useful as illustration, but not reliable as general procedural knowledge. | Mark as example-derived or exclude from formal P7E until separately reviewed. |
| CH49-S06 | p7card_CH49-S06_001 | revise_before_downstream | Key takeaways are quality standards, not a local process. | Keep as control/quality checklist evidence, not flow. |
| CH49-S09 | p7card_CH49-S09_001 | hold_or_rerun | No-SAR follow-up card over-merges documentation, KYC/CRA, client file update, monitoring, and recordkeeping into one sequence. | Split into smaller cards or model as parallel post-non-filing obligations with limited sequence. |
| CH49-S10 | p7card_CH49-S10_001 | hold_or_rerun | Defensive SAR material is explanatory/risk-indicator material converted into a multi-step process. | Recast as risk_indicator card with standards only; keep mitigation as a separate control if explicitly supported. |
| CH49-S13 | p7card_CH49-S13_001 | revise_before_downstream | SAR data use by law enforcement is partly external actor/intelligence use, not an internal CAMS execution flow. | Use only if P7 scope includes law-enforcement-side use cases; otherwise hold as context evidence. |
| CH49-S15 | p7card_CH49-S15_001 | revise_before_downstream | De-risking mitigation measures are parallel controls, but many are connected from trigger with `PRECEDES`. | Recast as control card with parallel mitigation options; avoid chronological interpretation. |

## Missing Or Incomplete

Batch 03 is incomplete. Goodall produced only `CH47-S15`; these section outputs are missing:

```text
CH47-S16
CH49-S01
CH49-S02
CH49-S03
CH49-S04
```

Do not continue batch-level extraction. Continue section by section, writing each `cards.raw.json` immediately after it is complete.

## Prompt Lessons

Before rerunning weak sections, add or enforce these extraction rules:

```text
1. If the source is a list of controls, do not connect list items with PRECEDES.
2. For control/risk_indicator cards, prefer one action using multiple standards/options unless the source states sequence.
3. Negative branches may be created only when they are necessary to close a stated decision and must be marked functional_dependency.
4. Case examples should be marked example-derived and should not become general procedural knowledge without review.
5. Large cards with many functional_dependency edges should be split or downgraded to a checklist/control card.
```

## Next Step

Recommended next step:

```text
Pause full-book expansion.
Patch P7C guidance for list/control materials.
Rerun only the revise/hold sections section-by-section.
Then run P7D again and approve the rerun outputs before P7E.
```
