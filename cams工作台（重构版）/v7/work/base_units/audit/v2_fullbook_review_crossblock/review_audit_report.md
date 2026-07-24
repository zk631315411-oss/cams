# v7 Fullbook Review Audit

Generated at: 2026-07-03T00:55:01
Input: `D:\守正公司工作区\cams考试\cams工作台（重构版）\v7\work\base_units\draft\v2_fullbook\v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock.json`

## Summary

- direct items: 4486
- review items: 141
- parent/context items: 210

## Review Classes

- other_review: 77
- too_broad_but_coherent_candidate: 50
- true_fragment_or_incomplete: 8
- cross_block_continuation_review: 6

## Direct Text Damage Candidates


## Samples: other_review

### v7u_tmp_pilot_v2fb_understanding-afc-technology_o020_l020_N000007 · needs_review

- chapter: Understanding AFC technology
- page: 378
- knowledge_en: Introduction to pros and cons
- en_quote: Some key pros and cons are as follows.
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o040_l020_N000029 · needs_review

- chapter: US AML/CFT regulatory landscape
- page: 195
- knowledge_en: introductory sentence listing UK authorities
- en_quote: The following are major authorities in the UK responsible for issuing guidance, investigating money laundering offenses, and enforcing AML regulations.
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_transaction-monitoring_o060_l020_N000009 · needs_review

- chapter: Transaction monitoring
- page: 344
- knowledge_en: collaboration on next steps
- en_quote: Now others will collaborate in the decision regarding next steps.
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_transaction-monitoring-scenario-calibration-testing_o020_l020_N000018 · needs_review

- chapter: Transaction monitoring scenario calibration testing
- page: 451
- knowledge_en: table introduction
- en_quote: The table below summarizes different categories of technology solutions:
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000020 · needs_review

- chapter: Financial Action Task Force
- page: 150
- knowledge_en: table introduction
- en_quote: The table below lists the area of focus and specific outcomes associated with each of the 11 IOs:
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_three-lines-of-defense_o000_l020_N000034 · needs_review

- chapter: Three lines of defense
- page: 250
- knowledge_en: List introduction
- en_quote: The following is a list of typical AFC functions found within the second line of defense.
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_types-of-financial-crime_o040_l020_N000003 · needs_review

