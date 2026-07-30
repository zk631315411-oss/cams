# Phase 04：跨章 core_point 关系

状态：P4A/P4B/P4B_review/P4C 已完成一轮全书 Top300 候选流程。

## 目标

P4 处理不同章节之间的 `core_point -> core_point` 关系，用于构建跨章复习路径和辅助检索线索。

P4 不负责生成最终题目证据。最终证据仍以 unit 级证据为准。

## 当前流程

```text
P4A：向量召回跨章 CP 对候选。
P4B：LLM 判断候选是否成边、关系类型和方向。
P4B_review：人工确认可疑关系。
P4C：给确认后的 P4 关系绑定 unit 证据。
```

## P4A

输入：P2A reviewed core points 与 P2B unit edges。

召回文本：

```text
title_en + section_title + P2A reason + selected P2B unit_text
```

默认只取关键 unit edge，最多 5 条。召回只表示“值得检查”，不表示已经成边。

## P4B

默认模型：`deepseek-v4-pro`，关闭 thinking。

默认执行方式：

```text
batch_size = 5
concurrency = 10
request_timeout = 120
```

每批只给 LLM 5 个候选 CP 对，降低批量扫题和单次失败风险。脚本会合并所有 batch 输出，并校验缺失、重复、非法关系类型和方向字段。

允许关系：

```text
summarizes
illustrates
grounds
contrasts
none
```

当前最容易误判的是 `grounds`。正式使用时，宽泛章节总论、泛泛 vulnerability、仅共享方法/术语的关系应进入人工 review 或直接拒绝。

## P4B review

全书 Top300 候选经 P4B 与人工 review 后：

```text
P4 主图保留：80
转 P5：2
拒绝：5
```

P4 主图关系分布：

```text
grounds: 72
illustrates: 7
summarizes: 1
```

正式关系输出：

```text
outputs/p4_reviewed_cross_chapter_relations.jsonl
outputs/p4_move_to_p5_candidates.jsonl
```

## P4C

P4C 只给已确认的 P4 关系绑定 unit 证据，不新增关系、不重判关系类型、不修改方向。

输入：P4B review 后的正式关系，以及 source/target CP 的 P2B unit edges。当前 `p4_reviewed_cross_chapter_relations.jsonl` 为 1,404 条；本文其他 80 条口径属于早期抽样阶段。

输出字段：

```text
p4_relation_id
relation_type
source_core_point_id
target_core_point_id
source_evidence_unit_ids
target_evidence_unit_ids
support_strength
evidence_summary
```

最终 P4C 输出：

```text
outputs/p4c_reviewed_cross_chapter_relation_evidence.jsonl
```

本轮结果：

```text
relation_count: 80
support_strength strong: 80
review_flags: none
```

## 文件

```text
scripts/run_p4_cross_chapter_relations.py
scripts/run_p4c_relation_evidence_binding_ds.py
prompts/p4b_cross_chapter_relation_v1.md
prompts/p4c_relation_evidence_binding_v1.md
inputs/
outputs/
  p4_reviewed_cross_chapter_relations.jsonl           # 当前正式 P4 关系（1,404 条）
  p4_move_to_p5_candidates.jsonl                       # 转 P5 候选
  p4c_reviewed_cross_chapter_relation_evidence.jsonl   # P4C 证据绑定
  p4_formal_all_chapters_top300_batch5x20_v1_*.jsonl   # 全书 Top300 批处理中间产物
  p4_formal_first10_top200_batch5x10_v1_*.jsonl        # 前10章 Top200 pilot 中间产物
reports/
runs/
```
