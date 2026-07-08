from __future__ import annotations

import http.client
import json
import os
import signal
import subprocess
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


RUNTIME_ROOT = Path(os.getenv("CAMS_RUNTIME_ROOT", "/opt/cams/runtime"))
WORKBENCH_ROOT = Path(os.getenv("CAMS_WORKBENCH_ROOT", RUNTIME_ROOT / "cams工作台"))
PYTHON = Path(os.getenv("CAMS_PYTHON", RUNTIME_ROOT / "venv" / "bin" / "python"))
LOG_DIR = Path(os.getenv("CAMS_LOG_DIR", RUNTIME_ROOT / "logs"))
IDLE_TIMEOUT_SECONDS = int(os.getenv("CAMS_API_IDLE_SECONDS", "600"))
START_TIMEOUT_SECONDS = int(os.getenv("CAMS_API_START_TIMEOUT_SECONDS", "180"))


SERVICES: dict[str, dict[str, Any]] = {
    "new-question": {
        "public_prefix": "/cams-api/new-question",
        "internal_prefix": "/api/new-question",
        "module_dir": WORKBENCH_ROOT / "新题解析模块",
        "port": 8765,
        "cmd": [str(PYTHON), "-m", "api.server"],
        "heavy_methods": {"POST"},
        "drafts_dir": WORKBENCH_ROOT / "新题解析模块" / "outputs" / "drafts",
        "list_summary": lambda data, path: {
            "draft_id": data.get("draft_id", path.stem),
            "created_at": data.get("created_at", ""),
            "status": data.get("status", ""),
            "ai_answer": (data.get("final", {}) or {}).get("ai_answer", []),
        },
    },
    "student-qa": {
        "public_prefix": "/cams-api/student-qa",
        "internal_prefix": "/api/student-qa",
        "module_dir": WORKBENCH_ROOT / "学生答疑模块_agentic",
        "port": 8766,
        "cmd": [str(PYTHON), "-m", "api.server"],
        "heavy_methods": {"POST"},
        "drafts_dir": WORKBENCH_ROOT / "学生答疑模块_agentic" / "outputs" / "drafts",
        "list_summary": lambda data, path: {
            "draft_id": data.get("draft_id", path.stem),
            "created_at": data.get("created_at", ""),
            "status": data.get("status", ""),
            "confidence": (data.get("final", {}) or {}).get("confidence", ""),
            "needs_teacher_review": (data.get("final", {}) or {}).get("needs_teacher_review", False),
            "student_stuck_point": (data.get("final", {}) or {}).get("student_stuck_point", ""),
        },
    },
}


class ManagedProcess:
    def __init__(self, key: str, config: dict[str, Any]) -> None:
        self.key = key
        self.config = config
        self.process: subprocess.Popen[bytes] | None = None
        self.last_used = 0.0
        self.active_requests = 0

    @property
    def port(self) -> int:
        return int(self.config["port"])

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def touch(self) -> None:
        self.last_used = time.time()

    def begin_request(self) -> None:
        self.active_requests += 1
        self.touch()

    def end_request(self) -> None:
        self.active_requests = max(0, self.active_requests - 1)
        self.touch()

    def start(self) -> None:
        if self.is_running():
            self.touch()
            return
        module_dir = Path(self.config["module_dir"])
        if not module_dir.exists():
            raise RuntimeError(f"module directory not found: {module_dir}")
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        stdout = (LOG_DIR / f"{self.key}.out.log").open("ab")
        stderr = (LOG_DIR / f"{self.key}.err.log").open("ab")
        env = os.environ.copy()
        env.setdefault("PYTHONUNBUFFERED", "1")
        self.process = subprocess.Popen(
            self.config["cmd"],
            cwd=str(module_dir),
            stdout=stdout,
            stderr=stderr,
            stdin=subprocess.DEVNULL,
            env=env,
            start_new_session=True,
        )
        self.touch()

    def stop(self) -> None:
        if not self.is_running():
            self.process = None
            return
        assert self.process is not None
        try:
            os.killpg(self.process.pid, signal.SIGTERM)
        except ProcessLookupError:
            self.process = None
            return
        except Exception:
            self.process.terminate()
        try:
            self.process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except Exception:
                self.process.kill()
            self.process.wait(timeout=10)
        finally:
            self.process = None


