# P3A chapter cross-section core_point relations v1

You are helping build Phase 3A for a CAMS v7 textbook knowledge graph.

Task: For one chapter, identify useful relations between core_points from different sections in the same chapter.

Allowed relation_type values:

```text
summarizes
illustrates
grounds
```

Do not output `alias_of`. In this version, repeated-topic cases should be handled by `summarizes`, `illustrates`, or `grounds`; if none fits, omit the relation.

Definitions:

- `section`: a textbook section identified by P1, such as `CH02-S05`.
- `core_point`: a review-outline node accepted by P2A/P2A_review.
- `relation`: a chapter-local relation from one core_point to another core_point in a different section.

Hard rules:

1. Work only inside the provided `chapter_id`.
2. Use only provided `core_point_id` values.
3. Source and target must be in different sections.
4. Do not create, split, merge, rename, or delete core_points.
5. Do not create core_point -> unit edges.
6. Do not create same-section or cross-chapter relations.
7. Output only strong relations useful for a chapter-level review mind map.
8. Do not connect all related topics just because they share a broad theme.
9. It is valid to output an empty `core_point_relations` array.
10. Return exactly one JSON object. No markdown.

Relation definitions and direction:

- `summarizes`: source is a summary or key-takeaway CP; target is the detailed/source CP being summarized. Direction is summary -> detailed/source.
- `illustrates`: source is a case, example, scenario, or concrete narrative; target is the concept/risk/control/process it illustrates. Direction is case/example -> concept.
- `grounds`: source is the prerequisite definition, framework, comparison, or conceptual foundation; target is the later expansion, application, example category, risk/control use, or specific case-type application that depends on that foundation. Direction is always foundation -> dependent application.

For `grounds`, the JSON fields have fixed meanings:

```text
source_core_point_id = foundation_core_point_id
target_core_point_id = dependent_application_core_point_id
```

Do not use `source_core_point_id` for the later CP just because the later CP mentions, applies, or points back to the foundation. If the later CP is grounded in the earlier framework, the earlier framework is the source.

How to decide `grounds`:

1. First identify which CP is the foundation.
   - Foundation CPs define terms, introduce a framework, list categories, establish a comparison, or give a general rule.
   - Words in the evidence/reason often include: defines, introduces, identifies, lists, establishes, framework, category, concept, comparison.
2. Then identify which CP depends on that foundation.
   - Dependent CPs apply the concept to a specific crime/risk/control, expand one category, explain a later consequence, or use the framework in a concrete context.
   - Words in the evidence/reason often include: later applies, later explains, expands, uses that framework, specific application, example of that category.
3. Output `source grounds target` with foundation as source and dependent application as target.
4. If your reason says "A introduces/defines/lists...; B later applies/explains...", then the relation must be `A grounds B`.
5. Never output `B grounds A` in that situation, even if B mentions or points back to A.
6. If you cannot clearly identify a foundation CP and a dependent CP, omit the relation.
7. Before final JSON, audit every `grounds` relation by rewriting it mentally as: "SOURCE provides the foundation for TARGET." If that sentence is false, swap the IDs or remove the relation.

Priority:

1. If the source section is `Key takeaways`, prefer `summarizes` when it clearly summarizes an earlier detailed CP.
2. If the source section is a `Case example`, prefer `illustrates`.
3. Use `grounds` for concept-to-application or overview-to-expansion. Direction must be overview/framework/basic concept -> later detailed expansion/application.
4. If a pair is merely about the same broad subject, omit it.
5. Never output relations within the same section, even if the section contains a case CP and a concept CP.
6. For `Key takeaways`, first check whether it summarizes the immediately preceding case or topic. Do not automatically target the chapter opening overview.
7. For `grounds`, do not connect sibling examples under the same chapter theme. One predicate-crime example does not ground another predicate-crime example.
8. For `illustrates`, the case/example must clearly demonstrate the target CP, not merely mention a similar term or method.
   If a case and another CP only share methods such as TBML, shell companies, crypto, hawala, front companies, or red flags, do not output `illustrates`; this belongs to P5 term/method indexing or an auxiliary retrieval layer.
