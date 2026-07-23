# -*- coding: utf-8 -*-
"""模拟 CAMS 备考新手，检测解析是否能让小白看懂。"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PHASE4 = HERE.parent

sys.path.insert(0, str(PHASE4 / "解析撰写"))
import generate_evidence_explanations as gen  # noqa: E402

MODEL = "deepseek-v4-flash"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"


def get_api_config() -> tuple[str, str]:
    for name in API_KEY_ENV_NAMES:
        value = os.environ.get(name)
        if value:
            base = os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL") or DEFAULT_BASE_URL
            return value, base
    raise RuntimeError("未设置 API key 环境变量")


def load_question(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_student_prompt(result: dict[str, Any]) -> str:
    stem = result.get("stem", "")
    options = result.get("options", {}) or {}
    exp = result.get("generated_explanation", {}) or {}

    answer = "、".join(exp.get("answer", []) or [])
    exam_point = (exp.get("exam_point", {}) or {}).get("text", "")
    core = (exp.get("core_analysis", {}) or {}).get("text", "")
    source_quote = ((exp.get("core_analysis", {}) or {}).get("source_quote", {}) or {}).get("exact_excerpt", "")
    easy = (exp.get("easy_mistake", {}) or {}).get("text", "")

    opt_text = "\n".join(f"  {k}: {v}" for k, v in options.items())
    err_lines: list[str] = []
    for row in exp.get("option_explanations", []) or []:
        err_lines.append(f"  {row.get('option', '')}: {row.get('analysis', '')}")
    err_text = "\n".join(err_lines) if err_lines else "（无）"

    # 教材原文依据（供学生对照核查）
    evidence_lines: list[str] = []
    for ev in exp.get("source_evidence", []) or []:
        heading = " > ".join(ev.get("heading_context", []) or [])
        page = ev.get("printed_page", "")
        page_str = f"（书内第{page}页）" if page else ""
        evidence_lines.append(
            f"### {ev.get('unit_id', '')} {page_str}\n"
            f"章节：{heading}\n"
            f"英文原文：{ev.get('en_quote', '')}\n"
        )
    evidence_text = "\n".join(evidence_lines) if evidence_lines else "（无）"

    return f"""你是一位刚开始备考 CAMS 考试的学员。你没看过教材，非金融/法律专业出身，英语也不是母语。你正在通过做练习题来学习——每道题看答案和解析，边做边学。

下面是一道题目、答案解析，以及解析所引用的教材原文。请你在阅读之后，以"追问"的方式提出你仍然不明白的问题。要求：

1. 不要复述解析内容，不要说自己"理解了"——直接提问
2. 追问要具体：引用解析中的原句，指出"这句话让我想到什么疑问"。**解析给出的定义和结论，去下面给的教材原文里核实。如果解析说"教材将X定义为Y"，但原文里根本没提X或者用的是另一个词——这就是你需要追问的地方。**
3. 追问要真实：像一个真的初学者那样，挑战解析里没说清楚的地方
   - 概念之间的区别到底在哪？（比如"A和B都是拆分交易，那到底怎么区分？"）
   - 解析用的判断标准能不能推广？（比如"这道题的判断依据是金额大小，下一题我还能用同样的标准吗？"）
   - 教材原文和你看到的案例之间是什么关系？（比如"教材只说类似，案例里的数字能不能当判断标准？"）
   - 解析说教材讲了什么，你去下面的教材原文里找——找到了就更好理解，找不到也可以问。
4. 禁止夸解析、禁止帮解析补充它没说清楚的内容
5. 有真实的疑问就提，没有不用硬凑。真的理解了就说"没有疑问"。

---

## 题目

{stem}

选项：
{opt_text}

## 答案解析

答案：{answer}

【考点】
{exam_point}

【核心解析】
{core}

教材原句：{source_quote if source_quote else "（无）"}

【错误项分析】
{err_text}

【易错提醒】
{easy if easy else "（无）"}

【解析引用的教材原文（供核对）】
{evidence_text}
"""


def call_student_llm(client: Any, prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=4000,
        timeout=120.0,
    )
    return (response.choices[0].message.content or "").strip()


def classify(question_id: str, response: str, output_dir: Path) -> None:
    """写出模拟学生反馈并打印摘要。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / f"{question_id}_student_review.md"
    md_path.write_text(
        f"# 模拟学生反馈 — {question_id}\n\n{response}\n",
        encoding="utf-8",
    )

    low = response.casefold()
    has_doubt = any(
        keyword in low
        for keyword in ("不明白", "不清楚", "不理解", "疑问", "困惑", "没看懂", "不懂")
    )
    if has_doubt:
        print(f"[{question_id}] [有疑问] 模拟学生未完全理解")
    else:
        print(f"[{question_id}] [通过] 模拟学生表示理解")

    print(f"  反馈保存至: {md_path}")


def _process_one(path: Path, client: Any, review_dir: Path) -> tuple[str, str]:
    result = load_question(path)
    qid = result.get("question_id", path.stem.removeprefix("q_"))
    if "generated_explanation" not in result:
        return qid, "skip"
    prompt = build_student_prompt(result)
    response = call_student_llm(client, prompt)
    classify(qid, response, review_dir)
    return qid, "done"


def main() -> None:
    parser = argparse.ArgumentParser(description="模拟学生：检测解析是否能让小白看懂")
    parser.add_argument("--output-dir", default=str(PHASE4 / "output" / "rerun_4q"))
    parser.add_argument("--question-id", action="append", default=[])
    parser.add_argument("--review-dir", default=str(HERE / "reviews"))
    parser.add_argument("--concurrency", type=int, default=1)
    args = parser.parse_args()

    api_key, base_url = get_api_config()
    from openai import OpenAI

    output_dir = Path(args.output_dir)
    question_dir = output_dir / "questions"
    if not question_dir.exists():
        raise RuntimeError(f"questions 目录不存在: {question_dir}")

    if args.question_id:
        files = [question_dir / f"q_{qid}.json" for qid in args.question_id]
        missing = [str(f) for f in files if not f.exists()]
        if missing:
            raise RuntimeError("指定题号输出不存在: " + ", ".join(missing))
    else:
        files = sorted(question_dir.glob("q_*.json"))

    review_dir = Path(args.review_dir)
    if args.concurrency <= 1:
        client = OpenAI(api_key=api_key, base_url=base_url)
        for i, path in enumerate(files, start=1):
            qid, status = _process_one(path, client, review_dir)
            print(f"[{i}/{len(files)}] {qid} | {status}")
    else:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            future_map = {}
            for path in files:
                client = OpenAI(api_key=api_key, base_url=base_url)
                future = executor.submit(_process_one, path, client, review_dir)
                future_map[future] = path
            for i, future in enumerate(as_completed(future_map), start=1):
                path = future_map[future]
                try:
                    qid, status = future.result()
                    print(f"[{i}/{len(files)}] {qid} | {status}")
                except Exception as exc:
                    qid = path.stem.removeprefix("q_")
                    print(f"[{i}/{len(files)}] {qid} | ERROR: {exc}")


if __name__ == "__main__":
    main()
