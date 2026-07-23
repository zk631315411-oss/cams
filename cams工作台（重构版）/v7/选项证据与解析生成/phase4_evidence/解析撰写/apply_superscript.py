# -*- coding: utf-8 -*-
"""批量将小节 md 中的（书内第XXX页）转换为 <sup>PXXX</sup> 上角标格式。"""

import re
import argparse
from pathlib import Path


def to_superscript(text: str) -> str:
    """将（书内第XXX页）替换为 <sup>PXXX</sup>。"""
    return re.sub(
        r"（书内第(\d+)页）",
        r"<sup>P\1</sup>",
        text,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="将小节 md 中的页码引用转为上角标格式"
    )
    parser.add_argument("--sections-dir", required=True, help="sections 目录路径")
    args = parser.parse_args()

    sections_dir = Path(args.sections_dir)
    if not sections_dir.exists():
        raise RuntimeError(f"目录不存在: {sections_dir}")

    md_files = sorted(sections_dir.glob("*.md"))
    if not md_files:
        print("未找到 md 文件")
        return

    total = 0
    for path in md_files:
        original = path.read_text(encoding="utf-8")
        converted = to_superscript(original)
        if converted != original:
            path.write_text(converted, encoding="utf-8")
            count = len(re.findall(r"<sup>P\d+</sup>", converted))
            total += count
            print(f"  {path.name}: {count} 处上角标化")

    print(f"\n共 {len(md_files)} 个文件，{total} 处上角标化完成")


if __name__ == "__main__":
    main()
