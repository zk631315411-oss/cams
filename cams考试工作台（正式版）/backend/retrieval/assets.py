"""正式版检索资产的路径解析、校验与懒加载。"""
from __future__ import annotations

import hashlib
import json
import os
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class AssetError(RuntimeError):
    """冻结检索资产缺失、损坏或彼此不一致。"""


@dataclass(frozen=True)
class WorkspacePaths:
    """所有运行时路径都由工作台根目录推导，业务代码不得拼接机器路径。"""

    root: Path

    @classmethod
    def resolve(cls, root: str | Path | None = None) -> "WorkspacePaths":
        value = root or os.environ.get("CAMS_WORKSPACE_ROOT")
        base = Path(value) if value else Path(__file__).resolve().parents[2]
        return cls(base.expanduser().resolve())

    @property
    def infrastructure(self) -> Path:
        return self.root / "data" / "infrastructure"

    @property
    def textbook_dir(self) -> Path:
        return self.infrastructure / "textbook"

    @property
    def index_dir(self) -> Path:
        return self.infrastructure / "index"

    @property
    def kg_dir(self) -> Path:
        return self.infrastructure / "kg"

    @property
    def terms_dir(self) -> Path:
        return self.infrastructure / "terms"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AssetError(f"冻结资产不存在: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetError(f"冻结资产无法读取: {path}") from exc
    if not isinstance(value, dict):
        raise AssetError(f"冻结资产必须为 JSON 对象: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_retrieval_defaults(root: str | Path | None = None) -> dict[str, Any]:
    """读取可选的 settings.toml；缺省时由 RetrievalConfig 的 V7 默认值接管。"""
    path = WorkspacePaths.resolve(root).root / "settings.toml"
    if not path.exists():
        return {}
    try:
        import tomllib
        with path.open("rb") as stream:
            values = tomllib.load(stream)
    except (OSError, ValueError) as exc:
        raise AssetError(f"无法读取检索配置: {path}") from exc
    retrieval = values.get("retrieval", {})
    if not isinstance(retrieval, dict):
        raise AssetError("settings.toml 的 [retrieval] 必须是对象")
    return dict(retrieval)


def _verify_manifest_asset(directory: Path, manifest: dict[str, Any]) -> Path:
    asset_name = str(manifest.get("asset_file") or "")
    expected_hash = str(manifest.get("sha256") or "").lower()
    if not asset_name or not expected_hash:
        raise AssetError(f"冻结资产清单缺少 asset_file 或 sha256: {directory / 'manifest.json'}")
    path = directory / asset_name
    if not path.exists():
        raise AssetError(f"冻结资产不存在: {path}")
    actual_hash = sha256_file(path)
    if actual_hash.lower() != expected_hash:
        raise AssetError(f"冻结资产哈希不匹配: {path.name}")
    return path


@dataclass
class RetrievalAssets:
    paths: WorkspacePaths
    textbook_manifest: dict[str, Any]
    index_manifest: dict[str, Any]
    kg_manifest: dict[str, Any]
    terms_manifest: dict[str, Any] | None
    index: dict[str, Any]
    kg: dict[str, Any] | None
    p5: dict[str, Any] | None

    @property
    def textbook_version(self) -> str:
        return str(self.textbook_manifest.get("version") or "unknown")

    def version_snapshot(self) -> dict[str, Any]:
        result = {
            "textbook": self.textbook_manifest.get("version"),
            "index": self.index_manifest.get("version"),
            "kg": self.kg_manifest.get("version") if self.kg else None,
            "terms": self.terms_manifest.get("version") if self.p5 and self.terms_manifest else None,
        }
        return result


_ASSET_CACHE: dict[tuple[str, bool, bool], RetrievalAssets] = {}
_BGE_MODEL: Any = None


def _load_pickle(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AssetError(f"冻结索引不存在: {path}")
    try:
        with path.open("rb") as stream:
            value = pickle.load(stream)
    except ModuleNotFoundError as exc:
        raise AssetError("读取冻结向量索引需要 numpy；请按 backend/requirements.txt 创建正式版运行环境") from exc
    except (OSError, pickle.PickleError, EOFError) as exc:
        raise AssetError(f"冻结索引无法读取: {path}") from exc
    if not isinstance(value, dict):
        raise AssetError("冻结索引格式错误：根节点必须为对象")
    return value


def _validate_index(index: dict[str, Any]) -> None:
    required = {
        "card_ids", "bge_vecs", "unit_lookup", "zh_bm25_docs", "zh_bm25_df",
        "zh_bm25_avgdl", "en_bm25_docs", "en_bm25_df", "en_bm25_avgdl",
    }
    missing = sorted(required - set(index))
    if missing:
        raise AssetError("冻结索引缺少字段: " + ", ".join(missing))
    card_ids, lookup = index["card_ids"], index["unit_lookup"]
    if not isinstance(card_ids, list) or not isinstance(lookup, dict):
        raise AssetError("冻结索引 card_ids 或 unit_lookup 类型错误")
    unresolved = [str(unit_id) for unit_id in card_ids if str(unit_id) not in lookup]
    if unresolved:
        raise AssetError(f"冻结索引存在 {len(unresolved)} 个无法定位的教材单元")


def _validate_kg(kg: dict[str, Any], unit_lookup: dict[str, Any]) -> None:
    unknown = {
        str(unit.get("unit_id")) for unit in kg.get("units", [])
        if unit.get("unit_id") and str(unit.get("unit_id")) not in unit_lookup
    }
    if unknown:
        raise AssetError(f"KG 存在不属于冻结索引的单元，例如: {sorted(unknown)[0]}")


def _load_p5(path: Path) -> dict[str, Any]:
    """保持重构版 P5 loader 的筛选规则，不直接把原始 JSON 当作运行索引。"""
    data = _read_json(path)
    aliases: list[dict[str, Any]] = []
    for group in data.get("alias_groups", []) or []:
        terms = [group.get("canonical_en", ""), group.get("canonical_zh", "")]
        for key in ("aliases_en", "aliases_zh", "all_terms"):
            terms.extend(group.get(key, []) or [])
        normalised = sorted({" ".join(str(term or "").strip().lower().split()) for term in terms if len(" ".join(str(term or "").strip().lower().split())) >= 2}, key=len, reverse=True)
        unit_ids = [str(unit_id) for unit_id in group.get("evidence_unit_ids", []) or [] if unit_id]
        if normalised and unit_ids:
            aliases.append({"alias_group_id": group.get("alias_group_id", ""),
                            "canonical_en": group.get("canonical_en", ""),
                            "canonical_zh": group.get("canonical_zh", ""), "terms": normalised,
                            "unit_ids": unit_ids, "alias_scope": group.get("alias_scope", "")})
    return {"aliases": aliases, "raw": data}


def load_assets(root: str | Path | None = None, *, enable_kg: bool = True,
                enable_p5: bool = False) -> RetrievalAssets:
    paths = WorkspacePaths.resolve(root)
    key = (str(paths.root), enable_kg, enable_p5)
    if key in _ASSET_CACHE:
        return _ASSET_CACHE[key]

    textbook_manifest = _read_json(paths.textbook_dir / "manifest.json")
    index_manifest = _read_json(paths.index_dir / "manifest.json")
    kg_manifest = _read_json(paths.kg_dir / "manifest.json")
    index_meta = _read_json(paths.index_dir / "v7_embedding_index_meta.json")
    index_path = _verify_manifest_asset(paths.index_dir, index_manifest)
    if index_meta.get("index_file") != index_path.name:
        raise AssetError("索引清单与索引元数据指向的文件不一致")
    _verify_manifest_asset(paths.textbook_dir, textbook_manifest)
    index = _load_pickle(index_path)
    _validate_index(index)

    kg = None
    if enable_kg:
        kg = _read_json(_verify_manifest_asset(paths.kg_dir, kg_manifest))
        _validate_kg(kg, index["unit_lookup"])

    p5, terms_manifest = None, None
    if enable_p5:
        terms_manifest = _read_json(paths.terms_dir / "manifest.json")
        p5 = _load_p5(_verify_manifest_asset(paths.terms_dir, terms_manifest))

    assets = RetrievalAssets(paths, textbook_manifest, index_manifest, kg_manifest,
                             terms_manifest, index, kg, p5)
    _ASSET_CACHE[key] = assets
    return assets


def get_bge_model(root: str | Path | None = None) -> Any:
    """按需加载本地 BGE-M3；缺依赖或模型时给出可执行的错误。"""
    global _BGE_MODEL
    if _BGE_MODEL is not None:
        return _BGE_MODEL
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise AssetError("缺少 sentence-transformers；请按 backend/requirements.txt 创建正式版运行环境") from exc
    bundled_model = WorkspacePaths.resolve(root).root / "runtime" / "models" / "bge-m3"
    model_name = os.environ.get("CAMS_BGE_MODEL_PATH") or (str(bundled_model) if bundled_model.exists() else "BAAI/bge-m3")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    try:
        _BGE_MODEL = SentenceTransformer(model_name, local_files_only=True)
    except Exception as exc:  # sentence-transformers 的异常类型随版本变化。
        raise AssetError(f"无法离线加载 BGE 模型 {model_name!r}；设置 CAMS_BGE_MODEL_PATH 指向本机模型目录") from exc
    return _BGE_MODEL
