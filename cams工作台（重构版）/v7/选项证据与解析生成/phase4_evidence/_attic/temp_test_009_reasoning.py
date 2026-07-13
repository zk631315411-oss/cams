# -*- coding: utf-8 -*-
"""单独测试 v7_q_000009，加 reasoning_effort，看能否选对 A"""

import json, pickle, os, sys
from openai import OpenAI

sys.path.insert(0, 'D:\\守正公司工作区\\cams考试\\cams工作台（重构版）\\v7\\选项证据与解析生成\\phase4_evidence\\scripts')
os.chdir('D:\\守正公司工作区\\cams考试\\cams工作台（重构版）\\v7\\选项证据与解析生成\\phase4_evidence')

from blind_adjudication import load_index, build_queries, get_bge_model, bge_search, BM25, search_and_merge, build_prompt

# 加载索引
pkl_path = 'D:\\守正公司工作区\\cams考试\\cams工作台（重构版）\\v7\\选项证据与解析生成\\phase3_index\\output\\index\\v7_index_5614abb1c4bf.pkl'
idx = load_index(pkl_path)

# 加载 009
v7_path = 'D:\\守正公司工作区\\cams考试\\cams工作台（重构版）\\v7\\选项证据与解析生成\\phase3.5_questions\\output\\v7_questions.json'
with open(v7_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
q009 = [q for q in data['items'] if q['question_id'] == 'v7_q_000009'][0]

# 构建 BM25 索引
from blind_adjudication import BM25
bm25_zh = BM25(idx['zh_bm25_docs'], idx['zh_bm25_df'], idx['zh_bm25_avgdl'])
bm25_en = BM25(idx['en_bm25_docs'], idx['en_bm25_df'], idx['en_bm25_avgdl'])

# 检索 -> 候选池
candidates = search_and_merge(
    q009, bge_vecs=idx['bge_vecs'], card_ids=idx['card_ids'],
    unit_lookup=idx['unit_lookup'], bm25_zh_index=bm25_zh,
    bm25_en_index=bm25_en, top_k=20, merge_top_k=30
)
print('候选池: %d 个单元' % len(candidates))

# 构建 prompt
prompt = build_prompt(q009, candidates)
print('prompt 长度: %d 字符' % len(prompt))
print()

# LLM 调用（加 reasoning_effort）
api_key = os.environ.get('DEEPSEEK_API_KEY') or os.environ.get('DS_API_KEY')
base_url = os.environ.get('DEEPSEEK_BASE_URL') or os.environ.get('DS_BASE_URL') or 'https://api.glm-5.2.com/v1'

client = OpenAI(api_key=api_key, base_url=base_url)

kwargs = {
    'model': 'deepseek-v4-pro',
    'messages': [{'role': 'user', 'content': prompt}],
    'temperature': 0,
    'max_tokens': 20000,
    'timeout': 180,
}

print('调用 LLM（加 reasoning_effort=high）...')
response = client.chat.completions.create(**kwargs)
llm_output = (response.choices[0].message.content or '').strip()

# 解析
import re
def strip_json_fence(text):
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)
    return text.strip()

cleaned = strip_json_fence(llm_output)
parsed = json.loads(cleaned)

print()
print('预测答案:', parsed.get('predicted_answer', []))
print()
for oa in parsed.get('option_analysis', []):
    print('选项 %s: judgement=%s, evidence_status=%s, evidence_cards=%d' % (
        oa['option'], oa['judgement'], oa['evidence_status'], len(oa.get('evidence_cards', []))
    ))
    for ec in oa.get('evidence_cards', []):
        print('  -> unit_id=%s, support=%s, reason=%s' % (
            ec['unit_id'], ec.get('support_type','?'), ec.get('reason','')[:80]
        ))