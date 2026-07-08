from __future__ import annotations

import http.client
import os
import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORKBENCH = ROOT / "cams工作台"
LOG_DIR = WORKBENCH / "logs"
PYTHON = ROOT / ".venv-new-question" / "Scripts" / "python.exe"
if not PYTHON.exists():
    PYTHON = Path(sys.executable)


def port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def start_if_needed(name: str, port: int, cwd: Path, args: list[str]) -> None:
    if port_open(port):
        print(f"[{name}] already listening on port {port}")
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stdout = (LOG_DIR / f"{name}.out.log").open("ab")
    stderr = (LOG_DIR / f"{name}.err.log").open("ab")
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    print(f"[{name}] starting on port {port} ...")
    subprocess.Popen(
        [str(PYTHON), *args],
        cwd=str(cwd),
        stdout=stdout,
        stderr=stderr,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=False,
    )


def find_dir(predicate) -> Path | None:
    if not WORKBENCH.exists():
        return None
    for path in WORKBENCH.iterdir():
        if path.is_dir() and predicate(path.name):
            return path
    return None


def check_http(name: str, port: int, path: str) -> None:
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        conn.request("GET", path)
        response = conn.getresponse()
        response.read()
        print(f"[{name}] OK {response.status} http://127.0.0.1:{port}{path}")
    except Exception:
        print(f"[{name}] not ready yet: http://127.0.0.1:{port}{path}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def main() -> int:
    if not WORKBENCH.exists():
        print(f"Workbench directory not found: {WORKBENCH}")
        return 1

    new_question_dir = find_dir(lambda name: name.endswith("题解析模块"))
    student_qa_dir = find_dir(lambda name: name.endswith("答疑模块_agentic"))

    start_if_needed(
        "workbench-front",
        5173,
        WORKBENCH,
        ["-m", "http.server", "5173", "--bind", "127.0.0.1"],
    )
    if new_question_dir:
        start_if_needed("new-question-api", 8765, new_question_dir, ["api/server.py"])
    else:
        print("[new-question-api] directory not found")

    if student_qa_dir:
        start_if_needed("student-qa-api", 8766, student_qa_dir, ["api/server.py"])
    else:
        print("[student-qa-api] directory not found")

    time.sleep(2)
    check_http("workbench-front", 5173, "/index.html")
    check_http("new-question-api", 8765, "/api/new-question/health")
    check_http("student-qa-api", 8766, "/api/student-qa/health")

    print()
    print("Workbench: http://127.0.0.1:5173/index.html")
    print(f"Logs: {LOG_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
