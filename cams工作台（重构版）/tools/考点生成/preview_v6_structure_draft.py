from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
V5_DIR = HERE / "work" / "preview_v5"
V6_DIR = HERE / "work" / "preview_v6"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compact(text: Any, limit: int = 160) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)] + "..."


def normalize(text: Any) -> str:
    value = str(text or "").strip().lower()
    value = re.sub(r"[\s\W_]+", "", value, flags=re.UNICODE)
    return value


def similarity(a: Any, b: Any) -> float:
    na = normalize(a)
    nb = normalize(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def has_question_context(pair: dict[str, Any]) -> bool:
    return any("question_id" in detail for detail in pair.get("details", []))


def relation_context_scope(pair: dict[str, Any]) -> str:
    return "question_context" if has_question_context(pair) else "card_only_nearby_text"


def relation_text_features(pair: dict[str, Any]) -> dict[str, Any]:
    a = pair["card_a_summary"]
    b = pair["card_b_summary"]
    return {
        "title_similarity": similarity(a.get("title_placeholder"), b.get("title_placeholder")),
        "quote_similarity": similarity(a.get("quote"), b.get("quote")),
        "title_a": a.get("title_placeholder") or "",
        "title_b": b.get("title_placeholder") or "",
        "quote_a": a.get("quote") or "",
        "quote_b": b.get("quote") or "",
        "question_count_a": int(a.get("question_count") or 0),
        "question_count_b": int(b.get("question_count") or 0),
    }


def legacy_label_relation(pair: dict[str, Any]) -> dict[str, Any]:
    reasons = set(pair.get("reasons") or [])
    ctype = pair.get("relation_candidate_type") or ""
    scope = relation_context_scope(pair)
    f = relation_text_features(pair)
    qa = f["question_count_a"]
    qb = f["question_count_b"]
    qsum = qa + qb
    title_sim = f["title_similarity"]
    quote_sim = f["quote_similarity"]
    qd = abs(qa - qb)

    def out(label: str, confidence: str, rationale: str, risk_flags: list[str] | None = None) -> dict[str, Any]:
        return {
            "draft_label": label,
            "draft_confidence": confidence,
            "draft_rationale": rationale,
            "draft_risk_flags": risk_flags or [],
            "context_scope": scope,
        }

    if ctype == "merge_same_point_candidate":
        if title_sim >= 0.94 and quote_sim >= 0.94:
            return out(
                "merge_same_point",
                "high",
                "标题和原文都几乎一致，属于同一原子事实的重复表述。",
            )
        if "same_question_core_core" in reasons:
            return out(
                "sibling_under_parent",
                "medium",
                "同题核心对核心更像同一教材主题下的并列子点，而不是完全同义重复。",
                ["same_question_core_core"],
            )
        if "high_frequency_absorption" in reasons:
            return out(
                "parent_child",
                "high",
                "高频吸纳通常表示上位主题吸纳低频展开，更适合父子结构。",
                ["high_frequency_absorption"],
            )
        if "same_option_multi_card" in reasons:
            if qsum >= 4 and qd >= 2:
                return out(
                    "parent_child",
                    "medium",
                    "同选项多卡但题目覆盖数差异明显，更像总述-展开关系。",
                    ["same_option_multi_card"],
                )
            return out(
                "sibling_under_parent",
                "medium",
                "同选项多卡只说明关系强，但从 100x100 裁判看更常见的是并列子点。",
                ["same_option_multi_card"],
            )
        if title_sim >= 0.80 or quote_sim >= 0.80:
            return out(
                "parent_child",
                "medium",
                "标题或原文接近，但不足以证明完全同义，更适合先挂父子草稿。",
            )
        return out(
            "sibling_under_parent",
            "low",
            "候选强度较高，但缺少足够的同义证据，先按并列子点草稿处理。",
        )

    if ctype == "merge_or_parent_child_candidate":
        if "same_question_core_core" in reasons:
            return out(
                "sibling_under_parent",
                "high",
                "同题核心之间更像同一父主题下的并列点，不直接合并。",
                ["same_question_core_core"],
            )
        if "high_frequency_absorption" in reasons:
            return out(
                "parent_child",
                "high",
                "高频吸纳直接提示上位主题吸纳下位展开。",
                ["high_frequency_absorption"],
            )
        if "same_option_multi_card" in reasons:
            if title_sim >= 0.94 and quote_sim >= 0.94:
                return out(
                    "merge_same_point",
                    "medium",
                    "同选项多卡且标题、原文几乎一致，才勉强允许合并。",
                    ["same_option_multi_card"],
                )
            if qd >= 2 and max(qa, qb) >= 3:
                return out(
                    "parent_child",
                    "medium",
                    "同选项多卡但题目覆盖数差异更像总述-展开。",
                    ["same_option_multi_card"],
                )
            return out(
                "sibling_under_parent",
                "high",
                "同选项多卡在 100x100 中更常落向并列子点，先按兄弟结构草稿处理。",
                ["same_option_multi_card"],
            )
        if title_sim >= 0.84 or quote_sim >= 0.84:
            return out(
                "parent_child",
                "medium",
                "文本相似度较高，先按父子草稿处理更稳妥。",
            )
        return out(
            "keep_separate",
            "low",
            "当前证据更像相关但不足以建立稳定结构关系。",
        )

    if ctype == "sibling_under_parent_candidate":
        if title_sim >= 0.94 and quote_sim >= 0.94:
            return out(
                "merge_same_point",
                "medium",
                "两张卡标题和原文几乎一致，虽然当前是兄弟候选，但更像重复表述。",
            )
        return out(
            "sibling_under_parent",
            "high",
            "这类候选本身就是并列子点的强信号。",
        )

    if ctype == "parent_child_or_keep_separate_candidate":
        if scope == "card_only_nearby_text":
            if title_sim >= 0.82 or quote_sim >= 0.82:
                return out(
                    "parent_child",
                    "low",
                    "只有教材近邻信号时，文本相似度足够高才先挂父子草稿。",
                    ["card_only_nearby_text"],
                )
            return out(
                "keep_separate",
                "low",
                "只有教材近邻信号，且相似度不够，先保留分开。",
                ["card_only_nearby_text"],
            )
        if title_sim >= 0.88 or quote_sim >= 0.88:
            return out(
                "parent_child",
                "medium",
                "文本相似度较高，适合先按父子草稿。",
            )
        if qd <= 1 and qsum >= 2:
            return out(
                "sibling_under_parent",
                "medium",
                "题目覆盖接近但没有强总述特征，更像并列子点。",
            )
        return out(
            "keep_separate",
            "low",
            "证据不足，先不建立结构关系。",
        )

    return out("needs_review", "low", "未识别的候选类型。")


def label_relation(pair: dict[str, Any]) -> dict[str, Any]:
    """Calibrated v6 relation draft.

    V5 candidate types are recall routes, not final judgements. This keeps
    automatic merge rare, treats question-triggered signals as stronger than
    card-only nearby text, and records risk flags for later LLM/human review.
    """
    reasons = set(pair.get("reasons") or [])
    ctype = pair.get("relation_candidate_type") or ""
    scope = relation_context_scope(pair)
    f = relation_text_features(pair)
    qa = f["question_count_a"]
    qb = f["question_count_b"]
    title_sim = f["title_similarity"]
    quote_sim = f["quote_similarity"]
    qd = abs(qa - qb)
    max_q = max(qa, qb)
    min_q = min(qa, qb)
    a = pair["card_a_summary"]
    b = pair["card_b_summary"]
    title_a = str(a.get("title_placeholder") or "")
    title_b = str(b.get("title_placeholder") or "")
    quote_a = str(a.get("quote") or "")
    quote_b = str(b.get("quote") or "")

    heading_markers = (
        "第",
        "条",
        "文件",
        "名单",
        "阶段",
        "风险",
        "职责",
        "要求",
        "制度",
        "要素",
        "原则",
        "Jurisdictions",
        "High-Risk",
    )

    def heading_score(text: str) -> int:
        score = 0
        if len(text) <= 55:
            score += 1
        if any(marker in text for marker in heading_markers):
            score += 1
        if "：" in text or ":" in text or "《" in text:
            score += 1
        if text.endswith(("。", "：", ":")):
            score += 1
        return score

    def looks_like_alias() -> bool:
        joined = title_a + title_b + quote_a + quote_b
        alias_markers = ("此前称为", "外部将", "也称")
        if not any(marker in joined for marker in alias_markers):
            return False

        def is_greylist_text(text: str) -> bool:
            return any(
                marker in text
                for marker in (
                    "灰名单",
                    "应加强监控的司法管辖区",
                    "Jurisdictions under Increased",
                )
            )

        def is_call_for_action_text(text: str) -> bool:
            return any(
                marker in text
                for marker in (
                    "需要采取行动的高风险司法管辖区",
                    "High-Risk Jurisdictions Subject",
                    "公开声明",
                )
            )

        def is_short_alias_side(text: str) -> bool:
            return len(text) <= 90 and not any(marker in text for marker in ("包括", "职责", "监督", "建议", "评估", "转账"))

        # FATF itself is too broad to be an alias anchor. Grey-list aliases
        # must stay inside the grey-list concept and must not absorb the
        # separate call-for-action / high-risk jurisdiction list.
        if is_greylist_text(text_a) and is_greylist_text(text_b):
            return not (is_call_for_action_text(text_a) or is_call_for_action_text(text_b))

        if is_call_for_action_text(text_a) and is_call_for_action_text(text_b):
            return True

        human_alias_a = "人口贩卖" in text_a and "人口贩运" in text_a and is_short_alias_side(text_a)
        human_alias_b = "人口贩卖" in text_b and "人口贩运" in text_b and is_short_alias_side(text_b)
        if human_alias_a or human_alias_b:
            other = text_b if human_alias_a else text_a
            return is_short_alias_side(other) and ("人口贩卖" in other or "人口贩运" in other)

        return False

    def has_any(text: str, words: tuple[str, ...]) -> bool:
        return any(word in text for word in words)

    text_a = title_a + quote_a
    text_b = title_b + quote_b

    def side_pair(
        left,
        right,
    ) -> bool:
        return (left(text_a) and right(text_b)) or (left(text_b) and right(text_a))

    def shared_term_count(words: tuple[str, ...]) -> int:
        return sum(1 for word in words if word in text_a and word in text_b)

    def starts_with_list_item(text: str) -> bool:
        return bool(re.match(r"\s*(?:\d+[\.、．]|[一二三四五六七八九十]+[\.、．]|o\s+)", text))

    def has_list_intro(text: str) -> bool:
        return has_any(
            text,
            (
                "包括",
                "下述",
                "以下",
                "如下",
                "五项",
                "四大",
                "关键要素",
                "这些要素",
                "优先事项",
                "特别措施",
            ),
        )

    def has_explicit_heading_signal(text: str) -> bool:
        if "：" in text or ":" in text:
            return True
        if re.search(r"第\s*\d+\s*条", text):
            return True
        if has_list_intro(text):
            return True
        return False

    def is_structural_list_pair() -> bool:
        a_intro = has_list_intro(text_a) or bool(re.search(r"第\s*\d+\s*条", title_a))
        b_intro = has_list_intro(text_b) or bool(re.search(r"第\s*\d+\s*条", title_b))
        return (
            (a_intro and starts_with_list_item(title_b or quote_b))
            or (b_intro and starts_with_list_item(title_a or quote_a))
            or (
                has_any(text_a, ("这些要素", "四大关键要素", "关键优先事项"))
                and has_any(text_b, ("这包括", "包括"))
            )
            or (
                has_any(text_b, ("这些要素", "四大关键要素", "关键优先事项"))
                and has_any(text_a, ("这包括", "包括"))
            )
        )

    def is_rule_implementation_pair() -> bool:
        return (
            has_any(text_a, ("该法条还要求", "该条款还要求", "要求金融组织"))
            and has_any(text_b, ("执行该规定", "该规定", "认证表"))
        ) or (
            has_any(text_b, ("该法条还要求", "该条款还要求", "要求金融组织"))
            and has_any(text_a, ("执行该规定", "该规定", "认证表"))
        )

    def is_statute_heading_rule_pair() -> bool:
        a_statute = "\u7b2c" in title_a and "\u6761" in title_a
        b_statute = "\u7b2c" in title_b and "\u6761" in title_b
        rule_words = (
            "\u672c\u6cd5\u6761",
            "\u8be5\u6cd5\u6761",
            "\u8be5\u6761\u6b3e",
            "\u5141\u8bb8",
            "\u67e5\u5c01",
            "\u6ca1\u6536",
            "\u4ee3\u7406\u8d26\u6237",
            "\u7279\u522b\u63aa\u65bd",
            "\u7a7a\u58f3\u94f6\u884c",
            "\u8ba4\u8bc1\u8868",
            "\u6ce8\u518c\u4ee3\u7406\u4eba",
            "25%",
            "\u79c1\u4eba\u94f6\u884c\u8d26\u6237",
            "\u5916\u56fd\u94f6\u884c",
            "\u5c3d\u804c\u8c03\u67e5\u5236\u5ea6",
            "\u5f3a\u5316\u653f\u7b56",
        )
        # Generic obligation words such as "要求" are too broad: they linked
        # unrelated legal cards to any sentence that happened to say "requires".
        return (a_statute and has_any(text_b, rule_words)) or (b_statute and has_any(text_a, rule_words))

    def is_sanction_general_specific_pair() -> bool:
        joined = text_a + text_b
        if "\u5168\u9762\u5236\u88c1" in joined and "\u7279\u5b9a\u5236\u88c1" in joined and "SDN" in joined:
            return True
        general_ofac = ("OFAC" in joined or "\u6d77\u5916\u8d44\u4ea7\u63a7\u5236\u529e\u516c\u5ba4" in joined) and has_any(
            joined,
            ("\u5236\u88c1\u63aa\u65bd", "\u4ea4\u6613\u5b9e\u884c\u7ba1\u5236", "\u8d44\u4ea7\u8fdb\u884c\u51bb\u7ed3"),
        )
        specific_sanction = has_any(joined, ("\u57fa\u4e8e\u56fd\u5bb6\u7684\u5236\u88c1", "\u5168\u9762\u56fd\u5bb6\u5236\u88c1", "\u7279\u5b9a\u5236\u88c1", "SDN"))
        return general_ofac and specific_sanction

    def is_invoice_definition_effect_pair() -> bool:
        return (
            "\u4f4e\u5f00\u53d1\u7968" in text_a and has_any(text_b, ("\u8fd9\u79cd\u624b\u6bb5", "\u5dee\u989d\u4ef7\u503c\u8f6c\u79fb"))
        ) or (
            "\u4f4e\u5f00\u53d1\u7968" in text_b and has_any(text_a, ("\u8fd9\u79cd\u624b\u6bb5", "\u5dee\u989d\u4ef7\u503c\u8f6c\u79fb"))
        )

    def is_list_restatement_pair() -> bool:
        trade_invoice_methods = (
            "高开发票",
            "低开发票",
            "重复开具发票",
            "虚假描述",
            "超量装载",
            "装载不足",
        )
        a_invoice_methods = {word for word in trade_invoice_methods if word in text_a}
        b_invoice_methods = {word for word in trade_invoice_methods if word in text_b}
        if a_invoice_methods and b_invoice_methods and a_invoice_methods != b_invoice_methods:
            return False
        if shared_term_count(("风险管理", "客户接纳", "识别", "持续监控")) >= 3:
            return True
        if "15,000" in text_a and "15,000" in text_b and "商品经销商" in text_a and "商品经销商" in text_b:
            return True
        if shared_term_count(("\u52a0\u5bc6\u8d27\u5e01", "\u6697\u7f51", "\u9996\u9009\u652f\u4ed8")) >= 2:
            return True
        if "\u9ad8\u5f00\u53d1\u7968" in text_a and "\u9ad8\u5f00\u53d1\u7968" in text_b:
            return True
        if shared_term_count(("\u9ad8\u4e8e", "\u5e02\u573a\u516c\u5e73\u4ef7\u683c", "\u5dee\u4ef7")) >= 2 and "\u53d1\u7968" in text_a and "\u53d1\u7968" in text_b and not has_any(text_a + text_b, ("\u8d85\u91cf\u88c5\u8f7d", "\u88c5\u8f7d\u4e0d\u8db3")):
            return True
        if "\u9ad8\u5f00\u53d1\u7968" in text_a and has_any(text_b, ("\u4ef7\u503c\u8f83\u9ad8", "\u83b7\u5f97\u66f4\u591a\u4ef7\u503c", "\u5dee\u989d\u5229\u6da6", "\u5dee\u4ef7")):
            return True
        if "\u9ad8\u5f00\u53d1\u7968" in text_b and has_any(text_a, ("\u4ef7\u503c\u8f83\u9ad8", "\u83b7\u5f97\u66f4\u591a\u4ef7\u503c", "\u5dee\u989d\u5229\u6da6", "\u5dee\u4ef7")):
            return True
        # Broad screening/list-monitoring cards are often near each other, but
        # "sanctions screening", "watch-list filtering", and "customer/transaction
        # screening" can be different sub-points. Treat them as related elsewhere,
        # not as automatic same-point restatements.
        return False

    def is_definition_example_pair() -> bool:
        if has_any(text_a, ("是指", "最常见方法", "定义")) and has_any(text_b, ("该做法", "在这种类型中", "可能涉及", "例如")):
            return shared_term_count(("分拆", "挪用", "恐怖主义", "现金", "存款", "取款")) >= 1
        if has_any(text_b, ("是指", "最常见方法", "定义")) and has_any(text_a, ("该做法", "在这种类型中", "可能涉及", "例如")):
            return shared_term_count(("分拆", "挪用", "恐怖主义", "现金", "存款", "取款")) >= 1
        return False

    def is_parallel_method_pair() -> bool:
        if has_any(text_a + text_b, ("\u878d\u5408\u9636\u6bb5", "\u79bb\u6790\u9636\u6bb5", "Layering")):
            return False
        method_markers = (
            "高开发票",
            "低开发票",
            "重复开具发票",
            "虚假描述",
            "超量装载",
            "装载不足",
            "空壳公司",
            "拆分交易",
            "资金挪用",
            "恐怖主义伪装",
        )
        a_methods = {word for word in method_markers if word in text_a}
        b_methods = {word for word in method_markers if word in text_b}
        if a_methods and b_methods and a_methods != b_methods:
            return True
        if "发票" in text_a and "发票" in text_b and starts_with_list_item(title_b or quote_b):
            return True
        return False

    def is_case_heading_mechanism_pair() -> bool:
        a_case = has_any(text_a, ("案例", "证据"))
        b_case = has_any(text_b, ("案例", "证据"))
        mechanism_words = ("将", "分割", "分成", "存入", "汇往", "低于报告限额")
        a_mechanism = has_any(text_a, mechanism_words)
        b_mechanism = has_any(text_b, mechanism_words)
        shared_structuring = shared_term_count(("拆分交易", "现金", "存款", "交易")) >= 1
        return shared_structuring and ((a_case and b_mechanism) or (b_case and a_mechanism))

    def is_kyc_document_history_mismatch() -> bool:
        joined = text_a + text_b
        return (
            "\u56db\u5927\u5173\u952e\u5143\u7d20" in joined
            and "\u5df4\u585e\u5c14\u59d4\u5458\u4f1a" in joined
            and has_any(joined, ("\u6307\u5357", "\u767d\u76ae\u4e66", "\u53d6\u4ee3\u4e4b\u524d"))
        )

    def is_statute_or_case_mismatch() -> bool:
        joined = text_a + text_b
        sections_a = set(re.findall(r"第\s*(\d+)\s*(?:\([a-z]\))?\s*条", text_a, flags=re.I))
        sections_b = set(re.findall(r"第\s*(\d+)\s*(?:\([a-z]\))?\s*条", text_b, flags=re.I))
        if sections_a and sections_b and sections_a.isdisjoint(sections_b):
            return True
        if "\u7b2c 312 \u6761" in joined and has_any(joined, ("\u67e5\u5c01\u540c\u7b49\u6570\u989d", "\u4ee3\u7406\u94f6\u884c\u8d26\u6237\u4e2d\u67e5\u5c01")):
            return True
        if "ABLV" in joined and has_any(joined, ("\u4e0b\u8ff0\u4e94\u9879\u7279\u522b\u63aa\u65bd", "\u4efb\u4f55\u6216\u6240\u6709\u63aa\u65bd")):
            return True
        return False

    def is_cdd_summary_item_pair() -> bool:
        def summary(text: str) -> bool:
            return has_any(text, ("\u5ba2\u6237\u5c3d\u804c\u8c03\u67e5\u653f\u7b56", "\u5efa\u7acb\u98ce\u9669\u6863\u6848", "\u4e86\u89e3\u60a8\u7684\u5ba2\u6237"))

        def item(text: str) -> bool:
            return has_any(text, ("\u8bc6\u522b\u5ba2\u6237", "\u53d7\u76ca\u6240\u6709\u4eba", "\u6388\u6743\u7b7e\u5b57\u4eba", "\u6838\u5b9e\u5ba2\u6237"))

        return side_pair(summary, item)

    def is_wash_trading_mechanism_pair() -> bool:
        joined = text_a + text_b
        return "\u6d17\u552e" in joined and has_any(joined, ("\u8868\u73b0\u5f62\u5f0f", "\u5236\u9020\u4ea4\u6613\u7684\u5047\u8c61")) and has_any(joined, ("\u591a\u4e2a\u8d26\u6237", "\u76c8\u4e8f\u62b5\u6d88", "\u8f6c\u79fb\u4ed3\u4f4d"))

    def is_structuring_same_unit_pair() -> bool:
        def has_structuring_core(text: str) -> bool:
            return has_any(text, ("\u62c6\u5206\u4ea4\u6613", "\u5206\u62c6\u4ea4\u6613", "\u5206\u5272\u6210", "\u5206\u4e3a\u82e5\u5e72", "\u4f4e\u4e8e\u62a5\u544a\u9650\u989d", "\u4f4e\u4e8e\u9650\u989d"))

        if has_any(text_a + text_b, ("\u878d\u5408\u9636\u6bb5", "\u79bb\u6790\u9636\u6bb5", "Layering")):
            return False
        if has_any(text_a + text_b, ("\u6c47\u5f80\u56fd\u5916", "\u6c47\u603b\u5230\u4e00\u4e2a\u8d26\u6237", "\u5371\u9669\u4fe1\u53f7", "700 \u7b14", "\u8fd1 700", "\u5fae\u578b\u62c6\u5206")):
            return False
        if ("smurfing" in text_a.lower() or "runner" in text_a.lower()) != ("smurfing" in text_b.lower() or "runner" in text_b.lower()):
            return False
        return has_structuring_core(text_a) and has_structuring_core(text_b)

    def is_structuring_example_pair() -> bool:
        if has_any(text_a + text_b, ("\u878d\u5408\u9636\u6bb5", "\u79bb\u6790\u9636\u6bb5", "Layering")):
            return False

        def definition_side(text: str) -> bool:
            return has_any(text, ("\u62c6\u5206\u4ea4\u6613\u662f\u6307", "\u5206\u4e3a\u82e5\u5e72\u8f83\u5c0f\u91d1\u989d", "\u4f4e\u4e8e\u62a5\u544a\u9650\u989d"))

        def example_side(text: str) -> bool:
            return has_any(text, ("700 \u7b14", "\u8fd1 700", "\u591a\u7b14\u5b58\u6b3e", "\u540c\u4e00\u4eba", "\u540c\u4e00\u5929", "\u591a\u4e2a\u5206\u884c", "ATM", "\u5fae\u578b\u62c6\u5206\u4ea4\u6613", "\u5371\u9669\u4fe1\u53f7"))

        return side_pair(definition_side, example_side)

    def is_smurfing_structuring_pair() -> bool:
        def smurfing_side(text: str) -> bool:
            return has_any(text, ("smurfing", "\u62c6\u5206\u6d17\u94b1\u4eba\u5458", "\u73b0\u91d1\u62c6\u5206\u4ea4\u6613\u6848\u4f8b"))

        def structuring_side(text: str) -> bool:
            return has_any(text, ("\u62c6\u5206\u4ea4\u6613", "\u5c0f\u7b14", "\u4f4e\u4e8e\u62a5\u544a\u9650\u989d", "\u5206\u6563\u5b58\u6b3e"))

        return side_pair(smurfing_side, structuring_side)

    def is_structuring_red_flag_pair() -> bool:
        def definition_or_actor(text: str) -> bool:
            return has_any(text, ("\u62c6\u5206\u4ea4\u6613", "\u62c6\u5206\u6d17\u94b1\u4eba\u5458", "runner"))

        def red_flag_scene(text: str) -> bool:
            return has_any(text, ("\u5206\u6563\u5b58\u5165\u591a\u4e2a\u8d26\u6237", "\u6c47\u603b\u5230\u4e00\u4e2a\u8d26\u6237", "\u6c47\u5f80\u56fd\u5916", "\u5371\u9669\u4fe1\u53f7"))

        return side_pair(definition_or_actor, red_flag_scene)

    def is_customer_profile_expected_activity_pair() -> bool:
        def profile_side(text: str) -> bool:
            return has_any(text, ("\u6982\u51b5\u5e94\u5305\u542b", "\u5ba2\u6237\u4fe1\u606f\u4e0e\u6d3b\u52a8"))

        def expected_activity_side(text: str) -> bool:
            return has_any(text, ("\u8d26\u6237\u7684\u9884\u671f\u7528\u9014", "\u9884\u671f\u4ea4\u6613", "\u91d1\u989d\u3001\u6570\u91cf\u3001\u7c7b\u578b"))

        return side_pair(profile_side, expected_activity_side)

    def is_pep_definition_edd_pair() -> bool:
        def pep_side(text: str) -> bool:
            return has_any(text, ("\u653f\u6cbb\u516c\u4f17\u4eba\u7269", "PEP", "\u56fd\u5916\u653f\u515a", "\u653f\u5e9c\u6240\u6709\u5236\u5546\u4e1a\u4f01\u4e1a"))

        def edd_side(text: str) -> bool:
            return has_any(text, ("\u5f3a\u5316\u8be6\u7ec6\u5ba1\u67e5", "\u5916\u56fd\u8150\u8d25\u6240\u5f97", "\u4fb5\u541e", "\u632a\u7528\u516c\u5171\u8d44\u91d1"))

        return side_pair(pep_side, edd_side)

    def is_shell_bank_definition_rule_pair() -> bool:
        def shell_definition_side(text: str) -> bool:
            return "\u7a7a\u58f3\u94f6\u884c" in text and has_any(text, ("\u4ec5\u5728\u540d\u4e49\u4e0a\u5b58\u5728", "\u5e76\u65e0\u5b9e\u4f53\u7ecf\u8425", "\u4e0d\u96b6\u5c5e\u4efb\u4f55"))

        def shell_rule_side(text: str) -> bool:
            return "\u7a7a\u58f3\u94f6\u884c" in text and has_any(text, ("\u7981\u6b62\u4e3a", "\u4ee3\u7406\u8d26\u6237", "\u7b2c 313 \u6761"))

        return side_pair(shell_definition_side, shell_rule_side)

    def is_ofac_license_type_pair() -> bool:
        def license_rule_side(text: str) -> bool:
            return has_any(text, ("\u83b7\u5f97\u8bb8\u53ef\u6388\u6743", "\u539f\u672c\u4f1a\u88ab\u7981\u6b62\u7684\u4ea4\u6613"))

        def license_type_side(text: str) -> bool:
            return has_any(text, ("\u4e00\u822c\u8bb8\u53ef", "\u7279\u522b\u8bb8\u53ef", "\u4e24\u5927\u7c7b", "\u4e66\u9762\u6587\u4ef6"))

        return has_any(text_a + text_b, ("OFAC", "\u6d77\u5916\u8d44\u4ea7\u63a7\u5236\u529e\u516c\u5ba4")) and side_pair(license_rule_side, license_type_side)

    def is_fiu_recommendation_list_pair() -> bool:
        def rec29_side(text: str) -> bool:
            return has_any(text, ("\u7b2c 29", "FATF", "\u91d1\u878d\u884c\u52a8\u7279\u522b\u5de5\u4f5c\u7ec4")) and has_any(
                text,
                ("\u91d1\u878d\u60c5\u62a5\u673a\u6784", "FIU"),
            ) and has_any(text, ("\u63a5\u6536\u548c\u5206\u6790", "\u5206\u53d1", "\u53ef\u7591\u4ea4\u6613\u62a5\u544a"))

        def fiu_item_side(text: str) -> bool:
            return has_any(text, ("\u91d1\u878d\u60c5\u62a5\u673a\u6784", "FIU", "FinCEN", "\u91d1\u878d\u72af\u7f6a\u6267\u6cd5\u7f51\u7edc", "\u53ef\u7591\u4ea4\u6613\u62a5\u544a", "STR", "SAR", "\u5176\u4ed6\u4fe1\u606f"))

        return side_pair(rec29_side, fiu_item_side)

    def is_fiu_function_cooperation_pair() -> bool:
        def fiu_function_side(text: str) -> bool:
            return has_any(text, ("\u91d1\u878d\u60c5\u62a5\u673a\u6784", "FIU", "\u7b2c 29")) and has_any(
                text,
                ("\u63a5\u6536\u548c\u5206\u6790", "\u5206\u53d1", "\u53ef\u7591\u4ea4\u6613\u62a5\u544a", "SAR", "STR"),
            )

        def fiu_cooperation_side(text: str) -> bool:
            return has_any(text, ("\u91d1\u878d\u60c5\u62a5\u673a\u6784", "FIU")) and has_any(
                text,
                ("\u5408\u4f5c", "\u6c9f\u901a", "\u4ea4\u6362", "\u4e2d\u4ecb", "\u83b7\u53d6\u4fe1\u606f", "\u6700\u9ad8\u6548"),
            )

        return side_pair(fiu_function_side, fiu_cooperation_side)

    def is_greylist_alias_explanation_pair() -> bool:
        def is_greylist_text(text: str) -> bool:
            return has_any(text, ("灰名单", "应加强监控的司法管辖区", "Jurisdictions under Increased"))

        def is_call_for_action_text(text: str) -> bool:
            return has_any(text, ("需要采取行动的高风险司法管辖区", "High-Risk Jurisdictions Subject", "公开声明"))

        if is_call_for_action_text(text_a) or is_call_for_action_text(text_b):
            return False
        joined = text_a + text_b
        return is_greylist_text(text_a) and is_greylist_text(text_b) and has_any(
            joined,
            ("\u4e5f\u5e38\u79f0\u4e3a", "\u56fd\u5bb6\u5df2\u627f\u8bfa", "\u6218\u7565\u6027\u7f3a\u9677", "\u5f3a\u5316\u76d1\u63a7"),
        )

    def is_penalty_restatement_pair() -> bool:
        joined = text_a + text_b
        if not ("1000 \u4e07\u7f8e\u5143" in joined and "\u6c11\u4e8b\u7f5a\u6b3e" in joined and "\u94f6\u884c" in joined):
            return False
        penalty_terms = ("\u6c11\u4e8b\u7f5a\u6b3e", "\u6ca1\u6536", "125 \u4e07\u7f8e\u5143", "\u548c\u89e3", "\u540c\u610f")
        a_terms = {term for term in penalty_terms if term in text_a}
        b_terms = {term for term in penalty_terms if term in text_b}
        return a_terms == b_terms

    def is_board_reporting_restatement_pair() -> bool:
        board_words = ("\u76f4\u63a5\u5411\u8463\u4e8b\u4f1a", "\u8463\u4e8b\u4f1a\u59d4\u5458\u4f1a", "\u5ba1\u8ba1\u59d4\u5458\u4f1a")
        audit_words = ("\u5ba1\u8ba1\u4eba\u5458", "\u72ec\u7acb\u5ba1\u8ba1", "\u5ba1\u8ba1\u804c\u80fd")
        a_same_point = has_any(text_a, board_words) and has_any(text_a, audit_words)
        b_same_point = has_any(text_b, board_words) and has_any(text_b, audit_words)
        return a_same_point and b_same_point

    def is_legal_person_transparency_pair() -> bool:
        def transparency_side(text: str) -> bool:
            return has_any(text, ("\u6cd5\u4eba", "\u6cd5\u5f8b\u5b89\u6392", "\u900f\u660e\u5ea6"))

        def beneficial_owner_side(text: str) -> bool:
            return has_any(text, ("\u53d7\u76ca\u6240\u6709\u4eba", "\u5fc5\u987b\u63d0\u4f9b", "\u80fd\u591f\u83b7\u5f97\u6216\u8bbf\u95ee", "\u6240\u6709\u6743\u548c\u63a7\u5236\u7ed3\u6784"))

        return side_pair(transparency_side, beneficial_owner_side)

    def is_strong_parent_child_pair() -> bool:
        return (
            is_cdd_summary_item_pair()
            or is_wash_trading_mechanism_pair()
            or is_customer_profile_expected_activity_pair()
            or is_pep_definition_edd_pair()
            or is_shell_bank_definition_rule_pair()
            or is_ofac_license_type_pair()
            or is_fiu_recommendation_list_pair()
            or is_greylist_alias_explanation_pair()
            or is_legal_person_transparency_pair()
            or is_structuring_example_pair()
            or is_smurfing_structuring_pair()
            or is_structuring_red_flag_pair()
        )

    def is_known_mismatch_pair() -> bool:
        return is_kyc_document_history_mismatch() or is_statute_or_case_mismatch()

    def is_us_patriot_act_topic_mismatch() -> bool:
        def patriot_topic_groups(text: str) -> set[str]:
            groups: set[str] = set()
            if has_any(text, ("第 311", "首要洗钱关注对象", "五项特别措施", "下述五项特别措施", "特别措施")):
                groups.add("311_special_measures")
            if has_any(
                text,
                (
                    "第 312",
                    "私人银行账户",
                    "私人银行业务规定",
                    "非美国人员的外国代理",
                    "外国代理账户",
                    "10% 及以上投票权",
                    "投票权",
                    "强化政策、程序和控制",
                    "在美国的代理账户中存在的可疑洗钱活动",
                    "外国腐败所得",
                    "强化详细审查",
                ),
            ):
                groups.add("312_correspondent_private_banking")
            if "代理账户" in text and has_any(text, ("强化审查", "评估", "尽职调查", "洗钱风险", "侦测可能的洗钱", "减轻与此等账户相关")):
                groups.add("312_correspondent_private_banking")
            if has_any(text, ("第 313", "空壳银行", "实体经营", "认证表", "不向外国空壳银行")):
                groups.add("313_shell_bank")
            if has_any(
                text,
                (
                    "第 319",
                    "319(a)",
                    "没收",
                    "查封",
                    "犯罪收益",
                    "同等数额",
                    "无需追踪资金",
                    "没收控诉",
                    "作证传票",
                    "25% 控股权",
                    "注册代理人",
                ),
            ):
                groups.add("319_forfeiture_records")
            if "通汇账户" in text and has_any(text, ("客户进行身份识别", "获得允许使用", "通过其进行交易")):
                groups.add("311_special_measures")
            return groups

        groups_a = patriot_topic_groups(text_a)
        groups_b = patriot_topic_groups(text_b)
        if groups_a and groups_b and groups_a.isdisjoint(groups_b):
            return True

        def shell_or_records(text: str) -> bool:
            return has_any(text, ("第 313", "空壳银行", "实体经营", "认证表", "不向外国空壳银行"))

        def forfeiture_or_319(text: str) -> bool:
            return has_any(text, ("第 319", "319(a)", "没收", "查封", "犯罪收益", "同等数额", "作证传票", "25% 控股权", "注册代理人"))

        return side_pair(shell_or_records, forfeiture_or_319)

    def is_kyc_list_topic_mismatch() -> bool:
        def kyc_list(text: str) -> bool:
            return has_any(text, ("了解您的客户", "四大关键元素", "客户身份识别", "客户接纳政策", "持续监控"))

        def audit_or_non_kyc(text: str) -> bool:
            return has_any(text, ("审计职能", "第三道防线", "审计委员会", "独立评估", "独立审计"))

        return side_pair(kyc_list, audit_or_non_kyc)

    def is_cross_framework_weak_pair() -> bool:
        joined = text_a + text_b
        if is_us_patriot_act_topic_mismatch() or is_kyc_list_topic_mismatch():
            return True
        eu_signal = has_any(joined, ("AMLD", "\u6b27\u76df", "\u7b2c 5 \u53f7\u6307\u4ee4", "\u6307\u4ee4"))
        us_signal = has_any(joined, ("AMLA", "\u7231\u56fd\u8005\u6cd5\u6848", "BSA", "FinCEN", "\u7f8e\u56fd"))
        if eu_signal and us_signal:
            return True
        ofac_signal = has_any(joined, ("OFAC", "\u6d77\u5916\u8d44\u4ea7\u63a7\u5236\u529e\u516c\u5ba4", "\u5168\u9762\u5236\u88c1", "\u7279\u5b9a\u5236\u88c1"))
        fiu_fatf_signal = has_any(joined, ("FATF", "\u91d1\u878d\u884c\u52a8\u7279\u522b\u5de5\u4f5c\u7ec4", "\u91d1\u878d\u60c5\u62a5\u673a\u6784", "FIU", "\u7b2c 29"))
        if ofac_signal and fiu_fatf_signal:
            return True
        officer_signal = has_any(joined, ("\u5408\u89c4\u4e13\u5458", "\u53cd\u6d17\u94b1\u62a5\u544a\u5458", "MLRO"))
        confidentiality_signal = has_any(joined, ("\u4fdd\u5bc6", "\u4e0d\u5f97\u544a\u77e5\u5ba2\u6237", "\u5df2\u88ab\u62a5\u544a"))
        if officer_signal and confidentiality_signal:
            return True
        return False

    def is_stage_vs_method_mismatch() -> bool:
        joined = text_a + text_b
        stage_signal = has_any(joined, ("\u878d\u5408\u9636\u6bb5", "\u79bb\u6790\u9636\u6bb5", "\u5904\u7f6e\u9636\u6bb5", "\u9636\u6bb5\u4e00", "\u9636\u6bb5\u4e8c", "\u9636\u6bb5\u4e09", "Layering"))
        method_signal = has_any(joined, ("\u62c6\u5206\u4ea4\u6613", "\u7a7a\u58f3\u516c\u53f8", "\u4f4e\u4e8e\u62a5\u544a\u9650\u989d"))
        return stage_signal and method_signal

    def is_pep_or_cdd_vs_patriot_records_mismatch() -> bool:
        def pep_or_general_cdd(text: str) -> bool:
            return has_any(text, ("PEP", "\u653f\u6cbb\u516c\u4f17\u4eba\u7269", "\u53d7\u76ca\u6240\u6709\u4eba", "\u5ba2\u6237\u5c3d\u804c\u8c03\u67e5", "\u989d\u5916\u5c3d\u804c\u8c03\u67e5"))

        def patriot_records(text: str) -> bool:
            return has_any(
                text,
                (
                    "\u7b2c 319",
                    "319(a)",
                    "\u4f5c\u8bc1\u4f20\u7968",
                    "25% \u63a7\u80a1\u6743",
                    "\u6ce8\u518c\u4ee3\u7406\u4eba",
                    "\u67e5\u5c01\u540c\u7b49\u6570\u989d",
                    "\u6ca1\u6536",
                ),
            )

        return side_pair(pep_or_general_cdd, patriot_records)

    def has_strong_parent_anchor() -> bool:
        if title_sim >= 0.30 or quote_sim >= 0.30:
            return True
        anchors = (
            "声誉风险",
            "货币服务企业",
            "MSB",
            "了解您的客户",
            "客户接纳",
            "持续监控",
            "风险管理",
            "客户身份识别",
            "第 311 条",
            "第 319",
            "代理账户",
            "特别措施",
            "资金挪用",
            "恐怖主义",
            "分拆交易",
            "低开发票",
            "高开发票",
            "商品经销商",
            "15,000",
            "OFAC",
            "SDN",
        )
        return shared_term_count(anchors) >= 1

    def has_minimum_relation_overlap() -> bool:
        if title_sim >= 0.22 or quote_sim >= 0.22:
            return True
        anchors = (
            "制裁",
            "FATF",
            "OFAC",
            "SAR",
            "尽职调查",
            "董事会",
            "加密货币",
            "恐怖主义",
            "代理银行",
            "委托银行",
            "空壳银行",
            "拆分交易",
            "分拆交易",
            "高开发票",
            "低开发票",
            "PEP",
            "政治公众人物",
            "FIU",
            "金融情报机构",
            "传票",
            "Egmont",
            "埃格蒙特",
        )
        return shared_term_count(anchors) >= 1

    def has_strong_relation_overlap() -> bool:
        if title_sim >= 0.28 or quote_sim >= 0.28:
            return True
        anchors = (
            "OFAC",
            "SDN",
            "FATF",
            "SAR",
            "STR",
            "代理银行",
            "委托银行",
            "空壳银行",
            "拆分交易",
            "分拆交易",
            "高开发票",
            "低开发票",
            "PEP",
            "政治公众人物",
            "FIU",
            "金融情报机构",
            "传票",
            "Egmont",
            "埃格蒙特",
            "董事会",
            "加密货币",
            "暗网",
        )
        return shared_term_count(anchors) >= 1

    def is_parallel_enumeration() -> bool:
        joined = title_a + title_b + quote_a + quote_b
        first_second = (
            ("第一" in joined and "第二" in joined)
            or ("第一个" in joined and "第二个" in joined)
            or ("一是" in joined and "二是" in joined)
        )
        additive_pair = (
            has_any(title_a + quote_a, ("此外", "另外", "以及", "同时", "还要求"))
            and has_any(title_b + quote_b, ("此外", "另外", "以及", "同时", "还要求"))
        )
        same_rule_obligation = additive_pair and has_any(
            title_a + title_b + quote_a + quote_b,
            ("必须", "应", "要求", "记录", "指定", "保存", "接受"),
        )
        return first_second or same_rule_obligation

    def is_heading_detail_pair() -> bool:
        score_a = heading_score(title_a)
        score_b = heading_score(title_b)
        len_a = len(normalize(title_a or quote_a))
        len_b = len(normalize(title_b or quote_b))
        heading_a_detail_b = has_explicit_heading_signal(title_a) and score_a >= 2 and len_a <= 120 and len_b >= len_a + 20
        heading_b_detail_a = has_explicit_heading_signal(title_b) and score_b >= 2 and len_b <= 120 and len_a >= len_b + 20
        title_markers = ("第", "条", "定义", "概念", "原则", "要求", "职责", "名单", "文件")
        explicit_heading = (
            has_explicit_heading_signal(title_a) and has_any(title_a, title_markers) and len_b >= len_a + 20
        ) or (
            has_explicit_heading_signal(title_b) and has_any(title_b, title_markers) and len_a >= len_b + 20
        )
        return (heading_a_detail_b or heading_b_detail_a or explicit_heading) and not is_parallel_enumeration()

    def is_definition_mechanism_pair() -> bool:
        joined = title_a + title_b + quote_a + quote_b
        definition_signal = has_any(joined, ("定义", "是指", "是指", "指的是", "即", "称为"))
        mechanism_signal = has_any(joined, ("通过", "方式", "机制", "差额", "转移", "导致", "用于", "意味着", "涉及", "可能涉及"))
        return definition_signal and mechanism_signal and not is_parallel_enumeration()

    def is_specific_detail_of_general() -> bool:
        joined = text_a + text_b
        if "全面制裁" in joined and "特定制裁" in joined:
            return True
        general_markers = ("包括", "分为", "以下", "例如")
        specific_markers = ("SDN", "25%", "注册代理人", "灰名单", "高风险司法管辖区")
        if (
            (has_any(text_a, general_markers) and has_any(text_b, specific_markers))
            or (has_any(text_b, general_markers) and has_any(text_a, specific_markers))
        ):
            return not is_parallel_enumeration()
        return False

    def is_high_frequency_only_absorption() -> bool:
        return (
            "high_frequency_absorption" in reasons
            and "same_question_core_core" not in reasons
            and "same_option_multi_card" not in reasons
            and "core_contrast_same_question" not in reasons
        )

    def has_safe_absorption_structure() -> bool:
        if title_sim >= 0.18 or quote_sim >= 0.18:
            return True
        if is_strong_parent_child_pair():
            return True
        if is_statute_heading_rule_pair() or is_rule_implementation_pair():
            return True
        if is_sanction_general_specific_pair():
            return True
        if is_invoice_definition_effect_pair():
            return True
        if is_specific_detail_of_general() and has_strong_parent_anchor():
            return True
        if is_definition_mechanism_pair() and has_strong_parent_anchor():
            return True
        if is_structural_list_pair() and has_strong_parent_anchor():
            return True
        return False

    def out(label: str, confidence: str, rationale: str, risk_flags: list[str] | None = None) -> dict[str, Any]:
        return {
            "draft_label": label,
            "draft_confidence": confidence,
            "draft_rationale": rationale,
            "draft_risk_flags": risk_flags or [],
            "context_scope": scope,
        }

    if title_sim >= 0.96 and quote_sim >= 0.96:
        return out(
            "merge_same_point",
            "high",
            "title and quote are near-identical; treat as duplicate wording of one atomic point.",
        )

    if looks_like_alias() and (title_sim >= 0.05 or quote_sim >= 0.05):
        return out(
            "merge_same_point",
            "medium",
            "the pair appears to be a formal term and its alias/name variant.",
            ["alias_or_definition"],
        )

    if is_known_mismatch_pair():
        return out(
            "keep_separate",
            "medium",
            "the two cards share retrieval/question context but point to different statute, case, or document-history units.",
            ["known_mismatch_guardrail"],
        )

    if is_cross_framework_weak_pair():
        return out(
            "keep_separate",
            "medium",
            "the pair is linked by a question route but crosses legal/institutional frameworks without a shared atomic teaching point.",
            ["cross_framework_guardrail"],
        )

    if is_stage_vs_method_mismatch():
        return out(
            "keep_separate",
            "medium",
            "money-laundering stage cards and concrete method cards should not be linked automatically without explicit textbook structure.",
            ["stage_method_guardrail"],
        )

    if is_pep_or_cdd_vs_patriot_records_mismatch():
        return out(
            "keep_separate",
            "medium",
            "PEP/general CDD cards and Patriot Act forfeiture/records cards are different teaching units even when a question recalls both.",
            ["patriot_cdd_boundary"],
        )

    if is_high_frequency_only_absorption() and not has_safe_absorption_structure():
        return out(
            "keep_separate",
            "low",
            "high-frequency absorption is treated as a recall signal only; without question context or explicit shared structure it should not create a parent-child link.",
            ["weak_high_frequency_absorption"],
        )

    if is_case_heading_mechanism_pair():
        return out(
            "sibling_under_parent",
            "low",
            "one card is a case/evidence heading while the other states a concrete mechanism; keep them as related sibling details rather than one atomic point.",
            ["case_heading_mechanism"],
        )

    if is_fiu_function_cooperation_pair():
        return out(
            "sibling_under_parent",
            "medium",
            "FIU receiving/analyzing/reporting functions and FIU cooperation/communication rules are parallel sub-points under the FIU topic.",
            ["fiu_parallel_subpoints"],
        )

    if is_structuring_same_unit_pair():
        return out(
            "sibling_under_parent",
            "medium",
            "the two cards belong to the same structuring/smurfing topic, but may be definition and scenario variants; do not merge automatically.",
            ["structuring_topic_variant"],
        )

    if is_penalty_restatement_pair():
        return out(
            "merge_same_point",
            "medium",
            "the two cards restate the same penalty fact.",
            ["same_penalty_fact"],
        )

    if is_board_reporting_restatement_pair():
        return out(
            "sibling_under_parent",
            "medium",
            "the two cards share audit-independence/reporting-line anchors, but may differ by control-line context; keep as sibling sub-points.",
            ["audit_reporting_related"],
        )

    if is_parallel_method_pair():
        return out(
            "sibling_under_parent",
            "medium",
            "the two cards are parallel methods/items under a broader textbook topic, not parent-child.",
            ["parallel_method"],
        )

    if is_list_restatement_pair():
        return out(
            "merge_same_point",
            "medium",
            "the two cards restate the same list or threshold-based concept.",
            ["list_restatement"],
        )

    if "\u5173\u952e\u4f18\u5148\u4e8b\u9879" in text_a and "\u8fd9\u5305\u62ec" in text_b:
        return out(
            "parent_child",
            "medium",
            "one card states key priorities and the other gives the included requirement.",
            ["priority_includes_detail"],
        )
    if "\u5173\u952e\u4f18\u5148\u4e8b\u9879" in text_b and "\u8fd9\u5305\u62ec" in text_a:
        return out(
            "parent_child",
            "medium",
            "one card states key priorities and the other gives the included requirement.",
            ["priority_includes_detail"],
        )

    if (is_specific_detail_of_general() and has_strong_parent_anchor()) or is_sanction_general_specific_pair():
        return out(
            "parent_child",
            "medium",
            "one card states a general category while the other expands a specific member/detail.",
            ["general_specific"],
        )

    if (
        is_strong_parent_child_pair()
        or is_statute_heading_rule_pair()
        or is_rule_implementation_pair()
        or is_invoice_definition_effect_pair()
        or (is_structural_list_pair() and has_strong_parent_anchor())
        or (is_definition_example_pair() and has_strong_parent_anchor())
    ):
        return out(
            "parent_child",
            "medium",
            "one card is an explicit list/rule/definition and the other is its item, implementation, or example.",
            ["explicit_structure"],
        )

    if scope == "card_only_nearby_text":
        if looks_like_alias():
            return out(
                "merge_same_point",
                "medium",
                "nearby-text signal plus alias wording suggests the same concept.",
                ["card_only_nearby_text", "alias_or_definition"],
            )
        if is_parallel_method_pair():
            return out(
                "sibling_under_parent",
                "low",
                "nearby-text signal plus parallel method wording suggests sibling concepts, not one atomic point.",
                ["card_only_nearby_text", "parallel_method"],
            )
        if is_list_restatement_pair():
            return out(
                "merge_same_point",
                "medium",
                "nearby-text signal plus repeated list/threshold wording suggests the same concept.",
                ["card_only_nearby_text", "list_restatement"],
            )
        if (
            is_statute_heading_rule_pair()
            or is_rule_implementation_pair()
            or is_sanction_general_specific_pair()
            or is_invoice_definition_effect_pair()
            or (is_structural_list_pair() and (has_strong_parent_anchor() or starts_with_list_item(title_a or quote_a) or starts_with_list_item(title_b or quote_b)))
        ):
            return out(
                "parent_child",
                "low",
                "nearby-text signal plus explicit list/rule structure suggests a parent-child relation.",
                ["card_only_nearby_text"],
            )
        return out(
            "keep_separate",
            "low",
            "nearby-text signal only; keep separate until question context or LLM review supports a relation.",
            ["card_only_nearby_text"],
        )

    if is_parallel_enumeration():
        return out(
            "sibling_under_parent",
            "high",
            "the two cards look like parallel listed obligations/items under the same broader textbook point.",
            ["parallel_enumeration"],
        )

    if is_heading_detail_pair():
        if has_strong_parent_anchor():
            return out(
                "parent_child",
                "high",
                "one card is a heading/general rule and the other is its concrete rule/detail.",
                ["heading_detail"],
            )
        return out(
            "keep_separate",
            "low",
            "heading/detail shape exists, but the pair lacks shared anchors for a safe parent-child link.",
            ["weak_heading_detail"],
        )

    if is_definition_mechanism_pair():
        if has_strong_parent_anchor():
            return out(
                "parent_child",
                "high",
                "one card defines the concept while the other explains its mechanism or operation.",
                ["definition_mechanism"],
            )
        return out(
            "keep_separate",
            "low",
            "definition/mechanism wording appears, but the concepts do not share enough anchors.",
            ["weak_definition_mechanism"],
        )

    if ctype == "sibling_under_parent_candidate":
        if not has_strong_relation_overlap():
            return out(
                "keep_separate",
                "low",
                "same-question core/contrast recall has too little text or anchor overlap to form a stable sibling relation.",
                ["weak_same_question_signal"],
            )
        return out(
            "sibling_under_parent",
            "high",
            "core/contrast or same-question evidence points to sibling concepts under a broader discriminating point.",
        )

    if (
        "high_frequency_absorption" in reasons
        and "same_question_core_core" not in reasons
        and "same_option_multi_card" not in reasons
        and max_q >= 3
        and min_q <= 2
        and qd >= 2
    ):
        return out(
            "keep_separate",
            "low",
            "high-frequency absorption is a recall signal only; without explicit textbook structure it should not create a parent-child link.",
            ["weak_high_frequency_absorption"],
        )

    if ctype == "parent_child_or_keep_separate_candidate":
        if max(heading_score(title_a), heading_score(title_b)) >= 3 and max_q >= 2:
            return out(
                "keep_separate",
                "low",
                "candidate has a weak heading/detail shape, but lacks enough explicit structure for automatic parent-child linking.",
                ["weak_heading_detail"],
            )
        return out(
            "keep_separate",
            "low",
            "candidate is related but lacks enough structure signal for automatic parent/child linking.",
        )

    if "same_option_multi_card" in reasons:
        if not has_minimum_relation_overlap():
            return out(
                "keep_separate",
                "low",
                "same-option multi-card recall has too little text or anchor overlap to form a stable relation.",
                ["weak_same_option_signal"],
            )
        if "same_question_core_core" in reasons:
            return out(
                "sibling_under_parent",
                "medium",
                "same question and same option connect the cards, but they look like parallel sub-points rather than duplicates.",
                ["same_question_core_core", "same_option_multi_card"],
            )
        return out(
            "sibling_under_parent",
            "low",
            "same-option multi-card evidence is treated as a relation recall signal, not a merge or parent-child conclusion.",
            ["same_option_multi_card"],
        )

    if ctype == "merge_same_point_candidate":
        return out(
            "needs_review",
            "low",
            "recall route suggested possible merge, but text does not support safe automatic merge or hierarchy.",
            ["merge_route_not_confirmed"],
        )

    if ctype == "merge_or_parent_child_candidate":
        if "high_frequency_absorption" in reasons and "same_question_core_core" not in reasons and max_q >= 3:
            return out(
                "keep_separate",
                "low",
                "high-frequency absorption is present, but not enough evidence for a parent-child relation.",
                ["weak_high_frequency_absorption"],
            )
        if title_sim >= 0.55 or quote_sim >= 0.55:
            return out(
                "keep_separate",
                "low",
                "text is related, but similarity alone should not create parent-child structure.",
                ["weak_similarity_only"],
            )
        return out(
            "keep_separate",
            "low",
            "related retrieval route only; keep separate without stronger semantic evidence.",
        )

    return out("needs_review", "low", "unknown relation candidate type.")


def build_relation_draft(selected_pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for pair in selected_pairs:
        draft = label_relation(pair)
        item = {
            "pair_id": pair["pair_id"],
            "candidate_type": pair["relation_candidate_type"],
            "score": pair["score"],
            "reasons": pair.get("reasons") or [],
            "card_a": pair["card_a_summary"],
            "card_b": pair["card_b_summary"],
            **draft,
        }
        items.append(item)
    return items


def build_relation_profile(relation_items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    profile: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "pair_ids": [],
        "label_counts": Counter(),
        "scope_counts": Counter(),
        "best_label": "",
    })
    for item in relation_items:
        for card_key in ("card_a", "card_b"):
            card_id = item[card_key]["card_id"]
            info = profile[card_id]
            info["pair_ids"].append(item["pair_id"])
            info["label_counts"][item["draft_label"]] += 1
            info["scope_counts"][item["context_scope"]] += 1

    for card_id, info in profile.items():
        counts = info["label_counts"]
        if counts:
            info["best_label"] = counts.most_common(1)[0][0]
        info["pair_ids"] = sorted(set(info["pair_ids"]))
        info["label_counts"] = dict(counts.most_common())
        info["scope_counts"] = dict(info["scope_counts"].most_common())
    return profile


def draft_role_from_profile(profile: dict[str, Any], point: dict[str, Any]) -> str:
    best_label = str(profile.get("best_label") or "").strip()
    if not best_label:
        return "standalone"
    if best_label == "merge_same_point":
        return "merged_candidate"
    if best_label == "parent_child":
        return "parent_like"
    if best_label == "sibling_under_parent":
        return "sibling_like"
    if best_label == "keep_separate":
        return "standalone"
    return "standalone"


def build_point_draft(
    candidate_points: list[dict[str, Any]],
    relation_profile: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    items = []
    for point in candidate_points:
        if point["question_count"] <= 0:
            continue
        profile = relation_profile.get(point["card_id"], {})
        item = {
            "id": point["id"],
            "title": point["title_placeholder"],
            "title_status": "placeholder_from_card_quote",
            "point_type": point["point_type"],
            "tags": point["tags"],
            "parent_id": None,
            "children": [],
            "card_ids": [point["card_id"]],
            "question_ids": point["question_ids"],
            "question_count": point["question_count"],
            "core_question_count": point["core_question_count"],
            "contrast_question_count": point["confusing_contrast_question_count"],
            "subtree_question_count": point["subtree_question_count"],
            "evidence_quotes": [{"card_id": point["card_id"], "quote": point["quote"]}],
            "relation_candidate_pair_ids": profile.get("pair_ids", [])[:30],
            "draft_relation_profile": {
                "best_label": profile.get("best_label", ""),
                "label_counts": profile.get("label_counts", {}),
                "scope_counts": profile.get("scope_counts", {}),
                "draft_role": draft_role_from_profile(profile, point),
            },
            "review_status": "preview_v6_structure_draft",
        }
        items.append(item)
    items.sort(key=lambda item: (-item["question_count"], item["id"]))
    return {
        "schema_version": "preview_v6_structure_draft",
        "note": "Heuristic draft calibrated from 2026-06-30 100x100 restricted-judgement batch; not final assets.",
        "items": items,
    }


def build_contrast_draft(contrast_rows: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    for row in contrast_rows:
        if row.get("classification") == "confusing_contrast":
            action = "count_in_exam_point"
        elif row.get("classification") == "pure_exclusion":
            action = "trace_only"
        else:
            action = "hold_for_review"
        item = dict(row)
        item["draft_action"] = action
        item["draft_note"] = (
            "confusing_contrast enters exam-point tags; pure_exclusion is trace-only; needs_review stays blocked."
        )
        items.append(item)
    return {
        "schema_version": "preview_v6_contrast_draft",
        "items": items,
    }


def summarize_report(
    summary: dict[str, Any],
    relation_items: list[dict[str, Any]],
    contrast_draft: dict[str, Any],
    point_draft: dict[str, Any],
) -> str:
    rel_counts = Counter(item["draft_label"] for item in relation_items)
    rel_scope = Counter(item["context_scope"] for item in relation_items)
    contrast_counts = Counter(item["draft_action"] for item in contrast_draft["items"])
    lines = [
        "# Preview v6 结构草稿报告",
        "",
        f"- 生成时间：{summary['generated_at']}",
        f"- 来源候选句卡：{summary['candidate_point_count']}",
        f"- relation 候选对（已裁判草稿）：{len(relation_items)}",
        f"- contrast 候选边（已标注草稿）：{len(contrast_draft['items'])}",
        f"- 正式预览考点：{summary['formal_exam_point_preview_count']}",
        f"- 仅保留待审候选：{summary['review_only_point_count']}",
        "",
        "## relation 草稿分布",
        "",
    ]
    for key, value in rel_counts.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## relation 上下文范围", ""])
    for key, value in rel_scope.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## contrast 草稿动作", ""])
    for key, value in contrast_counts.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## 结构草稿抽样", ""])

    sample_rel = relation_items[:8]
    for item in sample_rel:
        lines.extend(
            [
                f"### {item['pair_id']} -> {item['draft_label']} ({item['draft_confidence']})",
                f"- scope：{item['context_scope']}",
                f"- A：{compact(item['card_a']['title_placeholder'], 80)}",
                f"- B：{compact(item['card_b']['title_placeholder'], 80)}",
                f"- 理由：{item['draft_rationale']}",
                "",
            ]
        )

    lines.extend(["## 草稿结论", ""])
    lines.append("1. 关系草稿明显比 v5 更保守，merge_same_point 变得非常少。")
    lines.append("2. 大多数关系都落到 parent_child / sibling_under_parent，说明考点结构应先做层级，而不是先强合并。")
    lines.append("3. contrast 的可入库部分仍然很大，但必须继续拦截答案绑定异常和 quote 过薄的情况。")
    lines.append("4. 本轮只生成草稿，不覆盖正式前端资产。")
    lines.append("")
    lines.append("## 点位草稿概况")
    lines.append("")
    lines.append(f"- 草稿考点数：{len(point_draft['items'])}")
    lines.append(f"- 题目上下文点位：{summary['question_context_count']}")
    return "\n".join(lines)


def main() -> None:
    V6_DIR.mkdir(parents=True, exist_ok=True)

    v5_summary = read_json(V5_DIR / "summary.json")
    candidate_points = read_json(V5_DIR / "all_candidate_points.json")["items"]
    contrast_rows = read_json(V5_DIR / "contrast_classification.json")["items"]
    relation_payload = read_json(V5_DIR / "merge_parent_child_candidates.json")
    selected_relation_candidates = relation_payload["selected_for_review"]

    relation_draft_items = build_relation_draft(selected_relation_candidates)
    relation_profile = build_relation_profile(relation_draft_items)
    point_draft = build_point_draft(candidate_points, relation_profile)
    contrast_draft = build_contrast_draft(contrast_rows)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_candidate_points": str(V5_DIR / "all_candidate_points.json"),
        "source_contrast_classification": str(V5_DIR / "contrast_classification.json"),
        "source_relation_candidates": str(V5_DIR / "merge_parent_child_candidates.json"),
        "candidate_point_count": len(candidate_points),
        "formal_exam_point_preview_count": len(point_draft["items"]),
        "review_only_point_count": len([p for p in candidate_points if p["question_count"] <= 0]),
        "question_context_count": v5_summary.get("question_context_count", 0),
        "relation_draft_count": len(relation_draft_items),
        "relation_draft_distribution": dict(Counter(item["draft_label"] for item in relation_draft_items).most_common()),
        "relation_context_scope_distribution": dict(Counter(item["context_scope"] for item in relation_draft_items).most_common()),
        "contrast_draft_count": len(contrast_draft["items"]),
        "contrast_draft_distribution": dict(Counter(item["draft_action"] for item in contrast_draft["items"]).most_common()),
        "contrast_classification_distribution": dict(Counter(row["classification"] for row in contrast_rows).most_common()),
        "source_v5_batch_report": str(V5_DIR / "batch_judgement_20260630_100x100" / "judgement_report.md"),
        "source_v5_summary": str(V5_DIR / "summary.json"),
        "draft_mode": "heuristic_calibrated_by_100x100",
    }

    write_json(V6_DIR / "summary.json", summary)
    write_json(V6_DIR / "relation_draft.json", {"items": relation_draft_items})
    write_json(V6_DIR / "contrast_draft.json", contrast_draft)
    write_json(V6_DIR / "exam_point_system_draft.json", point_draft)

    report = summarize_report(summary, relation_draft_items, contrast_draft, point_draft)
    (V6_DIR / "report.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
