# -*- coding: utf-8 -*-
"""s4 — LLM：call_llm、parse、normalize、filter_citations、build_prompt。"""

from __future__ import annotations

import json, re
from typing import Any

import sys
from pathlib import Path as _Path
_PARENT = str(_Path(__file__).resolve().parent.parent)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from 公共函数.llm_utils import call_llm, parse_llm_output, strip_json_fence
from s1_indexing import get_llm_config
from s2_retrieval import format_candidates, format_option_supplements


def normalize_llm_result(parsed: dict[str, Any]) -> dict[str, Any]:
    """对 LLM JSON 做最小 schema 归一化。"""
    # 确保 option_analysis 存在且为 list
    opts = parsed.get("option_analysis", [])
    if not isinstance(opts, list): parsed["option_analysis"] = []
    for opt in parsed.get("option_analysis", []):
        if not isinstance(opt, dict): continue
        # evidence_cards 必须是 list
        cards = opt.get("evidence_cards", [])
        if not isinstance(cards, list): opt["evidence_cards"] = []
        # evidence_status=negative 但没有 negative card → 对齐
        if opt.get("evidence_status") == "negative":
            has_neg = any(c.get("support_type") == "negative" for c in opt["evidence_cards"] if isinstance(c, dict))
            if not has_neg:
                if opt["evidence_cards"]:
                    opt["evidence_cards"][0]["support_type"] = "negative"
                else:
                    opt["evidence_status"] = "none"
        # evidence_status=none 但 cards 不为空 → 对齐
        if opt.get("evidence_status") == "none" and opt["evidence_cards"]:
            opt["evidence_status"] = "indirect"
    # 确保 predicted_answer 存在
    if "predicted_answer" not in parsed: parsed["predicted_answer"] = []
    return parsed


def filter_llm_citations(parsed: dict[str, Any],
                         allowed_unit_ids: set[str]) -> tuple[dict[str, Any], list[str]]:
    """删除池外引用并保留审计记录。"""
    drops: list[str] = []
    framework = parsed.get("decision_framework") or {}
    cited = framework.get("cited_unit_ids", []) or []
    framework["cited_unit_ids"] = [uid for uid in cited if uid in allowed_unit_ids]
    for uid in cited:
        if uid not in allowed_unit_ids: drops.append(f"framework: {uid}")

    for opt in parsed.get("option_analysis", []) or []:
        if not isinstance(opt, dict): continue
        cards = []
        for card in opt.get("evidence_cards", []) or []:
            uid = card.get("unit_id", "")
            if uid in allowed_unit_ids: cards.append(card)
            else: drops.append(f"option {opt.get('option','?')}: {uid}")
        opt["evidence_cards"] = cards
    return parsed, drops


