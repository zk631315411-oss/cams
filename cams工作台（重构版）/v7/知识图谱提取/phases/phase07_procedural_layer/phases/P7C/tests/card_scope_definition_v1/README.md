# P7C Test: Card Scope Definition v1

## 目的

本实验用于明确 P7C 的提取边界：KG 能表达的内容，P7 不重复做；P7 只抽“处置路径”和“判断路径”。

P7 不是第二套 KG，也不是 section 总结器。

## KG 与 P7 分工

KG 负责：

```text
术语定义
概念解释
别名、缩写、术语规范化
事实陈述
单条教材证据
core point 与 unit 的证据定位
一般概念关系
```

P7 负责：

```text
遇到特定场景应该怎么处理
遇到特定条件应该怎么判断
使用哪些输入、证据、标准或控制
什么条件导致分支
动作或判断产生什么结果、后续处置或风险结论
```

## p7_card 定义

```text
p7_card = 教材支持的、section-local 的业务处置或判断路径。
```

一张 card 应尽量回答：

```text
场景或入口是什么
谁或哪个机制在处理
使用什么输入、证据、标准或控制
执行什么动作或作出什么判断
什么条件导致分支
输出、结果、后续处理或风险结论是什么
```

如果一段内容只能回答“这是什么”或“教材说了什么”，通常交给 KG；如果它能回答“怎么办”或“怎么判”，才进入 P7。

## 新增字段

只新增一个字段：

```text
card_type = process_card / judgement_card
```

`process_card`：回答“应该怎么做”。

`judgement_card`：回答“应该怎么判断”。判断卡可以进入后续簇或大图，在图中承担类似 decision / standard / judgement point 的角色。

保留现有字段：

```text
card_nature = execution / assessment / risk_indicator / control
flow_nodes
flow_edges
source_unit_ids
review_status
```

字段分工：

```text
card_type    说明这张卡是做事路径还是判断路径
card_nature  说明这张卡的知识用途
flow_nodes   正本节点
flow_edges   正本边
```

## 抽取边界

应该抽：

```text
有明确场景、触发条件、处理动作、判断标准、分支条件或输出结果
能够帮助判断选项是否符合 CAMS 处理逻辑
能够说明控制是否有效、何时有效、如何影响风险判断
能够说明风险指标如何改变处理或评估
能够说明行动何时应升级、记录、报告、限制或持续监控
```

不应该抽：

```text
纯术语定义
纯事实说明
纯背景材料
孤立例子
只有概念关系、没有处理或判断路径的内容
KG 已经可以通过 unit/core_point/alias/edge 表达的内容
```

非本机构内容不一刀切跳过。只要它会影响机构判断、报告、协作、后续处置或考试选项判断，就可以抽为 `judgement_card`。

## 粒度原则

card 大小不是第一目标。第一目标是：

```text
不遗漏关键信息
不产生幻觉
证据绑定清楚
后续可以进入簇或大图
```

大 card 可以通过，只要它没有幻觉、没有遗漏，并且 flow_nodes / flow_edges 可读。P7D 可以触发重跑，但不应仅因为 card 较大就自动拆分或丢弃。

## Prompt 文件

实验 prompt：

```text
prompts/section_card_extraction_scope_v1.md
```

该 prompt 只用于测试，不替换正式 P7C prompt。
