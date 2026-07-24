# -*- coding: utf-8 -*-
"""s6 — 解析撰写专用：输出层。Markdown 渲染、写盘、索引生成。"""

from __future__ import annotations

import json as _json
import re
import time
from pathlib import Path
from typing import Any

from 解析撰写.s1_explanation_data import (
    INSUFFICIENT_TEXT, load_question_result, SCHEMA_VERSION,
)


def chapter_text(result: dict[str, Any]) -> str:
    rows = result.get("chapter_mappings", []) or []
    if not rows:
        return "未映射"
    return "；".join(
        f"{row.get('real_chapter') or row.get('chapter_id', '')} {row.get('chapter_title', '')}".strip()
        for row in rows
    )


def render_markdown(
    result: dict[str, Any], explanation: dict[str, Any],
    standard_question: dict[str, Any] | None = None, export_mode: bool = False,
) -> str:
    lines: list[str] = [f"# {result.get('question_id', '')}\n\n"]
    lines.append(f"教材章节：{chapter_text(result)}\n\n")
    lines.append(f"题型：{result.get('question_type', '')}\n\n")
    lines.append(f"题干：{result.get('stem', '')}\n\n")
    standard_question = standard_question or {}
    stem_en = str(standard_question.get("stem_en", "") or "").strip()
    options_en = standard_question.get("options_en", {}) or {}
    if stem_en:
        lines.append(f"英文题干：{stem_en}\n\n")
    lines.append("选项：\n\n")
    for label, text in (result.get("options", {}) or {}).items():
        lines.append(f"- {label}. {text}\n")
        en_text = options_en.get(label, "")
        if en_text:
            lines.append(f"  English: {en_text}\n")

    answer = "、".join(explanation.get("answer", []) or []) or "未形成答案"
    deferral = explanation.get("deferral") if isinstance(explanation.get("deferral"), dict) else None
    if deferral and deferral.get("reason"):
        lines.append(f"\n## 【AI答案】\n\n{answer}\n\n")
        lines.append(f"> **解析被推迟（DEFERRED）**\n>\n")
        reason = deferral.get("reason", "")
        for rline in reason.split("\n"):
            lines.append(f"> {rline}\n")
        attempts = deferral.get("attempted_units", []) or []
        if attempts:
            lines.append(">\n> 已尝试但无法使用的 unit：\n")
            for uid in attempts:
                lines.append(f"> - {uid}\n")
        lines.append(">\n> 该题需人工撰写解析。\n")
        return "".join(lines)

    if export_mode:
        lines.append(f"\n答案：{answer}\n\n")
        lines.append("解析：\n\n")
        exam_point = explanation.get("exam_point", {}) or {}
        lines.append(f"考点：{exam_point.get('text') or INSUFFICIENT_TEXT}\n\n")
        core_analysis = explanation.get("core_analysis", {}) or {}
        lines.append(f"核心解析：{core_analysis.get('text') or INSUFFICIENT_TEXT}\n")
        source_quote = core_analysis.get("source_quote", {}) or {}
        if source_quote.get("exact_excerpt"):
            lines.append(f'教材原句："{source_quote["exact_excerpt"]}"\n')
        lines.append("\n")
        for row in explanation.get("option_explanations", []) or []:
            judgement = "正确" if row.get("judgement") == "correct" else "错误"
            lines.append(f"{row.get('option', '')}项{judgement}：{row.get('analysis', '')}\n")
        easy_mistake = explanation.get("easy_mistake", {}) or {}
        easy_text = (easy_mistake.get("text") or "").strip()
        if easy_text:
            lines.append(f"\n易错提醒：{easy_text}\n")
        return "".join(lines)

    # 教研格式
    lines.append(f"\n## 【AI答案】\n\n{answer}\n\n")
    flags = explanation.get("review_flags", []) or []
    if flags:
        lines.append("> **需人工复核**\n>\n")
        for f in flags:
            lines.append(f"> - {f}\n")
        lines.append("\n")
    lines.append("## 【考点】\n\n")
    exam_point = explanation.get("exam_point", {}) or {}
    lines.append((exam_point.get("text") or INSUFFICIENT_TEXT) + "\n\n")
    lines.append("## 【核心解析】\n\n")
    core_analysis = explanation.get("core_analysis", {}) or {}
    lines.append((core_analysis.get("text") or INSUFFICIENT_TEXT) + "\n\n")
    source_quote = core_analysis.get("source_quote", {}) or {}
    if source_quote.get("exact_excerpt"):
        lines.append(f'教材原句："{source_quote["exact_excerpt"]}"\n\n')
    lines.append("## 【错误项分析】\n\n")
    judgement_labels = {"correct": "正确", "incorrect": "错误", "insufficient": "证据不足"}
    basis_labels = {"textbook_direct": "教材直接依据", "textbook_definition_application": "教材定义应用",
                    "stem_contrast": "题干对照", "insufficient": "证据不足"}
    for row in explanation.get("option_explanations", []) or []:
        judgement = judgement_labels.get(str(row.get("judgement", "")), str(row.get("judgement", "")))
        basis = basis_labels.get(str(row.get("basis_type", "")), str(row.get("basis_type", "")))
        is_real_analysis = row.get("analysis", "") != INSUFFICIENT_TEXT
        if row.get("basis_type") == "insufficient" and is_real_analysis:
            basis = ""
        error_tag = ""
        if row.get("error_type") and not (row.get("basis_type") == "insufficient" and is_real_analysis):
            error_tag = f"｜{row['error_type']}"
        basis_tag = f"（{basis}）" if basis else ""
        lines.append(f"- **{row.get('option', '')} {judgement}{basis_tag}{error_tag}**：{row.get('analysis', '')}\n")
    lines.append("\n## 【易错提醒】\n\n")
    easy_mistake = explanation.get("easy_mistake", {}) or {}
    easy_text = (easy_mistake.get("text") or "").strip()
    lines.append((easy_text or "（无）") + "\n\n")
    lines.append("## 【教材原文依据】\n\n")
    primary_uid = str(explanation.get("primary_unit_id", "") or "").strip()
    if primary_uid:
        lines.append(f"> 核心引用单元：`{primary_uid}`\n\n")
    evidence_rows = explanation.get("source_evidence", []) or []
    if not evidence_rows:
        if not core_analysis.get("cited_unit_ids"):
            lines.append("本题依据题干明确事实直接推导，无教材引用。\n\n")
        else:
            lines.append(INSUFFICIENT_TEXT + "\n\n")
    for row in evidence_rows:
        used_by = "、".join(row.get("used_by", []) or []) or "未标注"
        heading = " > ".join(row.get("heading_context", []) or []) or "未标注"
        lines.append(f"### `{row.get('unit_id', '')}`\n\n")
        lines.append(f"- 用于：{used_by}\n")
        lines.append(f"- 章节：{heading}\n")
        pdf_page = row.get("pdf_page")
        printed_page = row.get("printed_page", "")
        if pdf_page is not None or printed_page:
            page_parts: list[str] = []
            if pdf_page is not None:
                page_parts.append(f"PDF第{pdf_page}页")
            if printed_page:
                page_parts.append(f"书内第{printed_page}页")
            lines.append(f"- 页码：{' / '.join(page_parts)}\n")
        lines.append(f"- 中文要点：{row.get('knowledge_zh', '') or '未提供'}\n")
        lines.append(f"- 英文原文：{row.get('en_quote', '') or '未提供'}\n\n")
    ref = explanation.get("reference_appendix", {}) or {}
    lines.append("## 【参考答案与参考解析】\n\n")
    lines.append(f"- 题库最终参考答案：{'、'.join(ref.get('final_answer', []) or []) or '未提供'}\n")
    lines.append(f"- 中文参考答案：{'、'.join(ref.get('cn_answer', []) or []) or '未提供'}\n\n")
    lines.append("### 中文参考解析\n\n")
    lines.append((ref.get("cn_explanation") or "未提供。") + "\n\n")
    lines.append(f"- 英文参考答案：{'、'.join(ref.get('en_answer', []) or []) or '未提供'}\n\n")
    lines.append("### 英文参考解析\n\n")
    lines.append((ref.get("en_explanation") or "未提供。") + "\n\n")
    lines.append("### 答案冲突提示\n\n")
    for message in ref.get("conflict_messages", []) or ["未发现答案冲突。"]:
        lines.append(f"- {message}\n")
    return "".join(lines)


