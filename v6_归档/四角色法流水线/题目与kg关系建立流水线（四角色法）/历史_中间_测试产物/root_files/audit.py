"""按验收目标审计 step1 输出"""
import json, os, re
from collections import Counter

d = 'D:/守正公司工作区/cams考试/题目与kg关系建立流水线（四角色法）/output/step1_ai_responses/'
files = sorted([f for f in os.listdir(d) if f.endswith('.json')])

# 1. Traceability
print("=" * 60)
print("1. 可追溯性")
print("=" * 60)
for f in files:
    with open(os.path.join(d,f), encoding='utf-8') as fh:
        data = json.load(fh)
    qid = data['question_id']
    q = data.get('quality', {})
    ai3 = data.get('ai3_output', '')
    opt_count = len(data.get('options', {}))
    real_status = restatus(ai3, opt_count)

    if real_status == 'answered':
        blocks = re.split(r'###\s*([A-E])', ai3)
        all_ok = True
        for i in range(1, len(blocks), 2):
            block = blocks[i+1] if i+1 < len(blocks) else ""
            jm = re.search(r'判断[：:]\s*(.+)', block)
            if jm and ('正确' in jm.group(1) or '错误' in jm.group(1)):
                if not re.search(r'v6_b\d+_N\d+', block):
                    all_ok = False
        print(f'{qid} ({real_status}): 正向判断挂card_id = {all_ok}')
    else:
        print(f'{qid} ({real_status}): 跳过')

    h = q.get('hallucinations', [])
    print(f'  幻觉={len(h)}/{q.get("total_cited",0)} | 选项={q.get("analyzed_options","?")}/{q.get("expected_options","?")} | 矛盾={q.get("conflict_count",0)}')

# Re-classify using strict >=50% rule
def restatus(ai3_text, option_count):
    if not ai3_text: return "ai3_empty"
    judgments = re.findall(r'判断[：:]\s*(.+)', ai3_text)
    confident = sum(1 for j in judgments if re.search(r'正确|错误|对|错', j) and '证据不足' not in j)
    if option_count > 0 and confident >= option_count * 0.5:
        return "answered"
    return "evidence_insufficient"

# 2. Answer rate
print()
print("=" * 60)
print("3. 可答率")
answered = 0
for f in files:
    with open(os.path.join(d,f), encoding='utf-8') as fh:
        data = json.load(fh)
    ai3 = data.get('ai3_output', '')
    opt_count = len(data.get('options', {}))
    real_status = restatus(ai3, opt_count)
    if real_status == 'answered':
        answered += 1
total = len(files)
rate = answered / total * 100 if total > 0 else 0
target = 70
gap = target - rate if rate < target else 0
print(f'{answered}/{total} = {rate:.0f}% (目标 >= 70%): {"PASS" if rate >= target else "差" + str(int(gap)) + "%"}')

# Per-chapter
chapters = Counter()
ch_ans = Counter()
for f in files:
    with open(os.path.join(d,f), encoding='utf-8') as fh:
        data = json.load(fh)
    ch = data['question_id'].rsplit('_',1)[0]
    chapters[ch] += 1
    ai3 = data.get('ai3_output', '')
    opt_count = len(data.get('options', {}))
    if restatus(ai3, opt_count) == 'answered':
        ch_ans[ch] += 1
print("按章节:")
for ch in sorted(chapters.keys()):
    print(f"  {ch}: {ch_ans[ch]}/{chapters[ch]}")

# 3. Sample AI #3 for answered
print()
print("=" * 60)
print("4. 已答题目 AI #3 摘录")
for f in files:
    with open(os.path.join(d,f), encoding='utf-8') as fh:
        data = json.load(fh)
    ai3 = data.get('ai3_output','')
    opt_count = len(data.get('options', {}))
    if restatus(ai3, opt_count) != 'answered':
        continue
    qid = data['question_id']
    print(f'\n--- {qid} ---')
    print(ai3[:800])

# 4. Summary
print()
print("=" * 60)
print("5. 汇总")
total_hallucinations = 0
total_conflicts = 0
option_missing = 0
for f in files:
    with open(os.path.join(d,f), encoding='utf-8') as fh:
        data = json.load(fh)
    q = data.get('quality', {})
    total_hallucinations += len(q.get('hallucinations', []))
    total_conflicts += q.get('conflict_count', 0)
    if not q.get('option_coverage_ok', True):
        option_missing += 1

print(f'总题数: {total}')
print(f'可追溯 (answered): {answered}')
print(f'证据不足: {total - answered}')
print(f'幻觉总数: {total_hallucinations}')
print(f'矛盾总数: {total_conflicts}')
print(f'选项缺失题数: {option_missing}')

# 5. Edge expansion audit
print()
print("=" * 60)
print("6. 沿边扩展审计")
for f in files:
    with open(os.path.join(d,f), encoding='utf-8') as fh:
        data = json.load(fh)
    qid = data['question_id']
    ev = data.get('evidence', [])
    direct = len([e for e in ev if e['source'] == 'bge_direct'])
    edge = len([e for e in ev if e['source'] == 'edge_expand'])
    cited = set(data.get('cited_cards', []))
    cited_direct = len([c for c in cited if any(e['card_id']==c and e['source']=='bge_direct' for e in ev)])
    cited_edge = len([c for c in cited if any(e['card_id']==c and e['source']=='edge_expand' for e in ev)])
    print(f'{qid}: 证据{len(ev)}条 (BGE直{direct} + 边{edge}) | 被引用{direct}+{edge}边')
