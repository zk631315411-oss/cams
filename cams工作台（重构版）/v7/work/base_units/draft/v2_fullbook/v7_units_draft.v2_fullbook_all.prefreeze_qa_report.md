# v7 Pre-freeze QA Combined Draft

Generated at: 2026-07-03T00:24:52

## Summary

- direct items: 4404
- review items: 271
- parent/context items: 210
- recovered ignored direct items: 6
- recovered ignored review items: 36
- direct surface fixes: 6
- direct items moved to review: 1
- duplicate unit_ids: 0
- duplicate direct sentence_ids: 0

## Ignored Route Decisions

- export_glossary_asset_candidate: 750
- keep_heading_context: 441
- keep_ignored: 139
- move_to_review: 36
- recover_as_direct_list_item: 6

### Recovered Direct Examples

- `v7en_b000770` P98 / pdf 103: As a front for illicit transactions
- `v7en_b001044` P135 / pdf 140: Military research facilities
- `v7en_b001045` P135 / pdf 140: Defense manufacturers
- `v7en_b001050` P135 / pdf 140: Missiles
- `v7en_b001051` P135 / pdf 140: Tanks
- `v7en_b001052` P135 / pdf 140: Aircraft

### Moved To Review Examples

- `v7en_b000579` P74 / pdf 79: Sudden, large flows of funds (ignored fragment may be useful but is not safe as direct evidence)
- `v7en_b000581` P75 / pdf 80: Rapid asset transfers between offshore entities (ignored fragment may be useful but is not safe as direct evidence)
- `v7en_b000589` P75 / pdf 80: Special purpose vehicles (SPVs) are legal entities created for specific and limited purposes. SPVs can be used in mergers and acquisitions, joint ventures, real estate projects, infrastructure development, and energy projects. SPVs can also be used to manage and protect intellectual property assets including trademarks and copyrights. SPVs are often used in complex financial transactions and investments such as securities and asset-backed financing. (SPV prose was routed non_content but looks like textbook content; send to review/LLM split)
- `v7en_b000615` P78 / pdf 83: A bank transfer is a different method used to electronically transfer funds. This is conducted between two banks and is usually domestic. Bank transfers use a settlement system called an automated clearing house (ACH). This system supports the transfer of credits and debits between banks. (bank transfer prose was routed non_content but looks like textbook content; send to review/LLM split)
- `v7en_b000627` P79 / pdf 84: Unusual timing of the transfer (ignored fragment may be useful but is not safe as direct evidence)
- `v7en_b000628` P79 / pdf 84: Complex transaction paths (ignored fragment may be useful but is not safe as direct evidence)
- `v7en_b000771` P98 / pdf 103: To launder illicit funds (ignored fragment may be useful but is not safe as direct evidence)
- `v7en_b001412` P178 / pdf 183: Understand risks (ignored fragment may be useful but is not safe as direct evidence)
- `v7en_b001413` P178 / pdf 183: Identify regulations and guidance (ignored fragment may be useful but is not safe as direct evidence)
- `v7en_b001414` P178 / pdf 183: Map requirements and draft policies (ignored fragment may be useful but is not safe as direct evidence)
- `v7en_b001415` P178 / pdf 183: Implement policies (ignored fragment may be useful but is not safe as direct evidence)
- `v7en_b001416` P178 / pdf 183: Continuously update policies with Íatest regulations and guidance (ignored fragment may be useful but is not safe as direct evidence)

## Text Cleanup Decisions

- apply_pdf_verified_surface_fix: 6
- move_direct_to_review: 1

### v7u_tmp_pilot_v2fb_data-as-an-input-for-solutions_o000_l020_N000044

- action: apply_pdf_verified_surface_fix
- `timeconsuming` -> `time-consuming` (pdf_text_page_470)
- before: There should be a balance between data that is clean and data that remains true to the source data. Data cleansing can be expensive and timeconsuming. Organizations need to discern when data is clean enough to use and not strive for 100% cleanness, which they will never be able to achieve.

### v7u_tmp_pilot_v2fb_data-as-an-input-for-solutions_o060_l020_N000013

- action: apply_pdf_verified_surface_fix
- `enduser` -> `end-user` (pdf_text_page_482)
- before: Magnify Bank has expanded and grown significantly over the past several years, and its transaction monitoring system has had issues keeping up with the increasing volume and complexity of alert activity. A central issue is that data comes to the system from several sources, and this data is often incomplete or provided in different formats, making the downstream analysis unreliable and, in some cases, obsolete. Magni...

### v7u_tmp_pilot_v2fb_technology-for-kyc_o020_l020_N000011

- action: apply_pdf_verified_surface_fix
- `In its , published in March of 2020` -> `In its Guidance on Digital Identity, published in March of 2020` (pdf_text_page_414)
- before: Also, FATF has issued guidelines to help organizations determine the suitability of digital identities for CDD. In its , published in March of 2020, FATF covers principles of a digital identify framework and how digital identities can be used for customer onboarding and due diligence in line with FATF's Recommendation 10.

### v7u_tmp_pilot_v2fb_technology-for-kyc_o080_l020_N000014

- action: move_direct_to_review
- reason: PDF text layer repeats the same garbled phrase; not reliable enough for direct evidence.
- before: Organizations should also ensure that their integrated systems are scalable with the growth of the organization and increased data volumes of varying to accommodate the development of the organization and increased data volumes in various formats to accommodate the growth of the organization and increased data volumes, as well as the development of the organization and the varying formats of data. The systems must be...

### v7u_tmp_pilot_v2fb_types-of-financial-crime_o020_l020_N000032

- action: apply_pdf_verified_surface_fix
- `financia account` -> `financial account` (pdf_text_page_33)
- before: The Common Reporting Standard (CRS), developed in response to the G-20 countries' request and approved by the OECD (Organization for Economic Cooperation and Development) Council, calls on jurisdictions to obtain information from their financial institutions and automatically exchange that information with other jurisdictions on an annual basis. It sets out the financia account information to be exchanged, the financ...

### v7u_tmp_pilot_v2fb_money-laundering-risks-associated-with-cryptoassets-and-other-fintechs_o020_l020_N000001

- action: apply_pdf_verified_surface_fix
- `origina funds` -> `original funds` (pdf_text_page_120)
- before: The use of mixer protocols does not necessarily indicate that the origina funds are illegal. Some users of such services simply believe in privacy and use these services to protect their information without doing anything illegal.

### v7u_tmp_pilot_v2fb_governance-process_o000_l020_N000014

- action: apply_pdf_verified_surface_fix
- `enduser` -> `end-user` (pdf_text_page_493)
- before: Committee members should include representatives from the enduser community, IT teams, and the upstream source data providers.