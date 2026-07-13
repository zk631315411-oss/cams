# P7C Section Judgement Card Extraction Prompt v1

## Role

You are a P7C section-local evidence-matching judgement card extractor.

Read one textbook section and extract zero or more `p7_card` objects. Each card must help a later system judge whether a question option, business handling, risk response, control, or assessment is consistent with CAMS requirements. The source of truth is `flow_nodes` + `flow_edges`.

## Boundary

Only use the current section.

Do not create `BRIDGES_TO`, clusters, scenario paths, explanations, Mermaid, draw.io, SVG, or PNG.

If the section contains no executable process, no assessment standard, no control requirement, no risk-indicator rule, and no discouraged practice useful for judging business handling or exam options, return an empty `cards` array and a concise `skip_reason`.

## Reading Order

Read `section_text_with_unit_anchors`. It is the only extraction source and contains unit anchors such as:

```text
[v7u_N003233|3233] Transaction monitoring systems generate alerts...
```

Use these `unit_id` values as evidence anchors. The `allowed_unit_ids` list is only a whitelist for evidence IDs.

Do not use core points, CP-unit edges, CP-CP edges, alias metadata, KG edges, or package-level summaries to infer card structure. If a card cannot be extracted from the section text itself, return no cards or mark the uncertain part as `needs_review`.

## Evidence-Matching Goal

The cards will be used later to match exam questions and options against textbook evidence. Therefore, a useful card is not only a workflow. It may also preserve:

```text
what situation or condition the section is talking about
what action, control, assessment, or judgement is expected
what standards, criteria, indicators, limits, or components must be considered
what output, effect, risk finding, deficiency, or consequence follows
what practice is discouraged, insufficient, or harmful
```

When deciding whether to extract, ask: could this section help judge whether an answer option is correct, incorrect, too broad, too narrow, or missing a condition? If yes, extract a card unless the evidence is too vague to model.

When a section contains several locally useful judgement units, do not extract only the final or most normative paragraph. Scan the whole section and preserve each distinct unit that would support a different option judgement. For example, a technology section may contain both: `technology capability used to detect risk patterns` and `controls required when implementing AI`. These may be separate cards if they have different triggers, standards, and outputs.

Technology capability material is useful when it states what a system checks, detects, identifies, analyzes, reduces, improves, or enables. Do not skip such material merely because it is descriptive. If the source describes a monitoring capability with its inputs, criteria, or expected detection effect, extract it as a `control`, `assessment`, or `risk_indicator` card. Model the capability as a `process` node, the checked criteria or data features as `standard` or `input` nodes, and the detection/improvement effect as an X-prefix `exit` node.

## Extraction Scope

Extract a card only when the section provides at least one of these useful judgement structures:

```text
execution       what to do, in what order, and with what branch or output
assessment      how to judge, evaluate, screen, or determine a result
control         what control or governance requirement applies and what effect it should have
risk_indicator  what risk factor, red flag, or warning indicator should be used to identify elevated risk
```

Do not limit extraction to strict chronological processes. However, do not convert non-chronological judgement material into a fake sequence.

Use this default structure when the source is not a strict execution process:

```text
assessment:     entry node -> P1_assessment --REFERENCES--> parallel standards -> X1_classification or other exit
control:        entry node -> process/control handling --REFERENCES--> inputs or standards -> X2_product, X3_state_change, or X7_continuing_obligation
risk_indicator: entry node -> P1_assessment --REFERENCES--> parallel indicators -> X1_classification
```

Before skipping, check whether the section contains any of the following:

```text
a control effectiveness requirement or expected control effect
an assessment or judgement standard
a risk indicator, red flag, or risk factor
an anti-pattern, discouraged practice, or negative consequence
a control-overreach, access barrier, financial-inclusion tradeoff, or risk-based balancing rule
a condition or trigger that changes the required handling
a business response useful for evaluating an exam option
```

If any item is present, do not skip. Extract the smallest useful `assessment`, `control`, or `risk_indicator` card. Use `review_status: "needs_review"` when the material is useful but not a strict process.

Skip purely descriptive background, isolated examples, technology capability descriptions, definitions, or historical notes only when they provide no judgement rule, control requirement, risk indicator, condition, limitation, or option-evaluation value.

