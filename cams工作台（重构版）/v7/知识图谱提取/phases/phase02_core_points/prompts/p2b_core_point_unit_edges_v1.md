# P2B core_point unit edges v1

You are helping build Phase 2B for a CAMS v7 textbook knowledge graph.

Task: For one target `core_point` inside one section, judge each candidate unit and create `core_point -> unit` semantic edges.

Definitions:

- `unit`: a frozen knowledge unit. Reference it only by `unit_id`.
- `target_core_point`: the P2A core_point currently being judged.
- `candidate_units`: units selected from the target core_point's P2A anchor/support/intervening/evidence spans.
- `sibling_core_points`: other P2A core_points in the same section, provided only to prevent accidental over-attachment.
- `edge`: a section-local relation from the target core_point to one unit.

Hard rules:

1. Work only inside the provided `section_id` and `target_core_point_id`.
2. Use only provided `unit_id` values.
3. Do not create new core_points.
4. Do not create cross-section or cross-chapter relations.
5. Every `candidate_unit_id` must receive exactly one edge for the target core_point.
6. Use `exclude` when a candidate unit belongs better to a sibling core_point or is only nearby text.
7. Prefer narrow accepted evidence. Do not attach every nearby unit merely because it appears in a P2A evidence span.
8. A unit outside `candidate_unit_ids` may be attached only if it is clearly necessary for the target core_point; otherwise ignore it.
9. Return exactly one JSON object. No markdown.
10. Do not output old fields such as `role`, `status`, or `confidence`.

Allowed edge_type values:

```text
defines
classifies
explains
states_rule
describes_process
indicates_risk
prescribes_measure
illustrates
states_consequence
provides_context
exclude
```

Edge type definitions:

- `defines`: the unit defines a concept, term, or boundary.
- `classifies`: the unit lists a type, category, form, component, or list item.
- `explains`: the unit explains, qualifies, distinguishes, limits, or expands the core_point.
- `states_rule`: the unit states a legal rule, compliance requirement, standard, obligation, or judgment criterion.
- `describes_process`: the unit describes a step, stage, sequence, method, typology, or operational process.
- `indicates_risk`: the unit states a risk, red flag, suspicious indicator, exposure, or vulnerability.
- `prescribes_measure`: the unit states a control, monitoring action, mitigation, remediation, or recommended action.
- `illustrates`: the unit gives an example, scenario, case fact, case action, or case outcome.
- `states_consequence`: the unit states a penalty, loss, impact, outcome, or consequence.
- `provides_context`: the unit is background, lead-in, transition, learning objective, or non-core context.
- `exclude`: the unit should not belong to this core_point.

Examples:

- Money laundering definition: a unit defining money laundering is `defines`; a unit listing predicate crime examples is `illustrates`; a unit explaining jurisdictional variation is `explains`.
- FATF 21 categories: the definition and list introduction are `defines` or `classifies`; each numbered predicate crime item is `classifies`; jurisdiction differences are `explains` or `provides_context`.
- Sanctions evasion: a unit stating sanctions targets try to evade sanctions is `explains`; payment/trade/ownership evasion methods are `describes_process`; required compliance programs are `prescribes_measure`; penalties are `states_consequence`.
- Cyber-enabled crime trust boundary: for a target core_point about trust, units about trust and deceptive credibility are `explains`. Units that only list outcomes such as disruption, fraudulently obtaining funds, extortion, or identity theft should be `exclude` if the section has a sibling outcomes core_point.
- Fraud red flags: a lead-in unit such as "Common red flags include" is `provides_context`; individual red-flag units are `indicates_risk`.
- Case section: narrative setup, scheme actions, detection, and legal outcome are usually `illustrates`. Explicit lessons or controls are `prescribes_measure`; penalties are `states_consequence`.

Return shape:

```json
{
  "section_id": "CH02-S06",
  "target_core_point_id": "cp_CH02_S06_002",
  "core_point_unit_edges": [
    {
      "edge_id": "edge_CH02_S06_002_001",
      "core_point_id": "cp_CH02_S06_002",
      "unit_id": "v7u_N000184",
      "edge_type": "explains",
      "reason": "Unit 184 explains that trust is the foundation of cyber-enabled crime."
    },
    {
      "edge_id": "edge_CH02_S06_002_002",
      "core_point_id": "cp_CH02_S06_002",
      "unit_id": "v7u_N000189",
      "edge_type": "exclude",
      "reason": "Unit 189 is about an outcome of cyber-enabled crime and belongs better to the sibling outcomes core_point."
    }
  ],
  "review_items": []
}
```
