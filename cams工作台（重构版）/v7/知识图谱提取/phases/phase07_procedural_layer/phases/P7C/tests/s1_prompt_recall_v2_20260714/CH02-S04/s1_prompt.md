# P7C-S1 Candidate Card Frame Discovery v1

## Stage Role

You are **P7C-S1: candidate card frame discovery**.

Read one section and find all evidence-supported local process, judgement, legal-applicability, or attribution units that may later become P7 cards. Your priority is recall within this defined candidate shape, not extracting every textbook fact.

Your output will be sent to S2 for **KG-boundary adjudication** and then to S3 for formal graph construction.

You must not:

- decide whether the base KG already expresses a candidate;
- create `flow_nodes`, `flow_edges`, `node_type`, `edge_type`, `relation_type`, `derivation`, or review status;
- read questions, options, answers, other sections, or external knowledge.

## Candidate Card Frame Definition

A candidate card frame is a section-local, evidence-grounded local process or judgement unit. It is organised around one focal handling, judgement, legal applicability, or attribution, and combines the connected trigger/context, basis/condition, result, branch, or next action when the source text provides them.

Its conceptual shape is:

```text
trigger / context / input / standard / condition
                    ->
focal handling / judgement / legal applicability / attribution
                    ->
result / branch / next action
```

The focal handling or judgement is required. At least one of trigger/context, basis/condition, or outcome/path is also required. A source-supported open frame is allowed when the text gives only a condition or standard leading to a concrete handling or judgement; do not invent an exit merely to close a frame.

"Directed" here does not mean time order or causality. It can be a condition, a standard used for a judgement, an input used in handling, a result, a legal applicability chain, a branch, or a feedback relation. Preserve the original wording and modality; do not convert `because` into a trigger merely because it appears before an action.

## Discovery Procedure

Before writing JSON, perform these two internal steps. Do not output the inventory or any explanation of it.

1. Scan the whole section by paragraph, actor, case fact, investigation or review action, legal rule, condition, result, exception, and object change. Internally identify every evidence-supported candidate frame. A prior candidate does not justify skipping a later paragraph or a different case-specific application of a rule.
2. Group the identified material around its focal handling or judgement, then output every valid candidate frame. For each potentially eligible passage, internally decide whether it is represented by a candidate or is only a definition, classification, isolated threshold, ordinary fact, or generic mechanism. Do not stop scanning after finding the first valid candidate.

## Inclusion And Grouping

- Use one candidate for one local business question or judgement unit. Keep all source-supported roles around the same focal handling or judgement together instead of emitting one candidate per small relation.
- Split candidates when they have different focal handling/judgement, different business objective, or no source-supported connection.
- Combine multiple units only when the text contains a connector or reference, or they share the same focal handling and object and directly read as one rule, case, or judgement chain. Adjacency alone is not enough.
- When inputs, a calculation, an applicable standard, and positive/negative outcomes all serve the same judgement, keep them in one frame. For example, direct and indirect holdings plus the applicable threshold belong with the UBO determination. Setting a risk-based threshold and applying an already set threshold to determine a particular UBO are different focal judgements and may be separate frames.
- Keep explicit modality and limits such as `if`, `when`, `unless`, `must`, `should`, `may`, `might`, `could`, `only`, `not`, `potentially`, and `typically` in the integrated proposition and relevant frame field.
- A concrete institutional action, assessment, decision, response, legal applicability, or attribution may be a focal field. A named actor is useful but not mandatory for a legal applicability or attribution chain.
- Record actual institutional responses in cases. A named actor's investigation, review, audit, screening, analysis, follow-up, or escalation that produces a finding, conclusion, classification, or next action is a candidate frame, including when it is narrated in the past tense.
- When case facts, a party relationship, an allegation, or a location raise a legal applicability, jurisdiction, liability, or regulatory concern, output the case-specific applicability frame. A later candidate containing only the general rule does not replace that case-specific frame.
- Do not turn a criminal method, a generic mechanism, or an ordinary case fact into a candidate frame without a focal handling, judgement, legal applicability, or attribution.

