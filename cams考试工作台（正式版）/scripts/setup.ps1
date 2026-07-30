param(
    [string]$Python = "python",
    [string]$OfflineBundle = ""
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    & $Python -m venv (Join-Path $root ".venv")
}

& $venvPython -m pip install --upgrade pip
if ($OfflineBundle) {
    $bundle = (Resolve-Path $OfflineBundle).Path
    $wheelhouse = Join-Path $bundle "wheelhouse"
    $model = Join-Path $bundle "model\bge-m3"
    if (-not (Test-Path $wheelhouse) -or -not (Test-Path $model)) {
        throw "Offline bundle must contain wheelhouse and model\bge-m3."
    }
    & $venvPython -m pip install --no-index --find-links $wheelhouse -r (Join-Path $root "backend\requirements.txt")
    $runtime = Join-Path $root "runtime\models"
    New-Item -ItemType Directory -Force -Path $runtime | Out-Null
    Copy-Item -Recurse -Force -LiteralPath $model -Destination (Join-Path $runtime "bge-m3")
} else {
    & $venvPython -m pip install --timeout 30 --retries 2 --progress-bar on -r (Join-Path $root "backend\requirements.txt")
    $runtime = Join-Path $root "runtime\models"
    New-Item -ItemType Directory -Force -Path $runtime | Out-Null
    $bundledModel = Join-Path $runtime "bge-m3"
    if (-not (Test-Path $bundledModel)) {
        $env:CAMS_SETUP_MODEL_DIR = $bundledModel
        & $venvPython -c "import os; from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3').save(os.environ['CAMS_SETUP_MODEL_DIR'])"
    }
}
. (Join-Path $PSScriptRoot "model-path.ps1")
$env:CAMS_BGE_MODEL_PATH = Resolve-CamsBgeModelPath -Root $root
& $venvPython -c "import os, numpy, sklearn, sentence_transformers, torch; from sentence_transformers import SentenceTransformer; SentenceTransformer(os.environ['CAMS_BGE_MODEL_PATH'], local_files_only=True); print('CAMS retrieval environment is ready.')"
