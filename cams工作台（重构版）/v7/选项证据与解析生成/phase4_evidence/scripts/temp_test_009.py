# -*- coding: utf-8 -*-
import json, pickle, sys, os
sys.path.insert(0, 'D:\\守正公司工作区\\cams考试\\cams工作台（重构版）\\v7\\选项证据与解析生成\\phase4_evidence\\scripts')
os.chdir('D:\\守正公司工作区\\cams考试\\cams工作台（重构版）\\v7\\选项证据与解析生成\\phase4_evidence')

from blind_adjudication import load_index, build_queries, get_bge_model, bge_search, BM25

pkl_path = 'D:\\守正公司工作区\\cams考试\\cams工作台（重构版）\\v7\\选项证据与解析生成\\phase3_index\\output\\index\\v7_index_5614abb1c4bf.pkl'
idx = load_index(pkl_path)
bge_vecs = idx['bge_vecs']
card_ids = idx['card_ids']
unit_lookup = idx['unit_lookup']

v7_path = 'D:\\守正公司工作区\\cams考试\\cams工作台（重构版）\\v7\\选项证据与解析生成\\phase3.5_questions\\output\\v7_questions.json'
with open(v7_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
q009 = [q for q in data['items'] if q['question_id'] == 'v7_q_000009'][0]

query_zh, query_en = build_queries(q009)
query_bge = query_zh + ' ' + query_en if query_en else query_zh
print('query_bge[:200]:', query_bge[:200])
print()

results = bge_search(query_bge, bge_vecs, card_ids, unit_lookup, top_k=10)
print('BGE top-10 (中英混合查询):')
for r in results:
    zh = r['knowledge_zh'][:60]
    print("  rank=%d score=%.4f | %s" % (r['rank'], r['score'], zh))
print()

# 和纯中文查询对比
print('BGE top-10 (纯中文查询对比):')
results_zh = bge_search(query_zh, bge_vecs, card_ids, unit_lookup, top_k=10)
for r in results_zh:
    zh = r['knowledge_zh'][:60]
    print("  rank=%d score=%.4f | %s" % (r['rank'], r['score'], zh))