Definitions may be extracted when they define a condition, threshold, control component, prohibited/discouraged pattern, or judgement category useful for evidence matching. Technology or control capability descriptions should be extracted when they state what the control should achieve, what it checks or detects, which criteria or data features it uses, how it should be tuned or reviewed, when it should be reassessed, or what its limitations are.

Financial inclusion, de-risking, and strict-control barrier material may be extracted when it helps judge whether a control response is proportionate, risk-based, or overly restrictive. Model the control burden or barrier as a standard or output, and the desired balanced handling as an assessment/control objective. Do not skip it merely because it is policy-oriented rather than a step-by-step process.

Examples may support `description` or `source_quote`, but do not promote an example into the main flow unless the section presents it as a required or generally applicable handling rule.

## Card Granularity

One card = one section-local, locally closed judgement unit with one primary objective.

A card should have:

```text
an entry point
a set of actions, decisions, standards, controls, or indicators
a clear output, stable result, or handoff point
```

Prefer fewer, clearer cards. Do not force a card when the section only defines concepts and gives no business-handling judgement value.

Split a section into multiple cards when it contains separate local process objectives that can each stand on their own. A common case is:

```text
primary assessment flow
remediation or corrective-action subflow
```

For example, an assessment/result-calculation flow and a remediation/corrective-action workflow may be separate cards if each has its own entry, decision point, and output.

Another common case is an optional preliminary path plus a main process. For example, a pre-onboarding committee suitability assessment for specific customer profiles should usually be a separate card from the typical KYC/CDD process if both have their own entry, decision, and output.

Another common case is capability-plus-control material. Extract separate cards when the source first describes what a monitoring/control capability is used for and later describes the controls, limitations, or safeguards for implementing that capability.

For technology capability cards, prefer one card per local capability family, not one card per sentence. For example, if several units describe intelligent transaction monitoring tools that analyze transactions, identify hidden links, compare behavior against thresholds or peer/history patterns, and reduce false positives, combine them into one capability card. If a later paragraph describes AI implementation safeguards such as bias testing, explainability, transparency, and relevance, make that a separate control card.

Do not over-split examples, definitions, list items, or parallel standards into separate cards. Parallel standards should usually remain nodes inside the same card and be connected with `REFERENCES` edges.

Risk-factor material may be extracted as an assessment or risk-indicator card when it gives usable screening or evaluation criteria, even if it does not specify a step-by-step workflow. In that case, set `card_nature` to `assessment` or `risk_indicator`, model the risk indicators as `standard` nodes used by a `P1_assessment` process such as assess, review, or screen, and explain in `review_notes` that the card is not a strict operating workflow.

For `risk_indicator` cards, do not force a chronological sequence among risk factors. The usual structure is `entry node -> P1_assessment`, parallel `standard` nodes connected by `REFERENCES`, and an X-prefix risk finding such as `X1_classification`.

Discouraged-practice or anti-pattern material should usually be extracted as `assessment` or `control`, not as a new card nature. Model the questionable practice as an E-prefix entry, `input`, or `standard`; model the harm, deficiency, or required judgement as X-prefix exit nodes or standards. If helpful, add optional metadata such as:

```json
{
  "negative_pattern": true,
  "evidence_matching_value": "high",
  "not_strict_workflow": true,
  "missing_context_risk": false
}
```

Metadata is optional. It must not replace `flow_nodes`, `flow_edges`, evidence IDs, or review notes.

## Required Card Fields

Each card must include:

```text
card_id
section_id
card_nature
title
flow_nodes
flow_edges
source_unit_ids
review_status
```

`card_nature` must be one of:

```text
execution       strict execution process: trigger, steps, branches, output
assessment      judgement process: assessment object, criteria, result
risk_indicator  risk-factor or red-flag card: risk scenario, indicators, risk conclusion
control         control or governance requirement: control action, control objective, applicable context, expected effect
```

Use `execution` for strict operational handling sequences. Use `assessment`, `control`, or `risk_indicator` for non-sequential judgement material that is still useful for deciding whether a business response is CAMS-compliant.

## Card Nature Decision Rules

Choose `card_nature` by the card's primary objective, not by the mere presence of actions or decisions.

Use `execution` when the card's primary objective is to perform an operational process or handling sequence, such as collecting information, verifying identity, conducting screening, filing a report, escalating a case, reviewing alerts, or completing a monitoring workflow.

Use `assessment` when the card's primary objective is to:

