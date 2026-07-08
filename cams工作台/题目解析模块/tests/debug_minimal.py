"""最小测试：只测 adjudicator 调用和解析，不跑 planner。"""
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
import run_agentic_search_experiment as agentic

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

# 用简单 plan，不调 planner
print("构建简单 plan...")
search_plan = {
    "stem": q.stem,
    "options": q.options,
    "option_plans": {
        label: {
            "search_queries": [f"{q.stem} {text}", text],
            "must_terms": agentic.extract_phrases(q.stem, text)[:6],
            "evidence_need": f"判断选项{label}",
            "option_claim": text,
            "related_terms": [],
            "contrast_terms": [],
            "avoid_confusions": [],
        }
        for label, text in q.options.items()
    },
}

print("跑检索...")
plans = agentic.option_plan_by_label(search_plan)
candidates_by_option = {}
for label, option_text in q.options.items():
    candidates, _ = agentic.retrieve_for_option(rt, q.stem, option_text, plans[label], top_k=20)
    candidates_by_option[label] = candidates
    print(f"  选项{label}: {len(candidates)} 候选")

print("构建 adjudicator prompt...")
prompt = build_known_answer_adjudicator_prompt(q.stem, q.options, q.answer, search_plan, candidates_by_option)
print(f"prompt 长度: {len(prompt)}")

print("调用 LLM...")
try:
    raw_adj = run_step1.call_llm(client, prompt, max_tokens=9000)
    print(f"raw_adj 类型: {type(raw_adj)}, 长度: {len(raw_adj)}")
    print(f"raw_adj 前500字:\n{raw_adj[:500]}")
    print("---")

    print("解析 JSON...")
    parsed = _parse_llm_json(raw_adj)
    print(f"parsed 类型: {type(parsed)}")
    if isinstance(parsed, dict):
        print(f"keys: {list(parsed.keys())}")
        oa = parsed.get("option_analysis")
        print(f"option_analysis 类型: {type(oa)}")
        if isinstance(oa, list) and oa:
            print(f"第一个元素类型: {type(oa[0])}")
except Exception as exc:
    print(f"\n!!! 异常: {type(exc).__name__}: {exc}")
    traceback.print_exc()
