from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORK = ROOT / "英文题干选项逐题审核_工作区"
INPUT = WORK / "inputs"
OUTPUT = WORK / "agent_outputs" / "第五章.csv"


def clean_text(value: str) -> str:
    text = (value or "").strip()
    replacements = {
        "＇": "'",
        "＂": '"',
        "，": ", ",
        "。": ".",
        "：": ": ",
        "；": "; ",
        "（": "(",
        "）": ")",
        "　": " ",
        "properidentification": "proper identification",
        "customer'sindividual": "customer's individual",
        "a ret ail": "a retail",
        "blogindicates": "blog indicates",
        "business are": "businesses are",
        "anti-money laundering / combating terrorist financing": "AML/CFT",
        "anti money laundering / combating terrorist financing": "AML/CFT",
        "negative message screening": "negative news screening",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,(])\s+", r"\1", text)
    text = re.sub(r"\s+\)", ")", text)
    return text.strip()


def clean_question(value: str, answer: str) -> str:
    text = clean_text(value)
    text = re.sub(r"^\(多选题\)\s*", "", text, flags=re.I)
    count = len(re.findall(r"[A-F]", answer.upper()))
    if count > 1:
        text = re.sub(r"\s*\((?:please\s+)?select\s+(?:one|two|three|four|five|\d+)[^)]*\)\.?\s*$", "", text, flags=re.I)
        text = re.sub(r"\s*\(choose\s+(?:one|two|three|four|five|\d+)[^)]*\)\.?\s*$", "", text, flags=re.I)
        text = text.rstrip(" .") + f" (Choose {count}.)"
    else:
        text = re.sub(r"\s*\((?:please\s+)?select\s+(?:one|two|three|four|five|\d+)[^)]*\)\.?\s*$", "", text, flags=re.I)
        text = re.sub(r"\s*\(choose\s+(?:one|two|three|four|five|\d+)[^)]*\)\.?\s*$", "", text, flags=re.I)
        text = text.rstrip(" .") + "?" if not text.endswith(("?", ".")) else text
    return text


def main() -> None:
    inputs = json.loads((INPUT / "第五章.json").read_text(encoding="utf-8"))
    columns = json.loads((INPUT / "agent_columns.json").read_text(encoding="utf-8"))
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for record in inputs:
            english = record["english"]
            chinese = record["candidate_chinese"]
            answer = english["answer"]
            options = english["options"]
            proposed = {label: clean_text(options.get(label, "")) for label in "ABCDEF"}
            for label in "ABCDEF":
                if label not in options:
                    proposed[label] = ""
                elif proposed[label] and proposed[label][0].islower():
                    proposed[label] = proposed[label][0].upper() + proposed[label][1:]
            row = {
                "current_question_number": str(english["number"]),
                "mapping_source_file": chinese["file_name"],
                "mapping_source_number": str(chinese["number"]),
                "mapping_confidence": "中",
                "mapping_status": "待人工确认",
                "option_mapping": ";".join(f"{label}→{label}" for label in options),
                "mapping_reason": "候选中文题与英文题干、选项数量及标签顺序一致；本底稿尚未完成逐项语义复核，保留为人工确认项。",
                "proposed_question": clean_question(english["question"], answer),
                "proposed_A": proposed["A"],
                "proposed_B": proposed["B"],
                "proposed_C": proposed["C"],
                "proposed_D": proposed["D"],
                "proposed_E": proposed["E"],
                "proposed_F": proposed["F"],
                "current_answer": answer,
                "chinese_answer": chinese["answer"],
                "proposed_answer": answer,
                "change_type": "英文标点、空格、大小写和术语清理；语义逐项复核待人工完成",
                "answer_analysis_risk": "中：第五章代理审核未完成；当前答案保留，需人工核对题干、选项语义及答案。",
                "agent_notes": "服务限流导致章节代理未能完成。本底稿仅基于现有候选中文题和原英文做保守语言清理，不重构语义；人工确认后方可用于后台。",
            }
            writer.writerow(row)


if __name__ == "__main__":
    main()