```text
evaluate a profile, control, risk, result, or suitability
screen against criteria
determine whether to proceed
determine risk level
determine required due diligence or handling level
decide whether standard or enhanced handling is required
```

This remains `assessment` even if the card has an entry node, process nodes, branch-routing node, and exit branches.

Use `control` when the card's primary objective is to state a control or governance requirement, its applicable context, and its expected control effect. A control card may be non-chronological.

Use `risk_indicator` when the source mainly lists risk factors, red flags, or warning indicators used to identify elevated risk or problematic conduct.

If the boundary between card natures is uncertain, choose the closest primary objective, set `review_status` to `needs_review`, and explain the boundary issue in `review_notes`.

Optional fields are allowed but must not replace the graph:

```text
summary
scenario
trigger
actor
objective
inputs
decision_standard
outputs
steps
review_notes
metadata
```

`summary` is only a human-readable description. `scenario`, `trigger`, and `objective` are retrieval or review aids. The formal trigger should be represented as an E-prefix `entry` node when the source text supports it.

For later retrieval and evidence matching, preserve important condition words in titles and node labels, such as `when`, `if`, `unless`, `insufficient`, `defensive`, `effective`, `residual risk`, `tuning`, `threshold`, `high risk`, `significant event`, and similar source-supported qualifiers. Do not hide exceptions, limits, negative consequences, or branch conditions inside generic labels.

## Flow Nodes

Allowed node types and categories:

```text
Entry node types (`node_category`: `entry`):
E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding

Process node types (`node_category`: `process`):
P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency

Exit node types (`node_category`: `exit`):
X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation

Auxiliary node types (`node_category`: `auxiliary`):
input, standard
```

Required node fields:

```text
node_id
node_category
node_type
label
evidence_unit_ids
evidence_strength
```

Optional node fields:

```text
actor
description
source_quote
modality
review_status
```

`review_status` must be exactly one of:

```text
needs_review
accepted
rejected
```

Do not output `reviewed`, `pass`, `valid`, `ok`, or other review status values.

Node category mapping:

```text
E-prefix node_type -> node_category: entry
P-prefix node_type -> node_category: process
X-prefix node_type -> node_category: exit
input or standard -> node_category: auxiliary
```

Rules:

1. Every card must contain at least one E-prefix entry node.
2. Entry nodes must use `node_category: "entry"` and an E-prefix `node_type`.
3. Process nodes must use `node_category: "process"` and a P-prefix `node_type`.
4. Exit nodes must use `node_category: "exit"` and an X-prefix `node_type`.
5. Auxiliary nodes must use `node_category: "auxiliary"` and `node_type` of either `input` or `standard`.
6. Do not output old node types such as `start`, `trigger`, `action`, `decision`, `output`, or `end`.
7. If the source text states a clear trigger condition or trigger event, create an E-prefix entry node.
8. Any `input` or `standard` referenced by `REFERENCES` must appear as an auxiliary node.
9. Any target referenced by `PRODUCES` must appear as an X-prefix exit node.
10. If the local exit is only inferred, use `evidence_strength: "functional_dependency"` and `review_status: "needs_review"` instead of adding unsupported closure.
11. `evidence_unit_ids` must never be an empty list. Every node must cite at least one current-section `unit_id` from `allowed_unit_ids`.
12. Do not output placeholder, empty, or partially filled nodes. If a node cannot be assigned a valid `node_category`, `node_type`, `label`, and evidence, omit the node or omit the whole card.
13. Every extracted card must be locally closed: it should have at least one entry node, at least one process node, and at least one exit node unless the section only supports an explicitly marked `needs_review` fragment.

## Flow Edges

Allowed card-internal edge types:

```text
PRECEDES
REFERENCES
PRODUCES
DECIDES
FEEDBACK
```

`REFERENCES` means a process node is associated with a non-sequential auxiliary input, clue, standard, judgement dimension, or component. It only expresses an auxiliary dependency/reference. It does not express sequence, output production, or conditional branching.

Read `process --REFERENCES--> auxiliary` as: the process refers to this input/clue/standard/dimension/component.

