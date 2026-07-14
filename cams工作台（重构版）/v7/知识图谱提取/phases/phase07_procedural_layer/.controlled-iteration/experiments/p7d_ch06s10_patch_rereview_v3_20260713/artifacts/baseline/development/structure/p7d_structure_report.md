# P7D Structure Validation Report

This report covers deterministic schema, ID, reference, evidence-scope, and graph-shape checks only. It does not confirm edge semantics.

input_file_count: 1
result_count: 2
pass: 1
fail: 1
validator_error: 0

## Error Types

- missing_entry_process_exit_path: 1

## Failures

- CH06-S10 | p7card_CH06-S10_001
  - missing_entry_process_exit_path: p7card_CH06-S10_001 has no directed entry -> process -> exit path
