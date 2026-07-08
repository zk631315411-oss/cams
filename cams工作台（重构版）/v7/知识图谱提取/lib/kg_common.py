from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


KG_ROOT = Path(__file__).resolve().parents[1]
V7_ROOT = KG_ROOT.parent
DEFAULT_UNITS_PATH = V7_ROOT / "work" / "base_units" / "units" / "v7_bilingual_units.json"
DEFAULT_FREEZE_MANIFEST_PATH = V7_ROOT / "work" / "base_units" / "units" / "unit_freeze_manifest.json"
LEGACY_KG_WORK_DIR = KG_ROOT / "archive" / "legacy_work_kg_20260705"
PHASES_DIR = KG_ROOT / "phases"

PHASE00_OUTPUTS = PHASES_DIR / "phase00_quality_gate" / "outputs"
PHASE00_REPORTS = PHASES_DIR / "phase00_quality_gate" / "reports"

PHASE01_OUTPUTS = PHASES_DIR / "phase01_chapter_index" / "outputs"
PHASE01_PREVIEWS = PHASES_DIR / "phase01_chapter_index" / "previews"

PHASE02_INPUTS = PHASES_DIR / "phase02_core_points" / "inputs"
PHASE02_OUTPUTS = PHASES_DIR / "phase02_core_points" / "outputs"
PHASE02_REPORTS = PHASES_DIR / "phase02_core_points" / "reports"
PHASE02_PREVIEWS = PHASES_DIR / "phase02_core_points" / "previews"

PHASE03_OUTPUTS = PHASES_DIR / "phase03_structure_edges" / "outputs"
PHASE03_PREVIEWS = PHASES_DIR / "phase03_structure_edges" / "previews"

PHASE04_OUTPUTS = PHASES_DIR / "phase04_bundles" / "outputs"
PHASE04_PREVIEWS = PHASES_DIR / "phase04_bundles" / "previews"

PHASE07_OUTPUTS = PHASES_DIR / "phase07_case_links" / "outputs"
PHASE07_PREVIEWS = PHASES_DIR / "phase07_case_links" / "previews"

PHASE08_OUTPUTS = PHASES_DIR / "phase08_cross_chapter" / "outputs"
PHASE08_REPORTS = PHASES_DIR / "phase08_cross_chapter" / "reports"
PHASE08_PREVIEWS = PHASES_DIR / "phase08_cross_chapter" / "previews"

PHASE08B_OUTPUTS = PHASES_DIR / "phase08b_vector_hidden" / "outputs"
PHASE08B_REPORTS = PHASES_DIR / "phase08b_vector_hidden" / "reports"
PHASE08B_PREVIEWS = PHASES_DIR / "phase08b_vector_hidden" / "previews"

PHASE09_OUTPUTS = PHASES_DIR / "phase09_terms" / "outputs"
PHASE09_PREVIEWS = PHASES_DIR / "phase09_terms" / "previews"

PHASE10_OUTPUTS = PHASES_DIR / "phase10_assembly_review" / "outputs"
PHASE10_REPORTS = PHASES_DIR / "phase10_assembly_review" / "reports"
PHASE10_PREVIEWS = PHASES_DIR / "phase10_assembly_review" / "previews"
PHASE10_REVIEW_PACKETS = PHASES_DIR / "phase10_assembly_review" / "review_packets"

PHASE10B_OUTPUTS = PHASES_DIR / "phase10b_llm_review" / "outputs"
PHASE10B_REPORTS = PHASES_DIR / "phase10b_llm_review" / "reports"
PHASE10B_PREVIEWS = PHASES_DIR / "phase10b_llm_review" / "previews"
PHASE10B_PROMPTS = PHASES_DIR / "phase10b_llm_review" / "prompts"

LEGACY_PHASE05_OUTPUTS = PHASES_DIR / "legacy_phase05_case_and_cross_links" / "outputs"

