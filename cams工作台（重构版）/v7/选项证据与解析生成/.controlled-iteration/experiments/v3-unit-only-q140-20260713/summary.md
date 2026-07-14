# Experiment v3-unit-only-q140-20260713

- Objective: Prevent blind-reason contamination in V3 textbook-grounded prose
- Hypothesis: Hiding model-authored blind reasons while keeping locked judgements and real unit text will remove unsupported claims without breaking V3 export readiness
- Changed variable: Prompt-visible factual material
- Execution status: ran
- Verdict: reject
- Issue count: 3

## Evaluation

The unit-only prompt removed the unsupported digital-asset claim, but it still conflated the contextual foreign-withdrawal fact with the decisive structuring definition and allowed unit IDs into prose.

## Next Action

Create a second isolated variant that separates decisive stem signals from contextual facts; handle internal-ID removal as deterministic normalization with regression tests.

## Run Return Codes

```json
{
  "development": {
    "baseline": 0,
    "variant": 0
  }
}
```
