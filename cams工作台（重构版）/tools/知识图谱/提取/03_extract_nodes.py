"""
Step 3：LLM 读每节原文 + summary，自主发现显式节点候选。

对标高代 03_extract_explicit_nodes.py。每节独立处理，不强制每个 H3 都是节点。
LLM 自主判断：本节有哪些知识点？每个带 evidence_span + type + definition。

输入：leaf_sections.jsonl + section_summaries.jsonl
输出：nodes_raw.jsonl（节点候选）+ node_extraction_warnings.jsonl
"""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

_WORK = Path(__file__).resolve().parent / "work"
_DS_API_KEY = "sk-795628e9d4584fc59545d7abac9d1209"

_MODEL = "deepseek-chat"
_BASE_URL = "https://api.deepseek.com/v1"
_TEMPERATURE = 0.0
_MAX_TOKENS = 2048
_MIMO_API_KEY = "tp-cl5nzlniz5bfyk9i3wsdw88d25haf8ghdh6nccojrw1hqgc4"
_DS_API_KEY = "sk-795628e9d4584fc59545d7abac9d1209"

# CAMS 节点类型（对标数学 KG 的 Concept/Method/Theorem 等）
VALID_NODE_TYPES = {"KnowledgePoint", "Regulation", "RiskIndicator", "CaseStudy", "Institution"}

PROMPT = """你是CAMS反洗钱教材知识图谱构建助手。你的任务是基于当前小节原文生成"显式节点候选"。

只输出 JSON 对象，不输出 Markdown 或解释性文字。

## 总原则

- 只能依据当前小节原文，不使用外部知识。
- Step 2 的 summary 只作主题导航，不是证据来源，也不是候选清单。
- 当前步骤只抽取节点候选，不抽关系边。
- evidence_span 必须是当前小节原文中的连续片段。
- 空数组是正确答案。如果本节没有独立的知识点，输出 {"nodes": []}。

## 节点类型

只能使用以下 5 类：

- KnowledgePoint：一般反洗钱知识点。包括洗钱概念、方法、阶段、风险类型、合规流程等。
- Regulation：法规、指令、法律、监管要求。如"欧盟第4号指令""美国爱国者法案第312条"。
- RiskIndicator：洗钱/恐怖融资的危险信号或红旗标志。如"异常现金交易""拆分交易"。
- CaseStudy：教材中的案例。当 source_scope="case" 时使用。概括该案例说明了什么反洗钱知识。
- Institution：机构、组织、工作组。如"金融行动特别工作组""巴塞尔委员会""埃格蒙特集团"。

## 小节类型规则

### content 节

可以抽取 KnowledgePoint、Regulation、RiskIndicator、Institution。

优先识别：
- 明确定义的概念或知识：生成 KnowledgePoint
- 被点名的法规/标准：生成 Regulation
- 被列出的风险信号：生成 RiskIndicator
- 被介绍的机构：生成 Institution

### case 节（source_scope="case"）

生成 CaseStudy 节点。标题应为案例对应的核心知识点，definition 应概括该案例说明了什么。evidence_span 应取案例中的关键事实句。

CaseStudy 节点不要与同节内 content 节点的 title 重复。

## 输出格式

{
  "nodes": [
    {
      "title": "洗钱的定义",
      "node_type": "KnowledgePoint",
      "definition": "洗钱是指对犯罪所得进行处理并掩饰其非法来源的过程",
      "evidence_span": "洗钱是指对犯罪所得进行处理并掩饰其非法来源，以期将犯罪所得用于合法或非法活动。"
    }
  ]
}

## 字段要求

- title：15字以内的知识点名称，能被教研检索和理解。不能是编号。
- definition：一句概括，≤40字，忠实于原文。
- evidence_span：当前小节原文中支持该节点的连续片段，必须逐字复制。
- node_type：只使用上述5种之一。

## 当前输入"""


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


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
        raise RuntimeError(f"无效 JSON: {text[:300]}")


def build_payload(section: dict, summary: dict) -> dict:
    return {
        "section_metadata": {
            "section_node_id": section["section_node_id"],
            "chapter": section.get("chapter", ""),
            "section": section.get("section", ""),
            "subsection": section.get("subsection", ""),
            "source_scope": section.get("source_scope", ""),
        },
        "section_text": section.get("text", ""),
        "section_summary": {
            "summary": summary.get("summary", ""),
        },
        "allowed_node_types": sorted(VALID_NODE_TYPES),
    }


