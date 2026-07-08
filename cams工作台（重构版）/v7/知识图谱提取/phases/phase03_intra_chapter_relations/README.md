# Phase 03: 同章跨 section 的 core_point 关系

## 任务

在同一章内，判断不同 section 的 core_point 之间是否存在对复习有用的关系，并为审核通过的关系绑定 unit 级证据。

P3 不修改 P2A 的 CP 边界，不修改 P2B 的 `core_point -> unit` 归属边，也不处理同 section 内的 CP 关系。同 section 内 CP 关系属于 P2C。

## 当前口径

P3 只保留三类关系：

| 关系 | 方向 | 含义 |
| --- | --- | --- |
| `summarizes` | Key takeaways CP -> 正文/案例 CP | 总结或回顾前文 |
| `illustrates` | Case/example CP -> 概念/风险/控制 CP | 案例具体说明某个概念 |
| `grounds` | 基础概念/框架/概述 CP -> 展开/应用 CP | 前者为后者提供知识基础 |

当前生产口径不输出 `alias_of`。重复主题如果不能归入上述三类关系，就不进入 P3 主边。

## 流程

```text
P3A: 按章读取全部 section 原文和 P2A reviewed CP，生成同章跨 section CP 关系候选
  -> P3A_review: 人工审核，删除同 section 边、过宽边、弱边、方向错误边
  -> P3B: 对审核通过的关系绑定 source/target 双方的 unit 级证据
```

## 输入

P3A 自动读取：

```text
phases/phase02_core_points/outputs/p2a_reviewed_core_points.<section_id>.json
phases/phase02_core_points/runs/<source_p2a_run>/input_section.json
```

P3B 自动读取：

```text
phases/phase03_intra_chapter_relations/outputs/p3_core_point_relations.jsonl
phases/phase02_core_points/runs/p2b*<core_point_id>/parsed_response.json
```

## 输出

```text
outputs/p3_core_point_relation_candidates.jsonl   # P3A 候选关系，待人工 review
outputs/p3_core_point_relations.jsonl             # P3A_review 后确认关系，供 P3B 使用
outputs/p3_relation_unit_evidence.jsonl           # P3B 关系证据绑定结果
outputs/p3_rejected_core_point_relations.jsonl    # 被拒绝的候选关系
reports/p3_relation_report.md
reports/p3_full_book_quality_check_20260706.md    # 全量质量检查
reports/p3_materialization_report.md              # 物化报告
previews/p3_core_point_relations_preview.md
```

## 脚本

| 文件 | 说明 |
| --- | --- |
| `prompts/p3a_chapter_section_relations_v1.md` | P3A prompt |
| `prompts/p3b_relation_evidence_binding_v1.md` | P3B prompt |
| `scripts/run_p3a_chapter_relations_ds.py` | 单章 P3A 调用 |
| `scripts/run_p3a_chapter_batch_ds.py` | 多章 P3A 批处理与候选聚合 |
| `scripts/run_p3b_relation_evidence_binding_ds.py` | 单批/单关系 P3B 证据绑定 |
| `scripts/run_p3b_binding_batch_ds.py` | P3B 并发调度与结果聚合 |
| `scripts/materialize_p3_full_book.py` | 全量物化 P3 产物 |

## 全书运行结果

全书 P3A/P3A_review/P3B 已全部完成：

```text
P3A accepted_relations: 229
P3A relation type distribution:
  grounds: 163
  illustrates: 38
  summarizes: 28
P3B evidence_binding: 229（全部通过）
```

关系分布：

```text
grounds: 163     — 基础概念/框架/概述 -> 展开/应用（占比 71%）
illustrates: 38  — 案例/示例 -> 概念/风险/控制（占比 17%）
summarizes: 28   — Key takeaways -> 正文/案例（占比 12%）
```

全书产物保留在：

```text
outputs/p3_core_point_relation_candidates.jsonl    # P3A 候选关系
outputs/p3_core_point_relations.jsonl              # P3A_review 后确认关系（229 条）
outputs/p3_relation_unit_evidence.jsonl            # P3B 关系证据绑定（229 条）
reports/p3_relation_report.md
reports/p3_full_book_quality_check_20260706.md     # 全量质量检查
reports/p3_materialization_report.md               # 物化报告
previews/p3_core_point_relations_preview.md
```

前五章 pilot 产物保留在 `outputs/*_first5.*` 文件中，不再作为当前口径。

## 边界

- P2C：同 section 内 CP -> CP 关系。
- P3：同章、跨 section 的 CP -> CP 关系。
- P4：跨章 CP -> CP 关系。
- P5：术语、别名、缩写、方法索引。
- P6：KG 总装、阅读视图、验收报告。
