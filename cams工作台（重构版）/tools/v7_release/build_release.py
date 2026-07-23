#!/usr/bin/env python3
"""Create an immutable, frontend-ready V7 workbench release package.

The publisher deliberately accepts a completed evidence directory as an input.
It never reads experimental runs implicitly and never calls an LLM or retrieval
service. A release is therefore a reproducible snapshot rather than a live view
of the V7 pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


RELEASE_SCHEMA = "cams-v7-workbench-release/v1"
UNIT_ID_RE = re.compile(r"^v7u_N\d+$")
FORBIDDEN_V6_ID_RE = re.compile(r"\bv6[a-z_\-]*N\d+\b", re.IGNORECASE)
EVIDENCE_STATUSES = {"direct", "indirect", "negative", "none"}


class ReleaseError(ValueError):
    """Raised when source assets cannot form a safe release."""


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReleaseError(f"Missing required input: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compact_unit(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "unit_id": raw["unit_id"],
        "chapter": raw.get("chapter", ""),
        "heading_context": raw.get("heading_context") or [],
        "heading_context_zh": raw.get("heading_context_zh") or [],
        "knowledge_zh": raw.get("knowledge_zh", ""),
        "knowledge_en": raw.get("knowledge_en", ""),
        "zh_display_text": raw.get("zh_display_text") or raw.get("knowledge_zh", ""),
        "zh_context_full": raw.get("zh_context_full"),
        "en_quote": raw.get("en_quote", ""),
        "terms": raw.get("terms") or [],
        "pdf_page": raw.get("pdf_page"),
        "printed_page": raw.get("printed_page"),
        "page_span": raw.get("page_span") or [],
        "unit_type": raw.get("unit_type") or raw.get("type") or "unknown",
        "evidence_status": raw.get("evidence_status") or "none",
        "risk_flags": normalize_flags(raw.get("risk_flags")),
        "unit_order": raw.get("unit_order"),
    }


def collect_ids(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "unit_id" and isinstance(item, str):
                yield item
            elif key == "cited_unit_ids" and isinstance(item, list):
                yield from (candidate for candidate in item if isinstance(candidate, str))
            else:
                yield from collect_ids(item)
    elif isinstance(value, list):
        for item in value:
            yield from collect_ids(item)


def has_forbidden_v6_id(value: Any) -> bool:
    if isinstance(value, str):
        return bool(FORBIDDEN_V6_ID_RE.search(value))
    if isinstance(value, dict):
        return any(has_forbidden_v6_id(item) for item in value.values())
    if isinstance(value, list):
        return any(has_forbidden_v6_id(item) for item in value)
    return False


def normalize_flags(value: Any) -> list[str]:
    """Convert upstream string/object risk markers into stable display labels."""
    if not value:
        return []
    if not isinstance(value, list):
        value = [value]
    labels = []
    for flag in value:
        if isinstance(flag, str):
            labels.append(flag)
        elif isinstance(flag, dict):
            labels.append(str(flag.get("code") or flag.get("name") or flag.get("type") or json.dumps(flag, ensure_ascii=False, sort_keys=True)))
        else:
            labels.append(str(flag))
    return labels


def normalize_evidence(raw: dict[str, Any], unit_ids: set[str]) -> dict[str, Any]:
    question_id = raw.get("question_id")
    if not isinstance(question_id, str) or not question_id:
        raise ReleaseError("Evidence result has no question_id")

    option_analysis = raw.get("option_analysis") or []
    if not isinstance(option_analysis, list):
        raise ReleaseError(f"{question_id}: option_analysis must be a list")

    normalized_options = []
    risk_flags: list[str] = []
    for option in option_analysis:
        status = option.get("evidence_status") or "none"
        if status not in EVIDENCE_STATUSES:
            raise ReleaseError(f"{question_id}: unsupported evidence status '{status}'")
        cards = option.get("evidence_cards") or []
        for card in cards:
            unit_id = card.get("unit_id")
            if unit_id not in unit_ids:
                raise ReleaseError(f"{question_id}: evidence references unknown unit {unit_id!r}")
        normalized_options.append(
            {
                "option": option.get("option"),
                "judgement": option.get("judgement") or "unknown",
                "decision_basis": option.get("decision_basis") or "unknown",
                "decision_reason": option.get("decision_reason") or "",
                "evidence_status": status,
                "evidence_cards": cards,
            }
        )

    checks = raw.get("validation_checks") or []
    if isinstance(checks, dict):
        checks = [checks]
    for check in checks:
        if isinstance(check, dict) and check.get("ok") is False:
            risk_flags.append("validation_failed")

    explanation = raw.get("generated_explanation") or None
    if explanation:
        for unit_id in collect_ids(explanation):
            if unit_id not in unit_ids:
                raise ReleaseError(f"{question_id}: explanation references unknown unit {unit_id!r}")
        readiness = explanation.get("software_readiness") or {}
        risk_flags.extend(normalize_flags(readiness.get("risk_flags")))
        if readiness.get("ready") is False:
            risk_flags.append("explanation_not_ready")

    if has_forbidden_v6_id(raw):
        raise ReleaseError(f"{question_id}: V6 card identifier found in evidence result")

    reference_audit = (explanation or {}).get("reference_appendix") or {}
    if reference_audit.get("cn_en_conflict") or reference_audit.get("blind_final_conflict"):
        risk_flags.append("reference_answer_conflict")

    if any(item["evidence_status"] in {"none", "negative"} for item in normalized_options):
        risk_flags.append("weak_or_missing_option_evidence")

    return {
        "question_id": question_id,
        "pipeline_status": raw.get("pipeline_status") or "unknown",
        "predicted_answer": raw.get("predicted_answer") or [],
        "chapter_mappings": raw.get("chapter_mappings") or [],
        "option_analysis": normalized_options,
        "generated_explanation": explanation,
        "reference_audit": reference_audit,
        "risk_flags": sorted(set(normalize_flags(risk_flags))),
    }


def build_chapters(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chapters: dict[str, dict[str, Any]] = {}
    for unit in units:
        title = unit["chapter"] or (unit["heading_context"] or ["未归类教材内容"])[0]
        chapter = chapters.setdefault(title, {"title": title, "unit_ids": [], "sections": defaultdict(list)})
        chapter["unit_ids"].append(unit["unit_id"])
        heading = unit["heading_context"]
        section = " / ".join(heading[1:]) if len(heading) > 1 else title
        chapter["sections"][section].append(unit["unit_id"])

    return [
        {
            "chapter_id": f"chapter-{index:02d}",
            "title": chapter["title"],
            "unit_ids": chapter["unit_ids"],
            "sections": [{"title": title, "unit_ids": ids} for title, ids in chapter["sections"].items()],
        }
        for index, chapter in enumerate(chapters.values(), start=1)
    ]


def create_release(args: argparse.Namespace) -> dict[str, Any]:
    units_source = Path(args.units).resolve()
    questions_source = Path(args.questions).resolve()
    evidence_root = Path(args.evidence_dir).resolve()
    output_root = Path(args.output_dir).resolve()

    unit_doc = read_json(units_source)
    raw_units = unit_doc.get("units") or []
    if not raw_units:
        raise ReleaseError("The unit source contains no units")
    units = [compact_unit(item) for item in raw_units]
    unit_ids = {unit["unit_id"] for unit in units}
    if len(unit_ids) != len(units) or any(not UNIT_ID_RE.match(unit_id) for unit_id in unit_ids):
        raise ReleaseError("Unit IDs must be unique V7 unit identifiers")
    if has_forbidden_v6_id(units):
        raise ReleaseError("V6 card identifier found in the unit source")

    question_doc = read_json(questions_source)
    raw_questions = question_doc.get("items") or question_doc.get("questions") or []
    questions_by_id = {item.get("question_id") or item.get("id"): item for item in raw_questions}
    if not questions_by_id or None in questions_by_id:
        raise ReleaseError("Question source must contain uniquely identified items")

    evidence_by_question: dict[str, dict[str, Any]] = {}
    for evidence_file in sorted(evidence_root.rglob("q_*.json")):
        evidence = normalize_evidence(read_json(evidence_file), unit_ids)
        question_id = evidence["question_id"]
        if question_id in evidence_by_question:
            raise ReleaseError(f"Duplicate evidence result for {question_id}: {evidence_file}")
        if question_id not in questions_by_id:
            raise ReleaseError(f"Evidence result has no matching standardized question: {question_id}")
        evidence_by_question[question_id] = evidence

    published_count = 0
    release_questions = []
    for question_id, raw in sorted(questions_by_id.items()):
        evidence = evidence_by_question.get(question_id)
        published = bool(evidence and evidence["pipeline_status"] == "ok")
        published_count += int(published)
        release_questions.append(
            {
                "question_id": question_id,
                "question_type": raw.get("question_type") or "unknown",
                "tier": raw.get("tier") or "unknown",
                "stem_zh": raw.get("stem_zh") or raw.get("stem") or "",
                "stem_en": raw.get("stem_en") or "",
                "options": raw.get("options") or {},
                "answer_reference": raw.get("answer_final") or raw.get("answer") or [],
                "chapter_mappings": (evidence or {}).get("chapter_mappings") or raw.get("chapter_mappings") or [],
                "risk_flags": sorted(set(normalize_flags(raw.get("risk_flags")) + normalize_flags((evidence or {}).get("risk_flags")))),
                "publication_status": "published" if published else "unpublished",
                "evidence_status": "available" if published else "not_published",
            }
        )

    release_id = args.release_id or datetime.now(timezone.utc).strftime("v7-%Y%m%dT%H%M%SZ")
    if not re.fullmatch(r"v7-[A-Za-z0-9T._-]+", release_id):
        raise ReleaseError("release_id must start with 'v7-' and contain only URL-safe characters")
    if output_root.exists():
        if not args.overwrite:
            raise ReleaseError(f"Release output already exists: {output_root}. Use --overwrite to replace it.")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    write_json(output_root / "units.json", {"schema_version": RELEASE_SCHEMA, "items": units})
    write_json(output_root / "chapters.json", {"schema_version": RELEASE_SCHEMA, "items": build_chapters(units)})
    write_json(output_root / "questions.json", {"schema_version": RELEASE_SCHEMA, "items": release_questions})
    write_json(output_root / "evidence.json", {"schema_version": RELEASE_SCHEMA, "items": list(evidence_by_question.values())})

    files = {}
    for name in ("units.json", "chapters.json", "questions.json", "evidence.json"):
        path = output_root / name
        files[name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    manifest = {
        "schema_version": RELEASE_SCHEMA,
        "release_id": release_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "published",
        "source": {
            "units": {"path": str(units_source), "sha256": sha256_file(units_source), "freeze_manifest": args.freeze_manifest},
            "questions": {"path": str(questions_source), "sha256": sha256_file(questions_source)},
            "evidence_dir": str(evidence_root),
        },
        "counts": {
            "units": len(units),
            "questions": len(release_questions),
            "published_questions": published_count,
            "unpublished_questions": len(release_questions) - published_count,
            "evidence_results": len(evidence_by_question),
        },
        "validation": {"valid": True, "errors": [], "forbidden_v6_ids": False},
        "files": files,
    }
    write_json(output_root / "manifest.json", manifest)

    if args.activate:
        active_path = output_root.parent / "active.json"
        write_json(active_path, {"schema_version": RELEASE_SCHEMA, "release_id": release_id, "release_path": output_root.name, "manifest": f"{output_root.name}/manifest.json"})
    return manifest


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--units", required=True, help="Frozen v7_bilingual_units.json")
    parser.add_argument("--questions", required=True, help="Standardized v7_questions.json")
    parser.add_argument("--evidence-dir", required=True, help="Completed evidence run directory")
    parser.add_argument("--output-dir", required=True, help="New immutable release directory")
    parser.add_argument("--release-id", help="Release identifier, defaults to UTC timestamp")
    parser.add_argument("--freeze-manifest", default="", help="Optional unit freeze manifest path recorded in metadata")
    parser.add_argument("--activate", action="store_true", help="Write active.json next to the release directory")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output directory")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        manifest = create_release(parse_args(argv or sys.argv[1:]))
    except ReleaseError as exc:
        print(f"Release failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"release_id": manifest["release_id"], "counts": manifest["counts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
