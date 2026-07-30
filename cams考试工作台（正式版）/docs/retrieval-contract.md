# 检索契约

当前检索层保留重构版 V7 的 BGE、BM25、RRF、检索头、P5、选项补充和 KG 扩展参数。所有运行路径从工作台根目录解析，不依赖历史重构版目录。

## 一般检索

入口：`search_evidence(root, query, top_k=20, language=auto, config=None)`。

流程：

```text
单查询 -> BGE-M3 + 对应语言 BM25 -> RRF -> merge_top_k -> KG 扩展
```

限制：不生成题目检索头，不启用 P5，`per_option_limit` 强制为 0。

返回主要字段：

- `retrieval_kind=general`
- `query`
- `asset_versions`、`textbook_version`
- `config`
- `main_candidates`
- `kg_candidates`
- `results`，为主候选加 KG 候选

## 题目检索

入口：`retrieve_question_evidence(root, question, config=None)`。

流程：

```text
中英文题干/选项检索头
-> P5 术语内联归一
-> 每个检索头执行 BGE-M3 + 对应语言 BM25
-> RRF 去重融合
-> 每个检索头最低保底
-> KG 扩展
-> 未进入主候选的选项补充池
```

返回主要字段：

- `retrieval_kind=question`
- `asset_versions`、`textbook_version`
- `config`、`query_heads`
- `main_candidates`
- `kg_candidates`
- `option_supplements`，按选项标签分组

题目检索只返回发现结果，不自动写题目档案。正式使用时必须通过 MCP `register_evidence` 登记。

## 候选字段

教材候选通常包括：

- `unit_id`
- 中文知识文本和/或英文原文
- 章节上下文、书内页和 PDF 页
- `route`、`score`、`fusion_score`
- `routes`、`languages`、`best_rank`
- `retrieval_hits[]`：检索头、语言、路线、排名、原始分数和查询
- KG 候选的 `kg`：种子单元、核心点、边类型、理由和相关度

输出登记到题目证据目录后，会生成稳定 `evidence_id` 并保留每轮发现历史。

## 配置

| 参数 | 默认值 | 规则 |
| --- | ---: | --- |
| `profile` | `v7_legacy_202607` | 参数快照标识 |
| `top_k` | 20 | 非负；一般检索函数参数会覆盖配置值 |
| `merge_top_k` | 30 | 非负 |
| `kg_max_extra` | 30 | 非负 |
| `per_option_limit` | 3 | 非负；一般模式强制 0 |
| `per_head_minimum` | 2 | 非负 |
| `rrf_k` | 60 | 必须大于 0 |
| `section_context_range` | 4 | 当前未参与算法；接手者需对照重构版判断，不能视为已实现 |
| `enable_kg` | true | 控制 KG 资产和扩展 |
| `enable_p5` | 题目 true | 一般模式强制 false |

配置合并顺序：代码默认值 -> `settings.toml` 的 `[retrieval]` -> 调用参数。未知字段会报错。

当前 `settings.example.toml` 的 `[workspace]`、`[server]`、`[codex]` 没有代码读取，不属于检索契约。

## 冻结资产

| 资产 | 当前版本 |
| --- | --- |
| 教材单元 | `v7-frozen-20260703` |
| 向量/BM25 索引 | `v7-index-5614abb1c4bf` |
| KG | `v7-kg-20260723` |
| P5 术语 | `v7-p5-20260723` |
| BGE-M3 | `BAAI/bge-m3` 快照 `5617a9f61b028005a4858fdac845db406aefb181` |

`assets.py` 会验证 manifest 指向资产的 SHA-256，并验证索引/KG 关联；PDF 阅读器的页渲染路径不等同于检索资产验证。

资产在进程内缓存。更新磁盘文件后必须重启 API/MCP。

## 错误与验收

以下情况会失败：资产缺失或哈希不符、索引字段错误、KG 引用未知单元、未知/非法参数、缺少 numpy/sentence-transformers、BGE 无法离线加载。

当前 Windows BGE-M3 加载失败，不能把测试替身通过作为真实检索可用证据。修复后的最低验收：

1. 断网加载本地模型并执行非空 `encode`。
2. 一般检索返回非空结果和完整资产版本。
3. 题目检索返回检索头、主候选、KG 候选和选项补充结构。
4. 候选可登记到题目目录并追溯到 `unit_id`、教材版本和页码。
