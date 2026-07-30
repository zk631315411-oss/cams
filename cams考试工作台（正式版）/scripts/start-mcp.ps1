$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Missing .venv. Run scripts\setup.ps1 first."
}

$server = Join-Path $root "backend\mcp_server.py"
. (Join-Path $PSScriptRoot "model-path.ps1")
$env:CAMS_BGE_MODEL_PATH = Resolve-CamsBgeModelPath -Root $root
& $python $server --workspace-root $root
