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

section_id: `CH08-S05`

section_title: `Private banking and wealth management risks > Special purpose vehicle risks`

section_text_with_unit_anchors:

```text
[v7u_N000642|642] Special purpose vehicles (SPVs) are legal entities created for specific and limited purposes.
ZH: 特殊目的载体（SPV）是为特定有限目的设立的法律实体

[v7u_N000643|643] SPVs can be used in mergers and acquisitions, joint ventures, real estate projects, infrastructure development, and energy projects.
ZH: SPV可用于并购、合资、房地产、基础设施和能源项目

[v7u_N000644|644] SPVs can also be used to manage and protect intellectual property assets including trademarks and copyrights.
ZH: SPV可用于管理和保护知识产权资产

[v7u_N000645|645] SPVs are often used in complex financial transactions and investments such as securities and asset-backed financing.
ZH: SPV常用于复杂金融交易和资产支持融资

[v7u_N000646|646] There are financial crime risks associated with SPVs.
ZH: SPV存在金融犯罪风险

[v7u_N000647|647] SPVs can have complex and opaque structures to disguise the true beneficial ownership.
ZH: SPV可能通过复杂不透明的结构掩盖真实受益所有人

[v7u_N000648|648] SPVs might be used to obscure the source of illicit funds. Criminals layer illicit proceeds through a series of transactions via the SPVs, transferring funds to or from financial institutions. This creates a complex web of
ZH: 犯罪分子通过SPV进行一系列交易来分层非法收益，掩盖资金来源

[v7u_N000649|649] There are several red flags that indicate attempts to disguise illicit funds or conduct fraudulent activities using SPVs. These include:
ZH: 列举利用SPV掩饰非法资金或欺诈活动的红旗信号信号

[v7u_N000650|650] Complex ownership structures involving multiple layers of companies
ZH: 涉及多层公司的复杂所有权结构是红旗信号

[v7u_N000651|651] Lack of transparency
ZH: 缺乏透明度是红旗信号

[v7u_N000652|652] Unclear purpose of the SPV
ZH: SPV目的不明确是红旗信号

[v7u_N000653|653] Criminals might select jurisdictions that have lenient regulatory oversight or tax-friendly environments. This enables them to hide their financial activities and minimize tax liabilities.
ZH: 犯罪分子选择监管宽松或税收优惠的司法管辖区以隐藏活动和避税

[v7u_N000654|654] Pooled investment vehicles (PIVs) are small investments pooled together from a large group of investors.
ZH: 集合投资工具（PIV）是从大量投资者汇集的小额投资

[v7u_N000655|655] PIVs can be used in Ponzi schemes and insider trading.
ZH: PIV可能被用于庞氏骗局和内幕交易

[v7u_N000656|656] Additionally, criminals might engage in trade-based money laundering using SPVs and PIVs. Criminals manipulate trade transactions between SPVs and PIVs by deflating or inflating prices.
ZH: 犯罪分子利用SPV和PIV进行贸易洗钱，操纵交易价格

[v7u_N000657|657] This process enables the movement of illicit funds while disguising it as legitimate trade activity.
ZH: 该过程将非法资金伪装成合法贸易活动进行转移

[v7u_N000658|658] Financial institutions must be vigilant in conducting enhanced due diligence (EDD) on SPVs and PIVs. It is important to ensure these investments comply with CDD regulations such as the Financial Crime Enforcement Network's CDD rule.
ZH: 金融机构必须对SPV和PIV进行强化尽职调查，遵守客户尽职调查规则

[v7u_N000659|659] Financial institutions must identify ultimate beneficial owners and understand the true purpose of these entities.
ZH: 金融机构必须识别最终受益所有人并了解实体真实目的

[v7u_N000660|660] This will help mitigate any potential financial crime risks associated with SPVs.
ZH: 这有助于减轻与SPV相关的金融犯罪风险
```
