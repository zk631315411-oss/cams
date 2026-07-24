# v7 Review Resolution Plan

Generated at: 2026-07-03T00:56:44
Input: `D:\守正公司工作区\cams考试\cams工作台（重构版）\v7\work\base_units\draft\v2_fullbook\v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock.json`

## Summary

- review items: 141

## Resolution Classes

- too_broad_resplit_candidate: 50
- manual_policy_review: 31
- ignored_visual_label_group_review: 22
- structural_parent_candidate: 9
- cross_block_join_candidate: 9
- ignored_short_bullet_neighbor_context_review: 8
- fragment_neighbor_join_or_discard: 5
- ignored_prose_llm_split_candidate: 2
- ignored_review_other: 2
- text_damage_manual_source_review: 1
- ignored_text_damage_manual: 1
- ignored_short_context_label_review: 1

## Recommended Actions

- rerun_llm_resplit_on_unit: 50
- manual_review: 33
- inspect_visual_or_table_group: 22
- inspect_neighbor_blocks_or_pdf_join: 17
- demote_to_parent_or_context: 9
- inspect_neighbor_blocks_then_join_or_discard: 5
- manual_pdf_source_review: 2
- run_sentence_grouping_or_manual_split: 2
- decide_context_parent_or_discard: 1

## Samples: too_broad_resplit_candidate

### v7u_tmp_pilot_v2fb_data-as-an-input-for-solutions_o040_l020_N000008

- action: rerun_llm_resplit_on_unit
- rationale: unit is coherent but exceeds the direct width gate
- chapter: Data as an input for solutions
- page: 471 / pdf 476
- heading: Data as an input for solutions / Case example: AI for money laundering detection
- knowledge_en: AI detection system identifies money laundering at Nova Capital Bank
- en_quote: Nova Capital Bank quickly witnesses the results of this updated technology. Within weeks, the system flags a customer whose patterns deviate from established normal behavior, indicating potential financial crime. The system analyzes large volumes of data, recognizing a relationship between the customer and a previously flagged entity that the conventional rules-based system would have likely missed. This discovery escalates, and the bank ultimately concludes that the customer is laundering money, thanks to Erik, the new detection system, and Nova Capital Bank's extensive internal data.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b003541` P471: After several months of testing and considering the guidance of the AI council within his organization, Erik finally convinces his organization to employ AI technologies to improve the efficiency and effectiveness of financial crime detection using internal data. Rather than defining a prescriptive risk and then mapping data points to it, the new system collates as much data as possible and uses it to construct a hol...
  - current `v7en_b003542` P471: Nova Capital Bank quickly witnesses the results of this updated technology. Within weeks, the system flags a customer whose patterns deviate from established normal behavior, indicating potential financial crime. The system analyzes large volumes of data, recognizing a relationship between the customer and a previously flagged entity that the conventional rules-based system would have likely missed. This discovery es...
  - next `v7en_b003543` P471: A common expectation is that AI systems are deployed to yield head count efficiencies. In Erik’s case, the goal was to make the ecosystem more effective at detecting financial crime, which was achieved.

### v7u_tmp_pilot_v2fb_data-as-an-input-for-solutions_o040_l020_N000019

- action: rerun_llm_resplit_on_unit
- rationale: unit is coherent but exceeds the direct width gate
- chapter: Data as an input for solutions
- page: 472 / pdf 477
- heading: Data as an input for solutions / External data
- knowledge_en: Organizational obligations when using external data
- en_quote: Organizations should take care when using external data. They are accountable for system accuracy. Organizations should validate and test externally provided data for accuracy, reliability, compatibility, and consistency. This is particularly relevant when using open-source or publicly available records.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b003551` P472: Organizations also use external data to perform a specific function, such as list screening. For larger financial institutions, data sources are usually third-party providers who collate data from multiple sources and provide a single preconfigured dataset. Another example of a specific function for external data is adverse media screening, which sources can supply automatically or manually.
  - current `v7en_b003552` P472: Organizations should take care when using external data. They are accountable for system accuracy. Organizations should validate and test externally provided data for accuracy, reliability, compatibility, and consistency. This is particularly relevant when using open-source or publicly available records.
  - next `v7en_b003553` P473: Organizations should consider the source of external data and whether additional checks are needed to validate its quality or assess potential malicious data or misinformation, such as incorrect adverse media reports. AI products provide useful information, but AI responses should be verified like any external data. It is more appropriate to use AI to locate primary sources, which can then be verified for accuracy. O...

### v7u_tmp_pilot_v2fb_technology-for-kyc_o000_l020_N000043

- action: rerun_llm_resplit_on_unit
- rationale: unit is coherent but exceeds the direct width gate
- chapter: Technology for KYC
- page: 407 / pdf 412
- heading: Technology for KYC / Perpetual KYC
- knowledge_en: Benefits of perpetual KYC practices
- en_quote: The implementation of perpetual KYC practices offers multiple benefits for organizations. One major benefit is effective financial crime risk management. By allowing updates and potential reviews, organizations can focus their resources on higher-risk areas. Investing in perpetual KYC practices not only reduces costs but also results in operational efficiencies by minimizing unnecessary reviews triggered by non-risk-increasing factors. Effective use of customer contact channels ensures that customer data remains up to date during each customer interaction, eliminating the need for complete refreshes each time. This, in turn, results in improved customer experience.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b003150` P407: External data might include voter registers, PEP databases, and other publicly available information. This approach leads organizations to adopt a data-led methodology, allowing customer file reviews to focus on the highest-risk customers on an “as-often-as-needed” basis. Perpetual KYC does not eliminate the need to carry out customer file reviews. It is a practice that ensures data is up to date, making any necessar...
  - current `v7en_b003151` P407: The implementation of perpetual KYC practices offers multiple benefits for organizations. One major benefit is effective financial crime risk management. By allowing updates and potential reviews, organizations can focus their resources on higher-risk areas. Investing in perpetual KYC practices not only reduces costs but also results in operational efficiencies by minimizing unnecessary reviews triggered by non-risk-...
  - next `v7en_b003152` P407: Effective risk management

### v7u_tmp_pilot_v2fb_technology-for-kyc_o060_l020_N000021

- action: rerun_llm_resplit_on_unit
- rationale: unit is coherent but exceeds the direct width gate
- chapter: Technology for KYC
- page: 420 / pdf 425
- heading: Technology for KYC / Fuzzy logic and partial matches
- knowledge_en: Fuzzy logic definition and capabilities
- en_quote: Fuzzy logic is a matching technique that is used to increase the effectiveness of screening processes by overcoming problems such as flawed records and databases. This technique is accomplished through algorithms that use degrees of similarity to determine the probability that two names are the same. Fuzzy logic can find matches in misspelled names, incomplete names, and names with different spellings but similar sounds or phonetics. In addition, fuzzy logic accepts different formats for date of birth and other inconsistencies.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b003232` P420: ## Fuzzy logic and partial matches
  - current `v7en_b003233` P420: Fuzzy logic is a matching technique that is used to increase the effectiveness of screening processes by overcoming problems such as flawed records and databases. This technique is accomplished through algorithms that use degrees of similarity to determine the probability that two names are the same. Fuzzy logic can find matches in misspelled names, incomplete names, and names with different spellings but similar sou...
  - next `v7en_b003234` P420: A partial match means the entity being screened is similar to an entry on a list, based on fuzzy logic and potentially other identifying factors, such as date of birth. Partial matches require further human intervention to determine if the match is a true match.

### v7u_tmp_pilot_v2fb_technology-for-kyc_o060_l020_N000032

- action: rerun_llm_resplit_on_unit
- rationale: unit is coherent but exceeds the direct width gate
- chapter: Technology for KYC
- page: 421 / pdf 426
- heading: Technology for KYC / Screening system tuning
- knowledge_en: Distinction between tuning and optimization
- en_quote: Tuning is not the same as optimization. Tuning involves adjusting the parameters of an existing system to improve its performance without changing its fundamental structure. In contrast, optimization involves making fundamental changes to the system’s design or algorithms to enhance performance. Optimization can include changing the code, adopting more efficient algorithms, or altering the underlying technology.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b003243` P421: Regulators around the world emphasize the importance of tuning screening systems to improve their effectiveness and efficiency. Untuned systems may fail to identify issues in time, leading to significant compliance breaches.
  - current `v7en_b003244` P421: Tuning is not the same as optimization. Tuning involves adjusting the parameters of an existing system to improve its performance without changing its fundamental structure. In contrast, optimization involves making fundamental changes to the system’s design or algorithms to enhance performance. Optimization can include changing the code, adopting more efficient algorithms, or altering the underlying technology.
  - next `v7en_b003245` P421: Although there are no fixed requirements for when to tune a system, good practice recommends tuning a system three months after implementation and then at least once a year or every six months, depending on its complexity. Some organizations tune their systems more frequently.

### v7u_tmp_pilot_v2fb_understanding-afc-technology_o020_l020_N000001

