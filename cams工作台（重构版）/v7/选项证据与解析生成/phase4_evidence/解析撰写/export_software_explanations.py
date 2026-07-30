# -*- coding: utf-8 -*-
"""将 V3.1 解析母版按 Section 导出为题库软件版 Markdown。

不阻断任何题目——复核检测请用 review_check.py。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

_PARENT = str(Path(__file__).resolve().parent.parent)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from 解析撰写.s1_explanation_data import (
    DEFAULT_QUESTIONS_PATH, KG_GRAPH_PATH, SOURCE_QUOTE_MAX_LENGTH,
    SOURCE_QUOTE_MIN_LENGTH, load_question_result, load_standard_questions,
)
from 解析撰写.s2_explanation_material import candidate_by_unit


EXPORT_SCHEMA_VERSION = "software_explanation_export_v2_0"
HERE = Path(__file__).resolve().parent
PHASE4 = HERE.parent


def _normalize_select_hint(text: str) -> str:
    """统一学生可见题干中的多选提示标点。"""
    if not text:
        return text
    text = re.sub(r"[（(]\s*选择两项\s*[.。]?\s*[)）]", "（选择两项。）", text)
    text = re.sub(r"[（(]\s*选择三项\s*[.。]?\s*[)）]", "（选择三项。）", text)
    return text


def _load_kg_section_index() -> dict[str, dict[str, Any]]:
    """加载 KG，返回 {unit_id: {real_chapter, real_section, section_order}} 索引。"""
    kg_path = KG_GRAPH_PATH
    if not kg_path.exists():
        return {}
    with open(kg_path, "r", encoding="utf-8") as f:
        kg: dict[str, Any] = json.load(f)

    section_index: dict[str, dict[str, Any]] = {}
    for sec in kg.get("sections", []) or []:
        sid = str(sec.get("section_id", ""))
        section_index[sid] = {
            "real_chapter": sec.get("real_chapter", ""),
            "real_section": sec.get("real_section") or sid,
            "section_order": sec.get("section_order", 0),
            "section_title": sec.get("section_title", ""),
        }

    unit_index: dict[str, dict[str, Any]] = {}
    for unit in kg.get("units", []) or []:
        uid = str(unit.get("unit_id", ""))
        sid = str(unit.get("section_id", ""))
        sec_info = section_index.get(sid, {})
        unit_index[uid] = {
            "real_chapter": unit.get("real_chapter") or sec_info.get("real_chapter", ""),
            "real_section": unit.get("real_section") or sec_info.get("real_section", ""),
            "section_order": sec_info.get("section_order", 0),
        }
    return unit_index


def _build_section_code_map(kg_index: dict[str, dict[str, Any]]) -> dict[str, str]:
    """直接采用 KG 已确定的 real_section 作为题目导出小节。"""
    section_pattern = re.compile(r"^p[1-4]-ch(?:[1-9]|1[0-6])-h[1-9][0-9]*$")
    return {
        uid: real_section
        for uid, info in kg_index.items()
        if (real_section := str(info.get("real_section", "") or "").strip())
        and section_pattern.fullmatch(real_section)
    }


def get_section_code(
    result: dict[str, Any],
    kg_index: dict[str, dict[str, Any]],
    code_map: dict[str, str],
) -> str:
    """从解析结果的 primary_unit_id 查出 section_code。"""
    explanation = result.get("generated_explanation", {}) or {}
    primary_uid = str(explanation.get("primary_unit_id", "") or "").strip()
    if primary_uid and primary_uid in code_map:
        return code_map[primary_uid]
    unit_map = candidate_by_unit(result)
    for uid in unit_map:
        if uid in code_map:
            return code_map[uid]
    return ""


def _convert_full_to_simplified(preview: str, qid: str) -> str:
    """将 explanations/ 完整格式预览转换为 DOCX 转换器能解析的简化格式。"""
    # 分离头部（题干+选项）和解析主体
    first_h2 = preview.find('\n## 【')
    if first_h2 == -1:
        return preview
    header = preview[:first_h2].strip()
    body = preview[first_h2:]

    # 移除英文题干行和选项英文行（DOCX只保留中文）
    header_lines = []
    for line in header.split('\n'):
        s = line.strip()
        if s.startswith('英文题干：') or s.startswith('English:'):
            continue
        if s.startswith('English:'):
            continue
        # 清理题干中的 [章节名] 前缀
        s = re.sub(r'^(题干：|题目：)\[.+?\]', r'\1', s)
        s = _normalize_select_hint(s)
        # 统一选项行格式。部分原始解析为 "A. xxx" 而非 "- A. xxx"，
        # DOCX 转换器只按 "- " 识别选项；这里补齐前缀，避免导入题库时选项不足。
        if re.match(r'^[A-H][\.．、]\s+', s):
            s = f'- {s}'
        header_lines.append(s)
    header = '\n'.join(header_lines)

    # 移除 blockquote 块（> **需人工复核** 等），包括块内单独的空引用行。
    body = re.sub(r'(?m)^(?:>[^\r\n]*(?:\r?\n|$))+', '', body)

    # 提取各 ## 段落
    sections: dict[str, str] = {}
    current_sec = None
    current_lines: list[str] = []
    for line in body.split('\n'):
        m = re.match(r'## 【(.+?)】', line)
        if m:
            if current_sec and current_lines:
                sections[current_sec] = '\n'.join(current_lines).strip()
            current_sec = m.group(1)
            current_lines = []
        else:
            current_lines.append(line)
    if current_sec and current_lines:
        sections[current_sec] = '\n'.join(current_lines).strip()

    # 答案
    answer = sections.get('AI答案', '').strip()
    # 移除答案后可能残留的 > 块（已在上面清理，但双保险）
    answer = re.sub(r'\n> .*', '', answer).strip()
    answer_letters = set(re.findall(r'[A-H]', answer))

    # 核心解析中提取教材原句。按整行保留，避免多段引文只导出第一段。
    core_text = sections.get('核心解析', '').strip()
    quote = ''
    m_quote = re.search(r'(?m)^教材原句[：:]\s*(.+?)\s*$', core_text)
    if m_quote:
        quote = m_quote.group(1).strip()
        core_text = (
            core_text[:m_quote.start()] + core_text[m_quote.end():]
        ).strip()

    # 构建简化格式
    out: list[str] = [header, '', f'答案：{answer}', '', '解析：', '']

    if '考点' in sections:
        out.append(f'考点：{sections["考点"].strip()}')
        out.append('')
    if core_text:
        out.append(f'核心解析：{core_text}')
        out.append('')
    if quote:
        out.append(f'教材原句：{quote}')
        out.append('')

    if '错误项分析' in sections:
        for line in sections['错误项分析'].split('\n'):
            line = line.strip()
            if not line or not line.startswith('-'):
                continue
            # 匹配所有变体：- **A 错误（x）｜y**： / - **A不选（x）｜y**： / - **A、B 正确｜x**：
            m_err = re.match(
                r'- \*\*([A-H](?:[、,][A-H])*)([^*]*)\*\*[：:]?\s*(.+)',
                line,
            )
            if m_err:
                letter = m_err.group(1)
                source_status = m_err.group(2)
                analysis = m_err.group(3).strip()
                labels = set(re.findall(r'[A-H]', letter))
                if labels & answer_letters and not labels <= answer_letters:
                    raise ValueError(f'{qid}: 同组选项同时包含正确项和错误项: {letter}')

                is_correct = bool(labels) and labels <= answer_letters
                if '正确' in source_status and not is_correct:
                    raise ValueError(f'{qid}: 原解析将非答案项标为正确: {letter}')
                if re.search(r'错误|不选|不如', source_status) and is_correct:
                    raise ValueError(f'{qid}: 原解析将答案项标为错误或不选: {letter}')

                judgement = '正确' if is_correct else '错误'
                out.append(f'{letter}项{judgement}：{analysis}')
            else:
                out.append(line)
        out.append('')

    easy_text = sections.get('易错提醒', '').strip()
    if easy_text and easy_text not in {'（无）', '(无)', '无'}:
        out.append(f'易错提醒：{easy_text}')
        out.append('')

    return '\n'.join(out)


def _validate_student_preview(preview: str, qid: str) -> None:
    """阻止答案与学生可见的选项正误标签发生矛盾。"""
    answer_match = re.search(
        r'^答案：\s*([A-H](?:\s*[、,，]\s*[A-H])*)\s*$', preview, re.M
    )
    if not answer_match:
        raise ValueError(f'{qid}: 学生版解析缺少有效答案')

    answer_letters = set(re.findall(r'[A-H]', answer_match.group(1)))
    conflicts: list[str] = []
    for match in re.finditer(
        r'^([A-H](?:[、,，][A-H])*)项(正确|错误)：', preview, re.M
    ):
        labels = set(re.findall(r'[A-H]', match.group(1)))
        judgement = match.group(2)
        if judgement == '正确' and not labels <= answer_letters:
            conflicts.append(f'{match.group(1)}项被标为正确但不在答案中')
        if judgement == '错误' and labels & answer_letters:
            conflicts.append(f'{match.group(1)}项被标为错误但属于答案')

    if conflicts:
        raise ValueError(f'{qid}: 学生版答案标签冲突: {"；".join(conflicts)}')


def render_software_analysis(explanation: dict[str, Any]) -> str:
    """将解析母版渲染为题库软件使用的解析文本。"""
    answer = "、".join(explanation.get("answer", []) or [])
    exam_point = explanation.get("exam_point", {}) or {}
    core = explanation.get("core_analysis", {}) or {}
    easy = explanation.get("easy_mistake", {}) or {}
    quote = (core.get("source_quote", {}) or {}).get("exact_excerpt", "")

    lines = [f"答案：{answer}\n\n", "解析：\n\n"]
    lines.append("【考点】\n")
    lines.append(f"{exam_point.get('text', '')}\n\n")
    lines.append("【核心解析】\n")
    lines.append(f"{core.get('text', '')}\n")
    if quote:
        lines.append(f"教材原句：\"{quote}\"\n")
    lines.append("\n")
    lines.append("【错误项分析】\n")
    for row in explanation.get("option_explanations", []) or []:
        judgement = "正确" if row.get("judgement") == "correct" else "错误"
        lines.append(f"{row.get('option', '')}项{judgement}：{row.get('analysis', '')}\n")
    easy_text = (easy.get("text", "") or "").strip()
    if easy_text:
        lines.append("\n【易错提醒】\n")
        lines.append(f"{easy_text}\n")
    return "".join(lines)


def render_question_preview(
    result: dict[str, Any], standard_question: dict[str, Any]
) -> str:
    """渲染单题的完整预览（题目 + 英文 + 解析）。"""
    qid = result.get("question_id", "")
    qtype = "单选题" if result.get("question_type") == "single" else "多选题"
    stem_en = str(standard_question.get("stem_en", "") or "").strip()
    options_en = standard_question.get("options_en", {}) or {}
    lines = [f"## {qid}\n\n", f"题型：{qtype}\n\n"]
    lines.append(f"题目：{_normalize_select_hint(str(result.get('stem', '') or ''))}\n\n")
    if stem_en:
        lines.append(f"English: {stem_en}\n\n")
    lines.append("选项：\n\n")
    for label, text in (result.get("options", {}) or {}).items():
        lines.append(f"- {label}. {text}\n")
        if options_en.get(label):
            lines.append(f"  English: {options_en[label]}\n")

    lines.append("\n" + render_software_analysis(result["generated_explanation"]))
    return "".join(lines)


def export_by_section(
    output_dir: Path,
    standard_questions: dict[str, dict[str, Any]],
    output_subdir: str = "software_export",
) -> dict[str, Any]:
    """按 Section 导出可入库的软件版解析预览。

    不阻断任何题目——所有有 generated_explanation 的题目都会导出。
    有问题标注在题目预览中。
    """
    question_dir = output_dir / "questions"
    if not question_dir.exists():
        raise RuntimeError(f"questions目录不存在: {question_dir}")

    kg_index = _load_kg_section_index()
    code_map = _build_section_code_map(kg_index) if kg_index else {}

    # 读所有题目并按 section 分组
    section_groups: dict[str, list[dict[str, Any]]] = {}
    unassigned: list[dict[str, Any]] = []
    total_selected = 0

    for path in sorted(question_dir.glob("q_*.json")):
        result = load_question_result(path)
        total_selected += 1
        section_code = get_section_code(result, kg_index, code_map)
        if section_code:
            section_groups.setdefault(section_code, []).append(result)
        else:
            unassigned.append(result)

    export_dir = output_dir / output_subdir
    section_dir = export_dir / "sections"
    section_dir.mkdir(parents=True, exist_ok=True)

    explanations_dir = output_dir / "explanations"

    exported_count = 0
    skipped_count = 0
    section_summaries: list[dict[str, Any]] = []

    for section_code, results in sorted(section_groups.items()):
        exported: list[dict[str, Any]] = []

        for result in results:
            qid = str(result.get("question_id", ""))
            explanation = result.get("generated_explanation", {}) or {}

            # 从 explanations/ 读取内部格式 md（唯一 md 源）
            md_path = explanations_dir / f"{qid}.md"
            if md_path.exists():
                preview = md_path.read_text(encoding="utf-8").strip()
                # 去掉 # v7_q_ 标题行
                preview = preview.replace(f"# {qid}\n\n", "", 1)
                # 切除内部诊断区块（只保留考点/核心解析/错误项分析/易错提醒）
                for cut_marker in ("\n## 【教材原文依据】", "\n## 【参考答案与参考解析】"):
                    idx = preview.find(cut_marker)
                    if idx != -1:
                        preview = preview[:idx].rstrip()
                # 从 md 提取答案用于判断是否可导出
                answer_match = re.search(r'## 【AI答案】\s*\n+([A-H,、，\s]+?)(?:\n|$)', preview)
                answer_from_md = [a.strip() for a in (re.split(r'[,、，]+', answer_match.group(1)) if answer_match else []) if a.strip()]
                if answer_from_md:
                    explanation["answer"] = answer_from_md  # 回填，供后续渲染使用
                # 转换为 DOCX 转换器能解析的简化格式
                preview = _convert_full_to_simplified(preview, qid)
            else:
                preview = None

            if not explanation.get("answer"):
                skipped_count += 1
                continue

            if preview is None:
                preview = render_question_preview(
                    result, standard_questions.get(qid, {})
                )

            preview = preview.replace("「", "“").replace("」", "”")
            _validate_student_preview(preview, qid)
            row = {
                "question_id": qid,
                "answer": explanation["answer"],
                "preview": preview,
            }
            exported.append(row)

        exported_count += len(exported)

        md_lines = [
            f"# {section_code} 题库软件版解析预览\n\n",
            f"可导出题目数：{len(exported)}\n\n",
        ]
        for row in exported:
            md_lines.append(row.pop("preview").rstrip() + "\n\n---\n\n")
        section_path = section_dir / f"{section_code}.md"
        section_path.write_text("".join(md_lines), encoding="utf-8")

        section_summaries.append({
            "section_code": section_code,
            "exported_count": len(exported),
            "markdown": str(section_path),
        })

    # 写汇总
    print("\n" + "=" * 60)
    print("导出汇总")
    print("=" * 60)
    print(f"总题数: {total_selected}")
    print(f"已导出: {exported_count}")
    print(f"跳过(无AI答案): {skipped_count}")
    print(f"未归属小节: {len(unassigned)}")
    print(f"小节数: {len(section_summaries)}")
    if unassigned:
        print("\n未归属小节题目:")
        for r in unassigned:
            print(f"  - {r.get('question_id', '?')}")
    print("=" * 60)
    print(f"\n复核检测请运行: python review_check.py --output-dir {output_dir}")
    print("=" * 60)

    summary = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "total_selected": total_selected,
        "exported_count": exported_count,
        "skipped_count": skipped_count,
        "unassigned_count": len(unassigned),
        "section_count": len(section_summaries),
        "sections": section_summaries,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    summary_path = export_dir / "export_results.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="将 V3 解析母版按 Section 导出为题库软件版格式（不阻断）。"
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--questions-path", default=str(DEFAULT_QUESTIONS_PATH))
    parser.add_argument("--output-subdir", default="software_export")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    standards = load_standard_questions(args.questions_path)

    summary = export_by_section(
        output_dir,
        standards,
        output_subdir=args.output_subdir,
    )
    print(
        f"\n[output] total={summary['total_selected']} | "
        f"exported={summary['exported_count']} | skipped={summary['skipped_count']} | "
        f"unassigned={summary['unassigned_count']} | sections={summary['section_count']}"
    )
    print(f"[output] sections={output_dir / args.output_subdir / 'sections/'}")
    print(f"[output] summary={output_dir / args.output_subdir / 'export_results.json'}")


if __name__ == "__main__":
    main()
