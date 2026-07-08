from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
KG_ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(KG_ROOT / "lib"))

from kg_common import DEFAULT_KG_WORK_DIR, ensure_dir, read_jsonl, write_text  # noqa: E402

ABBREVIATION_RE = re.compile(r"\b[A-Z][A-Z0-9]{2,}(?:/[A-Z0-9]{2,})?\b")


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 5 term alias map for v7 KG pilot.")
    parser.add_argument(
        "--eligible-units",
        type=Path,
        default=DEFAULT_KG_WORK_DIR / "phase0_quality_gate" / "eligible_units.jsonl",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_KG_WORK_DIR / "phase5_terms")
    args = parser.parse_args()

    # 读取 eligible units
    units = {unit["unit_id"]: unit for unit in read_jsonl(args.eligible_units)}

    # Step 1: 从 unit.terms 收集 (en, zh) 对
    # bucket: normalized_key -> {en_set, zh_set, unit_ids_set}
    buckets: dict[str, dict[str, set]] = {}

    for unit_id, unit in units.items():
        for term in unit.get("terms") or []:
            en = _norm(term.get("en"))
            zh = _norm(term.get("zh"))
            if not en and not zh:
                continue
            # 用全称作为 term_key（如果有 en 用 en，否则用 zh）
            key = _canonical_key(en, zh)
            bucket = buckets.setdefault(key, _empty_bucket())
            if en:
                bucket["en"].add(en)
            if zh:
                bucket["zh"].add(zh)
            bucket["unit_ids"].add(unit_id)

    # Step 2: 从 en_quote 抽缩写，尝试匹配到已有 bucket
    # 先建立 unit_id -> bucket_key 的反向索引
    unit_to_keys: dict[str, set[str]] = defaultdict(set)
    for key, bucket in buckets.items():
        for uid in bucket["unit_ids"]:
            unit_to_keys[uid].add(key)

    for unit_id, unit in units.items():
        for abbr_match in ABBREVIATION_RE.finditer(unit.get("en_quote") or ""):
            abbr = abbr_match.group()
            abbr_lower = abbr.lower()
            # 检查这个缩写是否已经有匹配的全称 bucket
            matched_bucket = _match_abbr_to_bucket(abbr_lower, buckets)
            if matched_bucket is not None:
                # 合并到已有 bucket
                buckets[matched_bucket]["en"].add(abbr)
                buckets[matched_bucket]["abbreviations"].add(abbr)
                buckets[matched_bucket]["unit_ids"].add(unit_id)
            else:
                # 独立缩写，新建 bucket
                key = abbr_lower
                bucket = buckets.setdefault(key, _empty_bucket())
                bucket["en"].add(abbr)
                bucket["abbreviations"].add(abbr)
                bucket["unit_ids"].add(unit_id)

    # Step 3: 构建输出
    aliases = []
    for key, bucket in sorted(buckets.items()):
        record: dict[str, Any] = {
            "term": key,
            "en": sorted(bucket["en"]),
            "zh": sorted(bucket["zh"]),
            "abbreviations": sorted(bucket["abbreviations"]),
            "aliases": [],
            "unit_count": len(bucket["unit_ids"]),
        }
        # risk_flags
        risks = _risk_flags(bucket)
        if risks:
            record["risk_flags"] = risks
        aliases.append(record)

    # 输出
    out_dir = ensure_dir(args.out_dir)
    out_path = out_dir / "p5_term_alias_map.json"
    write_text(out_path, json.dumps(aliases, ensure_ascii=False, indent=2))
    print(json.dumps({"term_count": len(aliases), "output": str(out_path)}, ensure_ascii=False, indent=2))

    # 输出 preview
    preview = _preview_markdown(aliases)
    preview_dir = ensure_dir(args.out_dir / ".." / "previews")
    write_text(preview_dir / "p5_term_alias_preview.md", preview)


def _empty_bucket() -> dict[str, set]:
    return {"en": set(), "zh": set(), "abbreviations": set(), "unit_ids": set()}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _canonical_key(en: str, zh: str) -> str:
    """用英文全称小写作为 term_key，没有英文则用中文"""
    if en:
        return en.lower().strip()
    return zh.strip()


def _match_abbr_to_bucket(abbr_lower: str, buckets: dict[str, dict[str, set]]) -> str | None:
    """尝试把缩写匹配到已有全称bucket：检查缩写出现的unit_ids与全称bucket的unit_ids重叠度"""
    # 如果缩写本身已经是一个bucket key，返回它自己
    if abbr_lower in buckets:
        return abbr_lower

    # 找所有en中包含缩写内容的bucket（比如 "k"
    candidates = []
    for key, bucket in buckets.items():
        bucket_en_lower = key.lower()
        # 缩写是否出现在全称中（去掉空格比较）
        # 比如 aml -> antimoneylaundering
        abbr_flat = abbr_lower.replace(" ", "")
        en_flat = bucket_en_lower.replace(" ", "")
        if abbr_flat in en_flat:
            candidates.append((key, bucket))

    # 如果有候选，选第一个（理论上应该只有一个）
    if candidates:
        return candidates[0][0]

    return None


def _risk_flags(bucket: dict[str, set]) -> list[str]:
    flags = []
    if len(bucket["zh"]) > 1:
        flags.append("multiple_zh")
    if len(bucket["en"]) > 1:
        flags.append("multiple_en")
    if not bucket["zh"]:
        flags.append("missing_zh")
    if not bucket["en"]:
        flags.append("missing_en")
    if bucket["abbreviations"] and not any(zh for zh in bucket["zh"]):
        flags.append("abbreviation_no_zh")
    return flags


def _preview_markdown(aliases: list[dict[str, Any]]) -> str:
    lines = [
        "# Phase 5 Term Alias Map Preview",
        "",
        f"- terms: {len(aliases)}",
        "",
        "| term | en | zh | abbreviations | unit_count | risks |",
        "|---|---|---|---:|---:|---|",
    ]
    for item in aliases[:80]:
        risks = ", ".join(item.get("risk_flags") or [])
        lines.append(
            f"| {item['term']} | {', '.join(item['en'])} | {', '.join(item['zh'])} | "
            f"{', '.join(item['abbreviations'])} | {item['unit_count']} | {risks} |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()