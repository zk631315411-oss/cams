# P7D Validation And Routing Report

P7D validates and routes findings only. Review/fail items require human confirmation before rerun, prompt changes, card deletion, or formal downstream use.

## Summary

input_file_count: 27
card_or_file_result_count: 36
pass: 2
pass_with_review_findings: 34
fail: 0
validator_error: 0
review_required: 6
review_notice: 28
review_result_none: 2
review_result_pass: 28
review_result_fail: 6

## Status By Section

- CH47-S01: pass_with_review_findings=1
- CH47-S02: pass_with_review_findings=2
- CH47-S03: pass_with_review_findings=2
- CH47-S04: pass_with_review_findings=1
- CH47-S05: pass=1
- CH47-S06: pass_with_review_findings=1
- CH47-S07: pass_with_review_findings=2
- CH47-S08: pass_with_review_findings=1
- CH47-S09: pass_with_review_findings=1
- CH47-S10: pass=1, pass_with_review_findings=1
- CH47-S11: pass_with_review_findings=1
- CH47-S12: pass_with_review_findings=1
- CH47-S13: pass_with_review_findings=2
- CH47-S14: pass_with_review_findings=1
- CH47-S15: pass_with_review_findings=3
- CH49-S05: pass_with_review_findings=1
- CH49-S06: pass_with_review_findings=1
- CH49-S07: pass_with_review_findings=2
- CH49-S08: pass_with_review_findings=1
- CH49-S09: pass_with_review_findings=1
- CH49-S10: pass_with_review_findings=1
- CH49-S11: pass_with_review_findings=2
- CH49-S12: pass_with_review_findings=1
- CH49-S13: pass_with_review_findings=1
- CH49-S14: pass_with_review_findings=2
- CH49-S15: pass_with_review_findings=1

## Review Finding Types

- object_marked_needs_review: 34
- functional_dependency_used: 33
- too_many_review_status_nodes_or_edges: 6
- weak_assessment_or_risk_card: 1

## Human Routing Queue

- pass_with_review_findings | notice | review_result=pass | CH47-S01 | p7card_CH47-S01_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S01_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S01_001 uses 1 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S02 | p7card_CH47-S02_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S02_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S02_001 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S02 | p7card_CH47-S02_002 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S02_002 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S02_002 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S03 | p7card_CH47-S03_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S03_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S03_001 uses 3 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S03 | p7card_CH47-S03_002 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S03_002 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S03_002 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | required | review_result=fail | CH47-S04 | p7card_CH47-S04_001 | report_review_findings
  - reason: review finding requires human decision before downstream use
  - review: object_marked_needs_review - p7card_CH47-S04_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S04_001 uses 7 functional_dependency node/edge evidence items
  - review: too_many_review_status_nodes_or_edges - p7card_CH47-S04_001 has 7 node/edge review marks
- pass_with_review_findings | notice | review_result=pass | CH47-S06 | p7card_CH47-S06_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S06_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S06_001 uses 1 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S07 | p7card_CH47-S07_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S07_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S07_001 uses 1 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S07 | p7card_CH47-S07_002 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S07_002 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S07_002 uses 1 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S08 | p7card_CH47-S08_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S08_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S08_001 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S09 | p7card_CH47-S09_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S09_001 card review_status is needs_review
  - review: weak_assessment_or_risk_card - p7card_CH47-S09_001 assessment card should include action, standard, and output nodes
  - review: functional_dependency_used - p7card_CH47-S09_001 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S10 | p7card_CH47-S10_002 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S10_002 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S10_002 uses 4 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S11 | p7card_CH47-S11_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S11_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S11_001 uses 4 functional_dependency node/edge evidence items
- pass_with_review_findings | required | review_result=fail | CH47-S12 | p7card_CH47-S12_001 | report_review_findings
  - reason: review finding requires human decision before downstream use
  - review: object_marked_needs_review - p7card_CH47-S12_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S12_001 uses 6 functional_dependency node/edge evidence items
  - review: too_many_review_status_nodes_or_edges - p7card_CH47-S12_001 has 6 node/edge review marks
- pass_with_review_findings | notice | review_result=pass | CH47-S13 | p7card_CH47-S13_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S13_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S13_001 uses 5 functional_dependency node/edge evidence items
- pass_with_review_findings | required | review_result=fail | CH47-S13 | p7card_CH47-S13_002 | report_review_findings
  - reason: review finding requires human decision before downstream use
  - review: object_marked_needs_review - p7card_CH47-S13_002 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S13_002 uses 7 functional_dependency node/edge evidence items
  - review: too_many_review_status_nodes_or_edges - p7card_CH47-S13_002 has 7 node/edge review marks
- pass_with_review_findings | required | review_result=fail | CH47-S14 | p7card_CH47-S14_001 | report_review_findings
  - reason: review finding requires human decision before downstream use
  - review: object_marked_needs_review - p7card_CH47-S14_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S14_001 uses 6 functional_dependency node/edge evidence items
  - review: too_many_review_status_nodes_or_edges - p7card_CH47-S14_001 has 6 node/edge review marks
- pass_with_review_findings | notice | review_result=pass | CH47-S15 | p7card_CH47-S15_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S15_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S15_001 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S15 | p7card_CH47-S15_002 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S15_002 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S15_002 uses 4 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH47-S15 | p7card_CH47-S15_003 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH47-S15_003 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH47-S15_003 uses 3 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S05 | p7card_CH49-S05_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S05_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S05_001 uses 5 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S06 | p7card_CH49-S06_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S06_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S06_001 uses 3 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S07 | p7card_CH49-S07_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S07_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S07_001 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S07 | p7card_CH49-S07_002 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S07_002 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S07_002 uses 3 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S08 | p7card_CH49-S08_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S08_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S08_001 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | required | review_result=fail | CH49-S09 | p7card_CH49-S09_001 | report_review_findings
  - reason: review finding requires human decision before downstream use
  - review: object_marked_needs_review - p7card_CH49-S09_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S09_001 uses 6 functional_dependency node/edge evidence items
  - review: too_many_review_status_nodes_or_edges - p7card_CH49-S09_001 has 6 node/edge review marks
- pass_with_review_findings | required | review_result=fail | CH49-S10 | p7card_CH49-S10_001 | report_review_findings
  - reason: review finding requires human decision before downstream use
  - review: object_marked_needs_review - p7card_CH49-S10_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S10_001 uses 7 functional_dependency node/edge evidence items
  - review: too_many_review_status_nodes_or_edges - p7card_CH49-S10_001 has 7 node/edge review marks
- pass_with_review_findings | notice | review_result=pass | CH49-S11 | p7card_CH49-S11_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S11_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S11_001 uses 5 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S11 | p7card_CH49-S11_002 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S11_002 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S11_002 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S12 | p7card_CH49-S12_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S12_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S12_001 uses 3 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S13 | p7card_CH49-S13_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S13_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S13_001 uses 4 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S14 | p7card_CH49-S14_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S14_001 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S14_001 uses 3 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S14 | p7card_CH49-S14_002 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S14_002 card review_status is needs_review
  - review: functional_dependency_used - p7card_CH49-S14_002 uses 2 functional_dependency node/edge evidence items
- pass_with_review_findings | notice | review_result=pass | CH49-S15 | p7card_CH49-S15_001 | report_review_findings
  - reason: review findings are visible notices; structure may continue in experiments after human awareness
  - review: object_marked_needs_review - p7card_CH49-S15_001 card review_status is needs_review
