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

## Inclusion And Grouping

Scan the complete section by paragraph, change of actor, object, condition, standard, result, and exception.

- Use one candidate for one local business question or judgement unit. Keep all source-supported roles around the same focal handling or judgement together instead of emitting one candidate per small relation.
- Split candidates when they have different focal handling/judgement, different business objective, or no source-supported connection.
- Combine multiple units only when the text contains a connector or reference, or they share the same focal handling and object and directly read as one rule, case, or judgement chain. Adjacency alone is not enough.
- Keep explicit modality and limits such as `if`, `when`, `unless`, `must`, `should`, `may`, `might`, `could`, `only`, `not`, `potentially`, and `typically` in the integrated proposition and relevant frame field.
- A concrete institutional action, assessment, decision, response, legal applicability, or attribution may be a focal field. A named actor is useful but not mandatory for a legal applicability or attribution chain.
- Record actual institutional responses in cases. Do not turn a criminal method, a generic mechanism, or an ordinary case fact into a candidate frame without a focal handling, judgement, legal applicability, or attribution.

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

### 4. Cross-unit judgement branch

```text
[v7u_N000489|489] ... identified at a threshold of 25% or more.
[v7u_N000494|494] Individual D is then considered a UBO with 82% shareholding.
[v7u_N000495|495] Individual C ... is not a UBO.
```

This may be one candidate only when the shared threshold and the positive and negative outcomes are all cited:

```json
{
  "candidate_id": "s1c_003",
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

### 5. `because` is a clue, not an automatic trigger

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

section_id: `CH06-S10`

section_title: `Money Laundering Risks in Financial Services > Control and ownership for AML compliance`

section_text_with_unit_anchors:

```text
[v7u_N000483|483] Control and ownership play a vital role in AML efforts, as they can often be obscured or concealed, allowing bad actors to disguise criminal activities and facilitate financial crime.
ZH: 控制权和所有权在反洗钱工作中至关重要

[v7u_N000484|484] A beneficial owner (BO) is defined as an individual or entity that possesses ownership of a legal entity, either through shareholding or other means.
ZH: 受益所有人（BO）的定义：通过持股或其他方式拥有法律实体的个人或实体

[v7u_N000485|485] In contrast, the ultimate beneficial owner (UBO) refers specifically to one or more natural persons who ultimately owns a substantial percentage of shareholding.
ZH: 最终受益所有人（UBO）的定义：最终持有重大比例股份的自然人

[v7u_N000486|486] It is important to note that a BO might appear to have ownership of a company but might not control the company. Conversely, a UBO might not directly hold shares but does exert ultimate control over it.
ZH: BO 可能拥有所有权但不控制公司，UBO 可能不直接持股但实施最终控制

[v7u_N000487|487] This distinction is crucial when it comes to regulatory requirements surrounding ownership structures.
ZH: BO 与 UBO 的区别对所有权结构的监管要求至关重要

[v7u_N000488|488] When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer.
ZH: 监管要求审查所有权结构时必须识别客户的 UBO

[v7u_N000489|489] For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more. That means you need to know every entity or individual who owns at least 25% of a customer.
ZH: 多数司法管辖区要求识别持股 25% 或以上的受益所有人

[v7u_N000490|490] Your organization will set the appropriate threshold using a riskbased approach.
ZH: 机构应采用风险为本的方法设定受益所有权阈值

[v7u_N000491|491] For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5% for customers who pose a significantly higher risk.
ZH: 高风险客户的受益所有人阈值可能低至 10% 甚至 5%

[v7u_N000492|492] For example, high-risk financial institutions with correspondent banking relationships in a high-risk jurisdiction might set their threshold at 5%.
ZH: 示例：高风险司法管辖区的代理行关系可能设定 5% 的阈值

[v7u_N000493|493] In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership.
ZH: 识别 UBO 需要同时考虑直接和间接持股

[v7u_N000494|494] Individual D owns 10% of Company A directly. They also own 72% of Company A indirectly, as they own 90% of shares of Company B, which owns 80% of Company A. Individual D is then considered a UBO with 82% shareholding of Company A.
ZH: 示例：个人 D 通过直接和间接持股合计 82%，成为 UBO

[v7u_N000495|495] Individual C, who owns 10% of Company A directly and an additional 8% indirectly via their 10% ownership of Company B, is not a UBO.
ZH: 示例：个人 C 直接持股 10% 加间接持股 8%，未达到 UBO 标准

[v7u_N000496|496] In companies where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified. This allows you to understand who is in control of the decision-making in the company when natural individual UBOs are not present.
ZH: 无自然人受益所有人时，应识别并核实控制人或名义受益所有人

[v7u_N000497|497] For example, for a company that is publicly listed on the stock exchange and has thousands of shareholders, a notional beneficial owner could be the president or chief executive officer, or equivalent.
ZH: 示例：上市公司可将总裁或 CEO 作为名义受益所有人
```