def select_question_files(
    output_dir: Path, question_ids: list[str], limit: int | None, resume: bool = False,
) -> list[Path]:
    questions_dir = output_dir / "questions"
    if not questions_dir.exists():
        raise RuntimeError(f"questions 目录不存在: {questions_dir}")
    if question_ids:
        files = [questions_dir / f"q_{qid}.json" for qid in question_ids]
        missing = [str(path) for path in files if not path.exists()]
        if missing:
            raise RuntimeError("指定题号输出不存在: " + ", ".join(missing))
        return files
    files = sorted(questions_dir.glob("q_*.json"))
    if resume:
        remaining = []
        for f in files:
            try:
                d = _json.loads(f.read_text(encoding="utf-8"))
                if not d.get("generated_explanation"):
                    remaining.append(f)
            except Exception:
                remaining.append(f)
        print(f"[resume] 跳过 {len(files) - len(remaining)} 题已解析，剩余 {len(remaining)} 题")
        files = remaining
    return files[:limit] if limit is not None and limit > 0 else files


def collect_generated_rows(output_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((output_dir / "questions").glob("q_*.json")):
        result = load_question_result(path)
        explanation = result.get("generated_explanation", {}) or {}
        if explanation.get("schema_version") != SCHEMA_VERSION:
            continue
        qid = str(result.get("question_id", path.stem.removeprefix("q_")))
        reference = explanation.get("reference_appendix", {}) or {}
        markdown_path = output_dir / "explanations" / f"{qid}.md"
        rows.append({
            "question_id": qid,
            "status": "ok" if markdown_path.exists() else "markdown_missing",
            "pipeline_status": result.get("pipeline_status", ""),
            "software_ready": bool((explanation.get("software_readiness", {}) or {}).get("ready")),
            "answer": explanation.get("answer", []) or [],
            "chapter_mappings": result.get("chapter_mappings", []) or [],
            "reference_conflict": bool(reference.get("cn_en_conflict") or reference.get("blind_final_conflict")),
            "markdown_path": str(markdown_path) if markdown_path.exists() else "",
        })
    return rows


def write_index(rows: list[dict[str, Any]], output_dir: Path) -> Path:
    path = output_dir / "explanations" / "index.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# V3.1 教研解析索引\n\n",
             "| 题号 | 章节 | 盲判状态 | 软件就绪 | 答案 | 参考冲突 | Markdown |\n",
             "|---|---|---|---|---|---|---|\n"]
    for row in sorted(rows, key=lambda x: x.get("question_id", "")):
        chapters = ",".join(item.get("real_chapter") or item.get("chapter_id", "")
                            for item in row.get("chapter_mappings", []) or [])
        name = Path(row.get("markdown_path", "")).name if row.get("markdown_path") else ""
        link = f"[打开]({name})" if name else ""
        lines.append(f"| {row.get('question_id', '')} | {chapters} | "
                     f"{row.get('pipeline_status', '')} | {row.get('software_ready', False)} | "
                     f"{','.join(row.get('answer', []) or [])} | "
                     f"{row.get('reference_conflict', '')} | {link} |\n")
    path.write_text("".join(lines), encoding="utf-8")
    return path