class _MappedDir:
    def __init__(self, default_dir: Path, file_map: dict[str, Path] | None = None):
        self.default_dir = default_dir
        self.file_map = file_map or {}

    def __truediv__(self, part: str) -> Path:
        return self.file_map.get(part, self.default_dir / part)

    def __fspath__(self) -> str:
        return str(self.default_dir)

    def __str__(self) -> str:
        return str(self.default_dir)

    def mkdir(self, *args: Any, **kwargs: Any) -> None:
        self.default_dir.mkdir(*args, **kwargs)

    def exists(self) -> bool:
        return self.default_dir.exists()


class _KgWorkRoot:
    def __init__(self) -> None:
        self.dir_map = {
            "phase0_quality_gate": _MappedDir(
                PHASE00_OUTPUTS,
                {"unit_quality_report.md": PHASE00_REPORTS / "unit_quality_report.md"},
            ),
            "phase1_chapter_skeleton": _MappedDir(PHASE01_OUTPUTS),
            "samples": _MappedDir(PHASE01_OUTPUTS),
            "phase2_core_points": _MappedDir(
                PHASE02_OUTPUTS,
                {"p2_materialization_report.md": PHASE02_REPORTS / "p2_materialization_report.md"},
            ),
            "phase3_structure_edges": _MappedDir(PHASE03_OUTPUTS),
            "phase4_bundles": _MappedDir(PHASE04_OUTPUTS),
            "phase5_case_and_cross_links": _MappedDir(LEGACY_PHASE05_OUTPUTS),
            "phase6_review": _MappedDir(
                PHASE10B_OUTPUTS,
                {
                    "llm_review_report.md": PHASE10B_REPORTS / "llm_review_report.md",
                    "llm_review_decisions_report.md": PHASE10B_REPORTS / "llm_review_decisions_report.md",
                    "llm_review_prompt_version.txt": PHASE10B_REPORTS / "llm_review_prompt_version.txt",
                },
            ),
            "phase6_terms": _MappedDir(PHASE09_OUTPUTS),
            "phase7a_case_links": _MappedDir(PHASE07_OUTPUTS),
            "phase7_retrieval_asset": _MappedDir(PHASE10_OUTPUTS),
            "phase8_cross_chapter": _MappedDir(PHASE08_OUTPUTS),
            "phase8b_vector_hidden": _MappedDir(PHASE08B_OUTPUTS),
            "markdown": _MappedDir(
                PHASE10_PREVIEWS,
                {
                    "phase1_chapter_skeleton_preview.md": PHASE01_PREVIEWS / "phase1_chapter_skeleton_preview.md",
                    "kg_core_point_preview.md": PHASE02_PREVIEWS / "kg_core_point_preview.md",
                    "kg_core_point_edges_preview.md": PHASE02_PREVIEWS / "kg_core_point_edges_preview.md",
                    "kg_structure_edges_preview.md": PHASE03_PREVIEWS / "kg_structure_edges_preview.md",
                    "kg_bundle_preview.md": PHASE04_PREVIEWS / "kg_bundle_preview.md",
                    "case_links_preview.md": PHASE07_PREVIEWS / "case_links_preview.md",
                    "cross_chapter_candidates_preview.md": PHASE08_PREVIEWS / "cross_chapter_candidates_preview.md",
                    "cross_chapter_review_recommendations.codex.md": PHASE08_PREVIEWS / "cross_chapter_review_recommendations.codex.md",
                    "vector_hidden_candidates_preview.md": PHASE08B_PREVIEWS / "vector_hidden_candidates_preview.md",
                    "term_alias_map_preview.md": PHASE09_PREVIEWS / "term_alias_map_preview.md",
                    "kg_priority_review_dashboard.md": PHASE10_REVIEW_PACKETS / "kg_priority_review_dashboard.md",
                    "kg_p0_review_groups.md": PHASE10_REVIEW_PACKETS / "kg_p0_review_groups.md",
                    "p0_review_recommendations.codex.md": PHASE10_REVIEW_PACKETS / "p0_review_recommendations.codex.md",
                    "p0_decision_packet.md": PHASE10_REVIEW_PACKETS / "p0_decision_packet.md",
                    "p1_decision_packet.md": PHASE10_REVIEW_PACKETS / "p1_decision_packet.md",
                    "llm_review_requests.priority_preview.md": PHASE10B_PREVIEWS / "llm_review_requests.priority_preview.md",
                },
            ),
            "reports": _MappedDir(
                PHASE10_REPORTS,
                {
                    "cross_chapter_review_recommendation_summary.json": PHASE08_REPORTS / "cross_chapter_review_recommendation_summary.json",
                    "vector_hidden_candidate_audit.jsonl": PHASE08B_REPORTS / "vector_hidden_candidate_audit.jsonl",
                    "vector_hidden_candidate_audit.md": PHASE08B_REPORTS / "vector_hidden_candidate_audit.md",
                    "vector_hidden_candidate_audit_summary.json": PHASE08B_REPORTS / "vector_hidden_candidate_audit_summary.json",
                    "vector_hidden_candidate_summary.json": PHASE08B_REPORTS / "vector_hidden_candidate_summary.json",
                },
            ),
        }
        self.file_map = {
            "kg_for_retrieval.json": PHASE10_OUTPUTS / "kg_for_retrieval.json",
            "workspace_manifest.json": PHASES_DIR / "workspace_manifest.json",
        }

    def __truediv__(self, part: str) -> Path | _MappedDir:
        if part in self.dir_map:
            return self.dir_map[part]
        return self.file_map.get(part, LEGACY_KG_WORK_DIR / part)

    def __fspath__(self) -> str:
        return str(PHASES_DIR)

    def __str__(self) -> str:
        return str(PHASES_DIR)

    def mkdir(self, *args: Any, **kwargs: Any) -> None:
        PHASES_DIR.mkdir(*args, **kwargs)

    def exists(self) -> bool:
        return PHASES_DIR.exists()


