# P7C Granularity Probe v1 Results

Run: `outputs/run_ds_none_c6`

Model: `deepseek-v4-pro`

Thinking effort: `none`

Concurrency: `6`

## Batch Summary

| section | baseline cards | probe cards | validation errors | initial judgement |
|---|---:|---:|---:|---|
| CH47-S03 | 2 | 2 | 0 | stable |
| CH47-S04 | 1 | 1 | 0 | stable |
| CH47-S06 | 1 | 4 | 0 | improved granularity |
| CH47-S08 | 1 | 1 | 0 | stable |
| CH47-S13 | 1 | 3 | 0 | changed; plausible but needs review |
| CH47-S16 | 1 | 1 | 0 | structurally stable, P7D worsened |
| CH49-S10 | 1 | 1 | 0 | stable |
| CH49-S14 | 2 | 2 | 0 | structurally stable, P7D worsened |
| CH49-S16 | 1 | 1 | 0 | stable as evidence/judgement card |

## CH47-S06 Result

The probe fixed the main overmerge problem. The previous single macro card had 25 nodes and 26 edges. The probe produced four cards:

| card | title | P7D route |
|---|---|---|
| p7card_CH47-S06_001 | Level 1 Initial Review of Transaction Monitoring Alert | pass / none |
| p7card_CH47-S06_002 | Level 2 Investigation of Transaction Monitoring Alert | pass_with_review_findings / notice |
| p7card_CH47-S06_003 | Level 3 Complex Analysis for Highly Suspicious Alerts | pass_with_review_findings / notice |
| p7card_CH47-S06_004 | SAR Filing, Ongoing Monitoring, and Preventive Recommendations | pass_with_review_findings / notice |

This is materially better for evidence matching than the baseline macro card.

## Side Effects

The addendum is not safe to merge globally yet.

P7D on the probe output:

```text
card_or_file_result_count: 16
pass: 1
pass_with_review_findings: 15
fail: 0
validator_error: 0
review_required: 5
review_notice: 10
```

Compared with the baseline focus-section P7D, `CH47-S06` improved from required/fail to pass+notice cards. However, other sections became more conservative:

- `CH47-S13` split from one card into three cards. This may be semantically defensible, but one card lacks review notes for functional dependency.
- `CH47-S16` remained one card, but P7D required review due to increased functional-dependency/review marks.
- `CH49-S14` remained two cards, but both became P7D required because of many functional dependencies and review marks.
- `CH49-S16` remains evidence/judgement material, not an execution graph card.

## Conclusion

The granularity addendum proves that prompt-only adjustment can make DS produce finer `CH47-S06` cards without breaking schema validation or fragmenting obvious control cards such as `CH47-S04`.

It is not ready to merge into the production P7C prompt because it increases review burden in some branching/communication sections.

Recommended next step:

1. Keep this as an experimental prompt.
2. Tighten the addendum so it targets named multi-level review/investigation sections more narrowly.
3. Re-run the same regression set.
4. Only merge if `CH47-S06` stays fine-grained and `CH47-S13`, `CH47-S16`, and `CH49-S14` do not worsen.

