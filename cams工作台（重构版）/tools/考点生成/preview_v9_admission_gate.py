from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
V8_DIR = HERE / "work" / "preview_v8_naming_sample"
OUT_DIR = HERE / "work" / "preview_v9_admission_gate"
DEFAULT_SOURCE_FILE = V8_DIR / "named_exam_points_sample50_full.json"
MIN_READY_QUOTE_CHARS = 18


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else HERE / path


def source_file() -> Path:
    return resolve_path(os.getenv("PREVIEW_V9_SOURCE_FILE", str(DEFAULT_SOURCE_FILE)))


def batch_name() -> str:
    raw = os.getenv("PREVIEW_V9_BATCH_NAME", "").strip()
    return "".join(ch for ch in raw if ch.isalnum() or ch in {"_", "-"})


def out_name(stem: str, suffix: str) -> str:
    name = batch_name()
    return f"{stem}_{name}.{suffix}" if name else f"{stem}.{suffix}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )


def is_virtual_parent(item: dict[str, Any]) -> bool:
    return not item.get("card_ids") and bool(item.get("children"))


def has_children(item: dict[str, Any]) -> bool:
    return bool(item.get("children"))


def should_split(item: dict[str, Any]) -> bool:
    split = item.get("split_recommendation") or {}
    return bool(split.get("should_split"))


def title_too_long(item: dict[str, Any]) -> bool:
    return len(str(item.get("title") or "")) > 18


def quote_texts(item: dict[str, Any]) -> list[str]:
    return [
        str(row.get("quote") or "").strip()
        for row in item.get("evidence_quotes") or []
        if str(row.get("quote") or "").strip()
    ]


def quote_context_needs_review(item: dict[str, Any]) -> bool:
    texts = quote_texts(item)
    if not texts:
        return True
    if any(len(text) < MIN_READY_QUOTE_CHARS for text in texts):
        return True
    return any(text.endswith(("包括：", "包括:", "如下：", "如下:", "：", ":")) for text in texts)


def contrast_counts(item: dict[str, Any]) -> tuple[int, int]:
    question_count = int(item.get("question_count") or 0)
    contrast_count = int(item.get("contrast_question_count") or 0)
    return question_count, contrast_count


def engineering_risks(item: dict[str, Any]) -> set[str]:
    risks: set[str] = set()
    virtual_parent = is_virtual_parent(item)
    children = has_children(item)
    question_count = int(item.get("question_count") or 0)
    subtree_question_count = int(item.get("subtree_question_count") or 0)
    card_count = len(item.get("card_ids") or [])
    child_count = len(item.get("children") or [])
    _, contrast_count = contrast_counts(item)

    if virtual_parent:
        risks.add("virtual_parent_review")
    if children:
        risks.add("parent_child_review")
    if children and subtree_question_count > question_count + 3:
        risks.add("broad_subtree_review")
    if title_too_long(item):
        risks.add("title_too_long")
    if card_count > 1:
        risks.add("multi_card_merge_review")
    if contrast_count >= 2 or (question_count > 0 and contrast_count / max(question_count, 1) >= 0.5):
        risks.add("contrast_heavy_review")
    if card_count == 1 and child_count >= 4:
        risks.add("narrow_parent_many_children_review")
    if question_count <= 1 and not children:
        risks.add("single_question_candidate_review")
    if quote_context_needs_review(item):
        risks.add("quote_context_review")
    return risks


def strong_direct_support(item: dict[str, Any]) -> bool:
    question_count = int(item.get("question_count") or 0)
    core_count = int(item.get("core_question_count") or 0)
    contrast_count = int(item.get("contrast_question_count") or 0)
    card_count = len(item.get("card_ids") or [])
    return (
        card_count == 1
        and not has_children(item)
        and question_count >= 3
        and core_count >= 3
        and contrast_count <= 1
    )


def moderate_direct_support(item: dict[str, Any], eng_risks: set[str]) -> bool:
    question_count = int(item.get("question_count") or 0)
    core_count = int(item.get("core_question_count") or 0)
    contrast_count = int(item.get("contrast_question_count") or 0)
    card_count = len(item.get("card_ids") or [])
    return (
        card_count == 1
        and not has_children(item)
        and question_count >= 2
        and core_count >= 2
        and contrast_count <= 1
        and "quote_context_review" not in eng_risks
    )


