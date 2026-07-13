# -*- coding: utf-8 -*-
"""测试 v7_q_000009：用考生角色 prompt"""

import json, pickle, os, sys
from openai import OpenAI

sys.path.insert(0, 'D:\\守正公司工作区\\cams考试\\cams工作台（重构版）\\v7\\选项证据与解析生成\\phase4_evidence\\scripts')
os.chdir('D:\\守正公司工作区\\cams考试\\cams工作台（重构版）\\v7\\选项证据与解析生成\\phase4_evidence')

from blind_adjudication import load_index, build_queries, get_bge_model, bge_search, BM25, search_and_merge

pkl_path = 'D:\\守正公司工作区\\cams考试\\cams工作台（重构版）\\v7\\选项证据与解析生成\\phase3_index\\output\\index\\v7_index_5614abb1c4bf.pkl'
idx = load_index(pkl_path)

v7_path = 'D:\\守正公司工作区\\cams考试\\cams工作台（重构版）\\v7\\选项证据与解析生成\\phase3.5_questions\\output\\v7_questions.json'
with open(v7_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
q009 = [q for q in data['items'] if q['question_id'] == 'v7_q_000009'][0]

bm25_zh = BM25(idx['zh_bm25_docs'], idx['zh_bm25_df'], idx['zh_bm25_avgdl'])
bm25_en = BM25(idx['en_bm25_docs'], idx['en_bm25_df'], idx['en_bm25_avgdl'])

candidates = search_and_merge(
    q009, bge_vecs=idx['bge_vecs'], card_ids=idx['card_ids'],
    unit_lookup=idx['unit_lookup'], bm25_zh_index=bm25_zh,
    bm25_en_index=bm25_en, top_k=20, merge_top_k=30
)
print('候选池: %d 个单元' % len(candidates))

# 构建候选文字
cand_text = ''
for c in candidates:
    cand_text += '--- 知识点 %s ---\n' % c['unit_id']
    cand_text += c['knowledge_zh'] + '\n'
    if c.get('en_quote'):
        cand_text += '（原文：' + c['en_quote'] + '）\n'
    cand_text += '\n'

# 考生角色 prompt
prompt = """你正在参加CAMS反洗钱认证考试。你考前只复习了以下知识点，现在考试时你只记得这些内容，没有其他背景知识。

你复习过的知识点：
%s

--- 考题 ---
%s
A: %s
B: %s
C: %s
D: %s

题型：单选题（只有一个正确答案）

请基于你复习过的知识点回答这道题。如果你复习过的知识点中没有任何一条能支撑某个选项，那这个选项就是错的。

请用 JSON 格式输出：
{
  "predicted_answer": ["A"],
  "reasoning": "简短说明你的推理过程，引用你记得的知识点编号",
  "option_analysis": [
    {
      "option": "A",
      "judgement": "correct|incorrect|insufficient",
      "evidence_status": "direct|indirect|none",
      "evidence_cards": [
        {"unit_id": "v7u_N000001", "support_type": "direct|indirect|negative", "reason": "为什么这个知识点支持或反驳该选项"}
      ]
    }
  ]
}""" % (
    cand_text,
    q009['stem'],
    q009['options'].get('A', ''),
    q009['options'].get('B', ''),
    q009['options'].get('C', ''),
    q009['options'].get('D', ''),
)

print('prompt 长度: %d 字符' % len(prompt))
print()

api_key = os.environ.get('DEEPSEEK_API_KEY') or os.environ.get('DS_API_KEY')
base_url = os.environ.get('DEEPSEEK_BASE_URL') or os.environ.get('DS_BASE_URL') or 'https://api.deepseek.com'

client = OpenAI(api_key=api_key, base_url=base_url)

kwargs = {
    'model': 'deepseek-v4-pro',
    'messages': [{'role': 'user', 'content': prompt}],
    'temperature': 0,
    'max_tokens': 20000,
    'timeout': 180,
    'reasoning_effort': 'high',
    'extra_body': {'thinking': {'type': 'enabled'}},
}

print('调用 LLM（考生角色 + thinking mode）...')
response = client.chat.completions.create(**kwargs)
llm_output = (response.choices[0].message.content or '').strip()

import re
def strip_json_fence(text):
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)
    return text.strip()

cleaned = strip_json_fence(llm_output)
parsed = json.loads(cleaned)

print()
print('推理过程:', parsed.get('reasoning', '无'))
print()
print('预测答案:', parsed.get('predicted_answer', []))
print()
for oa in parsed.get('option_analysis', []):
    print('选项 %s: judgement=%s, evidence_status=%s, evidence_cards=%d' % (
        oa['option'], oa['judgement'], oa['evidence_status'], len(oa.get('evidence_cards', []))
    ))
    for ec in oa.get('evidence_cards', []):
        print('  -> unit_id=%s, support=%s, reason=%s' % (
            ec['unit_id'], ec.get('support_type','?'), ec.get('reason','')[:100]
        ))