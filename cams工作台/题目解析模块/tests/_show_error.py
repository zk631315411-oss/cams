import json
from pathlib import Path

p = Path(r"d:\守正公司工作区\cams考试\cams工作台\题目解析模块\outputs\reports\sample_5_questions.json")
data = json.loads(p.read_text(encoding="utf-8"))
for d in data:
    q = d["question"]
    m = d["match"]
    print(f"题{q['number']} {q['id']} | status={m.get('status')} | analysis_generated={m.get('analysis_generated')}")
    if m.get("analysis_error"):
        print(f"  analysis_error: {m['analysis_error']}")
    if m.get("error"):
        print(f"  error: {m['error']}")
    print(f"  matched_card_ids: {m.get('evidence_count')} 张")
    print(f"  option_analysis: {len(m.get('option_analysis', []))} 条")
