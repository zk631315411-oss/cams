# P4C cross-chapter relation evidence binding v1

You are binding unit-level evidence to reviewed P4 cross-chapter core_point -> core_point relations.

Task: For each reviewed P4 relation, select evidence units from the provided source and target P2B unit-edge pools.

Do not create new relations. Do not reject relations. Do not change source/target IDs. Do not use units outside the provided source/target pools.

Allowed support_strength values:

```text
strong
medium
weak
```

Relation meanings and evidence selection rules:

## summarizes

- Meaning: the source CP is a concise summary, key takeaway, overview, or recap; the target CP is the detailed treatment of the same specific topic.
- `source_evidence_unit_ids`: units in the summary CP that state the summary.
- `target_evidence_unit_ids`: units in the detailed CP that are being summarized.

## illustrates

- Meaning: the source CP is a case, example, scenario, or concrete instance; the target CP is the concept/risk/control/process directly demonstrated by that example.
- `source_evidence_unit_ids`: units in the case/example CP that concretely illustrate the target.
- `target_evidence_unit_ids`: units in the target CP that define, explain, classify, state the risk/control/process, or otherwise name what is being illustrated.

## grounds

- Meaning: the source CP gives a concrete definition, classification, process, rule, framework, comparison, or general method; the target CP directly expands, applies, specializes, operationalizes, or instantiates it.
- `source_evidence_unit_ids`: foundation units in the source CP.
- `target_evidence_unit_ids`: dependent units in the target CP that apply, expand, specialize, operationalize, or instantiate the source foundation.

## contrasts

- Meaning: the two CPs form an explicit comparison, boundary, or distinction that is useful for review.
- `source_evidence_unit_ids`: units that state one side of the distinction.
- `target_evidence_unit_ids`: units that state the other side of the distinction.

Selection constraints:

1. Select only units from `source_core_point.p2b_unit_edges` for `source_evidence_unit_ids`.
2. Select only units from `target_core_point.p2b_unit_edges` for `target_evidence_unit_ids`.
3. Select 1-5 source units and 1-5 target units. Do not exceed 5 units on either side.
4. Do not include a unit just because it shares a term, method, industry, or broad topic.
5. For target evidence, select only units directly illustrated, summarized, grounded, or contrasted by the source evidence. Do not select every unit in the target CP.
6. If support is thin, still select the best available units and set `support_strength` to `weak` or `medium`.
7. Base the evidence choice on the provided unit_text, not only on titles or prior reasons.
8. If a CP contains a long list of methods, risks, controls, or examples, choose the lead definition/classification unit plus 2-3 representative list items most directly needed to prove this relation. Do not copy the whole list.
9. When a source or target CP has one definition unit plus five or more risk-element/list units, select at most 4 units from that CP in total. Select the definition unit and only the strongest representative list units.
10. Outputs with more than 5 source units or more than 5 target units are invalid.

Output exactly one JSON object:

```json
{
  "binding_batch_id": "p4c_relation_evidence_binding",
  "relation_evidence_bindings": [
    {
      "p4_relation_id": "p4vec_0001",
      "relation_type": "grounds",
      "source_core_point_id": "cp_CH19_S02_001",
      "target_core_point_id": "cp_CH26_S08_005",
      "source_evidence_unit_ids": ["v7u_N001234"],
      "target_evidence_unit_ids": ["v7u_N004321"],
      "support_strength": "strong",
      "evidence_summary": "Short explanation of how the selected source units support the relation to selected target units."
    }
  ]
}
```

No markdown. No extra text.
