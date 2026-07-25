from __future__ import annotations

import csv
import re
import shutil
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parent
CHINESE_DIR = ROOT / "中文版题目解析"
ENGLISH_DIR = ROOT / "英文版解析"
OUTPUT_DIR = ROOT / "英文版解析_中文版覆盖"


MANUAL_MATCHES = {
    ("英文版第三章.docx", 53): ("第三章.docx", 120),
    ("英文版第三章.docx", 61): ("第三章.docx", 27),
    ("英文版第二章.docx", 58): ("第二章.docx", 32),
    ("英文版第二章.docx", 92): ("第二章.docx", 49),
    ("英文版第二章.docx", 94): ("第二章.docx", 52),
    ("英文版第五章.docx", 1): ("第五章.docx", 85),
    ("英文版第五章.docx", 6): ("第五章.docx", 80),
    ("英文版第五章.docx", 56): ("第五章.docx", 48),
    ("英文版第六章.docx", 6): ("第六章.docx", 6),
    ("英文版第四章.docx", 84): ("第四章.docx", 163),
    ("英文版第四章.docx", 199): ("第四章.docx", 131),
    ("英文版第四章.docx", 201): ("第四章.docx", 79),
    ("英文版第四章.docx", 203): ("第四章.docx", 197),
    ("英文版第四章.docx", 204): ("第四章.docx", 133),
    ("英文版第四章.docx", 205): ("第四章.docx", 163),
    ("英文版第四章.docx", 208): ("第四章.docx", 205),
}


@dataclass
class Question:
    number: int
    question: str
    answer: str
    option_count: int
    start_index: int
    answer_index: int
    end_index: int
    analysis_elements: list


def element_text(element) -> str:
    # BaseOxmlElement.itertext() repeats run content in python-docx; read Word
    # text nodes directly so matching uses the same text users see in Word.
    return "".join(node.text or "" for node in element.xpath(".//w:t")).strip()


def parse_questions(document: Document) -> list[Question]:
    body = document.element.body
    children = list(body)
    texts = [element_text(child) if child.tag == qn("w:p") else "" for child in children]
    answer_indexes = [
        index
        for index, text in enumerate(texts)
        if re.match(r"^(答案|Answer)\s*[:：]", text, re.IGNORECASE)
    ]

    starts: list[int] = []
    previous_answer = -1
    for answer_index in answer_indexes:
        option_a_indexes = [
            index
            for index in range(previous_answer + 1, answer_index)
            if re.match(r"^A[.．、]", texts[index], re.IGNORECASE)
        ]
        if not option_a_indexes:
            raise ValueError(f"Cannot find option A before answer at body index {answer_index}")
        option_a_index = option_a_indexes[-1]
        question_indexes = [
            index
            for index in range(previous_answer + 1, option_a_index)
            if re.match(r"^\d+[.．、]", texts[index])
        ]
        if not question_indexes:
            raise ValueError(f"Cannot find question before answer at body index {answer_index}")
        starts.append(question_indexes[-1])
        previous_answer = answer_index

    questions: list[Question] = []
    for offset, (start_index, answer_index) in enumerate(zip(starts, answer_indexes), start=1):
        end_index = starts[offset] if offset < len(starts) else len(children) - 1
        option_count = sum(
            bool(re.match(r"^[A-Z][.．、]", texts[index], re.IGNORECASE))
            for index in range(start_index + 1, answer_index)
        )
        answer = re.split(r"[:：]", texts[answer_index], maxsplit=1)[-1]
        questions.append(
            Question(
                number=offset,
                question=texts[start_index],
                answer=re.sub(r"\s+", "", answer),
                option_count=option_count,
                start_index=start_index,
                answer_index=answer_index,
                end_index=end_index,
                analysis_elements=children[answer_index + 1 : end_index],
            )
        )
    return questions


def normalized_analysis(question: Question) -> str:
    text = "".join(element_text(element) for element in question.analysis_elements)
    text = re.sub(r"^解析\s*[:：]?", "", text)
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text).lower()


def assert_portable(elements: list, label: str) -> None:
    relationship_attributes = {
        qn("r:id"),
        qn("r:embed"),
        qn("r:link"),
    }
    for element in elements:
        if element.tag == qn("w:tbl") or element.xpath(".//w:drawing | .//w:pict"):
            raise ValueError(f"{label} contains a table or drawing and requires relationship-aware copying")
        for node in element.iter():
            if relationship_attributes.intersection(node.attrib):
                raise ValueError(f"{label} contains an external relationship")


def replace_analysis(document: Document, target: Question, source: Question) -> None:
    assert_portable(source.analysis_elements, f"source question {source.number}")
    body = document.element.body
    insertion_point = list(body)[target.end_index]
    for element in target.analysis_elements:
        body.remove(element)
    for element in source.analysis_elements:
        insertion_point.addprevious(deepcopy(element))


def load_documents(directory: Path) -> dict[str, Document]:
    return {path.name: Document(path) for path in directory.glob("*.docx")}


def main() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir()

    chinese_documents = load_documents(CHINESE_DIR)
    chinese_questions = {
        name: parse_questions(document) for name, document in chinese_documents.items()
    }
    chinese_by_analysis: dict[str, list[tuple[str, Question]]] = {}
    for name, questions in chinese_questions.items():
        for question in questions:
            chinese_by_analysis.setdefault(normalized_analysis(question), []).append((name, question))

    report_rows: list[dict[str, str | int]] = []
    totals = {"already_same": 0, "replaced": 0, "unmatched": 0}

    for source_path in sorted(ENGLISH_DIR.glob("*.docx")):
        output_path = OUTPUT_DIR / source_path.name
        shutil.copy2(source_path, output_path)
        document = Document(output_path)
        original_questions = parse_questions(document)

        replacements: list[tuple[Question, str, Question]] = []
        for target in original_questions:
            key = (source_path.name, target.number)
            existing_matches = chinese_by_analysis.get(normalized_analysis(target), [])
            if existing_matches:
                source_name, matched = existing_matches[0]
                status = "already_same"
                report_status = "已一致"
                note = "解析内容已与中文版一致"
                totals[status] += 1
            elif key in MANUAL_MATCHES:
                source_name, source_number = MANUAL_MATCHES[key]
                matched = chinese_questions[source_name][source_number - 1]
                replacements.append((target, source_name, matched))
                status = "replaced"
                report_status = "已覆盖"
                note = "按题干、选项和答案确认对应后覆盖"
                totals[status] += 1
            else:
                source_name = ""
                matched = None
                status = "unmatched"
                report_status = "未匹配"
                note = "中文版题库中未找到可确认的同题，保留原解析"
                totals[status] += 1

            report_rows.append(
                {
                    "英文文件": source_path.name,
                    "英文题号": target.number,
                    "英文题干": target.question,
                    "状态": report_status,
                    "中文来源文件": source_name,
                    "中文来源题号": matched.number if matched else "",
                    "中文来源题干": matched.question if matched else "",
                    "备注": note,
                }
            )

        # Work from the end so body indexes from the original parse stay valid.
        for target, source_name, matched in reversed(replacements):
            replace_analysis(document, target, matched)
        document.save(output_path)

    report_path = OUTPUT_DIR / "解析覆盖核对报告.csv"
    with report_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(report_rows[0]))
        writer.writeheader()
        writer.writerows(report_rows)

    print(
        f"already_same={totals['already_same']} "
        f"replaced={totals['replaced']} unmatched={totals['unmatched']}"
    )
    print(report_path)


if __name__ == "__main__":
    main()
