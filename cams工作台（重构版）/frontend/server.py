#!/usr/bin/env python3
"""为 V7 工作台提供服务：渲染教材 PDF 页面 + 题目审核 API"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import fitz


ROOT = Path(__file__).resolve().parent
TEXTBOOK_ROOT = ROOT / "data" / "releases" / "v7"
DOCUMENTS: dict[Path, fitz.Document] = {}

# ─── 审核模块全局状态 ────────────────────────────────────────
REVIEW_POOL_DIR = ROOT / "review_pool"
REVIEW_DRAFTS_DIR = REVIEW_POOL_DIR / "drafts"
REVIEW_PUBLISHED_DIR = REVIEW_POOL_DIR / "published"
REVIEW_INDEX_PATH = REVIEW_POOL_DIR / "index.json"

# 审核源缓存
_review_source_questions: list[dict] = []       # 源题库（前 395 题）
_review_source_release_id: str = ""
_review_source_release_path: str = ""
_review_source_loaded: bool = False
_review_source_lock = threading.Lock()

# 教材单元白名单（用于 evidence unit_id 校验）
_textbook_unit_ids: set[str] = set()
_textbook_units_loaded: bool = False

# 原子写入进程锁
_index_write_lock = threading.Lock()
_MAX_REQUEST_BODY = 1_000_000  # 1MB


# ═══════════════════════════════════════════════════════════════
# 现有功能（保持原样）
# ═══════════════════════════════════════════════════════════════

def resolve_textbook_pdf(language: str) -> tuple[Path, int]:
    """解析语言对应的教材 PDF 路径及总页数"""
    if language not in {"zh", "en"}:
        raise ValueError("language must be zh or en")
    active = json.loads((TEXTBOOK_ROOT / "textbook-active.json").read_text(encoding="utf-8"))
    release_path = Path(active["release_path"])
    release_dir = (TEXTBOOK_ROOT / release_path).resolve()
    if TEXTBOOK_ROOT.resolve() not in release_dir.parents:
        raise ValueError("invalid textbook release path")
    manifest = json.loads((release_dir / "manifest.json").read_text(encoding="utf-8"))
    asset_name = manifest["assets"]["zh_pdf" if language == "zh" else "en_pdf"]
    pdf_path = (release_dir / asset_name).resolve()
    if release_dir not in pdf_path.parents or pdf_path.suffix.lower() != ".pdf":
        raise ValueError("invalid textbook PDF path")
    return pdf_path, int(manifest["counts"]["bilingual_pdf_pages"])


def _load_textbook_units() -> None:
    """加载教材单元白名单，用于 evidence unit_id 校验"""
    global _textbook_unit_ids, _textbook_units_loaded
    try:
        active = json.loads((TEXTBOOK_ROOT / "textbook-active.json").read_text(encoding="utf-8"))
        release_path = Path(active["release_path"])
        release_dir = (TEXTBOOK_ROOT / release_path).resolve()
        units_file = release_dir / "units.json"
        data = json.loads(units_file.read_text(encoding="utf-8"))
        _textbook_unit_ids = {item["unit_id"] for item in data.get("items", [])}
        _textbook_units_loaded = True
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"[review] 加载教材单元白名单失败: {exc}")
        _textbook_unit_ids = set()


def _compute_question_hash(question: dict) -> str:
    """对题目 stem + options 计算 SHA256"""
    raw = json.dumps(
        {"stem": question.get("stem", ""), "options": question.get("options", {})},
        ensure_ascii=False, sort_keys=True
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _compute_textbook_units_hash() -> str:
    """对当前教材单元 ID 列表排序后计算 SHA256"""
    ids = sorted(_textbook_unit_ids)
    raw = "\n".join(ids)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════
# 审核源加载
# ═══════════════════════════════════════════════════════════════

def load_review_source() -> None:
    """从 review-active.json 指向的审核源加载数据"""
    global _review_source_questions, _review_source_release_id
    global _review_source_release_path, _review_source_loaded

    with _review_source_lock:
        if _review_source_loaded:
            return  # 已加载，跳过

        try:
            active_path = TEXTBOOK_ROOT / "review-active.json"
            if not active_path.exists():
                print("[review] 未找到 review-active.json，跳过审核源加载")
                return

            active = json.loads(active_path.read_text(encoding="utf-8"))
            _review_source_release_id = active.get("release_id", "unknown")
            _review_source_release_path = active.get("release_path", "")

            # 从项目根目录解析 release_path
            source_path = (ROOT / _review_source_release_path).resolve()
            if not source_path.exists():
                print(f"[review] 审核源路径不存在: {source_path}")
                return

            all_questions = json.loads(source_path.read_text(encoding="utf-8"))
            questions_list = all_questions.get("questions", [])

            # 取前 395 题，转换为 v7_q 格式
            total = min(active.get("total_count", 395), len(questions_list))
            _review_source_questions = []
            for i in range(total):
                src = questions_list[i]
                qid = f"v7_q_{i + 1:06d}"  # v7_q_000001, v7_q_000002, ...
                _review_source_questions.append({
                    "question_id": qid,
                    "source_index": i,
                    "source_id": src.get("id", ""),
                    "stem_zh": src.get("stem", ""),
                    "stem_en": src.get("stem_en", ""),
                    "options": src.get("options", {}),
                    "answer_reference": _parse_answer(src.get("answer", "")),
                    "explanation": src.get("explanation", ""),
                    "type": _infer_question_type(src.get("answer", "")),
                })

            _review_source_loaded = True
            print(f"[review] 审核源加载完成: {total} 题 (release: {_review_source_release_id})")

        except (OSError, json.JSONDecodeError, KeyError) as exc:
            print(f"[review] 审核源加载失败: {exc}")


def _parse_answer(answer_str: str) -> list[str]:
    """将 'A,B,C' 格式转为 ['A','B','C']"""
    if not answer_str:
        return []
    return [ch.strip() for ch in answer_str.split(",") if ch.strip()]


def _infer_question_type(answer_str: str) -> str:
    """根据答案格式推断题型"""
    parts = [ch.strip() for ch in answer_str.split(",") if ch.strip()]
    if len(parts) > 1:
        return "multiple_choice"
    return "single_choice"


def get_question(question_id: str) -> dict | None:
    """按 question_id 查找源题目"""
    for q in _review_source_questions:
        if q["question_id"] == question_id:
            return q
    return None


def get_evidence(question_id: str) -> list[dict]:
    """获取题目的机器证据（暂为空列表，等待 refresh-machine 填充）"""
    return []


def get_manifest_question() -> list[dict]:
    """返回队列列表所需的最小字段"""
    return _review_source_questions


# ═══════════════════════════════════════════════════════════════
# index.json 读写（带原子写入）
# ═══════════════════════════════════════════════════════════════

def _ensure_review_dirs() -> None:
    """确保审核池目录存在"""
    REVIEW_POOL_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)


def _read_index() -> dict:
    """读取审核池 index.json，若不存在则初始化"""
    if not REVIEW_INDEX_PATH.exists():
        return _init_index()
    try:
        return json.loads(REVIEW_INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _init_index()


def _init_index() -> dict:
    """首次启动：从审核源初始化全部为 unconfirmed"""
    load_review_source()
    entries: list[dict] = []
    for q in _review_source_questions:
        qid = q["question_id"]
        source_hash = _compute_question_hash(q)
        entries.append({
            "question_id": qid,
            "status": "unconfirmed",
            "source_hash": source_hash,
            "has_draft": False,
            "has_published": False,
            "version_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
    index = {
        "schema_version": "cams-review-index/v1",
        "source_release_id": _review_source_release_id,
        "source_release_path": _review_source_release_path,
        "textbook_units_hash": _compute_textbook_units_hash(),
        "entries": entries,
    }
    _write_index_atomic(index)
    return index


def _write_index_atomic(index: dict) -> None:
    """原子写入 index.json：临时文件 → os.rename"""
    with _index_write_lock:
        tmp = REVIEW_INDEX_PATH.with_suffix(".tmp.json")
        tmp.write_text(
            json.dumps(index, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        # Windows 下先删除目标文件再 rename
        if REVIEW_INDEX_PATH.exists():
            REVIEW_INDEX_PATH.unlink()
        tmp.rename(REVIEW_INDEX_PATH)


def _find_entry(index: dict, question_id: str) -> dict | None:
    """在 index 中查找题目条目"""
    for entry in index["entries"]:
        if entry["question_id"] == question_id:
            return entry
    return None


def _update_entry(question_id: str, updater) -> dict | None:
    """原子更新 index 中某个条目，updater 接收原 entry 返回新 entry"""
    index = _read_index()
    entry = _find_entry(index, question_id)
    if entry is None:
        return None
    new_entry = updater(entry)
    new_entry["updated_at"] = datetime.now(timezone.utc).isoformat()
    # 替换
    for i, e in enumerate(index["entries"]):
        if e["question_id"] == question_id:
            index["entries"][i] = new_entry
            break
    _write_index_atomic(index)
    return new_entry


# ═══════════════════════════════════════════════════════════════
# 安全校验
# ═══════════════════════════════════════════════════════════════

# 合法的 question_id 格式前缀
_QUESTION_ID_PATTERN = re.compile(r"^v7_q_\d{6}$")


def _validate_question_id(question_id: str) -> bool:
    """校验 question_id 格式"""
    return bool(_QUESTION_ID_PATTERN.match(question_id))


def _validate_unit_id(unit_id: str) -> bool:
    """校验 unit_id 是否在教材白名单中"""
    if not _textbook_units_loaded:
        _load_textbook_units()
    return unit_id in _textbook_unit_ids


def _safe_path(part: str) -> bool:
    """防止路径穿越"""
    return ".." not in part and "/" not in part and "\\" not in part


# ═══════════════════════════════════════════════════════════════
# 草稿 / 正式版文件读写
# ═══════════════════════════════════════════════════════════════

def _draft_path(question_id: str) -> Path:
    return REVIEW_DRAFTS_DIR / f"{question_id}.json"


def _published_path(question_id: str, version_id: str) -> Path:
    return REVIEW_PUBLISHED_DIR / f"{question_id}__{version_id}.json"


def _read_draft(question_id: str) -> dict | None:
    p = _draft_path(question_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_draft(question_id: str, data: dict) -> bool:
    """原子写入草稿"""
    try:
        p = _draft_path(question_id)
        tmp = p.with_suffix(".tmp.json")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        if p.exists():
            p.unlink()
        tmp.rename(p)
        return True
    except OSError:
        return False


def _read_published(question_id: str, version_id: str) -> dict | None:
    p = _published_path(question_id, version_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_published(question_id: str, version_id: str, data: dict) -> bool:
    """原子写入正式版本"""
    try:
        p = _published_path(question_id, version_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp.json")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        if p.exists():
            p.unlink()
        tmp.rename(p)
        return True
    except OSError:
        return False


def _list_published_versions(question_id: str) -> list[str]:
    """列出某题所有正式版本 ID（按文件名后缀排序）"""
    pattern = f"{question_id}__v*.json"
    files = sorted(REVIEW_PUBLISHED_DIR.glob(pattern))
    versions = []
    for f in files:
        # 从文件名提取 version_id: v7_q_000001__v1.json → v1
        parts = f.stem.split("__")
        if len(parts) == 2:
            versions.append(parts[1])
    return versions


# ═══════════════════════════════════════════════════════════════
# HTTP Handler
# ═══════════════════════════════════════════════════════════════

class WorkbenchHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_error(self, code, message=None, explain=None):
        """重写 send_error 以支持中文错误信息（避免 latin-1 编码错误）"""
        try:
            body = json.dumps({"error": message or HTTPStatus(code).phrase}, ensure_ascii=True)
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
        except Exception:
            super().send_error(code, message="Internal Server Error")

    # ── do_GET ──────────────────────────────────────────────
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = parse_qs(parsed.query)

        # 现有功能：教材 PDF 渲染
        if path == "/api/textbook-page":
            self.render_textbook_page(query)
            return

        # ── 审核 API ──
        if path == "/api/reviews/source-info":
            self.handle_source_info()
            return

        if path == "/api/reviews/questions":
            self.handle_list_questions(query)
            return

        # GET /api/reviews/questions/{id}
        m = re.match(r"^/api/reviews/questions/([^/]+)$", path)
        if m:
            qid = m.group(1)
            self.handle_get_question(qid)
            return

        # GET /api/reviews/questions/{id}/versions
        m = re.match(r"^/api/reviews/questions/([^/]+)/versions$", path)
        if m:
            qid = m.group(1)
            self.handle_list_versions(qid)
            return

        # GET /api/reviews/export
        if path == "/api/reviews/export":
            self.handle_export(query)
            return

        # 回退到静态文件服务
        super().do_GET()

    # ── do_PUT ──────────────────────────────────────────────
    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # PUT /api/reviews/questions/{id}/draft
        m = re.match(r"^/api/reviews/questions/([^/]+)/draft$", path)
        if m:
            qid = m.group(1)
            body = self._read_body()
            if body is None:
                return
            self.handle_save_draft(qid, body)
            return

        self.send_error(HTTPStatus.METHOD_NOT_ALLOWED)

    # ── do_POST ─────────────────────────────────────────────
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # POST /api/reviews/questions/{id}/confirm
        m = re.match(r"^/api/reviews/questions/([^/]+)/confirm$", path)
        if m:
            qid = m.group(1)
            body = self._read_body()
            if body is None:
                return
            self.handle_confirm(qid, body)
            return

        # POST /api/reviews/refresh-machine
        if path == "/api/reviews/refresh-machine":
            self.handle_refresh_machine()
            return

        self.send_error(HTTPStatus.METHOD_NOT_ALLOWED)

    # ── 工具方法 ────────────────────────────────────────────

    def _read_body(self) -> dict | None:
        """读取并校验请求体，返回 dict 或 None（出错时已发送响应）"""
        length = int(self.headers.get("Content-Length", 0))
        if length > _MAX_REQUEST_BODY:
            self.send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "请求体超过 1MB 限制")
            return None
        try:
            raw = self.rfile.read(length) if length > 0 else b"{}"
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_error(HTTPStatus.BAD_REQUEST, "请求体不是合法的 JSON")
            return None

    def _send_json(self, data, status: int = HTTPStatus.OK) -> None:
        """发送 JSON 响应"""
        raw = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    # ── 现有功能：教材渲染 ──────────────────────────────────

    def render_textbook_page(self, query: dict[str, list[str]]) -> None:
        try:
            language = query.get("lang", ["zh"])[0]
            page_number = int(query.get("page", ["1"])[0])
            scale = float(query.get("scale", ["1.6"])[0])
            pdf_path, page_count = resolve_textbook_pdf(language)
            if not 1 <= page_number <= page_count:
                raise ValueError("page is outside the textbook range")
            scale = min(2.5, max(0.8, scale))
            document = DOCUMENTS.get(pdf_path)
            if document is None:
                document = fitz.open(pdf_path)
                DOCUMENTS[pdf_path] = document
            page = document.load_page(page_number - 1)
            png = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).tobytes("png")
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
            self.send_error(HTTPStatus.BAD_REQUEST, str(error))
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(png)))
        self.send_header("Cache-Control", "public, max-age=86400")
        self.end_headers()
        self.wfile.write(png)

    # ══════════════════════════════════════════════════════
    # 审核 API 实现
    # ══════════════════════════════════════════════════════

    # ── 1. GET /api/reviews/source-info ──────────────────────
    def handle_source_info(self):
        try:
            load_review_source()
            index = _read_index()
            entries = index.get("entries", [])
            unconfirmed = sum(1 for e in entries if e["status"] == "unconfirmed")
            draft_count = sum(1 for e in entries if e["status"] == "draft")
            confirmed = sum(1 for e in entries if e["status"] == "confirmed")

            info = {
                "source_release_id": _review_source_release_id,
                "source_release_path": _review_source_release_path,
                "textbook_units_hash": index.get("textbook_units_hash", ""),
                "total": len(entries),
                "summary": {
                    "unconfirmed": unconfirmed,
                    "draft": draft_count,
                    "confirmed": confirmed,
                },
            }
            self._send_json(info)
        except Exception as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    # ── 2. GET /api/reviews/questions ───────────────────────
    def handle_list_questions(self, query: dict[str, list[str]]):
        try:
            load_review_source()
            index = _read_index()
            status_filter = (query.get("status") or [None])[0]
            search = (query.get("search") or [None])[0]

            result = []
            for q in get_manifest_question():
                qid = q["question_id"]
                entry = _find_entry(index, qid)
                formal_status = entry["status"] if entry else "unconfirmed"
                has_draft = entry["has_draft"] if entry else False

                # 状态筛选
                if status_filter and formal_status != status_filter:
                    continue

                stem = q.get("stem_zh", q.get("stem_en", ""))
                # 搜索筛选
                if search:
                    lower_search = search.lower()
                    if lower_search not in qid.lower() and lower_search not in stem.lower():
                        continue

                result.append({
                    "question_id": qid,
                    "stem_zh": stem,
                    "stem_en": q.get("stem_en", ""),
                    "formal_status": formal_status,
                    "has_draft": has_draft,
                    "machine_ok": True,  # 暂时标记为 True
                })

            self._send_json(result)
        except Exception as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    # ── 3. GET /api/reviews/questions/{id} ──────────────────
    def handle_get_question(self, question_id: str):
        try:
            if not _validate_question_id(question_id):
                self.send_error(HTTPStatus.BAD_REQUEST, "无效的 question_id 格式")
                return

            load_review_source()
            question = get_question(question_id)
            if question is None:
                self.send_error(HTTPStatus.NOT_FOUND, f"题目 {question_id} 不存在")
                return

            index = _read_index()
            entry = _find_entry(index, question_id)

            # 读取草稿
            draft = _read_draft(question_id)
            # 读取最新正式版本
            versions = _list_published_versions(question_id)
            latest_version_id = versions[-1] if versions else None
            published = _read_published(question_id, latest_version_id) if latest_version_id else None

            # 机器证据（暂从 get_evidence 获取）
            machine_evidence = get_evidence(question_id)

            # 构建前端所需格式
            data = {
                "question_id": question_id,
                "question": {
                    "id": question_id,
                    "stem_zh": question.get("stem_zh", ""),
                    "stem_en": question.get("stem_en", ""),
                    "options": question.get("options", {}),
                    "answer_reference": question.get("answer_reference", []),
                    "type": question.get("type", "single_choice"),
                    "explanation": question.get("explanation", ""),
                    "risk_flags": [],
                },
                "machine_judgement": {
                    "predicted_answer": question.get("answer_reference", []),
                    "explanation": question.get("explanation", ""),
                    "evidence": machine_evidence,
                },
                "machine_ok": True,
                "formal_status": entry["status"] if entry else "unconfirmed",
                "draft": draft,
                "published": published,
                "versions": versions,
            }

            # 如果有草稿的正式字段，使用草稿值；否则使用正式版或机器值
            if draft:
                data["formal_answer"] = draft.get("answer", [])
                data["formal_explanation"] = draft.get("explanation_markdown", "")
                data["formal_evidence"] = draft.get("evidence", [])
            elif published:
                data["formal_answer"] = published.get("answer", [])
                data["formal_explanation"] = published.get("explanation_markdown", "")
                data["formal_evidence"] = published.get("evidence", [])
            else:
                data["formal_answer"] = question.get("answer_reference", [])
                data["formal_explanation"] = question.get("explanation", "")
                data["formal_evidence"] = []

            self._send_json(data)
        except Exception as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    # ── 4. PUT /api/reviews/questions/{id}/draft ────────────
    def handle_save_draft(self, question_id: str, body: dict):
        try:
            if not _validate_question_id(question_id):
                self.send_error(HTTPStatus.BAD_REQUEST, "无效的 question_id 格式")
                return

            load_review_source()
            question = get_question(question_id)
            if question is None:
                self.send_error(HTTPStatus.NOT_FOUND, f"题目 {question_id} 不存在")
                return

            # 校验 evidence 中的 unit_id
            evidence = body.get("evidence", [])
            for ev in evidence:
                uid = ev.get("unit_id", "")
                if not _validate_unit_id(uid):
                    self.send_error(HTTPStatus.BAD_REQUEST,
                                    f"无效的 unit_id: {uid}")
                    return

            # 构建草稿数据
            draft_data = {
                "question_id": question_id,
                "answer": body.get("answer", []),
                "explanation_markdown": body.get("explanation", ""),
                "evidence": evidence,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            if not _write_draft(question_id, draft_data):
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "草稿写入失败")
                return

            # 更新 index 状态
            _update_entry(question_id, lambda e: {
                **e, "status": "draft", "has_draft": True
            })

            self._send_json({"status": "ok", "message": "草稿已保存"})
        except Exception as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    # ── 5. POST /api/reviews/questions/{id}/confirm ─────────
    def handle_confirm(self, question_id: str, body: dict):
        try:
            if not _validate_question_id(question_id):
                self.send_error(HTTPStatus.BAD_REQUEST, "无效的 question_id 格式")
                return

            load_review_source()
            question = get_question(question_id)
            if question is None:
                self.send_error(HTTPStatus.NOT_FOUND, f"题目 {question_id} 不存在")
                return

            # 校验 evidence 中的 unit_id
            evidence = body.get("evidence", [])
            for ev in evidence:
                uid = ev.get("unit_id", "")
                if not _validate_unit_id(uid):
                    self.send_error(HTTPStatus.BAD_REQUEST,
                                    f"无效的 unit_id: {uid}")
                    return

            # 计算版本号
            index = _read_index()
            entry = _find_entry(index, question_id)
            current_version_count = entry["version_count"] if entry else 0
            next_version = current_version_count + 1
            version_id = f"v{next_version}"

            # 获取父版本 ID
            versions = _list_published_versions(question_id)
            parent_version_id = versions[-1] if versions else None

            # 计算哈希
            question_hash = _compute_question_hash(question)
            textbook_units_hash = _compute_textbook_units_hash()

            # 构建正式版本契约
            now = datetime.now(timezone.utc).isoformat()
            published_data = {
                "question_id": question_id,
                "version_id": version_id,
                "parent_version_id": parent_version_id,
                "answer": body.get("answer", []),
                "explanation_markdown": body.get("explanation", ""),
                "evidence": evidence,
                "confirmed_at": now,
                "source_release_id": _review_source_release_id,
                "question_hash": question_hash,
                "textbook_release_id": _review_source_release_id,
                "textbook_units_hash": textbook_units_hash,
            }

            if not _write_published(question_id, version_id, published_data):
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "正式版本写入失败")
                return

            # 更新 index
            _update_entry(question_id, lambda e: {
                **e,
                "status": "confirmed",
                "has_published": True,
                "version_count": next_version,
            })

            # 确认后删除草稿
            draft_p = _draft_path(question_id)
            if draft_p.exists():
                try:
                    draft_p.unlink()
                except OSError:
                    pass

            self._send_json({
                "status": "ok",
                "version_id": version_id,
                "message": f"正式版本 {version_id} 已确认",
            })
        except Exception as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    # ── 6. GET /api/reviews/questions/{id}/versions ─────────
    def handle_list_versions(self, question_id: str):
        try:
            if not _validate_question_id(question_id):
                self.send_error(HTTPStatus.BAD_REQUEST, "无效的 question_id 格式")
                return

            versions = _list_published_versions(question_id)
            result = []
            for vid in versions:
                pub = _read_published(question_id, vid)
                if pub:
                    result.append({
                        "version_id": vid,
                        "parent_version_id": pub.get("parent_version_id"),
                        "confirmed_at": pub.get("confirmed_at", ""),
                    })
            self._send_json(result)
        except Exception as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    # ── 7. POST /api/reviews/refresh-machine ────────────────
    def handle_refresh_machine(self):
        try:
            load_review_source()
            index = _read_index()

            updated = 0
            for entry in index["entries"]:
                qid = entry["question_id"]
                question = get_question(qid)
                if question is None:
                    continue
                new_hash = _compute_question_hash(question)
                if entry.get("source_hash") != new_hash:
                    entry["source_hash"] = new_hash
                    updated += 1

            if updated > 0:
                _write_index_atomic(index)

            self._send_json({
                "status": "ok",
                "updated": updated,
                "total": len(index["entries"]),
            })
        except Exception as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    # ── 8. GET /api/reviews/export ──────────────────────────
    def handle_export(self, query: dict[str, list[str]]):
        try:
            qid = (query.get("id") or [None])[0]
            fmt = (query.get("format") or ["json"])[0]
            if fmt not in {"json", "md"}:
                self.send_error(HTTPStatus.BAD_REQUEST, "format 必须是 json 或 md")
                return

            if qid:
                # 单题导出
                if not _validate_question_id(qid):
                    self.send_error(HTTPStatus.BAD_REQUEST, "无效的 question_id")
                    return
                load_review_source()
                question = get_question(qid)
                if question is None:
                    self.send_error(HTTPStatus.NOT_FOUND, f"题目 {qid} 不存在")
                    return
                index = _read_index()
                entry = _find_entry(index, qid)
                versions = _list_published_versions(qid)
                latest_vid = versions[-1] if versions else None
                published = _read_published(qid, latest_vid) if latest_vid else None

                data = {
                    "question_id": qid,
                    "stem": question.get("stem_zh", ""),
                    "options": question.get("options", {}),
                    "formal_answer": published["answer"] if published else [],
                    "formal_explanation": published["explanation_markdown"] if published else "",
                    "formal_evidence": published["evidence"] if published else [],
                    "status": entry["status"] if entry else "unconfirmed",
                }
                items = [data]
            else:
                # 全部导出
                load_review_source()
                index = _read_index()
                items = []
                for entry in index["entries"]:
                    qid = entry["question_id"]
                    question = get_question(qid)
                    versions = _list_published_versions(qid)
                    latest_vid = versions[-1] if versions else None
                    published = _read_published(qid, latest_vid) if latest_vid else None
                    items.append({
                        "question_id": qid,
                        "stem": (question or {}).get("stem_zh", ""),
                        "formal_answer": published["answer"] if published else [],
                        "formal_explanation": published["explanation_markdown"] if published else "",
                        "status": entry["status"],
                    })

            if fmt == "md":
                lines = []
                for item in items:
                    lines.append(f"## {item['question_id']}")
                    lines.append("")
                    lines.append(item.get("stem", ""))
                    lines.append("")
                    lines.append("**答案**: " + ", ".join(item.get("formal_answer", [])))
                    lines.append("")
                    lines.append("**解析**:")
                    lines.append(item.get("formal_explanation", ""))
                    lines.append("")
                    lines.append("---")
                    lines.append("")
                content = "\n".join(lines)
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/markdown; charset=utf-8")
                self.send_header("Content-Disposition",
                                 f'attachment; filename="review_export.md"')
                raw = content.encode("utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            else:
                self._send_json(items)
        except Exception as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))


# ═══════════════════════════════════════════════════════════════
# 启动逻辑
# ═══════════════════════════════════════════════════════════════

def _ensure_review_pool() -> None:
    """确保审核池存在，若不存在则从审核源初始化"""
    _ensure_review_dirs()
    load_review_source()
    _load_textbook_units()

    # 如果 index.json 不存在，触发初始化
    if not REVIEW_INDEX_PATH.exists():
        print("[review] 首次启动：初始化审核池...")
        _init_index()
        print(f"[review] 审核池初始化完成: {REVIEW_POOL_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5175)
    args = parser.parse_args()

    # 初始化审核池
    _ensure_review_pool()

    mimetypes.add_type("application/pdf", ".pdf")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), WorkbenchHandler)
    print(f"CAMS V7 workbench: http://127.0.0.1:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
