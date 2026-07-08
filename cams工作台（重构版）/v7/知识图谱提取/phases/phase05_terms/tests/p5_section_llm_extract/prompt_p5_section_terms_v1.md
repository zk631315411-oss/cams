# Role

You extract a term dictionary from one CAMS textbook section.

# Scope

Extract only P5 dictionary information:

1. abbreviation <-> full form
2. Chinese <-> English
3. aliases / synonyms
4. occurrence evidence

Do not create core points. Do not create graph relations such as grounds, illustrates, summarizes, contains, prepares, or parallels. Do not explain the section.

# Input

You receive one section with unit-anchored English source text, Chinese summaries, and optional existing unit term hints.

# What To Extract

Extract terms that are useful for retrieval or review, especially:

- abbreviations: AML, CDD, PEP, SAR
- full forms: anti-money laundering, customer due diligence
- Chinese equivalents: 反洗钱, 客户尽职调查
- aliases and synonyms: suspicious activity report / suspicious transaction report where the section supports the connection
- laws, regulators, reports, roles, methods, typologies, systems, and key financial-crime concepts

Do not extract ordinary background words unless they are used as financial-crime, AML/CFT, compliance, regulation, typology, role, report, system, or control terms. Do not extract ordinary consequences such as education, health care, market share, bankruptcy, social isolation, or depression.

For long sections, prefer the most useful 8-20 dictionary entries instead of listing every noun phrase.

# Evidence Rules

Every extracted item must cite at least one unit_id from the input section.

Use the exact unit evidence. Do not cite a unit_id that is not in the input.

If the section text only mentions an abbreviation but does not explicitly give its full form, keep the abbreviation and leave full_forms empty unless the full form is provided by `terms_hint`.

Only put a value in `abbreviations` if that abbreviation literally appears in the section text or in `terms_hint`. If the text says `gross domestic product` but never says `GDP`, do not add `GDP`.

Use `evidence_type: "abbreviation_full_form"` only when the source text explicitly gives `full form (ABBR)` or `ABBR (full form)`.

Do not use outside knowledge to expand an abbreviation. Even if you know that GDP means gross domestic product, FIU means Financial Intelligence Unit, or SAR means suspicious activity report, mark the section evidence as `mention` unless this section explicitly expands it.

If the full form or Chinese equivalent is only available from the provided term hints, that is acceptable, but mark evidence_type as `term_hint`, not `abbreviation_full_form`.

Do not duplicate the same unit_id and evidence_type inside one term unless the evidence quotes are materially different.

Do not write self-corrections or reasoning inside JSON values. If you notice a possible issue, fix the JSON directly.

# Output JSON

Return one JSON object only:

```json
{
  "section_id": "CHxx-Sxx",
  "section_title": "...",
  "terms": [
    {
      "canonical_en": "anti-money laundering",
      "canonical_zh": "反洗钱",
      "abbreviations": ["AML"],
      "full_forms": ["anti-money laundering"],
      "aliases_en": [],
      "aliases_zh": [],
      "term_type": "concept",
      "occurrences": [
        {
          "unit_id": "v7u_N000001",
          "evidence_type": "abbreviation_full_form|translation|alias|mention|term_hint",
          "evidence_quote": "short exact quote or term hint"
        }
      ],
      "confidence": "high|medium|low",
      "notes": "brief reason, max 20 words"
    }
  ],
  "review_flags": []
}
```

Bad output when only the source text says `AFC` and the full form comes from term hints:

```json
{"unit_id": "v7u_N000004", "evidence_type": "abbreviation_full_form", "evidence_quote": "Joyce works in the AFC department"}
```

Also bad:

```json
{"unit_id": "v7u_N000019", "evidence_type": "abbreviation_full_form", "evidence_quote": "AML prosecutions"}
```

```json
{"unit_id": "v7u_N000285", "evidence_type": "abbreviation_full_form", "evidence_quote": "FIUs synthesized bank SARs"}
```

```json
{"unit_id": "v7u_N000293", "evidence_type": "abbreviation_full_form", "evidence_quote": "global gross domestic product, or US$2 trillion"}
```

```json
{"canonical_en": "gross domestic product", "abbreviations": ["GDP"]}
```

Reason: `AML prosecutions` mentions the abbreviation, but it does not expand AML in the source text.

Good output for the same case:

```json
{"unit_id": "v7u_N000004", "evidence_type": "mention", "evidence_quote": "Joyce works in the AFC department"}
```

```json
{"unit_id": "v7u_N000019", "evidence_type": "mention", "evidence_quote": "AML prosecutions"}
```

```json
{"canonical_en": "gross domestic product", "abbreviations": [], "occurrences": [{"unit_id": "v7u_N000293", "evidence_type": "mention", "evidence_quote": "global gross domestic product"}]}
```

and, if using the hint:

```json
{"unit_id": "v7u_N000004", "evidence_type": "term_hint", "evidence_quote": "anti-financial crime / 金融犯罪防控"}
```

# Examples

Input evidence:

```text
[v7u_N000164|164] The Common Reporting Standard (CRS), developed ... by the OECD (Organization for Economic Cooperation and Development) Council...
```

Good output terms:

```json
{
  "canonical_en": "Common Reporting Standard",
  "canonical_zh": "",
  "abbreviations": ["CRS"],
  "full_forms": ["Common Reporting Standard"],
  "aliases_en": [],
  "aliases_zh": [],
  "term_type": "standard",
  "occurrences": [{"unit_id": "v7u_N000164", "evidence_type": "abbreviation_full_form", "evidence_quote": "The Common Reporting Standard (CRS)"}],
  "confidence": "high",
  "notes": "explicit full form and abbreviation"
}
```

```json
{
  "canonical_en": "Organization for Economic Cooperation and Development",
  "canonical_zh": "",
  "abbreviations": ["OECD"],
  "full_forms": ["Organization for Economic Cooperation and Development"],
  "aliases_en": [],
  "aliases_zh": [],
  "term_type": "organization",
  "occurrences": [{"unit_id": "v7u_N000164", "evidence_type": "abbreviation_full_form", "evidence_quote": "OECD (Organization for Economic Cooperation and Development)"}],
  "confidence": "high",
  "notes": "explicit abbreviation and full form"
}
```

Input evidence:

```text
[v7u_N000035|35] ... weak AML/CFT regulations.
```

Good output:

```json
{
  "canonical_en": "AML/CFT",
  "canonical_zh": "",
  "abbreviations": ["AML/CFT"],
  "full_forms": [],
  "aliases_en": [],
  "aliases_zh": [],
  "term_type": "compound_abbreviation",
  "occurrences": [{"unit_id": "v7u_N000035", "evidence_type": "mention", "evidence_quote": "weak AML/CFT regulations"}],
  "confidence": "medium",
  "notes": "section mentions the abbreviation but does not expand it"
}
```
