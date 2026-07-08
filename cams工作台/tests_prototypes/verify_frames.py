"""
步骤6-8验证：误解类型→证据方向→检索→推理桥梁→学生回答
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from hybrid_retriever import (
    load_cards, BM25Retriever, EmbeddingRetriever,
    rrf_fuse, build_card_text,
)
from openai import OpenAI

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ── 1. 加载数据 ──────────────────────────────────────────────────
def load_frames():
    with open(os.path.join(DATA_DIR, "claim_evidence_frames.json"), "r", encoding="utf-8") as f:
        return json.load(f)

# ── 2. 步骤6：验证映射召回 ──────────────────────────────────────
def verify_retrieval(cards, frames):
    """用 evidence_directions 锚点检索，检查目标卡片是否在结果中"""
    bm25 = BM25Retriever(cards)
    emb = EmbeddingRetriever(cards)

    anchors = frames["frame_alignment"]["retrieval_verification_anchors"]
    target_ids = {ef["card_id"] for ef in frames["target_evidence_frames"]}

    print(f"验证检索: {len(anchors)} 个锚点, {len(target_ids)} 张目标卡片")
    print(f"目标卡片: {target_ids}")

    all_lists = []
    for q in anchors:
        all_lists.append(bm25.search(q, top_k=15))
        all_lists.append(emb.search(q, top_k=15))

    final = rrf_fuse(all_lists)

    # 找每张目标卡片的最佳排名
    all_ranked_ids = [idx for idx, _ in final]
    print(f"\n总命中卡片数: {len(all_ranked_ids)}")

    found = {}
    for tid in target_ids:
        target_idx = None
        for i, c in enumerate(cards):
            if c["card_id"] == tid:
                target_idx = i
                break
        if target_idx is None:
            found[tid] = {"rank": None, "status": "card not in dataset"}
            continue
        if target_idx in all_ranked_ids:
            rank = all_ranked_ids.index(target_idx) + 1
            found[tid] = {"rank": rank, "status": "FOUND"}
        else:
            found[tid] = {"rank": None, "status": "NOT IN RESULTS"}

    print("\n--- 目标卡片召回 ---")
    all_found = True
    for tid, info in found.items():
        card = cards[[c["card_id"] for c in cards].index(tid)]
        status_icon = "[OK]" if info["status"] == "FOUND" else "[MISS]"
        rank_str = f"#{info['rank']}" if info['rank'] else "未召回"
        print(f"  {status_icon} {tid}: {rank_str} | {card['knowledge'][:60]}...")
        if info["status"] != "FOUND":
            all_found = False

    recall = sum(1 for info in found.values() if info["status"] == "FOUND")
    print(f"\n召回: {recall}/{len(target_ids)}")

    # Top-15 展示
    print(f"\n--- RRF Top-10 ---")
    for i, (idx, score) in enumerate(final[:10]):
        card = cards[idx]
        marker = ">>" if card["card_id"] in target_ids else "  "
        print(f"  [{i+1}] {marker} {card['card_id']} | {card['knowledge'][:70]}")
        if i < 10:
            pass

    return found, all_found, final, len(target_ids)


# ── 3. 步骤7：LLM 写推理桥梁 ────────────────────────────────────
BRIDGE_PROMPT = """你是CAMS反洗钱教研专家。下面是关于一道CAMS考题的材料。

## 题目
{question_text}

## D选项 Claim Frame
- 选项：{option_label}
- 声称：{claim_text}
- 主体：{claim_subject}
- 对象：{claim_object}
- 方向：{claim_direction}
- 误解类型：{misconception_type}

## 教材证据 (Evidence Frames)
{evidence_frames_text}

## 任务
基于以上证据，写一段推理桥梁。要求：
1. 先直接回应"为什么不选D"
2. 引用证据，用 [card_id] 标注来源
3. 解释清楚"主体不一致"和"方向不一致"
4. 解释学生可能误解在哪里
5. 不超过200字
6. 不要用"综上所述"、"核心在于"等AI套话
7. 直接输出推理文本，不用JSON包裹"""


def build_evidence_frames_text(frames):
    lines = []
    for ef in frames["target_evidence_frames"]:
        f = ef["frame"]
        lines.append(
            f"[{ef['card_id']}] "
            f"主体={f['subject']}, 对象={f['object']}, 方向={f['direction']}, "
            f"机制={f['mechanism']}, 类型={f['evidence_type']}\n"
            f"  教材原文: {ef['citation']}"
        )
    return "\n\n".join(lines)


def write_reasoning_bridge(frames):
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    cf = frames["claim_frame"]
    mm = frames["misconception_mapping"]
    ev_text = build_evidence_frames_text(frames)

    question_text = """题干：(多选题)洗钱会对金融机构FI造成哪些后果?(选择两个。)
