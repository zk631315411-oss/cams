# -*- coding: utf-8 -*-
"""将盲判输出暂存并挂载人工确认的章节映射，供解析生成使用。

暂存副本接收已审核的章节映射，不修改检索/裁判管线拥有的盲判原始输出。
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


def load_mappings(path: Path) -> dict[str, dict[str, Any]]:
    """加载人工确认的章节映射 JSONL 文件。"""
    rows: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        row = json.loads(line)
        question_id = str(row.get("question_id", "")).strip()
        if not question_id:
            raise RuntimeError(f"章节映射第 {line_number} 行缺少 question_id")
        if question_id in rows:
            raise RuntimeError(f"章节映射题号重复: {question_id}")
        rows[question_id] = row
    return rows


def attach_mapping(result: dict[str, Any], mapping: dict[str, Any]) -> None:
    """将章节映射字段写入盲判结果字典。"""
    result["chapter_mappings"] = mapping.get("chapter_mappings", []) or []
    result["chapter_mapping_status"] = mapping.get("mapping_status", "")
    result["chapter_mapping_needs_source_repair"] = bool(
        mapping.get("needs_source_repair", False)
    )


def stage_run(source_dir: Path, target_dir: Path, mapping_path: Path) -> int:
    """复制盲判运行目录到目标位置并注入章节映射。

    返回成功暂存的题目数量。
    """
    if source_dir.resolve() == target_dir.resolve():
        raise RuntimeError("源目录和目标目录不能相同")
    if not (source_dir / "questions").is_dir():
        raise RuntimeError(f"盲判源目录缺少 questions: {source_dir}")
    if target_dir.exists():
        raise RuntimeError(f"目标目录已存在，拒绝覆盖: {target_dir}")

    mappings = load_mappings(mapping_path)
    shutil.copytree(source_dir, target_dir)

    question_paths = sorted((target_dir / "questions").glob("q_*.json"))
    if not question_paths:
        raise RuntimeError("目标目录没有 q_*.json")

    staged_ids: set[str] = set()
    for path in question_paths:
        result = json.loads(path.read_text(encoding="utf-8"))
        question_id = str(result.get("question_id", "")).strip()
        mapping = mappings.get(question_id)
        if not mapping:
            raise RuntimeError(f"缺少人工确认章节映射: {question_id}")
        attach_mapping(result, mapping)
        path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        staged_ids.add(question_id)

    # 同步更新盲判汇总 JSONL
    summary_path = target_dir / "blind_judgment_results.jsonl"
    if summary_path.exists():
        output_lines: list[str] = []
        for line in summary_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            result = json.loads(line)
            question_id = str(result.get("question_id", "")).strip()
            mapping = mappings.get(question_id)
            if not mapping:
                raise RuntimeError(f"盲判汇总缺少人工确认章节映射: {question_id}")
            attach_mapping(result, mapping)
            output_lines.append(json.dumps(result, ensure_ascii=False))
        summary_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    # 写入暂存元数据
    metadata = {
        "source_blind_run": str(source_dir.resolve()),
        "chapter_mapping_file": str(mapping_path.resolve()),
        "staged_question_count": len(staged_ids),
        "question_ids": sorted(staged_ids),
    }
    (target_dir / "explanation_stage_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return len(staged_ids)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="复制盲判运行结果并挂载已审核的章节映射。"
    )
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--target-dir", required=True)
    parser.add_argument("--chapter-map", required=True)
    args = parser.parse_args()

    count = stage_run(
        Path(args.source_dir), Path(args.target_dir), Path(args.chapter_map)
    )
    print(f"[output] staged_questions={count} | target={args.target_dir}")


if __name__ == "__main__":
    main()
