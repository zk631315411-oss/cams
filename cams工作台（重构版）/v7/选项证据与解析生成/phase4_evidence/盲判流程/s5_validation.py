# -*- coding: utf-8 -*-
"""s5 — 校验：盲判结果机械校验。"""

from __future__ import annotations

import re
from typing import Any

from s1_indexing import _load_kg_units


def validate_result(result: dict[str, Any], candidates: list[dict[str, Any]],
                    unit_lookup: dict[str, dict],
                    supplement_pool: dict[str, list[dict[str, Any]]] | None=None) -> list[str]:
    issues: list[str] = []

    candidate_unit_ids = {c["unit_id"] for c in candidates}
    candidate_unit_ids.update(row["unit_id"] for rows in (supplement_pool or {}).values()
                              for row in rows if row.get("unit_id"))
    kg_units = _load_kg_units()
    if kg_units:
        for c in candidates:
            from s1_indexing import _section_context_cards
            for card in _section_context_cards(c["unit_id"], candidate_unit_ids):
                candidate_unit_ids.add(card["unit_id"])
    valid_unit_ids = set(unit_lookup.keys())

    option_analysis = result.get("option_analysis", [])
    options = result.get("options", {})
    predicted_answer = result.get("predicted_answer", [])

    if not isinstance(predicted_answer, list):
        issues.append("predicted_answer 必须是数组")
    else:
        option_labels = {str(label) for label in options}
        invalid = [str(a) for a in predicted_answer if str(a) not in option_labels]
        if invalid: issues.append("predicted_answer 包含不存在的选项: " + ",".join(invalid))
        if result.get("question_type") == "single" and len(predicted_answer) != 1:
            issues.append("单选题 predicted_answer 必须且只能包含一个答案")

    framework = result.get("decision_framework")
    framework_ids: set[str] = set()
    if not isinstance(framework, dict):
        issues.append("缺少 decision_framework")
    else:
        ft = framework.get("type", "")
        if ft not in {"is_definition", "is_domain", "is_scenario"}:
            issues.append(f"非法 decision_framework.type={ft}")
        if not str(framework.get("rule_summary", "")).strip():
            issues.append("decision_framework 缺少 rule_summary")
        rc = framework.get("required_conditions", [])
        if not isinstance(rc, list):
            issues.append("decision_framework.required_conditions 必须是数组")
        elif ft == "is_definition" and not rc:
            issues.append("is_definition 类型必须给出 required_conditions")
        cited_ids = framework.get("cited_unit_ids", [])
        if not isinstance(cited_ids, list):
            issues.append("decision_framework.cited_unit_ids 必须是数组"); cited_ids = []
        for uid in cited_ids:
            uid = str(uid or "").strip()
            if not uid: issues.append("decision_framework 含空 unit_id"); continue
            if uid in framework_ids: issues.append(f"decision_framework: unit_id={uid} 重复引用"); continue
            framework_ids.add(uid)
            if uid not in valid_unit_ids: issues.append(f"decision_framework: 幻觉 unit_id={uid}（不在索引中）")
            if uid not in candidate_unit_ids: issues.append(f"decision_framework: unit_id={uid} 不在本题候选池中")

    if len(option_analysis) != len(options):
        issues.append(f"选项数量不匹配: analysis={len(option_analysis)} vs options={len(options)}")

    for opt in option_analysis:
        label = opt.get("option", "?")
        judgement = opt.get("judgement", "")
        decision_basis = opt.get("decision_basis", "")
        decision_reason = str(opt.get("decision_reason", "")).strip()
        evidence_status = opt.get("evidence_status", "")
        evidence_cards = opt.get("evidence_cards", [])

        if not judgement: issues.append(f"选项{label}: 缺少 judgement")
        if decision_basis not in {"direct_taxonomy", "definition_application", "domain_contrast", "stem_contrast", "insufficient"}:
            issues.append(f"选项{label}: 非法 decision_basis={decision_basis}")
        if not decision_reason: issues.append(f"选项{label}: 缺少 decision_reason")
        else:
            if re.search(r"候选池|补充池|召回|提示词|按约束|模型输出|原模型|白名单过滤|本次修复", decision_reason):
                issues.append(f"选项{label}: decision_reason 泄露内部检索或生成过程")
            absence = re.search(r"教材.{0,20}(?:未|没有).{0,20}(?:列|提及|单元|认定|提供).{0,30}(?:因此|所以|故|说明|应?排除|不属于|不正确|不是|并非)", decision_reason)
            exhaustive = (decision_basis=="direct_taxonomy" and isinstance(framework,dict) and framework.get("type")=="is_definition" and re.search(r"穷尽|完整|全部|21\s*类|21\s*categories", str(framework.get("rule_summary","")), flags=re.I))
            if absence and not exhaustive: issues.append(f"选项{label}: 不得用教材未列举或未召回直接证明选项错误")
            if decision_basis=="definition_application" and re.search(r"通常不|一般不|不必然", decision_reason):
                issues.append(f"选项{label}: definition_application 不得推测选项通常具有或不具有的事实")

        if not evidence_status: issues.append(f"选项{label}: 缺少 evidence_status")
        elif evidence_status not in {"direct","indirect","negative","none"}:
            issues.append(f"选项{label}: 非法 evidence_status={evidence_status}")
        if evidence_status=="direct" and not evidence_cards:
            issues.append(f"选项{label}: evidence_status=direct 但 evidence_cards 为空")
        if evidence_status=="negative":
            if not evidence_cards: issues.append(f"选项{label}: evidence_status=negative 但 evidence_cards 为空")
            elif not any(c.get("support_type")=="negative" for c in evidence_cards):
                issues.append(f"选项{label}: evidence_status=negative 但没有 negative evidence_card")
        if evidence_status=="none" and evidence_cards:
            issues.append(f"选项{label}: evidence_status=none 但 evidence_cards 不为空")

        seen_uids: set[str] = set()
        for card in evidence_cards:
            uid = card.get("unit_id",""); st = card.get("support_type","")
            if st and st not in {"direct","indirect","negative"}: issues.append(f"选项{label}: 非法 support_type={st}")
            if not uid: issues.append(f"选项{label}: evidence_card 缺少 unit_id"); continue
            if uid not in valid_unit_ids: issues.append(f"选项{label}: 幻觉 unit_id={uid}（不在索引中）")
            if uid not in candidate_unit_ids: issues.append(f"选项{label}: unit_id={uid} 不在本题候选池中")
            if uid in seen_uids: issues.append(f"选项{label}: unit_id={uid} 重复引用")
            seen_uids.add(uid)

        mentioned = set(re.findall(r"v7u_N\d+", decision_reason))
        unbound = sorted(mentioned - seen_uids - framework_ids)
        if unbound: issues.append(f"选项{label}: decision_reason 提到未结构化绑定的 unit_id=" + ",".join(unbound))
        if decision_basis in {"direct_taxonomy","definition_application","domain_contrast"} and not evidence_cards:
            issues.append(f"选项{label}: decision_basis={decision_basis} 但没有合法 evidence_cards")
        if decision_basis=="definition_application":
            if not framework_ids: issues.append(f"选项{label}: definition_application 但整题未引用定义 unit")
            elif not (seen_uids & framework_ids): issues.append(f"选项{label}: definition_application 未在 evidence_cards 绑定整题定义 unit")
        if decision_basis=="insufficient" and judgement!="insufficient":
            issues.append(f"选项{label}: decision_basis=insufficient 时 judgement 必须为 insufficient")

    return issues
