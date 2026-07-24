# v7 Remaining Review Policy Overlay

Generated at: 2026-07-03T09:40:01

## Summary

- processed review items: 91
- direct items: 4702
- review items: 10
- parent/context items: 271
- direct units added: 24
- parent/context units added: 61
- review units retained: 10
- duplicate unit_ids: 0
- duplicate direct sentence_ids: 0

## Action Counts

- move_to_parent_context: 61
- promote_to_direct: 18
- keep_review: 10
- split_to_direct: 2

## Policy Basis

- Visual/table labels are auxiliary context by default, not direct evidence.
- Teaching/navigation/module-intro text is context unless it states a testable knowledge assertion.
- Short bullets may be direct when the parent heading supplies the missing domain.
- Term: explanation, red-flag list items, and process/list steps may be direct even without terminal punctuation.
- Table/list lead-ins become parent/context, not direct evidence.
- Residual damaged fragments may remain in review when the source problem is explicit.

## Direct Samples

### v7u_tmp_pilot_v2fb_transaction-monitoring_o020_l020_N000001

- type: risk_indicator
- page: 333 / pdf 338
- heading: Transaction monitoring / Typical scenarios that would generate an alert
- knowledge_en: excessive channel use as red flag
- en_quote: Excessive use of a particular channel compared to what is expected for that customer type, such as high use of cash over electronic payments
- reason: complete red-flag list item; terminal punctuation is absent because the source is a list label

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000034

- type: process
- page: 154 / pdf 159
- heading: Financial Action Task Force / FATF 11 Immediate Outcomes
- knowledge_en: Assessor training definition fragment
- en_quote: Assessor training: Training for the experts who will perform assessment
- reason: colon-form process step with its own explanation

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000035

- type: process
- page: 154 / pdf 159
- heading: Financial Action Task Force / FATF 11 Immediate Outcomes
- knowledge_en: jurisdiction training definition fragment
- en_quote: Jurisdiction training: Training for representatives of the evaluated jurisdictions
- reason: colon-form process step with its own explanation

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000036

- type: process
- page: 154 / pdf 159
- heading: Financial Action Task Force / FATF 11 Immediate Outcomes
- knowledge_en: subheading fragment
- en_quote: Selection of assessors: Selection of the experts that form the assessment team
- reason: colon-form process step with its own explanation

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000037

- type: process
- page: 154 / pdf 159
- heading: Financial Action Task Force / FATF 11 Immediate Outcomes
- knowledge_en: FATF plenary discussion and voting on ratings
- en_quote: Plenary discussion: FATF plenary discusses the findings in the report and votes on the ratings
- reason: colon-form process step with its own explanation

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000038

- type: process
- page: 155 / pdf 160
- heading: Financial Action Task Force / FATF 11 Immediate Outcomes
- knowledge_en: final quality review step
- en_quote: Final quality review: All jurisdictions review the report before publishing
- reason: colon-form process step with its own explanation

### v7u_tmp_pilot_v2fb_types-of-financial-crime_o000_l020_N000007

- type: definition
- page: 22 / pdf 27
- heading: Types of financial crime / Predicate crimes and money laundering
- knowledge_en: Piracy definition
- en_quote: 20.Piracy: Maritime or cyber-based hijacking for financial gain
- reason: numbered predicate-crime definition; absent period is source list formatting

### v7u_tmp_pilot_v2fb_types-of-risk-assessment_o000_l020_N000005

- type: fact
- page: 267 / pdf 272
- heading: Types of risk assessment / The importance of risk assessment in AFC
- knowledge_en: Risks vary in nature, scale, and impact
- en_quote: Risks can vary in their nature, scale, and impact.
- reason: complete statement; prior label only supplies context

### v7u_tmp_pilot_v2fb_private-banking-and-wealth-management-risks_o000_l020_N000044

- type: risk_indicator
- page: 74 / pdf 79
- heading: Private banking and wealth management risks / Offshore financial center risks
- knowledge_en: fragment: round tripping
- en_quote: Round tripping or moving funds in and out
- reason: short risk/red-flag list item that is meaningful under its heading

### v7u_tmp_pilot_v2fb_corporate-and-investment-banking-risks_o000_l020_N000010

- type: risk_indicator
- page: 79 / pdf 84
- heading: Corporate and investment banking risks / Wire transfer risks
- knowledge_en: fragment: unusual volume or amount of transfer
- en_quote: Unusual volume or amount of the transfer
- reason: short risk/red-flag list item that is meaningful under its heading

### v7u_tmp_prefreeze_qa_ignored_N000001

