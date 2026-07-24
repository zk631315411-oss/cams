# v7 Direct Text Quality Audit

Generated at: 2026-07-03T00:12:04

## Summary

- direct items scanned: 4399
- issue units: 7

## Issue Counts

- missing_hyphen_enduser: 2
- missing_hyphen_timeconsuming: 1
- damaged_publication_reference: 1
- duplicated_phrase_accommodate: 1
- broken_financia_account: 1
- mojibake_or_replacement_char: 1

## Recommended Actions

- auto_surface_fix_candidate: 3
- manual_source_review: 2
- manual_source_review_or_review_gate: 2

## Samples: auto_surface_fix_candidate

### v7u_tmp_pilot_v2fb_data-as-an-input-for-solutions_o000_l020_N000044

- chapter: Data as an input for solutions
- page: 465 / pdf 470
- heading: Data as an input for solutions / Clean data for technology solutions
- knowledge_en: Balance between data cleanliness and fidelity
- en_quote: There should be a balance between data that is clean and data that remains true to the source data. Data cleansing can be expensive and timeconsuming. Organizations need to discern when data is clean enough to use and not strive for 100% cleanness, which they will never be able to achieve.
- issues: [{"issue": "missing_hyphen_timeconsuming", "matches": ["timeconsuming"], "recommended_action": "auto_surface_fix_candidate", "suggestion": "time-consuming", "rationale": "likely missing hyphen/space in extracted text"}]

### v7u_tmp_pilot_v2fb_data-as-an-input-for-solutions_o060_l020_N000013

- chapter: Data as an input for solutions
- page: 477 / pdf 482
- heading: Data as an input for solutions / Case example: Handling increased alert volume
- knowledge_en: Magnify Bank's data integration project
- en_quote: Magnify Bank has expanded and grown significantly over the past several years, and its transaction monitoring system has had issues keeping up with the increasing volume and complexity of alert activity. A central issue is that data comes to the system from several sources, and this data is often incomplete or provided in different formats, making the downstream analysis unreliable and, in some cases, obsolete. Magnify Bank has initiated a project to integrate data from multiple source systems and prepare it for various enduser applications.
- issues: [{"issue": "missing_hyphen_enduser", "matches": ["enduser"], "recommended_action": "auto_surface_fix_candidate", "suggestion": "end-user", "rationale": "likely missing hyphen/space in extracted text"}]

### v7u_tmp_pilot_v2fb_governance-process_o000_l020_N000014

- chapter: Governance process
- page: 488 / pdf 493
- heading: Governance process / Data governance committees
- knowledge_en: Committee membership composition
- en_quote: Committee members should include representatives from the enduser community, IT teams, and the upstream source data providers.
- issues: [{"issue": "missing_hyphen_enduser", "matches": ["enduser"], "recommended_action": "auto_surface_fix_candidate", "suggestion": "end-user", "rationale": "likely missing hyphen/space in extracted text"}]


## Samples: manual_source_review

### v7u_tmp_pilot_v2fb_technology-for-kyc_o020_l020_N000011

- chapter: Technology for KYC
- page: 409 / pdf 414
- heading: Technology for KYC / Digital onboarding technology
- knowledge_en: FATF guidelines on digital identities for CDD
- en_quote: Also, FATF has issued guidelines to help organizations determine the suitability of digital identities for CDD. In its , published in March of 2020, FATF covers principles of a digital identify framework and how digital identities can be used for customer onboarding and due diligence in line with FATF's Recommendation 10.
- issues: [{"issue": "damaged_publication_reference", "matches": ["In its ,"], "recommended_action": "manual_source_review", "suggestion": null, "rationale": "publication title appears missing from extraction"}]

### v7u_tmp_pilot_v2fb_types-of-financial-crime_o020_l020_N000032

- chapter: Types of financial crime
- page: 28 / pdf 33
- heading: Types of financial crime / Key takeaways
- knowledge_en: CRS definition and purpose
- en_quote: The Common Reporting Standard (CRS), developed in response to the G-20 countries' request and approved by the OECD (Organization for Economic Cooperation and Development) Council, calls on jurisdictions to obtain information from their financial institutions and automatically exchange that information with other jurisdictions on an annual basis. It sets out the financia account information to be exchanged, the financial institutions required to report, the different types of accounts and taxpayers covered, as well as common due diligence procedures to be followed by financial institutions. Its purpose is to combat tax evasion.
- issues: [{"issue": "broken_financia_account", "matches": ["financia account"], "recommended_action": "manual_source_review", "suggestion": "financial account", "rationale": "probable OCR deletion; verify against source before changing"}]


## Samples: manual_source_review_or_review_gate

### v7u_tmp_pilot_v2fb_technology-for-kyc_o080_l020_N000014

- chapter: Technology for KYC
- page: 424 / pdf 429
- heading: Technology for KYC / Integrating screening technology with other systems
- knowledge_en: Scalability and performance requirements for integrated systems
- en_quote: Organizations should also ensure that their integrated systems are scalable with the growth of the organization and increased data volumes of varying to accommodate the development of the organization and increased data volumes in various formats to accommodate the growth of the organization and increased data volumes, as well as the development of the organization and the varying formats of data. The systems must be able to handle an increase in data requirements without compromising performance.
- issues: [{"issue": "duplicated_phrase_accommodate", "matches": ["of varying to accommodate"], "recommended_action": "manual_source_review_or_review_gate", "suggestion": null, "rationale": "sentence appears to contain repeated or garbled extraction"}]

### v7u_tmp_pilot_v2fb_money-laundering-risks-associated-with-cryptoassets-and-other-fintechs_o020_l020_N000001

- chapter: Money laundering risks associated with cryptoassets and other FinTechs
- page: 115 / pdf 120
- heading: Money laundering risks associated with cryptoassets and other FinTechs / Mixers and tumblers
- knowledge_en: Mixer use not necessarily illegal
- en_quote: The use of mixer protocols does not necessarily indicate that the origina funds are illegal. Some users of such services simply believe in privacy and use these services to protect their information without doing anything illegal.
- issues: [{"issue": "mojibake_or_replacement_char", "matches": ["origina"], "recommended_action": "manual_source_review_or_review_gate", "suggestion": null, "rationale": "possible OCR/mojibake/extraction damage"}]