PROCESSES = {key: ManagedProcess(key, config) for key, config in SERVICES.items()}
LOCK = threading.RLock()


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip(";").strip()
        if not name or name in os.environ:
            continue
        os.environ[name] = value.strip('"').strip("'")


def load_runtime_env() -> None:
    _load_env_file(RUNTIME_ROOT / ".env")
    _load_env_file(RUNTIME_ROOT / "cams-new-question.env")


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


def _read_body(handler: BaseHTTPRequestHandler) -> bytes:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    return handler.rfile.read(length) if length else b""


def _service_for_path(path: str) -> tuple[str, dict[str, Any]] | None:
    for key, config in SERVICES.items():
        prefix = str(config["public_prefix"])
        if path == prefix or path.startswith(prefix + "/"):
            return key, config
    return None


def _internal_path(path: str, config: dict[str, Any]) -> str:
    public_prefix = str(config["public_prefix"])
    internal_prefix = str(config["internal_prefix"])
    suffix = path[len(public_prefix):]
    return internal_prefix + suffix


def _wait_for_health(config: dict[str, Any]) -> None:
    deadline = time.time() + START_TIMEOUT_SECONDS
    health_path = str(config["internal_prefix"]) + "/health"
    last_error = ""
    while time.time() < deadline:
        try:
            conn = http.client.HTTPConnection("127.0.0.1", int(config["port"]), timeout=4)
            conn.request("GET", health_path)
            response = conn.getresponse()
            response.read()
            conn.close()
            if response.status == 200:
                return
            last_error = f"health status {response.status}"
        except Exception as exc:
            last_error = str(exc)
        time.sleep(1)
    raise TimeoutError(f"service did not become healthy: {last_error}")


def _ensure_service(key: str) -> None:
    with LOCK:
        for other_key, proc in PROCESSES.items():
            if other_key != key:
                if proc.is_running() and proc.active_requests:
                    raise RuntimeError(f"{other_key} is still processing; please retry after it finishes")
                proc.stop()
        proc = PROCESSES[key]
        proc.start()
    _wait_for_health(proc.config)


def _proxy(handler: BaseHTTPRequestHandler, key: str, config: dict[str, Any], body: bytes) -> None:
    proc = PROCESSES[key]
    proc.begin_request()
    conn = None
    try:
        parsed = urlparse(handler.path)
        target_path = _internal_path(parsed.path, config)
        if parsed.query:
            target_path += "?" + parsed.query
        headers = {
            name: value
            for name, value in handler.headers.items()
            if name.lower() not in {"host", "content-length", "connection", "accept-encoding"}
        }
        if body:
            headers["Content-Length"] = str(len(body))
        conn = http.client.HTTPConnection("127.0.0.1", int(config["port"]), timeout=900)
        conn.request(handler.command, target_path, body=body, headers=headers)
        response = conn.getresponse()
        data = response.read()
        handler.send_response(response.status)
        for name, value in response.getheaders():
            lower = name.lower()
            if lower in {"transfer-encoding", "connection", "content-length"}:
                continue
            handler.send_header(name, value)
        handler.send_header("Content-Length", str(len(data)))
        handler.send_header("Access-Control-Allow-Origin", "*")
        handler.end_headers()
        handler.wfile.write(data)
    finally:
        if conn:
            conn.close()
        proc.end_request()


def _safe_draft_id(raw: str) -> str:
    return Path(raw).stem


def _draft_path(config: dict[str, Any], draft_id: str) -> Path:
    drafts_dir = Path(config["drafts_dir"])
    return drafts_dir / f"{_safe_draft_id(draft_id)}.json"


