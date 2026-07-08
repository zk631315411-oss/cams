from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
WORK_DIR = SCRIPT_DIR.parent
APP_DIR = WORK_DIR.parent
DATA_DIR = APP_DIR / "data" / "teaching_assets"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def compact(text: Any, limit: int = 260) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def index_by_id(items: list[dict[str, Any]], key: str = "id") -> dict[str, dict[str, Any]]:
    return {str(item[key]): item for item in items if item.get(key)}


def load_data(data_dir: Path) -> dict[str, Any]:
    questions = read_json(data_dir / "questions.json").get("questions", [])
    qa_records = read_json(data_dir / "qa.json").get("records", [])
    qa_bindings = read_json(data_dir / "qa_bindings.json").get("bindings", [])
    return {
        "questions_by_id": index_by_id(questions),
        "qa_by_id": index_by_id(qa_records),
        "qa_bindings": qa_bindings,
    }


def question_options(question: dict[str, Any]) -> list[dict[str, str]]:
    options = question.get("options") or {}
    if isinstance(options, dict):
        return [{"option": key, "text": value} for key, value in sorted(options.items())]
    if isinstance(options, list):
        result = []
        for item in options:
            if isinstance(item, dict):
                result.append({"option": item.get("option") or item.get("label") or "", "text": item.get("text") or ""})
        return result
    return []


def build_qa_by_question(bindings: list[dict[str, Any]], qa_by_id: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for binding in bindings:
        qid = binding.get("bound_question_id")
        qa_id = binding.get("qa_id")
        if not qid or not qa_id:
            continue
        record = qa_by_id.get(qa_id, {})
        grouped[qid].append(
            {
                "qa_id": qa_id,
                "question": compact(record.get("question") or binding.get("qa_question"), 320),
                "answer": compact(record.get("answer"), 120),
                "core_point": compact(record.get("core_point"), 320),
                "match_score": binding.get("match_score"),
                "inherited_card_ids": binding.get("inherited_card_ids") or [],
            }
        )
    return grouped


def summarize_card(card_rows: list[dict[str, Any]], card_score: dict[str, Any] | None) -> dict[str, Any]:
    first = card_rows[0]
    option_refs = []
    for row in sorted(card_rows, key=lambda item: (item.get("option") or "", not item.get("is_correct_answer"))):
        option_refs.append(
            {
                "option": row.get("option"),
                "option_text": compact(row.get("option_text"), 140),
                "is_correct_answer": row.get("is_correct_answer"),
                "support_type": row.get("support_type"),
                "evidence_status": row.get("evidence_status"),
                "signal_score": row.get("signal_score"),
                "signal_reasons": row.get("signal_reasons"),
                "evidence_reason": compact(row.get("evidence_reason"), 220),
                "option_explanation": compact(row.get("option_explanation"), 260),
                "common_trap": compact(row.get("common_trap"), 220),
            }
        )

    return {
        "card_id": first.get("card_id"),
        "card_type": first.get("card_type"),
        "chapter_path": first.get("chapter_path"),
        "knowledge": compact(first.get("card_knowledge"), 260),
        "quote": compact(first.get("card_quote"), 320),
        "source_line_start": first.get("source_line_start"),
        "source_line_end": first.get("source_line_end"),
        "aggregate_score": (card_score or {}).get("final_score"),
        "aggregate_role_hint": (card_score or {}).get("role_hint"),
        "aggregate_reasons": (card_score or {}).get("top_reasons", [])[:5],
        "option_refs": option_refs,
    }


def build_packs(work_dir: Path, data_dir: Path) -> list[dict[str, Any]]:
    data = load_data(data_dir)
    rows = read_jsonl(work_dir / "outputs" / "evidence_signals.jsonl")
    card_scores_payload = read_json(work_dir / "outputs" / "evidence_card_scores.json")
    card_scores = {item["card_id"]: item for item in card_scores_payload.get("cards", [])}
    qa_by_question = build_qa_by_question(data["qa_bindings"], data["qa_by_id"])

    rows_by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("question_id"):
            rows_by_question[row["question_id"]].append(row)

    packs = []
    for qid, qrows in sorted(rows_by_question.items()):
        question = data["questions_by_id"].get(qid, {})
        card_rows_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in qrows:
            card_rows_by_id[row["card_id"]].append(row)

        candidate_cards = [
            summarize_card(card_rows, card_scores.get(cid))
            for cid, card_rows in sorted(
                card_rows_by_id.items(),
                key=lambda item: (-(card_scores.get(item[0], {}).get("final_score") or 0), item[0]),
            )
        ]

        packs.append(
            {
                "question_id": qid,
                "section": question.get("section") or qrows[0].get("section"),
                "stem": question.get("stem") or qrows[0].get("stem"),
                "answer": question.get("answer") or qrows[0].get("answer"),
                "options": question_options(question),
                "question_explanation": compact(question.get("explanation"), 1200),
                "qa_records": qa_by_question.get(qid, []),
                "candidate_cards": candidate_cards,
                "instruction": {
                    "goal": "在候选证据卡中判断哪些承载考点，哪些只是辅助或背景，并给出可展示的考点标题。",
                    "constraints": [
                        "只能使用 candidate_cards 中出现的 card_id。",
                        "不能新增教材依据。",
                        "不要把每一张句卡都当成独立考点；能合并的知识单元需要合并。",
                        "需要区分 core、supporting、background、trap。",
                    ],
                },
            }
        )

    return packs


def render_sample_report(packs: list[dict[str, Any]]) -> str:
    lines = [
        "# LLM 判断输入包样例",
        "",
        f"- 题目包数量：{len(packs)}",
        "",
    ]
    for pack in packs[:5]:
        lines += [
            f"## {pack['question_id']} {pack.get('stem') or ''}",
            "",
            f"- 答案：{pack.get('answer') or ''}",
            f"- 候选卡：{len(pack.get('candidate_cards') or [])}",
            f"- 答疑：{len(pack.get('qa_records') or [])}",
            "",
        ]
        for card in (pack.get("candidate_cards") or [])[:4]:
            lines += [
                f"### {card['card_id']} | {card.get('aggregate_role_hint')} | {card.get('aggregate_score')} 分",
                "",
                f"- 类型：{card.get('card_type') or ''}",
                f"- 章节：{card.get('chapter_path') or ''}",
                f"- 知识：{card.get('knowledge') or ''}",
                "",
            ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build per-question LLM input packs for exam point role judging.")
    parser.add_argument("--work-dir", type=Path, default=WORK_DIR)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()

    packs = build_packs(args.work_dir, args.data_dir)
    outputs_dir = args.work_dir / "outputs"
    reports_dir = args.work_dir / "reports"

    write_jsonl(outputs_dir / "llm_question_packs.jsonl", packs)
    write_json(outputs_dir / "llm_question_packs.sample.json", {"packs": packs[:3]})
    (reports_dir / "llm_question_pack_sample.md").write_text(render_sample_report(packs), encoding="utf-8")

    print(f"wrote {len(packs)} question packs")
    print(outputs_dir / "llm_question_packs.jsonl")


if __name__ == "__main__":
    main()