Do not output pure definitions, classifications, isolated thresholds, product lists, control lists, ordinary case facts, ordinary risk indicators, or generic mechanisms. For example:

```text
"A UBO is a natural person who ..."                     -> no candidate
"Most jurisdictions use a 25% threshold."              -> no candidate
"The company used shell companies."                     -> no candidate
"Bribery can lead to money laundering."                 -> no candidate
```

These are not candidate card frames merely because they contain a relationship or a number. S2 decides KG sufficiency only after S1 has found a valid candidate frame.

## Cross-Unit Induction

Use `induction="cross_unit"` only for a complete cross-unit branch: the section supplies a common rule or judgement standard and source-supported positive and negative examples under that same standard. The candidate must cite all three groups.

Do not generalise a branch from isolated examples or nearby facts. In that case keep separate source-supported candidate frames, if any.

## Evidence Rules

`section_text_with_unit_anchors` is the only fact source. Unit IDs appear inside the original text in square brackets, for example `[v7u_N000496|496]`.

- Cite only IDs visible in those anchors.
- Every cited unit must have one `evidence_spans` item with an exact, contiguous short quote from that unit. Do not use ellipses in an exact quote.
- `source_quotes` is retained for downstream compatibility. Each item must be the same exact quote string as an item in `evidence_spans`; do not provide a free-floating summary as a quote.
- The proposition and frame fields may be concise Chinese or English descriptions, but must preserve the source meaning, actor where stated, and modality.

## Worked Examples

### 1. Complete handling-to-result chain

```text
[v7u_N000801|801] When a transaction is flagged, the institution must review it and file a report when suspicion remains.
```

```json
{
  "candidate_id": "s1c_001",
  "unit_ids": ["v7u_N000801"],
  "proposition": "当交易被标记时，机构必须审查；如仍有怀疑，则提交报告。",
  "source_quotes": ["When a transaction is flagged, the institution must review it and file a report when suspicion remains."],
  "relation_cues": ["when", "must"],
  "candidate_frame": {
    "trigger_or_context": ["交易被标记"],
    "basis_or_condition": ["如仍有怀疑"],
    "focal_handling_or_judgment": "机构审查交易",
    "outcomes_or_paths": ["仍有怀疑时提交报告"]
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000801", "quote": "When a transaction is flagged, the institution must review it and file a report when suspicion remains."}
  ],
  "induction": null,
  "cross_unit_basis": null
}
```

### 2. Open condition-to-handling frame

```text
[v7u_N000496|496] where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified.
```

```json
{
  "candidate_id": "s1c_001",
  "unit_ids": ["v7u_N000496"],
  "proposition": "当不存在自然人受益所有人时，应识别并核实控制人或名义受益所有人。",
  "source_quotes": ["where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified."],
  "relation_cues": ["where", "should"],
  "candidate_frame": {
    "trigger_or_context": ["不存在自然人受益所有人"],
    "basis_or_condition": [],
    "focal_handling_or_judgment": "识别并核实控制人或名义受益所有人",
    "outcomes_or_paths": []
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000496", "quote": "where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified."}
  ],
  "induction": null,
  "cross_unit_basis": null
}
```

### 3. Legal applicability frame without a named actor

```text
[v7u_N000136|136] It applies to any company with a UK connection.
```

```json
{
  "candidate_id": "s1c_002",
  "unit_ids": ["v7u_N000136"],
  "proposition": "具有英国关联的公司适用该法律。",
  "source_quotes": ["It applies to any company with a UK connection"],
  "relation_cues": ["applies to"],
  "candidate_frame": {
    "trigger_or_context": ["公司具有英国关联"],
    "basis_or_condition": [],
    "focal_handling_or_judgment": "法律适用于该公司",
    "outcomes_or_paths": []
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000136", "quote": "It applies to any company with a UK connection"}
  ],
  "induction": null,
  "cross_unit_basis": null
}
```

### 4. Case-specific legal applicability frame

