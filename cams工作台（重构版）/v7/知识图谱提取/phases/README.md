# v7 KG phases

本目录是 v7 知识图谱提取的 phase 自包含视图。

当前基础 KG 主线按 P0-P6 收敛。P7 是新建的流程型/操作型 KG overlay 阶段；P6 之后的旧 phase07/08/09/10 目录已归档到 `archive/legacy_after_p6_20260706/`，不再作为当前执行入口。

## Phase 列表

| Phase | 作用 |
|---|---|
| `phase00_quality_gate` | frozen units 输入门禁 |
| `phase01_chapter_index` | 章/节/unit 索引 |
| `phase02_core_points` | section 内 core point、unit 归属边、section 内 CP 关系 |
| `phase03_intra_chapter_relations` | 同章跨 section 的 CP 关系与 unit 证据 |
| `phase04_cross_chapter_relations` | 跨章 CP 关系与 unit 证据 |
| `phase05_terms` | 术语、别名、缩写检索辅助字典 |
| `phase06_kg_views` | KG 总装与三视图输出 |
| `phase07_procedural_layer` | 流程型/操作型 KG overlay：流程卡片、短流程边、局部闭环子图、桥接边 |
| `legacy_phase05_case_and_cross_links` | 早期合并阶段产物，当前不作为主口径 |
| `archive/legacy_after_p6_20260706` | P6 后旧 phase07/08/09/10 归档 |

## 状态

当前目录保留 P0-P6 基础 KG 主线，并新增 P7 overlay 骨架。旧 pilot 总装入口已归档，不再作为当前执行口径。
