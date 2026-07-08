"""
Preview v5: build a rule-based structure preview for the full exam-point system.

This script intentionally does not call any external LLM/API. It reads the
clean strong-evidence base from preview_v1 and produces reviewable artifacts:
- all sentence-card seed points are kept as candidates;
- contrast edges are conservatively classified;
- merge / parent-child / sibling relation candidates are recalled, not decided.
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
V1_DIR = HERE / "work" / "preview_v1"
OUT_DIR = HERE / "work" / "preview_v5"
QUESTIONS_DIR = (
    HERE.parent
    / "选项证据生成"
    / "新题解析模块复用"
    / "output"
    / "questions"
)

CONTRAST_SAMPLE_SIZE = 50
RELATION_JUDGEMENT_SAMPLE_PER_TYPE = int(os.getenv("PREVIEW_V5_RELATION_SAMPLE_PER_TYPE", "5"))
CONTRAST_JUDGEMENT_SAMPLE_LIMIT = int(os.getenv("PREVIEW_V5_CONTRAST_JUDGEMENT_SAMPLE_LIMIT", "20"))
MAX_RELATION_CANDIDATES_PER_POINT = int(os.getenv("PREVIEW_V5_MAX_RELATION_CANDIDATES_PER_POINT", "12"))
SELECTED_RELATION_REVIEW_LIMIT = int(os.getenv("PREVIEW_V5_RELATION_REVIEW_LIMIT", "600"))
SELECTED_RELATION_MIN_SCORE = int(os.getenv("PREVIEW_V5_RELATION_MIN_SCORE", "50"))
NEAR_CARD_DISTANCE = 3
ABSORB_NEAR_CARD_DISTANCE = 24
CALIBRATION_RELATION_PAIR_IDS = {
    "v6s_N00302__v6s_N00309",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compact(text: Any, limit: int = 160) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def card_num(card_id: str) -> int | None:
    match = re.search(r"N(\d+)$", str(card_id or ""))
    if not match:
        return None
    return int(match.group(1))


def top_focus(seed: dict[str, Any]) -> str:
    dist = seed.get("focus_type_distribution") or {}
    if not dist:
        return ""
    return max(dist.items(), key=lambda item: item[1])[0]


def pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))


def overlap(a: set[str], b: set[str]) -> set[str]:
    return a & b


def make_edge_key(edge: dict[str, Any]) -> str:
    return "::".join(
        [
            str(edge.get("question_id") or ""),
            str(edge.get("option") or ""),
            str(edge.get("card_id") or ""),
            str(edge.get("role") or ""),
        ]
    )


def load_question_contexts() -> dict[str, dict[str, Any]]:
    contexts: dict[str, dict[str, Any]] = {}
    if not QUESTIONS_DIR.exists():
        return contexts
    for path in sorted(QUESTIONS_DIR.glob("q_*.json")):
        data = read_json(path)
        qid = str(data.get("question_id") or path.stem.replace("q_", ""))
        contexts[qid] = {
            "question_id": qid,
            "section": data.get("section"),
            "question_type": data.get("question_type") or data.get("question_subtype"),
            "stem": data.get("stem") or data.get("question_text") or "",
            "options": data.get("options") or {},
            "answer": data.get("answer") or data.get("detected_answer") or "",
            "validation_status": ((data.get("pipeline") or {}).get("validate") or {}).get("validation_status"),
            "needs_teacher_review": bool((data.get("final") or {}).get("needs_teacher_review")),
        }
    return contexts


def classify_contrast(
    edge: dict[str, Any],
    qid_to_core_cards: dict[str, set[str]],
    question_contexts: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Conservative rule classifier for wrong-option evidence.

    The goal is not to be final. The output separates likely teachable
    confusion from pure exclusion and leaves ambiguous cases for review.
    """
    support_type = str(edge.get("support_type") or "")
    evidence_grade = str(edge.get("evidence_grade") or "")
    evidence_status = str(edge.get("evidence_status") or "")
    focus_type = str(edge.get("focus_type") or "")
    option_text = str(edge.get("option_text") or "")
    quote = str(edge.get("quote") or "")
    qid = str(edge.get("question_id") or "")
    context = (question_contexts or {}).get(qid, {})
    stem = str(context.get("stem") or "")
    has_core_peer = bool(qid_to_core_cards.get(qid))

    stage_words = {"处置", "离析", "融合", "放置", "分层", "整合"}
    risk_words = {"法律风险", "声誉", "运营", "操作风险", "合规风险", "风险"}
    institution_words = {
        "FIU",
        "金融情报机构",
        "金融情报",
        "FATF",
        "金融行动特别工作组",
        "OFAC",
        "海外资产控制办公室",
        "Egmont",
        "埃格蒙特",
        "制裁",
        "SDN",
    }
    option_quote = option_text + " " + quote

    concept_groups = {
        "stage": stage_words,
        "reputation_risk": {"声誉", "名誉"},
        "legal_risk": {"法律风险", "法律责任", "刑事", "民事"},
        "penalty": {"罚款", "惩罚", "处罚", "制裁"},
        "tax": {"逃税", "避税", "税"},
        "fiu": {"FIU", "金融情报机构", "金融情报"},
        "fatf": {"FATF", "金融行动特别工作组"},
        "ofac": {"OFAC", "海外资产控制办公室"},
        "egmont": {"Egmont", "埃格蒙特"},
        "sanctions": {"制裁", "OFAC", "SDN", "冻结", "禁止交易"},
        "due_diligence": {"尽职调查", "CDD", "EDD", "KYCC", "客户身份"},
        "risk_level": {"高风险", "低风险", "降低风险", "增强尽职调查"},
        "str_sar": {"可疑活动报告", "SAR", "报告可疑", "金融情报机构"},
        "subpoena_response": {"传票", "账户", "关闭", "回应", "执法"},
        "structuring": {"分散", "拆分", "低于报告限额", "门槛", "小额"},
        "cross_border_transfer": {"境外", "国外", "汇往", "转账", "汇款"},
    }

    def concept_hits(text: str) -> set[str]:
        return {
            label
            for label, words in concept_groups.items()
            if any(word in text for word in words)
        }

    option_hits = concept_hits(option_text)
    quote_hits = concept_hits(quote)
    shared_hits = option_hits & quote_hits

    def has_any(text: str, words: tuple[str, ...]) -> bool:
        return any(word in text for word in words)

    def is_action_error_or_thin_quote() -> bool:
        """Filter wrong actions that cite broad policy text but are not a concept."""
        if has_any(option_text, ("延迟", "忽略", "吊销执照")):
            return True
        if len(option_text.strip()) <= 16 and re.search(r"第\s*\d+\s*\(?[a-z]?\)?\s*条", option_text, re.I):
            return True
        if option_hits or shared_hits:
            return False
        if quote_hits and len(option_text.strip()) <= 18:
            return True
        return False

    def is_clear_teachable_direct() -> bool:
        if shared_hits:
            return True
        if is_clear_high_value_contrast():
            return True
        text = option_text + quote
        if has_any(text, ("前", "后")) and has_any(text, ("评估", "推出", "开发完成")):
            return True
        if "董事会" in text and has_any(text, ("审批", "监督", "不应参与", "合规政策")):
            return True
        if has_any(text, ("MLRO", "反洗钱报告员")) and has_any(text, ("唯一", "最终责任", "董事会")):
            return True
        if "AMLD" in text and has_any(text, ("成员国", "国内法律法规", "独立")):
            return True
        if "员工" in text and has_any(text, ("奢", "薪水", "生活方式")):
            return True
        return False

    def is_clear_timing_or_responsibility_contrast() -> bool:
        text = option_text + quote
        if has_any(text, ("推出新产品前", "开发完成后", "产品开发完成后")):
            return True
        if "董事会" in text and has_any(text, ("审批", "监督", "不应参与", "合规政策")):
            return True
        if has_any(text, ("MLRO", "反洗钱报告员")) and has_any(text, ("唯一", "最终责任", "董事会")):
            return True
        if "AMLD" in text and has_any(text, ("成员国", "纳入国内", "完全独立")):
            return True
        if has_any(text, ("奢华", "奢侈")) and has_any(text, ("薪水", "不相符")):
            return True
        return False

    def is_clear_numeric_threshold_contrast() -> bool:
        return bool(re.search(r"\d+\s*%", option_text) and re.search(r"\d+\s*%", quote))

    def is_clear_governance_contrast() -> bool:
        text = option_text + quote
        board_signal = has_any(text, ("\u8463\u4e8b\u4f1a", "\u8463\u4e8b"))
        role_boundary = has_any(
            text,
            (
                "CEO",
                "\u9996\u5e2d\u6267\u884c\u5b98",
                "\u5408\u89c4\u804c\u80fd",
                "\u5408\u89c4\u5b98",
                "\u6307\u5b9a\u7684\u53cd\u6d17\u94b1\u5408\u89c4\u5b98",
                "\u76f4\u63a5\u63a5\u89e6",
                "\u62a5\u544a",
                "\u4efb\u547d",
                "\u5ba1\u6279",
                "\u76d1\u7763",
                "\u65e5\u5e38\u7684\u5236\u5ea6\u7ba1\u7406",
                "\u6700\u7ec8\u8d23\u4efb",
                "\u8d1f\u8d23",
                "\u6574\u6539",
                "\u5ba1\u8ba1\u5e08",
                "\u68c0\u67e5\u4eba\u5458",
            ),
        )
        return board_signal and role_boundary

    def is_clear_cdd_continuity_contrast() -> bool:
        text = option_text + quote
        return has_any(text, ("\u4e00\u6b21\u6027\u8c03\u67e5", "\u6301\u7eed\u7684\u5c3d\u804c\u8c03\u67e5", "\u6301\u7eed\u5c3d\u804c\u8c03\u67e5", "\u4e1a\u52a1\u5173\u7cfb")) and "\u8c03\u67e5" in text

    def is_clear_document_destruction_contrast() -> bool:
        text = option_text + quote
        return has_any(text, ("\u9500\u6bc1", "\u6bc1", "\u8c03\u67e5\u901a\u77e5", "\u4e25\u91cd\u7684\u95ee\u9898")) and "\u6587\u4ef6" in text

    def is_clear_legal_consequence_contrast() -> bool:
        text = option_text + quote
        if len(option_text.strip()) <= 8:
            return False
        return has_any(text, ("\u5211\u4e8b\u8bc9\u8bbc", "\u5211\u4e8b\u5904\u7f5a", "\u5de8\u989d\u7f5a\u6b3e", "\u6c11\u4e8b\u8d23\u4efb")) and has_any(text, ("\u7f5a\u6b3e", "\u5904\u7f5a", "\u8d23\u4efb", "\u8bc9\u8bbc"))

    def is_clear_reporting_jurisdiction_contrast() -> bool:
        text = option_text + quote
        return has_any(text, ("\u5f3a\u5236\u6027\u8d27\u5e01\u62a5\u544a\u8981\u6c42", "\u5f3a\u5236\u8d27\u5e01\u5448\u62a5\u8981\u6c42", "\u8d27\u5e01\u62a5\u544a\u8981\u6c42")) and has_any(text, ("\u53f8\u6cd5\u7ba1\u8f96\u533a", "\u79fb\u52a8\u8d44\u91d1", "\u5e38\u89c1"))

    def is_clear_fiu_role_contrast() -> bool:
        text = option_text + quote + stem
        fiu_signal = has_any(text, ("FIU", "\u91d1\u878d\u60c5\u62a5\u673a\u6784", "\u91d1\u878d\u60c5\u62a5"))
        duty_signal = has_any(text, ("\u63a5\u6536\u548c\u5206\u6790", "\u53ef\u7591\u4ea4\u6613\u62a5\u544a", "\u8b66\u65b9\u548c\u6d77\u5173", "\u8d77\u8bc9"))
        return fiu_signal and duty_signal

    def is_clear_correspondent_bank_limitation_contrast() -> bool:
        text = option_text + quote
        return "\u4ee3\u7406\u94f6\u884c" in text and has_any(text, ("\u4e0d\u80fd\u5bf9\u59d4\u6258\u94f6\u884c\u7684\u5ba2\u6237", "KYCC", "\u59d4\u6258\u94f6\u884c\u4ea4\u6613", "STR"))

    def is_clear_confidentiality_contrast() -> bool:
        text = option_text + quote
        return has_any(text, ("\u4fdd\u5bc6", "\u4e0d\u5f97\u544a\u77e5\u5ba2\u6237", "\u5df2\u88ab\u62a5\u544a", "\u63d0\u4ea4\u53ef\u7591\u4ea4\u6613"))

    def is_clear_investigation_cooperation_contrast() -> bool:
        text = option_text + quote
        return has_any(text, ("\u9762\u8c08", "\u4f20\u7968", "\u63d0\u4f9b\u6587\u4ef6", "\u914d\u5408")) and has_any(text, ("\u62d2\u7edd", "\u5b89\u6392", "\u5728\u4e0d\u8981\u6c42\u4f5c\u8bc1\u4f20\u7968\u7684\u60c5\u51b5\u4e0b"))

    def is_clear_sar_reporting_action_contrast() -> bool:
        text = option_text + quote
        report_signal = has_any(text, ("\u53ef\u7591\u6d3b\u52a8\u62a5\u544a", "\u53ef\u7591\u4ea4\u6613\u62a5\u544a", "SAR", "STR"))
        duty_signal = has_any(quote, ("\u5fc5\u987b", "\u8981\u6c42", "\u62a5\u544a", "\u63d0\u4ea4", "\u5411\u6709\u5173\u653f\u5e9c\u673a\u6784", "\u91d1\u878d\u60c5\u62a5\u673a\u6784"))
        weak_action = has_any(option_text, ("\u7ee7\u7eed\u89c2\u5bdf", "\u5b9a\u671f\u5ba1\u67e5", "\u4e0d\u62a5\u544a", "\u6682\u4e0d\u62a5\u544a"))
        return report_signal and duty_signal and weak_action

    def is_clear_subpoena_scope_contrast() -> bool:
        text = option_text + quote
        subpoena_signal = "\u4f20\u7968" in text
        records_signal = has_any(text, ("\u8bb0\u5f55", "\u4fe1\u606f", "\u8d26\u6237", "\u4ee3\u7406\u8d26\u6237", "\u5916\u56fd\u94f6\u884c"))
        scope_signal = has_any(option_text, ("\u4efb\u4f55\u8d26\u6237", "\u5176\u4ed6\u56fd\u5bb6", "\u5916\u56fd\u53f8\u6cd5\u7ba1\u8f96\u533a", "\u9664\u5916"))
        return subpoena_signal and records_signal and scope_signal

    def is_clear_law_enforcement_response_boundary() -> bool:
        text = option_text + quote
        quote_signal = has_any(quote, ("\u6267\u6cd5", "\u9ad8\u7ea7\u7ba1\u7406\u5c42", "\u6307\u5b9a\u4e13\u4eba", "\u56de\u5e94\u6240\u6709\u6267\u6cd5\u8981\u6c42"))
        wrong_sharing_signal = has_any(option_text, ("\u540c\u4e8b\u5206\u4eab", "\u5206\u4eab\u8c03\u67e5", "\u6bcf\u5929\u5904\u7406\u6b64\u5ba2\u6237"))
        return "\u6267\u6cd5" in text and quote_signal and wrong_sharing_signal

    def is_clear_egmont_evidence_boundary() -> bool:
        text = option_text + quote
        return has_any(text, ("\u57c3\u683c\u8499\u7279", "\u8c05\u89e3\u5907\u5fd8\u5f55", "\u8bc1\u636e")) and has_any(text, ("\u4e0d\u662f\u7528\u6765\u83b7\u53d6\u8bc1\u636e", "\u6307\u5411\u8bc1\u636e\u7684\u4fe1\u606f"))

    def is_privacy_data_sharing_boundary() -> bool:
        text = option_text + quote + stem
        return has_any(text, ("\u6570\u636e\u9690\u79c1", "\u9690\u79c1\u6cd5", "\u5ba2\u6237\u6570\u636e", "\u81ea\u7531\u5171\u4eab", "\u8de8\u5883\u5171\u4eab"))

    def is_review_worthy_negative_concept() -> bool:
        text = option_text + quote + stem
        return is_privacy_data_sharing_boundary() or has_any(
            text,
            (
                "\u72ec\u7acb\u5185\u90e8\u5ba1\u8ba1",
                "\u5ba1\u8ba1",
                "\u8463\u4e8b\u4f1a",
                "CEO",
                "\u9996\u5e2d\u6267\u884c\u5b98",
                "\u5408\u89c4\u8ba1\u5212",
                "\u5408\u89c4\u804c\u80fd",
                "\u4f20\u7968",
                "\u641c\u67e5\u4ee4",
                "\u53ef\u7591\u6d3b\u52a8\u62a5\u544a",
                "SAR",
                "STR",
            ),
        )

    def is_cross_institution_mismatch() -> bool:
        text = option_text + quote
        if ("FIU" in stem or "\u91d1\u878d\u60c5\u62a5\u673a\u6784" in stem) and has_any(text, ("OFAC", "\u6d77\u5916\u8d44\u4ea7\u63a7\u5236\u529e\u516c\u5ba4", "\u653f\u5e9c\u548c\u76d1\u7ba1\u673a\u6784", "\u5236\u5b9a\u6cd5\u89c4", "\u9881\u5e03\u6cd5\u5f8b")):
            return True
        if "\u56fa\u6709\u98ce\u9669" in stem and has_any(text, ("\u4ea4\u6613\u76d1\u63a7\u7a0b\u5e8f", "\u76d1\u63a7\u7cfb\u7edf")):
            return True
        if "\u76f8\u4e92\u8bc4\u4f30" in stem and has_any(option_text, ("\u5236\u88c1\u98ce\u9669\u8bc4\u4f30", "\u56fd\u5bb6\u98ce\u9669\u8bc4\u4f30")):
            return True
        if "\u91d1\u878d\u72af\u7f6a\u98ce\u9669" in stem and "\u4e2a\u4eba\u8d23\u4efb" in option_text:
            return True
        return False

    def is_short_label_or_definition_only_mismatch() -> bool:
        if is_clear_high_value_contrast():
            return False
        if len(option_text.strip()) <= 12 and not shared_hits:
            return True
        if has_any(option_text, ("\u4fbf\u5229\u5e97", "\u653f\u5e9c\u652f\u7968")) and has_any(quote, ("\u53ef\u4e3a\u6d88\u8d39\u8005", "\u5151\u73b0\u652f\u7968")):
            return True
        if "\u6536\u5230\u53ef\u7591\u6d3b\u52a8\u62a5\u544a\u4e2d\u7684\u4f20\u7968" in option_text:
            return True
        return False

    def is_clear_high_value_contrast() -> bool:
        return (
            is_clear_timing_or_responsibility_contrast()
            or is_clear_numeric_threshold_contrast()
            or is_clear_governance_contrast()
            or is_clear_cdd_continuity_contrast()
            or is_clear_document_destruction_contrast()
            or is_clear_legal_consequence_contrast()
            or is_clear_reporting_jurisdiction_contrast()
            or is_clear_fiu_role_contrast()
            or is_clear_correspondent_bank_limitation_contrast()
            or is_clear_confidentiality_contrast()
            or is_clear_investigation_cooperation_contrast()
            or is_clear_sar_reporting_action_contrast()
            or is_clear_subpoena_scope_contrast()
            or is_clear_law_enforcement_response_boundary()
            or is_clear_egmont_evidence_boundary()
        )

    def is_clear_reversal() -> bool:
        lowering = any(word in option_text for word in ("降低", "减少", "减轻"))
        raising = any(word in quote for word in ("高风险", "增强", "特别关注", "提高"))
        increasing = any(word in option_text for word in ("增加", "扩大"))
        decreasing = any(word in quote for word in ("减少", "终止", "降低"))
        return (lowering and raising) or (increasing and decreasing)

    def is_option_quote_misaligned() -> bool:
        if not option_hits or not quote_hits:
            return False
        if option_hits & quote_hits:
            return False
        if "subpoena_response" in option_hits and "str_sar" in quote_hits:
            return True
        return False

    def is_teachable_negative_conflict() -> bool:
        if any(word in option_quote for word in stage_words):
            return True
        if "tax" in (option_hits | quote_hits) and {"逃税", "避税"} & set(re.findall(r"逃税|避税", option_quote)):
            return True
        if "间接" in stem and "penalty" in (option_hits | quote_hits):
            return True
        if shared_hits and not is_clear_reversal():
            return True
        return False

    def is_plain_reversal_without_stable_teaching_unit() -> bool:
        text = option_text + quote
        if quote and has_any(option_text, ("\u5141\u8bb8", "\u53ef\u4ee5", "\u7ef4\u62a4", "\u5fc5\u987b\u7ecf\u8fc7", "\u8fbe\u5230", "\u9650\u989d")) and has_any(quote, ("\u7981\u6b62", "\u4e0d\u5f97", "\u8981\u6c42\u51bb\u7ed3")):
            return True
        if "\u7acb\u5373\u5173\u95ed" in option_text and has_any(quote, ("\u9500\u6237\u6216\u4fdd\u7559\u8d26\u6237", "\u989d\u5916\u901a\u77e5")):
            return True
        if ("PEP" in text or "\u653f\u6cbb\u516c\u4f17\u4eba\u7269" in text) and "\u9ad8\u98ce\u9669\u56fd\u5bb6" in option_text and "\u9ad8\u98ce\u9669\u56fd\u5bb6" not in quote:
            return True
        if has_any(option_text, ("\u8eab\u4efd\u8bc1\u660e", "\u8eab\u4efd\u8bc6\u522b", "\u533f\u540d", "\u5f00\u6237")) and has_any(quote, ("\u6807\u51c6\u8eab\u4efd\u8bc6\u522b\u7a0b\u5e8f", "\u575a\u6301\u533f\u540d", "\u51b3\u4e0d\u5141\u8bb8")):
            return True
        if "\u4ec5" in option_text and has_any(quote, ("\u5e76\u6ca1\u6709", "\u5f88\u96be\u5bdf\u89c9\u5f02\u5e38\u6a21\u5f0f")):
            return True
        return False

    if evidence_grade == "negative_direct" or evidence_status == "conflict":
        if support_type in {"indirect", "context"}:
            if option_hits or quote_hits:
                return {
                    "classification": "needs_review",
                    "include_in_exam_point_count": False,
                    "reason": "negative/conflict 证据来自间接或背景材料，涉及教材概念但不自动计入。",
                }
            return {
                "classification": "pure_exclusion",
                "include_in_exam_point_count": False,
                    "reason": "negative/conflict 且证据偏间接，先作为追溯性排除证据。",
                }
        if is_plain_reversal_without_stable_teaching_unit():
            return {
                "classification": "needs_review",
                "include_in_exam_point_count": False,
                "reason": "错误项主要被原文直接反证，暂不自动计入考点，保留复核。",
            }
        if has_core_peer and is_clear_high_value_contrast():
            return {
                "classification": "confusing_contrast",
                "include_in_exam_point_count": True,
                "reason": "negative/conflict 形成清晰的时点、职责或法规层级辨析，可作为易错/辨析考点。",
            }
        if has_core_peer and is_teachable_negative_conflict():
            return {
                "classification": "confusing_contrast",
                "include_in_exam_point_count": True,
                "reason": "negative/conflict 证据虽为反向证据，但错误项本身承载可教学概念，可用于概念辨析。",
            }
        if "cross_border_transfer" in option_hits and "structuring" in quote_hits:
            return {
                "classification": "needs_review",
                "include_in_exam_point_count": False,
                "reason": "错误项涉及交易红旗的一部分，但 quote 指向更完整链条，先保留复核。",
            }
        if has_any(option_quote, ("身份证明", "身份识别", "匿名", "开户")):
            return {
                "classification": "needs_review",
                "include_in_exam_point_count": False,
                "reason": "错误项涉及客户身份识别/匿名开户边界，但当前规则不能确认是否为有效辨析，保留复核。",
            }
        if has_core_peer and (option_hits or quote_hits) and not is_clear_reversal():
            return {
                "classification": "needs_review",
                "include_in_exam_point_count": False,
                "reason": "negative/conflict 证据涉及教材概念，但规则无法确认是否为有效混淆，保留复核。",
            }
        if is_review_worthy_negative_concept():
            return {
                "classification": "needs_review",
                "include_in_exam_point_count": False,
                "reason": "negative/conflict 涉及职责、审计、传票或报告等可复核概念，先保留待审。",
            }
        return {
            "classification": "pure_exclusion",
            "include_in_exam_point_count": False,
            "reason": "negative_direct/conflict 更像用原文反证选项表述，不先计入正式考点。",
        }

    if support_type == "direct" and evidence_status == "direct":
        if is_cross_institution_mismatch() or is_short_label_or_definition_only_mismatch():
            return {
                "classification": "needs_review",
                "include_in_exam_point_count": False,
                "reason": "错误项与原文存在机构/对象/短标签错位，先保留复核。",
            }
        if is_plain_reversal_without_stable_teaching_unit():
            return {
                "classification": "needs_review",
                "include_in_exam_point_count": False,
                "reason": "错误项主要被原文直接反证，暂不自动计入考点，保留复核。",
            }
        if is_option_quote_misaligned():
            return {
                "classification": "needs_review",
                "include_in_exam_point_count": False,
                "reason": "错误项与 quote 均有教材概念，但概念焦点不一致，先保留复核。",
            }
        if has_any(option_text, ("延迟", "忽略", "吊销执照")):
            return {
                "classification": "needs_review",
                "include_in_exam_point_count": False,
                "reason": "错误项是处置动作错误，虽然命中直接原文概念，但 quote 不能稳定支撑一个教材知识点。",
            }
        if is_action_error_or_thin_quote() and not is_clear_teachable_direct():
            return {
                "classification": "needs_review",
                "include_in_exam_point_count": False,
                "reason": "错误项更像处置动作错误或薄弱反证，quote 不能稳定支撑一个教材概念辨析。",
            }
        return {
            "classification": "confusing_contrast",
            "include_in_exam_point_count": True,
            "reason": "错误项有直接教材依据，且与同题正确项并列，优先视为可教学的概念混淆。",
        }

    if support_type == "negative" and has_core_peer:
        if is_clear_high_value_contrast():
            return {
                "classification": "confusing_contrast",
                "include_in_exam_point_count": True,
                "reason": "错误项与原文形成清晰的时点、职责或法规层级辨析，可计入考点标签。",
            }
        if is_plain_reversal_without_stable_teaching_unit():
            return {
                "classification": "needs_review",
                "include_in_exam_point_count": False,
                "reason": "错误项主要被原文直接反证，暂不自动计入考点，保留复核。",
            }
        if "不合作国家和地区" in option_quote and has_any(quote, ("画上句号", "结束")):
            return {
                "classification": "needs_review",
                "include_in_exam_point_count": False,
                "reason": "错误项涉及历史名单机制，quote 是机制结束/历史变化，需人工确认是否形成稳定考点。",
            }
        if any(word in option_quote for word in stage_words):
            return {
                "classification": "confusing_contrast",
                "include_in_exam_point_count": True,
                "reason": "错误项涉及洗钱阶段等高价值概念辨析，暂计为有效混淆。",
            }
        if any(word in option_quote for word in risk_words | institution_words):
            return {
                "classification": "confusing_contrast" if shared_hits and not is_clear_reversal() else "needs_review",
                "include_in_exam_point_count": bool(shared_hits and not is_clear_reversal()),
                "reason": (
                    "错误项与原文共享明确教材概念，暂计为有效混淆。"
                    if shared_hits and not is_clear_reversal()
                    else "错误项涉及可教学概念，但 support_type=negative，需校准是否为有效混淆。"
                ),
            }
        return {
            "classification": "needs_review",
            "include_in_exam_point_count": False,
            "reason": "错误项有反向证据，但无法仅凭规则判断是否具备教学混淆价值。",
        }

    if support_type in {"indirect", "context"}:
        return {
            "classification": "needs_review",
            "include_in_exam_point_count": False,
            "reason": "错误项证据偏间接/背景，暂不计入，等待人工或 LLM 复核。",
        }

    if focus_type and focus_type != "other" and has_core_peer:
        return {
            "classification": "needs_review",
            "include_in_exam_point_count": False,
            "reason": "focus_type 提示可能相关，但规则证据不足，暂缓。",
        }

    return {
        "classification": "pure_exclusion",
        "include_in_exam_point_count": False,
        "reason": "未发现稳定的教学混淆信号，先按普通排除项处理。",
    }