- action: rerun_llm_resplit_on_unit
- rationale: unit is coherent but exceeds the direct width gate
- chapter: Understanding AFC technology
- page: 377 / pdf 382
- heading: Understanding AFC technology / Global AFC innovation
- knowledge_en: Evolution of financial crime prevention and the role of technology and collaboration
- en_quote: Over the past quarter century, financial crime prevention has transitioned from manual, retrospective analysis to automated monitoring and predictive modeling. This shift is driven by technological advancements and collaborative global initiatives. As financial crimes grow more complex, innovation and private-public cooperation remain crucial. By embracing advanced technologies and fostering collaboration, the global community can enhance financial system resilience and protect against financial crimes.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002973` P377: • Technological adoption mandates, such as the US AML Act of 2020 and FATF guidance, encourage financial institutions to modernize and integrate innovative technologies.
  - current `v7en_b002974` P377: Over the past quarter century, financial crime prevention has transitioned from manual, retrospective analysis to automated monitoring and predictive modeling. This shift is driven by technological advancements and collaborative global initiatives. As financial crimes grow more complex, innovation and private-public cooperation remain crucial. By embracing advanced technologies and fostering collaboration, the global...
  - next `v7en_b002975` P377: As financial crime prevention has evolved, so have criminals. Many organized crime groups use sophisticated AI-based technology and innovative techniques to produce synthetic identities and deepfakes and to get around AML controls. This technological race has made it even more imperative that organizations consider how they can stay ahead of criminals.

### v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o020_l020_N000006

- action: rerun_llm_resplit_on_unit
- rationale: unit is coherent but exceeds the direct width gate
- chapter: US AML/CFT regulatory landscape
- page: 186 / pdf 191
- heading: US AML/CFT regulatory landscape / Case study: US regulatory enforcement actions
- knowledge_en: SEC charges Wells Fargo affiliates for overcharging advisory fees
- en_quote: In August of 2023, the SEC charged two non-bank affiliates of Wells Fargo, Wells Fargo Clearing Services LLC and Wells Fargo Advisors Financial Network LLC, for overcharging more than 10,900 investment advisory accounts, amounting to over US$26.8 million in excessive fees. The SEC's investigation revealed that certain financial advisers had agreed to reduce advisory fees for clients, but did not enter the reductions into the billing system. Consequently, the financial advisers charged the clients higher fees than agreed upon. Wells Fargo consented to pay a US$35 million civil penalty to resolve the issue on behalf of its affiliates.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001493` P186: In March of 2023, the Federal Reserve Board imposed a US$67.8 million fine on Wells Fargo for providing a trade finance software platform to a foreign bank. The foreign bank used the platform to conduct transactions involving parties subject to US sanctions. The Federal Reserve Board concluded that Wells Fargo had insufficient policies and procedures to ensure compliance with US sanctions laws, leading to transaction...
  - current `v7en_b001494` P186: In August of 2023, the SEC charged two non-bank affiliates of Wells Fargo, Wells Fargo Clearing Services LLC and Wells Fargo Advisors Financial Network LLC, for overcharging more than 10,900 investment advisory accounts, amounting to over US$26.8 million in excessive fees. The SEC's investigation revealed that certain financial advisers had agreed to reduce advisory fees for clients, but did not enter the reductions ...
  - next `v7en_b001495` P186: In September of 2024, the OCC issued an enforcement action against Wells Fargo, identifying deficiencies in the bank's financial crimes risk management and AML controls. The OCC's formal agreement highlighted issues in areas such as suspicious activity reporting, currency transaction reporting, CDD, and customer identification programs. While the OCC did not impose monetary penalties, the agreement required Wells Far...

### v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o020_l020_N000023

- action: rerun_llm_resplit_on_unit
- rationale: unit is coherent but exceeds the direct width gate
- chapter: US AML/CFT regulatory landscape
- page: 189 / pdf 194
- heading: US AML/CFT regulatory landscape / History of AML regime in Europe
- knowledge_en: Challenges leading to EU AMLD amendments
- en_quote: Many of the EU’s provisions to the AMLDs were to address previous challenges. For example, some member states did not transpose the AMLDs in their national legislation in a timely manner or in full compliance. These factors resulted in lapses, such as banks failing to comply with core requirements and deficiencies in consolidated supervision for cross-border entities. This fragmentation between entities reduced the effectiveness of supervision and cooperation among authorities and resulted in AML breaches.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001512` P189: Since 1991, the EU has used directives to establish its AML/CFT regime. The first AML directive (1AMLD) primarily applied to banks and required member states to criminalize money laundering. Since then, the EU has amended the AMLDs, with the 2AMLD in 2001, 3AMLD in 2005, 4AMLD in 2015, and 5AMLD in 2018.
  - current `v7en_b001513` P189: Many of the EU’s provisions to the AMLDs were to address previous challenges. For example, some member states did not transpose the AMLDs in their national legislation in a timely manner or in full compliance. These factors resulted in lapses, such as banks failing to comply with core requirements and deficiencies in consolidated supervision for cross-border entities. This fragmentation between entities reduced the e...
  - next `v7en_b001514` P189: Until 2018, member states differed on the predicate offenses for money laundering. This led the EU to pass Directive 2018/1673, or the “AML Criminal Law Directive,” which establishes minimum rules concerning the definition of criminal offenses and penalties for money laundering. In 2024, the EU amended Directive 2018/1673 to ensure that violations of EU restrictive measures constitute a criminal offense. The EU also ...

### v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o060_l020_N000022

- action: rerun_llm_resplit_on_unit
- rationale: unit is coherent but exceeds the direct width gate
- chapter: US AML/CFT regulatory landscape
- page: 200 / pdf 205
- heading: US AML/CFT regulatory landscape / China AML regulations
- knowledge_en: Key expansions in revised AML Law
- en_quote: This revised AML Law expands the scope of the previous regime, both in terms of predicate offenses and in terms of sectors covered by the law. In doing so, the revisions aim to provide flexibility to address evolving risks. In terms of predicate offenses, the revised law now applies to any criminal activity. Additional sectors covered by the law include law firms, real estate agencies, and dealers in precious gems. Importantly, the revised law has extraterritorial application, extending the jurisdiction to include activities that occur outside of China, but which are deemed to pose a threat to China or its citizens.
- risk_flags: ["antecedent_requires_prior_context", "derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001598` P200: China revised its AML Law, which took effect on January 1, 2025. This revision reflects China’s commitment to aligning with international standards, particularly the FATF Recommendations, while addressing emerging risks in digital finance and cross-border crime.
  - current `v7en_b001599` P200: This revised AML Law expands the scope of the previous regime, both in terms of predicate offenses and in terms of sectors covered by the law. In doing so, the revisions aim to provide flexibility to address evolving risks. In terms of predicate offenses, the revised law now applies to any criminal activity. Additional sectors covered by the law include law firms, real estate agencies, and dealers in precious gems. I...
  - next `v7en_b001600` P200: Under the AML Law, obliged entities must abide by enhanced compliance obligations such as implementing enhanced internal controls, conducting CDD, and reporting suspicious transactions. The revised law emphasizes ongoing monitoring and mandates simplified CDD for low-risk clients to balance compliance and service efficiency. This law strengthens enforcement and escalates penalties for noncompliance, with large fines ...

### v7u_tmp_pilot_v2fb_concluding-an-investigation-and-suspicious-activity-reporting_o000_l020_N000001

