"""调试：只跑 1 题，打印 adjudicator 的 raw 输出。"""
import sys
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parents[1]
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

from env_setup import _load_env
_load_env()

from pipeline.evidence_pool import get_match_runtime
from pipeline.match_pipeline import build_known_answer_adjudicator_prompt, _call_planner
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
print(f"题干: {q.stem[:60]}")

print("\n加载 runtime...")
rt = get_match_runtime()
client = rt.base.client

print("\n跑 planner...")
raw_plan, search_plan = _call_planner(client, q.stem, q.options)
plans = agentic.option_plan_by_label(search_plan)

print("\n跑检索...")
candidates_by_option = {}
for label, option_text in q.options.items():
    option_plan = plans.get(label, {})
    if not option_plan.get("search_queries"):
        option_plan = {
            "search_queries": [f"{q.stem} {option_text}", option_text],
            "must_terms": agentic.extract_phrases(q.stem, option_text)[:6],
            "evidence_need": f"判断选项{label}是否符合题干",
            "option_claim": option_text,
            "related_terms": [],
            "contrast_terms": [],
            "avoid_confusions": [],
        }
    candidates, _ = agentic.retrieve_for_option(rt, q.stem, option_text, option_plan, top_k=20)
    candidates_by_option[label] = candidates
    print(f"  选项{label}: {len(candidates)} 候选")

print("\n跑 adjudicator...")
prompt = build_known_answer_adjudicator_prompt(q.stem, q.options, q.answer, search_plan, candidates_by_option)
print(f"prompt 长度: {len(prompt)} 字符")
raw_adj = run_step1.call_llm(client, prompt, max_tokens=9000)
print(f"\n=== RAW ADJUDICATOR OUTPUT (前2000字) ===")
print(raw_adj[:2000])
print(f"\n=== 长度: {len(raw_adj)} ===")
print(f"\n=== 类型: {type(raw_adj)} ===")

# 测试解析
from pipeline.match_pipeline import _parse_llm_json
parsed = _parse_llm_json(raw_adj)
print(f"\n=== PARSED ===")
print(f"类型: {type(parsed)}")
if isinstance(parsed, dict):
    print(f"keys: {list(parsed.keys())}")
    oa = parsed.get("option_analysis", [])
    print(f"option_analysis 类型: {type(oa)}, 长度: {len(oa) if isinstance(oa, list) else 'N/A'}")
    if isinstance(oa, list) and oa:
        print(f"第一个元素类型: {type(oa[0])}")
        if isinstance(oa[0], dict):
            print(f"第一个元素 keys: {list(oa[0].keys())}")
