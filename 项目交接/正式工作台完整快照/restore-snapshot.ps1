param(
    [Parameter(Mandatory = $true)]
    [string]$Destination,
    [switch]$KeepArchive
)

$ErrorActionPreference = "Stop"

$expectedParts = [ordered]@{
    "formal-workbench-20260730.tar.gz.part-000" = "5CA3474D4F955B191E318C7520A0B95FCBFA16AD47B3E7F76BFF2424D9DA22BB"
    "formal-workbench-20260730.tar.gz.part-001" = "36A6898CB4117FE7F2805FDE3BB7007568674872FA01A78CE3153A928FC285CA"
}
$expectedArchiveHash = "6A2A04B6542B04AA7849B637BDC5A5D29F13982D11A99FD4AFBFAF061B0539B1"
$snapshotDirectory = $PSScriptRoot
$destinationPath = [IO.Path]::GetFullPath($Destination)
$archivePath = Join-Path ([IO.Path]::GetTempPath()) "formal-workbench-20260730-$PID.tar.gz"

if (Test-Path -LiteralPath (Join-Path $destinationPath "cams考试工作台（正式版）")) {
    throw "Refusing to overwrite an existing restored workbench: $destinationPath"
}

New-Item -ItemType Directory -Force -Path $destinationPath | Out-Null
$output = [IO.File]::Create($archivePath)
try {
    foreach ($entry in $expectedParts.GetEnumerator()) {
        $partPath = Join-Path $snapshotDirectory $entry.Key
        if (-not (Test-Path -LiteralPath $partPath)) {
            throw "Missing snapshot part. Run git lfs pull first: $($entry.Key)"
        }
        $actualPartHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $partPath).Hash
        if ($actualPartHash -ne $entry.Value) {
            throw "Snapshot part hash mismatch: $($entry.Key)"
        }
        $input = [IO.File]::OpenRead($partPath)
        try {
            $input.CopyTo($output)
        }
        finally {
            $input.Dispose()
        }
    }
}
finally {
    $output.Dispose()
}

$actualArchiveHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archivePath).Hash
if ($actualArchiveHash -ne $expectedArchiveHash) {
    throw "Reassembled archive hash mismatch."
}

& tar.exe -xzf $archivePath -C $destinationPath
if ($LASTEXITCODE -ne 0) {
    throw "tar extraction failed with exit code $LASTEXITCODE"
}

if (-not $KeepArchive) {
    Remove-Item -Force -LiteralPath $archivePath
}

Write-Host "Snapshot restored and verified: $destinationPath"