def write_chapter_drafts(rows: list[dict[str, Any]], output_dir: Path) -> list[Path]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("status") != "ok" or not row.get("markdown_path"):
            continue
        for mapping in row.get("chapter_mappings", []) or []:
            chapter_id = mapping.get("real_chapter") or mapping.get("chapter_id", "")
            if not chapter_id:
                continue
            group = grouped.setdefault(chapter_id, {"chapter_title": mapping.get("chapter_title", ""), "rows": []})
            if not any(x.get("question_id") == row.get("question_id") for x in group["rows"]):
                group["rows"].append(row)

    chapter_dir = output_dir / "explanations" / "chapters"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for chapter_id, group in sorted(grouped.items()):
        question_rows = sorted(group["rows"], key=lambda x: x.get("question_id", ""))
        lines = [f"# {chapter_id} {group['chapter_title']} 教研解析草稿\n\n", f"题目数：{len(question_rows)}\n\n"]
        for row in question_rows:
            content = Path(row["markdown_path"]).read_text(encoding="utf-8")
            content = re.sub(r"^(#{1,5}) ", lambda m: "#" + m.group(1) + " ", content, flags=re.MULTILINE)
            lines.append(content.rstrip() + "\n\n---\n\n")
        path = chapter_dir / f"{chapter_id}.md"
        path.write_text("".join(lines), encoding="utf-8")
        paths.append(path)
    return paths