- type: risk_indicator
- page: 74 / pdf 79
- heading: Private banking and wealth management risks / Offshore financial center risks
- knowledge_en: Sudden, large flows of funds
- en_quote: Sudden, large flows of funds
- reason: short red-flag list item; heading supplies the risk domain

### v7u_tmp_prefreeze_qa_ignored_N000002

- type: risk_indicator
- page: 75 / pdf 80
- heading: Private banking and wealth management risks / Offshore financial center risks
- knowledge_en: Rapid asset transfers between offshore entities
- en_quote: Rapid asset transfers between offshore entities
- reason: short red-flag list item; heading supplies the risk domain

### v7u_tmp_prefreeze_qa_ignored_N000003_policy_split_N000001

- type: definition
- page: 75 / pdf 80
- heading: Private banking and wealth management risks / Special purpose vehicle risks
- knowledge_en: SPVs are legal entities created for specific and limited purposes
- en_quote: Special purpose vehicles (SPVs) are legal entities created for specific and limited purposes.
- reason: ignored prose block was deterministically split by existing sentence_ids

### v7u_tmp_prefreeze_qa_ignored_N000003_policy_split_N000002

- type: fact
- page: 75 / pdf 80
- heading: Private banking and wealth management risks / Special purpose vehicle risks
- knowledge_en: SPVs can be used for mergers, acquisitions, joint ventures, real estate, infrastructure, and energy projects
- en_quote: SPVs can be used in mergers and acquisitions, joint ventures, real estate projects, infrastructure development, and energy projects.
- reason: ignored prose block was deterministically split by existing sentence_ids

### v7u_tmp_prefreeze_qa_ignored_N000003_policy_split_N000003

- type: fact
- page: 75 / pdf 80
- heading: Private banking and wealth management risks / Special purpose vehicle risks
- knowledge_en: SPVs can manage and protect intellectual property assets
- en_quote: SPVs can also be used to manage and protect intellectual property assets including trademarks and copyrights.
- reason: ignored prose block was deterministically split by existing sentence_ids

### v7u_tmp_prefreeze_qa_ignored_N000003_policy_split_N000004

- type: fact
- page: 75 / pdf 80
- heading: Private banking and wealth management risks / Special purpose vehicle risks
- knowledge_en: SPVs are often used in complex financial transactions and asset-backed financing
- en_quote: SPVs are often used in complex financial transactions and investments such as securities and asset-backed financing.
- reason: ignored prose block was deterministically split by existing sentence_ids

### v7u_tmp_prefreeze_qa_ignored_N000004_policy_split_N000001

- type: definition
- page: 78 / pdf 83
- heading: Corporate and investment banking risks / Wire transfer risks
- knowledge_en: A bank transfer electronically transfers funds between two banks and is usually domestic
- en_quote: A bank transfer is a different method used to electronically transfer funds. This is conducted between two banks and is usually domestic.
- reason: ignored prose block was deterministically split by existing sentence_ids

### v7u_tmp_prefreeze_qa_ignored_N000004_policy_split_N000002

- type: process
- page: 78 / pdf 83
- heading: Corporate and investment banking risks / Wire transfer risks
- knowledge_en: Bank transfers use ACH settlement to support bank credit and debit transfers
- en_quote: Bank transfers use a settlement system called an automated clearing house (ACH). This system supports the transfer of credits and debits between banks.
- reason: ignored prose block was deterministically split by existing sentence_ids

### v7u_tmp_prefreeze_qa_ignored_N000005

- type: risk_indicator
- page: 79 / pdf 84
- heading: Corporate and investment banking risks / Wire transfer risks
- knowledge_en: Unusual timing of the transfer
- en_quote: Unusual timing of the transfer
- reason: short red-flag list item; heading supplies the risk domain

### v7u_tmp_prefreeze_qa_ignored_N000006

- type: risk_indicator
- page: 79 / pdf 84
- heading: Corporate and investment banking risks / Wire transfer risks
- knowledge_en: Complex transaction paths
- en_quote: Complex transaction paths
- reason: short red-flag list item; heading supplies the risk domain

### v7u_tmp_prefreeze_qa_ignored_N000008

- type: risk_indicator
- page: 98 / pdf 103
- heading: Money laundering risks associated with MSBs, payment service providers, and ecommerce / E-commerce risks
- knowledge_en: To launder illicit funds
- en_quote: To launder illicit funds
- reason: short list item describing an illicit e-commerce use; heading supplies the risk domain

### v7u_tmp_prefreeze_qa_ignored_N000023

