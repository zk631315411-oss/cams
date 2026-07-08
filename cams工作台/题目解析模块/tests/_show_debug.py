import json
from pathlib import Path

p = Path(r"d:\守正公司工作区\cams考试\cams工作台\题目解析模块\outputs\reports\sample_5_questions.json")
data = json.loads(p.read_text(encoding="utf-8"))
for d in data:
    q = d["question"]
    m = d["match"]
    print(f"\n=== 题{q['number']} {q['id']} ===")
    print(f"status: {m.get('status')}")
    print(f"analysis_generated: {m.get('analysis_generated')}")
    if m.get("analysis_error"):
        print(f"analysis_error: {m['analysis_error']}")
    if m.get("_debug_raw_adjudicator"):
        print(f"_debug_raw_adjudicator (前800字):")
        print(m["_debug_raw_adjudicator"][:800])
        print("---")
