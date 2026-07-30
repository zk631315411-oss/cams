@echo off
set "ROOT=%~dp0"
set "PYTHONHOME=%ROOT%runtime\python"
set "PYTHONUTF8=1"
set "CAMS_WORKSPACE_ROOT=%ROOT%"
set "CAMS_BGE_MODEL_PATH=%ROOT%runtime\models\bge-m3"
"%ROOT%runtime\python\python.exe" "%ROOT%backend\api.py" --workspace-root "%ROOT%" --port 8765
