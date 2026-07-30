param(
    [string]$ModelPath = "",
    [string]$OutputDirectory = "",
    [string]$PythonHome = "",
    [switch]$CreateArchive
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venv = Join-Path $root ".venv"
$venvPython = Join-Path $venv "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Missing .venv. Run scripts\setup.ps1 before building a portable package."
}

if (-not $PythonHome) {
    $PythonHome = (& $venvPython -c "import sys; print(sys.base_prefix)").Trim()
}
if (-not (Test-Path (Join-Path $PythonHome "python.exe"))) {
    throw "PythonHome must point to a complete Windows Python installation."
}
if (-not $ModelPath) {
    $cache = Join-Path $env:USERPROFILE ".cache\huggingface\hub\models--BAAI--bge-m3\snapshots"
    $ModelPath = (Get-ChildItem -LiteralPath $cache -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
}
if (-not $ModelPath -or -not (Test-Path (Join-Path $ModelPath "pytorch_model.bin"))) {
    throw "ModelPath must point to a local BAAI/bge-m3 snapshot containing pytorch_model.bin."
}

if (-not $OutputDirectory) { $OutputDirectory = Join-Path $root "dist\CAMS-Workbench-Portable" }
$package = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path $package) { Remove-Item -LiteralPath $package -Recurse -Force }
New-Item -ItemType Directory -Force -Path $package | Out-Null

# Copy the workbench, excluding build products and machine-local environments.
$excluded = @(".venv", "dist", "runtime", ".git", "__pycache__")
Get-ChildItem -LiteralPath $root -Force | Where-Object { $_.Name -notin $excluded } |
    Copy-Item -Destination $package -Recurse -Force

# A copied base Python plus the prepared virtual-environment packages is relocatable inside the package.
$runtimePython = Join-Path $package "runtime\python"
New-Item -ItemType Directory -Force -Path $runtimePython | Out-Null
Get-ChildItem -LiteralPath $PythonHome -Force | Copy-Item -Destination $runtimePython -Recurse -Force
Copy-Item -LiteralPath (Join-Path $venv "Lib\site-packages\*") -Destination (Join-Path $runtimePython "Lib\site-packages") -Recurse -Force

# Sentence Transformers uses PyTorch weights; the cached ONNX duplicate is intentionally excluded.
$runtimeModel = Join-Path $package "runtime\models\bge-m3"
New-Item -ItemType Directory -Force -Path $runtimeModel | Out-Null
Get-ChildItem -LiteralPath $ModelPath -Force | Where-Object { $_.Name -ne "onnx" } |
    Copy-Item -Destination $runtimeModel -Recurse -Force

Copy-Item -LiteralPath (Join-Path $root "scripts\portable\Start-Web.cmd") -Destination (Join-Path $package "Start-Web.cmd")
Copy-Item -LiteralPath (Join-Path $root "scripts\portable\Start-Codex-MCP.cmd") -Destination (Join-Path $package "Start-Codex-MCP.cmd")
Copy-Item -LiteralPath (Join-Path $root "scripts\portable\README-PORTABLE.md") -Destination (Join-Path $package "README-PORTABLE.md")

$env:PYTHONHOME = $runtimePython
$env:CAMS_WORKSPACE_ROOT = $package
$env:CAMS_BGE_MODEL_PATH = $runtimeModel
& (Join-Path $runtimePython "python.exe") -c "import numpy, sentence_transformers, torch; print('portable runtime imports passed')"
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
Remove-Item Env:CAMS_WORKSPACE_ROOT -ErrorAction SilentlyContinue
Remove-Item Env:CAMS_BGE_MODEL_PATH -ErrorAction SilentlyContinue

Get-ChildItem -LiteralPath $package -Recurse -File | Get-FileHash -Algorithm SHA256 |
    Select-Object @{Name="path";Expression={$_.Path.Substring($package.Length + 1)}}, Hash |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $package "manifest.json") -Encoding UTF8

if ($CreateArchive) {
    $archive = "$package.tar.gz"
    if (Test-Path $archive) { Remove-Item -LiteralPath $archive -Force }
    tar.exe -czf $archive -C (Split-Path $package) (Split-Path $package -Leaf)
    Write-Output "Portable archive ready: $archive"
} else {
    Write-Output "Portable directory ready: $package"
}
