# v7 Fullbook Review Audit

Generated at: 2026-07-03T10:53:28
Input: `D:\守正公司工作区\cams考试\cams工作台（重构版）\v7\work\base_units\draft\v2_fullbook\v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock_toobroad_policy_zh_enriched.json`

## Summary

- direct items: 4702
- review items: 10
- parent/context items: 271

## Review Classes

- true_fragment_or_incomplete: 5
- other_review: 5

## Direct Text Damage Candidates


## Samples: other_review

### v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000021 · needs_review

- chapter: AFC guidance from leading international organizations
- page: 170
- knowledge_en: IOSCO publication year
- en_quote: IOSCO published the in 2005.
- risk_flags: ["derived_from_fullbook_llm_grouping", "extraction_damage", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_private-banking-and-wealth-management-risks_o020_l020_N000009 · needs_review

- chapter: Private banking and wealth management risks
- page: 76
- knowledge_en: fragment describing money laundering effect
- en_quote: financial transactions, preventing detection by law enforcement and regulatory authorities, as it makes the money trail hard to trace.
- risk_flags: ["derived_from_fullbook_llm_grouping", "heading_context_reused_across_page", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_money-laundering-risks-associated-with-retail-and-commercial-banking_o000_l020_N000033 · needs_review

- chapter: Money laundering risks associated with retail and commercial banking
- page: 68
- knowledge_en: fragment about repayment and illegal source of funds
- en_quote: repayment if the source of funds derives from illegal activities or predicate offences to money laundering.
- risk_flags: ["derived_from_fullbook_llm_grouping", "heading_context_reused_across_page", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_technology-for-kyc_o080_l020_N000014 · needs_review

- chapter: Technology for KYC
- page: 424
- knowledge_en: Scalability and performance requirements for integrated systems
- en_quote: Organizations should also ensure that their integrated systems are scalable with the growth of the organization and increased data volumes of varying to accommodate the development of the organization and increased data volumes in various formats to accommodate the growth of the organization and increased data volumes, as well as the development of the organization and the varying formats of data. The systems must be able to handle an increase in data requirements without compromising performance.
- risk_flags: ["derived_from_fullbook_llm_grouping", "duplicated_phrase_accommodate", "moved_from_direct_to_review_prefreeze_qa", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

### v7u_tmp_prefreeze_qa_ignored_N000018 · needs_review

- chapter: Case example: Drafting policies for an AFC department based in APAC
- page: 178
- knowledge_en: Continuously update policies with Íatest regulations and guidance
- en_quote: Continuously update policies with Íatest regulations and guidance
- risk_flags: ["block_may_continue_next", "cross_block_sentence_candidate", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:text_damage_fragment", "needs_human_review_before_freeze", "policy_retained_review", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

## Samples: true_fragment_or_incomplete

### v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o020_l020_N000049 · needs_review

- chapter: US AML/CFT regulatory landscape
- page: 192
- knowledge_en: fragment: training to national competent authorities
- en_quote: training to national competent authorities.
- risk_flags: ["derived_from_fullbook_llm_grouping", "fragment", "heading_context_reused_across_page", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000014 · needs_review

- chapter: AFC guidance from leading international organizations
- page: 168
- knowledge_en: incomplete sentence about Wolfsberg Group publication
- en_quote: In 2000, the Wolfsberg Group published the .
- risk_flags: ["derived_from_fullbook_llm_grouping", "incomplete_sentence", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000016 · needs_review

- chapter: AFC guidance from leading international organizations
- page: 169
- knowledge_en: Incomplete publication statement
- en_quote: In 2006, the Wolfsberg Group published .
- risk_flags: ["derived_from_fullbook_llm_grouping", "incomplete_sentence", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_ongoing-afc-controls_o000_l020_N000026 · needs_review

- chapter: Ongoing AFC controls
- page: 320
- knowledge_en: fragment about exit policy and sanctions
- en_quote: organization's exit policy, subject to the necessary approvals and special licenses for specific transactions linked to sanctioned individuals and entities.
- risk_flags: ["derived_from_fullbook_llm_grouping", "fragment", "heading_context_reused_across_page", "needs_human_review_before_freeze", "policy_retained_review", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_afc-guidance-from-other-organizations_o000_l020_N000008 · needs_review

- chapter: AFC guidance from other organizations
- page: 171
- knowledge_en: incomplete sentence about G-20 guidance
- en_quote: The G-20 has authored several documents that provide essential guidance on anti-corruption measures, financial transparency, and international
- risk_flags: ["block_may_continue_next", "derived_from_fullbook_llm_grouping", "incomplete_sentence", "needs_human_review_before_freeze", "policy_retained_review", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]
