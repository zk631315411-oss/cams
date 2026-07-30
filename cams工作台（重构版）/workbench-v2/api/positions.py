from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from docx import Document
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import settings
from .content import normalize_stem, sha256_file
from .db import PositionSnapshot, Question, Version


QUESTION_START_RE = re.compile(r"^(\d+)[.．、]\s*(.+)$")
OPTION_A_RE = re.compile(r"^A[.．、]", re.IGNORECASE)


def parse_docx_questions(path: Path) -> tuple[str, list[dict[str, Any]]]:
    paragraphs = [paragraph.text.strip() for paragraph in Document(path).paragraphs]
    paper_title = ""
    if paragraphs and (":" in paragraphs[0] or "：" in paragraphs[0]):
        paper_title = re.split(r"[:：]", paragraphs[0], maxsplit=1)[1].strip()
    items: list[dict[str, Any]] = []
    for index, text in enumerate(paragraphs):
        match = QUESTION_START_RE.match(text)
        if not match:
            continue
        next_text = next((value for value in paragraphs[index + 1 :] if value), "")
        if not OPTION_A_RE.match(next_text):
            continue
        items.append({"ordinal": int(match.group(1)), "stem": match.group(2).strip()})
    return paper_title, items


def _snapshot_key(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return f"positions_{digest.hexdigest()[:16]}"


def import_positions(db: Session) -> dict[str, Any]:
    paths = sorted(settings.source_docx_root.glob("*.docx"))
    key = _snapshot_key(paths)
    if db.scalar(select(func.count()).select_from(PositionSnapshot).where(PositionSnapshot.snapshot_key == key)):
        rows = list(db.scalars(select(PositionSnapshot).where(PositionSnapshot.snapshot_key == key)))
        return _report(key, rows, reused=True)

    exact: dict[str, list[str]] = defaultdict(list)
    for question, version in db.execute(
        select(Question, Version).join(Version, Version.id == Question.current_version_id)
    ):
        for stem in (version.parsed_content.get("stem_zh", ""), version.parsed_content.get("stem_en", "")):
            normalized = normalize_stem(stem)
            if normalized:
                exact[normalized].append(question.id)

    rows: list[PositionSnapshot] = []
    for path in paths:
        title, items = parse_docx_questions(path)
        source_hash = sha256_file(path)
        section_code = path.stem
        for item in items:
            normalized = normalize_stem(item["stem"])
            candidates = list(dict.fromkeys(exact.get(normalized, [])))
            question_id = candidates[0] if len(candidates) == 1 else None
            confidence = "exact_unique" if len(candidates) == 1 else ("ambiguous" if candidates else "unmatched")
            note = "" if len(candidates) <= 1 else "候选：" + ", ".join(candidates)
            row = PositionSnapshot(
                snapshot_key=key,
                bank_version="v7",
                source_docx=str(path),
                source_hash=source_hash,
                paper_title=title,
                section_code=section_code,
                ordinal=item["ordinal"],
                stem=item["stem"],
                normalized_stem=normalized,
                question_id=question_id,
                confidence=confidence,
                note=note,
            )
            db.add(row)
            rows.append(row)
    db.commit()
    report = _report(key, rows, reused=False)
    report_dir = settings.content_root / "import-reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / f"{key}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def _report(key: str, rows: list[PositionSnapshot], reused: bool) -> dict[str, Any]:
    by_confidence: dict[str, int] = defaultdict(int)
    issues = []
    for row in rows:
        by_confidence[row.confidence] += 1
        if row.confidence != "exact_unique":
            issues.append(
                {
                    "section": row.section_code,
                    "ordinal": row.ordinal,
                    "stem": row.stem,
                    "confidence": row.confidence,
                    "note": row.note,
                }
            )
    return {
        "snapshot_key": key,
        "reused": reused,
        "total": len(rows),
        "counts": dict(by_confidence),
        "issues": issues,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
