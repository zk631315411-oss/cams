# Experiment p7c_coverage_decomposition_v5_20260713

- Objective: Resolve the remaining graph-shape, required-qualifier, and investigation-stage Patch failures using the fixed Audit and evidence contract
- Hypothesis: Targeted Patch rules for separate minimal cards, required qualifiers, and investigation-stage source matching will reduce rejected and structure-blocked edges without regressing accepted repairs
- Changed variable: targeted_patch_rules_v4_addendum
- Execution status: failed
- Verdict: reject
- Issue count: 2

## Evaluation

The targeted Patch addendum did not pass the development gate. The strict contract correctly blocked CH02 because one edge did not cover its source node, while CH06 still ignored the separate-card instruction. The failed output was preserved and was not retried or sent to P7D.

## Next Action

Stop prompt-only iteration. Keep v2 Audit and v4 strict Patch contract as the best development design. Before production integration, add deterministic safe routing: a contract-failed Patch must preserve the Audit claim as unresolved and leave the original graph unchanged. Treat CH02 as a schema/product boundary decision and route CH06 classification to a dedicated minimal-card construction path rather than relying on prompt compliance.

## Run Return Codes

```json
{
  "development": {
    "baseline": 0,
    "variant": 1
  }
}
```
