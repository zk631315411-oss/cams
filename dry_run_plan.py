import os, re

base = r'D:\守正公司工作区\cams考试\教材、答疑记录、习题与参考文献\答疑记录\答疑记录结构化'
files = sorted(os.listdir(base))

print('=' * 80)
print('DRY-RUN 修改清单 — 共 %d 个文件' % len([f for f in files if f.endswith('.md')]))
print('=' * 80)

rename_count = 0
answer_fix_count = 0
q_prefix_count = 0
h1_fix_count = 0
total_files_with_issues = 0

for fname in files:
    fpath = os.path.join(base, fname)
    if not fname.endswith('.md'):
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    issues = []
    new_fname = fname

    # --- 1. Check filename ---
    m_zhangjie_space = re.match(r'^第二章 (\d+\.\d+_.*\.md)$', fname)
    m_zhangjie_nospace = re.match(r'^第二章(\d+\.\d+_.*\.md)$', fname)
    m_zhangjie_other = re.match(r'^第二章_(.+\.md)$', fname)
    m_di_zhang = re.match(r'^第(\d+)章_(.+\.md)$', fname)

    if m_zhangjie_space:
        new_fname = m_zhangjie_space.group(1)
        issues.append('[文件名] 去掉"第二章 "前缀')
        rename_count += 1
    elif m_zhangjie_nospace:
        new_fname = m_zhangjie_nospace.group(1)
        issues.append('[文件名] 去掉"第二章"前缀，已有数字')
        rename_count += 1
    elif m_zhangjie_other:
        # '第二章_69题_xxx.md' - need to extract from H1
        h1_match = re.match(r'^# 第(\w+)章\s+(.*)', lines[0].strip()) if lines else None
        if h1_match:
            rest = h1_match.group(2)
            sec_match = re.match(r'(\d+\.\d+)\s', rest)
            if sec_match:
                rest_of_name = m_zhangjie_other.group(1)
                # Get title part (after first _ which is 69题_etc)
                parts = rest_of_name.split('_', 1)
                if len(parts) > 1:
                    new_fname = sec_match.group(1) + '_' + parts[1]
                else:
                    new_fname = sec_match.group(1) + '_' + rest_of_name
                issues.append('[文件名] 从H1提取章节号重命名: %s' % sec_match.group(1))
            else:
                issues.append('[文件名] 需人工确定章节号，H1无X.X格式: ' + lines[0].strip()[:80])
                new_fname = fname  # keep original
        rename_count += 1
    elif m_di_zhang:
        h1_match = re.match(r'^# 第(\w+)章\s+(.*)', lines[0].strip()) if lines else None
        if h1_match:
            rest = h1_match.group(2)
            sec_match = re.match(r'(\d+\.\d+)\s', rest)
            if sec_match:
                new_fname = sec_match.group(1) + '_' + m_di_zhang.group(2)
                issues.append('[文件名] 从H1提取章节号重命名: %s' % sec_match.group(1))
            else:
                issues.append('[文件名] 需人工确定章节号，H1无X.X格式: ' + lines[0].strip()[:80])
                new_fname = fname
        rename_count += 1

    # Check for extra parenthesis in filename
    if '(' in fname and not fname.startswith('3.5'):
        pass  # the 3.5 file has ( in name which is part of title

    # --- 2. Check ## 答案 line ---
    answer_lineno = None
    for i, line in enumerate(lines):
        if line.strip().startswith('## 答案'):
            answer_lineno = i
            break
    if answer_lineno is not None and answer_lineno + 1 < len(lines):
        ans_line = lines[answer_lineno + 1].strip()
        # Extract uppercase A-G letters
        letters = re.findall(r'[A-G]', ans_line)
        target = '答案：' + ','.join(letters) if letters else '答案：'
        if ans_line != target:
            # Show before/after
            before = ans_line[:60] + ('...' if len(ans_line) > 60 else '')
            issues.append('[答案行] "%s" -> "%s"' % (before, target))
            answer_fix_count += 1

    # --- 3. Check ## 学生提出的问题 for Q： ---
    for i, line in enumerate(lines):
        if line.strip().startswith('## 学生提出的问题'):
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if re.match(r'^Q：', next_line.strip()):
                    new_next = re.sub(r'^Q：', '', next_line.strip())
                    before_q = next_line.strip()[:50] + ('...' if len(next_line.strip()) > 50 else '')
                    issues.append('[学生问题] 去掉Q：前缀: "%s" -> "%s"' % (before_q, new_next[:50]))
                    q_prefix_count += 1
            break

    # --- 4. Check # H1 line ---
    h1 = lines[0].strip() if lines else ''
    # Fix double spaces after 第X章
    h1_fixed = re.sub(r'^(# 第\w+章)\s{2,}(\d+\.\d+)', r'\1 \2', h1)
    # Fix missing space: # 第二章2.8 -> # 第二章 2.8
    h1_fixed = re.sub(r'^(# 第\w+章)(\d+\.\d+)', r'\1 \2', h1_fixed)
    if h1_fixed != h1:
        before = h1[:80] + ('...' if len(h1) > 80 else '')
        after = h1_fixed[:80] + ('...' if len(h1_fixed) > 80 else '')
        issues.append('[H1标题] "%s" -> "%s"' % (before, after))
        h1_fix_count += 1

    # Print if any issues
    if issues or new_fname != fname:
        total_files_with_issues += 1
        # Sanitize for console
        safe_fname = fname.encode('gbk', errors='replace').decode('gbk', errors='replace')
        print('\n文件: %s' % safe_fname)
        if new_fname != fname:
            safe_new = new_fname.encode('gbk', errors='replace').decode('gbk', errors='replace')
            print('  -> 新文件名: %s' % safe_new)
        for iss in issues:
            safe_iss = iss.encode('gbk', errors='replace').decode('gbk', errors='replace')
            print('  %s' % safe_iss)

print('\n' + '=' * 80)
print('统计汇总:')
print('  有改动的文件: %d / %d' % (total_files_with_issues, len([f for f in files if f.endswith('.md')])))
print('  需重命名文件: %d' % rename_count)
print('  需修正答案行: %d' % answer_fix_count)
print('  需去掉Q：前缀: %d' % q_prefix_count)
print('  需修正H1标题: %d' % h1_fix_count)
print('=' * 80)
