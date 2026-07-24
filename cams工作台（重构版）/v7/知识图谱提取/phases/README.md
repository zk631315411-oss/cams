# v7 KG phases

本目录是 v7 知识图谱提取的 phase 自包含视图。

当前基础 KG 主线（P0-P6）已完成全书构建。P7 流程型/操作型 KG overlay 正在分批抽取中。P6 之后的旧 phase07/08/09/10 目录已归档到 `archive/legacy_after_p6_20260706/`，不再作为当前执行入口。

## Phase 列表

| Phase | 作用 | 状态 |
|---|---|---|
| `phase00_quality_gate` | frozen units 输入门禁 | 完成 |
| `phase01_chapter_index` | 章/section/unit 索引（CH01-CH59，339 sections） | 完成 |
| `phase02_core_points` | section 内 core point、unit 归属边、同 section CP 关系 | 完成 |
| `phase03_intra_chapter_relations` | 同章跨 section 的 CP 关系与 unit 证据 | 完成 |
| `phase04_cross_chapter_relations` | 跨章 CP 关系 Top300 候选 + 审核 | 完成 |
| `phase05_terms` | 术语/别名/缩写字典 + P5C alias index（184 groups，用于盲判检索扩展） | 完成 |
| `phase06_kg_views` | KG 总装：`kg_retrieval_graph.json`（59章/983 CP/4973 units/8632 edges）+ Markdown 知识树 + Obsidian 阅读库 | 完成 |
| `phase07_procedural_layer` | 流程型 KG overlay：P7A→P7G（P7C 全书分批抽取进行中）。产物用于盲判证据增强和解析生成 | 进行中 |
| `legacy_phase05_case_and_cross_links` | 早期合并阶段产物，已废弃 | 归档 |
| `archive/legacy_after_p6_20260706` | 旧 phase07/08/09/10 归档 | 归档 |

## P7 子阶段

```text
P7A  生成 chapter reading tasks
P7B  双路独立顺序阅读 → process_cards
P7C  流程节点归一化 + 边级对齐 + 全书分批抽取
P7D  冲突裁决 + 桥接边审核 + 证据校验
P7E  组装局部闭环流程子图
P7G  按题生成证明路径（card内最小路径运行时）
```

P7C 的 batch outputs 已物化到 `P7C/outputs/p7c_batch*_v*/`。

## P5C Alias Index

`phase05_terms/outputs/p5c_alias_index.json`（184 alias_groups）是盲判检索管线（`phase4_evidence/盲判流程/blind_adjudication.py`）的 P5 扩展数据源，用于术语同义词/缩写的跨表达匹配召回。

## P6 主产物

`phase06_kg_views/outputs/kg_retrieval_graph.json` 是 KG 的机器母版 JSON，同时也是盲判检索的 KG 导航扩展数据源。

全量统计：59 chapters / 983 core_points / 4973 units / 8632 edges
