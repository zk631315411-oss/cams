$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $here

try {
    $env:PYTHONUTF8 = "1"

    $batchName = "v15_current_v10_822_ds_full_prompt_v3"
    $rulesBatchName = "v15_current_v10_822_ds_full_prompt_v3_rules_v4b"
    $existingDsOutput = Join-Path $here "work\preview_v8_naming_sample\agent_naming_output_$batchName.json"

    if (-not (Test-Path -LiteralPath $existingDsOutput)) {
        throw "Missing existing DS naming output: $existingDsOutput. This no-API runner only validates and repackages an existing DS batch."
    }

    $env:PREVIEW_V5_RELATION_REVIEW_LIMIT = "3814"
    $env:PREVIEW_V5_MAX_RELATION_CANDIDATES_PER_POINT = "999"
    $env:PREVIEW_V5_RELATION_MIN_SCORE = "50"

    python -X utf8 preview_v1_seed_points.py
    python -X utf8 preview_v5_structure_preview.py
    python -X utf8 preview_v6_structure_draft.py
    python -X utf8 preview_v10_full828_materialize.py

    $env:PREVIEW_V8_SOURCE_DIR = "work/preview_v10_full828"
    $env:PREVIEW_V8_BATCH_NAME = $batchName
    $env:PREVIEW_V8_SAMPLE_LIMIT = "822"
    python -X utf8 preview_v8_naming_sample.py

    $env:PREVIEW_V9_SOURCE_FILE = "work/preview_v8_naming_sample/named_exam_points_sample_$batchName.json"
    $env:PREVIEW_V9_BATCH_NAME = $rulesBatchName
    python -X utf8 preview_v9_admission_gate.py

    PowerShell -NoProfile -ExecutionPolicy Bypass -File .\run_current_full_dry_run.ps1

    $summaryPath = Join-Path $here "work\preview_v15_full_dry_run_$rulesBatchName\summary.json"
    $summary = Get-Content -LiteralPath $summaryPath -Encoding UTF8 | ConvertFrom-Json

    if (
        $summary.source_point_count -ne 822 -or
        $summary.matched_named_count -ne 822 -or
        $summary.matched_admission_count -ne 822 -or
        $summary.missing_named_count -ne 0 -or
        $summary.missing_admission_count -ne 0 -or
        $summary.source_drift_count -ne 0
    ) {
        throw "Pipeline completed but summary is not production-clean. See $summaryPath"
    }

    Write-Host "pipeline ok: 822 points, 822 names, 822 admission decisions, 0 missing, 0 source drift"
}
finally {
    Pop-Location
}
