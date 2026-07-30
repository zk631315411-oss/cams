from __future__ import annotations

import difflib
import hashlib
import json
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import settings
from .db import AuditEvent, Question, Version, utcnow


QUESTION_ID_RE = re.compile(r"v7_q_\d{6}")
OPTION_RE = re.compile(
    r"^-\s*([A-F])\.\s*(.*?)\s*\n\s*English:\s*(.*?)(?=\n-\s*[A-F]\.|\n##\s|\Z)",
    re.MULTILINE | re.DOTALL,
)
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
EVIDENCE_ID_RE = re.compile(r"`(v7u_[A-Za-z0-9_-]+)`")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalize_stem(value: str) -> str:
    value = value.casefold().replace("\u3000", " ")
    return re.sub(r"[\W_]+", "", value, flags=re.UNICODE)


def _line_value(markdown: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}[：:]\s*(.*?)\s*$", markdown, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _section(markdown: str, title_contains: str) -> str:
    matches = list(SECTION_RE.finditer(markdown))
    for index, match in enumerate(matches):
        if title_contains in match.group(1):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
            return markdown[start:end].strip()
    return ""


def parse_markdown(markdown: str) -> dict[str, Any]:
    options = []
    for match in OPTION_RE.finditer(markdown):
        options.append(
            {
                "label": match.group(1),
                "zh": match.group(2).strip(),
                "en": match.group(3).strip(),
            }
        )
    answer_text = _section(markdown, "AI答案")
    answer_letters = re.findall(r"[A-F]", answer_text.splitlines()[0] if answer_text else "")
    stem_zh = _line_value(markdown, "题干")
    stem_en = _line_value(markdown, "英文题干")
    return {
        "title": markdown.splitlines()[0].lstrip("# ").strip() if markdown else "",
        "chapter": _line_value(markdown, "教材章节"),
        "question_type": _line_value(markdown, "题型") or "unknown",
        "stem_zh": stem_zh,
        "stem_en": stem_en,
        "options": options,
        "answer_letters": answer_letters,
        "exam_point": _section(markdown, "考点"),
        "core_analysis": _section(markdown, "核心解析"),
        "wrong_analysis": _section(markdown, "错误项分析"),
        "reminder": _section(markdown, "易错提醒"),
        "evidence_text": _section(markdown, "教材原文依据"),
        "evidence_unit_ids": list(dict.fromkeys(EVIDENCE_ID_RE.findall(_section(markdown, "教材原文依据")))),
        "has_evidence_section": "## 【教材原文依据】" in markdown,
    }


def _replace_line(markdown: str, label: str, value: str) -> str:
    pattern = re.compile(rf"^{re.escape(label)}[：:].*$", re.MULTILINE)
    replacement = f"{label}：{value}"
    return pattern.sub(replacement, markdown, count=1) if pattern.search(markdown) else markdown


def _replace_section(markdown: str, title_contains: str, value: str) -> str:
    matches = list(SECTION_RE.finditer(markdown))
    for index, match in enumerate(matches):
        if title_contains in match.group(1):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
            return markdown[: match.end()] + "\n\n" + value.strip() + "\n\n" + markdown[end:].lstrip("\n")
    return markdown


def apply_content_patch(markdown: str, patch: dict[str, Any]) -> str:
    if isinstance(patch.get("markdown"), str):
        return patch["markdown"].replace("\r\n", "\n").rstrip() + "\n"
    fields = patch.get("fields") or {}
    for key, label in (("stem_zh", "题干"), ("stem_en", "英文题干"), ("question_type", "题型")):
        if key in fields:
            markdown = _replace_line(markdown, label, str(fields[key]))
    if "options" in fields:
        lines = ["选项：", ""]
        for option in fields["options"]:
            lines.extend(
                [
                    f"- {option['label']}. {option.get('zh', '').strip()}",
                    f"  English: {option.get('en', '').strip()}",
                ]
            )
        start = re.search(r"^选项[：:].*$", markdown, re.MULTILINE)
        first_section = re.search(r"^##\s", markdown[start.end() :] if start else "", re.MULTILINE)
        if start and first_section:
            end = start.end() + first_section.start()
            markdown = markdown[: start.start()] + "\n".join(lines) + "\n\n" + markdown[end:]
    if "answer_letters" in fields:
        value = "、".join(fields["answer_letters"])
        markdown = _replace_section(markdown, "AI答案", value)
    for key, title in (
        ("exam_point", "考点"),
        ("core_analysis", "核心解析"),
        ("wrong_analysis", "错误项分析"),
        ("reminder", "易错提醒"),
    ):
        if key in fields:
            markdown = _replace_section(markdown, title, str(fields[key]))
    return markdown.replace("\r\n", "\n").rstrip() + "\n"


def stable_option_ids(question_id: str, parsed: dict[str, Any]) -> dict[str, str]:
    return {
        item["label"]: str(uuid.uuid5(uuid.NAMESPACE_URL, f"cams:{question_id}:option:{item['label']}"))
        for item in parsed["options"]
    }


def carry_option_ids(
    question_id: str,
    old_parsed: dict[str, Any],
    old_ids: dict[str, str],
    new_parsed: dict[str, Any],
) -> dict[str, str]:
    result: dict[str, str] = {}
    old_by_content: dict[str, list[str]] = {}
    for item in old_parsed.get("options", []):
        key = normalize_stem(item.get("zh", "") + "|" + item.get("en", ""))
        old_by_content.setdefault(key, []).append(old_ids.get(item["label"], ""))
    for item in new_parsed.get("options", []):
        key = normalize_stem(item.get("zh", "") + "|" + item.get("en", ""))
        candidates = [value for value in old_by_content.get(key, []) if value]
        if len(candidates) == 1:
            result[item["label"]] = candidates[0]
        elif item["label"] in old_ids:
            result[item["label"]] = old_ids[item["label"]]
        else:
            result[item["label"]] = str(uuid.uuid4())
    return result


