$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PhaseDir = Split-Path -Parent $ScriptDir
$PhasesDir = Split-Path -Parent $PhaseDir
$Python = "python"

& $Python (Join-Path $PhasesDir "phase00_quality_gate\scripts\phase0_quality_gate.py")
& $Python (Join-Path $ScriptDir "phase1_chapter_skeleton.py") --chapter-limit 5
