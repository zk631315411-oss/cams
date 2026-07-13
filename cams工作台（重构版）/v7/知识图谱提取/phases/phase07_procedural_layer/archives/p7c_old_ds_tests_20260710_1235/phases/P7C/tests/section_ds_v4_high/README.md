# P7C section DS v4 pro test

## Purpose

This folder is a small P7C experiment runner. It tests one section at a time with `deepseek-v4-pro`, saves the full prompt, raw response, parsed cards, run manifest, and validation report.

It is not the full-book P7C runner and does not write to formal P7C output folders.

## Inputs

Default inputs:

```text
../../prompts/section_card_extraction_v1.md
../P7B/section_packages/<section_id>/task.json
```

The runner reads `task.json`, but the prompt input is intentionally text-only:

```text
section_text_with_unit_anchors
allowed_unit_ids
```

It does not inject core points, CP-unit edges, CP-CP edges, alias metadata, or KG edges into the prompt.

Default `thinking_effort` is `none`.

Operational note: DS service is considered stable up to 20 concurrent requests. This test runner is still single-section/single-call by default; batch runners may use 20 as the planned stable concurrency ceiling.

## Outputs

For each run:

```text
outputs/<run_id>/<section_id>/prompt.md
outputs/<run_id>/<section_id>/raw_response.txt
outputs/<run_id>/<section_id>/cards.raw.json
outputs/<run_id>/<section_id>/run_manifest.json
outputs/<run_id>/<section_id>/validation_report.md
```

## Example

```powershell
python run_p7c_section_ds.py --section-id CH47-S01 --run-id smoke_ch47_s01_text_only
```

Current comparison pair:

```text
CH47-S01  reference has 1 card  (transaction monitoring alert generation and review)
CH42-S01  reference has 2 cards (pre-KYC assessment + typical KYC/CDD process)
```

The DS run should be compared against the existing reference cards with `compare_p7c_cards.py`.

API key environment variables follow the existing project convention:

```text
DEEPSEEK_API_KEY / DS_API_KEY / DS_KEY
DEEPSEEK_BASE_URL / DS_BASE_URL
```
