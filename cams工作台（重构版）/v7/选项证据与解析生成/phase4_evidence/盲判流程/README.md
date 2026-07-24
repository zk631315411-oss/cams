# 盲判流程

LLM 在不接触参考答案的前提下，检索教材知识单元、判断每道题每个选项的正误并绑定证据卡（evidence cards）。

主入口: `blind_adjudication.py`

## 模块关系

```
公共函数/（通用基础设施层）         盲判流程/（业务逻辑层）
┌─────────────────────┐         ┌──────────────────────┐
│ index.py            │───→ s1 │ 盲判检索头 + 上下文卡片 │
│   BM25, load_*, ... │    ───→│   + from 公共函数.index │
│ candidate.py        │───→ s3 │ 候选记录工厂（薄包装）   │
│   make_candidate    │    ───→│   from 公共函数.candidate│
│ retrieval.py        │───→ s2 │ 检索编排 + KG扩展 + RRF │
│   bge/bm25 搜索原语  │    ───→│   from 公共函数.retrieval│
│ llm_utils.py        │───→ s4 │ prompt构建 + 输出归一化  │
│   call/parse/strip  │    ───→│   from 公共函数.llm_utils│
└─────────────────────┘         │ s5 机械校验（纯盲判）    │
                                │ s6 输出写盘（纯盲判）    │
                                └──────────────────────┘
```

## 各模块职责

| 文件 | 来源 | 内容 |
|------|------|------|
| `s1_indexing.py` | `公共函数.index` (re-export) + 自定 | BM25、load_*、get_*、路径常量 等 17 个通用函数；**盲判自有**：`build_retrieval_heads`、`build_option_only_heads`、`_section_context_cards`、`_format_context_block` |
| `s2_retrieval.py` | `公共函数.retrieval` (re-export) + 自定 | `bge_search`、`bm25_search` (re-export)；**盲判自有**：`search_and_merge`、`retrieve_option_supplements`、`expand_with_kg`、`format_candidates`、`format_option_supplements` 等 10 个 |
| `s3_candidate.py` | `公共函数.candidate` (纯 re-export) | `make_candidate` — 候选记录统一工厂 |
| `s4_llm.py` | `公共函数.llm_utils` (re-export) + 自定 | `call_llm`、`parse_llm_output`、`strip_json_fence` (re-export)；**盲判自有**：`build_prompt`、`normalize_llm_result`、`filter_llm_citations` |
| `s5_validation.py` | 纯盲判 | `validate_result` — 机械校验（幻觉检测、候选池合规、字段自洽，约 25 条规则） |
| `s6_output.py` | 纯盲判 | `write_question_json`、`write_summary_jsonl`、`write_markdown_report` |
| `blind_adjudication.py` | 顶层入口 | `process_question()` 编排全流程，`main()` 解析参数并发调度 |

**设计原则：** 只有通用基础设施（BM25、BGE、LLM 调用、文本工具）放 `公共函数/`；检索编排、prompt 构建、校验规则、输出格式等盲判特有逻辑留在本地 s1-s6。

## 一题完整流程

```
blind_adjudication.process_question()
  │
  ├─ s2.search_and_merge()          ← BGE + BM25 + KG扩展 → 主候选池
  ├─ s2.retrieve_option_supplements()  ← 选项独立召回 → 补充池
  │
  ├─ s4.build_prompt()              ← 主池 + 补充池 → LLM prompt
  ├─ s4.call_llm()                  ← 调用 LLM API
  ├─ s4.parse_llm_output()          ← JSON 解析
  ├─ s4.normalize_llm_result()      ← schema 归一化
  ├─ s4.filter_llm_citations()      ← 过滤池外幻觉引用
  │
  ├─ 确定性修复                       ← negative 对齐、decision_reason 绑定
  │
  ├─ s6.write_question_json()       ← 每题详细 JSON
  ├─ s6.write_summary_jsonl()       ← 汇总 JSONL
  └─ s6.write_markdown_report()     ← 人读报告
```

## 用法

```powershell
# 小批量盲判（默认 manual_reviewed 题）
python blind_adjudication.py --limit 10 --concurrency 10

# 全量（前 N 题）
python blind_adjudication.py --all --limit 100 --concurrency 30

# 指定题号
python blind_adjudication.py --question-id v7_q_000009 --concurrency 1

# 按章节 + KG 扩展
python blind_adjudication.py `
  --chapter-map "../题库章节映射/数据/question_chapter_mappings.jsonl" `
  --chapter-id CH01 --enable-kg --concurrency 4

# 完整参数
python blind_adjudication.py `
  --limit 10 --concurrency 10 --model deepseek-v4-pro `
  --top-k 20 --merge-top-k 30 `
  --enable-kg --kg-max-extra 30 `
  --enable-p5 `
  --output-dir ../output/demo_run
```

## 输出

```
output/<run>/
├── questions/q_v7_q_*.json          ← 每题完整数据（候选池 + 选项分析 + 证据卡 + 预测答案）
├── blind_judgment_results.jsonl     ← 汇总（每题一行：状态、预测、候选数、问题数）
└── blind_judgment_report.md         ← 人读报告（状态分布 + 校验问题分布 + 每题详情）
```

## 机械校验要点（s5）

- 幻觉 unit_id（不在索引中 / 不在候选池中）
- 选项数量不匹配
- 单选题 predicted_answer 多个答案
- decision_framework 缺 rule_summary / required_conditions
- evidence_status 与 evidence_cards 矛盾
- decision_reason 泄露检索内部过程
- "教材未提及即错误"的伪逻辑
- definition_application 未绑定定义 unit
