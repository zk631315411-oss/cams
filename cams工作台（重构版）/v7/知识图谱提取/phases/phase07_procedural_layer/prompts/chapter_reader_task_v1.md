# P7 Chapter Reader Task v1

You are building a procedural / operational overlay for a textbook knowledge graph.

Read the assigned chapter or section group in textbook order. Do not rely on keyword snippets alone. Preserve the author's local sequence and section context.

## Reader Output

Return structured JSON only, matching the process card contract.

Top-level fields:

```json
{
  "task_id": "...",
  "reader_role": "reader_a_explicit|reader_b_process",
  "chapter_flow_overview_zh": "...",
  "process_cards": [],
  "bridge_needed": [],
  "warnings": []
}
```

## Extraction Rules


1. Read in textbook order.
2. First summarize the chapter-level process logic in Chinese.
3. Then create process cards section by section.
4. Each card must cite `unit_id` values and quote the supporting original text.
5. Extract short edges only. Do not generate a full-book workflow.
6. Distinguish ordinary forward flow from feedback loops.
7. Mark local loop roles when clear: `entry`, `process`, `decision`, `feedback`, `exit`.
8. Do not treat related concepts as process edges unless the text supports action, input, output, condition, trigger, review, validation, escalation, documentation, or feedback.
9. P5 aliases can normalize node names, but aliases are not evidence for an edge.

## Reader Roles

`reader_a_explicit`:

- Extract only edges directly supported by the cited unit text.
- If an edge seems plausible but not explicit, put it in `bridge_needed` or `warnings`, not in formal edges.

`reader_b_process`:

- Extract explicit edges and strong inference candidates.
- Strong inference must cite nearby units and include uncertainty flags.
- Weak inference must be marked and should not be proposed as formal.

## Edge Requirements

Every edge must include:

```json
{
  "source_id": "activity.example",
  "relation_type": "CHECKS_AGAINST",
  "target_id": "object.example",
  "edge_family": "input_context",
  "evidence_unit_ids": ["v7u_N000000"],
  "evidence_text": "Exact supporting text from the unit.",
  "derivation": "explicit|strong_inference|weak_inference",
  "confidence": 0.0,
  "warning_flags": []
}
```

## Do Not

- Do not invent industry-standard process steps without textbook evidence.
- Do not turn broad conceptual relatedness into procedural edges.
- Do not merge CDD, KYC, EDD, ongoing due diligence, and transaction monitoring into one node.
- Do not hide uncertainty.
- Do not output diagrams only; diagrams can be derived later from structured cards.