# Existing scripts still use DEFAULT_KG_WORK_DIR. It now routes default reads and
# writes into the phase self-contained layout while LEGACY_KG_WORK_DIR points to
# the archived old work/kg contents for explicit compatibility reads.
DEFAULT_KG_WORK_DIR = _KgWorkRoot()


BLOCKING_RISK_FLAGS = {
    "unit_too_broad",
    "sentence_group_conflict",
    "knowledge_needs_review",
}

def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_units(path: Path = DEFAULT_UNITS_PATH) -> list[dict[str, Any]]:
    data = load_json(path)
    if isinstance(data, dict) and isinstance(data.get("units"), list):
        return data["units"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unsupported units payload: {path}")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    ensure_dir(path.parent)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=False))
            f.write("\n")
            count += 1
    return count


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8", newline="\n")


def unit_sort_key(unit: dict[str, Any]) -> tuple[int, str]:
    order = unit.get("unit_order")
    if isinstance(order, int):
        return (order, unit.get("unit_id") or "")
    return (10**12, unit.get("unit_id") or "")


def ordered_chapters(units: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in units:
        chapter = unit.get("chapter") or "UNKNOWN"
        grouped[chapter].append(unit)

    chapters = []
    for chapter, chapter_units in grouped.items():
        chapter_units = sorted(chapter_units, key=unit_sort_key)
        pages = sorted({p for u in chapter_units for p in _as_list(u.get("page_span")) if isinstance(p, int)})
        printed_pages = sorted({str(p) for u in chapter_units for p in _as_list(u.get("printed_page_span")) if p is not None})
        chapters.append(
            {
                "chapter": chapter,
                "first_unit_order": unit_sort_key(chapter_units[0])[0],
                "first_unit_id": chapter_units[0].get("unit_id"),
                "unit_count": len(chapter_units),
                "pdf_page_span": _span(pages),
                "printed_page_span": _span(printed_pages),
                "units": chapter_units,
            }
        )
    return sorted(chapters, key=lambda c: (c["first_unit_order"], c["chapter"]))


def summarize_counter(counter: Counter, limit: int | None = None) -> list[dict[str, Any]]:
    items = counter.most_common(limit)
    return [{"name": key, "count": value} for key, value in items]


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _span(values: list[Any]) -> list[Any]:
    if not values:
        return []
    return [values[0], values[-1]] if values[0] != values[-1] else [values[0]]
