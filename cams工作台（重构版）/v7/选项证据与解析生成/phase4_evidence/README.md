# Phase 4: 选项证据召回、盲判与解析生成

盲判 LLM 在不接触参考答案的前提下，检索教材单元、判断每道题每个选项的正误并绑定证据卡；解析 LLM 基于盲判结果撰写教研可读的逐题解析；最终导出为中英双语题库软件版 Markdown。

## 核心脚本

| 脚本 | 角色 | 输入 | 输出 |
|------|------|------|------|
| `盲判流程/blind_adjudication.py` | 裁判 + 取证 | 题库 + 检索索引 | `output/<run>/questions/q_*.json` |
| `解析撰写/generate_evidence_explanations.py` | 解析撰写 | 盲判 JSON | `output/<run>/explanations/*.md` |
| `解析撰写/export_software_explanations.py` | 题库软件导出 | 解析 JSON | `output/<run>/software_export/chapters/CHxx.md` |
| `盲判流程/retrieval_validation.py` | 检索质量抽检 | 题库 + 索引 | 检索验证报告 |
| `题库章节映射/chapter_mapping.py` | 题目→章节映射 | 题库 + 索引 | `题库章节映射/数据/question_chapter_mappings.jsonl` |
| `导出为docx/md_to_docx.py` | Markdown → Word | 解析 MD | docx |

## 数据流

```
v7_questions.json + phase3_index + (可选 KG/P5)
        ↓
盲判流程/blind_adjudication.py ← 盲判：检索 + LLM 裁判 + 证据卡 + 机械校验 + 自动对齐
        ↓
output/<run>/questions/q_*.json
        ↓
解析撰写/generate_evidence_explanations.py ← 解析：答案锁定 + LLM 撰文 + 本地逐字校验 + 兜底
        ↓
output/<run>/explanations/*.md
        ↓
解析撰写/export_software_explanations.py ← 导出：门禁检查 + 中英双语题库软件版
        ↓
output/<run>/software_export/chapters/CHxx.md
```

## 关键设计

### LLM 只做判断和撰文，不填表

解析 LLM 只负责三段 prose（考点、核心解析、易错提醒）和可选的 `source_quote`。以下字段全部由本地代码派生，LLM 不碰：

| 字段 | 派生来源 |
|------|---------|
| `basis_type` | 盲判 `decision_basis` 直接映射 |
| `source_claims` | 盲判 `evidence_cards` 的 unit_id → 反查单元原文注入 |
| `error_type` | LLM 可选填 5 种标签，正确/证据不足自动覆盖 |
| `stem_quotes` / `option_quotes` | LLM 不提供时自动用选项/题干全文兜底 |

### 盲判机械对齐

`盲判流程/blind_adjudication.py` 在 `filter_llm_citations` 之后对 LLM 输出做确定性修复：
- `evidence_status=negative` 但无 negative card → 自动对齐
- `decision_reason` 提到但未绑定的 unit_id → 自动补入 evidence_cards
- 有 evidence_cards 但 `evidence_status=none` → 自动纠正

### 门禁分层

- **盲判层**：幻觉检测、候选池合规、字段自洽、推理边界（约 25 条）
- **解析层**：逐字校验、prose 质量、基础完整性、软件就绪评估
- **导出层**：只检查导出必需项（答案一致性、选项完整、source_quote 如提供则格式正确），不重复上游校验

### 章节映射

题目到真实教材章节（CH01-CH59）的映射由 `题库章节映射/数据/question_chapter_mappings.jsonl` 维护，经人工确认。盲判通过 `--chapter-map` 引用，实现按章节选题。

## 典型使用

```powershell
# 按章节跑全流程（以 CH01 为例）
$chapter = "CH01"
$out = "output/demo_$chapter"

# 1. 盲判（+KG 扩展）
python "盲判流程/blind_adjudication.py" `
  --chapter-map "题库章节映射/数据/question_chapter_mappings.jsonl" `
  --chapter-id $chapter --enable-kg --concurrency 4 `
  --model deepseek-v4-pro --output-dir $out

# 2. 解析
python "解析撰写/generate_evidence_explanations.py" `
  --output-dir $out --concurrency 4 --model deepseek-v4-pro --write-back

# 3. 导出
python "解析撰写/export_software_explanations.py" `
  --output-dir $out --chapter-id $chapter

# 单题调试
python "盲判流程/blind_adjudication.py" `
  --question-id v7_q_000009 --concurrency 1 `
  --enable-kg --model deepseek-v4-pro --output-dir output/demo_test
```

## 输出结构

```
output/<run>/
├── questions/q_*.json              ← 每题完整盲判 + 解析数据
├── blind_judgment_results.jsonl    ← 盲判汇总
├── blind_judgment_report.md        ← 盲判人读报告
├── explanations/
│   ├── v7_q_*.md                   ← 逐题教研解析（含教材原文附录 + 参考答案对比）
│   ├── index.md                    ← 全量索引
│   └── chapters/CHxx.md            ← 按章合并草稿
└── software_export/
    ├── chapters/CHxx.md            ← 题库软件版（中英双语，精简格式）
    └── review_required.md          ← 待复核清单
```

## 关键约束

1. 盲判阶段不读取参考答案。参考答案只用于后置审计与分歧诊断。
2. KG 与 P5 只用于扩展候选证据池，不直接作为答案依据。
3. 解析答案以盲判 `predicted_answer` 为准，解析阶段不得覆盖。
4. 机械校验不等同于语义校验。对象错配、条件跳跃等问题仍需人工复核。