9. Before returning `grounds`, check the reason against the direction. If the reason says the target introduces the foundation and the source is the later application, the direction is wrong; swap it or omit the relation.
10. If a Key takeaways section directly follows a case and uses the same lessons/consequences/mitigations from that case, target the case CP, not the earlier overview CP.
11. Do not create hub-and-spoke `grounds` edges from one broad chapter overview to many later CPs. A broad regulatory landscape, chapter introduction, or historical overview does not ground every later rule, agency, jurisdiction, or framework.
12. Do not use `grounds` for parallel regimes or comparative frameworks. For example, a US BSA overview does not ground EU AMLD, AMLA, MiCA, OFAC, or other parallel regulatory frameworks merely because all are AML regulation topics. Omit those relations unless the later CP explicitly depends on a specific definition, requirement, or mechanism introduced by the source CP.
13. For `grounds`, require a direct dependency: the target CP should need the source CP to be understood. Shared domain, chronology, legal history, or same chapter placement is not enough.

Good examples:

```json
[
  {
    "source_core_point_id": "cp_CH02_S02_001",
    "target_core_point_id": "cp_CH02_S01_002",
    "relation_type": "summarizes",
    "reason": "CH02-S02 is a key-takeaway section summarizing sanctions evasion, shell companies, and complex strategies covered in CH02-S01."
  },
  {
    "source_core_point_id": "cp_CH02_S04_001",
    "target_core_point_id": "cp_CH02_S03_001",
    "relation_type": "illustrates",
    "reason": "The FullTechGlobal case illustrates bribery forms, gifts, intermediaries, and ABC policy failures discussed in CH02-S03."
  },
  {
    "source_core_point_id": "cp_CH05_S01_002",
    "target_core_point_id": "cp_CH05_S04_001",
    "relation_type": "grounds",
    "reason": "CH05-S01 introduces financial crime risk types, and CH05-S04 expands the operational, legal, concentration, and reputational risk categories."
  }
]
```

More good examples from reviewed chapters:

```json
[
  {
    "source_core_point_id": "cp_CH02_S01_001",
    "target_core_point_id": "cp_CH02_S05_005",
    "relation_type": "grounds",
    "reason": "CH02-S01 defines predicate crimes and lists tax crimes as FATF predicate offenses; CH02-S05 later applies that framework to tax evasion as a predicate offense for money laundering."
  },
  {
    "source_core_point_id": "cp_CH02_S01_001",
    "target_core_point_id": "cp_CH02_S06_004",
    "relation_type": "grounds",
    "reason": "CH02-S01 introduces predicate crimes and money laundering as a foundation; CH02-S06 later applies that foundation to cyber-enabled crime's relationship with money laundering and terrorist financing."
  },
  {
    "source_core_point_id": "cp_CH02_S05_001",
    "target_core_point_id": "cp_CH02_S04_001",
    "relation_type": "summarizes",
    "reason": "CH02-S05 key takeaways summarize lessons from the FullTechGlobal case: intermediaries, shell companies, false invoicing, audits, monitoring, and anti-bribery clauses."
  },
  {
    "source_core_point_id": "cp_CH03_S04_001",
    "target_core_point_id": "cp_CH03_S05_001",
    "relation_type": "grounds",
    "reason": "CH03-S04 first distinguishes terrorism financing from money laundering, including legitimate and illegitimate sources; CH03-S05 then expands terrorism financing sources."
  },
  {
    "source_core_point_id": "cp_CH03_S07_001",
    "target_core_point_id": "cp_CH03_S06_004",
    "relation_type": "illustrates",
    "reason": "The Mr. Wolfe case explicitly uses hawala brokers, illustrating alternative remittance systems in CH03-S06."
  },
  {
    "source_core_point_id": "cp_CH05_S03_001",
    "target_core_point_id": "cp_CH05_S02_001",
    "relation_type": "summarizes",
    "reason": "CH05-S03 key takeaways immediately follow the HSBC case and summarize its lesson: AML failures expose institutions to regulatory and reputational risks."
  },
  {
    "source_core_point_id": "cp_CH05_S03_002",
    "target_core_point_id": "cp_CH05_S02_001",
    "relation_type": "summarizes",
    "reason": "CH05-S03 key takeaways summarize the HSBC case's corrective lessons: leadership accountability, ongoing compliance investment, and strong AML frameworks."
  },
  {
    "source_core_point_id": "cp_CH05_S01_002",
    "target_core_point_id": "cp_CH05_S04_001",
    "relation_type": "grounds",
    "reason": "CH05-S01 introduces operational, legal, concentration, and reputational risks; CH05-S04 later expands those categories."
  }
]
```

Bad examples:

```json
[
  {
    "source_core_point_id": "cp_CH02_S03_001",
    "target_core_point_id": "cp_CH02_S04_001",
    "relation_type": "summarizes",
    "reason": "Both mention bribery."
  },
  {
    "source_core_point_id": "cp_CH02_S04_001",
    "target_core_point_id": "cp_CH02_S03_001",
    "relation_type": "grounds",
    "reason": "The case is related to the concept."
  }
]
```

