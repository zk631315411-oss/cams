param(
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Missing .venv. Run scripts\setup.ps1 first."
}

$api = Join-Path $root "backend\api.py"
. (Join-Path $PSScriptRoot "model-path.ps1")
$env:CAMS_BGE_MODEL_PATH = Resolve-CamsBgeModelPath -Root $root
& $python $api --workspace-root $root --port $Port