- action: rerun_llm_resplit_on_unit
- rationale: unit is coherent but exceeds the direct width gate
- chapter: Concluding an investigation and suspicious activity reporting
- page: 350 / pdf 355
- heading: Concluding an investigation and suspicious activity reporting / Protecting the organization during an investigation
- knowledge_en: Reasons for investigations and consequences of weak AFC
- en_quote: Investigations by law enforcement, prosecutors, or regulatory authorities involving an organization can occur for various reasons. They can be against customers or employees of the organization or against the organization itself. They might result from fraud by its employees. More often, they occur because the organization has a weak or failing AFC program. Such failures increase the risk of money laundering, terrorist financing, and sanctions evasion.
- risk_flags: ["derived_from_fullbook_llm_grouping", "llm_group_too_broad_needs_review", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002789` P350: ## Protecting the organization during an investigation
  - current `v7en_b002790` P350: Investigations by law enforcement, prosecutors, or regulatory authorities involving an organization can occur for various reasons. They can be against customers or employees of the organization or against the organization itself. They might result from fraud by its employees. More often, they occur because the organization has a weak or failing AFC program. Such failures increase the risk of money laundering, terrori...
  - next `v7en_b002791` P350: To mitigate these risks, the organization must establish and maintain strong policies and procedures.


## Samples: manual_policy_review

### v7u_tmp_pilot_v2fb_transaction-monitoring_o060_l020_N000009

- action: manual_review
- rationale: remaining review item requires policy or source judgment
- chapter: Transaction monitoring
- page: 344 / pdf 349
- heading: Transaction monitoring / Suspicious activity escalation process
- knowledge_en: collaboration on next steps
- en_quote: Now others will collaborate in the decision regarding next steps.
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002755` P344: Throughout their research, investigators have been relying on the work and support of others. Some might have done previous research, perhaps when preparing a customer profile or researching previous transaction alerts. Some might have provided the information they personally know about the customer. Investigators filtered, organized, and prioritized. They relied on all of those sources and adequately documented the ...
  - current `v7en_b002756` P344: Now others will collaborate in the decision regarding next steps.
  - next `v7en_b002757` P344: Because each jurisdiction and organization is unique, the roles of people involved and the processes they use will differ. Failing to follow the process carefully can lead to legal and regulatory consequences. So, ask, learn, and move thoughtfully.

### v7u_tmp_pilot_v2fb_types-of-financial-crime_o040_l020_N000003

- action: manual_review
- rationale: remaining review item requires policy or source judgment
- chapter: Types of financial crime
- page: 29 / pdf 34
- heading: Types of financial crime / Key takeaways
- knowledge_en: teaching metadata about learning objectives
- en_quote: Knowing the common features of fraud, as well as typical motivations and red flags, will help you combat this crime.
- risk_flags: ["derived_from_fullbook_llm_grouping", "heading_context_reused_across_page", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000255` P28: The Common Reporting Standard (CRS), developed in response to the G-20 countries' request and approved by the OECD (Organization for Economic Cooperation and Development) Council, calls on jurisdictions to obtain information from their financial institutions and automatically exchange that information with other jurisdictions on an annual basis. It sets out the financia account information to be exchanged, the financ...
  - current `v7en_b000256` P29: Fraud is an intentional act of criminal deception in order to obtain an unjust or illegal advantage. Typically, fraud results in financial or personal gain. Notice that fraud is intentional and uses deception to achieve the goal. Fraud can be committed by one or more individuals—from low-level employees, to management, to government officials. It can be found in every country and every type of business. Knowing the c...
  - next `v7en_b000257` P29: People commit fraud for three major reasons: pressure, opportunity, and rationalization. This three-sided model is referred to as the “Fraud Triangle.” Pressure is sometimes called "incentive." It can be a financial problem that drives a person to commit fraud, such as gambling or other debt. This can create the pressure to commit fraud. Opportunity is often provided by a lack of effective internal controls within an...

### v7u_tmp_pilot_v2fb_governance-and-oversight_o000_l020_N000007

- action: manual_review
- rationale: remaining review item requires policy or source judgment
- chapter: Governance and oversight
- page: 291 / pdf 296
- heading: Governance and oversight / Drafting AFC policies and procedures
- knowledge_en: heading question
- en_quote: What are AFC policies and procedures?
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002274` P291: AFC policies and procedures form the core of an organization’s AFC compliance framework, ensuring effective risk management, adherence to regulations, and operational integrity. These policies must be clear, risk-based, and adaptable to evolving business models while aligning with global and jurisdictional AFC standards.
  - current `v7en_b002275` P291: What are AFC policies and procedures?
  - next `v7en_b002276` P291: • Policies establish the principles, objectives, and regulatory obligations for AFC compliance. They translate legal and regulatory requirements into business-specific commitments.

### v7u_tmp_pilot_v2fb_governance-and-oversight_o000_l020_N000008

- action: manual_review
- rationale: remaining review item requires policy or source judgment
- chapter: Governance and oversight
- page: 291 / pdf 296
- heading: Governance and oversight / Drafting AFC policies and procedures
- knowledge_en: heading question
- en_quote: Why are AFC policies and procedures important?
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002277` P291: • Procedures provide detailed, step-by-step implementation guidance to ensure policies are applied consistently across different business units and jurisdictions. Separate procedures are often written for a policy to tailor its execution to various business units and jurisdictions.
  - current `v7en_b002278` P291: Why are AFC policies and procedures important?
  - next `v7en_b002279` P291: • Policies and procedures ensure regulatory compliance. Institutions typically choose to align their policies with FATF Recommendations, Basel Committee on Banking Supervision (BCBS) guidelines, national AML laws, and regulatory expectations.

### v7u_tmp_pilot_v2fb_governance-and-oversight_o000_l020_N000013

- action: manual_review
- rationale: remaining review item requires policy or source judgment
- chapter: Governance and oversight
- page: 292 / pdf 297
- heading: Governance and oversight / Drafting AFC policies and procedures
- knowledge_en: heading or question
- en_quote: How are AFC policies designed and implemented?
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002284` P292: Good policies should include provisions for addressing any exceptions or exemptions and should clearly assign responsibilities to specific people or roles. They should also provide a schedule for reviewing the policy, typically on an annual basis, and stipulate events that would trigger an ad hoc review and update. Examples include the introduction of a new product or the occurrence of a relevant regulatory event. De...
  - current `v7en_b002285` P292: How are AFC policies designed and implemented?
  - next `v7en_b002286` P292: • Using a risk-based approach, organizations should customize policies based on customer, product, and transaction risks.

### v7u_tmp_pilot_v2fb_money-laundering-risks-in-financial-services_o000_l020_N000001

- action: manual_review
- rationale: remaining review item requires policy or source judgment
- chapter: Money Laundering Risks in Financial Services
- page: 50 / pdf 55
- heading: Money Laundering Risks in Financial Services / Introduction: Money laundering risks in financial services
- knowledge_en: module overview
- en_quote: This module covers various money laundering risks associated with financial services.
- risk_flags: ["antecedent_requires_prior_context", "derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000396` P50: ## Introduction: Money laundering risks in financial services
  - current `v7en_b000397` P50: This module covers various money laundering risks associated with financial services. The financial services sector is integral to the global economy, facilitating the movement and management of capital across borders. Given its central role, this industry is particularly vulnerable to the risks of money laundering. Understanding these risks is necessary for maintaining compliance, protecting the integrity of the fin...
  - next `v7en_b000398` P50: ## Student note: Sector-specific case studies

### v7u_tmp_pilot_v2fb_money-laundering-risks-in-financial-services_o000_l020_N000005

- action: manual_review
- rationale: remaining review item requires policy or source judgment
- chapter: Money Laundering Risks in Financial Services
- page: 50 / pdf 55
- heading: Money Laundering Risks in Financial Services / Introduction: Money laundering risks in financial services
- knowledge_en: learning outcomes
- en_quote: By learning these topics, you will be equipped to identify vulnerabilities, implement effective controls, and manage and mitigate risks, ensuring your organization remains secure and trusted by customers.
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000396` P50: ## Introduction: Money laundering risks in financial services
  - current `v7en_b000397` P50: This module covers various money laundering risks associated with financial services. The financial services sector is integral to the global economy, facilitating the movement and management of capital across borders. Given its central role, this industry is particularly vulnerable to the risks of money laundering. Understanding these risks is necessary for maintaining compliance, protecting the integrity of the fin...
  - next `v7en_b000398` P50: ## Student note: Sector-specific case studies

### v7u_tmp_pilot_v2fb_money-laundering-risks-in-financial-services_o000_l020_N000007

- action: manual_review
- rationale: remaining review item requires policy or source judgment
- chapter: Money Laundering Risks in Financial Services
- page: 50 / pdf 55
- heading: Money Laundering Risks in Financial Services / Student note: Sector-specific case studies
- knowledge_en: Encouragement to take sector-specific courses
- en_quote: For a detailed explanation and analysis of a specific sector, we encourage you to take one of our sector-specific case study courses.
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000398` P50: ## Student note: Sector-specific case studies
  - current `v7en_b000399` P50: This module will cover the key ML risks of various sectors, products, and services. For a detailed explanation and analysis of a specific sector, we encourage you to take one of our sector-specific case study courses.
  - next `v7en_b000400` P51: ## Case example: A new corporate banking role

### v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000021

- action: manual_review
- rationale: remaining review item requires policy or source judgment
- chapter: AFC guidance from leading international organizations
- page: 170 / pdf 175
- heading: AFC guidance from leading international organizations / International Organization of Securities Commissions AFC guidance
- knowledge_en: IOSCO publication year
- en_quote: IOSCO published the in 2005.
- risk_flags: ["derived_from_fullbook_llm_grouping", "extraction_damage", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001332` P170: IOSCO supports its members with technical assistance, education, and training.
  - current `v7en_b001333` P170: IOSCO published the in 2005. It provides AML guidance specifically for collective investment schemes such as mutual funds and exchange-traded funds. The guidance outlines policies, procedures, and client identification measures to mitigate the risk of money laundering in the industry.
  - next `v7en_b001334` P170: In 2003, the BCBS, International Association of Insurance Supervisors (IAIS), and IOSCO published a joint note detailing initiatives to combat AML/CFT. The note provided an overview of common AML/CFT standards across the three sectors and assessed gaps or inconsistencies in approaches. It also examined the relationships between institutions and their customers, focusing on vulnerable products or services.

### v7u_tmp_pilot_v2fb_private-banking-and-wealth-management-risks_o000_l020_N000010

- action: manual_review
- rationale: remaining review item requires policy or source judgment
- chapter: Private banking and wealth management risks
- page: 72 / pdf 77
- heading: Private banking and wealth management risks / Money laundering risks associated with private banking and wealth management
- knowledge_en: introductory sentence listing risks
- en_quote: Here are a few higher risks associated with private banking and wealth management.
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000554` P72: The compliance department must be empowered and robust in its approach to providing proper oversight and challenges to the business. Business leaders should use a balanced scorecard for performance evaluation. This ensures that managing risk remains a fundamental part of the private banker's role.
  - current `v7en_b000555` P72: Here are a few higher risks associated with private banking and wealth management.
  - next `v7en_b000556` P72: ## High-risk private banking and wealth management products


## Samples: ignored_visual_label_group_review

### v7u_tmp_prefreeze_qa_ignored_N000014

- action: inspect_visual_or_table_group
- rationale: short visual/table label needs its surrounding figure/table context
- chapter: Case example: Drafting policies for an AFC department based in APAC
- page: 178 / pdf 183
- heading: Case example: Drafting policies for an AFC department based in APAC
- knowledge_en: Understand risks
- en_quote: Understand risks
- risk_flags: ["ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:visual_or_table_label", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001411` P178: # Case example: Drafting policies for an AFC department based in APAC
  - current `v7en_b001412` P178: Understand risks
  - next `v7en_b001413` P178: Identify regulations and guidance

### v7u_tmp_prefreeze_qa_ignored_N000015

- action: inspect_visual_or_table_group
- rationale: short visual/table label needs its surrounding figure/table context
- chapter: Case example: Drafting policies for an AFC department based in APAC
- page: 178 / pdf 183
- heading: Case example: Drafting policies for an AFC department based in APAC
- knowledge_en: Identify regulations and guidance
- en_quote: Identify regulations and guidance
- risk_flags: ["block_may_continue_next", "cross_block_sentence_candidate", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:visual_or_table_label", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001412` P178: Understand risks
  - current `v7en_b001413` P178: Identify regulations and guidance
  - next `v7en_b001414` P178: Map requirements and draft policies

### v7u_tmp_prefreeze_qa_ignored_N000016

- action: inspect_visual_or_table_group
- rationale: short visual/table label needs its surrounding figure/table context
- chapter: Case example: Drafting policies for an AFC department based in APAC
- page: 178 / pdf 183
- heading: Case example: Drafting policies for an AFC department based in APAC
- knowledge_en: Map requirements and draft policies
- en_quote: Map requirements and draft policies
- risk_flags: ["block_may_continue_next", "cross_block_sentence_candidate", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:visual_or_table_label", "needs_human_review_before_freeze", "previous_block_may_continue_here", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001413` P178: Identify regulations and guidance
  - current `v7en_b001414` P178: Map requirements and draft policies
  - next `v7en_b001415` P178: Implement policies

### v7u_tmp_prefreeze_qa_ignored_N000017

- action: inspect_visual_or_table_group
- rationale: short visual/table label needs its surrounding figure/table context
- chapter: Case example: Drafting policies for an AFC department based in APAC
- page: 178 / pdf 183
- heading: Case example: Drafting policies for an AFC department based in APAC
- knowledge_en: Implement policies
- en_quote: Implement policies
- risk_flags: ["ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:visual_or_table_label", "needs_human_review_before_freeze", "previous_block_may_continue_here", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001414` P178: Map requirements and draft policies
  - current `v7en_b001415` P178: Implement policies
  - next `v7en_b001416` P178: Continuously update policies with Íatest regulations and guidance

### v7u_tmp_prefreeze_qa_ignored_N000019

- action: inspect_visual_or_table_group
- rationale: short visual/table label needs its surrounding figure/table context
- chapter: Types of risk assessment
- page: 267 / pdf 272
- heading: Types of risk assessment / The importance of risk assessment in AFC
- knowledge_en: National risk assessment (NRA)
- en_quote: National risk assessment (NRA)
- risk_flags: ["block_may_continue_next", "cross_block_sentence_candidate", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:visual_or_table_label", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002101` P267: Risk assessments and the risk-based approach (RBA) are important for understanding and analyzing risks. Taking necessary measures to mitigate risks minimizes their effects on a country or entity. The FATF Interpretive Note to Recommendation 1 also highlights the importance of the RBA.
  - current `v7en_b002102` P267: National risk assessment (NRA)
  - next `v7en_b002103` P267: Sectoral risk assessment (SRA)

### v7u_tmp_prefreeze_qa_ignored_N000020

- action: inspect_visual_or_table_group
- rationale: short visual/table label needs its surrounding figure/table context
- chapter: Types of risk assessment
- page: 267 / pdf 272
- heading: Types of risk assessment / The importance of risk assessment in AFC
- knowledge_en: Sectoral risk assessment (SRA)
- en_quote: Sectoral risk assessment (SRA)
- risk_flags: ["block_may_continue_next", "cross_block_sentence_candidate", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:visual_or_table_label", "needs_human_review_before_freeze", "previous_block_may_continue_here", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002102` P267: National risk assessment (NRA)
  - current `v7en_b002103` P267: Sectoral risk assessment (SRA)
  - next `v7en_b002104` P265: Enterprise-wide risk assessment (EWRA)

### v7u_tmp_prefreeze_qa_ignored_N000021

- action: inspect_visual_or_table_group
- rationale: short visual/table label needs its surrounding figure/table context
- chapter: Types of risk assessment
- page: 265 / pdf 270
- heading: Types of risk assessment / The importance of risk assessment in AFC
- knowledge_en: Enterprise-wide risk assessment (EWRA)
- en_quote: Enterprise-wide risk assessment (EWRA)
- risk_flags: ["block_may_continue_next", "cross_block_sentence_candidate", "heading_context_reused_across_page", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:visual_or_table_label", "needs_human_review_before_freeze", "paragraph_continues_across_page_candidate", "previous_block_may_continue_here", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002103` P267: Sectoral risk assessment (SRA)
  - current `v7en_b002104` P265: Enterprise-wide risk assessment (EWRA)
  - next `v7en_b002105` P267: Risks can vary in their nature, scale, and impact. An RBA requires countries and financial institutions to prioritize risks and apply appropriate measures based on their level of exposure. Not every risk applies to every institution. Understanding these factors will allow financial institutions to make informed decisions to balance risk and reward.

### v7u_tmp_prefreeze_qa_ignored_N000022

- action: inspect_visual_or_table_group
- rationale: short visual/table label needs its surrounding figure/table context
- chapter: Enterprise-wide risk assessment
- page: 276 / pdf 281
- heading: Enterprise-wide risk assessment / Determining inherent risks
- knowledge_en: Inherent risk matrix and key
- en_quote: Inherent risk matrix and key
- risk_flags: ["block_may_continue_next", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:visual_or_table_label", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002173` P276: Applying a risk-based approach refers to prioritizing risks that have high probability and severe impact. This does not mean an organization will not address other risks. It just means the organization will apply more resources, effort, and investment to building controls for the highest risks. The inherent risk assessment process should clearly prioritize the highest risks for the organization. A scoring mechanism m...
  - current `v7en_b002174` P276: Inherent risk matrix and key
  - next `v7en_b002175` PNone: <table><tr> Probability Impact <tr><td>Insignificant <td>Minor <td>Moderate <td>Major <td>Severe <tr><td>Almost certain <td> <td> <td> <td> <td> <tr><td>Likely <td> <td> <td> <td> <td> <tr><td>Possible <td> <td> <td> <td> <td> <tr><td>Unlikely <td> <td> <td> <td> <td> <tr><td>Rare <td> <td> <td> <td> <td>

### v7u_tmp_prefreeze_qa_ignored_N000024

- action: inspect_visual_or_table_group
- rationale: short visual/table label needs its surrounding figure/table context
- chapter: Onboarding AFC controls
- page: 307 / pdf 312
- heading: Onboarding AFC controls / Customer risk assessment
- knowledge_en: Customer profile
- en_quote: Customer profile
- risk_flags: ["ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:visual_or_table_label", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002429` P307: • Transactional behavior: Identify deviations from expected transaction patterns, unexplained high-volume cross-border transactions, or the use of complex payment structures.
  - current `v7en_b002430` P307: Customer profile
  - next `v7en_b002431` P307: Evaluating risks posed by customers

### v7u_tmp_prefreeze_qa_ignored_N000025

- action: inspect_visual_or_table_group
- rationale: short visual/table label needs its surrounding figure/table context
- chapter: Onboarding AFC controls
- page: 307 / pdf 312
- heading: Onboarding AFC controls / Customer risk assessment
- knowledge_en: Evaluating risks posed by customers
- en_quote: Evaluating risks posed by customers
- risk_flags: ["block_may_continue_next", "cross_block_sentence_candidate", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:visual_or_table_label", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002430` P307: Customer profile
  - current `v7en_b002431` P307: Evaluating risks posed by customers
  - next `v7en_b002432` P307: Jurisdiction


## Samples: cross_block_join_candidate

### v7u_tmp_pilot_v2fb_transaction-monitoring_o020_l020_N000001

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: source sentence appears split across adjacent blocks
- chapter: Transaction monitoring
- page: 333 / pdf 338
- heading: Transaction monitoring / Typical scenarios that would generate an alert
- knowledge_en: excessive channel use as red flag
- en_quote: Excessive use of a particular channel compared to what is expected for that customer type, such as high use of cash over electronic payments
- risk_flags: ["block_may_continue_next", "derived_from_fullbook_llm_grouping", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002663` P333: • High-turnover transactions or high-velocity remittance: Transactions that exceed the value or velocity of the customer’s peer group of customers
  - current `v7en_b002664` P333: Excessive use of a particular channel compared to what is expected for that customer type, such as high use of cash over electronic payments
  - next `v7en_b002665` P333: • Round trip transactions: A sent remittance returned as a received remittance immediately or shortly afterward

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000034

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: source sentence appears split across adjacent blocks
- chapter: Financial Action Task Force
- page: 154 / pdf 159
- heading: Financial Action Task Force / FATF 11 Immediate Outcomes
- knowledge_en: Assessor training definition fragment
- en_quote: Assessor training: Training for the experts who will perform assessment
- risk_flags: ["block_may_continue_next", "cleaned_residual_sub_bullet_marker", "derived_from_fullbook_llm_grouping", "fragment", "possible_list_item", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001164` P154: • Getting started:
  - current `v7en_b001165` P154: <sub>o Assessor training: Training for the experts who will perform assessment
  - next `v7en_b001166` P154: <sub>o Jurisdiction training: Training for representatives of the evaluated jurisdictions

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000035

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: source sentence appears split across adjacent blocks
- chapter: Financial Action Task Force
- page: 154 / pdf 159
- heading: Financial Action Task Force / FATF 11 Immediate Outcomes
- knowledge_en: jurisdiction training definition fragment
- en_quote: Jurisdiction training: Training for representatives of the evaluated jurisdictions
- risk_flags: ["block_may_continue_next", "cleaned_residual_sub_bullet_marker", "derived_from_fullbook_llm_grouping", "previous_block_may_continue_here", "source_sentence_may_continue_from_previous_block", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001165` P154: <sub>o Assessor training: Training for the experts who will perform assessment
  - current `v7en_b001166` P154: <sub>o Jurisdiction training: Training for representatives of the evaluated jurisdictions
  - next `v7en_b001167` P154: <sub>o Selection of assessors: Selection of the experts that form the assessment team

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000036

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: source sentence appears split across adjacent blocks
- chapter: Financial Action Task Force
- page: 154 / pdf 159
- heading: Financial Action Task Force / FATF 11 Immediate Outcomes
- knowledge_en: subheading fragment
- en_quote: Selection of assessors: Selection of the experts that form the assessment team
- risk_flags: ["block_may_continue_next", "cleaned_residual_sub_bullet_marker", "derived_from_fullbook_llm_grouping", "previous_block_may_continue_here", "source_sentence_may_continue_from_previous_block", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001166` P154: <sub>o Jurisdiction training: Training for representatives of the evaluated jurisdictions
  - current `v7en_b001167` P154: <sub>o Selection of assessors: Selection of the experts that form the assessment team
  - next `v7en_b001168` P154: • Technical review: Assessment team analyzes the jurisdiction’s laws and regulations

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000037

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: source sentence appears split across adjacent blocks
- chapter: Financial Action Task Force
- page: 154 / pdf 159
- heading: Financial Action Task Force / FATF 11 Immediate Outcomes
- knowledge_en: FATF plenary discussion and voting on ratings
- en_quote: Plenary discussion: FATF plenary discusses the findings in the report and votes on the ratings
- risk_flags: ["block_may_continue_next", "cleaned_residual_sub_bullet_marker", "derived_from_fullbook_llm_grouping", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001172` P154: • FATF plenary adoption:
  - current `v7en_b001173` P154: <sub>o Plenary discussion: FATF plenary discusses the findings in the report and votes on the ratings
  - next `v7en_b001174` P155: <sub>o Final quality review: All jurisdictions review the report before publishing

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000038

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: source sentence appears split across adjacent blocks
- chapter: Financial Action Task Force
- page: 155 / pdf 160
- heading: Financial Action Task Force / FATF 11 Immediate Outcomes
- knowledge_en: final quality review step
- en_quote: Final quality review: All jurisdictions review the report before publishing
- risk_flags: ["block_may_continue_next", "cleaned_residual_sub_bullet_marker", "derived_from_fullbook_llm_grouping", "fragment", "heading_context_reused_across_page", "paragraph_continues_across_page_candidate", "possible_metadata", "previous_block_may_continue_here", "source_sentence_may_continue_from_previous_block", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001173` P154: <sub>o Plenary discussion: FATF plenary discusses the findings in the report and votes on the ratings
  - current `v7en_b001174` P155: <sub>o Final quality review: All jurisdictions review the report before publishing
  - next `v7en_b001175` P155: • Publication and follow-up: Jurisdiction addresses issues and begins strengthening its AML measures

### v7u_tmp_pilot_v2fb_types-of-financial-crime_o000_l020_N000007

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: source sentence appears split across adjacent blocks
- chapter: Types of financial crime
- page: 22 / pdf 27
- heading: Types of financial crime / Predicate crimes and money laundering
- knowledge_en: Piracy definition
- en_quote: 20.Piracy: Maritime or cyber-based hijacking for financial gain
- risk_flags: ["block_may_continue_next", "derived_from_fullbook_llm_grouping", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000203` P22: 19. Forgery: Falsifying documents, financial records, or identities
  - current `v7en_b000204` P22: 20.Piracy: Maritime or cyber-based hijacking for financial gain
  - next `v7en_b000205` P22: 21. Insider trading and market manipulation: Illegal use of nonpublic information to achieve profits

### v7u_tmp_pilot_v2fb_types-of-risk-assessment_o000_l020_N000005

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: source sentence appears split across adjacent blocks
- chapter: Types of risk assessment
- page: 267 / pdf 272
- heading: Types of risk assessment / The importance of risk assessment in AFC
- knowledge_en: Risks vary in nature, scale, and impact
- en_quote: Risks can vary in their nature, scale, and impact.
- risk_flags: ["derived_from_fullbook_llm_grouping", "heading_context_reused_across_page", "paragraph_continues_across_page_candidate", "source_sentence_may_continue_from_previous_block", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002104` P265: Enterprise-wide risk assessment (EWRA)
  - current `v7en_b002105` P267: Risks can vary in their nature, scale, and impact. An RBA requires countries and financial institutions to prioritize risks and apply appropriate measures based on their level of exposure. Not every risk applies to every institution. Understanding these factors will allow financial institutions to make informed decisions to balance risk and reward.
  - next `v7en_b002106` P268: Three main types of risk assessments are national risk assessments (NRA), sectoral risk assessments (SRA), and enterprise-wide risk assessments (EWRA).

### v7u_tmp_pilot_v2fb_afc-guidance-from-other-organizations_o000_l020_N000008

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: source sentence appears split across adjacent blocks
- chapter: AFC guidance from other organizations
- page: 171 / pdf 176
- heading: AFC guidance from other organizations / G-20 Anti-Corruption Working Group AFC guidance
- knowledge_en: incomplete sentence about G-20 guidance
- en_quote: The G-20 has authored several documents that provide essential guidance on anti-corruption measures, financial transparency, and international
- risk_flags: ["block_may_continue_next", "derived_from_fullbook_llm_grouping", "incomplete_sentence", "source_sentence_may_continue_next_block", "source_text_lacks_terminal_punctuation", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001350` P171: • Enhancing whistle-blower protection mechanisms.
  - current `v7en_b001351` P171: The G-20 has authored several documents that provide essential guidance on anti-corruption measures, financial transparency, and international
  - next `v7en_b001352` P172: cooperation. They outline strategies for combating illicit financial activities, recovering stolen assets, and enhancing regulatory frameworks across jurisdictions to strengthen governance and promote integrity in both public and private sectors. These include:


## Samples: structural_parent_candidate

### v7u_tmp_pilot_v2fb_understanding-afc-technology_o020_l020_N000007

- action: demote_to_parent_or_context
- rationale: introductory/list-parent sentence is context rather than direct evidence
- chapter: Understanding AFC technology
- page: 378 / pdf 383
- heading: Understanding AFC technology / Technology implementation considerations
- knowledge_en: Introduction to pros and cons
- en_quote: Some key pros and cons are as follows.
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002983` P378: Time and effort to implement: Estimate the amount of time and effort needed to implement new technology in terms of engagement and focus from multiple teams within the organization, such as AFC compliance, operations, and technology.
  - current `v7en_b002984` P378: Financial institutions then have a choice to build AFC technology solutions inhouse or buy them from a third party or a combination of the two approaches. Buying from a third party includes off-the-shelf solutions and customized solutions that the vendor tailors to the organization’s needs. Some key pros and cons are as follows.
  - next `v7en_b002985` P378: <table><tr><td>Criteria <td>Build in-house <td>Buy customized solution <td>Buy off-the-shelf solution <tr><td>Pros <td>Fully customizedGreater controlCompetitive differentiation <td>Fully customized with vendor experienceGreater controlContinuous vendor support <td>Pre-built solutionsProven effectivenessContinuous vendor support through ongoing update <tr><td>Cons <td>Potentially higher development costsPotentially h...

### v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o040_l020_N000029

- action: demote_to_parent_or_context
- rationale: introductory/list-parent sentence is context rather than direct evidence
- chapter: US AML/CFT regulatory landscape
- page: 195 / pdf 200
- heading: US AML/CFT regulatory landscape / UK AML regulations
- knowledge_en: introductory sentence listing UK authorities
- en_quote: The following are major authorities in the UK responsible for issuing guidance, investigating money laundering offenses, and enforcing AML regulations.
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001554` P195: • Money Laundering, Terrorist Financing and Transfer of Funds (Information on the Payer) Regulations 2017.
  - current `v7en_b001555` P195: The following are major authorities in the UK responsible for issuing guidance, investigating money laundering offenses, and enforcing AML regulations.
  - next `v7en_b001556` P195: • The Financial Conduct Authority (FCA) regulates and supervises the conduct of financial services firms in the UK. The FCA sets standards, promotes competition, and prevents serious harm to customers within the financial services sector. The body was established in April 2013, taking over from the Financial Services Authority. Its primary focus is on the conduct of all financial firms, ensuring they treat customers ...

### v7u_tmp_pilot_v2fb_transaction-monitoring-scenario-calibration-testing_o020_l020_N000018

- action: demote_to_parent_or_context
- rationale: introductory/list-parent sentence is context rather than direct evidence
- chapter: Transaction monitoring scenario calibration testing
- page: 451 / pdf 456
- heading: Transaction monitoring scenario calibration testing / Technology to assist investigation
- knowledge_en: table introduction
- en_quote: The table below summarizes different categories of technology solutions:
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b003414` P451: ## Technology to assist investigation
  - current `v7en_b003415` P451: The table below summarizes different categories of technology solutions:
  - next `v7en_b003416` P451: <table><tr><td>Technology solution <td>Description <tr><td>Visualization <td>Identifies patternsDetects anomaliesUncovers networksMaps relationships <tr><td>Social network analysis <td>Identifies relationships, central figuresUncovers activity clusters <tr><td>Network analysis <td>Detects unusual transaction patternsGroups individuals and entities based on shared characteristics <tr><td>Open-source solution <td>Provi...

### v7u_tmp_pilot_v2fb_financial-action-task-force_o020_l020_N000020

- action: demote_to_parent_or_context
- rationale: introductory/list-parent sentence is context rather than direct evidence
- chapter: Financial Action Task Force
- page: 150 / pdf 155
- heading: Financial Action Task Force / FATF 11 Immediate Outcomes
- knowledge_en: table introduction
- en_quote: The table below lists the area of focus and specific outcomes associated with each of the 11 IOs:
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001156` P150: FATF’s IOs are not meant to be a checklist, but rather a starting point to assist assessors in determining the effectiveness of a jurisdiction's AML/CFT framework. FATF expects assessors to use their judgment and experience in determining their ratings.
  - current `v7en_b001157` P150: The table below lists the area of focus and specific outcomes associated with each of the 11 IOs:
  - next `v7en_b001158` P151: <table><tr><td>IO # <td>Area of Focus <td>Outcomes <tr><td>1.2. <td>Risk, policy, and coordinationInternational cooperation <td>A deep understanding of money laundering and terrorist financing risksAuthorities implementing targeted measures and coordinating responses, ensuring proactive threat mitigationEffective collaboration with foreign counterparts enhancing the ability to track and disrupt transnational financia...

### v7u_tmp_pilot_v2fb_three-lines-of-defense_o000_l020_N000034

- action: demote_to_parent_or_context
- rationale: introductory/list-parent sentence is context rather than direct evidence
- chapter: Three lines of defense
- page: 250 / pdf 255
- heading: Three lines of defense / Financial crime functions' structure
- knowledge_en: List introduction
- en_quote: The following is a list of typical AFC functions found within the second line of defense.
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001953` P250: ## Financial crime functions' structure
  - current `v7en_b001954` P250: The second line of defense in AFC consists of various functions, each specializing in distinct compliance and risk management areas. Each function has specific structures, roles, and responsibilities. How an organization structures its second-line AFC function depends on its size, complexity, geographic reach, and legacy. The following is a list of typical AFC functions found within the second line of defense.
  - next `v7en_b001955` P250: • The AML advisory function guides AML policies, procedures, and best practices. The function interprets regulatory requirements and supports business units in implementing compliant AML frameworks.

### v7u_tmp_pilot_v2fb_money-laundering-risks-associated-with-msbs-payment-service-providers-and-ecommerce_o000_l020_N000008

- action: demote_to_parent_or_context
- rationale: introductory/list-parent sentence is context rather than direct evidence
- chapter: Money laundering risks associated with MSBs, payment service providers, and ecommerce
- page: 90 / pdf 95
- heading: Money laundering risks associated with MSBs, payment service providers, and ecommerce / Payment service providers
- knowledge_en: heading or introductory fragment
- en_quote: Examples of PSPs and their offerings:
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000709` P90: As demand for digital solutions grows, PSPs are expected to expand product offerings, adapt to customer needs, and comply with changing regulations. This adaptability ensures they stay at the forefront of the payment landscape.
  - current `v7en_b000710` P90: Examples of PSPs and their offerings:
  - next `v7en_b000711` P90: <table><tr><td>PSP <td>Description <td>Products and services <tr><td>Payment aggregators <td>Aggregate payments for multiple merchants without requiring direct bank relationships <td>Online payment processingRecurring billing <tr><td>Card issuers <td>Provide credit, debit, and prepaid cards to consumers, typically branded with major card networks (e.g. Visa, MasterCard, American Express) <td>Credit cardsDebit cardsPr...

### v7u_tmp_pilot_v2fb_money-laundering-risks-associated-with-msbs-payment-service-providers-and-ecommerce_o020_l020_N000006

- action: demote_to_parent_or_context
- rationale: introductory/list-parent sentence is context rather than direct evidence
- chapter: Money laundering risks associated with MSBs, payment service providers, and ecommerce
- page: 96 / pdf 101
- heading: Money laundering risks associated with MSBs, payment service providers, and ecommerce / E-commerce
- knowledge_en: incomplete list header
- en_quote: Business models include:
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000752` P96: Electronic commerce (e-commerce) platforms facilitate the buying and selling of goods and services over the internet. They serve as intermediaries between sellers and buyers, providing a digital marketplace for transactions. There are various types of e-commerce platforms, each tailored to meet different business models and customer needs.
  - current `v7en_b000753` P96: Business models include:
  - next `v7en_b000754` P96: <table><tr><td>Business Model <td>Acronym <td>Description <td>Examples <tr><td>Business-to-consumer <td>B2C <td>The most common form of e-commerce, where businesses sell products directly to consumers <td>Online clothing stores, food delivery services, Amazon, Alibaba, Rakuten, AliExpress, Netflix and other streaming platforms <tr><td>Business-to-business <td>B2B <td>Involves transactions between businesses <td>Manuf...

### v7u_tmp_pilot_v2fb_money-laundering-risks-associated-with-insurance-securities-brokerage-and-custodian-services_o000_l020_N000036

- action: demote_to_parent_or_context
- rationale: introductory/list-parent sentence is context rather than direct evidence
- chapter: Money laundering risks associated with insurance, securities, brokerage, and custodian services
- page: 105 / pdf 110
- heading: Money laundering risks associated with insurance, securities, brokerage, and custodian services / Securities and brokerage risks
- knowledge_en: incomplete list introduction
- en_quote: Asset managers provide a variety of financial products and services, including:
- risk_flags: ["derived_from_fullbook_llm_grouping", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000826` P105: Asset managers or asset management companies conduct investments and handle assets on behalf of their customers. Asset managers are required to understand the money laundering risks of their business as they handle large volumes of capital across multiple jurisdictions, in diverse and evolving asset classes, often with anonymity in transactions, using complex financial products and third parties.
  - current `v7en_b000827` P105: Asset managers provide a variety of financial products and services, including:
  - next `v7en_b000828` P105: Exchange-traded funds (ETF): These are investment funds traded on stock exchanges, similar to individual stocks. They offer diversification and liquidity but can also obscure the identities of underlying investors.

### v7u_tmp_pilot_v2fb_ongoing-afc-controls_o000_l020_N000041

- action: demote_to_parent_or_context
- rationale: introductory/list-parent sentence is context rather than direct evidence
- chapter: Ongoing AFC controls
- page: 323 / pdf 328
- heading: Ongoing AFC controls / Politically exposed persons screening
- knowledge_en: introductory sentence listing challenges
- en_quote: Challenges in automated adverse media screening solutions include:
- risk_flags: ["derived_from_fullbook_llm_grouping", "heading_context_reused_across_page", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002585` P322: • Any follow-up actions: Were legal proceedings dismissed? Were regulatory fines settled? Were there any consequences for the individual such as personal fines, imprisonment, or travel bans? Risk assessments should reflect post-incident changes.
  - current `v7en_b002586` P323: Challenges in automated adverse media screening solutions include:
  - next `v7en_b002587` P323: Social media misinformation: The decline in platform-driven factchecking increases the likelihood of false or misleading reports. Organizations must agree to and prioritize verified sources.


## Samples: ignored_short_bullet_neighbor_context_review

### v7u_tmp_prefreeze_qa_ignored_N000001

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: short bullet has continuation risk and needs neighbor context
- chapter: Private banking and wealth management risks
- page: 74 / pdf 79
- heading: Private banking and wealth management risks / Offshore financial center risks
- knowledge_en: Sudden, large flows of funds
- en_quote: Sudden, large flows of funds
- risk_flags: ["block_may_continue_next", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:short_sub_bullet_continuation_risk", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000578` P74: • Unusual transaction patterns including:
  - current `v7en_b000579` P74: <sub>o Sudden, large flows of funds
  - next `v7en_b000580` P74: <sub>o Round tripping or moving funds in and out

### v7u_tmp_prefreeze_qa_ignored_N000002

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: short bullet has continuation risk and needs neighbor context
- chapter: Private banking and wealth management risks
- page: 75 / pdf 80
- heading: Private banking and wealth management risks / Offshore financial center risks
- knowledge_en: Rapid asset transfers between offshore entities
- en_quote: Rapid asset transfers between offshore entities
- risk_flags: ["block_may_continue_next", "heading_context_reused_across_page", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:short_sub_bullet_continuation_risk", "needs_human_review_before_freeze", "paragraph_continues_across_page_candidate", "previous_block_may_continue_here", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000580` P74: <sub>o Round tripping or moving funds in and out
  - current `v7en_b000581` P75: <sub>o Rapid asset transfers between offshore entities
  - next `v7en_b000582` P75: • Use of cash-intensive businesses by a customer registered in an OFC

### v7u_tmp_prefreeze_qa_ignored_N000005

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: short bullet has continuation risk and needs neighbor context
- chapter: Corporate and investment banking risks
- page: 79 / pdf 84
- heading: Corporate and investment banking risks / Wire transfer risks
- knowledge_en: Unusual timing of the transfer
- en_quote: Unusual timing of the transfer
- risk_flags: ["block_may_continue_next", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:short_sub_bullet_continuation_risk", "needs_human_review_before_freeze", "previous_block_may_continue_here", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000626` P79: <sub>o Unusual volume or amount of the transfer
  - current `v7en_b000627` P79: <sub>o Unusual timing of the transfer
  - next `v7en_b000628` P79: <sub>o Complex transaction paths

### v7u_tmp_prefreeze_qa_ignored_N000006

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: short bullet has continuation risk and needs neighbor context
- chapter: Corporate and investment banking risks
- page: 79 / pdf 84
- heading: Corporate and investment banking risks / Wire transfer risks
- knowledge_en: Complex transaction paths
- en_quote: Complex transaction paths
- risk_flags: ["block_may_continue_next", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:short_sub_bullet_continuation_risk", "needs_human_review_before_freeze", "previous_block_may_continue_here", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000627` P79: <sub>o Unusual timing of the transfer
  - current `v7en_b000628` P79: <sub>o Complex transaction paths
  - next `v7en_b000629` P79: • Unusual instructions with the wire transfer, such as a sequence of transfer instructions or the addition of an unrelated party name in the instructions

### v7u_tmp_prefreeze_qa_ignored_N000008

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: short bullet has continuation risk and needs neighbor context
- chapter: Money laundering risks associated with MSBs, payment service providers, and ecommerce
- page: 98 / pdf 103
- heading: Money laundering risks associated with MSBs, payment service providers, and ecommerce / E-commerce risks
- knowledge_en: To launder illicit funds
- en_quote: To launder illicit funds
- risk_flags: ["block_may_continue_next", "cross_block_sentence_candidate", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:short_sub_bullet_continuation_risk", "needs_human_review_before_freeze", "previous_block_may_continue_here", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000770` P98: <sub>o As a front for illicit transactions
  - current `v7en_b000771` P98: <sub>o To launder illicit funds
  - next `v7en_b000772` P98: Criminals can use e-commerce businesses to both illegally generate funds and launder them. Ultimately, these funds will be deposited with an FI. Therefore, FIs must strive to prevent and detect financial crime through their roles as payment processors, card issuers for customers, and account openers for merchants.

### v7u_tmp_prefreeze_qa_ignored_N000023

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: short bullet has continuation risk and needs neighbor context
- chapter: Governance and oversight
- page: 293 / pdf 298
- heading: Governance and oversight / Drafting AFC policies and procedures
- knowledge_en: System, procedural, and process updates
- en_quote: System, procedural, and process updates
- risk_flags: ["block_may_continue_next", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:short_sub_bullet_continuation_risk", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002290` P293: <sub>o Gap analysis and business risk assessment.
  - current `v7en_b002291` P293: <sub>o System, procedural, and process updates
  - next `v7en_b002292` P293: <sub>o Training and staff education.

### v7u_tmp_prefreeze_qa_ignored_N000031

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: short bullet has continuation risk and needs neighbor context
- chapter: Technology for KYC
- page: 421 / pdf 426
- heading: Technology for KYC / Fuzzy logic and partial matches
- knowledge_en: "Katherine Navel" and "Catherine Naval"
- en_quote: "Katherine Navel" and "Catherine Naval"
- risk_flags: ["block_may_continue_next", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:short_sub_bullet_continuation_risk", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b003237` P421: • Phonetic, identifying similar sounding names.
  - current `v7en_b003238` P421: <sub>o "Katherine Navel" and "Catherine Naval"
  - next `v7en_b003239` P421: • Edit Distance or Damerau-Levenshtein metric, calculating the number of character changes required to transform one name into another.

### v7u_tmp_prefreeze_qa_ignored_N000032

- action: inspect_neighbor_blocks_or_pdf_join
- rationale: short bullet has continuation risk and needs neighbor context
- chapter: Technology for KYC
- page: 421 / pdf 426
- heading: Technology for KYC / Fuzzy logic and partial matches
- knowledge_en: "McDowd" and "MacDawd"
- en_quote: "McDowd" and "MacDawd"
- risk_flags: ["block_may_continue_next", "cross_block_sentence_candidate", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:short_sub_bullet_continuation_risk", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b003239` P421: • Edit Distance or Damerau-Levenshtein metric, calculating the number of character changes required to transform one name into another.
  - current `v7en_b003240` P421: <sub>o "McDowd" and "MacDawd"
  - next `v7en_b003241` P421: Based on the fuzzy logic configuration, an organization will generate partial matches. These partial matches should then be investigated to determine whether they are true matches or false positives.


## Samples: fragment_neighbor_join_or_discard

### v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o020_l020_N000049

- action: inspect_neighbor_blocks_then_join_or_discard
- rationale: unit is a fragment; needs adjacent text or should remain non-direct
- chapter: US AML/CFT regulatory landscape
- page: 192 / pdf 197
- heading: US AML/CFT regulatory landscape / The role of AML Authority
- knowledge_en: fragment: training to national competent authorities
- en_quote: training to national competent authorities.
- risk_flags: ["derived_from_fullbook_llm_grouping", "fragment", "heading_context_reused_across_page", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001531` P191: • Monitor national competent authorities to ensure consistent application of the Single Rulebook. The AML Authority provides guidance, support, and
  - current `v7en_b001532` P192: training to national competent authorities. The AML Authority has the authorization to identify and act in cases of systematic failures regarding supervision. Such cases could involve breaches resulting from the improper application of national law transposing EU directives. Note that the AML Authority is not the EU FIU; rather, it plays a vital role in supporting and coordinating within the FIU's network.
  - next `v7en_b001533` P192: • Conduct regular assessments of money laundering and terrorist financing risks within the EU. The AML Authority identifies emerging threats and vulnerabilities, providing recommendations to mitigate these risks.

### v7u_tmp_pilot_v2fb_us-aml-cft-regulatory-landscape_o040_l020_N000040

- action: inspect_neighbor_blocks_then_join_or_discard
- rationale: unit is a fragment; needs adjacent text or should remain non-direct
- chapter: US AML/CFT regulatory landscape
- page: 197 / pdf 202
- heading: US AML/CFT regulatory landscape / Australia AML regulations
- knowledge_en: Incomplete list introduction
- en_quote: The AML/CTF Amendment Act 2024 introduces several key provisions, including:
- risk_flags: ["derived_from_fullbook_llm_grouping", "heading_context_reused_across_page", "incomplete_sentence", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b001569` P196: The primary legislation governing AML/CFT in Australia is the Anti-Money Laundering and Counter-Terrorism Financing Act 2006 (AML/CTF Act 2006). This act requires reporting entities to implement and maintain an AML/CFT compliance program. This program includes risk assessment, internal controls for CDD and regulatory reporting, employee training, and independent reviews.
  - current `v7en_b001570` P197: Australia recently passed the AML/CTF Amendment Act 2024, which is a significant enhancement of its AML/CFT framework. The purpose of the amendments is to ensure Australia’s laws align with FATF’s international standards and continue to effectively deter, detect, and disrupt money laundering as well as terrorism financing and proliferation financing. The AML/CTF Amendment Act 2024 introduces several key provisions, i...
  - next `v7en_b001571` P197: Extending AML/CFT obligations to DNFBPs, such as real estate agents, legal professionals, accountants, and dealers in precious metals and stones. This includes the obligations to identify and verify customers, conduct ongoing monitoring, and report suspicious activities to AUSTRAC.

### v7u_tmp_pilot_v2fb_afc-guidance-from-leading-international-organizations_o020_l020_N000014

- action: inspect_neighbor_blocks_then_join_or_discard
- rationale: unit is a fragment; needs adjacent text or should remain non-direct
- chapter: AFC guidance from leading international organizations
- page: 168 / pdf 173
- heading: AFC guidance from leading international organizations / Wolfsberg Group AFC guidance
- knowledge_en: incomplete sentence about Wolfsberg Group publication
- en_quote: In 2000, the Wolfsberg Group published the .
- risk_flags: ["derived_from_fullbook_llm_grouping", "incomplete_sentence", "zh_subspan_unavailable"]

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
- risk_flags: ["derived_from_fullbook_llm_grouping", "incomplete_sentence", "zh_subspan_unavailable"]

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
- risk_flags: ["derived_from_fullbook_llm_grouping", "fragment", "heading_context_reused_across_page", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002554` P319: • Escalation and reporting: High-risk entities are subjected to enhanced due diligence, and where necessary, suspicious activity reports are filed with FIUs if money laundering or other financial crime concerns arise. Sanctions violations will be reported to the relevant regulatory bodies. Those customers would typically be offboarded in accordance with the
  - current `v7en_b002555` P320: organization's exit policy, subject to the necessary approvals and special licenses for specific transactions linked to sanctioned individuals and entities.
  - next `v7en_b002556` P320: • AI-driven screening solutions: When appropriately tested and implemented, an AI-driven system can provide improved accuracy, reducing false positives and enhancing detection of hidden risks.


## Samples: ignored_prose_llm_split_candidate

### v7u_tmp_prefreeze_qa_ignored_N000003

- action: run_sentence_grouping_or_manual_split
- rationale: ignored block looks like textbook prose; split before direct evidence
- chapter: Private banking and wealth management risks
- page: 75 / pdf 80
- heading: Private banking and wealth management risks / Special purpose vehicle risks
- knowledge_en: Special purpose vehicles (SPVs) are legal entities created for specific and limited purposes. SPVs can be used in mergers and acquisitions, joint ventures, real estate projects, infrastructure development, and energy projects. SPVs can also be used to manage and protect intellectual property assets including trademarks and copyrights. SPVs are often used in complex financial transactions and investments such as securities and asset-backed financing
- en_quote: Special purpose vehicles (SPVs) are legal entities created for specific and limited purposes. SPVs can be used in mergers and acquisitions, joint ventures, real estate projects, infrastructure development, and energy projects. SPVs can also be used to manage and protect intellectual property assets including trademarks and copyrights. SPVs are often used in complex financial transactions and investments such as securities and asset-backed financing.
- risk_flags: ["ignored_original_route:ignored_non_content", "ignored_review_class:non_content_needs_sampling", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000588` P75: ## Special purpose vehicle risks
  - current `v7en_b000589` P75: Special purpose vehicles (SPVs) are legal entities created for specific and limited purposes. SPVs can be used in mergers and acquisitions, joint ventures, real estate projects, infrastructure development, and energy projects. SPVs can also be used to manage and protect intellectual property assets including trademarks and copyrights. SPVs are often used in complex financial transactions and investments such as secur...
  - next `v7en_b000590` P75: There are financial crime risks associated with SPVs.

### v7u_tmp_prefreeze_qa_ignored_N000004

- action: run_sentence_grouping_or_manual_split
- rationale: ignored block looks like textbook prose; split before direct evidence
- chapter: Corporate and investment banking risks
- page: 78 / pdf 83
- heading: Corporate and investment banking risks / Wire transfer risks
- knowledge_en: A bank transfer is a different method used to electronically transfer funds. This is conducted between two banks and is usually domestic. Bank transfers use a settlement system called an automated clearing house (ACH). This system supports the transfer of credits and debits between banks
- en_quote: A bank transfer is a different method used to electronically transfer funds. This is conducted between two banks and is usually domestic. Bank transfers use a settlement system called an automated clearing house (ACH). This system supports the transfer of credits and debits between banks.
- risk_flags: ["ignored_original_route:ignored_non_content", "ignored_review_class:non_content_needs_sampling", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b000614` P78: A wire transfer is an electronic transfer of funds between two parties. A wire transfer is conducted over a secure payment network such as SWIFT. Wire transfers are conducted domestically and cross-border.
  - current `v7en_b000615` P78: A bank transfer is a different method used to electronically transfer funds. This is conducted between two banks and is usually domestic. Bank transfers use a settlement system called an automated clearing house (ACH). This system supports the transfer of credits and debits between banks.
  - next `v7en_b000616` P78: Wire transfers carry risk because they can be used to send money to criminals. They are international, which makes them more attractive to use to send money across jurisdictions. Wire transfers can send funds immediately, and it can be difficult to reverse a transaction. They can also transfer a large amount of funds, which makes them riskier.


## Samples: ignored_review_other

### v7u_tmp_prefreeze_qa_ignored_N000027

- action: manual_review
- rationale: ignored recovery did not match a deterministic promotion rule
- chapter: Onboarding AFC controls
- page: 307 / pdf 312
- heading: Onboarding AFC controls / Customer risk assessment
- knowledge_en: Products
- en_quote: Products
- risk_flags: ["ignored_original_route:ignored_non_content", "ignored_review_class:non_content_needs_sampling", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002432` P307: Jurisdiction
  - current `v7en_b002433` P307: Products
  - next `v7en_b002434` P307: Channels

### v7u_tmp_prefreeze_qa_ignored_N000028

- action: manual_review
- rationale: ignored recovery did not match a deterministic promotion rule
- chapter: Onboarding AFC controls
- page: 307 / pdf 312
- heading: Onboarding AFC controls / Customer risk assessment
- knowledge_en: Channels
- en_quote: Channels
- risk_flags: ["ignored_original_route:ignored_non_content", "ignored_review_class:non_content_needs_sampling", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b002433` P307: Products
  - current `v7en_b002434` P307: Channels
  - next `v7en_b002435` P307: Transactional behavior


## Samples: ignored_short_context_label_review

### v7u_tmp_prefreeze_qa_ignored_N000030

- action: decide_context_parent_or_discard
- rationale: short label may be a heading/context node, not direct evidence
- chapter: Technology for KYC
- page: 407 / pdf 412
- heading: Technology for KYC / Perpetual KYC
- knowledge_en: Effective risk management
- en_quote: Effective risk management
- risk_flags: ["ignored_original_route:ignored_short_context_label", "ignored_review_class:short_context_label", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b003151` P407: The implementation of perpetual KYC practices offers multiple benefits for organizations. One major benefit is effective financial crime risk management. By allowing updates and potential reviews, organizations can focus their resources on higher-risk areas. Investing in perpetual KYC practices not only reduces costs but also results in operational efficiencies by minimizing unnecessary reviews triggered by non-risk-...
  - current `v7en_b003152` P407: Effective risk management
  - next `v7en_b003153` P408: ## Digital onboarding technology


## Samples: ignored_text_damage_manual

### v7u_tmp_prefreeze_qa_ignored_N000018

- action: manual_pdf_source_review
- rationale: ignored fragment contains extraction damage
- chapter: Case example: Drafting policies for an AFC department based in APAC
- page: 178 / pdf 183
- heading: Case example: Drafting policies for an AFC department based in APAC
- knowledge_en: Continuously update policies with Íatest regulations and guidance
- en_quote: Continuously update policies with Íatest regulations and guidance
- risk_flags: ["block_may_continue_next", "cross_block_sentence_candidate", "ignored_original_route:ignored_visual_text_fragment", "ignored_review_class:text_damage_fragment", "needs_human_review_before_freeze", "recovered_from_ignored_route_prefreeze_qa", "zh_subspan_unavailable"]

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
- risk_flags: ["derived_from_fullbook_llm_grouping", "duplicated_phrase_accommodate", "moved_from_direct_to_review_prefreeze_qa", "needs_human_review_before_freeze", "zh_subspan_unavailable"]

  Neighbor context:

  - prev `v7en_b003267` P424: Screening systems should be compatible with other systems. This includes data flows, workflow management tools, and application programming interface (API) integrations. Carrying out a complete assessment of all touchpoints with other systems and understanding the screening process workflow enables a more successful implementation later.
  - current `v7en_b003268` P424: Organizations should also ensure that their integrated systems are scalable with the growth of the organization and increased data volumes of varying to accommodate the development of the organization and increased data volumes in various formats to accommodate the growth of the organization and increased data volumes, as well as the development of the organization and the varying formats of data. The systems must be...
  - next `v7en_b003269` P424: <table><tr><td>Factor <td>Recommended actions <tr><td>Compatibility <td>·Ensure systems are compatible with data flows, workflow management tools, and API integrations.·Complete a compliance system assessment and consider all relevant systems. <tr><td>Scalability <td>·Ensure systems scale with organizational growth and increasing data volumes.·Systems should be able to handle increased data without compromising perfo...