def _try_llm(client: OpenAI, model: str, payload: str) -> dict:
    """单次 LLM 调用，返回 parsed JSON 或抛出异常"""
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你只输出合法 JSON 对象。"},
            {"role": "user", "content": PROMPT + "\n\n" + payload},
        ],
        temperature=_TEMPERATURE,
    )
    content = resp.choices[0].message.content or ""
    if not content.strip():
        raise ValueError("empty_response")
    return parse_json_response(content)


def call_llm_composite(section: dict, summary: dict) -> tuple[dict, str]:
    """优先 GLM，被过滤则降级 DS。返回 (result, used_model)"""
    payload = json.dumps(build_payload(section, summary), ensure_ascii=False)

    # 模型链：GLM → DS
    chain = [
        ("mimo-v2.5", "https://token-plan-cn.xiaomimimo.com/v1", _MIMO_API_KEY),
        ("deepseek-chat", "https://api.deepseek.com/v1", _DS_API_KEY),
    ]

    for model, base_url, api_key in chain:
        client = OpenAI(api_key=api_key, base_url=base_url)
        retries = 1 if "mimo" in model.lower() else 2  # GLM 只试 1 次
        for attempt in range(retries):
            try:
                result = _try_llm(client, model, payload)
                if model == "mimo-v2.5":
                    print(f"    MiMo 命中")
                return result, model
            except Exception:
                if attempt < retries - 1:
                    time.sleep(0.5)
        if model == "mimo-v2.5":
            print(f"    MiMo 过滤，降级 DS")

    return {"nodes": []}, "all_failed"


def validate_node(node: dict, section_text: str, section_node_id: str) -> list[str]:
    """本地硬校验，对标数学 KG 的 validate_node"""
    warnings: list[str] = []

    title = (node.get("title") or "").strip()
    if not title:
        warnings.append("empty_title")
    if len(title) > 40:
        warnings.append("title_too_long")

    ntype = node.get("node_type", "")
    if ntype not in VALID_NODE_TYPES:
        warnings.append(f"invalid_node_type:{ntype}")

    evidence = (node.get("evidence_span") or "").strip()
    if not evidence:
        warnings.append("empty_evidence_span")
    elif len(evidence) < 8:
        warnings.append("evidence_too_short")
    else:
        # 模糊匹配：去掉空白后核心 15 字在原文中
        clean_ev = re.sub(r"\s+", "", evidence)
        clean_text = re.sub(r"\s+", "", section_text)
        if len(clean_ev) >= 15 and clean_ev[:15] not in clean_text:
            warnings.append("evidence_not_found_in_text")

    definition = (node.get("definition") or "").strip()
    if not definition:
        warnings.append("empty_definition")

    return warnings


