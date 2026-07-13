# P7B：Section 材料包生成

## 定位

P7B 只负责给 P7C 准备 section 级材料包。

P7B 不调用 LLM，不抽 card，不判断流程，不生成 hint，不生成 bridge，不合并 cluster。

## 输入

```text
phase06_kg_views/outputs/kg_retrieval_graph.json
phase05_terms/outputs/p5c_alias_index.json
phase07_procedural_layer/inputs/procedural_schema_v2.json
```

P6 是主来源；P5 只做术语规范化提示，不作为证据来源。

## 输出

JSONL 批处理入口：

```text
outputs/p7_section_extraction_tasks.jsonl
```

按 section 拆分的阅读包：

```text
section_packages/<section_id>/task.json
section_packages/<section_id>/section_text.md
section_packages/<section_id>/units.json
section_packages/<section_id>/core_points.json
section_packages/<section_id>/cp_unit_edges.json
section_packages/<section_id>/same_section_cp_edges.json
section_packages/<section_id>/instructions.json
section_packages/<section_id>/alias_metadata.json
```

## Task 内容

每个 task 只对应一个 section，包含：

```text
chapter_id / chapter_title
section_id / section_title / section_order
section_text_with_unit_anchors
本 section 全部 units
本 section 全部 core_points
本 section 全部 CP -> unit 边
本 section 内 CP -> CP 边
alias_index
instructions
```

`section_text_with_unit_anchors` 是 P7C 主阅读材料；units、CP、边只做证据锚定和结构辅助。

## 供 P7C 使用的正式口径

P7B 的职责止于“材料提供”，但材料包必须同时适配两类 P7C 执行方式：

```text
1. 子代理 / Codex 阅读抽取：适合疑难 section、抽样复核、口径校准。
2. DS/API 批量抽取：适合生成全书初稿、可并发、可保存 prompt/raw/parsed/validation。
```

两种方式读取同一套 section package，不应改变 P7B 产物结构。P7B 不因为执行方式不同而增删 section 原文、unit、CP 或边。

当前流程口径：

```text
DS 可以作为 P7C 批量初稿生成器；
子代理 / Codex / 人工用于 review、疑难 section、关键章节和最终口径确认；
已由子代理生成且接近完成的产物不因 DS 测试而覆盖或回写；
DS 测试发现只作为后续批处理设计依据。
```

已完成的小样本发现：

```text
CH47-S01：DS v4 pro high-thinking 与子代理均输出 1 card，结构校验通过；DS 主流程更简洁，但少收部分上下文示例。
CH42-S01：DS v4 pro high-thinking 与子代理均输出 2 cards，结构校验通过；DS 能拆出预 KYC 和 KYC/CDD 主流程，但将预 KYC suitability assessment 标为 execution，而子代理标为 assessment，更符合 P7 card_nature 口径。
```

因此，后续如果用 DS 跑全书，必须保留 P7D 校验和 Codex/人工复核环节，尤其检查：

```text
card_nature 是否把 assessment / risk_indicator 错标为 execution
section 是否被过度拆分或过度合并
上下文示例是否被遗漏，导致后续 bridge / scenario path 证据不足
functional_dependency 是否被清楚标注 review_notes
```

## Instructions 口径

P7B 写入的 `instructions.json` 从 `inputs/procedural_schema_v2.json` 动态读取类型定义：

```text
node_categories = entry / process / exit / auxiliary
flow_node_types = E1-E8（入口） / P1-P10（处理） / X1-X7（出口） / input / standard
relation_types = R1-R12（业务语义关系，可选）
flow_edge_types = PRECEDES / REFERENCES / PRODUCES / DECIDES / FEEDBACK（渲染类型）
```

必填字段：
```text
card_id / section_id / title / flow_nodes / flow_edges / source_unit_ids / review_status
```

可选字段：
```text
summary / scenario / trigger / actor / objective / inputs / decision_standard / outputs / steps / review_notes / metadata
```

核心约束：
```text
flow_nodes / flow_edges 是正本
summary / steps 是人读辅助
trigger 字段不能替代 trigger 节点
每张 card 至少应有 node_category = entry 的节点
P5 alias 只做规范化，不作为证据
```

**注意**：instructions.json 中的类型列表从 schema 动态生成，不硬编码，确保与 schema 保持同步。

## Candidate-only

`--candidate-only` 只决定哪些 section 进入任务队列，不删减 task 内材料。

命中条件包括：

```text
unit.type 命中 process / rule / risk_indicator / case
P2B relation_type 命中 describes_process / prescribes_measure / states_rule / indicates_risk
section/CP 文本命中 monitoring / investigation / review / report / escalation / due diligence / screening / risk assessment / alert / SAR / KYC / EDD / transaction
```

## 当前脚本

```text
scripts/generate_section_extraction_tasks.py
```

示例：

```powershell
python scripts/generate_section_extraction_tasks.py --chapters CH47 CH49 --candidate-only --output outputs/p7_section_extraction_tasks_smoke_CH47_CH49.jsonl --write-section-packages --package-dir phases/P7B/section_packages
```
