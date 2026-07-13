#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 ch3_国际反洗钱_反恐融资活动标准.md 的格式问题
"""

import re

filepath = r"D:\守正公司工作区\cams考试\v6教材原文\chapters\ch3_国际反洗钱_反恐融资活动标准.md"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()
    original_lines = content.split('\n')

print(f"原文件总行数: {len(original_lines)}")

# 统计各项修复次数
stats = {
    'issue_6_o_to_bullet': 0,        # `o ` -> `• `
    'issue_4_double_bullet': 0,      # `• • ` -> `• `
    'issue_5_bullet_before_heading': 0,  # Remove `• ` before headings
    'issue_1_extra_space': 0,        # Extra spaces before `• `
    'issue_3_heading_blank_lines': 0, # 标题后多余空行
    'issue_2_excessive_blank_lines': 0, # 连续3+空行->2
}

lines = original_lines.copy()

# ============================================================
# Issue 6: 任何残留的 `o ` 前导改为 `• `
# 匹配行首(可选空白)后的 `o ` (但排除已经是 `• ` 的)
# 以及 `• o ` 的情况（去除多余的o子bullet）
# ============================================================
new_lines = []
for i, line in enumerate(lines):
    matched = False
    # Pattern 1: `• o ` at line start (after whitespace) -> `• `
    if re.match(r'^(\s*)•\s+o\s+', line):
        new_line = re.sub(r'^(\s*)•\s+o\s+', r'\1• ', line)
        matched = True
    # Pattern 2: standalone `o ` (after whitespace) at line start -> `• `
    elif re.match(r'^(\s*)o\s+', line):
        new_line = re.sub(r'^(\s*)o\s+', r'\1• ', line)
        matched = True
    else:
        new_line = line

    if matched and new_line != line:
        stats['issue_6_o_to_bullet'] += 1

    new_lines.append(new_line)
lines = new_lines

# ============================================================
# Issue 4: 任何残留的 `• • ` 双 bullet 改为 `• `
# ============================================================
new_lines = []
for line in lines:
    if '• • ' in line:
        new_line = line.replace('• • ', '• ')
        if new_line != line:
            stats['issue_4_double_bullet'] += 1
        new_lines.append(new_line)
    else:
        new_lines.append(line)
lines = new_lines

# ============================================================
# Issue 5: 任何标题前误加的 `• ` 去掉
# 匹配行首空白后紧跟 `• ` 然后紧跟 `##`/`###`等标题标记
# ============================================================
new_lines = []
for line in lines:
    new_line = re.sub(r'^(\s*)•\s+(#{1,5}\s)', r'\1\2', line)
    if new_line != line:
        stats['issue_5_bullet_before_heading'] += 1
    new_lines.append(new_line)
lines = new_lines

# ============================================================
# Issue 1: `• ` 前有额外空格的去掉
# 查找行中连续2个以上空格后紧接 `• ` 的情况，
# 将其减少为1个空格
# ============================================================
new_lines = []
for line in lines:
    # 先处理行内非行首连续空格：如 `text  • text` -> `text • text`
    new_line = re.sub(r' {2,}(?=•\s)', ' ', line)
    if new_line != line:
        stats['issue_1_extra_space'] += 1
    new_lines.append(new_line)
lines = new_lines

# ============================================================
# 重新合并为文本进行多行操作
# ============================================================
content = '\n'.join(lines)

# ============================================================
# Issue 3: 紧跟在标题（##/###/####/#####）后面的多余空白行（保留1个空行）
# 匹配标题行 + 3个以上换行符（即2个以上空行）
# 替换为标题行 + 2个换行符（即1个空行）
# ============================================================
# 先统计匹配次数
heading_blank_matches = re.findall(r'^(#{1,5}\s+.*?)\n{3,}', content, flags=re.MULTILINE)
stats['issue_3_heading_blank_lines'] = len(heading_blank_matches)
content = re.sub(r'^(#{1,5}\s+.*?)\n{3,}', r'\1\n\n', content, flags=re.MULTILINE)

# ============================================================
# Issue 2: 列表项之间多余的空白行（连续3+空行 -> 2空行）
# 4+个连续换行符 -> 3个换行符（即3+空行 -> 2空行）
# ============================================================
excessive_blank_matches = re.findall(r'\n{4,}', content)
stats['issue_2_excessive_blank_lines'] = len(excessive_blank_matches)
content = re.sub(r'\n{4,}', '\n\n\n', content)

# ============================================================
# 最终写回
# ============================================================
final_lines = content.split('\n')
print(f"修复后文件总行数: {len(final_lines)}")
print(f"行数变化: {len(final_lines) - len(original_lines)}")
print()

print("=" * 60)
print("修复统计:")
print("=" * 60)

issue_names = {
    'issue_6_o_to_bullet': '问题6：o 前导改为 •',
    'issue_4_double_bullet': '问题4：双 bullet 改为单 bullet',
    'issue_5_bullet_before_heading': '问题5：标题前误加的 • 去掉',
    'issue_1_extra_space': '问题1：• 前多余空格去除',
    'issue_3_heading_blank_lines': '问题3：标题后多余空行减少',
    'issue_2_excessive_blank_lines': '问题2：连续3+空行减少为2',
}

for key, name in issue_names.items():
    print(f"  {name}: {stats[key]} 处")

total_fixes = sum(stats.values())
print(f"\n总计修复: {total_fixes} 处")

# 写回文件
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n文件已写回: {filepath}")
print("完成!")
