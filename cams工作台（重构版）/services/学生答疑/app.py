"""
Local HTTP API for the agentic student-QA module.

It mirrors the new-question API style and intentionally depends only on the
Python standard library for the HTTP layer.
"""

from __future__ import annotations

import json
import os
import re
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_HERE = Path(__file__).resolve().parent

from logic import run_student_qa_pipeline  # noqa: E402

_MIN_AVAILABLE_MB_FOR_ANALYSIS = int(os.getenv("CAMS_MIN_AVAILABLE_MB", "450"))


def _load_local_env() -> None:
    """Best-effort local dev convenience; does not print secret values."""
    for env_path in (Path.home() / ".bashrc", Path.home() / ".zshrc", Path.home() / ".profile"):
        if not env_path.exists():
            continue
        try:
            lines = env_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            line = re.sub(r"^export\s+", "", line)
            for name in ("DEEPSEEK_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_BASE_URL"):
                if line.startswith(name + "=") and not os.environ.get(name):
                    value = line.split("=", 1)[1].strip().strip(";").strip()
                    os.environ[name] = value.strip('"').strip("'").strip()


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


def _available_memory_mb() -> int | None:
    try:
        meminfo = Path("/proc/meminfo").read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    for line in meminfo.splitlines():
        if line.startswith("MemAvailable:"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1]) // 1024
    return None


class StudentQaHandler(BaseHTTPRequestHandler):
    server_version = "CamsStudentQaAPI/0.1"

    def do_OPTIONS(self) -> None:
        _json_response(self, 200, {"ok": True})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/student-qa/health":
            _json_response(self, 200, {"ok": True, "service": "student-qa"})
            return
        if parsed.path == "/api/student-qa/drafts":
            _json_response(self, 200, {"drafts": self._list_drafts()})
            return
        if parsed.path.startswith("/api/student-qa/drafts/"):
            draft_id = parsed.path.rsplit("/", 1)[-1]
            draft = self._read_draft(draft_id)
            if draft is None:
                _json_response(self, 404, {"ok": False, "error": "draft_not_found"})
            else:
                _json_response(self, 200, {"ok": True, "draft": draft})
            return
        _json_response(self, 404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/student-qa/analyze":
            _json_response(self, 404, {"ok": False, "error": "not_found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            payload = json.loads(raw or "{}")
            text = str(payload.get("text", "")).strip()
            top_k = int(payload.get("top_k", 12) or 12)
            max_claims = int(payload.get("max_claims", 12) or 12)
        except Exception as exc:
            _json_response(self, 400, {"ok": False, "error": f"invalid_request: {exc}"})
            return

        if not text:
            _json_response(self, 400, {"ok": False, "error": "text_required"})
            return

        available_mb = _available_memory_mb()
        if available_mb is not None and available_mb < _MIN_AVAILABLE_MB_FOR_ANALYSIS:
            _json_response(
                self,
                503,
                {
                    "ok": False,
                    "error": "server_busy_low_memory",
                    "message": "服务器可用内存不足，当前答疑任务已暂停，请稍后再试。",
                    "available_mb": available_mb,
                },
            )
            return

        try:
            result = run_student_qa_pipeline(text, top_k=top_k, max_claims=max_claims)
            _json_response(self, 200, {"ok": True, "draft": result})
        except Exception as exc:
            traceback.print_exc()
            _json_response(self, 500, {"ok": False, "error": str(exc)})

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/student-qa/drafts/"):
            _json_response(self, 404, {"ok": False, "error": "not_found"})
            return

        draft_id = parsed.path.rsplit("/", 1)[-1]
        if self._delete_draft(draft_id):
            _json_response(self, 200, {"ok": True, "draft_id": Path(draft_id).stem})
        else:
            _json_response(self, 404, {"ok": False, "error": "draft_not_found"})

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[student-qa-api] " + fmt % args + "\n")

    @staticmethod
    def _drafts_dir() -> Path:
        return _HERE / "outputs" / "drafts"

    def _list_drafts(self) -> list[dict[str, Any]]:
        rows = []
        for path in sorted(self._drafts_dir().glob("*.json"), reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            final = data.get("final", {}) or {}
            rows.append({
                "draft_id": data.get("draft_id", path.stem),
                "created_at": data.get("created_at", ""),
                "status": data.get("status", ""),
                "confidence": final.get("confidence", ""),
                "needs_teacher_review": final.get("needs_teacher_review", False),
                "student_stuck_point": final.get("student_stuck_point", ""),
            })
        return rows[:50]

    def _read_draft(self, draft_id: str) -> dict[str, Any] | None:
        safe_id = Path(draft_id).stem
        path = self._drafts_dir() / f"{safe_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _delete_draft(self, draft_id: str) -> bool:
        safe_id = Path(draft_id).stem
        path = self._drafts_dir() / f"{safe_id}.json"
        if not path.exists() or path.parent != self._drafts_dir():
            return False
        path.unlink()
        return True


def main() -> int:
    _load_local_env()
    host = "127.0.0.1"
    port = 8766
    server = ThreadingHTTPServer((host, port), StudentQaHandler)
    print(f"[student-qa-api] listening on http://{host}:{port}")
    print("[student-qa-api] first analysis may take a while while evidence runtime loads")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[student-qa-api] stopping")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
