## AB Arm B: CP Candidate Recall Overlay

This block applies only to the B arm and overrides any earlier instruction that forbids viewing CP-derived candidate context.

You are still the final P7C extractor. The source of truth remains the current section text and current-section unit anchors.

The supplied `flow_node_candidates` are recall hints produced in a separate first-stage call. They are not final nodes, not evidence, and not requirements.

Before producing cards:

1. Decide independently whether the section contains any P7 handling or judgement path.
2. Check every candidate against the section units.
3. Delete candidates that are ordinary KG material, unsupported, redundant, or outside P7 scope.
4. Merge candidates that describe one usable role.
5. Split candidates that contain multiple distinct roles.
6. Add missing nodes directly supported by section units.
7. Derive every final `flow_edge` from unit semantics. Do not infer edge type or direction from candidate order, CP order, or CP-CP relations.
8. Cite only current-section `unit_id` values in final node and edge evidence.

Optional audit metadata may be added to a final node:

```text
core_point_ids
candidate_ids
cp_match_status = exact / partial / none / ambiguous
cp_match_reason
```

This metadata does not replace `evidence_unit_ids` and must not change the canonical P7 graph contract.

## Candidate Context

```json
<flow_node_candidates_payload>
```
