#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预览（不写回）修复效果
"""

import re

filepath = r"D:\守正公司工作区\cams考试\v6教材原文\chapters\ch3_国际反洗钱_反恐融资活动标准.md"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()
    original_lines = content.split('\n')

print(f"原文件总行数: {len(original_lines)}")

stats = {
    'issue_6_o_to_bullet': 0,
    'issue_4_double_bullet': 0,
    'issue_5_bullet_before_heading': 0,
    'issue_1_extra_space': 0,
    'issue_3_heading_blank_lines': 0,
    'issue_2_excessive_blank_lines': 0,
}

lines = original_lines.copy()

# --- Issue 6 ---
new_lines = []
for i, line in enumerate(lines):
    matched = False
    if re.match(r'^(\s*)•\s+o\s+', line):
        new_line = re.sub(r'^(\s*)•\s+o\s+', r'\1• ', line)
        matched = True
    elif re.match(r'^(\s*)o\s+', line):
        new_line = re.sub(r'^(\s*)o\s+', r'\1• ', line)
        matched = True
    else:
        new_line = line
    if matched and new_line != line:
        stats['issue_6_o_to_bullet'] += 1
    new_lines.append(new_line)
lines = new_lines

# --- Issue 4 ---
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

# --- Issue 5 ---
new_lines = []
for line in lines:
    new_line = re.sub(r'^(\s*)•\s+(#{1,5}\s)', r'\1\2', line)
    if new_line != line:
        stats['issue_5_bullet_before_heading'] += 1
    new_lines.append(new_line)
lines = new_lines

# --- Issue 1 ---
new_lines = []
for line in lines:
    new_line = re.sub(r' {2,}(?=•\s)', ' ', line)
    if new_line != line:
        stats['issue_1_extra_space'] += 1
    new_lines.append(new_line)
lines = new_lines

content_fixed = '\n'.join(lines)

# --- Issue 3 ---
heading_blank_count = len(re.findall(r'^(#{1,5}\s+.*?)\n{3,}', content_fixed, flags=re.MULTILINE))
stats['issue_3_heading_blank_lines'] = heading_blank_count
content_fixed = re.sub(r'^(#{1,5}\s+.*?)\n{3,}', r'\1\n\n', content_fixed, flags=re.MULTILINE)

# --- Issue 2 ---
excessive_count = len(re.findall(r'\n{4,}', content_fixed))
stats['issue_2_excessive_blank_lines'] = excessive_count
content_fixed = re.sub(r'\n{4,}', '\n\n\n', content_fixed)

final_lines = content_fixed.split('\n')
print(f"修复后总行数: {len(final_lines)}")
print(f"行数变化: {len(final_lines) - len(original_lines)}")
print()

# Print stats
issue_names = {
    'issue_6_o_to_bullet': '问题6：o 前导改为 •',
    'issue_4_double_bullet': '问题4：双 bullet 改为单 bullet',
    'issue_5_bullet_before_heading': '问题5：标题前误加的 •',
    'issue_1_extra_space': '问题1：• 前多余空格',
    'issue_3_heading_blank_lines': '问题3：标题后多余空行',
    'issue_2_excessive_blank_lines': '问题2：连续3+空行',
}

for key, name in issue_names.items():
    print(f"  {name}: {stats[key]} 处")

total = sum(stats.values())
print(f"\n总计修复: {total} 处")

# Show detailed diffs for issue 6
print("\n" + "=" * 60)
print("问题6 详细修改列表（o -> •）:")
print("=" * 60)
for i, (orig, new) in enumerate(zip(original_lines, lines)):
    if orig != new and ('• o' in orig or re.match(r'^\s*o\s+', orig)):
        if new != orig:
            print(f"  行 {i+1}: [{orig.strip()}] -> [{new.strip()}]")

# Show diffs for issue 4
print("\n" + "=" * 60)
print("问题4 详细修改列表（双 bullet）:")
print("=" * 60)
# Need to track through all transforms... let me just check original lines
# Actually re-run the comparison

# Show diffs for issue 5
print("\n" + "=" * 60)
print("问题5 详细修改列表（标题前 •）:")
print("=" * 60)
for i, (orig, new) in enumerate(zip(original_lines, lines)):
    if orig != new and re.match(r'^\s*•\s+#', orig):
        print(f"  行 {i+1}: [{orig.strip()}]")

# Show some examples of issue 1
print("\n" + "=" * 60)
print("问题1 示例（• 前多余空格 — 最多显示10处）:")
print("=" * 60)
count = 0
for i, (orig, new) in enumerate(zip(original_lines, lines)):
    if orig != new and count < 10:
        print(f"  行 {i+1}: [{orig.strip()}] -> [{new.strip()}]")
        count += 1

# Show some examples of issue 3
print("\n" + "=" * 60)
print(f"问题3: 共匹配到 {heading_blank_count} 处标题有多余空行")
print("=" * 60)
if heading_blank_count > 0:
    for m in re.finditer(r'^(#{1,5}\s+.*?)\n{3,}', content, flags=re.MULTILINE):
        heading = m.group(1).strip()
        print(f"  标题: {heading}")

# Show examples of issue 2
print("\n" + "=" * 60)
print(f"问题2: 共匹配到 {excessive_count} 处连续3+空行")
print("=" * 60)
