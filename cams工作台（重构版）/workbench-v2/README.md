# CAMS Research Workbench MVP

> Historical prototype. This MVP is no longer the formal CAMS workbench or release path. The formal application is maintained in `D:/守正公司工作区/cams考试工作台（正式版）/`.

The MVP is a standalone FastAPI + React application. It never writes to the
legacy reader or the phase4 explanation source directory.

## Local start

```powershell
cd workbench-v2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r api\requirements.txt
python -m api.cli import-content
python -m api.cli import-positions
uvicorn api.app:app --reload --port 8013

cd web
npm install
npm run dev
```

Open `http://localhost:5174` when that port is free. The default administrator is taken from
`ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env` (see `.env.example`).

`python -m api.cli verify` checks the real import: 395 unique questions and
the one known evidence exception. `python -m api.cli export-release <id>`
creates a DOCX delivery package for a release.

## Codex MCP

Copy the connection block in `codex-mcp.example.toml` into the local Codex MCP
configuration. The remote endpoint is mounted at `/mcp` on the API host. It
exposes `find_question`, `get_question`,
`begin_edit_task`, `search_kg`, `get_unit`, `open_source_page`,
`save_question`, `get_task_diff`, and `finish_edit_task`. The tools use the
dedicated local `codex` editor account and require its task lock for every
write.
