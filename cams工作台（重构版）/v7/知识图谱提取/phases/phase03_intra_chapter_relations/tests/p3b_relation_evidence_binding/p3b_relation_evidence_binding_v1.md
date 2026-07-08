# P3B relation evidence binding v1

You are binding unit-level evidence to reviewed P3A core_point -> core_point relations.

Task: For each reviewed P3A relation, select evidence units from the provided source and target P2B unit-edge pools.

Do not create new relations. Do not reject relations. Do not change source/target IDs. Do not use units outside the provided source/target pools.

Allowed support_strength values:

```text
strong
medium
weak
```

Evidence selection rules:

## summarizes

- `source_evidence_unit_ids`: units in the summary/key-takeaway CP that state the summary.
- `target_evidence_unit_ids`: units in the detailed/case/source CP that are being summarized.

## illustrates

- `source_evidence_unit_ids`: units in the case/example CP that concretely illustrate the target.
- `target_evidence_unit_ids`: units in the target CP that define, explain, classify, state the risk/control/process, or otherwise name what is being illustrated.

## grounds

- `source_evidence_unit_ids`: foundation units in the source CP, such as definitions, classifications, framework statements, comparisons, or general rules.
- `target_evidence_unit_ids`: dependent units in the target CP that apply, expand, operationalize, or instantiate the source foundation.

Selection constraints:

1. Select only units from `source_core_point.p2b_unit_edges` for `source_evidence_unit_ids`.
2. Select only units from `target_core_point.p2b_unit_edges` for `target_evidence_unit_ids`.
3. Prefer 1-5 source units and 1-5 target units.
4. Do not include a unit just because it shares a method or term; include it only if it supports this relation.
5. For target evidence, select only units directly illustrated, summarized, or grounded by the source evidence. Do not select every unit in the target CP.
6. If support is thin, still select the best available units and set `support_strength` to `weak` or `medium`.

Output exactly one JSON object:

```json
{
  "binding_batch_id": "p3b_relation_evidence_binding_test",
  "relation_evidence_bindings": [
    {
      "p3_relation_id": "p3a_rev_CH02_002",
      "relation_type": "illustrates",
      "source_core_point_id": "cp_CH02_S04_001",
      "target_core_point_id": "cp_CH02_S03_001",
      "source_evidence_unit_ids": ["v7u_N000138"],
      "target_evidence_unit_ids": ["v7u_N000115"],
      "support_strength": "strong",
      "evidence_summary": "Short explanation of how selected source units support the relation to selected target units."
    }
  ]
}
```

No markdown. No extra text.