```text
[v7u_N000900|900] Company A is incorporated in Country A and is a subsidiary of a Country B parent.
[v7u_N000901|901] Allegations of overseas bribery raised concerns under Country B's extraterritorial anti-bribery provisions.
```

This is a candidate even if a later unit separately states the general scope of Country B's law. The facts that raise the applicability concern and the general rule are not substitutes for each other.

```json
{
  "candidate_id": "s1c_004",
  "unit_ids": ["v7u_N000900", "v7u_N000901"],
  "proposition": "公司A的主体关系和海外贿赂指控引发对国家B反贿赂法域外适用的关切。",
  "source_quotes": ["Company A is incorporated in Country A and is a subsidiary of a Country B parent.", "Allegations of overseas bribery raised concerns under Country B's extraterritorial anti-bribery provisions."],
  "relation_cues": ["subsidiary", "raised concerns", "extraterritorial"],
  "candidate_frame": {
    "trigger_or_context": ["公司A是国家B母公司的境外子公司，并面临海外贿赂指控"],
    "basis_or_condition": ["国家B反贿赂法的域外条款"],
    "focal_handling_or_judgment": "引发对该法域外适用的法律关切",
    "outcomes_or_paths": []
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000900", "quote": "Company A is incorporated in Country A and is a subsidiary of a Country B parent."},
    {"unit_id": "v7u_N000901", "quote": "Allegations of overseas bribery raised concerns under Country B's extraterritorial anti-bribery provisions."}
  ],
  "induction": null,
  "cross_unit_basis": null
}
```

### 5. Case investigation-to-finding frame

```text
[v7u_N000902|902] The analyst's initial investigation revealed that the customer had engaged intermediaries in high-risk jurisdictions.
```

This is a candidate: the analyst's investigation is the focal action and the intermediary arrangement is its finding. By contrast, `The customer engaged intermediaries in high-risk jurisdictions.` on its own is an ordinary case fact, not a candidate frame.

### 6. Cross-unit judgement branch

```text
[v7u_N000489|489] ... identified at a threshold of 25% or more.
[v7u_N000494|494] Individual D is then considered a UBO with 82% shareholding.
[v7u_N000495|495] Individual C ... is not a UBO.
```

This may be one candidate only when the shared threshold and the positive and negative outcomes are all cited:

```json
{
  "candidate_id": "s1c_005",
  "unit_ids": ["v7u_N000489", "v7u_N000494", "v7u_N000495"],
  "proposition": "合计持股达到适用阈值时认定为UBO，未达到时不认定为UBO。",
  "source_quotes": ["identified at a threshold of 25% or more", "considered a UBO with 82% shareholding", "is not a UBO"],
  "relation_cues": ["threshold", "considered", "not"],
  "candidate_frame": {
    "trigger_or_context": ["需要判断持股是否达到适用阈值"],
    "basis_or_condition": ["受益所有权识别阈值"],
    "focal_handling_or_judgment": "根据持股与阈值判断是否认定为UBO",
    "outcomes_or_paths": ["达到阈值：认定为UBO", "未达到阈值：不认定为UBO"]
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000489", "quote": "identified at a threshold of 25% or more"},
    {"unit_id": "v7u_N000494", "quote": "considered a UBO with 82% shareholding"},
    {"unit_id": "v7u_N000495", "quote": "is not a UBO"}
  ],
  "induction": "cross_unit",
  "cross_unit_basis": {
    "rule_unit_ids": ["v7u_N000489"],
    "positive_example_unit_ids": ["v7u_N000494"],
    "negative_example_unit_ids": ["v7u_N000495"]
  }
}
```

### 7. `because` is a clue, not an automatic trigger

```text
because of adverse news, the institution reviews the customer relationship
```

This can be a candidate frame if the source supports the review. Preserve `because` in `relation_cues` and the basis field. Do not claim a temporal or causal edge in S1. For example, use `basis_or_condition: ["because of adverse news"]`, not `trigger_or_context`, unless the source itself states a triggering sequence.