选项：
A. 盈利业务的减少或损失
B. 代理银行设施的增加
C. 雇员人数减少
D. 公司税的增加
E. 调查费用和罚金的增加
正确答案：A,E"""

    prompt = BRIDGE_PROMPT.format(
        question_text=question_text,
        option_label="D",
        claim_text=cf["claim_text"],
        claim_subject=cf["subject"],
        claim_object=cf["object"],
        claim_direction=cf["direction"],
        misconception_type=mm["misconception_type"],
        evidence_frames_text=ev_text,
    )

    print("\n调用 DeepSeek v4-pro 写推理桥梁...")
    resp = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content": "你是CAMS反洗钱教研专家。输出简洁精准，不用套话。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=800,
    )
    return resp.choices[0].message.content.strip()


# ── 4. 步骤8：生成学生可读回答 ──────────────────────────────────
STUDENT_ANSWER_PROMPT = """你是CAMS助教。学生在刷题时问了下面这个问题。

## 题目
{question_text}

## 推理桥梁（教研已确认）
{reasoning_bridge}

## 任务
基于推理桥梁，生成一段学生可读的回答。要求：
1. 先直接回应学生的具体问题
2. 用学生能懂的语言解释
3. 保留证据引用 [card_id]
4. 控制在250字以内
5. 给出下次判断的简单方法
6. 不要用"综上所述"、"至关重要"等套话
直接输出回答文本"""  # noqa


def write_student_answer(frames, reasoning_bridge, student_question):
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    question_text = """题干：(多选题)洗钱会对金融机构FI造成哪些后果?(选择两个。)
选项：A.盈利业务的减少或损失 B.代理银行设施的增加 C.雇员人数减少 D.公司税的增加 E.调查费用和罚金的增加
正确答案：A,E"""

    prompt = STUDENT_ANSWER_PROMPT.format(
        question_text=question_text,
        reasoning_bridge=reasoning_bridge,
    )

    user_msg = f"学生问：{student_question}"

    print("调用 DeepSeek v4-pro 生成学生回答...")
    resp = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content": "你是CAMS助教，用简洁清晰的中文回答学生问题。"},
            {"role": "user", "content": prompt},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=600,
    )
    return resp.choices[0].message.content.strip()


# ── 5. 主流程 ────────────────────────────────────────────────────
def main():
    frames = load_frames()

    cards = load_cards(min_citation_len=0)

    # ── 步骤6：验证检索 ──
    print("=" * 60)
    print("步骤6: 验证误解映射 → 证据方向 → 检索召回")
    print("=" * 60)
    found, all_found, all_results, n_targets = verify_retrieval(cards, frames)

    critical_ids = {'v6_b03_N18', 'v6_b33_N23', 'v6_b33_N25', 'v6_b33_N38'}
    recall_count = sum(1 for info in found.values() if info["status"] == "FOUND")
    if not all_found:
        print(f"\n[WARN] {n_targets - recall_count}/{n_targets} 目标卡片未召回。")
        critical_found = all(found.get(tid, {}).get('status') == 'FOUND' for tid in critical_ids)
        if not critical_found:
            print("[FAIL] 核心证据卡片缺失，停止后续步骤。")
            output = {"step6_result": {tid: info for tid, info in found.items()}}
            with open(os.path.join(DATA_DIR, "verification_result.json"), "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            return
        print("[OK] 核心证据卡全部召回，继续后续步骤。")

    print(f"\n[PASS] 核心证据卡 {len(critical_ids)}/{len(critical_ids)} 召回成功。")

    # ── 步骤7：推理桥梁 ──
    print(f"\n{'='*60}")
    print("步骤7: LLM 基于 claim frame + evidence frame 写推理桥梁")
    print("=" * 60)
    bridge = write_reasoning_bridge(frames)
    print(f"\n--- 推理桥梁 ---\n{bridge}")

    # ── 步骤8：学生回答 ──
    print(f"\n{'='*60}")
    print("步骤8: LLM 生成学生可读回答")
    print("=" * 60)
    student_q = "将钱合法化的过程中不会交税吗？比如虚假交易的情境下，一方虚假地出售了产品或服务，给开了个假发票"
    answer = write_student_answer(frames, bridge, student_q)
    print(f"\n--- 学生回答 ---\n{answer}")

    # 保存全部结果
    output = {
        "step6_verification": {tid: info for tid, info in found.items()},
        "step7_reasoning_bridge": bridge,
        "step8_student_answer": answer,
    }
    with open(os.path.join(DATA_DIR, "verification_result.json"), "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n完整结果: data/verification_result.json")


if __name__ == "__main__":
    main()
