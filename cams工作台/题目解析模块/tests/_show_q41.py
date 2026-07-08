import json
from pathlib import Path

p = Path(r"d:\守正公司工作区\cams考试\cams工作台\题目解析模块\outputs\reports\sample_5_questions.json")
data = json.loads(p.read_text(encoding="utf-8"))

# 只看题 41 的完整解析（最佳示例）
d = data[4]  # 题 41
q = d["question"]
m = d["match"]
print(f"题{q['number']} {q['id']} | 答案: {q['answer']}")
print(f"题干: {q['stem']}")
print(f"状态: {m['status']} | 解析生成: {m['analysis_generated']} | 耗时: {m['elapsed_ms']:.0f}ms")
print(f"\n选项级解析:")
for row in m.get("option_analysis", []):
    label = row.get("option", "")
    judge = row.get("judgement", "")
    ev_status = row.get("evidence_status", "")
    explanation = row.get("explanation", "")
    common_trap = row.get("common_trap", "")
    ev_cards = row.get("evidence_cards", []) or []
    print(f"\n  选项{label} [{judge}] [证据:{ev_status}]")
    print(f"    解析: {explanation[:200]}")
    if common_trap:
        print(f"    易错点: {common_trap[:150]}")
    if ev_cards:
        print(f"    证据句卡 ({len(ev_cards)} 张):")
        for c in ev_cards[:2]:
            cid = c.get("card_id", "")
            quote = (c.get("quote") or "")[:100]
            reason = (c.get("reason") or "")[:120]
            print(f"      - {cid}: {quote}")
            print(f"        理由: {reason}")
