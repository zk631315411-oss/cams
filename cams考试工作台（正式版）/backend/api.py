"""原生 HTTP API，同时提供正式版前端静态文件。"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from backup import create_backup
from drafting.service import prepare_draft_input
from retrieval.assets import AssetError
from retrieval.service import retrieve_question_evidence, search_evidence
from storage import LockError, STORE, WorkspaceError, WorkspaceStore
from textbook import TextbookError, TextbookService

ROOT = Path(os.environ.get("CAMS_WORKSPACE_ROOT") or Path(__file__).resolve().parents[1]).resolve()
FRONTEND = ROOT / "frontend"
TEXTBOOK = TextbookService(ROOT)


class Handler(BaseHTTPRequestHandler):
    server_version = "CamsFormalAPI/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("[api] " + fmt % args + "\n")

    def _json(self, status: int, payload: object) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers(); self.wfile.write(raw)

    def _binary(self, status: int, content_type: str, raw: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _body(self) -> dict:
        size = int(self.headers.get("Content-Length", "0") or 0)
        if size > 2_000_000:
            raise WorkspaceError("请求体过大")
        raw = self.rfile.read(size).decode("utf-8") if size else "{}"
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise WorkspaceError("请求体必须为 JSON 对象")
        return value

    @staticmethod
    def _actor(body: dict) -> tuple[str, str]:
        return str(body.get("actor") or "web-user"), str(body.get("reason") or "未填写原因")

    @staticmethod
    def _expected(body: dict) -> tuple[int, int]:
        version, revision = body.get("expected_question_version"), body.get("expected_archive_revision")
        if not isinstance(version, int) or not isinstance(revision, int):
            raise WorkspaceError("请先刷新题目，再提交当前题目版本和档案修订号")
        return version, revision

    @staticmethod
    def _confirmed(body: dict, operation: str) -> None:
        if body.get("confirmed") is not True:
            raise WorkspaceError(f"{operation} 需要明确确认")
        if not str(body.get("reason") or "").strip():
            raise WorkspaceError(f"{operation} 必须填写修改理由")

    def _static(self, path: str) -> None:
        relative = Path(unquote(path.lstrip("/")) or "index.html")
        candidate = (FRONTEND / relative).resolve()
        if FRONTEND.resolve() not in candidate.parents and candidate != FRONTEND.resolve():
            self.send_error(403); return
        if candidate.is_dir(): candidate /= "index.html"
        if not candidate.exists() or not candidate.is_file():
            self.send_error(404); return
        raw = candidate.read_bytes()
        self.send_response(200)
        content_type = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
            content_type += "; charset=utf-8"
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers(); self.wfile.write(raw)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/health": return self._json(200, {"ok": True})
            if path == "/api/active-context": return self._json(200, STORE.read_active_context())
            if path == "/api/settings/deepseek": return self._json(200, STORE.read_deepseek_settings())
            if path == "/api/textbook/manifest": return self._json(200, {"textbook": TEXTBOOK.info()})
            if path == "/api/textbook/chapters": return self._json(200, TEXTBOOK.chapters())
            if path == "/api/textbook/page":
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                language = params.get("lang", ["zh"])[0]
                page = int(params.get("page", ["1"])[0])
                scale = float(params.get("scale", ["1.6"])[0])
                raw, _metadata = TEXTBOOK.render_page(language, page, scale)
                self._binary(200, "image/png", raw)
                return
            if path == "/api/questions":
                parsed = urlparse(self.path)
                params = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
                status, query = params.get("status", ""), params.get("query", "")
                offset, limit = max(0, int(params.get("offset", "0"))), min(500, max(1, int(params.get("limit", "500"))))
                all_rows = STORE.list_questions(status=status, query=query)
                return self._json(200, {"items": all_rows[offset:offset + limit], "total": len(all_rows), "offset": offset, "limit": limit})
            if path == "/api/releases": return self._json(200, {"items": STORE.list_releases()})
            parts = path.strip("/").split("/")
            if len(parts) >= 3 and parts[:2] == ["api", "questions"]:
                qid = parts[2]
                if len(parts) == 3:
                    return self._json(200, STORE.workflow_detail(qid))
                if len(parts) == 4 and parts[3] == "audit": return self._json(200, {"items": STORE.read_audit(qid)})
                if len(parts) == 4 and parts[3] == "tasks": return self._json(200, {"items": STORE.read_task_history(qid)})
                if len(parts) == 4 and parts[3] == "evidence":
                    params = {key: values[-1] for key, values in parse_qs(urlparse(self.path).query).items()}
                    return self._json(200, STORE.read_evidence_catalog(
                        qid, scope=params.get("scope", "all"), source_kind=params.get("source_kind", ""),
                        method=params.get("method", ""), option=params.get("option", ""),
                        run_id=params.get("run_id", ""),
                        offset=int(params.get("offset", "0")), limit=int(params.get("limit", "20"))))
                if len(parts) == 5 and parts[3] == "source":
                    intake = STORE.read_record(qid, "intake") or {}
                    allowed = {item.get("name") for item in intake.get("attachments", [])}
                    filename = unquote(parts[4])
                    if filename not in allowed:
                        raise WorkspaceError("原件不存在")
                    candidate = (STORE._question_dir(qid) / "source" / "files" / filename).resolve()
                    source_root = (STORE._question_dir(qid) / "source" / "files").resolve()
                    if source_root not in candidate.parents or not candidate.is_file():
                        raise WorkspaceError("原件不存在")
                    raw = candidate.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", mimetypes.guess_type(filename)[0] or "application/octet-stream")
                    self.send_header("Content-Length", str(len(raw)))
                    self.send_header("Content-Disposition", f"inline; filename*=UTF-8''{quote(filename)}")
                    self.end_headers(); self.wfile.write(raw); return
            if len(parts) == 4 and parts[:2] == ["api", "releases"] and parts[3] == "manifest":
                return self._json(200, {"manifest": STORE._read_json(STORE.releases / parts[2] / "manifest.json")})
            self._static(path)
        except ValueError as exc:
            self._json(400, {"ok": False, "error": str(exc)})
        except (WorkspaceError, TextbookError) as exc:
            self._json(404, {"ok": False, "error": str(exc)})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            body, actor_reason = self._body(), None
            actor, reason = self._actor(body)
            if path == "/api/settings/deepseek":
                return self._json(200, STORE.write_deepseek_settings(
                    bool(body.get("enabled")), str(body.get("base_url") or ""),
                    str(body.get("model") or ""), body.get("api_key")))
            if path == "/api/active-context":
                return self._json(200, STORE.write_active_context(str(body.get("question_id") or "")))
            if path == "/api/textbook/match":
                result = TEXTBOOK.match(str(body.get("language") or "zh"), int(body.get("page") or 1), str(body.get("query") or ""))
                return self._json(200, result)
            if path == "/api/questions":
                return self._json(405, {"ok": False, "error": "新题只能由 Codex 的 create_question_intake 建档"})
            if path == "/api/releases":
                self._confirmed(body, "构建发布包")
                return self._json(201, STORE.build_release(str(body["release_id"]), actor))
            parts = path.strip("/").split("/")
            if len(parts) != 4 or parts[:2] != ["api", "questions"]:
                return self._json(404, {"ok": False, "error": "not_found"})
            qid, action = parts[2], parts[3]
            if action == "ds-draft":
                version, revision = self._expected(body)
                result = STORE.write_ds_draft(qid, body.get("draft") or {}, actor, "frontend", reason, version, revision)
            elif action == "codex-review":
                version, revision = self._expected(body)
                result = STORE.write_codex_review(qid, body.get("review") or {}, actor, "frontend", reason, version, revision)
            elif action == "decision":
                self._confirmed(body, "记录人工决定")
                version, revision = self._expected(body)
                result = STORE.record_decision(qid, body.get("decision") or {}, actor, "frontend", reason, version, revision)
            elif action == "evidence-review":
                version, revision = self._expected(body)
                result = STORE.update_evidence_review(qid, body.get("updates") or [], actor, "frontend", reason, version, revision)
            elif action == "evidence-suggestion":
                version, revision = self._expected(body)
                result = STORE.curate_evidence(qid, body.get("updates") or [], actor, "frontend", reason,
                                               educator_suggestion=True, expected_question_version=version,
                                               expected_archive_revision=revision)
            elif action == "evidence-decision":
                self._confirmed(body, "确认或退回证据")
                version, revision = self._expected(body)
                result = STORE.review_evidence_candidate(qid, str(body.get("action") or ""), actor,
                                                         "frontend", reason, version, revision)
            elif action == "analysis-feedback":
                version, revision = self._expected(body)
                result = STORE.add_analysis_feedback(qid, str(body.get("section") or "overall"),
                                                     str(body.get("comment") or ""), actor, "frontend",
                                                     reason, version, revision)
            elif action == "polishing-complete":
                self._confirmed(body, "标记润色完成")
                version, revision = self._expected(body)
                result = STORE.mark_polishing_complete(qid, actor, "frontend", reason, version, revision)
            elif action == "workflow-decision":
                self._confirmed(body, "提交教研决定")
                version, revision = self._expected(body)
                result = STORE.record_workflow_decision(qid, str(body.get("decision") or ""), actor,
                                                        "frontend", reason, version, revision)
            elif action == "search": result = search_evidence(STORE.root, str(body.get("query") or ""), int(body.get("top_k") or 20), language=str(body.get("language") or "auto"), config=body.get("config") or {})
            elif action == "retrieve": result = retrieve_question_evidence(STORE.root, STORE.assert_ds_ready(qid)["content"], config=body.get("config") or {})
            elif action == "draft-input": result = prepare_draft_input(STORE, qid, config=body.get("config") or {})
            else: return self._json(404, {"ok": False, "error": "not_found"})
            self._json(200, result)
        except LockError as exc:
            self._json(409, {"ok": False, "error": str(exc)})
        except (WorkspaceError, AssetError, TextbookError, KeyError, ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"ok": False, "error": str(exc)})

    def do_PUT(self) -> None:
        path = urlparse(self.path).path
        try:
            body = self._body()
            actor, reason = self._actor(body)
            parts = path.strip("/").split("/")
            if len(parts) != 3 or parts[:2] != ["api", "questions"]:
                return self._json(404, {"ok": False, "error": "not_found"})
            self._confirmed(body, "修改题目")
            version, revision = self._expected(body)
            result = STORE.write_question(parts[2], body.get("content") or {}, actor, "frontend", reason, version, revision)
            self._json(200, {"question": result})
        except LockError as exc:
            self._json(409, {"ok": False, "error": str(exc)})
        except (WorkspaceError, AssetError, KeyError, ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"ok": False, "error": str(exc)})


def main() -> None:
    global ROOT, FRONTEND, STORE, TEXTBOOK
    parser = argparse.ArgumentParser(description="CAMS 正式版工作台 API")
    parser.add_argument("--host", default="127.0.0.1"); parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--workspace-root", type=Path, default=None)
    args = parser.parse_args()
    if args.workspace_root:
        ROOT = args.workspace_root.resolve()
        FRONTEND = ROOT / "frontend"
        STORE = WorkspaceStore(ROOT)
        TEXTBOOK = TextbookService(ROOT)
    try:
        create_backup(ROOT, reason="startup", daily=True)
    except OSError as exc:
        print(f"[api] backup warning: {exc}", file=sys.stderr)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"CAMS workbench: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__": main()
