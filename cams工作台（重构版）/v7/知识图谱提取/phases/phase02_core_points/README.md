# Phase 02 Core Points

Phase 02 当前包含 P2A、P2A_review、P2B 和 P2C。

```text
P2A：在单个 section 内识别复习骨架 core_point。
P2A_review：人工复核 P2A 产出的 CP 边界，形成人工裁决后的 CP。
P2B：对每个 core_point，判断候选 unit 的语义角色，产出 core_point -> unit 边。
P2C：在同一 section 内，识别 core_point 之间的结构关系。
```

P2A 不处理相邻小节关系，不处理同章小节间 core_point 关系，不处理跨章关系。

## P2A 目标

输入 P1 的 `章 -> section -> unit` 索引，按 section 处理，输出小节内复习用 core_point 节点。

P2A 要解决的问题是：

```text
这个 section 里，适合作为教材复习骨架的 core_point 有哪些？
```

P2A 不直接使用旧 unit `type` 作为输入。旧 `type` 是知识单元阶段基于局部 paragraph/window 得到的文本功能判断，不足以决定 section 级 core_point 粒度。

## 输入策略

每个 section 输入包含：

```text
section_text_with_unit_anchors
candidate_function_types
units
```

其中：

- `section_text_with_unit_anchors`：完整 section 原文，每段以 `[unit_id|unit_order]` 锚定。
- `candidate_function_types`：候选文本功能类型表。
- `units`：P1 输出的 unit 材料，但不包含旧 `type`、`unit_type`、`old_type`。

候选类型固定为：

```text
definition
classification
rule
process
risk_indicator
case
context
fact
needs_review
```

## 输出策略

P2A 输出两层：

1. `unit_function_labels`：对每个 unit 从候选类型表中选择一个文本功能类型。
2. `core_points`：section 内 core_point 草案。

core_point 必须表达连续性：

```text
concept_unit_spans
evidence_unit_spans
non_contiguous_concept
intervening_support_unit_ids
review_flags
```

这样可以表达教材中常见的写法：前面讲定义，中间插案例，后面回到同一主题继续讲定义或分类。

## 产物

### P2A 产物

```text
outputs/p2a_core_points.jsonl          # P2A 原始 CP 草案
outputs/p2a_unit_function_labels.jsonl # 每个 unit 的 function_type
reports/p2a_validation_report.md       # 校验报告
runs/<run_slug>/run_manifest.json      # 运行记录
```

### P2A_review 产物

```text
inputs/p2_manual_decisions.jsonl          # 人工裁决记录
outputs/p2a_reviewed_core_points.<section_id>.json  # review 后的 CP
reports/p2a_review_<section_id>.md        # review 报告
```

### P2B 产物

```text
runs/p2b*<core_point_id>/parsed_response.json  # CP -> unit 语义边
runs/p2b*<core_point_id>/run_manifest.json     # 运行记录
```

说明：当前 P2B 的正式可用结果保存在每个 CP 对应的 run 目录中，P6 暂按 core_point_id 解析最新 `parsed_response.json`。`outputs/p2b_core_point_unit_edges.jsonl` 尚未物化。

### P2C 产物

```text
runs/p2c*<section_id>/parsed_response.json     # 同 section CP -> CP 关系边（原始运行记录）
runs/p2c*<section_id>/run_manifest.json        # 运行记录
reports/p2c_*_summary.json                     # 批次运行汇总
outputs/p2c_core_point_relations.jsonl          # 全量物化后的正式 CP 关系（当前 P2C 主产物）
outputs/p2c_reviewed_relations.<section_id>.json  # 已人工物化的 reviewed 关系
```

全量 P2C 正式关系已物化到 `outputs/p2c_core_point_relations.jsonl`。`runs/p2c*/parsed_response.json` 只作为可追溯运行记录，不再作为当前 P2C 主产物。

## 归档

旧 P2 已归档至：

```text
archive/legacy_p2_before_p2a_20260705/
```

当前主线以 `contract.md` 和各环节 prompt 为准。

## P2A_review：人工复核

P2A LLM 输出后，对 CP 边界做一次人工复核。P2A_review 是人工裁决层，不强制脚本化；人可以直接给出判断，由产物记录最终 CP 边界。

复核目标：

