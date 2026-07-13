# s1：直接单元召回 A/B 测试

s1 读取 s0a/s0b/s0c 的分层检索头，运行直接单元召回。
s0a、s0b、s0c 是独立的 A/B 测试，不是流水线的分支。

## 目的

- 验证每个分层检索头实际召回的内容。
- 将 s0a、s0b、s0c 作为独立的检索实验运行。
- 检查每个 P5 查询转换是否改善了召回或引入了噪音。

## 输入

- `../s0/output/s0a_p5_heads/*.s0a.json`
- `../s0/output/s0b_alias_expanded_heads/*.s0b.json`
- `../s0/output/s0c_canonical_inline_heads/*.s0c.json`

## A/B 定义

s0a：

- baseline（基线）：原始字段头，由字段原文构建。
- test（测试）：P5 归一化头，来自 s0a 的 `query_zh`。

s0b：

- baseline（基线）：`query_original`。
- test（测试）：`query_expanded`，追加了 P5 别名提示。

s0c：

- baseline（基线）：`query_original`。
- test（测试）：`query_canonical`，内联了严格的缩写/全称注释。

## 过程

对于每个保留的检索头：

- `stem`
- `option_A`、`option_B`、`option_C`…… = 题干加单个选项
- `all_options` 仅当设置 `--include-all-options` 时启用

s1 将每个基线/测试查询分别通过：

- BGE
- BM25_zh
- BM25_en

每路结果单独保留，然后按 `unit_id` 合并以供检查。

## 输出

- `output/s1_direct_unit_retrieval/s0a/*.s1.s0a.json`
- `output/s1_direct_unit_retrieval/s0a/*.s1.s0a.md`
- `output/s1_direct_unit_retrieval/s0b/*.s1.s0b.json`
- `output/s1_direct_unit_retrieval/s0b/*.s1.s0b.md`
- `output/s1_direct_unit_retrieval/s0c/*.s1.s0c.json`
- `output/s1_direct_unit_retrieval/s0c/*.s1.s0c.md`

`s1_summary.py` 的汇总输出：

- `output/s1_summary/summary.md`
- `output/s1_summary/summary_heads.json`
- `output/s1_summary/summary_questions.json`
- `output/s1_summary/summary_heads.csv`
- `output/s1_summary/summary_questions.csv`

汇总脚本只读取已有的 s1 输出，不运行检索。

## 当前发现

首轮 50 题运行显示如下模式：

| experiment | questions | heads | changed_heads | added | dropped | common | avg_change_ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| s0a | 50 | 250 | 186 | 1062 | 1081 | 1909 | 0.4656 |
| s0b | 50 | 250 | 166 | 872 | 867 | 2123 | 0.3906 |
| s0c | 50 | 250 | 115 | 514 | 510 | 2480 | 0.2424 |

解读：

- `s0a` 破坏性太强，应保留为诊断分支。
- `s0b` 可增加有用的别名/定义单元，但可能将检索拉向术语定义。
- `s0c` 是最稳定的增强路线，但部分题目的变化率仍较高。
- 后续阶段的推荐候选池是 `baseline union s0c`，`s0b` 新增单元作为可检查的补充。

## 边界

- 不涉及知识图谱扩展。
- 不调用 LLM。
- 不做答案判定。
- P5 不直接产出单元；它仅在 s0a/s0b/s0c 中改变测试查询。

## 示例

```powershell
python tests/stepwise_retrieval/s1/s1_direct_unit_retrieval.py --question-id v7_q_000009 --experiment all
python tests/stepwise_retrieval/s1/s1_direct_unit_retrieval.py --question-id v7_q_000009 --experiment s0a
python tests/stepwise_retrieval/s1/s1_direct_unit_retrieval.py --question-id v7_q_000009 --experiment s0b
python tests/stepwise_retrieval/s1/s1_direct_unit_retrieval.py --question-id v7_q_000009 --experiment s0c
python tests/stepwise_retrieval/s1/s1_direct_unit_retrieval.py --experiment all --limit 20
python tests/stepwise_retrieval/s1/s1_summary.py --limit 50
```

`--limit` 和 `--offset` 在选定的实验中筛选排序后的公共题目 ID，以保持 s0a/s0b/s0c 批次对齐。