def single_question_direct_candidate(item: dict[str, Any], eng_risks: set[str]) -> bool:
    question_count = int(item.get("question_count") or 0)
    core_count = int(item.get("core_question_count") or 0)
    contrast_count = int(item.get("contrast_question_count") or 0)
    card_count = len(item.get("card_ids") or [])
    return (
        card_count == 1
        and not has_children(item)
        and question_count == 1
        and core_count >= 1
        and contrast_count == 0
        and "quote_context_review" not in eng_risks
    )


def strong_contrast_support(item: dict[str, Any]) -> bool:
    question_count = int(item.get("question_count") or 0)
    core_count = int(item.get("core_question_count") or 0)
    contrast_count = int(item.get("contrast_question_count") or 0)
    card_count = len(item.get("card_ids") or [])
    return (
        card_count == 1
        and not has_children(item)
        and question_count >= 5
        and core_count >= 4
        and contrast_count >= 2
    )


def priority_rank(priority: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(priority, 0)


def max_priority(*priorities: str) -> str:
    rank_to_priority = {0: "low", 1: "medium", 2: "high"}
    return rank_to_priority[max(priority_rank(priority) for priority in priorities)]


def decide(item: dict[str, Any]) -> dict[str, Any]:
    risks = set(item.get("naming_risk_flags") or [])
    confidence = item.get("naming_confidence")
    virtual_parent = is_virtual_parent(item)
    children = has_children(item)
    question_count = int(item.get("question_count") or 0)
    subtree_question_count = int(item.get("subtree_question_count") or 0)
    card_count = len(item.get("card_ids") or [])
    split_requested = should_split(item)
    eng_risks = engineering_risks(item)

    status = "ready_candidate"
    review_priority = "low"
    actions: list[str] = []
    reasons: list[str] = []

    if risks == {"none"}:
        if confidence == "high":
            status = "ready_candidate"
            reasons.append("high confidence and no risk flags")
        else:
            status = "ready_candidate"
            review_priority = "low"
            reasons.append("no risk flags, but confidence is not high")
    else:
        status = "needs_review"
        review_priority = "medium"
        reasons.append("has risk flags: " + ", ".join(sorted(risks)))

    broad_is_structural = split_requested or (
        children and subtree_question_count > question_count + 3
    ) or bool({"weak_merge", "parent_direction_uncertain"} & risks)
    if "too_broad" in risks and broad_is_structural:
        status = "split_recommended"
        review_priority = "high"
        actions.append("review_split")
        reasons.append("too_broad indicates the point may mix multiple teaching units")
    elif "too_broad" in risks:
        status = "needs_review"
        review_priority = "medium"
        actions.append("observe_broad_scope")
        reasons.append("too_broad is present, but split signals are not strong enough for automatic split queue")

    if "parent_direction_uncertain" in risks and children:
        if status != "split_recommended":
            if (
                not virtual_parent
                and not split_requested
                and question_count >= 3
                and len(item.get("children") or []) <= 1
            ):
                status = "ready_candidate_with_children"
                review_priority = "medium"
                actions.append("post_admission_parent_child_check")
                reasons.append("parent/child direction needs a light post-admission check")
            else:
                status = "parent_child_review"
                review_priority = "high"
                actions.append("review_parent_child_direction")
                reasons.append("parent/child direction is not stable enough for automatic formalization")
        else:
            actions.append("review_parent_child_direction")
            reasons.append("split queue must also review parent/child direction")
    elif "parent_direction_uncertain" in risks:
        actions.append("observe_parent_direction_signal")
        reasons.append("parent_direction_uncertain present without children, so it is not a parent/child queue blocker")

    if "weak_merge" in risks:
        if status in {"ready_candidate", "needs_review"} and not {"too_broad", "parent_direction_uncertain"} & risks:
            status = "merge_boundary_review"
            review_priority = "medium"
        actions.append("review_merge_boundary")
        reasons.append("weak_merge indicates the grouped cards or child points may be too loosely connected")

    if "contrast_uncertain" in risks:
        if status in {"ready_candidate", "needs_review"} and not {"too_broad", "evidence_thin"} & risks:
            status = "contrast_review"
            review_priority = "medium"
        elif status == "ready_candidate":
            status = "contrast_review"
            review_priority = "medium"
        if review_priority == "medium" and {"too_broad", "evidence_thin"} & risks:
            review_priority = "high"
        actions.append("review_contrast_value")
        reasons.append("contrast_uncertain means error-option evidence may not be a stable teaching signal")

    if "evidence_thin" in risks:
        if status in {"ready_candidate", "needs_review"}:
            if (
                ("contrast_heavy_review" in eng_risks or strong_contrast_support(item))
                and not {"too_broad", "weak_merge", "parent_direction_uncertain"} & risks
            ):
                status = "contrast_review"
                review_priority = max_priority(review_priority, "medium")
                actions.append("review_contrast_value")
                reasons.append(
                    "evidence_thin reclassified: contrast-heavy point mainly needs contrast review"
                )
            elif strong_direct_support(item) and not {"too_broad", "weak_merge", "parent_direction_uncertain"} & risks:
                status = "light_review"
                review_priority = max_priority(review_priority, "medium") if "contrast_uncertain" in risks else "low"
                actions.append("light_evidence_check")
                reasons.append(
                    "evidence_thin downgraded: single-card point has strong direct question support"
                )
            elif moderate_direct_support(item, eng_risks) and not {"too_broad", "weak_merge", "parent_direction_uncertain"} & risks:
                status = "light_review"
                review_priority = max_priority(review_priority, "medium") if "contrast_uncertain" in risks else "low"
                actions.append("light_evidence_check")
                reasons.append(
                    "evidence_thin downgraded: single-card point has moderate direct question support"
                )
            elif single_question_direct_candidate(item, eng_risks) and not {"too_broad", "weak_merge", "parent_direction_uncertain"} & risks:
                status = "single_question_candidate"
                review_priority = "low"
                actions.append("defer_display_strategy")
                actions.append("light_evidence_check")
                reasons.append(
                    "evidence_thin downgraded: single-question direct point should be separated, not sent to evidence supplement"
                )
            else:
                status = "evidence_supplement_candidate"
                review_priority = "medium" if question_count >= 5 or confidence == "high" else review_priority
                actions.append("supplement_evidence_context")
                reasons.append("evidence_thin means quote/question context may be insufficient")
        else:
            actions.append("supplement_evidence_context")
            reasons.append("evidence_thin means quote/question context may be insufficient")

    if virtual_parent:
        actions.append("preserve_parent_and_children")
        reasons.append("virtual parent is allowed, but must keep child points and traceable relation records")
        if risks == {"none"} and confidence == "high":
            status = "ready_candidate_with_children"
        elif status == "ready_candidate":
            status = "parent_child_review"
            review_priority = "medium"

    if children and not virtual_parent:
        actions.append("preserve_parent_and_children")
        if risks == {"none"} and status == "ready_candidate":
            status = "ready_candidate_with_children"
        if "parent_direction_uncertain" in risks:
            reasons.append("non-virtual parent has children but direction needs review")

    if "title_too_long" in eng_risks:
        if status in {"ready_candidate", "ready_candidate_with_children"}:
            status = "title_review"
        review_priority = max_priority(review_priority, "medium")
        actions.append("shorten_title")
        reasons.append("engineering check: title is longer than 18 Chinese characters")

    if "multi_card_merge_review" in eng_risks and status in {"ready_candidate", "ready_candidate_with_children"}:
        status = "merge_boundary_review"
        review_priority = max_priority(review_priority, "medium")
        actions.append("review_merge_boundary")
        reasons.append("engineering check: multi-card point needs merge-boundary review")

    if "contrast_heavy_review" in eng_risks and status in {"ready_candidate", "ready_candidate_with_children"}:
        status = "contrast_review"
        review_priority = max_priority(review_priority, "medium")
        actions.append("review_contrast_value")
        reasons.append("engineering check: contrast/error-option evidence is a large part of this point")

    if "narrow_parent_many_children_review" in eng_risks:
        status = "parent_child_review"
        review_priority = max_priority(review_priority, "high")
        actions.append("review_parent_child_direction")
        reasons.append("engineering check: one-card parent has many children and may be too narrow")

    if "broad_subtree_review" in eng_risks:
        status = "parent_child_review"
        review_priority = max_priority(review_priority, "high")
        actions.append("review_parent_child_direction")
        actions.append("review_split")
        reasons.append("engineering check: subtree question count is much larger than direct question count")
    elif "virtual_parent_review" in eng_risks:
        status = "parent_child_review"
        review_priority = max_priority(review_priority, "medium")
        actions.append("review_parent_child_direction")
        reasons.append("engineering check: virtual parent must be reviewed before formal admission")
    elif "parent_child_review" in eng_risks and status == "ready_candidate_with_children":
        review_priority = max_priority(review_priority, "medium")
        actions.append("post_admission_parent_child_check")
        reasons.append("engineering check: parent-child structure needs post-admission review")

    if "quote_context_review" in eng_risks and status in {"ready_candidate", "ready_candidate_with_children"}:
        status = "evidence_supplement_candidate"
        review_priority = max_priority(review_priority, "medium")
        actions.append("supplement_evidence_context")
        reasons.append("engineering check: evidence quote is too short or lacks display context")

    if "single_question_candidate_review" in eng_risks and status == "ready_candidate":
        status = "single_question_candidate"
        review_priority = max_priority(review_priority, "low")
        actions.append("defer_display_strategy")
        reasons.append("engineering check: single-question ordinary point should be separated from mature ready candidates")

    if not actions:
        actions.append("allow_formal_candidate")

    return {
        "exam_point_id": item["id"],
        "title": item.get("title"),
        "point_type": item.get("point_type"),
        "is_virtual_parent": virtual_parent,
        "has_children": children,
        "question_count": question_count,
        "subtree_question_count": subtree_question_count,
        "card_count": card_count,
        "split_requested": split_requested,
        "confidence": confidence,
        "risk_flags": item.get("naming_risk_flags") or [],
        "engineering_risk_flags": sorted(eng_risks),
        "admission_status": status,
        "review_priority": review_priority,
        "recommended_actions": sorted(set(actions)),
        "decision_reasons": reasons,
    }


def write_report(rows: list[dict[str, Any]]) -> None:
    status_counter = Counter(row["admission_status"] for row in rows)
    priority_counter = Counter(row["review_priority"] for row in rows)
    action_counter = Counter(action for row in rows for action in row["recommended_actions"])
    risk_counter = Counter(flag for row in rows for flag in row["risk_flags"])
    engineering_risk_counter = Counter(flag for row in rows for flag in row["engineering_risk_flags"])

    lines = [
        "# Preview v9 准入门禁报告",
        "",
        "本阶段把 v8 命名样本的风险标记转成工程决策。它不重新命名、不改变考点结构，只判断每个样本点能否进入候选正式资产，或者应进入哪类复核队列。",
        "",
        "## 输入",
        "",
        f"- source: `{source_file()}`",
        f"- items: {len(rows)}",
        "",
        "## 决策分布",
        "",
        "| status | count |",
        "|---|---:|",
    ]
    for status, count in status_counter.most_common():
        lines.append(f"| {status} | {count} |")

    lines.extend(["", "## 复核优先级", "", "| priority | count |", "|---|---:|"])
    for priority, count in priority_counter.most_common():
        lines.append(f"| {priority} | {count} |")

    lines.extend(["", "## DS 风险标记", "", "| risk | count |", "|---|---:|"])
    for risk, count in risk_counter.most_common():
        lines.append(f"| {risk} | {count} |")

    lines.extend(["", "## 工程风险标记", "", "| risk | count |", "|---|---:|"])
    for risk, count in engineering_risk_counter.most_common():
        lines.append(f"| {risk} | {count} |")

    lines.extend(["", "## 推荐动作", "", "| action | count |", "|---|---:|"])
    for action, count in action_counter.most_common():
        lines.append(f"| {action} | {count} |")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["admission_status"]].append(row)

    lines.extend(["", "## 重点复核样例"])
    for status in [
        "split_recommended",
        "parent_child_review",
        "merge_boundary_review",
        "evidence_supplement_candidate",
        "contrast_review",
        "single_question_candidate",
        "needs_review",
    ]:
        examples = grouped.get(status, [])[:8]
        if not examples:
            continue
        lines.extend(["", f"### {status}"])
        for row in examples:
            lines.extend(
                [
                    "",
                    f"- `{row['exam_point_id']}` {row['title']}",
                    f"  - confidence: {row['confidence']}; risks: {', '.join(row['risk_flags'])}",
                    f"  - engineering risks: {', '.join(row['engineering_risk_flags']) or 'none'}",
                    f"  - actions: {', '.join(row['recommended_actions'])}",
                    f"  - reason: {'; '.join(row['decision_reasons'][:3])}",
                ]
            )

    lines.extend(
        [
            "",
            "## 当前门禁规则",
            "",
            "- DS 风险只作为输入，不作为唯一通行证；脚本会额外生成 `engineering_risk_flags`。",
            "- 单卡、无 children、无工程风险、`risk_flags=[none]` 且高置信：进入 `ready_candidate`。",
            "- 多句卡点默认进入 `merge_boundary_review`，先看合并边界。",
            "- 错误项/辨析项占比较高默认进入 `contrast_review`，先看是否只是易错/辨析标签。",
            "- 虚拟父点默认进入 `parent_child_review`，必须保留子点和关系 trace。",
            "- 带 children 且子树题目数明显大于自身题目数：进入高优先级 `parent_child_review`，必要时拆分。",
            "- 标题超过 18 字会触发 `title_too_long` 和 `shorten_title` 动作。",
            "- 只有 1 道题支撑且无子点的普通点进入 `single_question_candidate`，先与成熟 ready 候选分开，等待前端展示策略确认。",
            "- 句卡原文过短或缺少展示上下文会触发 `quote_context_review`，进入 `evidence_supplement_candidate` 补上下文后再提升。",
            "- `too_broad` 只有在拆分信号较强时进入 `split_recommended`；否则保留为观察或复核。",
            "- `parent_direction_uncertain` 只有在确实存在 children 时才阻断；轻微方向问题可进入带子点候选并做后置检查。",
            "- `weak_merge`：进入 `merge_boundary_review`，专门复核合并边界。",
            "- `contrast_uncertain`：进入 `contrast_review`，专门复核错误项/辨析项是否有教学价值。",
            "- `evidence_thin`：进入 `evidence_supplement_candidate`，不是废弃，而是补 quote/context 后再提升。",
        ]
    )

    (OUT_DIR / out_name("admission_report", "md")).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source = source_file()
    payload = read_json(source)
    items = payload.get("items", [])
    rows = [decide(item) for item in items]

    ready_statuses = {"ready_candidate", "ready_candidate_with_children"}
    ready_ids = {row["exam_point_id"] for row in rows if row["admission_status"] in ready_statuses}
    ready_items = [item for item in items if item["id"] in ready_ids]

    write_json(
        OUT_DIR / out_name("admission_decisions", "json"),
        {
            "schema_version": "preview_v9_admission_decisions_v1",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_file": str(source),
            "items": rows,
        },
    )
    write_jsonl(OUT_DIR / out_name("admission_decisions", "jsonl"), rows)
    write_json(
        OUT_DIR / out_name("formal_candidate_draft", "json"),
        {
            "schema_version": "preview_v9_formal_candidate_draft_v1",
            "note": "Only ready_candidate and ready_candidate_with_children items from the configured v8 naming sample. This is still a draft, not the production asset.",
            "source_file": str(source),
            "items": ready_items,
        },
    )
    write_report(rows)

    summary = {
        "status": "ok",
        "source_count": len(items),
        "ready_candidate_count": len(ready_items),
        "status_distribution": dict(Counter(row["admission_status"] for row in rows).most_common()),
        "priority_distribution": dict(Counter(row["review_priority"] for row in rows).most_common()),
        "risk_distribution": dict(Counter(flag for row in rows for flag in row["risk_flags"]).most_common()),
        "engineering_risk_distribution": dict(
            Counter(flag for row in rows for flag in row["engineering_risk_flags"]).most_common()
        ),
        "outputs": {
            "admission_decisions": str(OUT_DIR / out_name("admission_decisions", "json")),
            "formal_candidate_draft": str(OUT_DIR / out_name("formal_candidate_draft", "json")),
            "report": str(OUT_DIR / out_name("admission_report", "md")),
        },
    }
    write_json(OUT_DIR / out_name("summary", "json"), summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
