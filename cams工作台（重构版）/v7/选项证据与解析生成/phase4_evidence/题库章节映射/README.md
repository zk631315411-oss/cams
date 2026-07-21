# 题库章节映射

## 状态

**2026-07-21 废弃旧方案，新方案待讨论。**

旧方案基于 KG 旧章号（CH01-CH59）做 BGE/BM25 相似度匹配，已归档。

## 当前问题

已基于 KG unit 的 `real_section` 字段做了第一版题目→小节映射。但存在以下问题需要讨论：

### 1. 粒度问题

**教研要求**：一道题只能对应一个最准确的小节（H3）。

当前做法：从题目引用的所有 unit 反推 `real_section`，结果是一道题可能命中多个 H3 节。例如 Ch1 的 Joyce 案例（5 个 unit，属 h1 Introduction），其内容覆盖风险指标、可疑交易处理等多个主题——引用这些 unit 作为证据的题目会被标为 h1，但题目实际考点可能在其他 H3 节。

### 2. 根因

KG 的 unit 切分粒度与"考点-小节"的对应关系不完全一致。一个 unit 可能包含跨主题内容，导致从 unit 反推的 H3 归属不够精确。

### 3. 需要讨论

- 是否需要 Agent 重新判定每道题的**唯一**最匹配 H3 节？
- 判定依据：题干 + evidence_cards 的 unit 内容 + KG unit 的 `real_section`
- 跨章节题如何处理？（教研是否接受跨章标记？）

## 旧文件

- `chapter_mapping.py` → 已归档至 `_attic/题库章节映射/chapter_mapping_deprecated.py`
- `数据/` → 旧版 chapter_batches (CH01-CH59)、candidates、mappings 等，仅供历史参考
