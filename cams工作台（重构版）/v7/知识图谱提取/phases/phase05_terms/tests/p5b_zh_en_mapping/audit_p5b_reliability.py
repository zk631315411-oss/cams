from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TEST_DIR = Path(__file__).resolve().parent
P5B_OUTPUT = TEST_DIR / "outputs" / "p5b_zh_en_mapping_all.json"
AUDIT_JSON = TEST_DIR / "outputs" / "p5b_zh_en_mapping_audit_all.json"
AUDIT_MD = TEST_DIR / "previews" / "p5b_zh_en_mapping_audit_all.md"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def is_ascii_text(value: str) -> bool:
    return bool(value) and all(ord(ch) < 128 for ch in value)


def is_acronym(value: str) -> bool:
    text = re.sub(r"[^A-Za-z0-9]", "", value or "")
    return len(text) >= 2 and text.upper() == text and bool(re.search(r"[A-Z]", text))


def norm_en_variant(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()
    text = re.sub(r"\b(reports|officers|controls|transactions|institutions|agencies|committees|databases|procedures)\b", lambda m: m.group(1)[:-1], text)
    text = re.sub(r"\b(s)\b", "", text)
    return re.sub(r"\s+", " ", text).strip()


def norm_zh_variant(value: str) -> str:
    text = re.sub(r"[《》“”\"'（）()\s]", "", value or "")
    text = text.replace("和", "与")
    text = text.replace("报告负责人", "报告官")
    text = text.replace("金融情报中心", "金融情报机构")
    text = text.replace("金融情报单位", "金融情报机构")
    return text


def classify_mapping(row: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    en = row["canonical_en"]
    zh = row["canonical_zh"]
    if is_ascii_text(zh):
        labels.append("zh_is_ascii_or_acronym")
    if is_acronym(en) and zh.upper() == en.upper():
        labels.append("untranslated_acronym")
    if row["decision"] == "clean" and row["count"] == 1:
        labels.append("clean_low_frequency")
    if row["decision"] == "clean" and row["count"] >= 10:
        labels.append("clean_high_frequency")
    if row["decision"] == "needs_review" and row["count"] >= 10:
        labels.append("high_frequency_conflict")
    return labels


def classify_en_conflict(row: dict[str, Any]) -> str:
    normalized = {norm_zh_variant(value) for value in row["zh_options"]}
    if len(normalized) == 1:
        return "format_or_wording_variant"
    if any(is_ascii_text(value) for value in row["zh_options"]):
        return "acronym_translation_variant"
    return "translation_variant"


def classify_zh_conflict(row: dict[str, Any]) -> str:
    normalized = {norm_en_variant(value) for value in row["en_options"]}
    if len(normalized) == 1:
        return "plural_or_wording_variant"
    if any(is_acronym(value) for value in row["en_options"]):
        return "abbreviation_full_form_variant"
    return "english_synonym_variant"


def sample_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return rows[:limit]


def main() -> None:
    payload = read_json(P5B_OUTPUT)
    mappings: list[dict[str, Any]] = payload["mappings"]
    en_conflicts: list[dict[str, Any]] = payload["en_conflicts"]
    zh_conflicts: list[dict[str, Any]] = payload["zh_conflicts"]

    labels_by_mapping: dict[str, list[str]] = {}
    label_counts: Counter[str] = Counter()
    for row in mappings:
        key = f"{row['en_key']}\t{row['canonical_zh']}"
        labels = classify_mapping(row)
        labels_by_mapping[key] = labels
        label_counts.update(labels)

    en_conflict_classes = Counter(classify_en_conflict(row) for row in en_conflicts)
    zh_conflict_classes = Counter(classify_zh_conflict(row) for row in zh_conflicts)

    clean_rows = [row for row in mappings if row["decision"] == "clean"]
    review_rows = [row for row in mappings if row["decision"] == "needs_review"]
    suspicious_clean = [
        row
        for row in clean_rows
        if "zh_is_ascii_or_acronym" in labels_by_mapping[f"{row['en_key']}\t{row['canonical_zh']}"]
        or "untranslated_acronym" in labels_by_mapping[f"{row['en_key']}\t{row['canonical_zh']}"]
    ]
    high_frequency_review = sorted([row for row in review_rows if row["count"] >= 10], key=lambda row: (-row["count"], row["en_key"], row["canonical_zh"]))
    clean_high_frequency = sorted([row for row in clean_rows if row["count"] >= 10], key=lambda row: (-row["count"], row["en_key"]))
    clean_low_frequency = sorted([row for row in clean_rows if row["count"] == 1], key=lambda row: (row["en_key"], row["canonical_zh"]))

    audit = {
        "summary": payload["summary"],
        "audit_counts": {
            "clean_high_frequency_count": len(clean_high_frequency),
            "clean_low_frequency_count": len(clean_low_frequency),
            "suspicious_clean_count": len(suspicious_clean),
            "high_frequency_review_count": len(high_frequency_review),
            "mapping_label_counts": dict(label_counts),
            "en_conflict_classes": dict(en_conflict_classes),
            "zh_conflict_classes": dict(zh_conflict_classes),
        },
        "samples": {
            "clean_high_frequency": sample_rows(clean_high_frequency, 40),
            "suspicious_clean": sample_rows(suspicious_clean, 80),
            "high_frequency_review": sample_rows(high_frequency_review, 80),
            "clean_low_frequency": sample_rows(clean_low_frequency, 40),
            "en_conflicts": sample_rows(en_conflicts, 80),
            "zh_conflicts": sample_rows(zh_conflicts, 80),
        },
    }

    write_json(AUDIT_JSON, audit)
    write_text(AUDIT_MD, preview_markdown(audit))
    print(json.dumps({"audit": str(AUDIT_JSON), **audit["audit_counts"]}, ensure_ascii=False, indent=2))


def table_rows(rows: list[dict[str, Any]], columns: list[str], limit: int = 40) -> list[str]:
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in rows[:limit]:
        values = []
        for col in columns:
            value = row.get(col, "")
            if isinstance(value, list):
                value = ", ".join(map(str, value))
            values.append(str(value).replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def preview_markdown(audit: dict[str, Any]) -> str:
    lines = ["# P5B zh/en reliability audit", "", "## Summary", ""]
    for key, value in audit["summary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Audit Counts", ""])
    for key, value in audit["audit_counts"].items():
        lines.append(f"- {key}: {value}")

    samples = audit["samples"]
    sections = [
        ("Clean High Frequency", "clean_high_frequency", ["canonical_en", "canonical_zh", "count"]),
        ("Suspicious Clean", "suspicious_clean", ["canonical_en", "canonical_zh", "count", "risk_flags"]),
        ("High Frequency Review", "high_frequency_review", ["canonical_en", "canonical_zh", "count", "risk_flags"]),
        ("Clean Low Frequency Sample", "clean_low_frequency", ["canonical_en", "canonical_zh", "count"]),
        ("English Conflicts", "en_conflicts", ["canonical_en", "zh_options", "total_count"]),
        ("Chinese Conflicts", "zh_conflicts", ["canonical_zh", "en_options", "total_count"]),
    ]
    for title, key, columns in sections:
        lines.extend(["", f"## {title}", ""])
        lines.extend(table_rows(samples[key], columns))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()

