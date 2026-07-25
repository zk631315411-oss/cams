# -*- coding: utf-8 -*-
"""解析质量复核：LLM 按五类证据错误模式独立审查每题解析。

用法：
    python quality_review.py --output-dir ../output --limit 5
    python quality_review.py --output-dir ../output --sample-per-chapter 3
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PHASE4 = HERE.parent
_SRC = PHASE4 / "解析撰写"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import generate_evidence_explanations as master
from export_software_explanations import _load_kg_section_index, _build_section_code_map

QUALITY_REVIEW_SCHEMA = "quality_review_v1_0"

_REVIEW_PROMPT = """你是一个独立的CAMS解析质量复核员。你的任务是逐项检查AI生成的试题解析是否存在证据错误。

## 题目

题干（中文）：{stem_cn}
题干（英文）：{stem_en}

选项：
{options_text}

## AI解析

AI答案：{ai_answer}
考点：{exam_point}

核心解析：
{core_analysis}

错误项分析：
{option_analyses}

易错提醒：
{easy_mistake}

{evidence_text}

## 复核任务

请按以下五类错误模式，逐项检查AI解析的**证据质量**。注意：本题不检查AI答案是否正确、是否与题库一致——答案正确性由机械校验负责。

**判断原则：以证据的 knowledge_zh 和 en_quote 实际内容为第一依据。heading_context（章节路径）只是组织标签，可能与内容不完全一致——当标签和内容矛盾时，信内容，不信标签。**

1. **语境偷换**：AI引用的证据，其**实际内容**所描述的场景是否与本题题干场景一致？
   先读懂证据原文在讲什么，再和题干比较。不要仅凭 heading_context 的标签词下判断。
   例如：证据内容讲的是"SAR后维持账户"，但题干问的是"开户时"的CDD义务 → 语境不匹配。

2. **主语借代**：证据原文的主语/对象（银行、赌场、MSB、VASP等）是否与AI结论中的主体一致？
   例如：证据讲的是私营部门间信息共享，但AI将其作为公私合作（PPP）的证据 → 主语不匹配。

3. **后合理化**：AI引用的核心证据是否真的支撑其答案？区分"合理推理"和"装饰性引用"：
   - 合理推理：证据提供了原则或定义，AI据此推导出结论 → 不算后合理化
   - 装饰性引用：证据与结论没有逻辑关联，只是恰好包含某个关键词 → 算后合理化

4. **页码幻觉**：AI引用的所有（PXX）页码是否都在"证据池所有有效页码"列表中？逐一核对，不在清单中的即为页码幻觉。

5. **语气放大**：AI是否将原文的不确定/限定表述升级为确定/绝对语气？
   注意区分"语气放大"和"合理总结"——从"面临风险"推出"缺乏监管会增加风险"属于合理推理，不算语气放大。

## 输出格式

严格按照以下JSON格式输出（不要输出任何其他内容）：

```json
{{
  "errors": {{
    "context_theft": {{"found": false, "detail": ""}},
    "subject_substitution": {{"found": false, "detail": ""}},
    "post_rationalization": {{"found": false, "detail": ""}},
    "page_hallucination": {{"found": false, "detail": ""}},
    "tone_amplification": {{"found": false, "detail": ""}}
  }},
  "verdict": "{{pass|minor_issue|needs_fix}}",
  "recommendation": "",
  "summary": ""
}}
```

注意：
- 只检查证据质量，不检查答案是否正确。AI答案与题库参考答案冲突不在此复核范围内。
- verdict 判定规则：
  - pass：五类错误均未发现
  - needs_fix：context_theft、post_rationalization、page_hallucination 三者任一 found=true，或 tone_amplification / subject_substitution 问题严重到影响解析可信度
  - minor_issue：仅 tone_amplification 或 subject_substitution 轻微问题时使用。含义是"有小瑕疵但解析整体可信任"