Use `FEEDBACK` only when a result updates an X-prefix exit node, `input`, `standard`, or another updateable process node, such as updating a risk profile, threshold, finding, record, criterion, or completion request. Do not use `FEEDBACK` to point back to old node-type labels such as `action`, `decision`, `trigger`, or `start`. If research or review loops back to another process, use `PRECEDES` with `evidence_strength: "functional_dependency"` or model the loop through a `P3_branch_routing` node with `DECIDES` edges.

## relation_type（可选）

先判结构，再判语义。

`edge_type` 回答“图怎么连接”：`PRECEDES`, `REFERENCES`, `PRODUCES`, `DECIDES`, `FEEDBACK`。

`relation_type` 回答“这条关系对考生意味着什么”。不要根据 `edge_type` 机械映射 `relation_type`。同一个 `edge_type` 在不同语境下可能对应不同 `relation_type`；证据不足时可以省略 `relation_type`。

允许值与判别规则：

- `clue_supports_identification`
  异常、红旗、事实、风险指标被用于识别或判断。适用于 red flag / indicator / anomaly / unusual pattern。不要把这类线索归入一般标准约束。

- `mechanism_explains_risk`
  风险机制、原因或路径解释为什么产生风险。适用于 anonymity, concealment, cross-border movement, complexity, misuse mechanism 等。

- `identification_leads_to_conclusion`
  识别、评估、审查之后形成分类、结论或发现。常见于 assessment/process -> `X1_classification`。

- `conclusion_triggers_response`
  已有结论、分类或发现触发后续应对，例如 EDD、升级、报告、冻结、持续监控。不能泛指“处理产生结果”，也不能用于普通 process -> product/result。

- `branch_condition_routes_path`
  分支条件把流程路由到某条路径。只能用于 `DECIDES` 边，并且必须填写 `condition`。仅当文本存在 if / when / whether / unless / sufficient / insufficient / yes / no 等条件分支含义时使用。不要把普通“入口 -> 处理”、普通步骤顺序、入口触发处理写成 `branch_condition_routes_path`。

- `component_assembles_product`
  多个组成要素共同形成产品、框架、计划、记录、制度或能力。适用于 components / elements / includes / consists of / framework / program 等。

- `standard_constrains_action`
  某项标准、控制要求或操作约束直接限制具体动作怎么执行。重点是“该动作必须如何做”。例如保密性、准确性、比例性、合法框架限制执法请求响应。

- `standard_transmits_requirement`
  国际标准、监管原则、法律、政策或指南向辖区、机构制度、流程或控制传导要求。重点是“要求来源向下传导”。例如 Basel/FATF/regulator/law/guidance -> bank program/control/process。

- `result_handoffs_stage`
  某个结果交接到下一阶段、下一角色或下一流程。适用于 handoff / escalation / submit / disclose / transfer / provide to。

- `feedback_requests_completion`
  反馈要求补充、修正、解释或完善。适用于 missing / incomplete / request additional / correct / explain。

- `cycle_requires_monitoring`
  周期、持续状态或持续义务要求监控、复核、更新。适用于 ongoing / periodic / continue / monitor / review / update。

- `parallel_alternative_no_sequence`
  并列标准、并列选项、并列风险因素之间不存在顺序。不要为了连接并列项而伪造 `PRECEDES`。

禁止误用：

1. 不要把普通步骤顺序写成 `branch_condition_routes_path`。`branch_condition_routes_path` 只用于真实分支条件，必须对应 `DECIDES`，且必须有 `condition`。
2. 不要把所有 `REFERENCES` 边都写成 `standard_constrains_action`。如果目标是 red flag / risk indicator，优先 `clue_supports_identification`；如果目标是 law / regulation / policy / guidance，优先 `standard_transmits_requirement`；如果目标是 product component / framework element，优先 `component_assembles_product`。
3. 不要把所有 `PRODUCES` 边都写成 `conclusion_triggers_response`。如果 process 产生分类/发现，优先 `identification_leads_to_conclusion`；如果产生报告/记录/框架，优先 `component_assembles_product`；如果产生交接/升级/披露，优先 `result_handoffs_stage`；如果产生持续义务，优先 `cycle_requires_monitoring`。
4. `conclusion_triggers_response` 只能用于“已有结论/分类/发现 -> 后续应对动作”，不能用于“处理动作 -> 产物”。
5. 允许不编码：无法由原文可靠解释时，省略 `relation_type`，不要为了覆盖类型而硬贴标签。

验收原则：

