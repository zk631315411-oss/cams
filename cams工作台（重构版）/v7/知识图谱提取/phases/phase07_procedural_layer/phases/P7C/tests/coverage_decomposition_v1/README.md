# P7C Coverage Decomposition v1

This isolated experiment splits the former one-call Coverage step into:

1. `Coverage Audit`: discover and classify proposition-level coverage gaps without graph construction.
2. `Coverage Patch`: construct additive candidate graph patches only for `missing` and `partially_covered` P7C claims.

The experiment reuses the initial extraction responses from the v23 ten-section run. This keeps the initial extraction, model, section sample, KG inputs, and P7D evaluator fixed while changing only the Coverage workflow.

The runner processes sections concurrently. Existing cards, nodes, and edges are immutable; all additions retain claim-level provenance and remain P7C candidates until P7D review.
