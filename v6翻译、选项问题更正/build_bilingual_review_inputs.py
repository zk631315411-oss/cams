from __future__ import annotations

import csv
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parent
ENGLISH_DIR = ROOT / "英文版解析_中文版覆盖"
CHINESE_DIR = ROOT / "中文版题目解析"
MAPPING_PATH = ENGLISH_DIR / "解析覆盖核对报告.csv"
WORK_DIR = ROOT / "英文题干选项逐题审核_工作区"
INPUT_DIR = WORK_DIR / "inputs"
OUTPUT_DIR = WORK_DIR / "agent_outputs"


CHAPTER_FILES = {
    "第二章": "英文版第二章.docx",
    "第三章": "英文版第三章.docx",
    "第四章": "英文版第四章.docx",
    "第五章": "英文版第五章.docx",
    "第六章": "英文版第六章.docx",
}


AGENT_COLUMNS = [
    "current_question_number",
    "mapping_source_file",
    "mapping_source_number",
    "mapping_confidence",
    "mapping_status",
    "option_mapping",
    "mapping_reason",
    "proposed_question",
    "proposed_A",
    "proposed_B",
    "proposed_C",
    "proposed_D",
    "proposed_E",
    "proposed_F",
    "current_answer",
    "chinese_answer",
    "proposed_answer",
    "change_type",
    "answer_analysis_risk",
    "agent_notes",
]


@dataclass
class Question:
    file_name: str
    chapter: str
    number: int
    question: str
    options: dict[str, str]
    answer: str
    analysis: str


def strip_question_number(text: str) -> str:
    return re.sub(r"^\d+[.．、]\s*", "", text.strip())


def strip_option_label(text: str) -> tuple[str, str] | None:
    match = re.match(r"^([A-Z])[.．、]\s*(.*)$", text.strip(), re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return match.group(1).upper(), match.group(2).strip()


def normalize_answer(text: str) -> str:
    value = re.split(r"[:：]", text, maxsplit=1)[-1]
    return "".join(re.findall(r"[A-Z]", value.upper()))


def parse_document(path: Path, chapter: str) -> list[Question]:
    paragraphs = [paragraph.text.strip() for paragraph in Document(path).paragraphs]
    answer_indexes = [
        index for index, text in enumerate(paragraphs) if re.match(r"^答案\s*[:：]", text)
    ]
    starts: list[int] = []
    previous_answer = -1
    for answer_index in answer_indexes:
        option_a_indexes = [
            index
            for index in range(previous_answer + 1, answer_index)
            if re.match(r"^A[.．、]", paragraphs[index], re.IGNORECASE)
        ]
        if not option_a_indexes:
            raise ValueError(f"Missing option A before answer {answer_index} in {path}")
        question_indexes = [
            index
            for index in range(previous_answer + 1, option_a_indexes[-1])
            if re.match(r"^\d+[.．、]", paragraphs[index])
        ]
        if not question_indexes:
            raise ValueError(f"Missing question before answer {answer_index} in {path}")
        starts.append(question_indexes[-1])
        previous_answer = answer_index

    questions: list[Question] = []
    for offset, (start, answer_index) in enumerate(zip(starts, answer_indexes), start=1):
        end = starts[offset] if offset < len(starts) else len(paragraphs)
        options = {}
        for text in paragraphs[start + 1 : answer_index]:
            parsed = strip_option_label(text)
            if parsed:
                label, value = parsed
                options[label] = value
        analysis = "\n".join(text for text in paragraphs[answer_index + 1 : end] if text)
        questions.append(
            Question(
                file_name=path.name,
                chapter=chapter,
                number=offset,
                question=strip_question_number(paragraphs[start]),
                options=options,
                answer=normalize_answer(paragraphs[answer_index]),
                analysis=analysis,
            )
        )
    return questions


def load_mapping() -> dict[tuple[str, int], dict[str, str]]:
    with MAPPING_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {(row["英文文件"], int(row["英文题号"])): row for row in rows}


def main() -> None:
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    INPUT_DIR.mkdir(parents=True)
    OUTPUT_DIR.mkdir()

    chinese_questions: list[Question] = []
    for path in sorted(CHINESE_DIR.glob("*.docx")):
        chapter = path.stem
        chinese_questions.extend(parse_document(path, chapter))
    chinese_index = {(question.file_name, question.number): question for question in chinese_questions}

    mapping = load_mapping()
    english_by_chapter: dict[str, list[dict]] = {}
    for chapter, file_name in CHAPTER_FILES.items():
        questions = parse_document(ENGLISH_DIR / file_name, chapter)
        records = []
        for question in questions:
            seed = mapping[(question.file_name, question.number)]
            source_file = seed["中文来源文件"]
            source_number = int(seed["中文来源题号"]) if seed["中文来源题号"] else None
            source = chinese_index.get((source_file, source_number)) if source_number else None
            records.append(
                {
                    "english": asdict(question),
                    "seed_mapping": {
                        "source_file": source_file,
                        "source_number": source_number,
                        "status": seed["状态"],
                        "note": seed["备注"],
                    },
                    "candidate_chinese": asdict(source) if source else None,
                }
            )
        english_by_chapter[chapter] = records
        (INPUT_DIR / f"{chapter}.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    (INPUT_DIR / "中文题库_全部.json").write_text(
        json.dumps([asdict(question) for question in chinese_questions], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (INPUT_DIR / "agent_columns.json").write_text(
        json.dumps(AGENT_COLUMNS, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (INPUT_DIR / "terminology.json").write_text(
        json.dumps(
            {
                "有意忽视": "willful blindness",
                "通汇账户": "payable-through account (PTA)",
                "委托银行": "respondent bank",
                "代理银行": "correspondent bank",
                "连环代理/巢状交易": "nesting",
                "货币服务企业": "money services business (MSB)",
                "银行保密法": "Bank Secrecy Act (BSA)",
                "可疑活动报告": "suspicious activity report (SAR)",
                "可疑交易报告": "suspicious transaction report (STR)",
                "金融情报机构": "financial intelligence unit (FIU)",
                "政治公众人物": "politically exposed person (PEP)",
                "反洗钱/反恐融资": "AML/CFT",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    manifest = {
        "english_counts": {chapter: len(records) for chapter, records in english_by_chapter.items()},
        "chinese_count": len(chinese_questions),
        "total_english": sum(len(records) for records in english_by_chapter.values()),
        "agent_output_columns": AGENT_COLUMNS,
    }
    (INPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
