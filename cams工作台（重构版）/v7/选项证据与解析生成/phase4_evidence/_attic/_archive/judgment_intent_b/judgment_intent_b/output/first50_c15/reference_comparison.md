# B线 intent_v1 后置参考对照

参考答案只用于跑后对照，未进入盲判 prompt。

| 题号 | baseline AI | intent_v1 AI | final参考 | intent冲突 | baseline冲突 | 中英冲突 | 意图 | 标准 |
|---|---|---|---|---|---|---|---|---|
| v7_q_000001 | C | C | C | False | False | False | best_action | best_remediation |
| v7_q_000002 | C | C | C | False | False | False | best_action | evidence_specificity |
| v7_q_000003 | A | A | A | False | False | False | best_action | scope_authority |
| v7_q_000004 | D | C | D | True | False | True | authority | scope_authority |
| v7_q_000005 | A | A | A | False | False | False | red_flag | red_flag_fit |
| v7_q_000006 | A | B | B | False | True | False | red_flag | red_flag_fit |
| v7_q_000007 | D | D | D | False | False | False | best_action | evidence_specificity |
| v7_q_000008 | B | B | B | False | False | False | best_action | best_remediation |
| v7_q_000009 | C | D | C | True | False | False | best_action | best_remediation |
| v7_q_000010 | A | A | A | False | False | False | concept_definition | concept_definition |
| v7_q_000011 | C | C | C | False | False | False | definition | concept_definition |
| v7_q_000012 | A | B | A | True | False | True | control_effectiveness | control_effect |
| v7_q_000013 | D | D | D | False | False | False | risk_effect | evidence_specificity |
| v7_q_000014 | C | C | C | False | False | True | red_flag | red_flag_fit |
| v7_q_000015 | A | A | A | False | False | False | definition | concept_definition |
| v7_q_000016 | C | C | C | False | False | False | purpose | concept_definition |
| v7_q_000017 | B | B | B | False | False | False | best_action | procedure_sequence |
| v7_q_000018 | D | D | D | False | False | False | purpose | concept_definition |
| v7_q_000019 | D | D | D | False | False | False | red_flag | red_flag_fit |
| v7_q_000020 | D | D | D | False | False | False | definition | concept_definition |
| v7_q_000021 | A | A | A | False | False | False | definition | concept_definition |
| v7_q_000022 | D | D | D | False | False | False | best_action | evidence_specificity |
| v7_q_000023 | B | B | B | False | False | False | definition | concept_definition |
| v7_q_000024 | B | B | B | False | False | False | procedure_sequence | evidence_specificity |
| v7_q_000025 | B | B | B | False | False | False | best_action | evidence_specificity |
| v7_q_000026 | D | B | B | False | True | False | first_step | sequence_priority |
| v7_q_000027 | A | A | A | False | False | False | other | evidence_specificity |
| v7_q_000028 | C | C | C | False | False | False | authority | scope_authority |
| v7_q_000029 | C | C | C | False | False | False | concept_definition | concept_definition |
| v7_q_000030 | C | C | C | False | False | False | procedure_sequence | sequence_priority |
| v7_q_000031 | D | D | D | False | False | False | definition | concept_definition |
| v7_q_000032 | B | B | B | False | False | False | best_action | best_remediation |
| v7_q_000033 | B | B | B | False | False | False | purpose | concept_definition |
| v7_q_000034 | C | C | C | False | False | False | definition | concept_definition |
| v7_q_000035 | B | B | B | False | False | False | definition | concept_definition |
| v7_q_000036 | A | C | A | True | False | False | red_flag | red_flag_fit |
| v7_q_000037 | D | D | D | False | False | False | definition | concept_definition |
| v7_q_000038 | B | B | B | False | False | False | authority | scope_authority |
| v7_q_000039 | B | B | D | True | True | True | authority | scope_authority |
| v7_q_000040 | D | D | D | False | False | False | authority | evidence_specificity |
| v7_q_000041 | D | D | D | False | False | False | definition | concept_definition |
| v7_q_000042 | A | A | A | False | False | False | purpose | concept_definition |
| v7_q_000043 | D | D | D | False | False | False | authority | scope_authority |
| v7_q_000044 | A | A | A | False | False | False | best_action | best_remediation |
| v7_q_000045 | B | B | B | False | False | False | purpose | concept_definition |
| v7_q_000046 | B | B | B | False | False | False | authority | scope_authority |
| v7_q_000047 | B | B | B | False | False | False | definition | concept_definition |
| v7_q_000048 | A | A | A | False | False | False | red_flag | red_flag_fit |
| v7_q_000049 | D | D | D | False | False | False | best_action | evidence_specificity |
| v7_q_000050 | D | D | D | False | False | False | purpose | concept_definition |
