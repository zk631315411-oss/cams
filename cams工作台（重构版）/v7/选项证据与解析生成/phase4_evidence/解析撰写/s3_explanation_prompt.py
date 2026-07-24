# -*- coding: utf-8 -*-
"""s3 — 解析撰写专用：Prompt 构建层。"""

from __future__ import annotations

from typing import Any

from 解析撰写.s2_explanation_material import (
    _build_context_augmented_material, _format_context_block,
    _format_prompt_card, candidate_by_unit, _material_card,
)


def build_prompt(
    result: dict[str, Any], standard_question: dict[str, Any] | None = None
) -> str:
    standard_question = standard_question or {}
    predicted = "、".join(result.get("predicted_answer", []) or []) or "未形成答案"
    option_lines = "\n".join(
        f"{label}. {text}" for label, text in (result.get("options", {}) or {}).items()
    )
    options_en = standard_question.get("options_en", {}) or {}
    option_en_lines = "\n".join(
        f"{label}. {options_en.get(label, '')}"
        for label in (result.get("options", {}) or {})
        if options_en.get(label)
    )

    # 使用上下文增强版材料卡（同 Section ±2 unit 连续展示）
    shown_context_keys: set[tuple[str, int]] = set()
    material_lines: list[str] = []
    for row in _build_context_augmented_material(result):
        material_lines.append(
            f"选项{row['option']}：{row['option_text']}\n"
            f"盲判标签：{row['judgement']} | 证据状态：{row['evidence_status']} | "
            f"原判断类型：{row['decision_basis']}"
        )
        material_lines.append("已裁判证据：")
        for card in row["evidence_cards"]:
            context_block = card.get("context_block", [])
            if context_block:
                section = context_block[0].get("real_section", "")
                center_order = next((c["unit_order"] for c in context_block if c["is_center"]), 0)
                ctx_key = (section, center_order)
                if ctx_key not in shown_context_keys:
                    material_lines.append(_format_context_block(context_block))
                    shown_context_keys.add(ctx_key)
            else:
                material_lines.append(_format_prompt_card(card))
        if not row["evidence_cards"]:
            material_lines.append("- 无")
        material_lines.append("解析补充候选：")
        for card in row["supplement_cards"]:
            context_block = card.get("context_block", [])
            if context_block:
                section = context_block[0].get("real_section", "")
                center_order = next((c["unit_order"] for c in context_block if c["is_center"]), 0)
                ctx_key = (section, center_order)
                if ctx_key not in shown_context_keys:
                    material_lines.append(_format_context_block(context_block))
                    shown_context_keys.add(ctx_key)
            else:
                material_lines.append(_format_prompt_card(card))
        if not row["supplement_cards"]:
            material_lines.append("- 无")

    framework = result.get("decision_framework", {}) or {}
    unit_map = candidate_by_unit(result)
    framework_material: list[str] = []
    for uid in framework.get("cited_unit_ids", []) or []:
        uid = str(uid)
        unit = unit_map.get(uid)
        if unit:
            framework_material.append(
                _format_prompt_card(_material_card(unit, uid, "shared_framework"))
            )

    chapter_text_value = "；".join(
        f"{row.get('real_chapter') or row.get('chapter_id', '')} {row.get('chapter_title', '')}".strip()
        for row in result.get("chapter_mappings", []) or []
    ) or "未映射"
    validation_text = "；".join(
        str(issue) for issue in result.get("validation_checks", []) or []
    ) or "无"

    return f"""你是一位CAMS反洗钱讲师。你的学生零基础、没看过教材、非金融法律专业背景、英文非母语，他们通过做题来学习，想象你坐在学生旁边，拿笔在纸上画给他看。

你的目标是：简明扼要且直击重点地**讲透题目内部的逻辑关系**，让学生看完解析后，换一道类似的题也能自己判断。

---

## 你的学生

- 零基础，没看过教材，边做题边学
- 非金融/法律专业出身
- 英文非母语，需要中英对照来理解选项原意

## 你的任务

对这道题（固定答案为"{predicted}"，不得改判），你需要让学生：

但**你有权拒答**。如果完成以下检查后发现材料无法支撑高质量解析，不要硬写——输出 deferral 字段说明理由。拒答条件（满足任一条即可拒答）：

- **核心证据缺位**：支撑正确项的核心 unit 与选项之间存在不可弥合的 gap（如证据要求"高风险司法管辖区"但选项只说"外国"，且没有其他 unit 能桥接）
- **主语不可调和**：所有可用证据的主语/场景与结论主语/题干场景不一致，且教材未声明等价关系
- **时间/阶段不可调和**：所有可用证据的业务阶段与题干时间节点不一致（如只有"S​​AR后"的证据来证明"开户时"）
- **证据整体偏弱**：正确项依赖的证据全部为 indirect/案例/推测性陈述，没有任何 direct 的教材原文

拒答时，`deferral.reason` 应具体指出哪个 gap 无法弥合、尝试了哪些 unit、为什么不能用。这比硬写一份证据歪曲的解析更有价值。

1. **知道考什么** —— exam_point：一句话，30字内。只写核心概念或能力点，不写判断结论，不引入题干没有的信息，不复述题干具体情节。示例：
   - 好："按金额粒度及分散方式区分 structuring 与 microstructuring"
   - 好："识别房地产场景下的 placement 阶段特征"
   - 坏："判断时需关注存款是否被故意拆分为多笔略低于报告限额的小额交易"（复述题干）
   - 坏："区分结构化与微结构化、贸易洗钱等手法"（题干没有提及贸易洗钱）

2. **知道正确答案为什么对** —— core_analysis：一个自然段落。先给概念定义或判断规则，再结合题干关键事实，推出正确答案为什么成立。如果教材原文用的术语和选项中出现的术语不完全一致，先准确引用教材原文的术语和定义，再说明两者的关系。不要偷换主语——不要把"教材定义了X"写成"教材定义了Y"。引用定义时直接给出定义内容和页码，不要加"教材明确指出""教材将……定义为"等前缀。示例：
	   - 坏："教材明确定义逃税为使用非法手段逃避纳税义务（P28）。"
	   - 好："逃税指使用非法手段逃避纳税义务（P28）。"
	   写完自问："如果换一道题干相似但选项不同的题，学生看完还能自己判断吗？"如果核心解析本身已经说明了判断方法，不画蛇添足。

3. **知道为什么正确项更优** —— option_explanations：只写真正有迷惑性的错误项。正确项不写（core_analysis已覆盖）。每个错误项的写法不是"排除它"，而是"在教材框架下，正确项比它更直接匹配"：
   - 错误项本身可能也有一定关联（如信托确实能隐藏所有权），但它在教材中的定义位置和题干条件的匹配度不如正确项。你要解释的是**为什么匹配度不如**，而不是**绝对不可能**。
   - 避免非黑即白的排除语气（"不属于""不可能""因此错误"）。改用比较级（"不如X直接""题干更支持X而非Y""更吻合教材对X的定义"）。
   - 明显无关的选项（题干压根没涉及该选项所需的要素），直接指出缺失即可，不展开。
   - 明显无关的选项不凑数
   - 不加"故该项不选""因此该项正确"等套话结尾

4. **下次不踩同样的坑** —— easy_mistake：如果有真正容易混淆的概念对，给出教材中的核心区分标准。如果没有独立于一、二、三之外的增量信息，留空（"text": ""）。

## 你的材料

以下是你可以使用的全部信息：

**题目**
中文题干：{result.get('stem', '')}
英文题干：{standard_question.get('stem_en', '')}
中文选项：
{option_lines}
英文选项：
{option_en_lines or '未提供'}

注意：本题来自英文考试，中文选项为翻译版本。当中文翻译与英文原意有偏差时（如 bending the rules 被译为"违规操作"），以英文原意为准。

**盲判框架**
固定答案：{predicted}
框架类型：{framework.get('type', '')}
{chr(10).join(framework_material) if framework_material else '无'}
教材章节：{chapter_text_value}

**选项材料（已标注教材类型和教材页码）**
{chr(10).join(material_lines)}

引用教材内容时，必须标注页码。例如："放置阶段指非法资金进入金融系统（P53）。"

## 证据红线（违反即失败，优先级最高）

**1. 禁止编造证据内容**：归因于教材的断言，其关键词必须真的出现在 unit 原文中。原文没有的词，不能说成教材说的。
   - ✗ 证据说"Tuning reduces false positives" → 写成"不应根据团队规模限制预警"（原文没有"团队规模"）
   - ✗ 证据说"verify authenticity of documents" → 写成"自动翻译文档"（原文没有"翻译"）

**2. 禁止张冠李戴**：写出的结论主语必须与证据原文主语一致。证据讲"银行"不能证"赌场"，证据讲"私营部门间信息共享"不能证"公私合作（PPP）"。如果证据来自特定案例（如大使馆、Tamayo案），该案例的具体情节不得上升为普遍定义。

**3. 禁止后合理化**：先有结论再找关键词匹配的 unit 装点门面。引用前自问："如果这个 unit 不在候选池里，我的结论会变吗？"不会变 → 这个引用在装饰，删掉。会变 → 它才真正在支撑判断。

**4. 标注推理边界**：基于教材事实推导的判断是推理，用"由此可推断""相比之下更可能"等表述，不要写成和教材事实一样的确定语气。教材原文的涵盖范围不能缩窄——原文说"customers or sectors"，不能说"仅限于行业部门"。

**5. 页码必须来自材料卡片元数据**（`书内第XX页` 或 `printed_page` 字段）。不得自编页码。无页码标注的 unit 不给它编页码。

**6. 禁止空口说"无教材引用"**：声称无引用之前，必须先扫一遍候选池。存在与题干主题词部分相关的 unit 就必须引用并说明覆盖了什么。跳过池中已有证据写"无教材引用"属于证据遗漏。

**7. 拒答仅作最后手段**：只有材料无覆盖且推理也无法判断时才拒答。能通过排除法、定义对比、场景匹配得出答案的，就基于推理作答。

## 写作规范

- 题干原文不添加程度副词、数量词、性质词。题干写"低于"就是低于，不是"略低于"。
- 教材原文用"such as""include""for example"等举例措辞的，不得转写成"清单""明确列举"等暗示穷举的词。
- 引用教材案例用描述性语言（"教材在Tamayo案例中展示了..."），不用规定性语言（"教材规定必须"）。
- 不以非黑即白的方式排除选项。改用比较级——"题干条件更直接匹配X而非Y"。
- 易错提醒给出具体区分标准，要么留空。不写"注意区分X和Y"这类空泛表达。
- JSON 文本中的引号用中文引号「」，不用 ASCII 双引号""。
- 当教材对某概念没有严格划分标准时，诚实说出。
- primary_unit_id：选对本题答案判断最重要的那个 unit_id。

## 输出 JSON

{{{{
  "deferral": null,
  "answer": ["A"],
  "primary_unit_id": "v7u_N000001",
  "exam_point": {{{{
    "text": "一句话，30字内，只写考什么"
  }}}},
  "core_analysis": {{{{
    "text": "定义/规则 → 题干关键事实 → 为什么正确答案成立",
    "cited_unit_ids": ["v7u_N000001"],
    "source_quote": {{{{
      "unit_id": "v7u_N000001",
      "exact_excerpt": "可选，40-240字符英文原文片段"
    }}}}
  }}}},
  "option_explanations": [
    {{{{
      "option": "B",
      "analysis": "仅错误项，不超过两句。不仅说不选，还说何时选",
      "error_type": "概念混淆|主体或阶段错配|范围或程度偏差|题干要素不匹配|证据不足",
      "stem_quotes": ["题干逐字片段"],
      "option_quotes": ["选项逐字片段"]
    }}}}
  ],
  "easy_mistake": {{{{
    "text": "有增量信息时写，否则留空\"\"",
    "cited_unit_ids": ["v7u_N000001"]
  }}}}
}}}}"""