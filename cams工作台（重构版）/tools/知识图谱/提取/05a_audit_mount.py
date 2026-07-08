"""
Step 5A：LLM 审核句卡挂载候选。

只审核 BGE 低置信度挂载（0.5-0.7 分），高置信度（citation 匹配或 ≥0.7）自动放行。

输入：card_mounts.jsonl + cards_v6_sentence.json + nodes_accepted.jsonl
输出：card_mounts_audited.jsonl（每节点，含每张卡的 accept/review 标记）
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from openai import OpenAI

_WORK = Path(__file__).resolve().parent / "work"
_WORKSPACE = Path(__file__).resolve().parents[3]
_CARDS_PATH = _WORKSPACE / "data" / "cards" / "cards_v6_sentence.json"
_DS_API_KEY = "sk-795628e9d4584fc59545d7abac9d1209"
_MIMO_API_KEY = "tp-cl5nzlniz5bfyk9i3wsdw88d25haf8ghdh6nccojrw1hqgc4"

_TEMPERATURE = 0.0

# 高置信度阈值：≥此值自动 accept，不调 LLM
_AUTO_ACCEPT_SCORE = 0.7
# LLM 每批处理的卡片数
_BATCH_SIZE = 20

PROMPT = """你是CAMS反洗钱教材知识图谱审核员。审核句卡与知识节点的挂载关系。

每张句卡已通过BGE向量相似度预匹配到当前知识节点。你的任务：判断每张卡是否确实属于该节点所代表的知识点。

判断标准：
- accept: 句卡内容与节点定义直接相关，句卡讨论的就是这个知识点
- review: 句卡与节点主题相近但不直接相关，或句卡内容太泛

输出格式：
{{"decisions": [{{"card_id": "v6s_N00001", "decision": "accept/review", "reason": ""}}]}}

## 当前节点
标题：{title}
定义：{definition}
类型：{node_type}

## 候选句卡"""


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_json_response(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        return {"decisions": []}


def main(chapter: int | None = None) -> int:
    cards_data = read_json(_CARDS_PATH)
    all_cards = {c["card_id"]: c for c in cards_data.get("cards", [])}

    # 加载节点
    node_map: dict[str, dict] = {}
    for ch in [2, 3, 4, 5]:
        if chapter and ch != chapter:
            continue
        for n in read_jsonl(_WORK / f"ch{ch}" / "nodes_accepted.jsonl"):
            node_map[n["node_id"]] = n

    chapters = [chapter] if chapter else [2, 3, 4, 5]
    total_accept = 0
    total_review = 0
    total_skip = 0

    for ch in chapters:
        mounts_path = _WORK / f"ch{ch}" / "card_mounts.jsonl"
        if not mounts_path.exists():
            print(f"跳过 ch{ch}: 无 card_mounts.jsonl")
            continue

        mounts = read_jsonl(mounts_path)
        out_path = _WORK / f"ch{ch}" / "card_mounts_audited.jsonl"

        print(f"\n===== 第{ch}章: {len(mounts)} 个节点有挂载 =====")

        with out_path.open("w", encoding="utf-8") as out_f:
            for m in mounts:
                nid = m["node_id"]
                node = node_map.get(nid)
                if not node:
                    continue

                all_node_cards = m["cards"]
                # 分类：高置信度自动过，低的送 LLM
                auto_pass = [c for c in all_node_cards
                             if c["method"] == "citation" or c["score"] >= _AUTO_ACCEPT_SCORE]
                need_audit = [c for c in all_node_cards
                              if c["method"] != "citation" and c["score"] < _AUTO_ACCEPT_SCORE]

                decisions: dict[str, str] = {}
                for c in auto_pass:
                    decisions[c["card_id"]] = "accept"

                # LLM 审核低置信度
                if need_audit:
                    node_title = node.get("title", "")
                    node_def = node.get("definition", "")
                    node_type = node.get("node_type", "")
                    prompt = PROMPT.replace("{title}", node_title).replace("{definition}", node_def).replace("{node_type}", node_type)

                    # 分批
                    for batch_start in range(0, len(need_audit), _BATCH_SIZE):
                        batch_cards = need_audit[batch_start:batch_start + _BATCH_SIZE]
                        batch_text = "\n".join(
                            f'[{c["card_id"]}] score={c["score"]:.3f}  '
                            f'{all_cards.get(c["card_id"],{}).get("knowledge","")[:120]}'
                            for c in batch_cards
                        )

                        for attempt in range(2):
                            try:
                                client = OpenAI(api_key=_DS_API_KEY, base_url="https://api.deepseek.com/v1")
                                resp = client.chat.completions.create(
                                    model="deepseek-chat",
                                    messages=[
                                        {"role": "system", "content": "你只输出合法 JSON 对象。"},
                                        {"role": "user", "content": prompt + "\n\n" + batch_text},
                                    ],
                                    temperature=_TEMPERATURE,
                                )
                                raw = parse_json_response(resp.choices[0].message.content or "{}")
                                for d in raw.get("decisions", []):
                                    cid = d.get("card_id", "")
                                    dec = d.get("decision", "accept")
                                    if cid and dec in ("accept", "review"):
                                        decisions[cid] = dec
                                break
                            except Exception:
                                if attempt < 1:
                                    time.sleep(1)

                    # 未决的默认 accept
                    for c in need_audit:
                        if c["card_id"] not in decisions:
                            decisions[c["card_id"]] = "accept"

                # 统计
                accept_n = sum(1 for v in decisions.values() if v == "accept")
                review_n = sum(1 for v in decisions.values() if v == "review")

                # 写入
                out_card_list = []
                for c in all_node_cards:
                    dec = decisions.get(c["card_id"], "accept")
                    out_card_list.append({**c, "decision": dec})

                out_f.write(json.dumps({"node_id": nid, "cards": out_card_list}, ensure_ascii=False) + "\n")

                total_accept += accept_n
                total_review += review_n
                total_skip += len(auto_pass)

        print(f"  -> {out_path} accept={total_accept} review={total_review} auto={total_skip}")

    print(f"\n总计: accept={total_accept}, review={total_review}, auto_accept={total_skip}")
    return 0


if __name__ == "__main__":
    import sys
    ch = None
    for a in sys.argv[1:]:
        try: ch = int(a)
        except ValueError: pass
    print("挂载审核: DS")
    raise SystemExit(main(chapter=ch))
