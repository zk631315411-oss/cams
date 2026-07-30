param(
    [string]$ModelPath = $env:CAMS_BGE_MODEL_PATH,
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Missing .venv. Run scripts\setup.ps1 first."
}
if (-not $ModelPath -or -not (Test-Path $ModelPath)) {
    throw "Set -ModelPath to a local BAAI/bge-m3 model directory."
}
if (-not $OutputPath) { $OutputPath = Join-Path $root "dist\cams-offline-win-py311" }

$bundle = [IO.Path]::GetFullPath($OutputPath)
$wheelhouse = Join-Path $bundle "wheelhouse"
$modelTarget = Join-Path $bundle "model\bge-m3"
New-Item -ItemType Directory -Force -Path $wheelhouse, (Split-Path $modelTarget) | Out-Null
& $python -m pip download --dest $wheelhouse -r (Join-Path $root "backend\requirements.txt")
Copy-Item -Recurse -Force -LiteralPath (Resolve-Path $ModelPath) -Destination $modelTarget
Get-ChildItem -LiteralPath $bundle -Recurse -File | Get-FileHash -Algorithm SHA256 |
    Select-Object @{Name="path";Expression={$_.Path.Substring($bundle.Length + 1)}}, Hash |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $bundle "manifest.json") -Encoding UTF8
Write-Output "Offline bundle ready: $bundle"
