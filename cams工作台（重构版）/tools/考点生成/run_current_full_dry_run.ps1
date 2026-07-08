$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $here

try {
    $env:PYTHONUTF8 = "1"

    $env:PREVIEW_V15_V10_DIR = "work/preview_v10_full828"
    $env:PREVIEW_V15_NAMED_FILE = "work/preview_v8_naming_sample/named_exam_points_sample_v15_current_v10_822_ds_full_prompt_v3.json"
    $env:PREVIEW_V15_ADMISSION_FILE = "work/preview_v9_admission_gate/admission_decisions_v15_current_v10_822_ds_full_prompt_v3_rules_v4b.json"
    $env:PREVIEW_V15_ADMISSION_SUMMARY_FILE = "work/preview_v9_admission_gate/summary_v15_current_v10_822_ds_full_prompt_v3_rules_v4b.json"
    $env:PREVIEW_V15_RELATION_LAYER_FILE = "work/preview_v14_relation_layer/relation_layer_strict_trace_all100_review_merged.json"
    $env:PREVIEW_V15_OUT_DIR = "work/preview_v15_full_dry_run_v15_current_v10_822_ds_full_prompt_v3_rules_v4b"

    python -X utf8 preview_v15_full_dry_run_asset.py
}
finally {
    Pop-Location
}