- chapter: Types of financial crime
- page: 29
- knowledge_en: teaching metadata about learning objectives
- en_quote: Knowing the common features of fraud, as well as typical motivations and red flags, will help you combat this crime.
- risk_flags: ["derived_from_fullbook_llm_grouping", "heading_context_reused_across_page", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_governance-and-oversight_o000_l020_N000007 · needs_review

- chapter: Governance and oversight
- page: 291
- knowledge_en: heading question
- en_quote: What are AFC policies and procedures?
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

## Samples: too_broad_but_coherent_candidate

### v7u_tmp_pilot_v2fb_data-as-an-input-for-solutions_o040_l020_N000008 · example

- chapter: Data as an input for solutions
- page: 471
- knowledge_en: AI detection system identifies money laundering at Nova Capital Bank
- en_quote: Nova Capital Bank quickly witnesses the results of this updated technology. Within weeks, the system flags a customer whose patterns deviate from established normal behavior, indicating potential financial crime. The system analyzes large volumes of data, recognizing a relationship between the customer and a previously flagged entity that the conventional rules-based system would have likely missed. This discovery escalates, and the bank ultimately concludes that the customer is laundering money, thanks to Erik, the new detection system, and Nova Capital Bank's extensive internal data.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_data-as-an-input-for-solutions_o040_l020_N000019 · obligation

- chapter: Data as an input for solutions
- page: 472
- knowledge_en: Organizational obligations when using external data
- en_quote: Organizations should take care when using external data. They are accountable for system accuracy. Organizations should validate and test externally provided data for accuracy, reliability, compatibility, and consistency. This is particularly relevant when using open-source or publicly available records.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_technology-for-kyc_o000_l020_N000043 · fact

- chapter: Technology for KYC
- page: 407
- knowledge_en: Benefits of perpetual KYC practices
- en_quote: The implementation of perpetual KYC practices offers multiple benefits for organizations. One major benefit is effective financial crime risk management. By allowing updates and potential reviews, organizations can focus their resources on higher-risk areas. Investing in perpetual KYC practices not only reduces costs but also results in operational efficiencies by minimizing unnecessary reviews triggered by non-risk-increasing factors. Effective use of customer contact channels ensures that customer data remains up to date during each customer interaction, eliminating the need for complete refreshes each time. This, in turn, results in improved customer experience.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_technology-for-kyc_o060_l020_N000021 · definition

- chapter: Technology for KYC
- page: 420
- knowledge_en: Fuzzy logic definition and capabilities
- en_quote: Fuzzy logic is a matching technique that is used to increase the effectiveness of screening processes by overcoming problems such as flawed records and databases. This technique is accomplished through algorithms that use degrees of similarity to determine the probability that two names are the same. Fuzzy logic can find matches in misspelled names, incomplete names, and names with different spellings but similar sounds or phonetics. In addition, fuzzy logic accepts different formats for date of birth and other inconsistencies.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_technology-for-kyc_o060_l020_N000032 · definition

- chapter: Technology for KYC
- page: 421
- knowledge_en: Distinction between tuning and optimization
- en_quote: Tuning is not the same as optimization. Tuning involves adjusting the parameters of an existing system to improve its performance without changing its fundamental structure. In contrast, optimization involves making fundamental changes to the system’s design or algorithms to enhance performance. Optimization can include changing the code, adopting more efficient algorithms, or altering the underlying technology.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_understanding-afc-technology_o020_l020_N000001 · fact

- chapter: Understanding AFC technology
- page: 377
- knowledge_en: Evolution of financial crime prevention and the role of technology and collaboration
- en_quote: Over the past quarter century, financial crime prevention has transitioned from manual, retrospective analysis to automated monitoring and predictive modeling. This shift is driven by technological advancements and collaborative global initiatives. As financial crimes grow more complex, innovation and private-public cooperation remain crucial. By embracing advanced technologies and fostering collaboration, the global community can enhance financial system resilience and protect against financial crimes.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o020_l020_N000006 · case_fact

- chapter: US AML/CFT regulatory landscape
- page: 186
- knowledge_en: SEC charges Wells Fargo affiliates for overcharging advisory fees
- en_quote: In August of 2023, the SEC charged two non-bank affiliates of Wells Fargo, Wells Fargo Clearing Services LLC and Wells Fargo Advisors Financial Network LLC, for overcharging more than 10,900 investment advisory accounts, amounting to over US$26.8 million in excessive fees. The SEC's investigation revealed that certain financial advisers had agreed to reduce advisory fees for clients, but did not enter the reductions into the billing system. Consequently, the financial advisers charged the clients higher fees than agreed upon. Wells Fargo consented to pay a US$35 million civil penalty to resolve the issue on behalf of its affiliates.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o020_l020_N000023 · fact

- chapter: US AML/CFT regulatory landscape
- page: 189
- knowledge_en: Challenges leading to EU AMLD amendments
- en_quote: Many of the EU’s provisions to the AMLDs were to address previous challenges. For example, some member states did not transpose the AMLDs in their national legislation in a timely manner or in full compliance. These factors resulted in lapses, such as banks failing to comply with core requirements and deficiencies in consolidated supervision for cross-border entities. This fragmentation between entities reduced the effectiveness of supervision and cooperation among authorities and resulted in AML breaches.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

## Samples: true_fragment_or_incomplete

### v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o020_l020_N000049 · needs_review

- chapter: US AML/CFT regulatory landscape
- page: 192
- knowledge_en: fragment: training to national competent authorities
- en_quote: training to national competent authorities.
- risk_flags: ["derived_from_fullbook_llm_grouping", "fragment", "heading_context_reused_across_page", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o040_l020_N000040 · needs_review

- chapter: US AML/CFT regulatory landscape
- page: 197
- knowledge_en: Incomplete list introduction
- en_quote: The AML/CTF Amendment Act 2024 introduces several key provisions, including:
- risk_flags: ["derived_from_fullbook_llm_grouping", "heading_context_reused_across_page", "incomplete_sentence", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000034 · needs_review

- chapter: Financial Action Task Force
- page: 154
- knowledge_en: Assessor training definition fragment
- en_quote: Assessor training: Training for the experts who will perform assessment
- risk_flags: ["block_may_continue_next", "cleaned_residual_sub_bullet_marker", "derived_from_fullbook_llm_grouping", "fragment", "possible_list_item", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000038 · needs_review

- chapter: Financial Action Task Force
- page: 155
- knowledge_en: final quality review step
- en_quote: Final quality review: All jurisdictions review the report before publishing
- risk_flags: ["block_may_continue_next", "cleaned_residual_sub_bullet_marker", "derived_from_fullbook_llm_grouping", "fragment", "heading_context_reused_across_page", "paragraph_continues_across_page_candidate", "possible_metadata", "previous_block_may_continue_here", "source_sentence_may_continue_from_previous_block", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000014 · needs_review

- chapter: AFC guidance from leading international organizations
- page: 168
- knowledge_en: incomplete sentence about Wolfsberg Group publication
- en_quote: In 2000, the Wolfsberg Group published the .
- risk_flags: ["derived_from_fullbook_llm_grouping", "incomplete_sentence", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000016 · needs_review

- chapter: AFC guidance from leading international organizations
- page: 169
- knowledge_en: Incomplete publication statement
- en_quote: In 2006, the Wolfsberg Group published .
- risk_flags: ["derived_from_fullbook_llm_grouping", "incomplete_sentence", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_ongoing-afc-controls_o000_l020_N000026 · needs_review

- chapter: Ongoing AFC controls
- page: 320
- knowledge_en: fragment about exit policy and sanctions
- en_quote: organization's exit policy, subject to the necessary approvals and special licenses for specific transactions linked to sanctioned individuals and entities.
- risk_flags: ["derived_from_fullbook_llm_grouping", "fragment", "heading_context_reused_across_page", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_afc-guidance-from-other-organizations_o000_l020_N000008 · needs_review

- chapter: AFC guidance from other organizations
- page: 171
- knowledge_en: incomplete sentence about G-20 guidance
- en_quote: The G-20 has authored several documents that provide essential guidance on anti-corruption measures, financial transparency, and international
- risk_flags: ["block_may_continue_next", "derived_from_fullbook_llm_grouping", "incomplete_sentence", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

## Samples: cross_block_continuation_review

### v7u_tmp_pilot_v2fb_transaction-monitoring_o020_l020_N000001 · red_flag

- chapter: Transaction monitoring
- page: 333
- knowledge_en: excessive channel use as red flag
- en_quote: Excessive use of a particular channel compared to what is expected for that customer type, such as high use of cash over electronic payments
- risk_flags: ["block_may_continue_next", "derived_from_fullbook_llm_grouping", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000035 · needs_review

- chapter: Financial Action Task Force
- page: 154
- knowledge_en: jurisdiction training definition fragment
- en_quote: Jurisdiction training: Training for representatives of the evaluated jurisdictions
- risk_flags: ["block_may_continue_next", "cleaned_residual_sub_bullet_marker", "derived_from_fullbook_llm_grouping", "previous_block_may_continue_here", "source_sentence_may_continue_from_previous_block", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000036 · needs_review

- chapter: Financial Action Task Force
- page: 154
- knowledge_en: subheading fragment
- en_quote: Selection of assessors: Selection of the experts that form the assessment team
- risk_flags: ["block_may_continue_next", "cleaned_residual_sub_bullet_marker", "derived_from_fullbook_llm_grouping", "previous_block_may_continue_here", "source_sentence_may_continue_from_previous_block", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000037 · needs_review

- chapter: Financial Action Task Force
- page: 154
- knowledge_en: FATF plenary discussion and voting on ratings
- en_quote: Plenary discussion: FATF plenary discusses the findings in the report and votes on the ratings
- risk_flags: ["block_may_continue_next", "cleaned_residual_sub_bullet_marker", "derived_from_fullbook_llm_grouping", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_types-of-financial-crime_o000_l020_N000007 · definition

- chapter: Types of financial crime
- page: 22
- knowledge_en: Piracy definition
- en_quote: 20.Piracy: Maritime or cyber-based hijacking for financial gain
- risk_flags: ["block_may_continue_next", "derived_from_fullbook_llm_grouping", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

### v7u_tmp_pilot_v2fb_types-of-risk-assessment_o000_l020_N000005 · fact

- chapter: Types of risk assessment
- page: 267
- knowledge_en: Risks vary in nature, scale, and impact
- en_quote: Risks can vary in their nature, scale, and impact.
- risk_flags: ["derived_from_fullbook_llm_grouping", "heading_context_reused_across_page", "paragraph_continues_across_page_candidate", "source_sentence_may_continue_from_previous_block", "zh_subspan_unavailable"]
