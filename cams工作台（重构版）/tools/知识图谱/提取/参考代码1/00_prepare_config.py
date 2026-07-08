"""
v4.3 Step 0: prepare a local Tree-KG-style construction config.

This config is for the local v4.3 pipeline. The public Tree-KG API is treated
as an optional adapter, not as the default dependency.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parents[1]
DEFAULT_INPUT = MODULE_DIR / "中间产物" / "高等代数上册_clean.md"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "中间产物"
DEFAULT_CONFIG = SCRIPT_DIR / "v4_3_config.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare v4.3 construction config.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input structured markdown.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Intermediate output directory.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Config JSON output path.")
    parser.add_argument("--textbook-id", default="gaodai_shang")
    parser.add_argument("--textbook-name", default="高等代数上册")
    parser.add_argument("--course-name", default="高等代数")
    parser.add_argument("--default-model", default=os.environ.get("LLM_DEFAULT_MODEL") or os.environ.get("DEEPSEEK_FLASH_MODEL", "gpt-5.4-mini"))
    parser.add_argument("--high-risk-model", default=os.environ.get("LLM_HIGH_RISK_MODEL") or os.environ.get("DEEPSEEK_HIGH_RISK_MODEL", "gpt-5.5"))
    parser.add_argument("--base-url", default=os.environ.get("LLM_API_BASE") or os.environ.get("DEEPSEEK_API_BASE", "https://api.openai.com/v1"))
    parser.add_argument("--allow-pro", action="store_true", help="Allow high-risk steps to use a stronger model.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing config.")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "version": "v4.3",
        "source": {
            "format": "structured_markdown",
            "input_path": str(args.input),
            "textbook_id": args.textbook_id,
            "textbook_name": args.textbook_name,
            "course_name": args.course_name,
        },
        "output": {
            "intermediate_dir": str(args.output_dir),
            "config_path": str(args.config),
        },
        "tree": {
            "heading_levels": {
                "chapter": 1,
                "section": 2,
                "subsection": 3,
                "anchor": 5,
            },
            "summary_source_scopes": ["core_content"],
            "skip_source_scopes": ["exercise", "example"],
        },
        "schema": {
            "node_types": ["Concept", "Method", "Formula", "Theorem", "ProblemClass"],
            "application_node_types": ["Method", "ProblemClass"],
            "rule_layer_node_types": ["RuleCase", "ConditionExpression", "Outcome", "LogicGroup"],
            "edge_types": [
                "HAS_SUBSECTION",
                "INTRODUCES",
                "HAS_EXAMPLE",
                "SUPERIOR",
                "EQUATIVE",
                "PART_OF",
                "HAS_PROPERTY",
                "USES",
                "GETS",
                "DERIVES",
                "HAS_RULE_CASE",
                "APPLIES_TO",
                "HAS_CONDITION",
                "HAS_CONDITION_AND",
                "HAS_CONDITION_OR",
                "HAS_OUTCOME",
                "HAS_OUTCOME_AND",
                "HAS_OUTCOME_OR",
                "PREREQUISITE_OF",
                "HAS_POSSIBLE_STATE",
            ],
            "weak_or_recommendation_edges": ["EQUATIVE"],
            "derived_edges": ["PREREQUISITE_OF", "HAS_POSSIBLE_STATE"],
            "forbidden_node_types": ["Definition", "AttributeValue"],
        },
        "llm": {
            "provider": "openai_compatible",
            "base_url": args.base_url,
            "default_model": args.default_model,
            "high_risk_model": args.high_risk_model,
            "allow_pro": bool(args.allow_pro),
            "temperature": 0.0,
            "timeout_seconds": 120,
        },
        "treekg_api": {
            "enabled": False,
            "submit_url": "https://pacman.cs.tsinghua.edu.cn/api/treekg/submit_task",
            "status_url_template": "https://pacman.cs.tsinghua.edu.cn/api/treekg/task_status/{task_id}",
            "result_url_template": "https://pacman.cs.tsinghua.edu.cn/api/treekg/task_result/{task_id}",
            "note": "Public API returned nginx 403 in local probe; keep as optional adapter.",
        },
    }


def main() -> None:
    args = parse_args()
    if args.config.exists() and not args.overwrite:
        raise FileExistsError(f"Config already exists: {args.config}. Use --overwrite to replace it.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.config.parent.mkdir(parents=True, exist_ok=True)
    config = build_config(args)
    args.config.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] wrote config -> {args.config}")
    print(f"[INFO] input -> {args.input}")
    print(f"[INFO] output_dir -> {args.output_dir}")


if __name__ == "__main__":
    main()
