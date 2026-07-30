"""Preview or apply the evidence-driven workflow migration."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from backup import create_backup
from storage import WorkspaceStore


def inspect(store: WorkspaceStore) -> dict[str, int]:
    result = {"questions": 0, "needs_workflow": 0, "legacy_imports": 0,
              "legacy_evidence": 0, "already_migrated": 0}
    for directory in sorted(store.questions.glob("v7_q_*")):
        if not (directory / "question.json").exists(): continue
        result["questions"] += 1
        if (directory / "workflow.json").exists(): result["already_migrated"] += 1
        else: result["needs_workflow"] += 1
        if (directory / "source" / "legacy_question.json").exists(): result["legacy_imports"] += 1
        if (directory / "evidence_review.json").exists() and not (directory / "evidence_catalog.json").exists():
            result["legacy_evidence"] += 1
    return result


def apply(store: WorkspaceStore) -> dict[str, int]:
    result = {"workflow_created": 0, "evidence_catalog_created": 0,
              "curation_migrated": 0, "skipped": 0}
    for directory in sorted(store.questions.glob("v7_q_*")):
        qid = directory.name
        if not (directory / "question.json").exists(): continue
        initialized = store.initialize_workflow_v2(qid)
        if initialized["changed"]: result["workflow_created"] += 1
        else: result["skipped"] += 1
        legacy = store._read_json(directory / "evidence_review.json")
        if not legacy or (directory / "evidence_catalog.json").exists(): continue
        workflow = store.read_workflow(qid)
        if workflow.get("stage") != "evidence_research" or workflow.get("disposition") != "active": continue
        question = store.read_question(qid)
        retrieval = legacy.get("retrieval") or {}
        payload = {"items": legacy.get("items") or [],
                   "asset_versions": retrieval.get("asset_versions") or {},
                   "config": retrieval.get("config") or {},
                   "query": "旧工作台检索结果迁移"}
        store.register_evidence_run(qid, payload, "legacy_import", "workflow-migration", "migration",
                                    "迁移旧 evidence_review，原文件保持不变",
                                    question["version"], question["archive_revision"])
        result["evidence_catalog_created"] += 1
        adopted_units = {item.get("unit_id") for item in legacy.get("items", []) if item.get("status") == "adopted"}
        if adopted_units:
            question = store.read_question(qid)
            catalog = store.read_evidence_catalog(qid, limit=100)
            updates = [{"evidence_id": item["evidence_id"], "selected": True,
                        "role": "support_answer", "note": "从旧工作台采用状态迁移"}
                       for item in catalog["items"] if item.get("unit_id") in adopted_units]
            if updates:
                store.curate_evidence(qid, updates, "workflow-migration", "migration",
                                      "迁移旧工作台采用状态", expected_question_version=question["version"],
                                      expected_archive_revision=question["archive_revision"])
                result["curation_migrated"] += len(updates)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--apply", action="store_true", help="默认只预览；传入后先备份再迁移")
    parser.add_argument("--backup-root", type=Path, default=None)
    args = parser.parse_args()
    store = WorkspaceStore(args.workspace_root)
    preview = inspect(store)
    output: dict[str, object] = {"mode": "apply" if args.apply else "preview", "preview": preview}
    if args.apply:
        output["backup"] = create_backup(store.root, args.backup_root, reason="before-workflow-v2", daily=False)
        output["result"] = apply(store)
        output["after"] = inspect(store)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
