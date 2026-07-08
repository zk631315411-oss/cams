# P2A section full-context probe

## 目标

验证 P2A 是否可以直接把一个完整 `section` 交给 LLM，在不提供旧 `type` 字段的情况下，让 LLM 判断：

1. 每个 unit 在当前 section 中的文本功能。
2. section 内适合复习骨架的 core_point 粒度。
3. 哪些 unit 是 core_point 的主要来源，哪些只是例子、背景或支撑。

本实验不修改正式 P2 产物，只作为重构 P2A prompt 和 contract 的依据。

## 背景判断

旧 `unit.type` 主要来自知识单元阶段的 LLM 局部窗口判断。该 LLM 通常只看一个 paragraph/block 的局部窗口，实际窗口为 1-8 句，平均约 2.81 句。因此旧 `type` 更适合描述 unit 的局部文本功能，不足以直接决定 section 级 core_point 粒度。

## 样本

```text
section_id: CH02-S03
section_title: Types of financial crime > Bribery and corruption
unit_order_span: 115-130
unit_count: 16
```

选择原因：该 section 中同时出现定义、分类、礼品/款待边界、案例、贿赂腐败与洗钱风险，复杂度适中，适合观察 LLM 是否会机械按文本功能拆点。

追加样本：

```text
section_id: CH02-S01
section_title: Types of financial crime > Predicate crimes and money laundering
unit_order_span: 60-111
unit_count: 52
purpose: 最大 section 压力测试，观察完整 section 输入是否超过 P2A 可控范围。

section_id: CH02-S05
section_title: Types of financial crime > Key takeaways
unit_order_span: 145-179
unit_count: 35
purpose: 混合型 Key takeaways 大 section 测试，观察是否需要规则整理视图辅助。
```

## 实验变量

第一轮输入不提供旧 `type` 字段，只提供：

```text
chapter_id
section_id
section_title
unit_order
unit_id
knowledge_zh
en_quote
```

后续可做第二轮对照：加入旧 `type` 字段，比较是否导致 core_point 过度切碎。

## 输出要求

LLM dry-run 输出分两层：

1. `unit_function_labels`：对每个 unit 做 section 视野下的文本功能判断。
2. `core_points`：输出 P2A core_point 草案，只包含节点和 anchor/support 来源，不输出 `core_point -> unit` 角色边。

P2B 才负责正式 `core_point -> unit` 归属/角色边。

## 验收关注点

1. 是否只使用输入中的 `unit_id`。
2. 是否没有跨出当前 section。
3. 是否把 core_point 粒度解释清楚。
4. 是否避免把每个文本功能变化都机械拆成 core_point。
5. 是否清楚区分 core_point 节点和后续 P2B unit 角色边。
