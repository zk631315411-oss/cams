# Search strategy

Date: 2026-07-07

## Research question

What kinds of feedback and explanation features best support exam-oriented learners during practice-question review, especially for improving correctness, error diagnosis, and transfer to similar items?

## Search posture

This scan is intended to support product/design work for s6, not to produce a publication-grade systematic review. The search therefore combines:

- DOI verification of known seminal sources.
- Keyword search for directly relevant feedback/explanation literature.
- Screening against s6 needs: practice questions, multiple-choice options, distractors, diagnosis of wrong choices, transfer to similar items, and explanation length/complexity.

## Databases and APIs

- Crossref REST API: DOI lookup and bibliographic query.
- Semantic Scholar Graph API: attempted for keyword search; anonymous calls returned HTTP 429 during this pass.
- OpenAlex REST API: attempted for keyword search; anonymous calls returned rate-limit responses during this pass. One query also exposed an outdated field name (`host_venue`), so future scripts should use `primary_location`/`sources` fields.

## Inclusion criteria

- Peer-reviewed review, meta-analysis, theoretical framework, or experiment related to feedback, testing, retrieval practice, worked examples, self-explanation, or cognitive load.
- Direct relevance to one or more s6 explanation design decisions: answer feedback, explanatory feedback, option-level feedback, transfer rules, diagnostic feedback, or brevity/detail tradeoff.
- Seminal older sources were included when they define a core mechanism or design principle.

## Exclusion criteria

- Sources focused only on item generation or distractor generation without learner-facing feedback design.
- Professional exam-prep manuals without research evidence.
- Search hits whose DOI metadata did not match the intended title.
- Grants, datasets, standards, book front matter, or unrelated works returned by broad keyword queries.

## Search strings used

- `elaborated feedback multiple choice test learning`
- `feedback enhances positive effects reduces negative effects multiple choice testing`
- `Focus on formative feedback Shute 2008`
- `The instructional effect of feedback in test-like events`
- `retrieval practice feedback multiple choice learning medical education`
- `worked examples self explanation learning transfer cognitive load`
- `multiple choice feedback distractor explanations learning`
- `elaborated feedback answer until correct multiple choice`
- `diagnostic feedback misconceptions learning feedback explanation`
- `cognitive load feedback complexity learning explanations`
- `self explanation worked examples transfer learning review`
- `exam preparation feedback explanations test taking strategy learning`
- `Self-explanations how students study and use examples in learning to solve problems`
- `Learning from examples instructional principles from the worked examples research Atkinson Derry Renkl Wortham`
- `instructional explanations support learning by self explanations Renkl worked-out examples`
- `The Power of Testing Memory Basic Research and Implications for Educational Practice Roediger Karpicke 2006`
- `Ten Benefits of Testing and Their Applications to Educational Practice Roediger`
- `feedback and self regulated learning Nicol Macfarlane-Dick 2006`

## Screening result

Included source families:

- Feedback theory and meta-analysis.
- Feedback in test-like and multiple-choice settings.
- Explanation feedback and transfer.
- Retrieval practice and practice testing.
- Worked examples and self-explanation.
- Cognitive load and explanation complexity.
- Self-regulated learning and feedback use.

Known limitations:

- Semantic Scholar and OpenAlex anonymous search were rate-limited, so Crossref carried most of the metadata verification.
- This pass did not perform full-text reading.
- Chinese-language exam-oriented learning literature was not yet searched; it may be useful later, but the first pass intentionally prioritized evidence on feedback/explanation design rather than general criticism of exam-oriented education.
