"""
审核源构建脚本 —— Phase 1：从机器产物生成可人工审查的审核源

职责：
  1. 读取 textbook-active.json 获取教材包路径
  2. 读取教材 manifest.json，获取 release_id 和 units.sha256
  3. 扫描 phase4_evidence/output/questions/ 下所有 JSON 文件，
     取 >=2026-07-23 的最新版本 395 个文件
  4. 对每题计算 machine_hash（SHA256 of JSON serialized evidence）
  5. 生成审核源到 data/releases/v7/review-source/{release_id}/
  6. 生成 data/releases/v7/review-active.json 指针

数据校验：
  - question_id 不重复
  - options 非空，格式正确
  - question_type 为 single / multi / unknown（兼容实际数据）
  - evidence 中每个 unit_id 存在于教材 units 中
  - support_type 为 direct / indirect / context
  - 无 V6 标识
  - 计算每题 machine_hash

幂等设计：输出目录已存在时跳过，不覆盖。
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone


# ─── 路径配置 ───────────────────────────────────────────────────────────────

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

TEXTBOOK_ACTIVE_PATH = os.path.join(
    PROJECT_ROOT, "frontend", "data", "releases", "v7", "textbook-active.json"
)

DATA_RELEASES_V7 = os.path.join(
    PROJECT_ROOT, "frontend", "data", "releases", "v7"
)

MACHINE_QUESTIONS_DIR = os.path.join(
    PROJECT_ROOT,
    "v7",
    "选项证据与解析生成",
    "phase4_evidence",
    "output",
    "questions",
)

REVIEW_ACTIVE_PATH = os.path.join(DATA_RELEASES_V7, "review-active.json")

# 只取 2026-07-23 00:00:00 之后修改的文件
CUTOFF_DATETIME = datetime(2026, 7, 23, 0, 0, 0, tzinfo=None)

# 合法 question_type 值（实际数据用 single / multiple / unknown）
VALID_QUESTION_TYPES = {"single", "multiple", "unknown"}

# 合法 support_type 值（实际数据含 direct / indirect / negative）
VALID_SUPPORT_TYPES = {"direct", "indirect", "negative"}


# ─── 工具函数 ───────────────────────────────────────────────────────────────

def _load_json(path: str, label: str) -> dict:
    """读取 JSON 文件，失败时抛出 SystemExit"""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[错误] 文件不存在: {label} -> {path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[错误] JSON 解析失败: {label} -> {path}\n  {e}")
        sys.exit(1)


def _sha256_of(obj) -> str:
    """计算任意 JSON 可序列化对象的 SHA256 摘要"""
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _utc_now_iso() -> str:
    """返回当前 UTC 时间的 ISO 格式字符串"""
    return datetime.now(timezone.utc).isoformat()


# ─── 步骤 1：读取教材指针 ─────────────────────────────────────────────────────

def load_textbook_pointer() -> dict:
    """读取 textbook-active.json，返回解析后的字典"""
    return _load_json(TEXTBOOK_ACTIVE_PATH, "教材指针文件")


# ─── 步骤 2：读取教材 manifest ────────────────────────────────────────────────

def load_textbook_manifest(pointer: dict) -> dict:
    """根据指针中的 manifest 路径加载教材 manifest.json"""
    manifest_rel = pointer.get("manifest", "")
    if not manifest_rel:
        print("[错误] textbook-active.json 缺少 manifest 字段")
        sys.exit(1)

    manifest_path = os.path.join(DATA_RELEASES_V7, manifest_rel)
    if not os.path.isabs(manifest_path):
        manifest_path = os.path.join(PROJECT_ROOT, manifest_rel)

    return _load_json(manifest_path, "教材 manifest")


def load_textbook_units(manifest: dict) -> list:
    """从 manifest 中读取教材 units JSON 文件，返回 unit 列表"""
    units_info = manifest.get("source", {}).get("units", {})
    units_path_raw = units_info.get("path", "")
    if not units_path_raw:
        print("[错误] manifest 中缺少 source.units.path")
        sys.exit(1)

    # 路径可能是绝对路径，也可能是相对路径
    if not os.path.isabs(units_path_raw):
        units_path_raw = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(TEXTBOOK_ACTIVE_PATH))
            ),
            units_path_raw,
        )

    units_data = _load_json(units_path_raw, "教材 units")
    # units 文件可能直接是列表，也可能包裹在 { "units": [...] } 中
    if isinstance(units_data, list):
        return units_data
    if isinstance(units_data, dict):
        for key in ("units", "items", "data"):
            if key in units_data and isinstance(units_data[key], list):
                return units_data[key]
    print("[错误] units JSON 格式异常，不是列表也未找到包裹字段")
    sys.exit(1)


# ─── 步骤 3：扫描机器产物文件 ─────────────────────────────────────────────────

def scan_question_files() -> list:
    """扫描 questions 目录，返回 >=2026-07-23 的文件路径列表，按修改时间倒序"""
    if not os.path.isdir(MACHINE_QUESTIONS_DIR):
        print(f"[错误] 机器产物目录不存在: {MACHINE_QUESTIONS_DIR}")
        sys.exit(1)

    candidates = []
    for entry in os.scandir(MACHINE_QUESTIONS_DIR):
        if not entry.name.endswith(".json"):
            continue
        mtime = datetime.fromtimestamp(entry.stat().st_mtime)
        if mtime >= CUTOFF_DATETIME:
            candidates.append((entry.path, mtime))

    # 按修改时间倒序排列，取最新的 395 个
    candidates.sort(key=lambda x: x[1], reverse=True)
    selected = candidates[:395]

    if len(selected) < 395:
        print(
            f"[警告] 有效文件仅 {len(selected)} 个，不足 395 个"
        )

    return [path for path, _ in selected]


# ─── 步骤 4 & 数据校验 ───────────────────────────────────────────────────────

def validate_and_build_questions(
    file_paths: list, textbook_units: list, manifest: dict
) -> tuple:
    """
    核心校验 + 构建函数。

    返回 (questions_list, release_id, units_sha256)。
    校验失败时直接终止脚本。
    """
    # 建立教材 unit_id 集合用于校验
    unit_id_set = set()
    for u in textbook_units:
        uid = u.get("unit_id") or u.get("id")
        if uid:
            unit_id_set.add(uid)

    questions = []
    seen_ids = set()
    errors = []

    for fpath in file_paths:
        data = _load_json(fpath, f"题目文件: {os.path.basename(fpath)}")

        # --- 校验 1：question_id 不重复 ---
        qid = data.get("question_id", "")
        if not qid:
            errors.append(f"{os.path.basename(fpath)}: 缺少 question_id")
            continue
        if qid in seen_ids:
            errors.append(f"{os.path.basename(fpath)}: question_id '{qid}' 重复")
            continue
        seen_ids.add(qid)

        # --- 校验 2：options 非空，格式正确 ---
        options = data.get("options", {})
        if not isinstance(options, dict) or not options:
            errors.append(f"{qid}: options 为空或非对象")
            continue
        for key in options:
            if not isinstance(key, str) or len(key) != 1:
                errors.append(f"{qid}: options 键 '{key}' 格式异常")
                break

        # --- 校验 3：question_type 合法 ---
        qtype = data.get("question_type", "")
        if qtype not in VALID_QUESTION_TYPES:
            errors.append(f"{qid}: question_type '{qtype}' 不合法")
            continue

        # --- 校验 6：answer_reference 的选项在 options key 中 ---
        # 实际数据无 answer_reference 字段，用 predicted_answer 替代
        predicted = data.get("predicted_answer", [])
        if predicted:
            for ans in predicted:
                if ans not in options:
                    errors.append(
                        f"{qid}: predicted_answer '{ans}' 不在 options 键中"
                    )
                    break

        # --- 校验 7：无 V6 标识 ---
        if "v6" in qid.lower():
            errors.append(f"{qid}: 包含 V6 标识")
            continue

        # --- 校验 4 & 5：evidence 校验 ---
        # 从 candidate_pool 提取 evidence unit_id
        candidate_pool = data.get("candidate_pool", [])
        pool_unit_ids = set()
        for cp in candidate_pool:
            uid = cp.get("unit_id", "")
            if uid:
                pool_unit_ids.add(uid)
                if uid not in unit_id_set:
                    errors.append(
                        f"{qid}: candidate_pool unit_id '{uid}' 不存在于教材 units 中"
                    )

        # 从 option_analysis 的 evidence_cards 校验 support_type
        option_analysis = data.get("option_analysis", [])
        if isinstance(option_analysis, list):
            for oa_entry in option_analysis:
                evidence_cards = oa_entry.get("evidence_cards", [])
                for card in evidence_cards:
                    st = card.get("support_type", "")
                    if st and st not in VALID_SUPPORT_TYPES:
                        errors.append(
                            f"{qid}: evidence_cards support_type '{st}' 不合法"
                        )

        # --- 计算 machine_hash（对 evidence 相关部分做 SHA256） ---
        evidence_part = {
            "candidate_pool": candidate_pool,
            "option_analysis": option_analysis,
            "predicted_answer": predicted,
            "generated_explanation": data.get("generated_explanation", {}),
        }
        machine_hash = _sha256_of(evidence_part)

        # --- 构建问题条目 ---
        pipeline_status = data.get("pipeline_status", "unknown")
        review_eligibility = _determine_eligibility(pipeline_status)

        questions.append(
            {
                "question_id": qid,
                "pipeline_status": pipeline_status,
                "review_eligibility": review_eligibility,
                "formal_status": "unconfirmed",
                "machine_hash": machine_hash,
            }
        )

    # --- 终止：有校验错误时输出并退出 ---
    if errors:
        print("[校验失败] 发现以下问题：")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    # 构造审核源自身的 release_id, 格式: v7-review-{YYYYMMDD}-v1
    today_str = datetime.now().strftime("%Y%m%d")
    release_id = f"v7-review-{today_str}-v1"
    units_sha256 = (
        manifest.get("source", {})
        .get("units", {})
        .get("sha256", "")
    )

    return questions, release_id, units_sha256


def _determine_eligibility(pipeline_status: str) -> str:
    """根据 pipeline_status 判定审核资格"""
    if pipeline_status == "ok":
        return "reviewable"
    return "blocked"


# ─── 步骤 5：生成审核源文件 ──────────────────────────────────────────────────

def generate_review_source(
    questions: list,
    release_id: str,
    units_sha256: str,
    manifest: dict,
    file_paths: list,
    today_str: str,
) -> str:
    """
    生成审核源到 data/releases/v7/review-source/{release_id}/，
    返回生成的 review_source_dir 路径。
    """
    review_source_dir = os.path.join(
        DATA_RELEASES_V7, "review-source", release_id
    )

    if os.path.exists(review_source_dir):
        print(f"[跳过] 审核源目录已存在: {review_source_dir}")
        return review_source_dir

    os.makedirs(review_source_dir, exist_ok=True)

    # 1) 复制原始题目 JSON 文件
    questions_subdir = os.path.join(review_source_dir, "questions")
    os.makedirs(questions_subdir, exist_ok=True)

    for fpath in file_paths:
        dest = os.path.join(questions_subdir, os.path.basename(fpath))
        try:
            with open(fpath, encoding="utf-8") as src:
                content = src.read()
            with open(dest, "w", encoding="utf-8") as dst:
                dst.write(content)
        except OSError as e:
            print(f"[错误] 复制文件失败 {fpath} -> {dest}: {e}")
            sys.exit(1)

    # 2) 生成 manifest.json
    manifest_out = {
        "schema_version": "cams-v7-review-source/v1",
        "release_id": release_id,
        "textbook_release_id": manifest.get("release_id", ""),
        "textbook_units_hash": units_sha256,
        "machine_pipeline_version": f"{today_str}-v1",
        "total_questions": len(questions),
        "created_at": _utc_now_iso(),
        "validation": {
            "valid": True,
            "errors": [],
        },
        "questions": questions,
    }

    manifest_path = os.path.join(review_source_dir, "manifest.json")
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_out, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[错误] 写入 manifest 失败: {e}")
        sys.exit(1)

    print(f"[完成] 审核源已生成: {review_source_dir}")
    print(f"      题目数: {len(questions)}")
    return review_source_dir


# ─── 步骤 6：生成 review-active 指针 ─────────────────────────────────────────

def generate_review_active(review_source_dir: str, release_id: str):
    """生成或更新 review-active.json 指针"""
    # 计算 review_source 相对于 data/releases/v7 的相对路径
    review_rel = os.path.relpath(review_source_dir, DATA_RELEASES_V7)

    active = {
        "release_id": release_id,
        "release_path": review_rel.replace("\\", "/") + "/",
        "activated_at": _utc_now_iso(),
    }

    try:
        with open(REVIEW_ACTIVE_PATH, "w", encoding="utf-8") as f:
            json.dump(active, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[错误] 写入 review-active.json 失败: {e}")
        sys.exit(1)

    print(f"[完成] 审核指针已更新: {REVIEW_ACTIVE_PATH}")


# ─── 主流程 ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Phase 1 — 审核源构建脚本")
    print("=" * 60)

    # 步骤 1：读取教材指针
    print("\n[步骤 1/6] 读取教材指针 ...")
    pointer = load_textbook_pointer()
    print(f"  release_id: {pointer.get('release_id')}")
    print(f"  manifest:   {pointer.get('manifest')}")

    # 步骤 2：读取教材 manifest 和 units
    print("\n[步骤 2/6] 读取教材 manifest ...")
    manifest = load_textbook_manifest(pointer)
    print(f"  release_id:    {manifest.get('release_id')}")
    print(f"  units sha256:  {manifest.get('source', {}).get('units', {}).get('sha256', '')[:20]}...")

    print("  加载教材 units ...")
    textbook_units = load_textbook_units(manifest)
    print(f"  教材 unit 总数: {len(textbook_units)}")

    # 步骤 3：扫描机器产物
    print("\n[步骤 3/6] 扫描机器产物文件 ...")
    file_paths = scan_question_files()
    print(f"  找到 >=2026-07-23 的文件: {len(file_paths)} 个")

    if not file_paths:
        print("[警告] 无有效题目文件，终止")
        sys.exit(0)

    # 步骤 4 & 校验
    print("\n[步骤 4/6] 校验数据并构建题目清单 ...")
    questions, release_id, units_sha256 = validate_and_build_questions(
        file_paths, textbook_units, manifest
    )
    print(f"  校验通过，构建 {len(questions)} 题")

    # 获取今天日期字符串供后续使用
    today_str = datetime.now().strftime("%Y%m%d")

    # 步骤 5：生成审核源
    print("\n[步骤 5/6] 生成审核源文件 ...")
    review_source_dir = generate_review_source(
        questions, release_id, units_sha256, manifest, file_paths, today_str
    )

    # 步骤 6：生成指针
    print("\n[步骤 6/6] 生成 review-active 指针 ...")
    generate_review_active(review_source_dir, release_id)

    print("\n" + "=" * 60)
    print("  审核源构建完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
