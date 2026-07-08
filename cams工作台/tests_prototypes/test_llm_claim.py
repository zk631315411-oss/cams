"""
测试：给 LLM 教材结构，看它能不能做出 Claim Decomposition + Evidence Frame 映射
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from openai import OpenAI

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ── 1. 加载教材结构 ──────────────────────────────────────────────
def load_textbook_structure():
    """提取 Ch2 各节的标题和核心概念"""
    with open(os.path.join(DATA_DIR, "chapters", "ch2.json"), "r", encoding="utf-8") as f:
        ch2 = json.load(f)
    with open(os.path.join(DATA_DIR, "cards_ch2.json"), "r", encoding="utf-8") as f:
        cards = json.load(f)
    card_by_id = {c["card_id"]: c for c in cards}

    lines = []
    for sec in ch2["sections"]:
        lines.append(f"\n## {sec['section_id']} {sec['section_title']}")
        for sub in sec["subsections"][:5]:
            card_ids = set()
            for p in sub["paragraphs"]:
                card_ids.update(p["card_ids"])
            concepts = []
            for cid in list(card_ids)[:4]:
                if cid in card_by_id:
                    concepts.append(card_by_id[cid]["knowledge"])
            lines.append(f"  [{sub['title'][:40]}] {'; '.join(concepts[:2])}")
    return "\n".join(lines)


# ── 2. Prompt ──────────────────────────────────────────────────────
PROMPT = """你是CAMS反洗钱教研专家。下面是CAMS教材第二章的目录和各节核心概念：

{textbook_structure}

现在有一道考试题和一个干扰项，需要你做 Claim Decomposition，即把选项拆解成结构化声明，然后从教材中找到反对这个声明的证据方向。

题目：
{question_text}

你需要分析的是干扰项 D："公司税的增加"，即"洗钱会对金融机构FI造成公司税的增加"。

请按以下步骤分析：

1. **Claim 拆解**：把这个选项拆成结构化声明
   - subject（主体是谁）
   - object（什么在变化）
   - direction（变化方向）
   - claim_type（这是什么类型的错误）

2. **误解诊断**：学生为什么可能会选这个？
   - misunderstanding_type（误解类型标签）
   - 学生可能的推理路径

3. **证据方向映射**：基于教材结构，从哪些小节可以找到反证材料？
   对每个证据方向，说明：
   - 教材哪一节
   - 要找什么类型的信息
   - 为什么这个信息可以反证D

4. **检索锚点**：基于以上分析，生成具体的检索锚点
   - 结构锚点（主体/方向对比类）
   - 机制锚点（具体的洗钱手段/案例类）

输出JSON格式，不要markdown包裹：
{{
  "claim_decomposition": {{
    "subject": "",
    "object": "",
    "direction": "",
    "claim_type": ""
  }},
  "misunderstanding": {{
    "type": "",
    "student_reasoning": ""
  }},
  "evidence_directions": [
    {{
      "section": "",
      "info_needed": "",
      "refutation_logic": ""
    }}
  ],
  "anchors": {{
    "structural": [""],
    "mechanism": ["", "", "", ""]
  }}
}}"""


def main():
    textbook = load_textbook_structure()

    question_text = """题干：(多选题)洗钱会对金融机构FI造成哪些后果?(选择两个。)
选项：
A. 盈利业务的减少或损失
B. 代理银行设施的增加
C. 雇员人数减少
D. 公司税的增加
E. 调查费用和罚金的增加
正确答案：A,E"""

    prompt = PROMPT.format(textbook_structure=textbook, question_text=question_text)

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    print("调用 DeepSeek v4-pro (含教材结构)...")
    resp = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content": "你是CAMS反洗钱教研专家。输出严格JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=3000,
    )

    raw = resp.choices[0].message.content.strip()
    # Save raw
    with open(os.path.join(DATA_DIR, "llm_claim_raw.txt"), "w", encoding="utf-8") as f:
        f.write(raw)

    # Parse
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    result = json.loads(raw)

    output_path = os.path.join(DATA_DIR, "llm_claim_decomposition.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n=== Claim Decomposition ===")
    cd = result.get("claim_decomposition", {})
    print(f"  subject: {cd.get('subject')}")
    print(f"  object: {cd.get('object')}")
    print(f"  direction: {cd.get('direction')}")
    print(f"  claim_type: {cd.get('claim_type')}")

    print(f"\n=== Misunderstanding ===")
    mu = result.get("misunderstanding", {})
    print(f"  type: {mu.get('type')}")
    print(f"  reasoning: {mu.get('student_reasoning', '')[:100]}...")

    print(f"\n=== Evidence Directions ===")
    for ed in result.get("evidence_directions", []):
        print(f"  [{ed.get('section', '')}] {ed.get('info_needed', '')[:80]}...")

    print(f"\n=== Anchors ===")
    anc = result.get("anchors", {})
    print(f"  structural: {anc.get('structural', [])}")
    print(f"  mechanism: {anc.get('mechanism', [])}")

    print(f"\n详细结果: {output_path}")


if __name__ == "__main__":
    main()
