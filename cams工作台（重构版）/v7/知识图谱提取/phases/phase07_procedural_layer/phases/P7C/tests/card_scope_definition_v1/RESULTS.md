# Card Scope Definition v1 Results

## Run

```text
run_id: run_ds_none_focus6
model: deepseek-v4-pro
thinking_effort: none
concurrency: 6
max_tokens: 32000
sections: CH47-S06, CH49-S13, CH49-S16, CH47-S03, CH47-S04, CH49-S10
```

Output:

```text
outputs/run_ds_none_focus6
```

## Summary

| section | cards | result | note |
|---|---:|---|---|
| CH47-S06 | 2 | pass | Multi-level alert review preserved as a larger process card; one inferred edge correctly marked needs_review. |
| CH49-S10 | 2 | pass_with_minor_issue | Defensive SAR judgement and avoidance handling were extracted; judgement card uses some PRECEDES edges where USES/PRODUCES would be cleaner. |
| CH49-S13 | 1 | needs_prompt_fix | Non-institution content was no longer skipped, but it was extracted as process_card rather than judgement_card. |
| CH47-S03 | 0 | false_negative | Technology capability and AI safeguard material can support option judgement; prompt treated it as ordinary KG only. |
| CH47-S04 | 0 | false_negative | TM tuning contains control purpose, components, threshold logic, tuning frequency, and significant-event trigger; should produce at least one judgement/control card. |
| CH49-S16 | 0 | likely_false_negative | Financial inclusion material gives a control-overreach / access-barrier judgement; should likely produce a judgement_card. |

## Findings

The new scope successfully reduced the risk of turning ordinary textbook facts into P7 cards.

However, it overcorrected. The prompt now misses material that is not a strict process but still has option-judgement value:

```text
technology/control capability with conditions, limitations, safeguards, or expected effects
control tuning with components, thresholds, frequency, and event-triggered reassessment
financial inclusion / control-overreach judgement material
```

The field simplification worked: `card_type` appeared in successful outputs, and old fields such as `kg_only`, `graph_route`, `granularity`, `atomic`, and `macro` were not emitted.

## Section Notes

### CH47-S06

Good result. The model kept the alert review lifecycle as a larger process card and did not force unnecessary splitting. Key Level 1, Level 2, Level 3, SAR filing, ongoing monitoring, and preventive measures were preserved.

The card marked one inferred edge as `needs_review`, which is appropriate.

### CH49-S10

Good result. The section produced:

```text
Assessment of Defensive SARs
Best Practice to Avoid Defensive SARs
```

This supports both judgement and handling. Minor issue: the assessment card models reasons/effects using a small sequence. For judgement cards, parallel criteria should usually use `USES` and consequences should use `PRODUCES`.

### CH49-S13

Partly successful. The section was not skipped, which fixes the previous mechanical skip problem for external actor content.

But the card was extracted as `process_card`. Under the current policy, external actor behavior should usually be a `judgement_card` unless the institution itself is executing the process. This section is more useful as evidence of SAR downstream value and investigation use, not as an institution-side process card.

### CH47-S03

False negative. The section contains technology capability and AI safeguard material that can support exam-option judgement:

```text
intelligent contextual analysis checks thresholds plus additional criteria
network analysis detects customer-network patterns and hidden links
AI monitoring identifies suspicious patterns in real time
AI implementation requires testing for bias, explainability, transparency, and contextual relevance
```

This should likely produce judgement/control cards rather than be skipped as ordinary KG.

### CH47-S04

False negative. The section contains a clear judgement/control structure:

```text
tuning refines parameters and thresholds
tuning improves suspicious activity detection, reduces false positives, improves resource use, supports regulatory compliance
tuning components include scenario setting, customer segmentation, threshold setting, and frequency
significant events or trends trigger special assessments
```

This should produce at least one `judgement_card` or `control` card.

### CH49-S16

Likely false negative. The section gives a judgement about AFC controls creating access barriers for vulnerable customers and strict documentation reducing financial inclusion. This is not an execution process, but it is useful for judging proportionality and control-overreach options.

## Prompt Implication

The next prompt revision should keep the KG/P7 boundary, but explicitly allow non-strict judgement cards when the section contains:

```text
control capability + expected effect
control limitation or safeguard
parameter/threshold/frequency judgement
significant-event trigger for reassessment
control-overreach, access-barrier, or proportionality judgement
external actor use that changes the value or interpretation of institution-side action
```

Do not reintroduce `kg_only`, `graph_route`, `granularity`, `atomic`, or `macro`.

## Promptfix Notes

### promptfix1

Run:

```text
outputs/run_ds_none_focus6_promptfix1
```

Result: not accepted.

It recovered CH47-S04 but caused regressions:

```text
CH49-S13 was skipped again.
CH47-S03 and CH49-S16 remained false negatives.
CH47-S06 failed validation because the model put explanations into qualifier and reversed a USES edge.
```

### promptfix2

Run:

```text
outputs/run_ds_none_focus6_promptfix2
```

Result: mostly accepted.

It introduced the missing concept that a judgement path does not need chronology:

```text
object/scenario -> criteria, limits, safeguards, effects -> judgement or implication
```

Outcomes:

```text
CH47-S03 recovered as judgement_card for AI safeguards.
CH49-S13 recovered as judgement_card for SAR downstream value and limitation.
CH49-S16 recovered as judgement_card for financial inclusion / documentation barrier judgement.
CH47-S06 validated successfully and kept the larger alert review card.
CH49-S10 remained useful.
CH47-S04 still skipped.
```

### promptfix3

Run:

```text
outputs/run_ds_none_ch47s04_promptfix3
```

Result: accepted for CH47-S04.

The prompt now explicitly treats parameter, threshold, scenario, segmentation, and frequency tuning as a control judgement path when the section explains what is adjusted, why it is adjusted, what criteria or triggers affect adjustment, and what control effect should result.

CH47-S04 output became one `judgement_card / control` card covering:

```text
tuning objectives
scenario setting
customer segmentation
threshold setting
tuning frequency
business/regulatory/anomaly/market-change drivers
significant-event reassessment
```

No validation errors.
