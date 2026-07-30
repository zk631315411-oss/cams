function Resolve-CamsBgeModelPath {
    param([Parameter(Mandatory = $true)][string]$Root)

    $model = (Resolve-Path (Join-Path $Root "runtime\models\bge-m3")).Path
    if ($env:OS -ne "Windows_NT" -or $model -notmatch '[^\x00-\x7F]') {
        return $model
    }

    # SentencePiece on Windows cannot reliably open model files through a Unicode path.
    $parent = Join-Path $env:LOCALAPPDATA "CAMSWorkbench\models"
    $link = Join-Path $parent "bge-m3"
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    if (Test-Path $link) {
        $item = Get-Item $link -Force
        if ($item.LinkType -ne "Junction" -or [string]$item.Target -ne $model) {
            throw "Model runtime path already exists but does not point to this CAMS workbench: $link"
        }
    } else {
        New-Item -ItemType Junction -Path $link -Target $model | Out-Null
    }
    return $link
}
