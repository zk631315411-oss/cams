# P7D Validation And Routing Report

P7D validates and routes findings only. Review/fail items require human confirmation before rerun, prompt changes, card deletion, or formal downstream use.

## Summary

input_file_count: 9
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

## Status By Section

- CH47-S02: pass_with_review_findings=2
- CH47-S09: pass_with_review_findings=1
- CH47-S11: pass=1
- CH47-S15: pass=1, pass_with_review_findings=1
- CH49-S03: pass_with_review_findings=1
- CH49-S08: pass_with_review_findings=1
- CH49-S12: pass_with_review_findings=1
- CH49-S15: pass_with_review_findings=2

## Review Finding Types

- functional_dependency_used: 9
- object_marked_needs_review: 7
- too_many_review_status_nodes_or_edges: 1
- possible_overmerged_card: 1

## Human Routing Queue

- pass_with_review_findings | notice | review_result=pass | CH47-S02 | p7card_CH47-S02_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: functional_dependency_used - p7card_CH47-S02_001 uses 3 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S02 | p7card_CH47-S02_002 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: functional_dependency_used - p7card_CH47-S02_002 uses 3 functional_dependency node/edge evidence items
- pass_with_review_findings | required | review_result=fail | CH47-S09 | p7card_CH47-S09_001 | report_review_findings
  - reason: review finding requires human decision before downstream use
  - review: object_marked_needs_review - p7card_CH47-S09_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S09_001 uses 7 functional_dependency node/edge evidence items
  - review: too_many_review_status_nodes_or_edges - p7card_CH47-S09_001 has 7 node/edge review marks
- pass_with_review_findings | notice | review_result=pass | CH47-S15 | p7card_CH47-S15_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S15_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S15_001 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S03 | p7card_CH49-S03_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S03_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S03_001 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S08 | p7card_CH49-S08_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S08_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S08_001 uses 5 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S12 | p7card_CH49-S12_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S12_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S12_001 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S15 | p7card_CH49-S15_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S15_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S15_001 uses 1 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S15 | p7card_CH49-S15_002 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S15_002 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S15_002 uses 1 functional_dependency node/edge evidence items
