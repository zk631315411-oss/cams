# Retrieval log

Date: 2026-07-07

## API attempts

### Semantic Scholar

Tried anonymous Graph API keyword searches, including:

- `elaborated feedback multiple choice test learning`
- `feedback enhances positive effects reduces negative effects multiple choice testing`
- `Focus on formative feedback Shute 2008`
- `The instructional effect of feedback in test-like events`
- `retrieval practice feedback multiple choice learning medical education`
- `worked examples self explanation learning transfer cognitive load`

Result: HTTP 429 Too Many Requests. No Semantic Scholar metadata was used as verified input in this pass.

### OpenAlex

Tried anonymous keyword searches, including:

- `multiple choice feedback distractor explanations learning`
- `elaborated feedback answer until correct multiple choice`
- `diagnostic feedback misconceptions learning feedback explanation`
- `cognitive load feedback complexity learning explanations`
- `self explanation worked examples transfer learning review`
- `exam preparation feedback explanations test taking strategy learning`

Result: anonymous search was rate-limited under elevated load. One request also showed that `host_venue` is no longer a valid `select` field; future scripts should use current OpenAlex fields such as `primary_location`, `sources`, or full results without the obsolete selector.

### Crossref

Used Crossref for DOI lookup and bibliographic search. Crossref provided the majority of verified metadata in `candidate_sources.json`.

## Included source families

- Feedback frameworks and meta-analyses: Hattie & Timperley; Shute; Kluger & DeNisi; Wisniewski et al.; Van der Kleij et al.; Nicol & Macfarlane-Dick.
- Test-like and multiple-choice feedback: Bangert-Drowns et al.; Kulik & Kulik; Butler & Roediger; Butler et al.; Mertens & Lindner; Slepkov & Godfrey.
- Retrieval practice and transfer: Roediger & Karpicke; Butler; Rowland; Adesope et al.; Pan & Rickard; Dunlosky et al.
- Worked examples and self-explanation: Chi et al.; Atkinson et al.; Renkl.
- Cognitive load: Sweller; Sweller et al.; Paas et al.

## Excluded or downgraded items

The following hits were excluded or not promoted because they were unrelated, returned mismatched metadata, or were not directly useful for s6 explanation design:

- `10.1016/j.cedpsych.2006.08.001`: Crossref returned a gifted-class/gender-ratio article, not a relevant feedback/cognitive-load source for s6.
- `10.1207/s1532690xci1803_3`: returned a science epistemology article, not a feedback/explanation design source.
- `10.1016/j.edurev.2007.10.001`: returned a teacher-career review, unrelated to s6.
- `10.1037/0022-0663.92.1.205`: DOI lookup returned 404 in this pass.
- `10.1007/s10648-010-9133-4`: DOI lookup returned 404 in this pass.
- `10.1177/0963721412438669`: DOI lookup returned 404 in this pass.
- Broad exam-preparation hits such as professional exam manuals were excluded because they were not evidence about learner-facing explanation design.
- Distractor-generation papers were excluded unless they addressed learner feedback, because s6 is about explanation writing, not item generation.

## Next retrieval gaps

- Search Chinese-language literature on exam-oriented learners only if it addresses feedback,错题复盘,答案解析, or practice-question review, not just general 应试教育 critique.
- Search domain-adjacent medical/accounting/compliance exam education literature for MCQ explanation practices.
- Read full text for the strongest 8-10 sources before turning these notes into a final s6 prompt specification.
