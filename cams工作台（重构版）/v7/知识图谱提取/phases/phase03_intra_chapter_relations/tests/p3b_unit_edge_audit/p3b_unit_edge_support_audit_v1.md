# P3B unit-edge support audit v1

You are auditing reviewed P3A relations for a CAMS v7 textbook knowledge graph.

Task: Decide whether each reviewed P3A relation is supported by the P2B core_point -> unit semantic edges of its source and target core_points.

You must not create new relations. You must not delete relations. You must not change source/target IDs or relation_type. Only audit the evidence support.

Allowed audit_status values:

```text
supported
weak_support
unsupported
```

Relation support criteria:

## summarizes

The source CP should look like a summary/key-takeaway CP, and its P2B edges should summarize or restate the target CP's detail/case/control/risk. The target CP should have detailed evidence edges such as `defines`, `explains`, `illustrates`, `indicates_risk`, `prescribes_measure`, `states_consequence`, or `describes_process`.

Use `supported` when the source edges clearly summarize the target's detailed unit edges.
Use `weak_support` when the relation is plausible but the P2B edge types do not clearly show summarization.
Use `unsupported` when the unit edges point to unrelated topics.

## illustrates

The source CP should contain case/example/scenario/narrative evidence, often visible through `illustrates`, `provides_context`, `states_consequence`, or concrete fact-chain edges. The target CP should contain the concept/risk/control/process being illustrated.

Use `supported` when the source P2B edges directly show a concrete example of the target CP.
Use `weak_support` when the source only shares a method or term with the target.
Use `unsupported` when the source does not illustrate the target CP.

## grounds

The source CP should have foundation edges such as `defines`, `classifies`, `provides_context`, `explains`, or `states_rule`. The target CP should have dependent/application edges such as `explains`, `describes_process`, `indicates_risk`, `prescribes_measure`, or `states_consequence`.

Use `supported` when source edges provide the framework/definition/category needed by target edges.
Use `weak_support` when the relation is conceptually plausible but P2B edges do not strongly show foundation -> application.
Use `unsupported` when source/target edges do not have foundation/application structure.

Output exactly one JSON object:

```json
{
  "audit_batch_id": "p3b_first5_unit_edge_audit",
  "relation_audits": [
    {
      "p3_relation_id": "p3a_rev_CH02_001",
      "audit_status": "supported",
      "source_support": "Source CP has ... P2B edges showing ...",
      "target_support": "Target CP has ... P2B edges showing ...",
      "notes": "Short reason."
    }
  ]
}
```

No markdown. No extra text.
