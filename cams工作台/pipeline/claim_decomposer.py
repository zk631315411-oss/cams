"""P3: Claim Decomposition — 选项命题拆解"""
import os, sys, json, re
from openai import OpenAI

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_DIR = os.path.join(DATA_DIR, "agentic_search_eval", "03_claim_decomposition")

PROMPT = """你是CAMS反洗钱考试命题分析助手。分析这道多选题，对每个选项做结构化拆解。

对每个选项，你需要从三个维度分析需要验证什么：
1. 主体（这个后果发生在谁身上？FI还是其他主体？）
2. 方向（这个后果是增加还是减少？教材里实际是什么方向？）
3. 机制（如果这个选项是错的，教材里可能通过什么机制来解释？）

每个选项输出：
- option
- claim: 完整命题
- expected_relation: must_be_true / likely_false
- needed_checks: 至少2个check，必须包含主体检查和方向/机制检查。每个check:
  - check: 验证点名称
  - search_intent: 检索意图
  - query_draft: 检索query（中文关键词，空格分隔）
  - observable_source: 每个词标注来源（question_text / controller_inference）

关键要求：
- 对于likely_false的选项（B/C/D），你必须思考：如果这个说法是错的，那教材里正确的说法应该是什么？谁才是真正的主体？真正的方向是什么？
- 例如D选项"公司税增加"——你需要思考：洗钱真的会导致税增加吗？如果是税减少，发生在谁身上？FI还是政府？把这些假设写成controller_inference词
- query_draft不能只是选项原文的复述。必须包含你基于结构分析推演出的检索方向
- 不能使用你知道的教材专业术语（"政府税收缩水""贸易洗钱""空壳公司""黑市比索""BMPE"）
- 输出JSON数组，不要markdown包裹

题目：
题干：(多选题)洗钱会对金融机构FI造成哪些后果？(选择两个。)
选项：
A. 盈利业务的减少或损失
B. 代理银行设施的增加
C. 雇员人数减少
D. 公司税的增加
E. 调查费用和罚金的增加
正确答案：A,E"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    resp = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": PROMPT}],
        temperature=0.1,
        max_tokens=4000,
    )

    raw = resp.choices[0].message.content or ""
    raw = raw.strip()
    # Save raw for debugging
    with open(os.path.join(OUT_DIR, "raw_response.txt"), "w", encoding="utf-8") as f:
        f.write(raw)
    # Also save full response
    full_resp = resp.choices[0].model_dump_json()
    with open(os.path.join(OUT_DIR, "full_response.json"), "w", encoding="utf-8") as f:
        f.write(full_resp)
    if not raw:
        print("ERROR: LLM returned empty response. Check full_response.json")
        sys.exit(1)
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import json_repair
        repaired = json_repair.repair_json(raw)
        result = json.loads(repaired)

    # Save
    out_path = os.path.join(OUT_DIR, "claim_decomp.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Leakage check
    oracle_words = ["政府税收缩水", "贸易洗钱", "虚假发票", "BMPE", "黑市比索", "空壳公司"]
    leakage = False
    for item in (result if isinstance(result, list) else [result]):
        if item.get("option") != "D":
            continue
        print(f"Option D claim: {item.get('claim', 'N/A')}")
        for check in item.get("needed_checks", []):
            qd = check.get("query_draft", "")
            leaked = [w for w in oracle_words if w in qd]
            if leaked:
                print(f"  LEAKAGE in '{check['check']}': {leaked}")
                leakage = True

    if leakage:
        print("\n[FAIL] Oracle word leakage detected")
    else:
        print("\n[PASS] No leakage")

    # Print D option fully
    for item in (result if isinstance(result, list) else [result]):
        if item.get("option") == "D":
            print(json.dumps(item, ensure_ascii=False, indent=2))

    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
