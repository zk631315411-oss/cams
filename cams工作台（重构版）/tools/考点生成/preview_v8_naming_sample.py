from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
V7_DIR = HERE / "work" / "preview_v7_sample"
OUT_DIR = HERE / "work" / "preview_v8_naming_sample"
QUESTIONS_FILE = ROOT / "data" / "source" / "questions.json"
DEFAULT_EXAM_POINT_FILES = [
    "exam_point_system_materialized_sample.json",
    "exam_point_system_full828.json",
]

DEFAULT_SAMPLE_LIMIT = 20
MAX_QUESTIONS_PER_POINT = 5
MAX_OPTIONS_PER_QUESTION = 4
MAX_CARDS_PER_POINT = 5
MAX_RELATIONS_PER_POINT = 8


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def sample_limit() -> int:
    return max(1, env_int("PREVIEW_V8_SAMPLE_LIMIT", DEFAULT_SAMPLE_LIMIT))


def id_from_row(row: dict[str, Any]) -> str | None:
    for key in ("exam_point_id", "id"):
        value = row.get(key)
        if value:
            return str(value)
    return None


def collect_ids(payload: Any) -> set[str]:
    ids: set[str] = set()
    if isinstance(payload, dict):
        for key in ("tasks", "records", "items"):
            rows = payload.get(key)
            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, dict):
                        ep_id = id_from_row(row)
                        if ep_id:
                            ids.add(ep_id)
        ep_id = id_from_row(payload)
        if ep_id:
            ids.add(ep_id)
    elif isinstance(payload, list):
        for row in payload:
            if isinstance(row, dict):
                ep_id = id_from_row(row)
                if ep_id:
                    ids.add(ep_id)
    return ids


def env_paths(name: str) -> list[Path]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    parts = [part.strip().strip('"') for part in raw.split(";") if part.strip()]
    return [Path(part) for part in parts]


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else HERE / path


def source_dir() -> Path:
    raw = os.getenv("PREVIEW_V8_SOURCE_DIR", "").strip().strip('"')
    return resolve_path(raw) if raw else V7_DIR


def source_file(env_name: str, default_names: list[str]) -> Path:
    raw = os.getenv(env_name, "").strip().strip('"')
    if raw:
        return resolve_path(raw)
    base = source_dir()
    for name in default_names:
        path = base / name
        if path.exists():
            return path
    return base / default_names[0]


def load_id_files(name: str) -> set[str]:
    ids: set[str] = set()
    for path in env_paths(name):
        if not path.exists():
            continue
        if path.suffix.lower() == ".jsonl":
            ids.update(collect_ids(read_jsonl(path)))
        else:
            ids.update(collect_ids(read_json(path)))
    return ids


def default_bucket_limits(total: int) -> tuple[int, int, int]:
    if total <= DEFAULT_SAMPLE_LIMIT:
        return 8, 6, 6
    multi = max(8, round(total * 0.4))
    structural = max(6, round(total * 0.3))
    contrast = max(6, total - multi - structural)
    return multi, structural, contrast


def batch_name() -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "", os.getenv("PREVIEW_V8_BATCH_NAME", "").strip())
    return value


def out_name(stem: str, suffix: str) -> str:
    name = batch_name()
    return f"{stem}_{name}.{suffix}" if name else f"{stem}.{suffix}"


def compact(text: Any, limit: int = 260) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)] + "..."


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(v for v in values if v))


def load_questions() -> dict[str, dict[str, Any]]:
    payload = read_json(QUESTIONS_FILE)
    items = payload.get("questions", []) if isinstance(payload, dict) else payload
    return {item["id"]: item for item in items}


def edge_key(edge: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(edge.get("question_id") or ""),
        str(edge.get("option") or ""),
        str(edge.get("card_id") or ""),
        str(edge.get("role") or ""),
    )


