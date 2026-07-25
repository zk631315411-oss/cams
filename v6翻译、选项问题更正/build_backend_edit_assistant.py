from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORK_DIR = ROOT / "英文题干选项逐题审核_工作区"
INPUT_DIR = WORK_DIR / "inputs"
AGENT_DIR = WORK_DIR / "agent_outputs"
OUTPUT_PATH = ROOT / "题库后台半自动审核数据.json"
CHAPTERS = ["第二章", "第三章", "第四章", "第五章", "第六章"]
OPTION_LABELS = list("ABCDEF")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def main() -> None:
    items = []
    summary = Counter()
    for chapter in CHAPTERS:
        inputs = read_json(INPUT_DIR / f"{chapter}.json")
        source_by_number = {
            int(record["english"]["number"]): record["english"] for record in inputs
        }
        for row in read_csv(AGENT_DIR / f"{chapter}.csv"):
            number = int(row["current_question_number"])
            source = source_by_number[number]
            original_options = {
                label: source["options"][label]
                for label in OPTION_LABELS
                if label in source["options"]
            }
            proposed_options = {
                label: row[f"proposed_{label}"] for label in original_options
            }
            changed = (
                row["proposed_question"].strip() != source["question"].strip()
                or any(
                    proposed_options[label].strip() != original_options[label].strip()
                    for label in original_options
                )
            )
            eligible = row["mapping_confidence"] == "高" and changed
            summary["total"] += 1
            summary["changed"] += int(changed)
            summary["eligible"] += int(eligible)
            summary["manual"] += int(changed and not eligible)
            summary["unchanged"] += int(not changed)
            items.append(
                {
                    "key": f"{chapter}-{number}",
                    "chapter": chapter,
                    "number": number,
                    "confidence": row["mapping_confidence"],
                    "mapping_status": row["mapping_status"],
                    "changed": changed,
                    "eligible": eligible,
                    "original": {
                        "question": source["question"],
                        "options": original_options,
                        "answer": source["answer"],
                    },
                    "proposed": {
                        "question": row["proposed_question"],
                        "options": proposed_options,
                        "answer": row["proposed_answer"],
                    },
                    "risk": row["answer_analysis_risk"],
                    "notes": row["agent_notes"],
                }
            )

    payload = {
        "meta": {
            "format": "cams-qbank-review-v1",
            "qbankId": 138,
            "qbankName": "英文版CAMS真题（V6考纲）",
            "total": summary["total"],
            "changed": summary["changed"],
            "eligible": summary["eligible"],
            "manual": summary["manual"],
            "unchanged": summary["unchanged"],
            "safety": "Only high-confidence changed items are eligible for assisted editing.",
        },
        "items": items,
    }
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload["meta"], ensure_ascii=False))
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
