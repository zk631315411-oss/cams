# P2B core_point to unit role edges

You are helping build Phase 2B for a CAMS v7 textbook knowledge graph.

Task: For one section, use P2A core_points and the section unit text to create `core_point -> unit` role edges.

Definitions:

- `unit`: a frozen knowledge unit. Reference it only by `unit_id`.
- `core_point`: a review-outline node already produced by P2A.
- `edge`: a section-local relation from one core_point to one unit.
- P2A evidence is a draft boundary. P2B must make the boundary cleaner.

Hard rules:

1. Work only inside the provided `section_id`.
2. Use only provided `core_point_id` and `unit_id` values.
3. Do not create new core_points.
4. Do not create cross-section or cross-chapter relations.
5. Prefer narrow accepted evidence. Do not attach every nearby unit to a core_point.
6. If a unit is in a P2A evidence span but actually belongs to another core_point, output an `exclude` edge with `status="excluded"` and explain why.
7. A unit may connect to more than one core_point only when the textbook sentence genuinely serves more than one review point.
8. Each non-empty core_point should normally have at least one `anchor` edge.
9. Return exactly one JSON object. No markdown.

Allowed roles:

```text
anchor
support
example
risk
measure
context
exclude
```

Role definitions:

- `anchor`: the unit states the core concept, definition, classification, model, rule, or main proposition.
- `support`: the unit explains, qualifies, or extends the core concept.
- `example`: the unit is a case/example/scenario illustrating the core concept.
- `risk`: the unit states a risk, red flag, exposure, or warning signal.
- `measure`: the unit states a control, requirement, remediation, monitoring step, or recommended action.
- `context`: the unit is a lead-in, background, or section bridge that helps reading but is not central.
- `exclude`: the unit should not belong to this core_point, even if P2A included it in a broad span.

Status values:

```text
accepted
excluded
needs_review
```

Confidence values:

```text
high
medium
low
```

Examples:

- Cyber-enabled crime trust boundary: if a core_point is about trust in cyber-enabled crime, units about trust and deceptive credibility are `anchor` or `support`. Units that only list outcomes such as network disruption, fraudulently obtaining funds, extortion, or identity theft should be `exclude` for the trust core_point if they are already a separate outcomes core_point.
- Definition-then-expansion structure: if one unit briefly defines operational risk and later units expand operational risk in detail, connect the definition as `anchor` and the later details as `support`, even when other risk definitions appear between them. Do not attach unrelated intervening definitions as support.
- Case section: if the entire section is one case core_point, narrative setup can be `context`, scheme actions can be `anchor` or `support`, detection/outcome can be `support`, and explicit lesson/control statements can be `measure`.
- Key takeaways: if multiple short units serve one review point, connect them by role. Do not mark a unit as `exclude` merely because it is short.

Return shape:

```json
{
  "section_id": "CH02-S06",
  "core_point_unit_edges": [
    {
      "edge_id": "edge_CH02_S06_001",
      "core_point_id": "cp_CH02_S06_002",
      "unit_id": "v7u_N000184",
      "role": "anchor",
      "relation_type": "belongs_to",
      "status": "accepted",
      "confidence": "high",
      "reason": "Unit 184 states that trust is the foundation of cyber-enabled crime."
    }
  ],
  "review_items": [
    {
      "item_id": "review_CH02_S06_001",
      "core_point_id": "cp_CH02_S06_002",
      "issue": "P2A span includes units from another review topic.",
      "unit_ids": ["v7u_N000188", "v7u_N000189"],
      "recommendation": "Keep these units under the outcomes core_point, not the trust core_point."
    }
  ]
}
```

