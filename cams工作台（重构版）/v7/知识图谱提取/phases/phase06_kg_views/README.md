# Phase 06 KG 总装与三视图输出

## 定位

P6 不再做新的抽取、判断或审核。P6 只负责把 P1-P4 的已确认产物总装成同一个 KG，并输出三种视图。P5 是后续选项证据生成的独立检索辅助文件，不进入 KG 阅读图谱。

核心原则：

```text
同一个 KG，一份机器母版，两个 Markdown 阅读视图。
```

## 当前产物状态

P6 全书产物已生成，当前母版规模如下：

```text
generated_at: 2026-07-06T16:51:08
chapters: 59
sections: 339
core_points: 983
units: 4973
edges: 8632
relation_edges: 1070
p5_terms: 1408 (external retrieval index)
```

轻量验收结果：无缺失边引用、无重复边 ID、无空边 ID，且没有缺 unit 归属边的 core point。当前已知限制是 P4 跨章关系基于已审核 Top300 候选，不等同于全书 all-pairs 穷尽关系。

## 三版产物

### 1. 机器检索 JSON

用途：服务后续选项证据生成、RAG 检索、按 CP/relation 扩展召回，并可与 P5 术语索引搭配使用。

输出：

```text
outputs/kg_retrieval_graph.json
```

这是 P6 的母版产物。后续 Markdown 树和 Obsidian vault 都从它渲染，避免三套产物不一致。

建议包含：

```text
chapters
sections
core_points
units
edges
metadata
```

P5 术语文件不作为 `terms` 节点进入本 JSON；P6 只在 `metadata.p5` 中记录其状态和文件位置。

### 2. 单文件树状 Markdown

用途：快速通读、整体审阅、人工验收、对外讨论。

输出：

```text
previews/kg_study_tree.md
```

阅读结构：

```text
chapter
  section
    core_point
      key units
      same-chapter relations
      cross-chapter relations
```

这版强调顺着教材读，不追求展示全部证据。

### 3. Obsidian 阅读库

用途：长期教研阅读、章节跳转、core_point 横跳、local graph 查看。

输出：

```text
previews/kg_reading_vault/
  00_index.md
  chapters/
    CH01.md
    CH02.md
    ...
```

第一版先采用“总索引 + 每章一个 Markdown”。暂不默认拆成每个 core_point 一个文件，避免阅读过碎。

## 输入

```text
P1 chapter/section/unit index
P2 reviewed core_points + core_point -> unit edges
P3 same-chapter core_point relations
P4 cross-chapter core_point relations
```

P5 不作为 P6 输入进入阅读图谱。P6 可在 `metadata` 中标明 P5 文件状态，方便后续选项证据生成流程定位。

## 边界

P6 不做：

```text
不新增 core_point
不新增关系边
不重判 P3/P4 关系
不修正 P5 词典
不把 P5 shared term 当作 P4 主图关系
不把 P5 terms 放入 KG 主图或阅读视图
不把 TopN 结果说成全书穷尽关系
```

P6 只做：

```text
读取
校验
总装
渲染
标注输入状态
```

## 最小目录

```text
phase06_kg_views/
  README.md
  scripts/
    assemble_retrieval_graph.py
    render_study_tree.py
    render_review_views.py      # 渲染 Obsidian 阅读库 + 验收报告
  outputs/
    kg_retrieval_graph.json
  previews/
    kg_study_tree.md
    kg_reading_vault/
      00_index.md
      chapters/
  reports/
    p6_light_check.md
    p6_light_check.json         # 轻量验收数据
    p6_render_report.md         # 渲染过程报告
```

`reports/p6_light_check.md` 是辅助产物，只记录缺失、重复、孤立节点、无证据边等问题，不作为 P6 主目标。