def _list_drafts(config: dict[str, Any]) -> list[dict[str, Any]]:
    drafts_dir = Path(config["drafts_dir"])
    summary = config["list_summary"]
    rows = []
    for path in sorted(drafts_dir.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rows.append(summary(data, path))
        except Exception:
            continue
    return rows[:50]


def _serve_lightweight(handler: BaseHTTPRequestHandler, key: str, config: dict[str, Any]) -> bool:
    parsed = urlparse(handler.path)
    internal = _internal_path(parsed.path, config)
    if handler.command == "GET" and internal.endswith("/health"):
        _json_response(handler, 200, {
            "ok": True,
            "service": key,
            "managed": True,
            "worker_running": PROCESSES[key].is_running(),
        })
        return True
    if handler.command == "GET" and internal.endswith("/drafts"):
        _json_response(handler, 200, {"drafts": _list_drafts(config)})
        return True
    drafts_prefix = str(config["internal_prefix"]) + "/drafts/"
    if internal.startswith(drafts_prefix):
        draft_id = internal.rsplit("/", 1)[-1]
        path = _draft_path(config, draft_id)
        if path.parent != Path(config["drafts_dir"]):
            _json_response(handler, 400, {"ok": False, "error": "invalid_draft_id"})
            return True
        if handler.command == "GET":
            if not path.exists():
                _json_response(handler, 404, {"ok": False, "error": "draft_not_found"})
            else:
                _json_response(handler, 200, {"ok": True, "draft": json.loads(path.read_text(encoding="utf-8"))})
            return True
        if handler.command == "DELETE":
            if not path.exists():
                _json_response(handler, 404, {"ok": False, "error": "draft_not_found"})
            else:
                path.unlink()
                _json_response(handler, 200, {"ok": True, "draft_id": path.stem})
            return True
    return False


class ManagerHandler(BaseHTTPRequestHandler):
    server_version = "CamsApiManager/0.1"

    def do_OPTIONS(self) -> None:
        _json_response(self, 200, {"ok": True})

    def do_GET(self) -> None:
        self._handle()

    def do_POST(self) -> None:
        self._handle()

    def do_DELETE(self) -> None:
        self._handle()

    def _handle(self) -> None:
        matched = _service_for_path(urlparse(self.path).path)
        if not matched:
            _json_response(self, 404, {"ok": False, "error": "not_found"})
            return
        key, config = matched
        try:
            if _serve_lightweight(self, key, config):
                return
            body = _read_body(self)
            if self.command in config["heavy_methods"]:
                _ensure_service(key)
            elif not PROCESSES[key].is_running():
                _json_response(self, 503, {"ok": False, "error": "worker_not_running"})
                return
            _proxy(self, key, config, body)
        except Exception as exc:
            traceback.print_exc()
            _json_response(self, 503, {"ok": False, "error": "manager_error", "message": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[cams-api-manager] " + fmt % args + "\n")


def idle_reaper() -> None:
    while True:
        time.sleep(30)
        now = time.time()
        with LOCK:
            for proc in PROCESSES.values():
                if proc.is_running() and not proc.active_requests and proc.last_used and now - proc.last_used > IDLE_TIMEOUT_SECONDS:
                    proc.stop()


def main() -> int:
    load_runtime_env()
    host = os.getenv("CAMS_API_MANAGER_HOST", "127.0.0.1")
    port = int(os.getenv("CAMS_API_MANAGER_PORT", "8780"))
    threading.Thread(target=idle_reaper, daemon=True).start()
    server = ThreadingHTTPServer((host, port), ManagerHandler)
    print(f"[cams-api-manager] listening on http://{host}:{port}")
    print(f"[cams-api-manager] idle timeout: {IDLE_TIMEOUT_SECONDS}s")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[cams-api-manager] stopping")
    finally:
        with LOCK:
            for proc in PROCESSES.values():
                proc.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
