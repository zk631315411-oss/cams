"""面向人工和自动化的正式版检索 CLI。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from storage import WorkspaceStore

from .service import retrieve_question_evidence, search_evidence


def _add_retrieval_arguments(parser: argparse.ArgumentParser, *, question_mode: bool) -> None:
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--merge-top-k", type=int, default=30)
    parser.add_argument("--kg-max-extra", type=int, default=30)
    parser.add_argument("--disable-kg", action="store_true")
    if question_mode:
        parser.add_argument("--disable-p5", action="store_true")
        parser.add_argument("--per-option-limit", type=int, default=3)
        parser.add_argument("--per-head-minimum", type=int, default=2)
    parser.add_argument("--rrf-k", type=int, default=60)


def _config(args: argparse.Namespace, *, question_mode: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "merge_top_k": args.merge_top_k,
        "kg_max_extra": args.kg_max_extra,
        "enable_kg": not args.disable_kg,
        "rrf_k": args.rrf_k,
    }
    if question_mode:
        result.update({"enable_p5": not args.disable_p5, "per_option_limit": args.per_option_limit,
                       "per_head_minimum": args.per_head_minimum})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="CAMS 正式版检索")
    parser.add_argument("--workspace-root", type=Path, default=None)
    commands = parser.add_subparsers(dest="command", required=True)
    general = commands.add_parser("search", help="一般检索：RAG + KG")
    general.add_argument("--query", required=True)
    general.add_argument("--language", choices=("auto", "zh", "en"), default="auto")
    _add_retrieval_arguments(general, question_mode=False)
    question = commands.add_parser("question", help="题目检索：检索头 + P5 + RAG + KG")
    question.add_argument("--question-id", required=True)
    _add_retrieval_arguments(question, question_mode=True)
    args = parser.parse_args()
    root = args.workspace_root
    if args.command == "search":
        result = search_evidence(root, args.query, args.top_k, language=args.language, config=_config(args, question_mode=False))
    else:
        store = WorkspaceStore(root or Path(__file__).resolve().parents[2])
        result = retrieve_question_evidence(root, store.read_question(args.question_id)["content"], config=_config(args, question_mode=True))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
