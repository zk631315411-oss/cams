"""
Local HTTP API for the new-question analysis module.

This intentionally uses only the Python standard library so the first usable
integration does not depend on an extra FastAPI/Flask installation.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

_HERE = Path(__file__).resolve().parent

from evidence_pool import load_new_question_runtime  # noqa: E402
from logic import run_new_question_pipeline  # noqa: E402

_RUNTIME = None
_MIN_AVAILABLE_MB_FOR_ANALYSIS = int(os.getenv("CAMS_MIN_AVAILABLE_MB", "450"))


def get_runtime():
    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME = load_new_question_runtime(evidence_scope="v6-sentence")
    return _RUNTIME


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


class NewQuestionHandler(BaseHTTPRequestHandler):
    server_version = "CamsNewQuestionAPI/0.1"

    def do_OPTIONS(self) -> None:
        _json_response(self, 200, {"ok": True})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/new-question/health":
            _json_response(self, 200, {"ok": True, "service": "new-question"})
            return
        if parsed.path == "/api/new-question/drafts":
            _json_response(self, 200, {"drafts": self._list_drafts()})
            return
        if parsed.path.startswith("/api/new-question/drafts/"):
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
        if parsed.path != "/api/new-question/analyze":
            _json_response(self, 404, {"ok": False, "error": "not_found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            payload = json.loads(raw or "{}")
            text = str(payload.get("text", "")).strip()
            top_k = int(payload.get("top_k", 30) or 30)
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
                    "message": "服务器可用内存不足，当前解析任务已暂停，请稍后再试。",
                    "available_mb": available_mb,
                },
            )
            return

        try:
            result = run_new_question_pipeline(text, rt=get_runtime(), top_k=top_k)
            _json_response(self, 200, {"ok": True, "draft": result})
        except Exception as exc:
            traceback.print_exc()
            _json_response(self, 500, {"ok": False, "error": str(exc)})

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/new-question/drafts/"):
            _json_response(self, 404, {"ok": False, "error": "not_found"})
            return

        draft_id = parsed.path.rsplit("/", 1)[-1]
        if self._delete_draft(draft_id):
            _json_response(self, 200, {"ok": True, "draft_id": Path(draft_id).stem})
        else:
            _json_response(self, 404, {"ok": False, "error": "draft_not_found"})

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[new-question-api] " + fmt % args + "\n")

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
            rows.append({
                "draft_id": data.get("draft_id", path.stem),
                "created_at": data.get("created_at", ""),
                "status": data.get("status", ""),
                "ai_answer": data.get("final", {}).get("ai_answer", []),
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
    host = "127.0.0.1"
    port = 8765
    server = ThreadingHTTPServer((host, port), NewQuestionHandler)
    print(f"[new-question-api] listening on http://{host}:{port}")
    print("[new-question-api] first analysis may take a while while BGE/runtime loads")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[new-question-api] stopping")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
