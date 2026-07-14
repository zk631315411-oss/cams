# Experiment p7c_coverage_decomposition_v2_20260713

- Objective: Reduce non-KG P7C proposition omissions without KG over-classification or unsupported procedural edges
- Hypothesis: A hard operational-relation gate in the proposition Audit will preserve the recall benefit of decomposition while excluding ordinary KG mechanisms and control effects
- Changed variable: coverage_audit_p7_eligibility_gate_v2
- Execution status: ran
- Verdict: reject
- Issue count: 4

## Evaluation

The v2 Audit gate removed the v1 KG over-classification and detected all four target gap classes, but the unchanged Patch builder converted only one target relation into an accepted answer-eligible edge. Patch construction quality violated mandatory gates.

## Next Action

Freeze the v2 Audit outputs and run a patch-only experiment. Change only the Patch prompt to require qualifier-preserving target labels, exact source-process evidence, new process nodes when existing nodes do not match, no active/passive duplicate exits, and unresolved output when the claim invents a subject.

## Run Return Codes

```json
{
  "development": {
    "baseline": 0,
    "variant": 0
  }
}
```