- 每个error的detail：如found=true，必须写清具体证据（必须从AI解析原文中逐字引用，不得用自己的话转述）
- summary：一句话总结复核结论"""


def _build_review_prompt(
    result: dict[str, Any],
    unit_map: dict[str, dict[str, Any]],
    standard_question: dict[str, Any] | None = None,
) -> str:
    exp = result.get("generated_explanation", {}) or {}

    stem_cn = str(result.get("stem", "") or "")
    stem_en = str(standard_question.get("stem_en", "") if standard_question else result.get("stem_en", ""))

    options_lines: list[str] = []
    options = result.get("options", {}) or {}
    options_en = (standard_question.get("options_en", {}) or {}) if standard_question else {}
    for label in sorted(options.keys()):
        opt_cn = str(options.get(label, ""))
        opt_en = str(options_en.get(label, ""))
        line = f"{label}. {opt_cn}"
        if opt_en:
            line += f"\n   English: {opt_en}"
        options_lines.append(line)
    options_text = "\n".join(options_lines)

    ai_answer = "、".join(exp.get("answer", []) or [])
    exam_point = str((exp.get("exam_point", {}) or {}).get("text", ""))
    core_analysis = str((exp.get("core_analysis", {}) or {}).get("text", ""))

    option_analyses_lines: list[str] = []
    for row in exp.get("option_explanations", []) or []:
        label = row.get("option", "")
        judgement = "正确" if row.get("judgement") == "correct" else "错误"
        analysis = str(row.get("analysis", "") or "")
        option_analyses_lines.append(f"{label}项（{judgement}）：{analysis}")
    option_analyses = "\n".join(option_analyses_lines)

    easy_mistake = str((exp.get("easy_mistake", {}) or {}).get("text", ""))

    # ── 全量证据池（盲判/解析/复核共享同一池）──
    cited_uids = _collect_cited_uids(exp)

    # 从 source_evidence 构建页码查找表
    page_lookup: dict[str, dict[str, Any]] = {}
    for se in (exp.get("source_evidence", []) or []):
        uid = str(se.get("unit_id", "") or "")
        if uid:
            page_lookup[uid] = {"pdf_page": se.get("pdf_page", ""), "printed_page": se.get("printed_page", "")}

    # 加载 KG 页码
    kg_page_map: dict[str, dict[str, Any]] = {}
    try:
        kg_path = master.KG_GRAPH_PATH
        if kg_path.exists():
            with open(kg_path, "r", encoding="utf-8") as f:
                kg = json.load(f)
            for u in kg.get("units", []) or []:
                uid = str(u.get("unit_id", ""))
                if uid:
                    kg_page_map[uid] = {"pdf_page": u.get("pdf_page", ""), "printed_page": u.get("printed_page", "")}
    except Exception:
        pass

    evidence_parts: list[str] = []
    all_pool_pages: set[int] = set()
    evidence_parts.append(f"## 本题证据池（共{len(unit_map)}个单元，盲判/解析/复核共享）\n")

    for uid in sorted(unit_map.keys()):
        unit = unit_map.get(uid, {})
        if not unit:
            continue
        zh = str(unit.get("knowledge_zh", "") or "")
        en = str(unit.get("en_quote", "") or "")
        hc = str(unit.get("heading_context", "") or "")
        pg = page_lookup.get(uid, {}) or kg_page_map.get(uid, {})
        printed = pg.get("printed_page", "") or unit.get("printed_page", "")
        page_info = f"P{printed}" if printed else ""
        if printed and str(printed).strip().isdigit():
            all_pool_pages.add(int(printed))
        is_cited = uid in cited_uids
        marker = " [AI已引用]" if is_cited else ""
        evidence_parts.append(
            f"### {uid}{marker}\n"
            f"章节路径：{hc}\n"
            f"页码：{page_info}\n"
            f"中文要点：{zh}\n"
            f"英文原文：{en}\n"
        )

    evidence_text = "\n".join(evidence_parts) if evidence_parts else "（无引用证据）"

    page_list = "、P".join(str(p) for p in sorted(all_pool_pages)) if all_pool_pages else "（无）"
    evidence_text += (
        f"\n\n## 证据池所有有效页码（共{len(all_pool_pages)}个）\n\n"
        f"P{page_list}\n\n"
        "（AI解析中的任何页码引用必须在此列表中，否则为页码幻觉）"
    )

    return _REVIEW_PROMPT.format(
        stem_cn=stem_cn, stem_en=stem_en, options_text=options_text,
        ai_answer=ai_answer, exam_point=exam_point, core_analysis=core_analysis,
        option_analyses=option_analyses, easy_mistake=easy_mistake,
        evidence_text=evidence_text,
    )


def _collect_cited_uids(exp: dict[str, Any]) -> set[str]:
    uids: set[str] = set()
    core = exp.get("core_analysis", {}) or {}
    for uid in (core.get("cited_unit_ids", []) or []):
        uids.add(str(uid))
    for row in (exp.get("option_explanations", []) or []):
        for uid in (row.get("cited_unit_ids", []) or []):
            uids.add(str(uid))
        for sc in (row.get("source_claims", []) or []):
            uid = str(sc.get("unit_id", "") or "")
            if uid:
                uids.add(uid)
    easy = exp.get("easy_mistake", {}) or {}
    for uid in (easy.get("cited_unit_ids", []) or []):
        uids.add(str(uid))
    return uids


def _parse_review_response(raw: str) -> dict[str, Any]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return {
        "errors": {}, "verdict": "parse_failed",
        "recommendation": "", "summary": f"无法解析LLM响应。原始输出：{raw[:500]}",
    }


def _select_review_targets(
    output_dir: Path, sample_per_chapter: int = 3
) -> list[tuple[str, str]]:
    question_dir = output_dir / "questions"
    if not question_dir.exists():
        raise RuntimeError(f"questions目录不存在: {question_dir}")

    kg_index = _load_kg_section_index()
    code_map = _build_section_code_map(kg_index) if kg_index else {}

    chapter_questions: dict[str, list[dict[str, Any]]] = {}
    conflicts: list[str] = []
    flagged: list[str] = []
    passed: list[str] = []

    for path in sorted(question_dir.glob("q_*.json")):
        result = master.load_question_result(path)
        qid = str(result.get("question_id", ""))
        exp = result.get("generated_explanation", {}) or {}
        ref = exp.get("reference_appendix", {}) or {}

        answer = [str(x).strip().upper() for x in exp.get("answer", []) or []]
        answer_set = set(answer)
        is_conflict = False
        for field in ("final_answer", "cn_answer", "en_answer"):
            ref_vals = set(str(x).strip().upper() for x in ref.get(field, []) or [])
            if ref_vals and ref_vals != answer_set:
                is_conflict = True
                break

        readiness = exp.get("software_readiness", {}) or {}
        risk_flags = readiness.get("risk_flags", []) or ref.get("risk_flags", []) or []

        primary_uid = str(exp.get("primary_unit_id", "") or "").strip()
        chapter = code_map.get(primary_uid, "unknown")
        if chapter == "unknown":
            unit_map = master.candidate_by_unit(result)
            for uid in unit_map:
                if uid in code_map:
                    chapter = code_map[uid]
                    break
        chapter_key = chapter.split("-")[1] if "-" in chapter else chapter
        chapter_questions.setdefault(chapter_key, []).append({"qid": qid, "result": result})

        if is_conflict:
            conflicts.append(qid)
        elif risk_flags:
            flagged.append(qid)
        else:
            passed.append(qid)

    targets: list[tuple[str, str]] = []
    targets.extend((qid, "conflict") for qid in conflicts)
    targets.extend((qid, "flagged") for qid in flagged)

    random.seed(42)
    for chapter, qs in sorted(chapter_questions.items()):
        chapter_passed = [q["qid"] for q in qs if q["qid"] in passed]
        if chapter_passed:
            sample_n = min(sample_per_chapter, len(chapter_passed))
            sampled = random.sample(chapter_passed, sample_n)
            targets.extend((qid, "sampled") for qid in sampled)

    return targets


def _load_standard_questions() -> dict[str, dict[str, Any]]:
    qp = master.DEFAULT_QUESTIONS_PATH
    if not Path(qp).exists():
        return {}
    with open(qp, "r", encoding="utf-8") as f:
        data = json.load(f)
    index: dict[str, dict[str, Any]] = {}
    for item in data.get("items", []) or []:
        qid = str(item.get("question_id", ""))
        if qid:
            index[qid] = item
    return index


def process_question(
    qid: str, review_type: str, output_dir: Path,
    standard_questions: dict[str, dict[str, Any]],
    api_key: str, base_url: str, model: str,
) -> dict[str, Any]:
    from openai import OpenAI

    path = output_dir / "questions" / f"q_{qid}.json"
    result = master.load_question_result(path)
    unit_map = master.candidate_by_unit(result)
    std_q = standard_questions.get(qid)

    prompt = _build_review_prompt(result, unit_map, std_q)

    client = OpenAI(api_key=api_key, base_url=base_url)
    raw = ""
    for attempt in range(3):
        try:
            raw = master.call_llm(
                client, prompt, model=model, max_tokens=6000,
                reasoning_effort="high", enable_thinking=True,
            )
            if raw and raw.strip():
                break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    review = _parse_review_response(raw)

    review["question_id"] = qid
    review["review_type"] = review_type
    review["model"] = model
    review["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

    review_dir = output_dir / "quality_reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_path = review_dir / f"{qid}.json"
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")

    return review


def _write_report(reviews: list[dict[str, Any]], output_dir: Path) -> None:
    review_dir = output_dir / "quality_reviews"
    review_dir.mkdir(parents=True, exist_ok=True)

    total = len(reviews)
    verdict_counts: dict[str, int] = {}
    error_counts: dict[str, int] = {}
    needs_fix: list[dict[str, Any]] = []

    for r in reviews:
        v = r.get("verdict", "unknown")
        verdict_counts[v] = verdict_counts.get(v, 0) + 1
        errors = r.get("errors", {}) or {}
        for err_type, err_detail in errors.items():
            if isinstance(err_detail, dict) and err_detail.get("found"):
                error_counts[err_type] = error_counts.get(err_type, 0) + 1
        if v in ("needs_fix", "minor_issue"):
            needs_fix.append(r)

    lines = ["# 解析质量复核报告\n\n", f"复核题数：{total} | 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n", "## Verdict 分布\n\n"]
    for v, c in sorted(verdict_counts.items()):
        lines.append(f"- {v}: {c}\n")
    lines.append(f"\n## 五类错误检出数\n\n")
    for e, c in sorted(error_counts.items()):
        lines.append(f"- {e}: {c}\n")

    if needs_fix:
        lines.append(f"\n## 需处理的题目（{len(needs_fix)}题）\n\n")
        for r in sorted(needs_fix, key=lambda x: (x.get("verdict", ""), x.get("question_id", ""))):
            qid = r.get("question_id", "")
            v = r.get("verdict", "")
            summary = r.get("summary", "")
            lines.append(f"### {qid} [{v}]\n\n{summary}\n\n")
            errors = r.get("errors", {}) or {}
            for err_type, err_detail in errors.items():
                if isinstance(err_detail, dict) and err_detail.get("found"):
                    lines.append(f"- {err_type}: {err_detail.get('detail', '')}\n")
            lines.append("\n")

    report_path = output_dir / "software_export" / "quality_review_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("".join(lines), encoding="utf-8")

    summary = {
        "schema_version": QUALITY_REVIEW_SCHEMA, "total": total,
        "verdict_counts": verdict_counts, "error_counts": error_counts,
        "needs_fix_count": len(needs_fix),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    summary_path = review_dir / "quality_review_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[output] report={report_path}")
    print(f"[output] summary={summary_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM 解析质量复核（五类证据错误检测）")
    parser.add_argument("--output-dir", required=True, help="phase4_evidence/output 目录")
    parser.add_argument("--sample-per-chapter", type=int, default=3, help="通过题每章抽样数（默认3）")
    parser.add_argument("--limit", type=int, default=0, help="最多复核题数（0=全部）")
    parser.add_argument("--question-ids", default="", help="限定复核的题目ID（逗号分隔）")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--concurrency", type=int, default=3)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    api_key, base_url, _ = master.get_llm_config()
    standard_questions = _load_standard_questions()

    targets = _select_review_targets(output_dir, args.sample_per_chapter)
    if args.question_ids:
        qid_set = {q.strip() for q in args.question_ids.split(",") if q.strip()}
        targets = [(qid, rt) for qid, rt in targets if qid in qid_set]
    if args.limit > 0:
        targets = targets[: args.limit]

    conflict_n = sum(1 for _, t in targets if t == "conflict")
    flagged_n = sum(1 for _, t in targets if t == "flagged")
    sampled_n = sum(1 for _, t in targets if t == "sampled")
    print(f"复核目标：{len(targets)}题（冲突{conflict_n} + 标记{flagged_n} + 抽样{sampled_n}）")

    reviews: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {executor.submit(process_question, qid, rt, output_dir, standard_questions, api_key, base_url, args.model): qid for qid, rt in targets}
        for i, future in enumerate(as_completed(futures), 1):
            qid = futures[future]
            try:
                review = future.result()
                reviews.append(review)
                print(f"  [{i}/{len(targets)}] {qid} → {review.get('verdict', '?')}")
            except Exception as e:
                print(f"  [{i}/{len(targets)}] {qid} → ERROR: {e}")

    _write_report(reviews, output_dir)


if __name__ == "__main__":
    main()
