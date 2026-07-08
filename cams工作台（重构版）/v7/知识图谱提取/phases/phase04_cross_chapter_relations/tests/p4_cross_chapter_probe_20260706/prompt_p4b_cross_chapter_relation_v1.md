# P4B cross-chapter relation judge v1

You are judging cross-chapter core_point -> core_point relations in a CAMS textbook knowledge graph.

Task: For each candidate pair, decide whether it should become a main KG cross-chapter relation. If accepted, choose the correct source -> target direction.

P4A is a recall step. A high vector similarity score means only "worth checking". It does not mean the pair should become a KG edge.

Allowed relation types:

```text
summarizes
illustrates
grounds
contrasts
none
```

Definitions:

## summarizes

Use when the source CP is a summary/key-takeaway/general recap of the target CP.

Direction:

```text
source_core_point_id = summary CP
target_core_point_id = detailed/source CP
```

Valid when:

- the source is shorter or more recap-like;
- the target is a detailed treatment of the same specific topic;
- a reader would naturally use the source as a revision summary before the target.

Do not use when:

- the source merely appears earlier in the textbook;
- the two CPs share a broad topic but are not summary/detail versions of the same point.

Example accept:

```text
CH01 Three Stages of Money Laundering -> CH03 Money Laundering Process
Reason: CH01 states the three-stage frame briefly; CH03 expands the same laundering process.
```

## illustrates

Use when the source CP is a case/example/scenario that directly illustrates the target CP.

Direction:

```text
source_core_point_id = case/example CP
target_core_point_id = concept/risk/control/process CP being illustrated
```

If one CP is a case/example and the other CP is a concept/framework, the case/example must be the source. A concept/framework CP does not `illustrates` a case CP.

Do not output `illustrates` when a case and another CP merely share methods such as TBML, shell companies, crypto, hawala, front companies, or red flags. Those belong to P5 term/method indexing.

Valid when:

- the source is a concrete case/example/scenario;
- the target names the concept, risk, control, process, or category directly demonstrated by the case;
- the case would be useful as evidence or a teaching example for the target CP.

Do not use when:

- the case only happens to mention similar methods or terms;
- the target is a broad consequences/risk/background CP not directly demonstrated by the case.

Example accept:

```text
CH03 Mr. Wolfe terrorist financing case -> CH02 Predicate Crimes and FATF Categories
Reason: the case directly demonstrates terrorist financing as a predicate crime category.
```

Example reject:

```text
CH02 sanctions evasion case -> CH04 Broader consequences of financial crime
Reason: the case may involve harms, but it does not directly teach CH04's consequences framework.
```

## grounds

Use when the source CP gives a specific definition, framework, classification, process, or rule that the target CP directly applies, expands, specializes, or operationalizes.

Direction:

```text
source_core_point_id = foundation CP
target_core_point_id = dependent/application/expansion CP
```

Strict judgment test: accept `grounds` only when all three gates pass:

1. Source has a concrete structure: definition, named concept, classification, process steps, rule, or explicit framework.
2. Target directly uses that same structure: it expands one category, applies one process, specializes one definition, or operationalizes one rule.
3. The edge would help a reader follow a review path, not merely remind them of broad background.

If any gate fails, reject.

Do not use `grounds` just because the source CP is broader, appears earlier, introduces a chapter, or mentions a category that appears in the target CP. The source must provide a concrete structure that the target CP actually develops.

A broad vulnerability overview does not ground a specific sector risk. A chapter introduction does not ground later chapter details. A general statement that a sector is vulnerable to money laundering does not ground every risk in that sector.

Operational indicators, red flags, investigation support, or compliance controls usually do not ground taxonomy/definition CPs. Reject these unless the dependency is explicit.

Valid when:

- the source gives a concrete definition, classification, process framework, comparison base, or rule;
- the target applies, expands, operationalizes, compares, or specializes that exact definition/framework;
- the target would lose important structure if the source CP were removed.

Do not use when:

- the source is only a broad introductory background CP;
- the source is a general vulnerability overview without a clear taxonomy, process, rule, or named framework;
- the source only says a sector is vulnerable, risky, important, or commonly abused;
- the target is merely another consequence, risk, obligation, or control under the same broad domain;
- the source says "financial crime exists / has types" and the target discusses financial crime risks, consequences, obligations, or compliance in general.

Example accept:

```text
CH01 Money Laundering Definition and Predicate Crimes -> CH02 Predicate Crimes and FATF Categories
Reason: CH02 specializes the predicate-crime concept introduced in CH01.
```

Example accept:

