# Experiment p7c_coverage_decomposition_v1_20260713

- Objective: Reduce non-KG P7C proposition omissions without increasing unsupported procedural edges
- Hypothesis: Separating proposition-level coverage audit from additive graph construction will detect and repair missing or partially covered P7C claims more reliably than the v23 one-call Coverage step
- Changed variable: coverage_workflow_one_call_to_two_stage_audit_then_patch
- Execution status: failed
- Verdict: reject
- Issue count: 4

## Evaluation

The two-stage workflow exposed proposition-level gaps, but Audit over-classified KG content, missed two target structures, and produced two Patch contract failures. Mandatory regression gates did not pass.

## Next Action

Create a new experiment that changes only the Audit eligibility gate: require an AML/CFT operational action or judgment linked to an input, condition, standard, or independent result; exclude general control effects and risk mechanisms; explicitly retain worked classification examples and action-based-on-input open relations.

## Run Return Codes

```json
{
  "development": {
    "baseline": 0,
    "variant": 1
  }
}
```