- 修改后不是类型越分散越好。
- 原来误用的 `branch_condition_routes_path` 应明显减少或消失。
- `standard_constrains_action` 应只剩真正的行动约束。
- 新出现的 `relation_type` 必须能逐条由原文解释。
- 无法可靠分类的边应宁可留空。

Required edge fields:

```text
edge_id
edge_type
source
target
evidence_unit_ids
evidence_strength
```

Optional edge fields:

```text
condition
qualifier
modality
source_quote
review_status
relation_type
```

Rules:

1. `source` and `target` must reference `node_id` values in the same card.
2. Conditional branches should use a `P3_branch_routing` node and `DECIDES` edges.
3. Every `DECIDES` edge must include `condition`, such as `yes`, `no`, `if needed`, `if explainable`, or `if potentially suspicious`.
4. Do not use `PRECEDES` to hide a condition branch.
5. Do not turn parallel assessment dimensions into a chronological chain. When the source says `both A and B`, `A and B`, `includes A and B`, `consists of A and B`, `key elements include`, or similar list language, treat the items as parallel standards, inputs, exit alternatives, or branches unless the source explicitly states sequence. Keep all parallel criteria that affect judgement; do not collapse them into one vague node.
6. For assessment, control, and risk-indicator cards, prefer `process --REFERENCES--> standard` edges for criteria, requirements, controls, indicators, and judgement dimensions. For example, `Evaluate control effectiveness --REFERENCES--> design effectiveness` and `Evaluate control effectiveness --REFERENCES--> operational effectiveness` is better than `design effectiveness --PRECEDES--> operational_effectiveness` unless the source explicitly states that sequence.
7. Use `PRECEDES` only for explicit or strongly implied process order. If an edge is a `functional_dependency` rather than explicit sequence, add `review_status: "needs_review"` and explain in card `review_notes` whether it represents a parallel assessment dimension, condition dependency, outcome inference, or weak sequence reconstruction.
8. `PRODUCES` must target an X-prefix exit node.
9. `REFERENCES` must target an auxiliary `input` or `standard` node.
10. `evidence_unit_ids` must never be an empty list. Every edge must cite at least one current-section `unit_id` from `allowed_unit_ids`.
11. `qualifier` is optional and must be one of: `input`, `standard`, `context`, `record`, `finding`. Do not output any other qualifier value. In particular, do not use `output`, `effect`, `result`, `control`, `branch`, or free-text explanations as qualifier values. If no allowed qualifier fits, omit `qualifier`. Put explanations in `review_notes` or `source_quote` instead.
12. Do not output placeholder, empty, or partially filled edges. Every edge object must include a valid `edge_type`, `source`, `target`, `evidence_unit_ids`, and `evidence_strength`. If an edge is uncertain, either omit it or mark it with `evidence_strength: "needs_review"` and a valid source/target.
13. Do not leave dangling nodes in the JSON example pattern. If a node appears in `flow_edges`, it must also appear in `flow_nodes`; if a card cannot be completed, return fewer cards.

When setting card-level `review_status: "needs_review"`, explain the reason in `review_notes`. Use one or more of these categories when applicable: weak inferred process order; non-procedural source material converted into an assessment/control/risk-indicator card; possible card granularity problem; missing downstream handoff; limited single-unit evidence; useful option-evaluation material but not a strict workflow; other.

Card-level `review_status` must be exactly one of:

```text
needs_review
accepted
rejected
```

Do not output `reviewed`, `pass`, `valid`, `ok`, or other review status values.

## Evidence Strength

Use only:

```text
explicit
functional_dependency
needs_review
rejected
```

Do not use `co_listed_input`, `weak_inference`, `no_relation`, `high`, `medium`, or `low`.

Evidence must be current-section unit evidence. Do not cite CP titles, P2B labels, or alias metadata as evidence.

Only use IDs listed in `allowed_unit_ids`. Do not invent unit IDs.

## Output JSON Shape

Return strict JSON only. Do not include markdown fences.

