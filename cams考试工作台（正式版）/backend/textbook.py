"""Read-only access to the frozen bilingual textbook release."""
from __future__ import annotations

import json
import re
from pathlib import Path
from threading import RLock
from typing import Any


class TextbookError(RuntimeError):
    pass


class TextbookService:
    def __init__(self, root: Path | str):
        self.root = Path(root).resolve() / "data" / "infrastructure" / "textbook"
        self._lock = RLock()

    def _manifest(self) -> dict[str, Any]:
        path = self.root / "manifest.json"
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise TextbookError("冻结教材 manifest 不存在") from exc
        except json.JSONDecodeError as exc:
            raise TextbookError("冻结教材 manifest 损坏") from exc
        release = manifest.get("viewer_release")
        if not isinstance(release, dict) or release.get("schema_version") != "cams-v7-textbook-release/v1":
            raise TextbookError("当前教材没有可用的双语阅读发布包")
        return manifest

    def info(self) -> dict[str, Any]:
        manifest = self._manifest()
        release = manifest["viewer_release"]
        return {
            "version": manifest.get("version"),
            "unit_count": manifest.get("unit_count"),
            "release_id": release.get("release_id"),
            "page_count": int(release.get("page_count") or 0),
            "assets": release.get("assets") or {},
            "sha256": release.get("sha256") or {},
        }

    def chapters(self) -> dict[str, Any]:
        name = self._manifest()["viewer_release"]["assets"].get("chapters", "chapters.json")
        return self._read_asset_json(name)

    def page_map(self) -> dict[str, Any]:
        name = self._manifest()["viewer_release"]["assets"].get("page_map", "page-map.json")
        return self._read_asset_json(name)

    def _read_asset_json(self, name: str) -> dict[str, Any]:
        path = self._safe_asset(name)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise TextbookError(f"教材资产不存在：{name}") from exc
        except json.JSONDecodeError as exc:
            raise TextbookError(f"教材资产损坏：{name}") from exc
        if not isinstance(value, dict):
            raise TextbookError(f"教材资产格式错误：{name}")
        return value

    def _safe_asset(self, name: str) -> Path:
        candidate = (self.root / str(name)).resolve()
        if self.root not in candidate.parents or not candidate.is_file():
            raise TextbookError("教材资产路径无效")
        return candidate

    def _pdf_path(self, language: str) -> Path:
        if language not in {"zh", "en"}:
            raise TextbookError("language 只能是 zh 或 en")
        assets = self._manifest()["viewer_release"]["assets"]
        return self._safe_asset(assets["zh_pdf"] if language == "zh" else assets["en_pdf"])

    def _page(self, language: str, page_number: int):
        try:
            import fitz
        except ImportError as exc:
            raise TextbookError("缺少 PyMuPDF，请先安装正式版运行依赖") from exc
        page_count = int(self._manifest()["viewer_release"].get("page_count") or 0)
        if page_number < 1 or page_number > page_count:
            raise TextbookError(f"页码超出范围：1-{page_count}")
        document = fitz.open(self._pdf_path(language))
        try:
            yield document, document.load_page(page_number - 1)
        finally:
            document.close()

    def render_page(self, language: str, page_number: int, scale: float = 1.6) -> tuple[bytes, dict[str, Any]]:
        scale = min(2.5, max(0.8, float(scale)))
        with self._lock:
            try:
                import fitz
            except ImportError as exc:
                raise TextbookError("缺少 PyMuPDF，请先安装正式版运行依赖") from exc
            page_count = int(self._manifest()["viewer_release"].get("page_count") or 0)
            if page_number < 1 or page_number > page_count:
                raise TextbookError(f"页码超出范围：1-{page_count}")
            document = fitz.open(self._pdf_path(language))
            try:
                page = document.load_page(page_number - 1)
                pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
                return pixmap.tobytes("png"), {
                    "language": language,
                    "page": page_number,
                    "page_count": page_count,
                    "width": float(page.rect.width),
                    "height": float(page.rect.height),
                }
            finally:
                document.close()

    @staticmethod
    def _queries(query: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", str(query or "")).strip()[:500]
        if not normalized:
            return []
        parts = [part.strip() for part in re.split(r"[。；;.!?！？\n]", normalized)]
        return list(dict.fromkeys([normalized] + [part for part in parts if len(part) >= 8]))

    def match(self, language: str, page_number: int, query: str) -> dict[str, Any]:
        queries = self._queries(query)
        if not queries:
            raise TextbookError("匹配原文不能为空")
        with self._lock:
            try:
                import fitz
            except ImportError as exc:
                raise TextbookError("缺少 PyMuPDF，请先安装正式版运行依赖") from exc
            page_count = int(self._manifest()["viewer_release"].get("page_count") or 0)
            if page_number < 1 or page_number > page_count:
                raise TextbookError(f"页码超出范围：1-{page_count}")
            document = fitz.open(self._pdf_path(language))
            try:
                page = document.load_page(page_number - 1)
                for index, candidate in enumerate(queries):
                    rectangles = page.search_for(candidate)
                    if rectangles:
                        width, height = float(page.rect.width), float(page.rect.height)
                        return {
                            "matched": True,
                            "match_mode": "exact" if index == 0 else "partial",
                            "query": candidate,
                            "boxes": [
                                {"x": rect.x0 / width, "y": rect.y0 / height,
                                 "width": rect.width / width, "height": rect.height / height}
                                for rect in rectangles
                            ],
                            "page": page_number,
                            "language": language,
                        }
                return {"matched": False, "match_mode": "none", "query": queries[0], "boxes": [], "page": page_number, "language": language}
            finally:
                document.close()
