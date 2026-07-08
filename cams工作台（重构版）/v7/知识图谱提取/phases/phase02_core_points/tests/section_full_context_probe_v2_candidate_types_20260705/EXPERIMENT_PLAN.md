# P2A section probe v2: section text with candidate type table

## 目标

修正 v1 实验口径。v1 去掉了旧 `type` 字段，但没有给候选类型表，导致子代理需要自由命名 unit 文本功能，实验不够干净。

v2 目标是测试：

1. 给完整 section 原文和 unit_id 锚点。
2. 不给每个 unit 的旧 `type` 标注。
3. 给一张候选类型表，让子代理必须从表内选择 unit function type。
4. 再基于 section 级视野判断 P2A core_point 粒度。

## 输入口径

每个样本输入包含：

```text
chapter_id
section_id
section_title
candidate_function_types
section_text_with_unit_anchors
units
```

`units` 内允许字段：

```text
unit_order
unit_id
knowledge_zh
en_quote
printed_page
pdf_page
```

禁止字段：

```text
type
unit_type
old_type
```

## 候选类型表

子代理必须从以下类型中选择 unit function type：

| type | 中文说明 |
|---|---|
| `definition` | 定义、概念边界、术语解释 |
| `classification` | 类型、类别、形式、构成项 |
| `rule` | 规则、要求、控制措施、应做事项 |
| `process` | 流程、阶段、步骤 |
| `risk_indicator` | 风险、红旗、警示信号、风险暴露 |
| `case` | 案例、示例、情景说明 |
| `context` | 背景、承接、列表引导、非核心上下文 |
| `fact` | 一般事实陈述，无法归入以上类型 |
| `needs_review` | 证据或类型不确定，需要人工复核 |

## 样本

```text
CH02-S01 Predicate crimes and money laundering
unit_count: 52
purpose: 最大 section 压力测试。

CH02-S05 Key takeaways
unit_count: 35
purpose: 混合型 Key takeaways section 测试。
```

## 输出要求

输出分两层：

1. `unit_function_labels`：每个 unit 必须从候选类型表中选择一个类型。
2. `core_points`：P2A core_point 草案，只输出节点、标题、anchor_unit_ids、support_unit_ids 和理由。

不输出正式 `core_point -> unit` 角色边；P2B 负责该部分。