def normalize_node(raw: dict, section: dict, node_index: int, model_name: str) -> dict:
    sid = section["section_node_id"]
    return {
        "node_id": f"{sid}:N{node_index:03d}",
        "section_node_id": sid,
        "chapter": section.get("chapter", ""),
        "section": section.get("section", ""),
        "subsection": section.get("subsection", ""),
        "source_scope": section.get("source_scope", ""),
        "title": (raw.get("title") or "").strip(),
        "node_type": raw.get("node_type", "KnowledgePoint"),
        "definition": (raw.get("definition") or "").strip(),
        "evidence_span": (raw.get("evidence_span") or "").strip(),
        "model": model_name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def main(
    chapter: int | None = None,
    limit: int = 0,
    mock: bool = False,
    keep_rejected: bool = False,
    append: bool = False,
    workers: int = 4,
) -> int:
    chapters = [chapter] if chapter else [2, 3, 4, 5]
    total_nodes = 0
    total_accepted = 0
    total_rejected = 0
    model_stats: dict[str, int] = {}

    for ch in chapters:
        leaf_path = _WORK / f"ch{ch}" / "leaf_sections.jsonl"
        sum_path = _WORK / f"ch{ch}" / "section_summaries.jsonl"
        if not leaf_path.exists() or not sum_path.exists():
            print(f"跳过 ch{ch}")
            continue

        sections = read_jsonl(leaf_path)
        summaries = {s["section_node_id"]: s for s in read_jsonl(sum_path)}
        if limit > 0:
            sections = sections[:limit]

        out_path = _WORK / f"ch{ch}" / "nodes_raw.jsonl"
        warn_path = _WORK / f"ch{ch}" / "node_extraction_warnings.jsonl"
        rej_path = _WORK / f"ch{ch}" / "nodes_rejected.jsonl"

        # 续跑：跳过已处理的节
        done_sids: set[str] = set()
        if append and out_path.exists():
            with out_path.open("r", encoding="utf-8") as f:
                for line in f:
                    d = json.loads(line)
                    done_sids.add(d.get("section_node_id", ""))
            print(f"续跑模式: {len(done_sids)} 节已完成，跳过")

        print(f"\n===== 第{ch}章: {len(sections)} 节 =====")
        fmode = "a" if append else "w"

        write_lock = threading.Lock()

        def _process_section(sec: dict, sm: dict) -> tuple[list[dict], list[dict], list[dict], str]:
            """处理单节 → (accepted_nodes, rejected_nodes, warnings, model)"""
            if mock:
                raw = {"nodes": [{"title": sec.get("subsection", ""), "node_type": "KnowledgePoint",
                       "definition": sm.get("summary", "")[:40], "evidence_span": sec.get("text", "")[:80]}]}
                mode = "mock"
            else:
                raw, mode = call_llm_composite(sec, sm)

            nodes = raw.get("nodes") if isinstance(raw.get("nodes"), list) else []
            txt = sec.get("text", "")
            accepted: list[dict] = []
            rejected: list[dict] = []
            warns: list[dict] = []

            for idx, n in enumerate(nodes):
                node = normalize_node(n, sec, idx, mode)
                w = validate_node(n, txt, sec["section_node_id"])
                if w:
                    rejected.append(node)
                    warns.append({"section_node_id": sec["section_node_id"],
                                  "node_id": node["node_id"], "title": node["title"], "warnings": w})
                else:
                    accepted.append(node)
            return accepted, rejected, warns, mode

        pending = [s for s in sections if s["section_node_id"] not in done_sids]
        print(f"\n===== 第{ch}章: {len(sections)} 节, 待处理 {len(pending)}, workers={workers} =====")

        with out_path.open(fmode, encoding="utf-8") as out_f, \
             warn_path.open(fmode, encoding="utf-8") as warn_f, \
             rej_path.open(fmode, encoding="utf-8") as rej_f:

            if workers <= 1 or mock:
                for sec in pending:
                    sid = sec["section_node_id"]
                    acc, rej, warns, mode = _process_section(sec, summaries.get(sid, {}))
                    with write_lock:
                        for n in acc: out_f.write(json.dumps(n, ensure_ascii=False) + "\n")
                        for w in warns: warn_f.write(json.dumps(w, ensure_ascii=False) + "\n")
                        if keep_rejected:
                            for n in rej: rej_f.write(json.dumps(n, ensure_ascii=False) + "\n")
                    total_accepted += len(acc); total_rejected += len(rej)
                    total_nodes += len(acc) + len(rej)
                    model_stats[mode] = model_stats.get(mode, 0) + 1
                    print(f"  [{sid}] {mode} nodes={len(acc)+len(rej)} accepted={len(acc)}")
            else:
                t0 = time.time()
                with ThreadPoolExecutor(max_workers=workers) as ex:
                    futures = {ex.submit(_process_section, sec, summaries.get(sec["section_node_id"], {})): sec for sec in pending}
                    for i, future in enumerate(as_completed(futures)):
                        acc, rej, warns, mode = future.result()
                        with write_lock:
                            for n in acc: out_f.write(json.dumps(n, ensure_ascii=False) + "\n")
                            for w in warns: warn_f.write(json.dumps(w, ensure_ascii=False) + "\n")
                            if keep_rejected:
                                for n in rej: rej_f.write(json.dumps(n, ensure_ascii=False) + "\n")
                            out_f.flush()
                        total_accepted += len(acc); total_rejected += len(rej)
                        total_nodes += len(acc) + len(rej)
                        model_stats[mode] = model_stats.get(mode, 0) + 1
                        if (i + 1) % 10 == 0:
                            print(f"  {i+1}/{len(pending)} acc={total_accepted} rej={total_rejected} ({time.time()-t0:.0f}s)")

    print(f"\n总计: 候选={total_nodes}, 通过={total_accepted}, 驳回={total_rejected}")
    print(f"模型分布: {model_stats}")
    return 0


if __name__ == "__main__":
    import sys
    ch = None; limit = 0; mock = False; keep_rejected = False; append = False; workers = 4
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--mock": mock = True
        elif a == "--keep-rejected": keep_rejected = True
        elif a == "--append": append = True
        elif a.startswith("--workers="): workers = int(a.split("=", 1)[1])
        elif a.startswith("--limit="): limit = int(a.split("=", 1)[1])
        else:
            try: ch = int(a)
            except ValueError: pass
        i += 1
    print(f"提取策略: MiMo优先 → DS降级  workers={workers}")
    raise SystemExit(main(chapter=ch, limit=limit, mock=mock, keep_rejected=keep_rejected, append=append, workers=workers))