```text
CH06 Unique vulnerabilities across banking services -> CH07 Commercial banking risks
Reason: CH06 gives a classification of banking services with distinct vulnerabilities; CH07 expands one classified service type.
```

Example accept:

```text
CH01 Three Stages of Money Laundering -> CH03 Money Laundering Process
Reason: CH01 provides the process framework; CH03 expands and applies that process.
```

Example reject:

```text
CH06 Financial services sector vulnerability overview -> CH07 Commercial banking risks
Reason: CH06 is a broad chapter introduction. It does not provide a concrete framework that CH07 directly develops.
```

Example reject:

```text
CH06 Banking sector is vulnerable to money laundering -> CH07 Retail banking risks
Reason: both discuss banking vulnerability, but the source is only a general vulnerability statement, not a classification, process, rule, or framework.
```

Example reject:

```text
CH06 Banking sector involvement in placement/layering/integration -> CH07 Retail or commercial banking risks
Reason: the three-stage laundering framework is concrete, but the target must directly organize or explain its risk discussion through placement/layering/integration. If the target only lists sector-specific risks such as remote onboarding, mule accounts, front companies, cash intensity, or monitoring difficulty, reject.
```

Example reject:

```text
CH06 General factors increasing banking vulnerability -> CH09 M&A risks
Reason: the factors are broad banking context; M&A risks are a different specific risk area and do not directly apply that factor list.
```

Example reject:

```text
CH09 Corporate banking vulnerability -> CH06 Corporate banking AFC program setup
Reason: risk context and controls are related, but the source does not provide a definition/framework/rule that the target directly expands.
```

Example reject:

```text
CH01 Definition and types of financial crime -> CH05 Types of Financial Crime Risks
Reason: CH01 is broad background. CH05's risk classification is not a direct application of CH01's definition/classification framework.
```

Example reject:

```text
CH01 Definition and types of financial crime -> CH04 Consequences of financial crime
Reason: CH04 consequences share the broad financial-crime domain but do not depend on CH01 as a concrete framework.
```

## contrasts

Use only when the two CPs are explicitly useful as a comparison or distinction across chapters.

Direction: choose the more general or earlier foundation CP as source when possible.

Reject instead of forcing `contrasts` if the pair is merely different topics.

Valid when:

- the two CPs form an explicit comparison, boundary, or distinction;
- reviewing one helps distinguish it from the other.

Do not use when:

- they are merely two different topics;
- they share a term but do not form a comparison.

Example accept:

```text
Terrorist financing vs. money laundering comparison -> Money laundering definition/process
Reason: the comparison depends on the distinction between the two concepts.
```

Relation priority:

```text
1. If source is a case/example and target is the directly demonstrated concept, use illustrates.
2. If source is a recap/key-takeaway and target is detailed treatment of the same specific topic, use summarizes.
3. If source provides a definition/framework/classification/process needed by target, use grounds.
4. If the relation is mainly a boundary or distinction, use contrasts.
5. If none of these are clearly true, reject.
```

Non-relation rules:

Return `none` if the pair is only:

1. Same broad topic, such as both mention financial crime, risk, ML, TF, fraud, or compliance.
2. Same method or term, such as shell company, crypto, TBML, hawala, red flags, sanctions, or KYC.
3. Same risk family without a direct review relationship.
4. Embedding-similar but not useful as a textbook review edge.
5. Better handled by P5 term/method indexing.
6. A general background CP is merely helpful context but not necessary foundation.

Additional calibration:

```text
Default reject: broad financial crime definition -> financial crime risks/consequences/obligations/compliance.
Default reject: money laundering definition -> any ML-related case/risk/control, unless the target directly expands the same definition/process/predicate-crime framework.
Default reject: predicate crime list -> any specific predicate crime case, unless the case directly demonstrates one listed category and is useful as a teaching example.
```

Output exactly one JSON object:

```json
{
  "batch_id": "p4_cross_chapter_probe_20260706",
  "decisions": [
    {
      "candidate_id": "p4cand_0001",
      "source_core_point_id": "cp_CH01_S05_002",
      "target_core_point_id": "cp_CH03_S05_002",
      "relation_type": "grounds",
      "decision": "accept",
      "reason": "CH01 provides the three-stage laundering framework; CH03 expands it in the laundering process discussion.",
      "risk_flags": []
    }
  ]
}
```

Use `decision = reject` and `relation_type = none` when the relation is not strong enough.

For accepted decisions, `source_core_point_id` and `target_core_point_id` must be one of the two CP IDs in the candidate pair. You may choose either direction. Do not invent CP IDs.

No markdown. No extra text.
