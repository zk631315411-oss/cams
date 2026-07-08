from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


SCRIPT_DIR = Path(__file__).resolve().parent
WORK_DIR = SCRIPT_DIR.parent
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_SAMPLE_IDS = ["2.1_4", "2.1_1", "2.1_2", "2.2_15", "2.2_9"]


SYSTEM_PROMPT = """你是 CAMS 考试教研助理。你只能根据输入中给出的题目、选项、解析、学生答疑和候选证据卡做判断。
不要新增不存在的证据卡，不要编造教材依据。输出必须是合法 JSON，不要输出 Markdown。"""


USER_PROMPT_TEMPLATE = """请判断这道题的候选证据卡如何形成考点。

要求：
1. 判断这道题真正考查的知识点。
2. 只在 candidate_cards 中选择 card_id。
3. 区分正式考点和易错辨析。正式考点进入 exam_points，易错辨析进入 trap_notes。
4. 不要一张句卡生成一个考点；同一知识单元应合并。
5. 考点标题要像老师整理的知识点，不要直接照抄选项。
6. 每道题通常只输出 1 个正式考点；只有题目确实同时考查两个独立知识单元时，才输出多个正式考点。
7. 正式考点应优先来自正确选项的 direct 证据。只用于排除错误选项的卡，不得进入 exam_points 的 core_card_ids。
8. direct 证据不必全部放入 core_card_ids；最核心的放 core_card_ids，补充场景或例证放 supporting_card_ids。
9. 易错辨析不是正式考点。处置/离析/融合、目标/手段、定义/例外等混淆说明应放入 trap_notes。

输出 JSON 格式：
{{
  "question_id": "",
  "exam_intent": "",
  "exam_points": [
    {{
      "title": "",
      "point_type": "core | frequent | textbook_note",
      "core_card_ids": [],
      "supporting_card_ids": [],
      "background_card_ids": [],
      "reason": "",
      "confidence": "high | medium | low"
    }}
  ],
  "trap_notes": [
    {{
      "title": "",
      "trap_card_ids": [],
      "related_core_card_ids": [],
      "reason": "",
      "confidence": "high | medium | low"
    }}
  ],
  "rejected_cards": [
    {{
      "card_id": "",
      "reason": ""
    }}
  ]
}}

题目输入：
{pack_json}
"""


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_env(work_dir: Path) -> None:
    load_dotenv(work_dir / ".env")


def env_value(name: str, fallback: str | None = None) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    return fallback


def client_from_env() -> tuple[OpenAI, str]:
    api_key = (
        env_value("DEEPSEEK_API_KEY")
        or env_value("DS_API_KEY")
        or env_value("DS_KEY")
        or env_value("OPENAI_API_KEY")
    )
    if not api_key:
        raise RuntimeError(
            "缺少 DEEPSEEK_API_KEY / DS_API_KEY / DS_KEY。可以设置环境变量，或在 考点确认/.env 中填写。"
        )

    base_url = env_value("DEEPSEEK_BASE_URL") or env_value("OPENAI_BASE_URL") or DEFAULT_BASE_URL
    model = env_value("DEEPSEEK_MODEL") or env_value("OPENAI_MODEL") or DEFAULT_MODEL
    return OpenAI(api_key=api_key, base_url=base_url), model


def select_packs(
    packs: list[dict[str, Any]],
    question_ids: list[str] | None,
    limit: int,
) -> list[dict[str, Any]]:
    by_id = {pack["question_id"]: pack for pack in packs}
    selected: list[dict[str, Any]] = []

    ids = question_ids or DEFAULT_SAMPLE_IDS
    for qid in ids:
        pack = by_id.get(qid)
        if pack:
            selected.append(pack)

    if question_ids:
        return selected[:limit] if limit else selected

    if limit and len(selected) >= limit:
        return selected[:limit]

    seen = {pack["question_id"] for pack in selected}
    for pack in packs:
        if pack["question_id"] not in seen:
            selected.append(pack)
        if limit and len(selected) >= limit:
            break

    return selected


def extract_json(text: str) -> dict[str, Any]:
    value = text.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value)
        value = re.sub(r"\s*```$", "", value)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        start = value.find("{")
        end = value.rfind("}")
        if start >= 0 and end > start:
            return json.loads(value[start : end + 1])
        raise


def candidate_card_ids(pack: dict[str, Any]) -> set[str]:
    return {card["card_id"] for card in pack.get("candidate_cards", []) if card.get("card_id")}


