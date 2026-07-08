from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
V6_DIR = HERE / "work" / "preview_v6"
OUT_DIR = V6_DIR / "dry_run_20260630_mid"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compact(text: Any, limit: int = 120) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)] + "..."


def sample_by_label(items: list[dict[str, Any]], label_key: str, limit_per_label: int) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        grouped[str(item.get(label_key) or "")].append(item)
    sample: list[dict[str, Any]] = []
    for label in sorted(grouped):
        rows = grouped[label]
        rows.sort(key=lambda x: (-int(x.get("score") or 0), str(x.get("pair_id") or x.get("edge_key") or "")))
        sample.extend(rows[:limit_per_label])
    return sample


def relation_risk(item: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    label = item.get("draft_label")
    text = " ".join(
        [
            str(item.get("card_a", {}).get("quote") or ""),
            str(item.get("card_b", {}).get("quote") or ""),
            str(item.get("card_a", {}).get("title_placeholder") or ""),
            str(item.get("card_b", {}).get("title_placeholder") or ""),
        ]
    )
    if label == "merge_same_point" and any(word in text for word in ("案例", "证据", "700", "汇往国外", "超量装载", "装载不足")):
        flags.append("merge_may_mix_definition_case_or_parallel_method")
    if label == "parent_child" and (
        ("OFAC" in text or "海外资产控制办公室" in text)
        and ("FATF" in text or "金融行动特别工作组" in text or "金融情报机构" in text)
    ):
        flags.append("parent_child_cross_institution")
    if label == "sibling_under_parent" and any(word in text for word in ("AMLD", "AMLA", "爱国者法案", "BSA", "FinCEN")):
        flags.append("sibling_cross_framework")
    if label == "sibling_under_parent" and int(item.get("score") or 0) <= 60:
        flags.append("low_score_sibling")
    return flags


def contrast_risk(item: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    action = item.get("draft_action")
    option_text = str(item.get("option_text") or "")
    quote = str(item.get("quote") or "")
    text = " ".join([option_text, quote])
    anchors = (
        "OFAC",
        "FATF",
        "FIU",
        "SDN",
        "制裁",
        "评估",
        "DNFBP",
        "客户",
        "风险",
        "监控",
        "报告",
        "名单",
        "董事会",
        "合规",
        "传票",
        "SAR",
        "STR",
    )
    shared_anchor = any(word in option_text and word in quote for word in anchors)
    if action == "count_in_exam_point" and any(word in text for word in ("OFAC", "FATF", "制裁", "评估", "DNFBP")) and not shared_anchor:
        flags.append("count_sensitive_sanctions_or_list_topic")
    if action == "hold_for_review" and any(word in text for word in ("董事会", "CEO", "传票", "SAR", "STR", "保密", "金融情报机构")):
        flags.append("hold_may_be_clear_responsibility_boundary")
    if action == "trace_only" and any(word in text for word in ("审计", "董事会", "合规", "传票", "SAR", "STR")):
        flags.append("trace_may_need_hold")
    return flags


def main() -> None:
    relation_items = read_json(V6_DIR / "relation_draft.json")["items"]
    contrast_items = read_json(V6_DIR / "contrast_draft.json")["items"]

    relation_risks = []
    for item in relation_items:
        risks = relation_risk(item)
        if risks:
            relation_risks.append(
                {
                    "pair_id": item["pair_id"],
                    "draft_label": item["draft_label"],
                    "score": item.get("score"),
                    "risks": risks,
                    "card_a": item.get("card_a", {}).get("card_id"),
                    "card_a_text": compact(item.get("card_a", {}).get("quote")),
                    "card_b": item.get("card_b", {}).get("card_id"),
                    "card_b_text": compact(item.get("card_b", {}).get("quote")),
                }
            )

    contrast_risks = []
    for item in contrast_items:
        risks = contrast_risk(item)
        if risks:
            contrast_risks.append(
                {
                    "edge_key": item["edge_key"],
                    "draft_action": item["draft_action"],
                    "classification": item.get("classification"),
                    "risks": risks,
                    "option_text": compact(item.get("option_text")),
                    "quote": compact(item.get("quote")),
                }
            )

    relation_sample = sample_by_label(relation_items, "draft_label", 30)
    contrast_sample = sample_by_label(contrast_items, "draft_action", 40)
    summary = {
        "relation_count": len(relation_items),
        "relation_distribution": dict(Counter(item["draft_label"] for item in relation_items).most_common()),
        "relation_risk_count": len(relation_risks),
        "relation_risk_distribution": dict(Counter(flag for item in relation_risks for flag in item["risks"]).most_common()),
        "contrast_count": len(contrast_items),
        "contrast_distribution": dict(Counter(item["draft_action"] for item in contrast_items).most_common()),
        "contrast_risk_count": len(contrast_risks),
        "contrast_risk_distribution": dict(Counter(flag for item in contrast_risks for flag in item["risks"]).most_common()),
        "verdict": "mid_batch_dry_run_ready_with_observation_flags",
        "note": "Dry-run report only. It does not write final frontend assets.",
    }

    write_json(OUT_DIR / "summary.json", summary)
    write_json(OUT_DIR / "relation_risks.json", {"items": relation_risks})
    write_json(OUT_DIR / "contrast_risks.json", {"items": contrast_risks})
    write_json(OUT_DIR / "relation_sample_120.json", {"items": relation_sample})
    write_json(OUT_DIR / "contrast_sample_120.json", {"items": contrast_sample})

    lines = [
        "# Preview v6 中批量 dry-run 检查报告",
        "",
        "本报告只检查 `work/preview_v6` 草稿产物，不写入正式前端资产。",
        "",
        "## 总览",
        "",
        f"- relation: {summary['relation_count']} 条；风险标记 {summary['relation_risk_count']} 条",
        f"- contrast: {summary['contrast_count']} 条；风险标记 {summary['contrast_risk_count']} 条",
        f"- 结论：{summary['verdict']}",
        "",
        "## Relation 分布",
        "",
    ]
    for key, value in summary["relation_distribution"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Relation 风险标记", ""])
    for key, value in summary["relation_risk_distribution"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Contrast 分布", ""])
    for key, value in summary["contrast_distribution"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Contrast 风险标记", ""])
    for key, value in summary["contrast_risk_distribution"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## 下一步", "", "- 可进入中批量 dry-run；重点观察 relation_risks 和 contrast_risks 中的标记项。"])
    (OUT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
