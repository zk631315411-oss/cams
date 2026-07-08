# Phase 01 章节/小节索引

## 目标

把 Phase 00 的 eligible units 按教材章节、heading、页码和 unit 顺序组织，建立 `章 -> 节 -> unit` 索引，并输出可控章节范围内的样本。

这里的“节”指教材顺序中连续出现的小节片段。P1 会按章内 `unit_order` 顺序扫描，当小节标题路径发生变化时开启新的小节片段，并生成稳定的 `section_id`。同名标题如果在同一章内分段出现，会生成不同的 `section_id`。

本阶段只建立章节和小节归属，不生成 core_point，不判断语义关系，不生成图谱边。

## 输入

- `phase00_quality_gate/outputs/eligible_units.jsonl`

## 输出

- `outputs/chapter_skeleton.jsonl`          # 章 -> section 骨架
- `outputs/all_chapters_units.jsonl`        # 全书 unit 索引（当前 P1 主产物，后续 phase 以此为准）
- `outputs/first_five_chapters_units.jsonl` # 前五章样本
- `outputs/first_two_chapters_units.jsonl`  # 前两章样本
- `previews/phase1_chapter_skeleton_preview.md`

核心字段：

- `section_id`：小节片段 ID，例如 `CH02-S05`。
- `section_order`：章内小节片段顺序。
- `section_title`：由 `heading_context` 前 3 层拼成的小节标题路径。

## 运行脚本

- `scripts/phase1_chapter_skeleton.py`

## 当前状态

当前目录是本阶段正式脚本、产物和预览位置。