- 检查同一 section 内是否有 CP 之间 unit 大量重叠（数据冲突）。
- 检查是否有明显的 CP 拆分过碎或过度合并。
- 不修改 LLM 未覆盖的语义细节，只处理 CP 边界。

人工判断记录在：

```text
inputs/p2_manual_decisions.jsonl
```

review 后的 CP 产物记录在：

```text
outputs/p2a_reviewed_core_points.<section_id>.json
reports/p2a_review_<section_id>.md
```

每条记录格式：

```json
{
  "section_id": "CH02-S03",
  "review_type": "merge_core_points",
  "source_core_point_ids": ["cp_CH02_S03_001", "cp_CH02_S03_003"],
  "result_core_point_id": "cp_CH02_S03_001",
  "decision": "CP1 与 CP3 合并，保留 cp_CH02_S03_001，标题调整为'贿赂：定义、形式、礼品风险与ABC政策'。",
  "reviewer": "human",
  "reviewed_at": "2026-07-06"
}
```

复核通过的 section 进入 P2B。存在 P2A_review 产物时，P2B 应以 review 后 CP 为准，不直接使用原始 P2A 草案。

## P2B：CP → unit 语义边

### 目标

对每个 P2A/P2A_review 产出的 core_point，将其候选 unit 分配语义角色，产出 core_point → unit 边。

P2B 要解决的问题是：

```text
这个 core_point 中，每个候选 unit 扮演什么语义角色？
哪个是定义、哪个是分类、哪个是案例、哪个是风险指标？
```

### 输入策略

每个 P2B 调用针对一个 core_point，输入包含：

```text
target_core_point       — 当前待判断的 CP
candidate_unit_ids      — 候选 unit 列表（来自 P2A 的 anchor/support/evidence 跨度）
candidate_units         — 候选 unit 的原文
sibling_core_points     — 同一 section 内的其他 CP（用于判断 exclude）
```

### 角色类型

```text
defines             — 定义概念
classifies          — 分类、列举类型
explains            — 解释、限定、扩展
states_rule         — 规则、要求、义务
describes_process   — 流程、步骤、方法
indicates_risk      — 风险、红旗、警示
prescribes_measure  — 控制措施、缓解行动
illustrates         — 案例、示例、场景
states_consequence  — 后果、处罚、影响
provides_context    — 背景、引导、承接
exclude             — 不属于该 CP
```

### 做法

- 按每个 core_point 调一次 DS pro（关 thinking）
- 脚本：`scripts/run_p2b_core_point_ds.py`
- prompt：`prompts/p2b_core_point_unit_edges_v1.md`

### 当前状态

P2B 已有全书 runs，P6 当前按 core_point_id 读取最新 `parsed_response.json`。后续建议补一个物化步骤，生成稳定的 `outputs/p2b_core_point_unit_edges.jsonl`。

## P2C：CP → CP 关系边

### 目标

对同一 section 内的所有 core_point，识别它们之间的结构关系，产出 CP → CP 关系边。

P2C 要解决的问题是：

```text
同一个 section 里，这些 CP 之间是什么关系？
哪个是总览、哪个是子项、哪个是案例、哪个是铺垫？
```

### 关系类型

```text
contains       — 总览/框架包含子概念/子类（方向：上位→下位）
illustrates    — 案例/示例说明某个概念（方向：案例→概念）
prepares       — 前提定义/基础为后续展开做准备（方向：基础→后续）
parallels      — 同层并列话题（方向：按教材顺序）
contrasts      — 显式对比/区分（方向：按教材顺序）
```

### 输入策略

每个 P2C 调用针对一个 section，输入包含：

```text
section_text_with_unit_anchors  — 完整 section 原文
core_points                     — 该 section 所有 CP（带 title 和 unit_edges_summary）
```

### 做法

- 按每个 section 调一次 DS pro（关 thinking）
- 脚本：`scripts/run_p2c_section_ds.py` / `scripts/run_p2c_batch_ds.py`
- prompt：`prompts/p2c_section_cp_relations_v1.md`

### 当前状态

已完成全量 runs：前 5 章 29 个 section + 后续章节批次，覆盖所有 section。全量 P2C 正式关系已物化到 `outputs/p2c_core_point_relations.jsonl`。批次状态见 `reports/p2c_*_summary.json`。

当前 `outputs/` 中的 reviewed 产物：

```text
outputs/p2c_reviewed_relations.CH13-S02.json
```
