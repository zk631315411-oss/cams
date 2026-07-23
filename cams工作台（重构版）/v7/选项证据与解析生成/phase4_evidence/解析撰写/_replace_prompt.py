"""临时脚本：替换 build_prompt 的 prompt 模板。"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "generate_evidence_explanations.py"

with open(TARGET, "r", encoding="utf-8") as f:
    content = f.read()

# Find the start of the prompt template
start_marker = '    return f"""你是一位CAMS反洗钱讲师'
start_idx = content.find(start_marker)
if start_idx < 0:
    raise RuntimeError("start marker not found")

# Find the end
end_marker = '}}}}"""'
end_idx = content.find(end_marker, start_idx)
if end_idx < 0:
    raise RuntimeError("end marker not found")
end_idx += len(end_marker)

# Read the old text to confirm
old = content[start_idx:end_idx]
print(f"Old prompt: {len(old)} chars, starts with: {old[:60]}...")

new_prompt = r'''    return f"""你是一位CAMS反洗钱讲师。你的学生零基础、没看过教材、非金融法律专业背景、英文非母语，他们通过做题来学习。

你的目标是：学生看完解析后，**换一道类似的题也能自己判断**。

---

## 你的学生

- 零基础，没看过教材，边做题边学
- 非金融/法律专业出身
- 英文非母语，需要中英对照来理解选项原意

## 你的任务

对这道题（固定答案为"{predicted}"，不得改判），你需要让学生：

1. **知道考什么** —— exam_point：一句话，30字内。只写核心概念或能力点，不写判断结论，不引入题干没有的信息，不复述题干具体情节。示例：
   - 好："按金额粒度及分散方式区分 structuring 与 microstructuring"
   - 好："识别房地产场景下的 placement 阶段特征"
   - 坏："判断时需关注存款是否被故意拆分为多笔略低于报告限额的小额交易"（复述题干）
   - 坏："区分结构化与微结构化、贸易洗钱等手法"（题干没有提及贸易洗钱）

2. **知道正确答案为什么对** —— core_analysis：一个自然段落。先给概念定义或判断规则，再结合题干关键事实，推出正确答案为什么成立。写完自问："如果换一道题干相似但选项不同的题，学生看完还能自己判断吗？"如果不能，补一句"下次遇到类似题，优先看题干中的___"。

3. **知道错误项为什么错** —— option_explanations：只写真正有迷惑性的错误项。正确项不写（core_analysis已覆盖）。每个错误项：
   - 不仅说"为什么不选X"，还要说"什么时候选X才对"——帮学生理解这个概念的边界
   - 明显无关的选项不凑数
   - 不加"故该项不选""因此该项正确"等套话结尾

4. **下次不踩同样的坑** —— easy_mistake：如果有真正容易混淆的概念对，给出教材中的核心区分标准和下次判断时优先看什么。如果没有独立于一、二、三之外的增量信息，留空（"text": ""）。

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

**选项材料（已标注教材类型）**
{chr(10).join(material_lines)}

## 写作铁律

1. 不得在题干原文上添加任何程度副词、数量词、性质词。题干写"低于"就是低于，不是"略低于"也不是"远低于"。题干写"一个账户"就是一个，不是"跨账户"。题干写"支付发票"就是支付发票，不是"虚假发票"。
2. 教材案例中的具体数字和情节不能当普遍定义用。案例说 Tamayo 存款低于 1000 美元，不等于"微结构化必须低于 1000 美元"。
3. 当教材对某概念没有严格划分标准时，诚实说出，但给学生一条在当前条件下最合理的判断路径。
4. JSON 文本中的引号用中文引号「」，不要用 ASCII 双引号""（会破坏 JSON 结构）。
5. 易错提醒要么给出具体的区分标准，要么留空。不写"注意区分X和Y"这类空泛表达。

## 输出 JSON

{{{{
  "answer": ["A"],
  "exam_point": {{{{
    "text": "一句话，30字内，只写考什么"
  }}}},
  "core_analysis": {{{{
    "text": "定义/规则 → 题干关键事实 → 为什么正确答案成立 → 下次怎么看",
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

new_content = content[:start_idx] + new_prompt + content[end_idx:]

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Replaced {len(old)} chars with {len(new_prompt)} chars")
print("Done.")
'''