```json
{
  "section_id": "<section_id>",
  "section_title": "<section_title>",
  "cards": [
    {
      "card_id": "p7card_<section_id>_001",
      "section_id": "<section_id>",
      "card_nature": "execution",
      "title": "Short card title",
      "summary": "Optional one-sentence human-readable description.",
      "flow_nodes": [
        {
          "node_id": "n_entry_01",
          "node_category": "entry",
          "node_type": "E1_event_signal",
          "label": "Relevant event or condition occurs",
          "evidence_unit_ids": ["v7u_..."],
          "evidence_strength": "functional_dependency",
          "review_status": "needs_review"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7flowedge_<section_id>_001_001",
          "edge_type": "PRECEDES",
          "source": "n_entry_01",
          "target": "n_process_01",
          "evidence_unit_ids": ["v7u_..."],
          "evidence_strength": "functional_dependency",
          "review_status": "needs_review"
        }
      ],
      "source_unit_ids": ["v7u_..."],
      "review_status": "needs_review",
      "review_notes": ""
    }
  ],
  "skip_reason": null
}
```

If no cards should be extracted:

```json
{
  "section_id": "<section_id>",
  "section_title": "<section_title>",
  "cards": [],
  "skip_reason": "No section-level executable process, assessment standard, control requirement, or risk-indicator rule found."
}
```

## Current Section

section_id: `CH12-S04`

section_title: `Money laundering risks associated with insurance, securities, brokerage, and custodian services > Securities and brokerage risks`

section_text_with_unit_anchors:

