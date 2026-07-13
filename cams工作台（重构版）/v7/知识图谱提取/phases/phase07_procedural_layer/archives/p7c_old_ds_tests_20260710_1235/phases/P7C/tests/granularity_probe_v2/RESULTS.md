# P7C Granularity Probe v2 Results

Run: `outputs/run_ds_none_c6`

Model: `deepseek-v4-pro`

Thinking effort: `none`

Concurrency: `6`

## Batch Summary

| section | baseline cards | v1 cards | v2 cards | validation errors | initial judgement |
|---|---:|---:|---:|---:|---|
| CH47-S03 | 2 | 2 | 2 | 0 | stable |
| CH47-S04 | 1 | 1 | 1 | 0 | stable |
| CH47-S06 | 1 | 4 | 4 | 0 | improved granularity retained |
| CH47-S08 | 1 | 1 | 1 | 0 | stable |
| CH47-S13 | 1 | 3 | 1 | 0 | count restored, P7D worse |
| CH47-S16 | 1 | 1 | 1 | 0 | improved vs v1 P7D route |
| CH49-S10 | 1 | 1 | 1 | 0 | stable |
| CH49-S14 | 2 | 2 | 2 | 0 | improved vs v1 P7D route |
| CH49-S16 | 1 | 1 | 1 | 0 | stable as judgement/evidence material |

## CH47-S06 Result

v2 keeps the desired CH47-S06 improvement without manually specifying split targets in the prompt. The model split the section into four cards because the source explicitly contains named review levels/stages:

| card | title | P7D route |
|---|---|---|
| p7card_CH47-S06_001 | Level 1 Alert Validity Examination | pass_with_review_findings / notice |
| p7card_CH47-S06_002 | Level 2 Detailed Investigation and Suspicious Activity Determination | pass_with_review_findings / notice |
| p7card_CH47-S06_003 | Level 3 Comprehensive Assessment and SAR Filing | pass_with_review_findings / notice |
| p7card_CH47-S06_004 | Post-SAR Ongoing Monitoring and Preventive Measures | pass_with_review_findings / required |

The fourth card is marked required only because P7D treats a 3-node card as possible overfragmentation. Semantically, it may still be useful as a post-SAR control card.

## P7D Summary

```text
card_or_file_result_count: 14
pass: 0
pass_with_review_findings: 14
fail: 0
validator_error: 0
review_required: 2
review_notice: 12
review_result_pass: 12
review_result_fail: 2
```

v2 improves over v1 by reducing required review burden from 5 cards to 2 cards while preserving the CH47-S06 split.

## Side Effects

Remaining concerns:

- `CH47-S13` stayed as one card, but P7D marks it required because it contains many `functional_dependency` items and review marks.
- `CH47-S06_004` is small and P7D flags it as possible overfragmentation. This may be a P7D rule issue rather than a P7C prompt issue.

Improved compared with v1:

- `CH49-S14` no longer gets required review solely due to the granularity prompt.
- `CH47-S16` is back to notice/pass rather than required/fail.
- `CH47-S13` no longer fragments into three cards.

## Conclusion

v2 is a better candidate than v1. It demonstrates that a narrow named-level addendum can make DS produce finer CH47-S06 cards without the broad side effects seen in v1.

Do not merge yet without one more review decision:

1. Decide whether `CH47-S06_004` should be accepted as a small post-SAR control card or folded into `CH47-S06_003`.
2. Decide whether the `CH47-S13` required result is acceptable as a separate P7D issue, unrelated to named-level granularity.

If both are acceptable, v2 can be considered for production prompt merge.

## Random 9-Section Probe

To avoid overfitting to the hand-picked regression set, a second probe sampled 9 additional sections with fixed seed `20260710`, excluding the original regression sections.

Sample:

```text
CH49-S12,CH49-S13,CH47-S09,CH49-S08,CH47-S15,CH49-S03,CH47-S11,CH49-S15,CH47-S02
```

Run: `outputs/random9_seed20260710_ds_none_c6`

P7D report: `outputs/random9_seed20260710_p7d_reports/p7d_validation_report.md`

### Random Probe Batch Summary

| section | cards | validation errors | P7D result summary |
|---|---:|---:|---|
| CH47-S02 | 2 | 0 | 2 notice/pass |
| CH47-S09 | 1 | 0 | 1 required/fail |
| CH47-S11 | 1 | 0 | 1 pass/none |
| CH47-S15 | 2 | 0 | 1 pass/none, 1 notice/pass |
| CH49-S03 | 1 | 0 | 1 notice/pass |
| CH49-S08 | 1 | 0 | 1 notice/pass |
| CH49-S12 | 1 | 0 | 1 notice/pass |
| CH49-S13 | 0 | 0 | skipped |
| CH49-S15 | 2 | 0 | 2 notice/pass |

P7D summary:

```text
card_or_file_result_count: 11
pass: 2
pass_with_review_findings: 9
fail: 0
validator_error: 0
review_required: 1
review_notice: 8
review_result_none: 2
review_result_pass: 8
review_result_fail: 1
```

### Random Probe Interpretation

The random probe does not show obvious broad side effects from the named-level addendum. There were no validation errors, no schema failures, and only one required/fail route.

The one required/fail route is `CH47-S09`, caused by many functional-dependency/review marks in an information-gathering card. This appears to be a general P7D evidence-strength issue, not a named-level granularity side effect.

One concern remains: `CH49-S13` was skipped in this random probe, whereas earlier runs sometimes extracted a law-enforcement SAR-use card. This points to extraction instability around sections that describe third-party use of SARs rather than an institution's own process. It should be tracked separately from the named-level granularity addendum.

### Updated Judgement

After the random probe, v2 remains the best candidate so far, but it is still not proven for production merge. Evidence now supports:

- v2 can split named-level CH47-S06 without manual split targets;
- v2 is less harmful than v1;
- v2 did not obviously damage 9 additional random sections;
- remaining instability exists in non-execution, third-party-use sections such as CH49-S13.

Recommended next test before merge: run a larger 32-section sample and compare baseline vs v2 using card count, validation errors, P7D required count, and skipped-section differences.