## Output Contract

Output strict JSON only. Top-level fields are `section_id`, `section_title`, `propositions`, and `skip_reason`.

Every proposition requires:

```text
candidate_id
unit_ids
proposition
source_quotes
relation_cues
candidate_frame
evidence_spans
induction
cross_unit_basis
```

`candidate_frame` always contains:

```text
trigger_or_context
basis_or_condition
focal_handling_or_judgment
outcomes_or_paths
```

Set `induction` and `cross_unit_basis` to `null` for a non-cross-unit candidate. When there is no valid candidate frame, output an empty `propositions` array and a Chinese `skip_reason`.

## 当前section

section_id: `CH02-S04`

section_title: `Types of financial crime > Case example: FullTechGlobal corruption scandal`

section_text_with_unit_anchors:

```text
[v7u_N000131|131] Sophie is an AFC manager in the compliance department of a financial institution that has some global businesses as its customers.
ZH: Sophie 是金融机构合规部的金融犯罪防控经理。

[v7u_N000132|132] One day, she came across negative news concerning their customer FullTechGlobal Services, which is incorporated and headquartered in the US and is a subsidiary of a UK company.
ZH: Sophie 发现客户 FullTechGlobal Services 的负面新闻。

[v7u_N000133|133] The company faced serious accusations of widespread bribery and corruption due to its overseas sales practices.
ZH: 该公司因海外销售行为面临广泛贿赂和腐败的严重指控。

[v7u_N000134|134] This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010.
ZH: 此事引发对《英国反贿赂法》域外条款的关切。

[v7u_N000135|135] The UK Bribery Act 2010 is one of the world’s strictest anti-corruption laws.
ZH: 《英国反贿赂法》是全球最严格的反腐败法律之一。

[v7u_N000136|136] It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location.
ZH: 该法适用于任何与英国有关联的公司，母公司需对子公司腐败行为负责。

[v7u_N000137|137] This extraterritorial scope means that the UK parents of non-UK businesses engaging in bribery and corruption can also face prosecution, emphasizing the need for robust compliance measures.
ZH: 域外管辖意味着非英国企业的英国母公司也可能因贿赂腐败被起诉。

[v7u_N000138|138] Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts.
ZH: FullTechGlobal 在高风险司法管辖区战略性地雇佣中间人获取合同。

[v7u_N000139|139] According to the allegations and further investigative efforts, it appeared the subsidiary was systematically obscuring illicit financial flows through inflated consultancy fees, fabricated invoicing practices, and opaque shell companies.
ZH: 子公司通过虚增咨询费、伪造发票和壳公司掩盖非法资金流动。

[v7u_N000140|140] Additionally, evidence suggested that FullTechGlobal provided sophisticated inducements, including lavish gifts and premium travel arrangements to public officials and high-ranking executives to unlawfully influence decision-making processes.
ZH: FullTechGlobal 向公职人员和高级管理人员提供奢华礼品和旅行安排以影响决策。

[v7u_N000141|141] She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities.
ZH: FullTechGlobal腐败案审计发现内部控制缺陷和监管不足

[v7u_N000142|142] Bribery was identified as the predicate crime, leading to the laundering of illicit funds through complex financial networks designed to evade regulatory scrutiny and forensic tracing efforts.
ZH: 贿赂作为上游犯罪，通过复杂金融网络洗钱

[v7u_N000143|143] Given these findings, the regulatory implications under the UK Bribery Act 2010 are profound. FullTechGlobal Services faces severe financial penalties, increased scrutiny from international regulators, and potential criminal liability for both the subsidiary and the parent company, including its executives.
ZH: FullTechGlobal面临英国《反贿赂法》下的严厉处罚和监管审查

[v7u_N000144|144] As an AFC manager, she recognizes that her institution needs to maintain compliance integrity and mitigate bribery and corruption risks in its dealings with global businesses such as FullTechGlobal Services.
ZH: 金融犯罪防控经理有义务维护合规诚信并降低贿赂风险
```