def classify_all_contrast(
    strong_edges: list[dict[str, Any]],
    question_contexts: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    qid_to_core_cards: dict[str, set[str]] = defaultdict(set)
    for edge in strong_edges:
        if edge.get("role") == "core":
            qid_to_core_cards[str(edge.get("question_id") or "")].add(str(edge.get("card_id") or ""))

    rows = []
    by_key: dict[str, dict[str, Any]] = {}
    for edge in strong_edges:
        if edge.get("role") != "contrast":
            continue
        decision = classify_contrast(edge, qid_to_core_cards, question_contexts)
        row = {
            "edge_key": make_edge_key(edge),
            "question_id": edge.get("question_id"),
            "section": edge.get("section"),
            "option": edge.get("option"),
            "option_text": edge.get("option_text"),
            "card_id": edge.get("card_id"),
            "quote": edge.get("quote"),
            "support_type": edge.get("support_type"),
            "evidence_grade": edge.get("evidence_grade"),
            "evidence_status": edge.get("evidence_status"),
            "focus_type": edge.get("focus_type"),
            **decision,
        }
        rows.append(row)
        by_key[row["edge_key"]] = row

    rows.sort(key=lambda item: (item["classification"], str(item["question_id"]), str(item["option"]), str(item["card_id"])))
    return rows, by_key


def select_contrast_sample(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["classification"]].append(row)

    target_order = ["confusing_contrast", "needs_review", "pure_exclusion"]
    base_targets = {
        "confusing_contrast": 18,
        "needs_review": 20,
        "pure_exclusion": 12,
    }

    sample: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(row: dict[str, Any]) -> None:
        key = row["edge_key"]
        if key in seen or len(sample) >= CONTRAST_SAMPLE_SIZE:
            return
        sample.append(row)
        seen.add(key)

    for cls in target_order:
        rows_for_cls = grouped.get(cls, [])
        support_seen: set[tuple[str, str]] = set()
        for row in rows_for_cls:
            sig = (str(row.get("support_type")), str(row.get("evidence_grade")))
            if sig not in support_seen:
                add(row)
                support_seen.add(sig)
            if sum(1 for item in sample if item["classification"] == cls) >= base_targets[cls]:
                break
        for row in rows_for_cls:
            if sum(1 for item in sample if item["classification"] == cls) >= base_targets[cls]:
                break
            add(row)

    for row in rows:
        if len(sample) >= CONTRAST_SAMPLE_SIZE:
            break
        add(row)
    return sample


def build_candidate_points(
    seed_points: list[dict[str, Any]],
    strong_edges: list[dict[str, Any]],
    contrast_by_key: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    edge_rows_by_card: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in strong_edges:
        edge_rows_by_card[str(edge.get("card_id") or "")].append(edge)

    items = []
    for idx, seed in enumerate(seed_points, start=1):
        card_id = seed["card_id"]
        edges = edge_rows_by_card.get(card_id, [])

        core_qids: set[str] = set()
        confusing_qids: set[str] = set()
        needs_review_qids: set[str] = set()
        pure_exclusion_qids: set[str] = set()
        raw_contrast_qids: set[str] = set()

        for edge in edges:
            qid = str(edge.get("question_id") or "")
            if edge.get("role") == "core":
                core_qids.add(qid)
            elif edge.get("role") == "contrast":
                raw_contrast_qids.add(qid)
                row = contrast_by_key.get(make_edge_key(edge))
                cls = (row or {}).get("classification")
                if cls == "confusing_contrast":
                    confusing_qids.add(qid)
                elif cls == "pure_exclusion":
                    pure_exclusion_qids.add(qid)
                else:
                    needs_review_qids.add(qid)

        v5_qids = core_qids | confusing_qids
        tags = []
        if confusing_qids:
            tags.append("易错/辨析")
        review_flags = []
        if needs_review_qids:
            review_flags.append("has_contrast_needs_review")
        if not v5_qids:
            review_flags.append("no_counted_core_or_confusing_contrast")

        formal_status = "candidate_not_final" if v5_qids else "review_only_not_counted"
        point_type = "高频考点" if len(v5_qids) >= 3 else "普通考点"
        if not v5_qids:
            point_type = "待审候选"

        items.append(
            {
                "id": f"EP5-{idx:04d}",
                "source_seed_id": seed.get("id"),
                "card_id": card_id,
                "title_placeholder": compact(seed.get("seed_title"), 80),
                "quote": (seed.get("card") or {}).get("quote"),
                "card": seed.get("card") or {},
                "sections": seed.get("sections") or {},
                "cross_chapter": seed.get("cross_chapter"),
                "top_focus_type": top_focus(seed),
                "raw_question_ids": seed.get("question_ids") or [],
                "raw_question_count": seed.get("question_count") or 0,
                "raw_core_question_count": seed.get("core_question_count") or 0,
                "raw_contrast_question_count": seed.get("contrast_question_count") or 0,
                "question_ids": sorted(v5_qids),
                "question_count": len(v5_qids),
                "core_question_ids": sorted(core_qids),
                "core_question_count": len(core_qids),
                "confusing_contrast_question_ids": sorted(confusing_qids),
                "confusing_contrast_question_count": len(confusing_qids),
                "needs_review_contrast_question_ids": sorted(needs_review_qids),
                "needs_review_contrast_question_count": len(needs_review_qids),
                "pure_exclusion_question_ids": sorted(pure_exclusion_qids),
                "pure_exclusion_question_count": len(pure_exclusion_qids),
                "point_type": point_type,
                "is_high_frequency": len(v5_qids) >= 3,
                "tags": tags,
                "review_flags": review_flags,
                "parent_id": None,
                "children": [],
                "subtree_question_count": len(v5_qids),
                "status": formal_status,
            }
        )

    items.sort(key=lambda item: (-item["question_count"], item["card_id"]))
    return items


def relation_role(card_id: str, qid: str, q_card_roles: dict[str, dict[str, set[str]]]) -> str:
    roles = q_card_roles.get(qid, {}).get(card_id, set())
    if roles == {"core"}:
        return "core"
    if roles == {"contrast"}:
        return "contrast"
    if roles:
        return "mixed"
    return ""


def add_candidate(
    pairs: dict[tuple[str, str], dict[str, Any]],
    a: str,
    b: str,
    reason: str,
    score: int,
    detail: dict[str, Any] | None = None,
) -> None:
    if a == b:
        return
    key = pair_key(a, b)
    item = pairs.setdefault(
        key,
        {
            "pair_id": f"{key[0]}__{key[1]}",
            "card_a": key[0],
            "card_b": key[1],
            "score": 0,
            "reasons": [],
            "details": [],
        },
    )
    item["score"] += score
    if reason not in item["reasons"]:
        item["reasons"].append(reason)
    if detail:
        item["details"].append(detail)


def classify_relation_candidate(pair: dict[str, Any], points_by_card: dict[str, dict[str, Any]]) -> str:
    reasons = set(pair.get("reasons") or [])
    a = points_by_card[pair["card_a"]]
    b = points_by_card[pair["card_b"]]

    if "same_option_multi_card" in reasons and pair.get("near_card_distance") in {0, 1, 2}:
        return "merge_same_point_candidate"
    if "same_option_multi_card" in reasons:
        return "merge_or_parent_child_candidate"
    if "core_contrast_same_question" in reasons:
        return "sibling_under_parent_candidate"
    if "high_frequency_absorption" in reasons:
        high = a if a["question_count"] >= b["question_count"] else b
        low = b if high is a else a
        if high["question_count"] >= 3 and low["question_count"] < 3:
            return "merge_or_parent_child_candidate"
    if "same_question_core_core" in reasons:
        return "merge_or_parent_child_candidate"
    if "near_card_id_same_section" in reasons:
        return "parent_child_or_keep_separate_candidate"
    return "needs_review_candidate"


def add_soft_focus_signals(pairs: dict[tuple[str, str], dict[str, Any]], points_by_card: dict[str, dict[str, Any]]) -> None:
    for pair in pairs.values():
        a = points_by_card[pair["card_a"]]
        b = points_by_card[pair["card_b"]]
        fa = a.get("top_focus_type") or ""
        fb = b.get("top_focus_type") or ""
        if fa and fa == fb and fa != "missing":
            if "same_focus_type_soft" not in pair["reasons"]:
                pair["reasons"].append("same_focus_type_soft")
            pair["score"] += 5
            pair["details"].append({"same_focus_type": fa})


def build_relation_candidates(
    candidate_points: list[dict[str, Any]],
    strong_edges: list[dict[str, Any]],
    contrast_by_key: dict[str, dict[str, Any]],
    question_contexts: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    points_by_card = {point["card_id"]: point for point in candidate_points}
    seeds = list(points_by_card)
    q_card_roles: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    q_option_cards: dict[tuple[str, str], set[str]] = defaultdict(set)
    q_option_roles: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

    for edge in strong_edges:
        cid = str(edge.get("card_id") or "")
        if cid not in points_by_card:
            continue
        role = str(edge.get("role") or "")
        if role == "contrast":
            row = contrast_by_key.get(make_edge_key(edge))
            if not row or row.get("classification") != "confusing_contrast":
                continue
        qid = str(edge.get("question_id") or "")
        option = str(edge.get("option") or "")
        q_card_roles[qid][cid].add(role)
        q_option_cards[(qid, option)].add(cid)
        q_option_roles[(qid, option)][cid].add(role)

    pairs: dict[tuple[str, str], dict[str, Any]] = {}

    for (qid, option), cards in q_option_cards.items():
        cards_sorted = sorted(cards)
        if len(cards_sorted) < 2:
            continue
        for i, a in enumerate(cards_sorted):
            for b in cards_sorted[i + 1 :]:
                context = question_contexts.get(qid, {})
                add_candidate(
                    pairs,
                    a,
                    b,
                    "same_option_multi_card",
                    70,
                    {
                        "question_id": qid,
                        "option": option,
                        "roles": {
                            a: sorted(q_option_roles[(qid, option)].get(a, [])),
                            b: sorted(q_option_roles[(qid, option)].get(b, [])),
                        },
                        "stem": compact(context.get("stem"), 260),
                        "option_text": compact((context.get("options") or {}).get(option), 180),
                        "options": {
                            label: compact(text, 120)
                            for label, text in (context.get("options") or {}).items()
                        },
                        "answer": context.get("answer"),
                        "question_type": context.get("question_type"),
                    },
                )

    for qid, card_roles in q_card_roles.items():
        cards_sorted = sorted(card_roles)
        for i, a in enumerate(cards_sorted):
            for b in cards_sorted[i + 1 :]:
                role_a = relation_role(a, qid, q_card_roles)
                role_b = relation_role(b, qid, q_card_roles)
                if role_a == "contrast" and role_b == "contrast":
                    continue
                reason = "core_contrast_same_question" if "contrast" in {role_a, role_b} else "same_question_core_core"
                context = question_contexts.get(qid, {})
                detail = {
                    "question_id": qid,
                    "role_a": role_a,
                    "role_b": role_b,
                    "stem": compact(context.get("stem"), 260),
                    "answer": context.get("answer"),
                    "question_type": context.get("question_type"),
                    "options": {
                        label: compact(text, 120)
                        for label, text in (context.get("options") or {}).items()
                    },
                }
                if role_a == "contrast" or role_b == "contrast":
                    contrast_edges = [
                        edge
                        for edge in strong_edges
                        if str(edge.get("question_id") or "") == qid
                        and str(edge.get("card_id") or "") in {a, b}
                        and edge.get("role") == "contrast"
                    ]
                    detail["contrast_classifications"] = [
                        {
                            "card_id": edge.get("card_id"),
                            "option": edge.get("option"),
                            "option_text": edge.get("option_text"),
                            "classification": (contrast_by_key.get(make_edge_key(edge)) or {}).get("classification"),
                            "reason": (contrast_by_key.get(make_edge_key(edge)) or {}).get("reason"),
                        }
                        for edge in contrast_edges
                    ]
                add_candidate(
                    pairs,
                    a,
                    b,
                    reason,
                    45 if reason == "same_question_core_core" else 55,
                    detail,
                )

    numbered = []
    for point in candidate_points:
        num = card_num(point["card_id"])
        if num is not None:
            numbered.append((num, point))
    numbered.sort(key=lambda item: item[0])

    for i, (num_a, point_a) in enumerate(numbered):
        j = i + 1
        while j < len(numbered):
            num_b, point_b = numbered[j]
            distance = num_b - num_a
            if distance > NEAR_CARD_DISTANCE:
                break
            same_sections = sorted(set(point_a["sections"]) & set(point_b["sections"]))
            if same_sections:
                add_candidate(
                    pairs,
                    point_a["card_id"],
                    point_b["card_id"],
                    "near_card_id_same_section",
                    20,
                    {"distance": distance, "same_sections": same_sections},
                )
            j += 1

    high_points = [point for point in candidate_points if point["question_count"] >= 3]
    low_points = [point for point in candidate_points if point["question_count"] < 3]
    for low in low_points:
        candidates = []
        low_sections = set(low["sections"])
        low_focus = low.get("top_focus_type") or ""
        low_num = card_num(low["card_id"])
        for high in high_points:
            same_sections = sorted(low_sections & set(high["sections"]))
            if not same_sections:
                continue
            same_focus = low_focus and low_focus == high.get("top_focus_type")
            high_num = card_num(high["card_id"])
            distance = abs(high_num - low_num) if high_num is not None and low_num is not None else None
            if not same_focus and (distance is None or distance > ABSORB_NEAR_CARD_DISTANCE):
                continue
            route_score = 25 + (20 if same_focus else 0)
            if distance is not None:
                if distance <= 3:
                    route_score += 15
                elif distance <= ABSORB_NEAR_CARD_DISTANCE:
                    route_score += max(0, 10 - distance // 4)
            candidates.append((route_score, distance if distance is not None else 999999, high, same_sections, same_focus))
        candidates.sort(key=lambda item: (-item[0], item[1], item[2]["card_id"]))
        for route_score, distance, high, same_sections, same_focus in candidates[:5]:
            add_candidate(
                pairs,
                low["card_id"],
                high["card_id"],
                "high_frequency_absorption",
                route_score,
                {
                    "low_card_id": low["card_id"],
                    "high_card_id": high["card_id"],
                    "same_sections": same_sections,
                    "same_focus": same_focus,
                    "distance": None if distance == 999999 else distance,
                },
            )

    add_soft_focus_signals(pairs, points_by_card)

    relation_items = []
    per_card_counts: Counter[str] = Counter()
    for pair in pairs.values():
        nums = [card_num(pair["card_a"]), card_num(pair["card_b"])]
        if nums[0] is not None and nums[1] is not None:
            pair["near_card_distance"] = abs(nums[0] - nums[1])
        else:
            pair["near_card_distance"] = None
        pair["relation_candidate_type"] = classify_relation_candidate(pair, points_by_card)
        pair["card_a_summary"] = summarize_point(points_by_card[pair["card_a"]])
        pair["card_b_summary"] = summarize_point(points_by_card[pair["card_b"]])
        relation_items.append(pair)

    relation_items.sort(key=lambda item: (-item["score"], item["relation_candidate_type"], item["card_a"], item["card_b"]))

    for item in relation_items:
        item["selected_for_review"] = False

    selected: list[dict[str, Any]] = []
    selected_pair_ids: set[str] = set()

    def try_select(item: dict[str, Any], min_score: int) -> bool:
        if len(selected) >= SELECTED_RELATION_REVIEW_LIMIT:
            return False
        if item["pair_id"] in selected_pair_ids:
            return False
        if item["score"] < min_score:
            return False
        a, b = item["card_a"], item["card_b"]
        if points_by_card[a]["question_count"] <= 0 or points_by_card[b]["question_count"] <= 0:
            return False
        if per_card_counts[a] >= MAX_RELATION_CANDIDATES_PER_POINT or per_card_counts[b] >= MAX_RELATION_CANDIDATES_PER_POINT:
            return False
        item["selected_for_review"] = True
        selected.append(item)
        selected_pair_ids.add(item["pair_id"])
        per_card_counts[a] += 1
        per_card_counts[b] += 1
        return True

    def force_select(item: dict[str, Any]) -> bool:
        if item["pair_id"] in selected_pair_ids:
            return False
        a, b = item["card_a"], item["card_b"]
        if points_by_card[a]["question_count"] <= 0 or points_by_card[b]["question_count"] <= 0:
            return False
        item["selected_for_review"] = True
        selected.append(item)
        selected_pair_ids.add(item["pair_id"])
        per_card_counts[a] += 1
        per_card_counts[b] += 1
        return True

    quota_plan = [
        ("merge_same_point_candidate", 120, 50),
        ("sibling_under_parent_candidate", 110, 50),
        ("parent_child_or_keep_separate_candidate", 60, 20),
        ("merge_or_parent_child_candidate", 310, 70),
    ]
    for relation_type, quota, min_score in quota_plan:
        picked = 0
        for item in relation_items:
            if item["relation_candidate_type"] != relation_type:
                continue
            if relation_type == "parent_child_or_keep_separate_candidate":
                # Near-card-only pairs are noisy. Keep them in the full file, but
                # only sample those with the extra focus signal into the main
                # review queue.
                if "same_focus_type_soft" not in set(item.get("reasons") or []):
                    continue
            if picked >= quota:
                break
            if try_select(item, min_score):
                picked += 1

    for item in relation_items:
        if len(selected) >= SELECTED_RELATION_REVIEW_LIMIT:
            break
        try_select(item, SELECTED_RELATION_MIN_SCORE)

    for item in relation_items:
        if item["pair_id"] in CALIBRATION_RELATION_PAIR_IDS:
            force_select(item)

    return relation_items, selected


def summarize_point(point: dict[str, Any]) -> dict[str, Any]:
    return {
        "card_id": point["card_id"],
        "title_placeholder": compact(point.get("title_placeholder"), 70),
        "question_count": point.get("question_count"),
        "core_question_count": point.get("core_question_count"),
        "confusing_contrast_question_count": point.get("confusing_contrast_question_count"),
        "point_type": point.get("point_type"),
        "tags": point.get("tags") or [],
        "top_focus_type": point.get("top_focus_type"),
        "quote": compact(point.get("quote"), 140),
    }


def build_components(selected_pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    component_edge_types = {
        "merge_same_point_candidate",
        "merge_or_parent_child_candidate",
        "sibling_under_parent_candidate",
    }
    for pair in selected_pairs:
        if pair.get("relation_candidate_type") in component_edge_types:
            union(pair["card_a"], pair["card_b"])

    groups: dict[str, set[str]] = defaultdict(set)
    pairs_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in selected_pairs:
        if pair.get("relation_candidate_type") not in component_edge_types:
            continue
        root = find(pair["card_a"])
        groups[root].update([pair["card_a"], pair["card_b"]])
        pairs_by_group[root].append(pair)

    components = []
    for idx, (root, cards) in enumerate(groups.items(), start=1):
        pairs = pairs_by_group[root]
        components.append(
            {
                "component_id": f"V5C-{idx:04d}",
                "card_ids": sorted(cards),
                "card_count": len(cards),
                "pair_count": len(pairs),
                "max_score": max(pair["score"] for pair in pairs),
                "relation_candidate_types": dict(Counter(pair["relation_candidate_type"] for pair in pairs).most_common()),
                "reasons": dict(Counter(reason for pair in pairs for reason in pair.get("reasons", [])).most_common()),
                "sample_pairs": [
                    {
                        "pair_id": pair["pair_id"],
                        "score": pair["score"],
                        "relation_candidate_type": pair["relation_candidate_type"],
                        "reasons": pair["reasons"],
                        "a": pair["card_a_summary"]["title_placeholder"],
                        "b": pair["card_b_summary"]["title_placeholder"],
                    }
                    for pair in sorted(pairs, key=lambda item: -item["score"])[:8]
                ],
                "status": "candidate_component_not_final",
            }
        )
    components.sort(key=lambda item: (-item["max_score"], -item["card_count"], item["component_id"]))
    return components


def build_exam_point_preview(candidate_points: list[dict[str, Any]], relation_candidates: list[dict[str, Any]]) -> dict[str, Any]:
    relations_by_card: dict[str, list[str]] = defaultdict(list)
    for pair in relation_candidates:
        if not pair.get("selected_for_review"):
            continue
        relations_by_card[pair["card_a"]].append(pair["pair_id"])
        relations_by_card[pair["card_b"]].append(pair["pair_id"])

    points = []
    for point in candidate_points:
        if point["question_count"] <= 0:
            continue
        points.append(
            {
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
                "relation_candidate_pair_ids": relations_by_card.get(point["card_id"], [])[:20],
                "review_status": "structure_preview_not_final",
            }
        )
    return {
        "schema_version": "preview_v5_structure_preview",
        "note": "This is a formal-counted structure preview. question_count=0 review-only points are written separately.",
        "items": points,
    }


def build_review_only_points(candidate_points: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    for point in candidate_points:
        if point["question_count"] > 0:
            continue
        items.append(
            {
                "id": point["id"],
                "card_id": point["card_id"],
                "title": point["title_placeholder"],
                "quote": point["quote"],
                "raw_question_ids": point["raw_question_ids"],
                "raw_question_count": point["raw_question_count"],
                "needs_review_contrast_question_ids": point["needs_review_contrast_question_ids"],
                "pure_exclusion_question_ids": point["pure_exclusion_question_ids"],
                "review_flags": point["review_flags"],
                "status": "review_only_not_counted",
                "note": "This point is preserved for traceability but is not counted as a formal exam point unless review promotes its contrast evidence.",
            }
        )
    return {
        "schema_version": "preview_v5_review_only_points",
        "items": items,
    }


def build_llm_relation_judgement_sample(selected_pairs: list[dict[str, Any]], per_type: int = 5) -> dict[str, Any]:
    relation_order = [
        "merge_same_point_candidate",
        "merge_or_parent_child_candidate",
        "sibling_under_parent_candidate",
        "parent_child_or_keep_separate_candidate",
    ]
    balanced_pairs: list[dict[str, Any]] = []
    seen_pair_ids: set[str] = set()

    def has_question_context(pair: dict[str, Any]) -> bool:
        for detail in pair.get("details", []):
            if "question_id" in detail:
                return True
        return False

    for relation_type in relation_order:
        picked = 0
        for pair in selected_pairs:
            if pair.get("relation_candidate_type") != relation_type:
                continue
            if pair["pair_id"] in seen_pair_ids:
                continue
            if not has_question_context(pair) and relation_type != "parent_child_or_keep_separate_candidate":
                continue
            balanced_pairs.append(pair)
            seen_pair_ids.add(pair["pair_id"])
            picked += 1
            if picked >= per_type:
                break

    items = []
    for pair in balanced_pairs:
        context_details = []
        for detail in pair.get("details", []):
            if "question_id" not in detail:
                continue
            context_details.append(
                {
                    "question_id": detail.get("question_id"),
                    "question_type": detail.get("question_type"),
                    "stem": detail.get("stem"),
                    "option": detail.get("option"),
                    "option_text": detail.get("option_text"),
                    "options": detail.get("options") or {},
                    "answer": detail.get("answer"),
                    "role_a": detail.get("role_a"),
                    "role_b": detail.get("role_b"),
                    "roles": detail.get("roles"),
                    "contrast_classifications": detail.get("contrast_classifications", []),
                }
            )
            if len(context_details) >= 3:
                break
        card_relation_contexts = []
        for detail in pair.get("details", []):
            if "question_id" in detail:
                continue
            card_relation_contexts.append(
                {
                    "distance": detail.get("distance"),
                    "same_sections": detail.get("same_sections", []),
                    "same_focus": detail.get("same_focus"),
                    "low_card_id": detail.get("low_card_id"),
                    "high_card_id": detail.get("high_card_id"),
                }
            )
        items.append(
            {
                "pair_id": pair["pair_id"],
                "candidate_type": pair["relation_candidate_type"],
                "score": pair["score"],
                "reasons": pair["reasons"],
                "context_scope": "question_context" if context_details else "card_only_nearby_text",
                "focus_type_note": "focus_type is a weak signal only; do not use it as a hard boundary.",
                "card_a": pair["card_a_summary"],
                "card_b": pair["card_b_summary"],
                "question_contexts": context_details,
                "card_relation_contexts": card_relation_contexts,
                "allowed_labels": [
                    "merge_same_point",
                    "parent_child",
                    "sibling_under_parent",
                    "keep_separate",
                    "needs_review",
                ],
                "instruction": (
                    "Judge whether these two sentence-card points should be merged, linked as parent/child, "
                    "treated as siblings under a virtual parent, kept separate, or reviewed by a human. "
                    "Use merge_same_point only when the two cards are true paraphrases or repeated wording of the same atomic fact. "
                    "If they are separate clauses/items under the same rule, prefer sibling_under_parent. "
                    "If one card is the general rule and the other is a concrete expansion or sub-rule, prefer parent_child. "
                    "Same option / multiple cards is evidence only, not a conclusion. "
                    "When context_scope is card_only_nearby_text, judge only from the two card quotes and nearby-text signal."
                ),
            }
        )
    return {
        "schema_version": "preview_v5_llm_relation_judgement_sample",
        "llm_used_to_create_this_file": False,
        "sampling_policy": f"balanced {per_type} per relation candidate type; card-only near-text samples are explicitly scoped",
        "items": items,
    }


def build_llm_contrast_judgement_sample(
    contrast_rows: list[dict[str, Any]],
    question_contexts: dict[str, dict[str, Any]],
    limit: int = 20,
) -> dict[str, Any]:
    rows = [row for row in contrast_rows if row.get("classification") == "needs_review"]
    items = []
    seen_questions: set[str] = set()

    def add(row: dict[str, Any]) -> None:
        context = question_contexts.get(str(row.get("question_id") or ""), {})
        option = str(row.get("option") or "")
        items.append(
            {
                "edge_key": row["edge_key"],
                "question_id": row.get("question_id"),
                "question_type": context.get("question_type"),
                "stem": context.get("stem"),
                "options": context.get("options") or {},
                "answer": context.get("answer"),
                "option": option,
                "option_text": row.get("option_text") or (context.get("options") or {}).get(option),
                "card_id": row.get("card_id"),
                "quote": row.get("quote"),
                "support_type": row.get("support_type"),
                "evidence_grade": row.get("evidence_grade"),
                "evidence_status": row.get("evidence_status"),
                "focus_type": row.get("focus_type"),
                "current_classification": row.get("classification"),
                "current_reason": row.get("reason"),
                "focus_type_note": "focus_type is a weak signal only; do not use it as a hard boundary.",
                "allowed_labels": [
                    "confusing_contrast",
                    "pure_exclusion",
                    "needs_review",
                ],
                "instruction": (
                    "Judge whether this wrong-option evidence is a teachable conceptual confusion, a pure exclusion/negative proof, "
                    "or still needs human review. Choose confusing_contrast only when the wrong option maps to a clear textbook concept, "
                    "stage, institution, risk type, or duty and creates meaningful confusion with the stem/correct option. "
                    "Choose pure_exclusion when it is only a simple negation, reversal, or exclusion with no separate teachable concept. "
                    "If uncertain, choose needs_review."
                ),
            }
        )

    for row in rows:
        qid = str(row.get("question_id") or "")
        if qid in seen_questions:
            continue
        add(row)
        seen_questions.add(qid)
        if len(items) >= limit:
            break
    for row in rows:
        if len(items) >= limit:
            break
        if any(item["edge_key"] == row["edge_key"] for item in items):
            continue
        add(row)

    return {
        "schema_version": "preview_v5_llm_contrast_judgement_sample",
        "llm_used_to_create_this_file": False,
        "sampling_policy": f"{limit} needs_review contrast edges, diversified by question first",
        "items": items,
    }


def write_report(summary: dict[str, Any], sample: list[dict[str, Any]], selected_pairs: list[dict[str, Any]]) -> None:
    lines = [
        "# Preview v5 结构预览报告",
        "",
        f"- 生成时间：{summary['generated_at']}",
        f"- 候选句卡考点：{summary['candidate_point_count']}",
        f"- 正式预览考点：{summary['formal_exam_point_preview_count']}",
        f"- 仅保留待审候选：{summary['review_only_point_count']}",
        f"- v5 规则后高频考点：{summary['high_frequency_point_count']}",
        f"- 普通考点：{summary['normal_point_count']}",
        f"- 带易错/辨析标签：{summary['tagged_confusing_point_count']}",
        f"- contrast 边总数：{summary['contrast_edge_count']}",
        f"- 关系候选对：{summary['relation_candidate_pair_count']}",
        f"- 已选入审查候选对：{summary['selected_relation_candidate_pair_count']}",
        f"- 候选组件：{summary['candidate_component_count']}",
        "",
        "## 与 README 对齐情况",
        "",
        "- 已覆盖 905 个 preview_v1 句卡种子，不再只看高频点。",
        "- 已把错误项 evidence 先分为 confusing_contrast / pure_exclusion / needs_review。",
        "- 已把合并、父子、兄弟关系作为候选关系输出，没有自动定稿。",
        "- 低频点暂未命名，只保留句卡原文占位名。",
        "- `question_count=0` 的候选点不进入正式预览，单独写入 `review_only_points.json`。",
        "- `llm_relation_judgement_sample.json` 是受限裁判输入样本，已补题干、选项全文和角色信息，但未外发给 LLM。",
        "- AI/key 不一致、needs_review、证据缺口、弱证据仍按 README 留在后续回收阶段。",
        "",
        "## contrast 初筛分布",
        "",
    ]
    for key, value in summary["contrast_classification_distribution"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## 关系候选分布", ""])
    for key, value in summary["relation_candidate_type_distribution"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## contrast 校准样本（前 20 条）", ""])
    for row in sample[:20]:
        lines.extend(
            [
                f"### {row['question_id']} {row['option']} - {row['classification']}",
                f"- 选项：{compact(row.get('option_text'), 120)}",
                f"- 句卡：{row.get('card_id')}；support={row.get('support_type')}；grade={row.get('evidence_grade')}",
                f"- 原文：{compact(row.get('quote'), 180)}",
                f"- 理由：{row.get('reason')}",
                "",
            ]
        )

    lines.extend(["", "## Top 关系候选（前 30 条）", ""])
    for pair in selected_pairs[:30]:
        lines.extend(
            [
                f"### {pair['pair_id']} score={pair['score']} {pair['relation_candidate_type']}",
                f"- 原因：{', '.join(pair.get('reasons') or [])}",
                f"- A：{pair['card_a_summary']['title_placeholder']}",
                f"- B：{pair['card_b_summary']['title_placeholder']}",
                "",
            ]
        )

    lines.extend(
        [
            "## 下一步需要拍板",
            "",
            "1. contrast 校准样本中，哪些 pure_exclusion/needs_review 应改成 confusing_contrast。",
            "2. 关系候选中，哪些应由 LLM 判断 merge_same_point / parent_child / sibling_under_parent / keep_separate。",
            "3. 是否允许对低频长尾点进入 LLM 命名阶段。",
        ]
    )
    (OUT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seed_points = read_json(V1_DIR / "seed_points.json")["items"]
    strong_edges = read_json(V1_DIR / "strong_edges.json")["items"]
    question_contexts = load_question_contexts()

    contrast_rows, contrast_by_key = classify_all_contrast(strong_edges, question_contexts)
    contrast_sample = select_contrast_sample(contrast_rows)
    candidate_points = build_candidate_points(seed_points, strong_edges, contrast_by_key)
    relation_candidates, selected_relation_candidates = build_relation_candidates(
        candidate_points,
        strong_edges,
        contrast_by_key,
        question_contexts,
    )
    components = build_components(selected_relation_candidates)
    exam_point_preview = build_exam_point_preview(candidate_points, relation_candidates)
    review_only_points = build_review_only_points(candidate_points)
    llm_relation_sample = build_llm_relation_judgement_sample(selected_relation_candidates, RELATION_JUDGEMENT_SAMPLE_PER_TYPE)
    llm_contrast_sample = build_llm_contrast_judgement_sample(
        contrast_rows,
        question_contexts,
        CONTRAST_JUDGEMENT_SAMPLE_LIMIT,
    )

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_seed_points": str(V1_DIR / "seed_points.json"),
        "source_strong_edges": str(V1_DIR / "strong_edges.json"),
        "candidate_point_count": len(candidate_points),
        "formal_exam_point_preview_count": len(exam_point_preview["items"]),
        "review_only_point_count": len(review_only_points["items"]),
        "question_context_count": len(question_contexts),
        "strong_edge_count": len(strong_edges),
        "contrast_edge_count": len(contrast_rows),
        "contrast_sample_size": len(contrast_sample),
        "contrast_classification_distribution": dict(Counter(row["classification"] for row in contrast_rows).most_common()),
        "contrast_counted_edge_count": sum(1 for row in contrast_rows if row["include_in_exam_point_count"]),
        "high_frequency_point_count": sum(1 for point in candidate_points if point["is_high_frequency"]),
        "normal_point_count": sum(1 for point in candidate_points if not point["is_high_frequency"]),
        "tagged_confusing_point_count": sum(1 for point in candidate_points if "易错/辨析" in point["tags"]),
        "point_question_count_distribution": dict(Counter(str(point["question_count"]) for point in candidate_points).most_common()),
        "relation_candidate_pair_count": len(relation_candidates),
        "selected_relation_candidate_pair_count": len(selected_relation_candidates),
        "relation_candidate_type_distribution": dict(Counter(pair["relation_candidate_type"] for pair in relation_candidates).most_common()),
        "selected_relation_candidate_type_distribution": dict(Counter(pair["relation_candidate_type"] for pair in selected_relation_candidates).most_common()),
        "candidate_component_count": len(components),
        "not_handled_in_v5_yet": [
            "flagged_questions",
            "evidence_gaps",
            "weak_signals",
            "LLM final relation judgement",
            "low-frequency naming",
        ],
        "llm_used": False,
    }

    write_json(OUT_DIR / "summary.json", summary)
    write_json(OUT_DIR / "all_candidate_points.json", {"items": candidate_points})
    write_json(OUT_DIR / "contrast_classification.json", {"items": contrast_rows})
    write_json(OUT_DIR / "contrast_classification_sample.json", {"items": contrast_sample})
    write_json(
        OUT_DIR / "merge_parent_child_candidates.json",
        {
            "items": relation_candidates,
            "selected_for_review": selected_relation_candidates,
            "candidate_components": components,
        },
    )
    write_json(OUT_DIR / "exam_point_system_preview.json", exam_point_preview)
    write_json(OUT_DIR / "review_only_points.json", review_only_points)
    write_json(OUT_DIR / "llm_relation_judgement_sample.json", llm_relation_sample)
    write_json(OUT_DIR / "llm_contrast_judgement_sample.json", llm_contrast_sample)
    write_report(summary, contrast_sample, selected_relation_candidates)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
