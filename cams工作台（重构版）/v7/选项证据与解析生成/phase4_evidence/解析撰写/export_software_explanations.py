# -*- coding: utf-8 -*-
"""将 V3.1 解析母版按 Section 导出为题库软件版 Markdown。

不阻断任何题目——复核检测请用 review_check.py。
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import generate_evidence_explanations as master


EXPORT_SCHEMA_VERSION = "software_explanation_export_v2_0"
HERE = Path(__file__).resolve().parent
PHASE4 = HERE.parent


def _load_kg_section_index() -> dict[str, dict[str, Any]]:
    """加载 KG，返回 {unit_id: {real_chapter, real_section, section_order}} 索引。"""
    kg_path = master.KG_GRAPH_PATH
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
    """根据 real_chapter 和 section_order，生成 section_code → 'p1-ch01-h1' 映射。

    规则：Part 编号从 real_chapter 提取（Ch1-Ch4→P1, Ch5-Ch7→P2, Ch8-Ch12→P3, Ch13-Ch16→P4），
    Chapter 编号取 real_chapter 的数字，节序号在每章内按 section_order 递增。
    """
    chapter_to_part: dict[str, int] = {}
    for ch_num in range(1, 17):
        if ch_num <= 4:
            chapter_to_part[f"Ch{ch_num}"] = 1
        elif ch_num <= 7:
            chapter_to_part[f"Ch{ch_num}"] = 2
        elif ch_num <= 12:
            chapter_to_part[f"Ch{ch_num}"] = 3
        else:
            chapter_to_part[f"Ch{ch_num}"] = 4

    sections: dict[str, tuple[str, int]] = {}
    for info in kg_index.values():
        rs = info.get("real_section", "")
        rc = info.get("real_chapter", "")
        so = info.get("section_order", 0)
        if rs and rc and so:
            if rs not in sections or so < sections[rs][1]:
                sections[rs] = (rc, so)

    chapter_h_counter: dict[str, int] = {}
    section_code: dict[str, str] = {}
    for rs, (rc, so) in sorted(sections.items(), key=lambda x: (x[1][0], x[1][1])):
        chapter_h_counter.setdefault(rc, 0)
        chapter_h_counter[rc] += 1
        h_num = chapter_h_counter[rc]
        part = chapter_to_part.get(rc, 0)
        ch_num = rc.replace("Ch", "")
        section_code[rs] = f"p{part}-ch{ch_num}-h{h_num}"

    code_map: dict[str, str] = {}
    for uid, info in kg_index.items():
        rs = info.get("real_section", "")
        if rs in section_code:
            code_map[uid] = section_code[rs]

    return code_map


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
    unit_map = master.candidate_by_unit(result)
    for uid in unit_map:
        if uid in code_map:
            return code_map[uid]
    return ""


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
    lines.append(f"题目：{result.get('stem', '')}\n\n")
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
        result = master.load_question_result(path)
        total_selected += 1
        section_code = get_section_code(result, kg_index, code_map)
        if section_code:
            section_groups.setdefault(section_code, []).append(result)
        else:
            unassigned.append(result)

    export_dir = output_dir / output_subdir
    section_dir = export_dir / "sections"
    section_dir.mkdir(parents=True, exist_ok=True)

    # 导入格式 md 源目录
    explanations_export_dir = output_dir / "explanations_export"

    exported_count = 0
    skipped_count = 0
    section_summaries: list[dict[str, Any]] = []

    for section_code, results in sorted(section_groups.items()):
        exported: list[dict[str, Any]] = []

        for result in results:
            qid = str(result.get("question_id", ""))
            explanation = result.get("generated_explanation", {}) or {}
            if not explanation.get("answer"):
                skipped_count += 1
                continue

            # 从 explanations_export/ 读取导入格式 md
            export_md_path = explanations_export_dir / f"{qid}.md"
            if export_md_path.exists():
                preview = export_md_path.read_text(encoding="utf-8").strip()
                # 去掉 # v7_q_ 标题行（小节 md 有自己的标题）
                preview = preview.replace(f"# {qid}\n\n", "", 1)
            else:
                # 回退：从 JSON 构建
                preview = render_question_preview(
                    result, standard_questions.get(qid, {})
                )

            preview = preview.replace("「", "“").replace("」", "”")
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
    parser.add_argument("--questions-path", default=str(master.DEFAULT_QUESTIONS_PATH))
    parser.add_argument("--output-subdir", default="software_export")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    standards = master.load_standard_questions(args.questions_path)

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