def selected_points(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    total = sample_limit()
    default_multi, default_structural, default_contrast = default_bucket_limits(total)
    multi_limit = env_int("PREVIEW_V8_MULTI_LIMIT", default_multi)
    structural_limit = env_int("PREVIEW_V8_STRUCTURAL_LIMIT", default_structural)
    contrast_limit = env_int("PREVIEW_V8_CONTRAST_LIMIT", default_contrast)

    def add_candidates(candidates: list[dict[str, Any]], limit: int) -> None:
        for point in candidates:
            if len(selected) >= total:
                return
            if len([item for item in selected if item.get("_bucket") == point.get("_bucket")]) >= limit:
                continue
            if point["id"] in selected_ids:
                continue
            selected.append(point)
            selected_ids.add(point["id"])

    multi = [
        {**point, "_bucket": "multi_card_or_high_frequency"}
        for point in points
        if point.get("card_ids") and (len(point.get("card_ids", [])) > 1 or int(point.get("question_count") or 0) >= 5)
    ]
    multi.sort(key=lambda p: (-int(p.get("question_count") or 0), -len(p.get("card_ids", [])), p["id"]))
    add_candidates(multi, multi_limit)

    structural = [
        {**point, "_bucket": "parent_or_virtual"}
        for point in points
        if point.get("children") or not point.get("card_ids")
    ]
    structural.sort(
        key=lambda p: (
            0 if not p.get("card_ids") else 1,
            -int(p.get("subtree_question_count") or 0),
            p["id"],
        )
    )
    add_candidates(structural, structural_limit)

    contrast = [
        {**point, "_bucket": "contrast_or_discrimination"}
        for point in points
        if "易错/辨析" in (point.get("tags") or []) or int(point.get("contrast_question_count") or 0) > 0
    ]
    contrast.sort(key=lambda p: (-int(p.get("contrast_question_count") or 0), -int(p.get("question_count") or 0), p["id"]))
    add_candidates(contrast, contrast_limit)

    if len(selected) < total:
        fallback = [{**point, "_bucket": "fallback"} for point in points]
        fallback.sort(key=lambda p: (-int(p.get("question_count") or 0), p["id"]))
        add_candidates(fallback, total - len(selected))

    return selected[:total]


def batch_points(points: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    start = max(0, env_int("PREVIEW_V8_START", 0))
    limit = max(1, env_int("PREVIEW_V8_LIMIT", sample_limit()))
    selected = selected_points(points)
    selected_before_filter = len(selected)
    include_ids = load_id_files("PREVIEW_V8_INCLUDE_IDS_FILE")
    exclude_ids = load_id_files("PREVIEW_V8_EXCLUDE_IDS_FILE")
    if include_ids:
        selected = [point for point in selected if point["id"] in include_ids]
    if exclude_ids:
        selected = [point for point in selected if point["id"] not in exclude_ids]
    return selected[start : start + limit], {
        "selected_total_before_filter": selected_before_filter,
        "selected_total": len(selected),
        "include_filter_count": len(include_ids),
        "exclude_filter_count": len(exclude_ids),
        "batch_start": start,
        "batch_limit": limit,
        "batch_count": len(selected[start : start + limit]),
    }


def group_edges(edges: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_ep: dict[str, dict[tuple[str, str, str, str], dict[str, Any]]] = defaultdict(dict)
    for edge in edges:
        ep_id = edge.get("exam_point_id")
        if not ep_id:
            continue
        by_ep[ep_id][edge_key(edge)] = edge
    return {ep_id: list(rows.values()) for ep_id, rows in by_ep.items()}


def summarize_questions(
    point: dict[str, Any],
    edges_by_ep: dict[str, list[dict[str, Any]]],
    questions_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = edges_by_ep.get(point["id"], [])
    rows.sort(
        key=lambda e: (
            0 if e.get("edge_scope") == "direct" else 1,
            str(e.get("question_id") or ""),
            str(e.get("option") or ""),
            str(e.get("card_id") or ""),
        )
    )
    by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in rows:
        by_question[str(edge.get("question_id") or "")].append(edge)

    question_items = []
    for qid, q_edges in list(by_question.items())[:MAX_QUESTIONS_PER_POINT]:
        question = questions_by_id.get(qid, {})
        q_edges.sort(key=lambda edge: (0 if edge.get("role") == "core" else 1, str(edge.get("option") or "")))
        question_items.append(
            {
                "question_id": qid,
                "stem": compact(question.get("stem"), 220),
                "answer": question.get("answer"),
                "evidence_options": [
                    {
                        "option": edge.get("option"),
                        "option_text": compact(edge.get("option_text"), 120),
                        "role": edge.get("role"),
                        "key_is_correct": edge.get("key_is_correct"),
                        "judgement": edge.get("judgement"),
                        "evidence_grade": edge.get("evidence_grade"),
                        "card_id": edge.get("card_id"),
                        "quote": compact(edge.get("quote"), 180),
                        "edge_scope": edge.get("edge_scope"),
                        "child_exam_point_id": edge.get("child_exam_point_id"),
                    }
                    for edge in q_edges[:MAX_OPTIONS_PER_QUESTION]
                ],
            }
        )
    return question_items


def build_prompt() -> str:
    return """# CAMS 考点命名与关系明确任务

你是 CAMS 教研助理。请只根据输入里的题目、选项证据、教材句卡和关系记录，对每个候选考点做“受限命名与关系说明”。

## 允许做什么

- 可以给候选考点命名。
- 可以写 `teaching_focus`，统一用“考查学生能否……”开头。
- 可以说明每张句卡在该考点中的作用。
- 可以说明题目为什么属于该考点。
- 可以提出拆分建议，但不要直接新增正式考点。
- 可以给虚拟父点命名，但必须说明它由哪些子点支撑。

## 禁止做什么

- 不得脱离输入材料自由发明新考点。
- 不得引用输入之外的教材内容。
- 不得把没有题目/句卡/子点支撑的内容写成考点。
- 不得只因为题目相同就强行合并；必须看教材句卡语义。

## 输出 JSON Schema

`risk_flags` 只能从以下枚举中选择零个或多个：`none`, `too_broad`, `weak_merge`, `parent_direction_uncertain`, `naming_uncertain`, `evidence_thin`, `contrast_uncertain`。如果没有风险，只写 `["none"]`，不要把整串枚举原样写进去。

## 风险审查要求

请先完成风险审查，再写 `risk_flags`。不要因为标题能写得顺就默认 `none`。

- 虚拟父点（没有 `card_ids` 但有 `children`）：必须检查子点是否真属于同一上位教材知识；如果只是同主题松散集合，标 `parent_direction_uncertain` 或 `too_broad`。
- 带 `children` 的非虚拟点：必须检查父点标题是否覆盖所有子点；如果父点标题过窄、子点跨多个规则/机构/阶段，标 `parent_direction_uncertain` 或 `too_broad`。
- 多句卡点：必须检查多张句卡是否确实是同一教材知识点；如果只是相邻、同章或同题牵连，标 `weak_merge`。
- `subtree_question_count` 明显大于 `question_count` 时：必须特别检查是否把父点写得太窄；如不确定，至少标 `parent_direction_uncertain`。
- 错误项/辨析项参与较多时：必须检查这些题是核心考查还是易错辨析信号；如不确定，标 `contrast_uncertain`。
- 证据只有标题句卡、短句卡，或 quote 不能直接支撑标题时：标 `evidence_thin`。
- 标题必须短，优先 6-16 字；超过 18 字通常说明命名不够抽象，除非教材专名无法压缩。

只有同时满足“教材句卡/子点支撑清楚、题目归属清楚、父子方向清楚、合并边界清楚”时，才能写 `["none"]`。

请写入一个 JSON 对象：

```json
{
  "schema_version": "preview_v8_agent_naming_output_v1",
  "agent": "subagent",
  "records": [
    {
      "exam_point_id": "EP7-0000",
      "title": "8-18字左右的短教材知识点名",
      "teaching_focus": "考查学生能否……",
      "relation_summary": "一句话说明这个考点如何由题目和句卡支撑",
      "card_roles": [
        {"card_id": "v6s_N00000", "role": "definition|rule|example|red_flag|contrast|detail|parent|child|alias|other", "reason": "简短理由"}
      ],
      "question_roles": [
        {"question_id": "2.1_1", "role": "direct_test|discrimination_test|scenario_application|definition_recall|other", "reason": "简短理由"}
      ],
      "split_recommendation": {
        "should_split": false,
        "reason": "如果建议拆分，说明拆成什么方向；否则说明无需拆分"
      },
      "risk_flags": ["none"],
      "confidence": "high|medium|low"
    }
  ]
}
```

只输出 JSON，不要输出 Markdown。
"""


def build_naming_input() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source_exam_point_system = source_file("PREVIEW_V8_EXAM_POINT_SYSTEM_FILE", DEFAULT_EXAM_POINT_FILES)
    source_edges = source_file("PREVIEW_V8_EDGES_FILE", ["exam_point_question_card_edges.json"])
    source_relation_records = source_file("PREVIEW_V8_RELATION_RECORDS_FILE", ["relation_judgement_records.jsonl"])
    points = read_json(source_exam_point_system)["items"]
    edges = read_json(source_edges)["items"]
    relation_records = read_jsonl(source_relation_records)
    relation_by_pair = {record.get("pair_id"): record for record in relation_records}
    questions_by_id = load_questions()
    edges_by_ep = group_edges(edges)
    points_by_id = {point["id"]: point for point in points}

    selected, batch_info = batch_points(points)
    tasks = []
    for order, point in enumerate(selected, start=1):
        relation_pair_ids = unique(
            list(point.get("materialize_relation_pair_ids", []))
            + list(point.get("relation_trace_pair_ids", []))
        )
        relation_records_for_point = [
            relation_by_pair[pair_id]
            for pair_id in relation_pair_ids
            if pair_id in relation_by_pair
        ]
        children = []
        for child_id in point.get("children", [])[:8]:
            child = points_by_id.get(child_id)
            if child:
                children.append(
                    {
                        "id": child["id"],
                        "current_title": compact(child.get("title"), 120),
                        "card_ids": child.get("card_ids", []),
                        "question_count": child.get("question_count"),
                        "tags": child.get("tags", []),
                    }
                )
        tasks.append(
            {
                "order": order,
                "selection_bucket": point.get("_bucket", ""),
                "exam_point_id": point["id"],
                "current_title": compact(point.get("title"), 180),
                "title_status": point.get("title_status"),
                "point_type": point.get("point_type"),
                "tags": point.get("tags", []),
                "parent_id": point.get("parent_id"),
                "children": children,
                "card_ids": point.get("card_ids", []),
                "question_ids": point.get("question_ids", []),
                "question_count": point.get("question_count"),
                "subtree_question_count": point.get("subtree_question_count"),
                "evidence_cards": [
                    {
                        "card_id": item.get("card_id"),
                        "quote": compact(item.get("quote"), 260),
                        "source_point_id": item.get("source_point_id"),
                    }
                    for item in point.get("evidence_quotes", [])[:MAX_CARDS_PER_POINT]
                ],
                "question_evidence": summarize_questions(point, edges_by_ep, questions_by_id),
                "relation_records": [
                    {
                        "pair_id": record.get("pair_id"),
                        "label": record.get("source_draft_label"),
                        "confidence": record.get("source_draft_confidence"),
                        "applied_action": record.get("applied_action"),
                        "rationale": record.get("source_draft_rationale"),
                        "card_a_id": record.get("card_a_id"),
                        "card_b_id": record.get("card_b_id"),
                        "parent_card_id": record.get("parent_card_id"),
                        "child_card_id": record.get("child_card_id"),
                        "direction_method": record.get("direction_method"),
                    }
                    for record in relation_records_for_point[:MAX_RELATIONS_PER_POINT]
                ],
            }
        )

    payload = {
        "schema_version": "preview_v8_agent_naming_input_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_exam_point_system": str(source_exam_point_system),
        "source_edges": str(source_edges),
        "source_relation_records": str(source_relation_records),
        "prompt_file": str(OUT_DIR / "agent_prompt.md"),
        "output_file": str(OUT_DIR / out_name("agent_naming_output", "json")),
        "selection_policy": {
            "total": sample_limit(),
            **batch_info,
            "buckets": [
                "multi_card_or_high_frequency",
                "parent_or_virtual",
                "contrast_or_discrimination",
                "fallback",
            ],
        },
        "tasks": tasks,
    }
    write_json(OUT_DIR / out_name("agent_naming_input", "json"), payload)
    (OUT_DIR / "agent_prompt.md").write_text(build_prompt(), encoding="utf-8")
    write_json(
        OUT_DIR / "agent_naming_output.schema.json",
        {
            "schema_version": "preview_v8_agent_naming_output_schema_v1",
            "required_top_level": ["schema_version", "agent", "records"],
            "required_record_fields": [
                "exam_point_id",
                "title",
                "teaching_focus",
                "relation_summary",
                "card_roles",
                "question_roles",
                "split_recommendation",
                "risk_flags",
                "confidence",
            ],
        },
    )
    return payload


def validate_output(output: dict[str, Any], expected_ids: set[str]) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []
    if output.get("schema_version") != "preview_v8_agent_naming_output_v1":
        errors.append("schema_version must be preview_v8_agent_naming_output_v1")
    records = output.get("records")
    if not isinstance(records, list):
        return errors + ["records must be a list"], warnings
    seen = set()
    required = {
        "exam_point_id",
        "title",
        "teaching_focus",
        "relation_summary",
        "card_roles",
        "question_roles",
        "split_recommendation",
        "risk_flags",
        "confidence",
    }
    for idx, record in enumerate(records, start=1):
        missing = required - set(record.keys())
        if missing:
            errors.append(f"record {idx} missing fields: {sorted(missing)}")
        ep_id = record.get("exam_point_id")
        if ep_id not in expected_ids:
            errors.append(f"record {idx} unknown exam_point_id: {ep_id}")
        if ep_id in seen:
            errors.append(f"duplicate exam_point_id: {ep_id}")
        seen.add(ep_id)
        if record.get("confidence") not in {"high", "medium", "low"}:
            errors.append(f"record {idx} invalid confidence: {record.get('confidence')}")
        if not str(record.get("teaching_focus") or "").startswith("考查学生能否"):
            errors.append(f"record {idx} teaching_focus must start with 考查学生能否")
        title = str(record.get("title") or "")
        if len(title) > 18:
            warnings.append(f"record {idx} title longer than 18 chars: {ep_id} len={len(title)}")
        risk_flags = record.get("risk_flags")
        allowed_risks = {
            "none",
            "too_broad",
            "weak_merge",
            "parent_direction_uncertain",
            "naming_uncertain",
            "evidence_thin",
            "contrast_uncertain",
        }
        if not isinstance(risk_flags, list) or not risk_flags:
            errors.append(f"record {idx} risk_flags must be a non-empty list")
        elif set(risk_flags) - allowed_risks:
            errors.append(f"record {idx} invalid risk_flags: {risk_flags}")
    missing_ids = expected_ids - seen
    if missing_ids:
        warnings.append(f"missing records for ids: {sorted(missing_ids)}")
    if not seen:
        errors.append("records must contain at least one expected exam_point_id")
    if len(records) >= 10 and all(record.get("risk_flags") == ["none"] for record in records):
        warnings.append("all records use risk_flags=[none]; review for over-confident self-assessment")
    return errors, warnings


def integrate_output(input_payload: dict[str, Any]) -> dict[str, Any] | None:
    output_path = OUT_DIR / out_name("agent_naming_output", "json")
    if not output_path.exists():
        return None

    output = read_json(output_path)
    expected_ids = {task["exam_point_id"] for task in input_payload["tasks"]}
    errors, warnings = validate_output(output, expected_ids)
    write_json(
        OUT_DIR / out_name("validation", "json"),
        {"errors": errors, "warnings": warnings, "error_count": len(errors), "warning_count": len(warnings)},
    )
    if errors:
        return {"status": "invalid", "errors": errors}

    source_exam_point_system = source_file("PREVIEW_V8_EXAM_POINT_SYSTEM_FILE", DEFAULT_EXAM_POINT_FILES)
    source_points = read_json(source_exam_point_system)["items"]
    selected_by_id = {task["exam_point_id"]: task for task in input_payload["tasks"]}
    records_by_id = {record["exam_point_id"]: record for record in output["records"]}
    named_items = []
    naming_records = []
    for point in source_points:
        record = records_by_id.get(point["id"])
        if not record:
            continue
        item = dict(point)
        item["title_before_naming"] = point.get("title")
        item["title"] = record["title"]
        item["teaching_focus"] = record["teaching_focus"]
        item["relation_summary"] = record["relation_summary"]
        item["card_roles"] = record["card_roles"]
        item["question_roles"] = record["question_roles"]
        item["split_recommendation"] = record["split_recommendation"]
        item["naming_risk_flags"] = record["risk_flags"]
        item["naming_confidence"] = record["confidence"]
        item["title_status"] = "agent_named_sample"
        item["review_status"] = "preview_v8_agent_named_sample"
        named_items.append(item)
        naming_records.append(
            {
                "record_type": "naming",
                "judgement_source": "subagent",
                "prompt_file": str(OUT_DIR / "agent_prompt.md"),
                "input_file": str(OUT_DIR / out_name("agent_naming_input", "json")),
                "output_file": str(OUT_DIR / out_name("agent_naming_output", "json")),
                "exam_point_id": point["id"],
                "selection_bucket": selected_by_id[point["id"]]["selection_bucket"],
                "title_before": point.get("title"),
                "title_after": record["title"],
                "teaching_focus": record["teaching_focus"],
                "confidence": record["confidence"],
                "risk_flags": record["risk_flags"],
                "split_recommendation": record["split_recommendation"],
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        )

    payload = {
        "schema_version": "preview_v8_named_exam_points_sample",
        "note": "Subagent-generated naming sample using the same constrained prompt intended for a future LLM executor.",
        "items": named_items,
    }
    write_json(OUT_DIR / out_name("named_exam_points_sample", "json"), payload)
    write_jsonl(OUT_DIR / out_name("naming_records", "jsonl"), naming_records)
    write_report(input_payload, output, named_items, naming_records)
    return {
        "status": "ok",
        "named_count": len(named_items),
        "expected_count": len(expected_ids),
        "missing_count": len(expected_ids) - len(named_items),
        "warnings": warnings,
        "risk_distribution": dict(Counter(flag for item in named_items for flag in item.get("naming_risk_flags", [])).most_common()),
        "confidence_distribution": dict(Counter(item.get("naming_confidence") for item in named_items).most_common()),
    }


def write_report(
    input_payload: dict[str, Any],
    output: dict[str, Any],
    named_items: list[dict[str, Any]],
    naming_records: list[dict[str, Any]],
) -> None:
    lines = [
        "# Preview v8 命名样本报告",
        "",
        "本轮用子代理代替 LLM，按固定提示词对 v7 样本做受限命名与关系说明。",
        "",
        "## 统计",
        "",
        f"- 输入任务：{len(input_payload['tasks'])}",
        f"- 命名输出：{len(output.get('records', []))}",
        f"- 整合样本：{len(named_items)}",
        f"- 未命名任务：{len(input_payload['tasks']) - len(named_items)}",
        f"- 置信度分布：{dict(Counter(item.get('naming_confidence') for item in named_items).most_common())}",
        f"- 风险标记分布：{dict(Counter(flag for item in named_items for flag in item.get('naming_risk_flags', [])).most_common())}",
        "",
        "## 样例",
        "",
    ]
    for item in named_items[:8]:
        lines.extend(
            [
                f"### {item['id']} {item['title']}",
                f"- 原标题：{compact(item.get('title_before_naming'), 120)}",
                f"- 考查方向：{item.get('teaching_focus')}",
                f"- 关系说明：{item.get('relation_summary')}",
                f"- 置信度：{item.get('naming_confidence')}；风险：{', '.join(item.get('naming_risk_flags') or [])}",
                f"- 句卡：{', '.join(item.get('card_ids') or ['（虚拟父点）'])}",
                f"- 题目：{', '.join(item.get('question_ids', [])[:8])}",
                "",
            ]
        )
    lines.extend(
        [
            "## 边界",
            "",
            "- 本轮命名只允许使用 `agent_naming_input.json` 中的题目、选项、句卡、关系记录。",
            "- 子代理可以建议拆分，但脚本不会自动改 v7 结构。",
            "- 后续接 DeepSeek 时，应复用同一 prompt 和 JSON schema。",
        ]
    )
    (OUT_DIR / out_name("naming_report", "md")).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    merge_batches_env = os.getenv("PREVIEW_V8_MERGE_BATCHES", "").strip()
    if merge_batches_env:
        result = merge_batch_outputs([name.strip() for name in merge_batches_env.split(",") if name.strip()])
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    input_payload = build_naming_input()
    result = integrate_output(input_payload)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_file": str(OUT_DIR / out_name("agent_naming_input", "json")),
        "prompt_file": str(OUT_DIR / "agent_prompt.md"),
        "expected_output_file": str(OUT_DIR / out_name("agent_naming_output", "json")),
        "task_count": len(input_payload["tasks"]),
        "integration": result or {"status": "waiting_for_agent_output"},
    }
    write_json(OUT_DIR / out_name("summary", "json"), summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def merge_batch_outputs(batch_names: list[str]) -> dict[str, Any]:
    merged_records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    source_files = []
    for raw_name in batch_names:
        name = "" if raw_name in {"default", "base", "batch1"} else re.sub(r"[^A-Za-z0-9_-]+", "", raw_name)
        path = OUT_DIR / (f"agent_naming_output_{name}.json" if name else "agent_naming_output.json")
        if not path.exists():
            return {"status": "missing_batch_output", "missing": str(path)}
        payload = read_json(path)
        for record in payload.get("records", []):
            ep_id = record.get("exam_point_id")
            if ep_id in seen_ids:
                return {"status": "duplicate_exam_point_id", "exam_point_id": ep_id, "file": str(path)}
            seen_ids.add(ep_id)
            merged_records.append(record)
        source_files.append(str(path))

    merged = {
        "schema_version": "preview_v8_agent_naming_output_v1",
        "agent": "subagent_merged_batches",
        "source_files": source_files,
        "records": merged_records,
    }
    merge_name = re.sub(r"[^A-Za-z0-9_-]+", "", os.getenv("PREVIEW_V8_MERGE_NAME", "merged").strip()) or "merged"
    merged_path = OUT_DIR / f"agent_naming_output_{merge_name}.json"
    write_json(merged_path, merged)

    old_batch = os.environ.get("PREVIEW_V8_BATCH_NAME")
    try:
        os.environ["PREVIEW_V8_BATCH_NAME"] = merge_name
        input_payload = build_naming_input()
        result = integrate_output(input_payload)
    finally:
        if old_batch is None:
            os.environ.pop("PREVIEW_V8_BATCH_NAME", None)
        else:
            os.environ["PREVIEW_V8_BATCH_NAME"] = old_batch

    return {
        "status": "ok",
        "merged_output": str(merged_path),
        "record_count": len(merged_records),
        "integration": result,
    }


if __name__ == "__main__":
    main()
