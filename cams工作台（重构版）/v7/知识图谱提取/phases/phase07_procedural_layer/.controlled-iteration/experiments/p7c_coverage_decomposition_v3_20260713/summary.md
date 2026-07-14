# Experiment p7c_coverage_decomposition_v3_20260713

- Objective: Improve semantic validity of additive Coverage graph patches while preserving the fixed v2 Audit ledger
- Hypothesis: Qualifier-aware node labels, exact source-process matching, and independent-result checks will convert more fixed Audit gaps into P7D-accepted edges with fewer rejected edges
- Changed variable: coverage_patch_builder_prompt_v2
- Execution status: ran
- Verdict: reject
- Issue count: 3

## Evaluation

Patch v2 reduced newly rejected edges from seven to three and produced three accepted edges, but a missing relation_type contract check blocked the UBO card from semantic review, CH02 still reused an unsupported source process, and three valid institutional-process claims were left unresolved.

## Next Action

Create a new patch evidence contract that permits explicitly named institutional processes without inventing an actor, requires every added edge evidence set to cover both endpoint evidence, validates relation_type against the schema, and defaults to omitting relation_type.

## Run Return Codes

```json
{
  "development": {
    "baseline": 0,
    "variant": 0
  }
}
```
