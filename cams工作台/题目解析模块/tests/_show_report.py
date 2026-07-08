import json
from pathlib import Path

p = Path(r"d:\守正公司工作区\cams考试\cams工作台\题目解析模块\outputs\reports\sample_5_questions.json")
data = json.loads(p.read_text(encoding="utf-8"))
for d in data:
    q = d["question"]
    m = d["match"]
    print(f"题{q['number']} {q['id']} | {m['status']} | {m['evidence_count']}cards | {m['elapsed_ms']:.0f}ms | kp={m['knowledge_point'][:25]}")
    # 前3张证据
    for i, cid in enumerate(m["matched_card_ids"][:3], 1):
        print(f"  [{i}] {cid}")
