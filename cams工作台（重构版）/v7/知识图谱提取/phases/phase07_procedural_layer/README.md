# Phase 07：流程型/操作型知识图谱层

## 定位

P7 在 P0-P6 已完成的教材复习型 KG 之上，新增一层流程型/操作型 overlay。

P7 不修改 P0-P6 产物，不重判 P2/P3/P4 的 core_point 关系，也不把 P5 术语索引写入主图。P7 的目标是把教材中有证据支持的业务动作、输入、输出、条件、分叉、反馈和桥接关系结构化，服务后续选项证据与解析生成。

核心口径：

```text
P0-P6 = 教材复习型 KG
P7 = 流程型/操作型 KG overlay
```

## 目标

P7 要回答的问题不是“两个 core_point 是否相关”，而是：

```text
某个业务动作使用什么输入？
产生什么资料、事件或记录？
在什么条件下触发下一步？
审核时对照什么基准？
调查阶段查看什么对象？
结果是否反馈更新风险画像、KYC refresh、阈值或监控策略？
不同流程子图之间通过什么对象或证据桥接？
```

典型目标链条：

```text
CDD/KYC -> customer profile / expected activity
customer profile / expected activity -> transaction monitoring baseline
abnormal activity -> alert
alert review -> customer profile / account history / transaction type
investigation -> historical transactions / fund flows / external information
investigation result -> risk reassessment / KYC refresh / SAR / close and document
```

## 核心产物

P7 的正式产物不是单张全书大流程图，而是：

```text
process cards               # 按章/节顺序阅读后留下的结构化流程卡片
procedural nodes            # Activity/Object/Event/Condition/Decision/Record 等节点
procedural edges            # 有 unit 证据的短流程边
process subgraphs           # 多个局部闭环流程子图
bridge edges                # 子图之间的桥接边
micro-textbook previews     # 面向后续解析系统的微缩教材文本
```

## 执行原则

1. 按教材原文顺序完整阅读，不用关键词片段替代上下文。
2. 输出采用结构化 process card，便于对比、校验、合并和回溯。
3. 每条正式边必须绑定 unit 级证据。
4. 只抽短边，不让 LLM 直接生成全书长链。
5. 长链由已审核短边程序化组装，并标注来源边。
6. 流程子图允许局部自环，但反馈边必须与普通顺序边区分。
7. 子图之间通过共享对象、明确桥接边或人工确认桥接关系连接。
8. explicit / strong_inference / weak_inference 必须分层；weak_inference 不进入正式层。

## 并行机制

P7 可以并行，但并行对象是“按统一契约抽局部流程卡片”，不是“各自画一张流程图”。

建议执行模式：

```text
主线程：定义 schema、生成任务、合并结果、裁决冲突、输出正式 overlay
Reader A：按章保守阅读，只抽 explicit 边
Reader B：按章流程阅读，允许 strong_inference，但必须标注证据和不确定性
脚本：归一化、去重、边类型校验、证据校验、差异对齐、报告生成
```

每个关键 chapter reading task 至少双读。两个 reader 互相不可见，输出统一格式。合并阶段把边分为：

```text
consensus_edge       # 两路均抽到
single_reader_edge   # 单路抽到，进入复核
conflict_edge        # 方向、类型或推理强度冲突
bridge_needed        # 两路都提示需要跨章背景
```

## 阶段草案

```text
P7A：生成 chapter reading tasks，不删上下文
P7B：双路独立顺序阅读，输出 chapter_flow_overview 和 process_cards
P7C：流程节点归一化、边级对齐、双路差异比较
P7D：冲突裁决、桥接边审核、证据校验
P7E：组装局部闭环流程子图
P7F：输出 kg_procedural_overlay.json 和微缩教材视图
```

## 输入

主要输入：

```text
../phase06_kg_views/outputs/kg_retrieval_graph.json
../phase05_terms/outputs/p5c_alias_index.json
```

P6 提供统一 KG 母版；P5C 只用于术语规范化和别名识别，不作为流程边证据。

## 输出规划

```text
outputs/p7_chapter_reading_tasks.jsonl
outputs/p7_process_cards.reader_a.jsonl
outputs/p7_process_cards.reader_b.jsonl
outputs/p7_process_cards_merged.jsonl
outputs/p7_procedural_nodes.jsonl
outputs/p7_procedural_edges.jsonl
outputs/p7_bridge_edges.jsonl
outputs/p7_process_subgraphs.json
outputs/kg_procedural_overlay.json

reports/p7_reader_diff_report.md
reports/p7_edge_quality_report.md
reports/p7_bridge_review_report.md

previews/p7_process_subgraphs.md
previews/p7_micro_textbook.md
```

## 边界

P7 不做：

```text
不修改 frozen unit
不修改 P1-P6 正式产物
不重判 P3/P4 的 CP 关系
不把术语同义关系当流程边
不让单个 LLM 一次性生成全书大流程图
不把行业常识写成正式教材边
```

P7 做：

```text
按章/节顺序完整阅读教材上下文
记录结构化流程卡片
抽取有证据支持的短流程边
识别局部闭环与反馈边
比较双路 reader 输出
合并多个流程子图和桥接边
为后续选项证据与解析生成提供流程路径和微缩教材
```

