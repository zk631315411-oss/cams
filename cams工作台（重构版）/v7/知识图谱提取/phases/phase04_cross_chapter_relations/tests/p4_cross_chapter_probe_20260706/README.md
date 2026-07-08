# P4 cross-chapter probe 20260706

## Purpose

This test probes Phase 04 under the current KG contract:

```text
P4 = cross-chapter core_point -> core_point relations
```

It does not create formal P4 outputs. It is used to check whether the candidate strategy and relation labels produce a small, reviewable set of useful cross-chapter relations.

## Scope

- Initial scope: chapters CH01-CH05.
- Inputs: P2A reviewed core_points and P2B unit edges.
- Output: draft cross-chapter relations for manual review.

## Proposed flow

```text
P4A_test: generate high-signal cross-chapter CP pair candidates.
P4B_test: ask LLM to accept/reject and classify candidates.
```

## Relation types

- `summarizes`: source CP summarizes target CP.
- `illustrates`: source CP is a case/example that directly illustrates target CP.
- `grounds`: source CP provides foundation/framework/definition for target CP.
- `contrasts`: source CP and target CP are explicitly useful as a comparison.

## Non-relations

Reject pairs that are only:

- same broad topic;
- same term or method;
- same risk family;
- weak embedding similarity;
- useful only for P5 term/method indexing.

## Expected outcome

A useful P4 test result should be sparse. It is acceptable to reject most candidates.
