"""最小测试2：跳过检索，只测 adjudicator LLM 调用和解析。"""
import sys
import traceback
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parents[1]
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

from env_setup import _load_env
_load_env()

from pipeline.evidence_pool import get_match_runtime
from pipeline.match_pipeline import build_known_answer_adjudicator_prompt, _parse_llm_json
from pipeline.question_loader import load_questions
import run_step1

_MD_DIR = (
    _MODULE_DIR.parent.parent
    / "教材、答疑记录、习题与参考文献"
    / "习题"
    / "习题结构化提取"
)

print("加载题目...")
questions = load_questions(_MD_DIR, sections=["3.1"])
q = questions[0]
print(f"题: {q.id} | 答案: {q.answer}")

print("加载 runtime...")
rt = get_match_runtime()
client = rt.base.client

# 构造假候选句卡（用 rt 里的真实句卡）
print("构造假候选...")
fake_candidates = {}
for label in q.options:
    # 随便取 3 张句卡作为假候选
    fake_candidates[label] = [
        {
            "card_id": f"v6s_N0000{i}",
            "citation": f"测试句卡 {i} 的内容",
            "knowledge": f"测试知识点 {i}",
            "score": 0.5 + i * 0.1,
            "source": "test",
        }
        for i in range(1, 4)
    ]

search_plan = {
    "stem": q.stem,
    "options": q.options,
    "option_plans": {
        label: {
            "option_claim": text,
            "evidence_need": f"判断{label}",
            "must_terms": [],
        }
        for label, text in q.options.items()
    },
}

print("构建 prompt...")
prompt = build_known_answer_adjudicator_prompt(q.stem, q.options, q.answer, search_plan, fake_candidates)
print(f"prompt 长度: {len(prompt)}")
print(f"prompt 前300字:\n{prompt[:300]}")
print("---")

print("调用 LLM...")
try:
    raw_adj = run_step1.call_llm(client, prompt, max_tokens=9000)
    print(f"raw_adj 类型: {type(raw_adj)}, 长度: {len(raw_adj)}")
    print(f"raw_adj 前1000字:\n{raw_adj[:1000]}")
    print("---")

    print("解析 JSON...")
    parsed = _parse_llm_json(raw_adj)
    print(f"parsed 类型: {type(parsed)}")
    if isinstance(parsed, dict):
        print(f"keys: {list(parsed.keys())}")
        oa = parsed.get("option_analysis")
        print(f"option_analysis 类型: {type(oa)}, 长度: {len(oa) if isinstance(oa, list) else 'N/A'}")
        if isinstance(oa, list) and oa:
            print(f"第一个元素类型: {type(oa[0])}")
            if isinstance(oa[0], dict):
                print(f"第一个元素 keys: {list(oa[0].keys())}")
except Exception as exc:
    print(f"\n!!! 异常: {type(exc).__name__}: {exc}")
    traceback.print_exc()