Reasons:

- A case/example does not summarize or ground a concept; it illustrates it.
- Shared broad topic is not enough.

More bad examples. These are INVALID JSON outputs and must not be copied:

```json
[
  {
    "source_core_point_id": "cp_CH02_S06_004",
    "target_core_point_id": "cp_CH02_S01_001",
    "relation_type": "grounds",
    "reason": "Cyber-enabled crime has a money laundering connection, so it grounds predicate crime concepts."
  },
  {
    "source_core_point_id": "cp_CH02_S05_005",
    "target_core_point_id": "cp_CH02_S01_001",
    "relation_type": "grounds",
    "reason": "CH02-S01 defines predicate crimes and lists tax crimes; CH02-S05 later applies that framework to tax evasion."
  },
  {
    "source_core_point_id": "cp_CH02_S06_004",
    "target_core_point_id": "cp_CH02_S01_001",
    "relation_type": "grounds",
    "reason": "CH02-S01 introduces predicate crimes and money laundering; CH02-S06 later explains cyber-enabled crime's connection to money laundering."
  },
  {
    "source_core_point_id": "cp_CH03_S01_002",
    "target_core_point_id": "cp_CH03_S02_003",
    "relation_type": "grounds",
    "reason": "Both discuss laundering proceeds from predicate crimes."
  },
  {
    "source_core_point_id": "cp_CH05_S03_001",
    "target_core_point_id": "cp_CH05_S01_002",
    "relation_type": "summarizes",
    "reason": "The key takeaway mentions risk exposure, so it summarizes the chapter risk overview."
  },
  {
    "source_core_point_id": "cp_CH05_S03_002",
    "target_core_point_id": "cp_CH05_S01_003",
    "relation_type": "summarizes",
    "reason": "The key takeaway mentions mitigation, so it summarizes the earlier compliance overview."
  },
  {
    "source_core_point_id": "cp_CH05_S04_001",
    "target_core_point_id": "cp_CH05_S01_002",
    "relation_type": "grounds",
    "reason": "The detailed risk categories ground the earlier overview."
  },
  {
    "source_core_point_id": "cp_CH24_S01_001",
    "target_core_point_id": "cp_CH24_S08_003",
    "relation_type": "grounds",
    "reason": "The BSA establishes the US AML regulatory structure; the EU's AMLA is a parallel supervisory authority."
  },
  {
    "source_core_point_id": "cp_CH24_S01_001",
    "target_core_point_id": "cp_CH24_S10_001",
    "relation_type": "grounds",
    "reason": "The BSA applies to cryptocurrency firms; MiCA provides the EU cryptoasset framework."
  }
]
```

Reasons:

- A later application does not ground an earlier framework.
- If the explanation says an earlier framework introduces the later topic, the earlier framework must be the source for `grounds`.
- If the explanation says "CH02-S01 defines... CH02-S05 later applies...", the only valid JSON direction is `source_core_point_id=cp_CH02_S01_001`, `target_core_point_id=cp_CH02_S05_005`.
- If the explanation says "CH02-S01 introduces... CH02-S06 later explains...", the only valid JSON direction is `source_core_point_id=cp_CH02_S01_001`, `target_core_point_id=cp_CH02_S06_004`.
- One predicate-crime example does not ground another predicate-crime example.
- A key-takeaway section following a case should usually summarize the case, not the distant chapter overview.
- Detailed expansion does not ground the overview that introduced it.
- A broad overview should not become a hub that grounds many later CPs.
- Parallel regulatory regimes belong to review comparison or P4/P5-style auxiliary indexing unless there is a direct dependency.

Direction examples:

```text
Good grounds: financial crime risk types -> operational/legal/reputational risk details
Bad grounds: operational/legal/reputational risk details -> financial crime risk types

Good summarizes: key takeaway -> earlier detailed CP
Bad summarizes: detailed CP -> key takeaway

Good illustrates: case example -> concept/risk/control CP
Bad illustrates: concept/risk/control CP -> case example
```

Return shape:

```json
{
  "chapter_id": "CH02",
  "core_point_relations": [
    {
      "relation_id": "p3a_rel_CH02_001",
      "source_core_point_id": "cp_CH02_S04_001",
      "target_core_point_id": "cp_CH02_S03_001",
      "relation_type": "illustrates",
      "reason": "The FullTechGlobal case concretely illustrates bribery forms and ABC failures discussed in CH02-S03."
    }
  ],
  "review_items": []
}
```

