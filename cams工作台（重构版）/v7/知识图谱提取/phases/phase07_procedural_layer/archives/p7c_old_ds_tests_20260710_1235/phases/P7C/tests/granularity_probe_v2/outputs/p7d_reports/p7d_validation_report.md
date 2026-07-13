# P7D Validation And Routing Report

P7D validates and routes findings only. Review/fail items require human confirmation before rerun, prompt changes, card deletion, or formal downstream use.

## Summary

input_file_count: 9
card_or_file_result_count: 14
pass: 0
pass_with_review_findings: 14
fail: 0
validator_error: 0
review_required: 2
review_notice: 12
review_result_none: 0
review_result_pass: 12
review_result_fail: 2

## Status By Section

- CH47-S03: pass_with_review_findings=2
- CH47-S04: pass_with_review_findings=1
- CH47-S06: pass_with_review_findings=4
- CH47-S08: pass_with_review_findings=1
- CH47-S13: pass_with_review_findings=1
- CH47-S16: pass_with_review_findings=1
- CH49-S10: pass_with_review_findings=1
- CH49-S14: pass_with_review_findings=2
- CH49-S16: pass_with_review_findings=1

## Review Finding Types

- functional_dependency_used: 13
- object_marked_needs_review: 12
- possible_overfragmented_cards: 1
- too_many_review_status_nodes_or_edges: 1
- possible_overmerged_card: 1

## Human Routing Queue

- pass_with_review_findings | notice | review_result=pass | CH47-S03 | p7card_CH47-S03_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S03_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S03_001 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S03 | p7card_CH47-S03_002 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S03_002 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S03_002 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S04 | p7card_CH47-S04_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S04_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S04_001 uses 4 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S06 | p7card_CH47-S06_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: functional_dependency_used - p7card_CH47-S06_001 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S06 | p7card_CH47-S06_002 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S06_002 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S06_002 uses 5 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S06 | p7card_CH47-S06_003 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S06_003 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S06_003 uses 5 functional_dependency node/edge evidence items
- pass_with_review_findings | required | review_result=fail | CH47-S06 | p7card_CH47-S06_004 | report_review_findings
  - reason: review finding requires human decision before downstream use
  - review: possible_overfragmented_cards - p7card_CH47-S06_004 is very small: 3 nodes
- pass_with_review_findings | notice | review_result=pass | CH47-S08 | p7card_CH47-S08_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S08_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S08_001 uses 5 functional_dependency node/edge evidence items
- pass_with_review_findings | required | review_result=fail | CH47-S13 | p7card_CH47-S13_001 | report_review_findings
  - reason: review finding requires human decision before downstream use
  - review: object_marked_needs_review - p7card_CH47-S13_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S13_001 uses 13 functional_dependency node/edge evidence items
  - review: too_many_review_status_nodes_or_edges - p7card_CH47-S13_001 has 13 node/edge review marks
- pass_with_review_findings | notice | review_result=pass | CH47-S16 | p7card_CH47-S16_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S16_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S16_001 uses 8 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S10 | p7card_CH49-S10_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S10_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S10_001 uses 3 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S14 | p7card_CH49-S14_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S14_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S14_001 uses 1 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S14 | p7card_CH49-S14_002 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S14_002 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S14_002 uses 4 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S16 | p7card_CH49-S16_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S16_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S16_001 uses 3 functional_dependency node/edge evidence items
