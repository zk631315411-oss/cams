#!/usr/bin/env python3
"""TOC-led semantic repair, pass 11: verified module-4 nodes."""

from pathlib import Path
import importlib.util

ROOT = Path(r"D:\守正公司工作区\cams考试")
FILE = ROOT / "教材、答疑记录、习题与参考文献" / "教材原文" / "v7" / "mineru提取" / "中文" / "v7_zh_mineru_merged.md"
spec = importlib.util.spec_from_file_location("repair", ROOT / "tools" / "repair_v7_chinese_heading_hierarchy.py")
repair = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(repair)


def find(lines: list[str], prefix: str, body: int, occurrence: int = 1) -> int:
    found = [i for i in range(body, len(lines)) if lines[i].strip().startswith(prefix)]
    if len(found) < occurrence:
        raise ValueError(prefix)
    return found[occurrence - 1]


def take(lines: list[str], index: int) -> str:
    value = lines.pop(index)
    if index < len(lines) and not lines[index].strip():
        lines.pop(index)
    return value


def move(lines: list[str], source: str, target: str, body: int, occurrence: int = 1) -> None:
    heading = take(lines, find(lines, source, body, occurrence))
    target_index = find(lines, target, body)
    lines[target_index:target_index] = [heading, ""]


def insert(lines: list[str], target: str, heading: str, body: int) -> None:
    index = find(lines, target, body)
    lines[index:index] = [heading, ""]


def main() -> None:
    lines = FILE.read_text(encoding="utf-8-sig").splitlines()
    body = repair.find_body_start(lines)
    toc = lines[:body]
    move(lines, "#### AFC 合规工具与技术", "客户入组、持续尽调、交易监测", body)
    move(lines, "#### 从传统系统转向基于 AI 的工具", "从传统规则系统转向 AI 工具", body)
    insert(lines, "机构在生物特征认证过程中采用活体检测技术", "#### 实时性检测技术", body)
    insert(lines, "在将筛选系统与其他系统", "#### 将筛查技术与其他系统整合", body)

    take(lines, find(lines, "#### 持续筛查的类型", body))
    move(lines, "#### 支付筛查技术", "支付筛查技术既能有效预防", body)
    take(lines, find(lines, "#### 支付与批量筛查技术", body))
    insert(lines, "数字资产与加密货币筛查", "#### 筛选数字资产和货币", body)

    take(lines, find(lines, "#### 交易监控与充分场景覆盖", body))
    insert(lines, "交易监控场景需要进行精细校准", "#### 事务监控场景校验测试", body)
    move(lines, "#### AI 工具的持续测试与调优", "AI 训练、回溯测试", body)
    move(lines, "#### 交易监控的网络分析解决方案", "网络分析", body)
    move(lines, "#### 辅助案件管理的技术", "案件管理平台", body)
    move(lines, "#### 区块链追踪技术", "区块链溯源", body)

    insert(lines, "某中型银行金融犯罪分析师莎拉", "#### 案例示例：为新TM系统识别数据", body)
    insert(lines, "数据挖掘与数据匹配技术", "#### 数据挖掘与匹配", body)
    move(lines, "#### 案例示例：分析客户行为", "Evertrust银行正着力提升", body)

    if lines[:body] != toc:
        raise RuntimeError("TOC was modified")
    rows = repair.heading_rows(lines[body:])
    if repair.jumps(rows):
        raise RuntimeError(f"Heading jumps: {repair.jumps(rows)[:3]}")
    FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("pass 11 complete", repair.count_levels(rows))


if __name__ == "__main__":
    main()
