$ErrorActionPreference = "Stop"

$Pipeline = $PSScriptRoot
$Root = Split-Path -Parent $Pipeline
$LogDir = Join-Path $Pipeline "output\run_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Transcript = Join-Path $LogDir "run50_combined_$Stamp.transcript.log"
Start-Transcript -Path $Transcript | Out-Null

try {
    $Bashrc = Get-Content -LiteralPath "C:\Users\hp\.bashrc" -Raw
    if ($Bashrc -match 'DEEPSEEK_API_KEY\s*=\s*"([^"]+)"') {
        $env:DEEPSEEK_API_KEY = $Matches[1]
    }
    elseif ($Bashrc -match "DEEPSEEK_API_KEY\s*=\s*'([^']+)'") {
        $env:DEEPSEEK_API_KEY = $Matches[1]
    }
    else {
        throw "DEEPSEEK_API_KEY not found in C:\Users\hp\.bashrc"
    }

    Set-Location -LiteralPath $Root
    python -X utf8 (Join-Path $Pipeline "run_step1.py") `
        --retrieval agentic `
        --limit 50 `
        --max-followups 1 `
        --top-k 35 `
        --card-scan off `
        --card-scan-chunk-size 180 `
        --evidence-scope ch2-plus-v6-except
}
finally {
    Stop-Transcript | Out-Null
}
