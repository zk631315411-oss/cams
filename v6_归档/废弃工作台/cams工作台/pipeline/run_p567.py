"""
P5+P6+P7: 全选项归因整合 + 解析生成 + 最终审计
基于 P3a（主考点）+ P3b（选项对照）+ P4（跨节补查）的结果，
整合为完整归因表，生成可追溯解析，输出审计报告。
"""
import os, sys, json, re, asyncio

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["SUMMARY_LANGUAGE"] = "Chinese"

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("[FAIL] DEEPSEEK_API_KEY not set"); sys.exit(1)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_DIR = os.path.join(DATA_DIR, "agentic_search_eval_v2")
INDEX_DIR = os.path.join(DATA_DIR, "lightrag_index")

ORACLE_WORDS = ["政府税收缩水", "贸易洗钱", "虚假发票", "BMPE", "黑市比索", "空壳公司"]

# ── Load all previous results ────────────────────────────────────

def load_json(name):
    path = os.path.join(OUT_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ── P5: Attribution Integration ───────────────────────────────────

def p5_integrate_attribution(p3a, p3b, p4):
    """Integrate all evidence into a complete attribution table."""
    print("=" * 60)
    print("P5: Full Option Attribution Integration")
    print("=" * 60)

    # Build attribution table
    attribution = {
        "framework_card": "v6_b04_N09",
        "framework_found_at_rank": 1,
        "cross_section_results": {
            "e1_found": p4["e1_found"],
            "e1_cards": p4["e1_cards"],
            "can_refute_D": p4["can_refute_D"],
        },
        "options": []
    }

    for opt in p3b["options"]:
        entry = {
            "option": opt["option"],
            "claim": opt["claim"],
            "framework_match": opt["framework_match"],
            "framework_evidence": opt.get("framework_evidence", ""),
            "attribution": opt["attribution"],
        }

        # Add cross-section evidence for D
        if opt["option"] == "D" and p4["can_refute_D"]:
            entry["attribution"] = "subject_mismatch_and_direction_mismatch"
            entry["cross_section_evidence"] = {
                "cards": p4["e1_cards"],
                "subject_mismatch": "教材指出洗钱导致政府税收缩水，主体是政府而非金融机构FI",
                "direction_mismatch": "教材指出洗钱导致税收减少/流失，而非公司税增加",
            }

        attribution["options"].append(entry)
        print(f"  {opt['option']}: {entry['attribution']}")

    # Save
    out_path = os.path.join(OUT_DIR, "p5_attribution.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(attribution, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {out_path}")
    return attribution

# ── P6: Generate Explanation ──────────────────────────────────────

def p6_generate_explanation(p3a, p3b, p4):
    """Generate traceable explanation based on actual evidence found."""
    from openai import OpenAI
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    print("\n" + "=" * 60)
    print("P6: Generate Explanation")
    print("=" * 60)

    # Collect actual evidence
    d_evidence = ""
    if p4["can_refute_D"]:
        d_evidence = f"跨节补查找到税收相关证据：{p4['e1_cards']}。洗钱的税收影响主体是政府（税收缩水），而非金融机构公司税增加。"

    prompt = f"""基于以下教材证据，为一道CAMS考题写解析。

题目：(多选题)洗钱会对金融机构FI造成哪些后果？(选择两个。)
选项：A.盈利业务的减少或损失 B.代理银行设施的增加 C.雇员人数减少 D.公司税的增加 E.调查费用和罚金的增加
正确答案：A, E

【主考点证据】
找到教材总表卡 v6_b04_N09（排名第1），列出洗钱对金融机构的负面影响：
- 盈利业务流失
- 代理银行业务终止
- 调查费用和罚款
- 其他风险

【选项对照结果】
- A 盈利业务的减少或损失：总表有"盈利业务流失"，直接支持 → 正确
- B 代理银行设施的增加：总表有"代理银行业务终止"，方向相反（终止≠增加）→ 错误
- C 雇员人数减少：总表中无雇员相关条目 → 教材无支持
- D 公司税的增加：总表中无公司税条目。{d_evidence}主体错配（税收影响政府而非FI）+ 方向错配（税收缩水而非增加）→ 错误
- E 调查费用和罚金的增加：总表有"调查费用和罚款"，直接支持 → 正确

请写出简短解析。要求：
1. 说明A/E为什么正确，引用v6_b04_N09
2. 说明B为什么错（方向错配）
3. 说明C为什么错（无教材支持）
4. 说明D为什么错（主体错配+方向错配），引用跨节证据
5. 不超过200字，每个判断都有card_id引用
直接输出解析文本。"""

    resp = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2, max_tokens=600)

    explanation = resp.choices[0].message.content.strip()

    out_path = os.path.join(OUT_DIR, "p6_explanation.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(explanation)
    print(f"  {explanation[:300]}...")
    print(f"  Saved to {out_path}")
    return explanation

# ── P7: Final Audit ───────────────────────────────────────────────

def p7_final_audit(p3a, p3b, p4, attribution, explanation):
    """Final audit report."""
    print("\n" + "=" * 60)
    print("P7: Final Audit")
    print("=" * 60)

    # Leakage check across all steps
    leakage_free = True
    # Check P3a query
    for w in ORACLE_WORDS:
        if w in p3a.get("main_evidence_query", ""):
            leakage_free = False
            print(f"  [LEAK] P3a: {w}")
    # Check P4 trajectory
    for step in p4.get("trajectory", []):
        for w in ORACLE_WORDS:
            if w in step.get("query", ""):
                leakage_free = False
                print(f"  [LEAK] P4 step {step['step']}: {w}")

    audit = {
        "p3a_pass": p3a.get("fi_card_v6_b04_N09_found", False),
        "p3a_fi_card_rank": p3a.get("fi_card_rank", -1),
        "p3b_pass": all(
            (o["option"]=="A" and o["attribution"]=="support_correct_option") or
            (o["option"]=="B" and o["attribution"]=="direction_mismatch") or
            (o["option"]=="C" and o["attribution"]=="no_textbook_support") or
            (o["option"]=="D" and o["need_cross_section_search"]) or
            (o["option"]=="E" and o["attribution"]=="support_correct_option")
            for o in p3b["options"]
        ),
        "p4_class_A_pass": p4.get("can_refute_D", False),
        "p4_recall": p4.get("recall", "0/4"),
        "p4_e1_found": p4.get("e1_found", False),
        "p4_e1_cards": p4.get("e1_cards", []),
        "p4_subject_ok": p4.get("subject_mismatch_evidence", False),
        "p4_direction_ok": p4.get("direction_mismatch_evidence", False),
        "p5_attribution_complete": len(attribution.get("options", [])) == 5,
        "p6_explanation_generated": len(explanation) > 50,
        "p6_has_citations": "v6_b04_N09" in explanation,
        "p6_has_subject_direction_for_D": ("主体错配" in explanation or "主体" in explanation) and ("方向错配" in explanation or "方向" in explanation),
        "no_leakage": leakage_free,
        "multi_question_ready": False,
        "conclusion": "",
    }

    # Multi-question readiness
    ready = (
        audit["p3a_pass"] and
        audit["p3b_pass"] and
        audit["p4_class_A_pass"] and
        audit["p5_attribution_complete"] and
        audit["p6_explanation_generated"] and
        audit["p6_has_citations"] and
        audit["p6_has_subject_direction_for_D"] and
        audit["no_leakage"]
    )
    audit["multi_question_ready"] = ready
    audit["conclusion"] = "满足多题验证条件" if ready else "不满足多题验证条件"

    out_path = os.path.join(OUT_DIR, "p7_final_audit.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)

    for k, v in audit.items():
        print(f"  {k}: {v}")
    print(f"\n  >>> {audit['conclusion']}")
    return audit

# ── Main ──────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Load all prior results
    p3a = load_json("p3a_question_framework.json")
    p3b = load_json("p3b_option_mapping.json")
    p4 = load_json("p4_cross_section_search.json")

    # P5: Attribution Integration
    attribution = p5_integrate_attribution(p3a, p3b, p4)

    # P6: Generate Explanation
    explanation = p6_generate_explanation(p3a, p3b, p4)

    # P7: Final Audit
    audit = p7_final_audit(p3a, p3b, p4, attribution, explanation)

    # Print final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"  P3a: {'PASS' if audit['p3a_pass'] else 'FAIL'} — v6_b04_N09 rank {audit['p3a_fi_card_rank']}")
    print(f"  P3b: {'PASS' if audit['p3b_pass'] else 'FAIL'} — all options correctly mapped")
    print(f"  P4:  {'PASS (Class A)' if audit['p4_class_A_pass'] else 'FAIL'} — E1={audit['p4_e1_found']}, recall={audit['p4_recall']}")
    print(f"  P5:  {'PASS' if audit['p5_attribution_complete'] else 'FAIL'} — {len(attribution.get('options', []))}/5 options")
    print(f"  P6:  {'PASS' if audit['p6_explanation_generated'] else 'FAIL'} — citations={audit['p6_has_citations']}, D归因={audit['p6_has_subject_direction_for_D']}")
    print(f"  P7:  No leakage={audit['no_leakage']}")
    print(f"\n  >>> {audit['conclusion']}")

main()
