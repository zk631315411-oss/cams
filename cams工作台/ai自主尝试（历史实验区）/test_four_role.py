"""四角色法测试：爱国者法案题目"""
import json, os, sys, re

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from openai import OpenAI
client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

# Load
with open(f"{DATA}/agentic_search_eval_v2/ch2_full_text.txt", "r", encoding="utf-8") as f:
    textbook = f.read()
with open(f"{DATA}/questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)["questions"]
with open(f"{DATA}/cards_ch2.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

# Find question
q = None
for qq in questions:
    if "爱国者法案" in qq["stem"] and "代理" in qq["stem"]:
        q = qq
        break

stem = q["stem"]
options = q["options"]
answer = q["answer"]
opt_text = " ".join(f"{k}. {v}" for k, v in options.items())

print("题目:", stem)
print("选项:", opt_text)
print("答案:", answer)
print()

# ====== AI #1: 联想者 ======
print("=" * 60)
print("AI #1 联想者")
print("=" * 60)

ai1_prompt = f"""你是CAMS反洗钱考试专家。请基于你的知识自由回答以下问题。

题目：{stem}
选项：{opt_text}
正确答案：{answer}

请做三件事：
1. 这道题考的是教材里哪个知识点？在哪个章节？
2. 每个选项为什么对或错？把你所有能想到的理由都写出来，可以跨章节联想。
3. 你的回答中哪些地方是"需要查教材原文验证的具体事实主张"？请明确标出。"""

resp = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": ai1_prompt}],
    max_tokens=8000
)
ai1_output = resp.choices[0].message.content.strip()
print(ai1_output[:3000])
print("...")

# ====== AI #2: 核查员 ======
print()
print("=" * 60)
print("AI #2 核查员")
print("=" * 60)

ai2_prompt = f"""以下是AI对一道CAMS题目的分析。请从中提取所有"需要查教材原文验证的具体事实主张"。

规则：
- 每条主张必须是可以从教材原文中查到证据的具体断言
- 不要提取"选A正确"这种结论性判断
- 提取"爱国者法案第XXX条规定了……""BSA要求……""教材第X章指出……"这类具体主张
- 输出格式：每条一行，格式为"需要验证：[具体主张]"
- 提取完所有主张后，为每条主张生成1-3个教材搜索关键词

AI分析：
{ai1_output}"""

resp = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": ai2_prompt}],
    max_tokens=8000
)
ai2_output = resp.choices[0].message.content.strip()
print(ai2_output[:2000])

# ====== Search ======
print()
print("=" * 60)
print("搜索证据")
print("=" * 60)

claims = re.findall(r'需要验证：(.+)', ai2_output)
if not claims:
    claims = ["爱国者法案 代理账户 记录保留", "外国银行 所有者 识别", "314 信息共享", "BSA 货币工具"]

evidence_parts = []
for claim in claims[:10]:
    claim_clean = claim.strip()
    print(f"\n搜索: {claim_clean[:100]}")

    # Search in cards
    keywords = re.findall(r'[一-鿿\w]+', claim_clean)
    card_matches = []
    for c in cards:
        full = f"{c.get('knowledge','')} {c.get('context_before','')} {c.get('context_after','')}"
        score = sum(1 for kw in keywords if kw.lower() in full.lower())
        if score >= 2:
            card_matches.append((score, c))

    card_matches.sort(key=lambda x: -x[0])
    for score, c in card_matches[:3]:
        snippet = c.get('knowledge','')[:250]
        evidence_parts.append(f"[{c['card_id']}] {snippet}")
        print(f"  [{c['card_id']}] (score={score})")

# Also search textbook
for claim in claims[:5]:
    kws = re.findall(r'[一-鿿]{3,}', claim.strip())
    for kw in kws[:2]:
        idx = textbook.lower().find(kw.lower())
        if idx >= 0:
            snippet = textbook[max(0,idx-30):idx+250]
            evidence_parts.append(f"[教材原文] ...{snippet}...")
            break

print(f"\n总证据: {len(evidence_parts)} 条")

# ====== AI #3: 裁判官（不看AI #1的输出）======
print()
print("=" * 60)
print("AI #3 裁判官（仅基于证据）")
print("=" * 60)

evidence_text = "\n---\n".join(evidence_parts[:20])

ai3_prompt = f"""你是CAMS反洗钱考试专家。以下是教材中检索到的相关证据。请仅基于这些证据回答问题。

题目：{stem}
选项：{opt_text}
正确答案：{answer}

教材证据：
{evidence_text[:5000]}

请逐一分析每个选项为什么对或错。每个判断必须引用来源（card_id或教材原文）。
证据不足时明确说"证据不足"。

格式：
## 选项分析
### A. ...
判断：正确/错误
证据：...

### B. ...
判断：正确/错误
证据：..."""

resp = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": ai3_prompt}],
    max_tokens=8000
)
ai3_output = resp.choices[0].message.content.strip()
print(ai3_output)

# Save
out_dir = f"{DATA}/agentic_search_eval_v2/kg"
with open(f"{out_dir}/four_role_test_result.txt", "w", encoding="utf-8") as f:
    f.write(f"=== AI #1 联想者 ===\n{ai1_output}\n\n")
    f.write(f"=== AI #2 核查员 ===\n{ai2_output}\n\n")
    f.write(f"=== AI #3 裁判官 ===\n{ai3_output}\n")

print(f"\n结果已保存到 {out_dir}/four_role_test_result.txt")