- type: process
- page: 293 / pdf 298
- heading: Governance and oversight / Drafting AFC policies and procedures
- knowledge_en: System, procedural, and process updates
- en_quote: System, procedural, and process updates
- reason: short implementation/update item; surrounding list supplies the policy-design context

### v7u_tmp_prefreeze_qa_ignored_N000031

- type: example
- page: 421 / pdf 426
- heading: Technology for KYC / Fuzzy logic and partial matches
- knowledge_en: "Katherine Navel" and "Catherine Naval"
- en_quote: "Katherine Navel" and "Catherine Naval"
- reason: name-matching example under fuzzy logic; direct only with parent context

### v7u_tmp_prefreeze_qa_ignored_N000032

- type: example
- page: 421 / pdf 426
- heading: Technology for KYC / Fuzzy logic and partial matches
- knowledge_en: "McDowd" and "MacDawd"
- en_quote: "McDowd" and "MacDawd"
- reason: name-matching example under fuzzy logic; direct only with parent context


## Retained Review Items

### v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o020_l020_N000049

- page: 192 / pdf 197
- heading: US AML/CFT regulatory landscape / The role of AML Authority
- en_quote: training to national competent authorities.
- reason: orphan sentence fragment; needs source-neighbor repair before it can be evidence

### v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000014

- page: 168 / pdf 173
- heading: AFC guidance from leading international organizations / Wolfsberg Group AFC guidance
- en_quote: In 2000, the Wolfsberg Group published the .
- reason: publication title is missing from source extraction

### v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000016

- page: 169 / pdf 174
- heading: AFC guidance from leading international organizations / Wolfsberg Group AFC guidance
- en_quote: In 2006, the Wolfsberg Group published .
- reason: publication title is missing from source extraction

### v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000021

- page: 170 / pdf 175
- heading: AFC guidance from leading international organizations / International Organization of Securities Commissions AFC guidance
- en_quote: IOSCO published the in 2005.
- reason: publication title is missing from source extraction

### v7u_tmp_pilot_v2fb_private-banking-and-wealth-management-risks_o020_l020_N000009

- page: 76 / pdf 81
- heading: Private banking and wealth management risks / Special purpose vehicle risks
- en_quote: financial transactions, preventing detection by law enforcement and regulatory authorities, as it makes the money trail hard to trace.
- reason: starts mid-phrase and lacks the subject needed for a direct evidence unit

### v7u_tmp_pilot_v2fb_money-laundering-risks-associated-with-retail-and-commercial-banking_o000_l020_N000033

- page: 68 / pdf 73
- heading: Money laundering risks associated with retail and commercial banking / Credit-related product risks
- en_quote: repayment if the source of funds derives from illegal activities or predicate offences to money laundering.
- reason: starts mid-phrase and lacks the subject needed for a direct evidence unit

### v7u_tmp_pilot_v2fb_ongoing-afc-controls_o000_l020_N000026

- page: 320 / pdf 325
- heading: Ongoing AFC controls / Ongoing due diligence
- en_quote: organization's exit policy, subject to the necessary approvals and special licenses for specific transactions linked to sanctioned individuals and entities.
- reason: starts mid-phrase and cannot stand alone as evidence

### v7u_tmp_pilot_v2fb_afc-guidance-from-other-organizations_o000_l020_N000008

- page: 171 / pdf 176
- heading: AFC guidance from other organizations / G-20 Anti-Corruption Working Group AFC guidance
- en_quote: The G-20 has authored several documents that provide essential guidance on anti-corruption measures, financial transparency, and international
- reason: sentence is visibly split at 'international' and needs a source join decision

### v7u_tmp_pilot_v2fb_technology-for-kyc_o080_l020_N000014

- page: 424 / pdf 429
- heading: Technology for KYC / Integrating screening technology with other systems
- en_quote: Organizations should also ensure that their integrated systems are scalable with the growth of the organization and increased data volumes of varying to accommodate the development of the organization and increased data volumes in various formats to accommodate the growth of the organization and increased data volumes, as well as the development of the organization and the varying formats of data. The systems must be able to handle an increase in data requirements without compromising performance.
- reason: source text has unresolved extraction damage around 'of varying to accommodate'

### v7u_tmp_prefreeze_qa_ignored_N000018

- page: 178 / pdf 183
- heading: Case example: Drafting policies for an AFC department based in APAC
- en_quote: Continuously update policies with Íatest regulations and guidance
- reason: source text contains mojibake/typo 'Íatest'; keep for manual source repair
