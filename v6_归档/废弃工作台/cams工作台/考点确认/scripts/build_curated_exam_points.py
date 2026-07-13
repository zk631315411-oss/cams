from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
WORK_DIR = SCRIPT_DIR.parent

STOPWORDS = {
    "的",
    "与",
    "和",
    "及",
    "或",
    "对",
    "中",
    "为",
    "在",
    "将",
    "通过",
    "进行",
    "核心",
    "定义",
    "识别",
    "特征",
    "考点",
    "理解",
    "常见",
    "风险",
}

SYNONYMS = {
    "结构化": "拆分",
    "Structuring": "拆分",
    "structuring": "拆分",
    "Smurfing": "拆分",
    "smurfing": "拆分",
    "微型拆分": "拆分",
    "巢状交易": "嵌套账户",
    "连环代理": "嵌套账户",
    "通汇账户嵌套": "嵌套账户",
    "政治公众人物": "PEP",
    "代理行": "代理银行",
    "对应银行": "委托银行",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def compact(text: Any, limit: int = 180) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def unique(items: list[Any]) -> list[Any]:
    result = []
    seen = set()
    for item in items:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, dict) else item
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def slug(text: str, fallback: str) -> str:
    ascii_part = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    if ascii_part:
        return ascii_part[:48]
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return fallback + "_" + digest


