# v7 Review Resolution Plan

Generated at: 2026-07-03T09:40:25
Input: `D:\守正公司工作区\cams考试\cams工作台（重构版）\v7\work\base_units\draft\v2_fullbook\v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock_toobroad_policy.json`

## Summary

- review items: 10

## Resolution Classes

- fragment_neighbor_join_or_discard: 4
- manual_policy_review: 3
- cross_block_join_candidate: 1
- text_damage_manual_source_review: 1
- ignored_text_damage_manual: 1

## Recommended Actions

- inspect_neighbor_blocks_then_join_or_discard: 4
- manual_review: 3
- manual_pdf_source_review: 2
- inspect_neighbor_blocks_or_pdf_join: 1

## Samples: fragment_neighbor_join_or_discard

### v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o020_l020_N000049

- action: inspect_neighbor_blocks_then_join_or_discard
- rationale: unit is a fragment; needs adjacent text or should remain non-direct
- chapter: US AML/CFT regulatory landscape
- page: 192 / pdf 197
- heading: US AML/CFT regulatory landscape / The role of AML Authority
- knowledge_en: fragment: training to national competent authorities
- en_quote: training to national competent authorities.
- risk_flags: ["derived_from_fullbook_llm_grouping", "fragment", "heading_context_reused_across_page", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001531` P191: • Monitor national competent authorities to ensure consistent application of the Single Rulebook. The AML Authority provides guidance, support, and
  - current `v7en_b001532` P192: training to national competent authorities. The AML Authority has the authorization to identify and act in cases of systematic failures regarding supervision. Such cases could involve breaches resulting from the improper application of national law transposing EU directives. Note that the AML Authority is not the EU FIU; rather, it plays a vital role in supporting and coordinating within the FIU's network.
  - next `v7en_b001533` P192: • Conduct regular assessments of money laundering and terrorist financing risks within the EU. The AML Authority identifies emerging threats and vulnerabilities, providing recommendations to mitigate these risks.

### v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000014

- action: inspect_neighbor_blocks_then_join_or_discard
- rationale: unit is a fragment; needs adjacent text or should remain non-direct
- chapter: AFC guidance from leading international organizations
- page: 168 / pdf 173
- heading: AFC guidance from leading international organizations / Wolfsberg Group AFC guidance
- knowledge_en: incomplete sentence about Wolfsberg Group publication
- en_quote: In 2000, the Wolfsberg Group published the .
- risk_flags: ["derived_from_fullbook_llm_grouping", "incomplete_sentence", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001314` P168: The Wolfsberg Group issues guidelines to assist members in managing their risks, helping them make sound decisions about clients to protect their operations from criminal abuse. Note that the group has no enforcement powers; therefore, its publications are designed to be adapted to its members’ needs and serve as guidance notes for financial institutions depending on their organizational risk, regulatory standards, a...
  - current `v7en_b001315` P168: In 2000, the Wolfsberg Group published the . The Wolfsberg Group routinely revises these principles to outline best practices for financial institutions to detect and mitigate risks associated with high-net-worth clients, PEPs, and offshore entities.
  - next `v7en_b001316` P168: Key provisions include:

### v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000016

- action: inspect_neighbor_blocks_then_join_or_discard
- rationale: unit is a fragment; needs adjacent text or should remain non-direct
- chapter: AFC guidance from leading international organizations
- page: 169 / pdf 174
- heading: AFC guidance from leading international organizations / Wolfsberg Group AFC guidance
- knowledge_en: Incomplete publication statement
- en_quote: In 2006, the Wolfsberg Group published .
- risk_flags: ["derived_from_fullbook_llm_grouping", "incomplete_sentence", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001320` P169: • Ongoing monitoring: Banks should conduct continuous reviews of transactions to detect suspicious activities.
  - current `v7en_b001321` P169: In 2006, the Wolfsberg Group published . It emphasizes that financial institutions should allocate resources based on the level of risk posed by a customer, transaction, or jurisdiction.
  - next `v7en_b001322` P169: In 2014, the Wolfsberg Group published . Since its publication, the Wolfsberg Group has updated the principles that establish best practices for financial institutions engaging in cross-border banking relationships. The best practices include:

### v7u_tmp_pilot_v2fb_ongoing-afc-controls_o000_l020_N000026

- action: inspect_neighbor_blocks_then_join_or_discard
- rationale: unit is a fragment; needs adjacent text or should remain non-direct
- chapter: Ongoing AFC controls
- page: 320 / pdf 325
- heading: Ongoing AFC controls / Ongoing due diligence
- knowledge_en: fragment about exit policy and sanctions
- en_quote: organization's exit policy, subject to the necessary approvals and special licenses for specific transactions linked to sanctioned individuals and entities.
- risk_flags: ["derived_from_fullbook_llm_grouping", "fragment", "heading_context_reused_across_page", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002554` P319: • Escalation and reporting: High-risk entities are subjected to enhanced due diligence, and where necessary, suspicious activity reports are filed with FIUs if money laundering or other financial crime concerns arise. Sanctions violations will be reported to the relevant regulatory bodies. Those customers would typically be offboarded in accordance with the
  - current `v7en_b002555` P320: organization's exit policy, subject to the necessary approvals and special licenses for specific transactions linked to sanctioned individuals and entities.
  - next `v7en_b002556` P320: • AI-driven screening solutions: When appropriately tested and implemented, an AI-driven system can provide improved accuracy, reducing false positives and enhancing detection of hidden risks.


## Samples: manual_policy_review

### v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000021

- action: manual_review
- rationale: remaining review item requires policy or source judgment
- chapter: AFC guidance from leading international organizations
- page: 170 / pdf 175
- heading: AFC guidance from leading international organizations / International Organization of Securities Commissions AFC guidance
- knowledge_en: IOSCO publication year
- en_quote: IOSCO published the in 2005.
- risk_flags: ["derived_from_fullbook_llm_grouping", "extraction_damage", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001332` P170: IOSCO supports its members with technical assistance, education, and training.
  - current `v7en_b001333` P170: IOSCO published the in 2005. It provides AML guidance specifically for collective investment schemes such as mutual funds and exchange-traded funds. The guidance outlines policies, procedures, and client identification measures to mitigate the risk of money laundering in the industry.
  - next `v7en_b001334` P170: In 2003, the BCBS, International Association of Insurance Supervisors (IAIS), and IOSCO published a joint note detailing initiatives to combat AML/CFT. The note provided an overview of common AML/CFT standards across the three sectors and assessed gaps or inconsistencies in approaches. It also examined the relationships between institutions and their customers, focusing on vulnerable products or services.

### v7u_tmp_pilot_v2fb_private-banking-and-wealth-management-risks_o020_l020_N000009

- action: manual_review
- rationale: remaining review item requires policy or source judgment
- chapter: Private banking and wealth management risks
- page: 76 / pdf 81
- heading: Private banking and wealth management risks / Special purpose vehicle risks
- knowledge_en: fragment describing money laundering effect
- en_quote: financial transactions, preventing detection by law enforcement and regulatory authorities, as it makes the money trail hard to trace.
- risk_flags: ["derived_from_fullbook_llm_grouping", "heading_context_reused_across_page", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000592` P75: • SPVs might be used to obscure the source of illicit funds. Criminals layer illicit proceeds through a series of transactions via the SPVs, transferring funds to or from financial institutions. This creates a complex web of
  - current `v7en_b000593` P76: financial transactions, preventing detection by law enforcement and regulatory authorities, as it makes the money trail hard to trace.
  - next `v7en_b000594` P76: There are several red flags that indicate attempts to disguise illicit funds or conduct fraudulent activities using SPVs. These include:

### v7u_tmp_pilot_v2fb_money-laundering-risks-associated-with-retail-and-commercial-banking_o000_l020_N000033

- action: manual_review
- rationale: remaining review item requires policy or source judgment
- chapter: Money laundering risks associated with retail and commercial banking
- page: 68 / pdf 73
- heading: Money laundering risks associated with retail and commercial banking / Credit-related product risks
- knowledge_en: fragment about repayment and illegal source of funds
- en_quote: repayment if the source of funds derives from illegal activities or predicate offences to money laundering.
- risk_flags: ["derived_from_fullbook_llm_grouping", "heading_context_reused_across_page", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000527` P67: • Recovery of funds: If the bank knows or suspects the customer is using illicit funds to repay the loan, the risk of default becomes a secondary risk to manage. The bank should not accept funds for the purposes of loan
  - current `v7en_b000528` P68: repayment if the source of funds derives from illegal activities or predicate offences to money laundering.
  - next `v7en_b000529` P68: • Risk appetite: When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval.


## Samples: cross_block_join_candidate

### v7u_tmp_pilot_v2fb_afc-guidance-from-other-organizations_o000_l020_N000008

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: source sentence appears split across adjacent blocks
- chapter: AFC guidance from other organizations
- page: 171 / pdf 176
- heading: AFC guidance from other organizations / G-20 Anti-Corruption Working Group AFC guidance
- knowledge_en: incomplete sentence about G-20 guidance
- en_quote: The G-20 has authored several documents that provide essential guidance on anti-corruption measures, financial transparency, and international
- risk_flags: ["block_may_continue_next", "derived_from_fullbook_llm_grouping", "incomplete_sentence", "needs_human_review_before_freeze", "policy_retained_review", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001350` P171: • Enhancing whistle-blower protection mechanisms.
  - current `v7en_b001351` P171: The G-20 has authored several documents that provide essential guidance on anti-corruption measures, financial transparency, and international
  - next `v7en_b001352` P172: cooperation. They outline strategies for combating illicit financial activities, recovering stolen assets, and enhancing regulatory frameworks across jurisdictions to strengthen governance and promote integrity in both public and private sectors. These include:


## Samples: ignored_text_damage_manual

### v7u_tmp_prefreeze_qa_ignored_N000018

- action: manual_pdf_source_review
- rationale: ignored fragment contains extraction damage
- chapter: Case example: Drafting policies for an AFC department based in APAC
- page: 178 / pdf 183
- heading: Case example: Drafting policies for an AFC department based in APAC
- knowledge_en: Continuously update policies with Íatest regulations and guidance
- en_quote: Continuously update policies with Íatest regulations and guidance
- risk_flags: ["block_may_continue_next", "cross_block_sentence_candidate", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:text_damage_fragment", "needs_human_review_before_freeze", "policy_retained_review", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001415` P178: Implement policies
  - current `v7en_b001416` P178: Continuously update policies with Íatest regulations and guidance
  - next `v7en_b001417` P178: Hiroshi is working for a newly incorporated financial institution based in the Asia-Pacific (APAC) region and was asked to set up policies and procedures for the AFC department. One of his tasks is to identify relevant reports and guidance papers that would impact AFC controls.


## Samples: text_damage_manual_source_review

### v7u_tmp_pilot_v2fb_technology-for-kyc_o080_l020_N000014

- action: manual_pdf_source_review
- rationale: direct text showed extraction damage or PDF text-layer damage
- chapter: Technology for KYC
- page: 424 / pdf 429
- heading: Technology for KYC / Integrating screening technology with other systems
- knowledge_en: Scalability and performance requirements for integrated systems
- en_quote: Organizations should also ensure that their integrated systems are scalable with the growth of the organization and increased data volumes of varying to accommodate the development of the organization and increased data volumes in various formats to accommodate the growth of the organization and increased data volumes, as well as the development of the organization and the varying formats of data. The systems must be able to handle an increase in data requirements without compromising performance.
- risk_flags: ["derived_from_fullbook_llm_grouping", "duplicated_phrase_accommodate", "moved_from_direct_to_review_prefreeze_qa", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b003267` P424: Screening systems should be compatible with other systems. This includes data flows, workflow management tools, and application programming interface (API) integrations. Carrying out a complete assessment of all touchpoints with other systems and understanding the screening process workflow enables a more successful implementation later.
  - current `v7en_b003268` P424: Organizations should also ensure that their integrated systems are scalable with the growth of the organization and increased data volumes of varying to accommodate the development of the organization and increased data volumes in various formats to accommodate the growth of the organization and increased data volumes, as well as the development of the organization and the varying formats of data. The systems must be...
  - next `v7en_b003269` P424: <table><tr><td>Factor <td>Recommended actions <tr><td>Compatibility <td>·Ensure systems are compatible with data flows, workflow management tools, and API integrations.·Complete a compliance system assessment and consider all relevant systems. <tr><td>Scalability <td>·Ensure systems scale with organizational growth and increasing data volumes.·Systems should be able to handle increased data without compromising perfo...
