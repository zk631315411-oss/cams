"""一次性导入旧工作台的标准化题库，不继承其审核或发布状态。"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from storage import STORE, WorkspaceError


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", required=True, help="旧 v7_questions.json")
    parser.add_argument("--ds-dir", default="", help="旧 output/questions 目录，可选")
    args = parser.parse_args()
    source = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    imported, skipped = 0, 0
    for raw in source.get("items", []):
        qid = str(raw.get("question_id") or "")
        if not qid:
            continue
        directory = STORE.questions / qid
        if (directory / "question.json").exists():
            skipped += 1
            continue
        content = dict(raw)
        content.pop("question_id", None)
        STORE.write_question(qid, content, "legacy-import", "migration", "从重构版导入；需重新核验")
        STORE._write_json(directory / "source" / "legacy_question.json", raw)
        if args.ds_dir:
            ds_file = Path(args.ds_dir) / f"q_{qid}.json"
            if ds_file.exists():
                shutil.copy2(ds_file, directory / "source" / "legacy_ds_result.json")
        imported += 1
    print(json.dumps({"imported": imported, "skipped": skipped}, ensure_ascii=False))


if __name__ == "__main__":
    main()