def answer_option_ids(parsed: dict[str, Any], option_ids: dict[str, str]) -> list[str]:
    return [option_ids[label] for label in parsed.get("answer_letters", []) if label in option_ids]


def compute_structured_changes(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "question_type",
        "stem_zh",
        "stem_en",
        "options",
        "answer_letters",
        "exam_point",
        "core_analysis",
        "wrong_analysis",
        "reminder",
        "evidence_unit_ids",
    ]
    return {
        field: {"before": before.get(field), "after": after.get(field)}
        for field in fields
        if before.get(field) != after.get(field)
    }


def version_markdown(version: Version) -> str:
    return Path(version.snapshot_path).read_text(encoding="utf-8")


def unified_diff(before: str, after: str, from_name: str, to_name: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=from_name,
            tofile=to_name,
        )
    )


def _write_snapshot(question_id: str, version_id: str, sequence: int, markdown: str) -> Path:
    question_dir = settings.content_root / "questions" / question_id
    versions_dir = question_dir / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)
    snapshot = versions_dir / f"v{sequence:04d}_{version_id}.md"
    snapshot.write_text(markdown, encoding="utf-8", newline="\n")
    (question_dir / "current.md").write_text(markdown, encoding="utf-8", newline="\n")
    return snapshot


def create_version(
    db: Session,
    question: Question,
    markdown: str,
    *,
    task_id: str | None,
    actor_id: int | None,
    note: str,
    bindings: dict[str, Any] | None = None,
    is_import: bool = False,
) -> Version:
    previous = db.get(Version, question.current_version_id) if question.current_version_id else None
    previous_parsed = previous.parsed_content if previous else {}
    parsed = parse_markdown(markdown)
    option_ids = (
        carry_option_ids(question.id, previous_parsed, previous.option_ids, parsed)
        if previous
        else stable_option_ids(question.id, parsed)
    )
    max_sequence = db.scalar(
        select(func.max(Version.sequence)).where(Version.question_id == question.id)
    ) or 0
    sequence = max_sequence + 1
    version_id = f"ver_{uuid.uuid4().hex}"
    snapshot = _write_snapshot(question.id, version_id, sequence, markdown)
    current_bindings = bindings or {
        "primary_cp_id": question.primary_cp_id,
        "supporting_cp_ids": question.supporting_cp_ids,
        "evidence_unit_ids": parsed.get("evidence_unit_ids", []),
    }
    version = Version(
        id=version_id,
        question_id=question.id,
        sequence=sequence,
        parent_id=previous.id if previous else None,
        task_id=task_id,
        snapshot_path=str(snapshot),
        content_hash=sha256_bytes(markdown.encode("utf-8")),
        parsed_content=parsed,
        option_ids=option_ids,
        answer_option_ids=answer_option_ids(parsed, option_ids),
        bindings=current_bindings,
        structured_changes=compute_structured_changes(previous_parsed, parsed),
        note=note,
        created_by=actor_id,
        is_import=is_import,
    )
    db.add(version)
    question.current_version_id = version.id
    question.current_path = str(settings.content_root / "questions" / question.id / "current.md")
    question.question_type = parsed.get("question_type", "unknown")
    question.evidence_unit_ids = current_bindings.get("evidence_unit_ids", [])
    question.primary_cp_id = current_bindings.get("primary_cp_id")
    question.supporting_cp_ids = current_bindings.get("supporting_cp_ids", [])
    question.updated_at = utcnow()
    return version


def import_content(db: Session, force: bool = False) -> dict[str, Any]:
    source_files = sorted(settings.source_markdown_root.glob("v7_q_*.md"))
    report: dict[str, Any] = {"source_count": len(source_files), "imported": 0, "skipped": 0, "attention": []}
    for source in source_files:
        question_id_match = QUESTION_ID_RE.search(source.stem)
        if not question_id_match:
            continue
        question_id = question_id_match.group(0)
        source_hash = sha256_file(source)
        existing = db.get(Question, question_id)
        if existing and not force:
            report["skipped"] += 1
            continue
        markdown = source.read_text(encoding="utf-8-sig")
        parsed = parse_markdown(markdown)
        needs_attention = not parsed["has_evidence_section"]
        if existing:
            question = existing
        else:
            question = Question(
                id=question_id,
                source_path=str(source),
                source_hash=source_hash,
                current_path="",
                question_type=parsed["question_type"],
                status="editing",
                needs_attention=needs_attention,
            )
            db.add(question)
            db.flush()
        question.needs_attention = needs_attention
        question.source_hash = source_hash
        create_version(
            db,
            question,
            markdown,
            task_id=None,
            actor_id=None,
            note="首次复制导入",
            is_import=True,
        )
        db.add(AuditEvent(action="content.import", object_type="question", object_id=question_id, details={"source_hash": source_hash}))
        report["imported"] += 1
        if needs_attention:
            report["attention"].append(question_id)
    db.commit()
    report["database_count"] = db.scalar(select(func.count()).select_from(Question))
    return report


def verify_import(db: Session) -> dict[str, Any]:
    questions = list(db.scalars(select(Question).order_by(Question.id)))
    source_unchanged = all(Path(q.source_path).exists() and sha256_file(Path(q.source_path)) == q.source_hash for q in questions)
    ids = [q.id for q in questions]
    return {
        "question_count": len(questions),
        "unique_count": len(set(ids)),
        "attention": [q.id for q in questions if q.needs_attention],
        "source_hashes_unchanged": source_unchanged,
        "valid": len(questions) == 395 and len(set(ids)) == 395 and source_unchanged,
    }
