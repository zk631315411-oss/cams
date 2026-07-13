# B线 intent_v1 后置参考对照

参考答案只用于跑后对照，未进入盲判 prompt。

| 题号 | baseline AI | intent_v1 AI | final参考 | intent冲突 | baseline冲突 | 中英冲突 | 意图 | 标准 |
|---|---|---|---|---|---|---|---|---|
| v7_q_000001 | C | C | C | False | False | False | best_action | best_remediation |
| v7_q_000003 | A | A | A | False | False | False | authority | scope_authority |
| v7_q_000006 | A | B | B | False | True | False | red_flag | red_flag_fit |
| v7_q_000009 | C | D | C | True | False | False | best_action | best_remediation |
| v7_q_000012 | A | B | A | True | False | True | control_effectiveness | risk_formula |
| v7_q_000016 | C | C | C | False | False | False | purpose | concept_definition |
| v7_q_000026 | D | B | B | False | True | False | first_step | sequence_priority |
| v7_q_000030 | C | C | C | False | False | False | procedure_sequence | sequence_priority |
| v7_q_000039 | B | B | D | True | True | True | authority | scope_authority |
| v7_q_000045 | B | B | B | False | False | False | purpose | evidence_specificity |