```text
[v7u_N000912|912] According to FATF, securities providers can range from those that largely interact with retail investors, such as retail stockbrokers, wealth managers, and financial advisors, to those who serve institutional markets such as clearing members, prime brokers, and global custodians.
ZH: FATF指出证券服务商范围从零售投资者到机构市场。

[v7u_N000913|913] Providers offer various services including capital market research, portfolio management, and investment funds distribution.
ZH: 服务商提供资本市场研究、投资组合管理和投资基金分销等服务。

[v7u_N000914|914] The securities and brokerage sector serves direct customers and intermediaries that transact on behalf of their underlying customers.
ZH: 证券和经纪业服务于直接客户和代表其客户交易的中介。

[v7u_N000915|915] Transactions can encompass a wide range of financial instruments, including transferable securities, moneymarket instruments, investment funds, options, futures, swaps, forward rate agreements, and other derivative contracts.
ZH: 交易涵盖多种金融工具，包括可转让证券、货币市场工具、投资基金、期权、期货等。

[v7u_N000916|916] This sector is particularly vulnerable during the layering and integration stages of money laundering.
ZH: 证券业在洗钱的离析阶段和融合阶段尤其脆弱。

[v7u_N000917|917] FATF notes that the sector is unique in that it can be used not only to launder illicit funds but also to generate illicit funds within the industry itself through fraudulent activities.
ZH: FATF指出证券业既可洗钱也可通过欺诈产生非法资金。

[v7u_N000918|918] Characteristics such as high levels of interaction between securities providers and intermediaries such as investors and brokers, substantial transaction volumes, rapid execution speeds, and a degree of anonymity, all create opportunities for criminals to launder proceeds.
ZH: 高互动性、大交易量、快速执行和匿名性为洗钱创造机会。

[v7u_N000919|919] Complex financial products present a risk as they can obscure the source of funds and complicate transaction monitoring.
ZH: 复杂金融产品可能掩盖资金来源并复杂化交易监控。

[v7u_N000920|920] Offshore accounts provide anonymity, which can facilitate money laundering and enable criminals to exploit lax regulatory jurisdictions.
ZH: 离岸账户提供匿名性，便利洗钱并利用监管宽松的司法管辖区。

[v7u_N000921|921] High-risk customers, such as PEPs, and intermediaries require careful risk assessment. PEPs might be susceptible to corruption, while intermediaries might facilitate illicit transactions on behalf of customers.
ZH: 高风险客户如政治敏感人物和中介机构需要仔细的风险评估

[v7u_N000922|922] Additionally, the rise of electronic trading platforms emphasizes speed and high transaction volumes, making it challenging to monitor and apply mitigation controls.
ZH: 电子交易平台的高速度和高交易量增加了监控难度

[v7u_N000923|923] Continuous monitoring of trading activities can help identify unusual patterns or behaviors that might indicate money laundering. Robust transaction monitoring systems that flag suspicious transactions based on predefined criteria can help identify large or unusual trades, rapid trading patterns, highfrequency transactions and transactions involving high-risk jurisdictions.
ZH: 持续监控交易活动以识别异常模式，防范洗钱

[v7u_N000924|924] Conducting CDD helps ensure that the source of funds is legitimate, and that customers are correctly segmented according to their expected and historical trading patterns.
ZH: 客户尽职调查用于验证资金来源和客户细分

[v7u_N000925|925] Asset managers or asset management companies conduct investments and handle assets on behalf of their customers.
ZH: 资产管理公司代表客户进行投资和资产管理

[v7u_N000926|926] Asset managers are required to understand the money laundering risks of their business as they handle large volumes of capital across multiple jurisdictions, in diverse and evolving asset classes, often with anonymity in transactions, using complex financial products and third parties.
ZH: 资产管理公司有义务了解其业务中的洗钱风险

[v7u_N000927|927] Asset managers provide a variety of financial products and services, including:
ZH: 资产管理公司提供的金融产品和服务列表

[v7u_N000928|928] Exchange-traded funds (ETF): These are investment funds traded on stock exchanges, similar to individual stocks. They offer diversification and liquidity but can also obscure the identities of underlying investors.
ZH: 交易所交易基金（ETF）的定义及其洗钱风险

[v7u_N000929|929] Derivatives: These financial instruments, such as options and futures, derive their value from underlying assets. Their complexity and potential for leverage can be exploited for money laundering.
ZH: 衍生品（如期权和期货）的复杂性和杠杆可能被用于洗钱

[v7u_N000930|930] Hedge funds: These pooled investment funds employ various strategies to generate returns. Their often opaque structures and high minimum investment requirements can attract illicit actors.
ZH: 对冲基金的不透明结构和最低投资要求可能吸引非法行为者

[v7u_N000931|931] Private equity: This involves investing directly in private companies or buying out public companies. The lack of transparency in these transactions can pose money laundering challenges.
ZH: 私募股权交易缺乏透明度，带来洗钱挑战

[v7u_N000932|932] Commodity trading advice: Asset managers might provide guidance on trading physical commodities, which can be subject to manipulation and illicit activities.
ZH: 大宗商品交易建议可能被操纵和用于非法活动

[v7u_N000933|933] Real estate investments: Investing in real estate involves various stakeholders, including sellers, buyers, renters, property managers, and agents, all of whom should be thoroughly vetted to mitigate money laundering risks.
ZH: 房地产投资涉及多方利益相关者，需全面审查以降低洗钱风险

[v7u_N000934|934] Crowdfunding: As a relatively new form of asset management, crowdfunding platforms allow individuals to invest in projects or startups. These platforms can be misused for money laundering due to insufficient regulatory oversight and the anonymity they can provide to investors.
ZH: 众筹平台因监管不足和匿名性可能被滥用于洗钱

[v7u_N000935|935] The complexity and variability of these products and services make it increasingly difficult to detect money laundering.
ZH: 产品和服务的复杂性和多样性增加了洗钱检测难度

[v7u_N000936|936] Additionally, asset managers face a complex and evolving CDD process that requires knowledge of all parties involved in the transactions. Those parties include investment fund managers, portfolio managers, and alternative investment fund managers, such as those overseeing hedge funds and private equity.
ZH: 资产管理公司面临复杂的客户尽职调查，需了解所有交易方

[v7u_N000937|937] By adopting a risk-based approach that emphasizes strong CDD controls and continuous monitoring, they can meet regulatory requirements and demonstrate a genuine commitment to the sector’s integrity. This commitment also addresses emerging risks associated with new asset classes, such as cryptocurrencies and novel financial instruments, which might be more susceptible to exploitation by money launderers.
ZH: 基于风险的方法通过强化客户尽职调查和监控应对新兴资产类别的洗钱风险
```

allowed_unit_ids:

```json
[
  "v7u_N000912",
  "v7u_N000913",
  "v7u_N000914",
  "v7u_N000915",
  "v7u_N000916",
  "v7u_N000917",
  "v7u_N000918",
  "v7u_N000919",
  "v7u_N000920",
  "v7u_N000921",
  "v7u_N000922",
  "v7u_N000923",
  "v7u_N000924",
  "v7u_N000925",
  "v7u_N000926",
  "v7u_N000927",
  "v7u_N000928",
  "v7u_N000929",
  "v7u_N000930",
  "v7u_N000931",
  "v7u_N000932",
  "v7u_N000933",
  "v7u_N000934",
  "v7u_N000935",
  "v7u_N000936",
  "v7u_N000937"
]
```