def build_prompt(question: dict[str, Any], candidates: list[dict[str, Any]],
                 supplement_pool: dict[str, list[dict[str, Any]]] | None=None,
                 flow_context: str="") -> str:
    """构建完整的盲判裁判 prompt（不含参考答案）。flow_context 为 P7E 流程上下文（可选）。"""
    stem = question.get("stem", "")
    options = question.get("options", {})
    stem_en = question.get("stem_en", "")
    options_en = question.get("options_en", {})
    qtype = question.get("question_type", "single")
    qtype_label = "单选题" if qtype == "single" else "多选题"

    opt_lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
    opt_en_lines = "\n".join(f"  {k}: {options_en.get(k, '')}" for k in options if options_en.get(k))
    stem_en_str = f"\n英文题干: {stem_en}" if stem_en else ""
    opt_en_str = f"\n英文选项:\n{opt_en_lines}" if opt_en_lines else ""

    candidates_text = format_candidates(candidates)
    supplements_text = format_option_supplements(question, supplement_pool or {})

    return f"""你是一个 CAMS 反洗钱考试题目裁判。你需要判断每道题的每个选项是否正确。

### 题目信息
题干: {stem}{stem_en_str}
选项:
{opt_lines}{opt_en_str}
题型: {qtype_label}

**注意**：本题来自英文考试，中文为翻译版本。当中文翻译与英文原意的强弱、边界不一致时（如英文为模糊边缘行为而中文译为明确违法），以英文为准进行判断。

{flow_context}
### 教材证据
以下是教材中与本题相关的知识单元（候选池），请基于这些单元判断每个选项：
其中 `KG导航` 只表示该单元与检索命中的单元在教材知识图谱中同属或相邻；它不是答案依据。最终判断必须回到知识单元的中英文原文。

{candidates_text}

### 单选项独立补充候选
以下内容由单个选项独立召回，只表示"可能与该选项概念相关"，不是已经成立的证据：
- 只有当某个 unit 同时解释选项含义及其与本题题干的关系时，才能引用。
- 不得因为某个选项没有补充候选就判定该选项错误。
- 不得引用仅因同词异义、翻译偏差或宽泛词命中的 unit。
- 补充候选不会自动改变答案；必须回到教材中英文原文做判断。

{supplements_text}

### 材料类型与推理权重
引用前先看单元标注的"教材类型"，据此决定如何使用：

**概念定义/规则规定（最高权重）**：提取必要条件做演绎推理。只有这类才能用于"不满足条件即排除选项"。
**核心区分/分类说明**：用于判断选项属于哪个类别、区分相近概念。
**事实陈述/常见表现（辅助）**：描述"通常怎样"，可与定义印证，不可单独排除选项。
**案例（最低权重）**：具体情节不得上升为普遍标准，只能帮助理解概念在场景中的表现。
**风险指标/流程描述**：匹配题干行为是否符合指标即可，不要求因果链条。

**教材特点说明**
本教材常将概念区分放在案例对比中，而非给出字典式定义。相近概念的划分标准可能只在案例中体现。当教材没有为某个概念提供独立的普遍定义时：
- 可以从案例对比中提取区分信息进行辨析，但需说明"教材案例表现为……教材未给出严格、普遍的划分标准"。
- 不得因教材未给出普遍标准就直接否定概念存在或判定 insufficient。
- 教材的"定义"声明（如 Microstructuring resembles traditional structuring but is typically used with digital asset laundering）即使简短，也应被视为该概念最权威的直接依据。

**风险指标/流程描述**
- 用于匹配题干行为是否符合指标或流程。
- 指出题干行为是否符合该指标即可，不要求建立因果链条。

**条件性概念**：教材中部分概念具有多种表现形式（如 placement 可表现为存款或购买资产）。不得将其单一表现描述为唯一对应关系，严禁机械断言。

**语境有效性（强制检查 —— 违反将导致证据失效）**
引用 unit 前，必须完成以下三项检查，缺一不可：

1. **主语一致性**：证据的主语/对象必须与结论的主语一致。
   - 证据讲的是"银行"的规则，不能直接套用到"赌场"。
   - 证据讲的是"PSP（支付服务提供商）"的业务特征，不能当作"MSB 客户"的风险信号。
   - 证据讲的是"私营部门间（银行对银行）"的信息共享，不能当作"公私合作（PPP）"的益处。
   - 判定方法：把证据原文的主语写出来，把结论的主语写出来，两者必须一致或存在教材明确声明的等价关系。

2. **时间节点/业务阶段匹配**：证据所处的业务阶段必须与题干场景的阶段一致。
   - 证据来自"SAR 提交后维持账户"章节，不能用来证明"客户开户时"应实施的控制。
   - 证据来自"持续尽调（ongoing due diligence）"章节，不能用来证明"首次准入（onboarding）"的流程。
   - 证据来自"调查结束后"的处置，不能用来证明"发现可疑信号时"的第一步操作。
   - 判定方法：读出证据的章节路径，确认章节描述的业务阶段（准入/持续监控/调查/报告后/退出），与题干问的时间节点对比。

3. **场景限定**：若证据来自特定场景（如大使馆、外交使团、某具体案例、某类机构），该 unit 的陈述只在该场景下有效，不能当作跨场景的普遍原则使用。来自 CH01 等通用章节的定义除外。案例中的具体数字、地点、行为方式属于该案例的特殊情节，不得将其上升为普遍定义或判断标准。

**语义贪污（强制检查）**
不得在复述题干事实时添加题干没有的限定词、程度词或结构特征：
- 题干写"低于"不得写成"略低于"；写"一个账户"不得写成"跨账户"。
- 写"支付发票"不得写成"虚假发票"；写"收到现金"不得写成"收到大量现金"。
- 题干没用程度副词你也不能用，题干没写的结构特征你不能补。
- 如果某个选项按其普通字面就不包含题干所要求的领域要素，可用 `stem_contrast` 和 `evidence_status=none` 判错。

### 输出要求
以 JSON 格式输出，不要包含其他内容。文本值中引用原文词汇时使用中文引号「」或单引号''，不得使用 ASCII 双引号""（会破坏 JSON 结构）：
- 先选择整题的 `decision_framework.type`：
  - `is_definition`：定义、类别或"哪些属于"题。必须先引用定义或明确分类规则，提取 `required_conditions`，再把规则逐项应用到选项。
  - `is_domain`：询问某一特定领域、计划或产品的警示信号。必须先建立领域边界，再区分"通用风险/通用渠道"和"该领域特有信号"。
  - `is_scenario`：其余场景匹配题。必须从题干事实与教材规则之间建立对应关系。
- 定义/类别题不得用"教材没有列举该选项"直接证明选项错误；只有引用材料明确给出穷尽分类时，未列入才可作为分类依据。
- 必须按选项和题干原文判断，不得补充题干或选项没有提供的特殊事实、动机、后果或运作机制。
- 定义应用必须区分"选项明确违反必要条件"和"题目没有提供该条件"。只有前者可以据定义判错并使用 `definition_application`；仅仅没有写出某个条件，不能证明选项错误，应标为 `insufficient`，除非教材给出了明确穷尽分类或题干事实可直接排除。
  排除选项时必须使用演绎逻辑：列出必要条件 → 指出选项文本缺少哪个条件 → 结论"不满足条件"。不得使用"通常""一般""往往"等概率措辞。
  示例——"上游犯罪的必要条件是产生非法收益（v7u_N000017）。选项X是暴力人身犯罪，题干未提供其产生非法收益的信息，不满足必要条件，因此不构成上游犯罪。"
- `required_conditions` 只是逐项核对规则，不允许据此推测选项通常具有或不具有题目未说明的动机、收益、伤害程度或附加情境。
- 特定领域题中，"某工具一般存在洗钱风险"不等于"该工具是题目所问领域的特有警示信号"。
- 如果某个选项按其普通字面就不包含题干所要求的领域要素，可用 `stem_contrast` 和 `evidence_status=none` 判错。
- 每个选项的 `decision_basis` 必须是以下五种之一（注意与 `decision_framework.type` 是两套独立的分类，不要混淆）：
  - `direct_taxonomy`：教材原文直接支持或反驳该选项。
  - `definition_application`：基于整题定义框架提取的必要条件，逐项核对该选项。
  - `domain_contrast`：基于教材原文建立的领域边界，判断选项属于领域内还是领域外。
  - `stem_contrast`：仅基于题干和选项的可见文字直接对照得出结论，不需教材单元。当你能从题干文字推理出选项正误但无教材 unit 引用时，使用此值而非 `insufficient`。
  - `insufficient`：现有材料无法做出任何可靠判断时才使用。如果你的 `judgement` 是 `correct` 或 `incorrect` 且写出了实质 `decision_reason`，说明你已做出判断，不应标 `insufficient`。
- `definition_application` 必须在 evidence_cards 中绑定整题所引定义 unit；`direct_taxonomy` 必须绑定明确分类 unit；`domain_contrast` 必须绑定领域规则或选项概念 unit。
- `decision_reason` 只写实体判断，不得出现"候选池、召回、提示词、约束、模型输出"等内部过程词。
- 在输出 JSON 前逐项自检：
  1. `definition_application` 的每个选项都必须从 `decision_framework.cited_unit_ids` 复制至少一个定义 unit 到本选项 `evidence_cards`。
  2. `direct_taxonomy` 和 `domain_contrast` 的 `evidence_cards` 不得为空；若理由同时比较通用概念和领域规则，应分别绑定相应 unit。
  3. `decision_reason` 中写出的每个 unit_id 都必须同时出现在本选项 `evidence_cards` 或整题 `decision_framework.cited_unit_ids`，不得只在 prose 中提 ID。
  4. 有 `indirect` 卡片时 `evidence_status` 不得写 `none`；只有确实没有卡片的 `stem_contrast` 才可使用 `none`。
  5. `decision_reason` 中复述题干事实时，与题干原文逐字核对：不得添加题干没有的程度副词（略、远、刚好）、数量词（多个、跨）、性质词（虚假、伪造）。
  6. 每个 `evidence_cards` 中引用的 unit，必须通过语境有效性三项检查：主语是否与结论一致？章节的业务阶段是否与题干时间节点匹配？是否将特定场景/案例的陈述当作普遍原则使用？任何一项不通过，该 unit 不得作为 `direct` 证据，最多降级为 `indirect` 或放弃引用。
- `evidence_status=direct` 表示教材直接支持该选项；`indirect` 表示只能间接支持；`negative` 表示教材证据反驳该选项；`none` 表示没有可引用证据，且 evidence_cards 必须为空。
{{
  "predicted_answer": ["A"],
  "decision_framework": {{
    "type": "is_definition|is_domain|is_scenario",
    "rule_summary": "题目采用的判断规则",
    "cited_unit_ids": ["v7u_N000001"],
    "required_conditions": ["规则成立所需条件"]
  }},
  "option_analysis": [
    {{
      "option": "A",
      "judgement": "correct|incorrect|insufficient",
      "decision_basis": "direct_taxonomy|definition_application|domain_contrast|stem_contrast|insufficient",
      "decision_reason": "从整题规则到该选项结论的完整判断理由",
      "evidence_status": "direct|indirect|negative|none",
      "evidence_cards": [
        {{"unit_id": "v7u_N000001", "support_type": "direct|indirect|negative", "reason": "为什么这个单元支持或反驳该选项"}}
      ]
    }}
  ]
}}"""
