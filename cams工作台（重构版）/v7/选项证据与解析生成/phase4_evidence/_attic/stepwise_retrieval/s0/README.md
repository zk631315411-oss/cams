# s0：P5 归一化与检索头构建

本目录包含 s0 的各变体。所有 s0 变体在 BGE/BM25 搜索、知识图谱扩展和 LLM 调用之前即停止。

## s0a：P5 归一化检索头

脚本：`s0a_p5_heads.py`

目的：
- 字段级 P5 术语匹配。
- 将规范术语直接追加到每个字段的归一化文本中。
- 从归一化后的字段文本构建检索头。

适用于观察 P5 归一化如何改变每个字段的宽视角检查。

输出：
- `output/s0a_p5_heads/*.s0a.json`
- `output/s0a_p5_heads/*.s0a.md`

## s0b：别名展开式检索头（用于 A/B 测试）

脚本：`s0b_alias_expanded_heads.py`

目的：
- 将 P5 作为窄范围的别名/缩写提示层。
- 同时保留 `query_original` 和经过策略过滤的 `query_expanded`。
- 展开前对提示进行分类：
  - `strong`：缩写、官方名称、精确别名、拼写或翻译变体。
  - `retrieval_equivalent`：有用的检索变体，但并非严格的概念等价。
  - `broad`：语义有效但过于宽泛，不适合自动展开。
  - `suppressed`：已知有噪音的提示，不应进入测试查询。
- 保持所有提示可审计，但只有 `strong` 和 `retrieval_equivalent` 提示会追加到 `query_expanded`。
- 让 s1 能够比较有/无 P5 别名提示的检索效果。

适合作为 s1 检索实验的首选输入。

输出：
- `output/s0b_alias_expanded_heads/*.s0b.json`
- `output/s0b_alias_expanded_heads/*.s0b.md`

关键字段：
- `query_original`：不带 P5 展开的题干/选项文本。
- `query_expanded`：原文加上可自动展开的提示。
- `query_expanded_all_hints`：仅用于检查的文本，追加了所有 P5 提示。
- `query_alias_hint_records`：提示级策略元数据。
- `query_broad_hints` / `query_suppressed_hints`：审计字段，不是 s1 的默认输入。

## s0c：规范内联式检索头（用于 A/B 测试）

脚本：`s0c_canonical_inline_heads.py`

目的：
- 测试内联规范注释是否比仅追加提示更适合作为检索头。
- 保留原文，同时在匹配术语旁边插入严格的 P5 全称注释。
- 让 s0c 独立于 s0a/s0b，以便 s1 能够清晰对比各路线。

示例：
- 原文：`FATF 对成员国的建议包括...`
- 规范内联：`FATF（Financial Action Task Force，金融行动特别工作组）对成员国的建议包括...`

策略：
- 第一版仅对 `abbreviation_full_form`（缩写-全称）做内联。
- 检索等效术语（如 SAR/STR）不做内联。
- 宽泛术语（如 jurisdiction/regulator）不做内联。
- P5 匹配结果仍是查询转换元数据，不是证据。

输出：
- `output/s0c_canonical_inline_heads/*.s0c.json`
- `output/s0c_canonical_inline_heads/*.s0c.md`

关键字段：
- `query_original`：原始题干/选项文本。
- `query_canonical`：原文加上严格的内联规范注释。
- `canonical_inline_hits`：匹配到的术语及插入的注释。

## 共享策略

- P5 `evidence_unit_ids` 仅作为后续检查的锚点。
- P5 匹配结果不是直接证据。
- P5 匹配结果不是知识图谱边。
- s0 阶段 P5 不调用检索或 LLM。

## 共享模块

`_common.py` 是 s0 三步脚本的公共代码模块，避免重复定义。

包含以下内容：

- **路径常量**：`S0_DIR`、`STEPWISE_DIR`、`TESTS_DIR`、`PHASE4_DIR`、`WORKSPACE_DIR`、`V7_ROOT`、`QUESTIONS_PATH`、`P5_ALIAS_INDEX_PATH`
- **I/O 工具**：`load_json`、`write_json`、`write_text`
- **文本工具**：`normalize_space`、`normalize_cjk_term`、`term_in_text`、`append_unique`
- **题目筛选**：`load_questions`、`select_questions`

三个脚本（s0a、s0b、s0c）均通过 `from _common import ...` 导入共享符号，各自的业务逻辑保持不变。

## 当前状态

s0 v1 阶段已完成，可用于分步实验。

完成标准：
- s0a、s0b、s0c 是 s1 的独立 A/B 输入。
- 所有变体保留选项级检索头：`stem`、`option_A`、`option_B`……
- 所有变体支持单题、多题、批量限制或全量生成。
- 输出为确定性 JSON 和 Markdown 检查文件。
- 本阶段不运行检索、知识图谱扩展、LLM 调用或答案判定。

遗留说明：
- P5 词典覆盖是数据质量问题。如果 P5 别名索引缺少某术语，s0 不会凭空创造。
- s0b 提示策略有意偏保守。应在 s1 通过召回质量评估，而非视为最终真理。

## 示例

```powershell
python tests/stepwise_retrieval/s0/s0a_p5_heads.py --question-id v7_q_000009 --include-all-options
python tests/stepwise_retrieval/s0/s0b_alias_expanded_heads.py --question-id v7_q_000009 --include-all-options
python tests/stepwise_retrieval/s0/s0c_canonical_inline_heads.py --question-id v7_q_000009 --include-all-options
python tests/stepwise_retrieval/s0/s0a_p5_heads.py --limit 20 --include-all-options
python tests/stepwise_retrieval/s0/s0b_alias_expanded_heads.py --limit 20 --include-all-options
python tests/stepwise_retrieval/s0/s0c_canonical_inline_heads.py --limit 20 --include-all-options
```