def latest_by_question(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        qid = row.get("question_id")
        if qid:
            by_id[qid] = row
    return [by_id[qid] for qid in sorted(by_id)]


def card_index(work_dir: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(work_dir / "outputs" / "evidence_card_scores.json")
    return {card["card_id"]: card for card in payload.get("cards", [])}


def qa_indexes(work_dir: Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    path = work_dir.parent / "data" / "teaching_assets" / "qa_bindings.json"
    if not path.exists():
        return {}, {}
    bindings = read_json(path).get("bindings", [])
    by_question: dict[str, list[str]] = defaultdict(list)
    by_card: dict[str, list[str]] = defaultdict(list)
    for binding in bindings:
        qa_id = binding.get("qa_id")
        if not qa_id:
            continue
        qid = binding.get("bound_question_id")
        if qid:
            by_question[qid].append(qa_id)
        for cid in binding.get("inherited_card_ids") or []:
            if cid:
                by_card[cid].append(qa_id)
    return by_question, by_card


def qa_ids_for_point(
    question_ids: list[str],
    source_ids: list[str],
    qa_by_question: dict[str, list[str]],
    qa_by_card: dict[str, list[str]],
) -> list[str]:
    ids: list[str] = []
    for qid in question_ids:
        ids.extend(qa_by_question.get(qid, []))
    for cid in source_ids:
        ids.extend(qa_by_card.get(cid, []))
    return unique([qa_id for qa_id in ids if qa_id])


def tokenize(text: str) -> set[str]:
    normalized = text or ""
    for src, dst in SYNONYMS.items():
        normalized = normalized.replace(src, dst)
    tokens = re.findall(r"[A-Za-z]+|[\u4e00-\u9fff]{2,}", normalized)
    result = set()
    for token in tokens:
        token = token.strip()
        if not token or token in STOPWORDS:
            continue
        if len(token) > 12 and re.fullmatch(r"[\u4e00-\u9fff]+", token):
            for i in range(0, len(token), 4):
                part = token[i : i + 4]
                if len(part) >= 2 and part not in STOPWORDS:
                    result.add(part)
        else:
            result.add(token)
    return result


def root_chapter(card_ids: list[str], cards_by_id: dict[str, dict[str, Any]]) -> str:
    chapters = []
    for cid in card_ids:
        path = (cards_by_id.get(cid) or {}).get("chapter_path") or ""
        if path:
            chapters.append(path.split(">")[0].strip())
    if not chapters:
        return ""
    return Counter(chapters).most_common(1)[0][0]


def clean_trap_notes(notes: list[dict[str, Any]], max_notes: int = 2) -> list[dict[str, Any]]:
    cleaned = []
    for note in notes:
        trap_ids = unique([cid for cid in note.get("trap_card_ids") or [] if cid])
        related_ids = unique([cid for cid in note.get("related_core_card_ids") or [] if cid])
        if not trap_ids:
            continue
        cleaned.append(
            {
                "title": compact(note.get("title"), 80),
                "trap_card_ids": trap_ids[:8],
                "related_core_card_ids": related_ids[:5],
                "reason": compact(note.get("reason"), 260),
                "confidence": note.get("confidence") or "medium",
            }
        )
    cleaned.sort(key=lambda item: (-(len(item["trap_card_ids"])), item["title"]))
    return cleaned[:max_notes]


def clean_rows(rows: list[dict[str, Any]], cards_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned = []
    for row in latest_by_question(rows):
        if row.get("status") != "ok":
            continue
        result = row.get("result") or {}
        qid = row.get("question_id")
        exam_points = []
        for point in result.get("exam_points") or []:
            core_ids = unique([cid for cid in point.get("core_card_ids") or [] if cid])
            supporting_ids = unique([cid for cid in point.get("supporting_card_ids") or [] if cid and cid not in core_ids])
            background_ids = unique(
                [
                    cid
                    for cid in point.get("background_card_ids") or []
                    if cid and cid not in core_ids and cid not in supporting_ids
                ]
            )
            if not core_ids:
                continue
            quality_flags = []
            if point.get("point_type") == "textbook_note":
                quality_flags.append("llm_point_type_textbook_note")
            if len(core_ids) > 3:
                quality_flags.append("many_core_cards")
            exam_points.append(
                {
                    "question_id": qid,
                    "title": compact(point.get("title"), 90),
                    "point_type": point.get("point_type") or "core",
                    "core_card_ids": core_ids,
                    "supporting_card_ids": supporting_ids,
                    "background_card_ids": background_ids,
                    "source_card_ids": unique(core_ids + supporting_ids + background_ids),
                    "reason": compact(point.get("reason"), 360),
                    "confidence": point.get("confidence") or "medium",
                    "quality_flags": quality_flags,
                    "tokens": sorted(tokenize(point.get("title") or result.get("exam_intent") or "")),
                    "root_chapter": root_chapter(core_ids + supporting_ids, cards_by_id),
                }
            )
        cleaned.append(
            {
                "question_id": qid,
                "exam_intent": compact(result.get("exam_intent"), 260),
                "exam_points": exam_points,
                "trap_notes": clean_trap_notes(result.get("trap_notes") or []),
                "rejected_cards": result.get("rejected_cards") or [],
            }
        )
    return cleaned


def should_merge(a: dict[str, Any], b: dict[str, Any]) -> tuple[bool, str]:
    a_core = set(a.get("core_card_ids") or [])
    b_core = set(b.get("core_card_ids") or [])
    a_source = set(a.get("source_card_ids") or [])
    b_source = set(b.get("source_card_ids") or [])
    a_tokens = set(a.get("tokens") or [])
    b_tokens = set(b.get("tokens") or [])
    shared = a_tokens & b_tokens
    union = a_tokens | b_tokens
    ratio = len(shared) / len(union) if union else 0

    if a_core & b_core:
        a_title = a.get("title") or ""
        b_title = b.get("title") or ""
        policy_terms = {"政策", "监督", "要求", "义务", "必要性"}
        risk_terms = {"风险", "要素", "情形", "因素"}
        a_policy = any(term in a_title for term in policy_terms)
        b_policy = any(term in b_title for term in policy_terms)
        a_risk = any(term in a_title for term in risk_terms)
        b_risk = any(term in b_title for term in risk_terms)
        if ((a_policy and b_risk) or (b_policy and a_risk)) and ratio < 0.45:
            return False, ""
        return True, "core_card_overlap"
    if (a_core & b_source or b_core & a_source) and ratio >= 0.35:
        return True, "core_support_overlap"

    if not union:
        return False, ""

    if a.get("root_chapter") and a.get("root_chapter") == b.get("root_chapter") and ratio >= 0.42:
        return True, "title_chapter_similarity"

    shared_keywords = {"拆分", "嵌套账户", "通汇账户", "代理银行", "PEP", "私人银行", "空壳银行"}
    if shared & shared_keywords and ratio >= 0.25:
        return True, "keyword_similarity"

    return False, ""


def union_find(size: int) -> tuple[list[int], Any, Any]:
    parent = list(range(size))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    return parent, find, union


def choose_title(points: list[dict[str, Any]]) -> str:
    if len(points) == 1:
        return points[0]["title"]
    sorted_points = sorted(
        points,
        key=lambda p: (
            -len(p.get("question_ids", [p.get("question_id")])),
            len(p.get("title") or ""),
            p.get("title") or "",
        ),
    )
    title = sorted_points[0].get("title") or "未命名考点"
    if "拆分交易" in " ".join(p.get("title") or "" for p in points):
        return "拆分交易的定义、识别与报告阈值规避"
    return title


def merge_points(
    cleaned_rows: list[dict[str, Any]],
    qa_by_question: dict[str, list[str]] | None = None,
    qa_by_card: dict[str, list[str]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    qa_by_question = qa_by_question or {}
    qa_by_card = qa_by_card or {}
    flat = []
    trap_by_question = {row["question_id"]: row.get("trap_notes") or [] for row in cleaned_rows}
    intent_by_question = {row["question_id"]: row.get("exam_intent") or "" for row in cleaned_rows}
    for row in cleaned_rows:
        for point in row.get("exam_points") or []:
            flat.append(point)

    parent, find, union = union_find(len(flat))
    merge_edges = []
    for i in range(len(flat)):
        for j in range(i + 1, len(flat)):
            ok, reason = should_merge(flat[i], flat[j])
            if ok:
                union(i, j)
                merge_edges.append(
                    {
                        "from_question_id": flat[i]["question_id"],
                        "to_question_id": flat[j]["question_id"],
                        "reason": reason,
                        "from_title": flat[i]["title"],
                        "to_title": flat[j]["title"],
                    }
                )

    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for idx, point in enumerate(flat):
        groups[find(idx)].append(point)

    curated = []
    for group_points in groups.values():
        question_ids = sorted({p["question_id"] for p in group_points})
        title = choose_title(group_points)
        core_ids = unique([cid for p in group_points for cid in p.get("core_card_ids") or []])
        supporting_ids = unique(
            [
                cid
                for p in group_points
                for cid in p.get("supporting_card_ids") or []
                if cid not in core_ids
            ]
        )
        background_ids = unique(
            [
                cid
                for p in group_points
                for cid in p.get("background_card_ids") or []
                if cid not in core_ids and cid not in supporting_ids
            ]
        )
        source_ids = unique(core_ids + supporting_ids + background_ids)
        trap_notes = []
        for qid in question_ids:
            trap_notes.extend(trap_by_question.get(qid, []))
        trap_notes = unique(trap_notes)[:4]
        point_types = [p.get("point_type") for p in group_points if p.get("point_type")]
        level = "frequent" if len(question_ids) >= 2 else (Counter(point_types).most_common(1)[0][0] if point_types else "core")
        quality_flags = unique([flag for p in group_points for flag in p.get("quality_flags") or []])
        if len(question_ids) >= 2:
            quality_flags.append("multi_question_supported")
        if level == "textbook_note":
            quality_flags.append("weak_directness_signal")
        item = {
            "id": "ep_curated_" + slug(title, "point"),
            "title": title,
            "level": level,
            "source_card_ids": source_ids,
            "core_card_ids": core_ids,
            "supporting_card_ids": supporting_ids,
            "background_card_ids": background_ids,
            "question_ids": question_ids,
            "qa_ids": qa_ids_for_point(question_ids, source_ids, qa_by_question, qa_by_card),
            "trap_notes": trap_notes,
            "exam_intents": [intent_by_question[qid] for qid in question_ids if intent_by_question.get(qid)],
            "reason": compact("；".join(p.get("reason") or "" for p in group_points if p.get("reason")), 520),
            "confidence": "high" if all(p.get("confidence") == "high" for p in group_points) else "medium",
            "generation_source": "deepseek_v4pro_role_judge_v1",
            "quality_flags": unique(quality_flags),
            "member_points": [
                {
                    "question_id": p["question_id"],
                    "title": p["title"],
                    "core_card_ids": p.get("core_card_ids") or [],
                    "supporting_card_ids": p.get("supporting_card_ids") or [],
                }
                for p in group_points
            ],
        }
        curated.append(item)

    curated.sort(key=lambda item: (-len(item["question_ids"]), item["title"]))
    return curated, merge_edges


def render_report(cleaned_rows: list[dict[str, Any]], curated: list[dict[str, Any]], merge_edges: list[dict[str, Any]]) -> str:
    original_points = sum(len(row.get("exam_points") or []) for row in cleaned_rows)
    original_traps = sum(len(row.get("trap_notes") or []) for row in cleaned_rows)
    curated_traps = sum(len(item.get("trap_notes") or []) for item in curated)
    levels = Counter(item.get("level") for item in curated)
    flags = Counter(flag for item in curated for flag in item.get("quality_flags") or [])

    lines = [
        "# Curated 考点生成报告",
        "",
        f"- 输入题目：{len(cleaned_rows)}",
        f"- 清洗后题目级正式考点：{original_points}",
        f"- 合并后考点：{len(curated)}",
        f"- 清洗后易错辨析：{original_traps}",
        f"- 合并后挂载易错辨析：{curated_traps}",
        f"- 合并边：{len(merge_edges)}",
        "",
        "## 考点层级",
        "",
    ]
    for level, count in levels.most_common():
        lines.append(f"- {level}: {count}")
    lines += ["", "## 质量标记", ""]
    if flags:
        for flag, count in flags.most_common():
            lines.append(f"- {flag}: {count}")
    else:
        lines.append("- 无")

    lines += ["", "## 合并边", ""]
    if not merge_edges:
        lines.append("- 无")
    for edge in merge_edges:
        lines.append(
            f"- {edge['from_question_id']} -> {edge['to_question_id']} | {edge['reason']} | {edge['from_title']} => {edge['to_title']}"
        )

    lines += ["", "## 合并后考点", ""]
    for item in curated:
        lines += [
            f"### {item['title']}",
            "",
            f"- ID：{item['id']}",
            f"- 层级：{item['level']}",
            f"- 题目：{', '.join(item['question_ids'])}",
            f"- 主卡：{', '.join(item['core_card_ids'])}",
            f"- 辅助：{', '.join(item['supporting_card_ids'])}",
            f"- 易错辨析：{len(item.get('trap_notes') or [])} 条",
            f"- 标记：{', '.join(item.get('quality_flags') or [])}",
            "",
        ]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build cleaned and curated exam points from LLM judgements.")
    parser.add_argument("--work-dir", type=Path, default=WORK_DIR)
    args = parser.parse_args()

    work_dir = args.work_dir
    rows = read_jsonl(work_dir / "outputs" / "llm_role_judgements.sample.jsonl")
    cards_by_id = card_index(work_dir)
    qa_by_question, qa_by_card = qa_indexes(work_dir)
    cleaned = clean_rows(rows, cards_by_id)
    curated, merge_edges = merge_points(cleaned, qa_by_question, qa_by_card)

    write_json(work_dir / "outputs" / "llm_role_judgements.cleaned.json", {"items": cleaned})
    write_json(
        work_dir / "outputs" / "exam_points_curated_mvp.json",
        {
            "version": "0.1",
            "asset_note": "由现有题目证据绑定与 DeepSeek v4-pro 受限判断生成的参考考点层，尚未接入前端。",
            "stats": {
                "input_questions": len(cleaned),
                "question_level_points": sum(len(row.get("exam_points") or []) for row in cleaned),
                "curated_points": len(curated),
                "merge_edges": len(merge_edges),
            },
            "exam_points": curated,
        },
    )
    write_json(work_dir / "outputs" / "curated_merge_edges.json", {"edges": merge_edges})
    (work_dir / "reports" / "curated_exam_points_report.md").write_text(
        render_report(cleaned, curated, merge_edges),
        encoding="utf-8",
    )

    print(f"cleaned questions: {len(cleaned)}")
    print(f"curated points: {len(curated)}")
    print(work_dir / "outputs" / "exam_points_curated_mvp.json")


if __name__ == "__main__":
    main()
