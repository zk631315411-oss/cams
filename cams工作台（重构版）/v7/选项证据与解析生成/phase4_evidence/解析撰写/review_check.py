# -*- coding: utf-8 -*-
"""复核检测入口：扫描 question JSON，输出需要人工复核的题目清单。不做导出。

用法示例：
    python review_check.py --output-dir ../output
"""

from __future__ import annotations

import argparse
from pathlib import Path

from 解析撰写.s5_explanation_review import run_review


def main() -> None:
    parser = argparse.ArgumentParser(
        description="扫描 question JSON，生成待复核清单。不做导出。"
    )
    parser.add_argument("--output-dir", required=True, help="phase4_evidence/output 目录")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    summary = run_review(output_dir)
    print(f"\n[output] review={summary['review_markdown']}")
    print(f"[output] summary={output_dir / 'software_export' / 'review_summary.json'}")


if __name__ == "__main__":
    main()