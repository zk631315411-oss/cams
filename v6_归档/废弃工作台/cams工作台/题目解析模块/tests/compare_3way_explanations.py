"""三方解析对比：教研原始解析 vs pro+关思考 vs flash+思考。

对同一批5题（flash的随机5题），逐选项打印三方解析，用于人工对比。
"""
import json
import re
from pathlib import Path

_ROOT = Path(r"D:\守正公司工作区\cams考试")
_ASSETS = _ROOT / "cams工作台" / "data" / "teaching_assets"
_MODULE = _ROOT / "cams工作台" / "题目解析模块"

# ==== 1. 教研原始解析：从习题md里解析 ====
_MD_DIR = _ROOT / "教材、答疑记录、习题与参考文献" / "习题" / "习题结构化"
_RE_Q = re.compile(r"^##\s*第(\d+)题\s*(.*)", re.MULTILINE)
_RE_OPT = re.compile(r"^-\s*([A-K])[\.、\)）]\s*(.+)", re.MULTILINE)
_RE_ANS = re.compile(r"答案\s*[:：]\s*([A-K,，、/;；\s]+)")
_RE_EXPL = re.compile(r"###\s*解析\s*\n(.+?)(?:\n---|\Z)", re.DOTALL)


def load_teacher_explanations(md_path: Path) -> dict[str, dict]:
    """从习题md解析教研解析，返回 {qid: {stem, options, answer, explanation}}。"""
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"^#\s*([\d.]+)\s*习题", text, re.MULTILINE)
    section = m.group(1).strip() if m else md_path.stem.replace("_", ".")

    blocks = re.split(r"(?=^##\s*第\d+题)", text, flags=re.MULTILINE)
    result = {}
    for block in blocks:
        qm = _RE_Q.search(block)
        if not qm:
            continue
        num = int(qm.group(1))
        stem = qm.group(2).strip()
        options = {om.group(1): om.group(2).strip() for om in _RE_OPT.finditer(block)}
        am = _RE_ANS.search(block)
        answer = ",".join(sorted(set(re.findall(r"[A-K]", am.group(1).upper())))) if am else ""
        em = _RE_EXPL.search(block)
        explanation = em.group(1).strip() if em else ""

        qid = f"{section}_{num}"
        result[qid] = {"stem": stem, "options": options, "answer": answer, "explanation": explanation}
    return result


# 加载第二章全部教研解析
teacher_all = {}
for md_path in sorted(_MD_DIR.glob("2_*_习题.md")):
    teacher_all.update(load_teacher_explanations(md_path))

# ==== 2. pro+关思考：从 option_evidence_map.json 取 ====
oem = json.loads((_ASSETS / "option_evidence_map.json").read_text(encoding="utf-8"))
pro_by_qid = {it["question_id"]: it for it in oem["items"]}

# ==== 3. flash+思考：从 outputs/flash_5q_comparison 取 ====
flash_files = sorted((_MODULE / "outputs" / "flash_5q_comparison").glob("*.json"))
flash_data = json.loads(flash_files[-1].read_text(encoding="utf-8"))
flash_by_qid = {r["question_id"]: r for r in flash_data["results"]}

# ==== 4. 三方对比 ====
TARGET_IDS = ["2.8_2", "2.1_29", "2.1_7", "2.3_1", "2.2_13"]

for qid in TARGET_IDS:
    t = teacher_all.get(qid, {})
    p = pro_by_qid.get(qid, {})
    f = flash_by_qid.get(qid, {})

    print(f"\n{'='*90}")
    print(f"题目 {qid}: {t.get('stem', '')}")
    print(f"标准答案: {t.get('answer', '')}")
    print(f"{'='*90}")

    # 教研解析（整段）
    t_expl = t.get("explanation", "")
    print(f"\n【教研解析】（来自习题md，{len(t_expl)} 字）:")
    print(t_expl[:600])
    if len(t_expl) > 600:
        print(f"  ...（共{len(t_expl)}字）")

    # pro 解析（逐选项）
    print(f"\n【pro+关思考】（deepseek-v4-pro）:")
    for o in p.get("options", []):
        label = o["option"]
        expl = o.get("explanation", "")
        trap = o.get("common_trap", "")
        cards = o.get("card_ids", [])
        print(f"  选项{label} [{o.get('judgement','?')}] | 证据{len(cards)}张")
        print(f"    解析: {expl[:200]}")
        if trap:
            print(f"    易错: {trap[:120]}")

    # flash 解析（逐选项）
    print(f"\n【flash+思考】（deepseek-v4-flash）:")
    for o in f.get("option_analysis", []):
        label = o.get("option", "?")
        expl = o.get("explanation", "")
        trap = o.get("common_trap", "")
        cards = o.get("evidence_cards", []) or []
        print(f"  选项{label} [{o.get('judgement','?')}] | 证据{len(cards)}张")
        print(f"    解析: {expl[:200]}")
        if trap:
            print(f"    易错: {trap[:120]}")

    print(f"\n{'─'*90}")