def correct_direct_card_ids(pack: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for card in pack.get("candidate_cards", []):
        cid = card.get("card_id")
        if not cid:
            continue
        for ref in card.get("option_refs") or []:
            if ref.get("is_correct_answer") and ref.get("support_type") == "direct":
                ids.add(cid)
                break
    return ids


def validate_result(pack: dict[str, Any], result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    allowed = candidate_card_ids(pack)
    correct_direct = correct_direct_card_ids(pack)

    if result.get("question_id") != pack.get("question_id"):
        errors.append("question_id mismatch")

    if "exam_points" not in result:
        errors.append("missing exam_points")
    if "trap_notes" not in result:
        errors.append("missing trap_notes")

    for idx, point in enumerate(result.get("exam_points") or []):
        core_ids = point.get("core_card_ids") or []
        if core_ids and correct_direct and not any(cid in correct_direct for cid in core_ids):
            errors.append(f"exam_points[{idx}].core_card_ids has no correct-option direct evidence")
        if point.get("point_type") == "trap":
            errors.append(f"exam_points[{idx}] uses forbidden point_type trap")
        for field in ["core_card_ids", "supporting_card_ids", "background_card_ids"]:
            for cid in point.get(field) or []:
                if cid not in allowed:
                    errors.append(f"exam_points[{idx}].{field} contains unknown card_id {cid}")

    for idx, note in enumerate(result.get("trap_notes") or []):
        for field in ["trap_card_ids", "related_core_card_ids"]:
            for cid in note.get(field) or []:
                if cid not in allowed:
                    errors.append(f"trap_notes[{idx}].{field} contains unknown card_id {cid}")

    for idx, rejected in enumerate(result.get("rejected_cards") or []):
        cid = rejected.get("card_id")
        if cid and cid not in allowed:
            errors.append(f"rejected_cards[{idx}] contains unknown card_id {cid}")

    return errors


def shrink_pack_for_prompt(pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "question_id": pack.get("question_id"),
        "stem": pack.get("stem"),
        "answer": pack.get("answer"),
        "options": pack.get("options"),
        "question_explanation": pack.get("question_explanation"),
        "qa_records": pack.get("qa_records"),
        "candidate_cards": pack.get("candidate_cards"),
    }


def judge_pack(client: OpenAI, model: str, pack: dict[str, Any], temperature: float) -> tuple[dict[str, Any], str]:
    prompt = USER_PROMPT_TEMPLATE.format(
        pack_json=json.dumps(shrink_pack_for_prompt(pack), ensure_ascii=False, indent=2)
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    text = response.choices[0].message.content or ""
    return extract_json(text), text


def load_done(path: Path) -> set[str]:
    if not path.exists():
        return set()
    done = set()
    for row in read_jsonl(path):
        if row.get("question_id") and row.get("status") == "ok":
            done.add(row["question_id"])
    return done


def render_report(results: list[dict[str, Any]]) -> str:
    lines = ["# LLM 考点角色判断样例结果", ""]
    ok_rows = [row for row in results if row.get("status") == "ok"]
    fail_rows = [row for row in results if row.get("status") != "ok"]
    lines += [f"- 成功：{len(ok_rows)}", f"- 失败：{len(fail_rows)}", ""]

    for row in ok_rows:
        result = row.get("result") or {}
        lines += [
            f"## {row.get('question_id')} {result.get('exam_intent') or ''}",
            "",
        ]
        exam_points = result.get("exam_points")
        if exam_points is None and result.get("points") is not None:
            exam_points = result.get("points")
        for point in exam_points or []:
            lines += [
                f"### {point.get('title') or ''}",
                "",
                f"- 类型：{point.get('point_type') or ''}",
                f"- 主卡：{', '.join(point.get('core_card_ids') or [])}",
                f"- 辅助：{', '.join(point.get('supporting_card_ids') or [])}",
                f"- 背景：{', '.join(point.get('background_card_ids') or [])}",
                f"- 置信度：{point.get('confidence') or ''}",
                f"- 理由：{point.get('reason') or ''}",
                "",
            ]
        trap_notes = result.get("trap_notes") or []
        if trap_notes:
            lines.append("易错辨析：")
            for note in trap_notes:
                lines += [
                    f"- {note.get('title') or ''}",
                    f"  - 易错卡：{', '.join(note.get('trap_card_ids') or [])}",
                    f"  - 关联主卡：{', '.join(note.get('related_core_card_ids') or [])}",
                    f"  - 理由：{note.get('reason') or ''}",
                ]
            lines.append("")
        rejected = result.get("rejected_cards") or []
        if rejected:
            lines.append("拒绝/弱相关卡：")
            for item in rejected[:8]:
                lines.append(f"- {item.get('card_id')}: {item.get('reason')}")
            lines.append("")

    if fail_rows:
        lines.append("## 失败记录")
        lines.append("")
        for row in fail_rows:
            lines.append(f"- {row.get('question_id')}: {row.get('error')}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DeepSeek/OpenAI-compatible role judging on question packs.")
    parser.add_argument("--work-dir", type=Path, default=WORK_DIR)
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--question-ids", default="")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.4)
    args = parser.parse_args()

    load_env(args.work_dir)
    client, model = client_from_env()

    input_path = args.input or args.work_dir / "outputs" / "llm_question_packs.jsonl"
    packs = read_jsonl(input_path)
    question_ids = [item.strip() for item in args.question_ids.split(",") if item.strip()] or None
    selected = select_packs(packs, question_ids, args.limit)

    out_path = args.work_dir / "outputs" / "llm_role_judgements.sample.jsonl"
    report_path = args.work_dir / "reports" / "llm_role_judgements_sample.md"
    raw_dir = args.work_dir / "cache" / "llm_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    done = set() if args.force else load_done(out_path)
    new_rows: list[dict[str, Any]] = []

    for pack in selected:
        qid = pack["question_id"]
        if qid in done:
            print(f"skip {qid} already done")
            continue
        print(f"judging {qid} ...")
        try:
            result, raw_text = judge_pack(client, model, pack, args.temperature)
            errors = validate_result(pack, result)
            status = "ok" if not errors else "invalid"
            row = {
                "question_id": qid,
                "status": status,
                "model": model,
                "validation_errors": errors,
                "result": result,
            }
            write_json(raw_dir / f"{qid.replace('.', '_')}.json", {"raw_text": raw_text, "parsed": result})
        except Exception as exc:
            row = {
                "question_id": qid,
                "status": "error",
                "model": model,
                "error": str(exc),
            }
        append_jsonl(out_path, row)
        new_rows.append(row)
        time.sleep(args.sleep)

    all_rows = read_jsonl(out_path) if out_path.exists() else new_rows
    wanted = {pack["question_id"] for pack in selected}
    report_rows = [row for row in all_rows if row.get("question_id") in wanted]
    report_path.write_text(render_report(report_rows), encoding="utf-8")
    print(f"wrote {len(new_rows)} new rows")
    print(out_path)
    print(report_path)


if __name__ == "__main__":
    main()
