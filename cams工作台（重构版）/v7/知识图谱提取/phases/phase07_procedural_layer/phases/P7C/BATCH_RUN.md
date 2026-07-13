# P7C Batch Run

This note defines the engineering entry point for batch P7C extraction. It is intentionally separate from `README.md` because that file contains legacy encoding issues.

## Entry Point

```powershell
python ../../scripts/run_p7c_batch_ds.py --sections all --run-id p7c_ds_none_v1 --thinking-effort none --concurrency 20
```

## Default Policy

```text
model: deepseek-v4-pro
thinking_effort: none
concurrency: 20
input_policy: section_text_with_unit_anchors + allowed_unit_ids only
```

`thinking_effort=none` is the default for first-pass P7C extraction. It gives better recall for control and judgement cards while keeping the prompt constrained to textbook section text.

`thinking_effort=high` is reserved for disputed sections after P7D review. It should not replace the first-pass `none` run, because A/B testing showed that `high` can be too conservative and skip useful control cards.

## Dry Run First

Run this before any real API batch:

```powershell
python ../../scripts/run_p7c_batch_ds.py --sections all --run-id dry_run_p7c_ds_none_v1 --thinking-effort none --concurrency 20 --dry-run
```

The dry run writes only `run_plan.json` and does not call the API.

## Outputs

```text
outputs/<run_id>/run_plan.json
outputs/<run_id>/run_summary.json
outputs/<run_id>/run_summary.md
outputs/<run_id>/<section_id>/prompt.md
outputs/<run_id>/<section_id>/raw_response.txt
outputs/<run_id>/<section_id>/cards.raw.json
outputs/<run_id>/<section_id>/validation_report.md
outputs/<run_id>/<section_id>/run_manifest.json
```

All manifest paths are written with forward slashes to avoid invalid JSON escape sequences on Windows.

## Current Stop Point

The batch runner is prepared, and dry-run planning has been tested against 32 section packages. Do not run the real batch until the user explicitly confirms.
